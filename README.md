FeedForBot
==========

[![PyPI Version](https://img.shields.io/pypi/v/feedforbot.svg)](https://pypi.python.org/pypi/feedforbot)
[![PyPI Downloads](https://img.shields.io/pypi/dm/feedforbot.svg)](https://pypi.python.org/pypi/feedforbot)
[![Docker Pulls](https://img.shields.io/docker/pulls/shpaker/feedforbot)](https://hub.docker.com/r/shpaker/feedforbot)
[![GHCR](https://img.shields.io/badge/GHCR-feedforbot-blue?logo=github)](https://ghcr.io/shpaker/feedforbot)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Monitors RSS/Atom feeds on a cron schedule and forwards new entries
to Telegram. Supports multiple feeds, Jinja2 message templates,
file-based caching to avoid duplicate sends, and optional Sentry
integration for error tracking.

Features
--------

- **Multiple feeds** — run any number of listener/transport pairs,
  each with its own cron schedule
- **Jinja2 templates** — full control over message formatting
  with access to article fields (`{{ TITLE }}`, `{{ URL }}`,
  `{{ TEXT }}`, `{{ CATEGORIES }}`, `{{ AUTHORS }}`, etc.)
- **Caching** — file-based (`~/.feedforbot/`) or in-memory; first
  run populates the cache silently to avoid flooding the channel
- **Sentry integration** — optional error tracking via `sentry-sdk`
- **Docker ready** — multi-arch images on GHCR and Docker Hub
- **Protocol-driven** — extend with custom listeners, transports,
  and cache backends by implementing simple protocols

Installation
------------

Requires **Python 3.10+**.

```commandline
pip install feedforbot -U
```

For the full CLI (Click, structlog, YAML config, Sentry):

```commandline
pip install "feedforbot[cli]" -U
```

Quick start
-----------

### As a library

```python
from feedforbot import Scheduler, TelegramBotTransport, RSSListener

scheduler = Scheduler(
    '*/5 * * * *',
    listener=RSSListener('https://www.debian.org/News/news'),
    transport=TelegramBotTransport(
        token='123456789:AAAAAAAAAA-BBBB-CCCCCCCCCCCC-DDDDDD',
        to='@channel',
    ),
)
scheduler.run()  # blocks, checks the feed every 5 minutes
```

### Async — multiple schedulers

```python
import asyncio

from feedforbot import Scheduler, TelegramBotTransport, RSSListener

schedulers = [
    Scheduler(
        '*/5 * * * *',
        listener=RSSListener('https://www.debian.org/News/news'),
        transport=TelegramBotTransport(
            token='123456789:AAAAAAAAAA-BBBB-CCCCCCCCCCCC-DDDDDD',
            to='@channel',
        ),
    ),
    Scheduler(
        '0 * * * *',
        listener=RSSListener('https://habr.com/ru/rss/all/all/'),
        transport=TelegramBotTransport(
            token='123456789:AAAAAAAAAA-BBBB-CCCCCCCCCCCC-DDDDDD',
            to='@another_channel',
        ),
    ),
]

async def main() -> None:
    await asyncio.gather(*(s.arun() for s in schedulers))

asyncio.run(main())
```

### CLI with YAML config

Create a `config.yml`:

```yaml
---
cache:
  type: 'files'
schedulers:
  - rule: '*/5 * * * *'
    listener:
      type: 'rss'
      params:
        url: 'https://habr.com/ru/rss/all/all/?fl=ru'
    transport:
      type: 'telegram_bot'
      params:
        token: '123456789:AAAAAAAAAA-BBBB-CCCCCCCCCCCC-DDDDDD'
        to: '@tmfeed'
        template: |-
          <b>{{ TITLE }}</b> #habr
          {{ ID }}
          <b>Tags</b>: {% for category in CATEGORIES %}{{ category }}{{ ", " if not loop.last else "" }}{% endfor %}
          <b>Author</b>: <a href="https://habr.com/users/{{ AUTHORS[0] }}">{{ AUTHORS[0] }}</a>
  - listener:
      type: 'rss'
      params:
        url: 'http://www.opennet.ru/opennews/opennews_all.rss'
    transport:
      type: 'telegram_bot'
      params:
        token: '123456789:AAAAAAAAAA-BBBB-CCCCCCCCCCCC-DDDDDD'
        to: '@tmfeed'
        disable_web_page_preview: yes
        template: |-
          <b>{{ TITLE }}</b> #opennet
          {{ URL }}

          {{ TEXT }}
```

Run:

```commandline
feedforbot --verbose config.yml
```

On the first run the cache is populated without sending messages,
so existing feed entries won't flood the channel.

#### Config reference

| Key | Description |
|-----|-------------|
| `cache.type` | `files` (persistent, default dir `~/.feedforbot/`) or `in_memory` |
| `cache.params` | Backend-specific options (e.g. custom path for `files`) |
| `schedulers[].rule` | Cron expression (e.g. `*/5 * * * *`) |
| `schedulers[].listener.type` | `rss` |
| `schedulers[].listener.params.url` | Feed URL |
| `schedulers[].transport.type` | `telegram_bot` |
| `schedulers[].transport.params.token` | Telegram Bot API token |
| `schedulers[].transport.params.to` | Chat ID or `@channel` name |
| `schedulers[].transport.params.template` | Jinja2 template string (HTML parse mode) |
| `schedulers[].transport.params.disable_web_page_preview` | `true` / `false` |

#### Template variables

All fields from `ArticleModel` are available in uppercase:

| Variable | Description |
|----------|-------------|
| `{{ TITLE }}` | Entry title |
| `{{ URL }}` | Entry link |
| `{{ ID }}` | Unique entry identifier |
| `{{ TEXT }}` | Entry summary / description |
| `{{ CATEGORIES }}` | List of tags/categories |
| `{{ AUTHORS }}` | List of authors |

Docker
------

Images are published to both **GHCR** and **Docker Hub** on every
release. Tags follow semver: `latest`, `4`, `4.0`, `4.0.0`.

```commandline
docker run -v $(pwd)/config.yml:/config.yml \
  ghcr.io/shpaker/feedforbot --verbose /config.yml
```

```commandline
docker run -v $(pwd)/config.yml:/config.yml \
  shpaker/feedforbot --verbose /config.yml
```

The container runs as a non-root user (`appuser`).

Healthcheck
-----------

The CLI includes a built-in HTTP healthcheck server. Pass
`--healthcheck-port` to expose a lightweight endpoint that responds
with `200 OK` on every request:

```commandline
feedforbot --healthcheck-port 8080 --verbose config.yml
```

Useful for container orchestrators (Docker `HEALTHCHECK`, Kubernetes
liveness probes, etc.):

```yaml
# docker-compose.yml
services:
  feedforbot:
    image: ghcr.io/shpaker/feedforbot
    command: ["--healthcheck-port", "8080", "--verbose", "/config.yml"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/"]
      interval: 30s
      timeout: 5s
      retries: 3
```

License
-------

[MIT](LICENSE)
