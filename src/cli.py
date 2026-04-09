import sys
import re
import asyncio
from typing import Callable, Optional

from src.run import TaskRunner
from src.tasks.register import (
    TaskModule,
    get_module_tasks,
    get_module_metadata,
)
from src.utils.config import Config


def _build_patterns():
    """动态构建正则表达式模式"""
    module_names = "|".join(re.escape(m.value) for m in TaskModule)
    return {
        "qq_module_task": re.compile(
            rf"^(\d+)\.({module_names})\.(.+)$", re.IGNORECASE
        ),
        "qq_module": re.compile(rf"^(\d+)\.({module_names})$", re.IGNORECASE),
        "module_task": re.compile(rf"^({module_names})\.(.+)$", re.IGNORECASE),
        "module": re.compile(rf"^({module_names})$", re.IGNORECASE),
    }


def _validate_task_name(task_name: str, registry: dict, module: str) -> None:
    """验证任务名称是否存在"""
    if task_name not in registry:
        available = "\n  ".join(registry.keys())
        raise ValueError(
            f"模块 '{module}' 未注册 '{task_name}' 任务\n\n可用任务: \n  {available}"
        )


def parse_arg(arg: str) -> tuple[Optional[str], TaskModule, Optional[str]]:
    """
    解析命令行参数，支持四种格式：
    1. module                  -> (None, TaskModule, None)
    2. module.task             -> (None, TaskModule, task)
    3. qq.module               -> (qq, TaskModule, None)
    4. qq.module.task          -> (qq, TaskModule, task)
    """
    patterns = _build_patterns()

    # 模式4: QQ号.模块名称.任务名称
    if result := patterns["qq_module_task"].match(arg):
        qq, module_val, task_name = result.groups()
        module = TaskModule(module_val.lower())
        registry = get_module_tasks(module)
        _validate_task_name(task_name, registry, module.value)
        return qq, module, task_name

    # 模式3: QQ号.模块名称
    if result := patterns["qq_module"].match(arg):
        qq, module_val = result.groups()
        module = TaskModule(module_val.lower())
        return qq, module, None

    # 模式2: 模块名称.任务名称
    if result := patterns["module_task"].match(arg):
        module_val, task_name = result.groups()
        module = TaskModule(module_val.lower())
        registry = get_module_tasks(module)
        _validate_task_name(task_name, registry, module.value)
        return None, module, task_name

    # 模式1: 模块名称
    if result := patterns["module"].match(arg):
        module = TaskModule(result.group(1).lower())
        return None, module, None

    # 构建错误信息
    available_modules = ", ".join(m.value for m in TaskModule)
    raise ValueError(
        f"参数格式错误: '{arg}'\n"
        f"支持的格式:\n"
        f"  1. 模块名称                 (如: {available_modules})\n"
        f"  2. 模块名称.任务名称         (如: noon.邪神秘宝)\n"
        f"  3. QQ号.模块名称             (如: 123456789.noon)\n"
        f"  4. QQ号.模块名称.任务名称     (如: 123456789.noon.邪神秘宝)\n"
        f"\n可用模块: {available_modules}\n"
        f"帮助命令: uv run main.py -h"
    )


def show_help() -> None:
    """动态生成帮助信息"""
    lines = [
        "Q宠大乐斗自动化助手",
        "",
        "用法:",
        "  uv run main.py -> 启动定时任务调度器",
        "  uv run main.py <参数> -> 执行指定任务",
        "",
        "参数格式（四种组合）:",
        "  1. 模块名称 -> 执行所有账号的该模块所有任务",
        "     示例: uv run main.py noon",
        "           uv run main.py evening",
        "",
        "  2. 模块名称.任务名称 -> 执行所有账号的该模块指定任务",
        "     示例: uv run main.py noon.邪神秘宝",
        "           uv run main.py evening.邪神秘宝",
        "",
        "  3. QQ号.模块名称 -> 执行该账号的该模块所有任务",
        "     示例: uv run main.py 123456789.noon",
        "           uv run main.py 987654321.evening",
        "",
        "  4. QQ号.模块名称.任务名称 -> 执行该账号该模块的指定任务",
        "     示例: uv run main.py 123456789.noon.邪神秘宝",
        "           uv run main.py 987654321.evening.邪神秘宝",
        "",
        "可用模块及任务:",
    ]

    # 动态生成各模块任务列表
    for module in TaskModule:
        metadata = get_module_metadata(module)
        schedule = metadata.get("schedule_time", "未设置")
        desc = metadata.get("description", "")

        lines.append(f"\n  {module.value} 模块 ({desc}, 建议 {schedule} 后执行):")

        tasks = get_module_tasks(module)
        if tasks:
            for name in tasks.keys():
                lines.append(f"    - {name}")
        else:
            lines.append("    (暂无注册任务)")
    print("\n".join(lines))


def _filter_registry_by_task(
    registry: dict[str, Callable], task_name: Optional[str]
) -> dict[str, Callable]:
    """根据任务名称过滤注册表"""
    if task_name is None:
        return registry

    if task_name not in registry:
        print(f"警告: 任务 '{task_name}' 不存在于当前模块")
        print(f"可用任务: {', '.join(registry.keys())}")
        return {}

    return {task_name: registry[task_name]}


def _run_single_arg(arg: str) -> None:
    """处理单个命令行参数"""
    try:
        qq, module, task_name = parse_arg(arg)
    except ValueError as e:
        print(e)
        sys.exit(1)

    # 获取对应模块的注册表
    full_registry = get_module_tasks(module)

    # 根据任务名称过滤
    registry = _filter_registry_by_task(full_registry, task_name)
    if not registry:
        sys.exit(1)

    # 加载Cookie并执行
    cookies = Config.load_cookies(qq)
    if not cookies:
        if qq:
            print(f"账号 {qq} 不存在或未配置 Cookie")
        else:
            print(f"请在 {Config.DLD_COOKIE_CONFIG_PATH} 中配置大乐斗 Cookie")
        sys.exit(1)

    asyncio.run(TaskRunner(cookies, module, registry).run())


def main() -> None:
    """主入口函数"""
    args = sys.argv[1:]

    # 无参数：启动定时任务调度器
    if len(args) == 0:
        from src.timing import execute_timing

        execute_timing()
        return

    # 帮助参数
    if len(args) == 1 and args[0] in ("-h", "--help", "help"):
        show_help()
        return

    # 单参数：解析并执行指定任务
    if len(args) == 1:
        _run_single_arg(args[0])
        return

    print(f"错误: 提供了 {len(args)} 个参数，只支持 0 或 1 个参数")
    print("使用 -h 或 --help 查看帮助")
