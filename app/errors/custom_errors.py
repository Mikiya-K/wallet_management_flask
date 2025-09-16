"""
自定义异常类
"""
from http import HTTPStatus

class AppException(Exception):
    """
    应用异常基类
    """
    status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    error_code = "internal_error"
    message = "An unexpected error occurred"

    def __init__(self, message=None, error_code=None, field_errors=None, **kwargs):
        """
        :param message: 人类可读的错误消息
        :param error_code: 机器可读的错误代码
        :param field_errors: 字段级错误详情 {字段名: [错误消息]}
        :param kwargs: 额外上下文信息
        """
        self.message = message or self.message
        self.error_code = error_code or self.error_code
        self.field_errors = field_errors or {}
        self.extra = kwargs

class BusinessException(AppException):
    """业务异常基类"""
    status_code = HTTPStatus.BAD_REQUEST
    error_code = "business_error"

class ValidationError(BusinessException):
    """数据验证异常"""
    error_code = "validation_error"
    message = "Data validation failed"

class AuthException(BusinessException):
    """认证异常"""
    status_code = HTTPStatus.UNAUTHORIZED
    error_code = "authentication_error"
    message = "Authentication failed"

class PermissionDeniedError(AuthException):
    """权限不足异常"""
    status_code = HTTPStatus.FORBIDDEN  # 403
    error_code = "permission_denied"
    message = "You don't have permission to perform this action"

class AccountLockedError(AuthException):
    """账户锁定异常"""
    error_code = "account_locked"
    message = "Account is temporarily locked"

class InvalidTokenError(AuthException):
    """无效令牌异常"""
    error_code = "invalid_token"
    message = "Invalid or expired authentication token"

class WalletPasswordError(BusinessException):
    """钱包密码异常基类"""
    error_code = "wallet_password_error"
    message = "Wallet password operation failed"

class WalletPasswordSetError(WalletPasswordError):
    """钱包密码设置失败异常"""
    error_code = "wallet_password_set_error"
    message = "Failed to set wallet password"

class InsufficientFundsError(BusinessException):
    """余额不足异常"""
    status_code = HTTPStatus.PAYMENT_REQUIRED
    error_code = "insufficient_funds"
    message = "Insufficient funds to complete the transaction"

class BlockchainError(BusinessException):
    """区块链操作异常"""
    status_code = HTTPStatus.SERVICE_UNAVAILABLE
    error_code = "blockchain_error"
    message = "Blockchain operation failed"

class WalletNotFoundError(BusinessException):
    """钱包未找到异常"""
    status_code = HTTPStatus.NOT_FOUND
    error_code = "wallet_not_found"
    message = "Requested wallet not found"

class TransferFailedError(BusinessException):
    """转账失败异常"""
    status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    error_code = "transfer_failed"
    message = "Blockchain operation succeeded‌ but the transfer failed"

class RemoveStakeError(BusinessException):
    """移除质押异常"""
    status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    error_code = "remove_stake_failed"
    message = "Blockchain operation succeeded‌ but remove staked failed"

class MinerRegistrationError(BusinessException):
    """矿工注册异常"""
    status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    error_code = "miner_registration_failed"
    message = "Miner registration failed"

class ResourceNotFoundError(BusinessException):
    """资源未找到异常"""
    status_code = HTTPStatus.NOT_FOUND
    error_code = "not_found"
    message = "The requested resource was not found"

class RateLimitExceededError(BusinessException):
    """速率限制异常"""
    status_code = HTTPStatus.TOO_MANY_REQUESTS
    error_code = "rate_limit_exceeded"
    message = "Too many requests, please try again later"

class ExternalServiceError(AppException):
    """外部服务异常"""
    status_code = HTTPStatus.BAD_GATEWAY
    error_code = "external_service_error"
    message = "Error communicating with external service"

class DatabaseError(AppException):
    """数据库异常"""
    error_code = "database_error"
    message = "Database operation failed"

class ConfigurationError(AppException):
    """配置异常"""
    error_code = "configuration_error"
    message = "System configuration error"
