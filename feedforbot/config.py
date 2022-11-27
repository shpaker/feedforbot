from enum import Enum
from pathlib import Path
from typing import Any, Type

from pydantic import BaseModel
from yaml import safe_load

from feedforbot import (
    CacheProtocol,
    FilesCache,
    InMemoryCache,
    ListenerProtocol,
    RSSListener,
    Scheduler,
    TelegramBotTransport,
    TransportProtocol,
)


class _CacheTypes(str, Enum):
    IN_MEMORY = "in_memory"
    FILES = "files"


class _CacheConfigMapping(Enum):
    IN_MEMORY = InMemoryCache
    FILES = FilesCache


class _ListenerTypes(str, Enum):
    RSS = "rss"


class _ListenerConfigMapping(Enum):
    RSS = RSSListener


class _TransportTypes(str, Enum):
    TELEGRAM_BOT = "telegram_bot"


class _TransportConfigMapping(Enum):
    TELEGRAM_BOT = TelegramBotTransport


class _ConfigEntryModel(BaseModel):
    params: dict[str, Any] = {}


class _ListenerConfigModel(_ConfigEntryModel):
    type: _ListenerTypes


class _TransportConfigModel(_ConfigEntryModel):
    type: _TransportTypes


class _CacheConfigModel(_ConfigEntryModel):
    type: _CacheTypes


class _SchedulerConfigModel(BaseModel):
    rule: str = "* * * * *"
    listener: _ListenerConfigModel
    transport: _TransportConfigModel


class _ConfigModel(BaseModel):
    cache: _CacheConfigModel
    schedulers: tuple[_SchedulerConfigModel, ...]


def _cache_from_config(
    config: _ConfigModel,
) -> Type[CacheProtocol]:
    name = config.cache.type.name
    return _CacheConfigMapping[name].value  # type: ignore


def _listener_from_config(
    scheduler_config: _SchedulerConfigModel,
) -> Type[ListenerProtocol]:
    name = scheduler_config.listener.type.name
    return _ListenerConfigMapping[name].value  # type: ignore


def _transport_from_config(
    scheduler_config: _SchedulerConfigModel,
) -> Type[TransportProtocol]:
    name = scheduler_config.transport.type.name
    return _TransportConfigMapping[name].value  # type: ignore


def _make_scheduler_from_config(
    config: _SchedulerConfigModel,
    *,
    cache_cls: Any,
) -> Scheduler:
    transport_cls = _transport_from_config(config)
    listener_cls = _listener_from_config(config)
    listener = listener_cls(**config.listener.params)
    return Scheduler(
        config.rule,
        listener=listener,
        transport=transport_cls(
            **config.transport.params,
        ),
        cache=cache_cls(
            id=f"{transport_cls}-{listener_cls}",
        ),
    )


def read_config(
    path: Path,
) -> tuple[Scheduler, ...]:
    with open(path, "r", encoding="utf-8") as fh:
        data = safe_load(fh.read())
    config = _ConfigModel(**data)
    cache_cls = _cache_from_config(config)
    return tuple(
        _make_scheduler_from_config(
            scheduler_config,
            cache_cls=cache_cls,
        )
        for scheduler_config in config.schedulers
    )
