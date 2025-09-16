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
    to = fields.Str(validate=validate.Length(equal=48), required=True, load_only=True)
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

class MinerRegistrationSchema(Schema):
    """矿工注册记录Schema"""
    id = fields.Int(dump_only=True)
    miners_id = fields.Int(dump_only=True)
    registered = fields.Int(dump_only=True, allow_none=True)
    status_text = fields.Str(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    start_time = fields.DateTime(dump_only=True, allow_none=True)
    registered_time = fields.DateTime(dump_only=True, allow_none=True)
    subnet = fields.Int(dump_only=True)
    end_time = fields.DateTime(dump_only=True, allow_none=True)
    uid = fields.Int(dump_only=True, allow_none=True)
    network = fields.Str(dump_only=True)
    max_fee = fields.Float(dump_only=True)

class MinerSchema(Schema):
    """矿工信息Schema"""
    id = fields.Int(dump_only=True)
    wallet = fields.Str(validate=validate.Length(max=50), dump_only=True)
    name = fields.Str(validate=validate.Length(max=100), dump_only=True)
    hotkey = fields.Str(validate=validate.Length(equal=48), dump_only=True)
    registrations = fields.List(fields.Nested(MinerRegistrationSchema), dump_only=True)

class MinerRegSchema(Schema):
    """矿工注册信息Schema"""
    miner_id = fields.Int(load_only=True)
    subnet = fields.Int(load_only=True)
    start_time = fields.DateTime(load_only=True, allow_none=True)
    end_time = fields.DateTime(load_only=True, allow_none=True)
    max_fee = fields.Float(load_only=True)
    network = fields.Str(validate=validate.OneOf(['local', 'test', 'finney', 'archive']), load_only=True)

class MinerRegBatchSchema(Schema):
    """批量矿工注册Schema"""
    registrations = fields.List(
        fields.Nested(MinerRegSchema),
        required=True,
        validate=validate.Length(min=1, max=100)  # 限制批量操作数量
    )

# =====================
# 外部钱包管理Schema
# =====================

class ExternalWalletSchema(Schema):
    """外部钱包信息Schema"""
    id = fields.Int(dump_only=True)
    name = fields.Str(validate=validate.Length(max=100), dump_only=True)
    address = fields.Str(validate=validate.Length(equal=48), dump_only=True)

class ExternalWalletCreateSchema(Schema):
    """创建外部钱包Schema"""
    name = fields.Str(validate=validate.Length(max=100), required=True, load_only=True)
    address = fields.Str(validate=validate.Length(equal=48), required=True, load_only=True)

class ExternalWalletUpdateSchema(Schema):
    """更新外部钱包Schema"""
    name = fields.Str(validate=validate.Length(max=100), required=True, load_only=True)
    address = fields.Str(validate=validate.Length(equal=48), required=True, load_only=True)

class ExternalTransferSchema(Schema):
    """向外部钱包转账Schema"""
    from_wallet = fields.Str(validate=validate.Length(max=50), required=True, load_only=True)
    to_address = fields.Str(validate=validate.Length(equal=48), required=True, load_only=True)
    amount = fields.Float(required=True, load_only=True)

# =====================
# 转账记录Schema
# =====================

class TransferRecordSchema(Schema):
    """转账记录Schema"""
    id = fields.Int(dump_only=True)
    operator_username = fields.Str(dump_only=True)
    from_wallet_name = fields.Str(dump_only=True)
    from_wallet_address = fields.Str(dump_only=True)
    to_wallet_name = fields.Str(dump_only=True)
    to_wallet_address = fields.Str(dump_only=True)
    amount = fields.Decimal(dump_only=True)
    balance_before = fields.Decimal(dump_only=True, allow_none=True)
    balance_after = fields.Decimal(dump_only=True, allow_none=True)
    status = fields.Str(dump_only=True)
    result_message = fields.Str(dump_only=True, allow_none=True)
    error_message = fields.Str(dump_only=True, allow_none=True)
    transfer_type = fields.Str(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
