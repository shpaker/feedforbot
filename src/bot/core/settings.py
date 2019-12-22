import logging
from dataclasses import dataclass
from enum import Enum, auto
from os import environ

from environs import Env

DEFAULT_FORMAT = '<b>$title</b>\n$url'
DEFAULT_DELAY = 300
DEFAULT_PREVIEW = True

LOG_FORMAT = '%(asctime)s [%(levelname)-8s] %(message)s'


class EnvVariable(Enum):
    FEEDS_PATH = auto()
    TELEGRAM_TOKEN = auto()
    DEBUG_LOGS = auto()
    REDIS_HOST = auto()
    REDIS_PORT = auto()


@dataclass
class Settings:

    token: str = None
    debug: bool = False
    # todo proxy to None

    log_format: str = LOG_FORMAT
    log_level: int = logging.NOTSET

    https_proxy: str = None

    redis_host: str = '127.0.0.1'
    redis_port: int = 6379

    feeds_path: str = None

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            logging.info('CREATE SETTINGS INSTANCE')
            cls.instance = super(Settings, cls).__new__(cls)

        return cls.instance

    def __post_init__(self):
        env = Env()
        env.read_env()

        self.token = env.str[EnvVariable.TELEGRAM_TOKEN.name]
        self.redis_host = env(EnvVariable.REDIS_HOST.name, 'localhost')
        self.redis_port = env.int(EnvVariable.REDIS_PORT.name, 6379)

        debug_logs = env.bool(EnvVariable.DEBUG_LOGS.name, False)

        if debug_logs:
            self.log_level = logging.DEBUG

        self.feeds_path = environ[EnvVariable.FEEDS_PATH.name]
