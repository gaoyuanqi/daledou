import os
from datetime import timedelta
from enum import StrEnum

import requests
import questionary

from .log import LoguruLogger


DLD_EXECUTION_MODE_ENV = "DLD_EXECUTION_MODE"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0",
}


class ExecutionMode(StrEnum):
    SEQUENTIAL = "sequential"
    CONCURRENT = "concurrent"


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


class ModulePath(StrEnum):
    OTHER = "src.daledou.tasks.other"
    ONE = "src.daledou.tasks.one"
    TWO = "src.daledou.tasks.two"


class TaskType(StrEnum):
    OTHER = "other"
    ONE = "one"
    TWO = "two"


def formatted_time(delta: timedelta) -> str:
    """格式化时间 HH:MM:SS"""
    total_seconds = int(delta.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def parse_qq_from_cookie(cookie: dict) -> str:
    """从cookie中获取QQ号"""
    return cookie["newuin"]


def parse_cookie(cookie: str) -> dict:
    """解析cookie字符串为字典格式"""
    cookies = {}
    for pair in cookie.split("; "):
        if "=" in pair:
            k, v = pair.split("=", 1)
            cookies[k.strip()] = v.strip()
    return cookies


def push(token: str, title: str, content: str, qq_logger: LoguruLogger) -> None:
    """pushplus微信通知"""
    if not token or len(token) != 32:
        qq_logger.warning("pushplus | PUSH_TOKEN 无效\n")
        return

    data = {
        "token": token,
        "title": title,
        "content": content,
    }
    try:
        response = requests.post(
            "http://www.pushplus.plus/send/", data=data, timeout=10
        )
        qq_logger.success(f"pushplus | {response.json()}\n")
    except Exception as e:
        qq_logger.error(f"pushplus | 发送失败: {e}\n")


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
