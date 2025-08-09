"""
本模块为大乐斗其它任务，只能命令行手动运行

使用以下命令运行本模块任务：
    >>> python main.py --other
"""

import time
from datetime import datetime

from ..core.daledou import DaLeDou, print_separator, Input


def compute(fail_value, deplete_value, now_value, total_value) -> int:
    """
    返回技能强化至满祝福或者满进度时消耗的材料数量

    进度满了会升级成功；祝福满了不一定升级成功

    Args:
        fail_value: int类型，失败祝福值或者进度
        deplete_value: int类型，强化一次消耗材料数量
        now_value: int类型，当前祝福值或者当前进度
        total_value: int类型，总祝福值或者总进度
    """
    # 计算强化次数，向上取整
    number = -((now_value - total_value) // fail_value)
    # 计算总消耗材料数量
    total_deplete = number * deplete_value
    return total_deplete


def get_backpack_number(d: DaLeDou, item_id: str | int) -> int:
    """返回背包物品id数量"""
    # 背包物品详情
    d.get(f"cmd=owngoods&id={item_id}")
    if "很抱歉" in d.html:
        number = 0
    else:
        number = d.find(r"数量：(\d+)")
    return int(number)


def get_store_points(d: DaLeDou, params: str) -> int:
    """返回商店积分"""
    # 商店
    d.get(params)
    result = d.find(r"<br />(.*?)<")
    _, store_points = result.split("：")
    return int(store_points)


class Exchange:
    """积分商店兑换"""

    def __init__(self, d: DaLeDou, url: dict, consume_num: int, possess_num: int):
        self.d = d
        # 材料兑换10个链接
        self.exchange_ten_url = url["ten"]
        # 材料兑换一个链接
        self.exchange_one_url = url["one"]
        # 材料消耗数量
        self.consume_num = consume_num
        # 材料拥有数量
        self.possess_num = possess_num

    def exchange(self):
        """如果材料消耗数量大于材料拥有数量则兑换两者差值数量的材料"""
        print_separator()
        if self.possess_num >= self.consume_num:
            return

        exchange_num = self.consume_num - self.possess_num
        ten_count, one_count = divmod(exchange_num, 10)
        if not self.exchange_count(self.exchange_ten_url, ten_count):
            return
        if not self.exchange_count(self.exchange_one_url, one_count):
            return

        # 兑换成功则两者数量一致
        self.possess_num = self.consume_num
        print_separator()

    def exchange_count(self, url: str, count: int) -> bool:
        """兑换足够数量返回True，否则返回False"""
        while count > 0:
            self.d.get(url)
            self.d.log(self.d.find())
            if "成功" in self.d.html:
                count -= 1
            elif "不足" in self.d.html:
                return False
        return True

    def update_possess_num(self):
        """更新材料拥有数量"""
        if self.possess_num >= self.consume_num:
            self.possess_num -= self.consume_num


def split_consume_data(d: DaLeDou, consume: str) -> tuple:
    """返回材料消耗名称、材料消耗数量、材料拥有数量"""
    result = d.findall(r"^(.*?)\*(\d+)（(\d+)）", consume)
    name, consume_num, possess_num = result[0]
    return name, int(consume_num), int(possess_num)


def upgrade(obj) -> bool:
    """将用户选择的技能升级，若没有符合的选项返回False，否则返回True"""
    while True:
        upgrade_names = []
        for _, _dict in obj.data.items():
            print_separator()
            if _dict["是否升级"]:
                upgrade_names.append(_dict["名称"])
            for k, v in _dict.items():
                print(f"{k}：{v}")

        while True:
            print_separator()
            name = Input.select("请选择强化任务：", upgrade_names)
            print_separator()
            if name is None:
                return False
            obj.upgrade(name)
            print_separator()
            return True


# ============================================================


class AoYi:
    """奥义自动兑换强化"""

    def __init__(self, d: DaLeDou):
        self.d = d
        # 帮派祭坛商店积分
        self.points = get_store_points(self.d, "cmd=exchange&subtype=10&costtype=12")

        self.fail_value = self.get_fail_value()
        self.data = self.get_data()

    def get_fail_value(self) -> int:
        """返回奥义失败祝福值"""
        # 祝福合集宝库
        self.d.get("cmd=newAct&subtype=143")
        if "=技能奥义=" not in self.d.html:
            return 2
        return int(self.d.find(r"奥义五阶5星.*?获得(\d+)"))

    def get_data(self) -> dict:
        """获取奥义数据"""
        data = {}
        name = "奥义"

        # 奥义
        self.d.get("cmd=skillEnhance&op=0")
        if "五阶&nbsp;5星" in self.d.html:
            return {}

        # 阶段
        level = self.d.find(r"阶段：(.*?)<").replace("&nbsp;", "")
        # 材料消耗数量
        consume_num = int(self.d.find(r"\*(\d+)"))
        # 材料拥有数量
        possess_num = int(self.d.find(r"（(\d+)）"))
        # 当前祝福值
        now_value = int(self.d.find(r"(\d+)/"))
        # 总祝福值
        total_value = int(self.d.find(r"\d+/(\d+)"))

        # 商店积分可兑换数量
        store_num = self.points // 40
        # 满祝福消耗数量
        full_value_consume_num = compute(
            self.fail_value, consume_num, now_value, total_value
        )

        data[name] = {
            "名称": name,
            "阶段": level,
            "消耗": f"奥秘元素*{consume_num}（{possess_num}）",
            "祝福值": f"{now_value}/{total_value}（↑{self.fail_value}）",
            "积分": f"{self.points}（{store_num}）",
            "满祝福消耗数量": f"{full_value_consume_num}（必成再+{consume_num}）",
            "是否升级": (possess_num + store_num)
            >= (full_value_consume_num + consume_num),
        }
        return data

    def upgrade(self, name):
        """奥义升级"""
        url = {
            "奥秘元素": {
                "ten": "cmd=exchange&subtype=2&type=1261&times=10&costtype=12",
                "one": "cmd=exchange&subtype=2&type=1261&times=1&costtype=12",
            }
        }

        data = self.data[name]

        consume_name, consume_num, possess_num = split_consume_data(
            self.d, data["消耗"]
        )
        e = Exchange(self.d, url[consume_name], consume_num, possess_num)

        # 关闭自动斗豆兑换
        self.d.get("cmd=skillEnhance&op=9&autoBuy=0")
        self.d.log("关闭自动斗豆兑换", name)

        while True:
            # 积分商店兑换材料
            e.exchange()

            # 升级
            self.d.get("cmd=skillEnhance&op=2")
            self.d.log(self.d.find(), name)
            self.d.log(self.d.find(r"祝福值：(.*?) "), name)
            if "升星失败" not in self.d.html:
                break

            # 更新材料拥有数量
            e.update_possess_num()


class JiNengLan:
    """奥义技能栏自动兑换强化"""

    def __init__(self, d: DaLeDou):
        self.d = d
        # 帮派祭坛商店积分
        self.points = get_store_points(self.d, "cmd=exchange&subtype=10&costtype=12")

        self.fail_value = self.get_fail_value()
        self.data = self.get_data()

    def get_fail_value(self) -> int:
        """返回奥义技能栏失败祝福值"""
        # 祝福合集宝库
        self.d.get("cmd=newAct&subtype=143")
        if "=技能奥义=" not in self.d.html:
            return 2
        return int(self.d.find(r"技能栏7星.*?失败(\d+)"))

    def get_data(self) -> dict:
        """获取奥义技能栏数据"""
        data = {}

        # 技能栏
        self.d.get("cmd=skillEnhance&op=0&view=storage")
        for _id in self.d.findall(r'storage_id=(\d+)">查看详情'):
            # 查看详情
            self.d.get(f"cmd=skillEnhance&op=4&storage_id={_id}")

            # 奥义名称
            name = self.d.find(r"<br />=(.*?)=")
            # 当前等级
            level = int(self.d.find(r"当前等级：(\d+)"))
            # 材料消耗数量
            consume_num = int(self.d.find(r"\*(\d+)"))
            # 材料拥有数量
            possess_num = int(self.d.find(r"（(\d+)）"))
            # 当前祝福值
            now_value = int(self.d.find(r"祝福值：(\d+)"))
            # 总祝福值
            total_value = int(self.d.find(r"祝福值：\d+/(\d+)"))

            if level <= 7:
                # 7级（含）前失败祝福值
                fail_value = self.fail_value
            else:
                # 7级后失败祝福值
                fail_value = 2

            # 商店积分可兑换数量
            store_num = self.points // 40
            # 满祝福消耗数量
            full_value_consume_num = compute(
                fail_value, consume_num, now_value, total_value
            )

            data[name] = {
                "名称": name,
                "id": _id,
                "当前等级": level,
                "消耗": f"四灵魂石*{consume_num}（{possess_num}）",
                "祝福值": f"{now_value}/{total_value}（↑{fail_value}）",
                "积分": f"{self.points}（{store_num}）",
                "满祝福消耗数量": f"{full_value_consume_num}（必成再+{consume_num}）",
                "是否升级": (possess_num + store_num) >= consume_num,
                "说明": "祝福值永久有效，可以随时升级",
            }
        return data

    def upgrade(self, name: str):
        """奥义技能栏升级"""
        url = {
            "四灵魂石": {
                "ten": "cmd=exchange&subtype=2&type=1262&times=10&costtype=12",
                "one": "cmd=exchange&subtype=2&type=1262&times=1&costtype=12",
            }
        }

        data = self.data[name]
        _id: str = data["id"]

        consume_name, consume_num, possess_num = split_consume_data(
            self.d, data["消耗"]
        )
        e = Exchange(self.d, url[consume_name], consume_num, possess_num)

        # 关闭自动斗豆兑换
        self.d.get(f"cmd=skillEnhance&op=10&storage_id={_id}&auto_buy=0")
        self.d.log("关闭自动斗豆兑换", name)

        while True:
            # 积分商店兑换材料
            e.exchange()

            # 升级
            self.d.get(f"cmd=skillEnhance&op=5&storage_id={_id}")
            self.d.log(self.d.find(), name)
            self.d.log(self.d.find(r"祝福值：(.*?) "), name)
            if "升星失败" not in self.d.html:
                break

            # 更新材料拥有数量
            e.update_possess_num()


def 奥义(d: DaLeDou):
    """奥义、技能栏自动兑换强化"""
    while True:
        category = Input.select("请选择分类：", ["奥义", "技能栏"])
        if category is None:
            return
        elif category == "奥义":
            upgrade(AoYi(d))
        elif category == "技能栏":
            upgrade(JiNengLan(d))


class 背包:
    """背包搜索工具"""

    def __init__(self, d: DaLeDou):
        self.d = d
        self.search(self.get_data())

    def get_data(self) -> list[dict]:
        """获取背包数据"""
        data = []
        self.d.get("cmd=store")
        page = int(self.d.find(r"第1/(\d+)"))
        for p in range(1, (page + 1)):
            self.d.get(f"cmd=store&store_type=0&page={p}")
            _, _html = self.d.html.split("清理")
            self.d.html, _ = _html.split("商店")
            for _id, name, number in self.d.findall(r'id=(\d+)">(.*?)</a>数量：(\d+)'):
                data.append(
                    {
                        "id": _id,
                        "name": name,
                        "number": number,
                    }
                )
        return data

    def search_backpack(self, query, items):
        """执行背包搜索"""
        results = []
        for item in items:
            if item["id"] == query or query.lower() in item["name"].lower():
                results.append(item)
        return results

    def search(self, data: list):
        while True:
            print_separator()
            text = Input.text("请输入物品ID或名称:")
            if text is None:
                break

            search_term = text.strip()
            if results := self.search_backpack(search_term, data):
                print(f"\n{'ID':<5}{'物品名称':<10}{'数量':<8}")
                print_separator()
                for item in results:
                    print(f"{item['id']:<5}{item['name']:<10}{item['number']:<8}")
                print()
            else:
                print("\n⚠️ 未找到匹配物品")


class 掠夺:
    """自动掠夺"""

    def __init__(self, d: DaLeDou):
        self.d = d
        self.max_combat_power = Input.number("请输入掠夺最大战力：")

        for _id in self.get_id():
            while True:
                print_separator()
                if not self.is_plunder(_id):
                    break
                if not self.plunder(_id):
                    return
                time.sleep(1)

    def get_id(self) -> list:
        """获取所有可掠夺的粮仓id"""
        self.d.get("cmd=forage_war&subtype=3")
        return self.d.findall(r'gra_id=(\d+)">掠夺')

    def is_plunder(self, gra_id: str) -> bool:
        """判断某粮仓第一个成员是否掠夺"""
        self.d.get(f"cmd=forage_war&subtype=3&op=1&gra_id={gra_id}")
        combat_power = self.d.find(r"<br />1.*? (\d+)\.")
        self.d.log(combat_power, f"{gra_id}战力")
        if combat_power:
            if int(combat_power) < self.max_combat_power:
                return True
        return False

    def plunder(self, gra_id: str) -> bool:
        """掠夺某粮仓第一个成员"""
        self.d.get(f"cmd=forage_war&subtype=4&gra_id={gra_id}")
        self.d.log(self.d.find("返回</a><br />(.*?)<"), "掠夺")
        self.d.log(self.d.find("生命：(.*?)<"), "生命")
        if "你已经没有足够的复活次数" in self.d.html:
            return False
        return True


class ShenZhuang:
    """神装自动兑换强化"""

    def __init__(self, d: DaLeDou):
        self.d = d
        self.fail_value = self.get_fail_value()
        self.data = self.get_data()

    def get_fail_value(self) -> int:
        """返回神装失败祝福值"""
        # 祝福合集宝库
        self.d.get("cmd=newAct&subtype=143")
        if "=神装=" not in self.d.html:
            return 2
        return 2 * int(self.d.find(r"神装进阶失败获得(\d+)"))

    def get_match_data(self, name, _id, backpack_id, store_url) -> dict | None:
        """获取神装匹配数据"""
        # 神装
        self.d.get(f"cmd=outfit&op=0&magic_outfit_id={_id}")
        if ("10阶" in self.d.html) or ("必成" in self.d.html):
            return

        # 阶层
        level = self.d.find(r"阶层：(.*?)<")
        # 材料消耗名称
        consume_name = self.d.find(r"进阶消耗：(.*?)\*")
        # 材料消耗数量
        consume_num = int(self.d.find(r"\*(\d+)"))
        # 材料拥有数量
        possess_num = int(self.d.find(r"剩余数量.*?(\d+)"))
        # 当前祝福值
        now_value = int(self.d.find(r"祝福值：(\d+)"))
        # 满祝福值
        total_value = int(self.d.find(r"祝福值：\d+/(\d+)"))

        # 满祝福消耗数量
        full_value_consume_num = compute(
            self.fail_value, consume_num, now_value, total_value
        )
        # 商店积分
        store_points = get_store_points(self.d, store_url)
        # 商店积分可兑换数量
        store_num = store_points // 40

        return {
            "名称": name,
            "id": _id,
            "阶层": level,
            "消耗": f"{consume_name}*{consume_num}（{possess_num}）",
            "祝福值": f"{now_value}/{total_value}（↑{self.fail_value}）",
            "积分": f"{store_points}（{store_num}）",
            "满祝福消耗数量": f"{full_value_consume_num}（必成再+{consume_num}）",
            "是否升级": (possess_num + store_num) >= consume_num,
            "说明": "祝福值永久有效，可以随时升级",
        }

    def get_data(self) -> dict:
        """获取神装数据，不包含满阶和必成数据"""
        data_dict = {
            "神兵": {
                "id": "0",
                "backpack_id": 3573,
                "store_url": "cmd=arena&op=queryexchange",
            },
            "神铠": {
                "id": "1",
                "backpack_id": 3574,
                "store_url": "cmd=arena&op=queryexchange",
            },
            "神羽": {
                "id": "2",
                "backpack_id": 3575,
                "store_url": "cmd=exchange&subtype=10&costtype=1",
            },
            "神兽": {
                "id": "3",
                "backpack_id": 3576,
                "store_url": "cmd=exchange&subtype=10&costtype=2",
            },
            "神饰": {
                "id": "4",
                "backpack_id": 3631,
                "store_url": "cmd=exchange&subtype=10&costtype=2",
            },
            "神履": {
                "id": "5",
                "backpack_id": 3636,
                "store_url": "cmd=exchange&subtype=10&costtype=3",
            },
        }
        data = {}

        for name, _dict in data_dict.items():
            _id = _dict["id"]
            backpack_id = _dict["backpack_id"]
            store_url = _dict["store_url"]
            result = self.get_match_data(name, _id, backpack_id, store_url)
            if result:
                data[name] = result
        return data

    def upgrade(self, name: str):
        """神装进阶"""
        url = {
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

        data = self.data[name]
        _id: str = data["id"]

        consume_name, consume_num, possess_num = split_consume_data(
            self.d, data["消耗"]
        )
        e = Exchange(self.d, url[consume_name], consume_num, possess_num)

        # 关闭自动斗豆兑换神装进阶材料
        self.d.get(f"cmd=outfit&op=4&auto_buy=2&magic_outfit_id={_id}")
        self.d.log(self.d.find(r"\|<br />(.*?)<br />"), name)

        while True:
            # 积分商店兑换材料
            e.exchange()

            # 进阶
            self.d.get(f"cmd=outfit&op=1&magic_outfit_id={_id}")
            self.d.log(self.d.find(r"神履.*?<br />(.*?)<br />"), name)
            self.d.log(self.d.find(r"祝福值：(.*?)<"), name)
            if "进阶失败" not in self.d.html:
                break

            # 更新材料拥有数量
            e.update_possess_num()


class ShenJi:
    """神技自动兑换强化"""

    def __init__(self, d: DaLeDou, store_name: str):
        self.d = d
        store = {
            "矿洞": get_store_points(self.d, "cmd=exchange&subtype=10&costtype=3"),
            "掠夺": get_store_points(self.d, "cmd=exchange&subtype=10&costtype=2"),
            "踢馆": get_store_points(self.d, "cmd=exchange&subtype=10&costtype=1"),
            "竞技场": get_store_points(self.d, "cmd=arena&op=queryexchange"),
        }
        # 积分商店名称
        self.store_name = store_name
        self.points = store[store_name]

        self.data = self.get_data()

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
        # 神秘精华拥有数量
        possess_num = get_backpack_number(self.d, 3567)
        # 积分商店可兑换数量
        store_num = self.points // 40

        for _id in self.get_data_id():
            self.d.get(f"cmd=outfit&op=2&magic_skill_id={_id}")
            # 神技名称
            name = self.d.find(r"<br />=(.*?)=<a")
            # 当前等级
            level = self.d.find(r"当前等级：(\d+)")
            # 升级消耗数量
            consume_num = int(self.d.find(r"\*(\d+)<"))
            # 升级成功率
            success = self.d.find(r"升级成功率：(.*?)<")
            # 当前效果
            effect = self.d.find(r"当前效果：(.*?)<")

            is_upgrade = True if store_num >= consume_num else False

            data[name] = {
                "名称": name,
                "id": _id,
                "当前等级": level,
                "消耗": f"神秘精华*{consume_num}（{possess_num}）",
                "升级成功率": success,
                "当前效果": effect,
                f"{self.store_name}积分": f"{self.points}（{store_num}）",
                "是否升级": is_upgrade,
            }
        return data

    def upgrade(self, name: str):
        """神技升级"""
        url = {
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

        data = self.data[name]
        _id: str = data["id"]

        _, consume_num, possess_num = split_consume_data(self.d, data["消耗"])
        e = Exchange(self.d, url[self.store_name], consume_num, possess_num)

        # 关闭自动斗豆兑换神技升级材料
        self.d.get(f"cmd=outfit&op=8&auto_buy=2&magic_outfit_id={_id}")
        self.d.log(self.d.find(r"\|<br />(.*?)<br />"), name)

        while True:
            # 积分商店兑换材料
            e.exchange()

            # 升级
            self.d.get(f"cmd=outfit&op=3&magic_skill_id={_id}")
            self.d.log(self.d.find(r"套装强化</a><br />(.*?)<br />"), name)
            if "升级失败" not in self.d.html:
                break

            # 更新材料拥有数量
            e.update_possess_num()


def 神装(d: DaLeDou):
    """神装自动兑换强化：神装进阶和神技升级"""
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
            upgrade(ShenJi(d, store_name.split("：")[0]))


class XingPan:
    """星石自动兑换合成"""

    def __init__(self, d: DaLeDou, level: int):
        self.d = d
        # 合成等级
        self.level = level
        # 各级合成次数
        self.count = {}
        # 各级转换关系
        self.level_ties = {
            1: 5,  # 5个1级星石合成一个2级星石
            2: 4,  # 4个2级星石合成一个3级星石
            3: 4,  # 4个3级星石合成一个4级星石
            4: 3,  # 3个4级星石合成一个5级星石
            5: 3,  # 3个5级星石合成一个6级星石
            6: 2,  # 2个6级星石合成一个7级星石
        }
        self.star_gem = {
            "日曜石": 1,
            "玛瑙石": 2,
            "迅捷石": 3,
            "月光石": 4,
            "翡翠石": 5,
            "紫黑玉": 6,
            "狂暴石": 7,
            "神愈石": 8,
        }

        # 幻境商店积分
        self.points = get_store_points(self.d, "cmd=exchange&subtype=10&costtype=9")

        self.data_id = self.get_star_id()
        self.data = self.get_data()

    def get_star_id(self) -> dict:
        """返回2~7级星石合成id"""
        data = {}
        for name, gem in self.star_gem.items():
            self.d.get(f"cmd=astrolabe&op=showgemupgrade&gem_type={gem}")
            result = self.d.findall(r"gem=(\d+)")[1:]

            # 2~7级星石合成id
            star_id = {i + 2: item for i, item in enumerate(result)}
            data[name] = {
                "id": star_id,
            }
        return data

    def get_data(self) -> dict:
        """获取1~6级星石数量及2~7级星石合成id"""
        data = {}
        for name, gem in self.star_gem.items():
            self.d.get(f"cmd=astrolabe&op=showgemupgrade&gem_type={gem}")
            result = self.d.findall(r"（(\d+)）")[1:]

            # 1~6级星石数量
            star_number = {i + 1: int(item) for i, item in enumerate(result)}
            # 幻境商店可兑换数量
            store_num = self.get_store_max_number(name)
            self.count[name] = {}
            # 一级星石兑换数量
            exchange_number = self.compute(name, self.level, star_number)

            data[name] = {
                "名称": name,
                "1级数量": star_number[1],
                "2级数量": star_number[2],
                "3级数量": star_number[3],
                "4级数量": star_number[4],
                "5级数量": star_number[5],
                "6级数量": star_number[6],
                "积分": f"{self.points}（{store_num}）",
                "一级星石兑换数量": exchange_number,
                "合成等级": self.level,
                "是否升级": store_num >= exchange_number,
            }
        return data

    def get_store_max_number(self, name: str) -> int:
        """返回幻境商店星石最大兑换数量"""
        data = {
            "翡翠石": 32,
            "玛瑙石": 40,
            "迅捷石": 40,
            "紫黑玉": 40,
            "日曜石": 48,
            "月光石": 32,
        }
        if price := data.get(name):
            return self.points // price
        return 0

    def compute(self, name: str, level: int, star_number: dict, count=1) -> int:
        """返回一级某星石兑换数量"""
        self.count[name][level] = count
        # 下一级
        level -= 1
        # 次级拥有数量
        possess_num = star_number[level]
        # 次级消耗数量
        consume_num = self.level_ties[level] * count

        if possess_num >= consume_num:
            return 0
        else:
            number = consume_num - possess_num
            if level == 1:
                # 一级星石兑换数量
                return number
            else:
                return self.compute(name, level, star_number, number)

    def upgrade(self, name: str):
        """星石合成"""
        url = {
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

        if name in url:
            exchange_num = self.data[name]["一级星石兑换数量"]
            Exchange(self.d, url[name], exchange_num, 0).exchange()

        id_dict = self.data_id[name]["id"]
        data = dict(sorted(self.count[name].items()))
        for level, count in data.items():
            _id = id_dict[level]
            for _ in range(count):
                # 合成
                self.d.get(f"cmd=astrolabe&op=upgradegem&gem={_id}")
                self.d.log(self.d.find(r"规则</a><br />(.*?)<"), f"{level}级{name}")


def 星盘(d: DaLeDou):
    """星石自动兑换合成"""
    level_list = ["2", "3", "4", "5", "6", "7"]
    while True:
        upgrade_level = Input.select("请选择合成星石等级：", level_list)
        if upgrade_level is None:
            return
        upgrade(XingPan(d, int(upgrade_level)))


class YongBing:
    """佣兵自动资质还童、悟性提升、阅历突飞"""

    def __init__(self, d: DaLeDou, category: str):
        self.d = d
        self.category = category

        self.data = self.get_data()

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
                "是否升级": True,
            }
        return data

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
            self.d.log(self.d.find(r"等级：(\d+)"), "等级")
            self.d.log(self.d.find(r"经验：(.*?)<"), "经验")
            self.d.log(self.d.find(r"消耗阅历（(\d+)"), "阅历")
            if "突飞成功" not in self.d.html:
                break

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
    """佣兵自动资质还童、悟性提升、阅历突飞"""
    while True:
        category = Input.select("请选择分类：", ["资质还童", "悟性提升", "阅历突飞"])
        if category is None:
            return
        upgrade(YongBing(d, category))


class ZhuanJing:
    """专精自动兑换强化"""

    def __init__(self, d: DaLeDou):
        self.d = d
        # 镖行天下商店积分
        self.points = get_store_points(self.d, "cmd=exchange&subtype=10&costtype=4")

        self.data = self.get_data()

    def get_fail_value(self, level: str) -> int:
        """返回专精失败祝福值"""
        # 祝福合集宝库
        self.d.get("cmd=newAct&subtype=143")
        if "=专精=" not in self.d.html:
            return 2
        if "五阶" in level:
            return int(self.d.find(r"专精.*?五阶5星.*?(\d+)"))
        return int(self.d.find(r"专精.*?四阶5星.*?(\d+)"))

    def get_data(self) -> dict:
        """获取专精数据"""
        data = {}
        for _id in range(4):
            self.d.get(f"cmd=weapon_specialize&op=0&type_id={_id}")
            if "9999" in self.d.html:
                continue

            # 阶段
            level = self.d.find(r"阶段：(.*?)<")
            # 星级
            star = self.d.find(r"星级：(.*?) ")
            # 材料消耗名称
            consume_name = self.d.find(r"消耗：(.*?)\*")
            # 材料消耗数量
            consume_num = int(self.d.find(r"消耗：.*?(\d+)"))
            # 材料拥有数量
            possess_num = int(self.d.find(r"剩余数量.*?(\d+)"))
            # 当前祝福值
            now_value = int(self.d.find(r"祝福值：(\d+)"))
            # 总祝福值
            total_value = int(self.d.find(r"祝福值：\d+/(\d+)"))

            name = consume_name[:4]
            fail_value = self.get_fail_value(level)
            # 商店积分可兑换数量
            store_num = self.points // 40
            # 满祝福消耗数量
            full_value_consume_num = compute(
                fail_value, consume_num, now_value, total_value
            )

            data[name] = {
                "名称": name,
                "id": _id,
                "阶段": level,
                "星级": star,
                "消耗": f"{consume_name}*{consume_num}（{possess_num}）",
                "祝福值": f"{now_value}/{total_value}（↑{fail_value}）",
                "积分": f"{self.points}（{store_num}）",
                "满祝福消耗数量": f"{full_value_consume_num}（必成再+{consume_num}）",
                "是否升级": (possess_num + store_num)
                >= (full_value_consume_num + consume_num),
            }
        return data

    def upgrade(self, name: str):
        """专精升级"""
        url = {
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

        data = self.data[name]
        _id: str = data["id"]

        consume_name, consume_num, possess_num = split_consume_data(
            self.d, data["消耗"]
        )
        e = Exchange(self.d, url[consume_name], consume_num, possess_num)

        # 关闭自动斗豆兑换
        self.d.get(f"cmd=weapon_specialize&op=9&type_id={_id}&auto_buy=0")
        self.d.log("关闭自动斗豆兑换", name)

        while True:
            # 积分商店兑换材料
            e.exchange()

            # 升级
            self.d.get(f"cmd=weapon_specialize&op=2&type_id={_id}")
            self.d.log(self.d.find(), name)
            self.d.log(self.d.find(r"祝福值：(.*?) "), name)
            if "升星失败" not in self.d.html:
                break

            # 更新材料拥有数量
            e.update_possess_num()


class WuQiLan:
    """专精武器栏自动兑换强化"""

    def __init__(self, d: DaLeDou):
        self.d = d
        # 镖行天下商店积分
        self.points = get_store_points(self.d, "cmd=exchange&subtype=10&costtype=4")

        self.fail_value = self.get_fail_value()
        self.data = self.get_data()

    def get_fail_value(self) -> int:
        """返回专精武器栏失败祝福值"""
        # 祝福合集宝库
        self.d.get("cmd=newAct&subtype=143")
        if "=专精=" not in self.d.html:
            return 2
        return int(self.d.find(r"武器栏失败获得(\d+)"))

    def get_data(self) -> dict:
        """获取专精武器栏数据"""
        data = {}
        # 材料拥有数量
        possess_num = get_backpack_number(self.d, 3659)
        for _id in range(1000, 1012):
            self.d.get(f"cmd=weapon_specialize&op=4&storage_id={_id}")
            if "当前等级：10" in self.d.html or "激活" in self.d.html:
                continue

            # 名称
            name = self.d.find(r"专精武器：(.*?) ")
            # 当前等级
            level = self.d.find(r"当前等级：(.*?)<")
            # 材料消耗名称
            consume_name = self.d.find(r"消耗：(.*?)\*")
            # 材料消耗数量
            consume_num = int(self.d.find(r"消耗：.*?(\d+)"))
            # 当前祝福值
            now_value = int(self.d.find(r"祝福值：(\d+)"))
            # 总祝福值
            total_value = int(self.d.find(r"祝福值：\d+/(\d+)"))

            # 商店积分可兑换数量
            store_num = self.points // 40
            # 满祝福消耗数量
            full_value_consume_num = compute(
                self.fail_value, consume_num, now_value, total_value
            )

            data[name] = {
                "名称": name,
                "id": _id,
                "等级": level,
                "消耗": f"{consume_name}*{consume_num}（{possess_num}）",
                "祝福值": f"{now_value}/{total_value}（↑{self.fail_value}）",
                "积分": f"{self.points}（{store_num}）",
                "满祝福消耗数量": f"{full_value_consume_num}（必成再+{consume_num}）",
                "是否升级": (possess_num + store_num)
                >= (full_value_consume_num + consume_num),
            }
        return data

    def upgrade(self, name: str):
        """专精武器栏升级"""
        url = {
            "千年寒铁": {
                "ten": "cmd=exchange&subtype=2&type=1209&times=10&costtype=4",
                "one": "cmd=exchange&subtype=2&type=1209&times=1&costtype=4",
            },
        }

        data = self.data[name]
        _id: str = data["id"]

        consume_name, consume_num, possess_num = split_consume_data(
            self.d, data["消耗"]
        )
        e = Exchange(self.d, url[consume_name], consume_num, possess_num)

        # 关闭自动斗豆兑换
        self.d.get(f"cmd=weapon_specialize&op=10&storage_id={_id}&auto_buy=0")
        self.d.log("关闭自动斗豆兑换", name)

        while True:
            # 积分商店兑换材料
            e.exchange()

            # 升级
            self.d.get(f"cmd=weapon_specialize&op=5&storage_id={_id}")
            self.d.log(self.d.find(), name)
            self.d.log(self.d.find(r"祝福值：(.*?) "))
            if "升星失败" not in self.d.html:
                break

            # 更新材料拥有数量
            e.update_possess_num()


def 专精(d: DaLeDou):
    """专精自动兑换强化"""
    while True:
        category = Input.select("请选择分类：", ["专精", "武器栏"])
        if category is None:
            return
        elif category == "专精":
            upgrade(ZhuanJing(d))
        elif category == "武器栏":
            upgrade(WuQiLan(d))


class LingShouPian:
    """神魔录灵兽篇自动兑换强化"""

    def __init__(self, d: DaLeDou):
        self.d = d
        # 问鼎天下商店积分
        self.points = get_store_points(self.d, "cmd=exchange&subtype=10&costtype=14")

        self.fail_value = self.get_fail_value()
        self.data = self.get_data()

    def get_fail_value(self) -> int:
        """返回灵兽篇失败祝福值"""
        # 祝福合集宝库
        self.d.get("cmd=newAct&subtype=143")
        if "=神魔录=" not in self.d.html:
            return 2
        return int(self.d.find(r"灵兽经五阶5星.*?获得(\d+)"))

    def get_data(self) -> dict:
        """获取灵兽篇数据"""
        data_dict = {
            "夔牛经": "1",
            "饕餮经": "2",
            "烛龙经": "3",
            "黄鸟经": "4",
        }
        data = {}

        for name, _id in data_dict.items():
            self.d.get(f"cmd=ancient_gods&op=1&id={_id}")
            if "五阶五级" in self.d.html:
                continue

            # 等级
            level = self.d.find(r"等级：(.*?)&")
            # 材料消耗名称
            consume_name = self.d.find(r"消耗：(.*?)\*")
            # 材料消耗数量
            consume_num = int(self.d.find(r"\*(\d+)"))
            # 材料拥有数量
            possess_num = int(self.d.find(r"（(\d+)）"))
            # 当前祝福值
            now_value = int(self.d.find(r"祝福值：(\d+)"))
            # 总祝福值
            total_value = int(self.d.find(r"祝福值：\d+/(\d+)"))

            # 满祝福消耗数量
            full_value_number = compute(
                self.fail_value, consume_num, now_value, total_value
            )
            # 商店积分可兑换数量
            store_num = self.points // 40

            data[name] = {
                "名称": name,
                "id": _id,
                "等级": level,
                "消耗": f"{consume_name}*{consume_num}（{possess_num}）",
                "祝福值": f"{now_value}/{total_value}（↑{self.fail_value}）",
                "积分": f"{self.points}（{store_num}）",
                "满祝福消耗数量": f"{full_value_number}（必成再+{consume_num}）",
                "是否升级": (possess_num + store_num)
                >= (full_value_number + consume_num),
            }
        return data

    def upgrade(self, name: str):
        """灵兽篇提升"""
        url = {
            "神魔残卷": {
                "ten": "cmd=exchange&subtype=2&type=1267&times=10&costtype=14",
                "one": "cmd=exchange&subtype=2&type=1267&times=1&costtype=14",
            }
        }

        data = self.data[name]
        _id: str = data["id"]

        consume_name, consume_num, possess_num = split_consume_data(
            self.d, data["消耗"]
        )
        e = Exchange(self.d, url[consume_name], consume_num, possess_num)

        # 关闭自动斗豆兑换
        self.d.get(f"cmd=ancient_gods&op=5&autoBuy=0&id={_id}")
        self.d.log("关闭自动斗豆兑换", name)

        while True:
            # 积分商店兑换材料
            e.exchange()

            # 提升一次
            self.d.get(f"cmd=ancient_gods&op=6&id={_id}&times=1")
            self.d.log(self.d.find(), name)
            self.d.log(self.d.find(r"祝福值：(.*?)<"), name)
            if "升级失败" not in self.d.html:
                break

            # 更新材料拥有数量
            e.update_possess_num()


class GuZhenPian:
    """古阵篇自动兑换突破"""

    def __init__(self, d: DaLeDou):
        self.d = d
        # 问鼎天下商店积分
        self.points = get_store_points(self.d, "cmd=exchange&subtype=10&costtype=14")

        self.data = self.get_data()

    def _get_backpack_number(self, consume_name: str) -> int:
        """获取碎片背包数量"""
        data_id = {
            "夔牛碎片": 5154,
            "饕餮碎片": 5155,
            "烛龙碎片": 5156,
            "黄鸟碎片": 5157,
        }
        return get_backpack_number(self.d, data_id[consume_name])

    def get_data(self) -> dict:
        """获取古阵篇数据"""
        data_dict = {
            "夔牛鼓": "1",
            "饕餮鼎": "2",
            "烛龙印": "3",
            "黄鸟伞": "4",
        }
        data = {}

        # 商店积分可兑换突破石数量
        t_store_num = self.points // 40
        # 突破石拥有数量
        t_possess_num = get_backpack_number(self.d, 5153)

        for name, _id in data_dict.items():
            # 宝物详情
            self.d.get(f"cmd=ancient_gods&op=4&id={_id}")

            # 当前等级
            now_level = self.d.find(r"等级：(\d+)")
            # 最高等级
            highest_level = self.d.find(r"至(\d+)")
            if now_level == highest_level:
                continue

            # 突破石消耗数量
            t_consume_num = int(self.d.find(r"突破石\*(\d+)"))
            # 碎片消耗名称
            s_consume_name = self.d.find(r"\+ (.*?)\*")
            # 碎片消耗数量
            s_consume_num = int(self.d.find(r"碎片\*(\d+)"))
            # 碎片拥有数量
            s_possess_num = self._get_backpack_number(s_consume_name)

            data[name] = {
                "名称": name,
                "id": _id,
                "等级": now_level,
                "消耗": f"突破石*{t_consume_num}（{t_possess_num}）+ {s_consume_name}*{s_consume_num}（{s_possess_num}）",
                "积分": f"{self.points}（{t_store_num}）",
                "是否升级": ((t_possess_num + t_store_num) >= t_consume_num)
                and (s_possess_num >= s_consume_num),
                "说明": "仅兑换突破石",
            }
        return data

    def upgrade(self, name: str):
        """古阵篇突破"""
        url = {
            "突破石": {
                "ten": "cmd=exchange&subtype=2&type=1266&times=10&costtype=14",
                "one": "cmd=exchange&subtype=2&type=1266&times=1&costtype=14",
            }
        }

        data = self.data[name]
        _id: str = data["id"]

        consume_name, consume_num, possess_num = split_consume_data(
            self.d, data["消耗"]
        )
        e = Exchange(self.d, url[consume_name], consume_num, possess_num)

        # 积分商店兑换材料
        e.exchange()

        # 突破等级
        self.d.get(f"cmd=ancient_gods&op=7&id={_id}")
        self.d.log(self.d.find(), name)


def 神魔录(d: DaLeDou):
    """神魔录：灵兽篇自动兑换强化、古阵篇自动兑换突破"""
    while True:
        category = Input.select("请选择分类：", ["灵兽篇", "古阵篇"])
        if category is None:
            return
        elif category == "灵兽篇":
            upgrade(LingShouPian(d))
        elif category == "古阵篇":
            upgrade(GuZhenPian(d))


def 柒承的忙碌日常(d: DaLeDou, name: str, number: int, ins_id: int):
    """最高550金币"""
    for i in range(number):
        # 开启副本
        d.get(f"cmd=jianghudream&op=beginInstance&ins_id={ins_id}")
        if "帮助" in d.html:
            # 您还未编辑副本队伍，无法开启副本
            d.log(d.find(), name).append()
            return

        is_defeat = False
        print_separator()
        count = i + 1
        print(f"第 {count} 次（余 {number - count}）")
        print_separator()

        for _ in range(8):
            if "进入下一天" in d.html:
                # 进入下一天
                d.get("cmd=jianghudream&op=goNextDay")
            else:
                d.log("请手动通关剩余天数后再使用脚本", name)
                return

            if _id := d.find(r'event_id=(\d+)">战斗'):
                # 战斗
                d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")
                # FIGHT!
                d.get("cmd=jianghudream&op=doPveFight")
                d.log(d.find(r"<p>(.*?)<br />"), name)
                if "战败" in d.html:
                    is_defeat = True
                    break
            elif _id := d.find(r'event_id=(\d+)">奇遇'):
                # 奇遇
                d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")
                d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), name)
                # 视而不见
                d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=2")
                d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), name)
            elif _id := d.find(r'event_id=(\d+)">商店'):
                # 商店
                d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")

        # 结束回忆
        d.get("cmd=jianghudream&op=endInstance")
        d.log(d.find(), name).append()

        if is_defeat:
            break

    # 领取首通奖励
    d.get(f"cmd=jianghudream&op=getFirstReward&ins_id={ins_id}")
    d.log(d.find(), name).append()


