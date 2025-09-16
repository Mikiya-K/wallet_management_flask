from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import wallet_bp
from .schemas import (
    WalletSchema, TransferSchema, RemoveStakeSchema,
    WalletPasswordSetSchema, WalletPasswordBatchSchema, WalletPasswordBatchResultSchema,
    MinerSchema, MinerRegSchema, MinerRegBatchSchema,
    ExternalWalletSchema, ExternalWalletCreateSchema, ExternalWalletUpdateSchema, ExternalTransferSchema
)
from .services import WalletService, WalletPasswordService, MinerService, ExternalWalletService, TransferRecordService
from app.utils.decorators import admin_required

@wallet_bp.route('', methods=['GET'])
@wallet_bp.response(200, WalletSchema(many=True))
@jwt_required()
def get_wallets_for_user():
    user_id = int(get_jwt_identity())
    wallets = WalletService.get_wallets_for_user(user_id)
    return wallets

@wallet_bp.route('', methods=['POST'])
@wallet_bp.arguments(TransferSchema)
@wallet_bp.response(200)
@jwt_required()
def transfer(data):
    user_id = int(get_jwt_identity())
    WalletService.transfer(user_id, data)

@wallet_bp.route('', methods=['PUT'])
@wallet_bp.arguments(RemoveStakeSchema)
@wallet_bp.response(200)
@jwt_required()
def remove_stake(data):
    WalletService.remove_stake(data)

# =====================
# 钱包密码管理API
# =====================

@wallet_bp.route('/password', methods=['PUT'])
@wallet_bp.arguments(WalletPasswordSetSchema)
@wallet_bp.response(200)
@jwt_required()
@admin_required
def set_wallet_password(data):
    """设置单个钱包密码（仅管理员）"""
    WalletPasswordService.set_single_password(data)

@wallet_bp.route('/password/batch', methods=['PUT'])
@wallet_bp.arguments(WalletPasswordBatchSchema)
@wallet_bp.response(200, WalletPasswordBatchResultSchema)
@jwt_required()
@admin_required
def set_wallets_password_batch(data):
    """批量设置钱包密码（仅管理员）"""
    result = WalletPasswordService.set_batch_passwords(data)
    return result

@wallet_bp.route('/sync', methods=['POST'])
@wallet_bp.response(200)
@jwt_required()
@admin_required
def sync_wallets():
    """从文件系统同步钱包到数据库（仅管理员）"""
    WalletService.sync_wallets_from_filesystem()

@wallet_bp.route('/miners', methods=['GET'])
@wallet_bp.response(200, MinerSchema(many=True))
@jwt_required()
def get_miners_for_user():
    """获取矿工信息"""
    user_id = int(get_jwt_identity())
    miners = MinerService.get_miners_for_user(user_id)
    return miners

@wallet_bp.route('/miners', methods=['POST'])
@wallet_bp.arguments(MinerRegSchema)
@wallet_bp.response(200)
@jwt_required()
def register_miner(data):
    """注册矿工"""
    MinerService.register_miner(data)

@wallet_bp.route('/miners/batch', methods=['POST'])
@wallet_bp.arguments(MinerRegBatchSchema)
@wallet_bp.response(200)
@jwt_required()
def register_miners_batch(data):
    """批量注册矿工"""
    MinerService.register_miners_batch(data)


# =====================
# 外部钱包管理API
# =====================

@wallet_bp.route('/external', methods=['GET'])
@wallet_bp.response(200, ExternalWalletSchema(many=True))
@jwt_required()
@admin_required
def get_external_wallets():
    """获取外部钱包列表（仅管理员）"""
    wallets = ExternalWalletService.get_all_external_wallets()
    return wallets

@wallet_bp.route('/external', methods=['POST'])
@wallet_bp.arguments(ExternalWalletCreateSchema)
@wallet_bp.response(200, ExternalWalletSchema)
@jwt_required()
@admin_required
def create_external_wallet(data):
    """创建外部钱包（仅管理员）"""
    wallet = ExternalWalletService.create_external_wallet(data)
    return wallet

@wallet_bp.route('/external/<int:wallet_id>', methods=['PUT'])
@wallet_bp.arguments(ExternalWalletUpdateSchema)
@wallet_bp.response(200, ExternalWalletSchema)
@jwt_required()
@admin_required
def update_external_wallet(data, wallet_id):
    """更新外部钱包（仅管理员）"""
    wallet = ExternalWalletService.update_external_wallet(wallet_id, data)
    return wallet

@wallet_bp.route('/external/<int:wallet_id>', methods=['DELETE'])
@wallet_bp.response(200)
@jwt_required()
@admin_required
def delete_external_wallet(wallet_id):
    """删除外部钱包（仅管理员）"""
    ExternalWalletService.delete_external_wallet(wallet_id)

@wallet_bp.route('/external/transfer', methods=['POST'])
@wallet_bp.arguments(ExternalTransferSchema)
@wallet_bp.response(200)
@jwt_required()
@admin_required
def transfer_to_external_wallet(data):
    """向外部钱包转账（仅管理员）"""
    user_id = int(get_jwt_identity())
    ExternalWalletService.transfer_to_external(user_id, data)

# =====================
# 转账记录API
# =====================

@wallet_bp.route('/transfer-records', methods=['GET'])
@wallet_bp.paginate()
@jwt_required()
def get_transfer_records(pagination_parameters):
    """获取转账记录（根据用户权限返回相应数据）"""
    user_id = int(get_jwt_identity())
    records = TransferRecordService.get_records_for_user(user_id, pagination_parameters.page, pagination_parameters.page_size)
    pagination_parameters.item_count = records['total']

    # 序列化转账记录
    serialized_records = [record.to_dict() for record in records['items']]

    return jsonify({
        "transfer_records": serialized_records,
    }), 200
