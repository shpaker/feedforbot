from typing import Protocol, Sequence

from feedforbot.core.article import ArticleModel


class CacheProtocol(
    Protocol,
):
    async def write(
        self,
        *articles: ArticleModel,
    ) -> None:
        ...

    async def read(
        self,
    ) -> Sequence[ArticleModel] | None:
        ...


class ListenerProtocol(
    Protocol,
):
    source_id: str

    async def receive(
        self,
    ) -> tuple[ArticleModel, ...]:
        ...


class TransportProtocol(
    Protocol,
):
    async def send(
        self,
        *articles: ArticleModel,
    ) -> list[ArticleModel]:
        ...
