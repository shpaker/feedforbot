# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).
Only full releases are listed — pre-release changes are included
in the next full version entry.

## [4.0.0] — Unreleased

### Changed

- Domain layer made synchronous; async execution moved to `Scheduler.arun()`
- Migrated from Poetry to uv + hatchling
- Dropped bandit; merged dev dependencies into single group
- Python requirement set to >=3.10 with CI matrix (3.10–3.14)
- Structured logging throughout core modules (cache, listener, scheduler, transport)
- Cache merges articles instead of overwriting — prevents re-sending articles that temporarily disappear from feeds
- Cache protocol uses `is_populated` property instead of `None` sentinel from `read()`
- Cache ID derived from listener/transport config values instead of `__repr__`
- `HttpClient` reuses a persistent `httpx.Client` (TCP/TLS connection reuse)
- `HttpClient` retries server errors (5xx) and network failures with exponential backoff (3 attempts)
- Jinja2 templates rendered via `SandboxedEnvironment` (SSTI mitigation)
- Sentry error reports include only `article_id`, not full article data
- Telegram Bot API token masked via `HttpClient` sensitive values (no token in logs or tracebacks)

### Added

- Full test suite: cache, config, http_client, listener, scheduler, transport (59 tests)
- `pytest-cov` for coverage reporting
- HTTP request timeouts (30s total, 10s connect) in `HttpClient`
- Correlation ID (`tick_id`) per scheduler tick for log tracing
- CLI `--healthcheck-port` option for container liveness probes
- JSON Schema for YAML config (`config.schema.json`, `just schema`)
- Dockerfile: multi-stage build, non-root `appuser`
- Docker images published to GHCR (`ghcr.io/shpaker/feedforbot`)
- OCI image labels and annotations for GHCR metadata

### Fixed

- Cache diff uses `set` lookups instead of linear search (O(n) vs O(n²))
- `FilesCache.read()` uses `try/except FileNotFoundError` instead of `exists()` + `open()` (TOCTOU fix)
- `FilesCache` creates nested data directories (`parents=True`)
- `FilesCache.write()` serializes datetimes properly (`model_dump(mode="json")`)
- CI version injection path for pyproject.toml and `__version__.py`
- Docker image tag strategy (removed SHA hash tags)
- GHCR package description display (provenance disabled, manifest annotations)

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

[4.0.0]: https://github.com/shpaker/feedforbot/compare/3.3.5...HEAD
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
