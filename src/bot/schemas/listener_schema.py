from marshmallow import Schema, fields


class ListenerSchema(Schema):
    url = fields.Str(required=True)
    id = fields.Str(required=True)
    delay = fields.Int(required=False, default=300)
    preview = fields.Bool(required=False, default=True)
    format = fields.Str(required=False, default='<b>$title</b>\n$url')
