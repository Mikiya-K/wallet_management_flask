from datetime import datetime
from app.extensions import db


class MinersToReg(db.Model):
    """矿工注册信息模型"""
    __tablename__ = 'miners_to_reg'

    id = db.Column(db.Integer, primary_key=True)
    miners_id = db.Column(db.Integer, db.ForeignKey('miners.id'), nullable=False, index=True)
    registered = db.Column(db.Integer, nullable=True, default=None)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_deleted = db.Column(db.Integer, nullable=False, default=0)
    start_time = db.Column(db.DateTime, nullable=True, comment='开始注册时间')
    registered_time = db.Column(db.DateTime, nullable=True, comment='注册成功时间')
    subnet = db.Column(db.Integer, nullable=False, comment='子网id')
    end_time = db.Column(db.DateTime, nullable=True, comment='注册的结束时间')
    uid = db.Column(db.Integer, nullable=True, comment='注册成功后记录的UID')
    network = db.Column(db.String(10), nullable=False, comment='网络名称')
    max_fee = db.Column(db.Float, nullable=False, comment='最多可接受注册费用')

    # 关系
    miner = db.relationship('Miners', back_populates='registrations', lazy='select')

    def __init__(self, miners_id, registered=None, start_time=None, subnet=None, end_time=None, network=None, max_fee=None):
        self.miners_id = miners_id
        self.registered = registered
        self.start_time = start_time
        self.subnet = subnet
        self.end_time = end_time
        self.network = network
        self.max_fee = max_fee

    def to_dict(self):
        """转换为字典格式 - 用于Schema序列化，保持datetime对象"""
        return {
            'id': self.id,
            'miners_id': self.miners_id,
            'registered': self.registered,
            'status_text': self.get_status_text(),  # 添加状态文本
            'created_at': self.created_at,  # 保持datetime对象
            'is_deleted': self.is_deleted,
            'start_time': self.start_time,  # 保持datetime对象
            'registered_time': self.registered_time,  # 保持datetime对象
            'subnet': self.subnet,
            'end_time': self.end_time,  # 保持datetime对象
            'uid': self.uid,
            'network': self.network,
            'max_fee': self.max_fee
        }

    def to_json_dict(self):
        """转换为JSON格式 - 用于直接返回，日期转为字符串"""
        return {
            'id': self.id,
            'miners_id': self.miners_id,
            'registered': self.registered,
            'status_text': self.get_status_text(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_deleted': self.is_deleted,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'registered_time': self.registered_time.isoformat() if self.registered_time else None,
            'subnet': self.subnet,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'uid': self.uid,
            'network': self.network,
            'max_fee': self.max_fee
        }

    def save(self):
        """保存到数据库"""
        db.session.add(self)
        db.session.commit()

    def delete(self):
        """软删除"""
        self.is_deleted = 1
        db.session.commit()

    def mark_registered(self, uid=None):
        """标记为已注册"""
        self.registered = 1
        self.registered_time = datetime.utcnow()
        if uid:
            self.uid = uid
        db.session.commit()

    def mark_failed(self):
        """标记为注册失败"""
        self.registered = 0
        db.session.commit()

    def get_status_text(self):
        """获取状态文本"""
        if self.registered is None:
            return "注册中"
        elif self.registered == 1:
            return "注册成功"
        elif self.registered == 0:
            return "注册失败"
        else:
            return "未知状态"

    @classmethod
    def create(cls, miners_id, subnet, network, max_fee, start_time=None, end_time=None):
        """创建新的矿工注册记录"""
        miner_reg = cls(
            miners_id=miners_id,
            subnet=subnet,
            network=network,
            max_fee=max_fee,
            start_time=start_time,
            end_time=end_time
        )
        miner_reg.save()

    @classmethod
    def find_by_miners_id(cls, miners_id):
        """根据矿工ID查找记录"""
        return cls.query.filter_by(miners_id=miners_id, is_deleted=0).all()

    @classmethod
    def find_active_registrations(cls):
        """查找所有活跃的注册记录"""
        return cls.query.filter_by(is_deleted=0).all()

    @classmethod
    def find_by_subnet(cls, subnet):
        """根据子网查找记录"""
        return cls.query.filter_by(subnet=subnet, is_deleted=0).all()

    def __repr__(self):
        return f'<MinersToReg {self.id}: miners_id={self.miners_id}, registered={self.registered}>'
