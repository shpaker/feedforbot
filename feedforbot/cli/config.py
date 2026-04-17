import sys
from enum import Enum


if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from enum import Enum as _StrBase

    class StrEnum(str, _StrBase):
        pass


from collections.abc import Callable
from pathlib import Path
from typing import Annotated, Any

from pydantic import BaseModel, Field, TypeAdapter
from yaml import safe_load

from feedforbot import (
    CacheProtocol,
    ListenerProtocol,
    RSSListener,
    Scheduler,
    TelegramBotTransport,
    TransportProtocol,
)


class _ListenerTypes(StrEnum):
    RSS = "rss"


class _ListenerConfigMapping(Enum):
    RSS = RSSListener


class _TransportTypes(StrEnum):
    TELEGRAM_BOT = "telegram_bot"


class _TransportConfigMapping(Enum):
    TELEGRAM_BOT = TelegramBotTransport


class _ConfigEntryModel(BaseModel):
    params: dict[str, Any] = {}


class _ListenerConfigModel(_ConfigEntryModel):
    type: _ListenerTypes


class _TransportConfigModel(_ConfigEntryModel):
    type: _TransportTypes


class _SchedulerConfigModel(BaseModel):
    rule: str = "* * * * *"
    cache_limit: int | None = None
    listener: _ListenerConfigModel
    transport: _TransportConfigModel


_SchedulersAdapter: TypeAdapter[tuple[_SchedulerConfigModel, ...]] = (
    TypeAdapter(
        Annotated[
            tuple[_SchedulerConfigModel, ...],
            Field(min_length=1),
        ],
    )
)


def _listener_from_config(
    scheduler_config: _SchedulerConfigModel,
) -> type[ListenerProtocol]:
    name = scheduler_config.listener.type.name
    return _ListenerConfigMapping[name].value


def _transport_from_config(
    scheduler_config: _SchedulerConfigModel,
) -> type[TransportProtocol]:
    name = scheduler_config.transport.type.name
    return _TransportConfigMapping[name].value


def _make_scheduler_from_config(
    config: _SchedulerConfigModel,
    *,
    cache_factory: Callable[[str], CacheProtocol],
) -> Scheduler:
    transport_cls = _transport_from_config(config)
    listener_cls = _listener_from_config(config)
    listener = listener_cls(**config.listener.params)
    transport = transport_cls(**config.transport.params)
    cache_id = (
        f"{config.listener.type.value}"
        f":{config.listener.params.get('url', '')}"
        f"|{config.transport.type.value}"
        f":{config.transport.params.get('to', '')}"
    )
    return Scheduler(
        config.rule,
        listener=listener,
        transport=transport,
        cache=cache_factory(cache_id),
        cache_limit=config.cache_limit,
    )


def read_config(
    path: Path,
    *,
    cache_factory: Callable[[str], CacheProtocol],
) -> tuple[Scheduler, ...]:
    with path.open(encoding="utf-8", mode="r") as fh:
        data = safe_load(fh.read())
    schedulers_config = _SchedulersAdapter.validate_python(data)
    return tuple(
        _make_scheduler_from_config(
            scheduler_config,
            cache_factory=cache_factory,
        )
        for scheduler_config in schedulers_config
    )
