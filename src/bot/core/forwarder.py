import asyncio
import logging
from dataclasses import asdict
from string import Template

from requests import request

from .listener import Listener
from ..models import FeedEntry


class Forwarder:

    def __init__(self,
                 token: str,
                 listener: Listener):
        self.token = token
        self.listener = listener

    def send_telegram_message(self,
                              text: str):
        url = f'https://api.telegram.org/bot{self.token}/sendMessage'
        data = dict(chat_id=self.listener.id,
                    text=text,
                    parse_mode='HTML')
        # todo check invalid token
        try:
            response = request(method='POST',
                               url=url,
                               data=data,
                               proxies=dict(http='socks5://localhost:9050',
                                            https='socks5://localhost:9050'))
            return response
        except Exception as err:
            logging.warning(err)

    def send_entry(self,
                   entry: FeedEntry):

        template_dict = asdict(entry)
        output = Template(self.listener.format).safe_substitute(template_dict)
        logging.debug(f'Send to "{self.listener.id}": "{output}"')
        preview = not self.listener.preview

            # self.src.sendMessage(self.userId, output, parse_mode='HTML',
            #                      disable_web_page_preview=preview)
        response = self.send_telegram_message(output)

        if response and response.ok:
            entry.forwarded = True

        return entry.forwarded

    async def listen(self):
        while True:
            logging.debug(f'Check feed {self.listener.url} for user_id {self.listener.id}')

            try:
                await self.check()
            except Exception as err:
                logging.warning(err)
            finally:
                await asyncio.sleep(self.listener.delay)

    async def check(self):
        feed = self.listener.feed
        new_messages = 0
        forwarded_messages = 0

        if not feed.entries:
            logging.info(f'Got empty feed from "{self.listener.url}"')

        for entry in feed.entries:
            if not entry.forwarded:
                new_messages += 1
                result = self.send_entry(entry)
                if result:
                    forwarded_messages += 1

        if new_messages:
            msg = f'Received {new_messages} new messages from {self.listener.url}, and forwarded {forwarded_messages}'
            logging.info(msg)

        if feed.entries:
            self.listener.store(feed)
