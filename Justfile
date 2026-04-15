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
  uv run pytest -vv --cov=feedforbot --cov-report=term-missing

schema:
  uv run python -c "from feedforbot.cli.config import _ConfigModel; import json; s = _ConfigModel.model_json_schema(); s['title'] = 'FeedForBot Configuration'; print(json.dumps(s, indent=2))" > config.schema.json

help:
  uv run python -m {{ SOURCE_DIR }} --help

# Deploy tmfeed to VDS
tmfeed-deploy:
  set -a && source tmfeed/.env && set +a && ansible-playbook -i tmfeed/inventory.ini tmfeed/deploy.yml
