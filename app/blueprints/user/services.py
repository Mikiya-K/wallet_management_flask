from app.extensions import db, logger
from app.models.user import User
from app.models.role import Role
from app.models.wallet import Wallet
from sqlalchemy.orm import subqueryload
from sqlalchemy.exc import SQLAlchemyError
from app.errors.custom_errors import ResourceNotFoundError, DatabaseError

class UserService:
    @staticmethod
    def list_users(page, page_size):
        """列出用户（分页）"""
        query = User.query.filter(User.is_active == True)

        # 应用过滤条件
        #if 'is_active' in query_params:
        #    query = query.filter(User.is_active == query_params['is_active'])
        #if 'role' in query_params:
        #    query = query.filter(User.roles.any(name=query_params['role']))

        query = query.options(subqueryload(User.roles), subqueryload(User.wallets)
                              ).execution_options(
                                  compiled_cache=None,  # 禁用查询编译缓存
                                  isolation_level='READ COMMITTED'  # 确保读取最新提交的数据
                              )

        # 分页
        users = query.paginate(
            page=page,
            per_page=page_size,
            error_out=False
        )

        return {
            "total": users.total,
            "items": users.items
        }

    @staticmethod
    def update_user(data):
        """更新用户角色"""
        user = User.find_by_name(data['username'])
        if not user or not user.is_active:
            raise ResourceNotFoundError("用户不存在")

        try:
            #user.is_active = data['is_active']
            # 更新角色信息
            user.remove_role()
            roles = data.get('roles')
            for role_name in roles:
                role = Role.find_by_name(role_name)
                if not role:
                    logger.warning(f"user not exists: {role_name}")
                    continue
                user.add_role(role)

            # 更新钱包信息
            user.remove_wallet()
            wallets = data.get('wallets')
            for wallet_name in wallets:
                wallet = Wallet.find_by_name(wallet_name)
                if not wallet:
                    logger.warning(f"wallet not exists: {wallet_name}")
                    continue
                user.add_wallet(wallet)

            db.session.commit()
            logger.info("Update user", user.id, "success")
        except SQLAlchemyError as e:
            db.session.rollback()
            raise DatabaseError("Error while updating user.", user.id) from e

        return user

    @staticmethod
    def delete_user(username):
        """删除用户"""
        user = User.find_by_name(username)
        if not user or not user.is_active:
            raise ResourceNotFoundError("用户不存在")

        try:
            user.remove_role()
            user.remove_wallet()
            user.delete()
            db.session.commit()
            logger.info("Delete user", user.id, "success")
        except SQLAlchemyError as e:
            db.session.rollback()
            raise DatabaseError("Error while deleting user.", user.id) from e
