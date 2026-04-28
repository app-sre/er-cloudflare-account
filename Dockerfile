FROM quay.io/redhat-services-prod/app-sre-tenant/er-base-terraform-main/er-base-terraform-main:0.5.0-6@sha256:d461e7418d12682e7da155c7760cf85b82c5d671e01d10fcb3ac3a1316d78af1 AS base
# keep in sync with pyproject.toml
LABEL konflux.additional-tags="0.1.0"
COPY LICENSE /licenses/
ENV VIRTUAL_ENV="${APP}/.venv" \
    PATH="${APP}/.venv/bin:${PATH}" \
    TERRAFORM_MODULE_SRC_DIR="./module"

#
# Builder image
#
FROM base AS builder
COPY --from=ghcr.io/astral-sh/uv:0.11.8@sha256:3b7b60a81d3c57ef471703e5c83fd4aaa33abcd403596fb22ab07db85ae91347 /uv /bin/uv

ENV UV_COMPILE_BYTECODE="true" \
    UV_NO_CACHE=true

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
COPY --from=builder ${APP} ${APP}
