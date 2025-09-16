# 导入所有模型以确保它们被Flask-Migrate检测到
from .user import User
from .role import Role
from .user_role import UserRole
from .wallet import Wallet
from .miners import Miners
from .miners_to_reg import MinersToReg
from .external_wallet import ExternalWallet
from .transfer_record import TransferRecord

__all__ = ['User', 'Role', 'UserRole', 'Wallet', 'Miners', 'MinersToReg', 'ExternalWallet', 'TransferRecord']
