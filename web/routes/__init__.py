"""API 路由模块"""

from fastapi import APIRouter

from web.routes import token, sign, schedule

# 创建主 API 路由
api_router = APIRouter(prefix="/api")

# 注册子路由
api_router.include_router(token.router, prefix="/token", tags=["Token 管理"])
api_router.include_router(sign.router, prefix="/sign", tags=["签到"])
api_router.include_router(schedule.router, prefix="/schedule", tags=["定时任务"])