"""
钱包密码加密/解密工具类
使用AES-256-GCM加密算法和基于钱包ID的PBKDF2密钥派生
"""

import base64
import secrets
from flask import current_app
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from app.extensions import logger


class WalletCryptoError(Exception):
    """钱包加密/解密异常"""
    pass


class WalletPasswordCrypto:
    """钱包密码加密/解密服务类"""

    # AES-256-GCM 密钥长度
    KEY_LENGTH = 32  # 256 bits

    # PBKDF2 默认迭代次数
    DEFAULT_ITERATIONS = 100000

    # 随机数长度
    NONCE_LENGTH = 12  # GCM 推荐的 nonce 长度

    # 盐值长度
    SALT_LENGTH = 16

    @classmethod
    def _get_master_key(cls) -> bytes:
        """获取主密钥"""
        master_key = current_app.config.get('WALLET_MASTER_KEY')
        if not master_key:
            raise WalletCryptoError("WALLET_MASTER_KEY 未配置")

        # 如果是字符串，转换为字节
        if isinstance(master_key, str):
            master_key = master_key.encode('utf-8')

        return master_key

    @classmethod
    def _get_iterations(cls) -> int:
        """获取PBKDF2迭代次数"""
        return current_app.config.get('WALLET_PBKDF2_ITERATIONS', cls.DEFAULT_ITERATIONS)

    @classmethod
    def _derive_key(cls, wallet_id: int, salt: bytes) -> bytes:
        """
        基于钱包ID和盐值派生加密密钥

        Args:
            wallet_id: 钱包ID
            salt: 盐值

        Returns:
            派生的32字节密钥
        """
        try:
            # 获取主密钥
            master_key = cls._get_master_key()

            # 将钱包ID转换为固定长度的字节并与主密钥组合
            # 使用固定长度避免不同ID产生相似的密钥材料
            wallet_id_bytes = wallet_id.to_bytes(8, byteorder='big')  # 8字节固定长度
            key_material = master_key + b':wallet:' + wallet_id_bytes

            # 使用PBKDF2派生密钥
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=cls.KEY_LENGTH,
                salt=salt,
                iterations=cls._get_iterations(),
                backend=default_backend()
            )

            derived_key = kdf.derive(key_material)
            logger.debug(f"为钱包 {wallet_id} 派生密钥成功")

            return derived_key

        except Exception as e:
            logger.error(f"密钥派生失败: {e}")
            raise WalletCryptoError(f"密钥派生失败: {e}")

    @classmethod
    def encrypt_password(cls, password: str, wallet_id: int) -> str:
        """
        加密钱包密码

        Args:
            password: 要加密的密码
            wallet_id: 钱包ID

        Returns:
            Base64编码的加密数据 (格式: salt:nonce:ciphertext)
        """
        try:
            if not password:
                raise WalletCryptoError("密码不能为空")

            # 生成随机盐值和nonce
            salt = secrets.token_bytes(cls.SALT_LENGTH)
            nonce = secrets.token_bytes(cls.NONCE_LENGTH)

            # 派生密钥
            key = cls._derive_key(wallet_id, salt)

            # 使用AES-GCM加密
            aesgcm = AESGCM(key)
            password_bytes = password.encode('utf-8')
            ciphertext = aesgcm.encrypt(nonce, password_bytes, None)

            # 组合数据: salt + nonce + ciphertext
            encrypted_data = salt + nonce + ciphertext

            # Base64编码
            encoded_data = base64.b64encode(encrypted_data).decode('utf-8')

            logger.info(f"钱包 {wallet_id} 密码加密成功")

            # 清理内存中的敏感数据
            # 注意：Python中无法完全保证内存清理，这只是尽力而为
            if 'key' in locals():
                key = None
            if 'password_bytes' in locals():
                password_bytes = None

            return encoded_data

        except Exception as e:
            logger.error(f"密码加密失败: {e}")
            raise WalletCryptoError(f"密码加密失败: {e}")

    @classmethod
    def decrypt_password(cls, encrypted_data: str, wallet_id: int) -> str:
        """
        解密钱包密码

        Args:
            encrypted_data: Base64编码的加密数据
            wallet_id: 钱包ID

        Returns:
            解密后的密码
        """
        try:
            if not encrypted_data:
                raise WalletCryptoError("加密数据不能为空")

            # Base64解码
            try:
                data = base64.b64decode(encrypted_data.encode('utf-8'))
            except Exception as e:
                raise WalletCryptoError(f"Base64解码失败: {e}")

            # 检查数据长度
            min_length = cls.SALT_LENGTH + cls.NONCE_LENGTH + 16  # 16是GCM标签长度
            if len(data) < min_length:
                raise WalletCryptoError("加密数据格式错误")

            # 分离数据
            salt = data[:cls.SALT_LENGTH]
            nonce = data[cls.SALT_LENGTH:cls.SALT_LENGTH + cls.NONCE_LENGTH]
            ciphertext = data[cls.SALT_LENGTH + cls.NONCE_LENGTH:]

            # 派生密钥
            key = cls._derive_key(wallet_id, salt)

            # 使用AES-GCM解密
            aesgcm = AESGCM(key)
            password_bytes = aesgcm.decrypt(nonce, ciphertext, None)

            # 转换为字符串
            password = password_bytes.decode('utf-8')

            logger.info(f"钱包 {wallet_id} 密码解密成功")

            # 清理内存中的敏感数据
            # 注意：Python中无法完全保证内存清理，这只是尽力而为
            if 'key' in locals():
                key = None
            if 'password_bytes' in locals():
                password_bytes = None

            return password

        except Exception as e:
            logger.error(f"密码解密失败: {e}")
            raise WalletCryptoError(f"密码解密失败: {e}")

    @classmethod
    def verify_password(cls, password: str, encrypted_data: str, wallet_id: int) -> bool:
        """
        验证密码是否正确

        Args:
            password: 要验证的密码
            encrypted_data: 存储的加密数据
            wallet_id: 钱包ID

        Returns:
            密码是否正确
        """
        try:
            decrypted_password = cls.decrypt_password(encrypted_data, wallet_id)
            return password == decrypted_password
        except Exception:
            return False
