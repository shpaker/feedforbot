import hashlib
from datetime import datetime, timezone
from typing import Any

from httpx import AsyncClient


def now() -> datetime:
    return datetime.now(tz=timezone.utc)


async def make_get_request(
    url: str,
) -> bytes:
    async with AsyncClient() as client:
        response = await client.get(url)
    response.raise_for_status()
    return response.read()


async def make_post_request(
    url: str,
    *,
    data: dict[str, Any],
) -> Any:
    async with AsyncClient() as client:
        response = await client.post(url, json=data)
    response.raise_for_status()
    return response.json()


def make_sha2(
    data: str,
) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()
