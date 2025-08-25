from marshmallow import Schema, fields, validate

class UserQuerySchema(Schema):
    """用户查询参数模式"""
    role = fields.Str()
    is_active = fields.Bool()

class UserUpdateSchema(Schema):
    """用户更新模式"""
    #is_active = fields.Bool(required=True)
    username = fields.String(required=True, load_only=True, validate=validate.Length(min=8, max=20))
    roles = fields.List(
        fields.Str(validate=validate.OneOf(["admin", "user"])),
        required=True
    )
    wallets = fields.List(fields.Str())

class UserDeleteSchema(Schema):
    """用户删除模式"""
    username = fields.String(required=True, load_only=True, validate=validate.Length(min=8, max=20))
