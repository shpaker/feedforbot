import asyncio
from logging import basicConfig
from pathlib import Path

from click import Context, argument, command, echo, option, pass_context, types

from feedforbot import VERSION
from feedforbot.config import read_config

VERBOSITY_LEVEL = (
    "WARNING",
    "INFO",
    "DEBUG",
    "NOTSET",
)


def _echo_version(
    ctx: Context,
    param: bool,  # noqa, pylint: disable=unused-argument
    value: str,
) -> None:
    if not value or ctx.resilient_parsing:
        return
    echo(VERSION)
    ctx.exit()


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
@option("--verbose", "-v", count=True)
@option(
    "--version",
    "-V",
    is_flag=True,
    default=False,
    expose_value=False,
    is_eager=True,
    callback=_echo_version,
)
@pass_context
def main(
    ctx: Context,  # noqa
    configuration: Path,
    verbose: int,
) -> None:
    ctx.obj = {
        "verbose": verbose,
    }
    if verbose >= len(VERBOSITY_LEVEL):
        verbose = len(VERBOSITY_LEVEL) - 1
    log_level = VERBOSITY_LEVEL[verbose]
    basicConfig(level=log_level)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    schedulers = read_config(configuration)
    for scheduler in schedulers:
        scheduler.run()
    loop.run_forever()
