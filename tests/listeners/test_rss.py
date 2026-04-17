from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from freezegun import freeze_time
from pytest import raises

from feedforbot.article import ArticleModel
from feedforbot.exceptions import HttpClientError, ListenerReceiveError
from feedforbot.listeners import RSSListener


_TESTING_URL = "http://q"


class FakeHttpClient:
    def __init__(
        self,
        get_response: bytes = b"",
        *,
        raise_on_get: Exception | None = None,
    ) -> None:
        self._get_response = get_response
        self._raise_on_get = raise_on_get
        self.closed = False

    def get(self, url: str) -> bytes:  # noqa: ARG002
        if self._raise_on_get is not None:
            raise self._raise_on_get
        return self._get_response

    def post(
        self,
        url: str,
        *,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        raise NotImplementedError

    def close(self) -> None:
        self.closed = True

    def __enter__(self) -> "FakeHttpClient":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()


@freeze_time("2012-01-14 12:00:01+00:00")
def test_receive_feed(
    read_mock: Callable[[str], str],
) -> None:
    http = FakeHttpClient(
        get_response=read_mock("rss_short").encode(),
    )
    listener = RSSListener(url=_TESTING_URL, http_client=http)
    feed = listener.receive()
    assert (
        feed[0].model_dump()
        == ArticleModel(
            id="https://aaa.ccc",
            published_at=datetime(
                2022,
                11,
                23,
                19,
                22,
                24,
                tzinfo=timezone.utc,
            ),
            grabbed_at=datetime(
                2012,
                1,
                14,
                12,
                0,
                1,
                tzinfo=timezone.utc,
            ),
            title="FOO",
            url="https://aaa.ccc",  # type: ignore[arg-type]
            text="BAR",
            categories=("a", "b", "c"),
        ).model_dump()
    )


@freeze_time("2023-04-10 12:00:00+00:00")
def test_receive_multiple_entries(
    read_mock: Callable[[str], str],
) -> None:
    http = FakeHttpClient(
        get_response=read_mock("rss_full").encode(),
    )
    listener = RSSListener(url=_TESTING_URL, http_client=http)
    feed = listener.receive()
    expected_entries = 3
    assert len(feed) == expected_entries

    assert feed[0].title == "Article One"
    assert feed[0].id == "https://example.com/1"
    assert str(feed[0].url) == "https://example.com/1"
    assert feed[0].text == "Hello  world"
    assert tuple(str(i) for i in feed[0].images) == (
        "https://example.com/img1.png",
        "https://example.com/img2.png",
    )
    assert feed[0].categories == ("tech", "python")
    assert feed[0].published_at == datetime(
        2023,
        4,
        10,
        8,
        0,
        0,
        tzinfo=timezone.utc,
    )

    assert feed[1].title == "Article Two"
    assert feed[1].id == "https://example.com/2"
    assert feed[1].published_at == datetime(
        2023,
        4,
        11,
        10,
        30,
        0,
        tzinfo=timezone.utc,
    )

    assert feed[2].title == "Article Three"
    assert feed[2].id == "urn:uuid:article-3"
    assert feed[2].published_at is None


def test_receive_raises_on_http_error() -> None:
    http = FakeHttpClient(
        raise_on_get=HttpClientError("fail"),
    )
    listener = RSSListener(url=_TESTING_URL, http_client=http)
    with raises(ListenerReceiveError):
        listener.receive()


def test_repr() -> None:
    http = FakeHttpClient()
    listener = RSSListener(url=_TESTING_URL, http_client=http)
    assert _TESTING_URL in repr(listener)
    assert "RSSListener" in repr(listener)


_MIXED_FEED = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
<title>t</title><link>http://x</link><description>d</description>
<item>
  <title>Good</title>
  <link>https://example.com/good</link>
  <description>ok body</description>
  <guid>https://example.com/good</guid>
</item>
<item>
  <link>https://example.com/bad</link>
  <guid>https://example.com/bad</guid>
</item>
</channel></rss>
"""


def test_receive_skips_malformed_entries() -> None:
    http = FakeHttpClient(get_response=_MIXED_FEED)
    listener = RSSListener(url=_TESTING_URL, http_client=http)
    feed = listener.receive()
    assert len(feed) == 1
    assert feed[0].title == "Good"


def test_close_closes_http_client() -> None:
    http = FakeHttpClient()
    listener = RSSListener(url=_TESTING_URL, http_client=http)
    listener.close()
    assert http.closed is True


def test_context_manager_closes_http_client() -> None:
    http = FakeHttpClient()
    with RSSListener(url=_TESTING_URL, http_client=http):
        pass
    assert http.closed is True
