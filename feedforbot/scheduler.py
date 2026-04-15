import asyncio
import threading
import time

from croniter import croniter

from feedforbot.cache import InMemoryCache
from feedforbot.exceptions import ListenerReceiveError
from feedforbot.logger import logger
from feedforbot.sentry import capture_exception, new_scope
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
        self._stop_event = threading.Event()

    def _tick(
        self,
    ) -> None:
        try:
            articles = self.listener.receive()
        except ListenerReceiveError as exc:
            with new_scope() as scope:
                scope.set_tag("cron", self.cron_rule)
                scope.set_tag("listener", self.listener.__repr__())
                scope.set_tag("transport", self.transport.__repr__())
                capture_exception(exc)
            logger.warning(
                "listener_receive_error: %s",
                self.listener,
            )
            return
        if (cached := self.cache.read()) is None:
            self.cache.write(*articles)
            return
        to_send = tuple(
            article for article in articles if article not in cached
        )
        if not to_send:
            self.cache.write(*articles)
            return
        ids = [article.id for article in to_send]
        logger.info(
            "send_articles: %s ids=%s",
            self.listener,
            ids,
        )
        failed = self.transport.send(*to_send)
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
        self.cache.write(*to_cache)

    def stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        logger.info(
            "scheduler_start: rule=%s listener=%s transport=%s cache=%s",
            self.cron_rule,
            self.listener,
            self.transport,
            self.cache,
        )
        self._stop_event.clear()
        cron = croniter(self.cron_rule)
        while not self._stop_event.is_set():
            delay = cron.get_next(float) - time.time()
            if delay > 0 and self._stop_event.wait(
                timeout=delay,
            ):
                break
            self._tick()

    async def arun(self) -> None:
        logger.info(
            "scheduler_start: rule=%s listener=%s transport=%s cache=%s",
            self.cron_rule,
            self.listener,
            self.transport,
            self.cache,
        )
        self._stop_event.clear()
        cron = croniter(self.cron_rule)
        while not self._stop_event.is_set():
            delay = cron.get_next(float) - time.time()
            if delay > 0:
                try:
                    await asyncio.sleep(delay)
                except asyncio.CancelledError:
                    return
            if self._stop_event.is_set():
                break
            await asyncio.to_thread(self._tick)
