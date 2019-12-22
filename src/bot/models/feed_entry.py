from dataclasses import dataclass
from html import escape


@dataclass
class FeedEntry:
    description: str
    published: str
    title: str
    url: str
    author: str
    tags: str

    forwarded: bool = False

    def __post_init__(self):
        self.author = escape(self.author)
        self.description = escape(self.description)
        # TODO rewrite from str to datetime type
        self.published = escape(self.published)
        self.title = escape(self.title)
        self.url = escape(self.url)
        self.tags = escape(self.tags)
