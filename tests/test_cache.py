import json
from pathlib import Path
from typing import Any

from feedforbot.article import ArticleModel
from feedforbot.cache import FilesCache, InMemoryCache


def _article(**kwargs: Any) -> ArticleModel:
    defaults: dict[str, Any] = {
        "id": "1",
        "title": "Test",
        "url": "https://example.com/1",
        "text": "body",
    }
    defaults.update(kwargs)
    return ArticleModel(**defaults)


class TestInMemoryCache:
    def test_not_populated_initially(self) -> None:
        cache = InMemoryCache(id="test")
        assert not cache.is_populated

    def test_read_returns_empty_when_not_populated(
        self,
    ) -> None:
        cache = InMemoryCache(id="test")
        assert tuple(cache.read()) == ()

    def test_write_and_read(self) -> None:
        cache = InMemoryCache(id="test")
        a1 = _article(id="1")
        a2 = _article(id="2")
        cache.write(a1, a2)
        assert cache.is_populated
        assert tuple(cache.read()) == (a1, a2)

    def test_write_overwrites(self) -> None:
        cache = InMemoryCache(id="test")
        a1 = _article(id="1")
        a2 = _article(id="2")
        cache.write(a1)
        cache.write(a2)
        assert tuple(cache.read()) == (a2,)

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

    def test_read_returns_empty_when_not_populated(
        self,
        tmp_path: Path,
    ) -> None:
        cache = FilesCache(id="test", data_dir=tmp_path)
        assert tuple(cache.read()) == ()

    def test_write_and_read(
        self,
        tmp_path: Path,
    ) -> None:
        cache = FilesCache(id="test", data_dir=tmp_path)
        a1 = _article(id="1")
        a2 = _article(id="2")
        cache.write(a1, a2)
        assert cache.is_populated
        result = tuple(cache.read())
        expected = 2
        assert len(result) == expected
        assert result[0].id == "1"
        assert result[1].id == "2"

    def test_write_creates_json_file(
        self,
        tmp_path: Path,
    ) -> None:
        cache = FilesCache(id="test", data_dir=tmp_path)
        cache.write(_article(id="1"))
        assert cache.cache_path.exists()
        data = json.loads(cache.cache_path.read_text())
        assert len(data) == 1

    def test_write_overwrites(
        self,
        tmp_path: Path,
    ) -> None:
        cache = FilesCache(id="test", data_dir=tmp_path)
        cache.write(_article(id="1"), _article(id="2"))
        cache.write(_article(id="3"))
        result = tuple(cache.read())
        assert len(result) == 1
        assert result[0].id == "3"

    def test_read_handles_empty_file(
        self,
        tmp_path: Path,
    ) -> None:
        cache = FilesCache(id="test", data_dir=tmp_path)
        cache.cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache.cache_path.write_text("")
        assert tuple(cache.read()) == ()

    def test_creates_data_dir(
        self,
        tmp_path: Path,
    ) -> None:
        data_dir = tmp_path / "sub" / "dir"
        cache = FilesCache(id="test", data_dir=data_dir)
        cache.write(_article(id="1"))
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
