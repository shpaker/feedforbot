from abc import ABC, abstractmethod
import sentry_sdk
from httpx import HTTPError, RequestError
from jinja2 import Template

from feedforbot.constants import APP_NAME, DEFAULT_MESSAGE_TEMPLATE
from feedforbot.core.article import ArticleModel
from feedforbot.core.utils import make_post_request
from feedforbot.exceptions import TransportSendError


class TransportBase(
    ABC,
):
    def __repr__(self) -> str:
        return f"<{APP_NAME}.{self.__class__.__name__}>"

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
        disable_notification: bool = False,
        disable_web_page_preview: bool = False,
    ) -> None:
        if isinstance(template, str):
            template = Template(template)
        self._to = to
        self._api_url = f"https://api.telegram.org/bot{token}/sendMessage"
        self._message_template = template
        self._disable_web_page_preview = disable_web_page_preview
        self._disable_notification = disable_notification

    def __repr__(self) -> str:
        return f"<{APP_NAME}.{self.__class__.__name__}: {self._to}>"

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
                        **article.model_dump(
                            by_alias=True,
                        ),
                    ),
                    "parse_mode": "HTML",
                    "disable_notification": self._disable_notification,
                    "disable_web_page_preview": self._disable_web_page_preview,
                },
            )
        except (HTTPError, RequestError) as exc:
            raise TransportSendError from exc
        is_ok: bool = response["ok"]
        return is_ok

    async def send(
        self,
        *articles: ArticleModel,
    ) -> list[ArticleModel]:
        failed = []
        for article in articles:
            try:
                is_success = await self._send_article(article)
            except TransportSendError as exc:
                with sentry_sdk.new_scope() as scope:
                    scope.set_tag('transport', self.__repr__())
                    scope.set_extra('article', article.model_dump())
                    sentry_sdk.capture_exception(exc)
                failed.append(article)
                continue
            if not is_success:
                failed.append(article)
        return failed
