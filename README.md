![Python version](https://img.shields.io/badge/python-3.5-brightgreen.svg)
<!--[![Build Status](https://travis-ci.org/shpaker/pyFeedsTgBot.svg?branch=master)](https://travis-ci.org/shpaker/pyFeedsTgBot)  -->
# FeedsBot for Telegram written on Python

## Environment variables

### Required variables:

* `TELEGRAM_TOKEN`
* `FEEDS_PATH`

### Optional variables:

* `DEBUG_LOGS`
* `REDIS_HOST`
* `REDIS_PORT`
* `TG_PROXY`

## Configuration file example

```yaml
- url : 'https://example.site/feed1.rss'
  id  : '@your_channel'
- url : 'https://example.site/feed2.rss'
  id  : '@your_channel'
```

## Install requirements

```bash
pip install --requirement requirements.txt
```

## Start service

```python
python app.py
```
