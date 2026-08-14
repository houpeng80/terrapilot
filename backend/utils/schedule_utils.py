import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler

from backend.utils.github_utils import pull_code

logger = logging.getLogger(__name__)

def sync_git_code_task():
    logger.info(f"begin to pull latest code from github: %s", {time.time()})
    pull_code()

scheduler = BackgroundScheduler()

def start_scheduler_sync_git_code():
    """项目启动时初始化并开启定时"""
    # 添加任务：每10分钟执行一次
    scheduler.add_job(
        sync_git_code_task,
        trigger="interval",
        seconds=600,
        id="git_sync_job",
        replace_existing=True,
        max_instances=1
    )
    # 启动后台定时
    if not scheduler.running:
        scheduler.start()
    logger.info("Scheduled task to pull code from GitHub has started and is running in the background.")

def stop_scheduler_sync_git_code():
    """程序退出优雅关闭"""
    if scheduler.running:
        scheduler.shutdown()

if __name__ == "__main__":
    # ========== 项目启动入口：先开启定时 ==========
    start_scheduler_sync_git_code()

    # 主线程正常跑其他业务逻辑，不会被定时阻塞
    try:
        while True:
            print("主程序运行中...")
            time.sleep(10)
    except KeyboardInterrupt:
        print("收到退出信号，关闭定时任务")
        stop_scheduler_sync_git_code()
