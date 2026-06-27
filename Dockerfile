FROM quay.io/redhat-services-prod/app-sre-tenant/er-base-terraform-main/er-base-terraform-main:0.6.0-6@sha256:d8b77d6253a9938040f5d7c7172f2d1b58773db2a1a9c618a1fb88d5e32ac850 AS base
# keep in sync with pyproject.toml
LABEL konflux.additional-tags="0.4.0"
COPY LICENSE /licenses/
ENV TERRAFORM_MODULE_SRC_DIR="./module"

#
# Builder image
#
FROM base AS builder
COPY --from=ghcr.io/astral-sh/uv:0.11.25@sha256:1e3808aa9023d0980e7c15b1fa7c1ac16ff35925780cf5c459858b2d693f01a9 /uv /bin/uv

# Terraform code
COPY ${TERRAFORM_MODULE_SRC_DIR} ${TERRAFORM_MODULE_SRC_DIR}
RUN terraform-provider-sync

COPY pyproject.toml uv.lock ./
# Test lock file is up to date
RUN uv lock --check
# Install the project dependencies
RUN uv sync --frozen --no-install-project --no-group dev

COPY README.md ./
COPY er_cloudflare_account ./er_cloudflare_account
RUN uv sync --frozen --no-group dev


#
# Test image
#
FROM builder AS test

COPY Makefile ./
RUN uv sync --frozen

COPY tests ./tests
RUN make test
#
# Production image
#
FROM base AS prod
COPY --from=builder ${TF_PLUGIN_CACHE_DIR} ${TF_PLUGIN_CACHE_DIR}
COPY --from=builder ${APP_ROOT} ${APP_ROOT}
