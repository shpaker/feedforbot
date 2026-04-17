import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import fakeredis
import pytest
from pytest import raises

from feedforbot import cache as cache_module
from feedforbot.article import ArticleModel
from feedforbot.cache import FilesCache, InMemoryCache, RedisCache


def _article(**kwargs: Any) -> ArticleModel:
    defaults: dict[str, Any] = {
        "id": "1",
        "title": "Test",
        "url": "https://example.com/1",
        "text": "body",
    }
    defaults.update(kwargs)
    return ArticleModel(**defaults)


_T0 = datetime(2025, 1, 1, tzinfo=timezone.utc)


class TestInMemoryCache:
    def test_not_populated_initially(self) -> None:
        cache = InMemoryCache(id="test")
        assert not cache.is_populated

    def test_known_ids_empty_when_not_populated(self) -> None:
        cache = InMemoryCache(id="test")
        assert cache.known_ids == set()

    def test_add_populates_and_known_ids(self) -> None:
        cache = InMemoryCache(id="test")
        cache.add(_article(id="1"), _article(id="2"))
        assert cache.is_populated
        assert cache.known_ids == {"1", "2"}

    def test_add_accumulates(self) -> None:
        cache = InMemoryCache(id="test")
        cache.add(_article(id="1"))
        cache.add(_article(id="2"))
        assert cache.known_ids == {"1", "2"}

    def test_add_updates_grabbed_at_for_existing_id(self) -> None:
        cache = InMemoryCache(id="test")
        cache.add(_article(id="1", grabbed_at=_T0))
        cache.add(_article(id="1", grabbed_at=_T0 + timedelta(days=1)))
        assert cache.known_ids == {"1"}

    def test_trim_keeps_most_recent(self) -> None:
        cache = InMemoryCache(id="test")
        cache.add(
            _article(id="old", grabbed_at=_T0),
            _article(id="mid", grabbed_at=_T0 + timedelta(days=1)),
            _article(id="new", grabbed_at=_T0 + timedelta(days=2)),
        )
        cache.trim(2)
        assert cache.known_ids == {"mid", "new"}

    def test_trim_noop_when_under_limit(self) -> None:
        cache = InMemoryCache(id="test")
        cache.add(_article(id="1"), _article(id="2"))
        cache.trim(10)
        assert cache.known_ids == {"1", "2"}

    def test_trim_zero_is_noop(self) -> None:
        cache = InMemoryCache(id="test")
        cache.add(_article(id="1"))
        cache.trim(0)
        assert cache.known_ids == {"1"}

    def test_repr(self) -> None:
        cache = InMemoryCache(id="test")
        assert "InMemoryCache" in repr(cache)


