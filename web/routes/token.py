"""Token 管理相关 API"""

from typing import Any, Dict

from fastapi import APIRouter
from pydantic import BaseModel

from store.token import load_tokens, save_tokens
from bohe_sign.login import get_bohe_token, verify_bohe_token

router = APIRouter()


class SetTokenRequest(BaseModel):
    """设置 Token 请求体"""
    token: str


class ApiResponse(BaseModel):
    """通用 API 响应"""
    success: bool
    message: str = ""
    data: Dict[str, Any] = {}


def mask_token(token: str, show_chars: int = 6) -> str:
    """对 Token 进行脱敏处理
    
    Args:
        token: 原始 Token
        show_chars: 首尾显示的字符数
        
    Returns:
        脱敏后的 Token
    """
    if not token:
        return ""
    if len(token) <= show_chars * 2:
        return token[:2] + "***" + token[-2:] if len(token) > 4 else "***"
    return token[:show_chars] + "***" + token[-show_chars:]


@router.get("/status", response_model=ApiResponse)
async def get_token_status() -> ApiResponse:
    """获取所有 Token 的状态"""
    tokens = load_tokens()
    
    linux_do_token = tokens.get("linux_do_token", "")
    linux_do_connect_token = tokens.get("linux_do_connect_token", "")
    bohe_sign_token = tokens.get("bohe_sign_token", "")
    
    # 检查薄荷 Token 是否有效
    bohe_valid = False
    if bohe_sign_token:
        bohe_valid = await verify_bohe_token(bohe_sign_token)
    
    return ApiResponse(
        success=True,
        data={
            "linux_do_token": {
                "exists": bool(linux_do_token),
                "masked": mask_token(linux_do_token) if linux_do_token else None
            },
            "linux_do_connect_token": {
                "exists": bool(linux_do_connect_token),
                "masked": mask_token(linux_do_connect_token) if linux_do_connect_token else None
            },
            "bohe_sign_token": {
                "exists": bool(bohe_sign_token),
                "valid": bohe_valid,
                "masked": mask_token(bohe_sign_token) if bohe_sign_token else None
            }
        }
    )


@router.post("/set", response_model=ApiResponse)
async def set_linux_do_token(request: SetTokenRequest) -> ApiResponse:
    """设置 Linux.do Token"""
    token = request.token.strip()
    
    if not token:
        return ApiResponse(
            success=False,
            message="Token 不能为空"
        )
    
    # 保存 Linux.do Token
    save_tokens(linux_do_token=token)
    
    return ApiResponse(
        success=True,
        message="Linux.do Token 已保存"
    )


@router.post("/refresh", response_model=ApiResponse)
async def refresh_bohe_token() -> ApiResponse:
    """刷新薄荷 Token（使用已存储的 Linux.do Token）"""
    tokens = load_tokens()
    linux_do_token = tokens.get("linux_do_token", "")
    
    if not linux_do_token and not tokens.get("linux_do_connect_token"):
        return ApiResponse(
            success=False,
            message="刷新失败：未找到有效的 Linux.do Token，请先设置 Token"
        )
    
    try:
        # 尝试获取新的薄荷 Token
        new_bohe_token, new_connect_token, new_ld_token = await get_bohe_token(linux_do_token)
        
        if new_bohe_token:
            return ApiResponse(
                success=True,
                message="Token 刷新成功",
                data={
                    "bohe_sign_token": {
                        "valid": True,
                        "masked": mask_token(new_bohe_token)
                    }
                }
            )
        else:
            return ApiResponse(
                success=False,
                message="刷新失败：无法获取薄荷 Token，请检查 Linux.do Token 是否有效"
            )
            
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"刷新失败：{str(e)}"
        )