# config.py
import os
import sys
from dotenv import load_dotenv
from urllib.parse import quote_plus

# 加载 .env 文件中的环境变量
load_dotenv()

# 基础配置类 - 包含所有环境通用设置
class Config:
    # =====================
    # 应用元数据配置
    # =====================
    APP_NAME = "MyFlaskApp"
    APP_VERSION = "1.0.0"
    PROPAGATE_EXCEPTIONS = True

    # =====================
    # 安全关键配置 (必须通过环境变量设置)
    # =====================
    # 生产环境必须设置，开发环境有默认值
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    MAX_LOGIN_ATTEMPTS = int(os.getenv('MAX_LOGIN_ATTEMPTS', 5))  # 最大登录失败次数

    # =====================
    # JWT 认证配置
    # =====================
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your_jwt_secret')
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_EXPIRES', 3600))  # 1小时
    JWT_REFRESH_TOKEN_EXPIRES = int(os.getenv('JWT_REFRESH_EXPIRES', 86400))  # 1天
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ['access', 'refresh']

    # =====================
    # 数据库配置 (使用环境变量)
    # =====================
    SQLALCHEMY_DATABASE_URI = os.getenv('FLASK_DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Redis 配置
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

    # Bittensor 配置
    BITTENSOR_NETWORK = os.getenv('BITTENSOR_NETWORK', 'test')
    BITTENSOR_WALLET_PATH = os.getenv('BITTENSOR_WALLET_PATH', '~/.bittensor/wallets')

    # =====================
    # 钱包密码加密配置
    # =====================
    WALLET_MASTER_KEY = os.getenv('WALLET_MASTER_KEY')
    WALLET_PBKDF2_ITERATIONS = int(os.getenv('WALLET_PBKDF2_ITERATIONS', 100000))

    # =====================
    # 跨域配置 (CORS)
    # =====================
    CORS_ENABLED = True
    CORS_ORIGINS = []

    # =====================
    # Flask-Smorest 配置
    # =====================
    API_TITLE = "MyFlaskAPI"
    API_VERSION = "v1"
    OPENAPI_VERSION = "3.0.2"
    OPENAPI_JSON_PATH = "api-spec.json"
    OPENAPI_URL_PREFIX = "/"
    OPENAPI_REDOC_PATH = "/redoc"
    OPENAPI_REDOC_URL = (
        "https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js"
    )
    OPENAPI_SWAGGER_UI_PATH = "/swagger-ui"
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    OPENAPI_RAPIDOC_PATH = "/rapidoc"
    OPENAPI_RAPIDOC_URL = "https://unpkg.com/rapidoc/dist/rapidoc-min.js"

    # =====================
    # Flask-Caching 配置
    # =====================
    CACHE_TYPE = "RedisCache"
    CACHE_REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CACHE_DEFAULT_TIMEOUT = 300  # 默认缓存时间（秒）
    CACHE_KEY_PREFIX = "myapp_"
    CACHE_THRESHOLD = 500  # 缓存阈值，超过此数量将清理最旧的缓存
    OPENAPI_SWAGGER_UI_CONFIG = {
        "deepLinking": True,
        "persistAuthorization": True,
        "displayRequestDuration": True
    }

    # =====================
    # 日志配置
    # =====================
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')
    LOG_FILE_PATH = os.getenv('LOG_FILE_PATH', 'logs/app.log')
    LOG_RETENTION = "30 days"  # 日志保留时间
    LOG_ROTATION = "100 MB"    # 日志文件轮转大小
    LOG_COMPRESSION = "zip"    # 日志压缩格式
    LOG_SERIALIZE = True       # 输出JSON格式

    # =====================
    # 配置验证方法
    # =====================
    @classmethod
    def validate(cls):
        """验证关键配置是否有效"""
        errors = []

        # 安全密钥验证
        if not cls.SECRET_KEY:
            errors.append("SECRET_KEY 必须设置")
        if cls.SECRET_KEY == 'dev-secret-key' and cls.ENV == 'production':
            errors.append("生产环境 SECRET_KEY 不能使用默认值")
        if len(cls.SECRET_KEY) < 16:
            errors.append("SECRET_KEY 长度至少16字符")

        # 数据库连接验证
        if not cls.SQLALCHEMY_DATABASE_URI:
            errors.append("DATABASE_URL 必须设置")

        # 钱包加密配置验证
        if not cls.WALLET_MASTER_KEY:
            errors.append("WALLET_MASTER_KEY 必须设置")
        elif len(cls.WALLET_MASTER_KEY) < 32:
            errors.append("WALLET_MASTER_KEY 长度至少32字符")

        if errors:
            error_msg = "\n".join([f"  - {error}" for error in errors])
            print(f"\n{'!' * 60}\n⚠️ 配置验证失败:\n{error_msg}\n{'!' * 60}")
            sys.exit(1)

# =========================================================================
# 开发环境配置
# =========================================================================
class DevelopmentConfig(Config):
    ENV = 'development'
    DEBUG = True

    # 开发环境默认值
    if not Config.SQLALCHEMY_DATABASE_URI:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///dev.db'

    # 开发环境钱包加密默认配置
    if not Config.WALLET_MASTER_KEY:
        WALLET_MASTER_KEY = 'HJ8vYxgGv33TcdwGgdBgNqLW6EPb8cHLu2DwubCPtS0='

    BITTENSOR_NETWORK = 'test'
    SQLALCHEMY_ECHO = True  # 输出SQL语句
    JSONIFY_PRETTYPRINT_REGULAR = True  # 美化JSON输出
    LOG_LEVEL = 'WARNING'

# =========================================================================
# 生产环境配置
# =========================================================================
class ProductionConfig(Config):
    ENV = 'production'
    DEBUG = False

    # 生产环境必须显式设置
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.getenv('FLASK_DATABASE_URL')

    # 性能优化
    JSONIFY_PRETTYPRINT_REGULAR = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    # 生产日志配置
    LOG_LEVEL = 'WARNING'

# =========================================================================
# 配置选择器
# =========================================================================
def get_config(env_name=None):
    """根据环境变量获取配置类"""
    env = env_name or os.getenv('ENV', 'development')

    config_mapping = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'default': DevelopmentConfig
    }

    config_class = config_mapping.get(env.lower(), config_mapping['default'])

    return config_class

# =========================================================================
# 辅助函数：智能解析数据库URL
# =========================================================================
def parse_database_url():
    """解析并处理数据库URL中的特殊字符"""
    # 获取环境变量中的 DATABASE_URL
    url = os.getenv('DATABASE_URL')
    if not url:
        return None

    # 检查是否包含协议，默认使用 '://' 分割协议部分
    protocol, remainder = url.split('://', 1) if '://' in url else (None, url)

    # 如果 URL 中包含 '@'，意味着可能有用户名和密码
    if '@' in remainder:
        user_pass, host_port_db = remainder.split('@', 1)

        # 如果用户名和密码存在且分隔符 ':' 存在
        if ':' in user_pass:
            user, password = user_pass.split(':', 1)
            # 对密码中的特殊字符进行 URL 编码
            password = quote_plus(password)
            # 返回统一格式的 URL
            return f"{protocol}://{user}:{password}@{host_port_db}"

    # 如果没有密码部分或没有特殊字符，直接返回原始 URL
    return url
