import asyncio
import signal
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import click
import sentry_sdk
from click import Context, argument, command, option, pass_context, types

from feedforbot.__version__ import __title__
from feedforbot.__version__ import __version__ as _version
from feedforbot.cli.config import read_config
from feedforbot.cli.configure_logging import configure_logging
from feedforbot.cli.healthcheck import run_healthcheck_server
from feedforbot.cli.utils import echo_version
from feedforbot.logger import logger


_VERBOSITY_LEVELS = (
    "WARNING",
    "INFO",
    "DEBUG",
    "NOTSET",
)


@command()
@argument(
    "configuration",
    required=True,
    type=types.Path(
        exists=True,
        resolve_path=True,
        dir_okay=False,
        path_type=Path,
    ),
)
@option(
    "--verbose",
    "-v",
    count=True,
)
@option(
    "--version",
    "-V",
    is_flag=True,
    default=False,
    expose_value=False,
    is_eager=True,
    callback=echo_version,
    help="Show script version and exit.",
)
@option(
    "--sentry",
    type=click.STRING,
    default=None,
    show_default=True,
    help="Sentry DSN.",
)
@option(
    "--healthcheck-port",
    type=click.INT,
    default=None,
    show_default=True,
    help="Port for HTTP healthcheck endpoint.",
)
@pass_context
def main(
    ctx: Context,
    configuration: Path,
    verbose: int,
    sentry: str | None,
    healthcheck_port: int | None,
) -> None:
    """
    Bot for forwarding updates from RSS/Atom feeds
    to Telegram messenger
    https://github.com/shpaker/feedforbot
    """
    ctx.obj = {"verbose": verbose}
    if sentry is not None:
        sentry_sdk.init(
            dsn=sentry,
            release=f"{__title__}-{_version}",
            attach_stacktrace=True,
        )
    if verbose >= len(_VERBOSITY_LEVELS):
        verbose = len(_VERBOSITY_LEVELS) - 1
    log_level = _VERBOSITY_LEVELS[verbose]
    configure_logging(log_level=log_level)
    schedulers = read_config(configuration)
    logger.info(
        "config_loaded: path=%s schedulers=%d",
        configuration,
        len(schedulers),
    )

    async def _run_forever() -> None:
        loop = asyncio.get_running_loop()
        loop.set_default_executor(
            ThreadPoolExecutor(max_workers=len(schedulers)),
        )
        tasks = [
            asyncio.create_task(scheduler.arun()) for scheduler in schedulers
        ]
        if healthcheck_port is not None:
            tasks.append(
                asyncio.create_task(
                    run_healthcheck_server(healthcheck_port),
                ),
            )

        def _shutdown(sig: signal.Signals) -> None:
            logger.info("shutdown: signal=%s", sig.name)
            for scheduler in schedulers:
                scheduler.stop()
            for task in tasks:
                task.cancel()

        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                sig,
                _shutdown,
                sig,
            )

        results = await asyncio.gather(
            *tasks,
            return_exceptions=True,
        )
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    "task_crashed: index=%d error=%s",
                    i,
                    result,
                )

    asyncio.run(_run_forever())
