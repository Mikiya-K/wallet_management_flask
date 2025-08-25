from marshmallow import Schema, fields, validate

class WalletSchema(Schema):
    #id = fields.Int(dump_only=True)
    #user_id = fields.Int(dump_only=True)
    coldkey_name = fields.Str(validate=validate.Length(max=50), dump_only=True)
    coldkey_address = fields.Str(validate=validate.Length(equal=48), dump_only=True)
    free = fields.Float(dump_only=True)
    staked = fields.Float(dump_only=True)
    total = fields.Float(dump_only=True)

    # 管理员专用字段（仅在管理员查看时返回）
    has_password = fields.Bool(dump_only=True, allow_none=True)

class TransferSchema(Schema):
    alias = fields.Str(validate=validate.Length(max=50), required=True, load_only=True)
    to = fields.Str(validate=validate.Length(max=50), required=True, load_only=True)
    amount = fields.Float(required=True, load_only=True)

class RemoveStakeSchema(Schema):
    coldkey_name = fields.Str(validate=validate.Length(max=50), required=True, load_only=True)
    amount = fields.Float(required=True, load_only=True)

# =====================
# 钱包密码管理Schema
# =====================

class WalletPasswordSetSchema(Schema):
    """单个钱包密码设置Schema"""
    coldkey_name = fields.Str(validate=validate.Length(max=50), required=True, load_only=True)
    password = fields.Str(required=True, load_only=True)

class WalletPasswordBatchSchema(Schema):
    """批量钱包密码设置Schema"""
    passwords = fields.List(
        fields.Nested(WalletPasswordSetSchema),
        required=True,
        validate=validate.Length(min=1, max=100)  # 限制批量操作数量
    )

class WalletPasswordResultSchema(Schema):
    """单个密码设置结果Schema"""
    coldkey_name = fields.Str(validate=validate.Length(max=50), dump_only=True)
    success = fields.Bool(dump_only=True)
    error = fields.Str(dump_only=True, allow_none=True)

class WalletPasswordBatchResultSchema(Schema):
    """批量密码设置结果Schema"""
    results = fields.List(fields.Nested(WalletPasswordResultSchema), dump_only=True)
    total = fields.Int(dump_only=True)
    success_count = fields.Int(dump_only=True)
    failure_count = fields.Int(dump_only=True)
