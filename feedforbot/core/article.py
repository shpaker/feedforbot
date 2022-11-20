from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, HttpUrl

from feedforbot.core.utils import now


def _to_upper(
    string: str,
) -> str:
    return string.upper()


class ArticleModel(
    BaseModel,
    alias_generator=_to_upper,
    allow_population_by_field_name=True,
):
    id: str
    published_at: datetime | None = None
    grabbed_at: datetime = Field(default_factory=now)
    title: str
    url: HttpUrl
    text: str
    images: tuple[HttpUrl, ...] = ()
    authors: tuple[str, ...] = ()

    def __eq__(
        self,
        other: Any,
    ) -> Any:
        return self.id == other.id
