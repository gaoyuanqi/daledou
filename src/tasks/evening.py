import asyncio
import random

from src.tasks.register import TaskModule, Registry
from src.utils.daledou import DaLeDou
from src.utils.date_time import DateTime
from .common import (
    c_get_material_quantity,
    c_get_doushenta_cd,
    c_邪神秘宝,
    c_帮派商会,
    c_任务派遣中心,
    c_侠士客栈,
    c_帮派巡礼,
    c_深渊秘境,
    c_龙凰论武,
    c_幸运金蛋,
    c_客栈同福,
    c_大笨钟,
)


registry = Registry(
    TaskModule.evening, schedule_time="20:01:00", description="晚间任务"
)
register = registry.register


@register()
async def 邪神秘宝(d: DaLeDou):
    await c_邪神秘宝(d)


@register()
async def 星盘(d: DaLeDou):
    """合成2、3、4级"""
    if DateTime.week() != 4:
        return

    for t in range(1, 9):
        await d.get(f"cmd=astrolabe&op=showgemupgrade&gem_type={t}")
        data = d.findall(r"<br />=(.*?)=.*?gem=(\d+).*?(\d+) （(\d+)")
        for material_name, g, need, possess in data[1:4]:
            for _ in range(int(possess) // int(need)):
                await d.get(f"cmd=astrolabe&op=upgradegem&gem_type={t}&gem={g}")
                d.log(f"{material_name} -> {d.find()}")


@register()
async def 帮派商会(d: DaLeDou):
    await c_帮派商会(d)


@register()
async def 任务派遣中心(d: DaLeDou):
    await c_任务派遣中心(d)


@register()
async def 侠士客栈(d: DaLeDou):
    await c_侠士客栈(d)


async def _run_dream_instance(
    d: DaLeDou,
    name: str,
    ins_id: str,
    material_quantity: int,
    duration: int,
    handle_day,
):
    """运行江湖长梦副本的公共函数

    参数:
        d: DaLeDou实例
        name: 副本名称
        ins_id: 副本ID
        material_quantity: 香炉数量
        duration: 副本时长
        handle_day: 处理每天事件的函数
    """
    for _ in range(material_quantity):
        # 开启副本
        await d.get(f"cmd=jianghudream&op=beginInstance&ins_id={ins_id}")
        d.log("开启副本", name)
        if "帮助" in d.html:
            # 您还未编辑副本队伍，无法开启副本
            return

        if current_name := d.find(r"你在(.*?)共度过了"):
            d.log(f"{name}: 请先手动完成 {current_name}", name)
            return

        for day in range(duration + 1):
            if "进入下一天" in d.html:
                # 进入下一天
                await d.get("cmd=jianghudream&op=goNextDay")
                day += 1
            else:
                d.log("请先手动通关剩余天数", name)
                return

            if await handle_day(day):
                # 结束回忆
                await d.get("cmd=jianghudream&op=endInstance")
                d.log(d.find(), name)
                return

        # 结束回忆
        await d.get("cmd=jianghudream&op=endInstance")
        d.log(d.find(), name)

    # 领取首通奖励
    await d.get(f"cmd=jianghudream&op=getFirstReward&ins_id={ins_id}")
    d.log(d.find(), name)


class JiangHuDream:
    def __init__(
        self,
        d: DaLeDou,
        name: str,
        ins_id: str,
    ):
        self.d = d
        self.name = name
        self.ins_id = ins_id

    async def begin_success(self) -> bool:
        """成功开启副本返回True，否则返回False"""
        # 开启副本
        await self.d.get(f"cmd=jianghudream&op=beginInstance&ins_id={self.ins_id}")
        self.d.log("开启副本", self.name)
        if "帮助" in self.d.html:
            # 您还未编辑副本队伍，无法开启副本
            return False

        # 其他副本还没有结束
        if current_name := self.d.find(r"你在(.*?)共度过了"):
            self.d.log(f"请先手动完成 {current_name}", self.name)
            return False

        return True

    async def next_day(self, day: int) -> int | None:
        """成功下一天返回加一天的数字，否则返回None"""
        if "进入下一天" in self.d.html:
            # 进入下一天
            await self.d.get("cmd=jianghudream&op=goNextDay")
            day += 1
            return day
        self.d.log("请先手动通关剩余天数", self.name)

    async def choose_fight(self, day: int, event_id: str) -> bool:
        """选择战斗事件

        如果战败返回False，否则返回True
        """
        # 战斗
        await self.d.get(f"cmd=jianghudream&op=chooseEvent&event_id={event_id}")
        # FIGHT!
        await self.d.get("cmd=jianghudream&op=doPveFight")
        self.d.log(f"第 {day} 天 -> {self.d.find(r'<p>(.*?)<br />')}", self.name)
        if "战败" in self.d.html:
            return False
        return True

    async def choose_adventure(self, day: int, event_id: str, adventure_ids: list[int]):
        """选择奇遇事件"""
        # 奇遇
        await self.d.get(f"cmd=jianghudream&op=chooseEvent&event_id={event_id}")
        self.d.log(
            f"第 {day} 天 -> {self.d.find(r'获得金币：\d+<br />(.*?)<br />')}",
            self.name,
        )
        for _id in adventure_ids:
            await self.d.get(f"cmd=jianghudream&op=chooseAdventure&adventure_id={_id}")
            self.d.log(
                f"第 {day} 天 -> {self.d.find(r'获得金币：\d+<br />(.*?)<br />')}",
                self.name,
            )

    async def choose_store(self):
        """选择商店事件"""
        if event_id := self.d.find(r'event_id=(\d+)">商店'):
            # 商店
            await self.d.get(f"cmd=jianghudream&op=chooseEvent&event_id={event_id}")

    async def end_memories(self):
        # 结束回忆
        await self.d.get("cmd=jianghudream&op=endInstance")
        self.d.log(self.d.find(), self.name)
        # 领取首通奖励
        await self.d.get(f"cmd=jianghudream&op=getFirstReward&ins_id={self.ins_id}")
        self.d.log(self.d.find(), self.name)


async def 柒承的忙碌日常(
    d: DaLeDou, name: str, ins_id: str, material_quantity: int, duration: int
):
    j = JiangHuDream(d, name, ins_id)
    for _ in range(material_quantity):
        if not await j.begin_success():
            break

        for day in range(duration + 1):
            day = await j.next_day(day)
            if day is None:
                return

            if event_id := d.find(r'event_id=(\d+)">战斗'):
                if not await j.choose_fight(day, event_id):
                    await j.end_memories()
                    return
            elif event_id := d.find(r'event_id=(\d+)">奇遇'):
                # 奇遇 -> 视而不见
                await j.choose_adventure(day, event_id, [2])
                continue
            await j.choose_store()
        await j.end_memories()


async def 群英拭剑谁为峰(
    d: DaLeDou, name: str, ins_id: str, material_quantity: int, duration: int
):
    j = JiangHuDream(d, name, ins_id)
    for _ in range(material_quantity):
        if not await j.begin_success():
            break

        for day in range(duration + 1):
            day = await j.next_day(day)
            if day is None:
                return

            if event_id := d.find(r'event_id=(\d+)">战斗\(等级2\)'):
                if not await j.choose_fight(day, event_id):
                    await j.end_memories()
                    return
        await j.end_memories()


async def 时空守护者(
    d: DaLeDou, name: str, ins_id: str, material_quantity: int, duration: int
):
    adventur = {
        "上前询问": [1, 1],  # 一口答应
        "解释身份": [2, 1],  # 题诗一首
        "原地思考": [2, 3],  # 默默低语
        "放她回去": [1],
    }

    j = JiangHuDream(d, name, ins_id)
    for _ in range(material_quantity):
        if not await j.begin_success():
            break

        for day in range(duration + 1):
            day = await j.next_day(day)
            if day is None:
                return

            if event_id := d.find(r'event_id=(\d+)">战斗\(等级2\)'):
                if not await j.choose_fight(day, event_id):
                    await j.end_memories()
                    return
            elif event_ids := d.findall(r'event_id=(\d+)">战斗\(等级1\)'):
                if day in {2, 4}:
                    event_id = event_ids[-1]
                else:
                    event_id = event_ids[0]
                if not await j.choose_fight(day, event_id):
                    await j.end_memories()
                    return
            elif event_ids := d.findall(r'event_id=(\d+)">奇遇\(等级2\)'):
                if day == 5:
                    event_id = event_ids[-1]
                else:
                    event_id = event_ids[0]
                adventure_ids = []
                for k, _ids in adventur.items():
                    if k in d.html:
                        adventure_ids = _ids
                        break
                await j.choose_adventure(day, event_id, adventure_ids)
            elif event_id := d.find(r'event_id=(\d+)">奇遇\(等级1\)'):
                if "转一次" in d.html:
                    adventure_ids = [3]
                elif "漩涡1" in d.html:
                    adventure_ids = [1]
                else:
                    adventure_ids = []
                await j.choose_adventure(day, event_id, adventure_ids)
            else:
                await j.choose_store()
        await j.end_memories()


async def 倚天屠龙归我心(
    d: DaLeDou, name: str, ins_id: str, material_quantity: int, duration: int
):
    j = JiangHuDream(d, name, ins_id)
    for _ in range(material_quantity):
        if not await j.begin_success():
            break

        for day in range(duration + 1):
            day = await j.next_day(day)
            if day is None:
                return

            if event_id := d.find(r'event_id=(\d+)">战斗\(等级2\)'):
                if not await j.choose_fight(day, event_id):
                    await j.end_memories()
                    return
            elif event_id := d.find(r'event_id=(\d+)">战斗\(等级1\)'):
                if not await j.choose_fight(day, event_id):
                    await j.end_memories()
                    return
            elif event_id := d.find(r'event_id=(\d+)">奇遇\(等级2\)'):
                if day in {1, 3, 7}:
                    # 前辈、开始回忆、狠心离去
                    adventure_ids = [1]
                elif day in {6, 8}:
                    # 昏昏沉沉、独自神伤
                    adventure_ids = [3]
                else:
                    adventure_ids = []
                await j.choose_adventure(day, event_id, adventure_ids)
                continue
            await j.choose_store()
        await j.end_memories()


async def 神雕侠侣(
    d: DaLeDou, name: str, ins_id: str, material_quantity: int, duration: int
):
    j = JiangHuDream(d, name, ins_id)
    for _ in range(material_quantity):
        if not await j.begin_success():
            break

        for day in range(duration + 1):
            day = await j.next_day(day)
            if day is None:
                return

            if event_id := d.find(r'event_id=(\d+)">战斗\(等级2\)'):
                if not await j.choose_fight(day, event_id):
                    await j.end_memories()
                    return
            if event_id := d.find(r'event_id=(\d+)">奇遇\(等级2\)'):
                # 奇遇 ->笼络侠客
                await j.choose_adventure(day, event_id, [3])
            await j.choose_store()
        await j.end_memories()


async def 雪山藏魂(
    d: DaLeDou, name: str, ins_id: str, material_quantity: int, duration: int
):
    is_conversation = False
    j = JiangHuDream(d, name, ins_id)
    for _ in range(material_quantity):
        if not await j.begin_success():
            break

        for day in range(duration + 1):
            day = await j.next_day(day)
            if day is None:
                return

            if day == 4:
                if event_id := d.find(r'event_id=(\d+)">奇遇\(等级2\)'):
                    # 奇遇 -> 尝试交谈（获得银狐玩偶） -> 询问大侠
                    is_conversation = True
                    await j.choose_adventure(day, event_id, [2, 2])
                    continue

            if event_ids := d.findall(r'event_id=(\d+)">战斗\(等级2\)'):
                if day in {2, 5}:
                    event_id = event_ids[-1]
                else:
                    event_id = event_ids[0]
                if not await j.choose_fight(day, event_id):
                    await j.end_memories()
                    return
            elif event_id := d.find(r'event_id=(\d+)">奇遇\(等级2\)'):
                if day == 1:
                    # 捉迷藏
                    adventure_ids = [1]
                elif day == 6:
                    if is_conversation:
                        # 飞书（需银狐玩偶）
                        adventure_ids = [1]
                    else:
                        # 刀剑归真
                        adventure_ids = [2]
                else:
                    adventure_ids = []
                await j.choose_adventure(day, event_id, adventure_ids)
            await j.choose_store()
        await j.end_memories()


async def 桃花自古笑春风(
    d: DaLeDou, name: str, ins_id: str, material_quantity: int, duration: int
):
    j = JiangHuDream(d, name, ins_id)
    for _ in range(material_quantity):
        if not await j.begin_success():
            break

        for day in range(duration + 1):
            day = await j.next_day(day)
            if day is None:
                return

            if event_ids := d.findall(r'event_id=(\d+)">战斗\(等级2\)'):
                event_id = event_ids[-1]
                if not await j.choose_fight(day, event_id):
                    await j.end_memories()
                    return
            elif event_id := d.find(r'event_id=(\d+)">奇遇\(等级2\)'):
                if day in {1, 7}:
                    # 过去看看 -> 以西湖来对
                    # 摸黑进入 -> 纯路人
                    adventure_ids = [2, 2]
                elif day == 5:
                    # 我的
                    adventure_ids = [2]
                else:
                    adventure_ids = []
                await j.choose_adventure(day, event_id, adventure_ids)
        await j.end_memories()


async def 战乱襄阳(
    d: DaLeDou, name: str, ins_id: str, material_quantity: int, duration: int
):
    j = JiangHuDream(d, name, ins_id)
    for _ in range(material_quantity):
        if not await j.begin_success():
            break

        for day in range(duration + 1):
            day = await j.next_day(day)
            if day is None:
                return

            if event_ids := d.findall(r'event_id=(\d+)">战斗\(等级2\)'):
                event_id = event_ids[-1]
                if not await j.choose_fight(day, event_id):
                    await j.end_memories()
                    return
            elif event_id := d.find(r'event_id=(\d+)">奇遇\(等级2\)'):
                if day == 4:
                    # 向左突围 > 周遭探查 > 捣毁粮仓
                    adventure_ids = [1, 1, 1]
                else:
                    adventure_ids = []
                await j.choose_adventure(day, event_id, adventure_ids)
        await j.end_memories()


async def 天涯浪子(
    d: DaLeDou, name: str, ins_id: str, material_quantity: int, duration: int
):
    j = JiangHuDream(d, name, ins_id)
    for _ in range(material_quantity):
        if not await j.begin_success():
            break

        for day in range(duration + 1):
            day = await j.next_day(day)
            if day is None:
                return

            if event_ids := d.findall(r'event_id=(\d+)">战斗'):
                event_id = event_ids[-1]
                if not await j.choose_fight(day, event_id):
                    await j.end_memories()
                    return
            elif event_id := d.find(r'event_id=(\d+)">奇遇'):
                if day == 1:
                    # 问其身份 -> 锦囊2
                    adventure_ids = [1, 2]
                elif day == 2:
                    # 重金求见 -> 相约明日
                    adventure_ids = [2, 2]
                elif day == 3:
                    # 阁楼3
                    adventure_ids = [3]
                elif day == 4:
                    # 结为姐弟
                    adventure_ids = [2]
                elif day == 5:
                    # 筹备计划 -> 是
                    adventure_ids = [2, 1]
                elif day == 6:
                    # 锦囊1
                    adventure_ids = [1]
                else:
                    adventure_ids = []
                await j.choose_adventure(day, event_id, adventure_ids)
        await j.end_memories()


async def 全真古墓意难平(
    d: DaLeDou, name: str, ins_id: str, material_quantity: int, duration: int
):
    j = JiangHuDream(d, name, ins_id)
    for _ in range(material_quantity):
        if not await j.begin_success():
            break

        for day in range(duration + 1):
            day = await j.next_day(day)
            if day is None:
                return

            if event_id := d.find(r'event_id=(\d+)">战斗\(等级2\)'):
                if not await j.choose_fight(day, event_id):
                    await j.end_memories()
                    return
            elif event_id := d.find(r'event_id=(\d+)">战斗\(等级1\)'):
                if not await j.choose_fight(day, event_id):
                    await j.end_memories()
                    return
            elif day == 1:
                # 奇遇1 -> 宅家乐斗
                await j.choose_adventure(day, "1", [2])
            elif day == 3:
                # 奇遇2 -> 环顾四周
                await j.choose_adventure(day, "1", [1])
            elif day == 7:
                # 奇遇2 -> 坚持本心 -> 李莫愁
                await j.choose_adventure(day, "1", [2, 2])
            elif day == 2:
                if event_id := d.find(r'event_id=(\d+)">奇遇\(等级1\)'):
                    # 奇遇1 -> 全真剑法
                    await j.choose_adventure(day, event_id, [3])
                elif event_id := d.find(r'event_id=(\d+)">奇遇\(等级2\)'):
                    # 奇遇2 -> 同意约战
                    await j.choose_adventure(day, event_id, [1])
                else:
                    await j.choose_store()
            elif day == 5:
                if event_id := d.find(r'event_id=(\d+)">奇遇\(等级1\)'):
                    # 奇遇1 -> 暂且撤退
                    await j.choose_adventure(day, event_id, [2])
                elif event_id := d.find(r'event_id=(\d+)">奇遇\(等级2\)'):
                    # 奇遇2 -> 切磋武功
                    await j.choose_adventure(day, event_id, [1])
                else:
                    await j.choose_store()
            elif day == 6:
                if event_id := d.find(r'event_id=(\d+)">奇遇\(等级1\)'):
                    # 奇遇1 -> 暂且撤退
                    await j.choose_adventure(day, event_id, [2])
                else:
                    await j.choose_store()

        await j.end_memories()


async def 南海有岛名侠客(
    d: DaLeDou, name: str, ins_id: str, material_quantity: int, duration: int
):
    j = JiangHuDream(d, name, ins_id)
    for _ in range(material_quantity):
        if not await j.begin_success():
            break

        for day in range(duration + 1):
            day = await j.next_day(day)
            if day is None:
                return

            if event_ids := d.findall(r'event_id=(\d+)">战斗\(等级2\)'):
                event_id = event_ids[-1]
                if not await j.choose_fight(day, event_id):
                    await j.end_memories()
                    return
            elif event_id := d.find(r'event_id=(\d+)">奇遇\(等级2\)'):
                if day in {1, 5}:
                    # 即刻前往 / 采摘野果（30金币）
                    adventure_ids = [1]
                elif day in {6, 8}:
                    # 龙岛主 -> 岛中闲逛（80金币）
                    adventure_ids = [1, 2]
                else:
                    adventure_ids = []
                await j.choose_adventure(day, event_id, adventure_ids)
        await j.end_memories()


async def 老鹅的圣诞冒险(
    d: DaLeDou, name: str, ins_id: str, material_quantity: int, duration: int
):
    j = JiangHuDream(d, name, ins_id)
    for _ in range(material_quantity):
        if not await j.begin_success():
            break

        for day in range(duration + 1):
            day = await j.next_day(day)
            if day is None:
                return

            if event_ids := d.findall(r'event_id=(\d+)">战斗'):
                if day == 3:
                    event_id = event_ids[1]
                else:
                    event_id = event_ids[0]
                if not await j.choose_fight(day, event_id):
                    await j.end_memories()
                    return
            elif event_id := d.find(r'event_id=(\d+)">奇遇'):
                if day == 1:
                    # 喝口酒（30金币，血量-20%）
                    adventure_ids = [1]
                elif day == 2:
                    # 要挟清官（30金币，血量-30）
                    adventure_ids = [3]
                elif day == 4:
                    if "继续前行" in d.html:
                        # 继续前行 -> 认真搜寻（25金币）
                        adventure_ids = [1, 1]
                    elif "路线1" in d.html:
                        # 路线1（血量+10% / 10金币，血量-10%）
                        adventure_ids = [1]
                    elif "视而不见" in d.html:
                        # 视而不见（无 / 血量-10%）
                        adventure_ids = [2]
                    else:
                        adventure_ids = []
                elif day == 5:
                    # 抓住麋鹿 -> 圣诞祝福（复活你的一名侠士）
                    adventure_ids = [2, 2]
                else:
                    adventure_ids = []
                await j.choose_adventure(day, event_id, adventure_ids)
        await j.end_memories()


async def 世外桃源梦一场(
    d: DaLeDou, name: str, ins_id: str, material_quantity: int, duration: int
):
    j = JiangHuDream(d, name, ins_id)
    for _ in range(material_quantity):
        if not await j.begin_success():
            break

        for day in range(duration + 1):
            day = await j.next_day(day)
            if day is None:
                return

            if event_ids := d.findall(r'event_id=(\d+)">战斗\(等级2\)'):
                if day in {2, 3}:
                    event_id = event_ids[-1]
                else:
                    event_id = event_ids[0]
                if not await j.choose_fight(day, event_id):
                    await j.end_memories()
                    return
            elif event_id := d.find(r'event_id=(\d+)">奇遇\(等级2\)'):
                if day == 1:
                    # 向下望去（血量-5） -> 向下望去（血量-5）
                    adventure_ids = [2, 2]
                elif day == 6:
                    # 强势出手（势不可挡buff：力量+20%）
                    adventure_ids = [1]
                else:
                    adventure_ids = []
                await j.choose_adventure(day, event_id, adventure_ids)
        await j.end_memories()


async def 中原武林之危(
    d: DaLeDou, name: str, ins_id: str, material_quantity: int, duration: int
):
    j = JiangHuDream(d, name, ins_id)
    for _ in range(material_quantity):
        if not await j.begin_success():
            break

        for day in range(duration + 1):
            day = await j.next_day(day)
            if day is None:
                return

            if event_ids := d.findall(r'event_id=(\d+)">战斗'):
                event_id = event_ids[-1]
                if await j.choose_fight(day, event_id):
                    continue
                await j.end_memories()
                return
        await j.end_memories()


@register()
async def 江湖长梦(d: DaLeDou):
    # 江湖长梦
    await d.get("cmd=jianghudream")
    ins_data = d.findall(r'id=(\d+)">(.*?)<')
    if not ins_data:
        d.log("无法获取副本id")
        return

    config: dict[str, dict] = d.config("江湖长梦")
    for name, data_dict in config.items():
        enabled: bool = data_dict["enabled"]
        if not enabled:
            continue
        material_name: str = data_dict["material_name"]
        material_id: int = data_dict["material_id"]

        for ins_id, copy_name in ins_data:
            if name != copy_name:
                continue

            await d.get(f"cmd=jianghudream&op=showCopyInfo&id={ins_id}")
            duration = d.find(r"副本时长：(\d+)")
            if duration is None:
                d.log(f"{name} -> 获取副本时长失败")
                break

            if "常规副本" not in d.html:
                year = d.find(r"-(\d+)年")
                month = d.find(r"-\d+年(\d+)月")
                day = d.find(r"-\d+年\d+月(\d+)日")
                if year is None or month is None or day is None:
                    d.log(f"{name} -> 获取结束日期失败")
                    return

                # 结束前一天日期
                end_date = DateTime.get_offset_date(
                    2000 + int(year), int(month), int(day)
                )
                if DateTime.current_date() > end_date:
                    d.log(f"{name} -> 不在开启时间内")
                    continue

            material_quantity = await c_get_material_quantity(d, material_id)
            if material_quantity == 0:
                d.log(f"{name} -> {material_name}不足")
                continue

            await globals()[name](d, name, ins_id, material_quantity, int(duration))


@register()
async def 深渊之潮(d: DaLeDou):
    await c_帮派巡礼(d)
    await c_深渊秘境(d)


@register()
async def 侠客岛(d: DaLeDou):
    """领取侠客行奖励"""
    # 侠客行
    await d.get("cmd=knight_island&op=viewmissionindex")
    for p in d.findall(r"getmissionreward&amp;pos=(\d+)"):
        # 领取
        await d.get(f"cmd=knight_island&op=getmissionreward&pos={p}")
        d.log(d.find(r"斗豆）<br />(.*?)<br />"))


@register()
async def 龙凰之境(d: DaLeDou):
    await c_龙凰论武(d)


@register()
async def 背包(d: DaLeDou):
    use: list[str] = d.config("背包.使用")
    data = []
    for p in range(1, 50):
        d.log(f"第 {p} 页")
        await d.get(f"cmd=store&store_type=0&page={p}")
        data += d.findall(r'id=(\d+)">(.*?)</a>数量：(\d+)')
        if "下页" not in d.html:
            break
    for _id, material_name, quantity in data:
        if not any(u in material_name for u in use):
            continue
        for _ in range(int(quantity)):
            # 使用
            await d.get(f"cmd=use&id={_id}")
            if "您使用了" in d.html or "你打开" in d.html:
                d.log(d.find())
                continue
            # 使用规则
            # 提示信息
            d.log(f"{material_name}（{_id}） -> {d.find(r'】</p><p>(.*?)<')}")
            break


@register()
async def 镶嵌(d: DaLeDou):
    """每周四升级（碎 > 1 > 2 > 3 > 4）"""
    if DateTime.week() != 4:
        return

    for p in range(1, 8):
        await d.get(f"cmd=upgradepearl&type=1&pearl_type={p}")
        data_1 = d.findall(r"<br />.*?:(\d+), (\d+).*?exchangetype=(\d+)")
        data_2 = d.findall(r"><br />(.*?):(\d+), (\d+).*?pearl_id=(\d+)")

        for need, possess, e in data_1:
            for _ in range(int(possess) // int(need)):
                # 魂珠碎片 -> 1
                await d.get(f"cmd=upgradepearl&type=6&exchangetype={e}")
                d.log(d.find(r"魂珠升级</p><p>(.*?)</p>"))

        for material_name, need, possess, _id in data_2[:3]:
            for _ in range(int(possess) // int(need)):
                # 1 -> 2 -> 3 -> 4
                await d.get(f"cmd=upgradepearl&type=3&pearl_id={_id}&pearl_type={p}")
                d.log(f"{material_name} -> {d.find(r'魂珠升级</p><p>(.*?)<')}")


async def 普通合成(d: DaLeDou):
    for p in range(1, 20):
        # 下一页
        await d.get(f"cmd=weapongod&sub=12&stone_type=0&quality=0&page={p}")
        data = d.findall(r"拥有：(\d+)/(\d+).*?stone_id=(\d+)")
        for possess, need, _id in data:
            for _ in range(int(possess) // int(need)):
                # 普通合成
                await d.get(f"cmd=weapongod&sub=13&stone_id={_id}")
                d.log(d.find(r"背包<br /></p>(.*?)<"))

        if "下一页" not in d.html:
            break


async def 符石分解(d: DaLeDou):
    """仅分解I、II类符石"""
    data = []
    for p in range(1, 10):
        d.log(f"查找符石分解第 {p} 页")
        # 下一页
        await d.get(f"cmd=weapongod&sub=9&stone_type=0&page={p}")
        data += d.findall(r">\d+. (.*?) \(数量:(\d+).*?stone_id=(\d+)")
        if "下一页" not in d.html:
            break

    for material_name, num, _id in data:
        # 检查后缀是否为 I 或 II（排除 III）
        if (
            material_name.endswith("I")
            and not material_name.endswith("II")
            and not material_name.endswith("III")
        ):
            # 分解I
            await d.get(f"cmd=weapongod&sub=11&stone_id={_id}&num={num}&i_p_w=num%7C")
            d.log(f"{material_name} -> {d.find(r'背包</a><br /></p>(.*?)<')}")
        elif material_name.endswith("II") and not material_name.endswith("III"):
            # 分解II
            await d.get(f"cmd=weapongod&sub=11&stone_id={_id}&num={num}&i_p_w=num%7C")
            d.log(f"{material_name} -> {d.find(r'背包</a><br /></p>(.*?)<')}")


async def 符石打造(d: DaLeDou):
    # 符石
    await d.get("cmd=weapongod&sub=7")
    count = d.find(r"符石水晶：(\d+)")
    if count is None:
        d.log("获取符石水晶数量失败")
        return

    quotient, remainder = divmod(int(count), 60)
    for _ in range(quotient):
        # 打造十次
        await d.get("cmd=weapongod&sub=8&produce_type=1&times=10")
        d.log(d.find(r"背包</a><br /></p>(.*?)<"))
    for _ in range(remainder // 6):
        # 打造一次
        await d.get("cmd=weapongod&sub=8&produce_type=1&times=1")
        d.log(d.find(r"背包</a><br /></p>(.*?)<"))


@register()
async def 神匠坊(d: DaLeDou):
    if DateTime.week() != 4:
        return

    await 普通合成(d)
    await 符石分解(d)
    await 符石打造(d)


@register()
async def 每日宝箱(d: DaLeDou):
    if DateTime.week() != 4:
        return

    # 每日宝箱
    await d.get("cmd=dailychest")
    for t, possess, need in d.findall(r'type=(\d+)">打开.*?(\d+)/(\d+)'):
        for _ in range(min(10, int(possess) // int(need))):
            # 打开
            await d.get(f"cmd=dailychest&op=open&type={t}")
            d.log(d.find(r"说明</a><br />(.*?)<"))
            if "今日开宝箱次数已达上限" in d.html:
                break


@register()
async def 猜单双(d: DaLeDou):
    # 猜单双
    await d.get("cmd=oddeven")
    for _ in range(5):
        value = d.findall(r'value=(\d+)">.*?数')
        if not value:
            d.log("猜单双已经结束")
            break

        value = random.choice(value)
        # 单数1 双数2
        await d.get(f"cmd=oddeven&value={value}")
        d.log(d.find())


@register()
async def 煮元宵(d: DaLeDou):
    # 煮元宵
    await d.get("cmd=yuanxiao2014")
    for _ in range(4):
        # 开始烹饪
        await d.get("cmd=yuanxiao2014&op=1")
        if "领取烹饪次数" in d.html:
            d.log("没有烹饪次数了")
            break

        for _ in range(20):
            maturity = d.find(r"当前元宵成熟度：(\d+)")
            if maturity is None:
                d.log("获取元宵成熟度失败")
                return
            if int(maturity) < 96:
                # 继续加柴
                await d.get("cmd=yuanxiao2014&op=2")
                continue
            # 赶紧出锅
            await d.get("cmd=yuanxiao2014&op=3")
            d.log(d.find(r"活动规则</a><br /><br />(.*?)。"))
            break


@register()
async def 元宵节(d: DaLeDou):
    # 领取
    await d.get("cmd=newAct&subtype=101&op=1")
    d.log(d.find(r"】</p>(.*?)<br />"))
    # 领取形象卡
    await d.get("cmd=newAct&subtype=101&op=2&index=0")
    d.log(d.find(r"】</p>(.*?)<br />"))


@register()
async def 刮刮卡(d: DaLeDou):
    for _id in range(3):
        # 领取
        await d.get(f"cmd=newAct&subtype=148&op=2&id={_id}")
        d.log(d.find(r"奖池预览</a><br /><br />(.*?)<br />"))

    for _ in range(20):
        # 刮卡
        await d.get("cmd=newAct&subtype=148&op=1")
        d.log(d.find(r"奖池预览</a><br /><br />(.*?)<br />"))
        if "您没有刮刮卡了" in d.html:
            break
        elif "不在刮奖时间不能刮奖" in d.html:
            break


@register()
async def 娃娃机(d: DaLeDou):
    """仅免费抓取"""
    # 娃娃机
    await d.get("cmd=newAct&subtype=124&op=0")
    if "免费次数：1/1" not in d.html:
        d.log("没有免费抓取次数")
        return

    # 抓取一次
    await d.get("cmd=newAct&subtype=124&op=1")
    d.log(d.find())


@register()
async def 吉利兑(d: DaLeDou):
    # 吉利兑
    await d.get("cmd=geelyexchange")
    for _id in d.findall(r'id=(\d+)">领取</a>'):
        # 领取
        await d.get(f"cmd=geelyexchange&op=GetTaskReward&id={_id}")
        d.log(d.find(r"】<br /><br />(.*?)<br /><br />"))

    month = d.find(r"至(\d+)月")
    day = d.find(r"至\d+月(\d+)日")
    if month is None or day is None:
        d.log("获取结束日期失败")
        return

    # 结束前一天日期
    end_date = DateTime.get_offset_date(DateTime.year(), int(month), int(day))
    if DateTime.current_date() != end_date:
        return

    exchange_config: dict[int, dict] = d.config("吉利兑.exchange")
    for _id, item in exchange_config.items():
        material_name: str = item["material_name"]
        quantity: int = item["quantity"]
        if quantity <= 0:
            continue
        for _ in range(quantity):
            # 兑换
            await d.get(f"cmd=geelyexchange&op=ExchangeProps&id={_id}")
            d.log(f"{material_name}*1 -> {d.find(r'】<br /><br />(.*?)<br />')}")
            if "你的精魄不足，快去完成任务吧~" in d.html:
                break
            elif "该物品已达兑换上限~" in d.html:
                break


@register()
async def 激运牌(d: DaLeDou):
    for _id in [0, 1]:
        # 领取
        await d.get(f"cmd=realgoods&op=getTaskReward&id={_id}")
        d.log(d.find(r"<br /><br />(.*?)<br />"))

    count = d.find(r"我的激运牌：(\d+)")
    if count is None:
        d.log("获取激运牌次数失败")
        return

    for _ in range(int(count)):
        # 我要翻牌
        await d.get("cmd=realgoods&op=lotteryDraw")
        d.log(d.find(r"<br /><br />(.*?)<br />"))


@register()
async def 回忆录(d: DaLeDou):
    """每周四领取回忆礼包、进阶礼包"""
    if DateTime.week() != 4:
        return

    for _id in range(1, 11):
        # 领取
        await d.get(f"cmd=newAct&subtype=171&op=3&id={_id}")
        d.log(d.find(r"6点<br />(.*?)<br />"))


@register()
async def 愚人节(d: DaLeDou):
    for _ in range(5):
        # 提升一次
        await d.get("cmd=foolsday&gb_id=5")
        d.log(d.find(r"\d+<br /><br />(.*?)<"))
        if "提升20幸运值" not in d.html:
            break

    # 礼包1、礼包2
    for _id in d.findall(r'gb_id=(\d+)">拆开'):
        # 拆开
        await d.get(f"cmd=foolsday&gb_id={_id}")
        if "确认" in d.html:
            d.log("今日幸运度较低，是否确认拆开礼包？")
            await d.get("cmd=foolsday&gb_id=1")
        d.log(d.find(r"\d+<br /><br />(.*?)<"))


async def 疯狂许愿(d: DaLeDou, link_text: str):
    # 儿童节、开学季
    await d.get("cmd=newAct&subtype=130")
    if "取消返回" in d.html:
        # 取消返回
        await d.get("cmd=newAct&subtype=130&op=6")

    if "op=2" not in d.html:
        d.log("你已经领取过了", link_text)
        return

    config = d.config(f"{link_text}.id")
    if config is None:
        d.log(f"你没有设置{link_text}", link_text)
        return

    t, s = d.findall(r"type=(\d+)&sub_type=(\d+)", config)[0]
    # 选择分类
    await d.get(f"cmd=newAct&subtype=130&op=2&type={t}")
    # 选择
    await d.get(f"cmd=newAct&subtype=130&op=3&type={t}&sub_type={s}")
    d.log(d.find(r"】</p>(.*?)<"), link_text)


@register()
async def 儿童节(d: DaLeDou):
    await 疯狂许愿(d, "儿童节")


@register()
async def 开学季(d: DaLeDou):
    await 疯狂许愿(d, "开学季")


@register()
async def 大笨钟(d: DaLeDou):
    await c_大笨钟(d)


@register()
async def 幸运金蛋(d: DaLeDou):
    await c_幸运金蛋(d)


@register()
async def 客栈同福(d: DaLeDou):
    await c_客栈同福(d)


async def 斗神塔(d: DaLeDou, link_text: str):
    name = f"{link_text}-斗神塔"
    count: int = d.config(f"{link_text}.斗神塔")
    if count <= 0:
        d.log(f"你设置斗神塔挑战次数为{count}", name)
        return

    second = await c_get_doushenta_cd(d)
    for _ in range(count):
        # 自动挑战
        await d.get("cmd=towerfight&type=11")
        d.log(d.find(), name)
        if "结束挑战" in d.html:
            await asyncio.sleep(second)
            # 结束挑战
            await d.get("cmd=towerfight&type=7")
            d.log(d.find(), name)
        else:
            break


@register()
async def 节日福利(d: DaLeDou):
    await 斗神塔(d, "节日福利")


@register()
async def 双旦福利(d: DaLeDou):
    await 斗神塔(d, "双旦福利")


@register()
async def 金秋福利(d: DaLeDou):
    await 斗神塔(d, "金秋福利")


@register()
async def 春节福利(d: DaLeDou):
    await 斗神塔(d, "春节福利")


@register()
async def 新春拜年(d: DaLeDou):
    # 新春拜年
    await d.get("cmd=newAct&subtype=147")
    if "op=3" not in d.html:
        d.log("没有礼物收取")
        return

    # 收取礼物
    await d.get("cmd=newAct&subtype=147&op=3")
    d.log(d.find(r"祝您：.*?<br /><br />(.*?)<br />"))


@register()
async def 神魔转盘(d: DaLeDou):
    """仅免费抽奖一次"""
    # 神魔转盘
    await d.get("cmd=newAct&subtype=88&op=0")
    if "免费抽奖一次" not in d.html:
        d.log("没有免费抽奖次数了")
        return

    # 幸运抽奖
    await d.get("cmd=newAct&subtype=88&op=1")
    d.log(d.find())


@register()
async def 乐斗驿站(d: DaLeDou):
    # 领取
    await d.get("cmd=newAct&subtype=167&op=2")
    d.log(d.find())


@register()
async def 幸运转盘(d: DaLeDou):
    # 转动转盘
    await d.get("cmd=newAct&subtype=57&op=roll")
    d.log(d.find(r"0<br /><br />(.*?)<br />"))


@register()
async def 冰雪企缘(d: DaLeDou):
    # 冰雪企缘
    await d.get("cmd=newAct&subtype=158&op=0")
    gift = d.findall(r"gift_type=(\d+)")
    if not gift:
        d.log("没有礼包领取")
        return

    for _id in gift:
        # 领取
        await d.get(f"cmd=newAct&subtype=158&op=2&gift_type={_id}")
        d.log(d.find())


@register()
async def 甜蜜夫妻(d: DaLeDou):
    """
    如果拥有夫妻关系则每天领取夫妻甜蜜好礼
    如果单身则每天领取单身鹅鼓励好礼
    """
    # 甜蜜夫妻
    await d.get("cmd=newAct&subtype=129")
    for f in d.findall(r"flag=(\d+)"):
        # 领取
        await d.get(f"cmd=newAct&subtype=129&op=1&flag={f}")
        d.log(d.find(r"】</p>(.*?)<br />"))


@register()
async def 乐斗菜单(d: DaLeDou):
    # 乐斗菜单
    await d.get("cmd=menuact")
    if gift := d.find(r"套餐.*?gift=(\d+).*?点单</a>"):
        # 点单
        await d.get(f"cmd=menuact&sub=1&gift={gift}")
        d.log(d.find(r"哦！<br /></p>(.*?)<br />"))


@register()
async def 周周礼包(d: DaLeDou):
    # 周周礼包
    await d.get("cmd=weekgiftbag&sub=0")
    if _id := d.find(r';id=(\d+)">领取'):
        # 领取
        await d.get(f"cmd=weekgiftbag&sub=1&id={_id}")
        d.log(d.find())


@register()
async def 登录有礼(d: DaLeDou):
    # 登录有礼
    await d.get("cmd=newAct&subtype=56")
    # 登录奖励
    if g := d.find(r"gift_type=1.*?gift_index=(\d+)"):
        # 领取
        await d.get(f"cmd=newAct&subtype=56&op=draw&gift_type=1&gift_index={g}")
        d.log(d.find())
    # 额外奖励
    if g := d.find(r"gift_type=2.*?gift_index=(\d+)"):
        # 领取
        await d.get(f"cmd=newAct&subtype=56&op=draw&gift_type=2&gift_index={g}")
        d.log(d.find())


@register()
async def 活跃礼包(d: DaLeDou):
    """领取50、80活跃礼包"""
    for p in ["1", "2"]:
        # 领取
        await d.get(f"cmd=newAct&subtype=94&op={p}")
        d.log(d.find(r"】.*?<br />(.*?)<br />"))


@register()
async def 清明上香(d: DaLeDou):
    # 清明上香
    await d.get("cmd=newAct&subtype=142")
    for _id, count in d.findall(r"id=(\d+).*?（(\d+)）"):
        for _ in range(int(count)):
            # 领取檀木香 | 龙涎香
            await d.get(f"cmd=newAct&subtype=142&op=1&id={_id}")
            d.log(d.find())


@register()
async def 徽章战令(d: DaLeDou):
    # 领取每日礼包
    await d.get("cmd=badge&op=1")
    d.log(d.find())


async def 生肖福卡_好友赠卡(d: DaLeDou):
    # 好友赠卡
    await d.get("cmd=newAct&subtype=174&op=4")
    for name, qq, card_id in d.findall(r"送您(.*?)\*.*?oppuin=(\d+).*?id=(\d+)"):
        # 领取
        await d.get(f"cmd=newAct&subtype=174&op=6&oppuin={qq}&card_id={card_id}")
        d.log(d.find())


async def 生肖福卡_分享福卡(d: DaLeDou):
    qq: int = d.config("生肖福卡.QQ")
    if qq is None:
        return

    # 生肖福卡
    await d.get("cmd=newAct&subtype=174")
    pattern = "[子丑寅卯辰巳午未申酉戌亥][鼠牛虎兔龙蛇马羊猴鸡狗猪]"
    data = d.findall(rf"({pattern})\s+(\d+).*?id=(\d+)")
    _, max_number, _id = max(data, key=lambda x: int(x[1]))
    if int(max_number) >= 2:
        # 分享福卡
        await d.get(f"cmd=newAct&subtype=174&op=5&oppuin={qq}&card_id={_id}&confirm=1")
        d.log(d.find(r"~<br /><br />(.*?)<br />"))


async def 生肖福卡_领取福卡(d: DaLeDou):
    # 生肖福卡
    await d.get("cmd=newAct&subtype=174")
    for _id in d.findall(r"task_id=(\d+)"):
        # 领取
        await d.get(f"cmd=newAct&subtype=174&op=7&task_id={_id}")
        d.log(d.find(r"~<br /><br />(.*?)<br />"))


async def 生肖福卡_合卡(d: DaLeDou):
    # 生肖福卡
    await d.get("cmd=newAct&subtype=174")
    # 合卡结束日期
    month, day = d.findall(r"合卡时间：.*?至(\d+)月(\d+)日")[0]
    if DateTime.month() == int(month) and DateTime.day() == int(day):
        return

    # 合成周年福卡
    await d.get("cmd=newAct&subtype=174&op=8")
    d.log(d.find(r"。<br /><br />(.*?)<br />"))


async def 生肖福卡_抽奖(d: DaLeDou):
    # 生肖福卡
    await d.get("cmd=newAct&subtype=174")
    # 兑奖开始日期
    month, day = d.findall(r"兑奖时间：(\d+)月(\d+)日")[0]
    if not (DateTime.month() == int(month) and DateTime.day() >= int(day)):
        return

    # 分斗豆
    await d.get("cmd=newAct&subtype=174&op=9")
    d.log(d.find(r"。<br /><br />(.*?)<br />"))

    # 抽奖
    await d.get("cmd=newAct&subtype=174&op=2")
    for _id, data in d.findall(r"id=(\d+).*?<br />(.*?)<br />"):
        numbers = d.findall(r"\d+", data)
        min_number = min(numbers, key=lambda x: int(x))
        for _ in range(int(min_number)):
            # 春/夏/秋/冬宵抽奖
            await d.get(f"cmd=newAct&subtype=174&op=10&id={_id}&confirm=1")
            if "您还未合成周年福卡" in d.html:
                # 合卡时间已过
                # 继续抽奖
                await d.get(f"cmd=newAct&subtype=174&op=10&id={_id}")
            d.log(d.find(r"幸运抽奖<br /><br />(.*?)<br />"))


@register()
async def 生肖福卡(d: DaLeDou):
    await 生肖福卡_好友赠卡(d)
    await 生肖福卡_分享福卡(d)
    await 生肖福卡_领取福卡(d)

    if DateTime.week() != 4:
        return

    await 生肖福卡_合卡(d)
    await 生肖福卡_抽奖(d)


@register()
async def 长安盛会(d: DaLeDou):
    """
    盛会豪礼: 点击领取  id  1
    签到宝箱: 点击领取  id  2
    全民挑战: 点击参与  id  3，4，5
    """
    # 5089真黄金卷轴 3036黄金卷轴
    await d.get("cmd=newAct&subtype=118&op=2&select_id=5089")
    for _id in d.findall(r"op=1&amp;id=(\d+)"):
        if _id in ["1", "2"]:
            # 点击领取
            await d.get(f"cmd=newAct&subtype=118&op=1&id={_id}")
            d.log(d.find())
        else:
            count = d.find(r"剩余转动次数：(\d+)")
            if count is None:
                d.log("获取剩余转动次数失败")
                return
            for _ in range(int(count)):
                # 点击参与
                await d.get(f"cmd=newAct&subtype=118&op=1&id={_id}")
                d.log(d.find())


@register()
async def 深渊秘宝(d: DaLeDou):
    """
    三魂秘宝: 每天仅免费抽奖一次
    七魄秘宝: 每天仅免费抽奖一次
    """
    # 深渊秘宝
    await d.get("cmd=newAct&subtype=175")
    t_list = d.findall(r'type=(\d+)&amp;times=1">免费抽奖')
    if not t_list:
        d.log("没有免费抽奖次数了")
        return

    for t in t_list:
        # 领取
        await d.get(f"cmd=newAct&subtype=175&op=1&type={t}&times=1")
        d.log(d.find())


@register()
async def 中秋礼盒(d: DaLeDou):
    # 中秋礼盒
    await d.get("cmd=midautumngiftbag&sub=0")
    for _id in d.findall(r"amp;id=(\d+)"):
        # 领取
        await d.get(f"cmd=midautumngiftbag&sub=1&id={_id}")
        d.log(d.find())
        if "已领取完该系列任务所有奖励" in d.html:
            continue


@register()
async def 双节签到(d: DaLeDou):
    """
    签到奖励: 每天领取一次
    额外奖励金: 截止日前一天领取
    """
    # 领取签到奖励
    await d.get("cmd=newAct&subtype=144&op=1")
    d.log(d.find())

    month = d.find(r"至(\d+)月")
    day = d.find(r"至\d+月(\d+)日")
    if month is None or day is None:
        d.log("获取结束日期失败")
        return

    # 结束前一天日期
    end_date = DateTime.get_offset_date(DateTime.year(), int(month), int(day))
    if DateTime.current_date() == end_date:
        # 奖励金
        await d.get("cmd=newAct&subtype=144&op=3")
        d.log(d.find())


@register()
async def 斗境探秘(d: DaLeDou):
    # 斗境探秘
    await d.get("cmd=newAct&subtype=177")

    # 领取每日探秘奖励
    for _id in d.findall(r"id=(\d+)&amp;type=2"):
        # 领取
        await d.get(f"cmd=newAct&subtype=177&op=2&id={_id}&type=2")
        d.log(d.find(r"】<br /><br />(.*?)<br />"))

    # 领取累计探秘奖励
    for _id in d.findall(r"id=(\d+)&amp;type=1"):
        # 领取
        await d.get(f"cmd=newAct&subtype=177&op=2&id={_id}&type=1")
        d.log(d.find(r"】<br /><br />(.*?)<br />"))


@register()
async def 春联大赛(d: DaLeDou):
    # 开始答题
    await d.get("cmd=newAct&subtype=146&op=1")
    if "您的活跃度不足" in d.html:
        d.log("您的活跃度不足50")
        return

    couplets: dict = d.config("春联大赛")
    for _ in range(3):
        if "今日答题已结束" in d.html:
            d.log("今日答题已结束")
            break

        shang_lian = d.find(r"上联：([^ &]*)")
        d.log(f"上联: {shang_lian}")
        options_A, index_A = d.findall(r"<br />A.(.*?)<.*?index=(\d+)")[0]
        options_B, index_B = d.findall(r"<br />B.(.*?)<.*?index=(\d+)")[0]
        options_C, index_C = d.findall(r"<br />C.(.*?)<.*?index=(\d+)")[0]
        options_dict = {
            options_A: index_A,
            options_B: index_B,
            options_C: index_C,
        }

        if xia_lian := couplets.get(shang_lian):
            index = options_dict[xia_lian]
            # 选择
            await d.get(f"cmd=newAct&subtype=146&op=3&index={index}")
            d.log(f"下联: {xia_lian}")
            # 确定选择
            await d.get("cmd=newAct&subtype=146&op=2")
            d.log(d.find())
        else:
            d.log("题库没有找到对联，请在配置文件更新题库")
            break

    # 领取斗币
    for _id in d.findall(r'id=(\d+)">领取'):
        # 领取
        await d.get(f"cmd=newAct&subtype=146&op=4&id={_id}")
        d.log(d.find())


@register()
async def 预热礼包(d: DaLeDou):
    # 领取
    await d.get("cmd=newAct&subtype=117&op=1")
    d.log(d.find(r"<br /><br />(.*?)<"))


@register()
async def 豪侠出世(d: DaLeDou):
    # 签到好礼
    await d.get("cmd=knightdraw&op=view&sub=signin&ty=free")
    for _id in d.findall(r"giftId=(\d+)"):
        # 领取
        await d.get(f"cmd=knightdraw&op=reqreward&sub=signin&ty=free&giftId={_id}")
        d.log(d.find(r"活动规则</a><br />(.*?)<br />"))


@register()
async def 乐斗游记(d: DaLeDou):
    # 乐斗游记
    await d.get("cmd=newAct&subtype=176")
    # 今日游记任务
    for _id in d.findall(r"task_id=(\d+)"):
        # 领取
        await d.get(f"cmd=newAct&subtype=176&op=1&task_id={_id}")
        d.log(d.find(r"积分。<br /><br />(.*?)<br />"))

    # 一键领取
    await d.get("cmd=newAct&subtype=176&op=5")
    d.log(d.find(r"积分。<br /><br />(.*?)<br />"))

    # 兑换
    count = d.find(r"溢出积分：(\d+)")
    if count is None:
        d.log("获取溢出积分失败")
        return

    quotient, remainder = divmod(int(count), 10)
    for _ in range(quotient):
        # 兑换十次
        await d.get("cmd=newAct&subtype=176&op=2&num=10")
        d.log(d.find(r"积分。<br /><br />(.*?)<br />"))
    for _ in range(remainder):
        # 兑换一次
        await d.get("cmd=newAct&subtype=176&op=2&num=1")
        d.log(d.find(r"积分。<br /><br />(.*?)<br />"))


@register()
async def 喜从天降(d: DaLeDou):
    """活动时间20.00-22.00"""
    # 喜从天降
    await d.get("cmd=newAct&subtype=137")
    count = d.find(r"剩余燃放次数：(\d+)")
    if count is None:
        d.log("获取燃放次数失败")
        return

    for _ in range(int(count)):
        # 点燃烟花
        await d.get("cmd=newAct&subtype=137&op=1")
        d.log(d.find())


@register()
async def 微信兑换(d: DaLeDou):
    if DateTime.week() != 4:
        return

    code: int = d.config("微信兑换.兑换码")
    # 兑换
    await d.get(
        f"cmd=weixin&cdkey={code}&sub=2&zapp_sid=&style=0&channel=0&i_p_w=cdkey|"
    )
    d.log(d.find())


@register()
async def 浩劫宝箱(d: DaLeDou):
    # 老版大乐斗首页
    await d.get("cmd=index&style=1")
    t1 = d.find(r'subtype=(\d+)">浩劫宝箱')

    # 浩劫宝箱
    await d.get(f"cmd=newAct&subtype={t1}")
    if t2 := d.find(r"subtype=(\d+)"):
        # 领取
        await d.get(f"cmd=newAct&subtype={t2}")
        d.log(d.find())


@register()
async def 端午有礼(d: DaLeDou):
    """
    活动期间最多可以得到 4x7=28 个粽子

    index
    3       礼包4: 消耗10粽子得到 淬火结晶*5+真黄金卷轴*5+徽章符文石*5+修为丹*5+境界丹*5+元婴飞仙果*5
    2       礼包3: 消耗8粽子得到 2级日曜石*1+2级玛瑙石*1+2级迅捷石*1+2级月光石*1+2级紫黑玉*1
    1       礼包2: 消耗6粽子得到 阅历羊皮卷*5+无字天书*5+河图洛书*5+还童天书*1
    0       礼包1: 消耗4粽子得到 中体力*2+挑战书*2+斗神符*2
    """
    if DateTime.week() != 4:
        return

    for _ in range(2):
        # 礼包4
        await d.get("cmd=newAct&subtype=121&op=1&index=3")
        d.log(d.find(r"】<br /><br />(.*?)<br />"))
        if "您的端午香粽不足" in d.html:
            break

    # 礼包3
    await d.get("cmd=newAct&subtype=121&op=1&index=2")
    d.log(d.find(r"】<br /><br />(.*?)<br />"))


@register()
async def 圣诞有礼(d: DaLeDou):
    # 圣诞有礼
    await d.get("cmd=newAct&subtype=145")
    for _id in d.findall(r"task_id=(\d+)"):
        # 点亮奖励
        await d.get(f"cmd=newAct&subtype=145&op=1&task_id={_id}")
        d.log(d.find())

    # 连线奖励
    for i in d.findall(r"index=(\d+)"):
        await d.get(f"cmd=newAct&subtype=145&op=2&index={i}")
        d.log(d.find())


@register()
async def 新春礼包(d: DaLeDou):
    for _id in [280, 281, 282]:
        # 领取
        await d.get(f"cmd=xinChunGift&subtype=2&giftid={_id}")
        d.log(d.find())


@register()
async def 登录商店(d: DaLeDou):
    if DateTime.week() != 4:
        return

    t: int = d.config("登录商店.id")
    if t is None:
        d.log("你没有配置兑换物品id")
        return

    for _ in range(5):
        # 兑换5次
        await d.get(f"cmd=newAct&op=exchange&subtype=52&type={t}&times=5")
        d.log(d.find(r"<br /><br />(.*?)<br /><br />"))
    for _ in range(3):
        # 兑换1次
        await d.get(f"cmd=newAct&op=exchange&subtype=52&type={t}&times=1")
        d.log(d.find(r"<br /><br />(.*?)<br /><br />"))


@register()
async def 盛世巡礼(d: DaLeDou):
    if DateTime.week() != 4:
        return

    for s in range(1, 8):
        # 点击进入
        await d.get(f"cmd=newAct&subtype=150&op=2&sceneId={s}")
        if "他已经给过你礼物了" in d.html:
            d.log(f"地点{s}礼物已领取")
        elif s == 7 and ("点击继续" not in d.html):
            d.log(f"地点{s}礼物已领取")
        elif _id := d.find(r"itemId=(\d+)"):
            # 收下礼物
            await d.get(f"cmd=newAct&subtype=150&op=5&itemId={_id}")
            d.log(d.find(r"礼物<br />(.*?)<br />"))


@register("5.1礼包")
async def 五一礼包(d: DaLeDou):
    for _id in range(3):
        # 领取
        await d.get(f"cmd=newAct&subtype=113&op=1&id={_id}")
        d.log(d.find(r"】<br /><br />(.*?)<"))


@register()
async def 好礼提升(d: DaLeDou):
    # 领取
    await d.get("cmd=newAct&subtype=43&op=get")
    d.log(d.find())


@register()
async def 周年祝福(d: DaLeDou):
    for day in range(1, 8):
        await d.get(f"cmd=newAct&subtype=165&op=3&day={day}")
        d.log(d.find())


# ---------------以下大乐斗首页链接文本待定-----------


@register()
async def 年兽大作战(d: DaLeDou):
    # 年兽大作战
    await d.get("cmd=newAct&subtype=170&op=0")
    if "等级不够" in d.html:
        d.log("等级不够，还未开启年兽大作战哦！")
        return

    # 自选武技库
    if choose_count := d.html.count("暂未选择"):
        choose_ids = []
        for t in range(5):
            # 大、中、小、投、技
            await d.get(f"cmd=newAct&subtype=170&op=4&type={t}")
            choose_ids += d.findall(r'id=(\d+)">选择')
            if len(choose_ids) >= choose_count:
                break
        if len(choose_ids) < choose_count:
            d.log("自选武技库数量不够补位")
            return
        for _id in choose_ids[:choose_count]:
            # 选择
            await d.get(f"cmd=newAct&subtype=170&op=7&id={_id}")
            name = d.find(rf'id={_id}">(.*?)<')
            d.log(f"{name}：{d.find()}")

    # 随机武技库
    if "剩余免费随机次数：1" in d.html:
        # 随机
        await d.get("cmd=newAct&subtype=170&op=6")
        d.log(d.find())

    for _ in range(3):
        # 挑战
        await d.get("cmd=newAct&subtype=170&op=8")
        d.log(d.find())
        await asyncio.sleep(0.2)


@register()
async def 新春登录礼(d: DaLeDou):
    # 新春登录礼
    await d.get("cmd=newAct&subtype=99&op=0")
    days = d.findall(r"day=(\d+)")
    if not days:
        d.log("没有礼包领取")
        return

    for day in days:
        # 领取
        await d.get(f"cmd=newAct&subtype=99&op=1&day={day}")
        d.log(d.find())


@register()
async def 爱的同心结(d: DaLeDou):
    config: list[int] = d.config("爱的同心结.QQ")
    if config is not None:
        for uin in config:
            # 赠送
            await d.get(f"cmd=loveknot&sub=3&uin={uin}")
            d.log(d.find())
            if "你当前没有同心结哦" in d.html:
                break

    data = {
        "4016": 2,  # 礼包5
        "4015": 4,  # 礼包4
        "4014": 10,  # 礼包3
        "4013": 16,  # 礼包2
        "4012": 20,  # 礼包1
    }
    for _id, count in data.items():
        for _ in range(count):
            # 兑换
            await d.get(f"cmd=loveknot&sub=2&id={_id}")
            d.log(d.find())
            if "恭喜您兑换成功" not in d.html:
                break


@register()
async def 重阳太白诗会(d: DaLeDou):
    # 领取重阳礼包
    await d.get("cmd=newAct&subtype=168&op=2")
    d.log(d.find(r"<br /><br />(.*?)<br />"))


@register()
async def 五一预订礼包(d: DaLeDou):
    # 5.1预订礼包
    await d.get("cmd=lokireservation")
    if _id := d.find(r"idx=(\d+)"):
        # 领取
        await d.get(f"cmd=lokireservation&op=draw&idx={_id}")
        d.log(d.find(r"<br /><br />(.*?)<"))
    else:
        d.log("没有登录礼包领取")
