from datetime import datetime
from app.extensions import db


class Miners(db.Model):
    """矿工信息模型"""
    __tablename__ = 'miners'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, comment='矿工名称')
    wallet = db.Column(db.String(50), nullable=False, comment='钱包名称')
    hotkey = db.Column(db.String(48), nullable=False, comment='hotkey')
    coldkey_id = db.Column(db.Integer, db.ForeignKey('wallets.id'), nullable=True, comment='关联的钱包ID')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    registrations = db.relationship('MinersToReg', back_populates='miner', lazy='select')
    coldkey_wallet = db.relationship('Wallet', back_populates='miners', lazy='select')

    def __init__(self, name, wallet, hotkey, coldkey_id=None):
        self.name = name
        self.wallet = wallet
        self.hotkey = hotkey
        self.coldkey_id = coldkey_id

    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'wallet': self.wallet,
            'hotkey': self.hotkey,
            'coldkey_id': self.coldkey_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def save(self):
        """保存到数据库"""
        db.session.add(self)
        db.session.commit()

    def delete(self):
        """删除矿工"""
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def create(cls, name, wallet, hotkey, coldkey_id=None):
        """创建新矿工"""
        miner = cls(
            name=name,
            wallet=wallet,
            hotkey=hotkey,
            coldkey_id=coldkey_id
        )
        miner.save()
        return miner

    @classmethod
    def find_by_id(cls, miner_id):
        """通过ID查找矿工"""
        return cls.query.get(miner_id)

    @classmethod
    def find_by_hotkey(cls, hotkey):
        """通过hotkey查找矿工"""
        return cls.query.filter_by(hotkey=hotkey).first()

    @classmethod
    def find_by_wallet(cls, wallet):
        """通过钱包名称查找矿工"""
        return cls.query.filter_by(wallet=wallet).all()

    @classmethod
    def find_by_name(cls, name):
        """通过名称查找矿工"""
        return cls.query.filter_by(name=name).first()

    @classmethod
    def find_by_coldkey_id(cls, coldkey_id):
        """通过coldkey_id查找矿工"""
        return cls.query.filter_by(coldkey_id=coldkey_id).all()

    @classmethod
    def find_by_wallet_name(cls, wallet_name):
        """通过钱包名称查找矿工"""
        return cls.query.filter_by(wallet=wallet_name).all()

    @classmethod
    def find_by_coldkey_wallet(cls, coldkey_wallet):
        """通过 Wallet 对象查找对应的矿工列表"""
        return cls.query.filter_by(coldkey_id=coldkey_wallet.id).all()

    def __repr__(self):
        return f'<Miners {self.id}: name={self.name}, wallet={self.wallet}, hotkey={self.hotkey}, coldkey_id={self.coldkey_id}>'
