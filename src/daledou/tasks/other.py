"""
本模块为大乐斗其它任务
"""

import time
from abc import ABC, abstractmethod

from ..core.daledou import DaLeDou, print_separator, Input


def compute(fail_value, consume_num, now_value, total_value) -> int:
    """
    返回技能强化至满祝福或者满进度时消耗的材料数量

    进度满了会升级成功；祝福满了不一定升级成功

    Args:
        fail_value: int类型，失败祝福值或者进度
        consume_num: int类型，强化一次消耗材料数量
        now_value: int类型，当前祝福值或者当前进度
        total_value: int类型，总祝福值或者总进度
    """
    # 计算强化次数，向上取整
    upgrade_count = -((now_value - total_value) // fail_value)
    # 计算总消耗材料数量
    total_deplete = upgrade_count * consume_num
    return total_deplete


def get_blessing_value(d: DaLeDou) -> tuple[int, int]:
    """返回当前祝福（进度）、总祝福（进度）"""
    now_value = int(d.find(r"(\d+)/\d+"))
    total_value = int(d.find(r"\d+/(\d+)"))
    return now_value, total_value


def get_blessing_event(d: DaLeDou) -> str:
    """请求祝福活动"""
    d.get("cmd=index&channel=0")
    if "祝福合集宝库" in d.html:
        d.get("cmd=newAct&subtype=143")
    elif "远方祝福" in d.html:
        d.get("cmd=newAct&subtype=153")


def get_consume(d: DaLeDou, backpack_id: str = None) -> tuple[str, int, int]:
    """返回材料消耗名称、消耗数量、拥有数量"""
    consume_name = d.find(r"消耗：(.*?)\*")
    consume_num = int(d.find(r"\*(\d+)"))
    if backpack_id is None:
        possess_num = int(d.find(r"消耗：.*?\d+.*?(\d+)"))
    else:
        possess_num = d.get_backpack_number(backpack_id)
    return consume_name, consume_num, possess_num


def get_store_points(d: DaLeDou, params: str) -> int:
    """返回商店积分"""
    # 商店
    d.get(params)
    result = d.find(r"<br />(.*?)<")
    _, store_points = result.split("：")
    return int(store_points)


def is_close_auto_buy(d: DaLeDou, name: str, close_url: str) -> bool:
    """是否关闭自动斗豆兑换"""
    # 关闭自动斗豆兑换
    d.get(close_url)
    if "关闭自动" in d.html or "关闭斗豆" in d.html:
        d.log("存在没有关闭自动斗豆兑换，请手动关闭", name)
        return False
    d.log("关闭自动斗豆兑换", name)
    print_separator()
    return True


class Exchange:
    """积分商店兑换"""

    def __init__(
        self,
        d: DaLeDou,
        url: dict,
        consume_num: int,
        possess_num: int,
        store_name: str,
        regex: str | None = None,
    ):
        self.d = d
        # 材料兑换10个链接
        self.exchange_ten_url = url["ten"]
        # 材料兑换一个链接
        self.exchange_one_url = url["one"]
        self.consume_num = consume_num
        self.possess_num = possess_num
        self.store_name = store_name
        self.regex = regex

    def is_exchange(self) -> bool:
        """
        如果材料拥有数量大于等于消耗数量则不需兑换返回True

        如果材料消耗数量大于材料拥有数量则兑换两者差值数量的材料：
            成功兑换差值则返回True
            不足兑换差值则返回False
        """
        if self.possess_num >= self.consume_num:
            return True

        exchange_num = self.consume_num - self.possess_num

        if self.exchange_ten_url == self.exchange_one_url:
            # 有些物品只能一个兑换，比如江湖长梦、许愿帮铺
            if not self.exchange_count(self.exchange_one_url, exchange_num):
                return False
        else:
            ten_count, one_count = divmod(exchange_num, 10)
            if not self.exchange_count(self.exchange_ten_url, ten_count):
                return False
            if not self.exchange_count(self.exchange_one_url, one_count):
                return False

        # 兑换成功则两者数量一致
        self.possess_num = self.consume_num
        print_separator()
        return True

    def exchange_count(self, url: str, count: int) -> bool:
        """兑换足够数量返回True，否则返回False"""
        while count > 0:
            self.d.get(url)
            self.d.log(self.d.find(self.regex), self.store_name)
            if "成功" in self.d.html:
                count -= 1
            elif "不足" in self.d.html or "达到当日兑换上限" in self.d.html:
                return False
        return True

    def update_possess_num(self):
        """更新材料拥有数量"""
        if self.possess_num >= self.consume_num:
            self.possess_num -= self.consume_num
        print_separator()


class BaseUpgrader(ABC):
    def __init__(self, d: DaLeDou):
        self.d = d
        self.data = self.get_data()

    def exchange_instances(
        self, name: str, exchange_url_map: dict, regex: str | None = None
    ) -> Exchange:
        consume_name = self.data[name]["consume_name"]
        consume_num = self.data[name]["consume_num"]
        possess_num = self.data[name]["possess_num"]
        store_name = self.data[name]["store_name"]
        return Exchange(
            self.d,
            exchange_url_map[consume_name],
            consume_num,
            possess_num,
            store_name,
            regex,
        )

    @abstractmethod
    def get_data(self) -> dict[str, dict]:
        pass

    @abstractmethod
    def upgrade(self, name: str):
        pass


def upgrade(upgrader: BaseUpgrader):
    """执行升级流程"""
    if not upgrader.data:
        print("没有可强化的任务\n")
        print_separator()
        return

    upgrade_names = []
    for name, data in upgrader.data.items():
        if data.get("是否强化", False):
            upgrade_names.append(name)
        for k, v in data.items():
            if k in {
                "consume_name",
                "consume_num",
                "possess_num",
                "store_name",
                "store_regex",
            }:
                continue
            print(f"{k}：{v}")
        print_separator()

    selected = Input.select("请选择强化任务：", upgrade_names)
    if selected is None:
        print_separator()
        return

    upgrader.upgrade(selected)
    print_separator()


# ============================================================


class AoYi(BaseUpgrader):
    EXCHANGE_URL_MAP = {
        "奥秘元素": {
            "ten": "cmd=exchange&subtype=2&type=1261&times=10&costtype=12",
            "one": "cmd=exchange&subtype=2&type=1261&times=1&costtype=12",
        }
    }

    def __init__(self, d: DaLeDou):
        super().__init__(d)

    def get_data(self) -> dict:
        """获取奥义数据"""
        get_blessing_event(self.d)
        if "奥义" in self.d.html:
            fail_value = int(self.d.find(r"奥义五阶5星.*?获得(\d+)"))
        else:
            fail_value = 2

        data = {}
        store_name = "帮派祭坛"
        store_points = get_store_points(self.d, "cmd=exchange&subtype=10&costtype=12")
        store_exchange_num = store_points // 40

        # 奥义
        self.d.get("cmd=skillEnhance&op=0")
        if "五阶&nbsp;5星" in self.d.html:
            return {}

        name = "奥义"
        stage = self.d.find(r"阶段：(.*?)<").replace("&nbsp;", "")
        consume_name, consume_num, possess_num = get_consume(self.d)
        now_value, total_value = get_blessing_value(self.d)
        full_value_consume_num = compute(
            fail_value, consume_num, now_value, total_value
        )

        data[name] = {
            "名称": name,
            "阶段": stage,
            "消耗": f"{consume_name}*{consume_num}（{possess_num}）",
            "祝福值": f"{now_value}/{total_value}（↑{fail_value}）",
            "积分": f"{store_points}（{store_exchange_num}）",
            "满祝福消耗数量": f"{full_value_consume_num}（必成再+{consume_num}）",
            "是否强化": (possess_num + store_exchange_num)
            >= (full_value_consume_num + consume_num),
            "consume_name": consume_name,
            "consume_num": consume_num,
            "possess_num": possess_num,
            "store_name": store_name,
        }
        return data

    def upgrade(self, name: str):
        """奥义升级"""
        close_url = "cmd=skillEnhance&op=9&autoBuy=0"
        if not is_close_auto_buy(self.d, name, close_url):
            return

        e = super().exchange_instances(name, self.EXCHANGE_URL_MAP)
        while True:
            if not e.is_exchange():
                return

            # 升级
            self.d.get("cmd=skillEnhance&op=2")
            self.d.log(self.d.find(), name)
            self.d.log(self.d.find(r"祝福值：(.*?) "), name)
            if "升星失败" not in self.d.html:
                break

            e.update_possess_num()


class JiNengLan(BaseUpgrader):
    EXCHANGE_URL_MAP = {
        "四灵魂石": {
            "ten": "cmd=exchange&subtype=2&type=1262&times=10&costtype=12",
            "one": "cmd=exchange&subtype=2&type=1262&times=1&costtype=12",
        }
    }

    def __init__(self, d: DaLeDou):
        super().__init__(d)

    def get_data(self) -> dict:
        """获取奥义技能栏数据"""
        get_blessing_event(self.d)
        if "奥义" in self.d.html:
            fail_value = int(self.d.find(r"技能栏7星.*?失败(\d+)"))
        else:
            fail_value = 2

        data = {}
        store_name = "帮派祭坛"
        store_points = get_store_points(self.d, "cmd=exchange&subtype=10&costtype=12")
        store_exchange_num = store_points // 40

        # 技能栏
        self.d.get("cmd=skillEnhance&op=0&view=storage")
        for _id in self.d.findall(r'storage_id=(\d+)">查看详情'):
            # 查看详情
            self.d.get(f"cmd=skillEnhance&op=4&storage_id={_id}")

            name = self.d.find(r"<br />=(.*?)=")
            level = int(self.d.find(r"当前等级：(\d+)"))
            consume_name, consume_num, possess_num = get_consume(self.d)
            now_value, total_value = get_blessing_value(self.d)

            if level >= 8:
                fail_value = 2

            full_value_consume_num = compute(
                fail_value, consume_num, now_value, total_value
            )

            data[name] = {
                "名称": name,
                "id": _id,
                "当前等级": level,
                "消耗": f"{consume_name}*{consume_num}（{possess_num}）",
                "祝福值": f"{now_value}/{total_value}（↑{fail_value}）",
                "积分": f"{store_points}（{store_exchange_num}）",
                "满祝福消耗数量": f"{full_value_consume_num}（必成再+{consume_num}）",
                "是否强化": (possess_num + store_exchange_num)
                >= (full_value_consume_num + consume_num),
                "consume_name": consume_name,
                "consume_num": consume_num,
                "possess_num": possess_num,
                "store_name": store_name,
            }
        return data

    def upgrade(self, name: str):
        """奥义技能栏升级"""
        _id: str = self.data[name]["id"]
        close_url = f"cmd=skillEnhance&op=10&storage_id={_id}&auto_buy=0"
        if not is_close_auto_buy(self.d, name, close_url):
            return

        e = super().exchange_instances(name, self.EXCHANGE_URL_MAP)
        while True:
            if not e.is_exchange():
                return

            # 升级
            self.d.get(f"cmd=skillEnhance&op=5&storage_id={_id}")
            self.d.log(self.d.find(), name)
            self.d.log(self.d.find(r"祝福值：(.*?) "), name)
            if "升星失败" not in self.d.html:
                break

            e.update_possess_num()


def 奥义(d: DaLeDou):
    while True:
        category = Input.select("请选择分类：", ["奥义", "技能栏"])
        if category is None:
            return
        elif category == "奥义":
            upgrade(AoYi(d))
        elif category == "技能栏":
            upgrade(JiNengLan(d))


def 背包(d: DaLeDou):
    data = []
    d.get("cmd=store")
    page = int(d.find(r"第1/(\d+)"))
    for p in range(1, (page + 1)):
        d.get(f"cmd=store&store_type=0&page={p}")
        d.html = d.find(r"清理(.*?)商店")
        for _id, name, number in d.findall(r'id=(\d+)">(.*?)</a>数量：(\d+)'):
            data.append(
                {
                    "id": _id,
                    "name": name,
                    "number": number,
                }
            )

    def search_backpack(query):
        """执行背包搜索"""
        results = []
        for item in data:
            if item["id"] == query or query.lower() in item["name"].lower():
                results.append(item)
        return results

    def get_display_width(text):
        """计算字符串的显示宽度（中文算2个字符，英文算1个）"""
        width = 0
        for char in text:
            # 中文、日文、韩文等全角字符算2个宽度
            if "\u4e00" <= char <= "\u9fff" or char in "：；，。！？（）【】「」":
                width += 2
            else:
                width += 1
        return width

    def pad_to_width(text, target_width):
        """将文本填充到目标宽度"""
        current_width = get_display_width(text)
        if current_width >= target_width:
            return text
        return text + " " * (target_width - current_width)

    while True:
        text = Input.text("请输入物品ID或名称:")
        if text is None:
            break

        search_term = text.strip()
        if results := search_backpack(search_term):
            # 计算每列的最大显示宽度
            id_width = max(
                get_display_width("ID"),
                max(get_display_width(item["id"]) for item in results),
            )
            name_width = max(
                get_display_width("物品名称"),
                max(get_display_width(item["name"]) for item in results),
            )
            number_width = max(
                get_display_width("数量"),
                max(get_display_width(item["number"]) for item in results),
            )

            # 打印表头
            header = f"{pad_to_width('ID', id_width)} {pad_to_width('物品名称', name_width)} {pad_to_width('数量', number_width)}"
            print(f"\n{header}")
            print_separator()

            # 打印数据行
            for item in results:
                row = f"{pad_to_width(item['id'], id_width)} {pad_to_width(item['name'], name_width)} {pad_to_width(item['number'], number_width)}"
                print(row)
            print()
        else:
            print("\n⚠️ 未找到匹配物品")
        print_separator()


class JiTanShouHuShou(BaseUpgrader):
    EXCHANGE_URL_MAP = {
        "大型武器符咒": {
            "ten": "cmd=longdreamexchange&op=exchange&key_id=19&page=2",
            "one": "cmd=longdreamexchange&op=exchange&key_id=19&page=2",
        },
        "中型武器符咒": {
            "ten": "cmd=longdreamexchange&op=exchange&key_id=20&page=2",
            "one": "cmd=longdreamexchange&op=exchange&key_id=20&page=2",
        },
        "小型武器符咒": {
            "ten": "cmd=longdreamexchange&op=exchange&key_id=21&page=2",
            "one": "cmd=longdreamexchange&op=exchange&key_id=21&page=2",
        },
        "投掷武器符咒": {
            "ten": "cmd=longdreamexchange&op=exchange&key_id=21&page=2",
            "one": "cmd=longdreamexchange&op=exchange&key_id=21&page=2",
        },
    }

    REGEX = r"</a><br />(.*?)<"

    def __init__(self, d: DaLeDou):
        super().__init__(d)

    def get_data(self) -> dict:
        """获取祭坛守护兽数据"""
        data = {}
        fail_value = 2
        store_points = get_store_points(self.d, "cmd=longdreamexchange")
        store_exchange_num = store_points // 750

        # 江湖长梦
        self.d.get("cmd=longdreamexchange&page_type=0&page=2")
        store_exchange_data = {
            "大型武器符咒": min(
                store_exchange_num, 50 - int(self.d.find(r"大型武器符咒.*?(\d+)/"))
            ),
            "中型武器符咒": min(
                store_exchange_num, 50 - int(self.d.find(r"中型武器符咒.*?(\d+)/"))
            ),
            "小型武器符咒": min(
                store_exchange_num, 50 - int(self.d.find(r"小型武器符咒.*?(\d+)/"))
            ),
            "投掷武器符咒": min(
                store_exchange_num, 50 - int(self.d.find(r"投掷武器符咒.*?(\d+)/"))
            ),
        }

        for _id in [3, 2, 1, 0]:
            self.d.get(f"cmd=weapon_seal&op=0&type_id={_id}")
            if "五阶" in self.d.html and "5星" in self.d.html:
                continue

            stage = self.d.find(r"阶段：(.*?)<")
            star = self.d.find(r"星级：(.*?) ")
            consume_name, consume_num, possess_num = get_consume(self.d)
            now_value, total_value = get_blessing_value(self.d)
            name = consume_name[:4]
            store_exchange_num = store_exchange_data[consume_name]
            full_value_consume_num = compute(
                fail_value, consume_num, now_value, total_value
            )
            store_name = f"江湖长梦-{consume_name}*1"

            data[name] = {
                "名称": name,
                "id": _id,
                "阶段": stage,
                "星级": star,
                "消耗": f"{consume_name}*{consume_num}（{possess_num}）",
                "祝福值": f"{now_value}/{total_value}（↑{fail_value}）",
                "积分": f"{store_points}（{store_exchange_num}）",
                "满祝福消耗数量": f"{full_value_consume_num}（必成再+{consume_num}）",
                "是否强化": (possess_num + store_exchange_num)
                >= (full_value_consume_num + consume_num),
                "consume_name": consume_name,
                "consume_num": consume_num,
                "possess_num": possess_num,
                "store_name": store_name,
            }
        return data

    def upgrade(self, name: str):
        """祭坛守护兽升级"""
        _id: str = self.data[name]["id"]
        close_url = f"cmd=weapon_seal&op=9&type_id={_id}&auto_buy=0"
        if not is_close_auto_buy(self.d, name, close_url):
            return

        e = super().exchange_instances(name, self.EXCHANGE_URL_MAP, self.REGEX)
        while True:
            if not e.is_exchange():
                return

            # 升级
            self.d.get(f"cmd=weapon_seal&op=2&type_id={_id}")
            self.d.log(self.d.find(), name)
            self.d.log(self.d.find(r"祝福值：(.*?) "), name)
            if "升星失败" not in self.d.html:
                break

            e.update_possess_num()


class FengYinJiTan(BaseUpgrader):
    EXCHANGE_URL_MAP = {
        "石中剑": {
            "ten": "cmd=longdreamexchange&op=exchange&key_id=19&page=2",
            "one": "cmd=longdreamexchange&op=exchange&key_id=19&page=2",
        }
    }

    REGEX = r"</a><br />(.*?)<"

    def __init__(self, d: DaLeDou):
        super().__init__(d)

    def get_data(self) -> dict:
        """获取封印祭坛数据"""
        data = {}
        fail_value = 2
        store_points = get_store_points(self.d, "cmd=longdreamexchange")

        # 江湖长梦
        self.d.get("cmd=longdreamexchange&page_type=0&page=2")
        store_exchange_num = min(
            store_points // 750, 50 - int(self.d.find(r"石中剑.*?(\d+)/"))
        )
        store_name = "江湖长梦-石中剑*1"

        for _id in [1009, 1007, 1003, 1000]:
            self.d.get(f"cmd=weapon_seal&op=4&sacrificial_id={_id}")
            if "2阶0星" in self.d.html:
                continue

            name = self.d.find(r"<br />=(.*?)=")
            level = self.d.find(r"当前等级：(\d+)")
            now_value, total_value = get_blessing_value(self.d)
            consume_name, consume_num, possess_num = get_consume(self.d, "6496")
            full_value_consume_num = compute(
                fail_value, consume_num, now_value, total_value
            )

            data[name] = {
                "名称": name,
                "id": _id,
                "等级": level,
                "消耗": f"{consume_name}*{consume_num}（{possess_num}）",
                "祝福值": f"{now_value}/{total_value}（↑{fail_value}）",
                "积分": f"{store_points}（{store_exchange_num}）",
                "满祝福消耗数量": f"{full_value_consume_num}（必成再+{consume_num}）",
                "是否强化": (possess_num + store_exchange_num)
                >= (full_value_consume_num + consume_num),
                "consume_name": consume_name,
                "consume_num": consume_num,
                "possess_num": possess_num,
                "store_name": store_name,
            }
        return data

    def upgrade(self, name: str):
        """祭坛守护兽升级"""
        _id: str = self.data[name]["id"]
        close_url = f"cmd=weapon_seal&op=10&sacrificial_id={_id}&auto_buy=0"
        if not is_close_auto_buy(self.d, name, close_url):
            return

        e = super().exchange_instances(name, self.EXCHANGE_URL_MAP, self.REGEX)
        while True:
            if not e.is_exchange():
                return

            # 升级
            self.d.get(f"cmd=weapon_seal&op=5&sacrificial_id={_id}")
            self.d.log(self.d.find(), name)
            self.d.log(self.d.find(r"祝福值：(.*?) "), name)
            if "升星失败" not in self.d.html:
                break

            e.update_possess_num()


def 封印(d: DaLeDou):
    while True:
        category = Input.select("请选择分类：", ["祭坛守护兽", "封印祭坛"])
        if category is None:
            return
        elif category == "祭坛守护兽":
            upgrade(JiTanShouHuShou(d))
        elif category == "封印祭坛":
            upgrade(FengYinJiTan(d))


def 掠夺(d: DaLeDou):
    while True:
        max_combat_power = Input.number("请输入掠夺最大战力：")
        if max_combat_power is None:
            return

        d.get("cmd=forage_war&subtype=3")
        for _id in d.findall(r'gra_id=(\d+)">掠夺'):
            while True:
                print_separator()
                d.get(f"cmd=forage_war&subtype=3&op=1&gra_id={_id}")
                combat_power = d.find(r"<br />1.*? (\d+)\.")
                d.log(combat_power, f"{_id}战力")

                if combat_power is None:
                    break
                if int(combat_power) > max_combat_power:
                    break

                d.get(f"cmd=forage_war&subtype=4&gra_id={_id}")
                d.log(d.find("返回</a><br />(.*?)<"), "掠夺")
                d.log(d.find("生命：(.*?)<"), "生命")
                if "你已经没有足够的复活次数" in d.html:
                    return
                time.sleep(1)
        print_separator()


class ShenZhuang(BaseUpgrader):
    EXCHANGE_URL_MAP = {
        "凤凰羽毛": {
            "ten": "cmd=exchange&subtype=2&type=1100&times=10&costtype=1",
            "one": "cmd=exchange&subtype=2&type=1100&times=1&costtype=1",
        },
        "奔流气息": {
            "ten": "cmd=exchange&subtype=2&type=1205&times=10&costtype=3",
            "one": "cmd=exchange&subtype=2&type=1205&times=1&costtype=3",
        },
        "潜能果实": {
            "ten": "cmd=exchange&subtype=2&type=1200&times=10&costtype=2",
            "one": "cmd=exchange&subtype=2&type=1200&times=1&costtype=2",
        },
        "上古玉髓": {
            "ten": "cmd=exchange&subtype=2&type=1201&times=10&costtype=2",
            "one": "cmd=exchange&subtype=2&type=1201&times=1&costtype=2",
        },
        "神兵原石": {
            "ten": "cmd=arena&op=exchange&id=3573&times=10",
            "one": "cmd=arena&op=exchange&id=3573&times=1",
        },
        "软猥金丝": {
            "ten": "cmd=arena&op=exchange&id=3574&times=10",
            "one": "cmd=arena&op=exchange&id=3574&times=1",
        },
    }

    PAGE_DATA = [
        {
            "name": "神兵",
            "id": "0",
            "store_name": "竞技场",
            "store_url": "cmd=arena&op=queryexchange",
        },
        {
            "name": "神铠",
            "id": "1",
            "store_name": "竞技场",
            "store_url": "cmd=arena&op=queryexchange",
        },
        {
            "name": "神羽",
            "id": "2",
            "store_name": "踢馆",
            "store_url": "cmd=exchange&subtype=10&costtype=1",
        },
        {
            "name": "神兽",
            "id": "3",
            "store_name": "掠夺",
            "store_url": "cmd=exchange&subtype=10&costtype=2",
        },
        {
            "name": "神饰",
            "id": "4",
            "store_name": "掠夺",
            "store_url": "cmd=exchange&subtype=10&costtype=2",
        },
        {
            "name": "神履",
            "id": "5",
            "store_name": "矿洞",
            "store_url": "cmd=exchange&subtype=10&costtype=3",
        },
    ]

    def __init__(self, d: DaLeDou):
        super().__init__(d)

    def get_data(self) -> dict:
        """获取神装数据，不包含满阶和必成数据"""
        get_blessing_event(self.d)
        if "神装" in self.d.html:
            fail_value = 2 * int(self.d.find(r"神装进阶失败获得(\d+)"))
        else:
            fail_value = 2

        data = {}
        for item in self.PAGE_DATA:
            name = item["name"]
            _id = item["id"]
            store_name = item["store_name"]
            store_url = item["store_url"]

            # 神装
            self.d.get(f"cmd=outfit&op=0&magic_outfit_id={_id}")
            if "10阶" in self.d.html or "必成" in self.d.html:
                continue

            level = self.d.find(r"阶层：(.*?)<")
            consume_name, consume_num, possess_num = get_consume(self.d)
            now_value, total_value = get_blessing_value(self.d)
            full_value_consume_num = compute(
                fail_value, consume_num, now_value, total_value
            )
            store_points = get_store_points(self.d, store_url)
            store_exchange_num = store_points // 40

            data[name] = {
                "名称": name,
                "id": _id,
                "阶层": level,
                "消耗": f"{consume_name}*{consume_num}（{possess_num}）",
                "祝福值": f"{now_value}/{total_value}（↑{fail_value}）",
                f"{store_name}积分": f"{store_points}（{store_exchange_num}）",
                "满祝福消耗数量": f"{full_value_consume_num}（必成再+{consume_num}）",
                "是否强化": (possess_num + store_exchange_num)
                >= (full_value_consume_num + consume_num),
                "consume_name": consume_name,
                "consume_num": consume_num,
                "possess_num": possess_num,
                "store_name": store_name,
            }

        return data

    def upgrade(self, name: str):
        """神装进阶"""
        _id: str = self.data[name]["id"]
        close_url = f"cmd=outfit&op=4&auto_buy=2&magic_outfit_id={_id}"
        if not is_close_auto_buy(self.d, name, close_url):
            return

        e = super().exchange_instances(name, self.EXCHANGE_URL_MAP)
        while True:
            if not e.is_exchange():
                return

            # 进阶
            self.d.get(f"cmd=outfit&op=1&magic_outfit_id={_id}")
            self.d.log(self.d.find(r"神履.*?<br />(.*?)<br />"), name)
            self.d.log(self.d.find(r"祝福值：(.*?)<"), name)
            if "进阶失败" not in self.d.html:
                break

            e.update_possess_num()


class ShenJi(BaseUpgrader):
    EXCHANGE_URL_MAP = {
        "矿洞": {
            "ten": "cmd=exchange&subtype=2&type=1206&times=10&costtype=3",
            "one": "cmd=exchange&subtype=2&type=1206&times=1&costtype=3",
        },
        "掠夺": {
            "ten": "cmd=exchange&subtype=2&type=1202&times=10&costtype=2",
            "one": "cmd=exchange&subtype=2&type=1202&times=1&costtype=2",
        },
        "踢馆": {
            "ten": "cmd=exchange&subtype=2&type=1101&times=10&costtype=1",
            "one": "cmd=exchange&subtype=2&type=1101&times=1&costtype=1",
        },
        "竞技场": {
            "ten": "cmd=arena&op=exchange&id=3567&times=10",
            "one": "cmd=arena&op=exchange&id=3567&times=1",
        },
    }

    def __init__(self, d: DaLeDou, store_name: str, store_points: int):
        self.store_name = store_name
        self.store_points = store_points
        super().__init__(d)

    def get_data_id(self) -> list:
        """获取神装附带技能id，不包含满级id"""
        data = []
        for _id in range(6):
            # 神装
            self.d.get(f"cmd=outfit&op=0&magic_outfit_id={_id}")
            data += self.d.findall(r'skill_id=(\d+)">升级十次.*?等级：(\d+)')

        return [_id for _id, level in data if level != "10"]

    def get_data(self) -> dict:
        """获取神技详情数据"""
        data = {}
        store_exchange_num = self.store_points // 40
        consume_name = "神秘精华"
        possess_num = self.d.get_backpack_number("3567")

        for _id in self.get_data_id():
            self.d.get(f"cmd=outfit&op=2&magic_skill_id={_id}")

            name = self.d.find(r"<br />=(.*?)=<a")
            level = self.d.find(r"当前等级：(\d+)")
            consume_num = int(self.d.find(r"\*(\d+)<"))
            success = self.d.find(r"升级成功率：(.*?)<")
            effect = self.d.find(r"当前效果：(.*?)<")

            data[name] = {
                "名称": name,
                "id": _id,
                "当前等级": level,
                "消耗": f"{consume_name}*{consume_num}（{possess_num}）",
                "升级成功率": success,
                "当前效果": effect,
                f"{self.store_name}积分": f"{self.store_points}（{store_exchange_num}）",
                "是否强化": store_exchange_num >= consume_num,
                "consume_name": self.store_name,  # EXCHANGE_URL_MAP["consume_name"] 值是 self.store_name
                "consume_num": consume_num,
                "possess_num": possess_num,
                "store_name": self.store_name,
            }
        return data

    def upgrade(self, name: str):
        """神技升级"""
        _id: str = self.data[name]["id"]
        close_url = f"cmd=outfit&op=8&auto_buy=2&magic_outfit_id={_id}"
        if not is_close_auto_buy(self.d, name, close_url):
            return

        e = super().exchange_instances(name, self.EXCHANGE_URL_MAP)
        while True:
            if not e.is_exchange():
                return

            # 升级
            self.d.get(f"cmd=outfit&op=3&magic_skill_id={_id}")
            self.d.log(self.d.find(r"套装强化</a><br />(.*?)<br />"), name)
            if "升级失败" not in self.d.html:
                break

            e.update_possess_num()


def 神装(d: DaLeDou):
    while True:
        category = Input.select("请选择分类：", ["神装", "神技"])
        if category is None:
            return
        elif category == "神装":
            upgrade(ShenZhuang(d))
        elif category == "神技":
            select_store = []
            store_dict = {
                "矿洞": get_store_points(d, "cmd=exchange&subtype=10&costtype=3"),
                "掠夺": get_store_points(d, "cmd=exchange&subtype=10&costtype=2"),
                "踢馆": get_store_points(d, "cmd=exchange&subtype=10&costtype=1"),
                "竞技场": get_store_points(d, "cmd=arena&op=queryexchange"),
            }
            for k, v in store_dict.items():
                select_store.append(f"{k}：{v}")

            store_name = Input.select("请选择商店：", select_store)
            if store_name is None:
                return
            store_name, store_points = store_name.split("：")
            upgrade(ShenJi(d, store_name, int(store_points)))


class XingPan(BaseUpgrader):
    EXCHANGE_URL_MAP = {
        "翡翠石": {
            "ten": "cmd=exchange&subtype=2&type=1233&times=10&costtype=9",
            "one": "cmd=exchange&subtype=2&type=1233&times=1&costtype=9",
        },
        "玛瑙石": {
            "ten": "cmd=exchange&subtype=2&type=1234&times=10&costtype=9",
            "one": "cmd=exchange&subtype=2&type=1234&times=1&costtype=9",
        },
        "迅捷石": {
            "ten": "cmd=exchange&subtype=2&type=1235&times=10&costtype=9",
            "one": "cmd=exchange&subtype=2&type=1235&times=1&costtype=9",
        },
        "紫黑玉": {
            "ten": "cmd=exchange&subtype=2&type=1236&times=10&costtype=9",
            "one": "cmd=exchange&subtype=2&type=1236&times=1&costtype=9",
        },
        "日曜石": {
            "ten": "cmd=exchange&subtype=2&type=1237&times=10&costtype=9",
            "one": "cmd=exchange&subtype=2&type=1237&times=1&costtype=9",
        },
        "月光石": {
            "ten": "cmd=exchange&subtype=2&type=1238&times=10&costtype=9",
            "one": "cmd=exchange&subtype=2&type=1238&times=1&costtype=9",
        },
    }

    PRICE = {
        "翡翠石": 32,
        "玛瑙石": 40,
        "迅捷石": 40,
        "紫黑玉": 40,
        "日曜石": 48,
        "月光石": 32,
    }

    STAR_GEM = {
        "日曜石": 1,
        "玛瑙石": 2,
        "迅捷石": 3,
        "月光石": 4,
        "翡翠石": 5,
        "紫黑玉": 6,
        "狂暴石": 7,
        "神愈石": 8,
    }

    SYNTHESIS_RULES = {
        1: 5,  # 5个1级星石合成一个2级星石
        2: 4,  # 4个2级星石合成一个3级星石
        3: 4,  # 4个3级星石合成一个4级星石
        4: 3,  # 3个4级星石合成一个5级星石
        5: 3,  # 3个5级星石合成一个6级星石
        6: 2,  # 2个6级星石合成一个7级星石
    }

    def __init__(self, d: DaLeDou, synth_level: int):
        self.synth_level = synth_level
        self.synth_count = {}
        super().__init__(d)

    def compute_exchange_level1_num(
        self, name: str, level: int, star_number: dict, count=1
    ) -> int:
        """返回一级某星石兑换数量"""
        self.synth_count[name][level] = count
        # 下一级
        level -= 1
        # 次级拥有数量
        possess_num = star_number[level]
        # 次级消耗数量
        consume_num = self.SYNTHESIS_RULES[level] * count

        if possess_num >= consume_num:
            return 0
        else:
            number = consume_num - possess_num
            if level == 1:
                # 一级星石兑换数量
                return number
            else:
                return self.compute_exchange_level1_num(
                    name, level, star_number, number
                )

    def get_synth_id(self, name: str) -> dict[int, str]:
        """返回2~7级星石合成id"""
        gem = self.STAR_GEM[name]
        self.d.get(f"cmd=astrolabe&op=showgemupgrade&gem_type={gem}")
        _ids = self.d.findall(r"gem=(\d+)")[1:]
        return {level: synth_id for level, synth_id in enumerate(_ids, start=2)}

    def get_store_max_number(self, name: str, store_points: int) -> int:
        """返回幻境商店星石最大兑换数量"""
        if price := self.PRICE.get(name):
            return store_points // price
        return 0

    def get_data(self) -> dict:
        """获取1~6级星石数量及2~7级星石合成id"""
        data = {}
        store_name = "幻境"
        store_points = get_store_points(self.d, "cmd=exchange&subtype=10&costtype=9")

        for name, gem in self.STAR_GEM.items():
            self.d.get(f"cmd=astrolabe&op=showgemupgrade&gem_type={gem}")
            result = self.d.findall(r"（(\d+)）")[1:]

            self.synth_count[name] = {level: 0 for level in range(2, self.synth_level)}
            # 1~6级星石数量
            star_number = {i + 1: int(item) for i, item in enumerate(result)}
            # 幻境商店可兑换数量
            store_exchange_num = self.get_store_max_number(name, store_points)
            # 一级星石兑换数量
            exchange_level1_num = self.compute_exchange_level1_num(
                name, self.synth_level, star_number
            )

            data[name] = {
                "名称": name,
                "1级数量": star_number[1],
                "2级数量": star_number[2],
                "3级数量": star_number[3],
                "4级数量": star_number[4],
                "5级数量": star_number[5],
                "6级数量": star_number[6],
                "积分": f"{store_points}（{store_exchange_num}）",
                "一级星石兑换数量": exchange_level1_num,
                "合成等级": self.synth_level,
                "是否强化": store_exchange_num >= exchange_level1_num,
                "consume_name": name,
                "consume_num": exchange_level1_num,
                "possess_num": 0,
                "store_name": store_name,
            }
        return data

    def upgrade(self, name: str):
        """星石合成"""
        if name in self.EXCHANGE_URL_MAP:
            e = super().exchange_instances(name, self.EXCHANGE_URL_MAP)
            if not e.is_exchange():
                return

        synth_id = self.get_synth_id(name)
        for level, count in self.synth_count[name].items():
            if count == 0:
                continue

            _id = synth_id[level]
            for _ in range(count):
                # 合成
                self.d.get(f"cmd=astrolabe&op=upgradegem&gem={_id}")
                self.d.log(self.d.find(r"规则</a><br />(.*?)<"), f"{level}级{name}")


def 星盘(d: DaLeDou):
    level_list = ["2", "3", "4", "5", "6", "7"]
    while True:
        synth_level = Input.select("请选择合成星石等级：", level_list)
        if synth_level is None:
            return
        upgrade(XingPan(d, int(synth_level)))


class YongBing(BaseUpgrader):
    def __init__(self, d: DaLeDou, category: str):
        self.category = category
        super().__init__(d)

    def 还童(self, name: str, _id: str):
        """佣兵还童或者高级还童为卓越资质"""
        while True:
            # 还童
            self.d.get(f"cmd=newmercenary&sub=6&id={_id}&type=1&confirm=1")
            self.d.log(self.d.find(), name)
            self.d.log(self.d.find(r"资质：(.*?)<"), "资质")
            if "卓越" in self.d.html:
                return
            if "你需要还童卷轴" in self.d.html:
                break
        while True:
            # 高级还童
            self.d.get(f"cmd=newmercenary&sub=6&id={_id}&type=2&confirm=1")
            self.d.log(self.d.find(), name)
            if "卓越" in self.d.html:
                return
            if "你需要还童天书" in self.d.html:
                break

    def 提升(self, name: str, _id: str):
        """佣兵悟性提升"""
        while True:
            # 提升
            self.d.get(f"cmd=newmercenary&sub=5&id={_id}")
            self.d.log(self.d.find(), name)
            self.d.log(self.d.find(r"悟性：(\d+)"), "悟性")
            if "升级悟性" not in self.d.html:
                break

    def 突飞(self, name: str, _id: str):
        """佣兵突飞十次"""
        while True:
            # 提升
            self.d.get(f"cmd=newmercenary&sub=4&id={_id}&count=10&tfl=1")
            self.d.log(self.d.find(), name)
            if "突飞成功" not in self.d.html:
                break

            self.d.log(self.d.find(r"等级：(\d+)"), "等级")
            self.d.log(self.d.find(r"经验：(.*?)<"), "经验")
            self.d.log(self.d.find(r"消耗阅历（(\d+)"), "阅历")

    def get_data(self) -> dict:
        """获取佣兵数据"""
        data = {}

        # 佣兵
        self.d.get("cmd=newmercenary")
        for _id in self.d.findall(r"sub=2&amp;id=(\d+)"):
            # 佣兵信息
            self.d.get(f"cmd=newmercenary&sub=2&id={_id}")

            # 名称
            name = self.d.find(r"<br /><br />(.+?)(?=<| )")
            # 战力
            combat_power = self.d.find(r"战力：(\d+)")
            # 资质
            aptitude = self.d.find(r"资质：(.*?)<")
            # 悟性
            savvy = self.d.find(r"悟性：(\d+)")
            # 等级
            level = self.d.find(r"等级：(\d+)")

            if self.category == "资质还童":
                # 卓越资质或者等级不为1时取消还童（还童会将等级重置为1）
                if aptitude == "卓越" or level != "1":
                    continue
            elif self.category == "阅历突飞":
                # 满级或者资质不是卓越时取消突飞
                if level == "20" or aptitude != "卓越":
                    continue
            elif self.category == "悟性提升" and savvy == "10":
                continue

            data[name] = {
                "名称": name,
                "id": _id,
                "战力": combat_power,
                "资质": aptitude,
                "悟性": savvy,
                "等级": level,
                "是否强化": True,
            }
        return data

    def upgrade(self, name: str):
        """执行佣兵任务"""
        _id: str = self.data[name]["id"]

        if self.category == "资质还童":
            self.还童(name, _id)
        elif self.category == "悟性提升":
            self.提升(name, _id)
        elif self.category == "阅历突飞":
            self.突飞(name, _id)


def 佣兵(d: DaLeDou):
    while True:
        category = Input.select("请选择分类：", ["资质还童", "悟性提升", "阅历突飞"])
        if category is None:
            return
        upgrade(YongBing(d, category))


class WuQiZhuanJing(BaseUpgrader):
    EXCHANGE_URL_MAP = {
        "投掷武器符文石": {
            "ten": "cmd=exchange&subtype=2&type=1208&times=10&costtype=4",
            "one": "cmd=exchange&subtype=2&type=1208&times=1&costtype=4",
        },
        "小型武器符文石": {
            "ten": "cmd=exchange&subtype=2&type=1211&times=10&costtype=4",
            "one": "cmd=exchange&subtype=2&type=1211&times=1&costtype=4",
        },
        "中型武器符文石": {
            "ten": "cmd=exchange&subtype=2&type=1210&times=10&costtype=4",
            "one": "cmd=exchange&subtype=2&type=1210&times=1&costtype=4",
        },
        "大型武器符文石": {
            "ten": "cmd=exchange&subtype=2&type=1213&times=10&costtype=4",
            "one": "cmd=exchange&subtype=2&type=1213&times=1&costtype=4",
        },
    }

    def __init__(self, d: DaLeDou):
        super().__init__(d)

    def get_fail_value(self, level: str) -> int:
        """返回专精失败祝福值"""
        get_blessing_event(self.d)
        if "专精" not in self.d.html:
            return 2

        if "五阶" in level:
            return int(self.d.find(r"专精.*?五阶5星.*?(\d+)"))
        return int(self.d.find(r"专精.*?四阶5星.*?(\d+)"))

    def get_data(self) -> dict:
        """获取专精数据"""
        data = {}
        store_name = "镖行天下"
        store_points = get_store_points(self.d, "cmd=exchange&subtype=10&costtype=4")
        store_exchange_num = store_points // 40

        for _id in range(4):
            self.d.get(f"cmd=weapon_specialize&op=0&type_id={_id}")
            if "9999" in self.d.html:
                continue

            stage = self.d.find(r"阶段：(.*?)<")
            star = self.d.find(r"星级：(.*?) ")
            consume_name, consume_num, possess_num = get_consume(self.d)
            now_value, total_value = get_blessing_value(self.d)
            name = consume_name[:4]
            fail_value = self.get_fail_value(stage)
            full_value_consume_num = compute(
                fail_value, consume_num, now_value, total_value
            )

            data[name] = {
                "名称": name,
                "id": _id,
                "阶段": stage,
                "星级": star,
                "消耗": f"{consume_name}*{consume_num}（{possess_num}）",
                "祝福值": f"{now_value}/{total_value}（↑{fail_value}）",
                "积分": f"{store_points}（{store_exchange_num}）",
                "满祝福消耗数量": f"{full_value_consume_num}（必成再+{consume_num}）",
                "是否强化": (possess_num + store_exchange_num)
                >= (full_value_consume_num + consume_num),
                "consume_name": consume_name,
                "consume_num": consume_num,
                "possess_num": possess_num,
                "store_name": store_name,
            }
        return data

    def upgrade(self, name: str):
        """武器专精升级"""
        _id: str = self.data[name]["id"]
        close_url = f"cmd=weapon_specialize&op=9&type_id={_id}&auto_buy=0"
        if not is_close_auto_buy(self.d, name, close_url):
            return

        e = super().exchange_instances(name, self.EXCHANGE_URL_MAP)
        while True:
            if not e.is_exchange():
                return

            # 升级
            self.d.get(f"cmd=weapon_specialize&op=2&type_id={_id}")
            self.d.log(self.d.find(), name)
            self.d.log(self.d.find(r"祝福值：(.*?) "), name)
            if "升星失败" not in self.d.html:
                break

            e.update_possess_num()


class WuQiLan(BaseUpgrader):
    EXCHANGE_URL_MAP = {
        "千年寒铁": {
            "ten": "cmd=exchange&subtype=2&type=1209&times=10&costtype=4",
            "one": "cmd=exchange&subtype=2&type=1209&times=1&costtype=4",
        }
    }

    def __init__(self, d: DaLeDou):
        super().__init__(d)

    def get_data(self) -> dict:
        """获取专精武器栏数据"""
        data = {}
        store_name = "镖行天下"
        store_points = get_store_points(self.d, "cmd=exchange&subtype=10&costtype=4")
        store_exchange_num = store_points // 40

        get_blessing_event(self.d)
        if "专精" in self.d.html:
            fail_value = int(self.d.find(r"武器栏失败获得(\d+)"))
        else:
            fail_value = 2

        for _id in range(1000, 1012):
            self.d.get(f"cmd=weapon_specialize&op=4&storage_id={_id}")
            if "当前等级：10" in self.d.html or "激活" in self.d.html:
                continue

            name = self.d.find(r"专精武器：(.*?) ")
            level = self.d.find(r"当前等级：(.*?)<")
            now_value, total_value = get_blessing_value(
                self.d,
            )
            consume_name, consume_num, possess_num = get_consume(self.d, "3659")
            full_value_consume_num = compute(
                fail_value, consume_num, now_value, total_value
            )

            data[name] = {
                "名称": name,
                "id": _id,
                "等级": level,
                "消耗": f"{consume_name}*{consume_num}（{possess_num}）",
                "祝福值": f"{now_value}/{total_value}（↑{fail_value}）",
                "积分": f"{store_points}（{store_exchange_num}）",
                "满祝福消耗数量": f"{full_value_consume_num}（必成再+{consume_num}）",
                "是否强化": (possess_num + store_exchange_num)
                >= (full_value_consume_num + consume_num),
                "consume_name": consume_name,
                "consume_num": consume_num,
                "possess_num": possess_num,
                "store_name": store_name,
            }
        return data

    def upgrade(self, name: str):
        """专精武器栏升级"""
        _id: str = self.data[name]["id"]
        close_url = f"cmd=weapon_specialize&op=10&storage_id={_id}&auto_buy=0"
        if not is_close_auto_buy(self.d, name, close_url):
            return

        e = super().exchange_instances(name, self.EXCHANGE_URL_MAP)
        while True:
            if not e.is_exchange():
                return

            # 升级
            self.d.get(f"cmd=weapon_specialize&op=5&storage_id={_id}")
            self.d.log(self.d.find(), name)
            self.d.log(self.d.find(r"祝福值：(.*?) "))
            if "升星失败" not in self.d.html:
                break

            e.update_possess_num()


def 专精(d: DaLeDou):
    while True:
        category = Input.select("请选择分类：", ["武器专精", "武器栏"])
        if category is None:
            return
        elif category == "武器专精":
            upgrade(WuQiZhuanJing(d))
        elif category == "武器栏":
            upgrade(WuQiLan(d))


class LingShouPian(BaseUpgrader):
    EXCHANGE_URL_MAP = {
        "神魔残卷": {
            "ten": "cmd=exchange&subtype=2&type=1267&times=10&costtype=14",
            "one": "cmd=exchange&subtype=2&type=1267&times=1&costtype=14",
        }
    }

    def __init__(self, d: DaLeDou):
        super().__init__(d)

    def get_data(self) -> dict:
        """获取灵兽篇数据"""
        get_blessing_event(self.d)
        if "神魔录" in self.d.html:
            fail_value = int(self.d.find(r"灵兽经五阶5星.*?获得(\d+)"))
        else:
            fail_value = 2

        data = {}
        store_name = "问鼎天下"
        store_points = get_store_points(self.d, "cmd=exchange&subtype=10&costtype=14")
        store_exchange_num = store_points // 40

        for _id in ["1", "2", "3", "4"]:
            self.d.get(f"cmd=ancient_gods&op=1&id={_id}")
            if "等级：五阶五级" in self.d.html:
                continue

            name = self.d.find(r"解锁.*?品质：(.*?)达到")
            level = self.d.find(r"等级：(.*?)&")
            consume_name, consume_num, possess_num = get_consume(self.d)
            now_value, total_value = get_blessing_value(self.d)
            full_value_consume_num = compute(
                fail_value, consume_num, now_value, total_value
            )

            data[name] = {
                "名称": name,
                "id": _id,
                "等级": level,
                "消耗": f"{consume_name}*{consume_num}（{possess_num}）",
                "祝福值": f"{now_value}/{total_value}（↑{fail_value}）",
                "积分": f"{store_points}（{store_exchange_num}）",
                "满祝福消耗数量": f"{full_value_consume_num}（必成再+{consume_num}）",
                "是否强化": (possess_num + store_exchange_num)
                >= (full_value_consume_num + consume_num),
                "consume_name": consume_name,
                "consume_num": consume_num,
                "possess_num": possess_num,
                "store_name": store_name,
            }
        return data

    def upgrade(self, name: str):
        """灵兽篇提升"""
        _id: str = self.data[name]["id"]
        close_url = f"cmd=ancient_gods&op=5&autoBuy=0&id={_id}"
        if not is_close_auto_buy(self.d, name, close_url):
            return

        e = super().exchange_instances(name, self.EXCHANGE_URL_MAP)
        while True:
            if not e.is_exchange():
                return

            # 提升一次
            self.d.get(f"cmd=ancient_gods&op=6&id={_id}&times=1")
            self.d.log(self.d.find(), name)
            self.d.log(self.d.find(r"祝福值：(.*?)<"), name)
            if "升级失败" not in self.d.html:
                break

            e.update_possess_num()


class GuZhenPian(BaseUpgrader):
    EXCHANGE_URL_MAP = {
        "突破石": {
            "ten": "cmd=exchange&subtype=2&type=1266&times=10&costtype=14",
            "one": "cmd=exchange&subtype=2&type=1266&times=1&costtype=14",
        }
    }

    # 背包碎片id
    S_ID = {
        "夔牛碎片": "5154",
        "饕餮碎片": "5155",
        "烛龙碎片": "5156",
        "黄鸟碎片": "5157",
    }

    def __init__(self, d: DaLeDou):
        super().__init__(d)

    def get_data(self) -> dict:
        """获取古阵篇数据"""
        data = {}
        store_name = "问鼎天下"
        store_points = get_store_points(self.d, "cmd=exchange&subtype=10&costtype=14")
        # 商店积分可兑换突破石数量
        t_store_exchange_num = store_points // 40
        t_consume_name = "突破石"
        # 突破石拥有数量
        t_possess_num = self.d.get_backpack_number("5153")

        for _id in ["1", "2", "3", "4"]:
            # 宝物详情
            self.d.get(f"cmd=ancient_gods&op=4&id={_id}")

            # 当前等级
            now_level = self.d.find(r"等级：(\d+)")
            # 最高等级
            highest_level = self.d.find(r"至(\d+)")
            if now_level == highest_level:
                continue

            name = self.d.find(r"<br /><br />(.*?)&")
            # 突破石消耗数量
            t_consume_num = int(self.d.find(r"突破石\*(\d+)"))
            # 碎片消耗名称
            s_consume_name = self.d.find(r"\+ (.*?)\*")
            # 碎片消耗数量
            s_consume_num = int(self.d.find(r"碎片\*(\d+)"))
            # 碎片拥有数量
            s_possess_num = self.d.get_backpack_number(self.S_ID[s_consume_name])

            data[name] = {
                "名称": name,
                "id": _id,
                "等级": now_level,
                "消耗": f"{t_consume_name}*{t_consume_num}（{t_possess_num}）+ {s_consume_name}*{s_consume_num}（{s_possess_num}）",
                "积分": f"{store_points}（{t_store_exchange_num}）",
                "是否强化": ((t_possess_num + t_store_exchange_num) >= t_consume_num)
                and (s_possess_num >= s_consume_num),
                "consume_name": t_consume_name,
                "consume_num": t_consume_num,
                "possess_num": t_possess_num,
                "store_name": store_name,
                "说明": "因碎片限兑，仅兑换突破石",
            }
        return data

    def upgrade(self, name: str):
        """古阵篇突破"""
        _id: str = self.data[name]["id"]
        e = super().exchange_instances(name, self.EXCHANGE_URL_MAP)
        if not e.is_exchange():
            return

        # 突破等级
        self.d.get(f"cmd=ancient_gods&op=7&id={_id}")
        self.d.log(self.d.find(), name)


def 神魔录(d: DaLeDou):
    while True:
        category = Input.select("请选择分类：", ["灵兽篇", "古阵篇"])
        if category is None:
            return
        elif category == "灵兽篇":
            upgrade(LingShouPian(d))
        elif category == "古阵篇":
            upgrade(GuZhenPian(d))


def jiang_hu_chang_meng(
    d: DaLeDou,
    name: str,
    ins_id: str,
    incense_burner_number: int,
    copy_duration: int,
    event,
):
    """运行江湖长梦副本的公共函数

    参数:
        d：DaLeDou实例
        name：副本名称
        ins_id：副本ID
        incense_burner_number：香炉数量
        copy_duration：副本时长
        event：处理每天事件的函数
    """
    for i in range(incense_burner_number):
        # 开启副本
        d.get(f"cmd=jianghudream&op=beginInstance&ins_id={ins_id}")
        if "帮助" in d.html:
            # 您还未编辑副本队伍，无法开启副本
            d.log(d.find(), name).append()
            return

        print_separator()
        count = i + 1
        print(f"第 {count} 次（余 {incense_burner_number - count}）")
        print_separator()

        for day in range(copy_duration + 1):
            if "进入下一天" in d.html:
                # 进入下一天
                d.get("cmd=jianghudream&op=goNextDay")
                day += 1
            else:
                d.log("请手动通关剩余天数后再使用脚本", f"{name}-第{day}天")
                return

            is_defeat = event(day)
            if is_defeat:
                break

        # 结束回忆
        d.get("cmd=jianghudream&op=endInstance")
        d.log(d.find(), name).append()

        if is_defeat:
            return

    # 领取首通奖励
    d.get(f"cmd=jianghudream&op=getFirstReward&ins_id={ins_id}")
    d.log(d.find(), name).append()


def 柒承的忙碌日常(
    d: DaLeDou, name: str, ins_id: str, incense_burner_number: int, copy_duration: int
):
    def event(day: int) -> bool:
        """战败返回True，否则返回False"""
        if _id := d.find(r'event_id=(\d+)">战斗'):
            # 战斗
            d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")
            # FIGHT!
            d.get("cmd=jianghudream&op=doPveFight")
            d.log(d.find(r"<p>(.*?)<br />"), f"{name}-第{day}天")
            if "战败" in d.html:
                return True
        elif _id := d.find(r'event_id=(\d+)">奇遇'):
            # 奇遇
            d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")
            d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")
            # 视而不见
            d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=2")
            d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")
        elif _id := d.find(r'event_id=(\d+)">商店'):
            # 商店
            d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")

        return False

    jiang_hu_chang_meng(d, name, ins_id, incense_burner_number, copy_duration, event)


def 群英拭剑谁为峰(
    d: DaLeDou, name: str, ins_id: str, incense_burner_number: int, copy_duration: int
):
    def event(day: int) -> bool:
        """战败返回True，否则返回False"""
        if _id := d.find(r'event_id=(\d+)">战斗\(等级2\)'):
            # 战斗
            d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")
            # FIGHT!
            d.get("cmd=jianghudream&op=doPveFight")
            d.log(d.find(r"<p>(.*?)<br />"), f"{name}-第{day}天")
            if "战败" in d.html:
                return True
        return False

    jiang_hu_chang_meng(d, name, ins_id, incense_burner_number, copy_duration, event)


def 时空守护者(
    d: DaLeDou, name: str, ins_id: str, incense_burner_number: int, copy_duration: int
):
    def event(day: int) -> bool:
        """战败返回True，否则返回False"""
        if _id := d.find(r'event_id=(\d+)">战斗\(等级2\)'):
            # 战斗
            d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")
            # FIGHT!
            d.get("cmd=jianghudream&op=doPveFight")
            d.log(d.find(r"<p>(.*?)<br />"), f"{name}-第{day}天")
            if "战败" in d.html:
                return True
        elif _ids := d.findall(r'event_id=(\d+)">战斗\(等级1\)'):
            if day == 2 or day == 4:
                _id = _ids[-1]
            else:
                _id = _ids[0]
            # 战斗
            d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")
            # FIGHT!
            d.get("cmd=jianghudream&op=doPveFight")
            d.log(d.find(r"<p>(.*?)<br />"), f"{name}-第{day}天")
            if "战败" in d.html:
                return True
        elif _ids := d.findall(r'event_id=(\d+)">奇遇\(等级2\)'):
            if day == 5:
                _id = _ids[-1]
            else:
                _id = _ids[0]
            # 奇遇
            d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")
            d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")
            if "上前询问" in d.html:
                # 上前询问
                d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=1")
                d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")
                # 一口答应
                d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=1")
            elif "解释身份" in d.html:
                # 解释身份
                d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=2")
                d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")
                # 题诗一首
                d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=1")
            elif "原地思考" in d.html:
                # 原地思考
                d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=2")
                d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")
                # 默默低语
                d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=3")
            elif "放她回去" in d.html:
                # 放她回去
                d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=1")
            d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")
        elif _id := d.find(r'event_id=(\d+)">奇遇\(等级1\)'):
            # 奇遇
            d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")
            d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")
            if "转一次" in d.html:
                # 转一次
                d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=3")
            elif "漩涡1" in d.html:
                # 漩涡1
                d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=1")
            d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")
        elif _id := d.find(r'event_id=(\d+)">商店'):
            # 商店
            d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")

        return False

    jiang_hu_chang_meng(d, name, ins_id, incense_burner_number, copy_duration, event)


def 倚天屠龙归我心(
    d: DaLeDou, name: str, ins_id: str, incense_burner_number: int, copy_duration: int
):
    def event(day: int) -> bool:
        """战败返回True，否则返回False"""
        if _id := d.find(r'event_id=(\d+)">战斗\(等级2\)'):
            # 战斗
            d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")
            # FIGHT!
            d.get("cmd=jianghudream&op=doPveFight")
            d.log(d.find(r"<p>(.*?)<br />"), f"{name}-第{day}天")
            if "战败" in d.html:
                return True
        elif _id := d.find(r'event_id=(\d+)">战斗\(等级1\)'):
            # 战斗
            d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")
            # FIGHT!
            d.get("cmd=jianghudream&op=doPveFight")
            d.log(d.find(r"<p>(.*?)<br />"), f"{name}-第{day}天")
            if "战败" in d.html:
                return True
        elif _id := d.find(r'event_id=(\d+)">奇遇\(等级2\)'):
            # 奇遇
            d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")
            d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")
            if day in [1, 3, 7]:
                # 前辈、开始回忆、狠心离去
                d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=1")
            elif day in [6, 8]:
                # 昏昏沉沉、独自神伤
                d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=3")
            d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")
        elif _id := d.find(r'event_id=(\d+)">商店'):
            # 商店
            d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")

        return False

    jiang_hu_chang_meng(d, name, ins_id, incense_burner_number, copy_duration, event)


def 神雕侠侣(
    d: DaLeDou, name: str, ins_id: str, incense_burner_number: int, copy_duration: int
):
    def event(day: int) -> bool:
        """战败返回True，否则返回False"""
        if _id := d.find(r'event_id=(\d+)">战斗\(等级2\)'):
            # 战斗
            d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")
            # FIGHT!
            d.get("cmd=jianghudream&op=doPveFight")
            d.log(d.find(r"<p>(.*?)<br />"), f"{name}-第{day}天")
            if "战败" in d.html:
                return True
        elif _id := d.find(r'event_id=(\d+)">奇遇\(等级2\)'):
            # 奇遇
            d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")
            d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")
            # 笼络侠客
            d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=3")
            d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")
        elif _id := d.find(r'event_id=(\d+)">商店'):
            # 商店
            d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")

        return False

    jiang_hu_chang_meng(d, name, ins_id, incense_burner_number, copy_duration, event)


def 雪山藏魂(
    d: DaLeDou, name: str, ins_id: str, incense_burner_number: int, copy_duration: int
):
    is_conversation = False

    def event(day: int) -> bool:
        """战败返回True，否则返回False"""
        nonlocal is_conversation

        if day == 4:
            if _id := d.find(r'event_id=(\d+)">奇遇\(等级2\)'):
                # 奇遇
                d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")
                d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")
                # 尝试交谈（获得银狐玩偶）
                d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=2")
                d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")
                is_conversation = True
                # 询问大侠
                d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=2")
                return False

        if _ids := d.findall(r'event_id=(\d+)">战斗\(等级2\)'):
            if day in [2, 5]:
                _id = _ids[-1]
            else:
                _id = _ids[0]
            # 战斗
            d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")
            # FIGHT!
            d.get("cmd=jianghudream&op=doPveFight")
            d.log(d.find(r"<p>(.*?)<br />"), f"{name}-第{day}天")
            if "战败" in d.html:
                return True
        elif _id := d.find(r'event_id=(\d+)">奇遇\(等级2\)'):
            # 奇遇
            d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")
            d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")
            if day == 1:
                # 捉迷藏
                d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=1")
            elif day == 6:
                if is_conversation:
                    # 飞书（需银狐玩偶）
                    d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=1")
                else:
                    # 刀剑归真
                    d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=2")
            d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")
        elif _id := d.find(r'event_id=(\d+)">商店'):
            # 商店
            d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")

        return False

    jiang_hu_chang_meng(d, name, ins_id, incense_burner_number, copy_duration, event)


def 桃花自古笑春风(
    d: DaLeDou, name: str, ins_id: str, incense_burner_number: int, copy_duration: int
):
    def event(day: int) -> bool:
        """战败返回True，否则返回False"""
        if _ids := d.findall(r'event_id=(\d+)">战斗\(等级2\)'):
            _id = _ids[-1]
            # 战斗
            d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")
            # FIGHT!
            d.get("cmd=jianghudream&op=doPveFight")
            d.log(d.find(r"<p>(.*?)<br />"), f"{name}-第{day}天")
            if "战败" in d.html:
                return True
        elif _id := d.find(r'event_id=(\d+)">奇遇\(等级2\)'):
            # 奇遇
            d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")
            d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")
            if day == 1:
                # 过去看看
                d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=2")
                d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")
                # 以西湖来对
                d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=2")
            elif day == 5:
                # 我的
                d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=2")
            elif day == 7:
                # 摸黑进入
                d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=2")
                d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")
                # 纯路人
                d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=2")
            d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")

        return False

    jiang_hu_chang_meng(d, name, ins_id, incense_burner_number, copy_duration, event)


def 战乱襄阳(
    d: DaLeDou, name: str, ins_id: str, incense_burner_number: int, copy_duration: int
):
    def event(day: int) -> bool:
        """战败返回True，否则返回False"""
        if _ids := d.findall(r'event_id=(\d+)">战斗\(等级2\)'):
            _id = _ids[-1]
            # 战斗
            d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")
            # FIGHT!
            d.get("cmd=jianghudream&op=doPveFight")
            d.log(d.find(r"<p>(.*?)<br />"), f"{name}-第{day}天")
            if "战败" in d.html:
                return True
        elif _id := d.find(r'event_id=(\d+)">奇遇\(等级2\)'):
            # 奇遇
            d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")
            d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")
            if day == 4:
                for _ in range(3):
                    # 向左突围 > 周遭探查 > 捣毁粮仓
                    d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=1")
                    d.log(
                        d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天"
                    )

        return False

    jiang_hu_chang_meng(d, name, ins_id, incense_burner_number, copy_duration, event)


def 天涯浪子(
    d: DaLeDou, name: str, ins_id: str, incense_burner_number: int, copy_duration: int
):
    def event(day: int) -> bool:
        """战败返回True，否则返回False"""
        if _ids := d.findall(r'event_id=(\d+)">战斗'):
            _id = _ids[-1]
            # 战斗
            d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")
            # FIGHT!
            d.get("cmd=jianghudream&op=doPveFight")
            d.log(d.find(r"<p>(.*?)<br />"), f"{name}-第{day}天")
            if "战败" in d.html:
                return True
        elif _id := d.find(r'event_id=(\d+)">奇遇'):
            # 奇遇
            d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")
            d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")
            if day == 1:
                # 问其身份
                d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=1")
                d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")
                # 锦囊2
                d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=2")
            elif day == 2:
                # 重金求见
                d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=2")
                d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")
                # 相约明日
                d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=2")
            elif day == 3:
                # 阁楼3
                d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=3")
            elif day == 4:
                # 结为姐弟
                d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=2")
            elif day == 5:
                # 筹备计划
                d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=2")
                d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")
                # 是
                d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=1")
            elif day == 6:
                # 锦囊1
                d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=1")
            d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")

        return False

    jiang_hu_chang_meng(d, name, ins_id, incense_burner_number, copy_duration, event)


def 全真古墓意难平(
    d: DaLeDou, name: str, ins_id: str, incense_burner_number: int, copy_duration: int
):
    def event(day: int) -> bool:
        """战败返回True，否则返回False"""
        if _id := d.find(r'event_id=(\d+)">战斗\(等级2\)'):
            # 战斗
            d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")
            # FIGHT!
            d.get("cmd=jianghudream&op=doPveFight")
            d.log(d.find(r"<p>(.*?)<br />"), f"{name}-第{day}天")
            if "战败" in d.html:
                return True
        elif _id := d.find(r'event_id=(\d+)">战斗\(等级1\)'):
            # 战斗
            d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")
            # FIGHT!
            d.get("cmd=jianghudream&op=doPveFight")
            d.log(d.find(r"<p>(.*?)<br />"), f"{name}-第{day}天")
            if "战败" in d.html:
                return True
        elif day == 1:
            # 奇遇1
            d.get("cmd=jianghudream&op=chooseEvent&event_id=1")
            d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")
            # 宅家乐斗
            d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=2")
            d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")
        elif day == 2:
            if _id := d.find(r'event_id=(\d+)">奇遇\(等级1\)'):
                # 奇遇1
                d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")
                d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")
                # 全真剑法
                d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=3")
            elif _id := d.find(r'event_id=(\d+)">奇遇\(等级2\)'):
                # 奇遇2
                d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")
                d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")
                # 同意约战
                d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=1")
            elif _id := d.find(r'event_id=(\d+)">商店'):
                # 商店
                d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")
            d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")
        elif day == 3:
            # 奇遇2
            d.get("cmd=jianghudream&op=chooseEvent&event_id=1")
            d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")
            # 环顾四周
            d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=1")
            d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")
        elif day == 5:
            if _id := d.find(r'event_id=(\d+)">奇遇\(等级1\)'):
                # 奇遇1
                d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")
                d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")
                # 暂且撤退
                d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=2")
            elif _id := d.find(r'event_id=(\d+)">奇遇\(等级2\)'):
                # 奇遇2
                d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")
                d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")
                # 切磋武功
                d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=1")
            elif _id := d.find(r'event_id=(\d+)">商店'):
                # 商店
                d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")
            d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")
        elif day == 6:
            if _id := d.find(r'event_id=(\d+)">奇遇\(等级1\)'):
                # 奇遇1
                d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")
                d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")
                # 暂且撤退
                d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=2")
            elif _id := d.find(r'event_id=(\d+)">商店'):
                # 商店
                d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")
            d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")
        elif day == 7:
            # 奇遇2
            d.get("cmd=jianghudream&op=chooseEvent&event_id=1")
            d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")
            # 坚持本心
            d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=2")
            d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")
            # 李莫愁
            d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=2")
            d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")

        return False

    jiang_hu_chang_meng(d, name, ins_id, incense_burner_number, copy_duration, event)


def get_open_copy_data(d: DaLeDou) -> dict:
    """获取开放副本数据"""
    from datetime import datetime, timedelta

    from ..core.utils import get_shanghai_now

    base_data = {
        "柒承的忙碌日常": {
            "material_name": "追忆香炉",
            "material_id": "6477",
            "ins_id": "1",
        },
        "群英拭剑谁为峰": {
            "material_name": "拭剑香炉",
            "material_id": "6940",
            "ins_id": "32",
        },
        "时空守护者": {
            "material_name": "时空香炉",
            "material_id": "6532",
            "ins_id": "47",
        },
        "倚天屠龙归我心": {
            "material_name": "九阳香炉",
            "material_id": "6904",
            "ins_id": "48",
        },
        "神雕侠侣": {
            "material_name": "盛世香炉",
            "material_id": "6476",
            "ins_id": "49",
        },
        "雪山藏魂": {
            "material_name": "雪山香炉",
            "material_id": "8121",
            "ins_id": "50",
        },
        "桃花自古笑春风": {
            "material_name": "桃花香炉",
            "material_id": "6825",
            "ins_id": "51",
        },
        "战乱襄阳": {
            "material_name": "忠义香炉",
            "material_id": "6888",
            "ins_id": "52",
        },
        "天涯浪子": {
            "material_name": "中秋香炉",
            "material_id": "6547",
            "ins_id": "53",
        },
        "全真古墓意难平": {
            "material_name": "全真香炉",
            "material_id": "6662",
            "ins_id": "54",
        },
    }

    copy_data = {}
    for k, v in base_data.items():
        material_name = v["material_name"]
        material_id = v["material_id"]
        ins_id = v["ins_id"]

        incense_burner_number = d.get_backpack_number(material_id)
        if incense_burner_number == 0:
            print(f"{k}（{material_name}不足）")
            continue

        d.get(f"cmd=jianghudream&op=showCopyInfo&id={ins_id}")
        copy_duration = int(d.find(r"副本时长：(\d+)"))
        if "常规副本" in d.html:
            copy_data[k] = v
            copy_data[k]["copy_duration"] = copy_duration
            copy_data[k]["incense_burner_number"] = incense_burner_number
            continue

        end_year = 2000 + int(d.find(r"-(\d+)年"))
        end_month = int(d.find(r"-\d+年(\d+)月"))
        end_day = int(d.find(r"-\d+年\d+月(\d+)日"))
        current_date = get_shanghai_now().date()
        end_date = datetime(end_year, end_month, end_day).date() - timedelta(days=1)
        if current_date <= end_date:
            copy_data[k] = v
            copy_data[k]["copy_duration"] = copy_duration
            copy_data[k]["incense_burner_number"] = incense_burner_number
        else:
            print(f"{k}（未开启）")

    if not len(copy_data):
        print_separator()
    else:
        print()

    return copy_data


def 江湖长梦(d: DaLeDou):
    while True:
        data = get_open_copy_data(d)
        category = Input.select("请选择分类：", list(data))
        if category is None:
            return

        material_name = data[category]["material_name"]
        ins_id = data[category]["ins_id"]
        incense_burner_number = data[category]["incense_burner_number"]
        copy_duration = data[category]["copy_duration"]
        print(f"{material_name}数量：{incense_burner_number}")

        globals()[category](d, category, ins_id, incense_burner_number, copy_duration)
        print_separator()


class SanHun(BaseUpgrader):
    EXCHANGE_URL_MAP = {
        "御魂丹-天": {
            "ten": "cmd=abysstide&op=abyssexchange&id=1&times=10",
            "one": "cmd=abysstide&op=abyssexchange&id=1&times=1",
        },
        "御魂丹-地": {
            "ten": "cmd=abysstide&op=abyssexchange&id=2&times=10",
            "one": "cmd=abysstide&op=abyssexchange&id=2&times=1",
        },
        "御魂丹-命": {
            "ten": "cmd=abysstide&op=abyssexchange&id=3&times=10",
            "one": "cmd=abysstide&op=abyssexchange&id=3&times=1",
        },
    }

    def __init__(self, d: DaLeDou):
        super().__init__(d)

    def get_data(self) -> dict:
        """获取三魂数据"""
        data = {}
        store_name = "深渊黑商"
        store_points = get_store_points(self.d, "cmd=abysstide&op=viewabyssshop")
        store_exchange_num = store_points // 90
        fail_value = 2

        for _id in ["1", "2", "3"]:
            self.d.get(f"cmd=abysstide&op=showsoul&soul_id={_id}")
            if "五阶五星" in self.d.html:
                continue

            name = self.d.find(r"丹-(.*?)\*") + "魂"
            stage = self.d.find(r"阶段：(.*?)<")
            consume_name, consume_num, possess_num = get_consume(self.d)
            now_value, total_value = get_blessing_value(self.d)
            full_value_consume_num = compute(
                fail_value, consume_num, now_value, total_value
            )

            data[name] = {
                "名称": name,
                "id": _id,
                "阶段": stage,
                "消耗": f"{consume_name}*{consume_num}（{possess_num}）",
                "进度": f"{now_value}/{total_value}（↑{fail_value}）",
                "积分": f"{store_points}（{store_exchange_num}）",
                "满进度消耗数量": full_value_consume_num,
                "是否强化": (possess_num + store_exchange_num)
                >= full_value_consume_num,
                "consume_name": consume_name,
                "consume_num": full_value_consume_num,  # 一次性兑换
                "possess_num": possess_num,
                "store_name": store_name,
            }
        return data

    def upgrade(self, name: str):
        """三魂进阶"""
        _id: str = self.data[name]["id"]
        close_url = f"cmd=abysstide&op=setauto&value=0&soul_id={_id}"
        if not is_close_auto_buy(self.d, name, close_url):
            return

        e = super().exchange_instances(name, self.EXCHANGE_URL_MAP)
        if not e.is_exchange():
            return

        now_value, total_value = self.data[name]["进度"].split("（")[0].split("/")
        quotient, remainder = divmod((int(total_value) - int(now_value)), 20)
        for _ in range(quotient):
            # 进阶十次
            self.d.get(f"cmd=abysstide&op=upgradesoul&soul_id={_id}&times=10")
            self.d.log(self.d.find(r"进度：(.*?)&"), name)
        for _ in range(remainder // 2):
            # 进阶
            self.d.get(f"cmd=abysstide&op=upgradesoul&soul_id={_id}&times=1")
            self.d.log(self.d.find(r"进度：(.*?)&"), name)


class QiPo(BaseUpgrader):
    EXCHANGE_URL_MAP = {
        "气魄之书": {
            "ten": "cmd=abysstide&op=wishexchange&id=5",
            "one": "cmd=abysstide&op=wishexchange&id=5",
        },
        "力魄之书": {
            "ten": "cmd=abysstide&op=wishexchange&id=6",
            "one": "cmd=abysstide&op=wishexchange&id=6",
        },
        "精魄之书": {
            "ten": "cmd=abysstide&op=wishexchange&id=7",
            "one": "cmd=abysstide&op=wishexchange&id=7",
        },
        "英魄之书": {
            "ten": "cmd=abysstide&op=wishexchange&id=8",
            "one": "cmd=abysstide&op=wishexchange&id=8",
        },
        "中枢之书": {
            "ten": "cmd=abysstide&op=wishexchange&id=9",
            "one": "cmd=abysstide&op=wishexchange&id=9",
        },
        "天冲之书": {
            "ten": "cmd=abysstide&op=wishexchange&id=10",
            "one": "cmd=abysstide&op=wishexchange&id=10",
        },
        "灵慧之书": {
            "ten": "cmd=abysstide&op=wishexchange&id=11",
            "one": "cmd=abysstide&op=wishexchange&id=11",
        },
    }

    def __init__(self, d: DaLeDou):
        super().__init__(d)

    def get_data(self) -> dict:
        """获取七魄数据"""
        data = {}
        store_name = "许愿帮铺"
        store_points = get_store_points(self.d, "cmd=abysstide&op=viewwishshop")
        store_exchange_num = store_points // 18
        fail_value = 2

        # 许愿帮铺
        self.d.get("cmd=abysstide&op=viewwishshop")
        store_exchange_data = {
            "气魄之书": min(
                store_exchange_num, 200 - int(self.d.find(r"气魄之书.*?(\d+)/"))
            ),
            "力魄之书": min(
                store_exchange_num, 200 - int(self.d.find(r"力魄之书.*?(\d+)/"))
            ),
            "精魄之书": min(
                store_exchange_num, 200 - int(self.d.find(r"精魄之书.*?(\d+)/"))
            ),
            "英魄之书": min(
                store_exchange_num, 200 - int(self.d.find(r"英魄之书.*?(\d+)/"))
            ),
            "中枢之书": min(
                store_exchange_num, 200 - int(self.d.find(r"中枢之书.*?(\d+)/"))
            ),
            "天冲之书": min(
                store_exchange_num, 200 - int(self.d.find(r"天冲之书.*?(\d+)/"))
            ),
            "灵慧之书": min(
                store_exchange_num, 200 - int(self.d.find(r"灵慧之书.*?(\d+)/"))
            ),
        }

        for _id in ["1", "2", "3", "4", "5", "6", "7"]:
            self.d.get(f"cmd=abysstide&op=showmortal&mortal_id={_id}")
            if "解锁" in self.d.html:
                continue

            level = self.d.find(r"当前等级：(\d+)")
            consume_name, consume_num, possess_num = get_consume(self.d)
            now_value, total_value = get_blessing_value(self.d)
            store_exchange_num = store_exchange_data[consume_name]
            full_value_consume_num = compute(
                fail_value, consume_num, now_value, total_value
            )
            name = consume_name[:2]

            data[name] = {
                "名称": name,
                "id": _id,
                "等级": level,
                "消耗": f"{consume_name}*{consume_num}（{possess_num}）",
                "祝福": f"{now_value}/{total_value}（↑{fail_value}）",
                "积分": f"{store_points}（{store_exchange_num}）",
                "满祝福消耗数量": f"{full_value_consume_num}（必成再+{consume_num}）",
                "是否强化": (possess_num + store_exchange_num)
                >= (full_value_consume_num + consume_num),
                "consume_name": consume_name,
                "consume_num": consume_num,
                "possess_num": possess_num,
                "store_name": store_name,
            }
        return data

    def upgrade(self, name: str):
        """七魄升级"""
        _id: str = self.data[name]["id"]
        e = super().exchange_instances(name, self.EXCHANGE_URL_MAP)
        while True:
            if not e.is_exchange():
                return

            # 升级
            self.d.get(f"cmd=abysstide&op=upgrademortal&mortal_id={_id}&times=1")
            self.d.log(self.d.find(), name)
            self.d.log(self.d.find(r"祝福值：(.*?)<"), name)
            if "升级失败祝福提升" not in self.d.html:
                break

            e.update_possess_num()


def 深渊之潮(d: DaLeDou):
    while True:
        category = Input.select("请选择分类：", ["三魂", "七魄"])
        if category is None:
            return
        elif category == "三魂":
            upgrade(SanHun(d))
        elif category == "七魄":
            upgrade(QiPo(d))


def 问道(d: DaLeDou):
    name = "问道"
    close_url = "cmd=immortals&op=setauto&type=0&status=0"
    if not is_close_auto_buy(d, name, close_url):
        return

    while True:
        # 问道10次
        d.get("cmd=immortals&op=asktao&times=10")
        d.log(d.find(r"帮助</a><br />(.*?)<"))
        if "问道石不足" in d.html:
            # 一键炼化多余制作书
            d.get("cmd=immortals&op=smeltall")
            d.log(d.find(r"帮助</a><br />(.*?)<"))
            break
    print_separator()


class XianWuXiuZhen(BaseUpgrader):
    def __init__(self, d: DaLeDou):
        super().__init__(d)

    def get_fail_value(self, consume_name: str, now_level: int) -> int:
        """返回史诗、传说、神话失败祝福值"""
        blessing_data = {
            "史诗残片": "史诗级法宝",
            "传说残片": "传说级法宝",
            "神话残片": "神话级法宝",
        }
        get_blessing_event(self.d)
        if "仙武修真" not in self.d.html:
            return 2

        level, fail_value = self.d.findall(
            rf"{blessing_data[consume_name]}(\d+)级.*?(\d+)点"
        )[0]
        if now_level <= int(level):
            return int(fail_value)
        return 2

    def get_data(self) -> dict:
        """获取仙武修真宝物数据"""
        data = {}
        max_level = {
            "史诗": 9,
            "传说": 12,
            "神话": 15,
        }

        # 宝物
        self.d.get("cmd=immortals&op=viewtreasure")
        for _id in self.d.findall(r'treasureid=(\d+)">强化'):
            # 强化
            self.d.get(f"cmd=immortals&op=viewupgradepage&treasureid={_id}")

            name = self.d.find(r'id">(.*?)&nbsp')
            level = int(self.d.find(r"\+(\d+)"))
            if level == max_level[name[:2]]:
                continue

            consume_name, consume_num, possess_num = get_consume(self.d)
            now_value, total_value = get_blessing_value(self.d)
            fail_value = self.get_fail_value(consume_name, level)
            full_value_consume_num = compute(
                fail_value, consume_num, now_value, total_value
            )

            data[name] = {
                "名称": name,
                "id": _id,
                "当前等级": level,
                "消耗": f"{consume_name}*{consume_num}（{possess_num}）",
                "祝福值": f"{now_value}/{total_value}（↑{fail_value}）",
                "满祝福消耗数量": f"{full_value_consume_num}（必成再+{consume_num}）",
                "是否强化": possess_num >= (full_value_consume_num + consume_num),
            }
        return data

    def upgrade(self, name: str):
        """法宝升级"""
        _id: str = self.data[name]["id"]
        close_url = f"cmd=immortals&op=setauto&type=1&status=0&treasureid={_id}"
        if not is_close_auto_buy(self.d, name, close_url):
            return

        while True:
            # 升级
            self.d.get(f"cmd=immortals&op=upgrade&treasureid={_id}&times=1")
            self.d.log(self.d.find(r'id">(.*?)<'), name)
            self.d.log(self.d.find(r"祝福值：(.*?)&"), name)
            if "升级失败" not in self.d.html:
                break
            print_separator()


def 仙武修真(d: DaLeDou):
    while True:
        category = Input.select("请选择分类：", ["问道", "宝物"])
        if category is None:
            return
        elif category == "问道":
            问道(d)
        elif category == "宝物":
            upgrade(XianWuXiuZhen(d))


class XinYuanYingShenQi(BaseUpgrader):
    CATRGORY_URL = {
        "投掷武器": "op=1&type=0",
        "小型武器": "op=1&type=1",
        "中型武器": "op=1&type=2",
        "大型武器": "op=1&type=3",
        "被动技能": "op=2&type=4",
        "伤害技能": "op=2&type=5",
        "特殊技能": "op=2&type=6",
    }

    CATRGORY_TYPE = {
        "投掷武器": "0",
        "小型武器": "1",
        "中型武器": "2",
        "大型武器": "3",
        "被动技能": "4",
        "伤害技能": "5",
        "特殊技能": "6",
    }

    def __init__(self, d: DaLeDou, category: str):
        self.category = category
        super().__init__(d)

    def get_data(self) -> dict:
        """获取神器数据"""

        data = {}
        consume_name = "真黄金卷轴"
        params = self.CATRGORY_URL[self.category]
        self.d.get(f"cmd=newAct&subtype=104&{params}")
        # 材料拥有数量
        possess_num = int(self.d.find(r"我的真黄金卷轴：(\d+)"))
        self.d.html = self.d.html.split("|")[-1]

        # 获取神器名称
        name_list = self.d.findall(r"([\u4e00-\u9fff]+)&nbsp;\d+星")
        # 获取神器星级
        level_list = self.d.findall(r"(\d+)星")
        # 获取神器id
        id_list = self.d.findall(r"item_id=(\d+).*?一键")
        # 材料消耗数量
        consume_num_list = self.d.findall(r":(\d+)")
        # 当前祝福值
        now_value_list = self.d.findall(r"(\d+)/")
        # 满祝福值
        total_value_list = self.d.findall(r"/(\d+)")

        # 过滤5星
        result = [(k, v) for k, v in zip(name_list, level_list) if v != "5"]
        for index, t in enumerate(result):
            name, star_level = t
            consume_num = int(consume_num_list[index])
            now_value = int(now_value_list[index])
            total_value = int(total_value_list[index])

            if star_level in ["0", "1", "2"]:
                fali_value = 0
                full_value_consume_num = consume_num
                consume_num = 0
            else:
                fali_value = 2
                full_value_consume_num = compute(
                    fali_value, consume_num, now_value, total_value
                )

            data[name] = {
                "名称": name,
                "id": id_list[index],
                "星级": star_level,
                "消耗": f"{consume_name}*{consume_num}（{possess_num}）",
                "祝福值": f"{now_value}/{total_value}（↑{fali_value}）",
                "满祝福消耗数量": f"{full_value_consume_num}（必成再+{consume_num}）",
                "是否强化": possess_num >= (full_value_consume_num + consume_num),
            }
        return data

    def upgrade(self, name: str):
        """升级神器"""
        _id: str = self.data[name]["id"]
        t = self.CATRGORY_TYPE[self.category]
        close_url = f"cmd=newAct&subtype=104&op=4&autoBuy=0&type={t}"
        if not is_close_auto_buy(self.d, name, close_url):
            return

        while True:
            # 升级一次
            self.d.get(
                f"cmd=newAct&subtype=104&op=3&one_click=0&item_id={_id}&type={t}"
            )
            self.d.log(self.d.find(), name)
            self.d.log(
                self.d.find(rf"{name}.*?:\d+ [\u4e00-\u9fff]+ (.*?)<br />"), name
            )
            if "恭喜您" in self.d.html:
                break
            print_separator()


def 新元婴神器(d: DaLeDou):
    category_list = [
        "投掷武器",
        "小型武器",
        "中型武器",
        "大型武器",
        "被动技能",
        "伤害技能",
        "特殊技能",
    ]

    while True:
        category = Input.select("请选择分类：", category_list)
        if category is None:
            return
        upgrade(XinYuanYingShenQi(d, category))


class 巅峰之战进行中:
    def __init__(self, d: DaLeDou):
        self.d = d

        while True:
            self.current_exploits = self.get_exploits()
            print(f"当前战功：{self.current_exploits}")
            print_separator()
            self.retain_exploits = Input.number("请输入要保留的战功：")
            if self.retain_exploits is None:
                break
            print_separator()
            if self.retain_exploits > self.current_exploits:
                continue
            self.pelted()
            print_separator()

    def get_exploits(self) -> int:
        """获取五行战功"""
        # 五行-合成
        self.d.get("cmd=element&subtype=4")
        return int(self.d.find(r"拥有:(\d+)"))

    def pelted(self):
        """太空探宝16倍场景投掷"""
        while self.retain_exploits < self.current_exploits:
            # 投掷
            self.d.get("cmd=element&subtype=7")
            if "【夺宝奇兵】" in self.d.html:
                self.d.log(self.d.find(r"<br /><br />(.*?)<br />"), "夺宝奇兵")
                self.d.log(self.d.find(r"进度：(.*?)<"), "夺宝奇兵")
                self.current_exploits = int(self.d.find(r"拥有:(\d+)"))
                if "您的战功不足" in self.d.html:
                    break
            elif "【选择场景】" in self.d.html:
                if "你掷出了" in self.d.html:
                    self.d.log(self.d.find(r"】<br />(.*?)<br />"), "夺宝奇兵")
                # 选择太空探宝
                self.d.get("cmd=element&subtype=15&gameType=3")
