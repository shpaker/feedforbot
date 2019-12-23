from dataclasses import dataclass
from enum import Enum, auto

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
    log_debug: bool = False

    https_proxy: str = None

    redis_host: str = '127.0.0.1'
    redis_port: int = 6379

    feeds_path: str = None

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Settings, cls).__new__(cls)

        return cls.instance

    def __post_init__(self):
        env = Env()
        env.read_env()

        self.token = env.str(EnvVariable.TELEGRAM_TOKEN.name)
        self.feeds_path = env.str(EnvVariable.FEEDS_PATH.name)
        self.redis_host = env(EnvVariable.REDIS_HOST.name, 'localhost')
        self.redis_port = env.int(EnvVariable.REDIS_PORT.name, 6379)
        self.log_debug = env.bool(EnvVariable.DEBUG_LOGS.name, False)
