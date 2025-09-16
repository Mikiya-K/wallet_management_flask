import datetime
from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token
from app.extensions import logger
from app.models.user import User
from app.errors.custom_errors import AuthException, AccountLockedError

class AuthService:
    @staticmethod
    def register_user(name, password):
        """注册新用户"""
        if User.find_by_name(name):
            raise AuthException("用户名已被注册")
        user = User.create(
            name=name,
            password=password
        )

        logger.info(f"User {name} registered successfully")
        return user

    @staticmethod
    def authenticate_user(name, password):
        """认证用户并返回用户对象"""
        user = User.find_by_name(name)

        # 检查账户是否存在
        if not user:
            raise AuthException("Invalid name or password")

        # 检查账户是否锁定
        if not user.is_active:
            raise AccountLockedError("Account is locked")

        # 验证密码
        if not user.verify_password(password):
            # 记录登录失败
            if not user.record_login_failure():
                raise AccountLockedError("Account locked due to too many failed attempts")
            raise AuthException("Invalid name or password")

        # 登录成功
        user.record_login_success()
        logger.info(f"User {name} authenticated successfully")
        return user

    @staticmethod
    def create_tokens(user):
        """创建访问令牌和刷新令牌"""
        # 设置令牌有效期
        access_expires = datetime.timedelta(seconds=current_app.config['JWT_ACCESS_TOKEN_EXPIRES'])
        refresh_expires = datetime.timedelta(seconds=current_app.config['JWT_REFRESH_TOKEN_EXPIRES'])

        # 创建令牌
        access_token = create_access_token(
            identity=str(user.id),
            fresh=True,
            expires_delta=access_expires
        )
        refresh_token = create_refresh_token(
            identity=str(user.id),
            expires_delta=refresh_expires
        )
        roles = [role.name for role in user.roles]

        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'username': user.name,
                'roles': roles
            }
        }

    @staticmethod
    def refresh_access_token(user_id):
        """刷新访问令牌"""
        access_expires = datetime.timedelta(seconds=current_app.config['JWT_ACCESS_TOKEN_EXPIRES'])

        access_token = create_access_token(
            identity=user_id,
            fresh=False,
            expires_delta=access_expires
        )

        return {
            'access_token': access_token
        }
