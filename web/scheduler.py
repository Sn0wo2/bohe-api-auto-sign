"""APScheduler 定时任务管理模块"""

import asyncio
from datetime import datetime
from typing import Any, Dict, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from store.config import load_config, save_config

# 调度器实例
scheduler: Optional[AsyncIOScheduler] = None

# 签到任务 ID
SIGN_JOB_ID = "daily_sign"


async def scheduled_sign() -> None:
    """定时签到任务"""
    # 延迟导入避免循环依赖
    from bohe_sign.sign import do_sign
    
    print(f"[{datetime.now().isoformat()}] 执行定时签到任务...")
    result = await do_sign(trigger="scheduled")
    
    if result.get("success"):
        print(f"[{datetime.now().isoformat()}] 定时签到成功: {result.get('message')}")
    else:
        print(f"[{datetime.now().isoformat()}] 定时签到失败: {result.get('message')}")


def get_scheduler() -> AsyncIOScheduler:
    """获取调度器实例"""
    global scheduler
    if scheduler is None:
        scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")
    return scheduler


def setup_scheduler() -> None:
    """初始化调度器，从配置恢复任务"""
    global scheduler
    scheduler = get_scheduler()
    
    config = load_config()
    
    if config.get("schedule_enabled") and config.get("schedule_time"):
        time_str = config["schedule_time"]
        try:
            hour, minute = map(int, time_str.split(":"))
            scheduler.add_job(
                scheduled_sign,
                CronTrigger(hour=hour, minute=minute),
                id=SIGN_JOB_ID,
                replace_existing=True
            )
            print(f"已恢复定时签到任务，每日 {time_str} 执行")
        except ValueError as e:
            print(f"恢复定时任务失败，时间格式错误: {e}")
    
    if not scheduler.running:
        scheduler.start()
        print("调度器已启动")


def shutdown_scheduler() -> None:
    """关闭调度器"""
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown()
        print("调度器已关闭")


def update_schedule(enabled: bool, time_str: Optional[str] = None) -> Dict[str, Any]:
    """更新定时任务配置
    
    Args:
        enabled: 是否启用定时任务
        time_str: 定时时间，格式为 HH:MM
        
    Returns:
        更新结果字典
    """
    global scheduler
    
    if scheduler is None:
        scheduler = get_scheduler()
        if not scheduler.running:
            scheduler.start()
    
    # 先移除现有任务
    existing_job = scheduler.get_job(SIGN_JOB_ID)
    if existing_job:
        scheduler.remove_job(SIGN_JOB_ID)
    
    next_run = None
    
    if enabled and time_str:
        try:
            hour, minute = map(int, time_str.split(":"))
            
            # 验证时间格式
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                return {
                    "success": False,
                    "message": "时间格式无效，小时必须在 0-23 之间，分钟必须在 0-59 之间"
                }
            
            trigger = CronTrigger(hour=hour, minute=minute)
            job = scheduler.add_job(
                scheduled_sign,
                trigger,
                id=SIGN_JOB_ID,
                replace_existing=True
            )
            
            next_run = job.next_run_time.isoformat() if job.next_run_time else None
            print(f"定时签到任务已设置，每日 {time_str} 执行，下次运行: {next_run}")
            
        except ValueError:
            return {
                "success": False,
                "message": "时间格式无效，请使用 HH:MM 格式"
            }
    
    # 保存配置
    config = load_config()
    config["schedule_enabled"] = enabled
    config["schedule_time"] = time_str if enabled else None
    save_config(config)
    
    return {
        "success": True,
        "message": "定时任务已设置" if enabled else "定时任务已取消",
        "data": {
            "enabled": enabled,
            "time": time_str,
            "next_run": next_run
        }
    }


def get_schedule_status() -> Dict[str, Any]:
    """获取定时任务状态
    
    Returns:
        定时任务状态字典
    """
    global scheduler
    config = load_config()
    
    enabled = config.get("schedule_enabled", False)
    time_str = config.get("schedule_time")
    next_run = None
    last_run = None
    
    if scheduler:
        job = scheduler.get_job(SIGN_JOB_ID)
        if job:
            if job.next_run_time:
                next_run = job.next_run_time.isoformat()
    
    return {
        "enabled": enabled,
        "time": time_str,
        "next_run": next_run,
        "last_run": last_run
    }


def delete_schedule() -> Dict[str, Any]:
    """删除定时任务
    
    Returns:
        删除结果字典
    """
    return update_schedule(enabled=False, time_str=None)