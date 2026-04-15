FeedForBot
==========

[![PyPI](https://img.shields.io/pypi/v/feedforbot.svg)](https://pypi.python.org/pypi/feedforbot)
[![PyPI](https://img.shields.io/pypi/dm/feedforbot.svg)](https://pypi.python.org/pypi/feedforbot)
[![Docker Pulls](https://img.shields.io/docker/pulls/shpaker/feedforbot)](https://hub.docker.com/r/shpaker/feedforbot)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Monitors RSS/Atom feeds on a cron schedule and forwards new entries to Telegram.
Supports multiple feeds, Jinja2 message templates, file-based caching
to avoid duplicate sends, and optional Sentry integration.

Installation
------------

Requires Python 3.14+.

```commandline
pip install feedforbot -U
```

For the CLI (includes Click, structlog, YAML config, Sentry):

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

Async version — useful when running multiple schedulers
or combining with other async tasks:

```python
import asyncio

from feedforbot import Scheduler, TelegramBotTransport, RSSListener

scheduler = Scheduler(
    '*/5 * * * *',
    listener=RSSListener('https://www.debian.org/News/news'),
    transport=TelegramBotTransport(
        token='123456789:AAAAAAAAAA-BBBB-CCCCCCCCCCCC-DDDDDD',
        to='@channel',
    ),
)

asyncio.run(scheduler.arun())
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

Docker
------

```commandline
docker run -v $(pwd)/config.yml:/config.yml \
  ghcr.io/shpaker/feedforbot --verbose /config.yml
```

Also available on [Docker Hub](https://hub.docker.com/r/shpaker/feedforbot):

```commandline
docker run -v $(pwd)/config.yml:/config.yml \
  shpaker/feedforbot --verbose /config.yml
```
