# AGENTS.md

This file provides guidance to AI coding agents when working with code in this repository.

## Build and Development Commands

```bash
# Setup development environment
make dev-env
source .venv/bin/activate

# Run full test suite (lint + type check + tests)
make test

# Run a single test
uv run pytest tests/test_main.py::test_function_name -vv

# Format and lint code
make format

# Type checking only
uv run mypy

# Generate variables.tf from Pydantic models
make generate-variables-tf

# Lock Terraform providers for multiple platforms
make providers-lock

# Build container image
make build
```

## Architecture

This is an External Resources v2 (ERv2) module that provisions Cloudflare accounts via Terraform. The module follows a Python-to-Terraform configuration pipeline:

1. **Pydantic Input Models** (`er_cloudflare_account/app_interface_input.py`) - Define the input schema that App Interface provides. `AppInterfaceInput` wraps `CloudflareAccount` data with provisioning metadata.

2. **Entry Point** (`er_cloudflare_account/__main__.py`) - CLI `generate-tf-config` parses input and generates Terraform backend config + variables JSON via `external-resources-io`.

3. **State Import** (`er_cloudflare_account/import_tfstate.py`) - CLI `import-tfstate` imports existing Cloudflare resources into Terraform state. Uses Cloudflare API to resolve member IDs from emails.

4. **Terraform Module** (`module/`) - Provisions `cloudflare_account` and `cloudflare_account_member` resources. Member keys are sanitized emails (lowercase, non-alphanumeric replaced with `-`).

## Key Patterns

- Input models extend `external-resources-io` base classes for ERv2 compatibility
- Terraform variables are auto-generated from Pydantic models via `external-resources-io tf generate-variables-tf`
- Environment variable `DRY_RUN=True|False` controls import-tfstate execution
- `CLOUDFLARE_API_TOKEN` environment variable required for Terraform and API operations