import hashlib
import json
from collections.abc import Iterable
from pathlib import Path

import aiofiles
import aiofiles.os
import orjson

from feedforbot.__version__ import APP_NAME
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
        return f"<{APP_NAME}.{self.__class__.__name__}>"

    async def write(
        self,
        *articles: ArticleModel,
    ) -> None:
        self._cache = articles

    async def read(
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
        return f"<{APP_NAME}.{self.__class__.__name__}: {self.cache_path}>"

    async def write(
        self,
        *articles: ArticleModel,
    ) -> None:
        await self._ensure_data_dir()
        async with aiofiles.open(
            self.cache_path,
            mode="wb",
        ) as fh:
            await fh.write(
                orjson.dumps(
                    [article.model_dump() for article in articles],
                    option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS,
                ),
            )

    async def read(
        self,
    ) -> Iterable[ArticleModel] | None:
        if not await aiofiles.os.path.exists(
            self.cache_path,
        ):
            return None
        async with aiofiles.open(
            self.cache_path,
        ) as fh:
            contents = await fh.read()
        if not contents:
            return None
        return tuple(ArticleModel(**data) for data in json.loads(contents))

    async def _ensure_data_dir(
        self,
    ) -> None:
        if await aiofiles.os.path.exists(self.data_dir):
            return
        try:
            await aiofiles.os.mkdir(self.data_dir)
        except FileExistsError:
            return
