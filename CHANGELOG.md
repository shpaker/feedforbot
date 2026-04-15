# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).
Only full releases are listed — pre-release changes are included
in the next full version entry.

## [4.0.0] — Unreleased

### Changed

- Migrated from Poetry to uv
- Python >=3.10 with CI matrix (3.10–3.14)
- Structured logging throughout core modules
- Cache merges articles instead of overwriting — prevents re-sending articles that temporarily disappear from feeds
- HTTP client reuses persistent connections and retries server errors with exponential backoff
- Jinja2 templates rendered in sandbox (SSTI mitigation)
- Telegram Bot API token no longer appears in logs or tracebacks

### Added

- Healthcheck endpoint (`--healthcheck-port`)
- JSON Schema for YAML config (`just schema`)
- HTTP request timeouts (30s total, 10s connect)
- Correlation ID per scheduler tick for log tracing
- Docker images published to GHCR (`ghcr.io/shpaker/feedforbot`)

### Fixed

- Scheduler silently dying on unhandled tick exceptions — now catches, logs with full traceback, reports to Sentry, and continues
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
