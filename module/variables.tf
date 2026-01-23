variable "account_id" {
  type    = string
  default = null
}

variable "enforce_twofactor" {
  type    = bool
  default = null
}

variable "members" {
  type    = list(object({ email = string, roles = list(string) }))
  default = []
}

variable "name" {
  type = string
}

variable "type" {
  type    = string
  default = null
}
