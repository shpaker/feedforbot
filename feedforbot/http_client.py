import time
from collections.abc import Sequence
from typing import Any

import httpx

from feedforbot.exceptions import (
    HttpResponseError,
    HttpTransportError,
)
from feedforbot.logger import logger
from feedforbot.types import HttpClientProtocol


_DEFAULT_TIMEOUT = httpx.Timeout(30.0, connect=10.0)
_DEFAULT_MAX_RETRIES = 3
_DEFAULT_BACKOFF_BASE = 1.0
_DEFAULT_BACKOFF_FACTOR = 2.0
_SERVER_ERROR_THRESHOLD = 500


class _LoggingHTTPTransport(
    httpx.HTTPTransport,
):
    def __init__(
        self,
        sensitive_values: Sequence[str] = (),
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._sensitive_values = tuple(v for v in sensitive_values if v)

    def _mask(self, value: str) -> str:
        masked = value
        for secret in self._sensitive_values:
            masked = masked.replace(secret, "***")
        return masked

    def handle_request(
        self,
        request: httpx.Request,
    ) -> httpx.Response:
        method = request.method
        url = self._mask(str(request.url))
        host = request.url.host

        logger.info(
            "http_request: %s %s host=%s",
            method,
            url,
            host,
        )
        logger.debug(
            "http_request_detail: %s %s headers=%s body=%s",
            method,
            url,
            dict(request.headers),
            self._mask(
                request.content.decode("utf-8", "replace"),
            )
            if request.content
            else None,
        )

        start = time.perf_counter()
        try:
            response = super().handle_request(
                request,
            )
        except Exception as exc:
            duration_ms = round(
                (time.perf_counter() - start) * 1000,
            )
            logger.error(
                "http_error: %s %s host=%s duration_ms=%d error=%s",
                method,
                url,
                host,
                duration_ms,
                exc,
            )
            raise

        duration_ms = round(
            (time.perf_counter() - start) * 1000,
        )
        logger.info(
            "http_response: %s %s host=%s status=%s duration_ms=%d",
            method,
            url,
            host,
            response.status_code,
            duration_ms,
        )
        logger.debug(
            "http_response_detail: %s %s status=%s headers=%s",
            method,
            url,
            response.status_code,
            dict(response.headers),
        )
        return response


class HttpClient(HttpClientProtocol):
    def __init__(
        self,
        sensitive_values: Sequence[str] = (),
        timeout: httpx.Timeout = _DEFAULT_TIMEOUT,
        max_retries: int = _DEFAULT_MAX_RETRIES,
        backoff_base: float = _DEFAULT_BACKOFF_BASE,
        backoff_factor: float = _DEFAULT_BACKOFF_FACTOR,
    ) -> None:
        transport = _LoggingHTTPTransport(
            sensitive_values=sensitive_values,
            retries=1,
        )
        self._client = httpx.Client(
            transport=transport,
            timeout=timeout,
        )
        self._max_retries = max_retries
        self._backoff_base = backoff_base
        self._backoff_factor = backoff_factor

    def _request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        last_exc: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                response = self._client.request(
                    method,
                    url,
                    **kwargs,
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code < _SERVER_ERROR_THRESHOLD:
                    raise HttpResponseError from exc
                last_exc = exc
            except httpx.HTTPError as exc:
                last_exc = exc
            else:
                return response
            if attempt < self._max_retries - 1:
                delay = self._backoff_base * (self._backoff_factor**attempt)
                logger.info(
                    "http_retry: attempt=%d delay=%.1fs",
                    attempt + 1,
                    delay,
                )
                time.sleep(delay)
        if isinstance(last_exc, httpx.HTTPStatusError):
            raise HttpResponseError from last_exc
        raise HttpTransportError from last_exc

    def get(self, url: str) -> bytes:
        response = self._request("GET", url)
        return response.content

    def post(
        self,
        url: str,
        *,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        response = self._request("POST", url, json=data)
        return response.json()

    def close(self) -> None:
        self._client.close()
