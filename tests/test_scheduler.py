import asyncio
from collections.abc import Iterable
from typing import Any

from pytest import mark

from feedforbot.article import ArticleModel
from feedforbot.exceptions import ListenerReceiveError
from feedforbot.scheduler import Scheduler


def _article(**kwargs: Any) -> ArticleModel:
    defaults: dict[str, Any] = {
        "id": "1",
        "title": "Test",
        "url": "https://example.com/1",
        "text": "body",
    }
    defaults.update(kwargs)
    return ArticleModel(**defaults)


class FakeListener:
    source_id: str = "fake-source"

    def __init__(
        self,
        articles: tuple[ArticleModel, ...] = (),
        *,
        raise_on_receive: Exception | None = None,
    ) -> None:
        self._articles = articles
        self._raise_on_receive = raise_on_receive

    def receive(self) -> tuple[ArticleModel, ...]:
        if self._raise_on_receive is not None:
            raise self._raise_on_receive
        return self._articles


class FakeTransport:
    def __init__(
        self,
        failed: list[ArticleModel] | None = None,
    ) -> None:
        self._failed = failed or []
        self.sent: list[ArticleModel] = []

    def send(
        self,
        *articles: ArticleModel,
    ) -> list[ArticleModel]:
        self.sent.extend(articles)
        return self._failed


class FakeCache:
    def __init__(
        self,
        cached: Iterable[ArticleModel] | None = None,
    ) -> None:
        if cached is None:
            self._cached: tuple[ArticleModel, ...] = ()
            self._populated = False
        else:
            self._cached = tuple(cached)
            self._populated = True
        self.written: list[tuple[ArticleModel, ...]] = []

    @property
    def is_populated(self) -> bool:
        return self._populated

    def read(self) -> Iterable[ArticleModel]:
        return self._cached

    def write(self, *articles: ArticleModel) -> None:
        self._cached = articles
        self._populated = True
        self.written.append(articles)


def _make_scheduler(
    *,
    listener: FakeListener | None = None,
    transport: FakeTransport | None = None,
    cache: FakeCache | None = None,
) -> Scheduler:
    return Scheduler(
        "* * * * *",
        listener=listener or FakeListener(),
        transport=transport or FakeTransport(),
        cache=cache,
    )


def test_first_run_populates_cache_without_sending() -> None:
    a1 = _article(id="1")
    a2 = _article(id="2")
    transport = FakeTransport()
    cache = FakeCache(cached=None)

    scheduler = _make_scheduler(
        listener=FakeListener(articles=(a1, a2)),
        transport=transport,
        cache=cache,
    )
    scheduler._tick()  # noqa: SLF001

    assert transport.sent == []
    assert len(cache.written) == 1
    assert cache.written[0] == (a1, a2)


def test_sends_new_articles() -> None:
    old = _article(id="old")
    new = _article(id="new")
    transport = FakeTransport()
    cache = FakeCache(cached=[old])

    scheduler = _make_scheduler(
        listener=FakeListener(articles=(old, new)),
        transport=transport,
        cache=cache,
    )
    scheduler._tick()  # noqa: SLF001

    assert transport.sent == [new]
    assert cache.written[0] == (old, new)


def test_no_new_articles_updates_cache() -> None:
    a1 = _article(id="1")
    transport = FakeTransport()
    cache = FakeCache(cached=[a1])

    scheduler = _make_scheduler(
        listener=FakeListener(articles=(a1,)),
        transport=transport,
        cache=cache,
    )
    scheduler._tick()  # noqa: SLF001

    assert transport.sent == []
    assert len(cache.written) == 1
    assert cache.written[0] == (a1,)


def test_listener_error_is_handled() -> None:
    transport = FakeTransport()
    cache = FakeCache()

    scheduler = _make_scheduler(
        listener=FakeListener(
            raise_on_receive=ListenerReceiveError("boom"),
        ),
        transport=transport,
        cache=cache,
    )
    scheduler._tick()  # noqa: SLF001

    assert transport.sent == []
    assert cache.written == []


def test_partial_send_failure_excludes_failed_from_cache() -> None:
    old = _article(id="old")
    a1 = _article(id="a1")
    a2 = _article(id="a2")
    transport = FakeTransport(failed=[a2])
    cache = FakeCache(cached=[old])

    scheduler = _make_scheduler(
        listener=FakeListener(articles=(old, a1, a2)),
        transport=transport,
        cache=cache,
    )
    scheduler._tick()  # noqa: SLF001

    assert transport.sent == [a1, a2]
    written_ids = {a.id for a in cache.written[0]}
    assert "old" in written_ids
    assert "a1" in written_ids
    assert "a2" not in written_ids


def test_all_send_failed_keeps_old_in_cache() -> None:
    old = _article(id="old")
    new1 = _article(id="n1")
    new2 = _article(id="n2")
    transport = FakeTransport(failed=[new1, new2])
    cache = FakeCache(cached=[old])

    scheduler = _make_scheduler(
        listener=FakeListener(articles=(old, new1, new2)),
        transport=transport,
        cache=cache,
    )
    scheduler._tick()  # noqa: SLF001

    assert set(transport.sent) == {new1, new2}
    written_ids = {a.id for a in cache.written[0]}
    assert "old" in written_ids
    assert "n1" not in written_ids
    assert "n2" not in written_ids


def test_reappearing_article_not_resent() -> None:
    a1 = _article(id="1")
    a2 = _article(id="2")
    transport = FakeTransport()
    cache = FakeCache(cached=[a1, a2])

    scheduler = _make_scheduler(
        listener=FakeListener(articles=(a1,)),
        transport=transport,
        cache=cache,
    )
    scheduler._tick()  # noqa: SLF001
    assert transport.sent == []

    scheduler2 = Scheduler(
        "* * * * *",
        listener=FakeListener(articles=(a1, a2)),
        transport=transport,
        cache=cache,
    )
    scheduler2._tick()  # noqa: SLF001
    assert transport.sent == []


def test_default_cache_is_in_memory() -> None:
    scheduler = _make_scheduler()

    from feedforbot.cache import InMemoryCache  # noqa: PLC0415

    assert isinstance(scheduler.cache, InMemoryCache)


def test_stop_before_run() -> None:
    scheduler = _make_scheduler()
    scheduler.stop()
    assert scheduler._stop_event.is_set()  # noqa: SLF001


def test_run_stop_from_thread() -> None:
    cache = FakeCache(cached=None)
    tick_count = 0

    class StopAfterFirstTick(Scheduler):
        def _tick(self) -> None:
            nonlocal tick_count
            tick_count += 1
            super()._tick()
            self.stop()

    scheduler = StopAfterFirstTick(
        "* * * * *",
        listener=FakeListener(articles=(_article(),)),
        transport=FakeTransport(),
        cache=cache,
    )
    scheduler.run()
    assert tick_count == 1


@mark.asyncio
async def test_arun_stop() -> None:
    cache = FakeCache(cached=None)
    scheduler = _make_scheduler(
        listener=FakeListener(articles=(_article(),)),
        cache=cache,
    )

    async def stop_soon() -> None:
        await asyncio.sleep(0.05)
        scheduler.stop()

    stop_task = asyncio.create_task(stop_soon())
    task = asyncio.create_task(scheduler.arun())
    await asyncio.gather(task, stop_task)
