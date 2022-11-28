from abc import ABC, abstractmethod
from time import mktime

from bs4 import BeautifulSoup
from feedparser import FeedParserDict, parse
from httpx import HTTPError, RequestError

from feedforbot.constants import APP_NAME
from feedforbot.core.article import ArticleModel
from feedforbot.core.utils import make_get_request
from feedforbot.exceptions import ListenerReceiveError


class ListenerBase(
    ABC,
):
    def __repr__(self) -> str:
        return f"<{APP_NAME}.{self.__class__.__name__}>"

    @abstractmethod
    async def receive(
        self,
    ) -> tuple[ArticleModel, ...]:
        raise NotImplementedError


class RSSListener(
    ListenerBase,
):
    def __init__(
        self,
        url: str,
    ) -> None:
        self.url = url

    def __repr__(self) -> str:
        return f"<{APP_NAME}.{self.__class__.__name__}: {self.url}>"

    def _parse_entry(  # noqa
        self,
        entry: FeedParserDict,
    ) -> ArticleModel:
        soup = BeautifulSoup(entry.summary, "html.parser")
        authors: tuple[str, ...] = ()
        if "authors" in entry and entry.authors != [{}]:
            authors = tuple(author.name for author in entry.authors)
        text = soup.text
        _id = entry.id if "id" in entry else entry.link
        published_at = (
            None if "published_parsed" not in entry else entry.published_parsed
        )
        if published_at is None and "updated_parsed" in entry:
            published_at = entry.updated_parsed
        return ArticleModel(
            id=_id,
            published_at=mktime(published_at) if published_at else None,
            title=entry.title,
            url=entry.link if "link" in entry else _id,
            text=text.strip(),
            images=tuple(img["src"] for img in soup.find_all("img")),
            authors=authors,
            categories=tuple(tag.term for tag in entry.tags)
            if "tags" in entry
            else (),
        )

    async def receive(
        self,
    ) -> tuple[ArticleModel, ...]:
        try:
            response = await make_get_request(self.url)
        except (HTTPError, RequestError) as exc:
            raise ListenerReceiveError from exc
        parsed = parse(response)
        return tuple(self._parse_entry(entry) for entry in parsed.entries)
