# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).
Only full releases are listed — pre-release changes are included
in the next full version entry.

## [5.0.0] — 2026-04-17

### Added

- `--healthcheck-host` CLI option (defaults to `127.0.0.1`) — previously bound to `0.0.0.0` unconditionally
- `HttpClientProtocol`, `ListenerProtocol`, `TransportProtocol` are now context managers (`__enter__`/`__exit__`) with a required `close()` method — scheduler closes listener/transport (and their HTTP clients) cleanly on shutdown
- Per-scheduler `cache_limit` config option — caps the number of entries kept in cache (keeps the N most recent by `grabbed_at`); unbounded when unset
- `--cache-dsn` CLI flag (default `file:`) — cache backend is now configured on the command line via a URL-style DSN (`file:` persists at `~/.feedforbot/`, `file:///custom/path` uses a custom directory, `memory:` is in-process). Designed to scale to future backends (e.g. `redis://host:6379/0`) without proliferating flags
- `RedisCache` backend + `redis://…` / `rediss://…` / `unix://…` DSN schemes — shared cache suitable for multi-instance deployments and docker-compose setups. Ships with the `cli` extra (`pip install feedforbot[cli]`) and the GHCR Docker image. The `redis` package is an **optional** dependency — `RedisCache(...)` raises a clear `ImportError` when it isn't installed, so core installs (`pip install feedforbot`) stay minimal

### Changed

- **Breaking:** healthcheck endpoint now responds only at `/health` (previously matched every path) — Docker/Kubernetes probes configured against `/` must be updated
- **Breaking:** YAML config is now a top-level list of listener+transport entries; the `cache:` and `schedulers:` wrapper keys have been removed. CLI positional argument renamed from `CONFIGURATION` to `SCHEDULERS_FILE`. Cache backend selection moved from `cache.type` in the YAML to the new `--cache-dsn` CLI flag.
- **Breaking:** `CacheProtocol` redesigned around `is_populated` / `known_ids` / `add(*articles)` / `trim(limit)` (previously `read` / `write` / `is_populated`). `FilesCache` on-disk schema is now `[{"id", "grabbed_at"}]` (no title/url/text). Files written by earlier versions are detected on load, deleted, and treated as a first-run (no spam on upgrade). Custom cache implementations must be updated.

### Fixed

- `FilesCache` writes atomically (tempfile + `os.replace`) — no more corrupted cache on crash/power loss mid-write
- `FilesCache` tolerates corrupt/invalid cache files — logs a warning, deletes the file and treats it as a first-run instead of propagating to Sentry
- `FilesCache` no longer grows unbounded — use the new `cache_limit` scheduler option to cap retention
- `HttpClient.post` raises `HttpResponseError` on non-JSON or non-object payloads (e.g. HTML error pages from Telegram API proxies) instead of leaking `JSONDecodeError`
- Telegram default and custom templates now HTML-escape article fields (title/text/etc.) — prevents Telegram API rejecting messages with `&`, `<`, `>` in content
- Config with empty `schedulers: []` is now rejected at parse time instead of crashing with `ValueError` in `ThreadPoolExecutor`
- `RSSListener` skips individual malformed feed entries (missing `summary`/`title`) with a warning instead of failing the whole tick
- Telegram bot token masking now covers error-path log lines (`http_error:`) — token could previously leak via `str(exc)` when httpx included the URL in connection errors
- HTTP 429 flood-wait responses are now retried after the `Retry-After` delay (capped by `max_retry_after`, default 60s) instead of failing the send immediately — Telegram rate-limit bursts self-heal
- CLI graceful shutdown: `shutdown_start` / `shutdown_complete` are logged on SIGTERM/SIGINT, `CancelledError` is no longer reported as a crash, a second signal forces an immediate `loop.stop()` escape hatch, and Windows (no POSIX signals) falls back to `KeyboardInterrupt` without raising

## [4.0.0] — 2026-04-15

### Changed

- Migrated from Poetry to uv
- Python >=3.10 with CI matrix (3.10–3.14)
- Structured logging throughout core modules
- Domain layer made synchronous (async only in Scheduler)
- Cache merges articles instead of overwriting — prevents re-sending articles that temporarily disappear from feeds
- HTTP client reuses persistent connections and retries server errors with exponential backoff
- Jinja2 templates rendered in sandbox (SSTI mitigation)
- Telegram Bot API token no longer appears in logs or tracebacks
- New articles sorted chronologically before sending
- All GitHub Actions pinned to commit SHAs

