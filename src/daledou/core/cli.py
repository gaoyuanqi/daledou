import argparse
import time
from importlib import import_module

from schedule import every, repeat, run_pending

from .daledou import (
    ModulePath,
    print_separator,
    Runtime,
    TaskSchedule,
    TaskType,
    TIMING_INFO,
)


@repeat(every().day.at(Runtime.ONE.value))
def _run_one():
    # 每天定时运行第一轮任务
    TaskSchedule.run(TaskType.ONE, import_module(ModulePath.ONE.value))
    print(TIMING_INFO)
    print_separator()


@repeat(every().day.at(Runtime.TWO.value))
def _run_two():
    # 每天定时运行第二轮任务
    TaskSchedule.run(TaskType.TWO, import_module(ModulePath.TWO.value))
    print(TIMING_INFO)
    print_separator()


def run_serve() -> None:
    """命令行入口点"""
    parser = argparse.ArgumentParser(
        description="大乐斗任务调度程序", formatter_class=argparse.RawTextHelpFormatter
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--timing", action="store_true", help="启动定时任务守护进程")
    group.add_argument("--other", action="store_true", help="执行其他任务")
    group.add_argument(
        "--one",
        nargs="*",
        metavar="FUNC",
        help="执行第一轮所有任务（可选具体函数）\n示例: --one 邪神秘宝",
    )
    group.add_argument(
        "--two",
        nargs="*",
        metavar="FUNC",
        help="执行第二轮所有任务（可选具体函数）\n示例: --two 邪神秘宝",
    )

    print_separator()
    args = parser.parse_args()
    if args.timing:
        TaskSchedule.debug_run_timing()
        while True:
            run_pending()
            time.sleep(1)
    elif args.one is not None:
        module_type = import_module(ModulePath.ONE.value)
        if args.one:
            TaskSchedule.debug_run(TaskType.ONE, args.one, module_type)
        else:
            TaskSchedule.run(TaskType.ONE, module_type)
    elif args.two is not None:
        module_type = import_module(ModulePath.TWO.value)
        if args.two:
            TaskSchedule.debug_run(TaskType.TWO, args.two, module_type)
        else:
            TaskSchedule.run(TaskType.TWO, module_type)
    elif args.other is not None:
        TaskSchedule.debug_run_other(import_module(ModulePath.OTHER.value))
