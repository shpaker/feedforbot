from types import TracebackType
from typing import Any, Protocol

from feedforbot.article import ArticleModel


class HttpClientProtocol(
    Protocol,
):
    def get(
        self,
        url: str,
    ) -> bytes: ...

    def post(
        self,
        url: str,
        *,
        data: dict[str, Any],
    ) -> dict[str, Any]: ...

    def close(self) -> None: ...

    def __enter__(self) -> "HttpClientProtocol": ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...


class CacheProtocol(
    Protocol,
):
    @property
    def is_populated(self) -> bool: ...

    @property
    def known_ids(self) -> set[str]: ...

    def add(
        self,
        *articles: ArticleModel,
    ) -> None: ...

    def trim(
        self,
        limit: int,
    ) -> None: ...


class ListenerProtocol(
    Protocol,
):
    source_id: str

    def receive(
        self,
    ) -> tuple[ArticleModel, ...]: ...

    def close(self) -> None: ...

    def __enter__(self) -> "ListenerProtocol": ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...


class TransportProtocol(
    Protocol,
):
    def send(
        self,
        *articles: ArticleModel,
    ) -> list[ArticleModel]: ...

    def close(self) -> None: ...

    def __enter__(self) -> "TransportProtocol": ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...