def 群英拭剑谁为峰(d: DaLeDou, name: str, number: int, ins_id: int):
    """最高550金币"""
    for i in range(number):
        # 开启副本
        d.get(f"cmd=jianghudream&op=beginInstance&ins_id={ins_id}")
        if "帮助" in d.html:
            # 您还未编辑副本队伍，无法开启副本
            d.log(d.find(), name).append()
            return

        is_defeat = False
        print_separator()
        count = i + 1
        print(f"第 {count} 次（余 {number - count}）")
        print_separator()

        for _ in range(8):
            if "进入下一天" in d.html:
                # 进入下一天
                d.get("cmd=jianghudream&op=goNextDay")
            else:
                d.log("请手动通关剩余天数后再使用脚本", name)
                return

            if _id := d.find(r'event_id=(\d+)">战斗\(等级2\)'):
                # 战斗
                d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")
                # FIGHT!
                d.get("cmd=jianghudream&op=doPveFight")
                d.log(d.find(r"<p>(.*?)<br />"), name)
                if "战败" in d.html:
                    is_defeat = True
                    break

        # 结束回忆
        d.get("cmd=jianghudream&op=endInstance")
        d.log(d.find(), name).append()

        if is_defeat:
            break

    # 领取首通奖励
    d.get(f"cmd=jianghudream&op=getFirstReward&ins_id={ins_id}")
    d.log(d.find(), name).append()


