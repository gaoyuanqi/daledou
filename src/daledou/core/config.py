from pathlib import Path

import yaml

from .utils import (
    TaskType,
    DateTime,
    parse_cookie,
)


class ConfigManager:
    """配置管理器"""

    # 配置目录结构
    CONFIG_DIR = Path("./config")
    ACCOUNTS_DIR = CONFIG_DIR / "accounts"
    MERGED_DIR = CONFIG_DIR / "merged"
    DEFAULT_CONFIG_PATH = CONFIG_DIR / "default.yaml"
    GLOBAL_CONFIG_PATH = CONFIG_DIR / "global.yaml"

    TASK_CONFIG_KEY = "TASK_CONFIG"

    @classmethod
    def ensure_directories(cls) -> None:
        """确保配置目录存在"""
        cls.ACCOUNTS_DIR.mkdir(parents=True, exist_ok=True)
        cls.MERGED_DIR.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _read_file_content(file_path: Path) -> str:
        """读取文件内容"""
        if not file_path.exists():
            raise FileNotFoundError(f"{file_path} 不存在")

        try:
            with file_path.open("r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            raise ValueError(f"{file_path} 读取错误：{e}")

    @staticmethod
    def _load_yaml_file(file_path: Path) -> dict:
        """加载YAML配置文件"""
        if not file_path.exists():
            raise FileNotFoundError(f"{file_path} 不存在")

        try:
            with file_path.open("r", encoding="utf-8") as fp:
                return yaml.safe_load(fp) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"{file_path} 解析错误：{e}")

    @staticmethod
    def _save_yaml_file(file_path: Path, data: dict) -> None:
        """保存数据到YAML文件"""
        try:
            with file_path.open("w", encoding="utf-8") as fp:
                yaml.dump(data, fp, allow_unicode=True, sort_keys=False)
        except Exception as e:
            raise ValueError(f"{file_path} 保存失败：{e}")

    @classmethod
    def _merge_task_orchestration(cls, account_config: dict) -> dict:
        """合并任务编排配置

        将账号配置中的任务编排与全局配置合并，账号配置具有更高优先级。
        如果账号配置中定义了某个任务，则覆盖全局配置中的同名任务；
        如果账号配置中没有定义某个任务，则继承全局配置中的该任务。

        Args:
            account_config: 账号配置字典

        Returns:
            dict: 合并后的配置字典
        """
        global_config = cls._load_yaml_file(cls.GLOBAL_CONFIG_PATH)
        merged_config = account_config.copy()

        task_types = [str(task_type) for task_type in TaskType]
        for task_type in task_types:
            if task_type not in global_config:
                continue

            global_tasks = global_config[task_type]

            # 如果账号配置中没有该任务类型或者任务类型值为非字典，直接继承全局配置
            if task_type not in account_config or not isinstance(
                account_config[task_type], dict
            ):
                merged_config[task_type] = global_tasks
            else:
                # 如果账号配置中有该任务类型，进行任务级别的合并
                account_tasks = account_config[task_type]
                merged_tasks = global_tasks.copy()
                merged_tasks.update(account_tasks)
                merged_config[task_type] = merged_tasks

        return merged_config

    @classmethod
    def _merge_task_config(cls, account_config: dict) -> dict:
        """合并任务配置

        将全局配置中的 TASK_CONFIG 合并到账号配置的 TASK_CONFIG 中，
        账号配置具有更高优先级。

        Args:
            account_config: 账号配置字典

        Returns:
            dict: 合并后的配置字典
        """
        global_config = cls._load_yaml_file(cls.GLOBAL_CONFIG_PATH)
        global_task_config = global_config.get(cls.TASK_CONFIG_KEY, {})

        if not global_task_config:
            return account_config

        def deep_merge(account_dict: dict, global_dict: dict) -> dict:
            """深度合并字典"""
            for key, value in global_dict.items():
                if key not in account_dict:
                    account_dict[key] = value
                elif isinstance(value, dict) and isinstance(account_dict[key], dict):
                    deep_merge(account_dict[key], value)
            return account_dict

        # 合并全局配置到账号配置的 TASK_CONFIG 中
        if cls.TASK_CONFIG_KEY not in account_config or not isinstance(
            account_config[cls.TASK_CONFIG_KEY], dict
        ):
            account_config[cls.TASK_CONFIG_KEY] = {}

        account_config[cls.TASK_CONFIG_KEY] = deep_merge(
            account_config[cls.TASK_CONFIG_KEY].copy(), global_task_config
        )

        return account_config

    @classmethod
    def _merge_account_with_global(cls, account_config: dict) -> dict:
        """将账号配置与全局配置合并

        完整的配置合并流程：
        1. 合并任务编排
        2. 合并任务配置

        Args:
            account_config: 账号配置字典

        Returns:
            dict: 完全合并后的配置字典
        """
        merged_config = cls._merge_task_orchestration(account_config)
        merged_config = cls._merge_task_config(merged_config)
        return merged_config


