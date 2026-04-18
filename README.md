FeedForBot 📡
=============

[![PyPI Version](https://img.shields.io/pypi/v/feedforbot.svg)](https://pypi.python.org/pypi/feedforbot)
[![PyPI Downloads](https://img.shields.io/pypi/dm/feedforbot.svg)](https://pypi.python.org/pypi/feedforbot)
[![Docker Pulls](https://img.shields.io/docker/pulls/shpaker/feedforbot)](https://hub.docker.com/r/shpaker/feedforbot)
[![GHCR](https://img.shields.io/badge/GHCR-feedforbot-blue?logo=github)](https://ghcr.io/shpaker/feedforbot)
[![Lint](https://github.com/shpaker/feedforbot/actions/workflows/lint.yml/badge.svg)](https://github.com/shpaker/feedforbot/actions/workflows/lint.yml)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

> RSS/Atom in, Telegram out. 🪄 Fresh entries arrive, templated into
> tidy messages, deduped via your cache of choice — on a cron schedule,
> with a healthcheck and graceful shutdown baked in.

✨ Features
-----------

- 📬 **Multiple feeds** — any number of listeners/transports, each on its own cron
- 🎨 **Jinja2 templates** — sandbox + HTML autoescape, full access to article fields
- 💾 **Pluggable cache** — files, in-memory, or Redis; first run silent to avoid flood
- 🩺 **Healthcheck** — HTTP `/health` for Docker/Kubernetes probes
- 🛡️ **Resilient delivery** — auto-retry on Telegram flood-wait, skip malformed entries
- 🧹 **Graceful shutdown** — SIGTERM/SIGINT drain ticks and close handles cleanly
- 🐛 **Sentry integration** — optional error tracking
- 🐳 **Docker ready** — multi-arch GHCR + Docker Hub images, runs as non-root
- 🧩 **Protocol-driven** — custom listeners/transports/caches via simple protocols

📦 Installation
---------------

Requires **Python 3.10+**.

```commandline
pip install feedforbot -U
```

For the full CLI (Click, structlog, YAML config, Sentry, Redis):

```commandline
pip install "feedforbot[cli]" -U
```

🚀 Quick start
--------------

### 🐍 As a library

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

### ⚡ Async — multiple schedulers

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

### 📝 CLI with YAML config

Create a `schedulers.yml` — a top-level list of listener+transport entries:

```yaml
---
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
feedforbot --verbose schedulers.yml
```

On the first run the cache is populated without sending messages,
so existing feed entries won't flood the channel. 🤫

#### 📋 Config reference

Each list entry supports:

| Key | Description |
|-----|-------------|
| `rule` | Cron expression (e.g. `*/5 * * * *`), optional — defaults to `* * * * *` (every minute) |
| `cache_limit` | Max cache entries kept (keeps N most recent by `grabbed_at`), optional — unbounded when unset |
| `listener.type` | `rss` |
| `listener.params.url` | Feed URL |
| `transport.type` | `telegram_bot` |
| `transport.params.token` | Telegram Bot API token |
| `transport.params.to` | Chat ID or `@channel` name |
| `transport.params.template` | Jinja2 template string (HTML parse mode), optional — defaults to `{{ TITLE }}\n\n{{ TEXT }}\n\n{{ URL }}` |
| `transport.params.disable_web_page_preview` | `true` / `false`, optional — defaults to `false` |
| `transport.params.disable_notification` | `true` / `false`, optional — defaults to `false` |

An empty top-level list is rejected at parse time.

#### 💾 Cache CLI flag

Cache backend selection is a CLI concern (not part of the schedulers file).
`--cache-dsn` takes a URL-style DSN; scheme selects the backend:

| DSN | Backend |
|-----|---------|
| `file:` (default) | Persistent on-disk cache at `~/.feedforbot/` |
| `file:///custom/path` | Persistent on-disk cache at a custom directory |
| `memory:` | In-process cache (lost on restart) |
| `redis://host:6379/0` | Shared Redis cache (requires `feedforbot[cli]` or `pip install redis`). Useful for multi-instance deployments and docker-compose setups where a separate Redis container holds state. |

#### 🧩 Template variables

All fields from `ArticleModel` are available in uppercase:

| Variable | Description |
|----------|-------------|
| `{{ TITLE }}` | Entry title |
| `{{ URL }}` | Entry link |
| `{{ ID }}` | Unique entry identifier |
| `{{ TEXT }}` | Entry summary / description |
| `{{ CATEGORIES }}` | List of tags/categories |
| `{{ AUTHORS }}` | List of authors |
| `{{ GRABBED_AT }}` | Timestamp when the entry was fetched (UTC) |

Templates render in a Jinja2 sandbox with HTML autoescape enabled
(messages use `parse_mode=HTML`). Article fields containing `&`,
`<`, `>` are escaped automatically — you don't need to guard against
Telegram rejecting the message for invalid HTML.

#### 🎛️ CLI options

| Option | Description |
|--------|-------------|
| `SCHEDULERS_FILE` | Positional — path to the YAML schedulers config |
| `-v`, `--verbose` | Repeat for more detail (`-v` INFO, `-vv` DEBUG, `-vvv` NOTSET) |
| `-V`, `--version` | Print version and exit |
| `--cache-dsn` | Cache backend DSN (see table above); default `file:` |
| `--sentry` | Sentry DSN for error reporting |
| `--healthcheck-port` | Port for the HTTP healthcheck server (disabled when unset) |
| `--healthcheck-host` | Bind host for the healthcheck server; default `127.0.0.1`. Use `0.0.0.0` inside containers when the port is exposed to the host |

🐳 Docker
---------

Images are published to both **GHCR** and **Docker Hub** on every
release. Tags follow semver: `latest`, `5`, `5.0`, `5.0.0`.

```commandline
docker run -v $(pwd)/schedulers.yml:/schedulers.yml \
  ghcr.io/shpaker/feedforbot --verbose /schedulers.yml
```

```commandline
docker run -v $(pwd)/schedulers.yml:/schedulers.yml \
  shpaker/feedforbot --verbose /schedulers.yml
```

The container runs as a non-root user (`appuser`).

🩺 Healthcheck
--------------

The CLI includes a built-in HTTP healthcheck server. Pass
`--healthcheck-port` to expose a lightweight endpoint that responds
with `200 OK` at `/health` (other paths return `404 Not Found`):

```commandline
feedforbot --healthcheck-port 8080 --verbose schedulers.yml
```

The server binds to `127.0.0.1` by default. Pass
`--healthcheck-host 0.0.0.0` when the port must be reachable from
outside the container (e.g. for an external probe); the in-container
Docker `HEALTHCHECK` below works either way since it queries
`localhost` from the same network namespace.

Useful for container orchestrators (Docker `HEALTHCHECK`, Kubernetes
liveness probes, etc.):

```yaml
# docker-compose.yml
services:
  feedforbot:
    image: ghcr.io/shpaker/feedforbot
    command: ["--healthcheck-port", "8080", "--verbose", "/schedulers.yml"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 5s
      retries: 3
```

🧱 Docker Compose with Redis
----------------------------

For multi-instance deployments or when you want cache state to
survive container rebuilds without a host volume for JSON files,
run `feedforbot` alongside a Redis container and point
`--cache-dsn` at it:

```yaml
# docker-compose.yml
services:
  redis:
    image: redis:7-alpine
    restart: always
    volumes:
      - ./redis_data:/data
    command: ["redis-server", "--save", "60", "1", "--appendonly", "no"]
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3
      start_period: 5s

  feedforbot:
    image: ghcr.io/shpaker/feedforbot
    restart: always
    depends_on:
      redis:
        condition: service_healthy
    volumes:
      - ./schedulers.yml:/schedulers.yml:ro
    command: >
      -v
      --cache-dsn redis://redis:6379/0
      --healthcheck-port 8080
      /schedulers.yml
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s
```

A working Ansible playbook that deploys this layout is in
[tmfeed/deploy.playbook.yml](tmfeed/deploy.playbook.yml).

📄 License
----------

[MIT](LICENSE)