def 时空守护者(d: DaLeDou, name: str, number: int, ins_id: int):
    """最高450金币"""
    for i in range(number):
        # 开启副本
        d.get(f"cmd=jianghudream&op=beginInstance&ins_id={ins_id}")
        if "帮助" in d.html:
            # 您还未编辑副本队伍，无法开启副本
            d.log(d.find(), name).append()
            return

        is_defeat = False
        print_separator()
        count = i + 1
        print(f"第 {count} 次（余 {number - count}）")
        print_separator()

        for day in range(9):
            if "进入下一天" in d.html:
                # 进入下一天
                d.get("cmd=jianghudream&op=goNextDay")
                day += 1
            else:
                d.log("请手动通关剩余天数后再使用脚本", name)
                return

            if _id := d.find(r'event_id=(\d+)">战斗\(等级2\)'):
                # 战斗
                d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")
                # FIGHT!
                d.get("cmd=jianghudream&op=doPveFight")
                d.log(d.find(r"<p>(.*?)<br />"), name)
                if "战败" in d.html:
                    is_defeat = True
                    break
            elif _ids := d.findall(r'event_id=(\d+)">战斗\(等级1\)'):
                if day == 2 or day == 4:
                    _id = _ids[-1]
                else:
                    _id = _ids[0]
                # 战斗
                d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")
                # FIGHT!
                d.get("cmd=jianghudream&op=doPveFight")
                d.log(d.find(r"<p>(.*?)<br />"), name)
                if "战败" in d.html:
                    is_defeat = True
                    break
            elif _ids := d.findall(r'event_id=(\d+)">奇遇\(等级2\)'):
                if day == 5:
                    _id = _ids[-1]
                else:
                    _id = _ids[0]
                # 奇遇
                d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")
                d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), name)
                if "上前询问" in d.html:
                    # 上前询问
                    d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=1")
                    d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), name)
                    # 一口答应
                    d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=1")
                elif "解释身份" in d.html:
                    # 解释身份
                    d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=2")
                    d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), name)
                    # 题诗一首
                    d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=1")
                elif "原地思考" in d.html:
                    # 原地思考
                    d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=2")
                    d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), name)
                    # 默默低语
                    d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=3")
                elif "放她回去" in d.html:
                    # 放她回去
                    d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=1")
                d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), name)
            elif _id := d.find(r'event_id=(\d+)">奇遇\(等级1\)'):
                # 奇遇
                d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")
                d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), name)
                if "转一次" in d.html:
                    # 转一次
                    d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=3")
                elif "漩涡1" in d.html:
                    # 漩涡1
                    d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=1")
                d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), name)
            elif _id := d.find(r'event_id=(\d+)">商店'):
                # 商店
                d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")

        # 结束回忆
        d.get("cmd=jianghudream&op=endInstance")
        d.log(d.find(), name).append()

        if is_defeat:
            break

    # 领取首通奖励
    d.get(f"cmd=jianghudream&op=getFirstReward&ins_id={ins_id}")
    d.log(d.find(), name).append()


