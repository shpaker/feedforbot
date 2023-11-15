import json
from abc import ABC, abstractmethod
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import aiofiles
import aiofiles.os
import orjson

from feedforbot.constants import APP_NAME, DEFAULT_FILES_CACHE_DIR
from feedforbot.core.article import ArticleModel
from feedforbot.core.utils import make_sha2


class CacheBase(ABC):
    def __init__(
        self,
        id: str,
    ) -> None:
        self.id = id

    def __repr__(self) -> str:
        return f"<{APP_NAME}.{self.__class__.__name__}>"

    @abstractmethod
    async def write(
        self,
        *articles: ArticleModel,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def read(
        self,
    ) -> Iterable[ArticleModel] | None:
        raise NotImplementedError


class InMemoryCache(
    CacheBase,
):
    def __init__(
        self,
        **kwargs: Any,
    ):
        self._cache: Iterable[ArticleModel] | None = None
        super().__init__(**kwargs)

    async def write(
        self,
        *articles: ArticleModel,
    ) -> None:
        self._cache = articles

    async def read(
        self,
    ) -> Iterable[ArticleModel] | None:
        return self._cache


class FilesCache(
    CacheBase,
):
    def __init__(
        self,
        id: str,
        data_dir: Path = DEFAULT_FILES_CACHE_DIR,
    ) -> None:
        self.data_dir = data_dir.resolve()
        self.cache_path = self.data_dir / f"{make_sha2(id)}.json"
        super().__init__(id)

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
        if not await aiofiles.os.path.exists(self.cache_path):
            return None
        async with aiofiles.open(
            self.cache_path,
            mode="r",
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
