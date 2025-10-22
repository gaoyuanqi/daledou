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
def job_one() -> None:
    """每天定时执行第一轮任务"""
    _execute_one()
    print(TIMING_INFO)
    print_separator()


@repeat(every().day.at(TIMING_TWO))
def job_two() -> None:
    """每天定时执行第二轮任务"""
    _execute_two()
    print(TIMING_INFO)
    print_separator()


def _execute_one() -> None:
    """执行第一轮任务"""
    TaskSchedule.execute(TASK_TYPE_ONE, MODULE_PATH_ONE)


def _execute_two() -> None:
    """执行第二轮任务"""
    TaskSchedule.execute(TASK_TYPE_TWO, MODULE_PATH_TWO)


def _execute_timing() -> None:
    """运行定时任务"""
    if not Config.list_all_qq_numbers():
        return

    print(TIMING_INFO)
    print_separator()

    while True:
        run_pending()
        time.sleep(1)


class CLIHandler:
    """命令行处理器"""

    def __init__(self):
        self.tasks = {}
        self._setup_tasks()

    def _setup_tasks(self) -> None:
        """设置可用任务"""
        self.tasks = {
            "执行任务": self.execute_tasks,
            "调试任务": self.execute_debug,
            "配置账号": self.configure_account,
            "重建配置": self.rebuild_all_configs,
        }

    def execute_tasks(self) -> None:
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

        # 任务类型选择
        tasks = {
            "定时任务": _execute_timing,
            "第一轮任务": _execute_one,
            "第二轮任务": _execute_two,
        }

        print("💡 任务类型说明：")
        print("• 第一轮包含绝大部分日常任务，建议 13:01 后执行")
        print("• 第二轮是收尾日常任务，建议 20:01 后执行")
        print("• 定时任务是定时执行第一、二轮任务\n")

        task = Input.select("请选择任务：", list(tasks))
        if task is None:
            return

        tasks[task]()

    def execute_debug(self) -> None:
        """调试任务 - 单账号单任务执行"""
        task_map = {
            "第一轮任务": (TASK_TYPE_ONE, MODULE_PATH_ONE),
            "第二轮任务": (TASK_TYPE_TWO, MODULE_PATH_TWO),
            "其它任务": (TASK_TYPE_OTHER, MODULE_PATH_OTHER),
        }

        print("💡 调试模式：每次仅执行单个账号的单个任务")
        print("💡 支持热重载：修改任务代码后无需重启程序")
        print("💡 重载模块：common、one、two、other\n")

        task = Input.select("请选择调试任务：", list(task_map))
        if task is None:
            return

        task_type, module_path = task_map[task]
        TaskSchedule.execute_debug(task_type, module_path)

    def configure_account(self) -> None:
        """配置账号 - 创建或更新账号配置"""
        print("💡 操作说明：")
        print("• 添加新账号会创建对应的配置文件")
        print("• 如果账号已存在，则仅更新Cookie，保留其它所有配置\n")

        print("💡 获取大乐斗Cookie流程：")
        print("1. 应用商店下载Via浏览器")
        print("2. 将Via设为默认浏览器")
        print("3. 使用Via一键登录文字版大乐斗")
        print("4. 等待3秒后点击Via左上角✓")
        print("5. 再点击查看Cookies\n")

        while True:
            cookie = Input.text("请输入大乐斗Cookie：")
            if cookie is None:
                break

            ck = parse_cookie(cookie)
            if not ck:
                print("\n❌ Cookie格式不正确")
                print_separator()
                continue

            session = SessionManager.create_verified_session(ck)
            if session is None:
                print("\n❌ Cookie无效或验证失败")
                print_separator()
                continue

            qq = parse_qq_from_cookie(ck)
            account_config_path = Config.create_account_config(f"{qq}.yaml", cookie)
            print(f"\n✅ 账号 {qq} 配置成功！")
            print(f"📁 账号配置文件：{account_config_path}")
            print_separator()

    def rebuild_all_configs(self) -> None:
        """重建配置 - 重新生成所有账号的合并配置文件"""
        account_files = Config.list_numeric_config_files()
        if not account_files:
            print("❌ 没有找到账号配置文件")
            print_separator()
            return

        for account_file in account_files:
            try:
                Config.load_and_merge_account_config(account_file)
                print(f"✅ {account_file}: 合并配置已重建")
            except Exception as e:
                print(f"❌ {e}")
                print_separator()
                return

        print("\n💡「执行任务」、「调试任务」会自动重建配置")

        print("\n💡 配置查看说明:")
        print("• 账号配置: config/accounts/QQ号.yaml")
        print("• 全局配置: config/global.yaml")
        print("• 合并配置: config/merged/QQ号.yaml (最终生效配置)")
        print_separator()


def run_serve() -> None:
    """运行主服务"""
    account_files = Config.list_numeric_config_files()
    Config.sync_merged_directory(account_files)

    handler = CLIHandler()

    if not account_files:
        print_separator()
        print("❌ 没有找到账号配置文件")
        print("💡 请先使用「配置账号」功能，配置成功后再重启程序\n")
        available_tasks = {"配置账号": handler.configure_account}
    else:
        print_separator()
        available_tasks = handler.tasks

    task = Input.select("请选择任务：", list(available_tasks))
    if task is None:
        return

    available_tasks[task]()