def 倚天屠龙归我心(d: DaLeDou, name: str, number: int, ins_id: int):
    """最高558金币"""
    for i in range(number):
        # 开启副本
        d.get(f"cmd=jianghudream&op=beginInstance&ins_id={ins_id}")
        if "帮助" in d.html:
            # 您还未编辑副本队伍，无法开启副本
            d.log(d.find(), name).append()
            return

        is_defeat = False
        print_separator()
        count = i + 1
        print(f"第 {count} 次（余 {number - count}）")
        print_separator()

        for day in range(10):
            if "进入下一天" in d.html:
                # 进入下一天
                d.get("cmd=jianghudream&op=goNextDay")
                day += 1
            else:
                d.log("请手动通关剩余天数后再使用脚本", name)
                return

            if _id := d.find(r'event_id=(\d+)">战斗\(等级2\)'):
                # 战斗
                d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")
                # FIGHT!
                d.get("cmd=jianghudream&op=doPveFight")
                d.log(d.find(r"<p>(.*?)<br />"), name)
                if "战败" in d.html:
                    is_defeat = True
                    break
            elif _id := d.find(r'event_id=(\d+)">战斗\(等级1\)'):
                # 战斗
                d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")
                # FIGHT!
                d.get("cmd=jianghudream&op=doPveFight")
                d.log(d.find(r"<p>(.*?)<br />"), name)
                if "战败" in d.html:
                    is_defeat = True
                    break
            elif _id := d.find(r'event_id=(\d+)">奇遇\(等级2\)'):
                # 奇遇
                d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")
                d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), name)
                if day in [1, 3, 7]:
                    # 前辈、开始回忆、狠心离去
                    d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=1")
                elif day in [6, 8]:
                    # 昏昏沉沉、独自神伤
                    d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=3")
                d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), name)
            elif _id := d.find(r'event_id=(\d+)">商店'):
                # 商店
                d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")

        # 结束回忆
        d.get("cmd=jianghudream&op=endInstance")
        d.log(d.find(), name).append()

        if is_defeat:
            break

    # 领取首通奖励
    d.get(f"cmd=jianghudream&op=getFirstReward&ins_id={ins_id}")
    d.log(d.find(), name).append()


