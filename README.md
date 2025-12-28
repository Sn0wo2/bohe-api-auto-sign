# 薄荷 API 自动签到 (Bohe API Auto Sign)

通过 Linux.do Connect OAuth 认证自动获取薄荷签到平台 Token 的工具。

## 功能特点

- 🔐 通过 [Linux.do Connect](https://connect.linux.do) OAuth 认证
- 🎫 自动获取薄荷签到平台 (`qd.x666.me`) 的访问 Token
- 💾 自动管理和刷新 Token，持久化存储到本地文件
- 🔄 智能 Token 刷新机制，优先使用缓存的 Token
- 🌐 Web 控制面板，可视化管理签到任务
- ⏰ 定时任务调度，支持自定义签到时间

## Web 控制面板

本项目提供了一个可视化的 Web 控制面板，方便管理 Token 和签到任务。

### 功能介绍

- **Token 管理**：查看、设置和刷新 Linux.do Token
- **手动签到**：一键触发签到操作
- **定时任务**：配置每日自动签到时间（默认每天 8:00）
- **签到日志**：查看历史签到记录和状态

### 启动方式

#### 本地启动

```bash
# 使用 Poetry
poetry run uvicorn web.app:app --host 0.0.0.0 --port 8000

# 或直接使用 Python（需先安装依赖）
uvicorn web.app:app --host 0.0.0.0 --port 8000
```

#### Docker 启动

```bash
# 使用 Docker Compose
docker compose up -d

# 查看日志
docker compose logs -f
```

### 访问地址

启动后访问：`http://localhost:8000`

### 界面说明

Web 控制面板包含以下功能区域：

1. **Token 设置区**：顶部卡片区域，用于输入和保存 Linux.do Token
2. **操作按钮区**：包含「手动签到」和「刷新 Token」按钮
3. **定时任务设置**：配置每日自动签到的时间
4. **签到日志区**：展示最近的签到记录，包括时间、状态和消息

## 环境要求

- Python >= 3.12
- Poetry（推荐）或 pip

## 安装

### 使用 Poetry（推荐）

```bash
# 克隆项目
git clone https://github.com/Sn0wo2/bohe_api_auto_sign.git
cd bohe_api_auto_sign

# 安装依赖
poetry install
```

### 使用 pip

```bash
pip install linux-do-connect-token==0.0.2b2
```

## Docker 部署

### 使用 Docker Compose（推荐）

1. **准备配置文件**

   ```bash
   # 创建数据目录
   mkdir -p data
   
   # 创建并编辑 token.json 配置文件
   cat > data/token.json << 'EOF'
   {
       "bohe_sign_token": "",
       "linux_do_connect_token": "",
       "linux_do_token": "你的_linux_do_cookie_token"
   }
   EOF
   ```

2. **启动服务**

   ```bash
   # 构建并启动容器
   docker compose up -d
   
   # 查看日志
   docker compose logs -f
   ```

   服务启动后，Web 控制面板可通过 `http://localhost:8000` 访问。

3. **常用命令**

   ```bash
   # 停止服务
   docker compose down
   
   # 重新构建并启动
   docker compose up -d --build
   
   # 查看容器状态
   docker compose ps
   ```

### 使用 Docker 命令

1. **构建镜像**

   ```bash
   docker build -t bohe-auto-sign .
   ```

2. **运行容器**

   ```bash
   # 确保 data 目录和 token.json 已准备好
   docker run -d \
     --name bohe-auto-sign \
     -p 8000:8000 \
     -v $(pwd)/data:/app/data \
     bohe-auto-sign
   ```

3. **查看日志**

   ```bash
   docker logs -f bohe-auto-sign
   ```

### 端口说明

| 端口 | 说明 |
|------|------|
| 8000 | Web 控制面板 HTTP 服务端口 |

## 配置

### 1. 创建配置目录

```bash
mkdir -p data
```

### 2. 配置 Token

在 `./data/token.json` 文件中配置你的认证信息：

```json
{
    "bohe_sign_token": "",
    "linux_do_connect_token": "",
    "linux_do_token": "你的_linux_do_cookie_token"
}
```

### 3. 获取 `linux_do_token`

`linux_do_token` 是你在 [Linux.do](https://linux.do) 网站的认证 Cookie。获取方法：

1. 登录 [Linux.do](https://linux.do)
2. 打开浏览器开发者工具（F12）
3. 进入 **Application** / **应用程序** 标签页
4. 在 **Cookies** 中找到 `linux.do` 域名
5. 复制 `_t` 的值（这就是你的 `linux_do_token`）

## 使用方法

### 运行程序

```bash
# 使用 Poetry
poetry run python main.py

# 或直接使用 Python
python main.py
```

### 运行流程

程序会按以下顺序尝试获取有效的 `bohe_sign_token`：

1. **检查本地缓存** - 如果本地有有效的 `bohe_sign_token`，直接使用
2. **使用 Connect Token 刷新** - 尝试使用缓存的 `linux_do_connect_token` 刷新
3. **完整登录流程** - 使用 `linux_do_token` 进行完整的 OAuth 认证

成功获取 Token 后，所有 Token 会自动保存到 `./data/token.json`。

## 项目结构

```
bohe_api_auto_sign/
├── main.py              # 主程序入口（命令行模式）
├── pyproject.toml       # 项目配置和依赖
├── poetry.lock          # 依赖锁定文件
├── Dockerfile           # Docker 镜像构建文件
├── docker-compose.yml   # Docker Compose 配置
├── bohe_sign/           # 核心模块
│   ├── __init__.py
│   ├── login.py         # 登录和 Token 获取逻辑
│   └── sign.py          # 签到逻辑
├── store/               # 存储模块
│   ├── __init__.py
│   ├── token.py         # Token 持久化管理
│   ├── config.py        # 配置存储（定时任务设置）
│   └── log.py           # 签到日志存储
├── web/                 # Web 模块
│   ├── __init__.py
│   ├── app.py           # FastAPI 应用入口
│   ├── scheduler.py     # 定时任务调度器
│   ├── routes/          # API 路由
│   │   ├── __init__.py
│   │   ├── token.py     # Token 相关 API
│   │   ├── sign.py      # 签到相关 API
│   │   └── schedule.py  # 定时任务 API
│   └── static/          # 前端静态文件
│       ├── index.html   # 主页面
│       ├── css/
│       │   └── style.css
│       └── js/
│           └── app.js
└── data/                # 数据目录（自动创建）
    ├── token.json       # Token 存储文件
    ├── config.json      # 配置文件
    └── log.json         # 签到日志文件
```

## API 说明

### `get_bohe_token(token: str = "")`

获取薄荷 API Token 的主函数。

**参数：**
- `token` (可选): Linux.do 的认证 Token，如果不提供则从本地文件读取

**返回值：**
- `tuple[str | None, str | None, str | None]`: (bohe_token, linux_do_connect_token, linux_do_token)

### `verify_bohe_token(token: str)`

验证薄荷 Token 是否有效。

**参数：**
- `token`: 要验证的薄荷 Token

**返回值：**
- `bool`: Token 是否有效

## 依赖

- [linux-do-connect-token](https://pypi.org/project/linux-do-connect-token/) - Linux.do Connect OAuth 客户端
- [curl_cffi](https://github.com/yifeikong/curl_cffi) - HTTP 请求库（由 linux-do-connect-token 依赖）

## 许可证

[MIT License](LICENSE)

## 作者

[Sn0wo2](https://github.com/Sn0wo2)

## 致谢

感谢 [Linux.do](https://linux.do) 社区和薄荷签到平台的支持。

> 薄荷的恩情还不完 ✋😭✋