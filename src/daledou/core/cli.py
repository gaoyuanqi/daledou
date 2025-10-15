import os
import time

from schedule import every, repeat, run_pending

from .config import Config
from .daledou import TaskSchedule
from .session import SessionManager
from .utils import (
    EXECUTION_MODE_ENV,
    MODULE_PATH_ONE,
    MODULE_PATH_OTHER,
    MODULE_PATH_TWO,
    TASK_TYPE_ONE,
    TASK_TYPE_OTHER,
    TASK_TYPE_TWO,
    TIMING_INFO,
    TIMING_ONE,
    TIMING_TWO,
    Input,
    get_execution_mode,
    parse_cookie,
    parse_qq_from_cookie,
    print_separator,
)


@repeat(every().day.at(TIMING_ONE))
def job_one():
    """每天定时执行第一轮任务"""
    _execute_one()
    print(TIMING_INFO)
    print_separator()


@repeat(every().day.at(TIMING_TWO))
def job_two():
    """每天定时执行第二轮任务"""
    _execute_two()
    print(TIMING_INFO)
    print_separator()


def _add_account():
    """添加账号"""
    while True:
        print("💡 操作说明：")
        print("• 添加新账号会创建对应的配置文件")
        print("• 如果账号已存在，则会覆盖原有配置\n")
        print("💡 获取大乐斗Cookie流程：")
        print("1. 应用商店下载Via浏览器")
        print("2. 将Via设为默认浏览器")
        print("3. 使用Via一键登录文字版大乐斗")
        print("4. 等待3秒后点击Via左上角✓")
        print("5. 再点击查看Cookies\n")
        cookie = Input.text("请输入大乐斗Cookie：")
        if cookie is None:
            break

        ck = parse_cookie(cookie)
        session = SessionManager.create_verified_session(ck)
        if session is None:
            print("\n❌ Cookie无效或验证失败")
            print_separator()
            continue

        qq = parse_qq_from_cookie(ck)
        Config.create_user_config(f"{qq}.yaml", cookie)
        print(f"\n✅ 账号 {qq} 添加成功！")
        print(f"📁 配置文件：config/{qq}.yaml")
        print_separator()


def _execute_one():
    """执行第一轮任务"""
    TaskSchedule.execute(TASK_TYPE_ONE, MODULE_PATH_ONE)


def _execute_two():
    """执行第二轮任务"""
    TaskSchedule.execute(TASK_TYPE_TWO, MODULE_PATH_TWO)


def _execute_timing():
    """运行定时任务"""
    if not Config.list_all_qq_numbers():
        return
    print(TIMING_INFO)
    print_separator()
    while True:
        run_pending()
        time.sleep(1)


def _execute_tasks():
    """运行任务 - 包含所有任务类型和执行模式选择"""
    modes = {"顺序执行": "sequential", "并发执行": "concurrent"}

    current_mode = get_execution_mode()
    current_mode_name = "顺序执行" if current_mode == "sequential" else "并发执行"

    print(f"💡 当前执行模式: {current_mode_name}")
    print("• 顺序执行：账号依次执行")
    print("• 并发执行：多账号同时执行（最多5个）\n")
    mode = Input.select("请选择执行模式：", list(modes))
    if mode is None:
        return

    os.environ[EXECUTION_MODE_ENV] = modes[mode]
    print(f"已设置为{mode}")
    print_separator()

    # 任务类型
    tasks = {
        "第一轮任务": _execute_one,
        "第二轮任务": _execute_two,
        "定时任务": _execute_timing,
    }

    print("💡 任务类型说明：")
    print("• 第一轮包含绝大部分日常任务，建议 13:01 后执行")
    print("• 第二轮是收尾日常任务，建议 20:01 后执行")
    print("• 定时任务是定时执行第一、二轮任务\n")
    task = Input.select("请选择任务：", list(tasks))
    if task is None:
        return
    tasks[task]()


def _execute_debug():
    """调试任务 - 单账号单任务执行，不受执行模式影响"""
    _map = {
        "第一轮任务": (TASK_TYPE_ONE, MODULE_PATH_ONE),
        "第二轮任务": (TASK_TYPE_TWO, MODULE_PATH_TWO),
        "其它任务": (TASK_TYPE_OTHER, MODULE_PATH_OTHER),
    }

    print("💡 调试模式：每次仅执行单个账号的单个任务")
    print("💡 支持热重载：修改任务代码后无需重启程序（需回退到选择账号菜单）")
    print("💡 重载模块：common、one、two、other\n")
    task = Input.select("请选择调试任务：", list(_map))
    if task is None:
        return

    task_type, module_path = _map[task]
    TaskSchedule.execute_debug(task_type, module_path)


def run_serve():
    """运行服务"""
    config_files = Config.list_numeric_config_files()
    if config_files is None:
        print_separator()
        print("❌ config 目录丢失，请确保项目结构完整\n")
        return

    if not config_files:
        print_separator()
        print("❌ 没有找到账号配置文件")
        print("💡 请先使用 添加账号 功能，添加成功后再重启程序\n")
        tasks = {
            "添加账号": _add_account,
        }
    else:
        print_separator()
        tasks = {
            "执行任务": _execute_tasks,
            "调试任务": _execute_debug,
            "添加账号": _add_account,
        }

    task = Input.select("请选择任务：", list(tasks))
    if task is None:
        return
    tasks[task]()
