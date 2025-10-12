import time

import requests
from requests import Session
from requests.adapters import HTTPAdapter

from .utils import HEADERS


class SessionManager:
    """会话管理类"""

    _adapter: HTTPAdapter | None = None

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

    @staticmethod
    def create_verified_session(cookie: dict) -> Session | None:
        """创建并验证会话"""
        url = "https://dld.qzapp.z.qq.com/qpet/cgi-bin/phonepk?cmd=index"
        session = Session()
        adapter = SessionManager._get_shared_adapter()
        session.mount("https://", adapter)
        session.cookies.update(cookie)
        session.headers.update(HEADERS)

        for _ in range(3):
            try:
                res = session.get(url, allow_redirects=False, timeout=10)
                res.encoding = "utf-8"
                if "商店" in res.text:
                    return session
            except Exception:
                time.sleep(1)

    @staticmethod
    def get_index_html(session: Session) -> str | None:
        """获取大乐斗首页内容"""
        url = "https://dld.qzapp.z.qq.com/qpet/cgi-bin/phonepk?cmd=index"
        for _ in range(3):
            response = session.get(url, headers=HEADERS)
            response.encoding = "utf-8"
            if "商店" in response.text:
                return response.text.split("【退出】")[0]
