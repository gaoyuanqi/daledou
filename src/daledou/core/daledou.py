import os
import re
import threading
import time
import traceback
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from enum import Enum
from functools import lru_cache
from pathlib import Path
from shutil import copy
from types import ModuleType
from typing import Any, Generator, Pattern, Self

import questionary
import requests
import yaml
from loguru import logger
from requests import Session
from requests.adapters import HTTPAdapter


CPU_COUNT = os.cpu_count() or 1
CONFIG_DIR = Path("./config")
DEFAULT_CONFIG_PATH = CONFIG_DIR / "default_config.yaml"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0",
}

LoguruLogger = type(logger)


class TaskType(Enum):
    TIMING = "timing"
    ONE = "one"
    TWO = "two"
    OTHER = "other"


class ModulePath(Enum):
    ONE = "src.daledou.tasks.one"
    TWO = "src.daledou.tasks.two"
    OTHER = "src.daledou.tasks.other"


class Runtime(Enum):
    ONE = "13:01"  # 第一轮定时运行时间
    TWO = "20:01"  # 第二轮定时运行时间


class ConfigManager:
    """配置管理类"""

    @staticmethod
    def create_user_config(file: str):
        """创建用户配置文件"""
        create_path = CONFIG_DIR / Path(file).name
        if not create_path.exists():
            copy(DEFAULT_CONFIG_PATH, create_path)

    @staticmethod
    def load_settings_config(key: str) -> list[str] | str:
        """加载settings.yaml配置项"""
        config_path = CONFIG_DIR / Path("settings.yaml").name
        if not config_path.exists():
            raise FileNotFoundError(f"配置文件 {config_path} 不存在")

        try:
            with config_path.open("r", encoding="utf-8") as fp:
                config_data = yaml.safe_load(fp)
                return config_data.get(key)
        except yaml.YAMLError as e:
            raise ValueError(f"配置文件解析错误：{e}")

    @staticmethod
    def load_user_config(file: str) -> dict:
        """加载用户配置文件"""
        config_path = CONFIG_DIR / Path(file).name
        if not config_path.exists():
            raise FileNotFoundError(f"配置文件 {config_path} 不存在")

        try:
            with config_path.open("r", encoding="utf-8") as fp:
                return yaml.safe_load(fp)
        except yaml.YAMLError as e:
            raise ValueError(f"配置文件解析错误：{e}")

    @staticmethod
    def load_user_cookies() -> list[str] | None:
        """加载用户大乐斗cookies"""
        if cookies := ConfigManager.load_settings_config("DALEDOU_COOKIES"):
            return cookies
        print("config/settings.yaml文件没有配置大乐斗cookies")


class Input:
    """处理用户输入"""

    @staticmethod
    def select(message: str, tasks: list) -> str | None:
        """在终端中显示任务列表供用户选择"""
        if not tasks:
            print("没有符合要求的选项")
            return

        selected = questionary.select(
            message=message,
            choices=tasks + ["取消操作"],
            use_arrow_keys=True,
            instruction="(使用↑↓方向键选择，Enter确认)",
        ).ask()

        return selected if selected != "取消操作" else None

    @staticmethod
    def text(message: str) -> str | None:
        """获取用户输入的文本"""
        response = questionary.text(
            message=message,
            instruction="(取消操作按键：CTRL + C)",
            validate=lambda text: True if text.strip() else "输入不能为空",
        ).ask()
        if response is not None:
            return response

    @staticmethod
    def _validate_number(input):
        try:
            num = int(input)
            if num < 0:
                return "数值不能小于 0"
            return True
        except ValueError:
            return "请输入有效的数字"

    @staticmethod
    def number(message: str) -> int | None:
        """获取用户输入的数字"""
        response = questionary.text(
            message=message,
            validate=Input._validate_number,
            instruction="(取消操作按键：CTRL + C)",
        ).ask()
        if response is not None:
            return int(response)


class LogContext:
    def __init__(self, qq: str):
        self.qq = qq

    def __enter__(self) -> LoguruLogger:
        self.user_logger, self.handler_id = LogManager.get_user_logger(self.qq)
        return self.user_logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        LogManager.remove_handler(self.handler_id)


