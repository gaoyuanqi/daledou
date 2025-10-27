import os
import re
import queue
import threading
import time
import traceback
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from functools import lru_cache
from importlib import import_module
from typing import Generator, Pattern, Self

from requests import Session

from .config import Config
from .log import LogManager, LoguruLogger
from .session import SessionManager
from .utils import (
    DLD_EXECUTION_MODE_ENV,
    HEADERS,
    ExecutionMode,
    Input,
    ModulePath,
    TaskType,
    formatted_time,
    print_separator,
    push,
)


_CPU_COUNT = os.cpu_count() or 1
_IS_WINDOWS = sys.platform.startswith("win")
_MAX_CONCURRENCY = 5


class DaLeDou:
    """大乐斗实例方法"""

    _pattern_cache = lru_cache(maxsize=256)(re.compile)
    _shared_default_pattern = re.compile(r"<br />(.*?)<", re.DOTALL)

    def __init__(
        self,
        qq: str,
        session: Session,
        qq_logger: LoguruLogger,
        handler_id: int,
        task_config: dict[str, dict],
        push_token: str | None = None,
    ):
        self._qq = qq
        self._session = session
        self._qq_logger = qq_logger
        self._handler_id = handler_id
        self._config = task_config
        self._push_token = push_token
        self._task_names: list[str] = list(task_config)
        self._task_len: int = len(self.task_names)

        self._start_time = None
        self._end_time = None
        self._current_task_index = 0
        self._last_log: str | None = None
        self._pushplus_content: list[str] = [
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 星期{self.week}"
        ]

        self.html: str | None = None
        self.current_task_name: str | None = None

    @property
    def year(self) -> int:
        return datetime.now().year

    @property
    def month(self) -> int:
        return datetime.now().month

    @property
    def day(self) -> int:
        return datetime.now().day

    @property
    def week(self) -> int:
        return datetime.now().isoweekday()

    @property
    def config(self) -> dict[str, dict]:
        return self._config

    @property
    def pushplus_content(self) -> str:
        """返回pushplus内容"""
        self.append(f"\n【运行时间】{self._get_running_time()}")
        return "\n".join(self._pushplus_content)

    @property
    def task_names(self) -> list[str]:
        return self._task_names

    @classmethod
    def _compile_pattern(cls, pattern: str) -> Pattern:
        return cls._pattern_cache(pattern, re.DOTALL)

    def _get_progress(self) -> str:
        """获取进度字符串"""
        return f"{self._current_task_index}/{self._task_len}"

    def _get_running_time(self) -> str:
        """获取运行时间"""
        if self._start_time is None:
            return "未开始"

        if self._end_time:
            delta = self._end_time - self._start_time
        else:
            delta = datetime.now() - self._start_time
        return formatted_time(delta)

    def append(self, info: str | None = None) -> None:
        """向pushplus正文追加消息内容

        示例:
            >>> # 直接追加字符串
            >>> d.append("大乐斗") # 将"大乐斗"添加到正文

            >>> # 链式调用追加日志内容
            >>> d.log("大乐斗").append() # 将日志内容写入正文

            >>> # 分步操作
            >>> d.log("旧日志内容")
            >>> d.log("大乐斗")
            >>> d.append() # 将最近的日志内容"大乐斗"追加到正文
        """
        content = info or self._last_log
        if content:
            self._pushplus_content.append(content)

    def complete_task(self):
        """记录任务完成"""
        self._current_task_index += 1

        # 检查是否完成所有任务
        if self._current_task_index >= self._task_len:
            self._end_time = datetime.now()
            self.log(f"{self._get_running_time()}", "运行时间")

    def find(self, regex: str | None = None) -> str | None:
        """返回成功匹配的首个结果"""
        if not self.html:
            return None

        pattern = (
            self._compile_pattern(regex) if regex else self._shared_default_pattern
        )
        _match = pattern.search(self.html)
        return _match.group(1) if _match else None

    def findall(self, regex: str, html: str | None = None) -> list[str]:
        """返回匹配的所有结果"""
        content = html or self.html
        if not content:
            return []
        return re.findall(regex, content, re.DOTALL)

    def get(self, path: str) -> str:
        """发送GET请求获取HTML源码

        Args:
            path: URL路径参数，以cmd开头

        Returns:
            成功时返回HTML文本，失败时返回None
        """
        url = f"https://dld.qzapp.z.qq.com/qpet/cgi-bin/phonepk?{path}"
        for _ in range(3):
            response = self._session.get(url, headers=HEADERS, timeout=10)
            self.html = response.text
            if "系统繁忙" in self.html:
                time.sleep(0.2)
                continue
            elif "操作频繁" in self.html:
                time.sleep(1)
                continue
            break
        return self.html

    def get_display_info(self):
        """获取终端显示信息"""
        return (
            f"{self._qq} | "
            f"进度: {self._get_progress():>5} | "
            f"运行时间: {self._get_running_time()}"
        )

    def log(self, info: str, task_name: str | None = None) -> Self:
        """记录日志信息"""
        self._last_log = info
        task = task_name or self.current_task_name
        self._qq_logger.info(f"{self._qq} | {task} | {info}")
        return self

    def pushplus_send(self, task_type: TaskType) -> None:
        """发送pushplus通知"""
        push(
            token=self._push_token,
            title=f"{self._qq} {task_type}",
            content=self.pushplus_content,
            qq_logger=self._qq_logger,
        )

    def remove_qq_handler(self):
        """移除QQ日志处理器"""
        LogManager.remove_handler(self._handler_id)

    def start_timing(self):
        """开始执行任务"""
        self._start_time = datetime.now()


