
# 薄荷签到项目 Web 控制界面架构设计

## 1. 整体架构设计

### 1.1 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                      用户浏览器                              │
│                 HTML + CSS + JavaScript                      │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP/REST API
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI 后端服务                          │
│  ┌──────────────┬──────────────┬──────────────────────────┐ │
│  │  Token API   │   Sign API   │     Schedule API         │ │
│  └──────────────┴──────────────┴──────────────────────────┘ │
│                           │                                  │
│  ┌────────────────────────┴─────────────────────────────┐   │
│  │              APScheduler 定时任务调度器               │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│                      核心业务模块                            │
│  ┌──────────────┬──────────────┬──────────────────────────┐ │
│  │ bohe_sign/   │    store/    │      data/               │ │
│  │ login.py     │  token.py    │   token.json             │ │
│  │ sign.py      │  config.py   │   config.json            │ │
│  │              │  log.py      │   sign_log.json          │ │
│  └──────────────┴──────────────┴──────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 技术选型

| 组件 | 技术选择 | 说明 |
|------|---------|------|
| Web 框架 | FastAPI | Python 异步 Web 框架，性能优秀，自带 OpenAPI 文档 |
| ASGI 服务器 | Uvicorn | 高性能 ASGI 服务器 |
| 定时任务 | APScheduler | Python 定时任务库，支持持久化 |
| 前端 | HTML + CSS + JS | 原生技术栈，无需构建工具 |
| 数据存储 | JSON 文件 | 保持与现有结构兼容，轻量化 |

### 1.3 核心设计原则

1. **向后兼容**：保持现有 [`main.py`](main.py:1) 和核心模块不变，新增功能以扩展形式添加
2. **单一职责**：每个模块专注于特定功能
3. **响应式设计**：前端支持桌面端和移动端
4. **容器化部署**：更新 Docker 配置以支持 Web 服务

---

## 2. 需要添加的依赖

### 2.1 pyproject.toml 更新

```toml
[project]
name = "bohe-api-auto-sign"
version = "0.1.0"
description = "Auto sign bohe api with web control panel"
authors = [
    { name = "Sn0wo2" }
]
license = { text = "MIT" }
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "linux-do-connect-token==0.0.2b2",
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "apscheduler>=3.10.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "httpx>=0.27.0",
]
```

### 2.2 依赖说明

| 依赖 | 版本 | 用途 |
|------|------|------|
| fastapi | >=0.115.0 | Web API 框架 |
| uvicorn[standard] | >=0.32.0 | ASGI 服务器，standard 包含 websockets 支持 |
| apscheduler | >=3.10.0 | 定时任务调度 |
| pydantic | >=2.0.0 | 数据验证（FastAPI 依赖） |

---

## 3. 新增文件结构

```
bohe_api_auto_sign/
├── main.py                     # [保留] 原有入口，可用于 CLI 模式
├── pyproject.toml              # [修改] 添加新依赖
├── Dockerfile                  # [修改] 更新启动命令
├── docker-compose.yml          # [修改] 暴露端口
│
├── web/                        # [新增] Web 模块
│   ├── __init__.py
│   ├── app.py                  # FastAPI 应用主入口
│   ├── deps.py                 # 依赖注入
│   ├── scheduler.py            # APScheduler 配置与管理
│   │
│   ├── routes/                 # API 路由模块
│   │   ├── __init__.py
│   │   ├── token.py            # Token 管理相关 API
│   │   ├── sign.py             # 签到操作相关 API
│   │   └── schedule.py         # 定时任务相关 API
│   │
│   └── static/                 # 静态文件目录
│       ├── index.html          # 主页面
│       ├── css/
│       │   └── style.css       # 样式文件
│       └── js/
│           └── app.js          # 前端交互逻辑
│
├── bohe_sign/                  # [扩展] 核心业务模块
│   ├── __init__.py             # [保留]
│   ├── login.py                # [保留] 登录与 Token 获取
│   └── sign.py                 # [新增] 签到逻辑实现
│
├── store/                      # [扩展] 存储模块
│   ├── __init__.py             # [保留]
│   ├── token.py                # [保留] Token 存储
│   ├── config.py               # [新增] 配置存储（定时任务配置等）
│   └── log.py                  # [新增] 签到日志存储
│
└── data/                       # [扩展] 数据目录
    ├── token.json              # [保留] Token 存储
    ├── config.json             # [新增] 配置文件
    └── sign_log.json           # [新增] 签到日志
```

