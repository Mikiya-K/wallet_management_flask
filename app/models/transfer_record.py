from datetime import datetime
from app.extensions import db

class TransferRecord(db.Model):
    """转账记录模型"""
    __tablename__ = 'transfer_records'

    id = db.Column(db.Integer, primary_key=True)
    operator_username = db.Column(db.String(50), nullable=False, index=True, comment='操作人账户名')

    # 转出钱包信息
    from_wallet_name = db.Column(db.String(50), nullable=False, index=True, comment='转出钱包名称')
    from_wallet_address = db.Column(db.String(48), nullable=False, comment='转出钱包地址')

    # 转入钱包信息
    to_wallet_name = db.Column(db.String(100), nullable=False, comment='转入钱包名称（外部钱包为备注，本地钱包为钱包名）')
    to_wallet_address = db.Column(db.String(48), nullable=False, comment='转入钱包地址')

    # 转账信息
    amount = db.Column(db.Numeric(20, 9), nullable=False, comment='转账数量（TAO）')

    # 余额信息
    balance_before = db.Column(db.Numeric(20, 9), nullable=True, comment='转出钱包操作前余额')
    balance_after = db.Column(db.Numeric(20, 9), nullable=True, comment='转出钱包操作后余额')

    # 操作结果
    status = db.Column(db.String(20), nullable=False, index=True, comment='操作状态：success/failed')
    result_message = db.Column(db.Text, nullable=True, comment='操作结果详细信息')
    error_message = db.Column(db.Text, nullable=True, comment='失败时的错误信息')

    # 转账类型
    transfer_type = db.Column(db.String(20), nullable=False, index=True, comment='转账类型：local/external')

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True, comment='操作时间')

    def __init__(self, operator_username, from_wallet_name, from_wallet_address,
                 to_wallet_address, amount, transfer_type, to_wallet_name,
                 balance_before=None, balance_after=None, status='success',
                 result_message=None, error_message=None):
        self.operator_username = operator_username
        self.from_wallet_name = from_wallet_name
        self.from_wallet_address = from_wallet_address
        self.to_wallet_name = to_wallet_name
        self.to_wallet_address = to_wallet_address
        self.amount = amount
        self.transfer_type = transfer_type
        self.balance_before = balance_before
        self.balance_after = balance_after
        self.status = status
        self.result_message = result_message
        self.error_message = error_message

    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'operator_username': self.operator_username,
            'from_wallet_name': self.from_wallet_name,
            'from_wallet_address': self.from_wallet_address,
            'to_wallet_name': self.to_wallet_name,
            'to_wallet_address': self.to_wallet_address,
            'amount': str(self.amount) if self.amount else None,
            'balance_before': str(self.balance_before) if self.balance_before else None,
            'balance_after': str(self.balance_after) if self.balance_after else None,
            'status': self.status,
            'result_message': self.result_message,
            'error_message': self.error_message,
            'transfer_type': self.transfer_type,
            'created_at': self.created_at
        }

    def save(self):
        """保存到数据库"""
        db.session.add(self)
        db.session.commit()

    @classmethod
    def create(cls, operator_username, from_wallet_name, from_wallet_address,
               to_wallet_address, amount, transfer_type, to_wallet_name,
               balance_before=None, balance_after=None, status='success',
               result_message=None, error_message=None):
        """创建转账记录"""
        record = cls(
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
        record.save()
        return record

    def __repr__(self):
        return f'<TransferRecord {self.operator_username}: {self.from_wallet_name} -> {self.to_wallet_address} ({self.amount} TAO)>'
