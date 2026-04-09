"""
配置加载模块，提供 YAML 配置文件的统一加载接口
"""

from http.cookies import SimpleCookie
from pathlib import Path
from typing import Optional, Any, Final

import yaml

from src.tasks.register import TaskModule


class ConfigError(Exception):
    """配置模块基础异常"""

    pass


class ConfigFileNotFoundError(ConfigError):
    """配置文件不存在"""

    pass


class ConfigKeyError(ConfigError):
    """YAML 键错误"""

    pass


class ConfigYAMLError(ConfigError):
    """YAML 解析错误"""

    pass


class ConfigResolver:
    """配置解析器，支持三层回退：账号配置 → default.yaml → 异常"""

    NOT_FOUND: Final = object()

    def __init__(
        self,
        qq: str,
        module: TaskModule,
    ):
        self._qq = qq
        self._module = module
        self._full_account: dict = Config.load_account(qq)
        self._full_default: dict = Config.load_default()

        if (
            self._module not in self._full_account
            and self._module not in self._full_default
        ):
            raise ConfigKeyError(
                f"配置键 {self._module} 不存在，"
                f"你扩展了 {self._module} 模块？ -> "
                f"在账号配置或者默认配置添加 '{self._module}: null'"
            )

        # 读取模块配置
        self._account = self._full_account.get(self._module)
        self._default = self._full_default.get(self._module)

    def get(self, key: str) -> Any:
        """获取配置值

        优先级：
        1. 账号配置中存在该键（包括 null）→ 使用
        2. default.yaml 中存在该键 → 使用
        3. 都不存在 → 抛出 ConfigKeyError

        Args:
            key: 配置键，格式 "task.key"（如 "矿洞.floor"）

        Returns:
            配置值（任意类型，包括 None）

        Raises:
            ConfigKeyError: 键格式错误或配置键不存在
        """
        keys = key.split(".")

        # 第一层：账号配置
        if isinstance(self._account, dict):
            account_value = self._deep_get(self._account, keys)
            if account_value is not self.NOT_FOUND:
                return account_value

        # 第二层：默认配置
        if isinstance(self._default, dict):
            default_value = self._deep_get(self._default, keys)
            if default_value is not self.NOT_FOUND:
                return default_value

        # 第三层：未找到，抛出异常
        raise ConfigKeyError(f"配置键 '{self._module}.{key}' 未找到")

    def _deep_get(self, data: dict, keys: list[str]) -> Any:
        """深层字典取值"""
        current = data
        for k in keys:
            if not isinstance(current, dict) or k not in current:
                return self.NOT_FOUND
            current = current[k]
        return current


class Config:
    # 配置目录路径定义
    CONFIG_DIR = Path("./config")
    ACCOUNTS_DIR = CONFIG_DIR / "accounts"

    # 具体配置文件路径
    DEFAULT_CONFIG_PATH = CONFIG_DIR / "default.yaml"
    DLD_COOKIE_CONFIG_PATH = CONFIG_DIR / "dld_cookie.yaml"

    @classmethod
    def _parse_cookie(cls, cookie: str) -> dict:
        """
        解析cookie字符串为字典

        Args:
            cookie: cookie字符串

        Returns:
            解析后的配置字典
        """
        jar = SimpleCookie()
        jar.load(cookie)
        return {k: v.value for k, v in jar.items()}

    @classmethod
    def _load_yaml_file(cls, file_path: Path) -> dict:
        """
        加载指定路径的 YAML 配置文件

        Args:
            file_path: YAML 文件的 Path 对象路径

        Returns:
            解析后的配置字典

        Raises:
            ConfigFileNotFoundError: 文件不存在时抛出
            ConfigYAMLError: YAML解析错误时时抛出
        """
        if not file_path.exists():
            raise ConfigFileNotFoundError(f"{file_path} 不存在")

        try:
            with file_path.open("r", encoding="utf-8") as fp:
                return yaml.safe_load(fp)
        except yaml.YAMLError as e:
            raise ConfigYAMLError(f"{file_path} 解析错误: {e}")

    @classmethod
    def load_account(cls, qq: str) -> dict:
        """
        加载 accounts/qq.yaml

        Args:
            qq: QQ号字符串
            key: 模块枚举值

        Returns:
            账号配置字典
        """
        file_path = cls.ACCOUNTS_DIR / f"{qq}.yaml"
        if not file_path.exists():
            if not cls.DEFAULT_CONFIG_PATH.exists():
                raise ConfigFileNotFoundError(f"{cls.DEFAULT_CONFIG_PATH} 不存在")

            cls.ACCOUNTS_DIR.mkdir(parents=True, exist_ok=True)

            # 构造以枚举值为顶级键的字典
            yaml_data = {task.value: None for task in TaskModule}
            with open(file_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    yaml_data,
                    f,
                    sort_keys=False,
                    allow_unicode=True,
                )

        return cls._load_yaml_file(file_path)

    @classmethod
    def load_default(cls) -> dict:
        """
        加载 default.yaml

        Returns:
            默认配置字典
        """
        return cls._load_yaml_file(cls.DEFAULT_CONFIG_PATH)

    @classmethod
    def load_cookies(cls, qq: Optional[str] = None) -> dict[str, dict[str, str]]:
        """
        从配置文件加载大乐斗 Cookie，支持按 QQ 号过滤

        Args:
            qq: 需要获取 Cookie 的 QQ 号
                - 如果为 None，返回所有已配置账号的 Cookie 字典
                - 如果指定了具体的 QQ 号，但配置中不存在该账号，则返回空字典
                - 如果指定了具体的 QQ 号且存在匹配，则返回仅包含该账号的字典

        Returns:
            字典格式：{qq: {"newuin": qq, "key": "value", ...}, ...}
            当 qq 为 None 时，返回所有账号；当 qq 非 None 且未找到时，返回空字典
        """
        result = {}
        cookie_dict = cls._load_yaml_file(cls.DLD_COOKIE_CONFIG_PATH)
        cookies_list = cookie_dict["DALEDOU_COOKIES"]
        if not cookies_list:
            return result

        for cookie_str in cookies_list:
            cookie_dict = cls._parse_cookie(cookie_str)
            if newuin := cookie_dict.get("newuin"):
                if qq is not None and qq == newuin:
                    return {qq: cookie_dict}
                result[newuin] = cookie_dict

        return {} if qq is not None else result
