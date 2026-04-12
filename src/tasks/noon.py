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


registry = Registry(TaskModule.noon, schedule_time="13:01:00", description="午间任务")
register = registry.register


@register()
async def 邪神秘宝(d: DaLeDou):
    await c_邪神秘宝(d)


@register()
async def 华山论剑(d: DaLeDou):
    """
    每月1~25号挑战，26号领取赛季段位奖励、荣誉兑换
    """
    if not (1 <= DateTime.day() <= 260):
        return

    if DateTime.day() == 26:
        # 领取赛季段位奖励
        await d.get(r"cmd=knightarena&op=drawranking")
        d.log(d.find())

        exchange_config: dict[int, dict] = d.config("华山论剑.exchange")
        for _id, item in exchange_config.items():
            quantity: int = item["quantity"]
            if quantity <= 0:
                continue
            quotient, remainder = divmod(quantity, 10)
            for _ in range(quotient):
                await d.get(f"cmd=knightarena&op=exchange&id={_id}&times=10")
                d.log(d.find())
                if "成功" not in d.html:
                    break
            for _ in range(remainder):
                await d.get(f"cmd=knightarena&op=exchange&id={_id}&times=1")
                d.log(d.find())
                if "成功" not in d.html:
                    break

        return

    knight_config: list[dict] = d.config("华山论剑.战阵调整")
    if knight_config is None:
        d.log("你没有设置战阵调整，跳过挑战")
        return

    # 更改侠士/选择侠士
    await d.get("cmd=knightarena&op=viewsetknightlist&pos=0")
    knight_data = dict(d.findall(r">([\u4e00-\u9fff]+) \d+级.*?knightid=(\d+)"))
    if not knight_data:
        d.log("战阵调整侠士不足，跳过挑战")
        return

    for item in knight_config:
        is_fail: bool = False
        count: int = item["count"]
        knights: list[str] = item["knights"]

        # 战阵调整
        for i, knight in enumerate(knights, 1):
            if i > 3:
                break
            if _id := knight_data.get(knight, None):
                # 出战
                await d.get(f"cmd=knightarena&op=setknight&id={_id}&pos={i}&type=1")
                d.log(f"第{i}战 -> {knight}")
            else:
                d.log(f"第{i}战 -> 您没有{knight}")
                is_fail = True
                break

        if is_fail:
            d.log("当前编队出战侠士失败，跳过该编队挑战")
            continue

        # 挑战
        for _ in range(count):
            # 免费挑战/开始挑战
            await d.get("cmd=knightarena&op=challenge")
            d.log(d.find())
            if "增加荣誉点数" not in d.html:
                # 请先设置上阵侠士后再开始战斗
                # 当前论剑队伍中有侠士耐久不足，请更换上阵！
                break


@register()
async def 分享(d: DaLeDou):
    is_end: bool = False
    second = await c_get_doushenta_cd(d)

    # 分享
    await d.get("cmd=sharegame&subtype=1")
    for _ in range(9):
        # 一键分享
        await d.get("cmd=sharegame&subtype=6")
        d.log(d.find(r"】</p>(.*?)<p>"))
        if ("达到当日分享次数上限" in d.html) or is_end:
            d.log(d.find(r"</p><p>(.*?)<br />"))
            break

        for _ in range(10):
            # 开始挑战 or 挑战下一层
            await d.get("cmd=towerfight&type=0")
            d.log(f"斗神塔 -> {d.find()}")
            await asyncio.sleep(second)
            if "您战胜了" not in d.html:
                is_end = True
                break
            # 您败给了
            # 已经到了塔顶
            # 已经没有剩余的周挑战数
            # 您需要消耗斗神符才能继续挑战斗神塔

    # 自动挑战
    await d.get("cmd=towerfight&type=11")
    d.log(f"斗神塔 -> {d.find()}")
    await asyncio.sleep(second)
    if "结束挑战" in d.html:
        # 结束挑战
        await d.get("cmd=towerfight&type=7")
        d.log(f"斗神塔 -> {d.find()}")

    if DateTime.week() != 4:
        return

    # 领取奖励
    await d.get("cmd=sharegame&subtype=3")
    for s in d.findall(r"sharenums=(\d+)"):
        # 领取
        await d.get(f"cmd=sharegame&subtype=4&sharenums={s}")
        d.log(d.find(r"】</p>(.*?)<p>"))

    if d.html.count("已领取") == 14:
        # 重置分享
        await d.get("cmd=sharegame&subtype=7")
        d.log(d.find(r"】</p>(.*?)<p>"))


@register()
async def 好友(d: DaLeDou):
    """乐斗好友BOSS"""
    count: int = d.config("好友.贡献药水.count")
    for _ in range(count):
        # 使用贡献药水*1
        await d.get("cmd=use&id=3038&store_type=1&page=1")
        if "使用规则" in d.html:
            d.log(d.find(r"】</p><p>(.*?)<br />"))
            break
        d.log(d.find())

    # 好友首页
    await d.get("cmd=friendlist&page=1")
    for u in d.findall(r"侠：.*?B_UID=(\d+)"):
        # 乐斗
        await d.get(f"cmd=fight&B_UID={u}")
        if "使用规则" in d.html:
            d.log(d.find(r"】</p><p>(.*?)<br />"))
            break
        d.log(d.find(r"<br />(.*?)，"))


@register()
async def 帮友(d: DaLeDou):
    """乐斗帮友BOSS"""
    # 帮友首页
    await d.get("cmd=viewmem&page=1")
    for u in d.findall(r"侠：.*?B_UID=(\d+)"):
        # 乐斗
        await d.get(f"cmd=fight&B_UID={u}")
        d.log(d.find(r"<br />(.*?)，"))


@register()
async def 侠侣(d: DaLeDou):
    """
    每天乐斗侠侣BOSS、情师徒拜
    每周二、五、日报名侠侣争霸
    """
    enabled: bool = d.config("侠侣.情师徒拜.enabled")

    # 侠侣
    await d.get("cmd=viewxialv&page=1")
    if enabled:
        uin = d.findall(r"</a>\d+.*?B_UID=(\d+)")
    else:
        uin = d.findall(r"侠：.*?B_UID=(\d+)")
    for u in uin:
        # 乐斗
        await d.get(f"cmd=fight&B_UID={u}")
        if "使用规则" in d.html:
            d.log(d.find(r"】</p><p>(.*?)<br />"))
        else:
            d.log(d.find(r"<br />(.*?)！"))
        if "体力值不足" in d.html:
            break

    if DateTime.week() not in {2, 5, 7}:
        return

    # 报名侠侣争霸
    await d.get("cmd=cfight&subtype=9")
    if "使用规则" in d.html:
        d.log(d.find(r"】</p><p>(.*?)<br />"))
    else:
        d.log(d.find(r"报名状态.*?<br />(.*?)<br />"))


@register()
async def 武林(d: DaLeDou):
    # 报名
    await d.get("cmd=fastSignWulin&ifFirstSign=1")
    if "使用规则" in d.html:
        d.log(d.find(r"】</p><p>(.*?)<br />"))
    else:
        d.log(d.find(r"升级。<br />(.*?) "))


@register()
async def 群侠(d: DaLeDou):
    knight_config: list[str] = d.config("群侠.设置战队")
    if knight_config is None:
        d.log("你必须设置战队才能报名")
        return

    # 更改侠士/选择侠士
    await d.get("cmd=knightfight&op=viewsetknightlist&pos=0")
    if "报名状态：已报名" in d.html:
        d.log(d.find(r"报名状态：(.*?)<"))
        return
    knight_data = dict(d.findall(r">([\u4e00-\u9fff]+) \d+级.*?knightid=(\d+)"))
    if not knight_data:
        d.log("设置战队侠士不足")
        return

    for i, knight in enumerate(knight_config, 1):
        if i > 5:
            break
        if _id := knight_data.get(knight, None):
            # 出战
            await d.get(f"cmd=knightfight&op=set_knight&id={_id}&pos={i}&type=1")
            d.log(f"第{i}战 -> {knight}")
        else:
            d.log(f"第{i}战 -> 您没有{knight}，跳过报名")
            return

    # 报名
    await d.get("cmd=knightfight&op=signup")
    d.log(d.find(r"侠士侠号.*?<br />(.*?)<br />"))


@register()
async def 结拜(d: DaLeDou):
    if DateTime.week() not in {1, 2}:
        return

    for _id in [1, 2, 3, 5, 4]:
        # 报名
        await d.get(f"cmd=brofight&subtype=1&gidIdx={_id}")
        d.log(d.find(r"排行</a><br />(.*?)<"))
        if "请换一个赛区报名" in d.html or "你们无法报名" in d.html:
            continue
        break


@register()
async def 巅峰之战进行中(d: DaLeDou):
    if DateTime.week() in {1, 2}:
        # 领奖
        await d.get("cmd=gvg&sub=1")
        d.log(d.find(r"】</p>(.*?)<br />"))

        _id: int = d.config("巅峰之战进行中.id")
        # 报名
        await d.get(f"cmd=gvg&sub=4&group={_id}&check=1")
        d.log(d.find(r"】</p>(.*?)<br />"))
        return

    for _ in range(14):
        # 征战
        await d.get("cmd=gvg&sub=5")
        if "战线告急" in d.html:
            d.log(d.find(r"支援！<br />(.*?)<"))
        else:
            d.log(d.find(r"】</p>(.*?)<"))

        if "你在巅峰之战中" not in d.html:
            # 冷却时间
            # 撒花祝贺
            # 请您先报名再挑战
            # 您今天已经用完复活次数了
            break


