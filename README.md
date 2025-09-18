# 钱包管理 Flask 应用

一个基于 Flask 的 Bittensor 钱包管理系统，支持钱包创建、密码管理、矿工注册等功能。

## 🚀 快速部署

### 前置要求

- Python 3.10+
- PostgreSQL 数据库
- Redis (可选，用于缓存)
- PM2 (用于进程管理)
- Node.js (用于 PM2)

### 1. 克隆项目

```bash
git clone https://github.com/Mikiya-K/wallet_management_flask.git
cd wallet_management_flask
```

### 2. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件
nano .env
```

**必须配置的关键变量：**

```bash
# =============================================================================
# 🔴 核心必须配置项（缺少任何一项都无法启动）
# =============================================================================

# 1. 应用环境配置
ENV=production                    # 运行环境：development, production

# 2. 安全密钥配置（生产环境必须设置强密钥）
SECRET_KEY=your-very-secure-secret-key-here-at-least-32-characters
JWT_SECRET_KEY=your-jwt-secret-key-here-different-from-secret-key

# 3. 数据库配置（两个数据库连接都必须配置）
# 基础数据库连接（用于注册服务动态创建连接）
DATABASE_URL=postgresql://username:password@localhost
# Flask应用专用数据库连接（包含具体数据库名）
FLASK_DATABASE_URL=postgresql://username:password@localhost/wallet_management

# 4. 钱包密码加密配置（用于安全存储钱包密码）
# 生成方法：python -c "import base64, os; print(base64.b64encode(os.urandom(32)).decode())"
WALLET_MASTER_KEY=your-base64-encoded-32-byte-master-key-here

# =============================================================================
# 🟡 重要配置项（建议配置，有默认值）
# =============================================================================

# 5. Bittensor网络配置
BITTENSOR_NETWORK=test            # 网络类型：test, main
BITTENSOR_WALLET_PATH=~/.bittensor/wallets

# 6. Redis缓存配置（用于性能优化）
REDIS_URL=redis://localhost:6379/0

# 7. 初始管理员配置
INITIAL_ADMIN_USERNAME=admin
INITIAL_ADMIN_PASSWORD=your-secure-admin-password

# =============================================================================
# 🟢 可选配置项（高级配置）
# =============================================================================

# 8. JWT认证配置
JWT_ACCESS_EXPIRES=3600           # 访问令牌过期时间（秒）
JWT_REFRESH_EXPIRES=86400         # 刷新令牌过期时间（秒）

# 9. 安全配置
MAX_LOGIN_ATTEMPTS=5              # 最大登录失败次数

# 10. 日志配置
LOG_LEVEL=WARNING                 # 日志级别：DEBUG, INFO, WARNING, ERROR
LOG_FILE_PATH=logs/app.log        # 日志文件路径

# 11. 钱包加密高级配置
WALLET_PBKDF2_ITERATIONS=100000   # PBKDF2迭代次数，建议100000以上

# 12. 矿工注册服务基础区块配置（可选，有默认值）
BASE_BLOCK_18=2720320             # 子网18的基础区块
BASE_BLOCK_22=2807542             # 子网22的基础区块
BASE_BLOCK_41=4177902             # 子网41的基础区块
BASE_BLOCK_180=3514065            # 子网180的基础区块
BASE_BLOCK_44=3550319             # 子网44的基础区块
BASE_BLOCK_4=5282253              # 子网4的基础区块
BASE_BLOCK_172=4177902            # 子网172的基础区块
BASE_BLOCK_123=5794330            # 子网123的基础区块

```

## 🔧 配置验证和安全提醒

### 配置验证

应用启动时会自动验证关键配置：

```bash
# 如果配置有误，会显示类似错误：
⚠️ 配置验证失败:
  - SECRET_KEY 必须设置
  - DATABASE_URL 必须设置
  - WALLET_MASTER_KEY 必须设置
  - WALLET_MASTER_KEY 长度至少32字符
```

### 生成安全密钥

```bash
# 生成 WALLET_MASTER_KEY（Base64编码的32字节密钥）
python -c "import base64, os; print(base64.b64encode(os.urandom(32)).decode())"

# 生成 SECRET_KEY 和 JWT_SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 🔒 安全提醒

1. **生产环境必须使用强密钥**，不要使用示例中的密钥
2. **定期轮换密钥**，特别是 SECRET_KEY 和 JWT_SECRET_KEY
3. **确保数据库用户权限最小化**
4. **使用 HTTPS 连接数据库**（如果是远程数据库）
5. **定期备份 WALLET_MASTER_KEY**，丢失将无法解密钱包密码
6. **生产环境必须设置强的初始管理员密码**
7. **部署后建议立即修改初始管理员密码**
8. **确保 .env 文件不被提交到版本控制系统**

### 5. 创建数据库

```bash
# 连接到 PostgreSQL
psql -U postgres

# 创建数据库
CREATE DATABASE wallet_management;
CREATE DATABASE metagraph;
# 数据库metagraph需包含表regevents、hyperparameters_normalized

# 创建用户（可选）
CREATE USER your_username WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE wallet_management TO your_username;
GRANT ALL PRIVILEGES ON DATABASE metagraph TO your_username;
```

### 6. 初始化数据库

```bash
# 激活虚拟环境
source venv/bin/activate

# 运行数据库迁移
flask db upgrade
```

### 7. 启动服务

```bash
# 按照实际使用需求修改ecosystem.config.js（含启动路径与地址及端口）
nano ecosystem.config.js

# 使用 PM2 启动所有服务
pm2 start ecosystem.config.js

# 查看服务状态
pm2 status

# 查看日志
pm2 logs
```

### 8. 验证部署

