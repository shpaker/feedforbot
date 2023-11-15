import asyncio
from logging import basicConfig
from pathlib import Path

import click
import sentry_sdk
from click import Context, argument, command, option, pass_context, types

from feedforbot import VERSION
from feedforbot.config import read_config
from feedforbot.constants import APP_NAME, VERBOSITY_LEVELS
from feedforbot.utils import echo_version


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
@pass_context
def main(
    ctx: Context,
    configuration: Path,
    verbose: int,
    sentry: str | None,
) -> None:
    """
    Bot for forwarding updates from RSS/Atom feeds to Telegram messenger
    https://github.com/shpaker/feedforbot
    """
    ctx.obj = {"verbose": verbose}
    if sentry is not None:
        sentry_sdk.init(
            dsn=sentry,
            release=f"{APP_NAME}-{VERSION}",
            attach_stacktrace=True,
        )
    if verbose >= len(VERBOSITY_LEVELS):
        verbose = len(VERBOSITY_LEVELS) - 1
    log_level = VERBOSITY_LEVELS[verbose]
    basicConfig(level=log_level)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    schedulers = read_config(configuration)
    for scheduler in schedulers:
        scheduler.run()
    loop.run_forever()