class TestFilesCache:
    def test_not_populated_initially(
        self,
        tmp_path: Path,
    ) -> None:
        cache = FilesCache(id="test", data_dir=tmp_path)
        assert not cache.is_populated

    def test_known_ids_empty_when_not_populated(
        self,
        tmp_path: Path,
    ) -> None:
        cache = FilesCache(id="test", data_dir=tmp_path)
        assert cache.known_ids == set()

    def test_add_and_known_ids(
        self,
        tmp_path: Path,
    ) -> None:
        cache = FilesCache(id="test", data_dir=tmp_path)
        cache.add(_article(id="1"), _article(id="2"))
        assert cache.is_populated
        assert cache.known_ids == {"1", "2"}

    def test_add_persists_across_instances(
        self,
        tmp_path: Path,
    ) -> None:
        c1 = FilesCache(id="test", data_dir=tmp_path)
        c1.add(_article(id="1"), _article(id="2"))
        c2 = FilesCache(id="test", data_dir=tmp_path)
        assert c2.known_ids == {"1", "2"}

    def test_write_creates_json_file_with_slim_schema(
        self,
        tmp_path: Path,
    ) -> None:
        cache = FilesCache(id="test", data_dir=tmp_path)
        cache.add(_article(id="1", title="big title", text="huge body"))
        data = json.loads(cache.cache_path.read_text())
        assert len(data) == 1
        assert set(data[0].keys()) == {"id", "grabbed_at"}

    def test_trim_keeps_most_recent(
        self,
        tmp_path: Path,
    ) -> None:
        cache = FilesCache(id="test", data_dir=tmp_path)
        cache.add(
            _article(id="old", grabbed_at=_T0),
            _article(id="mid", grabbed_at=_T0 + timedelta(days=1)),
            _article(id="new", grabbed_at=_T0 + timedelta(days=2)),
        )
        cache.trim(2)
        reloaded = FilesCache(id="test", data_dir=tmp_path)
        assert reloaded.known_ids == {"mid", "new"}

    def test_read_handles_empty_file(
        self,
        tmp_path: Path,
    ) -> None:
        cache = FilesCache(id="test", data_dir=tmp_path)
        cache.cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache.cache_path.write_text("")
        assert cache.known_ids == set()

    def test_read_handles_corrupt_json(
        self,
        tmp_path: Path,
    ) -> None:
        cache = FilesCache(id="test", data_dir=tmp_path)
        cache.cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache.cache_path.write_text("{not valid json")
        assert cache.known_ids == set()

    def test_corrupt_file_is_deleted_and_treated_as_first_run(
        self,
        tmp_path: Path,
    ) -> None:
        cache = FilesCache(id="test", data_dir=tmp_path)
        cache.cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache.cache_path.write_text("{not json")
        assert cache.is_populated is False
        assert not cache.cache_path.exists()

    def test_old_schema_is_deleted_and_treated_as_first_run(
        self,
        tmp_path: Path,
    ) -> None:
        cache = FilesCache(id="test", data_dir=tmp_path)
        cache.cache_path.parent.mkdir(parents=True, exist_ok=True)
        old_payload = [
            {
                "id": "1",
                "title": "legacy",
                "url": "https://example.com/1",
                "text": "body",
            },
        ]
        cache.cache_path.write_text(json.dumps(old_payload))
        assert cache.is_populated is False
        assert not cache.cache_path.exists()

    def test_creates_data_dir(
        self,
        tmp_path: Path,
    ) -> None:
        data_dir = tmp_path / "sub" / "dir"
        cache = FilesCache(id="test", data_dir=data_dir)
        cache.add(_article(id="1"))
        assert data_dir.exists()

    def test_deterministic_path(
        self,
        tmp_path: Path,
    ) -> None:
        c1 = FilesCache(id="same-id", data_dir=tmp_path)
        c2 = FilesCache(id="same-id", data_dir=tmp_path)
        assert c1.cache_path == c2.cache_path

    def test_different_ids_different_paths(
        self,
        tmp_path: Path,
    ) -> None:
        c1 = FilesCache(id="id-a", data_dir=tmp_path)
        c2 = FilesCache(id="id-b", data_dir=tmp_path)
        assert c1.cache_path != c2.cache_path

    def test_repr(
        self,
        tmp_path: Path,
    ) -> None:
        cache = FilesCache(id="test", data_dir=tmp_path)
        assert "FilesCache" in repr(cache)
        assert str(tmp_path) in repr(cache)

    def test_write_is_atomic_no_stray_tmp_files(
        self,
        tmp_path: Path,
    ) -> None:
        cache = FilesCache(id="test", data_dir=tmp_path)
        cache.add(_article(id="1"))
        cache.add(_article(id="2"))
        leftovers = [
            p for p in tmp_path.iterdir() if p.name != cache.cache_path.name
        ]
        assert leftovers == []

    def test_write_does_not_leave_partial_file_on_error(
        self,
        tmp_path: Path,
        monkeypatch: Any,
    ) -> None:
        import os as os_mod  # noqa: PLC0415

        cache = FilesCache(id="test", data_dir=tmp_path)
        cache.add(_article(id="original"))
        original_content = cache.cache_path.read_text()

        def _boom(src: str, dst: str) -> None:  # noqa: ARG001
            raise OSError("disk full")

        monkeypatch.setattr(os_mod, "replace", _boom)
        with raises(OSError, match="disk full"):
            cache.add(_article(id="replacement"))

        assert cache.cache_path.read_text() == original_content
        leftovers = [
            p for p in tmp_path.iterdir() if p.name != cache.cache_path.name
        ]
        assert leftovers == []


