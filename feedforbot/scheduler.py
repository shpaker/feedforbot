import asyncio
import threading
import time
from datetime import datetime, timezone

import structlog
from croniter import croniter
from epyxid import XID

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
        cache_limit: int | None = None,
    ) -> None:
        self.cron_rule = cron_rule
        self.listener = listener
        self.transport = transport
        self.cache = cache or InMemoryCache(id=listener.source_id)
        self.cache_limit = cache_limit
        self._stop_event = threading.Event()

    def _tick(
        self,
    ) -> None:
        tick_id = str(XID())
        structlog.contextvars.bind_contextvars(tick_id=tick_id)
        try:
            self._tick_inner()
        except Exception as exc:  # noqa: BLE001
            with new_scope() as scope:
                scope.set_tag("cron", self.cron_rule)
                scope.set_tag("listener", repr(self.listener))
                scope.set_tag("transport", repr(self.transport))
                capture_exception(exc)
            logger.exception(
                "scheduler_tick_error: %s",
                self.listener,
            )
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
            self.cache.add(*articles)
            self._maybe_trim()
            return
        known = self.cache.known_ids
        to_send = tuple(a for a in articles if a.id not in known)
        if not to_send:
            logger.debug(
                "scheduler_no_new_articles: %s",
                self.listener,
            )
            self.cache.add(*articles)
            self._maybe_trim()
            return
        _oldest = datetime.min.replace(tzinfo=timezone.utc)
        to_send = tuple(
            sorted(
                to_send,
                key=lambda a: a.published_at or _oldest,
            )
        )
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
        failed_id_set = {a.id for a in failed}
        cacheable = tuple(a for a in articles if a.id not in failed_id_set)
        self.cache.add(*cacheable)
        self._maybe_trim()

    def _maybe_trim(self) -> None:
        if self.cache_limit is not None:
            self.cache.trim(self.cache_limit)

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
        with self.listener, self.transport:
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
        with self.listener, self.transport:
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