### 3.1 文件职责说明

#### Web 模块 (`web/`)

| 文件 | 职责 |
|------|------|
| [`web/app.py`](web/app.py:1) | FastAPI 应用实例创建、中间件配置、路由注册、静态文件挂载 |
| [`web/deps.py`](web/deps.py:1) | 依赖注入，如获取 scheduler 实例 |
| [`web/scheduler.py`](web/scheduler.py:1) | APScheduler 实例管理、任务添加/删除/查询 |
| [`web/routes/token.py`](web/routes/token.py:1) | Token 状态查询、Linux.do Token 设置、Token 刷新 |
| [`web/routes/sign.py`](web/routes/sign.py:1) | 手动签到、签到日志查询、签到状态查询 |
| [`web/routes/schedule.py`](web/routes/schedule.py:1) | 定时任务配置的 CRUD 操作 |

#### 扩展的核心模块

| 文件 | 职责 |
|------|------|
| [`bohe_sign/sign.py`](bohe_sign/sign.py:1) | 执行签到操作，调用薄荷 API 完成签到 |
| [`store/config.py`](store/config.py:1) | 管理配置文件，包括定时任务时间设置 |
| [`store/log.py`](store/log.py:1) | 签到日志的读写操作 |

---

## 4. API 接口设计

### 4.1 接口总览

| 模块 | 方法 | 路径 | 说明 |
|------|------|------|------|
| Token | GET | `/api/token/status` | 获取所有 Token 的状态 |
| Token | POST | `/api/token/linux-do` | 设置 Linux.do Token |
| Token | POST | `/api/token/refresh` | 刷新薄荷 Token |
| 签到 | POST | `/api/sign/now` | 立即执行签到 |
| 签到 | GET | `/api/sign/status` | 获取签到状态 |
| 签到 | GET | `/api/sign/logs` | 获取签到日志列表 |
| 定时 | GET | `/api/schedule` | 获取定时任务配置 |
| 定时 | POST | `/api/schedule` | 创建/更新定时任务 |
| 定时 | DELETE | `/api/schedule` | 删除定时任务 |

### 4.2 详细接口定义

#### 4.2.1 Token 管理接口

**GET /api/token/status**

获取当前所有 Token 的状态信息。

```json
// Response 200
{
  "success": true,
  "data": {
    "linux_do_token": {
      "exists": true,
      "masked": "eyJ0eX...***...abc123"
    },
    "linux_do_connect_token": {
      "exists": true,
      "masked": "sess_...***...xyz"
    },
    "bohe_sign_token": {
      "exists": true,
      "valid": true,
      "masked": "bohe_...***...def"
    }
  }
}
```

**POST /api/token/linux-do**

设置或更新 Linux.do Token。

```json
// Request
{
  "token": "eyJ0eXAiOiJKV1QiLC..."
}

// Response 200
{
  "success": true,
  "message": "Linux.do Token 已保存"
}

// Response 400
{
  "success": false,
  "message": "Token 格式无效"
}
```

**POST /api/token/refresh**

刷新薄荷 Token（使用已存储的 Linux.do Token）。

```json
// Response 200
{
  "success": true,
  "message": "Token 刷新成功",
  "data": {
    "bohe_sign_token": {
      "valid": true,
      "masked": "bohe_...***...new"
    }
  }
}

// Response 400
{
  "success": false,
  "message": "刷新失败：未找到有效的 Linux.do Token"
}
```

#### 4.2.2 签到接口

**POST /api/sign/now**

立即执行签到操作。

```json
// Response 200
{
  "success": true,
  "message": "签到成功",
  "data": {
    "sign_time": "2024-12-28T09:00:00+08:00",
    "reward": "获得 10 积分"
  }
}

// Response 400
{
  "success": false,
  "message": "签到失败：今日已签到"
}
```

**GET /api/sign/status**

获取当前签到状态。

