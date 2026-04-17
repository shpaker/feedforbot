import contextlib
import hashlib
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import cast

from feedforbot.__version__ import __title__
from feedforbot.article import ArticleModel
from feedforbot.logger import logger
from feedforbot.types import CacheProtocol


try:
    import redis as _redis
except ImportError:  # pragma: no cover
    _redis = None  # type: ignore[assignment]


_DEFAULT_FILES_CACHE_DIR = Path.home() / ".feedforbot"

_REDIS_KEY_PREFIX = "feedforbot"
_REDIS_POPULATED_FIELD = "__populated__"


class InMemoryCache(CacheProtocol):
    def __init__(
        self,
        id: str,  # noqa: ARG002
    ) -> None:
        self._entries: dict[str, datetime] = {}
        self._populated: bool = False

    def __repr__(self) -> str:
        return f"<{__title__}.{self.__class__.__name__}>"

    @property
    def is_populated(self) -> bool:
        return self._populated

    @property
    def known_ids(self) -> set[str]:
        return set(self._entries.keys())

    def add(
        self,
        *articles: ArticleModel,
    ) -> None:
        for article in articles:
            self._entries[article.id] = article.grabbed_at
        self._populated = True

    def trim(
        self,
        limit: int,
    ) -> None:
        if limit <= 0 or len(self._entries) <= limit:
            return
        kept = sorted(
            self._entries.items(),
            key=lambda item: item[1],
            reverse=True,
        )[:limit]
        self._entries = dict(kept)


class FilesCache(CacheProtocol):
    def __init__(
        self,
        id: str,
        data_dir: Path = _DEFAULT_FILES_CACHE_DIR,
    ) -> None:
        self.id = id
        self.data_dir = data_dir.resolve()
        sha = hashlib.sha256(id.encode("utf-8")).hexdigest()
        self.cache_path = self.data_dir / f"{sha}.json"
        self._entries: dict[str, datetime] | None = None

    def __repr__(self) -> str:
        return f"<{__title__}.{self.__class__.__name__}: {self.cache_path}>"

    @property
    def is_populated(self) -> bool:
        if not self.cache_path.exists():
            return False
        self._load()
        return self.cache_path.exists()

    @property
    def known_ids(self) -> set[str]:
        self._load()
        assert self._entries is not None  # noqa: S101
        return set(self._entries.keys())

    def add(
        self,
        *articles: ArticleModel,
    ) -> None:
        self._load()
        assert self._entries is not None  # noqa: S101
        for article in articles:
            self._entries[article.id] = article.grabbed_at
        self._flush()

    def trim(
        self,
        limit: int,
    ) -> None:
        self._load()
        assert self._entries is not None  # noqa: S101
        if limit <= 0 or len(self._entries) <= limit:
            return
        kept = sorted(
            self._entries.items(),
            key=lambda item: item[1],
            reverse=True,
        )[:limit]
        self._entries = dict(kept)
        self._flush()

    def _load(self) -> None:
        if self._entries is not None:
            return
        try:
            with open(self.cache_path) as fh:
                contents = fh.read()
        except FileNotFoundError:
            self._entries = {}
            return
        if not contents:
            self._entries = {}
            return
        try:
            raw = json.loads(contents)
            entries: dict[str, datetime] = {}
            for item in raw:
                aid = item["id"]
                entries[aid] = datetime.fromisoformat(item["grabbed_at"])
            self._entries = entries
        except Exception:  # noqa: BLE001
            logger.warning(
                "cache_read_corrupt: path=%s — deleting to recover",
                self.cache_path,
            )
            with contextlib.suppress(OSError):
                self.cache_path.unlink()
            self._entries = {}

    def _flush(self) -> None:
        assert self._entries is not None  # noqa: S101
        self._ensure_data_dir()
        payload = json.dumps(
            [
                {"id": aid, "grabbed_at": ts.isoformat()}
                for aid, ts in sorted(
                    self._entries.items(),
                    key=lambda item: (item[1], item[0]),
                )
            ],
            indent=2,
        )
        fd, tmp_path = tempfile.mkstemp(
            prefix=f"{self.cache_path.name}.",
            suffix=".tmp",
            dir=self.data_dir,
        )
        tmp = Path(tmp_path)
        try:
            with os.fdopen(fd, mode="w") as fh:
                fh.write(payload)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, self.cache_path)  # noqa: PTH105
        except BaseException:
            with contextlib.suppress(OSError):
                tmp.unlink()
            raise
        logger.debug(
            "cache_write: path=%s entries=%d",
            self.cache_path,
            len(self._entries),
        )

    def _ensure_data_dir(
        self,
    ) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)


class RedisCache(CacheProtocol):
    def __init__(
        self,
        id: str,
        url: str,
    ) -> None:
        if _redis is None:
            raise ImportError(  # noqa: TRY003
                "feedforbot: RedisCache requires the `redis` package. "
                "Install with `pip install feedforbot[cli]` "
                "or `pip install redis`.",
            )
        self.id = id
        self.url = url
        sha = hashlib.sha256(id.encode("utf-8")).hexdigest()
        self._key = f"{_REDIS_KEY_PREFIX}:{sha}"
        self._client = _redis.Redis.from_url(
            url,
            decode_responses=True,
        )

    def __repr__(self) -> str:
        return f"<{__title__}.{self.__class__.__name__}: {self._key}>"

    @property
    def is_populated(self) -> bool:
        return bool(
            self._client.hexists(self._key, _REDIS_POPULATED_FIELD),
        )

    @property
    def known_ids(self) -> set[str]:
        fields = cast("list[str]", self._client.hkeys(self._key))
        return {f for f in fields if f != _REDIS_POPULATED_FIELD}

    def add(
        self,
        *articles: ArticleModel,
    ) -> None:
        mapping: dict[str, str] = {
            article.id: article.grabbed_at.isoformat() for article in articles
        }
        mapping[_REDIS_POPULATED_FIELD] = "1"
        self._client.hset(self._key, mapping=mapping)

    def trim(
        self,
        limit: int,
    ) -> None:
        if limit <= 0:
            return
        raw = cast("dict[str, str]", self._client.hgetall(self._key))
        raw.pop(_REDIS_POPULATED_FIELD, None)
        if len(raw) <= limit:
            return
        entries = sorted(
            raw.items(),
            key=lambda item: datetime.fromisoformat(item[1]),
            reverse=True,
        )
        to_remove = [aid for aid, _ in entries[limit:]]
        if to_remove:
            self._client.hdel(self._key, *to_remove)
