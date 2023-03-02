FeedForBot
==========

[![PyPI](https://img.shields.io/pypi/v/feedforbot.svg)](https://pypi.python.org/pypi/feedforbot)
[![PyPI](https://img.shields.io/pypi/dm/feedforbot.svg)](https://pypi.python.org/pypi/feedforbot)
[![Docker Pulls](https://img.shields.io/docker/pulls/shpaker/feedforbot)](https://hub.docker.com/r/shpaker/feedforbot)
[![PyPI](https://img.shields.io/badge/code%20style-black-000000.svg)](href="https://github.com/psf/black)

Forward links from RSS/Atom feeds to messengers

Installation
------------

```commandline
pip install feedforbot -U
```

Usage
-----

### From code

```python
import asyncio

from feedforbot import Scheduler, TelegramBotTransport, RSSListener


def main():
  loop = asyncio.new_event_loop()
  asyncio.set_event_loop(loop)
  scheduler = Scheduler(
    '* * * * *',
    listener=RSSListener('https://www.debian.org/News/news'),
    transport=TelegramBotTransport(
      token='123456789:AAAAAAAAAA-BBBB-CCCCCCCCCCCC-DDDDDD',
      to='@channel',
    )
  )
  scheduler.run()
  loop.run_forever()

if __name__ == '__main__':
  main()
```

### CLI

#### Save to file `config.yml` data

```yaml  
---
cache:
  type: 'files'
schedulers:
  - listener:
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
        url: 'https://habr.com/ru/rss/news/?fl=ru'
    transport:
      type: 'telegram_bot'
      params:
        token: '123456789:AAAAAAAAAA-BBBB-CCCCCCCCCCCC-DDDDDD'
        to: '@tmfeed'
        template: |-
          <b>{{ TITLE }}</b> #habr
          {{ ID }}
          <b>Tags</b>: {% for category in CATEGORIES %}{{ category }}{{ ", " if not loop.last else "" }}{% endfor %}
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

#### Start script

```commandline
feedforbot --verbose config.yml
```

### Docker 

#### Docker Hub

```commandline
docker run shpaker/feedforbot --help
```

#### GHCR

```commandline
docker run ghcr.io/shpaker/feedforbot --help
```
