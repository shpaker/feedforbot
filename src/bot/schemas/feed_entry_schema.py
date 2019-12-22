from marshmallow import Schema, fields


class FeedEntrySchema(Schema):
    description = fields.Str(required=True, allow_none=True)
    published = fields.Str(required=True, allow_none=True)
    title = fields.Str(required=True, allow_none=True)
    url = fields.Str(required=True, allow_none=True)
    author = fields.Str(required=True, allow_none=True)
    tags = fields.Str(required=True, allow_none=True)
    forwarded = fields.Bool(required=True)
