from datetime import datetime, timezone
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    field_serializer,
    field_validator,
)
from pydantic_core.core_schema import SerializationInfo

from feedforbot.core.utils import now


def _to_upper(
    string: str,
) -> str:
    return string.upper()


class ArticleModel(
    BaseModel,
):
    model_config = ConfigDict(
        alias_generator=_to_upper,
        populate_by_name=True,
    )

    id: str
    published_at: datetime | None = None
    grabbed_at: datetime = Field(default_factory=now)
    title: str
    url: HttpUrl
    text: str
    images: tuple[HttpUrl, ...] = ()
    authors: tuple[str, ...] = ()
    categories: tuple[str, ...] = ()

    def __eq__(
        self,
        other: Any,
    ) -> Any:
        return self.id == other.id

    @field_serializer("url")
    def serialize_url(
        self,
        value: HttpUrl,
        _info: SerializationInfo,
    ) -> str:
        return str(value)

    @field_serializer("images")
    def serialize_images(
        self,
        value: tuple[HttpUrl, ...],
        _info: SerializationInfo,
    ) -> tuple[str, ...]:
        return tuple(str(entry) for entry in value)

    @field_validator("published_at")
    @classmethod
    def _published_at(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
