import sentry_sdk
from jinja2 import Template

from feedforbot.__version__ import APP_NAME
from feedforbot.article import ArticleModel
from feedforbot.exceptions import (
    HttpClientError,
    TransportSendError,
)
from feedforbot.http_client import HttpClient
from feedforbot.types import HttpClientProtocol, TransportProtocol


_DEFAULT_MESSAGE_TEMPLATE = Template("{{ TITLE }}\n\n{{ TEXT }}\n\n{{ URL }}")


class TelegramBotTransport(TransportProtocol):
    def __init__(
        self,
        token: str,
        to: str,
        template: Template = _DEFAULT_MESSAGE_TEMPLATE,
        disable_notification: bool = False,
        disable_web_page_preview: bool = False,
        http_client: HttpClientProtocol | None = None,
    ) -> None:
        if isinstance(template, str):
            template = Template(template)
        self._to = to
        self._api_url = f"https://api.telegram.org/bot{token}/sendMessage"
        self._message_template = template
        self._disable_web_page_preview = disable_web_page_preview
        self._disable_notification = disable_notification
        self._http = http_client or HttpClient(
            sensitive_values=(token,),
        )

    def __repr__(self) -> str:
        return f"<{APP_NAME}.{self.__class__.__name__}: {self._to}>"

    async def _send_article(
        self,
        article: ArticleModel,
    ) -> bool:
        try:
            response = await self._http.post(
                self._api_url,
                data={
                    "chat_id": self._to,
                    "text": self._message_template.render(
                        **article.model_dump(
                            by_alias=True,
                        ),
                    ),
                    "parse_mode": "HTML",
                    "disable_notification": (self._disable_notification),
                    "disable_web_page_preview": (
                        self._disable_web_page_preview
                    ),
                },
            )
        except HttpClientError as exc:
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
                    scope.set_tag("transport", self.__repr__())
                    scope.set_extra("article", article.model_dump())
                    sentry_sdk.capture_exception(exc)
                failed.append(article)
                continue
            if not is_success:
                failed.append(article)
        return failed
