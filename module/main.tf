provider "cloudflare" {
  # API token will be read from CLOUDFLARE_API_TOKEN environment variable
}

data "cloudflare_resource_groups" "account" {
  account_id = var.account_id
  name       = "com.cloudflare.api.account.${var.account_id}"
}

data "cloudflare_account_permission_groups" "permission_group" {
  for_each = toset(flatten([for member in var.members : member.roles]))

  account_id = var.account_id
  name       = each.value
}

locals {
  permission_group_ids_by_name = {
    for role_name, groups in data.cloudflare_account_permission_groups.permission_group :
    role_name => [
      for group in groups.result :
      group.id
      if group.meta.scopes == "com.cloudflare.api.account"
    ]
  }

  permission_group_id_by_name = {
    for role_name, ids in local.permission_group_ids_by_name :
    role_name => length(ids) == 1 ? ids[0] : null
  }

  resource_group_id = length(data.cloudflare_resource_groups.account.result[*].id) == 1 ? data.cloudflare_resource_groups.account.result[0].id : null
}

resource "cloudflare_account" "this" {
  name = var.name

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
  policies = [{
    access = "allow"
    permission_groups = [
      for role_name in each.value.roles :
      { id = local.permission_group_id_by_name[role_name] }
    ]
    resource_groups = [{
      id = local.resource_group_id
    }]
  }]

  lifecycle {
    ignore_changes = [status]

    precondition {
      condition = alltrue([
        for permission_group_id in values(local.permission_group_id_by_name) :
        permission_group_id != null
      ])
      error_message = "Every member role must resolve to exactly one account-scoped Cloudflare permission group."
    }

    precondition {
      condition     = local.resource_group_id != null
      error_message = "The account must expose exactly one Cloudflare account resource group."
    }
  }
}