```bash
# 检查服务状态
pm2 list

# 测试 Flask 应用
curl http://localhost:16003/health

# 查看日志
pm2 logs wallet-management-flask
pm2 logs miner-register
```

## 📋 服务管理

### PM2 常用命令

```bash
# 启动服务
pm2 start ecosystem.config.js

# 重启服务
pm2 restart all
pm2 restart wallet-management-flask
pm2 restart miner-register

# 停止服务
pm2 stop all
pm2 delete all

# 查看日志
pm2 logs
pm2 logs --lines 50

# 监控服务
pm2 monit
```

### 服务说明

- **wallet-management-flask**: Flask Web 应用 (端口 16003)
- **miner-register**: 矿工自动注册服务

## 🏗️ 项目结构

```
wallet_management_flask/
├── app/                    # Flask 应用主目录
│   ├── blueprints/        # 蓝图模块
│   │   ├── auth/          # 认证相关
│   │   └── wallet/        # 钱包管理
│   ├── models/            # 数据模型
│   ├── utils/             # 工具函数
│   │   ├── register.py    # 矿工注册服务
│   │   └── wallet_db.py   # 钱包数据库操作
│   ├── errors/            # 错误处理
│   ├── config.py          # 配置文件
│   └── __init__.py        # 应用工厂
├── logs/                  # 日志文件
├── migrations/            # 数据库迁移文件
├── ecosystem.config.js    # PM2 配置文件
├── wsgi.py               # WSGI 入口文件
├── requirements.txt      # Python 依赖
├── .env.example         # 环境变量模板
└── README.md            # 项目说明
```

## 🔧 配置说明

### 环境变量

详细的环境变量配置请参考 `.env.example` 文件。

### 数据库配置

项目使用两个数据库：

1. **wallet_management**: 主数据库，存储钱包、用户等信息
2. **metagraph**: Bittensor 网络数据，用于注册决策

### PM2 配置

`ecosystem.config.js` 配置了两个服务：

- Flask Web 应用使用 Gunicorn 运行
- 矿工注册服务作为后台任务运行
- 自动加载 `.env` 文件中的环境变量

## 🛠️ 开发指南

### 本地开发

```bash
# 激活虚拟环境
source venv/bin/activate

# 设置开发环境
export ENV=development

# 启动开发服务器
flask run --host=0.0.0.0 --port=16003
```

### 数据库迁移

```bash
# 创建迁移文件
flask db migrate -m "描述变更"

# 应用迁移
flask db upgrade

# 回滚迁移
flask db downgrade
```

### 测试

```bash
# 运行测试
python -m pytest

# 运行特定测试
python -m pytest tests/test_wallet.py
```

## 📊 功能特性

### 🔐 钱包管理

- **钱包创建**: 支持创建新的 Bittensor 钱包
- **密码加密**: 使用 AES-GCM 加密存储钱包密码
- **批量操作**: 支持批量钱包管理
- **安全验证**: 多层安全验证机制

### ⚡ 矿工注册

- **智能注册**: 基于历史数据的智能注册时机
- **多网络支持**: 支持多个 Bittensor 子网
- **黑名单检查**: 自动检查注册黑名单
- **费用优化**: 动态费用配置

### 🔄 自动化服务

- **后台任务**: 自动化矿工注册服务
- **进程管理**: PM2 进程监控和自动重启
- **日志记录**: 详细的操作日志和错误追踪
- **健康检查**: 服务健康状态监控

### 🛡️ 安全特性

- **JWT 认证**: 基于 JWT 的用户认证
- **密码加密**: 钱包密码安全加密存储
- **访问控制**: 细粒度的权限控制
- **审计日志**: 完整的操作审计记录

## 📊 API 接口

### 认证接口

```bash
POST /auth/login          # 用户登录
POST /auth/logout         # 用户登出
POST /auth/refresh        # 刷新令牌
```

### 钱包管理接口

```bash
GET  /wallet/list         # 获取钱包列表
POST /wallet/create       # 创建新钱包
PUT  /wallet/{id}         # 更新钱包信息
DELETE /wallet/{id}       # 删除钱包
POST /wallet/decrypt      # 解密钱包密码
```

### 矿工注册接口

```bash
GET  /miner/status        # 获取注册状态
POST /miner/register      # 手动注册矿工
GET  /miner/history       # 获取注册历史
```

### 系统接口

```bash
GET  /health              # 健康检查
GET  /metrics             # 系统指标
```

## 🔒 安全注意事项

1. **密钥管理**

   - 生产环境必须使用强密钥
   - 定期轮换 SECRET_KEY 和 JWT_SECRET_KEY
   - 妥善保管 WALLET_MASTER_KEY

2. **数据库安全**

   - 使用最小权限的数据库用户
   - 启用数据库连接加密
   - 定期备份数据库

3. **网络安全**
   - 使用 HTTPS 部署
   - 配置防火墙规则
   - 限制数据库访问

## 🐛 故障排除

### 常见问题

1. **数据库连接失败**

   ```bash
   # 检查数据库服务
   sudo systemctl status postgresql

   # 检查连接配置
   psql -U username -d wallet_management -h localhost
   ```

2. **PM2 服务启动失败**

   ```bash
   # 查看详细错误
   pm2 logs --lines 50

   # 检查配置文件
   pm2 start ecosystem.config.js --dry-run
   ```

3. **环境变量未加载**

   ```bash
   # 检查 .env 文件
   cat .env

   # 重启 PM2 服务
   pm2 restart all --update-env
   ```

## 📝 更新日志

### v1.0.0 (2025-09-16)

- 初始版本发布
- 支持钱包管理和矿工注册
- 集成 PM2 进程管理
- 优化数据库连接架构

---

**注意**: 这是一个 Bittensor 生态系统的工具，使用前请确保了解相关风险和责任。
