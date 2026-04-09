"""日期时间工具模块

提供常用日期时间的获取、格式化及计算功能

本模块依赖系统本地时间，请确保当前系统时区为上海时间（Asia/Shanghai，UTC+8）
"""

from datetime import date, datetime, timedelta


class DateTime:
    """日期时间工具类，提供常用日期时间的获取、格式化与计算功能

    本类所有方法均基于系统本地时间（当前为上海时间 Asia/Shanghai，UTC+8）
    """

    @staticmethod
    def now() -> datetime:
        """获取当前系统本地时间

        Returns:
            datetime: 当前系统本地日期时间对象
        """
        return datetime.now()

    @staticmethod
    def current_date() -> date:
        """获取当前系统本地日期

        Returns:
            date: 当前日期对象，例如 ``date(2026, 4, 2)``

        Examples:
            >>> DateTime.date()
            datetime.date(2026, 4, 2)
        """
        return datetime.now().date()

    @staticmethod
    def year() -> int:
        """获取当前系统本地年份

        Returns:
            int: 当前年份，例如 2026
        """
        return datetime.now().year

    @staticmethod
    def month() -> int:
        """获取当前系统本地月份

        Returns:
            int: 当前月份，范围 1-12
        """
        return datetime.now().month

    @staticmethod
    def day() -> int:
        """获取当前系统本地日期（月中的第几天）

        Returns:
            int: 当前日，范围 1-31
        """
        return datetime.now().day

    @staticmethod
    def week() -> int:
        """获取当前系统本地星期几（ISO 8601 标准）

        Returns:
            int: 星期几，范围 1-7，其中周一为 1，周日为 7

        Examples:
            >>> DateTime.week()  # 假设今天是周四
            4
        """
        return datetime.now().isoweekday()

    @staticmethod
    def format_timedelta(delta: timedelta) -> str:
        """将时间差格式化为 ``HH:MM:SS`` 字符串

        将 timedelta 对象转换为易读的时间字符串格式，支持正数和负数时间差

        Args:
            delta (timedelta): 需要格式化的 timedelta 对象

        Returns:
            str: 格式为 ``HH:MM:SS`` 的时间差字符串，不足两位补零

        Examples:
            >>> from datetime import timedelta
            >>> DateTime.format_timedelta(timedelta(hours=5, minutes=30, seconds=15))
            '05:30:15'
        """
        total_seconds = int(delta.total_seconds())
        total_seconds = abs(total_seconds)
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    @classmethod
    def get_offset_date(
        cls, year: int, month: int, day: int, days_offset: int = 1
    ) -> date:
        """获取指定日期偏移指定天数后的日期

        计算从指定日期向前或向后偏移若干天后的日期

        Args:
            year (int): 年份，如 2026
            month (int): 月份，范围 1-12
            day (int): 日期，范围 1-31（需符合该月实际天数）
            days_offset (int, optional): 相对于目标日期的天数偏移量，默认为 1

                - **正数**：表示目标日期之前的天数（往回推）
                - **负数**：表示目标日期之后的天数（往后推）

                例如，``days_offset=1`` 表示获取目标日期前一天

        Returns:
            date: 偏移后的日期对象

        Raises:
            ValueError: 如果传入的日期无效（如 2026-02-30）

        Examples:
            >>> DateTime.get_offset_date(2026, 4, 2, days_offset=1)  # 前一天
            datetime.date(2026, 4, 1)
            >>> DateTime.get_offset_date(2026, 4, 2, days_offset=-1)  # 后一天
            datetime.date(2026, 4, 3)
            >>> DateTime.get_offset_date(2026, 1, 1, days_offset=1)  # 跨年
            datetime.date(2025, 12, 31)
        """
        end_date = datetime(year, month, day).date()
        return end_date - timedelta(days=days_offset)
