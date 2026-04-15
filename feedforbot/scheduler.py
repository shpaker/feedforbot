import sentry_sdk
from aiocron import Cron

from feedforbot.cache import InMemoryCache
from feedforbot.exceptions import ListenerReceiveError
from feedforbot.logger import logger
from feedforbot.types import (
    CacheProtocol,
    ListenerProtocol,
    TransportProtocol,
)


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
        self._crontab: Cron | None = None

    async def action(
        self,
    ) -> None:
        try:
            articles = await self.listener.receive()
        except ListenerReceiveError as exc:
            with sentry_sdk.new_scope() as scope:
                scope.set_tag("cron", self.cron_rule)
                scope.set_tag("listener", self.listener.__repr__())
                scope.set_tag("transport", self.transport.__repr__())
                sentry_sdk.capture_exception(exc)
            logger.warning(
                "listener_receive_error: %s",
                self.listener,
            )
            return
        if (cached := await self.cache.read()) is None:
            await self.cache.write(*articles)
            return
        to_send = tuple(
            article for article in articles if article not in cached
        )
        if not to_send:
            await self.cache.write(*articles)
            return
        ids = [article.id for article in to_send]
        logger.info(
            "send_articles: %s ids=%s",
            self.listener,
            ids,
        )
        failed = await self.transport.send(*to_send)
        if failed:
            failed_ids = [article.id for article in failed]
            logger.warning(
                "send_articles_failed: %s ids=%s",
                self.listener,
                failed_ids,
            )
        to_cache = tuple(
            article for article in articles if article not in failed
        )
        await self.cache.write(*to_cache)

    def stop(
        self,
    ) -> None:
        if self._crontab is not None:
            self._crontab.stop()
            self._crontab = None

    def run(
        self,
    ) -> None:
        logger.info(
            "scheduler_start: rule=%s listener=%s transport=%s cache=%s",
            self.cron_rule,
            self.listener,
            self.transport,
            self.cache,
        )
        self._crontab = Cron(
            spec=self.cron_rule,
            func=self.action,
        )
        self._crontab.start()
