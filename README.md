# External Resources Cloudflare Account Module

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

External Resources (ERv2) module to provision and manage Cloudflare account via Terraform.

## Features

- Cloudflare account provisioning
- Account members management
- Import existing Cloudflare resources into Terraform state

## Usage

### Environment Setup

Create a `.env` file from `.env.example` and configure your Cloudflare API token:

```bash
cp .env.example .env
# Edit .env with your CLOUDFLARE_API_TOKEN
source .env
```

### Importing Existing Resources

To import existing Cloudflare resources into Terraform state,
ensure env vars are set and `terraform init` done, then run in terraform working directory:

```bash
# Preview what will be imported
DRY_RUN=True import-tfstate

# Execute import
DRY_RUN=False import-tfstate
```

## Development

### Setup

Create and activate a development virtual environment:

```bash
make dev-env
source .venv/bin/activate
```

### Testing

```bash
# Run full test suite (lint + type check + tests)
make test

# Run a single test
uv run pytest tests/test_main.py::test_function_name -vv

# Type checking only
uv run mypy
```

### Code Quality

```bash
# Format and lint code
make format
```

### Terraform

```bash
# Generate variables.tf from Pydantic models
make generate-variables-tf

# Lock providers for multiple platforms
make providers-lock
```

## Architecture

This module follows the ERv2 pattern:

1. **Pydantic input models** (`er_cloudflare_account/app_interface_input.py`) - Define input schema from App Interface
2. **Entry point** (`er_cloudflare_account/__main__.py`) - Parses input and generates Terraform config
3. **State import** (`er_cloudflare_account/import_tfstate.py`) - Imports existing resources into Terraform state
4. **Terraform module** (`module/`) - Provisions account and members

## License

This project is licensed under the terms of the [Apache 2.0 license](/LICENSE).
