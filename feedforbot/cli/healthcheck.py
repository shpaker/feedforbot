import asyncio
from http import HTTPStatus

from feedforbot.logger import logger


async def run_healthcheck_server(
    port: int,
    host: str = "0.0.0.0",
) -> None:
    async def _handle(
        reader: asyncio.StreamReader,  # noqa: ARG001
        writer: asyncio.StreamWriter,
    ) -> None:
        body = b"ok"
        header = (
            f"HTTP/1.1 {HTTPStatus.OK.value} {HTTPStatus.OK.phrase}\r\n"
            f"Content-Type: text/plain\r\n"
            f"Content-Length: {len(body)}\r\n"
            f"\r\n"
        )
        writer.write(header.encode() + body)
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(
        _handle,
        host,
        port,
    )
    logger.info(
        "healthcheck_start: host=%s port=%d",
        host,
        port,
    )
    async with server:
        await server.serve_forever()
