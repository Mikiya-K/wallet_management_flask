#!/usr/bin/env python3
"""
测试钱包加密工具类
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.utils.wallet_crypto import WalletPasswordCrypto, WalletCryptoError


def test_encrypt_decrypt():
    """测试加密和解密功能"""
    print("🔐 测试钱包密码加密/解密功能...")

    # 测试数据
    test_password = "test_password_123"
    test_wallet_id = 1

    try:
        # 测试加密
        print(f"原始密码: {test_password}")
        encrypted_data = WalletPasswordCrypto.encrypt_password(test_password, test_wallet_id)
        print(f"加密数据: {encrypted_data[:50]}...")

        # 测试解密
        decrypted_password = WalletPasswordCrypto.decrypt_password(encrypted_data, test_wallet_id)
        print(f"解密密码: {decrypted_password}")

        # 验证结果
        if test_password == decrypted_password:
            print("✅ 加密/解密测试通过!")
        else:
            print("❌ 加密/解密测试失败!")
            return False

        # 测试密码验证
        is_valid = WalletPasswordCrypto.verify_password(test_password, encrypted_data, test_wallet_id)
        print(f"密码验证结果: {is_valid}")

        if is_valid:
            print("✅ 密码验证测试通过!")
        else:
            print("❌ 密码验证测试失败!")
            return False

        # 测试错误密码验证
        is_invalid = WalletPasswordCrypto.verify_password("wrong_password", encrypted_data, test_wallet_id)
        if not is_invalid:
            print("✅ 错误密码验证测试通过!")
        else:
            print("❌ 错误密码验证测试失败!")
            return False

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_different_wallets():
    """测试不同钱包ID产生不同的加密结果"""
    print("\n🔑 测试不同钱包ID加密...")

    test_password = "same_password"
    wallet_id_1 = 1
    wallet_id_2 = 2

    try:
        encrypted_1 = WalletPasswordCrypto.encrypt_password(test_password, wallet_id_1)
        encrypted_2 = WalletPasswordCrypto.encrypt_password(test_password, wallet_id_2)

        print(f"钱包1加密: {encrypted_1[:50]}...")
        print(f"钱包2加密: {encrypted_2[:50]}...")

        if encrypted_1 != encrypted_2:
            print("✅ 不同钱包ID产生不同加密结果!")

            # 验证各自能正确解密
            decrypted_1 = WalletPasswordCrypto.decrypt_password(encrypted_1, wallet_id_1)
            decrypted_2 = WalletPasswordCrypto.decrypt_password(encrypted_2, wallet_id_2)

            if decrypted_1 == test_password and decrypted_2 == test_password:
                print("✅ 各自解密正确!")
                return True
            else:
                print("❌ 解密结果错误!")
                return False
        else:
            print("❌ 相同密码在不同钱包ID下产生了相同的加密结果!")
            return False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_error_cases():
    """测试错误情况"""
    print("\n⚠️ 测试错误情况处理...")

    try:
        # 测试空密码
        try:
            WalletPasswordCrypto.encrypt_password("", 1)
            print("❌ 空密码应该抛出异常!")
            return False
        except WalletCryptoError:
            print("✅ 空密码正确抛出异常!")

        # 测试无效加密数据
        try:
            WalletPasswordCrypto.decrypt_password("invalid_data", 1)
            print("❌ 无效数据应该抛出异常!")
            return False
        except WalletCryptoError:
            print("✅ 无效数据正确抛出异常!")

        # 测试空加密数据
        try:
            WalletPasswordCrypto.decrypt_password("", 1)
            print("❌ 空数据应该抛出异常!")
            return False
        except WalletCryptoError:
            print("✅ 空数据正确抛出异常!")

        return True

    except Exception as e:
        print(f"❌ 错误测试失败: {e}")
        return False


if __name__ == "__main__":
    print("🚀 开始测试钱包密码加密工具类...\n")

    # 创建Flask应用和应用上下文
    app = create_app()

    with app.app_context():
        # 运行所有测试
        tests = [
            test_encrypt_decrypt,
            test_different_wallets,
            test_error_cases
        ]

        passed = 0
        total = len(tests)

        for test in tests:
            if test():
                passed += 1
            print()

        print(f"📊 测试结果: {passed}/{total} 通过")

        if passed == total:
            print("🎉 所有测试通过!")
            sys.exit(0)
        else:
            print("💥 部分测试失败!")
            sys.exit(1)
