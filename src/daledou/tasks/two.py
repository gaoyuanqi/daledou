"""
本模块为大乐斗第二轮任务
"""

import random
import re
import time
from collections import Counter

from ..core.daledou import DaLeDou
from ..core.utils import DateTime
from .common import (
    c_get_doushenta_cd,
    c_get_exchange_config,
    c_邪神秘宝,
    c_帮派商会,
    c_任务派遣中心,
    c_侠士客栈,
    c_帮派巡礼,
    c_深渊秘境,
    c_龙凰论武,
    c_幸运金蛋,
    c_客栈同福,
    c_乐斗大笨钟,
)


def 邪神秘宝(d: DaLeDou):
    c_邪神秘宝(d)


def 帮派商会(d: DaLeDou):
    c_帮派商会(d)


def 任务派遣中心(d: DaLeDou):
    c_任务派遣中心(d)


def 侠士客栈(d: DaLeDou):
    c_侠士客栈(d)


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
    counter = Counter()

    def 结束回忆():
        nonlocal counter
        # 结束回忆
        d.get("cmd=jianghudream&op=endInstance")
        msg = d.find()
        counter.update({msg: 1})
        d.log(msg, name)

    for _ in range(incense_burner_number):
        # 开启副本
        d.get(f"cmd=jianghudream&op=beginInstance&ins_id={ins_id}")
        if "帮助" in d.html:
            # 您还未编辑副本队伍，无法开启副本
            d.log(d.find(), name).append()
            return

        if current_name := d.find(r"你在(.*?)共度过了"):
            d.log(f"{name}：请先手动完成 {current_name}", name).append()
            return

        for day in range(copy_duration + 1):
            if "进入下一天" in d.html:
                # 进入下一天
                d.get("cmd=jianghudream&op=goNextDay")
                day += 1
            else:
                d.log(f"{name}：请手动通关剩余天数", name).append()
                return

            is_defeat = event(day)
            if is_defeat:
                结束回忆()
                for k, v in counter.items():
                    d.append(f"{v}次{k}")
                return

        结束回忆()

    for k, v in counter.items():
        d.append(f"{v}次{k}")

    # 领取首通奖励
    d.get(f"cmd=jianghudream&op=getFirstReward&ins_id={ins_id}")
    d.log(d.find(), name)
    if "请勿重复领取" not in d.html:
        d.append()


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


