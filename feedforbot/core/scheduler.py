import asyncio

from aiocron import Cron
import sentry_sdk

from feedforbot.core.cache import InMemoryCache
from feedforbot.core.types import (
    CacheProtocol,
    ListenerProtocol,
    TransportProtocol,
)
from feedforbot.exceptions import ListenerReceiveError
from feedforbot.logger import logger


class Scheduler:
    def __init__(
        self,
        cron_rule: str,
        *,
        listener: ListenerProtocol,
        transport: TransportProtocol,
        cache: CacheProtocol | None = None,
    ) -> None:
        self.cron_rule = cron_rule
        self.listener = listener
        self.transport = transport
        self.cache = cache or InMemoryCache(id=listener.source_id)

    async def action(
        self,
    ) -> None:
        try:
            articles = await self.listener.receive()
        except ListenerReceiveError as exc:
            with sentry_sdk.new_scope() as scope:
                scope.set_tag('cron', self.cron_rule)
                scope.set_tag('listener', self.listener.__repr__())
                scope.set_tag('transport', self.transport.__repr__())
                sentry_sdk.capture_exception(exc)
            logger.warning(f"ListenerReceiveError {self.listener}")
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
                f"SEND\n"
                f"  from : {self.listener}\n"
                f"  ids  :\n"
                f"    {ids}",
            )
        failed = await self.transport.send(*to_send)
        if failed:
            ids = "\n    ".join([article.id for article in to_send])
            logger.warning(
                f"FAILED\n"
                f"  from : {self.listener}\n"
                f"  ids  :\n"
                f"    {ids}",
            )
        to_cache = tuple(
            article for article in articles if article not in failed
        )
        await self.cache.write(*to_cache)

    def run(
        self,
    ) -> None:
        logger.info(
            f"SCHEDULER\n"
            f"  rule      : {self.cron_rule}\n"
            f"  listen    : {self.listener}\n"
            f"  transport : {self.transport}\n"
            f"  cache     : {self.cache}",
        )
        crontab = Cron(
            spec=self.cron_rule,
            func=self.action,
            loop=asyncio.get_event_loop(),
        )
        crontab.start()
