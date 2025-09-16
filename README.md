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
# 数据库配置
DATABASE_URL=postgresql://username:password@localhost
FLASK_DATABASE_URL=postgresql://username:password@localhost/wallet_management

# 安全密钥（请生成你自己的密钥）
SECRET_KEY=your-very-secure-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
WALLET_MASTER_KEY=your-base64-encoded-32-byte-master-key

# 应用环境
ENV=production
```

**生成安全密钥：**

```bash
# 生成 WALLET_MASTER_KEY
python -c "import base64, os; print(base64.b64encode(os.urandom(32)).decode())"

# 生成其他密钥
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 5. 创建数据库

```bash
# 连接到 PostgreSQL
psql -U postgres

# 创建数据库
CREATE DATABASE wallet_management;
CREATE DATABASE metagraph;
# 数据库metagraph需包含表regevents

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
# 按照实际使用需求修改ecosystem.config.js（含启动路径）
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

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 支持

如有问题或建议，请：

1. 查看 [Issues](https://github.com/Mikiya-K/wallet_management_flask/issues)
2. 创建新的 Issue
3. 联系项目维护者

---

**注意**: 这是一个 Bittensor 生态系统的工具，使用前请确保了解相关风险和责任。
