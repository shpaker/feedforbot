SOURCE_DIR := "feedforbot"

linters: mypy ruff-check
tests: pytest
format: ruff-format ruff-fix

ruff-format:
  uv run ruff format {{ SOURCE_DIR }} tests

ruff-fix:
  uv run ruff check --fix --unsafe-fixes {{ SOURCE_DIR }} tests

ruff-check:
  uv run ruff check {{ SOURCE_DIR }}

mypy:
  uv run mypy --pretty -p {{ SOURCE_DIR }}

pytest:
  uv run pytest -vv

help:
  uv run python -m {{ SOURCE_DIR }} --help