def 神雕侠侣(d: DaLeDou, name: str, number: int, ins_id: int):
    """最高500金币"""
    for i in range(number):
        # 开启副本
        d.get(f"cmd=jianghudream&op=beginInstance&ins_id={ins_id}")
        if "帮助" in d.html:
            # 您还未编辑副本队伍，无法开启副本
            d.log(d.find(), name).append()
            return

        is_defeat = False
        print_separator()
        count = i + 1
        print(f"第 {count} 次（余 {number - count}）")
        print_separator()

        for _ in range(8):
            if "进入下一天" in d.html:
                # 进入下一天
                d.get("cmd=jianghudream&op=goNextDay")
            else:
                d.log("请手动通关剩余天数后再使用脚本", name)
                return

            if _id := d.find(r'event_id=(\d+)">战斗\(等级2\)'):
                # 战斗
                d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")
                # FIGHT!
                d.get("cmd=jianghudream&op=doPveFight")
                d.log(d.find(r"<p>(.*?)<br />"), name)
                if "战败" in d.html:
                    is_defeat = True
                    break
            elif _id := d.find(r'event_id=(\d+)">奇遇\(等级2\)'):
                # 奇遇
                d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")
                d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), name)
                # 笼络侠客
                d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=3")
                d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), name)
            elif _id := d.find(r'event_id=(\d+)">商店'):
                # 商店
                d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")

        # 结束回忆
        d.get("cmd=jianghudream&op=endInstance")
        d.log(d.find(), name).append()

        if is_defeat:
            break

    # 领取首通奖励
    d.get(f"cmd=jianghudream&op=getFirstReward&ins_id={ins_id}")
    d.log(d.find(), name).append()