def _generate_daledou_instances(
    task_type: TaskType, select_qq: str | None = None
) -> Generator[DaLeDou, None, None]:
    """生成大乐斗账号实例的生成器"""
    for config_file in Config.list_numeric_config_files():
        if select_qq is not None and select_qq not in config_file:
            continue

        account_config = Config.load_and_merge_account_config(config_file)
        qq, cookie, push_token, is_activate_account = Config.parse_account_credentials(
            account_config
        )

        qq_logger, handler_id = LogManager.get_qq_logger(qq)
        if not is_activate_account:
            qq_logger.warning(f"{qq} | {config_file} 配置账号为未激活状态，已跳过执行")
            push(
                push_token,
                f"{qq} | 账号未激活",
                f"{config_file} 配置账号为未激活状态，已跳过执行",
                qq_logger,
            )
            continue

        session = SessionManager.create_verified_session(cookie)
        if session is None:
            qq_logger.error(
                f"{qq} | Cookie无效或已过期，请在 {config_file} 配置文件中更新Cookie"
            )
            push(
                push_token,
                f"{qq} | Cookie无效或已过期",
                f"请在 {config_file} 配置文件中更新Cookie",
                qq_logger,
            )
            continue

        html = SessionManager.get_index_html(session)
        if html is None:
            qq_logger.warning(
                f"{qq} 无法连接大乐斗服务器，可能服务繁忙或正在维护，已跳过执行"
            )
            push(
                push_token,
                f"{qq} | 连接失败",
                "无法连接大乐斗服务器，可能服务繁忙或正在维护，已跳过执行",
                qq_logger,
            )
            continue

        task_config = Config.filter_active_tasks(account_config, task_type, html)
        if not task_config:
            qq_logger.warning(
                f"{qq} | 无可用任务，可能{task_type}类型任务不在执行时间、未找到或者未配置"
            )
            push(
                push_token,
                f"{qq} | 无可用任务",
                f"可能{task_type}类型任务不在执行时间、未找到或者未配置",
                qq_logger,
            )
            continue

        yield DaLeDou(
            qq,
            session,
            qq_logger,
            handler_id,
            task_config,
            push_token,
        )


def _run_tasks(d: DaLeDou, task_names: list[str], module_path: ModulePath):
    """执行单个账号的所有任务"""
    module_type = import_module(module_path)
    d.start_timing()
    for task_name in task_names:
        try:
            d.current_task_name = task_name
            d.append(f"\n【{task_name}】")

            task_func = getattr(module_type, task_name, None)
            if task_func and callable(task_func):
                task_func(d)
            else:
                d.log(f"函数 {task_name} 不存在").append()

            d.complete_task()
        except Exception:
            d.log(traceback.format_exc()).append()


