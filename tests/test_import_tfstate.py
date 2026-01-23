"""Tests for import_tfstate module."""

import subprocess
from collections.abc import Iterator
from unittest.mock import MagicMock, call, create_autospec, patch

import pytest
from cloudflare.types.shared.member import Member, User

from er_cloudflare_account.import_tfstate import (
    main,
    sanitize_email,
)


def setup_cloudflare_client(
    mock_cloudflare: MagicMock,
    *,
    members: list | None = None,
) -> MagicMock:
    """Configure the Cloudflare client mock with account members."""
    mock_client = mock_cloudflare.return_value
    mock_client.accounts.members.list.return_value = members or []
    return mock_client


def build_input_data(
    *,
    account_id: str = "acct-123",
    members: list[dict] | None = None,
) -> dict:
    """Build input data with optional overrides."""
    return {
        "data": {
            "account_id": account_id,
            "name": "Test Account",
            "members": members or [],
        },
        "provision": {
            "provision_provider": "cloudflare",
            "provisioner": "dev",
            "provider": "account",
            "identifier": "cloudflare-account-example",
            "target_cluster": "appint-ex-01",
            "target_namespace": "cloudflare-account-example",
            "target_secret_name": "creds-cloudflare-account-example",
            "module_provision_data": {
                "tf_state_bucket": "external-resources-terraform-state-dev",
                "tf_state_region": "us-east-1",
                "tf_state_dynamodb_table": "external-resources-terraform-lock",
                "tf_state_key": "cloudflare/dev/account/example/terraform.tfstate",
            },
        },
    }


def create_mock_member(member_id: str, email: str) -> MagicMock:
    """Create a mock Cloudflare account member."""
    mock_user = create_autospec(User, instance=True)
    mock_user.configure_mock(email=email)

    mock_member = create_autospec(Member, instance=True)
    mock_member.configure_mock(id=member_id, user=mock_user)
    return mock_member


@pytest.fixture
def mock_read_input() -> Iterator[MagicMock]:
    """Mock read_input_from_file."""
    with patch("er_cloudflare_account.import_tfstate.read_input_from_file") as mock:
        yield mock


@pytest.fixture
def mock_cloudflare() -> Iterator[MagicMock]:
    """Mock Cloudflare client."""
    with patch("er_cloudflare_account.import_tfstate.Cloudflare") as mock:
        yield mock


@pytest.fixture
def mock_terraform_run() -> Iterator[MagicMock]:
    """Mock terraform_run."""
    with patch("er_cloudflare_account.import_tfstate.terraform_run") as mock:
        yield mock


@pytest.fixture(autouse=True)
def mock_logger() -> Iterator[MagicMock]:
    """Mock logger to suppress log output in tests."""
    with patch("er_cloudflare_account.import_tfstate.logger") as mock:
        yield mock


@pytest.fixture
def mock_dry_run(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DRY_RUN", "True")


@pytest.fixture
def mock_non_dry_run(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DRY_RUN", "False")


def test_import_account_only(
    mock_non_dry_run: None,  # noqa: ARG001
    mock_terraform_run: MagicMock,
    mock_cloudflare: MagicMock,
    mock_read_input: MagicMock,
) -> None:
    """Test importing account without members."""
    mock_read_input.return_value = build_input_data()
    setup_cloudflare_client(mock_cloudflare)

    main()

    assert mock_terraform_run.call_count == 1
    mock_terraform_run.assert_called_with(
        ["import", "cloudflare_account.this", "acct-123"],
        dry_run=False,
    )


def test_import_account_with_members(
    mock_non_dry_run: None,  # noqa: ARG001
    mock_terraform_run: MagicMock,
    mock_cloudflare: MagicMock,
    mock_read_input: MagicMock,
) -> None:
    """Test importing account with members."""
    mock_read_input.return_value = build_input_data(
        members=[
            {"email": "user@example.com", "roles": ["Administrator Read Only"]},
        ]
    )

    mock_member = create_mock_member("member-456", "user@example.com")
    setup_cloudflare_client(mock_cloudflare, members=[mock_member])

    main()

    mock_terraform_run.assert_has_calls([
        call(["import", "cloudflare_account.this", "acct-123"], dry_run=False),
        call(
            [
                "import",
                'cloudflare_account_member.this["user-example-com"]',
                "acct-123/member-456",
            ],
            dry_run=False,
        ),
    ])


def test_member_not_found_fails(
    mock_non_dry_run: None,  # noqa: ARG001
    mock_terraform_run: MagicMock,
    mock_cloudflare: MagicMock,
    mock_read_input: MagicMock,
) -> None:
    """Test member in config but not in Cloudflare causes failure."""
    mock_read_input.return_value = build_input_data(
        members=[
            {"email": "missing@example.com", "roles": ["Administrator Read Only"]},
        ]
    )
    setup_cloudflare_client(mock_cloudflare)

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
    # Account import should still be attempted
    assert mock_terraform_run.call_count == 1


def test_import_failure_exits_with_error(
    mock_non_dry_run: None,  # noqa: ARG001
    mock_terraform_run: MagicMock,
    mock_cloudflare: MagicMock,
    mock_read_input: MagicMock,
) -> None:
    """Test main exits with code 1 when terraform import fails."""
    mock_read_input.return_value = build_input_data()
    setup_cloudflare_client(mock_cloudflare)
    mock_terraform_run.side_effect = subprocess.CalledProcessError(
        returncode=1, cmd=["terraform", "import"]
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1


def test_dry_run_flag(
    mock_dry_run: None,  # noqa: ARG001
    mock_terraform_run: MagicMock,
    mock_cloudflare: MagicMock,
    mock_read_input: MagicMock,
) -> None:
    """Test dry_run config is passed to terraform_run."""
    mock_read_input.return_value = build_input_data()
    setup_cloudflare_client(mock_cloudflare)

    main()

    mock_terraform_run.assert_called_with(
        ["import", "cloudflare_account.this", "acct-123"],
        dry_run=True,
    )


@pytest.mark.parametrize(
    ("email", "expected"),
    [
        ("user@example.com", "user-example-com"),
        ("User.Name+tag@Example.COM", "user-name-tag-example-com"),
        ("test123@domain.org", "test123-domain-org"),
        ("a..b@@c..d", "a-b-c-d"),
    ],
)
def test_sanitize_email(email: str, expected: str) -> None:
    """Test email sanitization matches Terraform's format."""
    assert sanitize_email(email) == expected
