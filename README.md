![Python version](https://img.shields.io/badge/python-3.5-brightgreen.svg)
<!--[![Build Status](https://travis-ci.org/shpaker/pyFeedsTgBot.svg?branch=master)](https://travis-ci.org/shpaker/pyFeedsTgBot)  -->
# FeedsBot for Telegram written on Python
Ботик перенаправляющий новые сообщения с указанных RSS к указанным Телеграм-получателям (таковыми могут выступать как каналы, так и конкретные пользователи, если указать в качестве получаетеля числовой ID конкретного пользователя). Бот может работать с большим количеством источников.  
Для запуска необходим пайтон не ниже версии 3,5 ибо аскини. И не забываем установить зависимости:  
```bash
pip install -r requirements.txt
```
Скриптик маленький и немного страшненький, но он же работает и это отрадно.  
Если захотелось сказать мне спасибо, то можно меня поддержать копейкой на следующей страничке:  
http://yasobe.ru/na/screwdriver  
А если финансовые отношения для вас не приемлемы, то подписывайтесь на канал https://t.me/g33ks  
Всем бобра!

## Usage
Для базового использования необходимо всего лиш корректно заполнить файл config.yml
```yaml
token: 'Секретный_токен_вашего_бота'
feeds:
  - url    : 'https://example.site/feed1.rss' # Источник
    id     : '@your_channel' # Получатель
    delay  : 300   # Период опроса. Опционально. 600 по умолчанию, т.е. 10 минут
    preview: False # Опционально. True по умолчанию 
    format : '<a href="$url">$title</a>\n<b>Author:</b> $author' # Опционально. Формат выводимого сообщения. По умолчанию: '<b>$title</b>\n$url' by default
  - url    : 'https://example.site/feed2.rss'
    id     : 'your_telegram_id'
```
И запустить скрипт  
```python
python app.py
```
Опции запуска можно посмотреть с коммандой `-h`
```python
python app.py -h
```
## В формате выводимого сообщения можно использовать слежующие ключевые слова:
* $author
* $description
* $tags
* $time
* $title
* $url
