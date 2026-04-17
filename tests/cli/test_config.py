from collections.abc import Callable
from pathlib import Path

from pydantic import ValidationError
from pytest import raises

from feedforbot import (
    CacheProtocol,
    FilesCache,
    InMemoryCache,
    RSSListener,
    Scheduler,
    TelegramBotTransport,
)
from feedforbot.cli.config import read_config


def _in_memory_factory(cache_id: str) -> CacheProtocol:
    return InMemoryCache(id=cache_id)


def _files_factory(
    data_dir: Path,
) -> Callable[[str], CacheProtocol]:
    def _factory(cache_id: str) -> CacheProtocol:
        return FilesCache(id=cache_id, data_dir=data_dir)

    return _factory


def _write_config(
    tmp_path: Path,
    content: str,
) -> Path:
    config_path = tmp_path / "config.yml"
    config_path.write_text(content)
    return config_path


def test_minimal_config(tmp_path: Path) -> None:
    path = _write_config(
        tmp_path,
        """
- listener:
    type: rss
    params:
      url: https://example.com/feed
  transport:
    type: telegram_bot
    params:
      token: fake-token
      to: "@chan"
""",
    )
    schedulers = read_config(path, cache_factory=_in_memory_factory)
    assert len(schedulers) == 1
    s = schedulers[0]
    assert isinstance(s, Scheduler)
    assert isinstance(s.listener, RSSListener)
    assert isinstance(s.transport, TelegramBotTransport)
    assert isinstance(s.cache, InMemoryCache)
    assert s.cron_rule == "* * * * *"


def test_files_cache(tmp_path: Path) -> None:
    path = _write_config(
        tmp_path,
        """
- listener:
    type: rss
    params:
      url: https://example.com/feed
  transport:
    type: telegram_bot
    params:
      token: fake-token
      to: "@chan"
""",
    )
    schedulers = read_config(
        path,
        cache_factory=_files_factory(tmp_path),
    )
    cache = schedulers[0].cache
    assert isinstance(cache, FilesCache)
    assert cache.data_dir == tmp_path.resolve()


def test_custom_cron_rule(tmp_path: Path) -> None:
    path = _write_config(
        tmp_path,
        """
- rule: "*/5 * * * *"
  listener:
    type: rss
    params:
      url: https://example.com/feed
  transport:
    type: telegram_bot
    params:
      token: fake-token
      to: "@chan"
""",
    )
    schedulers = read_config(path, cache_factory=_in_memory_factory)
    assert schedulers[0].cron_rule == "*/5 * * * *"


def test_multiple_schedulers(tmp_path: Path) -> None:
    path = _write_config(
        tmp_path,
        """
- listener:
    type: rss
    params:
      url: https://example.com/feed1
  transport:
    type: telegram_bot
    params:
      token: token1
      to: "@chan1"
- listener:
    type: rss
    params:
      url: https://example.com/feed2
  transport:
    type: telegram_bot
    params:
      token: token2
      to: "@chan2"
""",
    )
    schedulers = read_config(path, cache_factory=_in_memory_factory)
    expected = 2
    assert len(schedulers) == expected


def test_invalid_listener_type(tmp_path: Path) -> None:
    path = _write_config(
        tmp_path,
        """
- listener:
    type: unknown
    params:
      url: https://example.com
  transport:
    type: telegram_bot
    params:
      token: fake
      to: "@chan"
""",
    )
    with raises(ValidationError):
        read_config(path, cache_factory=_in_memory_factory)


def test_empty_config_rejected(tmp_path: Path) -> None:
    path = _write_config(tmp_path, "[]\n")
    with raises(ValidationError):
        read_config(path, cache_factory=_in_memory_factory)


def test_invalid_root_is_not_list(tmp_path: Path) -> None:
    path = _write_config(
        tmp_path,
        """
schedulers:
  - listener:
      type: rss
      params:
        url: https://example.com/feed
    transport:
      type: telegram_bot
      params:
        token: fake
        to: "@chan"
""",
    )
    with raises(ValidationError):
        read_config(path, cache_factory=_in_memory_factory)


def test_cache_id_is_stable(tmp_path: Path) -> None:
    path = _write_config(
        tmp_path,
        """
- listener:
    type: rss
    params:
      url: https://example.com/feed
  transport:
    type: telegram_bot
    params:
      token: fake-token
      to: "@chan"
""",
    )
    s1 = read_config(path, cache_factory=_in_memory_factory)
    s2 = read_config(path, cache_factory=_in_memory_factory)
    c1 = s1[0].cache
    c2 = s2[0].cache
    assert isinstance(c1, InMemoryCache)
    assert isinstance(c2, InMemoryCache)
