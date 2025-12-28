"""签到日志存储模块 - 管理签到日志的读写操作"""

import json
import os
from datetime import datetime, date
from typing import Any, Dict, List, Optional

LOG_FILE = "./data/sign_log.json"
MAX_LOGS = 50  # 保存最近 50 条记录


def _ensure_data_dir() -> None:
    """确保 data 目录存在"""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)


def _get_default_data() -> Dict[str, Any]:
    """获取默认的日志数据结构"""
    return {
        "logs": [],
        "stats": {
            "total_signs": 0,
            "continuous_days": 0,
            "last_sign_date": None
        }
    }


def load_logs() -> Dict[str, Any]:
    """加载签到日志数据"""
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return _get_default_data()


def save_logs(data: Dict[str, Any]) -> bool:
    """保存签到日志数据
    
    Args:
        data: 日志数据字典
        
    Returns:
        是否保存成功
    """
    _ensure_data_dir()
    
    try:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving logs: {e}")
        return False


def add_sign_log(
    status: str,
    message: str,
    trigger: str = "manual"
) -> Dict[str, Any]:
    """添加签到日志
    
    Args:
        status: 签到状态 (success/failed)
        message: 签到消息
        trigger: 触发方式 (manual/scheduled)
        
    Returns:
        新添加的日志条目
    """
    data = load_logs()
    logs = data.get("logs", [])
    stats = data.get("stats", {})
    
    # 生成新的日志 ID
    new_id = 1
    if logs:
        new_id = max(log.get("id", 0) for log in logs) + 1
    
    # 创建日志条目
    now = datetime.now()
    log_entry = {
        "id": new_id,
        "time": now.isoformat(),
        "status": status,
        "message": message,
        "trigger": trigger
    }
    
    # 添加到日志列表头部
    logs.insert(0, log_entry)
    
    # 保持最多 MAX_LOGS 条记录
    if len(logs) > MAX_LOGS:
        logs = logs[:MAX_LOGS]
    
    # 更新统计数据
    today_str = now.date().isoformat()
    
    if status == "success":
        stats["total_signs"] = stats.get("total_signs", 0) + 1
        
        last_sign_date = stats.get("last_sign_date")
        
        if last_sign_date:
            try:
                last_date = date.fromisoformat(last_sign_date)
                today = now.date()
                days_diff = (today - last_date).days
                
                if days_diff == 1:
                    # 连续签到
                    stats["continuous_days"] = stats.get("continuous_days", 0) + 1
                elif days_diff > 1:
                    # 连续签到中断
                    stats["continuous_days"] = 1
                # days_diff == 0 表示同一天重复签到，不更新连续天数
            except ValueError:
                stats["continuous_days"] = 1
        else:
            stats["continuous_days"] = 1
        
        stats["last_sign_date"] = today_str
    
    data["logs"] = logs
    data["stats"] = stats
    save_logs(data)
    
    return log_entry


def get_sign_logs(page: int = 1, limit: int = 10) -> Dict[str, Any]:
    """获取签到日志列表（分页）
    
    Args:
        page: 页码（从 1 开始）
        limit: 每页数量
        
    Returns:
        包含分页信息和日志列表的字典
    """
    data = load_logs()
    logs = data.get("logs", [])
    total = len(logs)
    
    # 计算分页
    start = (page - 1) * limit
    end = start + limit
    page_logs = logs[start:end]
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "logs": page_logs
    }


def get_sign_stats() -> Dict[str, Any]:
    """获取签到统计数据
    
    Returns:
        签到统计数据字典
    """
    data = load_logs()
    stats = data.get("stats", {})
    logs = data.get("logs", [])
    
    # 检查今日是否已签到
    signed_today = False
    last_sign_time = None
    today_str = date.today().isoformat()
    
    if logs:
        for log in logs:
            if log.get("status") == "success":
                log_time = log.get("time", "")
                if log_time:
                    try:
                        log_date = datetime.fromisoformat(log_time).date()
                        if log_date.isoformat() == today_str:
                            signed_today = True
                            last_sign_time = log_time
                            break
                        # 找到最近一次成功签到时间
                        if last_sign_time is None:
                            last_sign_time = log_time
                    except ValueError:
                        pass
    
    return {
        "signed_today": signed_today,
        "last_sign_time": last_sign_time,
        "continuous_days": stats.get("continuous_days", 0),
        "total_signs": stats.get("total_signs", 0)
    }