@register()
async def 矿洞(d: DaLeDou):
    f: int = d.config("矿洞.floor")
    m: int = d.config("矿洞.mode")

    # 佣兵
    await d.get("cmd=newmercenary")
    mercenary_ids = []
    # 全部佣兵
    mercenary_all = d.findall(r'id=(\d+)">(.*?)</a>')
    # 出战阵容
    mercenary_battle = d.findall(r"<br />\d+. (.*?) ")
    for _id, mercenary_name in mercenary_all:
        if mercenary_name in mercenary_battle:
            mercenary_ids.append(_id)

    if "10019" in d.html:
        # 出战鹤仙人
        await d.get("cmd=newmercenary&sub=3&id=10019")
        d.log(f"{d.find(r'！<br />(.*?)<')} -> {d.find()}")
        is_success = True
    else:
        is_success = False

    # 矿洞
    await d.get("cmd=factionmine")
    for _ in range(5):
        if "副本挑战中" in d.html:
            # 挑战
            await d.get("cmd=factionmine&op=fight")
            d.log(d.find())
            if "挑战次数不足" in d.html:
                break
            await asyncio.sleep(1.5)
        elif "开启副本" in d.html:
            # 确认开启
            await d.get(f"cmd=factionmine&op=start&floor={f}&mode={m}")
            d.log(d.find())
            if "当前不能开启此副本" in d.html:
                break
        elif "领取奖励" in d.html:
            await d.get("cmd=factionmine&op=reward")
            d.log(d.find())

    if not is_success:
        return

    # 恢复原始佣兵
    for _id in mercenary_ids:
        # 出战
        await d.get(f"cmd=newmercenary&sub=3&id={_id}")
        d.log(f"恢复{d.find(r'！<br />(.*?)<')} -> {d.find()}")


@register()
async def 掠夺(d: DaLeDou):
    if DateTime.week() == 3:
        # 领取胜负奖励
        await d.get("cmd=forage_war&subtype=6")
        d.log(d.find())
        # 报名
        await d.get("cmd=forage_war&subtype=1")
        d.log(d.find())
        return

    if DateTime.week() != 2:
        return

    # 掠夺
    await d.get("cmd=forage_war")
    if ("本轮轮空" in d.html) or ("未报名" in d.html):
        d.log(d.find(r"本届战况：(.*?)<br />"))
        return

    data = []
    # 掠夺
    await d.get("cmd=forage_war&subtype=3")
    if gra_id := d.findall(r'gra_id=(\d+)">掠夺'):
        for _id in gra_id:
            await d.get(f"cmd=forage_war&subtype=3&op=1&gra_id={_id}")
            if zhanli := d.find(r"<br />1.*? (\d+)\."):
                data.append((int(zhanli), _id))
        if data:
            # 掠夺一次战力最小的成员
            _, _id = min(data)
            await d.get(f"cmd=forage_war&subtype=4&gra_id={_id}")
            d.log(d.find())
    else:
        d.log("已占领对方全部粮仓")

    # 领奖
    await d.get("cmd=forage_war&subtype=5")
    d.log(d.find())


@register()
async def 踢馆(d: DaLeDou):
    if DateTime.week() == 6:
        # 报名
        await d.get("cmd=facchallenge&subtype=1")
        d.log(d.find())
        # 领奖
        await d.get("cmd=facchallenge&subtype=7")
        d.log(d.find())
        return

    if DateTime.week() != 5:
        return

    def generate_sequence():
        # 试炼、高倍转盘序列
        for t in [2, 2, 2, 2, 2, 4]:
            yield t
        # 挑战序列
        for _ in range(30):
            yield 3

    for t in generate_sequence():
        await d.get(f"cmd=facchallenge&subtype={t}")
        d.log(d.find())
        if "您的复活次数已耗尽" in d.html:
            break
        elif "您的挑战次数已用光" in d.html:
            break
        elif "你们帮没有报名参加这次比赛" in d.html:
            break


@register()
async def 竞技场(d: DaLeDou):
    if not (1 <= DateTime.day() <= 25):
        return

    if d.config("竞技场.河图洛书.enabled"):
        # 兑换10个河图洛书
        await d.get("cmd=arena&op=exchange&id=5435&times=10")
        d.log(d.find())

    for _ in range(10):
        # 免费挑战 or 开始挑战
        await d.get("cmd=arena&op=challenge")
        d.log(d.find())
        if "免费挑战次数已用完" in d.html:
            break

    # 领取奖励
    await d.get("cmd=arena&op=drawdaily")
    d.log(d.find())


@register()
async def 十二宫(d: DaLeDou):
    _id: int = d.config("十二宫.id")
    # 请猴王扫荡
    await d.get(f"cmd=zodiacdungeon&op=autofight&scene_id={_id}")
    if "恭喜你" in d.html:
        d.log(d.find(r"恭喜你，(.*?)！"))
        return
    elif "是否复活再战" in d.html:
        d.log(d.find(r"<br.*>(.*?)，"))
        return

    # 你已经不幸阵亡，请复活再战！
    # 挑战次数不足
    # 当前场景进度不足以使用自动挑战功能
    d.log(d.find(r"<p>(.*?)<br />"))


@register()
async def 许愿(d: DaLeDou):
    # 领取许愿奖励 > 领取 > 许愿
    for sub in [5, 1, 6]:
        await d.get(f"cmd=wish&sub={sub}")
        d.log(d.find())


@register()
async def 抢地盘(d: DaLeDou):
    """随机攻占一次无限制区"""
    # 无限制区
    await d.get("cmd=recommendmanor&type=11&page=1")
    if manorid := d.findall(r'manorid=(\d+)">攻占</a>'):
        _id = random.choice(manorid)
        # 攻占
        await d.get(f"cmd=manorfight&fighttype=1&manorid={_id}")
        d.log(d.find(r"</p><p>(.*?)。"))


@register()
async def 历练(d: DaLeDou):
    config: dict[int, int] = d.config("历练")

    # 乐斗助手
    await d.get("cmd=view&type=6")
    if "取消自动使用活力药水" in d.html:
        # 取消自动使用活力药水
        await d.get("cmd=set&type=11")
        d.log("取消自动使用活力药水")

    for _id, count in config.items():
        if count <= 0:
            continue
        for _ in range(count):
            await d.get(f"cmd=mappush&subtype=3&mapid=6&npcid={_id}&pageid=2")
            if "您还没有打到该历练场景" in d.html:
                d.log(d.find(r"介绍</a><br />(.*?)<br />"))
                break

            d.log(d.find(r"阅历值：\d+<br />(.*?)<br />"))
            if "活力不足" in d.html:
                return
            elif "BOSS" not in d.html:
                # 你今天和xx挑战次数已经达到上限了，请明天再来挑战吧
                # 还不能挑战
                break


@register()
async def 镖行天下(d: DaLeDou):
    """
    镖师是蔡八斗且有免费刷新次数时刷新
    顺序拦截3次
    """
    # 镖行天下
    await d.get("cmd=cargo")
    if "护送完成" in d.html:
        # 领取奖励
        await d.get("cmd=cargo&op=16")
        d.log(d.find())

    if "剩余护送次数：1" in d.html:
        # 护送押镖
        await d.get("cmd=cargo&op=7")
        if result := d.find(r"免费刷新次数：(\d+)"):
            count = int(result)
        else:
            d.log("获取免费刷新次数失败，免费次数重置为0")
            count = 0

        for _ in range(count):
            d.log(d.find(r"当前镖师：(.*?)<"))
            if "蔡八斗" not in d.html:
                break
            # 刷新押镖
            await d.get("cmd=cargo&op=8")
            d.log(d.find())

        # 启程护送
        await d.get("cmd=cargo&op=6")
        d.log(d.find())

    for _ in range(10):
        # 刷新
        await d.get("cmd=cargo&op=3")
        d.log(d.find())
        if "刷新过于频繁" in d.html:
            await asyncio.sleep(2)
            continue
        for u in d.findall(r'passerby_uin=(\d+)">拦截'):
            # 拦截
            await d.get(f"cmd=cargo&op=14&passerby_uin={u}")
            d.log(d.find())
            if "剩余拦截次数：0" in d.html:
                return


@register()
async def 幻境(d: DaLeDou):
    # 幻境
    await d.get("cmd=misty")
    if "挑战次数：0/1" in d.html:
        d.log(r"您的挑战次数已用完，请明日再战！")
        return

    if "累积星数" in d.html and "op=return" in d.html:
        # 返回飘渺幻境
        await d.get("cmd=misty&op=return")

    _id: int = d.config("幻境.id")
    await d.get(f"cmd=misty&op=start&stage_id={_id}")
    if "副本未开通" in d.html:
        d.log(f"{_id} -> 副本未开通")
        return

    for _ in range(5):
        # 乐斗
        await d.get("cmd=misty&op=fight")
        d.log(d.find(r"星数.*?<br />(.*?)<br />"))
        if "尔等之才" in d.html:
            break

    # 领取奖励
    for _ in range(10):
        b_id = d.find(r"box_id=(\d+)")
        if b_id is None:
            break
        await d.get(f"cmd=misty&op=reward&box_id={b_id}")
        d.log(d.find(r"星数.*?<br />(.*?)<br />"))

    # 返回飘渺幻境
    await d.get("cmd=misty&op=return")


