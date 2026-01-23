"""Import existing Cloudflare resources into Terraform state."""

import logging
import re
import subprocess

from cloudflare import Cloudflare
from external_resources_io.config import Config
from external_resources_io.input import parse_model, read_input_from_file
from external_resources_io.log import setup_logging
from external_resources_io.terraform import terraform_run
from pydantic import BaseModel

from .app_interface_input import (
    AppInterfaceInput,
    CloudflareAccount,
    CloudflareAccountMember,
)

logger = logging.getLogger(__name__)


class AccountNotFoundError(Exception):
    """Raised when an account cannot be found in Cloudflare."""


class ImportResult(BaseModel):
    """Result of a terraform import operation."""

    resource_address: str
    import_id: str
    success: bool
    error_message: str | None = None


def get_ai_input() -> AppInterfaceInput:
    """Get the AppInterfaceInput from the input file."""
    return parse_model(AppInterfaceInput, read_input_from_file())


def import_resource(
    resource_address: str,
    import_id: str,
    *,
    dry_run: bool = False,
) -> ImportResult:
    """Execute terraform import for a single resource.

    Args:
        resource_address: Terraform resource address (e.g., "cloudflare_account.this").
        import_id: The import ID (e.g., "account_id" or "account_id/member_id").
        dry_run: If True, only log the command without executing.

    Returns:
        ImportResult with success status and any error message.
    """
    try:
        terraform_run(["import", resource_address, import_id], dry_run=dry_run)
        logger.info("Successfully imported %s", resource_address)
        return ImportResult(
            resource_address=resource_address,
            import_id=import_id,
            success=True,
        )
    except subprocess.CalledProcessError as e:
        error_msg = str(e.stderr) if e.stderr else str(e)
        logger.warning("Failed to import %s: %s", resource_address, error_msg)
        return ImportResult(
            resource_address=resource_address,
            import_id=import_id,
            success=False,
            error_message=error_msg,
        )


def import_account(account_id: str, *, dry_run: bool = False) -> ImportResult:
    """Import the Cloudflare account."""
    return import_resource("cloudflare_account.this", account_id, dry_run=dry_run)


def sanitize_email(email: str) -> str:
    """Convert email to Terraform resource key format.

    Matches Terraform's: replace(lower(member.email), "/[^a-z0-9]+/", "-")

    Args:
        email: The email address to sanitize.

    Returns:
        Sanitized string suitable for use as a Terraform resource key.
    """
    return re.sub(r"[^a-z0-9]+", "-", email.lower())


def import_account_members(
    client: Cloudflare,
    account_id: str,
    members: list[CloudflareAccountMember],
    *,
    dry_run: bool = False,
) -> list[ImportResult]:
    """Import account members.

    Args:
        client: Cloudflare API client.
        account_id: The Cloudflare account ID.
        members: List of members from configuration to import.
        dry_run: If True, only log commands without executing.

    Returns:
        List of ImportResult for each member import operation.
    """
    try:
        member_id_by_email = {
            email: member.id
            for member in client.accounts.members.list(account_id=account_id)
            if (user := member.user) and (email := user.email)
        }
    except Exception:
        logger.exception("Failed to list members for account ID %s", account_id)
        return []

    results: list[ImportResult] = []
    for member in members:
        member_id = member_id_by_email.get(member.email)
        resource_address = (
            f'cloudflare_account_member.this["{sanitize_email(member.email)}"]'
        )

        if member_id is None:
            error_msg = f"Account member '{member.email}' not found"
            logger.error(error_msg)
            results.append(
                ImportResult(
                    resource_address=resource_address,
                    import_id="",
                    success=False,
                    error_message=error_msg,
                )
            )
        else:
            results.append(
                import_resource(
                    resource_address,
                    f"{account_id}/{member_id}",
                    dry_run=dry_run,
                )
            )
    return results


def import_state(
    client: Cloudflare,
    account: CloudflareAccount,
    *,
    dry_run: bool = False,
) -> list[ImportResult]:
    """Import all resources for a Cloudflare account.

    Args:
        client: Cloudflare API client.
        account: The CloudflareAccount configuration.
        dry_run: If True, only log commands without executing.

    Returns:
        List of ImportResult for each import operation.
    """
    if account.account_id is None:
        msg = "Account ID is required for import"
        logger.error(msg)
        raise AccountNotFoundError(msg)

    logger.info("Importing resources for account ID: %s", account.account_id)

    return [
        import_account(account.account_id, dry_run=dry_run),
        *import_account_members(
            client, account.account_id, account.members, dry_run=dry_run
        ),
    ]


def main() -> None:
    """Main entry point for import-tfstate CLI."""
    setup_logging()
    config = Config()

    ai_input = get_ai_input()
    client = Cloudflare()

    results = import_state(client, ai_input.data, dry_run=config.dry_run)

    succeeded = sum(1 for r in results if r.success)
    failed = sum(1 for r in results if not r.success)

    logger.info("Import complete: %d succeeded, %d failed", succeeded, failed)

    if failed > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
