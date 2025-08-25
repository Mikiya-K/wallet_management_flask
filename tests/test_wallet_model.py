#!/usr/bin/env python3
"""
测试Wallet模型的密码管理功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 设置Flask应用上下文
from app import create_app
from app.extensions import db
from app.models.wallet import Wallet
from app.models.user import User

def test_wallet_password_management():
    """测试钱包密码管理功能"""

    # 创建应用上下文
    app = create_app()

    with app.app_context():
        print("🚀 开始测试钱包密码管理功能...")

        # 创建测试用户
        test_user = User.create("test_user_wallet", "test_password")
        print(f"✅ 创建测试用户: {test_user.name}")

        # 创建测试钱包
        test_wallet = Wallet.create(
            coldkey_name="test_wallet_crypto",
            coldkey_address="5" + "0" * 47,  # 48字符地址
            user_id=test_user.id
        )
        print(f"✅ 创建测试钱包: {test_wallet.coldkey_name}")

        # 测试计数器
        passed_tests = 0
        total_tests = 0

        # =====================
        # 测试1: 初始状态检查
        # =====================
        total_tests += 1
        print("\n🔍 测试1: 检查钱包初始状态...")

        if not test_wallet.has_password():
            print("✅ 新钱包未设置密码 - 正确")
            passed_tests += 1
        else:
            print("❌ 新钱包不应该有密码")

        # =====================
        # 测试2: 设置密码
        # =====================
        total_tests += 1
        print("\n🔐 测试2: 设置钱包密码...")

        test_password = "my_secure_wallet_password_123"
        if test_wallet.set_password(test_password):
            print("✅ 密码设置成功")
            if test_wallet.has_password():
                print("✅ 钱包状态正确显示已设置密码")
                passed_tests += 1
            else:
                print("❌ 钱包状态错误")
        else:
            print("❌ 密码设置失败")

        # =====================
        # 测试3: 密码验证
        # =====================
        total_tests += 1
        print("\n🔑 测试3: 验证钱包密码...")

        # 正确密码验证
        if test_wallet.verify_password(test_password):
            print("✅ 正确密码验证通过")

            # 错误密码验证
            if not test_wallet.verify_password("wrong_password"):
                print("✅ 错误密码验证失败 - 正确")
                passed_tests += 1
            else:
                print("❌ 错误密码不应该验证通过")
        else:
            print("❌ 正确密码验证失败")

        # =====================
        # 测试4: 修改密码（使用基础方法组合）
        # =====================
        total_tests += 1
        print("\n🔄 测试4: 修改钱包密码...")

        new_password = "new_secure_password_456"
        # 先验证旧密码，再设置新密码
        if test_wallet.verify_password(test_password) and test_wallet.set_password(new_password):
            print("✅ 密码修改成功")

            # 验证新密码
            if test_wallet.verify_password(new_password):
                print("✅ 新密码验证通过")

                # 验证旧密码失效
                if not test_wallet.verify_password(test_password):
                    print("✅ 旧密码已失效 - 正确")
                    passed_tests += 1
                else:
                    print("❌ 旧密码不应该仍然有效")
            else:
                print("❌ 新密码验证失败")
        else:
            print("❌ 密码修改失败")

        # =====================
        # 测试5: 移除密码（使用基础方法组合）
        # =====================
        total_tests += 1
        print("\n🗑️ 测试5: 移除钱包密码...")

        # 先验证密码，再设置为None
        if test_wallet.verify_password(new_password):
            test_wallet.encrypted_password = None
            db.session.commit()
            print("✅ 密码移除成功")

            if not test_wallet.has_password():
                print("✅ 钱包状态正确显示未设置密码")

                # 验证密码已无法使用
                if not test_wallet.verify_password(new_password):
                    print("✅ 移除后密码验证失败 - 正确")
                    passed_tests += 1
                else:
                    print("❌ 移除后密码不应该仍然有效")
            else:
                print("❌ 钱包状态错误")
        else:
            print("❌ 密码验证失败，无法移除")

        # =====================
        # 测试6: 错误处理
        # =====================
        total_tests += 1
        print("\n⚠️ 测试6: 错误处理...")

        # 空密码设置
        if not test_wallet.set_password(""):
            print("✅ 空密码设置正确拒绝")

            # 空密码验证
            if not test_wallet.verify_password(""):
                print("✅ 空密码验证正确拒绝")
                passed_tests += 1
            else:
                print("❌ 空密码验证不应该通过")
        else:
            print("❌ 空密码设置不应该成功")

        # 清理测试数据
        print("\n🧹 清理测试数据...")
        db.session.delete(test_wallet)
        db.session.delete(test_user)
        db.session.commit()
        print("✅ 测试数据清理完成")

        # 输出测试结果
        print(f"\n📊 测试结果: {passed_tests}/{total_tests} 通过")

        if passed_tests == total_tests:
            print("🎉 所有测试通过!")
            return True
        else:
            print("💥 部分测试失败!")
            return False

if __name__ == "__main__":
    success = test_wallet_password_management()
    sys.exit(0 if success else 1)
