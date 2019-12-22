import asyncio
import logging
from dataclasses import asdict
from string import Template

from requests import request

from ..models import FeedEntry
from .listener import Listener


class Forwarder:

    def __init__(self,
                 token: str,
                 listener: Listener):

        self.token = token
        self.listener = listener

    def forward_to_telegram(self, text):
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
        logging.info(f'Send to "{self.listener.id}": "{output}"')
        preview = not self.listener.preview

            # self.src.sendMessage(self.userId, output, parse_mode='HTML',
            #                      disable_web_page_preview=preview)
        response = self.forward_to_telegram(output)

        if response.ok:
            entry.forwarded = True

    async def run(self):
        logging.info(f'Start forwarding "{self.listener.url}" to "{self.listener.id}"')

        while True:
            try:
                feed = self.listener.feed

                if not feed.entries:
                    logging.info(f'Got empty feed from "{self.listener.url}"')

                for entry in feed.entries:
                        if not entry.forwarded:
                            self.send_entry(entry)

                self.listener.store_feed(feed)
            except Exception as err:
                logging.warning(err)
            finally:
                await asyncio.sleep(self.listener.delay)