@register()
async def 群雄逐鹿(d: DaLeDou):
    """周六报名、领奖"""
    if DateTime.week() != 6:
        return

    for op in ["signup", "drawreward"]:
        await d.get(f"cmd=thronesbattle&op={op}")
        d.log(d.find(r"届群雄逐鹿<br />(.*?)<br />"))


@register()
async def 画卷迷踪(d: DaLeDou):
    for _ in range(20):
        # 准备完成进入战斗
        await d.get("cmd=scroll_dungeon&op=fight&buff=0")
        d.log(d.find(r"</a><br /><br />(.*?)<br />"))
        if "没有挑战次数" in d.html:
            break
        elif "征战书不足" in d.html:
            break


@register()
async def 门派(d: DaLeDou):
    # 万年寺
    if d.config("门派.门派高香.enabled"):
        # 兑换门派高香*1
        await d.get("cmd=exchange&subtype=2&type=1248&times=1")
        d.log(d.find())

    # 普通香炉、高香香炉
    for op in ["fumigatefreeincense", "fumigatepaidincense"]:
        await d.get(f"cmd=sect&op={op}")
        d.log(d.find(r"修行。<br />(.*?)<br />"))

    # 八叶堂
    # 进入木桩训练、进入同门切磋
    ops = ["trainingwithnpc", "trainingwithmember"]
    if d.config("门派.门派战书.enabled"):
        await d.get("cmd=exchange&subtype=2&type=1249&times=1")
        d.log(d.find())
        if "成功" in d.html:
            # 追加一次进入同门切磋
            ops.append("trainingwithmember")

    for op in ops:
        await d.get(f"cmd=sect&op={op}")
        d.log(d.find())

    # 金顶
    ranks = [
        "rank=1&pos=1",  # 掌门
        "rank=2&pos=1",  # 首座
        "rank=2&pos=2",  # 首座
        "rank=3&pos=1",  # 堂主
        "rank=3&pos=2",  # 堂主
        "rank=3&pos=3",  # 堂主
        "rank=3&pos=4",  # 堂主
    ]
    for rank in ranks:
        # 切磋
        await d.get(f"cmd=sect&op=trainingwithcouncil&{rank}")
        d.log(d.find())

    # 五花堂
    wuhuatang = await d.get("cmd=sect_task")
    tasks = {
        "进入华藏寺看一看": "cmd=sect_art",
        "进入伏虎寺看一看": "cmd=sect_trump",
        "进入金顶看一看": "cmd=sect&op=showcouncil",
        "进入八叶堂看一看": "cmd=sect&op=showtraining",
        "进入万年寺看一看": "cmd=sect&op=showfumigate",
    }
    for name, url in tasks.items():
        if name in wuhuatang:
            await d.get(url)
            d.log(name)
    if "查看一名" in wuhuatang:
        # 查看一名同门成员的资料 or 查看一名其他门派成员的资料
        d.log("查看好友第二页所有成员")
        # 好友第2页
        await d.get("cmd=friendlist&page=2")
        for uin in d.findall(r"</a>\d+.*?B_UID=(\d+)"):
            # 查看好友
            await d.get(f"cmd=totalinfo&B_UID={uin}")
            d.log(f"查看好友 -> {uin}")
    if "进行一次心法修炼" in wuhuatang:
        for _id in range(101, 119):
            # 修炼
            await d.get(f"cmd=sect_art&subtype=2&art_id={_id}&times=1")
            d.log(d.find())
            if "修炼成功" in d.html:
                break

    # 五花堂
    await d.get("cmd=sect_task")
    for task_id in d.findall(r'task_id=(\d+)">完成'):
        # 完成
        await d.get(f"cmd=sect_task&subtype=2&task_id={task_id}")
        d.log(d.find())


@register()
async def 门派邀请赛(d: DaLeDou):
    if DateTime.week() in {1, 2}:
        # 组队报名
        await d.get("cmd=secttournament&op=signup")
        d.log(d.find())
        # 领取奖励
        await d.get("cmd=secttournament&op=getrankandrankingreward")
        d.log(d.find())
        return

    exchange_config: dict[int, dict] = d.config("门派邀请赛.exchange")
    for _id, item in exchange_config.items():
        quantity: int = item["quantity"]
        if quantity <= 0:
            continue
        quotient, remainder = divmod(quantity, 10)
        for _ in range(quotient):
            await d.get(f"cmd=exchange&subtype=2&type={_id}&times=10")
            d.log(d.find())
            if "成功" not in d.html:
                break
        for _ in range(remainder):
            await d.get(f"cmd=exchange&subtype=2&type={_id}&times=1")
            d.log(d.find())
            if "成功" not in d.html:
                break

    for _ in range(10):
        # 开始挑战
        await d.get("cmd=secttournament&op=fight")
        d.log(d.find())
        if "已达最大挑战上限" in d.html:
            break
        elif "门派战书不足" in d.html:
            break


@register()
async def 会武(d: DaLeDou):
    if DateTime.week() in {1, 2, 3}:
        for _ in range(21):
            # 挑战
            await d.get("cmd=sectmelee&op=dotraining")
            if "试炼场】" in d.html:
                d.log(d.find(r"最高伤害：\d+<br />(.*?)<br />"))
                continue
            d.log(d.find(r"规则</a><br />(.*?)<br />"))
            if "你已达今日挑战上限" in d.html:
                break
            elif "你的试炼书不足" in d.html and d.config("会武.试炼书.enabled"):
                # 兑换试炼书*1
                await d.get("cmd=exchange&subtype=2&type=1265&times=1&costtype=13")
                d.log(d.find())
                if "成功" not in d.html:
                    break

    elif DateTime.week() == 4:
        # 冠军助威 丐帮
        await d.get("cmd=sectmelee&op=cheer&sect=1003")
        # 冠军助威
        await d.get("cmd=sectmelee&op=showcheer")
        d.log(d.find())

        exchange_config: dict[int, dict] = d.config("会武.exchange")
        for _id, item in exchange_config.items():
            quantity: int = item["quantity"]
            if quantity <= 0:
                continue
            quotient, remainder = divmod(quantity, 10)
            for _ in range(quotient):
                await d.get(f"cmd=exchange&subtype=2&type={_id}&times=10&costtype=13")
                d.log(d.find())
                if "成功" not in d.html:
                    break
            for _ in range(remainder):
                await d.get(f"cmd=exchange&subtype=2&type={_id}&times=1&costtype=13")
                d.log(d.find())
                if "成功" not in d.html:
                    break

    elif DateTime.week() == 6:
        # 领奖
        await d.get("cmd=sectmelee&op=showreward")
        d.log(d.find(r"<br />(.*?)。"))
        d.log(d.find(r"。<br />(.*?)。"))
        # 领取
        await d.get("cmd=sectmelee&op=drawreward")
        if "本届已领取奖励" in d.html:
            d.log(d.find(r"规则</a><br />(.*?)<br />"))
        else:
            d.log(d.find())


@register()
async def 梦想之旅(d: DaLeDou):
    # 普通旅行
    await d.get("cmd=dreamtrip&sub=2")
    d.log(d.find())

    if DateTime.week() != 4:
        return

    quantity: int = d.config("梦想之旅.梦幻旅行.count")
    if d.html.count("已去过") < quantity:
        d.log(f"已去过数量低于{quantity}")
        return

    # 获取当前区域所有未去过的目的地
    if place := d.findall(r"([\u4e00-\u9fa5\s\-]+)(?=\s未去过)"):
        bmapid = d.find(r'bmapid=(\d+)">梦幻旅行')
        for name in place:
            # 梦幻旅行
            await d.get(f"cmd=dreamtrip&sub=3&bmapid={bmapid}")
            s = d.find(rf"{name}.*?smapid=(\d+)")
            # 去这里
            await d.get(f"cmd=dreamtrip&sub=2&smapid={s}")
            d.log(d.find())

    # 领取礼包
    for _ in range(2):
        if b := d.findall(r"sub=4&amp;bmapid=(\d+)"):
            # 区域礼包 1 or 2 or 3 or 4
            # 超级礼包 0
            await d.get(f"cmd=dreamtrip&sub=4&bmapid={b[0]}")
            d.log(d.find())


