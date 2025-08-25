from flask import request, g
from app.extensions import logger
import time
import uuid

class AccessLogger:
    """访问日志记录器"""

    def __init__(self, app=None):
        if app:
            self.init_app(app)

    def init_app(self, app):
        """初始化日志中间件"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)

    def before_request(self):
        """请求前钩子"""
        # 记录请求开始时间
        g.start_time = time.time()
        g.request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))

        """记录请求信息"""
        # 跳过健康检查以减少日志噪音
        if request.path == '/health':
            return

        # 记录请求开始
        logger.info(
            f"请求开始: {request.method} {request.path} "
            f"来自 {request.remote_addr} "
            f"(ID: {g.request_id})"
        )

    def after_request(self, response):
        """请求后钩子 - 记录访问日志"""
        # 跳过健康检查以减少日志噪音
        if request.path == '/health':
            return

        # 计算请求处理时间
        duration = round((time.time() - g.start_time) * 1000, 2)  # 毫秒

        # 收集日志数据
        log_data = {
            "request_id": g.request_id,
            "method": request.method,
            "path": request.path,
            "status": response.status_code,
            "duration_ms": duration,
            "ip": request.remote_addr,
            "response_size": response.calculate_content_length() or 0,
            "query_params": dict(request.args)
        }

        # 添加用户信息（如果认证）
        try:
            from flask_jwt_extended import get_jwt_identity
            user_id = get_jwt_identity()
            if user_id:
                log_data['user_id'] = user_id
        except Exception:
            pass

        # 添加自定义上下文
        if hasattr(g, 'log_context'):
            log_data.update(g.log_context)

        # 根据状态码确定日志级别
        log_level = "INFO"
        if 500 <= response.status_code <= 599:
            log_level = "ERROR"
        elif 400 <= response.status_code <= 499:
            log_level = "WARNING"

        # 使用 loguru 的结构化日志
        logger.bind(**log_data).log(
            log_level,
            "{method} {path} - {status} | {duration_ms}ms",
            method=request.method,
            path=request.path,
            status=response.status_code,
            duration_ms=duration
        )

        # 添加 X-Request-ID 到响应头部
        response.headers['X-Request-ID'] = g.request_id

        # 为API响应添加缓存头
        #if request.path.startswith('/api') and response.status_code == 200:
        #    response.headers['Cache-Control'] = 'public, max-age=60'

        return response
