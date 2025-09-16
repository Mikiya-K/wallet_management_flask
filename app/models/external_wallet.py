from datetime import datetime
from app.extensions import db

class ExternalWallet(db.Model):
    """外部钱包模型"""
    __tablename__ = 'external_wallets'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, comment='钱包备注名称')
    address = db.Column(db.String(48), nullable=False, unique=True, index=True, comment='钱包地址')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    def __init__(self, name, address):
        self.name = name
        self.address = address

    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    def save(self):
        """保存到数据库"""
        db.session.add(self)
        db.session.commit()

    def delete(self):
        """软删除外部钱包"""
        self.is_active = False
        db.session.commit()

    def hard_delete(self):
        """硬删除外部钱包"""
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def create(cls, name, address):
        """创建外部钱包"""
        external_wallet = cls(
            name=name,
            address=address
        )
        external_wallet.save()
        return external_wallet

    @classmethod
    def find_by_id(cls, wallet_id):
        """通过ID查找外部钱包"""
        return cls.query.filter_by(id=wallet_id, is_active=True).first()

    @classmethod
    def find_by_address(cls, address):
        """通过地址查找外部钱包"""
        return cls.query.filter_by(address=address, is_active=True).first()

    @classmethod
    def find_by_name(cls, name):
        """通过名称查找外部钱包"""
        return cls.query.filter_by(name=name, is_active=True).first()

    @classmethod
    def get_all_active(cls):
        """获取所有活跃的外部钱包"""
        return cls.query.filter_by(is_active=True).order_by(cls.name).all()

    def update(self, name=None, address=None):
        """更新外部钱包信息"""
        if name is not None:
            self.name = name
        if address is not None:
            self.address = address

        self.updated_at = datetime.utcnow()
        db.session.commit()

    def __repr__(self):
        return f'<ExternalWallet {self.name}: {self.address}>'
