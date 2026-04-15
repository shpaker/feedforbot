from typing import Any

from feedforbot.article import ArticleModel
from feedforbot.exceptions import HttpClientError
from feedforbot.transports import TelegramBotTransport


_TOKEN = "fake-token"
_CHAT_ID = "12345"


def _article(**kwargs: Any) -> ArticleModel:
    defaults: dict[str, Any] = {
        "id": "1",
        "title": "Test Title",
        "url": "https://example.com/1",
        "text": "Test body",
    }
    defaults.update(kwargs)
    return ArticleModel(**defaults)


class FakeHttpClient:
    def __init__(
        self,
        post_response: dict[str, Any] | None = None,
        *,
        raise_on_post: Exception | None = None,
    ) -> None:
        self._post_response = post_response or {"ok": True}
        self._raise_on_post = raise_on_post
        self.post_calls: list[dict[str, Any]] = []

    def get(self, url: str) -> bytes:
        raise NotImplementedError

    def post(
        self,
        url: str,
        *,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        self.post_calls.append({"url": url, "data": data})
        if self._raise_on_post is not None:
            raise self._raise_on_post
        return self._post_response


def test_send_single_article() -> None:
    http = FakeHttpClient()
    transport = TelegramBotTransport(
        token=_TOKEN,
        to=_CHAT_ID,
        http_client=http,
    )
    article = _article()
    failed = transport.send(article)
    assert failed == []
    assert len(http.post_calls) == 1
    call = http.post_calls[0]
    assert call["data"]["chat_id"] == _CHAT_ID
    assert call["data"]["parse_mode"] == "HTML"
    assert "Test Title" in call["data"]["text"]
    assert "https://example.com/1" in call["data"]["text"]


def test_send_multiple_articles() -> None:
    http = FakeHttpClient()
    transport = TelegramBotTransport(
        token=_TOKEN,
        to=_CHAT_ID,
        http_client=http,
    )
    a1 = _article(id="1", title="First")
    a2 = _article(id="2", title="Second")
    a3 = _article(id="3", title="Third")
    failed = transport.send(a1, a2, a3)
    assert failed == []
    expected_calls = 3
    assert len(http.post_calls) == expected_calls


def test_send_custom_template() -> None:
    http = FakeHttpClient()
    transport = TelegramBotTransport(
        token=_TOKEN,
        to=_CHAT_ID,
        template="Link: {{ URL }}",
        http_client=http,
    )
    failed = transport.send(_article())
    assert failed == []
    assert http.post_calls[0]["data"]["text"] == (
        "Link: https://example.com/1"
    )


def test_send_string_template() -> None:
    http = FakeHttpClient()
    transport = TelegramBotTransport(
        token=_TOKEN,
        to=_CHAT_ID,
        template="<b>{{ TITLE }}</b>",
        http_client=http,
    )
    failed = transport.send(_article())
    assert failed == []
    assert http.post_calls[0]["data"]["text"] == ("<b>Test Title</b>")


def test_send_disable_notification() -> None:
    http = FakeHttpClient()
    transport = TelegramBotTransport(
        token=_TOKEN,
        to=_CHAT_ID,
        disable_notification=True,
        http_client=http,
    )
    transport.send(_article())
    assert http.post_calls[0]["data"]["disable_notification"] is True


def test_send_disable_web_page_preview() -> None:
    http = FakeHttpClient()
    transport = TelegramBotTransport(
        token=_TOKEN,
        to=_CHAT_ID,
        disable_web_page_preview=True,
        http_client=http,
    )
    transport.send(_article())
    assert http.post_calls[0]["data"]["disable_web_page_preview"] is True


def test_send_api_returns_not_ok() -> None:
    http = FakeHttpClient(post_response={"ok": False})
    transport = TelegramBotTransport(
        token=_TOKEN,
        to=_CHAT_ID,
        http_client=http,
    )
    article = _article()
    failed = transport.send(article)
    assert failed == [article]


def test_send_http_error_returns_failed() -> None:
    http = FakeHttpClient(
        raise_on_post=HttpClientError("network error"),
    )
    transport = TelegramBotTransport(
        token=_TOKEN,
        to=_CHAT_ID,
        http_client=http,
    )
    article = _article()
    failed = transport.send(article)
    assert failed == [article]


def test_send_partial_failure() -> None:
    call_count = 0

    fail_on_call = 2

    class FailOnSecondHttpClient:
        def get(self, url: str) -> bytes:
            raise NotImplementedError

        def post(
            self,
            url: str,  # noqa: ARG002
            *,
            data: dict[str, Any],  # noqa: ARG002
        ) -> dict[str, Any]:
            nonlocal call_count
            call_count += 1
            if call_count == fail_on_call:
                raise HttpClientError("fail")
            return {"ok": True}

    transport = TelegramBotTransport(
        token=_TOKEN,
        to=_CHAT_ID,
        http_client=FailOnSecondHttpClient(),
    )
    a1 = _article(id="1")
    a2 = _article(id="2")
    a3 = _article(id="3")
    failed = transport.send(a1, a2, a3)
    assert len(failed) == 1
    assert failed[0] == a2


def test_repr() -> None:
    http = FakeHttpClient()
    transport = TelegramBotTransport(
        token=_TOKEN,
        to=_CHAT_ID,
        http_client=http,
    )
    assert _CHAT_ID in repr(transport)
    assert "TelegramBotTransport" in repr(transport)
