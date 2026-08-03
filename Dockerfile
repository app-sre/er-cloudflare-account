FROM quay.io/redhat-services-prod/app-sre-tenant/er-base-terraform-main/er-base-terraform-main:0.6.0-12@sha256:da8c452228f77f067bb95698e2c7a60c7785cae6b68f3942f0ce9ef244bafe2e AS base
# keep in sync with pyproject.toml
LABEL konflux.additional-tags="0.4.0"
COPY LICENSE /licenses/
ENV TERRAFORM_MODULE_SRC_DIR="./module"

#
# Builder image
#
FROM base AS builder
COPY --from=ghcr.io/astral-sh/uv:0.12.1@sha256:cf4eedcaa81655197f625739489effcbe71b61ceb1506f332c3facae5deceded /uv /bin/uv

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
