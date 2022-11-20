from abc import ABC, abstractmethod
from datetime import datetime
from time import mktime

from bs4 import BeautifulSoup
from feedparser import FeedParserDict, parse

from feedforbot.core.article import ArticleModel
from feedforbot.core.utils import make_get_request


class ListenerBase(
    ABC,
):
    def __init__(
        self,
        source_id: str,
    ) -> None:
        self.source_id = source_id

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
        source_id: str | None = None,
    ) -> None:
        if source_id is None:
            source_id = f"rss:{url}"
        super().__init__(source_id=source_id)
        self.url = url

    def _parse_entry(  # noqa
        self,
        entry: FeedParserDict,
    ) -> ArticleModel:
        soup = BeautifulSoup(entry.summary, "html.parser")
        authors = (
            tuple(author.name for author in entry.authors)
            if "authors" in entry
            else ()
        )
        text = soup.text
        _id = entry.id if "id" in entry else entry.link
        return ArticleModel(
            id=_id,
            published_at=datetime.fromtimestamp(
                mktime(entry.published_parsed),
            ),
            title=entry.title,
            url=entry.link if "link" in entry else _id,
            text=text.strip(),
            images=tuple(img["src"] for img in soup.find_all("img")),
            authors=authors,
        )

    async def receive(
        self,
    ) -> tuple[ArticleModel, ...]:
        response = await make_get_request(self.url)
        parsed = parse(response)
        return tuple(self._parse_entry(entry) for entry in parsed.entries)
