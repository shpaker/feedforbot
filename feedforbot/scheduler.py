import asyncio
import threading
import time

import structlog
from croniter import croniter
from epyxid import XID

from feedforbot.article import ArticleModel
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
        tick_id = str(XID())
        structlog.contextvars.bind_contextvars(tick_id=tick_id)
        try:
            self._tick_inner()
        finally:
            structlog.contextvars.unbind_contextvars("tick_id")

    def _tick_inner(
        self,
    ) -> None:
        logger.debug("scheduler_tick: %s", self.listener)
        try:
            articles = self.listener.receive()
        except ListenerReceiveError as exc:
            with new_scope() as scope:
                scope.set_tag("cron", self.cron_rule)
                scope.set_tag("listener", repr(self.listener))
                scope.set_tag("transport", repr(self.transport))
                capture_exception(exc)
            logger.warning(
                "listener_receive_error: %s",
                self.listener,
            )
            return
        if not self.cache.is_populated:
            logger.info(
                "scheduler_first_run: %s articles=%d",
                self.listener,
                len(articles),
            )
            self.cache.write(*articles)
            return
        cached_set = set(self.cache.read())
        to_send = tuple(
            article for article in articles if article not in cached_set
        )
        if not to_send:
            logger.debug(
                "scheduler_no_new_articles: %s",
                self.listener,
            )
            merged = self._merge_articles(cached_set, articles)
            self.cache.write(*merged)
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
        failed_set = set(failed)
        cacheable = tuple(
            article for article in articles if article not in failed_set
        )
        merged = self._merge_articles(cached_set, cacheable)
        self.cache.write(*merged)

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

    @staticmethod
    def _merge_articles(
        cached: set[ArticleModel],
        *groups: tuple[ArticleModel, ...],
    ) -> tuple[ArticleModel, ...]:
        seen: dict[str, ArticleModel] = {a.id: a for a in cached}
        for group in groups:
            for article in group:
                seen[article.id] = article
        return tuple(seen.values())
