import sys
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger


if TYPE_CHECKING:
    from loguru import Logger
else:
    Logger = type(logger)


_sink_ids = {}


def setup_logger() -> None:
    """设置控制台输出格式"""
    logger.remove()
    logger.add(
        sink=sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <cyan>{extra[qq]}</cyan> | {message}",
        colorize=True,
    )


def qq_logger(qq: str) -> Logger:
    """
    获取指定 QQ 的 logger 实例，并确保其对应的文件 sink 已添加

    返回的 logger 实例已经绑定了 qq 字段，后续调用 .info() 等方法时，
    会自动将 qq 写入日志的 extra 属性，供 filter 过滤使用。
    """
    if qq not in _sink_ids:
        log_path = Path(f"log/{qq}/{{time:YYYY-MM-DD}}.log")
        log_path.parent.mkdir(parents=True, exist_ok=True)

        sink_id = logger.add(
            str(log_path),
            rotation="1 day",
            level="INFO",
            format="{time:HH:mm:ss} | {message}",
            retention="30 days",
            filter=lambda record: record["extra"].get("qq") == qq,
        )
        _sink_ids[qq] = sink_id

    return logger.bind(qq=qq)


setup_logger()
