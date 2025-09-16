import bittensor
import asyncio
from flask import current_app
from app.models.user import User
from app.models.wallet import Wallet
from app.models.miners import Miners
from app.models.miners_to_reg import MinersToReg
from app.models.external_wallet import ExternalWallet
from app.models.transfer_record import TransferRecord
from app.utils.wallet_db import get_coldkey_wallets_for_path, insert_wallets_to_db, get_hotkey_wallets_for_path, insert_hotkeys_to_db
from app.utils.wallet_crypto import WalletPasswordCrypto
from app.utils.blockchain import get_wallets_balances, transfer, remove_stake
from app.errors.custom_errors import ResourceNotFoundError, WalletNotFoundError, BlockchainError, TransferFailedError, WalletPasswordSetError, WalletPasswordError, MinerRegistrationError
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

        # 从文件系统读取hotkeys
        filesystem_hotkeys = get_hotkey_wallets_for_path(wallet_path)

        logger.info(f"开始同步hotkeys，从路径 {wallet_path} 发现 {len(filesystem_hotkeys)} 个hotkeys")

        # 直接调用已有的函数
        insert_hotkeys_to_db(filesystem_hotkeys)

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
    def transfer(user_id, data):
        alias = data['alias']
        to = data['to']
        transfer_amount = data['amount']

        # 获取操作人信息
        operator = User.find_by_id(user_id)
        if not operator:
            raise ResourceNotFoundError("操作用户不存在")

        # 获取发送方和接收方钱包信息
        walletInfo = Wallet.find_by_name(alias)
        toInfo = Wallet.find_by_address(to)

        if walletInfo is None or toInfo is None:
            raise WalletNotFoundError

        # 获取接收方地址
        toAddress = toInfo.coldkey_address

        # 获取转账前余额
        balance_before = TransferRecordService.get_wallet_balance(walletInfo.coldkey_address)
        if balance_before is None:
            logger.warning(f"无法获取钱包 {alias} 的余额，但继续执行转账")
            # 不终止转账，继续执行，但余额字段将为None

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

            # 获取转账后余额
            balance_after = TransferRecordService.get_wallet_balance(walletInfo.coldkey_address)
            # 如果获取转账后余额失败，保持为None

            if success:
                result = f"成功从 {alias} 转账 {transfer_amount} TAO 到地址 {toAddress}。"
                logger.info("transfer", result if result is not None else "No result")

                # 记录成功转账
                TransferRecordService.create_record(
                    operator_username=operator.name,
                    from_wallet_name=alias,
                    from_wallet_address=walletInfo.coldkey_address,
                    to_wallet_name=toInfo.coldkey_name,  # 本地钱包名称
                    to_wallet_address=toAddress,
                    amount=transfer_amount,
                    transfer_type='local',
                    balance_before=balance_before,
                    balance_after=balance_after,
                    status='success',
                    result_message=result
                )
            else:
                # 记录失败转账
                TransferRecordService.create_record(
                    operator_username=operator.name,
                    from_wallet_name=alias,
                    from_wallet_address=walletInfo.coldkey_address,
                    to_wallet_name=toInfo.coldkey_name,
                    to_wallet_address=toAddress,
                    amount=transfer_amount,
                    transfer_type='local',
                    balance_before=balance_before,
                    balance_after=balance_before,  # 失败时余额不变
                    status='failed',
                    error_message="Transfer failed"
                )
                raise TransferFailedError

        except Exception as e:
            # 记录异常转账
            TransferRecordService.create_record(
                operator_username=operator.name,
                from_wallet_name=alias,
                from_wallet_address=walletInfo.coldkey_address,
                to_wallet_name=toInfo.coldkey_name,
                to_wallet_address=toAddress,
                amount=transfer_amount,
                transfer_type='local',
                balance_before=balance_before,
                balance_after=balance_before,  # 异常时余额不变
                status='failed',
                error_message=str(e)
            )

            if isinstance(e, (BlockchainError, WalletPasswordError, TransferFailedError)):
                raise
            else:
                raise BlockchainError(f"Failed to transfer: {str(e)}")

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

