from pathlib import Path

from pydantic import ValidationError
from pytest import raises

from feedforbot import (
    FilesCache,
    InMemoryCache,
    RSSListener,
    Scheduler,
    TelegramBotTransport,
)
from feedforbot.cli.config import read_config


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
cache:
  type: in_memory
schedulers:
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
    schedulers = read_config(path)
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
cache:
  type: files
schedulers:
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
    schedulers = read_config(path)
    assert isinstance(schedulers[0].cache, FilesCache)


def test_custom_cron_rule(tmp_path: Path) -> None:
    path = _write_config(
        tmp_path,
        """
cache:
  type: in_memory
schedulers:
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
    schedulers = read_config(path)
    assert schedulers[0].cron_rule == "*/5 * * * *"


def test_multiple_schedulers(tmp_path: Path) -> None:
    path = _write_config(
        tmp_path,
        """
cache:
  type: in_memory
schedulers:
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
    schedulers = read_config(path)
    expected = 2
    assert len(schedulers) == expected


def test_invalid_cache_type(tmp_path: Path) -> None:
    path = _write_config(
        tmp_path,
        """
cache:
  type: redis
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
        read_config(path)


def test_invalid_listener_type(tmp_path: Path) -> None:
    path = _write_config(
        tmp_path,
        """
cache:
  type: in_memory
schedulers:
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
        read_config(path)


def test_cache_id_is_stable(tmp_path: Path) -> None:
    path = _write_config(
        tmp_path,
        """
cache:
  type: in_memory
schedulers:
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
    s1 = read_config(path)
    s2 = read_config(path)
    c1 = s1[0].cache
    c2 = s2[0].cache
    assert isinstance(c1, InMemoryCache)
    assert isinstance(c2, InMemoryCache)
