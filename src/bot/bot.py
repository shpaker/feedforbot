import asyncio
from json import load as json_load
from typing import List

from redis import ConnectionPool, Redis
from yaml import load as yaml_load

from .core import Settings, Listener, Forwarder
from .schemas import ListenerSchema


class Bot(object):

    def __init__(self):
        self.settings = Settings()
        self.redis_pool = ConnectionPool(host=self.settings.redis_host,
                                         port=self.settings.redis_port)
        self.listeners: List[Listener] = self.read_listeners(self.settings.feeds_path)

    def __enter__(self):
        self.loop = asyncio.get_event_loop()
        return self
        # self.loop.set_exception_handler(self.loop_exception_handler)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.loop.close()
        if exc_val:
            raise

    def read_listeners(self, path: str):
        listeners = list()

        with open(path, 'r') as _f:
            feeds_raw = _f.read()

        listener_schema = ListenerSchema()
        raw_listeners = json_load(feeds_raw) if feeds_raw.endswith('.json') else yaml_load(feeds_raw)

        for raw_listener in raw_listeners:
            raw_listener = listener_schema.dump(raw_listener)

            listener = Listener(url=raw_listener['url'],
                                id=raw_listener['id'],
                                delay=raw_listener['delay'],
                                preview=raw_listener['preview'],
                                format=raw_listener['format'],
                                redis_client=Redis(connection_pool=self.redis_pool))

            listeners.append(listener)

            return listeners

    def run(self):
        for listener in self.listeners:
            forwarder = Forwarder(token=self.settings.token,
                                  listener=listener)
            asyncio.ensure_future(forwarder.run())

        self.loop.run_forever()