class LogManager:
    """日志管理类"""

    @staticmethod
    def get_user_logger(qq: str) -> tuple[LoguruLogger, int]:
        """获取用户专属日志记录器

        返回:
            tuple[LoguruLogger, int]: (日志记录器实例, 处理器ID)
        """
        log_dir = Path(f"./log/{qq}")
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.log"

        user_logger = logger.bind(user_qq=qq)
        handler_id = user_logger.add(
            sink=log_file,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{message}</level>",
            enqueue=True,
            encoding="utf-8",
            retention="30 days",
            level="INFO",
            filter=lambda record: record["extra"].get("user_qq") == qq,
        )

        return user_logger, handler_id

    @staticmethod
    def init_console_format() -> None:
        """初始化控制台输出格式"""
        LogManager.remove_handler()
        logger.add(
            sink=sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{message}</level>",
            colorize=True,
        )

    @staticmethod
    def remove_handler(handler_id: int | None = None) -> None:
        """移除日志处理器，默认移除所有处理器"""
        if handler_id is None:
            logger.remove()
        else:
            logger.remove(handler_id)


class TaskManager:
    """任务规划类"""

    # 任务名称映射为函数名称
    _task_name_map = {
        "5.1礼包": "五一礼包",
        "5.1预订礼包": "五一预订礼包",
    }

    @staticmethod
    def _get_available_tasks(task_type: TaskType) -> list[str]:
        """获取可用任务"""
        now = datetime.now()
        day = now.day
        week = now.isoweekday()

        task = {
            "timing": {
                "商店": True,  # 这个任务不会执行，也不需添加任务
            },
            "one": {
                "邪神秘宝": True,
                "华山论剑": day <= 26,
                "斗豆月卡": True,
                "分享": True,
                "乐斗": True,
                "武林": True,
                "群侠": True,
                "侠侣": week in {2, 5, 7},
                "结拜": week == 1,
                "巅峰之战进行中": week != 2,
                "矿洞": True,
                "掠夺": week in {2, 3},
                "踢馆": week in {5, 6},
                "竞技场": day <= 25,
                "十二宫": True,
                "许愿": True,
                "抢地盘": True,
                "历练": True,
                "镖行天下": True,
                "幻境": True,
                "群雄逐鹿": week == 6,
                "画卷迷踪": True,
                "门派": True,
                "门派邀请赛": week != 2,
                "会武": week not in {5, 7},
                "梦想之旅": True,
                "问鼎天下": True,
                "帮派商会": True,
                "帮派远征军": True,
                "帮派黄金联赛": True,
                "任务派遣中心": True,
                "武林盟主": True,
                "全民乱斗": True,
                "侠士客栈": True,
                "大侠回归三重好礼": week == 4,
                "飞升大作战": True,
                "深渊之潮": True,
                "侠客岛": True,
                "时空遗迹": True,
                "世界树": True,
                "龙凰之境": day <= 27 and day not in {2, 3, 26},
                "任务": True,
                "我的帮派": True,
                "帮派祭坛": True,
                "每日奖励": True,
                "领取徒弟经验": True,
                "今日活跃度": True,
                "仙武修真": True,
                "乐斗黄历": True,
                "器魂附魔": True,
                "兵法": week in {4, 6},
                "猜单双": True,
                "煮元宵": True,
                "万圣节": True,
                "元宵节": week == 4,
                "神魔转盘": True,
                "乐斗驿站": True,
                "幸运转盘": True,
                "冰雪企缘": True,
                "甜蜜夫妻": True,
                "乐斗菜单": True,
                "客栈同福": True,
                "周周礼包": True,
                "登录有礼": True,
                "活跃礼包": True,
                "上香活动": True,
                "徽章战令": True,
                "生肖福卡": True,
                "长安盛会": True,
                "深渊秘宝": True,
                "中秋礼盒": True,
                "双节签到": True,
                "乐斗游记": True,
                "斗境探秘": True,
                "幸运金蛋": True,
                "春联大赛": True,
                "新春拜年": True,
                "喜从天降": True,
                "节日福利": True,
                "预热礼包": True,
                "5.1礼包": week == 4,
                "浩劫宝箱": week == 4,
                "端午有礼": week == 4,
                "圣诞有礼": week == 4,
                "新春礼包": week == 4,
                "登录商店": week == 4,
                "盛世巡礼": week == 4,
                "新春登录礼": True,
                "年兽大作战": True,
                "惊喜刮刮卡": True,
                "开心娃娃机": True,
                "好礼步步升": True,
                "企鹅吉利兑": True,
                "乐斗大笨钟": True,
                "乐斗激运牌": True,
                "乐斗能量棒": True,
                "乐斗回忆录": week == 4,
                "爱的同心结": week == 4,
                "乐斗儿童节": week == 4,
                "周年生日祝福": week == 4,
                "重阳太白诗会": True,
                "5.1预订礼包": True,
            },
            "two": {
                "邪神秘宝": True,
                "帮派商会": True,
                "任务派遣中心": True,
                "侠士客栈": True,
                "深渊之潮": True,
                "侠客岛": True,
                "龙凰之境": 4 <= day <= 25,
                "背包": True,
                "镶嵌": week == 4,
                "神匠坊": day == 20,
                "每日宝箱": day == 20,
                "商店": True,
                "客栈同福": True,
                "幸运金蛋": True,
                "新春拜年": True,
                "乐斗大笨钟": True,
            },
            "other": {
                "奥义": True,
                "背包": True,
                "掠夺": week == 2,
                "神装": True,
                "星盘": True,
                "佣兵": True,
                "专精": True,
                "神魔录": True,
                "江湖长梦": True,
                "深渊之潮": True,
                "仙武修真": True,
                "新元婴神器": True,
                "巅峰之战进行中": True,
            },
        }

        return [k for k, v in task[task_type.value].items() if v]

    @staticmethod
    def _fetch_dld_index(qq: str, session: Session) -> str | None:
        """获取大乐斗首页内容"""
        url = "https://dld.qzapp.z.qq.com/qpet/cgi-bin/phonepk?cmd=index"
        for _ in range(3):
            response = session.get(url, headers=HEADERS)
            response.encoding = "utf-8"
            if "商店" in response.text:
                return response.text.split("【退出】")[0]

    @staticmethod
    def _normalize_task_names(task_names: list[str]) -> list[str]:
        """规范化任务名称到函数名称"""
        return [TaskManager._task_name_map.get(name, name) for name in task_names]

    @staticmethod
    def get_task_func_names(
        qq: str, session: Session, task_type: TaskType
    ) -> list[str]:
        """获取任务对应的函数名称列表"""
        html = TaskManager._fetch_dld_index(qq, session)
        if not html:
            return

        task = TaskManager._get_available_tasks(task_type)
        return TaskManager._normalize_task_names([m for m in task if m in html])


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
    def parse_cookie(cookie_str: str) -> dict:
        """解析Cookie字符串为字典"""
        cookies = {}
        for item in cookie_str.split("; "):
            if "=" in item:
                k, v = item.split("=", 1)
                cookies[k.strip()] = v.strip()
        return cookies

    @staticmethod
    def create_verified_session(qq: str, cookie_dict: dict) -> Session | None:
        """创建并验证会话"""
        url = "https://dld.qzapp.z.qq.com/qpet/cgi-bin/phonepk?cmd=index"

        session = Session()
        adapter = SessionManager._get_shared_adapter()
        session.mount("https://", adapter)

        session.cookies.update(cookie_dict)
        session.headers.update(HEADERS)

        for _ in range(3):
            try:
                res = session.get(url, allow_redirects=False, timeout=10)
                res.encoding = "utf-8"
                if "商店" in res.text:
                    return session
            except Exception:
                time.sleep(1)