### Added

- Healthcheck endpoint (`--healthcheck-port`)
- JSON Schema for YAML config (`just schema`)
- HTTP request timeouts (30s total, 10s connect)
- Correlation ID per scheduler tick for log tracing
- Docker images published to GHCR (`ghcr.io/shpaker/feedforbot`)
- Comprehensive test suite (listeners, transports, scheduler, cache, http client, config)
- GitHub Actions deploy workflow for tmfeed (triggers on release or config change)

### Fixed

- Scheduler silently dying on unhandled tick exceptions — now catches, logs with full traceback, reports to Sentry, and continues
- `TelegramBotTransport` silently ignoring API errors (ok=false)
- `ArticleModel.__eq__` raising `AttributeError` on non-model types
- `RSSListener` crashing on `<img>` tags without `src` attribute
- Cache diff performance (set lookups instead of linear search)
- File cache race condition on read
- File cache datetime serialization
- Docker image tag strategy and GHCR metadata

## [3.3.5] — 2024-12-29

### Changed

- Bumped dependencies

## [3.3.4] — 2024-11-23

### Changed

- Bumped dependencies

## [3.3.3] — 2024-02-20

### Fixed

- Incorrect scope creation in Sentry event handler

## [3.3.2] — 2024-02-16

### Changed

- Bumped dependencies

## [3.3.1] — 2023-11-15

### Changed

- Extended Sentry error reports with additional context
- Bumped dependencies

## [3.3.0] — 2022-12-07

### Added

- Additional parameters for Telegram Bot API transport (`disable_web_page_preview`, etc.)

## [3.2.0] — 2022-11-28

### Added

- Categories support in feed articles (`{{ CATEGORIES }}` template variable)

## [3.1.2] — 2022-11-28

### Fixed

- `FileExistsError` when cache directory already exists

## [3.1.1] — 2022-11-28

### Fixed

- Incorrect cache IDs causing cache misses

## [3.1.0] — 2022-11-28

### Added

- Sentry integration for error tracking

## [3.0.2] — 2022-11-27

### Fixed

- Typo in logging level name

## [3.0.1] — 2022-11-27

### Added

- `__repr__` methods for core classes
- Improved logging output

## [3.0.0] — 2022-11-27

### Changed

- Complete rewrite: protocol-driven architecture with `ListenerProtocol`, `TransportProtocol`, `CacheProtocol`
- Pydantic v2 models for articles
- Click-based CLI with YAML configuration
- Jinja2 message templates
- File-based and in-memory cache backends
- Docker support

[4.0.0]: https://github.com/shpaker/feedforbot/compare/3.3.5...4.0.0
[3.3.5]: https://github.com/shpaker/feedforbot/compare/3.3.4...3.3.5
[3.3.4]: https://github.com/shpaker/feedforbot/compare/3.3.3...3.3.4
[3.3.3]: https://github.com/shpaker/feedforbot/compare/3.3.2...3.3.3
[3.3.2]: https://github.com/shpaker/feedforbot/compare/3.3.1...3.3.2
[3.3.1]: https://github.com/shpaker/feedforbot/compare/3.3.0...3.3.1
[3.3.0]: https://github.com/shpaker/feedforbot/compare/3.2.0...3.3.0
[3.2.0]: https://github.com/shpaker/feedforbot/compare/3.1.2...3.2.0
[3.1.2]: https://github.com/shpaker/feedforbot/compare/3.1.1...3.1.2
[3.1.1]: https://github.com/shpaker/feedforbot/compare/3.1.0...3.1.1
[3.1.0]: https://github.com/shpaker/feedforbot/compare/3.0.2...3.1.0
[3.0.2]: https://github.com/shpaker/feedforbot/compare/3.0.1...3.0.2
[3.0.1]: https://github.com/shpaker/feedforbot/compare/3.0.0...3.0.1
[3.0.0]: https://github.com/shpaker/feedforbot/releases/tag/3.0.0