```json
// Response 200
{
  "success": true,
  "data": {
    "signed_today": true,
    "last_sign_time": "2024-12-28T09:00:00+08:00",
    "continuous_days": 7,
    "total_signs": 30
  }
}
```

**GET /api/sign/logs**

获取签到日志列表。

```json
// Request Query Params
// ?page=1&limit=10

// Response 200
{
  "success": true,
  "data": {
    "total": 30,
    "page": 1,
    "limit": 10,
    "logs": [
      {
        "id": 1,
        "time": "2024-12-28T09:00:00+08:00",
        "status": "success",
        "message": "签到成功，获得 10 积分",
        "trigger": "manual"
      },
      {
        "id": 2,
        "time": "2024-12-27T08:00:00+08:00",
        "status": "success",
        "message": "签到成功，获得 10 积分",
        "trigger": "scheduled"
      }
    ]
  }
}
```

#### 4.2.3 定时任务接口

**GET /api/schedule**

获取当前定时任务配置。

```json
// Response 200
{
  "success": true,
  "data": {
    "enabled": true,
    "time": "08:00",
    "next_run": "2024-12-29T08:00:00+08:00",
    "last_run": "2024-12-28T08:00:00+08:00"
  }
}

// Response 200 (无定时任务)
{
  "success": true,
  "data": {
    "enabled": false,
    "time": null,
    "next_run": null,
    "last_run": null
  }
}
```

**POST /api/schedule**

创建或更新定时任务。

```json
// Request
{
  "enabled": true,
  "time": "08:00"
}

// Response 200
{
  "success": true,
  "message": "定时任务已设置",
  "data": {
    "enabled": true,
    "time": "08:00",
    "next_run": "2024-12-29T08:00:00+08:00"
  }
}

// Response 400
{
  "success": false,
  "message": "时间格式无效，请使用 HH:MM 格式"
}
```

**DELETE /api/schedule**

删除定时任务。

```json
// Response 200
{
  "success": true,
  "message": "定时任务已删除"
}
```

### 4.3 通用响应格式

所有 API 响应遵循统一格式：

```json
{
  "success": boolean,       // 操作是否成功
  "message": string,        // 可选，操作结果消息
  "data": object | null     // 可选，返回数据
}
```

### 4.4 错误响应

```json
// 400 Bad Request
{
  "success": false,
  "message": "请求参数错误",
  "errors": ["token 字段不能为空"]
}

// 500 Internal Server Error
{
  "success": false,
  "message": "服务器内部错误"
}
```

---

## 5. 前端页面设计

### 5.1 页面布局

采用单页面卡片式布局，从上到下依次为：

```
┌─────────────────────────────────────────────────────────────┐
│                         Header                               │
│                    薄荷签到控制面板                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      状态概览卡片                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ Token 状态   │  │ 今日签到    │  │  连续签到天数        │ │
│  │ ✓ 有效      │  │ ✓ 已完成    │  │  7 天               │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    Token 管理卡片                            │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  Linux.do Token                                        │ │
│  │  [********************]  [保存]                        │ │
│  └───────────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  [刷新薄荷 Token]                                      │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    签到操作卡片                              │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  [立即签到]                                            │ │
│  └───────────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  自动签到时间:  [08:00]  [启用/禁用]                   │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    签到日志卡片                              │
│  ┌─────────┬────────────┬──────────┬────────────────────┐  │
│  │  时间   │   状态     │  触发方式 │   消息             │  │
│  ├─────────┼────────────┼──────────┼────────────────────┤  │
│  │ 12-28   │  ✓ 成功   │   手动    │  获得 10 积分      │  │
│  │ 12-27   │  ✓ 成功   │   定时    │  获得 10 积分      │  │
│  │ 12-26   │  ✗ 失败   │   定时    │  Token 已过期      │  │
│  └─────────┴────────────┴──────────┴────────────────────┘  │
│                      [加载更多]                              │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 设计要点

#### 5.2.1 响应式设计

```css
/* 移动端优先设计 */
.container {
  max-width: 800px;
  margin: 0 auto;
  padding: 1rem;
}

.card {
  background: var(--card-bg);
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* 状态指示器网格 */
.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 1rem;
}

