SOURCE_DIR := "feedforbot"

linters: mypy ruff bandit
tests: pytest
format: isort black

isort:
  poetry run isort {{ SOURCE_DIR }} --diff --color --check-only

black:
  poetry run isort {{ SOURCE_DIR }}

ruff:
  poetry run ruff check --fix --unsafe-fixes {{ SOURCE_DIR }}

mypy:
  poetry run mypy --pretty -p {{ SOURCE_DIR }}

bandit:
  poetry run bandit -r {{ SOURCE_DIR }}

safety:
  poetry run safety --disable-optional-telemetry-data check --file poetry.lock

pytest:
  poetry run pytest -vv
