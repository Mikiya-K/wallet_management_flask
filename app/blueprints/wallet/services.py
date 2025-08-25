import bittensor
import asyncio
from flask import current_app
from app.models.user import User
from app.models.wallet import Wallet
from app.utils.wallet_db import get_coldkey_wallets_for_path, insert_wallets_to_db
from app.utils.wallet_crypto import WalletPasswordCrypto
from app.utils.blockchain import get_wallets_balances, transfer, remove_stake
from app.errors.custom_errors import ResourceNotFoundError, WalletNotFoundError, BlockchainError, TransferFailedError, RemoveStakeError, WalletPasswordSetError, WalletPasswordError
from app.extensions import logger

class Wallet_http:
    def __init__(self, coldkey_name, coldkey_address, free, staked, total,
                 has_password=None):
        self.coldkey_name = coldkey_name
        self.coldkey_address = coldkey_address
        self.free = free
        self.staked = staked
        self.total = total
        # 管理员专用字段
        self.has_password = has_password

class WalletService:
    @staticmethod
    def sync_wallets_from_filesystem():
        """
        从文件系统同步钱包到数据库
        """
        # 获取钱包路径
        wallet_path = current_app.config['BITTENSOR_WALLET_PATH']

        # 从文件系统读取钱包
        filesystem_wallets = get_coldkey_wallets_for_path(wallet_path)

        logger.info(f"开始同步钱包，从路径 {wallet_path} 发现 {len(filesystem_wallets)} 个钱包")

        # 直接调用已有的函数
        insert_wallets_to_db(filesystem_wallets)

        logger.info("钱包同步完成")

    @staticmethod
    def get_wallets_for_user(user_id):
        user = User.find_by_id(user_id)

        if not user:
            raise ResourceNotFoundError("用户不存在")

        WalletService.sync_wallets_from_filesystem()

        # 判断用户权限，只做一次
        is_admin = user.has_role('admin')

        if is_admin:
            # 管理员可以查看所有钱包
            wallets = Wallet.query.all()
        else:
            wallets = user.wallets

        # 获取所有的 coldkey 地址
        coldkeys = [wallet.coldkey_address for wallet in wallets]

        # 异步获取所有钱包的自由余额和质押余额
        try:
            free_balances, staked_balances = asyncio.run(get_wallets_balances(coldkeys))
        except Exception as e:
            raise BlockchainError(f"Failed to get balances: {str(e)}")

        # 包装钱包信息
        wallets_list = []

        for wallet in wallets:
            name = wallet.coldkey_name
            coldkey = wallet.coldkey_address
            free = free_balances[coldkey].tao
            staked = staked_balances[coldkey][0].tao

            # 创建基础 Wallet 对象
            wallet_data = {
                'coldkey_name': name,
                'coldkey_address': coldkey,
                'free': free,
                'staked': staked,
                'total': free + staked
            }

            # 如果是管理员，添加密码状态信息
            if is_admin:
                wallet_data['has_password'] = wallet.has_password()

            wallet_obj = Wallet_http(**wallet_data)
            wallets_list.append(wallet_obj)

        return wallets_list

    @staticmethod
    def transfer(data):
        alias = data['alias']
        to = data['to']
        transfer_amount = data['amount']

        # 获取发送方和接收方钱包信息
        walletInfo = Wallet.find_by_name(alias)
        toInfo = Wallet.find_by_name(to)

        if walletInfo is None or toInfo is None:
            raise WalletNotFoundError

        # 获取接收方地址
        toAddress = toInfo.coldkey_address

        # 将 TAO 金额转换为 Bittensor 的 Balance 类型
        amount = bittensor.Balance.from_tao(transfer_amount)

        # 获取钱包密码（只能从数据库获取）
        if not walletInfo.has_password():
            logger.error(f"钱包 {alias} 未设置密码，无法执行转账操作")
            raise WalletPasswordError(f"钱包 {alias} 未设置密码，请先设置钱包密码")

        wallet_password = WalletPasswordCrypto.decrypt_password(walletInfo.encrypted_password, walletInfo.id)

        # 执行转账操作
        wallet_path = current_app.config['BITTENSOR_WALLET_PATH']
        wallet = bittensor.Wallet(name=alias, path=wallet_path)

        try:
            success = transfer(wallet, alias, toAddress, amount, wallet_password)
        except Exception as e:
            raise BlockchainError(f"Failed to transfer: {str(e)}")

        if success:
            result = f"成功从 {alias} 转账 {transfer_amount} TAO 到地址 {toAddress}。"
            logger.info("transfer", result if result is not None else "No result")
        else:
            raise TransferFailedError

    @staticmethod
    def remove_stake(data):
        alias = data['coldkey_name']
        remove_amount = data['amount']

        walletInfo = Wallet.find_by_name(alias)

        if walletInfo is None :
            raise WalletNotFoundError

        # 获取钱包密码（只能从数据库获取）
        if not walletInfo.has_password():
            logger.error(f"钱包 {alias} 未设置密码，无法执行解质押操作")
            raise WalletPasswordError(f"钱包 {alias} 未设置密码，请先设置钱包密码")

        wallet_password = WalletPasswordCrypto.decrypt_password(walletInfo.encrypted_password, walletInfo.id)

        # 执行解质押操作
        wallet_path = current_app.config['BITTENSOR_WALLET_PATH']
        wallet = bittensor.Wallet(name=alias, path=wallet_path)

        try:
            asyncio.run(remove_stake(wallet, alias, remove_amount, wallet_password))
        except Exception as e:
            raise BlockchainError(f"Failed to remove stake: {str(e)}")

