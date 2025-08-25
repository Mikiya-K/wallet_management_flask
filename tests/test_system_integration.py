#!/usr/bin/env python3
"""
测试钱包密码管理系统集成
"""

import sys
import os
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 设置Flask应用上下文
from app import create_app
from app.extensions import db
from app.models.wallet import Wallet
from app.models.user import User
from app.blueprints.wallet.services import WalletPasswordService
from app.utils.blockchain import transfer, remove_stake

def test_system_integration():
    """测试钱包密码管理系统集成"""

    # 创建应用上下文
    app = create_app()

    with app.app_context():
        print("🚀 开始测试钱包密码管理系统集成...")

        # 创建测试用户
        test_user = User.create("test_user_integration", "test_password")
        print(f"✅ 创建测试用户: {test_user.name}")

        # 创建测试钱包
        test_wallet = Wallet.create(
            coldkey_name="test_wallet_integration",
            coldkey_address="5" + "0" * 47,
            user_id=test_user.id
        )
        print(f"✅ 创建测试钱包: {test_wallet.coldkey_name}")

        # 测试计数器
        passed_tests = 0
        total_tests = 0

        # =====================
        # 测试1: 设置钱包密码
        # =====================
        total_tests += 1
        print("\n🔐 测试1: 设置钱包密码...")

        test_password = "integration_test_password_123"
        if test_wallet.set_password(test_password):
            print("✅ 钱包密码设置成功")
            passed_tests += 1
        else:
            print("❌ 钱包密码设置失败")

        # =====================
        # 测试2: 获取钱包密码服务
        # =====================
        total_tests += 1
        print("\n📤 测试2: 获取钱包密码服务...")

        try:
            retrieved_password = WalletPasswordService.get_wallet_password(test_wallet.id)
            if retrieved_password == test_password:
                print("✅ 密码获取服务正常工作")
                passed_tests += 1
            else:
                print("❌ 获取的密码不正确")
        except Exception as e:
            print(f"❌ 密码获取服务失败: {e}")

        # =====================
        # 测试3: 区块链操作密码集成（模拟）
        # =====================
        total_tests += 1
        print("\n🔗 测试3: 区块链操作密码集成...")

        # 模拟bittensor钱包和区块链操作
        with patch('bittensor.Wallet') as mock_wallet_class, \
             patch('bittensor.core.extrinsics.transfer.transfer_extrinsic') as mock_transfer, \
             patch('app.utils.blockchain.SubtensorInterface') as mock_subtensor:

            # 设置模拟对象
            mock_wallet = MagicMock()
            mock_wallet.coldkey_file.save_password_to_env = MagicMock()
            mock_wallet.unlock_coldkey = MagicMock()
            mock_wallet_class.return_value = mock_wallet
            mock_transfer.return_value = True

            # 模拟当前应用配置
            with patch('flask.current_app') as mock_app:
                mock_app.config = {
                    'BITTENSOR_WALLET_PATH': '/test/path',
                    'BITTENSOR_WALLET_PASSWORD': None  # 没有统一密码
                }
                mock_app.subtensor = MagicMock()

                try:
                    # 测试transfer函数使用数据库密码
                    success = transfer(
                        wallet=mock_wallet,
                        alias=test_wallet.coldkey_name,
                        toAddress="5" + "1" * 47,
                        amount=1.0,
                        wallet_password=test_password
                    )

                    if success:
                        print("✅ 区块链转账操作密码集成成功")
                        # 验证密码被正确传递
                        mock_wallet.coldkey_file.save_password_to_env.assert_called_with(test_password)
                        mock_wallet.unlock_coldkey.assert_called_once()
                        passed_tests += 1
                    else:
                        print("❌ 区块链转账操作失败")

                except Exception as e:
                    print(f"❌ 区块链操作密码集成失败: {e}")

        # =====================
        # 测试4: 未设置密码的钱包回退机制
        # =====================
        total_tests += 1
        print("\n🔄 测试4: 未设置密码的钱包回退机制...")

        # 创建没有密码的钱包
        test_wallet_no_password = Wallet.create(
            coldkey_name="test_wallet_no_password",
            coldkey_address="5" + "2" * 47,
            user_id=test_user.id
        )

        with patch('bittensor.Wallet') as mock_wallet_class, \
             patch('bittensor.core.extrinsics.transfer.transfer_extrinsic') as mock_transfer:

            mock_wallet = MagicMock()
            mock_wallet.coldkey_file.save_password_to_env = MagicMock()
            mock_wallet.unlock_coldkey = MagicMock()
            mock_wallet_class.return_value = mock_wallet
            mock_transfer.return_value = True

            with patch('flask.current_app') as mock_app:
                mock_app.config = {
                    'BITTENSOR_WALLET_PATH': '/test/path',
                    'BITTENSOR_WALLET_PASSWORD': 'fallback_password'  # 统一密码
                }
                mock_app.subtensor = MagicMock()

                # 同时需要patch app.utils.blockchain中的current_app
                with patch('app.utils.blockchain.current_app', mock_app):
                    try:
                        # 测试没有密码的钱包使用配置文件密码
                        success = transfer(
                            wallet=mock_wallet,
                            alias=test_wallet_no_password.coldkey_name,
                            toAddress="5" + "1" * 47,
                            amount=1.0,
                            wallet_password=None  # 没有传递密码
                        )

                        if success:
                            print("✅ 回退到配置文件密码机制正常工作")
                            # 验证使用了配置文件中的密码
                            mock_wallet.coldkey_file.save_password_to_env.assert_called_with('fallback_password')
                            passed_tests += 1
                        else:
                            print("❌ 回退机制失败")

                    except Exception as e:
                        print(f"❌ 回退机制测试失败: {e}")

        # =====================
        # 测试5: 错误处理
        # =====================
        total_tests += 1
        print("\n⚠️ 测试5: 错误处理...")

        try:
            # 测试获取不存在钱包的密码
            WalletPasswordService.get_wallet_password(99999)
            print("❌ 应该抛出异常但没有")
        except Exception as e:
            if "钱包不存在" in str(e):
                print("✅ 正确处理不存在的钱包")
                passed_tests += 1
            else:
                print(f"❌ 异常信息不正确: {e}")

        # 清理测试数据
        print("\n🧹 清理测试数据...")
        db.session.delete(test_wallet)
        db.session.delete(test_wallet_no_password)
        db.session.delete(test_user)
        db.session.commit()
        print("✅ 测试数据清理完成")

        # 输出测试结果
        print(f"\n📊 系统集成测试结果: {passed_tests}/{total_tests} 通过")

        if passed_tests == total_tests:
            print("🎉 所有系统集成测试通过!")
            return True
        else:
            print("💥 部分系统集成测试失败!")
            return False

if __name__ == "__main__":
    success = test_system_integration()
    sys.exit(0 if success else 1)
