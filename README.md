![Python version](https://img.shields.io/badge/python-3.5-brightgreen.svg)
<!--[![Build Status](https://travis-ci.org/shpaker/pyFeedsTgBot.svg?branch=master)](https://travis-ci.org/shpaker/pyFeedsTgBot)  -->
# FeedForBot

Forward links from RSS/Atom feeds to Telegram

## Configuration via environment variables

For configuration via environment variables should to set variable `ENV_CONFIGURATION` to `True`.

### Required variables:

* `TELEGRAM_TOKEN`
* `FEEDS_PATH`
* `REDIS_HOST`

### Optional variables:

* `IS_DEBUG`
* `REDIS_PORT`
* `TG_PROXY`

## Configuration file 

```yaml
- url   : 'http://feeds.rucast.net/radio-t'
  id    : '9429534'
- url   : 'http://www.opennet.ru/opennews/opennews_all.rss'
  id    : '@tmfeed'
  format: '<b>$title</b>\n$url\n$description #opennet'
```

## docker-compose example

### files and dirs

```bash
.
├── docker-compose.yml
├── feeds.yml
└── redis_data
```

### docker-compose.yml

```yaml
version: '3.7'

services:

  feedforbot:
    image: shpaker/feedforbot:2
    volumes:
      - ./bot_config.yml:/feedforbot/feeds.yml
    environment:
      TG_TOKEN: 123456789:AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqR
      TG_PROXY: socks5://proxy.feedforbot:9050
      REDIS_HOST: redis.feedforbot
      IS_DEBUG: "True"
    depends_on:
      - redis
      - proxy
    networks:
      feedforbot:
        aliases:
          - bot.feedforbot

  redis:
    image: redis:5-alpine
    command: redis-server --appendonly yes
    expose:
      - '6379'
    volumes:
      - ./redis_data:/data
    networks:
      feedforbot:
        aliases:
          - redis.feedforbot

  proxy:
    image: shpaker/torsocks:0.3.4.11
    expose:
      - '9050'
    restart: on-failure
    networks:
      feedforbot:
        aliases:
          - proxy.feedforbot

networks:
  feedforbot:
```