def 雪山藏魂(d: DaLeDou, name: str, number: int, ins_id: int):
    """最高490金币"""
    for i in range(number):
        # 开启副本
        d.get(f"cmd=jianghudream&op=beginInstance&ins_id={ins_id}")
        if "帮助" in d.html:
            # 您还未编辑副本队伍，无法开启副本
            d.log(d.find(), name).append()
            return

        is_defeat = False
        print_separator()
        count = i + 1
        print(f"第 {count} 次（余 {number - count}）")
        print_separator()

        for day in range(8):
            if "进入下一天" in d.html:
                # 进入下一天
                d.get("cmd=jianghudream&op=goNextDay")
                day += 1
            else:
                d.log("请手动通关剩余天数后再使用脚本", name)
                return

            if day == 4:
                is_conversation = False
                if _id := d.find(r'event_id=(\d+)">奇遇\(等级2\)'):
                    # 奇遇
                    d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")
                    d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), name)
                    # 尝试交谈（获得银狐玩偶）
                    d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=2")
                    d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), name)
                    is_conversation = True
                    # 询问大侠
                    d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=2")
                    continue

            if _ids := d.findall(r'event_id=(\d+)">战斗\(等级2\)'):
                if day in [2, 5]:
                    _id = _ids[-1]
                else:
                    _id = _ids[0]
                # 战斗
                d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")
                # FIGHT!
                d.get("cmd=jianghudream&op=doPveFight")
                d.log(d.find(r"<p>(.*?)<br />"), name)
                if "战败" in d.html:
                    is_defeat = True
                    break
            elif _id := d.find(r'event_id=(\d+)">奇遇\(等级2\)'):
                # 奇遇
                d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")
                d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), name)
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
                d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), name)
            elif _id := d.find(r'event_id=(\d+)">商店'):
                # 商店
                d.get(f"cmd=jianghudream&op=chooseEvent&event_id={_id}")

        # 结束回忆
        d.get("cmd=jianghudream&op=endInstance")
        d.log(d.find(), name).append()

        if is_defeat:
            break

    # 领取首通奖励
    d.get(f"cmd=jianghudream&op=getFirstReward&ins_id={ins_id}")
    d.log(d.find(), name).append()


