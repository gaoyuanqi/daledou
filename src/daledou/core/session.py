import time

import requests
from requests import Session
from requests.adapters import HTTPAdapter

from .utils import HEADERS


class SessionManager:
    """会话管理类"""

    _adapter: HTTPAdapter | None = None
    INDEX_URL = "https://dld.qzapp.z.qq.com/qpet/cgi-bin/phonepk?cmd=index"

    @classmethod
    def _get_shared_adapter(cls) -> HTTPAdapter:
        """获取共享HTTP适配器实例"""
        if cls._adapter is None:
            cls._adapter = requests.adapters.HTTPAdapter(
                pool_connections=50,
                pool_maxsize=100,
                max_retries=3,
                pool_block=False,
            )
        return cls._adapter

    @classmethod
    def _set_utf8_encoding(cls, response, *args, **kwargs):
        """响应钩子：自动设置UTF-8编码"""
        response.encoding = "utf-8"
        return response

    @classmethod
    def create_verified_session(cls, cookie: dict) -> Session | None:
        """创建并验证会话"""
        session = Session()
        adapter = cls._get_shared_adapter()
        session.mount("https://", adapter)
        session.cookies.update(cookie)
        session.headers.update(HEADERS)

        session.hooks["response"] = [cls._set_utf8_encoding]

        for _ in range(3):
            try:
                res = session.get(cls.INDEX_URL, allow_redirects=False, timeout=10)
                if "商店" in res.text:
                    return session
            except Exception:
                time.sleep(1)

    @classmethod
    def get_index_html(cls, session: Session) -> str | None:
        """获取大乐斗首页内容"""
        for _ in range(3):
            response = session.get(cls.INDEX_URL, headers=HEADERS)
            if "商店" in response.text:
                return response.text.split("【退出】")[0]