class Config(ConfigManager):
    """配置管理类 - 负责配置文件的创建、加载和解析"""

    @classmethod
    def create_account_config(cls, config_file: str, cookie: str) -> Path:
        """创建或更新账号配置文件

        当配置文件不存在时，基于模板创建新的账号配置文件，包含基础配置和任务编排模板
        当配置文件已存在时，仅更新COOKIE字段的值，保留其他所有配置
        无论哪种情况，都会生成合并后的配置文件到merged目录

        Args:
            config_file: 配置文件名（通常为QQ号）
            cookie: 大乐斗Cookie字符串

        Raises:
            ValueError: 当配置文件存在但找不到格式正确的COOKIE配置时抛出

        Returns:
            Path: 账号配置文件路径
        """
        import re

        cls.ensure_directories()
        account_config_path = cls.ACCOUNTS_DIR / config_file

        def replace_cookie_in_content(file_path: Path, cookie: str) -> str:
            """在配置内容中替换COOKIE值"""
            content = cls._read_file_content(file_path)
            pattern = r'^COOKIE:\s*"([^"]*)"'
            replacement = f'COOKIE: "{cookie}"'
            new_content, count = re.subn(
                pattern, replacement, content, flags=re.MULTILINE
            )
            if count == 0:
                raise ValueError(f"{file_path} 配置内容中找不到格式正确的 COOKIE 配置")
            return new_content

        if not account_config_path.exists():
            new_content = replace_cookie_in_content(cls.DEFAULT_CONFIG_PATH, cookie)
        else:
            new_content = replace_cookie_in_content(account_config_path, cookie)

        # 写入配置文件
        with account_config_path.open("w", encoding="utf-8") as f:
            f.write(new_content)

        cls.load_and_merge_account_config(config_file)

        return account_config_path

    @classmethod
    def load_and_merge_account_config(cls, config_file: str) -> dict[str, dict]:
        """加载账号配置并与全局配置合并

        加载账号配置文件，与全局配置进行完整合并（包括任务编排和任务配置），
        并将合并结果保存到merged目录。

        Args:
            config_file: 配置文件名

        Returns:
            dict: 完全合并后的配置字典
        """
        cls.ensure_directories()
        account_config_path = cls.ACCOUNTS_DIR / config_file
        merged_config_path = cls.MERGED_DIR / config_file

        account_config = cls._load_yaml_file(account_config_path)
        merged_config = cls._merge_account_with_global(account_config)
        cls._save_yaml_file(merged_config_path, merged_config)

        return merged_config

    @classmethod
    def filter_active_tasks(
        cls, account_config: dict, task_type: TaskType, html_content: str
    ) -> dict[str, dict]:
        """根据当前日期和页面内容筛选活跃任务

        根据星期和日期条件过滤出当前需要执行的任务，
        同时检查任务在页面中是否存在。

        Args:
            account_config: 账号配置字典
            task_type: 任务类型枚举
            html_content: 大乐斗首页HTML内容，用于检查任务是否存在

        Returns:
            dict[str, dict]: 过滤后的任务配置字典，键为函数名，值为任务配置
                             如果没有配置该类型的任务或没有符合条件的任务，返回空字典
        """
        active_tasks = {}
        task_definitions: dict[str, dict] = account_config.get(task_type, {})

        if not task_definitions:
            return active_tasks

        current_day_of_month = DateTime.now().day
        current_day_of_week = DateTime.now().isoweekday()

        task_config = account_config.get(cls.TASK_CONFIG_KEY, {})

        for task_name, task_schedule_config in task_definitions.items():
            if task_schedule_config is None:
                continue

            # 检查任务是否在页面中存在
            if task_name not in html_content:
                continue

            func_name = task_schedule_config.get("func_name", task_name)

            # 检查星期条件
            if scheduled_weekdays := task_schedule_config.get("weeks"):
                if current_day_of_week in scheduled_weekdays:
                    active_tasks[func_name] = task_config.get(task_name, {})
                    continue

            # 检查日期条件
            if scheduled_days := task_schedule_config.get("days"):
                for day_range in scheduled_days:
                    start_day = day_range["start"]
                    end_day = day_range["end"]
                    if start_day <= current_day_of_month <= end_day:
                        active_tasks[func_name] = task_config.get(task_name, {})
                        break

        return active_tasks

    @staticmethod
    def parse_account_credentials(
        account_config: dict,
    ) -> tuple[dict, str]:
        """从配置数据中解析用户凭证和激活状态

        Args:
            account_config: 账号配置字典

        Returns:
            tuple: Cookie字典、推送token
        """
        cookie: dict = parse_cookie(account_config["COOKIE"])
        push_token: str = account_config["PUSH_TOKEN"]
        return cookie, push_token

    @classmethod
    def list_all_qq_numbers(cls) -> list[str]:
        """获取所有已配置的QQ号列表

        从配置文件名称中提取QQ号，配置文件命名格式为"QQ号.yaml"

        Returns:
            list[str]: QQ号列表，如果没有配置文件则返回空列表
        """
        cls.ensure_directories()

        qq_numbers = []
        for file in cls.ACCOUNTS_DIR.iterdir():
            if (
                file.is_file()
                and file.stem.isdigit()
                and file.suffix.lower() == ".yaml"
            ):
                qq_numbers.append(file.stem)

        return qq_numbers
