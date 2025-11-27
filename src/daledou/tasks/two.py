"""
本模块为大乐斗第二轮任务
"""

from collections import Counter

from ..core.daledou import DaLeDou
from ..core.utils import DateTime
from .common import (
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
    open_count = 0

    def 结束回忆():
        nonlocal open_count
        # 结束回忆
        d.get("cmd=jianghudream&op=endInstance")
        d.log(d.find(), name)
        open_count += 1
        if open_count <= 10:
            d.append()
        else:
            d.append(f"{name}：共结束回忆 {open_count} 次（战败最多一次）")

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
                return

        结束回忆()

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


def 客栈同福(d: DaLeDou):
    c_客栈同福(d)


def 幸运金蛋(d: DaLeDou):
    c_幸运金蛋(d)


def 新春拜年(d: DaLeDou):
    # 新春拜年
    d.get("cmd=newAct&subtype=147")
    if "op=3" not in d.html:
        d.log("没有礼物收取").append()
        return

    # 收取礼物
    d.get("cmd=newAct&subtype=147&op=3")
    d.log(d.find(r"祝您：.*?<br /><br />(.*?)<br />")).append()


def 乐斗大笨钟(d: DaLeDou):
    c_乐斗大笨钟(d)
