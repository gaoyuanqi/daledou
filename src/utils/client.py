import asyncio
import traceback

import httpx


class RequestError(Exception):
    pass


class Client:
    BASE_URL = "https://dld.qzapp.z.qq.com/qpet/cgi-bin/phonepk?"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0",
    }

    def __init__(self, qq: str, cookies: dict[str, str]):
        self._qq = qq
        self._cookies = httpx.Cookies()
        for name, value in cookies.items():
            self._cookies.set(name, value)

        self._client = httpx.AsyncClient(
            headers=self.HEADERS,
            cookies=self._cookies,
            timeout=10.0,
            follow_redirects=True,
        )
        self.html: str = ""

    async def get(self, path: str) -> str:
        url = f"{self.BASE_URL}{path}"
        try:
            for _ in range(3):
                response = await self._client.get(url)
                self.html = response.text
                if "系统繁忙" in self.html:
                    await asyncio.sleep(0.2)
                    continue
                return self.html
            return self.html
        except httpx.TooManyRedirects:
            raise RequestError(f"超过最大重定向次数（可能Cookie失效）: {url}")
        except Exception:
            raise RequestError(traceback.format_exc())

    async def close(self):
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()
