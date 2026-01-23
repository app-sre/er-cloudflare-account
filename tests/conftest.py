import pytest
from external_resources_io.input import parse_model

from er_cloudflare_account.app_interface_input import AppInterfaceInput


@pytest.fixture
def raw_input_data() -> dict:
    """Fixture to provide test data for the AppInterfaceInput."""
    return {
        "data": {
            "account_id": "some-id",
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
                "tf_state_key": "cloudflare/dev/account/cloudflare-account-example/terraform.tfstate",
            },
        },
    }


@pytest.fixture
def ai_input(raw_input_data: dict) -> AppInterfaceInput:
    """Fixture to provide the AppInterfaceInput."""
    return parse_model(AppInterfaceInput, raw_input_data)
