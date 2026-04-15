from collections.abc import Iterable
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


class CacheProtocol(
    Protocol,
):
    @property
    def is_populated(self) -> bool: ...

    def write(
        self,
        *articles: ArticleModel,
    ) -> None: ...

    def read(
        self,
    ) -> Iterable[ArticleModel]: ...


class ListenerProtocol(
    Protocol,
):
    source_id: str

    def receive(
        self,
    ) -> tuple[ArticleModel, ...]: ...


class TransportProtocol(
    Protocol,
):
    def send(
        self,
        *articles: ArticleModel,
    ) -> list[ArticleModel]: ...