def 江湖长梦_副本(d: DaLeDou) -> dict:
    base_data = {
        "柒承的忙碌日常": {
            "material_name": "追忆香炉",
            "material_id": 6477,
            "ins_id": 1,
        },
        "群英拭剑谁为峰": {
            "material_name": "拭剑香炉",
            "material_id": 6940,
            "ins_id": 32,
        },
        "时空守护者": {
            "material_name": "时空香炉",
            "material_id": 6532,
            "ins_id": 47,
        },
        "倚天屠龙归我心": {
            "material_name": "九阳香炉",
            "material_id": 6904,
            "ins_id": 48,
        },
        "神雕侠侣": {
            "material_name": "盛世香炉",
            "material_id": 6476,
            "ins_id": 49,
        },
        "雪山藏魂": {
            "material_name": "雪山香炉",
            "material_id": 8121,
            "ins_id": 50,
        },
    }

    print_separator()
    copy = {}
    for k, v in base_data.items():
        material_name = v["material_name"]
        material_id = v["material_id"]
        ins_id = v["ins_id"]

        number = get_backpack_number(d, material_id)
        if number == 0:
            print(f"{k}（{material_name}不足）")
            continue

        d.get(f"cmd=jianghudream&op=showCopyInfo&id={ins_id}")
        if "常规副本" in d.html:
            copy[k] = v
            copy[k]["number"] = number
            continue

        year = int(d.find(r"-(\d+)年"))
        month = int(d.find(r"-\d+年(\d+)月"))
        day = int(d.find(r"-\d+年\d+月(\d+)日"))
        end_time = datetime(2000 + year, month, day, 6, 0)
        current_time = datetime.now()
        if current_time < end_time:
            copy[k] = v
            copy[k]["number"] = number
        else:
            print(f"{k}（未开启）")

    if len(base_data) != len(copy):
        print_separator()
    return copy


def 江湖长梦(d: DaLeDou):
    """江湖长梦副本挑战次数即香炉数量，战败则提前结束"""
    while True:
        copy = 江湖长梦_副本(d)
        category = Input.select("请选择分类：", list(copy))
        if category is None:
            return

        material_name = copy[category]["material_name"]
        ins_id = copy[category]["ins_id"]
        number = copy[category]["number"]
        print_separator()
        print(f"{material_name}数量：{number}")

        globals()[category](d, category, number, ins_id)


