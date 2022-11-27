FROM python:3.10-slim as base-image
ARG POETRY_VERSION=1.2.2
WORKDIR /service
RUN pip install "poetry==$POETRY_VERSION"
ADD pyproject.toml poetry.lock README.md ./
ADD feedforbot feedforbot
RUN poetry build
RUN python -m venv .venv
RUN .venv/bin/pip install dist/*.whl

FROM python:3.10-slim as runtime-image
WORKDIR /service
COPY --from=base-image /service/.venv ./.venv
ENTRYPOINT ["/service/.venv/bin/python3", "-m", "feedforbot"]
