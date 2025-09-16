#!/bin/bash

# 钱包管理系统 - 优化后的Gunicorn配置
#
# 配置说明:
# -w 4: 4个worker进程，适合CPU密集型任务
# -k gevent: 使用异步worker，提高并发处理能力
# --worker-connections 1000: 每个worker最多处理1000个连接
# --timeout 300: 请求超时时间300秒（与Nginx一致）
# --max-requests 1000: 每个worker处理1000个请求后重启（防止内存泄漏）
# --max-requests-jitter 100: 随机化重启时间，避免同时重启
# --preload: 预加载应用，提高启动速度
# --access-logfile: 访问日志
# --error-logfile: 错误日志

./venv/bin/gunicorn \
  -w 4 \
  -k sync \
  -b 0.0.0.0:16003 \
  --timeout 300 \
  --max-requests 1000 \
  --max-requests-jitter 100 \
  --preload \
  --access-logfile logs/gunicorn-access.log \
  --error-logfile logs/gunicorn-error.log \
  --log-level info \
  --enable-stdio-inheritance \
  wsgi:app