class SanHun:
    """深渊之潮灵枢精魄三魂自动兑换强化"""

    def __init__(self, d: DaLeDou):
        self.d = d
        # 深渊积分
        self.points = get_store_points(self.d, "cmd=abysstide&op=viewabyssshop")

        self.data = self.get_data()

    def get_data(self) -> dict:
        """获取三魂数据"""
        data_dict = {"天魂": "1", "地魂": "2", "命魂": "3"}
        data = {}

        # 商店积分可兑换数量
        store_num = self.points // 90

        for name, _id in data_dict.items():
            self.d.get(f"cmd=abysstide&op=showsoul&soul_id={_id}")
            if "五阶五星" in self.d.html:
                continue
            # 阶段
            level = self.d.find(r"阶段：(.*?)<")
            # 材料消耗名称
            consume_name = self.d.find(r"消耗：(.*?)\*")
            # 材料消耗数量
            consume_num = int(self.d.find(r"消耗：.*?\*(\d+)"))
            # 材料拥有数量
            possess_num = int(self.d.find(r"\((\d+)\)"))
            # 当前进度
            now_value = int(self.d.find(r"进度：(\d+)/"))
            # 总进度
            total_value = int(self.d.find(r"进度：\d+/(\d+)"))

            # 满进度消耗数量
            full_value_consume_num = compute(2, consume_num, now_value, total_value)

            data[name] = {
                "名称": name,
                "id": _id,
                "阶段": level,
                "消耗": f"{consume_name}*{consume_num}（{possess_num}）",
                "进度": f"{now_value}/{total_value}（↑2）",
                "积分": f"{self.points}（{store_num}）",
                "满进度消耗数量": full_value_consume_num,
                "是否升级": (possess_num + store_num) >= full_value_consume_num,
                "说明": "进度值永久有效",
            }
        return data

    def upgrade(self, name: str):
        """三魂进阶"""
        url = {
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

        data = self.data[name]
        _id: str = data["id"]
        now_value, total_value = data["进度"].split("（")[0].split("/")
        full_value_consume_num: int = data["满进度消耗数量"]

        consume_name, _, possess_num = split_consume_data(self.d, data["消耗"])
        e = Exchange(self.d, url[consume_name], full_value_consume_num, possess_num)

        # 关闭自动斗豆兑换
        self.d.get(f"cmd=abysstide&op=setauto&value=0&soul_id={_id}")
        self.d.log("关闭自动斗豆兑换", name)

        # 积分商店兑换材料
        e.exchange()

        quotient, remainder = divmod((int(total_value) - int(now_value)), 20)
        for _ in range(quotient):
            # 进阶十次
            self.d.get(f"cmd=abysstide&op=upgradesoul&soul_id={_id}&times=10")
            self.d.log(self.d.find(r"进度：(.*?)&"), name)
        for _ in range(remainder // 2):
            # 进阶
            self.d.get(f"cmd=abysstide&op=upgradesoul&soul_id={_id}&times=1")
            self.d.log(self.d.find(r"进度：(.*?)&"), name)


def 深渊之潮(d: DaLeDou):
    """深渊之潮灵枢精魄三魂自动兑换强化"""
    while True:
        is_upgrade = upgrade(SanHun(d))
        if not is_upgrade:
            break


def 问道(d: DaLeDou):
    # 关闭自动斗豆
    d.get("cmd=immortals&op=setauto&type=0&status=0")
    d.log("问道关闭自动斗豆")
    while True:
        # 问道10次
        d.get("cmd=immortals&op=asktao&times=10")
        d.log(d.find(r"帮助</a><br />(.*?)<"))
        if "问道石不足" in d.html:
            # 一键炼化多余制作书
            d.get("cmd=immortals&op=smeltall")
            d.log(d.find(r"帮助</a><br />(.*?)<"))
            break


class XianWuXiuZhen:
    """仙武修真宝物自动强化"""

    def __init__(self, d: DaLeDou):
        self.d = d
        self.data = self.get_data()

    def get_fail_value(self, consume_name: str, now_level: int) -> int:
        """返回史诗、传说、神话失败祝福值"""
        data = {
            "史诗残片": "史诗级法宝",
            "传说残片": "传说级法宝",
            "神话残片": "神话级法宝",
        }
        # 祝福合集宝库
        self.d.get("cmd=newAct&subtype=143")
        if "=仙武修真=" not in self.d.html:
            return 2
        level, fail_value = self.d.findall(rf"{data[consume_name]}(\d+)级.*?(\d+)点")[0]
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

            # 法宝名称
            name = self.d.find(r'id">(.*?)&nbsp')
            # 当前等级
            level = int(self.d.find(r"\+(\d+)"))
            if level == max_level[name[:2]]:
                continue

            # 材料消耗名称
            consume_name = self.d.find(r"消耗：(.*?)\*")
            # 材料消耗数量
            consume_num = int(self.d.find(r"消耗：.*?(\d+)"))
            # 材料拥有数量
            possess_num = int(self.d.find(r"剩余数量.*?(\d+)"))
            # 当前祝福值
            now_value = int(self.d.find(r"祝福值：(\d+)"))
            # 总祝福值
            total_value = int(self.d.find(r"祝福值：\d+/(\d+)"))

            # 失败祝福值
            fail_value = self.get_fail_value(consume_name, level)
            # 满祝福消耗数量
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
                "是否升级": possess_num >= (full_value_consume_num + consume_num),
            }
        return data

    def upgrade(self, name: str):
        """法宝升级"""
        _id: str = self.data[name]["id"]

        # 关闭自动斗豆兑换
        self.d.get(f"cmd=immortals&op=setauto&type=1&status=0&treasureid={_id}")
        self.d.log("关闭自动斗豆兑换", name)

        while True:
            # 升级
            self.d.get(f"cmd=immortals&op=upgrade&treasureid={_id}&times=1")
            self.d.log(self.d.find(r'id">(.*?)<'), name)
            self.d.log(self.d.find(r"祝福值：(.*?)&"), name)
            if "升级失败" not in self.d.html:
                break


def 仙武修真(d: DaLeDou):
    """
    问道并一键炼化制作书
    宝物自动强化
    """
    while True:
        category = Input.select("请选择分类：", ["问道", "宝物"])
        if category is None:
            return
        elif category == "问道":
            print_separator()
            问道(d)
            print_separator()
        elif category == "宝物":
            upgrade(XianWuXiuZhen(d))


class XinYuanYingShenQi:
    """新元婴神器自动强化"""

    def __init__(self, d: DaLeDou, category: str):
        self.d = d
        self.category = category
        self.data = self.get_data(self.category)

    def get_data(self, name: str) -> dict:
        """获取神器数据"""
        url_params = {
            "投掷武器": "op=1&type=0",
            "小型武器": "op=1&type=1",
            "中型武器": "op=1&type=2",
            "大型武器": "op=1&type=3",
            "被动技能": "op=2&type=4",
            "伤害技能": "op=2&type=5",
            "特殊技能": "op=2&type=6",
        }
        data = {}
        params = url_params[name]
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
            name, level = t
            consume_num = int(consume_num_list[index])
            now_value = int(now_value_list[index])
            total_value = int(total_value_list[index])

            if level in ["0", "1", "2"]:
                number = consume_num
                fali_value = 0
            else:
                number = compute(2, consume_num, now_value, total_value)
                fali_value = 2

            data[name] = {
                "名称": name,
                "id": id_list[index],
                "星级": level,
                "消耗": f"真黄金卷轴*{consume_num}（{possess_num}）",
                "祝福值": f"{now_value}/{total_value}（↑{fali_value}）",
                "满祝福消耗数量": number,
                "是否升级": possess_num >= number,
            }
        return data

    def upgrade(self, name: str):
        """升级神器"""
        params_data = {
            "投掷武器": "0",
            "小型武器": "1",
            "中型武器": "2",
            "大型武器": "3",
            "被动技能": "4",
            "伤害技能": "5",
            "特殊技能": "6",
        }

        _id: str = self.data[name]["id"]
        t = params_data[self.category]

        # 关闭自动斗豆兑换
        self.d.get("cmd=newAct&subtype=104&op=4&autoBuy=0&type=1")
        self.d.log("关闭自动斗豆兑换", name)

        p = f"cmd=newAct&subtype=104&op=3&one_click=0&item_id={_id}&type={t}"
        while True:
            # 升级一次
            self.d.get(p)
            self.d.log(self.d.find())
            self.d.log(
                self.d.find(rf"{name}.*?:\d+ [\u4e00-\u9fff]+ (.*?)<br />"), name
            )
            if "恭喜您" in self.d.html:
                break


def 新元婴神器(d: DaLeDou):
    """新元婴神器自动强化"""
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
    """夺宝奇兵太空探宝场景自动投掷"""

    def __init__(self, d: DaLeDou):
        self.d = d

        while True:
            self.current_exploits = self.get_exploits()
            print_separator()
            print(f"当前战功：{self.current_exploits}")
            print_separator()
            self.retain_exploits = Input.number("请输入要保留的战功：")
            if self.retain_exploits is None:
                break
            if self.retain_exploits > self.current_exploits:
                continue
            self.pelted()

    def get_exploits(self) -> int:
        """获取五行战功"""
        # 五行-合成
        self.d.get("cmd=element&subtype=4")
        return int(self.d.find(r"拥有:(\d+)"))

    def pelted(self):
        """太空探宝16倍场景投掷"""
        print_separator()
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
                print_separator()
