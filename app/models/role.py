from app.extensions import db

class Role(db.Model):
    """角色模型"""
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # 多对多用户关系
    users = db.relationship(
        'User',
        secondary='user_roles',
        back_populates='roles',
        lazy='select'
    )

    def __init__(self, name, description=None):
        self.name = name
        self.description = description

    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def save(self):
        """保存角色到数据库"""
        db.session.add(self)
        db.session.commit()

    def delete(self):
        """删除角色"""
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def find_by_name(cls, name):
        """通过名称查找角色"""
        return cls.query.filter_by(name=name).first()

    @classmethod
    def get_default_role(cls):
        """
        获取默认角色（'user'角色）
        """
        default_role_name = "user"
        role = cls.find_by_name(default_role_name)
        return role
