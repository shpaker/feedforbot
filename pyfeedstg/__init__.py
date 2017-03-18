import asyncio
import html
import logging
from string import Template

import yaml

from .forwarder import Forwarder


class Server(object):
    def __init__(self, filename='config.yml', sendLastEntry=False):
        self.filename = filename
        self.sendLastEntry = sendLastEntry
        try:
            with open(filename, 'r', encoding='utf-8') as stream:
                self.config = yaml.load(stream)
        except Exception:
            raise

    def run(self):
        loop = asyncio.get_event_loop()
        for feed in self.config['feeds']:
            forwarder = Forwarder(token=self.config['token'],
                                  url=feed['url'],
                                  userId=feed['id'],
                                  sendLastEntry=self.sendLastEntry)
            if 'delay' in feed:
                forwarder.delay = feed['delay']
            if 'format' in feed:
                forwarder.customFormat = feed['format'].replace('\\n', '\n')
            if 'preview' in feed:
                forwarder.telegramPreview = feed['preview']
            asyncio.ensure_future(forwarder.run())
        loop.run_forever()
