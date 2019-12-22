import json

import feedparser
from marshmallow import Schema
from redis import Redis

from ..models import Feed, FeedEntry
from ..schemas import FeedSchema


class Listener:

    def __init__(self,
                url: str,
                id: str,
                delay: int,
                preview: bool,
                format: str,
                redis_client: Redis):

        self.url: str = url
        self.id: str = id
        self.delay: int = delay
        self.preview: bool = preview
        self.format: str = format.replace('\\n', '\n')
        self.redis: Redis = redis_client

        self._feed_schema: Schema = FeedSchema()

    def read_from_db(self):
        stored_feed = Feed()
        stored_entries_bytes: bytes = self.redis.hget(name=self.id,
                                                      key=self.url)

        if not stored_entries_bytes:
            res = self.store_feed(stored_feed)
            return stored_feed

        stored_entries_str = stored_entries_bytes.decode()
        stored_entries_dict = json.loads(stored_entries_str)
        stored_entries_dict = self._feed_schema.dump(stored_entries_dict)

        for raw_entry in stored_entries_dict['entries']:
            entry = FeedEntry(description=raw_entry['description'],
                              published=raw_entry['published'],
                              title=raw_entry['title'],
                              url=raw_entry['url'],
                              author=raw_entry['author'],
                              tags=raw_entry['tags'],
                              forwarded=raw_entry['forwarded'])
            stored_feed.entries.append(entry)

        return stored_feed

    def store_feed(self, feed: Feed) -> int:
        feed_dumped = self._feed_schema.dump(feed)
        result = self.redis.hset(name=self.id,
                                 key=self.url,
                                 value=json.dumps(feed_dumped).encode())
        return result

    @property
    def feed(self):
        old_feed = self.read_from_db()
        raw_feed = feedparser.parse(self.url)
        new_feed = Feed()
        new_feed.from_raw(raw_entries=list(raw_feed.entries),
                          old_entries=old_feed.entries)

        return new_feed
