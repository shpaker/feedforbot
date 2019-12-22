from typing import List, Dict

from ..models import FeedEntry


class Feed:

    def __init__(self):
        self.entries: List[FeedEntry] = list()

    def from_raw(self,
                 raw_entries: List[Dict],
                 old_entries:List[FeedEntry] = None):

        for raw_entry in raw_entries:
            tags = []
            if 'tags' in raw_entry['tags']:
                tags = [tags.append(tag.get('term')) for tag in raw_entry.get('tags')]

            entry = FeedEntry(description=raw_entry.get('summary'),
                              published=raw_entry.get('published'),
                              title=raw_entry.get('title'),
                              url=raw_entry.get('id') if 'id' in raw_entry else raw_entry.get('url'),
                              author=raw_entry.get('author'),
                              tags=', '.join(tags))

            self.entries.append(entry)

        self.entries.reverse()

        if old_entries:
            for raw_entry in self.entries:
                for old_entry in old_entries:
                    if old_entry.url == raw_entry.url:
                        raw_entry.forwarded = old_entry.forwarded
