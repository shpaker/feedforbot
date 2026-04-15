from click import Context, echo

from feedforbot.__version__ import __version__


def echo_version(
    ctx: Context,
    param: bool,  # noqa: ARG001
    value: str,
) -> None:
    if not value or ctx.resilient_parsing:
        return
    echo(__version__)
    ctx.exit()
