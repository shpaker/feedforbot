from collections.abc import Iterable
from typing import Any, Protocol

from feedforbot.article import ArticleModel


class HttpClientProtocol(
    Protocol,
):
    async def get(
        self,
        url: str,
    ) -> bytes: ...

    async def post(
        self,
        url: str,
        *,
        data: dict[str, Any],
    ) -> dict[str, Any]: ...


class CacheProtocol(
    Protocol,
):
    async def write(
        self,
        *articles: ArticleModel,
    ) -> None: ...

    async def read(
        self,
    ) -> Iterable[ArticleModel] | None: ...


class ListenerProtocol(
    Protocol,
):
    source_id: str

    async def receive(
        self,
    ) -> tuple[ArticleModel, ...]: ...


class TransportProtocol(
    Protocol,
):
    async def send(
        self,
        *articles: ArticleModel,
    ) -> list[ArticleModel]: ...
