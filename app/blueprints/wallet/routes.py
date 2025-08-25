from flask_jwt_extended import jwt_required, get_jwt_identity
from . import wallet_bp
from .schemas import (
    WalletSchema, TransferSchema, RemoveStakeSchema,
    WalletPasswordSetSchema, WalletPasswordBatchSchema, WalletPasswordBatchResultSchema
)
from .services import WalletService, WalletPasswordService
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
    WalletService.transfer(data)

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