async def 问鼎天下_商店兑换(d: DaLeDou):
    """智能补足神魔录古阵篇宝物升级碎片材料

    如果当前等级低于最高等级且拥有数量低于需要数量时则兑换碎片
    """
    name = "神魔录"
    data = {
        "夔牛鼓": {
            "id": 1,
            "t": 1270,
            "backpack_id": 5154,
            "material_name": "夔牛碎片",
        },
        "饕餮鼎": {
            "id": 2,
            "t": 1271,
            "backpack_id": 5155,
            "material_name": "饕餮碎片",
        },
        "烛龙印": {
            "id": 3,
            "t": 1268,
            "backpack_id": 5156,
            "material_name": "烛龙碎片",
        },
        "黄鸟伞": {
            "id": 4,
            "t": 1269,
            "backpack_id": 5157,
            "material_name": "黄鸟碎片",
        },
    }
    for treasure, _dict in data.items():
        _id = _dict["id"]
        t = _dict["t"]
        backpack_id = _dict["backpack_id"]
        material_name = _dict["material_name"]

        possess = await c_get_material_quantity(d, backpack_id)

        # 神魔录古阵篇宝物详情
        await d.get(f"cmd=ancient_gods&op=4&id={_id}")
        # 当前等级
        now_level = d.find(r"等级：(\d+)")
        # 最高等级
        max_level = d.find(r"最高提升至(\d+)")
        d.log(f"{treasure} -> 当前 {now_level} 级", name)
        d.log(f"{treasure} -> 最高 {max_level} 级", name)
        if now_level == max_level:
            continue

        # 碎片消耗数量
        need = d.find(r"碎片\*(\d+)")
        if need is None:
            d.log(f"{treasure} -> 获取{material_name}需要数量失败")
            continue

        need = int(need)
        if need <= possess:
            continue

        d.log(f"{treasure} -> 消耗{material_name}*{need}（{possess}）", name)
        q, r = divmod((need - possess), 10)
        if q:
            # 兑换10个
            await d.get(f"cmd=exchange&subtype=2&type={t}&times=10&costtype=14")
            d.log(f"{treasure} -> {d.find()}")
            return
        for _ in range(r):
            # 兑换1个
            await d.get(f"cmd=exchange&subtype=2&type={t}&times=1&costtype=14")
            d.log(f"{treasure} -> {d.find()}")


@register()
async def 问鼎天下(d: DaLeDou):
    if DateTime.week() == 1:
        # 领取奖励
        await d.get("cmd=tbattle&op=drawreward")
        d.log(d.find())
        await 问鼎天下_商店兑换(d)
    elif DateTime.week() == 6:
        # 淘汰赛助威
        _id = d.config("问鼎天下.淘汰赛")
        if _id is None:
            d.log("你没有设置淘汰赛助威帮派id")
            return
        await d.get(f"cmd=tbattle&op=cheerregionbattle&id={_id}")
        d.log(d.find())
        return
    elif DateTime.week() == 7:
        # 排名赛助威
        _id = d.config("问鼎天下.排名赛")
        if _id is None:
            d.log("你没有设置排名赛助威帮派id")
            return
        await d.get(f"cmd=tbattle&op=cheerchampionbattle&id={_id}")
        d.log(d.find())
        return

    # 问鼎天下
    await d.get("cmd=tbattle")
    if "放弃" in d.html:
        d.log("已有占领资源点，本任务结束")
        return

    if "你占领的领地已经枯竭" in d.html:
        # 领取
        await d.get("cmd=tbattle&op=drawreleasereward")
        d.log(d.find())

    remaining_occupy_count = d.find(r"剩余抢占次数：(\d+)")
    if remaining_occupy_count is None:
        d.log("获取剩余抢占次数失败")
        return

    remaining_occupy_count = int(remaining_occupy_count)
    if remaining_occupy_count == 0:
        d.log("没有抢占次数了")
        return

    region: int = d.config("问鼎天下.region")
    count: int = d.config("问鼎天下.count")
    if count >= remaining_occupy_count:
        count = max(0, remaining_occupy_count - 1)

    # 区域
    await d.get(f"cmd=tbattle&op=showregion&region={region}")
    for _id in d.findall(r"id=(\d+).*?攻占</a>")[:4]:
        while count:
            # 攻占1级资源点
            await d.get(f"cmd=tbattle&op=occupy&id={_id}&region={region}")
            d.log(d.find())
            if "你主动与" in d.html:
                count -= 1
                if "放弃" in d.html:
                    # 放弃
                    await d.get("cmd=tbattle&op=abandon")
                    d.log(d.find())
            else:
                break
        if count == 0:
            break

    # 区域
    await d.get(f"cmd=tbattle&op=showregion&region={region}")
    # 攻占3级资源点最后一个
    _id = d.findall(r"id=(\d+).*?攻占</a>")[-1]
    await d.get(f"cmd=tbattle&op=occupy&id={_id}&region=1")
    d.log(d.find())


@register()
async def 帮派商会(d: DaLeDou):
    await c_帮派商会(d)


async def 帮派远征军_攻击(d: DaLeDou, p_id: str, u: str) -> bool:
    # 攻击
    await d.get(f"cmd=factionarmy&op=fightWithUsr&point_id={p_id}&opp_uin={u}")
    if "加入帮派第一周不能参与帮派远征军" in d.html:
        return False
    if "【帮派远征军-征战结束】" in d.html:
        d.log(d.find())
        if "您未能战胜" in d.html:
            return False
    elif "【帮派远征军】" in d.html:
        d.log(d.find(r"<br /><br />(.*?)</p>"))
        if "您的血量不足" in d.html:
            return False
    return True


async def 帮派远征军_领取(d: DaLeDou):
    point_ids = []
    land_ids = []
    for _id in range(5):
        await d.get(f"cmd=factionarmy&op=viewIndex&island_id={_id}")
        point_ids += d.findall(r'point_id=(\d+)">领取奖励')
        if "未解锁" in d.html:
            break
        land_ids += d.findall(r'island_id=(\d+)">领取岛屿宝箱')

    # 领取奖励
    for p_id in point_ids:
        await d.get(f"cmd=factionarmy&op=getPointAward&point_id={p_id}")
        d.log(d.find())

    # 领取岛屿宝箱
    for i_id in land_ids:
        await d.get(f"cmd=factionarmy&op=getIslandAward&island_id={i_id}")
        d.log(d.find())


@register()
async def 帮派远征军(d: DaLeDou):
    while True:
        # 帮派远征军
        await d.get("cmd=factionarmy&op=viewIndex&island_id=-1")
        p_id = d.find(r'point_id=(\d+)">参战')
        if p_id is None:
            d.log("已经全部通关了")
            await 帮派远征军_领取(d)
            break
        # 参战
        await d.get(f"cmd=factionarmy&op=viewpoint&point_id={p_id}")

        data = []
        for _ in range(20):
            data += d.findall(r'(\d+)\.\d+<a.*?opp_uin=(\d+)">攻击')
            pages = d.find(r'pages=(\d+)">下一页')
            if not data or pages is None:
                break
            # 下一页
            await d.get(f"cmd=factionarmy&op=viewpoint&point_id={p_id}&page={pages}")

        for _, u in sorted(data, key=lambda x: int(x[0])):
            if not await 帮派远征军_攻击(d, p_id, u):
                await 帮派远征军_领取(d)
                return


async def 帮派黄金联赛_参战(d: DaLeDou):
    # 参战
    await d.get("cmd=factionleague&op=2")
    if "opp_uin" not in d.html:
        d.log("敌人已全部阵亡")
        return

    data = []
    if pages := d.find(r'pages=(\d+)">末页'):
        _pages = int(pages)
    else:
        _pages = 1
    for p in range(1, _pages + 1):
        await d.get(f"cmd=factionleague&op=2&pages={p}")
        data += d.findall(r"%&nbsp;&nbsp;(\d+).*?opp_uin=(\d+)")

    for _, u in sorted(data, key=lambda x: int(x[0])):
        # 攻击
        await d.get(f"cmd=factionleague&op=4&opp_uin={u}")
        if "勇士，" in d.html:
            d.log(d.find())
            if "不幸战败" in d.html:
                return
        elif "您已阵亡" in d.html:
            d.log(d.find(r"<br /><br />(.*?)</p>"))
            return

    # 参战
    await d.get("cmd=factionleague&op=2")
    if "opp_uin" not in d.html:
        d.log("敌人已全部阵亡")
        return


@register()
async def 帮派黄金联赛(d: DaLeDou):
    # 帮派黄金联赛
    await d.get("cmd=factionleague&op=0")
    if "领取奖励" in d.html:
        # 领取轮次奖励
        await d.get("cmd=factionleague&op=5")
        d.log(d.find(r"<p>(.*?)<br /><br />"))
    elif "领取帮派赛季奖励" in d.html:
        # 领取帮派赛季奖励
        await d.get("cmd=factionleague&op=7")
        d.log(d.find(r"<p>(.*?)<br /><br />"))
    elif "已参与防守" not in d.html:
        # 参与防守
        await d.get("cmd=factionleague&op=1")
        d.log(d.find(r"<p>(.*?)<br /><br />"))
    elif "休赛期" in d.html:
        d.log("休赛期无任何操作")

    if "op=2" in d.html:
        await 帮派黄金联赛_参战(d)


@register()
async def 任务派遣中心(d: DaLeDou):
    await c_任务派遣中心(d)


