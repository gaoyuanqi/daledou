import os
import textwrap
from datetime import timedelta
from typing import Literal, TypeAlias

import requests
import questionary

from .log import LoguruLogger


# 执行模式环境变量名
EXECUTION_MODE_ENV = "DLD_EXECUTION_MODE"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0",
}

MODULE_PATH_COMMON = "src.daledou.tasks.common"
MODULE_PATH_ONE = "src.daledou.tasks.one"
MODULE_PATH_OTHER = "src.daledou.tasks.other"
MODULE_PATH_TWO = "src.daledou.tasks.two"

TASK_TYPE_ONE = "one"
TASK_TYPE_OTHER = "other"
TASK_TYPE_TWO = "two"
TaskType: TypeAlias = Literal[TASK_TYPE_ONE, TASK_TYPE_OTHER, TASK_TYPE_TWO]

TIMING_ONE = "13:01"  # 第一轮定时运行时间
TIMING_TWO = "20:01"  # 第二轮定时运行时间
TIMING_INFO = textwrap.dedent(f"""
    定时任务守护进程已启动：
    第一轮默认 {TIMING_ONE} 定时运行
    第二轮默认 {TIMING_TWO} 定时运行

    任务配置目录：config
    任务日志目录：log
""")


def formatted_time(delta: timedelta) -> str:
    """格式化时间 HH:MM:SS"""
    total_seconds = int(delta.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def get_execution_mode() -> str:
    """获取执行模式"""
    return os.environ.get(EXECUTION_MODE_ENV, "sequential")  # 默认顺序执行


def parse_cookie(cookie: str) -> dict:
    """解析cookie字符串为字典格式"""
    cookies = {}
    for pair in cookie.split("; "):
        if "=" in pair:
            k, v = pair.split("=", 1)
            cookies[k.strip()] = v.strip()
    return cookies


def parse_qq_from_cookie(cookie: dict) -> str:
    """从cookie中获取QQ号"""
    return cookie["newuin"]


def push(token: str, title: str, content: str, qq_logger: LoguruLogger) -> None:
    """pushplus微信通知"""
    if not token or not len(token) == 32:
        qq_logger.warning("pushplus | PUSH_TOKEN 无效\n")
        return

    url = "http://www.pushplus.plus/send/"
    data = {
        "token": token,
        "title": title,
        "content": content,
    }
    res = requests.post(url, data=data, timeout=10)
    qq_logger.success(f"pushplus | {res.json()}\n")


def print_separator() -> None:
    """打印分隔符，根据终端宽度自适应"""
    try:
        width = os.get_terminal_size().columns
    except OSError:
        width = 48

    if width <= 80:
        separator = "-" * width
    elif width <= 120:
        separator = "-" * int(width * 0.8)
    else:
        separator = "-" * int(width * 0.6)

    print(separator)


class Input:
    """处理用户输入"""

    @staticmethod
    def select(message: str, tasks: list) -> str | None:
        """在终端中显示任务列表供用户选择"""
        if not tasks:
            print("没有符合要求的选项\n")
            return

        selected = questionary.select(
            message=message,
            choices=tasks + ["退出"],
            use_arrow_keys=True,
            instruction="(↑↓选择，Enter确认)",
        ).ask()

        if selected == "退出":
            return

        if selected is not None:
            print("\n正在加载数据，请勿回车")
            print_separator()

        return selected

    @staticmethod
    def text(message: str) -> str | None:
        """获取用户输入的文本"""
        print("💡 退出按键： CTRL + C\n")
        response = questionary.text(
            message=message,
            instruction="",
            validate=lambda text: True if text.strip() else "输入不能为空",
        ).ask()
        if response is not None:
            return response

    @staticmethod
    def _validate_number(input):
        try:
            num = int(input)
            if num < 0:
                return "数值不能小于 0"
            return True
        except ValueError:
            return "请输入有效的数字"

    @staticmethod
    def number(message: str) -> int | None:
        """获取用户输入的数字"""
        print("💡 退出按键： CTRL + C\n")
        response = questionary.text(
            message=message,
            validate=Input._validate_number,
            instruction="",
        ).ask()
        if response is not None:
            return int(response)
