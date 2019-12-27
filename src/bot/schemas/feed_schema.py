from marshmallow import Schema, fields

from ..schemas import FeedEntrySchema


class FeedSchema(Schema):
    entries = fields.List(fields.Nested(FeedEntrySchema, allow_none=False))
