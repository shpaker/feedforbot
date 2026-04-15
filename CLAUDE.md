# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

All commands use uv. Use `just` targets for convenience (see `Justfile`), or invoke directly:

```bash
# Tests
uv run pytest -vv                          # all tests
uv run pytest -vv tests/listeners/         # single directory
uv run pytest -vv tests/listeners/test_rss.py::test_name  # single test

# Linting
uv run mypy --pretty -p feedforbot
uv run ruff check --fix --unsafe-fixes feedforbot
uv run bandit -r feedforbot

# Formatting
uv run ruff format feedforbot tests
uv run ruff check --fix feedforbot tests

# Run CLI
uv run feedforbot --help
uv run feedforbot --verbose config.yml
```

## Architecture

The domain abstractions live in `feedforbot/` and are protocol-driven:

- **`ListenerProtocol`** — fetches articles from a source (`receive() -> tuple[ArticleModel, ...]`). Only implementation: `RSSListener` (fetches via `HttpClient`, parses with feedparser + BeautifulSoup).
- **`TransportProtocol`** — delivers articles (`send(*articles) -> list[ArticleModel]`). Only implementation: `TelegramBotTransport` (Jinja2 template → Telegram Bot API).
- **`CacheProtocol`** — tracks which articles have already been sent (`read/write`). Two implementations: `InMemoryCache` (in-process, lost on restart) and `FilesCache` (JSON files in `~/.feedforbot/`, keyed by SHA2 of the listener+transport identity).
- **`HttpClient`** — synchronous HTTP client wrapping httpx. Raises `HttpTransportError` (network/timeout) or `HttpResponseError` (4xx/5xx) — both subclass `HttpClientError`. httpx is an implementation detail and must not leak outside this module.

**`Scheduler`** wires these together: on each cron tick it calls `listener.receive()`, diffs against cache, sends new articles via transport, then updates the cache. Public API: `run()` (sync blocking cron loop) and `arun()` (async cron loop); `stop()` signals both to exit. Internally `_tick()` executes one iteration synchronously. Uses `croniter` directly for cron scheduling. First run (empty cache) populates the cache without sending — this prevents spam on startup.

**`ArticleModel`** uses Pydantic v2 with `alias_generator=str.upper`, so template variables are uppercase (`{{ TITLE }}`, `{{ URL }}`, `{{ CATEGORIES }}`, etc.). Equality is identity-based on `id` (the feed entry ID or link).

CLI infrastructure lives in `feedforbot/cli/`:
- **`cli/app.py`** — Click command, Sentry init, event loop
- **`cli/config.py`** — reads YAML config, constructs `Scheduler` instances via `Enum`-based mappings
- **`cli/logger.py`** — structlog configuration
- **`cli/utils.py`** — CLI helpers (version echo)

Package metadata (`APP_NAME`, `VERSION`, etc.) lives in `feedforbot/__version__.py`.

## Extending

To add a new listener or transport:
1. Create a new class implementing `ListenerProtocol` / `TransportProtocol` in `feedforbot/`.
2. Add an entry to the corresponding `_*Types` and `_*ConfigMapping` enums in `feedforbot/cli/config.py`.
3. Export from `feedforbot/__init__.py`.

## Testing rules

- **`respx`** is allowed **only** in `tests/test_http_client.py` (tests for `HttpClient` itself). All other tests must use dependency inversion — inject fakes/stubs implementing the corresponding protocols instead of mocking HTTP at the transport level.
- **`HttpClient`** and **`HttpClientProtocol`** are internal implementation details and must **not** be re-exported from `feedforbot/__init__.py`.

## Changelog rules

- `CHANGELOG.md` records only **full releases** (no entries for `rc`/`alpha`/`beta` tags). Pre-release changes are folded into the next full version entry.
- Format: [Keep a Changelog](https://keepachangelog.com/), sections: Added / Changed / Fixed / Removed.
- **Before every push**, verify that `CHANGELOG.md` is up to date: if the branch introduces user-visible changes (features, fixes, breaking changes), they must be listed under the `[Unreleased]` / next-version heading before pushing.

## Formatting rules

- `ruff format` line length: **79**
- `ruff check` line length: **79**
- mypy is strict (`disallow_untyped_defs`, `no_implicit_reexport`)
