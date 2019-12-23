import logging

from .bot import Bot
from .core import Settings


def main():
    settings = Settings()
    log_level = logging.INFO

    if settings.log_debug:
        log_level = logging.DEBUG

    logging.basicConfig(format=settings.log_format,
                        level=log_level)
    with Bot() as bot:
        bot.run()
