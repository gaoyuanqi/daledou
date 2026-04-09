from enum import StrEnum
from typing import Callable, Optional


class TaskModule(StrEnum):
    noon = "noon"
    evening = "evening"


# 任务注册表：{TaskModule: {task_name: func}}
TASKS_REGISTRY: dict[TaskModule, dict[str, Callable]] = {}

# 模块元数据：存储额外配置（如执行时间、描述等）
MODULE_METADATA: dict[TaskModule, dict] = {}


class Registry:
    def __init__(
        self,
        key: TaskModule,
        schedule_time: Optional[str] = None,
        description: Optional[str] = None,
    ):
        """
        初始化注册器

        Args:
            key: 模块枚举值
            schedule_time: 定时执行时间（如 "13:01:00"），None 表示不定时执行
            description: 模块描述
        """
        if key not in TASKS_REGISTRY:
            TASKS_REGISTRY[key] = {}
            MODULE_METADATA[key] = {
                "schedule_time": schedule_time,
                "description": description or f"{key.value} 模块",
            }
        self.registry = TASKS_REGISTRY[key]
        self.key = key

    def register(self, link_text: Optional[str] = None) -> Callable:
        """
        返回一个装饰器，用于将函数注册到当前任务模块下

        Args:
            link_text: 大乐斗老版首页任务链接文本，如果不提供则使用函数名

        Returns:
            装饰器函数
        """

        def decorator(func: Callable) -> Callable:
            task_key = link_text or func.__name__
            if task_key in self.registry:
                raise KeyError(
                    f"[Registry] 任务 '{task_key}' 在模块 '{self.key}' 中重复注册"
                )
            self.registry[task_key] = func
            return func

        return decorator

    @property
    def tasks(self) -> dict[str, Callable]:
        """返回已注册的任务字典"""
        return self.registry


def get_all_modules() -> list[TaskModule]:
    """获取所有已注册的模块"""
    return list(TASKS_REGISTRY.keys())


def get_module_tasks(module: TaskModule) -> dict[str, Callable]:
    """获取指定模块的所有任务"""
    return TASKS_REGISTRY.get(module, {})


def get_module_metadata(module: TaskModule) -> dict:
    """获取模块元数据"""
    return MODULE_METADATA.get(module, {})
