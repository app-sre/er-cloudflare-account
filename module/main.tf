provider "cloudflare" {
  # API token will be read from CLOUDFLARE_API_TOKEN environment variable
}

data "cloudflare_account_roles" "this" {
  account_id = var.account_id
}

locals {
  role_id_by_name = {
    for role in data.cloudflare_account_roles.this.result : role.name => role.id
  }
}

resource "cloudflare_account" "this" {
  name = var.name
  type = var.type

  settings = {
    enforce_twofactor = var.enforce_twofactor
  }
}

resource "cloudflare_account_member" "this" {
  for_each = {
    for member in var.members : replace(lower(member.email), "/[^a-z0-9]+/", "-") => member
  }

  account_id = cloudflare_account.this.id
  email      = each.value.email
  roles      = [for role_name in each.value.roles : local.role_id_by_name[role_name]]

  lifecycle {
    ignore_changes = [status]
  }
}
