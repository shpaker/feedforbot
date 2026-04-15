from click import Context, echo

from feedforbot.__version__ import VERSION


def echo_version(
    ctx: Context,
    param: bool,  # noqa: ARG001
    value: str,
) -> None:
    if not value or ctx.resilient_parsing:
        return
    echo(VERSION)
    ctx.exit()
