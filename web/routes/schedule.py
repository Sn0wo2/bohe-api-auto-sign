"""定时任务相关 API"""

import re
from typing import Any, Dict, Optional

from fastapi import APIRouter
from pydantic import BaseModel, field_validator

from web.scheduler import get_schedule_status, update_schedule, delete_schedule

router = APIRouter()


class ScheduleRequest(BaseModel):
    """设置定时任务请求体"""
    enabled: bool = True
    time: Optional[str] = None
    
    @field_validator("time")
    @classmethod
    def validate_time(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        # 验证时间格式 HH:MM
        if not re.match(r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$", v):
            raise ValueError("时间格式无效，请使用 HH:MM 格式")
        return v


class ApiResponse(BaseModel):
    """通用 API 响应"""
    success: bool
    message: str = ""
    data: Dict[str, Any] = {}


@router.get("", response_model=ApiResponse)
async def get_schedule() -> ApiResponse:
    """获取当前定时任务配置"""
    status = get_schedule_status()
    
    return ApiResponse(
        success=True,
        data=status
    )


@router.post("", response_model=ApiResponse)
async def set_schedule(request: ScheduleRequest) -> ApiResponse:
    """设置定时签到任务"""
    if request.enabled and not request.time:
        return ApiResponse(
            success=False,
            message="启用定时任务时必须指定时间"
        )
    
    result = update_schedule(
        enabled=request.enabled,
        time_str=request.time
    )
    
    return ApiResponse(
        success=result.get("success", False),
        message=result.get("message", ""),
        data=result.get("data", {})
    )


@router.delete("", response_model=ApiResponse)
async def remove_schedule() -> ApiResponse:
    """删除定时任务"""
    result = delete_schedule()
    
    return ApiResponse(
        success=result.get("success", False),
        message=result.get("message", "定时任务已删除")
    )