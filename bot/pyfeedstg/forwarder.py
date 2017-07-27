import asyncio
import html
import logging
from string import Template

import feedparser
import telepot


class Forwarder(object):
    def __init__(self, token, url, userId, delay=600, customFormat='<b>$title</b>\n$url',
                 telegramPreview=True, sendLatestEntry=False):
        self.bot = telepot.Bot(token)
        self.url = url
        self.userId = userId
        self.delay = delay
        self.format = customFormat
        self.telegramPreview = telegramPreview
        self.sendLatestEntry = sendLatestEntry
        self.feed = feedparser.parse(url)
        # self.title = self.feed['feed']['title']

    def getUpdates(self):
        """
        Загрузка нового RSS и сравнение с загруженным ранее
        Возвращает массив новых записей newEntries
        """
        newEntries = []
        updatedFeed = feedparser.parse(self.url)

        if len(updatedFeed['entries']) > 0:
            logging.debug('Get {} records from "{}", old feed contains {}'
                          .format(len(updatedFeed['entries']),
                                  self.url,
                                  len(self.feed['entries'])))

            for newEntry in updatedFeed['entries']:
                isNewEntry = True

                matcher = 'id' if 'id' in newEntry else 'link'

                for oldEntry in self.feed['entries']:
                    if newEntry[matcher] == oldEntry[matcher]:
                        isNewEntry = False

                if isNewEntry is True:
                    newEntries.append(newEntry)
                # if entry not in self.feed['entries']:
                #     newEntries.append(entry)
            self.feed = updatedFeed
        else:
            logging.warning('Get empty feed from "{}"'.format(self.url))
        return newEntries

    def sendEntry(self, entry):
        tags = []
        if 'tags' in entry:
            for tag in entry['tags']:
                tags.append(tag['term'])

        template = {}
        if 'summary' in entry:
            template['description'] = html.escape(entry['summary'])
        if 'published' in entry:
            template['time'] = html.escape(entry['published'])
        if 'title' in entry:
            template['title'] = html.escape(entry['title'])
        if 'id' in entry:
            template['url'] = html.escape(entry['id'])
        elif 'link' in entry:
            template['url'] = html.escape(entry['link'])
        if 'author' in entry:
            template['author'] = html.escape(entry['author'])
        if 'tags' in entry:
            template['tags'] = html.escape(', '.join(tags))

        output = Template(self.format).safe_substitute(template)
        logging.info('Send to "{}": "{}"'.format(self.userId, output))
        preview = not self.telegramPreview

        try:
            self.bot.sendMessage(self.userId, output, parse_mode='HTML',
                                 disable_web_page_preview=preview)
        except Exception as err:
            logging.warning(err)

    async def run(self):
        logging.info('Start listening "{}"'.format(self.url))

        if self.sendLatestEntry:
            try:
                self.sendEntry(self.feed['entries'][0])
            except Exception as err:
                logging.warning(err)

        while True:
            await asyncio.sleep(self.delay)
            newEntries = self.getUpdates()

            if len(newEntries) > 0:
                logging.info('Get {} entries from "{}"'
                             .format(len(newEntries), self.url))

            for entry in newEntries:
                try:
                    self.sendEntry(entry)
                except Exception as err:
                    logging.warning(err)
