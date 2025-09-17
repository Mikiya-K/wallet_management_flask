"""Add initial roles and admin user

Revision ID: 62272a64bc7a
Revises: e7687d5a927b
Create Date: 2025-09-17 05:07:13.457486

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text
from werkzeug.security import generate_password_hash
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '62272a64bc7a'
down_revision = 'e7687d5a927b'
branch_labels = None
depends_on = None


def upgrade():
    # 获取数据库连接
    conn = op.get_bind()

    # 定义角色表结构
    roles_table = sa.table(
        'roles',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('description', sa.String(255)),
        sa.Column('created_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime)
    )

    # 定义要添加的角色
    roles_to_add = [
        {
            'name': 'admin',
            'description': '系统管理员角色，拥有所有权限',
        },
        {
            'name': 'user',
            'description': '普通用户角色，拥有基本权限',
        }
    ]

    # 添加角色
    current_time = datetime.utcnow()
    for role_data in roles_to_add:
        # 检查角色是否已存在
        role_exists = conn.execute(
            text(f"SELECT id FROM roles WHERE name = '{role_data['name']}'")
        ).fetchone()

        if not role_exists:
            # 添加角色
            op.bulk_insert(roles_table,
                [
                    {
                        'name': role_data['name'],
                        'description': role_data['description'],
                        'created_at': current_time,
                        'updated_at': current_time
                    }
                ]
            )
            print(f"Added role: {role_data['name']}")

    # 2. 添加 btc2Moon 用户到 users 表
    users_table = sa.table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean),
        sa.Column('last_login', sa.DateTime),
        sa.Column('failed_login_attempts', sa.Integer),
        sa.Column('created_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime)
    )

    # 检查用户是否已存在
    user_exists = conn.execute(
        text("SELECT id FROM users WHERE name = 'btc2Moon'")
    ).fetchone()

    if not user_exists:
        # 生成密码哈希
        password_hash = generate_password_hash('btc2Moon')

        current_time = datetime.utcnow()
        op.bulk_insert(users_table,
            [
                {
                    'name': 'btc2Moon',
                    'password_hash': password_hash,
                    'is_active': True,
                    'last_login': None,
                    'failed_login_attempts': 0,
                    'created_at': current_time,
                    'updated_at': current_time
                }
            ]
        )
        print("Added user: btc2Moon")

    # 3. 向 user_roles 表添加权限分配
    # 获取 admin 角色 ID
    admin_role = conn.execute(
        text("SELECT id FROM roles WHERE name = 'admin'")
    ).fetchone()

    # 获取 btc2Moon 用户 ID
    btc2moon_user = conn.execute(
        text("SELECT id FROM users WHERE name = 'btc2Moon'")
    ).fetchone()

    # 如果角色和用户都存在，则创建关联
    if admin_role and btc2moon_user:
        role_id = admin_role[0]
        user_id = btc2moon_user[0]

        # 检查关联是否已存在
        association_exists = conn.execute(
            text("SELECT id FROM user_roles WHERE user_id = :user_id AND role_id = :role_id"),
            {'user_id': user_id, 'role_id': role_id}
        ).fetchone()

        if not association_exists:
            user_roles_table = sa.table(
                'user_roles',
                sa.Column('id', sa.Integer, primary_key=True),
                sa.Column('user_id', sa.Integer),
                sa.Column('role_id', sa.Integer),
                sa.Column('created_at', sa.DateTime)
            )

            current_time = datetime.utcnow()
            op.bulk_insert(user_roles_table,
                [
                    {
                        'user_id': user_id,
                        'role_id': role_id,
                        'created_at': current_time
                    }
                ]
            )
            print("Assigned admin role to btc2Moon user")


def downgrade():
    # 获取数据库连接
    conn = op.get_bind()

    # 1. 删除权限分配
    # 获取 admin 角色 ID
    admin_role = conn.execute(
        text("SELECT id FROM roles WHERE name = 'admin'")
    ).fetchone()

    # 获取 btc2Moon 用户 ID
    btc2moon_user = conn.execute(
        text("SELECT id FROM users WHERE name = 'btc2Moon'")
    ).fetchone()

    if admin_role and btc2moon_user:
        role_id = admin_role[0]
        user_id = btc2moon_user[0]

        op.execute(
            text("DELETE FROM user_roles WHERE user_id = :user_id AND role_id = :role_id"),
            {'user_id': user_id, 'role_id': role_id}
        )
        print("Removed admin role from btc2Moon user")

    # 2. 删除 btc2Moon 用户
    op.execute(
        text("DELETE FROM users WHERE name = 'btc2Moon'")
    )
    print("Removed user: btc2Moon")

    # 3. 删除添加的角色
    roles_to_remove = ['admin', 'user']
    for role_name in roles_to_remove:
        op.execute(
            text(f"DELETE FROM roles WHERE name = '{role_name}'")
        )
        print(f"Removed role: {role_name}")
