from abc import ABC, abstractmethod
from collections.abc import Iterable
from email.utils import parsedate_to_datetime
from typing import TYPE_CHECKING

from bs4 import BeautifulSoup
from feedparser import FeedParserDict, parse
from httpx import HTTPError, RequestError

from feedforbot.constants import APP_NAME
from feedforbot.core.article import ArticleModel
from feedforbot.core.utils import make_get_request
from feedforbot.exceptions import ListenerReceiveError

if TYPE_CHECKING:
    from datetime import datetime


class ListenerBase(
    ABC,
):
    def __repr__(self) -> str:
        return f"<{APP_NAME}.{self.__class__.__name__}>"

    @abstractmethod
    async def receive(
        self,
    ) -> Iterable[ArticleModel]:
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

    def _parse_entry(
        self,
        entry: FeedParserDict,
    ) -> ArticleModel:
        soup = BeautifulSoup(entry.summary, "html.parser")
        authors: tuple[str, ...] = ()
        if "authors" in entry and entry.authors != [{}]:
            authors = tuple(author.name for author in entry.authors)
        text = soup.text
        _id = entry.id if "id" in entry else entry.link
        published_at: datetime | None = None
        if "published" in entry:
            published_at = parsedate_to_datetime(entry.published)
        if published_at is None and "updated" in entry:
            published_at = parsedate_to_datetime(entry.updated)
        return ArticleModel(
            id=_id,
            published_at=published_at,
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
    ) -> Iterable[ArticleModel]:
        try:
            response = await make_get_request(self.url)
        except (HTTPError, RequestError) as exc:
            raise ListenerReceiveError from exc
        parsed = parse(response)
        return tuple(self._parse_entry(entry) for entry in parsed.entries)
