#!/usr/bin/env python3
"""
测试钱包密码管理API
"""

import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 设置Flask应用上下文
from app import create_app
from app.extensions import db
from app.models.wallet import Wallet
from app.models.user import User
from app.models.role import Role
from flask_jwt_extended import create_access_token

def test_wallet_password_api():
    """测试钱包密码管理API"""

    # 创建应用上下文
    app = create_app()

    with app.app_context():
        print("🚀 开始测试钱包密码管理API...")

        # 创建测试客户端
        client = app.test_client()

        # 创建管理员用户
        admin_user = User.create("test_admin_api", "admin_password")
        admin_role = Role.query.filter_by(name='admin').first()
        if admin_role:
            admin_user.roles.append(admin_role)
            db.session.commit()

        # 创建普通用户
        normal_user = User.create("test_user_api", "user_password")

        # 创建测试钱包
        test_wallet1 = Wallet.create(
            coldkey_name="test_wallet_api_1",
            coldkey_address="5" + "1" * 47,
            user_id=normal_user.id
        )

        test_wallet2 = Wallet.create(
            coldkey_name="test_wallet_api_2",
            coldkey_address="5" + "2" * 47,
            user_id=normal_user.id
        )

        # 生成JWT令牌
        admin_token = create_access_token(identity=str(admin_user.id))
        normal_token = create_access_token(identity=str(normal_user.id))

        # 测试计数器
        passed_tests = 0
        total_tests = 0

        # =====================
        # 测试1: 管理员设置单个钱包密码
        # =====================
        total_tests += 1
        print("\n🔐 测试1: 管理员设置单个钱包密码...")

        response = client.put(
            f'/api/wallets/{test_wallet1.coldkey_name}/password',
            json={'password': 'test_password_123'},
            headers={'Authorization': f'Bearer {admin_token}'}
        )

        if response.status_code == 200:
            print("✅ API调用成功")

            # 验证密码是否设置成功
            db.session.refresh(test_wallet1)
            if test_wallet1.has_password() and test_wallet1.verify_password('test_password_123'):
                print("✅ 密码设置并验证成功")
                passed_tests += 1
            else:
                print("❌ 密码设置失败")
        else:
            print(f"❌ API调用失败: {response.status_code} - {response.get_json()}")

        # =====================
        # 测试2: 普通用户无权限设置密码
        # =====================
        total_tests += 1
        print("\n🚫 测试2: 普通用户无权限设置密码...")

        response = client.put(
            f'/api/wallets/{test_wallet2.coldkey_name}/password',
            json={'password': 'should_fail'},
            headers={'Authorization': f'Bearer {normal_token}'}
        )

        if response.status_code == 403:
            print("✅ 正确拒绝普通用户访问")
            passed_tests += 1
        else:
            print(f"❌ 权限控制失败: {response.status_code}")

        # =====================
        # 测试3: 批量设置钱包密码
        # =====================
        total_tests += 1
        print("\n📦 测试3: 批量设置钱包密码...")

        batch_data = {
            'passwords': [
                {'coldkey_name': test_wallet1.coldkey_name, 'password': 'batch_password_1'},
                {'coldkey_name': test_wallet2.coldkey_name, 'password': 'batch_password_2'},
                {'coldkey_name': 'nonexistent_wallet', 'password': 'should_fail'}  # 不存在的钱包
            ]
        }

        response = client.put(
            '/api/wallets/password/batch',
            json=batch_data,
            headers={'Authorization': f'Bearer {admin_token}'}
        )

        if response.status_code == 200:
            result = response.get_json()
            print(f"✅ 批量API调用成功")
            print(f"   总数: {result['total']}")
            print(f"   成功: {result['success_count']}")
            print(f"   失败: {result['failure_count']}")

            # 验证结果
            if (result['total'] == 3 and
                result['success_count'] == 2 and
                result['failure_count'] == 1):
                print("✅ 批量处理结果正确")

                # 验证密码是否设置成功
                db.session.refresh(test_wallet1)
                db.session.refresh(test_wallet2)

                if (test_wallet1.verify_password('batch_password_1') and
                    test_wallet2.verify_password('batch_password_2')):
                    print("✅ 批量密码设置验证成功")
                    passed_tests += 1
                else:
                    print("❌ 批量密码验证失败")
            else:
                print("❌ 批量处理结果不正确")
        else:
            print(f"❌ 批量API调用失败: {response.status_code} - {response.get_json()}")

        # =====================
        # 测试4: 无效钱包ID
        # =====================
        total_tests += 1
        print("\n❌ 测试4: 设置不存在钱包的密码...")

        response = client.put(
            '/api/wallets/nonexistent_wallet/password',
            json={'password': 'test_password'},
            headers={'Authorization': f'Bearer {admin_token}'}
        )

        if response.status_code == 404:
            print("✅ 正确处理不存在的钱包")
            passed_tests += 1
        else:
            print(f"❌ 错误处理失败: {response.status_code}")

        # =====================
        # 测试5: 无效请求数据
        # =====================
        total_tests += 1
        print("\n📝 测试5: 无效请求数据...")

        response = client.put(
            f'/api/wallets/{test_wallet1.coldkey_name}/password',
            json={'invalid_field': 'test'},
            headers={'Authorization': f'Bearer {admin_token}'}
        )

        if response.status_code == 422:  # 数据验证失败
            print("✅ 正确处理无效请求数据")
            passed_tests += 1
        else:
            print(f"❌ 数据验证失败: {response.status_code}")

        # 清理测试数据
        print("\n🧹 清理测试数据...")
        db.session.delete(test_wallet1)
        db.session.delete(test_wallet2)
        db.session.delete(admin_user)
        db.session.delete(normal_user)
        db.session.commit()
        print("✅ 测试数据清理完成")

        # 输出测试结果
        print(f"\n📊 API测试结果: {passed_tests}/{total_tests} 通过")

        if passed_tests == total_tests:
            print("🎉 所有API测试通过!")
            return True
        else:
            print("💥 部分API测试失败!")
            return False

if __name__ == "__main__":
    success = test_wallet_password_api()
    sys.exit(0 if success else 1)
