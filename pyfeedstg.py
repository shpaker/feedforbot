import asyncio
import html
import logging
from string import Template

import feedparser
import telepot
import yaml


class Server(object):
    def __init__(self, filename='config.yml'):
        self.filename = filename
        try:
            with open(filename, 'r', encoding='utf-8') as stream:
                try:
                    self.config = yaml.load(stream)
                except yaml.YAMLError as err:
                    logging.error(err)
        except OSError as err:
            logging.error(err)

    def run(self):
        loop = asyncio.get_event_loop()
        for feed in self.config['feeds']:
            forwarder = FeedForwarder(token=self.config['token'],
                                      url=feed['url'],
                                      userId=feed['id'])
            if 'delay' in feed:
                forwarder.delay = feed['delay']
            if 'format' in feed:
                forwarder.customFormat = feed['format'].replace('\\n', '\n')
            if 'preview' in feed:
                forwarder.telegramPreview = feed['preview']
            asyncio.ensure_future(forwarder.run())
        loop.run_forever()


class FeedForwarder(object):
    def __init__(self, token, url, userId,
                 delay=600,
                 customFormat='<b>$title$</b>\n$url$',
                 telegramPreview=True):
        self.bot = telepot.Bot(token)
        self.url = url
        self.userId = userId
        self.delay = delay
        self.format = customFormat
        self.telegramPreview = telegramPreview
        self.feed = feedparser.parse(url)
        self.title = self.feed['feed']['title']

    # Загрузка нового RSS и сравнение с загруженной ранее
    # Возвращает массив новых записей newEntries
    def getUpdates(self):
        newEntries = []
        updatedFeed = feedparser.parse(self.url)
        if len(updatedFeed['entries']) > 0:
            logging.debug('Get {} records from "{}", old feed contains {}'
                          .format(len(updatedFeed['entries']),
                                  self.url,
                                  len(self.feed['entries'])))
            for newEntry in updatedFeed['entries']:
                isNewEntry = True
                for oldEntry in self.feed['entries']:
                    if newEntry["id"] == oldEntry["id"]:
                        isNewEntry = False
                if isNewEntry is True:
                    newEntries.append(newEntry)
                # if entry not in self.feed['entries']:
                #     newEntries.append(entry)
            self.feed = updatedFeed
        else:
            logging.warning('Get empty feed from "{}"'.format(self.url))
        return newEntries

    def sendEntry(self, id, entry):
        tags = []
        if 'tags' in entry:
            for tag in entry['tags']:
                tags.append(tag['term'])

        templateDict = dict(author=html.escape(entry['author']),
                            description=html.escape(entry['summary']),
                            tags=html.escape(', '.join(tags)),
                            time=entry['published'],
                            title=html.escape(entry['title']),
                            url=entry['id'])

        outputText = Template(self.customFormat).safe_substitute(templateDict)
        logging.info('Send to "{}": "{}"'.format(id, outputText))
        disablePagePreview = not self.telegramPreview
        try:
            self.bot.sendMessage(id,
                                 outputText,
                                 parse_mode='HTML',
                                 disable_web_page_preview=disablePagePreview)
        except Exception as err:
            logging.warning(err)

    async def run(self):
        logging.info('Start listening "{}" on "{}"'.format(self.title,
                                                           self.url))
        self.sendEntry(self.userId, self.feed["entries"][0])
        while True:
            await asyncio.sleep(self.delay)
            rssNewEntries = self.getUpdates()
            if len(rssNewEntries) > 0:
                logging.info('Get {} new entries from "{}"'.
                             format(len(rssNewEntries), self.url))
            for entry in rssNewEntries:
                    self.sendEntry(self.userId, entry)