@register()
async def 武林盟主(d: DaLeDou):
    if DateTime.week() in {3, 5, 7}:
        # 武林盟主
        await d.get("cmd=wlmz&op=view_index")
        if data := d.findall(r'section_id=(\d+)&amp;round_id=(\d+)">'):
            for s, r in data:
                await d.get(f"cmd=wlmz&op=get_award&section_id={s}&round_id={r}")
                d.log(d.find(r"<br /><br />(.*?)</p>"))
        else:
            d.log("没有奖励领取")

    if DateTime.week() in [1, 3, 5]:
        _id: int = d.config("武林盟主.id")
        if _id is None:
            d.log("你没有配置报名赛场id")
            return
        await d.get(f"cmd=wlmz&op=signup&ground_id={_id}")
        if "总决赛周不允许报名" in d.html or "您的战力不足" in d.html:
            d.log(d.find(r"战报</a><br />(.*?)<br />"))
        elif "您已报名" in d.html:
            d.log(d.find(r"赛场】<br />(.*?)<br />"))
    elif DateTime.week() in [2, 4, 6]:
        for index in range(8):
            # 选择
            await d.get(f"cmd=wlmz&op=guess_up&index={index}")
            d.log(d.find(r"规则</a><br />(.*?)<br />"))
        # 确定竞猜选择
        await d.get("cmd=wlmz&op=comfirm")
        d.log(d.find(r"战报</a><br />(.*?)<br />"))


@register()
async def 全民乱斗(d: DaLeDou):
    collect_status = False
    for t in [2, 3, 4]:
        await d.get(f"cmd=luandou&op=0&acttype={t}")
        for _id in d.findall(r'.*?id=(\d+)">领取</a>'):
            collect_status = True
            # 领取
            await d.get(f"cmd=luandou&op=8&id={_id}")
            d.log(d.find(r"斗】<br /><br />(.*?)<br />"))
    if not collect_status:
        d.log("没有礼包领取")


@register()
async def 侠士客栈(d: DaLeDou):
    await c_侠士客栈(d)

    # 共建回馈
    await d.get("cmd=notice&op=view&sub=total")
    for _id in d.findall(r"giftId=(\d+)"):
        # 领取
        await d.get(f"cmd=notice&op=reqreward&giftId={_id}&sub=total")
        d.log(d.find(r"<p>.*?<br />(.*?)<"))


@register()
async def 江湖长梦(d: DaLeDou):
    if DateTime.day() != 20:
        return

    exchange_config: dict[int, dict] = d.config("江湖长梦.exchange")
    for _id, item in exchange_config.items():
        material_name: str = item["material_name"]
        quantity: int = item["quantity"]
        if quantity <= 0:
            continue
        for _ in range(quantity):
            await d.get(f"cmd=longdreamexchange&op=exchange&key_id={_id}")
            if "成功" not in d.html:
                d.log(f"{material_name}*1 -> {d.find()}")
                break
            d.log(f"{material_name}*1 -> {d.find(r'</a><br />(.*?)<')}")


@register()
async def 大侠回归三重好礼(d: DaLeDou):
    # 大侠回归三重好礼
    await d.get("cmd=newAct&subtype=173&op=1")
    if data := d.findall(r"subtype=(\d+).*?taskid=(\d+)"):
        for s, t in data:
            # 领取
            await d.get(f"cmd=newAct&subtype={s}&op=2&taskid={t}")
            d.log(d.find(r"】<br /><br />(.*?)<br />"))
    else:
        d.log("没有礼包领取")


async def 备战天赋(d: DaLeDou, _id: int):
    # 备战天赋
    await d.get("cmd=ascendheaven&op=viewprepare")
    start_id = d.find(r"id=(\d+)")
    if start_id is None:
        return

    for i in range(int(start_id), _id + 1):
        while True:
            # 激活
            await d.get(f"cmd=ascendheaven&op=activeskill&id={i}")
            d.log(d.find())
            if "激活心法失败" in d.html:
                continue
            if "激活心法成功" in d.html:
                break
            # 您尚未点击上一级天赋，无法点击该天赋
            # 您报名的不是排位赛，无法修改备战天赋
            return


@register()
async def 飞升大作战(d: DaLeDou):
    enabled: bool = d.config("飞升大作战.玄铁令.enabled")
    t: int = d.config("飞升大作战.type")
    _id: int | None = d.config("飞升大作战.id")

    # 飞升大作战
    await d.get("cmd=ascendheaven")
    if "赛季结算中" in d.html:
        enabled = False

    if enabled and t == 1:  # 报名单排模式之前兑换
        # 兑换玄铁令*1
        await d.get("cmd=ascendheaven&op=exchange&id=2&times=1")
        d.log(d.find())
    elif enabled and t == 3:  # 报名双排模式之前兑换
        # 兑换玄铁令*1
        await d.get("cmd=ascendheaven&op=exchange&id=2&times=1")
        d.log(d.find())
        # 兑换玄铁令*1
        await d.get("cmd=ascendheaven&op=exchange&id=2&times=1")
        d.log(d.find())

    # 报名
    await d.get(f"cmd=ascendheaven&op=signup&type={t}")
    d.log(d.find())
    if "你报名参加了" in d.html or "你已经报名参赛" in d.html:
        if t in {1, 3} and _id is not None:
            await 备战天赋(d, _id)
    else:
        # 当前为休赛期，不在报名时间、还没有入场券玄铁令
        # 报名匹配模式
        await d.get("cmd=ascendheaven&op=signup&type=2")
        d.log(d.find())

    if DateTime.week() != 4:
        return

    # 飞升大作战
    await d.get("cmd=ascendheaven")
    if "赛季结算中" not in d.html:
        return

    # 境界修为
    await d.get("cmd=ascendheaven&op=showrealm")
    for s in d.findall(r"season=(\d+)"):
        # 领取奖励
        await d.get(f"cmd=ascendheaven&op=getrealmgift&season={s}")
        d.log(d.find())


async def 许愿帮铺(d: DaLeDou):
    exchange_config: dict[int, dict] = d.config("深渊之潮.exchange")
    for _id, item in exchange_config.items():
        material_name: str = item["material_name"]
        quantity: int = item["quantity"]
        if quantity <= 0:
            continue
        if "之书" in material_name:
            quotient = quantity // 25
        else:
            quotient = 0

        count = 0
        for _ in range(quotient):
            await d.get(f"cmd=abysstide&op=wishexchangetimes&id={_id}&times=25")
            d.log(d.find())
            if "成功" not in d.html:
                break
            count += 25
        for _ in range(quantity - count):
            await d.get(f"cmd=abysstide&op=wishexchange&id={_id}")
            d.log(d.find())
            if "成功" not in d.html:
                break


@register()
async def 深渊之潮(d: DaLeDou):
    await c_帮派巡礼(d)
    await c_深渊秘境(d)
    if DateTime.day() == 20:
        await 许愿帮铺(d)


@register()
async def 侠客岛(d: DaLeDou):
    # 侠客行
    await d.get("cmd=knight_island&op=viewmissionindex")
    pos = d.findall(r"viewmissiondetail&amp;pos=(\d+)")
    if not pos:
        for name, duration in d.findall(r"([^<>]+?)（需要.*?任务时长：([^<]+)"):
            d.log(f"{name} -> {duration}")
        return

    config: set[str] = set(d.config("侠客岛.侠客行"))
    free_refresh_count = d.find(r"免费刷新剩余：(\d+)")
    if free_refresh_count is None:
        d.log("获取免费刷新剩余失败，将免费次数重置为0")
        free_refresh_count = 0
    else:
        free_refresh_count = int(free_refresh_count)

    for p in pos:
        for _ in range(5):
            # 侠客行
            await d.get("cmd=knight_island&op=viewmissionindex")
            reward = d.find(rf'pos={p}">接受.*?任务奖励：([^<]+)')

            # 接受
            await d.get(f"cmd=knight_island&op=viewmissiondetail&pos={p}")
            task_name = d.find(r"([^>]+?)（")
            d.log(f"{task_name} -> {reward}")

            if reward not in config and free_refresh_count > 0:
                # 刷新
                await d.get(f"cmd=knight_island&op=refreshmission&pos={p}")
                d.log(f"{task_name} -> {d.find(r'斗豆）<br />(.*?)<br />')}")
                free_refresh_count -= 1
                continue

            # 快速委派
            await d.get(f"cmd=knight_island&op=autoassign&pos={p}")
            d.log(f"{task_name} -> {d.find(r'）<br />(.*?)<br />')}")

            if "快速委派成功" in d.html:
                # 开始任务
                await d.get(f"cmd=knight_island&op=begin&pos={p}")
                d.log(f"{task_name} -> {d.find(r'斗豆）<br />(.*?)<br />')}")
                break

            if "符合条件侠士数量不足" in d.html and free_refresh_count > 0:
                # 刷新
                await d.get(f"cmd=knight_island&op=refreshmission&pos={p}")
                d.log(f"{task_name} -> {d.find(r'斗豆）<br />(.*?)<br />')}")
                free_refresh_count -= 1
                continue
            else:
                d.log(f"{task_name} -> 没有免费刷新次数了")
                break


