from app.extensions import db

class UserRole(db.Model):
    """用户角色关联模型"""
    __tablename__ = 'user_roles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # 唯一约束，确保每个用户每个角色只有一个关联
    __table_args__ = (
        db.UniqueConstraint('user_id', 'role_id', name='uq_user_role'),
    )

    def __init__(self, user_id, role_id):
        self.user_id = user_id
        self.role_id = role_id

    def save(self):
        """保存关联到数据库"""
        db.session.add(self)
        db.session.commit()

    @classmethod
    def assign_role(cls, user_id, role_id):
        """为用户分配角色"""
        assignment = cls.query.filter_by(user_id=user_id, role_id=role_id).first()
        if not assignment:
            assignment = cls(user_id=user_id, role_id=role_id)
            assignment.save()

    @classmethod
    def remove_role(cls, user_id, role_id):
        """移除用户的角色"""
        assignment = cls.query.filter_by(user_id=user_id, role_id=role_id).first()
        if assignment:
            db.session.delete(assignment)
            db.session.commit()
