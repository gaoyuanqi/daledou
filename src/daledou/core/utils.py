import os
import sys
import textwrap
from datetime import date, datetime, timedelta
from enum import StrEnum
from pathlib import Path

import pytz
import requests
import questionary
from loguru import logger


DLD_EXECUTION_MODE_ENV = "DLD_EXECUTION_MODE"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0",
}

LoguruLogger = type(logger)


class DateTime:
    """日期时间工具类（基于上海时区）"""

    # 上海时区
    SHANGHAI_TZ = pytz.timezone("Asia/Shanghai")

    @classmethod
    def now(cls) -> datetime:
        """获取当前时间（上海时区）"""
        return datetime.now(cls.SHANGHAI_TZ)

    @classmethod
    def formatted_datetime(cls) -> str:
        """获取格式化的日期时间"""
        return cls.now().strftime("%Y-%m-%d %H:%M:%S")

    @classmethod
    def formatted_date(cls) -> str:
        """获取格式化的日期"""
        return cls.now().strftime("%Y-%m-%d")

    @classmethod
    def formatted_time(cls) -> str:
        """获取格式化的时间"""
        return cls.now().strftime("%H:%M:%S")

    @staticmethod
    def format_timedelta(delta: timedelta) -> str:
        """格式化时间差 -> HH:MM:SS"""
        total_seconds = int(delta.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    @classmethod
    def get_current_and_end_date_offset(
        cls, end_year: int, end_month: int, end_day: int, days_offset: int = 1
    ) -> tuple[date, date]:
        """
        获取当前日期和结束日期偏移指定天数后的日期

        Args:
            end_year: 结束年
            end_month: 结束月
            end_day: 结束日
            days_offset: 相对于结束日期的天数偏移量，默认为1（表示结束日期前一天）
                        - 正数表示结束日期之前的天数
                        - 负数表示结束日期之后的天数

        Returns:
            tuple[date, date]: (当前日期, 结束日期偏移后的日期)
        """
        current_date = cls.now().date()
        end_date = datetime(end_year, end_month, end_day).date()
        offset_date = end_date - timedelta(days=days_offset)

        return current_date, offset_date


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


class LogManager:
    """日志管理类"""

    @classmethod
    def _shanghai_time_patcher(cls, record):
        """动态为所有日志记录添加上海时间"""
        record["extra"]["shanghai_time"] = DateTime.formatted_datetime()
        return record

    @classmethod
    def get_qq_logger(cls, qq: str) -> tuple[LoguruLogger, int]:
        """获取qq专属日志记录器

        Returns:
            tuple[LoguruLogger, int]: (日志记录器实例, 处理器ID)
        """
        log_dir = Path(f"./log/{qq}")
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{DateTime.formatted_date()}.log"

        logger.configure(patcher=cls._shanghai_time_patcher)

        user_logger = logger.bind(user_qq=qq)
        handler_id = user_logger.add(
            sink=log_file,
            format="<green>{extra[shanghai_time]}</green> | <level>{message}</level>",
            enqueue=True,
            encoding="utf-8",
            retention="30 days",
            level="INFO",
            filter=lambda record: record["extra"].get("user_qq") == qq,
        )

        return user_logger, handler_id

    @staticmethod
    def remove_handler(handler_id: int | None = None) -> None:
        """移除日志处理器，默认移除所有处理器"""
        if handler_id is None:
            logger.remove()
        else:
            logger.remove(handler_id)

    @classmethod
    def set_terminal_output_format(cls) -> None:
        """设置控制台输出格式"""
        cls.remove_handler()
        logger.configure(patcher=cls._shanghai_time_patcher)
        logger.add(
            sink=sys.stderr,
            format="<green>{extra[shanghai_time]}</green> | <level>{message}</level>",
            colorize=True,
        )


class ModulePath(StrEnum):
    OTHER = "src.daledou.tasks.other"
    ONE = "src.daledou.tasks.one"
    TWO = "src.daledou.tasks.two"


class TaskType(StrEnum):
    OTHER = "other"
    ONE = "one"
    TWO = "two"


class TimingConfig:
    """定时配置常量类"""

    # 使用上海时区的时间
    ONE_EXECUTION_TIME: str = "13:01:00"
    TWO_EXECUTION_TIME: str = "20:01:00"

    @classmethod
    def print_schedule_info(cls) -> str:
        """打印定时任务信息"""
        print(
            textwrap.dedent(f"""
            当前上海时间：{DateTime.formatted_datetime()}

            定时任务守护进程已启动：
            每天上海时间 {cls.ONE_EXECUTION_TIME} 执行第一轮任务
            每天上海时间 {cls.TWO_EXECUTION_TIME} 执行第二轮任务

            任务配置目录：config
            任务日志目录：log
        """)
        )


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
