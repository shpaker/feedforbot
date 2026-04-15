FROM ghcr.io/astral-sh/uv:0.7 AS uv

FROM python:3.14-slim AS builder

COPY --from=uv /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /service

# Cache dependency layer
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-editable --extra cli --no-dev

# Install project
COPY README.md ./
COPY feedforbot feedforbot
RUN uv sync --frozen --no-editable --extra cli --no-dev

FROM python:3.14-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --system appgroup && \
    useradd --system --gid appgroup --no-create-home appuser

WORKDIR /service
COPY --from=builder --chown=appuser:appgroup /service/.venv ./.venv

USER appuser

ENTRYPOINT ["/service/.venv/bin/python3", "-m", "feedforbot"]