class Concurrency:
    """并发执行所有账号"""

    @classmethod
    def _display_accounts_status(
        cls, active_accounts: list[DaLeDou], completed_count: int
    ):
        """打印活跃账号状态和已完成账号数"""
        # 清屏并移动光标到左上角
        if _IS_WINDOWS:
            os.system("cls")
        else:
            sys.stdout.write("\033[2J\033[H")
            sys.stdout.flush()

        if not active_accounts:
            return

        print_separator()
        print(f"已完成账号数: {completed_count}")

        for d in active_accounts:
            print_separator()
            print(d.get_display_info())
        print_separator()

    @classmethod
    def execute_accounts(cls, task_type: TaskType, module_path: ModulePath):
        """并发执行多个账号"""
        global_start_time = datetime.now()
        optimal_concurrency = min(_CPU_COUNT * 2, _MAX_CONCURRENCY)
        d_gen = _generate_daledou_instances(task_type)
        active_accounts = []
        completed_count = 0
        lock = threading.Lock()
        account_queue = queue.Queue()
        executor = None

        def fill_queue():
            try:
                for d in d_gen:
                    account_queue.put(d)
            finally:
                for _ in range(optimal_concurrency):
                    account_queue.put(None)

        filler_thread = threading.Thread(target=fill_queue, daemon=True)
        filler_thread.start()

        def monitor_status(monitor_event: threading.Event):
            """账号状态监控线程"""
            while not monitor_event.is_set():
                with lock:
                    cls._display_accounts_status(active_accounts, completed_count)
                time.sleep(0.5)

        monitor_event = threading.Event()
        monitor_thread = threading.Thread(
            target=monitor_status, args=(monitor_event,), daemon=True
        )
        monitor_thread.start()

        try:
            with ThreadPoolExecutor(max_workers=optimal_concurrency) as executor:
                futures = {}

                def worker():
                    nonlocal completed_count, active_accounts
                    while True:
                        try:
                            d = account_queue.get(timeout=1)
                            if d is None:
                                account_queue.task_done()
                                return

                            with lock:
                                active_accounts.append(d)

                            try:
                                _run_tasks(d, d.task_names, module_path)
                                d.pushplus_send(task_type)
                            finally:
                                d.remove_qq_handler()
                                with lock:
                                    active_accounts.remove(d)
                                    completed_count += 1

                            account_queue.task_done()
                        except queue.Empty:
                            if not filler_thread.is_alive() and account_queue.empty():
                                return
                        except Exception:
                            traceback.print_exc()
                            account_queue.task_done()

                for _ in range(optimal_concurrency):
                    future = executor.submit(worker)
                    futures[future] = future

                for future in as_completed(futures):
                    future.result()

            filler_thread.join(timeout=5)
        finally:
            monitor_event.set()
            monitor_thread.join(timeout=1)
            with lock:
                cls._display_accounts_status(active_accounts, completed_count)

        end_time = datetime.now()
        total_time = end_time - global_start_time
        print_separator()
        print(f"总完成账号数: {completed_count}")
        print(f"总运行时间: {formatted_time(total_time)}")
        print(
            f"任务完成时间：{end_time.strftime('%Y-%m-%d %H:%M:%S')} 星期{end_time.isoweekday()}"
        )
        print_separator()


class TaskSchedule:
    @classmethod
    def _execute_sequential(cls, task_type: TaskType, module_path: ModulePath):
        """顺序执行所有账号"""
        # 日志同时输出终端和文件
        LogManager.set_terminal_output_format()

        for d in _generate_daledou_instances(task_type):
            _run_tasks(d, d.task_names, module_path)
            d.pushplus_send(task_type)
            d.remove_qq_handler()
            print_separator()

    @classmethod
    def _execute_concurrent(cls, task_type: TaskType, module_path: ModulePath):
        """并发执行所有账号"""
        # 仅写入日志文件，不输出到终端
        LogManager.remove_handler()

        Concurrency.execute_accounts(task_type, module_path)

    @classmethod
    def execute(cls, task_type: TaskType, module_path: ModulePath):
        """执行任务（根据环境变量选择模式）"""
        mode = os.environ.get(DLD_EXECUTION_MODE_ENV, ExecutionMode.SEQUENTIAL)
        if mode == ExecutionMode.SEQUENTIAL:
            cls._execute_sequential(task_type, module_path)
        else:
            cls._execute_concurrent(task_type, module_path)

    @staticmethod
    def execute_debug(task_type: TaskType, module_path: ModulePath):
        """调试模式 - 选择特定账号和任务执行"""
        qq_list = Config.list_all_qq_numbers()
        if not qq_list:
            return

        from importlib import reload

        # 日志同时输出终端和文件
        LogManager.set_terminal_output_format()

        common_module = "src.daledou.tasks.common"
        task_types = {TaskType.ONE, TaskType.TWO}

        while True:
            qq = Input.select("请选择账号：", qq_list)
            if qq is None:
                return

            if task_type in task_types:
                reload(import_module(common_module))
            reload(import_module(module_path))

            for d in _generate_daledou_instances(task_type, qq):
                task_name = Input.select("请选择任务：", d.task_names)
                if task_name is None:
                    break

                if task_type in task_types:
                    d._task_len = 1

                _run_tasks(d, [task_name], module_path)

                if task_type in task_types:
                    print_separator()
                    print(d.pushplus_content)
                d.remove_qq_handler()
                print_separator()
