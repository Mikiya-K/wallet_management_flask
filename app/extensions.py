import sys
import bittensor
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_cors import CORS
from flask_smorest import Api
from flask_caching import Cache
from loguru import logger

# 数据库扩展
db = SQLAlchemy()

# JWT 认证
jwt = JWTManager()

# 数据库迁移
migrate = Migrate()

# 跨域支持
cors = CORS()

# REST API 文档 (Flask-Smorest)
api = Api()

# 缓存系统 (Flask-Caching)
cache = Cache()

def init_extensions(app):
    """初始化所有扩展"""
    # 基础扩展
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    api.init_app(app)
    cache.init_app(app)

    # 配置日志
    logger.remove()
    logger.add(sys.stdout,
               level=app.config['LOG_LEVEL'],
               format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")
    logger.add(app.config['LOG_FILE_PATH'],
               level=app.config['LOG_LEVEL'],
               retention=app.config['LOG_RETENTION'],
               rotation=app.config['LOG_ROTATION'],
               compression=app.config['LOG_COMPRESSION'],
               serialize=app.config['LOG_SERIALIZE'],
               enqueue=True)

    app.logger = logger

    # 根据配置启用跨域
    if app.config['CORS_ENABLED']:
        cors.init_app(app, resources={
            r"/api/*": {"origins": app.config['CORS_ORIGINS']}
        })

    subtensor = bittensor.subtensor(network=app.config['BITTENSOR_NETWORK'])
    app.subtensor = subtensor

    return app