/* 移动端适配 */
@media (max-width: 480px) {
  .status-grid {
    grid-template-columns: 1fr;
  }
}
```

#### 5.2.2 CSS 变量主题

```css
:root {
  /* 主色调 - 薄荷绿 */
  --primary-color: #00b894;
  --primary-hover: #00a085;
  
  /* 状态颜色 */
  --success-color: #00b894;
  --error-color: #e74c3c;
  --warning-color: #f39c12;
  
  /* 背景与文字 */
  --bg-color: #f5f6fa;
  --card-bg: #ffffff;
  --text-color: #2d3436;
  --text-secondary: #636e72;
  
  /* 边框与阴影 */
  --border-color: #dfe6e9;
  --shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* 深色模式支持（可选） */
@media (prefers-color-scheme: dark) {
  :root {
    --bg-color: #1a1a2e;
    --card-bg: #16213e;
    --text-color: #eaeaea;
    --text-secondary: #a0a0a0;
  }
}
```

#### 5.2.3 交互反馈

```javascript
// 按钮点击状态
async function handleSignNow() {
  const btn = document.getElementById('sign-btn');
  btn.disabled = true;
  btn.textContent = '签到中...';
  
  try {
    const response = await fetch('/api/sign/now', { method: 'POST' });
    const result = await response.json();
    
    if (result.success) {
      showToast('签到成功！', 'success');
      refreshStatus();
    } else {
      showToast(result.message, 'error');
    }
  } catch (error) {
    showToast('网络错误', 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = '立即签到';
  }
}

// Toast 通知
function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);
  
  setTimeout(() => toast.remove(), 3000);
}
```

#### 5.2.4 状态指示器组件

```html
<!-- 状态徽章 -->
<div class="status-badge status-valid">
  <span class="status-icon">✓</span>
  <span class="status-text">Token 有效</span>
</div>

<div class="status-badge status-invalid">
  <span class="status-icon">✗</span>
  <span class="status-text">Token 无效</span>
</div>
```

```css
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 0.875rem;
}

.status-valid {
  background: rgba(0, 184, 148, 0.1);
  color: var(--success-color);
}

.status-invalid {
  background: rgba(231, 76, 60, 0.1);
  color: var(--error-color);
}
```

---

## 6. Docker 部署配置更新

### 6.1 更新后的 Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=1.8.4 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

ENV PATH="$POETRY_HOME/bin:$PATH"

RUN pip install poetry==$POETRY_VERSION

COPY pyproject.toml poetry.lock* ./

RUN poetry install --no-root --only main

COPY . .

RUN mkdir -p /app/data

VOLUME ["/app/data"]

# 暴露 Web 服务端口
EXPOSE 8000

# 启动 Web 服务
CMD ["uvicorn", "web.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 6.2 更新后的 docker-compose.yml

```yaml
services:
  bohe-auto-sign:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: bohe-auto-sign
    restart: unless-stopped
    ports:
      - "8000:8000"      # 暴露 Web 控制面板端口
    volumes:
      - ./data:/app/data  # 持久化数据目录
    environment:
      - TZ=Asia/Shanghai
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
```

---

## 7. 签到逻辑实现要点

### 7.1 签到 API 调用

基于现有代码分析，薄荷签到 API 应位于 `https://qd.x666.me/api/`。签到模块需要实现：

```python
# bohe_sign/sign.py

from curl_cffi import requests
from store.token import load_tokens
from store.log import add_sign_log

IMPERSONATE = "chrome"
SIGN_API = "https://qd.x666.me/api/user/sign"

async def do_sign() -> dict:
    """执行签到操作"""
    tokens = load_tokens()
    bohe_token = tokens.get("bohe_sign_token")
    
    if not bohe_token:
        return {"success": False, "message": "未找到有效的薄荷 Token"}
    
    try:
        async with requests.AsyncSession() as session:
            r = await session.post(
                SIGN_API,
                headers={"Authorization": f"Bearer {bohe_token}"},
                json={},
                impersonate=IMPERSONATE
            )
            result = r.json()
            
            # 记录日志
            log_entry = {
                "status": "success" if result.get("success") else "failed",
                "message": result.get("message", ""),
                "trigger": "manual"  # 或 "scheduled"
            }
            add_sign_log(log_entry)
            
            return result
    except Exception as e:
        add_sign_log({"status": "failed", "message": str(e), "trigger": "manual"})
        return {"success": False, "message": f"签到请求失败: {e}"}
```

