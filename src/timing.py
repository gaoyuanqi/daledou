import asyncio
import time

from schedule import Scheduler, every, idle_seconds, run_pending

from src.run import TaskRunner
from src.tasks.register import (
    TaskModule,
    TASKS_REGISTRY,
    MODULE_METADATA,
    get_all_modules,
)
from src.utils.config import Config


scheduler = Scheduler()


def create_job(module: TaskModule):
    """为指定模块创建任务执行函数"""

    async def job():
        registry = TASKS_REGISTRY.get(module, {})
        if not registry:
            print(f"[定时任务] {module.value} 模块没有注册任务，跳过")
            return

        print(f"[定时任务] 开始执行 {module.value} 模块 ({len(registry)} 个任务)")
        await TaskRunner(
            Config.load_cookies(),
            module,
            registry,
        ).run()
        print(f"[定时任务] {module.value} 模块执行完成")

    return job


def setup_schedule():
    """动态设置所有定时任务"""
    print("-" * 50)
    print("定时任务守护进程已启动")

    scheduled_modules = []

    for module in get_all_modules():
        metadata = MODULE_METADATA.get(module, {})
        schedule_time = metadata.get("schedule_time")

        if schedule_time:
            create_job(module)
            every().day.at(schedule_time).do(
                lambda m=module: asyncio.run(create_job(m)())
            )
            scheduled_modules.append(
                f"  - {module.value}: 每天 {schedule_time}（上海时间）"
            )
        else:
            print(f"  - {module.value}: 未设置执行时间（仅支持手动触发）")

    if scheduled_modules:
        print("\n已配置定时任务:")
        for line in scheduled_modules:
            print(line)
    else:
        print("\n警告: 没有配置任何定时任务")

    print("-" * 50)


def execute_timing() -> None:
    """启动定时任务循环"""
    while True:
        setup_schedule()
        n = idle_seconds()
        if n is None:
            break
        elif n > 0:
            time.sleep(n)
        run_pending()
