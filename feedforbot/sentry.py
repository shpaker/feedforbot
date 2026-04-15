from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Protocol


if TYPE_CHECKING:
    from collections.abc import Generator


class _ScopeProtocol(Protocol):
    def set_tag(self, key: str, value: str) -> None: ...
    def set_extra(self, key: str, value: object) -> None: ...


class _NoOpScope:
    def set_tag(self, key: str, value: str) -> None:
        pass

    def set_extra(self, key: str, value: object) -> None:
        pass


def _get_sentry() -> Any | None:
    try:
        import sentry_sdk  # noqa: PLC0415
    except ImportError:  # pragma: no cover
        return None
    else:
        return sentry_sdk


def capture_exception(exc: BaseException) -> None:
    sdk = _get_sentry()
    if sdk is not None:
        sdk.capture_exception(exc)


@contextmanager
def new_scope() -> Generator[_ScopeProtocol]:
    sdk = _get_sentry()
    if sdk is not None:
        with sdk.new_scope() as scope:
            yield scope
    else:  # pragma: no cover
        yield _NoOpScope()