class WalletPasswordService:
    """钱包密码管理服务"""

    @staticmethod
    def set_single_password(data: dict):
        """
        设置单个钱包密码（通过钱包名称）

        Args:
            data: 包含coldkey_name和password的字典

        Raises:
            ResourceNotFoundError: 钱包不存在
            WalletPasswordSetError: 密码设置失败
        """
        coldkey_name = data['coldkey_name']
        password = data['password']

        wallet = Wallet.find_by_name(coldkey_name)
        if not wallet:
            logger.error(f"钱包密码设置失败: 钱包 {coldkey_name} 不存在")
            raise ResourceNotFoundError(f"钱包 {coldkey_name} 不存在")

        if not wallet.set_password(password):
            logger.error(f"钱包 {coldkey_name} 密码设置失败")
            raise WalletPasswordSetError(f"钱包 {coldkey_name} 密码设置失败")

        logger.info(f"管理员成功设置钱包 {coldkey_name} 的密码")

    @staticmethod
    def set_batch_passwords(data: dict) -> dict:
        """
        批量设置钱包密码

        Args:
            data: 包含passwords列表的字典

        Returns:
            dict: 包含处理结果的字典
        """
        passwords = data['passwords']
        results = []
        success_count = 0
        failure_count = 0

        logger.info(f"开始批量设置 {len(passwords)} 个钱包的密码")

        for item in passwords:
            coldkey_name = item['coldkey_name']
            password = item['password']

            try:
                WalletPasswordService.set_single_password({
                    'coldkey_name': coldkey_name,
                    'password': password
                })
                results.append({
                    "coldkey_name": coldkey_name,
                    "success": True,
                    "error": None
                })
                success_count += 1

            except Exception as e:
                results.append({
                    "coldkey_name": coldkey_name,
                    "success": False,
                    "error": str(e)
                })
                failure_count += 1
                logger.warning(f"钱包 {coldkey_name} 密码设置失败: {e}")

        result_summary = {
            "results": results,
            "total": len(passwords),
            "success_count": success_count,
            "failure_count": failure_count
        }

        logger.info(f"批量密码设置完成: 总数 {len(passwords)}, 成功 {success_count}, 失败 {failure_count}")
        return result_summary
