"""配置存储模块 - 管理定时任务配置等"""

import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

CONFIG_FILE = "./data/config.json"


def _ensure_data_dir() -> None:
    """确保 data 目录存在"""
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)


def load_config() -> Dict[str, Any]:
    """加载配置文件"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    # 返回默认配置
    default_config = {
        "schedule_enabled": False,
        "schedule_time": None,
        "last_modified": None
    }
    return default_config


def save_config(config: Dict[str, Any]) -> bool:
    """保存配置到文件
    
    Args:
        config: 要保存的配置字典
        
    Returns:
        是否保存成功
    """
    _ensure_data_dir()
    
    # 更新修改时间
    config["last_modified"] = datetime.now().isoformat()
    
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False


def get_schedule_config() -> Dict[str, Any]:
    """获取定时任务配置
    
    Returns:
        包含 enabled, time, last_modified 的字典
    """
    config = load_config()
    return {
        "enabled": config.get("schedule_enabled", False),
        "time": config.get("schedule_time"),
        "last_modified": config.get("last_modified")
    }


def set_schedule_config(enabled: bool, time_str: Optional[str] = None) -> bool:
    """设置定时任务配置
    
    Args:
        enabled: 是否启用定时任务
        time_str: 定时时间，格式为 HH:MM
        
    Returns:
        是否设置成功
    """
    config = load_config()
    config["schedule_enabled"] = enabled
    config["schedule_time"] = time_str if enabled else None
    return save_config(config)