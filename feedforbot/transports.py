from types import TracebackType

from jinja2 import select_autoescape
from jinja2.sandbox import SandboxedEnvironment

from feedforbot.__version__ import __title__
from feedforbot.article import ArticleModel
from feedforbot.exceptions import (
    HttpClientError,
    TransportSendError,
)
from feedforbot.http_client import HttpClient
from feedforbot.logger import logger
from feedforbot.sentry import capture_exception, new_scope
from feedforbot.types import HttpClientProtocol, TransportProtocol


_SANDBOX = SandboxedEnvironment(
    autoescape=select_autoescape(
        default=True,
        default_for_string=True,
    ),
)
_DEFAULT_TEMPLATE_STR = "{{ TITLE }}\n\n{{ TEXT }}\n\n{{ URL }}"
_DEFAULT_MESSAGE_TEMPLATE = _SANDBOX.from_string(
    _DEFAULT_TEMPLATE_STR,
)


class TelegramBotTransport(TransportProtocol):
    def __init__(
        self,
        token: str,
        to: str,
        template: str | None = None,
        disable_notification: bool = False,
        disable_web_page_preview: bool = False,
        http_client: HttpClientProtocol | None = None,
    ) -> None:
        self._to = to
        self._api_url = f"https://api.telegram.org/bot{token}/sendMessage"
        self._message_template = (
            _SANDBOX.from_string(template)
            if template is not None
            else _DEFAULT_MESSAGE_TEMPLATE
        )
        self._disable_web_page_preview = disable_web_page_preview
        self._disable_notification = disable_notification
        self._http = http_client or HttpClient(
            sensitive_values=(token,),
        )

    def __repr__(self) -> str:
        return f"<{__title__}.{self.__class__.__name__}: {self._to}>"

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "TelegramBotTransport":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    def _send_article(
        self,
        article: ArticleModel,
    ) -> None:
        logger.debug(
            "transport_send_article: chat_id=%s article_id=%s",
            self._to,
            article.id,
        )
        try:
            response = self._http.post(
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
        if not response.get("ok", False):
            raise TransportSendError

    def send(
        self,
        *articles: ArticleModel,
    ) -> list[ArticleModel]:
        failed = []
        for article in articles:
            try:
                self._send_article(article)
            except TransportSendError as exc:
                logger.warning(
                    "transport_send_error: chat_id=%s article_id=%s",
                    self._to,
                    article.id,
                )
                with new_scope() as scope:
                    scope.set_tag(
                        "transport",
                        repr(self),
                    )
                    scope.set_extra(
                        "article_id",
                        article.id,
                    )
                    capture_exception(exc)
                failed.append(article)
        logger.info(
            "transport_send: chat_id=%s total=%d failed=%d",
            self._to,
            len(articles),
            len(failed),
        )
        return failed