class MinerService:
    @staticmethod
    def get_miners_for_user(user_id):
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

        # 使用关系查询获取所有miners
        miners = []
        for wallet in wallets:
            miners.extend(wallet.miners)

        # 转换miners数据为Schema需要的格式，并附加注册信息
        miners_data = []
        for miner in miners:
            miner_dict = {
                'id': miner.id,
                'wallet': miner.wallet,
                'name': miner.name,
                'hotkey': miner.hotkey,
                'registrations': [reg.to_dict() for reg in miner.registrations]  # 直接使用关系
            }
            miners_data.append(miner_dict)

        return miners_data

    @staticmethod
    def register_miner(data):
        miner_id = data['miner_id']
        subnet = data['subnet']
        network = data['network']
        max_fee = data['max_fee']
        start_time = data['start_time'] if 'start_time' in data else None
        end_time = data['end_time'] if 'end_time' in data else None

        miner = Miners.find_by_id(miner_id)
        if not miner:
            raise ResourceNotFoundError(f"矿工 {miner_id} 不存在")

        # 创建注册记录
        try:
            MinersToReg.create(miner_id, subnet, network, max_fee, start_time, end_time)
        except Exception as e:
            raise MinerRegistrationError(f"创建注册记录失败: {e}")

    @staticmethod
    def register_miners_batch(data):
        """
        批量注册矿工

        Args:
            data: 包含registrations列表的字典
        """
        registrations = data['registrations']
        results = []
        success_count = 0
        failure_count = 0

        logger.info(f"开始批量注册 {len(registrations)} 个矿工")

        for item in registrations:
            miner_id = item['miner_id']

            try:
                MinerService.register_miner(item)
                results.append({
                    "miner_id": miner_id,
                    "success": True,
                    "error": None
                })
                success_count += 1

            except Exception as e:
                results.append({
                    "miner_id": miner_id,
                    "success": False,
                    "error": str(e)
                })
                failure_count += 1
                logger.warning(f"矿工 {miner_id} 注册失败: {e}")

        result_summary = {
            "results": results,
            "total": len(registrations),
            "success_count": success_count,
            "failure_count": failure_count
        }

        logger.info(f"批量矿工注册完成: 总数 {len(registrations)}, 成功 {success_count}, 失败 {failure_count}")
        return result_summary


class ExternalWalletService:
    """外部钱包管理服务"""

    @staticmethod
    def get_all_external_wallets():
        """获取所有外部钱包列表"""
        external_wallets = ExternalWallet.get_all_active()
        return [wallet.to_dict() for wallet in external_wallets]

    @staticmethod
    def create_external_wallet(data):
        """创建外部钱包"""
        name = data['name']
        address = data['address']

        # 检查地址是否已存在
        existing_wallet = ExternalWallet.find_by_address(address)
        if existing_wallet:
            raise ResourceNotFoundError(f"地址 {address} 已存在")

        try:
            external_wallet = ExternalWallet.create(name, address)
            logger.info(f"成功创建外部钱包: {name} ({address})")
            return external_wallet.to_dict()
        except Exception as e:
            logger.error(f"创建外部钱包失败: {e}")
            raise ResourceNotFoundError(f"创建外部钱包失败: {e}")

    @staticmethod
    def update_external_wallet(wallet_id, data):
        """更新外部钱包"""
        external_wallet = ExternalWallet.find_by_id(wallet_id)
        if not external_wallet:
            raise ResourceNotFoundError(f"外部钱包 {wallet_id} 不存在")

        name = data.get('name')
        address = data.get('address')

        # 如果要更新地址，检查新地址是否已存在
        if address and address != external_wallet.address:
            existing_wallet = ExternalWallet.find_by_address(address)
            if existing_wallet:
                raise ResourceNotFoundError(f"地址 {address} 已存在")

        try:
            external_wallet.update(name=name, address=address)
            logger.info(f"成功更新外部钱包 {wallet_id}: {external_wallet.name}")
            return external_wallet.to_dict()
        except Exception as e:
            logger.error(f"更新外部钱包失败: {e}")
            raise ResourceNotFoundError(f"更新外部钱包失败: {e}")

    @staticmethod
    def delete_external_wallet(wallet_id):
        """删除外部钱包（软删除）"""
        external_wallet = ExternalWallet.find_by_id(wallet_id)
        if not external_wallet:
            raise ResourceNotFoundError(f"外部钱包 {wallet_id} 不存在")

        try:
            external_wallet.delete()
            logger.info(f"成功删除外部钱包 {wallet_id}: {external_wallet.name}")
        except Exception as e:
            logger.error(f"删除外部钱包失败: {e}")
            raise ResourceNotFoundError(f"删除外部钱包失败: {e}")

    @staticmethod
    def transfer_to_external(user_id, data):
        """向外部钱包转账"""
        from_wallet = data['from_wallet']
        to_address = data['to_address']
        transfer_amount = data['amount']

        # 获取操作人信息
        operator = User.find_by_id(user_id)
        if not operator:
            raise ResourceNotFoundError("操作用户不存在")

        # 检查外部钱包地址是否存在
        external_wallet = ExternalWallet.find_by_address(to_address)
        if not external_wallet:
            raise ResourceNotFoundError(f"外部钱包地址 {to_address} 不存在")

        # 获取发送方钱包信息
        wallet_info = Wallet.find_by_name(from_wallet)
        if not wallet_info:
            raise WalletNotFoundError(f"发送方钱包 {from_wallet} 不存在")

        # 获取转账前余额
        balance_before = TransferRecordService.get_wallet_balance(wallet_info.coldkey_address)
        if balance_before is None:
            logger.warning(f"无法获取钱包 {from_wallet} 的余额，但继续执行转账")
            # 不终止转账，继续执行，但余额字段将为None

        # 检查钱包密码
        if not wallet_info.has_password():
            logger.error(f"钱包 {from_wallet} 未设置密码，无法执行转账操作")
            raise WalletPasswordError(f"钱包 {from_wallet} 未设置密码，请先设置钱包密码")

        # 获取钱包密码
        wallet_password = WalletPasswordCrypto.decrypt_password(wallet_info.encrypted_password, wallet_info.id)

        # 将 TAO 金额转换为 Bittensor 的 Balance 类型
        amount = bittensor.Balance.from_tao(transfer_amount)

        # 执行转账操作
        wallet_path = current_app.config['BITTENSOR_WALLET_PATH']
        wallet = bittensor.Wallet(name=from_wallet, path=wallet_path)

        try:
            success = transfer(wallet, from_wallet, to_address, amount, wallet_password)

            # 获取转账后余额
            balance_after = TransferRecordService.get_wallet_balance(wallet_info.coldkey_address)
            # 如果获取转账后余额失败，保持为None

            if success:
                result = f"成功从 {from_wallet} 转账 {transfer_amount} TAO 到外部钱包 {external_wallet.name} ({to_address})"
                logger.info("transfer", result if result is not None else "No result")

                # 记录成功转账
                TransferRecordService.create_record(
                    operator_username=operator.name,
                    from_wallet_name=from_wallet,
                    from_wallet_address=wallet_info.coldkey_address,
                    to_wallet_name=external_wallet.name,  # 外部钱包备注
                    to_wallet_address=to_address,
                    amount=transfer_amount,
                    transfer_type='external',
                    balance_before=balance_before,
                    balance_after=balance_after,
                    status='success',
                    result_message=result
                )
            else:
                # 记录失败转账
                TransferRecordService.create_record(
                    operator_username=operator.name,
                    from_wallet_name=from_wallet,
                    from_wallet_address=wallet_info.coldkey_address,
                    to_wallet_name=external_wallet.name,
                    to_wallet_address=to_address,
                    amount=transfer_amount,
                    transfer_type='external',
                    balance_before=balance_before,
                    balance_after=balance_before,  # 失败时余额不变
                    status='failed',
                    error_message="Transfer failed"
                )
                raise TransferFailedError

        except Exception as e:
            # 记录异常转账
            TransferRecordService.create_record(
                operator_username=operator.name,
                from_wallet_name=from_wallet,
                from_wallet_address=wallet_info.coldkey_address,
                to_wallet_name=external_wallet.name,
                to_wallet_address=to_address,
                amount=transfer_amount,
                transfer_type='external',
                balance_before=balance_before,
                balance_after=balance_before,  # 异常时余额不变
                status='failed',
                error_message=str(e)
            )

            if isinstance(e, (BlockchainError, WalletPasswordError, TransferFailedError)):
                raise
            else:
                raise BlockchainError(f"Failed to transfer: {str(e)}")


