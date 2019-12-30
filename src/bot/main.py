import logging
from dataclasses import asdict
from pprint import pformat
from typing import Optional

from .bot import Bot
from .core import Settings

DEFAULT_REDIS_PORT = 6379
DEFAULT_IS_DEBUG = False
DEFAULT_TG_PROXY = None


def main(tg_token: str,
         feeds_path: str,
         redis_host: str,
         redis_port: int = DEFAULT_REDIS_PORT,
         is_debug: bool = DEFAULT_IS_DEBUG,
         tg_proxy: Optional[str] = DEFAULT_TG_PROXY) -> None:

    settings = Settings(tg_token=tg_token,
                        is_debug=is_debug,
                        tg_proxy=tg_proxy,
                        redis_host=redis_host,
                        redis_port=redis_port,
                        feeds_path=feeds_path)

    log_level = logging.DEBUG if settings.is_debug else logging.INFO
    logging.basicConfig(format=settings.log_format,
                        level=log_level)

    settings_dict = asdict(settings)
    settings_dict.pop('tg_token')
    logging.info(f'Settings:\n{pformat(settings_dict)}')

    with Bot(settings=settings) as bot:
        bot.run()