async def 八卦迷阵(d: DaLeDou):
    _data = {
        "离": 1,
        "坤": 2,
        "兑": 3,
        "乾": 4,
        "坎": 5,
        "艮": 6,
        "震": 7,
        "巽": 8,
    }
    # 八卦迷阵
    await d.get("cmd=spacerelic&op=goosip")
    result = d.find(r"([乾坤震巽坎离艮兑]{4})")
    if result is None:
        result = d.config("时空遗迹.八卦迷阵")

    for i in result:
        # 点击八卦
        await d.get(f"cmd=spacerelic&op=goosip&id={_data[i]}")
        d.log(f"{i} -> {d.find(r'分钟<br /><br />(.*?)<br />')}")
        if "恭喜您" not in d.html:
            # 你被迷阵xx击败，停留在了本层
            # 耐力不足，无法闯关
            # 你被此门上附着的阵法传送回了第一层
            # 请遵循迷阵规则进行闯关
            break
        # 恭喜您进入到下一层
        # 恭喜您已通关迷阵，快去领取奖励吧

    if "恭喜您已通关迷阵" in d.html:
        # 领取通关奖励
        await d.get("cmd=spacerelic&op=goosipgift")
        d.log(d.find(r"分钟<br /><br />(.*?)<br />"))


async def 遗迹商店(d: DaLeDou):
    exchange_config: dict[int, dict] = d.config("时空遗迹.exchange")
    for _id, item in exchange_config.items():
        material_name: str = item["material_name"]
        quantity: int = item["quantity"]
        t: int = item["type"]
        if quantity <= 0:
            continue
        quotient, remainder = divmod(quantity, 10)
        for _ in range(quotient):
            # 兑换十次
            await d.get(f"cmd=spacerelic&op=buy&type={t}&id={_id}&num=10")
            d.log(
                f"{material_name}*10 -> {d.find(r'售卖区.*?<br /><br /><br />(.*?)<')}"
            )
            if "兑换成功" not in d.html:
                break
        for _ in range(remainder):
            # 兑换一次
            await d.get(f"cmd=spacerelic&op=buy&type={t}&id={_id}&num=1")
            d.log(
                f"{material_name}*1 -> {d.find(r'售卖区.*?<br /><br /><br />(.*?)<')}"
            )
            if "兑换成功" not in d.html:
                break


async def 异兽洞窟(d: DaLeDou):
    _ids: list = d.config("时空遗迹.异兽洞窟")
    if _ids is None:
        d.log("你没有设置异兽洞窟id")
        return

    for _id in _ids:
        await d.get(f"cmd=spacerelic&op=monsterdetail&id={_id}")
        if "剩余挑战次数：0" in d.html:
            d.log("异兽洞窟没有挑战次数")
            break
        if "剩余血量：0" in d.html:
            # 扫荡
            await d.get(f"cmd=spacerelic&op=saodang&id={_id}")
        else:
            # 挑战
            await d.get(f"cmd=spacerelic&op=monsterfight&id={_id}")
        d.log(d.find(r"次数.*?<br /><br />(.*?)&"))
        if "请按顺序挑战异兽" in d.html:
            continue
        break


async def 悬赏任务(d: DaLeDou):
    data = []
    for t in [1, 2]:
        await d.get(f"cmd=spacerelic&op=task&type={t}")
        data += d.findall(r"type=(\d+)&amp;id=(\d+)")
    for t, _id in data:
        await d.get(f"cmd=spacerelic&op=task&type={t}&id={_id}")
        d.log(d.find(r"赛季任务</a><br /><br />(.*?)<"))
        if "您未完成该任务" in d.html:
            continue


async def 遗迹征伐(d: DaLeDou):
    # 遗迹征伐
    await d.get("cmd=spacerelic&op=relicindex")
    year = d.find(r"(\d+)年")
    month = d.find(r"(\d+)月")
    day = d.find(r"(\d+)日")
    if year is None or month is None or day is None:
        d.log("获取结束日期失败")
        return

    # 当前日期
    current_date = DateTime.current_date()
    # 结束前一天日期
    end_date = DateTime.get_offset_date(int(year), int(month), int(day))
    if current_date == end_date:
        # 悬赏任务-登录奖励
        await d.get("cmd=spacerelic&op=task&type=1&id=1")
        d.log(d.find(r"赛季任务</a><br /><br />(.*?)<"))
        # 排行奖励
        await d.get("cmd=spacerelic&op=getrank")
        d.log(d.find(r"奖励</a><br /><br />(.*?)<"))

        await 遗迹商店(d)
        return

    # 结束前七天日期
    end_date = DateTime.get_offset_date(int(year), int(month), int(day), 7)
    if current_date >= end_date:
        # 第八周（结束日期上周四~本周三）
        d.log("当前处于休赛期，结束前一天领取登录奖励、赛季奖励和悬赏商店兑换")
        return

    await 异兽洞窟(d)

    # 联合征伐挑战
    await d.get("cmd=spacerelic&op=bossfight")
    d.log(d.find(r"挑战</a><br />(.*?)&"))

    await 悬赏任务(d)


@register()
async def 时空遗迹(d: DaLeDou):
    await 八卦迷阵(d)
    await 遗迹征伐(d)


@register()
async def 世界树(d: DaLeDou):
    # 世界树
    await d.get("cmd=worldtree")
    # 一键领取经验奖励
    await d.get("cmd=worldtree&op=autoget&id=1")
    d.log(d.find(r"福宝<br /><br />(.*?)<br />"))

    async def get_id() -> str | None:
        # 温养武器选择
        for t in range(4):
            await d.get(f"cmd=worldtree&op=viewweaponpage&type={t}")
            for _id in d.findall(r"weapon_id=(\d+)"):
                # 选择
                await d.get(f"cmd=worldtree&op=setweapon&weapon_id={_id}&type={t}")
                d.log(d.find(r"当前武器：(.*?)<"))
                return _id

    # 源宝树
    await d.get("cmd=worldtree&op=viewexpandindex")
    if "免费温养" not in d.html:
        d.log("没有免费温养次数")
        return

    if "weapon_id=0" in d.html and not get_id():
        d.log("没有武器可选择")
        return

    # 源宝树
    await d.get("cmd=worldtree&op=viewexpandindex")
    _id = d.find(r"weapon_id=(\d+)")
    # 免费温养
    await d.get(f"cmd=worldtree&op=dostrengh&times=1&weapon_id={_id}")
    d.log(d.find(r"规则</a><br />(.*?)<br />"))
    d.log(f"当前进度 -> {d.find(r'当前进度:(.*?)<')}")


async def 龙凰论武(d: DaLeDou):
    if 1 <= DateTime.day() <= 3:
        _id: int = d.config("龙凰之境.龙凰论武.id")
        # 报名
        await d.get(f"cmd=dragonphoenix&op=sign&zone={_id}")
        d.log(d.find())
    elif 4 <= DateTime.day() <= 25:
        await c_龙凰论武(d)
        # 每日领奖
        await d.get("cmd=dragonphoenix&op=gift")
        d.log(d.find(r"/\d+</a><br /><br />(.*?)<"))
    elif DateTime.day() == 27:
        # 排行奖励
        await d.get("cmd=dragonphoenix&op=rankreward")
        d.log(d.find(r"<br /><br /><br />(.*?)<"))


async def 龙凰云集(d: DaLeDou):
    if DateTime.day() != 27:
        return

    # 龙凰云集
    await d.get("cmd=dragonphoenix&op=yunji")
    for _id in d.findall(r"idx=(\d+)"):
        # 领奖
        await d.get(f"cmd=dragonphoenix&op=reward&idx={_id}")
        d.log(d.find(r"<br /><br /><br />(.*?)<"))
        if "当前无可领取奖励" in d.html:
            break

    exchange_config: dict[int, dict] = d.config("龙凰之境.exchange")
    for _id, item in exchange_config.items():
        material_name: str = item["material_name"]
        quantity: int = item["quantity"]
        if quantity <= 0:
            continue
        quotient, remainder = divmod(quantity, 10)
        for _ in range(quotient):
            await d.get(f"cmd=dragonphoenix&op=buy&id={_id}&num=10")
            d.log(f"{material_name}*10 -> {d.find(r'<br /><br /><br />(.*?)<')}")
            if "成功" not in d.html:
                break
        for _ in range(remainder):
            await d.get(f"cmd=dragonphoenix&op=buy&id={_id}&num=1")
            d.log(f"{material_name}*1 -> {d.find(r'<br /><br /><br />(.*?)<')}")
            if "成功" not in d.html:
                break


async def 龙吟破阵(d: DaLeDou):
    if not (1 <= DateTime.day() <= 3):
        return

    # 领取
    await d.get("cmd=dragonphoenix&op=getlastreward")
    d.log(d.find(r"领取<br /><br />(.*?)<"))


@register()
async def 龙凰之境(d: DaLeDou):
    await 龙凰论武(d)
    await 龙凰云集(d)
    await 龙吟破阵(d)


async def 增强经脉(d: DaLeDou):
    # 经脉
    await d.get("cmd=intfmerid&sub=1")
    if "关闭" in d.html:
        # 关闭合成两次确认
        await d.get("cmd=intfmerid&sub=19")
        d.log("传功 -> 关闭合成两次确认")
    if "取消" in d.html and "doudou=0" in d.html:
        # 取消传功符不足用斗豆代替
        await d.get("cmd=intfmerid&sub=21&doudou=0")
        d.log("传功 -> 取消传功符不足用斗豆代替")

    count = d.find(r"传功符</a>:(\d+)")
    if count is None:
        d.log("传功 -> 获取传功符数量失败")
        return

    if int(count) < 200:
        d.log("传功 -> 传功符数量不足200")
        return

    for _ in range(12):
        # 经脉
        await d.get("cmd=intfmerid&sub=1")
        _id = d.find(r'master_id=(\d+)">传功</a>')

        # 传功
        await d.get(f"cmd=intfmerid&sub=2&master_id={_id}")
        d.log(f"传功 -> {d.find(r'</p>(.*?)<p>')}")
        if "传功符不足！" in d.html:
            return

        # 一键拾取
        await d.get("cmd=intfmerid&sub=5")
        d.log(f"传功 -> {d.find(r'</p>(.*?)<p>')}")
        # 一键合成
        await d.get("cmd=intfmerid&sub=10&op=4")
        d.log(f"传功 -> {d.find(r'</p>(.*?)<p>')}")


