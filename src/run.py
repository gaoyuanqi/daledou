import asyncio
import sys
import traceback
from collections import Counter
from typing import Callable

from src.tasks.register import TaskModule
from src.utils.client import Client, RequestError
from src.utils.config import Config, ConfigResolver
from src.utils.daledou import DaLeDou
from src.utils.date_time import DateTime


class TaskRunner:
    """异步任务执行器，支持多账号并发处理"""

    def __init__(
        self,
        cookies: dict[str, dict[str, str]],
        module: TaskModule,
        registry: dict[str, Callable],
        max_concurrency: int = 5,
    ):
        """
        初始化任务执行器

        Args:
            cookies: 账号cookie字典，格式 {"qq": {"newuin": "...", ...}}
            module: 任务模块枚举
            registry: 任务注册表，键为任务名，值为对应的异步函数
            max_concurrency: 最大并发数
        """
        self.cookies = cookies
        self.module = module
        self.registry = registry
        self.max_concurrency = max_concurrency

        if not self.registry:
            print(f"{self.module}模块没有注册任务")
            sys.exit(1)

        if not self.cookies:
            print(f"未设置大乐斗Cookie：{Config.DLD_COOKIE_CONFIG_PATH}")
            sys.exit(1)

        self.semaphore = asyncio.Semaphore(self.max_concurrency)
        self.stats_lock = asyncio.Lock()
        self.queue = asyncio.Queue()
        self.statistics = Counter()

    async def run(self) -> None:
        """
        执行任务的主入口
        """
        total_start = DateTime.now()

        for qq, cookie_dict in self.cookies.items():
            await self.queue.put((qq, cookie_dict))

        workers = [
            asyncio.create_task(self._worker()) for _ in range(self.max_concurrency)
        ]

        await self.queue.join()
        for _ in range(self.max_concurrency):
            await self.queue.put(None)

        await asyncio.gather(*workers)

        elapsed = DateTime.now() - total_start
        print(f"总耗时: {DateTime.format_timedelta(elapsed)}")

        success_count = self.statistics.pop("success", 0)
        failure_total = sum(self.statistics.values())
        print(f"所有账号处理完成 | 成功：{success_count} | 失败：{failure_total}\n")
        if failure_total:
            print("失败原因统计：")
            for reason, count in self.statistics.items():
                print(f"-- {reason}\n")

    async def _worker(self) -> None:
        """
        工作协程，从队列获取账号并处理任务
        """
        while True:
            account_data = await self.queue.get()
            if account_data is None:
                self.queue.task_done()
                break

            async with self.semaphore:
                qq, cookie_dict = account_data

                if not cookie_dict:
                    failure_reason = f"{qq}: Cookie为空"
                    async with self.stats_lock:
                        self.statistics[failure_reason] += 1
                    self.queue.task_done()
                    continue

                try:
                    account_start = DateTime.now()
                    async with Client(qq, cookie_dict) as client:
                        config_resolver = ConfigResolver(qq, self.module)
                        d = DaLeDou(
                            qq,
                            client,
                            config_resolver,
                        )

                        index_html = await d.get("cmd=index&style=1")
                        if "邪神秘宝" not in index_html:
                            raise RequestError("非大乐斗首页（可能繁忙或者维护）")

                        for task_name, task_func in self.registry.items():
                            try:
                                if f">{task_name}<" in index_html:
                                    d.task_name = task_name
                                    await task_func(d)
                            except RequestError:
                                raise
                            except Exception:
                                d.log(traceback.format_exc(), task_name)
                                continue

                        elapsed = DateTime.now() - account_start
                        d.log(f"{DateTime.format_timedelta(elapsed)}\n", "运行耗时")

                    async with self.stats_lock:
                        self.statistics["success"] += 1
                except Exception as e:
                    traceback.print_exc()
                    failure_reason = f"{qq}: {str(e)}"
                    async with self.stats_lock:
                        self.statistics[failure_reason] += 1
                finally:
                    self.queue.task_done()
