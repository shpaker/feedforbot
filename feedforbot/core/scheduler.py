import asyncio

from aiocron import Cron
from httpx import HTTPError, RequestError

from feedforbot.core.types import (
    CacheProtocol,
    ListenerProtocol,
    TransportProtocol,
)
from feedforbot.logger import logger


class Scheduler:
    def __init__(
        self,
        cron_rule: str,
        *,
        listener: ListenerProtocol,
        transport: TransportProtocol,
        cache: CacheProtocol,
    ) -> None:
        self.cron_rule = cron_rule
        self.listener = listener
        self.transport = transport
        self.cache = cache

    async def action(
        self,
    ) -> None:
        try:
            articles = await self.listener.receive()
        except (HTTPError, RequestError):
            return
        if (cached := await self.cache.read()) is None:
            await self.cache.write(*articles)
            return
        to_send = tuple(
            article for article in articles if article not in cached
        )
        if to_send:
            ids = "\n    ".join([article.id for article in to_send])
            logger.info(
                f"To send"
                f"  count : {len(to_send)}\n"
                f"  from  : {self.listener.source_id}\n"
                f"  ids   :\n"
                f"    {ids}"
            )
        failed = await self.transport.send(*to_send)
        if failed:
            ids = "\n    ".join([article.id for article in to_send])
            logger.info(
                f"Failed"
                f"  count : {len(failed)}\n"
                f"  from  : {self.listener.source_id}\n"
                f"  ids   :\n"
                f"    {ids}"
            )
        to_cache = tuple(
            article for article in articles if article not in failed
        )
        await self.cache.write(*to_cache)

    def run(
        self,
    ) -> None:
        logger.info(
            (
                f"Scheduler\n"
                f"  rule      : {self.cron_rule}\n"
                f"  listen    : {self.listener.source_id}\n"
                f"  transport : "
                f'{self.transport.__class__.__name__.split("Transport")[0]}\n'
                f"  cache     : "
                f'{self.cache.__class__.__name__.split("Cache")[0]}'
            )
        )
        crontab = Cron(
            spec=self.cron_rule,
            func=self.action,
            loop=asyncio.get_event_loop(),
        )
        crontab.start()
