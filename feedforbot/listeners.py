from email.utils import parsedate_to_datetime
from typing import TYPE_CHECKING

from bs4 import BeautifulSoup
from feedparser import FeedParserDict, parse

from feedforbot.__version__ import __title__
from feedforbot.article import ArticleModel
from feedforbot.exceptions import (
    HttpClientError,
    ListenerReceiveError,
)
from feedforbot.http_client import HttpClient
from feedforbot.logger import logger
from feedforbot.types import HttpClientProtocol, ListenerProtocol


if TYPE_CHECKING:
    from datetime import datetime


class RSSListener(ListenerProtocol):
    def __init__(
        self,
        url: str,
        http_client: HttpClientProtocol | None = None,
    ) -> None:
        self.url = url
        self.source_id = url
        self._http = http_client or HttpClient()

    def __repr__(self) -> str:
        return f"<{__title__}.{self.__class__.__name__}: {self.url}>"

    def _parse_entry(
        self,
        entry: FeedParserDict,
    ) -> ArticleModel:
        soup = BeautifulSoup(entry.summary, "html.parser")
        _id = entry.get("id") or entry.get("link")
        published_at: datetime | None = None
        if published := entry.get("published"):
            published_at = parsedate_to_datetime(published)
        elif updated := entry.get("updated"):
            published_at = parsedate_to_datetime(updated)
        return ArticleModel(
            id=_id,
            published_at=published_at,
            title=entry.title,
            url=entry.get("link") or _id,
            text=soup.text.strip(),
            images=tuple(
                img["src"] for img in soup.find_all("img") if img.get("src")
            ),
            authors=tuple(
                a["name"] for a in entry.get("authors", ()) if "name" in a
            ),
            categories=tuple(
                tag["term"] for tag in entry.get("tags", ()) if "term" in tag
            ),
        )

    def receive(
        self,
    ) -> tuple[ArticleModel, ...]:
        try:
            response = self._http.get(self.url)
        except HttpClientError as exc:
            raise ListenerReceiveError from exc
        parsed = parse(response)
        articles = tuple(self._parse_entry(entry) for entry in parsed.entries)
        logger.info(
            "listener_receive: %s entries=%d",
            self,
            len(articles),
        )
        logger.debug(
            "listener_receive_ids: %s ids=%s",
            self,
            [a.id for a in articles],
        )
        return articles
