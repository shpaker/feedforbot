SOURCE_PATH := "feedforbot/"
TEST_PATH := "tests/"

upgrade:
    uv lock --upgrade

lint:
    uv run ruff check {{ SOURCE_PATH }}
    uv run python -m mypy --pretty {{ SOURCE_PATH }}

fix:
    uv run ruff format {{ SOURCE_PATH }} {{ TEST_PATH }}
    uv run ruff check --fix --unsafe-fixes {{ SOURCE_PATH }}

tests:
    uv run pytest {{ TEST_PATH }}
