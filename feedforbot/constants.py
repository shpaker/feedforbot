from pathlib import Path

from jinja2 import Template

APP_NAME = "FeedForBot"
DEFAULT_MESSAGE_TEMPLATE = Template("{{ TITLE }}\n\n{{ TEXT }}\n\n{{ URL }}")
DEFAULT_FILES_CACHE_DIR = Path.home() / f".{APP_NAME.lower()}"
VERBOSITY_LEVELS = (
    "WARNING",
    "INFO",
    "DEBUG",
    "NOTSET",
)
