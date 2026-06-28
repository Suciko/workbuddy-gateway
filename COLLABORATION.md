# 协作开发指南

## 快速开始

```bash
# 1. 克隆仓库
git clone git@github.com:Suciko/workbuddy-gateway.git
cd workbuddy-gateway

# 2. 创建虚拟环境
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # Linux/macOS

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env，填入你的 CODEBUDDY_PASSWORD 等配置

# 5. 准备账号凭证 (如需签到功能)
# 创建 accounts/ 目录结构，参考 accounts/README.md

# 6. 启动
python web.py
```

## Git 注意事项

### 绝对不能提交的内容 (已在 .gitignore 中)

| 文件/目录 | 说明 |
|-----------|------|
| `accounts/` | 账号凭证、Session、登录状态 |
| `.codebuddy_creds/` | API Token 凭证 |
| `*.db` / `*.sqlite` | 本地数据库 |
| `.env` | 环境变量 (含密码) |
| `config/config.json` | 运行时覆盖配置 |
| `logs/` | 日志文件 |
| `scratch/` | 临时实验文件 |

### 提交前检查

```bash
git status   # 确认没有敏感文件被加入
git diff --cached   # 确认暂存区内容
```

### 分支规范

```
main        ← 稳定版本
feature/*   ← 新功能开发分支
fix/*       ← Bug 修复分支
```

### 工作流程

1. 拉取最新代码: `git pull`
2. 创建功能分支: `git checkout -b feature/xxx`
3. 开发 + 提交: `git add ... && git commit -m "..."`
4. 推送: `git push -u origin feature/xxx`
5. 在 GitHub 上创建 Pull Request
6. 代码审查后合并到 main

## 项目结构

```
├── web.py                  # 主入口
├── config.py               # 配置管理 (env → config.json → 默认值)
├── src/
│   ├── auth.py             # API 鉴权
│   ├── codebuddy_router.py # 核心路由
│   ├── codebuddy_token_manager.py  # Token 管理
│   ├── codebuddy_api_client.py     # API 客户端
│   ├── codebuddy_auth_router.py    # 认证路由
│   ├── frontend_router.py  # 前端路由
│   ├── settings_router.py  # 设置接口
│   ├── models.py           # 数据模型
│   ├── usage_stats_manager.py     # 用量统计
│   └── keyword_replacer.py # 关键词替换
├── frontend/admin.html     # Web 管理界面
├── Dockerfile              # Docker 构建
├── docker-compose.yml      # Docker 编排
└── requirements.txt        # Python 依赖
```

## 账号凭证准备

签到功能需要 WorkBuddy 登录态。每个账号在 `accounts/account_N/` 下需要 5 项凭证：

```
accounts/account_1/
├── local_storage/
├── sessions/
├── workbuddy.db
├── user-state.json
└── settings.json
```

这些文件从本地 `C:\Users\<用户名>\.workbuddy` 目录复制获得。每个开发者需要用自己的账号。

详细说明见 [accounts/README.md](accounts/README.md)
