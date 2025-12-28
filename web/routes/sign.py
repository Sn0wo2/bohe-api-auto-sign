"""签到相关 API"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from bohe_sign.sign import do_sign, get_sign_status
from store.log import get_sign_logs

router = APIRouter()


class ApiResponse(BaseModel):
    """通用 API 响应"""
    success: bool
    message: str = ""
    data: Dict[str, Any] = {}


@router.post("/now", response_model=ApiResponse)
async def sign_now() -> ApiResponse:
    """立即执行签到"""
    result = await do_sign(trigger="manual")
    
    return ApiResponse(
        success=result.get("success", False),
        message=result.get("message", ""),
        data=result.get("data", {})
    )


@router.get("/status", response_model=ApiResponse)
async def get_status() -> ApiResponse:
    """获取签到状态"""
    status = await get_sign_status()
    
    return ApiResponse(
        success=True,
        data=status
    )


@router.get("/logs", response_model=ApiResponse)
async def get_logs(
    page: int = Query(default=1, ge=1, description="页码"),
    limit: int = Query(default=10, ge=1, le=50, description="每页数量")
) -> ApiResponse:
    """获取签到日志列表"""
    logs_data = get_sign_logs(page=page, limit=limit)
    
    return ApiResponse(
        success=True,
        data=logs_data
    )