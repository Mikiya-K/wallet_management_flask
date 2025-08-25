from flask import Flask, jsonify
from flask_jwt_extended import jwt_required
from .config import get_config, parse_database_url
from .extensions import init_extensions
from app.utils.access_logger import AccessLogger
from app.errors.handlers import register_error_handlers
from .utils.decorators import admin_required

# 应用工厂函数
def create_app(config_class=None):
    """
    创建并配置Flask应用实例
    :param config_class: 可选的配置类，用于覆盖默认配置
    :return: Flask应用实例
    """
    # 配置加载
    config = get_config(config_class)

    # 特殊处理数据库URL
    if not config.SQLALCHEMY_DATABASE_URI:
        config.SQLALCHEMY_DATABASE_URI = parse_database_url()

    # 创建应用实例
    app = Flask(__name__)

    # 应用配置
    app.config.from_object(config)

    # 扩展初始化
    with app.app_context():
        init_extensions(app)

    access_logger = AccessLogger(app)
    register_error_handlers(app)

    from .extensions import logger, api, db, cache

    # 生产环境安全验证
    if app.config['ENV'] == 'production':
        logger.warning("生产环境配置验证中...")
        try:
            # 验证关键配置
            from .config import Config
            Config.validate()

            # 确保调试模式关闭
            if app.debug:
                raise RuntimeError("生产环境禁止启用调试模式")

        except Exception as e:
            logger.critical(f"生产环境配置验证失败: {str(e)}")
            raise

    # 蓝图注册
    from app.blueprints.auth import auth_bp
    from app.blueprints.user import user_bp
    from app.blueprints.wallet import wallet_bp

    api.register_blueprint(auth_bp)
    api.register_blueprint(user_bp)
    api.register_blueprint(wallet_bp)

    # 表创建
    with app.app_context():
        db.create_all()

    # 健康检查端点
    @app.route('/health')
    @cache.cached(timeout=10)  # 缓存10秒
    def health_check():
        """健康检查端点"""
        # 检查数据库连接状态
        try:
            db.engine.execute('SELECT 1')
            db_status = "connected"
        except Exception as e:
            db_status = f"disconnected: {str(e)}"

        # 检查缓存状态
        cache_status = "active" if cache.cache else "inactive"

        return jsonify({
            "status": "healthy",
            "environment": app.config['ENV'],
            "debug": app.debug,
            "database": db_status,
            "cache": cache_status
        })

    # 缓存管理端点
    @app.route('/cache/clear', methods=['POST'])
    @jwt_required()
    @admin_required
    def clear_cache_endpoint():
        """清除应用缓存"""
        try:
            cache.clear()
            logger.info("应用缓存已通过API清除")
            return jsonify({"status": "success", "message": "缓存已清除"})
        except Exception as e:
            logger.error(f"清除缓存失败: {str(e)}")
            return jsonify({"error": "清除缓存失败"}), 500

    # 应用启动日志
    logger.success(f"应用创建完成: {config.APP_NAME}")
    logger.info(f"API 端点前缀: /api/v1")
    if app.config.get('OPENAPI_URL_PREFIX') and app.config.get('OPENAPI_SWAGGER_UI_PATH'):
        logger.info(f"API 文档: {app.config['OPENAPI_URL_PREFIX']}{app.config['OPENAPI_SWAGGER_UI_PATH']}")
    logger.info(f"缓存系统: {app.config['CACHE_TYPE']} (超时: {app.config['CACHE_DEFAULT_TIMEOUT']}秒)")

    # 生产环境额外日志
    if app.config['ENV'] == 'production':
        logger.warning("生产环境安全特性已启用:")
        logger.warning(f"- 调试模式: {'禁用' if not app.debug else '启用 - 警告!'}")
        logger.warning(f"- CORS 启用: {app.config.get('CORS_ENABLED', False)}")
        logger.warning(f"- JWT 过期时间: {app.config.get('JWT_ACCESS_TOKEN_EXPIRES', '未配置')}秒")

    return app