class TransferRecordService:
    """转账记录管理服务"""

    @staticmethod
    def create_record(operator_username, from_wallet_name, from_wallet_address,
                     to_wallet_address, amount, transfer_type, to_wallet_name,
                     balance_before=None, balance_after=None, status='success',
                     result_message=None, error_message=None):
        """创建转账记录"""
        try:
            record = TransferRecord.create(
                operator_username=operator_username,
                from_wallet_name=from_wallet_name,
                from_wallet_address=from_wallet_address,
                to_wallet_name=to_wallet_name,
                to_wallet_address=to_wallet_address,
                amount=amount,
                transfer_type=transfer_type,
                balance_before=balance_before,
                balance_after=balance_after,
                status=status,
                result_message=result_message,
                error_message=error_message
            )
            logger.info(f"转账记录创建成功: {operator_username} {from_wallet_name} -> {to_wallet_address} ({amount} TAO)")
            return record
        except Exception as e:
            logger.error(f"创建转账记录失败: {e}")
            # 转账记录创建失败不应该影响转账操作，只记录错误
            return None

    @staticmethod
    def get_records_for_user(user_id, page, page_size):
        """获取转账记录（根据用户权限返回相应数据）"""
        user = User.find_by_id(user_id)
        if not user:
            raise ResourceNotFoundError("用户不存在")

        # 判断用户权限，只做一次
        is_admin = user.has_role('admin')

        if is_admin:
            # 管理员可以查看所有转账记录
            query = TransferRecord.query.order_by(TransferRecord.created_at.desc())
        else:
            # 普通用户只能查看自己的转账记录
            query = TransferRecord.query.filter_by(operator_username=user.name).order_by(TransferRecord.created_at.desc())

        records = query.paginate(
            page=page,
            per_page=page_size,
            error_out=False
        )

        return {
            "total": records.total,
            "items": records.items
        }

    @staticmethod
    def get_wallet_balance(wallet_address):
        """获取单个钱包的余额"""
        try:
            # 使用现有的get_wallets_balances函数
            free_balances, staked_balances = asyncio.run(get_wallets_balances([wallet_address]))

            # 获取自由余额
            free_balance = free_balances.get(wallet_address)
            if free_balance:
                return float(free_balance.tao)
            else:
                logger.warning(f"无法获取钱包 {wallet_address} 的余额")
                return None

        except Exception as e:
            logger.error(f"获取钱包余额失败: {e}")
            return None
