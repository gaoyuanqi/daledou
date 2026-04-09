import asyncio

import httpx


class CookieInvalid(Exception):
    pass


class RequestError(Exception):
    pass


class Client:
    BASE_URL = "https://dld.qzapp.z.qq.com/qpet/cgi-bin/phonepk?"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...",
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
            follow_redirects=False,
        )
        self.html: str = ""

    async def get(self, path: str) -> str:
        url = f"{self.BASE_URL}{path}"
        for _ in range(3):
            response = await self._client.get(url)
            self.html = response.text
            if response.status_code != 200 and "大乐斗" not in self.html:
                raise CookieInvalid(
                    f"Cookie 无效，"
                    f"状态码={response.status_code}，"
                    f"URL={url}，\n"
                    f"响应: \n{self.html}"
                )

            if "系统繁忙" in self.html:
                await asyncio.sleep(0.2)
                continue
            return self.html
        return self.html

    async def close(self):
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()
