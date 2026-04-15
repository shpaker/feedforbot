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
            self._mask(request.content.decode("utf-8", "replace"))
            if request.content
            else None,
        )

        start = time.perf_counter()
        try:
            response = super().handle_request(
                request,
            )
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start) * 1000)
            logger.error(
                "http_error: %s %s host=%s duration_ms=%d error=%s",
                method,
                url,
                host,
                duration_ms,
                exc,
            )
            raise

        duration_ms = round((time.perf_counter() - start) * 1000)
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
    ) -> None:
        self._transport = _LoggingHTTPTransport(
            sensitive_values=sensitive_values,
        )

    def get(self, url: str) -> bytes:
        try:
            with httpx.Client(
                transport=self._transport,
            ) as client:
                response = client.get(url)
        except httpx.HTTPStatusError as exc:
            raise HttpResponseError from exc
        except httpx.HTTPError as exc:
            raise HttpTransportError from exc
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise HttpResponseError from exc
        return response.content

    def post(
        self,
        url: str,
        *,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        try:
            with httpx.Client(
                transport=self._transport,
            ) as client:
                response = client.post(url, json=data)
        except httpx.HTTPStatusError as exc:
            raise HttpResponseError from exc
        except httpx.HTTPError as exc:
            raise HttpTransportError from exc
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise HttpResponseError from exc
        return response.json()
