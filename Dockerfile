FROM python:3.14-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /service
ADD pyproject.toml uv.lock README.md ./
ADD feedforbot feedforbot
RUN uv build
RUN uv venv .venv
RUN .venv/bin/pip install dist/*.whl

FROM python:3.14-slim AS runtime
WORKDIR /service
COPY --from=builder /service/.venv ./.venv
ENTRYPOINT ["/service/.venv/bin/python3", "-m", "feedforbot"]
