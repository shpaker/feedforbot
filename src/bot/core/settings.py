from dataclasses import dataclass
from typing import Optional


LOG_FORMAT = '%(asctime)s [%(levelname)-8s] %(message)s'

@dataclass
class Settings:
    tg_token: str
    is_debug: bool
    tg_proxy: Optional[str]
    redis_host: str
    redis_port: int
    feeds_path: str
    log_format: str = LOG_FORMAT
