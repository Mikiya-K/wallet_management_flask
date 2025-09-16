from app.extensions import db
from app.utils.wallet_crypto import WalletPasswordCrypto, WalletCryptoError
from app.extensions import logger

class Wallet(db.Model):
    """钱包模型"""
    __tablename__ = 'wallets'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    coldkey_name = db.Column(db.String(50), nullable=False, unique=True, index=True)
    coldkey_address = db.Column(db.String(48), nullable=False, unique=True)

    # 加密密码字段
    encrypted_password = db.Column(db.Text, nullable=True)  # 存储加密后的密码

    # 关系
    user = db.relationship('User', back_populates='wallets', lazy='select')
    miners = db.relationship('Miners', back_populates='coldkey_wallet', lazy='select')

    def save(self):
        """保存钱包到数据库"""
        db.session.add(self)
        db.session.commit()

    @classmethod
    def create(cls, coldkey_name, coldkey_address, user_id=None):
        """创建钱包"""
        user = cls(
            coldkey_name=coldkey_name,
            coldkey_address=coldkey_address,
            user_id=user_id
        )
        user.save()
        return user

    @classmethod
    def find_by_name(cls, coldkey_name):
        """通过coldkey_name查找钱包"""
        return cls.query.filter(cls.coldkey_name == coldkey_name).first()

    @classmethod
    def find_by_address(cls, coldkey_address):
        """通过coldkey_address查找钱包"""
        return cls.query.filter(cls.coldkey_address == coldkey_address).first()

    @classmethod
    def find_by_user(cls, user_id):
        """查找用户的所有钱包"""
        return cls.query.filter(cls.user_id == user_id).all()

    # =====================
    # 密码管理方法
    # =====================

    def set_password(self, password: str) -> bool:
        """
        设置钱包密码

        Args:
            password: 要设置的密码

        Returns:
            bool: 设置成功返回True，失败返回False
        """
        try:
            if not password:
                logger.error(f"钱包 {self.id} 设置密码失败: 密码不能为空")
                return False

            # 加密密码
            encrypted_password = WalletPasswordCrypto.encrypt_password(password, self.id)
            self.encrypted_password = encrypted_password

            # 保存到数据库
            db.session.commit()

            logger.info(f"钱包 {self.id} ({self.coldkey_name}) 密码设置成功")
            return True

        except WalletCryptoError as e:
            logger.error(f"钱包 {self.id} 密码加密失败: {e}")
            db.session.rollback()
            return False
        except Exception as e:
            logger.error(f"钱包 {self.id} 设置密码时发生未知错误: {e}")
            db.session.rollback()
            return False

    def verify_password(self, password: str) -> bool:
        """
        验证钱包密码

        Args:
            password: 要验证的密码

        Returns:
            bool: 密码正确返回True，错误返回False
        """
        try:
            if not self.has_password():
                logger.warning(f"钱包 {self.id} ({self.coldkey_name}) 未设置密码")
                return False

            if not password:
                logger.warning(f"钱包 {self.id} 密码验证失败: 输入密码为空")
                return False

            # 解密存储的密码并比较
            stored_password = WalletPasswordCrypto.decrypt_password(
                self.encrypted_password, self.id
            )

            is_valid = stored_password == password

            if is_valid:
                logger.debug(f"钱包 {self.id} ({self.coldkey_name}) 密码验证成功")
            else:
                logger.warning(f"钱包 {self.id} ({self.coldkey_name}) 密码验证失败")

            return is_valid

        except WalletCryptoError as e:
            logger.error(f"钱包 {self.id} 密码解密失败: {e}")
            return False
        except Exception as e:
            logger.error(f"钱包 {self.id} 验证密码时发生未知错误: {e}")
            return False

    def has_password(self) -> bool:
        """
        检查钱包是否设置了密码

        Returns:
            bool: 已设置密码返回True，未设置返回False
        """
        return self.encrypted_password is not None and self.encrypted_password.strip() != ""
