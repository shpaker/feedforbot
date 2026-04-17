import logging
from http import HTTPStatus

import httpx
import pytest
from pytest import raises
from respx import MockRouter

from feedforbot.exceptions import (
    HttpResponseError,
    HttpTransportError,
)
from feedforbot.http_client import HttpClient


_BASE_URL = "http://example.com"


def _messages(
    caplog: pytest.LogCaptureFixture,
    prefix: str,
) -> list[str]:
    return [
        r.getMessage()
        for r in caplog.records
        if r.getMessage().startswith(prefix)
    ]


def _no_retry_client(
    **kwargs: object,
) -> HttpClient:
    return HttpClient(max_retries=1, **kwargs)  # type: ignore[arg-type]


def test_get_returns_bytes(
    respx_mock: MockRouter,
) -> None:
    respx_mock.get(f"{_BASE_URL}/feed").respond(
        content=b"<rss/>",
    )
    client = _no_retry_client()
    result = client.get(f"{_BASE_URL}/feed")
    assert result == b"<rss/>"


def test_get_raises_on_error_status(
    respx_mock: MockRouter,
) -> None:
    respx_mock.get(f"{_BASE_URL}/feed").respond(
        status_code=404,
    )
    client = _no_retry_client()
    with raises(HttpResponseError):
        client.get(f"{_BASE_URL}/feed")


def test_post_returns_json(
    respx_mock: MockRouter,
) -> None:
    respx_mock.post(f"{_BASE_URL}/api").respond(
        json={"ok": True, "result": 42},
    )
    client = _no_retry_client()
    result = client.post(
        f"{_BASE_URL}/api",
        data={"key": "value"},
    )
    assert result == {"ok": True, "result": 42}


def test_post_sends_json_body(
    respx_mock: MockRouter,
) -> None:
    route = respx_mock.post(f"{_BASE_URL}/api").respond(
        json={"ok": True},
    )
    client = _no_retry_client()
    client.post(
        f"{_BASE_URL}/api",
        data={"chat_id": "123", "text": "hello"},
    )
    request = route.calls[0].request
    assert request.headers["content-type"] == "application/json"


def test_post_raises_on_error_status(
    respx_mock: MockRouter,
) -> None:
    respx_mock.post(f"{_BASE_URL}/api").respond(
        status_code=500,
    )
    client = _no_retry_client()
    with raises(HttpResponseError):
        client.post(
            f"{_BASE_URL}/api",
            data={"key": "value"},
        )


def test_logs_request_and_response(
    respx_mock: MockRouter,
    caplog: pytest.LogCaptureFixture,
) -> None:
    respx_mock.get(f"{_BASE_URL}/data").respond(
        status_code=200,
        content=b"ok",
    )
    client = _no_retry_client()
    with caplog.at_level(logging.DEBUG, logger="feedforbot"):
        client.get(f"{_BASE_URL}/data")

    requests = _messages(caplog, "http_request:")
    assert len(requests) == 1
    assert "GET" in requests[0]
    assert f"{_BASE_URL}/data" in requests[0]

    responses = _messages(caplog, "http_response:")
    assert len(responses) == 1
    assert str(HTTPStatus.OK.value) in responses[0]

    details = _messages(caplog, "http_request_detail:")
    assert len(details) == 1
    assert "headers=" in details[0]


def test_logs_error_on_network_failure(
    respx_mock: MockRouter,
    caplog: pytest.LogCaptureFixture,
) -> None:
    respx_mock.get(f"{_BASE_URL}/fail").mock(
        side_effect=httpx.ConnectError("connection refused"),
    )
    client = _no_retry_client()
    with (
        caplog.at_level(logging.INFO, logger="feedforbot"),
        raises(HttpTransportError),
    ):
        client.get(f"{_BASE_URL}/fail")

    errors = _messages(caplog, "http_error:")
    assert len(errors) == 1
    assert "GET" in errors[0]
    assert "duration_ms=" in errors[0]


def test_masks_sensitive_values_in_logs(
    respx_mock: MockRouter,
    caplog: pytest.LogCaptureFixture,
) -> None:
    token = "secret-bot-token-123"
    url = f"{_BASE_URL}/bot{token}/sendMessage"
    respx_mock.post(url).respond(json={"ok": True})

    client = _no_retry_client(sensitive_values=(token,))
    with caplog.at_level(logging.DEBUG, logger="feedforbot"):
        client.post(url, data={"chat_id": "1"})

    for record in caplog.records:
        if record.name == "feedforbot":
            assert token not in record.getMessage()

    requests = _messages(caplog, "http_request:")
    assert "***" in requests[0]


def test_masks_sensitive_values_on_error(
    respx_mock: MockRouter,
    caplog: pytest.LogCaptureFixture,
) -> None:
    token = "secret-bot-token-456"
    url = f"{_BASE_URL}/bot{token}/sendMessage"
    respx_mock.post(url).mock(
        side_effect=httpx.ConnectError("refused"),
    )

    client = _no_retry_client(sensitive_values=(token,))
    with (
        caplog.at_level(logging.INFO, logger="feedforbot"),
        raises(HttpTransportError),
    ):
        client.post(url, data={"chat_id": "1"})

    for record in caplog.records:
        if record.name == "feedforbot":
            assert token not in record.getMessage()


