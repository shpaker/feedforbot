from datetime import datetime, timezone
from typing import Callable
from unittest.mock import AsyncMock

from freezegun import freeze_time
from pytest import MonkeyPatch, mark

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


@freeze_time("2012-01-14 12:00:01")
@mark.asyncio
async def test_receive_feed(
    read_mock: Callable[[str], str],
    monkeypatch: MonkeyPatch,
) -> None:
    mock_data = read_mock("rss_short")
    _http_get_mock(monkeypatch, mock_data)
    listener = RSSListener(url="http://q")
    feed = await listener.receive()  # pylint: disable=protected-access
    assert len(feed) == 2, feed
    assert feed[1].json(indent=2) == ArticleModel(
        id="https://aaa.ccc",
        published_at=datetime(2022, 11, 23, 16, 22, 24),
        grabbed_at=datetime(2012, 1, 14, 12, 0, 1, tzinfo=timezone.utc),
        title="FOO",
        url="https://aaa.ccc",
        text="BAR",
        categories=("a", "b", "c"),
    ).json(indent=2)
