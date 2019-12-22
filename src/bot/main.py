import logging

from .bot import Bot
from .core import Settings


def main():

    settings = Settings()
    logging.basicConfig(format=settings.log_format,
                        level=settings.log_level)
    with Bot() as bot:
        bot.run()
