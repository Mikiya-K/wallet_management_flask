#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
矿工注册后台服务程序
基于Django数据库配置，定期查询miners_to_reg表并处理注册逻辑
"""

import os
import sys
import time
import signal
import logging
import threading
import random
from typing import List, Dict, Any
from dotenv import load_dotenv

from sqlalchemy.exc import OperationalError, InterfaceError, DatabaseError

# Bittensor相关导入
import bittensor as bt
from bittensor.core.subtensor import Subtensor
from bittensor import SubnetHyperparameters
from bittensor_wallet import Wallet

# 添加项目路径到sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
console_root = os.path.dirname(os.path.dirname(project_root))  # 向上两级到项目根目录
sys.path.insert(0, console_root)

# 数据库连接
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 加载环境变量
load_dotenv(os.path.join(console_root, '.env'))

# 获取数据库配置
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

def create_database_url(database_name):
    """基于 DATABASE_URL 创建指定数据库的连接URL"""
    return f"{DATABASE_URL}/{database_name}"

# 创建主数据库连接 (wallet_management)
main_database_url = create_database_url('wallet_management')
main_engine = create_engine(main_database_url)
MainSession = sessionmaker(bind=main_engine)
db_session = MainSession()

# 创建 metagraph 数据库连接
metagraph_database_url = create_database_url('metagraph')
metagraph_engine = create_engine(metagraph_database_url)
MetagraphSession = sessionmaker(bind=metagraph_engine)
metagraph_session = MetagraphSession()

# 导入加密相关库
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

# 基础区块配置
BASE_BLOCK = {
    18: int(os.getenv('BASE_BLOCK_18', '2720320')),
    22: int(os.getenv('BASE_BLOCK_22', '2807542')),
    41: int(os.getenv('BASE_BLOCK_41', '4177902')),
    180: int(os.getenv('BASE_BLOCK_180', '3514065')),
    44: int(os.getenv('BASE_BLOCK_44', '3550319')),
    4: int(os.getenv('BASE_BLOCK_4', '5282253')),
    172: int(os.getenv('BASE_BLOCK_172', '4177902'))
}

# 配置日志
import os
log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'miner_register.log'))
        # 移除StreamHandler，避免与PM2日志重复
    ]
)
logger = logging.getLogger(__name__)


class MinerRegistrationService:
    """
    矿工注册服务类
    """

    def __init__(self, check_interval: int = 15):
        """
        初始化注册服务

        Args:
            check_interval: 检查间隔时间（秒），默认15秒
        """
        self.check_interval = check_interval
        self.running = False
        self.thread = None

    def start(self):
        """
        启动注册服务
        """
        if self.running:
            logger.warning("注册服务已经在运行中")
            return

        self.running = True
        self.thread = threading.Thread(target=self._run_service, daemon=True)
        self.thread.start()
        logger.info(f"矿工注册服务已启动，检查间隔: {self.check_interval}秒")

    def stop(self):
        """
        停止注册服务
        """
        if not self.running:
            logger.warning("注册服务未在运行")
            return

        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        logger.info("矿工注册服务已停止")

    def _run_service(self):
        """
        运行注册服务主循环
        """
        logger.info("注册服务开始")

        while self.running:
            try:
                # 查询需要注册的矿工
                pending_registrations = self._get_pending_registrations()
            except (OperationalError, InterfaceError, DatabaseError) as e:
                logger.error(f"数据库连接异常，程序即将退出: {e}")
                logger.error("等待外部管理程序重启...")
                os._exit(1)
            except Exception as e:
                logger.warning(f"查询需要注册的矿工异常: {e}")
                time.sleep(30)
                break

            if pending_registrations:
                logger.info(f"发现 {len(pending_registrations)} 个待注册的矿工")
                self._process_registration(pending_registrations)
            else:
                logger.info("没有发现待注册的矿工")

            # 等待下一次检查
            logger.info(f"等待 {self.check_interval} 秒后再次检查")
            time.sleep(self.check_interval)

        logger.info("注册服务结束")

    def _get_pending_registrations(self) -> List[dict]:
        """
        获取待注册的矿工记录

        Returns:
            待注册的MinersToReg记录列表
        """
        try:
            # 查询条件: registered = 0 且 is_deleted = 0 且 (当前时间 > start_time 或 start_time 为 null)
            query = text("""
                SELECT r.*, m.name as miner_name, m.wallet, m.hotkey
                FROM miners_to_reg r
                JOIN miners m ON r.miners_id = m.id
                WHERE (r.registered = 0 OR r.registered IS NULL)
                AND r.is_deleted = 0
                AND (r.start_time < NOW() OR r.start_time IS NULL)
                AND (r.end_time > NOW() OR r.end_time IS NULL)
            """)

            result = db_session.execute(query)
            pending_regs = [dict(row._mapping) for row in result]

            return pending_regs

        except (OperationalError, InterfaceError, DatabaseError):
            # 数据库连接异常，向上传播给主循环处理
            raise
        except Exception as e:
            logger.error(f"查询待注册矿工时出错: {e}")
            return []

    def _check_hotkey_not_registered(self, hotkey, netuid):
        """
        检查hotkey是否在注册黑名单中
        如果在黑名单中则返回False，否则返回True
        """
        try:
            # 查询regblacklist表中是否存在该hotkey
            query = text("SELECT COUNT(*) FROM regblacklist WHERE subnet = :netuid AND hotkey = :hotkey")
            result = metagraph_session.execute(query, {'netuid': netuid, 'hotkey': hotkey}).scalar()

            # 如果COUNT为0，说明不在黑名单中，返回True
            # 如果COUNT大于0，说明在黑名单中，返回False
            return result == 0

        except Exception as e:
            logger.error(f"检查hotkey黑名单状态时出错: {e}")
            # 出错时默认返回True，允许注册
            return True

    # 执行注册
    def _process_registration(self, pending_registrations: List[dict]):
        if not pending_registrations:
            return

        # 按网络分组处理
        networks_groups = {}
        for reg_record in pending_registrations:
            network = reg_record['network']
            if network not in networks_groups:
                networks_groups[network] = []
            networks_groups[network].append(reg_record)

        # 为每个网络创建独立的连接和处理
        for network, network_registrations in networks_groups.items():
            logger.info(f"处理网络 {network} 的 {len(network_registrations)} 个注册请求")
            self._process_network_registrations(network, network_registrations)

    def _process_network_registrations(self, network: str, pending_registrations: List[dict]):
        """处理特定网络的注册请求"""
        wallets = {}

        logger.info(f"创建Subtensor连接用于注册，网络: {network}")
        subtensor = Subtensor(network=network)

        for reg_record in pending_registrations:
            if not self.running:
                break

            try:
                # 获取矿工信息和配置
                miner_name = reg_record['miner_name']
                wallet_name = reg_record['wallet']
                hotkey = reg_record['hotkey']
                netuid = reg_record['subnet']

                logger.info(f"🔐 开始打开钱包: ID={reg_record['id']}, "
                           f"Miner={miner_name}, Wallet={wallet_name}, "
                           f"Hotkey={hotkey}, Netuid={netuid}")

                wallet = Wallet(name=wallet_name, hotkey=miner_name)

                # 从数据库获取钱包密码
                password = self._get_wallet_password(wallet_name)
                coldkey = wallet.get_coldkey(password=password)
                wallet.set_coldkey(keypair=coldkey, overwrite=False, save_coldkey_to_env=False)
                hotkey_key = f"{wallet_name}-{miner_name}-{hotkey}"
                wallets[hotkey_key] = wallet

                if not self._check_hotkey_not_registered(hotkey, netuid):
                    logger.warning(f"🈲 此 hotkey 禁止在子网 {netuid} 注册")
                    # 更新数据库状态为已删除
                    self._mark_registration_deleted(reg_record)
                    # 从待注册列表中移除
                    if hotkey_key in wallets:
                        del wallets[hotkey_key]
                    continue

                if subtensor.is_hotkey_registered(netuid=netuid, hotkey_ss58=hotkey):
                    logger.warning(f"ℹ️ 此 hotkey 已注册 {hotkey}")
                    # 更新数据库状态为已注册
                    self._update_registration_status(reg_record, True)
                    # 从待注册列表中移除
                    if hotkey_key in wallets:
                        del wallets[hotkey_key]
            except Exception as e:
                logger.error(f"处理注册记录 {reg_record['id']} 时出错: {e}")

        if len(wallets) > 0:
            logger.info(f"当前有 {len(wallets)} 个矿工待注册")

            # 按子网分组处理
            subnet_groups = {}
            for reg_record in pending_registrations:
                netuid = reg_record['subnet']
                if netuid not in subnet_groups:
                    subnet_groups[netuid] = []
                subnet_groups[netuid].append(reg_record)

            # 为每个子网执行注册逻辑
            for netuid, subnet_registrations in subnet_groups.items():
                logger.info(f"处理子网 {netuid} 的 {len(subnet_registrations)} 个注册请求")

                # 按max_fee分组，相同max_fee的一起处理
                fee_groups = {}
                for reg_record in subnet_registrations:
                    max_fee = reg_record['max_fee']
                    if max_fee not in fee_groups:
                        fee_groups[max_fee] = []
                    fee_groups[max_fee].append(reg_record)

                # 为每个费用组检查注册条件
                for max_fee, fee_registrations in fee_groups.items():
                    logger.info(f"检查子网 {netuid} 费用组 max_fee={max_fee} 的 {len(fee_registrations)} 个注册请求")

                    if self._wait_register(subtensor, netuid, BASE_BLOCK, max_fee, wallets):
                        logger.info(f"子网 {netuid} 费用组 max_fee={max_fee} 注册条件满足，开始执行注册")
                        self._execute_registration(subtensor, netuid, wallets, fee_registrations)
                    else:
                        logger.info(f"子网 {netuid} 费用组 max_fee={max_fee} 注册条件不满足，等待下一轮")
        else:
            logger.info("当前没有待注册的矿工")

    def _get_wallet_password(self, wallet_name: str) -> str:
        """从数据库获取钱包密码"""
        try:
            # 查询钱包记录
            query = text("SELECT id, encrypted_password FROM wallets WHERE coldkey_name = :wallet_name")
            result = db_session.execute(query, {'wallet_name': wallet_name}).fetchone()

            if not result:
                logger.error(f"未找到钱包: {wallet_name}")
                raise Exception(f"未找到钱包: {wallet_name}")

            wallet_id, encrypted_password = result

            if not encrypted_password:
                logger.error(f"钱包 {wallet_name} 未设置密码")
                raise Exception(f"钱包 {wallet_name} 未设置密码")

            # 解密密码 - 使用独立的解密方法，不依赖Flask应用上下文
            password = self._decrypt_wallet_password(encrypted_password, wallet_id)
            logger.info(f"成功获取钱包 {wallet_name} 的密码")

            return password

        except Exception as e:
            logger.error(f"获取钱包 {wallet_name} 密码失败: {e}")
            raise

    def _decrypt_wallet_password(self, encrypted_data: str, wallet_id: int) -> str:
        """
        独立的密码解密方法，不依赖Flask应用上下文
        直接从环境变量获取配置
        """
        try:
            # 从环境变量获取配置
            master_key = os.getenv('WALLET_MASTER_KEY')
            if not master_key:
                raise Exception("WALLET_MASTER_KEY 环境变量未配置")

            iterations = int(os.getenv('WALLET_PBKDF2_ITERATIONS', '100000'))

            # 常量定义
            KEY_LENGTH = 32  # 256 bits
            SALT_LENGTH = 16
            NONCE_LENGTH = 12

            if not encrypted_data:
                raise Exception("加密数据不能为空")

            # Base64解码
            try:
                data = base64.b64decode(encrypted_data.encode('utf-8'))
            except Exception as e:
                raise Exception(f"Base64解码失败: {e}")

            # 检查数据长度
            min_length = SALT_LENGTH + NONCE_LENGTH + 16  # 16是GCM标签长度
            if len(data) < min_length:
                raise Exception("加密数据格式错误")

            # 分离数据
            salt = data[:SALT_LENGTH]
            nonce = data[SALT_LENGTH:SALT_LENGTH + NONCE_LENGTH]
            ciphertext = data[SALT_LENGTH + NONCE_LENGTH:]

            # 派生密钥
            master_key_bytes = master_key.encode('utf-8')
            wallet_id_bytes = wallet_id.to_bytes(8, byteorder='big')
            key_material = master_key_bytes + b':wallet:' + wallet_id_bytes

            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=KEY_LENGTH,
                salt=salt,
                iterations=iterations,
                backend=default_backend()
            )
            key = kdf.derive(key_material)

            # 使用AES-GCM解密
            aesgcm = AESGCM(key)
            password_bytes = aesgcm.decrypt(nonce, ciphertext, None)

            # 转换为字符串
            password = password_bytes.decode('utf-8')

            logger.debug(f"钱包 {wallet_id} 密码解密成功")
            return password

        except Exception as e:
            logger.error(f"密码解密失败: {e}")
            raise Exception(f"密码解密失败: {e}")

    def _get_last_interval_boot_block(self, subtensor: bt.subtensor, base_boot_block: int, cur_block: int, netuid: int):
        """获取上一个区间开始的block"""
        subnetInfo: SubnetHyperparameters = subtensor.get_subnet_hyperparameters(
            netuid=netuid, block=cur_block
        )
        diff_blocks = cur_block - base_boot_block
        past_blocks = diff_blocks % subnetInfo.adjustment_interval
        return cur_block - past_blocks

    def _wait_register(self, subtensor, netuid: int, BASE_BLOCK: dict, max_fee: float, wallets: dict) -> bool:
        """等待注册条件满足"""
        if netuid not in BASE_BLOCK:
            logger.warning(f"子网 {netuid} 未配置基础区块，跳过注册")
            return False
        base_boot_block = BASE_BLOCK[netuid]
        cur_block = subtensor.get_current_block()
        subnetInfo: SubnetHyperparameters = subtensor.get_subnet_hyperparameters(netuid=netuid, block=cur_block)
        MAX_REGISTRATION_COUNT_PER_INTERVAL = subnetInfo.target_regs_per_interval * 3
        time.sleep(1)
        estimate_recycle = 0
        recycle = subtensor.recycle(netuid=netuid, block=cur_block)

        for hotkey_key in wallets.keys():
            logger.debug(f"{hotkey_key} wait to register")
        lastblock = 0

        # 满足注册条件
        if recycle.tao <= max_fee:
            last_interval_boot_block = self._get_last_interval_boot_block(subtensor=subtensor, base_boot_block=base_boot_block, cur_block=cur_block, netuid=netuid)
            reg_number = self._query_register_events_count_by_netuid(netuid, last_interval_boot_block, cur_block)
            logger.debug(f"current_recycle less than max_fee {recycle} {max_fee} reg Num {reg_number} less than 3 start to reg")
            if reg_number < 3:
                return True

        while True:
            time.sleep(1)
            cur_block = subtensor.get_current_block()
            roundBlock = (cur_block - base_boot_block) % subnetInfo.adjustment_interval
            roundNum = int((cur_block - base_boot_block) / subnetInfo.adjustment_interval)

            if cur_block > lastblock:
                logger.debug(f"max_fee {max_fee} wait cur {cur_block} round {roundNum} block {roundBlock} recycle {recycle}")

            lastblock = cur_block
            if roundBlock == (359 - 2) and estimate_recycle <= 0:  # launchFrom = 359
                last_interval_boot_block = self._get_last_interval_boot_block(subtensor=subtensor, base_boot_block=base_boot_block, cur_block=cur_block, netuid=netuid)
                reg_number = self._query_register_events_count_by_netuid(netuid, last_interval_boot_block, cur_block)
                recycle = subtensor.recycle(netuid=netuid, block=cur_block)
                estimate_recycle = self._estimate_next_recycle(netuid, reg_number, recycle.tao, MAX_REGISTRATION_COUNT_PER_INTERVAL)
                logger.debug(f"estimate_recycle {estimate_recycle}")

            if roundBlock == 359 and recycle.tao > 0:  # launchFrom = 359
                if estimate_recycle <= max_fee:
                    logger.debug(f"estimate_recycle less than max_fee {estimate_recycle} {max_fee} start to reg")
                    return True
                else:
                    logger.debug(f"estimate_recycle big than max_fee {estimate_recycle} {max_fee} wait next round")
                    return False

    def _estimate_next_recycle(self, netuid: int, reg_num: int, cur_recycle: float, max_reg_limit: int) -> float:
        """估算下一轮回收费用"""
        recycly_rate = {
            18: [0.786, 1.0, 1.106, 1.428571],
            19: [0.9, 1.0, 1.1, 1.2],
            22: [1.0, 1.0, 1.0, 1.0],
            41: [1.0, 1.0, 1.0, 1.0],
            180: [0.5, 1.0, 1.5, 2],
            172: [0.5, 1.0, 1.5, 2],  # 添加测试网netuid
        }

        estimate_recycle = None
        if reg_num == 0:
            estimate_recycle = cur_recycle * recycly_rate[netuid][0]
        elif reg_num <= max_reg_limit / 3:
            estimate_recycle = cur_recycle * recycly_rate[netuid][1]
        elif reg_num > max_reg_limit / 3 and reg_num <= max_reg_limit * 2 / 3:
            estimate_recycle = cur_recycle * recycly_rate[netuid][2]
        elif reg_num > max_reg_limit * 2 / 3 and reg_num <= max_reg_limit:
            estimate_recycle = cur_recycle * recycly_rate[netuid][3]

        estimateValue = estimate_recycle if netuid != 41 else max(0.25, estimate_recycle)
        logger.debug(f"EstimateNextRecycle: {netuid}, reg_num {reg_num} miners, cur_recycle {cur_recycle} max_reg_limit {max_reg_limit} estimate_recycle {estimateValue}")
        return estimateValue

    def _query_register_events_count_by_netuid(self, netuid: int, beg_block: int, end_block: int) -> int:
        """查询注册事件数量"""
        try:
            query = text("SELECT COUNT(*) FROM regevents WHERE subnet = :netuid AND block BETWEEN :beg_block AND :end_block")
            result = metagraph_session.execute(query, {
                'netuid': netuid,
                'beg_block': beg_block,
                'end_block': end_block
            }).scalar()
            return result if result else 0
        except Exception as e:
            logger.error(f"查询注册事件数量时出错: {e}")
            return 0

    def _execute_registration(self, subtensor, netuid: int, wallets: dict, pending_registrations: List[dict]):
        """执行注册逻辑"""

        logger.info(f"开始执行顺序注册，共 {len(wallets)} 个钱包")

        i = 0
        # 创建键的副本以避免在迭代过程中修改字典
        wallet_keys = list(wallets.keys())

        # 从注册记录中获取网络信息
        network = pending_registrations[0]['network'] if pending_registrations else 'test'

        for hotkey_key in wallet_keys:
            self._reg_worker_sequential(hotkey_key, network, netuid, wallets, pending_registrations)
            i += 1
            # 注册间隔延迟，避免速率限制
            if i < len(wallet_keys):
                time.sleep(5)  # 每次注册间隔5秒

        logger.info("顺序注册完成")

    def _reg_worker_sequential(self, hotkey_key: str, network: str, netuid: int, wallets: dict, pending_registrations: List[dict]):
        """顺序注册工作方法"""

        if hotkey_key in wallets.keys():
            wallet = wallets[hotkey_key]
            # 创建独立的subtensor连接
            thread_subtensor = None
            try:
                logger.info(f"{hotkey_key} 开始注册")

                # 创建subtensor连接
                thread_subtensor = Subtensor(network=network)

                # 执行燃烧注册
                result = thread_subtensor.burned_register(wallet=wallet, netuid=int(netuid))

                if result:
                    logger.info(f"✅ {hotkey_key} 注册成功！返回信息: {result}")
                    # 更新数据库状态
                    self._update_wallet_registration_status(hotkey_key, pending_registrations, True)
                    # 从待注册列表中移除
                    if hotkey_key in wallets:
                        del wallets[hotkey_key]
                else:
                    logger.warning(f"❌ {hotkey_key} 注册失败，返回信息: {result}")
                    self._update_wallet_registration_status(hotkey_key, pending_registrations, False)

            except Exception as err:
                logger.error(f"⚠️ {hotkey_key} 注册异常: {err}")
                self._update_wallet_registration_status(hotkey_key, pending_registrations, False)
            finally:
                # 清理subtensor连接
                if thread_subtensor:
                    try:
                        thread_subtensor.close()
                    except:
                        pass
        else:
            logger.warning(f"{hotkey_key} 注册错误：找不到钱包热键")

    def _reg_worker(self, i: int, hotkey_key: str, network: str, netuid: int, wallets: dict, pending_registrations: List[dict], launch_delay: int):
        """注册工作线程"""

        # 计算延迟时间
        delay = launch_delay + i * 20  # 增加线程间延迟以避免速率限制
        if i == 0:
            delay = delay + random.randint(-200, 100) / 100
        elif i == 1:
            delay = delay + random.randint(0, 200) / 100
        else:
            delay = delay + random.randint(0, 200) / 100

        logger.debug(f"{hotkey_key} {i} register delay {delay}")
        time.sleep(delay)

        if hotkey_key in wallets.keys():
            wallet = wallets[hotkey_key]
            # 为每个线程创建独立的subtensor连接
            thread_subtensor = None
            try:
                logger.info(f"{hotkey_key} 开始注册")

                # 创建线程专用的subtensor连接
                thread_subtensor = Subtensor(network=network)

                # 执行燃烧注册
                result = thread_subtensor.burned_register(wallet=wallet, netuid=int(netuid))

                if result:
                    logger.info(f"✅ {hotkey_key} 注册成功！返回信息: {result}")
                    # 更新数据库状态
                    self._update_wallet_registration_status(hotkey_key, pending_registrations, True)
                    # 从待注册列表中移除
                    if hotkey_key in wallets:
                        del wallets[hotkey_key]
                else:
                    logger.warning(f"❌ {hotkey_key} 注册失败，返回信息: {result}")
                    self._update_wallet_registration_status(hotkey_key, pending_registrations, False)

            except Exception as err:
                logger.error(f"⚠️ {hotkey_key} 注册异常: {err}")
                self._update_wallet_registration_status(hotkey_key, pending_registrations, False)
            finally:
                # 清理线程专用的subtensor连接
                if thread_subtensor:
                    try:
                        thread_subtensor.close()
                    except:
                        pass
        else:
            logger.warning(f"{hotkey_key} 注册错误：找不到钱包热键")

    def _update_wallet_registration_status(self, hotkey_key: str, pending_registrations: List[dict], success: bool):
        """更新钱包注册状态"""
        try:
            # 从hotkey_key解析出钱包信息
            parts = hotkey_key.split('-')
            if len(parts) >= 3:
                wallet_name = parts[0]
                miner_name = parts[1]
                hotkey_addr = parts[2]

                # 查找对应的注册记录
                for reg_record in pending_registrations:
                    if (reg_record['wallet'] == wallet_name and
                        reg_record['miner_name'] == miner_name and
                        reg_record['hotkey'] == hotkey_addr):

                        self._update_registration_status(reg_record, success)
                        break

        except Exception as e:
            logger.error(f"更新钱包注册状态时出错: {e}")

    def _update_registration_status(self, reg_record: dict, success: bool):
        """
        更新注册状态

        Args:
            reg_record: 注册记录字典
            success: 注册是否成功
        """
        try:
            if success:
                query = text("""
                    UPDATE miners_to_reg
                    SET registered = 1, registered_time = NOW()
                    WHERE id = :id
                """)
            else:
                query = text("""
                    UPDATE miners_to_reg
                    SET registered = 0
                    WHERE id = :id
                """)

            db_session.execute(query, {'id': reg_record['id']})
            db_session.commit()

        except Exception as e:
            db_session.rollback()
            logger.error(f"更新注册状态时出错: {e}")

    def _mark_registration_deleted(self, reg_record: dict):
        """
        标记注册记录为已删除

        Args:
            reg_record: 注册记录字典
        """
        try:
            query = text("UPDATE miners_to_reg SET is_deleted = 1 WHERE id = :id")
            db_session.execute(query, {'id': reg_record['id']})
            db_session.commit()
            logger.info(f"已将注册记录 {reg_record['id']} 标记为删除")
        except Exception as e:
            db_session.rollback()
            logger.error(f"更新注册记录 {reg_record['id']} 删除状态时出错: {e}")

    def get_status(self) -> Dict[str, Any]:
        """
        获取服务状态

        Returns:
            服务状态信息
        """
        return {
            'running': self.running,
            'check_interval': self.check_interval,
            'thread_alive': self.thread.is_alive() if self.thread else False
        }



def signal_handler(signum, frame):
    """
    信号处理器，用于优雅关闭服务
    """
    logger.info(f"接收到信号 {signum}，准备关闭服务...")
    global service
    if service:
        service.stop()
    sys.exit(0)

def test_database_connection():
    """
    测试数据库连接
    """
    logger.info("测试数据库连接...")

    try:
        # 测试数据库连接
        logger.info("📡 数据库连接成功")

        # 测试查询
        miners_count = db_session.execute(text("SELECT COUNT(*) FROM miners")).scalar()
        reg_count = db_session.execute(text("""
            SELECT COUNT(*) FROM miners_to_reg
            WHERE (registered = 0 OR registered IS NULL) AND is_deleted = 0
        """)).scalar()
        pending_count = db_session.execute(text("""
            SELECT COUNT(*) FROM miners_to_reg
            WHERE (registered = 0 OR registered IS NULL) AND is_deleted = 0
            AND (start_time < NOW() OR start_time IS NULL)
            AND (end_time > NOW() OR end_time IS NULL)
        """)).scalar()

        logger.info(f"[数据库统计] Miners 总数: {miners_count}, "
                   f"待注册总数: {reg_count}, 当前待注册: {pending_count}")

    except Exception as e:
        logger.error(f"数据库连接测试失败: {e}")
        return False

    return True

def main():
    """
    主函数
    """
    logger.info("矿工注册服务启动中...")

    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 测试数据库连接
    if not test_database_connection():
        logger.error("数据库连接失败，服务退出")
        sys.exit(1)

    # 创建并启动注册服务
    global service
    service = MinerRegistrationService(check_interval=15)
    service.start()

    try:
        # 保持主线程运行
        while service.running:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("接收到键盘中断，关闭服务...")
    finally:
        service.stop()
        logger.info("矿工注册服务已关闭")



if __name__ == '__main__':
    main()
