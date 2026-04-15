import hashlib
import json
from collections.abc import Iterable
from pathlib import Path

from feedforbot.__version__ import __title__
from feedforbot.article import ArticleModel
from feedforbot.logger import logger
from feedforbot.types import CacheProtocol


_DEFAULT_FILES_CACHE_DIR = Path.home() / ".feedforbot"


class InMemoryCache(CacheProtocol):
    def __init__(
        self,
        id: str,  # noqa: ARG002
    ) -> None:
        self._cache: tuple[ArticleModel, ...] = ()
        self._populated: bool = False

    def __repr__(self) -> str:
        return f"<{__title__}.{self.__class__.__name__}>"

    @property
    def is_populated(self) -> bool:
        return self._populated

    def write(
        self,
        *articles: ArticleModel,
    ) -> None:
        self._cache = articles
        self._populated = True

    def read(
        self,
    ) -> Iterable[ArticleModel]:
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

    @property
    def is_populated(self) -> bool:
        return self.cache_path.exists()

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
                    [article.model_dump(mode="json") for article in articles],
                    indent=2,
                    sort_keys=True,
                ),
            )
        logger.debug(
            "cache_write: path=%s articles=%d",
            self.cache_path,
            len(articles),
        )

    def read(
        self,
    ) -> Iterable[ArticleModel]:
        try:
            with open(self.cache_path) as fh:
                contents = fh.read()
        except FileNotFoundError:
            logger.debug(
                "cache_read: path=%s found=false",
                self.cache_path,
            )
            return ()
        if not contents:
            logger.debug(
                "cache_read: path=%s empty=true",
                self.cache_path,
            )
            return ()
        articles = tuple(ArticleModel(**data) for data in json.loads(contents))
        logger.debug(
            "cache_read: path=%s found=true articles=%d",
            self.cache_path,
            len(articles),
        )
        return articles

    def _ensure_data_dir(
        self,
    ) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