def formatted_time(delta: timedelta) -> str:
    """格式化时间 HH:MM:SS"""
    total_seconds = int(delta.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def print_separator() -> None:
    """打印分隔符，根据终端宽度自适应"""
    try:
        width = os.get_terminal_size().columns
    except OSError:
        width = 80

    if width <= 80:
        separator = "-" * width
    elif width <= 120:
        separator = "-" * int(width * 0.8)
    else:
        separator = "-" * int(width * 0.6)

    print(separator)


def push(title: str, content: str, user_logger: LoguruLogger) -> None:
    """pushplus微信通知"""
    token: str = ConfigManager.load_settings_config("PUSHPLUS_TOKEN")
    if not token or not len(token) == 32:
        user_logger.warning(f"pushplus |无效token： {token}")
        return

    url = "http://www.pushplus.plus/send/"
    data = {
        "token": token,
        "title": title,
        "content": content,
    }
    res = requests.post(url, data=data, timeout=10)
    user_logger.success(f"pushplus | {res.json()}")


class DaLeDou:
    """大乐斗实例方法"""

    _pattern_cache = lru_cache(maxsize=256)(re.compile)
    _shared_default_pattern = re.compile(r"<br />(.*?)<", re.DOTALL)

    def __init__(
        self,
        qq: str,
        session: Session,
        user_logger: LoguruLogger,
        task_type: TaskType,
        task_names: list[str],
    ):
        self._qq = qq
        self._session = session
        self._user_logger = user_logger
        self._task_type = task_type.value
        self._task_names = task_names

        ConfigManager.create_user_config(f"{self._qq}.yaml")

        self._start_time = None
        self._end_time = None
        self._current_task_index = 0
        self._last_log: str | None = None
        self._pushplus_content: list[str] = [
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 星期{self.week}"
        ]
        self._config: dict[str, Any] = ConfigManager.load_user_config(
            f"{self._qq}.yaml"
        )

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
    def config(self) -> dict[str, Any]:
        return self._config

    @property
    def task_names(self) -> list[str]:
        return self._task_names

    @classmethod
    def _compile_pattern(cls, pattern: str) -> Pattern:
        return cls._pattern_cache(pattern, re.DOTALL)

    def get(self, path: str) -> str | None:
        """送GET请求获取HTML源码

        参数:
            path: URL路径参数，以cmd开头
        返回:
            成功时返回HTML文本，失败时返回None
        """
        url = f"https://dld.qzapp.z.qq.com/qpet/cgi-bin/phonepk?{path}"
        for _ in range(3):
            response = self._session.get(url, headers=HEADERS, timeout=10)
            response.encoding = "utf-8"
            self.html = response.text
            if "系统繁忙" in self.html:
                time.sleep(0.2)
                continue
            elif "操作频繁" in self.html:
                time.sleep(1)
                continue
            return self.html

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

    def log(self, info: str, task_name: str | None = None) -> Self:
        """记录日志信息"""
        task = task_name or self.current_task_name
        self._user_logger.info(f"{self._qq} | {task} | {info}")
        self._last_log = info
        return self

    def append(self, info: str | None = None) -> None:
        """
        向pushplus正文追加消息内容

        示例：
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

    def pushplus_content(self) -> str:
        self.append(f"\n【运行时间】{self._get_running_time()}")
        return "\n".join(self._pushplus_content)

    def pushplus_send(self) -> None:
        """发送pushplus通知"""
        push(
            title=f"{self._qq} {self._task_type}",
            content=self.pushplus_content(),
            user_logger=self._user_logger,
        )

    def _get_progress(self) -> str:
        """获取进度字符串"""
        return f"{self._current_task_index}/{len(self.task_names)}"

    def _get_running_time(self) -> str:
        """获取运行时间"""
        if self._start_time is None:
            return "未开始"

        if self._end_time:
            delta = self._end_time - self._start_time
        else:
            delta = datetime.now() - self._start_time
        return formatted_time(delta)

    def start_timing(self):
        """开始执行任务"""
        self._start_time = datetime.now()

    def complete_task(self):
        """记录任务完成"""
        self._current_task_index += 1

        # 检查是否完成所有任务
        if self._current_task_index >= len(self.task_names):
            self._end_time = datetime.now()
            self.log(f"{self._get_running_time()}", "运行时间")

    def get_display_info(self):
        """获取终端显示信息"""
        return (
            f"{self._qq} | "
            f"进度: {self._get_progress():>5} | "
            f"运行时间: {self._get_running_time()}"
        )


def get_all_qq() -> list[str]:
    """返回所有QQ"""
    qq_list = []
    cookies: list = ConfigManager.load_user_cookies()
    if cookies is None:
        return
    for cookie in cookies:
        cookie_dict = SessionManager.parse_cookie(cookie)
        qq = cookie_dict["newuin"]
        qq_list.append(qq)
    return qq_list


def generate_dld_debug_instances(
    task_type: TaskType, select_qq: str | None = None
) -> Generator[DaLeDou, None, None]:
    """生成调试模式的大乐斗实例"""
    cookies: list = ConfigManager.load_user_cookies()
    if cookies is None:
        return

    LogManager.init_console_format()
    for cookie in cookies:
        cookie_dict = SessionManager.parse_cookie(cookie)
        qq = cookie_dict["newuin"]

        if select_qq is not None and select_qq != qq:
            continue

        with LogContext(qq) as user_logger:
            session = SessionManager.create_verified_session(qq, cookie_dict)
            if session is None:
                user_logger.error(f"{qq} | Cookie无效")
                continue

            task_names = TaskManager.get_task_func_names(qq, session, task_type)
            if not task_names:
                user_logger.warning(f"{qq} | 未找到可用任务，可能官方繁忙或者维护")
                continue

            user_logger.success(f"{qq} | Cookie有效")
            yield DaLeDou(qq, session, user_logger, task_type, task_names)


def generate_dld_instances(task_type: TaskType) -> Generator[DaLeDou, None, None]:
    """生成并发模式的大乐斗实例"""
    cookies: list = ConfigManager.load_user_cookies()
    if cookies is None:
        return

    LogManager.remove_handler()
    for cookie in cookies:
        cookie_dict = SessionManager.parse_cookie(cookie)
        qq = cookie_dict["newuin"]

        user_logger, _ = LogManager.get_user_logger(qq)
        session = SessionManager.create_verified_session(qq, cookie_dict)
        if session is None:
            user_logger.error(f"{qq} | Cookie无效")
            push(
                f"{qq} | Cookie无效",
                "请更换Cookie",
                user_logger,
            )
            continue

        task_names = TaskManager.get_task_func_names(qq, session, task_type)
        if not task_names:
            user_logger.warning(f"{qq} | 未找到可用任务，可能官方繁忙或者维护")
            push(
                f"{qq} | 未找到可用任务",
                "可能官方繁忙或者维护",
                user_logger,
            )
            continue

        yield DaLeDou(qq, session, user_logger, task_type, task_names)


def run_account_tasks(d: DaLeDou, task_names: list[str], module_type: ModuleType):
    """执行单个账号的所有任务"""
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


class TaskExecutor:
    """线程管理类，用于并发执行多个大乐斗账号"""

    @staticmethod
    def run(task_type: TaskType, module_type: ModuleType):
        """并发执行多个账号"""
        ds = list(generate_dld_instances(task_type))
        if not ds:
            return

        global_start_time = datetime.now()
        optimal_concurrency = min(CPU_COUNT * 4, len(ds))
        monitor_event = threading.Event()

        def monitor_status():
            """账号状态监控线程"""
            while not monitor_event.is_set():
                TaskExecutor._print_accounts_status(ds)
                time.sleep(0.5)

        monitor_thread = threading.Thread(target=monitor_status, daemon=True)
        monitor_thread.start()

        try:
            with ThreadPoolExecutor(max_workers=optimal_concurrency) as executor:
                futures = [
                    executor.submit(TaskExecutor._run_account_tasks, d, module_type)
                    for d in ds
                ]
                for future in futures:
                    future.result()
        finally:
            monitor_event.set()
            monitor_thread.join(timeout=1)
            TaskExecutor._print_accounts_status(ds)

        _now = datetime.now()
        total_time = _now - global_start_time
        print(f"总运行时间: {formatted_time(total_time)}")
        print(f"结束时间：{_now.strftime('%Y-%m-%d %H:%M:%S')} 星期{_now.isoweekday()}")
        print_separator()

    @staticmethod
    def _run_account_tasks(d: DaLeDou, module_type: ModuleType):
        """执行单个账号的所有任务"""
        run_account_tasks(d, d.task_names, module_type)
        d.pushplus_send()

    @staticmethod
    def _print_accounts_status(accounts: list[DaLeDou]):
        """打印所有账号状态到控制台"""
        # 清屏并移动光标到左上角
        os.system("cls" if os.name == "nt" else "clear")

        print_separator()
        for d in accounts:
            print(d.get_display_info())
        print_separator()
