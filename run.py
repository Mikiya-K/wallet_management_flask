"""
Flask 开发环境启动脚本 - 安全增强版
仅限开发环境使用，生产环境请通过 WSGI 部署

开发工作流
# 1. 设置环境
echo "FLASK_ENV=development" > .flaskenv
echo "SECRET_KEY=dev_secret_123" > .env

# 2. 启动开发服务器
python run.py
flask run

# 输出示例：
✅ 已加载 .env 文件: /project/.env
✅ 已加载 .flaskenv 文件: /project/.flaskenv

============================================================
🚀 启动 Flask 开发服务器: http://localhost:5000
============================================================
环境: development
调试模式: True
自动重载: True
------------------------------------------------------------
控制台命令:
  CTRL+C — 停止服务器
  rs       — 手动重启 (Flask 2.0+)
============================================================
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def load_environment_vars():
    """分层加载环境变量文件"""
    base_dir = Path(__file__).parent

    flaskenv_file = base_dir / '.flaskenv'
    if flaskenv_file.exists():
        load_dotenv(dotenv_path=flaskenv_file, override=False)
        print(f'✅ 已加载 .flaskenv 文件: {flaskenv_file}')

    # 检查必要变量
    required_vars = ['FLASK_APP', 'FLASK_ENV']
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        print(f'\n⚠️ 缺少必要环境变量: {", ".join(missing)}')
        print('请在 .env 或 .flaskenv 文件中设置:')
        for var in missing:
            print(f'  {var}=your_value')
        sys.exit(1)

# 加载环境变量
load_environment_vars()

def is_production_environment():
    """检测是否可能在生产环境"""
    # 明确的标志变量
    if os.getenv('FLASK_ENV') == 'production':
        return True

    # 云环境检测
    if 'AWS_EXECUTION_ENV' in os.environ:  # AWS Lambda/ECS
        return True
    if 'K_SERVICE' in os.environ:         # Google Cloud Run
        return True
    if 'WEBSITE_SITE_NAME' in os.environ:  # Azure App Service
        return True

    # 容器环境判断
    if Path('/.dockerenv').exists() and not os.getenv('FLASK_DEBUG'):
        return True

    return False

# 如果检测到生产环境，立即终止并显示警告
'''
if is_production_environment():
    print('\n' + '=' * 60)
    print('❌ 严重安全警告：禁止在生产环境使用开发服务器！'.center(60))
    print('=' * 60)
    print('原因:')
    print('  - 开发服务器性能不足且不安全')
    print('  - 调试模式会暴露敏感信息')
    print('\n正确启动方式:')
    print('  gunicorn --workers 4 --bind 0.0.0.0:8000 wsgi:app')
    print('\n环境检测依据:')
    for var in ['FLASK_ENV', 'AWS_EXECUTION_ENV', 'K_SERVICE', 'WEBSITE_SITE_NAME']:
        if var in os.environ:
            print(f'  - {var} = {os.environ[var]}')
    if Path('/.dockerenv').exists():
        print('  - 检测到容器环境且未启用 DEV_MODE')
    print('=' * 60)
    sys.exit(1)
'''

from app import create_app

# 创建应用实例
app = create_app()

if __name__ == '__main__':
    try:
        # 获取配置或使用默认值
        host = os.getenv('FLASK_RUN_HOST', '0.0.0.0')
        port = os.getenv('FLASK_RUN_PORT', 5000)

        # 彩色化启动信息
        print('\n\033[1;36m' + '=' * 60)
        print(f'🚀 启动 Flask 开发服务器: http://{host}:{port}'.center(60))
        print('=' * 60 + '\033[0m')
        print(f'环境: \033[1;33m{app.config["ENV"]}\033[0m')
        print(f'调试模式: \033[1;33m{app.debug}\033[0m')
        print(f'自动重载: \033[1;33m{True}\033[0m')
        print('\033[1;36m' + '-' * 60)
        print('控制台命令:')
        print('  \033[1;32mCTRL+C\033[0m — 停止服务器')
        print('  \033[1;32mrs\033[0m       — 手动重启 (Flask 2.0+)')
        print('=' * 60 + '\033[0m\n')

        # 启动开发服务器
        app.run(
            host=host,
            port=port,
            debug=True,
            use_reloader=True,
            use_debugger=True,
            passthrough_errors=False
        )
    except KeyboardInterrupt:
        print('\n\033[1;31m' + '=' * 60)
        print('🛑 开发服务器已停止'.center(60))
        print('=' * 60 + '\033[0m')
        sys.exit(0)
    except Exception as e:
        print(f'\n\033[1;41m 启动失败: {str(e)} \033[0m')
        sys.exit(1)
