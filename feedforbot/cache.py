import hashlib
import json
from collections.abc import Iterable
from pathlib import Path

from feedforbot.__version__ import __title__
from feedforbot.article import ArticleModel
from feedforbot.types import CacheProtocol


_DEFAULT_FILES_CACHE_DIR = Path.home() / ".feedforbot"


class InMemoryCache(CacheProtocol):
    def __init__(
        self,
        id: str,  # noqa: ARG002
    ) -> None:
        self._cache: Iterable[ArticleModel] | None = None

    def __repr__(self) -> str:
        return f"<{__title__}.{self.__class__.__name__}>"

    def write(
        self,
        *articles: ArticleModel,
    ) -> None:
        self._cache = articles

    def read(
        self,
    ) -> Iterable[ArticleModel] | None:
        return self._cache


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

    def __repr__(self) -> str:
        return f"<{__title__}.{self.__class__.__name__}: {self.cache_path}>"

    def write(
        self,
        *articles: ArticleModel,
    ) -> None:
        self._ensure_data_dir()
        with open(
            self.cache_path,
            mode="w",
        ) as fh:
            fh.write(
                json.dumps(
                    [article.model_dump() for article in articles],
                    indent=2,
                    sort_keys=True,
                ),
            )

    def read(
        self,
    ) -> Iterable[ArticleModel] | None:
        if not self.cache_path.exists():
            return None
        with open(self.cache_path) as fh:
            contents = fh.read()
        if not contents:
            return None
        return tuple(ArticleModel(**data) for data in json.loads(contents))

    def _ensure_data_dir(
        self,
    ) -> None:
        self.data_dir.mkdir(exist_ok=True)