async def 助阵(d: DaLeDou):
    """无字天书或者河图洛书提升3次"""
    data = {
        1: [0],
        2: [0, 1],
        3: [0, 1, 2],
        9: [0, 1, 2],
        4: [0, 1, 2, 3],
        5: [0, 1, 2, 3],
        6: [0, 1, 2, 3],
        7: [0, 1, 2, 3],
        8: [0, 1, 2, 3, 4],
        10: [0, 1, 2, 3],
        11: [0, 1, 2, 3],
        12: [0, 1, 2, 3],
        13: [0, 1, 2, 3],
        14: [0, 1, 2, 3],
        15: [0, 1, 2, 3],
        16: [0, 1, 2, 3],
        17: [0, 1, 2, 3],
        18: [0, 1, 2, 3, 4],
    }

    def get_id_index():
        for f_id, index_list in data.items():
            for index in index_list:
                yield (f_id, index)

    count = 0
    for _id, i in get_id_index():
        if count == 3:
            break
        p = f"cmd=formation&type=4&formationid={_id}&attrindex={i}&times=1"
        for _ in range(3):
            # 提升
            await d.get(p)
            if "助阵组合所需佣兵不满足条件，不能提升助阵属性经验" in d.html:
                d.log(f"助阵 -> {d.find(r'<br /><br />(.*?)。')}")
                return
            elif "阅历不足" in d.html:
                d.log(f"助阵 -> {d.find(r'<br /><br />(.*?)，')}")
                return

            d.log(f"助阵 -> {d.find()}")
            if "提升成功" in d.html:
                count += 1
            elif "经验值已经达到最大" in d.html:
                break
            elif "你还没有激活该属性" in d.html:
                return


async def 查看好友资料(d: DaLeDou):
    # 乐斗助手
    await d.get("cmd=view&type=6")
    if "开启查看好友信息和收徒" in d.html:
        #  开启查看好友信息和收徒
        await d.get("cmd=set&type=1")
        d.log("查看好友 -> 开启查看好友信息和收徒")
    # 好友第2页
    await d.get("cmd=friendlist&page=2")
    for uin in d.findall(r"</a>\d+.*?B_UID=(\d+)"):
        d.log(f"查看好友 -> {uin}")
        await d.get(f"cmd=totalinfo&B_UID={uin}")


async def 兵法研习(d: DaLeDou):
    """
    兵法      消耗     id    功能
    金兰之泽  孙子兵法  2544  增加生命
    雷霆一击  孙子兵法  2570  增加伤害
    残暴攻势  武穆遗书  21001 增加暴击几率
    不屈意志  武穆遗书  21032 降低受到暴击几率
    """
    for _id in [21001, 2570, 21032, 2544]:
        await d.get(f"cmd=brofight&subtype=12&op=practice&baseid={_id}")
        d.log(f"兵法 -> {d.find(r'武穆遗书：\d+个<br />(.*?)<br />')}")
        if "研习成功" in d.html:
            break


async def 挑战陌生人(d: DaLeDou):
    # 斗友
    await d.get("cmd=friendlist&type=1")
    for u in d.findall(r"</a>\d+.*?B_UID=(\d+)")[:4]:
        await d.get(f"cmd=fight&B_UID={u}&page=1&type=9")
        d.log(f"挑战陌生人 -> {d.find(r'删</a><br />(.*?)！')}")


@register()
async def 任务(d: DaLeDou):
    # 日常任务
    task_html = await d.get("cmd=task&sub=1")
    if "助阵" in task_html:
        await 助阵(d)
    if "增强经脉" in task_html:
        await 增强经脉(d)
    if "查看好友资料" in task_html:
        await 查看好友资料(d)
    if "兵法研习" in task_html:
        await 兵法研习(d)
    if "挑战陌生人" in task_html:
        await 挑战陌生人(d)

    # 一键完成任务
    await d.get("cmd=task&sub=7")
    for k, v in d.findall(r'id=\d+">(.*?)</a>.*?>(.*?)</a>'):
        d.log(f"{k} -> {v}")


async def 帮派供奉(d: DaLeDou):
    _ids: list = d.config("我的帮派.帮派供奉")
    if _ids is None:
        return

    for _id in _ids:
        for _ in range(5):
            # 供奉
            await d.get(f"cmd=oblation&id={_id}&page=1")
            if "供奉成功" in d.html:
                d.log(f"{_id} -> {d.find()}")
                continue
            d.log(f"{_id} -> {d.find(r'】</p><p>(.*?)<br />')}")
            break
        if "每天最多供奉5次" in d.html:
            break


async def 帮派任务(d: DaLeDou):
    # 帮派任务
    task_html = await d.get("cmd=factiontask&sub=1")
    tasks = {
        "帮战冠军": "cmd=facwar&sub=4",
        "查看帮战": "cmd=facwar&sub=4",
        "查看帮贡": "cmd=factionhr&subtype=14",
        "查看祭坛": "cmd=altar",
        "查看踢馆": "cmd=facchallenge&subtype=0",
        "查看要闻": "cmd=factionop&subtype=8&pageno=1&type=2",
        # '加速贡献': 'cmd=use&id=3038&store_type=1&page=1',
        "粮草掠夺": "cmd=forage_war",
    }
    for name, url in tasks.items():
        if name in task_html:
            await d.get(url)
            d.log(name)
    if "帮派修炼" in task_html:
        count = 0
        for _id in [2727, 2758, 2505, 2536, 2437, 2442, 2377, 2399, 2429]:
            for _ in range(4):
                # 修炼
                await d.get(f"cmd=factiontrain&type=2&id={_id}&num=1&i_p_w=num%7C")
                d.log(d.find(r"规则说明</a><br />(.*?)<br />"))
                if "技能经验增加" in d.html:
                    count += 1
                    continue
                # 帮贡不足
                # 你今天获得技能升级经验已达到最大！
                # 你需要提升帮派等级来让你进行下一步的修炼
                break
            if count == 4:
                break
    # 帮派任务
    await d.get("cmd=factiontask&sub=1")
    for _id in d.findall(r'id=(\d+)">领取奖励</a>'):
        # 领取奖励
        await d.get(f"cmd=factiontask&sub=3&id={_id}")
        d.log(d.find(r"日常任务</a><br />(.*?)<br />"))


@register()
async def 我的帮派(d: DaLeDou):
    # 我的帮派
    await d.get("cmd=factionop&subtype=3&facid=0")
    if "你的职位" not in d.html:
        d.log("您还没有加入帮派")
        return

    await 帮派供奉(d)
    await 帮派任务(d)

    if DateTime.week() != 7:
        return

    # 领取奖励 》报名帮战 》激活祝福
    for sub in [4, 9, 6]:
        await d.get(f"cmd=facwar&sub={sub}")
        d.log(d.find(r"</p>(.*?)<br /><a.*?查看上届"))


@register()
async def 帮派祭坛(d: DaLeDou):
    # 帮派祭坛
    await d.get("cmd=altar")
    for _ in range(30):
        if "转动轮盘" in d.html:
            # 转动轮盘
            await d.get("cmd=altar&op=spinwheel")
            if "转动轮盘" in d.html:
                d.log(d.find())
            if "转转券不足" in d.html or "已达转转券转动次数上限" in d.html:
                return
        if "【随机分配】" in d.html:
            all_disbanded = True
            data = d.findall(r"op=(.*?)&amp;id=(\d+)")
            for op, _id in data:
                # 选择
                await d.get(f"cmd=altar&op={op}&id={_id}")
                if "选择路线" in d.html:
                    # 向前|向左|向右
                    await d.get(f"cmd=altar&op=dosteal&id={_id}")
                if "该帮派已解散" in d.html or "系统繁忙" in d.html:
                    d.log(d.find(r"<br /><br />(.*?)<br />"))
                    continue
                all_disbanded = False
                if "转动轮盘" in d.html:
                    d.log(d.find())
                    break
            if all_disbanded and data:
                return
        if "领取奖励" in d.html:
            await d.get("cmd=altar&op=drawreward")
            d.log(d.find())


@register()
async def 每日奖励(d: DaLeDou):
    for key in ["login", "meridian", "daren", "wuzitianshu"]:
        # 每日奖励
        await d.get(f"cmd=dailygift&op=draw&key={key}")
        d.log(d.find())


@register()
async def 领取徒弟经验(d: DaLeDou):
    # 领取徒弟经验
    await d.get("cmd=exp")
    d.log(d.find(r"每日奖励</a><br />(.*?)<br />"))


