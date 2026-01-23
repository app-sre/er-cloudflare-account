from external_resources_io.input import AppInterfaceProvision
from pydantic import BaseModel


class CloudflareAccountMember(BaseModel):
    """
    Data model for Cloudflare Account Member

    https://registry.terraform.io/providers/cloudflare/cloudflare/latest/docs/resources/account_member
    """

    email: str
    roles: list[str]


class CloudflareAccount(BaseModel):
    """
    Data model for Cloudflare Account

    https://registry.terraform.io/providers/cloudflare/cloudflare/latest/docs/resources/account
    """

    account_id: str | None = None
    name: str
    type: str | None = None
    enforce_twofactor: bool | None = None
    members: list[CloudflareAccountMember] = []


class AppInterfaceInput(BaseModel):
    """Input model for AWS MSK"""

    data: CloudflareAccount
    provision: AppInterfaceProvision
