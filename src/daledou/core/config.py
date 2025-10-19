import textwrap
from datetime import datetime
from pathlib import Path

import yaml

from .utils import parse_cookie, parse_qq_from_cookie, TaskType


_TASK_CONFIG_KEY = "TASK_CONFIG"

_CONFIG_DIR = Path("./config")
_ACCOUNT_CONFIG_PATH = _CONFIG_DIR / Path("account_config.yaml").name
_DEFAULT_CONFIG_PATH = _CONFIG_DIR / Path("default_config.yaml").name
_GLOBAL_CONFIG_PATH = _CONFIG_DIR / Path("global_config.yaml").name


class Config:
    """配置管理类 - 负责配置文件的创建、加载和解析"""

    @staticmethod
    def _merge_global_config(account_config: dict) -> dict:
        """将全局配置合并到账号配置中

        将全局配置中的 GLOBAL_CONFIG 合并到账号配置的 TASK_CONFIG 中，
        账号配置具有更高优先级。

        Args:
            account_config: 账号配置字典

        Returns:
            dict: 合并后的配置字典
        """
        if not _GLOBAL_CONFIG_PATH.exists():
            raise FileNotFoundError(f"配置文件 {_GLOBAL_CONFIG_PATH} 不存在")

        try:
            with _GLOBAL_CONFIG_PATH.open("r", encoding="utf-8") as fp:
                global_config = yaml.safe_load(fp)
        except yaml.YAMLError as e:
            raise ValueError(f"配置文件解析错误：{e}")

        merged_config = account_config.copy()
        global_task_config = global_config.get(_TASK_CONFIG_KEY, {})

        # 深度合并配置，账号配置优先级更高
        def deep_merge(user_dict, global_dict):
            for key, value in global_dict.items():
                if key not in user_dict:
                    user_dict[key] = value
                elif isinstance(value, dict) and isinstance(user_dict[key], dict):
                    deep_merge(user_dict[key], value)
            return user_dict

        # 合并全局配置到账号配置的 TASK_CONFIG 中
        if global_task_config:
            merged_config[_TASK_CONFIG_KEY] = deep_merge(
                merged_config[_TASK_CONFIG_KEY].copy(), global_task_config
            )

        return merged_config

    @staticmethod
    def create_account_config(config_file: str, cookie: str):
        """创建账号配置文件

        基于模板创建新的账号配置文件，包含基础配置和任务配置模板

        Args:
            config_file: 配置文件名（通常为QQ号）
            cookie: 大乐斗Cookie字符串
        """
        config_path = _CONFIG_DIR / Path(config_file).name
        user_config_template = textwrap.dedent(f"""\
            # =============================================
            # 账号配置
            # =============================================

            # 大乐斗cookie - 从浏览器复制完整的Cookie字符串
            COOKIE: "{cookie}"

            # 账号激活状态
            IS_ACTIVATE_ACCOUNT: true # 激活账号，参与任务执行
            # IS_ACTIVATE_ACCOUNT: false # 不激活账号，跳过该账号的所有任务

            # pushplus推送token - 微信服务号 > 个人中心 > 开发设置 > 用户token
            PUSH_TOKEN: ""


        """)
        with _DEFAULT_CONFIG_PATH.open("r", encoding="utf-8") as f:
            default_config = f.read()
        with config_path.open("w", encoding="utf-8") as f:
            f.write(user_config_template + default_config)

    @staticmethod
    def filter_active_tasks(
        account_config: dict, task_type: TaskType, html_content: str
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

        current_time = datetime.now()
        current_day_of_month = current_time.day
        current_day_of_week = current_time.isoweekday()

        task_config = account_config.get(_TASK_CONFIG_KEY, {})

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
    def list_all_qq_numbers() -> list[str]:
        """获取所有已配置的QQ号列表

        从配置文件名称中提取QQ号，配置文件命名格式为"QQ号.yaml"

        Returns:
            list[str]: QQ号列表，如果没有配置文件则返回空列表
        """
        qq_numbers = []
        config_files = Config.list_numeric_config_files()
        if config_files is None:
            return qq_numbers

        for file_name in config_files:
            qq_number, _ = file_name.split(".", 1)
            qq_numbers.append(qq_number)
        return qq_numbers

    @staticmethod
    def list_numeric_config_files() -> list[str] | None:
        """列出配置目录下所有数字命名的YAML配置文件

        扫描配置目录，筛选出以纯数字命名且扩展名为yaml或yml的文件

        Returns:
            list[str] | None: 配置文件名列表，如果目录不存在则返回None
        """
        if not _CONFIG_DIR.exists():
            return

        return [
            file.name
            for file in _CONFIG_DIR.iterdir()
            if (
                file.is_file()
                and file.stem.isdigit()
                and file.suffix.lower() in [".yaml", ".yml"]
            )
        ]

    @staticmethod
    def load_account_config(config_file: str) -> dict[str, dict]:
        """加载并解析账号配置文件，并与全局配置合并

        Args:
            config_file: 配置文件名

        Returns:
            dict: 解析后的配置字典（已合并全局配置）

        Raises:
            FileNotFoundError: 配置文件不存在时抛出
            ValueError: 配置文件解析错误时抛出
        """
        config_path = _CONFIG_DIR / Path(config_file).name
        if not config_path.exists():
            raise FileNotFoundError(f"配置文件 {config_path} 不存在")

        try:
            with config_path.open("r", encoding="utf-8") as fp:
                account_config = yaml.safe_load(fp)
        except yaml.YAMLError as e:
            raise ValueError(f"配置文件解析错误：{e}")

        return Config._merge_global_config(account_config)

    @staticmethod
    def parse_account_credentials(account_config: dict) -> tuple[str, dict, str, bool]:
        """从配置数据中解析用户凭证和激活状态

        Args:
            account_config: 账号配置字典

        Returns:
            tuple: 包含QQ号、Cookie字典、推送token、账号激活状态的元组
        """
        cookie: dict = parse_cookie(account_config["COOKIE"])
        qq: str = parse_qq_from_cookie(cookie)
        push_token: str = account_config["PUSH_TOKEN"]
        is_activate_account: bool = account_config["IS_ACTIVATE_ACCOUNT"]
        return qq, cookie, push_token, is_activate_account
