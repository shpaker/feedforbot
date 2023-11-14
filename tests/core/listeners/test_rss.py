from datetime import datetime, timezone
from typing import Callable
from unittest.mock import AsyncMock

from freezegun import freeze_time
from pytest import MonkeyPatch, mark
from respx import MockRouter

from feedforbot.core import listeners
from feedforbot.core.article import ArticleModel
from feedforbot.core.listeners import RSSListener


def _http_get_mock(
    monkeypatch: MonkeyPatch,
    return_value: str,
) -> None:
    monkeypatch.setattr(
        listeners,
        "make_get_request",
        AsyncMock(return_value=return_value),
    )


_TESTING_URL = "http://q"


@freeze_time("2012-01-14 12:00:01+00:00")
@mark.asyncio
async def test_receive_feed(
    read_mock: Callable[[str], str],
    respx_mock: MockRouter,
) -> None:
    respx_mock.get(_TESTING_URL).respond(text=read_mock("rss_short"))
    listener = RSSListener(url=_TESTING_URL)
    feed = await listener.receive()
    assert (
        feed[0].model_dump()
        == ArticleModel(
            id="https://aaa.ccc",
            published_at=datetime(
                2022, 11, 23, 16, 22, 24, tzinfo=timezone.utc
            ),
            grabbed_at=datetime(2012, 1, 14, 12, 0, 1, tzinfo=timezone.utc),
            title="FOO",
            url="https://aaa.ccc",
            text="BAR",
            categories=("a", "b", "c"),
        ).model_dump()
    )