def test_retry_on_server_error(
    respx_mock: MockRouter,
) -> None:
    route = respx_mock.get(f"{_BASE_URL}/flaky")
    route.side_effect = [
        httpx.Response(500),
        httpx.Response(200, content=b"ok"),
    ]
    client = HttpClient(
        max_retries=2,
        backoff_base=0.01,
    )
    result = client.get(f"{_BASE_URL}/flaky")
    assert result == b"ok"
    expected_calls = 2
    assert len(route.calls) == expected_calls


def test_no_retry_on_client_error(
    respx_mock: MockRouter,
) -> None:
    route = respx_mock.get(f"{_BASE_URL}/gone").respond(
        status_code=404,
    )
    client = HttpClient(
        max_retries=3,
        backoff_base=0.01,
    )
    with raises(HttpResponseError):
        client.get(f"{_BASE_URL}/gone")
    assert len(route.calls) == 1


def test_retry_exhausted_raises(
    respx_mock: MockRouter,
) -> None:
    respx_mock.get(f"{_BASE_URL}/down").respond(
        status_code=503,
    )
    client = HttpClient(
        max_retries=2,
        backoff_base=0.01,
    )
    with raises(HttpResponseError):
        client.get(f"{_BASE_URL}/down")


def test_post_raises_on_non_json_response(
    respx_mock: MockRouter,
) -> None:
    respx_mock.post(f"{_BASE_URL}/api").respond(
        status_code=200,
        content=b"<html>503 backend down</html>",
        headers={"content-type": "text/html"},
    )
    client = _no_retry_client()
    with raises(HttpResponseError):
        client.post(
            f"{_BASE_URL}/api",
            data={"key": "value"},
        )


def test_masks_token_in_exception_message(
    respx_mock: MockRouter,
    caplog: pytest.LogCaptureFixture,
) -> None:
    token = "secret-bot-token-789"
    url = f"{_BASE_URL}/bot{token}/sendMessage"
    respx_mock.post(url).mock(
        side_effect=httpx.ConnectError(
            f"failed to connect to {url}",
        ),
    )

    client = _no_retry_client(sensitive_values=(token,))
    with (
        caplog.at_level(logging.INFO, logger="feedforbot"),
        raises(HttpTransportError),
    ):
        client.post(url, data={"chat_id": "1"})

    errors = _messages(caplog, "http_error:")
    assert len(errors) == 1
    assert token not in errors[0]
    assert "***" in errors[0]


def test_retry_on_429_with_retry_after_header(
    respx_mock: MockRouter,
) -> None:
    route = respx_mock.post(f"{_BASE_URL}/api")
    route.side_effect = [
        httpx.Response(
            429,
            headers={"Retry-After": "0"},
            json={"ok": False},
        ),
        httpx.Response(200, json={"ok": True}),
    ]
    client = HttpClient(max_retries=3, backoff_base=0.01)
    result = client.post(f"{_BASE_URL}/api", data={})
    assert result == {"ok": True}
    expected_calls = 2
    assert len(route.calls) == expected_calls


def test_429_without_retry_after_gives_up(
    respx_mock: MockRouter,
) -> None:
    route = respx_mock.post(f"{_BASE_URL}/api").respond(
        status_code=429,
        json={"ok": False},
    )
    client = HttpClient(max_retries=3, backoff_base=0.01)
    with raises(HttpResponseError):
        client.post(f"{_BASE_URL}/api", data={})
    assert len(route.calls) == 1


def test_429_retry_after_above_cap_gives_up(
    respx_mock: MockRouter,
) -> None:
    route = respx_mock.post(f"{_BASE_URL}/api").respond(
        status_code=429,
        headers={"Retry-After": "300"},
        json={"ok": False},
    )
    client = HttpClient(
        max_retries=3,
        backoff_base=0.01,
        max_retry_after=60.0,
    )
    with raises(HttpResponseError):
        client.post(f"{_BASE_URL}/api", data={})
    assert len(route.calls) == 1


def test_429_exhausts_retries(
    respx_mock: MockRouter,
) -> None:
    route = respx_mock.post(f"{_BASE_URL}/api").respond(
        status_code=429,
        headers={"Retry-After": "0"},
        json={"ok": False},
    )
    client = HttpClient(
        max_retries=2,
        backoff_base=0.01,
        max_retry_after=60.0,
    )
    with raises(HttpResponseError):
        client.post(f"{_BASE_URL}/api", data={})
    expected_calls = 2
    assert len(route.calls) == expected_calls


def test_post_raises_on_non_object_json(
    respx_mock: MockRouter,
) -> None:
    respx_mock.post(f"{_BASE_URL}/api").respond(
        status_code=200,
        json=["not", "an", "object"],
    )
    client = _no_retry_client()
    with raises(HttpResponseError):
        client.post(
            f"{_BASE_URL}/api",
            data={"key": "value"},
        )