### 7.2 APScheduler 配置

```python
# web/scheduler.py

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.triggers.cron import CronTrigger
from store.config import load_config, save_config
from bohe_sign.sign import do_sign

scheduler = AsyncIOScheduler(
    jobstores={"default": MemoryJobStore()},
    timezone="Asia/Shanghai"
)

SIGN_JOB_ID = "daily_sign"

async def scheduled_sign():
    """定时签到任务"""
    result = await do_sign()
    # 更新日志中的触发方式为 scheduled
    return result

def setup_scheduler():
    """初始化调度器，从配置恢复任务"""
    config = load_config()
    
    if config.get("schedule_enabled") and config.get("schedule_time"):
        hour, minute = map(int, config["schedule_time"].split(":"))
        scheduler.add_job(
            scheduled_sign,
            CronTrigger(hour=hour, minute=minute),
            id=SIGN_JOB_ID,
            replace_existing=True
        )
    
    scheduler.start()

def update_schedule(enabled: bool, time_str: str | None):
    """更新定时任务配置"""
    # 先移除现有任务
    if scheduler.get_job(SIGN_JOB_ID):
        scheduler.remove_job(SIGN_JOB_ID)
    
    if enabled and time_str:
        hour, minute = map(int, time_str.split(":"))
        scheduler.add_job(
            scheduled_sign,
            CronTrigger(hour=hour, minute=minute),
            id=SIGN_JOB_ID,
            replace_existing=True
        )
    
    # 保存配置
    save_config({"schedule_enabled": enabled, "schedule_time": time_str})
```

---

## 8. 数据存储格式

### 8.1 config.json

```json
{
  "schedule_enabled": true,
  "schedule_time": "08:00",
  "last_modified": "2024-12-28T10:00:00+08:00"
}
```

### 8.2 sign_log.json

```json
{
  "logs": [
    {
      "id": 1,
      "time": "2024-12-28T09:00:00+08:00",
      "status": "success",
      "message": "签到成功，获得 10 积分",
      "trigger": "manual"
    },
    {
      "id": 2,
      "time": "2024-12-27T08:00:00+08:00",
      "status": "success",
      "message": "签到成功，获得 10 积分",
      "trigger": "scheduled"
    }
  ],
  "stats": {
    "total_signs": 30,
    "continuous_days": 7,
    "last_sign_date": "2024-12-28"
  }
}
```

---

## 9. 实现步骤建议

1. **第一阶段：基础框架搭建**
   - 创建 `web/` 目录结构
   - 实现 FastAPI 应用基础配置
   - 添加静态文件服务
   - 创建基础 HTML 页面

2. **第二阶段：Token 管理功能**
   - 实现 Token 相关 API
   - 扩展 [`store/token.py`](store/token.py:1) 添加状态查询方法
   - 前端 Token 管理界面

3. **第三阶段：签到功能**
   - 实现 [`bohe_sign/sign.py`](bohe_sign/sign.py:1) 签到逻辑
   - 创建 [`store/log.py`](store/log.py:1) 日志存储
   - 签到 API 和前端界面

4. **第四阶段：定时任务**
   - 配置 APScheduler
   - 实现定时任务 API
   - 前端定时任务配置界面

5. **第五阶段：Docker 部署优化**
   - 更新 Dockerfile 和 docker-compose.yml
   - 添加健康检查
   - 测试容器化部署

---

## 10. 安全考虑

1. **Token 安全**：前端显示 Token 时进行脱敏处理（仅显示前后几位）
2. **CORS 配置**：生产环境限制允许的来源
3. **请求频率限制**：防止恶意调用签到 API
4. **日志清理**：定期清理过期的签到日志

---

## 11. 扩展功能（可选）

1. **多账号支持**：支持管理多个 Linux.do 账号
2. **通知功能**：签到结果推送（邮件、Webhook 等）
3. **数据统计**：签到统计图表
4. **API Token 认证**：保护 API 接口