class TestRedisCache:
    @pytest.fixture
    def fake_server(
        self,
        monkeypatch: Any,
    ) -> fakeredis.FakeServer:
        server = fakeredis.FakeServer()

        def _fake_from_url(
            url: str,  # noqa: ARG001
            **_: Any,
        ) -> fakeredis.FakeStrictRedis:
            return fakeredis.FakeStrictRedis(
                server=server,
                decode_responses=True,
            )

        monkeypatch.setattr(
            cache_module._redis.Redis,  # type: ignore[attr-defined] # noqa: SLF001
            "from_url",
            staticmethod(_fake_from_url),
        )
        return server

    def test_not_populated_initially(
        self,
        fake_server: fakeredis.FakeServer,  # noqa: ARG002
    ) -> None:
        cache = RedisCache(id="test", url="redis://localhost:6379/0")
        assert not cache.is_populated

    def test_known_ids_empty_when_not_populated(
        self,
        fake_server: fakeredis.FakeServer,  # noqa: ARG002
    ) -> None:
        cache = RedisCache(id="test", url="redis://localhost:6379/0")
        assert cache.known_ids == set()

    def test_add_populates_and_known_ids(
        self,
        fake_server: fakeredis.FakeServer,  # noqa: ARG002
    ) -> None:
        cache = RedisCache(id="test", url="redis://localhost:6379/0")
        cache.add(_article(id="1"), _article(id="2"))
        assert cache.is_populated
        assert cache.known_ids == {"1", "2"}

    def test_add_accumulates(
        self,
        fake_server: fakeredis.FakeServer,  # noqa: ARG002
    ) -> None:
        cache = RedisCache(id="test", url="redis://localhost:6379/0")
        cache.add(_article(id="1"))
        cache.add(_article(id="2"))
        assert cache.known_ids == {"1", "2"}

    def test_add_persists_across_instances(
        self,
        fake_server: fakeredis.FakeServer,  # noqa: ARG002
    ) -> None:
        c1 = RedisCache(id="test", url="redis://localhost:6379/0")
        c1.add(_article(id="1"), _article(id="2"))
        c2 = RedisCache(id="test", url="redis://localhost:6379/0")
        assert c2.known_ids == {"1", "2"}
        assert c2.is_populated

    def test_populated_field_excluded_from_known_ids(
        self,
        fake_server: fakeredis.FakeServer,  # noqa: ARG002
    ) -> None:
        cache = RedisCache(id="test", url="redis://localhost:6379/0")
        cache.add(_article(id="1"))
        assert "__populated__" not in cache.known_ids

    def test_trim_keeps_most_recent(
        self,
        fake_server: fakeredis.FakeServer,  # noqa: ARG002
    ) -> None:
        cache = RedisCache(id="test", url="redis://localhost:6379/0")
        cache.add(
            _article(id="old", grabbed_at=_T0),
            _article(id="mid", grabbed_at=_T0 + timedelta(days=1)),
            _article(id="new", grabbed_at=_T0 + timedelta(days=2)),
        )
        cache.trim(2)
        reloaded = RedisCache(id="test", url="redis://localhost:6379/0")
        assert reloaded.known_ids == {"mid", "new"}

    def test_trim_noop_when_under_limit(
        self,
        fake_server: fakeredis.FakeServer,  # noqa: ARG002
    ) -> None:
        cache = RedisCache(id="test", url="redis://localhost:6379/0")
        cache.add(_article(id="1"), _article(id="2"))
        cache.trim(10)
        assert cache.known_ids == {"1", "2"}

    def test_trim_zero_is_noop(
        self,
        fake_server: fakeredis.FakeServer,  # noqa: ARG002
    ) -> None:
        cache = RedisCache(id="test", url="redis://localhost:6379/0")
        cache.add(_article(id="1"))
        cache.trim(0)
        assert cache.known_ids == {"1"}

    def test_different_ids_different_keys(
        self,
        fake_server: fakeredis.FakeServer,  # noqa: ARG002
    ) -> None:
        c1 = RedisCache(id="id-a", url="redis://localhost:6379/0")
        c2 = RedisCache(id="id-b", url="redis://localhost:6379/0")
        c1.add(_article(id="only-a"))
        c2.add(_article(id="only-b"))
        assert c1.known_ids == {"only-a"}
        assert c2.known_ids == {"only-b"}

    def test_repr(
        self,
        fake_server: fakeredis.FakeServer,  # noqa: ARG002
    ) -> None:
        cache = RedisCache(id="test", url="redis://localhost:6379/0")
        assert "RedisCache" in repr(cache)
        assert "feedforbot:" in repr(cache)

    def test_raises_import_error_when_redis_missing(
        self,
        monkeypatch: Any,
    ) -> None:
        monkeypatch.setattr(cache_module, "_redis", None)
        with raises(ImportError, match="RedisCache requires"):
            RedisCache(id="test", url="redis://localhost:6379/0")