def 南海有岛名侠客(
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
            if day in {1, 5}:
                # 即刻前往 / 采摘野果（30金币）
                d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=1")
            elif day == 3:
                # 龙岛主
                d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=1")
                d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")
                # 岛中闲逛（80金币）
                d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=2")
            d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")
        return False

    jiang_hu_chang_meng(d, name, ins_id, incense_burner_number, copy_duration, event)


def 老鹅的圣诞冒险(
    d: DaLeDou, name: str, ins_id: str, incense_burner_number: int, copy_duration: int
):
    def event(day: int) -> bool:
        """战败返回True，否则返回False"""
        if _ids := d.findall(r'event_id=(\d+)">战斗'):
            if day == 3:
                _id = _ids[1]
            else:
                _id = _ids[0]
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
                # 喝口酒（30金币，血量-20%）
                d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=1")
            elif day == 2:
                # 要挟清官（30金币，血量-30）
                d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=3")
            elif day == 4:
                if "继续前行" in d.html:
                    # 继续前行
                    d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=1")
                    d.log(
                        d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天"
                    )
                    # 认真搜寻（25金币）
                    d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=1")
                elif "路线1" in d.html:
                    # 路线1（血量+10% / 10金币，血量-10%）
                    d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=1")
                elif "视而不见" in d.html:
                    # 视而不见（无 / 血量-10%）
                    d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=2")
            elif day == 5:
                # 抓住麋鹿
                d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=2")
                d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")
                # 圣诞祝福（复活你的一名侠士）
                d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=2")
            d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")
        return False

    jiang_hu_chang_meng(d, name, ins_id, incense_burner_number, copy_duration, event)


def 世外桃源梦一场(
    d: DaLeDou, name: str, ins_id: str, incense_burner_number: int, copy_duration: int
):
    def event(day: int) -> bool:
        """战败返回True，否则返回False"""
        if _ids := d.findall(r'event_id=(\d+)">战斗\(等级2\)'):
            if day in {2, 3}:
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
                # 向下望去（血量-5）
                d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=2")
                d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")
                # 小心摸索（谨小慎微buff：速度+30%）
                d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=2")
            elif day == 6:
                # 强势出手（势不可挡buff：力量+20%）
                d.get("cmd=jianghudream&op=chooseAdventure&adventure_id=1")
            d.log(d.find(r"获得金币：\d+<br />(.*?)<br />"), f"{name}-第{day}天")
        return False

    jiang_hu_chang_meng(d, name, ins_id, incense_burner_number, copy_duration, event)


def 江湖长梦(d: DaLeDou):
    copy_data = {
        "柒承的忙碌日常": {
            "material_name": "追忆香炉",
            "material_id": "6477",
        },
        "群英拭剑谁为峰": {
            "material_name": "拭剑香炉",
            "material_id": "6940",
        },
        "时空守护者": {
            "material_name": "时空香炉",
            "material_id": "6532",
        },
        "倚天屠龙归我心": {
            "material_name": "九阳香炉",
            "material_id": "6904",
        },
        "神雕侠侣": {
            "material_name": "盛世香炉",
            "material_id": "6476",
        },
        "雪山藏魂": {
            "material_name": "雪山香炉",
            "material_id": "8121",
        },
        "桃花自古笑春风": {
            "material_name": "桃花香炉",
            "material_id": "6825",
        },
        "战乱襄阳": {
            "material_name": "忠义香炉",
            "material_id": "6888",
        },
        "天涯浪子": {
            "material_name": "中秋香炉",
            "material_id": "6547",
        },
        "全真古墓意难平": {
            "material_name": "全真香炉",
            "material_id": "6662",
        },
        "南海有岛名侠客": {
            "material_name": "海岛香炉",
            "material_id": "6982",
        },
        "老鹅的圣诞冒险": {
            "material_name": "圣诞香炉",
            "material_id": "6609",
        },
        "世外桃源梦一场": {
            "material_name": "回梦香炉",
            "material_id": "6855",
        },
    }

    config: dict[str, bool] = d.config["江湖长梦"]["open"]
    if config is None:
        d.log("你没有启用任何一个副本").append()
        return

    # 江湖长梦
    d.get("cmd=jianghudream")
    ins_data = d.findall(r'id=(\d+)">(.*?)<')
    if not ins_data:
        d.log("无法获取副本数据").append()
        return

    for ins_id, copy in ins_data:
        if copy not in copy_data:
            continue
        copy_data[copy]["ins_id"] = ins_id

    for name, is_open in config.items():
        if not is_open:
            continue

        if name not in copy_data:
            d.log(f"{name}：还未开发该副本").append()
            continue

        material_name = copy_data[name]["material_name"]
        material_id = copy_data[name]["material_id"]
        ins_id = copy_data[name]["ins_id"]

        d.get(f"cmd=jianghudream&op=showCopyInfo&id={ins_id}")
        copy_duration = int(d.find(r"副本时长：(\d+)"))
        if "常规副本" not in d.html:
            end_year = 2000 + int(d.find(r"-(\d+)年"))
            end_month = int(d.find(r"-\d+年(\d+)月"))
            end_day = int(d.find(r"-\d+年\d+月(\d+)日"))

            # 获取当前日期和结束日期前一天
            current_date, day_before_end = DateTime.get_current_and_end_date_offset(
                end_year, end_month, end_day
            )
            if current_date > day_before_end:
                d.log(f"{name}：不在开启时间内").append()
                continue

        incense_burner_number = d.get_backpack_number(material_id)
        if incense_burner_number == 0:
            d.log(f"{name}：{material_name}不足").append()
            continue

        globals()[name](d, name, ins_id, incense_burner_number, copy_duration)


def 深渊之潮(d: DaLeDou):
    c_帮派巡礼(d)
    c_深渊秘境(d)


def 侠客岛(d: DaLeDou):
    # 侠客行
    d.get("cmd=knight_island&op=viewmissionindex")
    data = d.findall(r"getmissionreward&amp;pos=(\d+)")
    if not data:
        d.log("没有奖励领取").append()
        return

    for p in data:
        # 领取
        d.get(f"cmd=knight_island&op=getmissionreward&pos={p}")
        d.log(d.find(r"斗豆）<br />(.*?)<br />")).append()


def 龙凰之境(d: DaLeDou):
    c_龙凰论武(d)


def 背包(d: DaLeDou):
    use: list[str] = d.config["背包"]
    if use is None:
        d.log("你没有配置背包").append()
        return

    # 背包
    d.get("cmd=store&store_type=0")
    total_pages = d.find(r"第1/(\d+)")
    if total_pages is None:
        d.log("没有找到总页数").append()
        return

    data = []
    for p in range(1, int(total_pages) + 1):
        d.get(f"cmd=store&store_type=0&page={p}")
        d.log(f"查找第 {p} 页")
        if "使用规则" in d.html:
            d.log(d.find(r"】</p><p>(.*?)<"))
            continue
        d.html = d.find(r"清理(.*?)商店")
        for _id, name, number in d.findall(r'id=(\d+)">(.*?)</a>数量：(\d+)'):
            for item in use:
                if item not in name:
                    continue
                data.append((_id, name, int(number)))

    counter = Counter()
    for _id, name, number in set(data):
        for _ in range(number):
            # 使用
            d.get(f"cmd=use&id={_id}")
            if "您使用了" in d.html or "你打开" in d.html:
                msg = d.find()
                d.log(msg)
                counter.update({msg: 1})
                continue
            elif "该物品不能被使用" in d.html:
                d.log(f"{name}{_id}：该物品不能被使用").append()
            elif "提示信息" in d.html:
                d.log(f"{name}{_id}：需二次确定使用").append()
            elif "使用规则" in d.html:
                # 该物品今天已经不能再使用了
                # 很抱歉，系统繁忙，请稍后再试
                d.log(f"{name}{_id}：" + d.find(r"】</p><p>(.*?)<"))
            else:
                d.log(f"{name}{_id}：没有匹配到使用结果").append()
            break

    for k, v in counter.items():
        d.append(f"{v}次{k}")


def 镶嵌(d: DaLeDou):
    def get_p():
        for p_1 in range(4001, 4062, 10):
            # 魂珠1级
            yield p_1
        for p_2 in range(4002, 4063, 10):
            # 魂珠2级
            yield p_2
        for p_3 in range(4003, 4064, 10):
            # 魂珠3级
            yield p_3

    for _id in range(2000, 2007):
        for _ in range(50):
            # 魂珠碎片 -> 1
            d.get(f"cmd=upgradepearl&type=6&exchangetype={_id}")
            d.log(d.find(r"魂珠升级</p><p>(.*?)</p>"), f"镶嵌-{_id}")
            if "不能合成该物品" in d.html:
                # 抱歉，您的xx魂珠碎片不足，不能合成该物品！
                break
            d.append()

    count = 0
    for _id in get_p():
        for _ in range(50):
            # 1 -> 2 -> 3 -> 4
            d.get(f"cmd=upgradepearl&type=3&pearl_id={_id}")
            d.log(d.find(r"魂珠升级</p><p>(.*?)<"), f"镶嵌-{_id}")
            if "您拥有的魂珠数量不够" in d.html:
                break
            count += 1
    if count:
        d.append(f"升级成功*{count}")


def 普通合成(d: DaLeDou):
    data = []
    # 神匠坊背包
    for p in range(1, 20):
        # 下一页
        d.get(f"cmd=weapongod&sub=12&stone_type=0&quality=0&page={p}")
        d.log(f"背包第 {p} 页")
        data += d.findall(r"拥有：(\d+)/(\d+).*?stone_id=(\d+)")
        if "下一页" not in d.html:
            break
    for possess, consume, _id in data:
        if int(possess) < int(consume):
            # 符石碎片不足
            continue
        count = int(possess) // int(consume)
        for _ in range(count):
            # 普通合成
            d.get(f"cmd=weapongod&sub=13&stone_id={_id}")
            d.log(d.find(r"背包<br /></p>(.*?)!")).append()


def 符石分解(d: DaLeDou):
    config: list[int] = d.config["神匠坊"]
    if config is None:
        d.log("你没有配置神匠坊符石分解").append()
        return

    data = []
    # 符石分解
    for p in range(1, 10):
        # 下一页
        d.get(f"cmd=weapongod&sub=9&stone_type=0&page={p}")
        d.log(f"符石分解第 {p} 页")
        data += d.findall(r"数量:(\d+).*?stone_id=(\d+)")
        if "下一页" not in d.html:
            break
    for num, _id in data:
        if int(_id) not in config:
            continue
        # 分解
        d.get(f"cmd=weapongod&sub=11&stone_id={_id}&num={num}&i_p_w=num%7C")
        d.log(d.find(r"背包</a><br /></p>(.*?)<")).append()


def 符石打造(d: DaLeDou):
    # 符石
    d.get("cmd=weapongod&sub=7")
    number = int(d.find(r"符石水晶：(\d+)"))
    quotient, remainder = divmod(number, 60)
    for _ in range(quotient):
        # 打造十次
        d.get("cmd=weapongod&sub=8&produce_type=1&times=10")
        d.log(d.find(r"背包</a><br /></p>(.*?)<")).append()
    for _ in range(remainder // 6):
        # 打造一次
        d.get("cmd=weapongod&sub=8&produce_type=1&times=1")
        d.log(d.find(r"背包</a><br /></p>(.*?)<")).append()


def 神匠坊(d: DaLeDou):
    普通合成(d)
    符石分解(d)
    符石打造(d)


def 每日宝箱(d: DaLeDou):
    # 每日宝箱
    d.get("cmd=dailychest")
    data = d.findall(r'type=(\d+)">打开.*?(\d+)/(\d+)')
    if not data:
        d.log("没有可打开的宝箱").append()
        return

    counter = Counter()
    for t, possess, consume in data:
        for _ in range(min(10, int(possess) // int(consume))):
            # 打开
            d.get(f"cmd=dailychest&op=open&type={t}")
            msg = d.find(r"说明</a><br />(.*?)<")
            d.log(msg)
            if "今日开宝箱次数已达上限" in d.html:
                break
            counter.update({msg: 1})

    for k, v in counter.items():
        d.append(f"{v}次{k}")


def 商店(d: DaLeDou):
    urls = [
        "cmd=longdreamexchange",  # 江湖长梦
        "cmd=wlmz&op=view_exchange",  # 武林盟主
        "cmd=arena&op=queryexchange",  # 竞技场
        "cmd=ascendheaven&op=viewshop",  # 飞升大作战
        "cmd=abysstide&op=viewabyssshop",  # 深渊之潮-深渊黑商
        "cmd=abysstide&op=viewwishshop",  # 深渊之潮-许愿帮铺
        "cmd=exchange&subtype=10&costtype=1",  # 踢馆
        "cmd=exchange&subtype=10&costtype=2",  # 掠夺
        "cmd=exchange&subtype=10&costtype=3",  # 矿洞
        "cmd=exchange&subtype=10&costtype=4",  # 镖行天下
        "cmd=exchange&subtype=10&costtype=9",  # 幻境
        "cmd=exchange&subtype=10&costtype=10",  # 群雄逐鹿
        "cmd=exchange&subtype=10&costtype=11",  # 门派邀请赛
        "cmd=exchange&subtype=10&costtype=12",  # 帮派祭坛
        "cmd=exchange&subtype=10&costtype=13",  # 会武
        "cmd=exchange&subtype=10&costtype=14",  # 问鼎天下
    ]
    for url in urls:
        d.get(url)
        d.log(d.find()).append()


def 福利(d: DaLeDou):
    # 首页
    d.get("cmd=index")
    name = d.find(r">([\u4e00-\u9fa5]+)福利</a>")
    if name is None:
        d.log("只在节日/双旦/金秋/春节等多倍福利时执行").append()
        return

    name = f"{name}-斗神塔"
    d.append(name)
    challenge_count: int = d.config["福利"]["斗神塔"]
    if challenge_count <= 0:
        d.log(f"你设置斗神塔挑战次数为{challenge_count}", name).append()
        return

    count = 0
    second = c_get_doushenta_cd(d)
    for _ in range(challenge_count):
        # 自动挑战
        d.get("cmd=towerfight&type=11")
        d.log(d.find(), name)
        if "扫荡完成" in d.html:
            count += 1
        if "结束挑战" in d.html:
            time.sleep(second)
            # 结束挑战
            d.get("cmd=towerfight&type=7")
            d.log(d.find(), name)
        else:
            d.append()
            break
    if count:
        d.append(f"斗神塔自动挑战*{count}")


def 猜单双(d: DaLeDou):
    # 猜单双
    d.get("cmd=oddeven")
    for _ in range(5):
        value = d.findall(r'value=(\d+)">.*?数')
        if not value:
            d.log("猜单双已经结束").append()
            break

        value = random.choice(value)
        # 单数1 双数2
        d.get(f"cmd=oddeven&value={value}")
        d.log(d.find()).append()


def 煮元宵(d: DaLeDou):
    # 煮元宵
    d.get("cmd=yuanxiao2014")
    for _ in range(4):
        # 开始烹饪
        d.get("cmd=yuanxiao2014&op=1")
        if "领取烹饪次数" in d.html:
            d.log("没有烹饪次数了").append()
            break

        for _ in range(20):
            maturity = d.find(r"当前元宵成熟度：(\d+)")
            if int(maturity) < 96:
                # 继续加柴
                d.get("cmd=yuanxiao2014&op=2")
                continue
            # 赶紧出锅
            d.get("cmd=yuanxiao2014&op=3")
            d.log(d.find(r"活动规则</a><br /><br />(.*?)。")).append()
            break


def 元宵节(d: DaLeDou):
    # 领取
    d.get("cmd=newAct&subtype=101&op=1")
    d.log(d.find(r"】</p>(.*?)<br />")).append()
    # 领取形象卡
    d.get("cmd=newAct&subtype=101&op=2&index=0")
    d.log(d.find(r"】</p>(.*?)<br />")).append()


def 幸运金蛋(d: DaLeDou):
    c_幸运金蛋(d)


def 客栈同福(d: DaLeDou):
    c_客栈同福(d)


def 新春拜年(d: DaLeDou):
    # 新春拜年
    d.get("cmd=newAct&subtype=147")
    if "op=3" not in d.html:
        d.log("没有礼物收取").append()
        return

    # 收取礼物
    d.get("cmd=newAct&subtype=147&op=3")
    d.log(d.find(r"祝您：.*?<br /><br />(.*?)<br />")).append()


def 神魔转盘(d: DaLeDou):
    # 神魔转盘
    d.get("cmd=newAct&subtype=88&op=0")
    if "免费抽奖一次" not in d.html:
        d.log("没有免费抽奖次数了").append()
        return

    # 幸运抽奖
    d.get("cmd=newAct&subtype=88&op=1")
    d.log(d.find()).append()


def 乐斗驿站(d: DaLeDou):
    # 领取
    d.get("cmd=newAct&subtype=167&op=2")
    d.log(d.find()).append()


def 幸运转盘(d: DaLeDou):
    d.get("cmd=newAct&subtype=57&op=roll")
    d.log(d.find(r"0<br /><br />(.*?)<br />")).append()


def 冰雪企缘(d: DaLeDou):
    # 冰雪企缘
    d.get("cmd=newAct&subtype=158&op=0")
    gift = d.findall(r"gift_type=(\d+)")
    if not gift:
        d.log("没有礼包领取").append()
        return

    for _id in gift:
        # 领取
        d.get(f"cmd=newAct&subtype=158&op=2&gift_type={_id}")
        d.log(d.find()).append()


def 甜蜜夫妻(d: DaLeDou):
    # 甜蜜夫妻
    d.get("cmd=newAct&subtype=129")
    flag = d.findall(r"flag=(\d+)")
    if not flag:
        d.log("没有礼包领取").append()
        return

    for f in flag:
        # 领取
        d.get(f"cmd=newAct&subtype=129&op=1&flag={f}")
        d.log(d.find(r"】</p>(.*?)<br />")).append()


def 乐斗菜单(d: DaLeDou):
    # 乐斗菜单
    d.get("cmd=menuact")
    if gift := d.find(r"套餐.*?gift=(\d+).*?点单</a>"):
        # 点单
        d.get(f"cmd=menuact&sub=1&gift={gift}")
        d.log(d.find(r"哦！<br /></p>(.*?)<br />")).append()
    else:
        d.log("没有点单次数了").append()


def 周周礼包(d: DaLeDou):
    # 周周礼包
    d.get("cmd=weekgiftbag&sub=0")
    if _id := d.find(r';id=(\d+)">领取'):
        # 领取
        d.get(f"cmd=weekgiftbag&sub=1&id={_id}")
        d.log(d.find()).append()
    else:
        d.log("没有礼包领取").append()


def 登录有礼(d: DaLeDou):
    # 登录有礼
    d.get("cmd=newAct&subtype=56")
    if g := d.find(r"gift_type=1.*?gift_index=(\d+)"):
        # 领取
        d.get(f"cmd=newAct&subtype=56&op=draw&gift_type=1&gift_index={g}")
        d.log(d.find()).append()
    if g := d.find(r"gift_type=2.*?gift_index=(\d+)"):
        # 领取
        d.get(f"cmd=newAct&subtype=56&op=draw&gift_type=2&gift_index={g}")
        d.log(d.find()).append()


def 活跃礼包(d: DaLeDou):
    for p in ["1", "2"]:
        d.get(f"cmd=newAct&subtype=94&op={p}")
        d.log(d.find(r"】.*?<br />(.*?)<br />")).append()


def 上香活动(d: DaLeDou):
    for _ in range(2):
        # 檀木香
        d.get("cmd=newAct&subtype=142&op=1&id=1")
        d.log(d.find()).append()
        # 龙涎香
        d.get("cmd=newAct&subtype=142&op=1&id=2")
        d.log(d.find()).append()


def 徽章战令(d: DaLeDou):
    # 领取每日礼包
    d.get("cmd=badge&op=1")
    d.log(d.find()).append()


def 生肖福卡_好友赠卡(d: DaLeDou):
    # 好友赠卡
    d.get("cmd=newAct&subtype=174&op=4")
    for name, qq, card_id in d.findall(r"送您(.*?)\*.*?oppuin=(\d+).*?id=(\d+)"):
        # 领取
        d.get(f"cmd=newAct&subtype=174&op=6&oppuin={qq}&card_id={card_id}")
        d.log(d.find()).append()


def 生肖福卡_分享福卡(d: DaLeDou):
    qq: int = d.config["生肖福卡"]
    if qq is None:
        return

    # 生肖福卡
    d.get("cmd=newAct&subtype=174")
    pattern = "[子丑寅卯辰巳午未申酉戌亥][鼠牛虎兔龙蛇马羊猴鸡狗猪]"
    data = d.findall(rf"({pattern})\s+(\d+).*?id=(\d+)")
    _, max_number, _id = max(data, key=lambda x: int(x[1]))
    if int(max_number) >= 2:
        # 分享福卡
        d.get(f"cmd=newAct&subtype=174&op=5&oppuin={qq}&card_id={_id}&confirm=1")
        d.log(d.find(r"~<br /><br />(.*?)<br />")).append()


def 生肖福卡_领取福卡(d: DaLeDou):
    # 生肖福卡
    d.get("cmd=newAct&subtype=174")
    for _id in d.findall(r"task_id=(\d+)"):
        # 领取
        d.get(f"cmd=newAct&subtype=174&op=7&task_id={_id}")
        d.log(d.find(r"~<br /><br />(.*?)<br />")).append()


def 生肖福卡_合卡(d: DaLeDou):
    # 生肖福卡
    d.get("cmd=newAct&subtype=174")
    # 合卡结束日期
    month, day = d.findall(r"合卡时间：.*?至(\d+)月(\d+)日")[0]
    if d.month == int(month) and d.day == int(day):
        return

    # 合成周年福卡
    d.get("cmd=newAct&subtype=174&op=8")
    d.log(d.find(r"。<br /><br />(.*?)<br />")).append()


def 生肖福卡_抽奖(d: DaLeDou):
    # 生肖福卡
    d.get("cmd=newAct&subtype=174")
    # 兑奖开始日期
    month, day = d.findall(r"兑奖时间：(\d+)月(\d+)日")[0]
    if not (d.month == int(month) and d.day >= int(day)):
        return

    # 分斗豆
    d.get("cmd=newAct&subtype=174&op=9")
    d.log(d.find(r"。<br /><br />(.*?)<br />")).append()

    # 抽奖
    d.get("cmd=newAct&subtype=174&op=2")
    for _id, data in d.findall(r"id=(\d+).*?<br />(.*?)<br />"):
        numbers = re.findall(r"\d+", data)
        min_number = min(numbers, key=lambda x: int(x))
        for _ in range(int(min_number)):
            # 春/夏/秋/冬宵抽奖
            d.get(f"cmd=newAct&subtype=174&op=10&id={_id}&confirm=1")
            if "您还未合成周年福卡" in d.html:
                # 继续抽奖
                d.get(f"cmd=newAct&subtype=174&op=10&id={_id}")
            d.log(d.find(r"幸运抽奖<br /><br />(.*?)<br />")).append()


def 生肖福卡(d: DaLeDou):
    生肖福卡_好友赠卡(d)
    生肖福卡_分享福卡(d)
    生肖福卡_领取福卡(d)

    if d.week != 4:
        return

    生肖福卡_合卡(d)
    生肖福卡_抽奖(d)


def 长安盛会(d: DaLeDou):
    """
    盛会豪礼：点击领取  id  1
    签到宝箱：点击领取  id  2
    全民挑战：点击参与  id  3，4，5
    """
    # 5089真黄金卷轴 3036黄金卷轴
    d.get("cmd=newAct&subtype=118&op=2&select_id=5089")
    for _id in d.findall(r"op=1&amp;id=(\d+)"):
        if _id in ["1", "2"]:
            # 点击领取
            d.get(f"cmd=newAct&subtype=118&op=1&id={_id}")
            d.log(d.find()).append()
        else:
            turn_count = d.find(r"剩余转动次数：(\d+)")
            for _ in range(int(turn_count)):
                # 点击参与
                d.get(f"cmd=newAct&subtype=118&op=1&id={_id}")
                d.log(d.find()).append()


def 深渊秘宝(d: DaLeDou):
    # 深渊秘宝
    d.get("cmd=newAct&subtype=175")
    t_list = d.findall(r'type=(\d+)&amp;times=1">免费抽奖')
    if not t_list:
        d.log("没有免费抽奖次数了").append()
        return

    for t in t_list:
        # 领取
        d.get(f"cmd=newAct&subtype=175&op=1&type={t}&times=1")
        d.log(d.find()).append()


def 中秋礼盒(d: DaLeDou):
    # 中秋礼盒
    d.get("cmd=midautumngiftbag&sub=0")
    _ids = d.findall(r"amp;id=(\d+)")
    if not _ids:
        d.log("没有礼包领取").append()
        return

    for _id in _ids:
        # 领取
        d.get(f"cmd=midautumngiftbag&sub=1&id={_id}")
        d.log(d.find()).append()
        if "已领取完该系列任务所有奖励" in d.html:
            continue


def 双节签到(d: DaLeDou):
    # 领取签到奖励
    d.get("cmd=newAct&subtype=144&op=1")
    d.log(d.find()).append()

    end_month = int(d.find(r"至(\d+)月"))
    end_day = int(d.find(r"至\d+月(\d+)日"))
    # 获取当前日期和结束日期前一天
    current_date, day_before_end = DateTime.get_current_and_end_date_offset(
        d.year, end_month, end_day
    )
    if current_date == day_before_end:
        # 奖励金
        d.get("cmd=newAct&subtype=144&op=3")
        d.log(d.find()).append()


def 斗境探秘(d: DaLeDou):
    # 斗境探秘
    d.get("cmd=newAct&subtype=177")
    # 领取每日探秘奖励
    for _id in d.findall(r"id=(\d+)&amp;type=2"):
        # 领取
        d.get(f"cmd=newAct&subtype=177&op=2&id={_id}&type=2")
        d.log(d.find(r"】<br /><br />(.*?)<br />")).append()

    # 领取累计探秘奖励
    for _id in d.findall(r"id=(\d+)&amp;type=1"):
        # 领取
        d.get(f"cmd=newAct&subtype=177&op=2&id={_id}&type=1")
        d.log(d.find(r"】<br /><br />(.*?)<br />")).append()


def 春联大赛(d: DaLeDou):
    # 开始答题
    d.get("cmd=newAct&subtype=146&op=1")
    if "您的活跃度不足" in d.html:
        d.log("您的活跃度不足50").append()
        return

    couplets_dict = d.config["春联大赛"]
    for _ in range(3):
        if "今日答题已结束" in d.html:
            d.log("今日答题已结束").append()
            break

        shang_lian = d.find(r"上联：([^ &]*)")
        d.log(f"上联：{shang_lian}").append()
        options_A, index_A = d.findall(r"<br />A.(.*?)<.*?index=(\d+)")[0]
        options_B, index_B = d.findall(r"<br />B.(.*?)<.*?index=(\d+)")[0]
        options_C, index_C = d.findall(r"<br />C.(.*?)<.*?index=(\d+)")[0]
        options_dict = {
            options_A: index_A,
            options_B: index_B,
            options_C: index_C,
        }

        if xia_lian := couplets_dict.get(shang_lian):
            index = options_dict[xia_lian]
            # 选择
            d.get(f"cmd=newAct&subtype=146&op=3&index={index}")
            d.log(f"下联：{xia_lian}").append()
            # 确定选择
            d.get("cmd=newAct&subtype=146&op=2")
            d.log(d.find()).append()
        else:
            d.log("题库没有找到对联，请在配置文件更新题库").append()
            break

    for _id in d.findall(r'id=(\d+)">领取'):
        # 领取
        d.get(f"cmd=newAct&subtype=146&op=4&id={_id}")
        d.log(d.find()).append()


def 预热礼包(d: DaLeDou):
    # 领取
    d.get("cmd=newAct&subtype=117&op=1")
    d.log(d.find(r"<br /><br />(.*?)<")).append()


def 豪侠出世(d: DaLeDou):
    # 签到好礼
    d.get("cmd=knightdraw&op=view&sub=signin&ty=free")
    for _id in d.findall(r"giftId=(\d+)"):
        # 领取
        d.get(f"cmd=knightdraw&op=reqreward&sub=signin&ty=free&giftId={_id}")
        d.log(d.find(r"活动规则</a><br />(.*?)<br />")).append()


def 乐斗游记(d: DaLeDou):
    # 乐斗游记
    d.get("cmd=newAct&subtype=176")
    # 今日游记任务
    for _id in d.findall(r"task_id=(\d+)"):
        # 领取
        d.get(f"cmd=newAct&subtype=176&op=1&task_id={_id}")
        d.log(d.find(r"积分。<br /><br />(.*?)<br />")).append()

    if d.week != 4:
        return

    # 一键领取
    d.get("cmd=newAct&subtype=176&op=5")
    d.log(d.find(r"积分。<br /><br />(.*?)<br />")).append()
    d.log(d.find(r"十次</a><br />(.*?)<br />乐斗")).append()

    # 兑换
    number = int(d.find(r"溢出积分：(\d+)"))
    quotient, remainder = divmod(number, 10)
    for _ in range(quotient):
        # 兑换十次
        d.get("cmd=newAct&subtype=176&op=2&num=10")
        d.log(d.find(r"积分。<br /><br />(.*?)<br />"))
    for _ in range(remainder):
        # 兑换一次
        d.get("cmd=newAct&subtype=176&op=2&num=1")
        d.log(d.find(r"积分。<br /><br />(.*?)<br />"))
    d.append(f"消耗{number}溢出积分兑换传功符*{number}")


def 微信兑换(d: DaLeDou):
    code: int = d.config["微信兑换"]
    # 兑换
    d.get(f"cmd=weixin&cdkey={code}&sub=2&zapp_sid=&style=0&channel=0&i_p_w=cdkey|")
    d.log(d.find()).append()


def 浩劫宝箱(d: DaLeDou):
    d.get("cmd=index")
    t1 = d.find(r'subtype=(\d+)">浩劫宝箱')
    # 浩劫宝箱
    d.get(f"cmd=newAct&subtype={t1}")
    t2 = d.find(r"subtype=(\d+)")
    if t2 is None:
        d.log("没有可领取的礼包").append()
        return
    d.get(f"cmd=newAct&subtype={t2}")
    d.log(d.find()).append()


def 端午有礼(d: DaLeDou):
    """
    活动期间最多可以得到 4x7=28 个粽子

    index
    3       礼包4：消耗10粽子得到 淬火结晶*5+真黄金卷轴*5+徽章符文石*5+修为丹*5+境界丹*5+元婴飞仙果*5
    2       礼包3：消耗8粽子得到 2级日曜石*1+2级玛瑙石*1+2级迅捷石*1+2级月光石*1+2级紫黑玉*1
    1       礼包2：消耗6粽子得到 阅历羊皮卷*5+无字天书*5+河图洛书*5+还童天书*1
    0       礼包1：消耗4粽子得到 中体力*2+挑战书*2+斗神符*2
    """
    for _ in range(2):
        # 礼包4
        d.get("cmd=newAct&subtype=121&op=1&index=3")
        d.log(d.find(r"】<br /><br />(.*?)<br />")).append()
        if "您的端午香粽不足" in d.html:
            break

    # 礼包3
    d.get("cmd=newAct&subtype=121&op=1&index=2")
    d.log(d.find(r"】<br /><br />(.*?)<br />")).append()


def 圣诞有礼(d: DaLeDou):
    # 圣诞有礼
    d.get("cmd=newAct&subtype=145")
    for _id in d.findall(r"task_id=(\d+)"):
        # 任务描述：领取奖励
        d.get(f"cmd=newAct&subtype=145&op=1&task_id={_id}")
        d.log(d.find()).append()

    # 连线奖励
    for i in d.findall(r"index=(\d+)"):
        d.get(f"cmd=newAct&subtype=145&op=2&index={i}")
        d.log(d.find()).append()


def 新春礼包(d: DaLeDou):
    for _id in [280, 281, 282]:
        # 领取
        d.get(f"cmd=xinChunGift&subtype=2&giftid={_id}")
        d.log(d.find()).append()


def 喜从天降(d: DaLeDou):
    """活动时间20.00-22.00"""
    # 喜从天降
    d.get("cmd=newAct&subtype=137")
    for _ in range(int(d.find(r"剩余燃放次数：(\d+)"))):
        # 点燃烟花
        d.get("cmd=newAct&subtype=137&op=1")
        d.log(d.find()).append()


def 登录商店(d: DaLeDou):
    t: int = d.config["登录商店"]
    if t is None:
        d.log("你没有配置兑换物品id").append()
        return

    for _ in range(5):
        # 兑换5次
        d.get(f"cmd=newAct&op=exchange&subtype=52&type={t}&times=5")
        d.log(d.find(r"<br /><br />(.*?)<br /><br />")).append()
    for _ in range(3):
        # 兑换1次
        d.get(f"cmd=newAct&op=exchange&subtype=52&type={t}&times=1")
        d.log(d.find(r"<br /><br />(.*?)<br /><br />")).append()


def 盛世巡礼(d: DaLeDou):
    for s in range(1, 8):
        # 点击进入
        d.get(f"cmd=newAct&subtype=150&op=2&sceneId={s}")
        if "他已经给过你礼物了" in d.html:
            d.log(f"地点{s}礼物已领取").append()
        elif s == 7 and ("点击继续" not in d.html):
            d.log(f"地点{s}礼物已领取").append()
        elif _id := d.find(r"itemId=(\d+)"):
            # 收下礼物
            d.get(f"cmd=newAct&subtype=150&op=5&itemId={_id}")
            d.log(d.find(r"礼物<br />(.*?)<br />")).append()


def 五一礼包(d: DaLeDou):
    for _id in range(3):
        # 领取
        d.get(f"cmd=newAct&subtype=113&op=1&id={_id}")
        d.log(d.find(r"】<br /><br />(.*?)<")).append()


def 乐斗大笨钟(d: DaLeDou):
    c_乐斗大笨钟(d)


def 年兽大作战(d: DaLeDou):
    # 年兽大作战
    d.get("cmd=newAct&subtype=170&op=0")
    if "等级不够" in d.html:
        d.log("等级不够，还未开启年兽大作战哦！").append()
        return

    # 自选武技库
    if choose_count := d.html.count("暂未选择"):
        choose_ids = []
        for t in range(5):
            # 大、中、小、投、技
            d.get(f"cmd=newAct&subtype=170&op=4&type={t}")
            choose_ids += d.findall(r'id=(\d+)">选择')
            if len(choose_ids) >= choose_count:
                break
        if len(choose_ids) < choose_count:
            d.log(
                f"自选武技库数量不够补位：需选择{choose_count}个，但只有{len(choose_ids)}个"
            ).append()
            return
        for _id in choose_ids[:choose_count]:
            # 选择
            d.get(f"cmd=newAct&subtype=170&op=7&id={_id}")
            name = d.find(rf'id={_id}">(.*?)<')
            d.log(f"{name}：{d.find()}").append()

    # 随机武技库
    if "剩余免费随机次数：1" in d.html:
        # 随机
        d.get("cmd=newAct&subtype=170&op=6")
        d.log(d.find()).append()

    for _ in range(3):
        # 挑战
        d.get("cmd=newAct&subtype=170&op=8")
        d.log(d.find()).append()
        time.sleep(0.2)


def 惊喜刮刮卡(d: DaLeDou):
    # 领取
    for _id in range(3):
        d.get(f"cmd=newAct&subtype=148&op=2&id={_id}")
        d.log(d.find(r"奖池预览</a><br /><br />(.*?)<br />")).append()

    # 刮卡
    for _ in range(20):
        d.get("cmd=newAct&subtype=148&op=1")
        d.log(d.find(r"奖池预览</a><br /><br />(.*?)<br />")).append()
        if "您没有刮刮卡了" in d.html:
            break
        elif "不在刮奖时间不能刮奖" in d.html:
            break


def 开心娃娃机(d: DaLeDou):
    # 开心娃娃机
    d.get("cmd=newAct&subtype=124&op=0")
    if "1/1" not in d.html:
        d.log("没有免费抓取次数").append()
        return

    # 抓取一次
    d.get("cmd=newAct&subtype=124&op=1")
    d.log(d.find()).append()


def 好礼步步升(d: DaLeDou):
    d.get("cmd=newAct&subtype=43&op=get")
    d.log(d.find()).append()


def 企鹅吉利兑_兑换(d: DaLeDou):
    config: list[dict] = d.config["企鹅吉利兑"]["exchange"]
    if config is None:
        d.log("你没有配置兑换物品").append()
        return

    for name, _id, exchange_quantity in c_get_exchange_config(config):
        count = 0
        for _ in range(exchange_quantity):
            d.get(f"cmd=geelyexchange&op=ExchangeProps&id={_id}")
            d.log(d.find(r"】<br /><br />(.*?)<br />"), name)
            if "你的精魄不足，快去完成任务吧~" in d.html:
                break
            elif "该物品已达兑换上限~" in d.html:
                break
            count += 1
        if count:
            d.append(f"兑换{name}*{count}")


def 企鹅吉利兑(d: DaLeDou):
    # 企鹅吉利兑
    d.get("cmd=geelyexchange")
    if _ids := d.findall(r'id=(\d+)">领取</a>'):
        for _id in _ids:
            # 领取
            d.get(f"cmd=geelyexchange&op=GetTaskReward&id={_id}")
            d.log(d.find(r"】<br /><br />(.*?)<br /><br />")).append()
    else:
        d.log("没有礼包领取").append()

    year = d.year
    month = int(d.find(r"至(\d+)月"))
    day = int(d.find(r"至\d+月(\d+)日"))
    # 获取当前日期和结束日期前一天
    current_date, day_before_end = DateTime.get_current_and_end_date_offset(
        year, month, day
    )
    if current_date == day_before_end:
        企鹅吉利兑_兑换(d)


def 乐斗激运牌(d: DaLeDou):
    for _id in [0, 1]:
        # 领取
        d.get(f"cmd=realgoods&op=getTaskReward&id={_id}")
        d.log(d.find(r"<br /><br />(.*?)<br />")).append()

    number = int(d.find(r"我的激运牌：(\d+)"))
    for _ in range(number):
        # 我要翻牌
        d.get("cmd=realgoods&op=lotteryDraw")
        d.log(d.find(r"<br /><br />(.*?)<br />")).append()


def 乐斗回忆录(d: DaLeDou):
    for _id in range(1, 11):
        # 领取
        d.get(f"cmd=newAct&subtype=171&op=3&id={_id}")
        d.log(d.find(r"6点<br />(.*?)<br />")).append()


def 疯狂许愿(d: DaLeDou, config: str):
    # 乐斗儿童节、乐斗开学季
    d.get("cmd=newAct&subtype=130")
    if "取消返回" in d.html:
        # 取消返回
        d.get("cmd=newAct&subtype=130&op=6")

    if "op=2" not in d.html:
        d.log("你已经领取过了").append()
        return

    t, s = d.findall(r"type=(\d+)&sub_type=(\d+)", config)[0]
    # 选择分类
    d.get(f"cmd=newAct&subtype=130&op=2&type={t}")
    # 选择
    d.get(f"cmd=newAct&subtype=130&op=3&type={t}&sub_type={s}")
    d.log(d.find(r"】</p>(.*?)<")).append()


def 乐斗儿童节(d: DaLeDou):
    疯狂许愿(d, d.config["乐斗儿童节"])


def 乐斗开学季(d: DaLeDou):
    疯狂许愿(d, d.config["乐斗开学季"])


def 新春登录礼(d: DaLeDou):
    # 新春登录礼
    d.get("cmd=newAct&subtype=99&op=0")
    day = d.findall(r"day=(\d+)")
    if not day:
        d.log("没有礼包领取").append()
        return

    for d in day:
        # 领取
        d.get(f"cmd=newAct&subtype=99&op=1&day={d}")
        d.log(d.find()).append()


def 爱的同心结(d: DaLeDou):
    config: list[int] = d.config["爱的同心结"]
    if config is not None:
        for uin in config:
            # 赠送
            d.get(f"cmd=loveknot&sub=3&uin={uin}")
            d.log(d.find()).append()
            if "你当前没有同心结哦" in d.html:
                break

    data = {
        "4016": 2,
        "4015": 4,
        "4014": 10,
        "4013": 16,
        "4012": 20,
    }
    for _id, count in data.items():
        for _ in range(count):
            # 兑换
            d.get(f"cmd=loveknot&sub=2&id={_id}")
            d.log(d.find())
            if "恭喜您兑换成功" not in d.html:
                break
            d.append()


def 重阳太白诗会(d: DaLeDou):
    d.get("cmd=newAct&subtype=168&op=2")
    d.log(d.find(r"<br /><br />(.*?)<br />")).append()


def 五一预订礼包(d: DaLeDou):
    # 5.1预订礼包
    d.get("cmd=lokireservation")
    if _id := d.find(r"idx=(\d+)"):
        # 领取
        d.get(f"cmd=lokireservation&op=draw&idx={_id}")
        d.log(d.find(r"<br /><br />(.*?)<")).append()
    else:
        d.log("没有登录礼包领取").append()


def 周年生日祝福(d: DaLeDou):
    for day in range(1, 8):
        d.get(f"cmd=newAct&subtype=165&op=3&day={day}")
        d.log(d.find()).append()
