from flask import current_app
from datetime import datetime
from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from .user_role import UserRole  # 导入关联表模型

class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    failed_login_attempts = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    wallets = db.relationship('Wallet', back_populates='user', lazy='select')

    # 多对多角色关系
    roles = db.relationship(
        'Role',
        secondary='user_roles',
        back_populates='users',
        lazy='select'
    )

    @property
    def password(self):
        """防止直接访问密码"""
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        """设置密码并自动哈希"""
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)

    def has_role(self, role_name):
        """检查用户是否有指定角色"""
        return any(ur.name == role_name for ur in self.roles)

    def add_role(self, role):
        """为用户添加角色"""
        if not self.has_role(role.name):
            UserRole.assign_role(self.id, role.id)

    def add_wallet(self, wallet):
        """为用户添加钱包"""
        self.wallets.append(wallet)

    def remove_role(self):
        """移除用户的角色"""
        for user_role in self.roles[:]:
            self.roles.remove(user_role)

    def remove_wallet(self):
        """移除用户的钱包"""
        for wallet in self.wallets[:]:
            wallet.user_id = None
            self.wallets.remove(wallet)

    def lock_account(self):
        """锁定账户"""
        self.is_active = False
        db.session.commit()

    def unlock_account(self):
        """解锁账户"""
        self.is_active = True
        self.failed_login_attempts = 0
        db.session.commit()

    def record_login_success(self):
        """记录成功登录"""
        self.last_login = datetime.utcnow()
        self.failed_login_attempts = 0
        db.session.commit()

    def record_login_failure(self):
        """记录失败登录"""
        self.failed_login_attempts += 1
        db.session.commit()

        if self.failed_login_attempts >= current_app.config['MAX_LOGIN_ATTEMPTS']:
            self.lock_account()
            return False
        return True

    def to_dict(self, include_relationships=True):
        """转换为字典格式"""
        data = {
            #'id': self.id,
            'name': self.name
        }

        if include_relationships:
            data["roles"] = [role.name for role in self.roles]
            data["wallets"] = [wallet.coldkey_name for wallet in self.wallets]

        return data

    def save(self):
        """保存用户"""
        db.session.add(self)
        if not self.roles:
            self.assign_default_role()
        db.session.commit()

    def assign_default_role(self):
        """分配默认角色"""
        from .role import Role
        default_role = Role.get_default_role()
        if default_role:
            self.add_role(default_role)

    def delete(self):
        """删除用户（软删除）"""
        self.is_active = False

    @classmethod
    def create(cls, name, password):
        """创建新用户"""
        user = cls(
            name=name,
            password=password,
        )
        user.save()
        return user

    @classmethod
    def find_by_id(cls, user_id):
        """通过ID查找用户"""
        return cls.query.get(user_id)

    @classmethod
    def find_by_name(cls, name):
        """通过name查找用户"""
        return cls.query.filter(cls.name == name).first()
