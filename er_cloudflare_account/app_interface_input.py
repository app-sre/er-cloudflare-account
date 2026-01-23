from external_resources_io.input import AppInterfaceProvision
from pydantic import BaseModel


class CloudflareAccount(BaseModel):
    """
    Data model for Cloudflare Account

    https://registry.terraform.io/providers/cloudflare/cloudflare/latest/docs/resources/account
    """

    account_id: str


class AppInterfaceInput(BaseModel):
    """Input model for AWS MSK"""

    data: CloudflareAccount
    provision: AppInterfaceProvision
