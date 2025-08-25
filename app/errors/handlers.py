"""
全局错误处理器 - 统一日志记录
"""
from flask import request, jsonify, g, current_app
from app.extensions import logger
from werkzeug.exceptions import default_exceptions
from .custom_errors import AppException

def register_error_handlers(app):
    """
    注册全局错误处理器
    """
    # 处理自定义异常
    app.errorhandler(AppException)(handle_app_exception)

    # 处理所有HTTP标准异常
    for code in default_exceptions:
        app.errorhandler(code)(handle_http_exception)

    # 处理404异常（特殊处理）
    app.errorhandler(404)(handle_not_found)

    # 处理405异常（特殊处理）
    app.errorhandler(405)(handle_method_not_allowed)

    # 处理所有未捕获异常
    app.errorhandler(Exception)(handle_unexpected_error)

def handle_app_exception(e):
    """
    处理自定义应用异常 - 统一在此记录日志
    """
    # 准备日志上下文
    log_context = {
        "error_code": e.error_code,
        "status_code": e.status_code,
        "request_id": g.get("request_id", "N/A"),
        "path": request.path,
        "method": request.method,
        "user_id": g.get("user_id", "N/A")
    }

    # 添加异常额外上下文
    if e.extra:
        log_context.update(e.extra)

    # 根据状态码确定日志级别
    if e.status_code >= 500:
        # 服务器错误 - 记录错误级别日志
        logger.bind(**log_context).error(
            "Application Exception: {message}",
            message=e.message
        )
    elif e.status_code >= 400:
        # 客户端错误 - 记录警告级别日志
        logger.bind(**log_context).warning(
            "Application Exception: {message}",
            message=e.message
        )

    # 构建错误响应
    response = {
        'error': {
            'code': e.error_code,
            'message': e.message,
            'status': e.status_code,
            'request_id': g.get("request_id", "N/A")
        }
    }

    # 添加字段级错误详情
    if e.field_errors:
        response['error']['field_errors'] = e.field_errors

    # 添加额外上下文（仅开发环境）
    if current_app.config['DEBUG'] and e.extra:
        response['error']['details'] = e.extra

    return jsonify(response), e.status_code

def handle_http_exception(e):
    """
    处理标准HTTP异常
    """
    # 准备日志上下文
    log_context = {
        "status_code": e.code,
        "request_id": g.get("request_id", "N/A"),
        "path": request.path,
        "method": request.method,
        "user_id": g.get("user_id", "N/A")
    }

    # 根据状态码确定日志级别
    if e.code >= 500:
        logger.bind(**log_context).error(
            "HTTP Exception: {name} - {description}",
            name=e.name, description=e.description
        )
    elif e.code >= 400:
        logger.bind(**log_context).warning(
            "HTTP Exception: {name} - {description}",
            name=e.name, description=e.description
        )

    # 构建响应
    return jsonify({
        'error': {
            'code': e.code,
            'message': e.description,
            'status': e.code,
            'type': e.name,
            'request_id': g.get("request_id", "N/A")
        }
    }), e.code

def handle_not_found(e):
    """
    处理404资源未找到异常
    """
    logger.bind(
        request_id=g.get("request_id", "N/A"),
        path=request.path,
        method=request.method
    ).info("Resource not found")

    response = {
        'error': {
            'code': 404,
            'message': 'The requested resource was not found',
            'status': 404,
            'path': request.path,
            'request_id': g.get("request_id", "N/A")
        }
    }
    return jsonify(response), 404

def handle_method_not_allowed(e):
    """
    处理405方法不允许异常
    """
    logger.bind(
        request_id=g.get("request_id", "N/A"),
        path=request.path,
        method=request.method,
        allowed_methods=e.valid_methods
    ).warning("Method not allowed")

    response = {
        'error': {
            'code': 405,
            'message': 'The method is not allowed for the requested URL',
            'status': 405,
            'allowed_methods': e.valid_methods,
            'request_id': g.get("request_id", "N/A")
        }
    }
    return jsonify(response), 405

def handle_unexpected_error(e):
    """
    处理未预期的异常 - 记录完整堆栈
    """
    # 记录异常堆栈
    logger.opt(exception=e).bind(
        request_id=g.get("request_id", "N/A"),
        path=request.path,
        method=request.method,
        user_id=g.get("user_id", "N/A")
    ).critical("Unhandled Exception")

    # 构建响应
    response = {
        'error': {
            'code': 500,
            'message': "An internal server error occurred",
            'status': 500,
            'request_id': g.get("request_id", "N/A")
        }
    }

    # 开发环境添加调试信息
    if current_app.config['DEBUG']:
        response['error']['details'] = {
            'type': type(e).__name__,
            'message': str(e)
        }

    return jsonify(response), 500
