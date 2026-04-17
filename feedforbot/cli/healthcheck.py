import asyncio
from http import HTTPStatus

from feedforbot.logger import logger


_HEALTH_PATH = "/health"


async def run_healthcheck_server(
    port: int,
    host: str = "127.0.0.1",
) -> None:
    async def _handle(
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        request_line = await reader.readline()
        parts = request_line.decode("latin-1", errors="replace").split()
        match parts:
            case [_, target, *_]:
                path = target.split("?", 1)[0]
            case _:
                path = ""

        if path == _HEALTH_PATH:
            status = HTTPStatus.OK
            body = b"ok"
        else:
            status = HTTPStatus.NOT_FOUND
            body = b"not found"

        header = (
            f"HTTP/1.1 {status.value} {status.phrase}\r\n"
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
