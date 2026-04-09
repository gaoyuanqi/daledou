import re
from typing import Optional, Pattern, Any

from src.utils.client import Client
from src.utils.log import qq_logger

from src.utils.config import ConfigResolver


class DaLeDou:
    _compiled_regexes: dict[str, Pattern] = {}

    def __init__(
        self,
        qq: str,
        client: Client,
        config_resolver: ConfigResolver,
    ):
        self._qq = qq
        self._client = client
        self._config = config_resolver
        self._logger = qq_logger(qq)

        self.html: str = ""
        self.task_name: str | None = None

    def config(self, key: str) -> Any:
        """配置解析器"""
        return self._config.get(key)

    def find(self, regex: str = r"<br />(.*?)<") -> Optional[str]:
        """返回首个匹配结果"""
        if self.html is None:
            return

        if regex not in self._compiled_regexes:
            self._compiled_regexes[regex] = re.compile(regex, re.DOTALL)
        pattern = self._compiled_regexes[regex]

        result = pattern.search(self.html)
        return result.group(1) if result else None

    def findall(self, regex: str, html: Optional[str] = None) -> list:
        """返回所有匹配结果"""
        content = html or self.html
        if not content:
            return []
        return re.findall(regex, content, re.DOTALL)

    async def get(self, path: str) -> str:
        self.html = await self._client.get(path)
        return self.html

    def log(self, msg: Optional[str], task_name: Optional[str] = None) -> None:
        log_prefix = task_name or self.task_name
        self._logger.info(f"{log_prefix}：{msg}")
