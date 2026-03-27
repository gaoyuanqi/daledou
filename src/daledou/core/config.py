from pathlib import Path

import yaml

from .utils import (
    TaskType,
    DateTime,
    parse_cookie,
)


class ConfigManager:
    """配置管理器"""

    COOKIE_KEY = "COOKIE"
    PUSH_TOKEN_KEY = "PUSH_TOKEN"
    TASK_CONFIG_KEY = "TASK_CONFIG"

    # 配置目录结构
    CONFIG_DIR = Path("./config")
    ACCOUNTS_DIR = CONFIG_DIR / "accounts"
    MERGED_DIR = CONFIG_DIR / "merged"
    DEFAULT_CONFIG_PATH = CONFIG_DIR / "default.yaml"
    GLOBAL_CONFIG_PATH = CONFIG_DIR / "global.yaml"

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
    def _merge_task_type(cls, account_config: dict, global_config: dict) -> dict:
        """将全局任务类型与账号任务类型合并，账号优先级更高"""
        merged_config = {}

        task_types = [str(task_type) for task_type in TaskType]
        for task_type in task_types:
            account_task_type = account_config.get(task_type, {})
            global_task_type = global_config.get(task_type, {})

            if not isinstance(account_task_type, dict):
                account_task_type = {}

            if not isinstance(global_task_type, dict):
                raise ValueError(
                    f"{cls.GLOBAL_CONFIG_PATH}：{task_type} 必须是字典格式"
                )

            merged_config[task_type] = global_task_type | account_task_type

        return merged_config

    @classmethod
    def _merge_task_config(cls, account_config: dict, global_config: dict) -> dict:
        """将全局任务配置与账号任务配置合并，账号优先级更高"""
        merged_config = {}
        account_task_config = account_config.get(cls.TASK_CONFIG_KEY, {})
        global_task_config = global_config.get(cls.TASK_CONFIG_KEY, {})

        if not isinstance(account_task_config, dict):
            account_task_config = {}

        if not isinstance(global_task_config, dict):
            raise ValueError(
                f"{cls.GLOBAL_CONFIG_PATH}：{cls.TASK_CONFIG_KEY} 必须是字典格式"
            )

        def deep_merge(account_dict: dict, global_dict: dict) -> dict:
            """深度合并字典"""
            for g_key, g_value in global_dict.items():
                if g_key not in account_dict:
                    account_dict[g_key] = g_value
                elif isinstance(account_dict[g_key], dict) and isinstance(
                    g_value, dict
                ):
                    deep_merge(account_dict[g_key], g_value)
            return account_dict

        merged_config[cls.TASK_CONFIG_KEY] = deep_merge(
            account_task_config.copy(), global_task_config.copy()
        )

        return merged_config


class Config(ConfigManager):
    """配置管理类 - 负责配置文件的创建、加载和解析"""

    @classmethod
    def save_account_config(
        cls, account_file: str, cookie: str, push_token: str = ""
    ) -> Path:
        """保存账号配置 - 创建或更新账号配置文件

        Args:
            account_file: 账号配置文件名
            cookie: 大乐斗Cookie字符串
            push_token: pushplus推送加token字符串

        Returns:
            Path: 账号配置文件路径
        """
        import re

        cls.ensure_directories()
        account_config_path = cls.ACCOUNTS_DIR / account_file

        def replace_config_in_content(file_path: Path) -> str:
            """在配置内容中替换COOKIE和PUSH_TOKEN值"""
            content = cls._read_file_content(file_path)

            cookie_pattern = r'^COOKIE:\s*"([^"]*)"'
            cookie_replacement = f'COOKIE: "{cookie}"'
            new_content, count = re.subn(
                cookie_pattern, cookie_replacement, content, flags=re.MULTILINE
            )
            if count == 0:
                raise ValueError(f"{file_path} 读取错误：缺失 COOKIE 字段")

            if push_token:
                push_token_pattern = r'^PUSH_TOKEN:\s*"([^"]*)"'
                push_token_replacement = f'PUSH_TOKEN: "{push_token}"'
                new_content, count = re.subn(
                    push_token_pattern,
                    push_token_replacement,
                    new_content,
                    flags=re.MULTILINE,
                )
                if count == 0:
                    raise ValueError(f"{file_path} 读取错误：缺失 PUSH_TOKEN 字段")

            return new_content

        if not account_config_path.exists():
            new_content = replace_config_in_content(cls.DEFAULT_CONFIG_PATH)
        else:
            new_content = replace_config_in_content(account_config_path)

        with account_config_path.open("w", encoding="utf-8") as f:
            f.write(new_content)

        cls.load_account_config(account_file)

        return account_config_path

    @classmethod
    def load_account_config(cls, account_file: str) -> tuple[dict, str, dict]:
        """加载账号配置

        Args:
            account_file: 账号配置文件名

        Returns:
            tuple: (cookie字典, push_token字符串, 合并后的配置字典)
        """
        cls.ensure_directories()
        account_config_path = cls.ACCOUNTS_DIR / account_file
        merged_config_path = cls.MERGED_DIR / account_file

        account_config = cls._load_yaml_file(account_config_path)
        global_config = cls._load_yaml_file(cls.GLOBAL_CONFIG_PATH)

        try:
            cookie: dict = parse_cookie(account_config[cls.COOKIE_KEY])
            push_token: str = account_config[cls.PUSH_TOKEN_KEY]
        except Exception as e:
            raise ValueError(f"{account_config_path} 读取失败：缺失 {e} 字段")

        merged_task_type = cls._merge_task_type(account_config, global_config)
        merged_task_config = cls._merge_task_config(account_config, global_config)
        merged_config = merged_task_type | merged_task_config
        merged_config[cls.COOKIE_KEY] = cookie
        merged_config[cls.PUSH_TOKEN_KEY] = push_token
        cls._save_yaml_file(merged_config_path, merged_config)

        return cookie, push_token, merged_config

    @classmethod
    def filter_active_tasks(
        cls, merged_config: dict, task_type: TaskType, html_content: str
    ) -> dict[str, dict]:
        """根据当前日期和页面内容筛选活跃任务

        Args:
            merged_config: 合并后的配置字典
            task_type: 任务类型枚举
            html_content: 大乐斗首页HTML内容，用于检查任务是否存在

        Returns:
            dict[str, dict]: 过滤后的任务配置字典，键为函数名，值为任务配置
        """
        active_tasks = {}
        task_definitions: dict[str, dict] = merged_config.get(task_type, {})

        if not task_definitions:
            return active_tasks

        current_day_of_month = DateTime.now().day
        current_day_of_week = DateTime.now().isoweekday()

        task_config = merged_config.get(cls.TASK_CONFIG_KEY, {})

        for task_name, task_schedule_config in task_definitions.items():
            if task_schedule_config is None:
                continue

            if task_name not in html_content:
                continue

            func_name = task_schedule_config.get("func_name", task_name)

            if scheduled_weekdays := task_schedule_config.get("weeks"):
                if current_day_of_week in scheduled_weekdays:
                    active_tasks[func_name] = task_config.get(task_name, {})
                    continue

            if scheduled_days := task_schedule_config.get("days"):
                for day_range in scheduled_days:
                    start_day = day_range["start"]
                    end_day = day_range["end"]
                    if start_day <= current_day_of_month <= end_day:
                        active_tasks[func_name] = task_config.get(task_name, {})
                        break

        return active_tasks

    @classmethod
    def list_all_qq_numbers(cls) -> list[str]:
        """获取所有已配置的QQ号列表

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
