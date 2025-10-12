import sys
from datetime import datetime
from pathlib import Path

from loguru import logger


LoguruLogger = type(logger)


class LogManager:
    """日志管理类"""

    @staticmethod
    def get_qq_logger(qq: str) -> tuple[LoguruLogger, int]:
        """获取qq专属日志记录器

        Returns:
            tuple[LoguruLogger, int]: (日志记录器实例, 处理器ID)
        """
        log_dir = Path(f"./log/{qq}")
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.log"

        user_logger = logger.bind(user_qq=qq)
        handler_id = user_logger.add(
            sink=log_file,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{message}</level>",
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

    @staticmethod
    def set_terminal_output_format() -> None:
        """设置控制台输出格式"""
        LogManager.remove_handler()
        logger.add(
            sink=sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{message}</level>",
            colorize=True,
        )
