"""FastAPI 应用主入口"""

import os
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from web.routes import api_router
from web.scheduler import setup_scheduler, shutdown_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化调度器
    print("正在启动应用...")
    setup_scheduler()
    
    yield
    
    # 关闭时清理调度器
    print("正在关闭应用...")
    shutdown_scheduler()


# 创建 FastAPI 应用
app = FastAPI(
    title="薄荷签到控制面板",
    description="薄荷签到自动化工具 Web 控制界面",
    version="0.1.0",
    lifespan=lifespan
)


# 注册 API 路由
app.include_router(api_router)


# 健康检查端点
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """健康检查"""
    return {"status": "ok"}


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """全局异常处理器"""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": f"服务器内部错误: {str(exc)}"
        }
    )


# 静态文件目录
static_dir = os.path.join(os.path.dirname(__file__), "static")

# 根路径返回 index.html
@app.get("/")
async def serve_index():
    """返回主页面"""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse(
        status_code=404,
        content={"success": False, "message": "页面未找到"}
    )


# 挂载静态文件目录（CSS、JS 等资源）
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)