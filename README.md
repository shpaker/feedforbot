# FeedsBot for Telegram written on Python
Forwarding new articles from RSS/Atom feeds to Telegram.

##Usage
You can write the configuration file...  
```yaml
token: 'YOUR_SECRET_TELEGRAM_TOKEN'
feeds:
  - url    : 'https://example.site/feed1.rss'
    id     : '@your_channel'
    delay  : 300   # Optional. 600 by default
    preview: False # Optional. True by default 
    format : '<a href="$url$">$title$</a>\n<b>Tags:</b> $tags$\n<b>Author:</b> $author$' # Optional. '<b>$title$</b>\n$url$' by default
  - url    : 'https://example.site/feed2.rss'
    id     : 'your_telegram_id'
```
... and execute script:  
```python
python app.py
```
