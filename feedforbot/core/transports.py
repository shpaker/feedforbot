from abc import ABC, abstractmethod

from httpx import HTTPError, RequestError
from jinja2 import Template

from feedforbot.constants import DEFAULT_MESSAGE_TEMPLATE
from feedforbot.core.article import ArticleModel
from feedforbot.core.utils import make_post_request


class TransportBase(
    ABC,
):
    @abstractmethod
    async def send(
        self,
        *articles: ArticleModel,
    ) -> list[ArticleModel]:
        raise NotImplementedError


class TelegramBotTransport(
    TransportBase,
):
    def __init__(
        self,
        token: str,
        to: str,
        template: Template = DEFAULT_MESSAGE_TEMPLATE,
    ) -> None:
        if isinstance(template, str):
            template = Template(template)
        self._to = to
        self._api_url = f"https://api.telegram.org/bot{token}/sendMessage"
        self._message_template = template

    async def _send_article(
        self,
        article: ArticleModel,
    ) -> bool:
        try:
            response = await make_post_request(
                self._api_url,
                data={
                    "chat_id": self._to,
                    "text": self._message_template.render(
                        **article.dict(by_alias=True),
                    ),
                    "parse_mode": "HTML",
                },
            )
        except (HTTPError, RequestError):
            return False
        is_ok: bool = response["ok"]
        return is_ok

    async def send(
        self,
        *articles: ArticleModel,
    ) -> list[ArticleModel]:
        failed = []
        for article in articles:
            is_success = await self._send_article(article)
            if not is_success:
                failed.append(article)
        return failed
