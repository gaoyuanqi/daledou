import argparse
import textwrap
import time
from importlib import import_module

from schedule import every, repeat, run_pending

from .daledou import (
    get_all_qq,
    generate_dld_debug_instances,
    Input,
    ModulePath,
    print_separator,
    run_account_tasks,
    Runtime,
    TaskExecutor,
    TaskType,
)

MODULE_TYPE_ONE = import_module(ModulePath.ONE.value)
MODULE_TYPE_TWO = import_module(ModulePath.TWO.value)
TIMING_INFO = textwrap.dedent(f"""
    定时任务守护进程已启动：
    第一轮默认 {Runtime.ONE.value} 定时运行
    第二轮默认 {Runtime.TWO.value} 定时运行

    任务配置：config/你的QQ.yaml
    任务日志：log/

    立即运行第一轮命令：
    python main.py --one 或 uv run main.py --one

    立即运行第二轮命令：
    python main.py --two 或 uv run main.py --two

    取消操作按键：CTRL + C（并发需多按几次）
""")


@repeat(every().day.at(Runtime.ONE.value))
def _run_one():
    # 每天定时运行第一轮任务
    TaskExecutor.run(TaskType.ONE, MODULE_TYPE_ONE)
    print(TIMING_INFO)
    print_separator()


@repeat(every().day.at(Runtime.TWO.value))
def _run_two():
    # 每天定时运行第二轮任务
    TaskExecutor.run(TaskType.TWO, MODULE_TYPE_TWO)
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
        for _ in generate_dld_debug_instances(TaskType.TIMING):
            pass
        print_separator()
        print(TIMING_INFO)
        print_separator()
        while True:
            run_pending()
            time.sleep(1)
    elif args.one is not None:
        if args.one:
            for d in generate_dld_debug_instances(TaskType.ONE):
                print_separator()
                run_account_tasks(d, args.one, MODULE_TYPE_ONE)
                print_separator()
                print(d.pushplus_content())
                print_separator()
        else:
            TaskExecutor.run(TaskType.ONE, MODULE_TYPE_ONE)
    elif args.two is not None:
        if args.two:
            for d in generate_dld_debug_instances(TaskType.TWO):
                print_separator()
                run_account_tasks(d, args.two, MODULE_TYPE_TWO)
                print_separator()
                print(d.pushplus_content())
                print_separator()
        else:
            TaskExecutor.run(TaskType.TWO, MODULE_TYPE_TWO)
    elif args.other is not None:
        qq = Input.select("请选择账号：", get_all_qq())
        if qq is None:
            return
        print_separator()
        for d in generate_dld_debug_instances(TaskType.OTHER, qq):
            print_separator()
            task_name = Input.select("请选择任务：", d.task_names)
            if task_name is None:
                break
            run_account_tasks(d, [task_name], import_module(ModulePath.OTHER.value))
            print_separator()
