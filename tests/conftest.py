from pathlib import Path

from pytest import fixture

_MOCK_DIR = Path(__file__).parent / "mocks"
_DEFAULT_EXTENSION = ".xml"


@fixture(name="read_mock")
def _read_mock():
    def _func(
        name: str,
        strip: bool = True,
    ) -> str:
        if not name.lower().endswith(_DEFAULT_EXTENSION):
            name = name + _DEFAULT_EXTENSION
        filepath = _MOCK_DIR / name
        with open(filepath, "r", encoding="utf-8") as fh:
            data = fh.read()
        if strip:
            data = data.strip()
        return data

    return _func
