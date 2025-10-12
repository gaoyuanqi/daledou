import textwrap
from datetime import datetime
from pathlib import Path

import yaml

from .utils import parse_cookie, parse_qq_from_cookie, TaskType


_CONFIG_DIR = Path("./config")
_DEFAULT_CONFIG_PATH = _CONFIG_DIR / Path("default_config.yaml").name


class Config:
    """配置管理类 - 负责配置文件的创建、加载和解析"""

    @staticmethod
    def create_user_config(config_file: str, cookie: str):
        """创建用户配置文件

        基于模板创建新的用户配置文件，包含基础配置和任务配置模板

        Args:
            config_file: 配置文件名（通常为QQ号）
            cookie: 用户Cookie字符串
        """
        config_path = _CONFIG_DIR / Path(config_file).name
        user_config_template = textwrap.dedent(f"""\
            # =============================================
            # 用户配置
            # =============================================

            # 大乐斗cookie - 从浏览器复制完整的Cookie字符串
            COOKIE: {cookie}

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
        config_data: dict, task_type: TaskType, html_content: str
    ) -> dict[str, dict]:
        """根据当前日期和页面内容筛选活跃任务

        根据星期和日期条件过滤出当前需要执行的任务，
        同时检查任务在页面中是否存在。

        Args:
            config_data: 加载的配置数据字典
            task_type: 任务类型枚举
            html_content: 大乐斗首页HTML内容，用于检查任务是否存在

        Returns:
            dict[str, dict]: 过滤后的任务配置字典，键为函数名，值为任务配置
                             如果没有配置该类型的任务或没有符合条件的任务，返回空字典
        """
        tasks = {}
        task_configs: dict[str, dict | None] = config_data.get(task_type)
        if not task_configs:
            return tasks

        now = datetime.now()
        current_day = now.day
        current_weekday = now.isoweekday()

        for task_name, task_config in task_configs.items():
            if task_name not in html_content or task_config is None:
                continue

            task_item = task_config.copy()
            func_name = task_item.pop("func_name", task_name)

            # 按星期筛选
            if weeks := task_item.pop("weeks", None):
                if current_weekday in weeks:
                    tasks[func_name] = task_item
            # 按日期筛选
            elif days := task_item.pop("days", None):
                for date_range in days:
                    start: int = date_range["start"]
                    end: int = date_range["end"]
                    if start <= current_day <= end:
                        tasks[func_name] = task_item
                        break
        return tasks

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
    def load_user_config(config_file: str) -> dict[str, dict]:
        """加载并解析用户配置文件

        Args:
            config_file: 配置文件名

        Returns:
            dict: 解析后的配置字典

        Raises:
            FileNotFoundError: 配置文件不存在时抛出
            ValueError: 配置文件解析错误时抛出
        """
        config_path = _CONFIG_DIR / Path(config_file).name
        if not config_path.exists():
            raise FileNotFoundError(f"配置文件 {config_path} 不存在")

        try:
            with config_path.open("r", encoding="utf-8") as fp:
                return yaml.safe_load(fp)
        except yaml.YAMLError as e:
            raise ValueError(f"配置文件解析错误：{e}")

    @staticmethod
    def parse_user_credentials(config_data: dict) -> tuple[str, dict, str, bool]:
        """从配置数据中解析用户凭证和激活状态

        Args:
            config_data: 加载的配置数据字典

        Returns:
            tuple: 包含QQ号、Cookie字典、推送token、账号激活状态的元组
        """
        cookie: dict = parse_cookie(config_data["COOKIE"])
        qq: str = parse_qq_from_cookie(cookie)
        push_token: str = config_data["PUSH_TOKEN"]
        is_activate_account: bool = config_data["IS_ACTIVATE_ACCOUNT"]
        return qq, cookie, push_token, is_activate_account