@register()
async def 今日活跃度(d: DaLeDou):
    # 今日活跃度
    await d.get("cmd=liveness")
    if activity_level := d.find(r"今日活跃度：(\d+)"):
        if 77 <= int(activity_level) < 80 and "16.[0/1]" in d.html:
            d.log(activity_level)
            await 助阵(d)
        elif 75 <= int(activity_level) < 80 and "15.[0/1]" in d.html:
            d.log(activity_level)
            await 增强经脉(d)

    # 今日活跃度
    await d.get("cmd=liveness")
    d.log(d.find(r"今日活跃度：(\d+)"))
    if "帮派总活跃" in d.html:
        d.log(d.find(r"帮派总活跃：(.*?)<"))

    # 领取今日活跃度礼包
    for giftbag_id in range(1, 5):
        await d.get(f"cmd=liveness_getgiftbag&giftbagid={giftbag_id}&action=1")
        d.log(d.find(r"】<br />(.*?)<p>"))

    # 领取帮派总活跃奖励
    await d.get("cmd=factionop&subtype=18")
    if "创建帮派" in d.html:
        d.log(d.find(r"帮派</a><br />(.*?)<br />"))
    else:
        d.log(d.find())


@register()
async def 仙武修真(d: DaLeDou):
    for task_id in range(1, 4):
        # 领取
        await d.get(f"cmd=immortals&op=getreward&taskid={task_id}")
        d.log(d.find(r"帮助</a><br />(.*?)<br />"))

    count = d.find(r"剩余挑战次数：(\d+)")
    if count is None:
        d.log("获取挑战次数失败")
        return

    for _ in range(int(count)):
        _id = random.choice([1, 2, 3])
        # 寻访
        await d.get(f"cmd=immortals&op=visitimmortals&mountainId={_id}")
        d.log(d.find(r"帮助</a><br />(.*?)<"))
        d.log(f"本次寻访：{d.find(r'本次寻访：.*?>(.*?)<')}")
        # 挑战
        await d.get("cmd=immortals&op=fightimmortals")
        d.log(d.find(r"帮助</a><br />(.*?)<"))


@register()
async def 乐斗黄历(d: DaLeDou):
    # 领取
    await d.get("cmd=calender&op=2")
    d.log(d.find(r"<br /><br />(.*?)<br />"))
    # 占卜
    await d.get("cmd=calender&op=4")
    d.log(d.find(r"<br /><br />(.*?)<br />"))


@register()
async def 器魂附魔(d: DaLeDou):
    for _id in range(1, 4):
        # 领取
        await d.get(f"cmd=enchant&op=gettaskreward&task_id={_id}")
        d.log(d.find())


@register()
async def 兵法(d: DaLeDou):
    if DateTime.week() == 4:
        # 助威
        await d.get("cmd=brofight&subtype=13")
        _id = d.find(r"teamid=(\d+).*?助威</a>")
        # 确定
        await d.get(f"cmd=brofight&subtype=13&teamid={_id}&type=5&op=cheer")
        d.log(d.find(r"领奖</a><br />(.*?)<br />"))

    if DateTime.week() != 6:
        return

    # 领奖
    await d.get("cmd=brofight&subtype=13&op=draw")
    d.log(d.find(r"领奖</a><br />(.*?)<br />"))

    for t in range(1, 6):
        await d.get(f"cmd=brofight&subtype=10&type={t}")
        for remainder, u in d.findall(r"50000.*?(\d+).*?champion_uin=(\d+)"):
            if remainder == "0":
                continue
            # 领斗币
            await d.get(f"cmd=brofight&subtype=10&op=draw&champion_uin={u}&type={t}")
            d.log(d.find(r"排行</a><br />(.*?)<br />"))
            return


def get_boss_id():
    """返回历练高等级到低等级场景每关最后两个BOSS的id"""
    for _id in range(6394, 6013, -20):
        yield _id
        yield (_id - 1)


async def 点亮(d: DaLeDou) -> bool:
    # 点亮南瓜灯
    await d.get("cmd=hallowmas&gb_id=1")
    while True:
        if cushaw_id := d.findall(r"cushaw_id=(\d+)"):
            c_id = random.choice(cushaw_id)
            # 南瓜
            await d.get(f"cmd=hallowmas&gb_id=4&cushaw_id={c_id}")
            d.log(d.find())
            if "活力" in d.html:
                return True
        if "请领取今日的活跃度礼包来获得蜡烛吧" in d.html:
            break
    return False


async def 点亮南瓜灯(d: DaLeDou):
    # 乐斗助手
    await d.get("cmd=view&type=6")
    if "取消自动使用活力药水" in d.html:
        # 取消自动使用活力药水
        await d.get("cmd=set&type=11")
        d.log("取消自动使用活力药水")
    for _id in get_boss_id():
        count = 3
        while count:
            await d.get(f"cmd=mappush&subtype=3&npcid={_id}&pageid=2")
            if "您还没有打到该历练场景" in d.html:
                d.log(d.find(r"介绍</a><br />(.*?)<br />"), "历练")
                break
            d.log(d.find(r"\d+<br />(.*?)<"), "历练")
            if "活力不足" in d.html:
                if not await 点亮(d):
                    return
                continue
            elif "BOSS" not in d.html:
                # 你今天和xx挑战次数已经达到上限了，请明天再来挑战吧
                # 还不能挑战
                break
            count -= 1


@register()
async def 万圣节(d: DaLeDou):
    await 点亮南瓜灯(d)

    # 万圣节
    await d.get("cmd=hallowmas")
    month, day = d.findall(r"(\d+)月(\d+)日6点")[0]

    # 结束前一天日期
    end_date = DateTime.get_offset_date(DateTime.year(), int(month), int(day))
    if DateTime.current_date() == end_date:
        # 兑换礼包B 消耗40个南瓜灯
        await d.get("cmd=hallowmas&gb_id=6")
        d.log(d.find())
        # 兑换礼包A 消耗20个南瓜灯
        await d.get("cmd=hallowmas&gb_id=5")
        d.log(d.find())


@register()
async def 能量棒(d: DaLeDou):
    # 能量棒
    await d.get("cmd=newAct&subtype=108&op=0")
    data = d.findall(r"id=(\d+)")
    if not data:
        d.log("没有可领取的能量棒")
        return

    # 乐斗助手
    await d.get("cmd=view&type=6")
    if "取消自动使用活力药水" in d.html:
        # 取消自动使用活力药水
        await d.get("cmd=set&type=11")
        d.log("取消自动使用活力药水")

    for _id in get_boss_id():
        count = 3
        while count:
            await d.get(f"cmd=mappush&subtype=3&npcid={_id}&pageid=2")
            if "您还没有打到该历练场景" in d.html:
                d.log(d.find(r"介绍</a><br />(.*?)<br />"), "历练")
                break
            d.log(d.find(r"\d+<br />(.*?)<"), "历练")
            if "活力不足" in d.html:
                if not data:
                    return
                # 领取活力能量棒
                await d.get(f"cmd=newAct&subtype=108&op=1&id={data.pop()}")
                d.log(d.find(r"<br /><br />(.*?)<"))
                continue
            elif "BOSS" not in d.html:
                # 你今天和xx挑战次数已经达到上限了，请明天再来挑战吧
                # 还不能挑战
                break
            count -= 1


@register()
async def 大笨钟(d: DaLeDou):
    await c_大笨钟(d)


@register()
async def 幸运金蛋(d: DaLeDou):
    await c_幸运金蛋(d)


@register()
async def 客栈同福(d: DaLeDou):
    await c_客栈同福(d)


@register()
async def 反向历练(d: DaLeDou, link_text: str):
    if not d.config(f"{link_text}.历练"):
        return

    # 乐斗助手
    await d.get("cmd=view&type=6")
    if "开启自动使用活力药水" in d.html:
        # 开启自动使用活力药水
        await d.get("cmd=set&type=11")
        d.log("历练 -> 开启自动使用活力药水")

    for _id in get_boss_id():
        for _ in range(3):
            await d.get(f"cmd=mappush&subtype=3&mapid=6&npcid={_id}&pageid=2")
            if "您还没有打到该历练场景" in d.html:
                d.log(f"历练 -> {d.find(r'介绍</a><br />(.*?)<br />')}")
                break
            d.log(f"历练 -> {d.find(r'阅历值：\d+<br />(.*?)<br />')}")
            if "活力不足" in d.html or "活力药水使用次数已达到每日上限" in d.html:
                return
            elif "BOSS" not in d.html:
                # 你今天和xx挑战次数已经达到上限了，请明天再来挑战吧
                # 还不能挑战
                break


@register()
async def 节日福利(d: DaLeDou):
    await 反向历练(d, "节日福利")


@register()
async def 双旦福利(d: DaLeDou):
    await 反向历练(d, "双旦福利")


@register()
async def 金秋福利(d: DaLeDou):
    await 反向历练(d, "金秋福利")


@register()
async def 春节福利(d: DaLeDou):
    await 反向历练(d, "春节福利")


@register()
async def 新春拜年(d: DaLeDou):
    # 新春拜年
    await d.get("cmd=newAct&subtype=147")
    if "op=1" in d.html:
        for i in random.sample(range(5), 3):
            # 选中
            await d.get(f"cmd=newAct&subtype=147&op=1&index={i}")
        # 赠礼
        await d.get("cmd=newAct&subtype=147&op=2")
        d.log("已赠礼")
