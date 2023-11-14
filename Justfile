SOURCE_DIR := "feedforbot"

linters: mypy ruff bandit safety

ruff:
  poetry run ruff check --fix {{ SOURCE_DIR }}

mypy:
  poetry run mypy --pretty -p {{ SOURCE_DIR }}

bandit:
  poetry run bandit -r {{ SOURCE_DIR }}

safety:
  poetry run safety --disable-optional-telemetry-data check --full-report --file poetry.lock

pytest:
  poetry run pytest -vv
