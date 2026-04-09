import random

from src.utils.daledou import DaLeDou
from src.utils.date_time import DateTime


async def c_get_material_quantity(d: DaLeDou, item_id: str | int) -> int:
    """返回背包物品数量"""
    await d.get(f"cmd=owngoods&id={item_id}")
    if "很抱歉" in d.html:
        return 0

    number_str = d.find(r"数量：(\d+)")
    if number_str is None:
        return 0
    return int(number_str)


async def c_get_doushenta_cd(d: DaLeDou) -> int:
    """返回斗神塔冷却时间"""
    # 达人等级对应斗神塔CD时间
    cd = {
        "1": 7,
        "2": 6,
        "3": 5,
        "4": 4,
        "5": 3,
        "6": 2,
        "7": 1,
        "8": 1,
        "9": 1,
        "10": 1,
    }
    # 乐斗达人
    await d.get("cmd=ledouvip")
    if level := d.find(r"当前级别：(\d+)"):
        return cd[level]
    else:
        # 还未成为达人
        return 10


async def c_邪神秘宝(d: DaLeDou):
    """
    高级秘宝: 抽奖一次
    极品秘宝: 抽奖一次
    """
    for i in [0, 1]:
        # 免费一次 或 抽奖一次
        await d.get(f"cmd=tenlottery&op=2&type={i}")
        d.log(d.find(r"】</p>(.*?)<br />"))


async def 帮派宝库(d: DaLeDou):
    """领取礼包"""
    for _ in range(20):
        # 帮派宝库
        await d.get("cmd=fac_corp&op=0")
        data = d.findall(r'gift_id=(\d+)&amp;type=(\d+)">点击领取')
        if not data:
            break

        for _id, t in data:
            await d.get(f"cmd=fac_corp&op=3&gift_id={_id}&type={t}")
            d.log(f"帮派宝库 -> {d.find(r'</p>(.*?)<br />')}")
            if "恭喜您领取了" in d.html:
                continue
            # 领取上限
            # 入帮24小时才能领取商会礼包
            return


async def 交易会所(d: DaLeDou):
    """交易物品"""
    config: list[str] = d.config("帮派商会.交易会所")
    if config is None:
        return

    # 交易会所
    await d.get("cmd=fac_corp&op=1")
    if "已交易" in d.html:
        return

    for material_name, t, _id in d.findall(
        r"要(.*?)，.*?type=(\d+)&amp;goods_id=(\d+)"
    ):
        if not any(i in material_name for i in config):
            continue
        # 点击交易
        await d.get(f"cmd=fac_corp&op=4&type={t}&goods_id={_id}")
        d.log(f"{material_name} -> {d.find(r'</p>(.*?)<br />')}")


async def 兑换商店(d: DaLeDou):
    """兑换物品"""
    config: list[str] = d.config("帮派商会.兑换商店")
    if config is None:
        return

    # 兑换商店
    await d.get("cmd=fac_corp&op=2")
    if "已兑换" in d.html:
        return

    for material_name, _id in d.findall(r"</a><br />(.*?)&.*?type_id=(\d+)"):
        if not any(i in material_name for i in config):
            continue
        # 兑换
        await d.get(f"cmd=fac_corp&op=5&type_id={_id}")
        d.log(d.find(r"</p>(.*?)<br />"))


async def c_帮派商会(d: DaLeDou):
    await 帮派宝库(d)
    await 交易会所(d)
    await 兑换商店(d)


async def c_任务派遣中心(d: DaLeDou):
    """
    领取奖励: 最多3次
    接受: 最多3次（优先S、B级，如果没有免费刷新次数则选择A级）
    """
    # 任务派遣中心
    await d.get("cmd=missionassign&subtype=0")
    for _id in d.findall(r'0时0分.*?mission_id=(.*?)">查看'):
        # 查看
        await d.get(f"cmd=missionassign&subtype=1&mission_id={_id}")
        task_name = d.find(r"任务名称：(.*?)<")
        # 领取奖励
        await d.get(f"cmd=missionassign&subtype=5&mission_id={_id}")
        d.log(f"{task_name} -> {d.find(r'\[任务派遣中心\](.*?)<br />')}")

    fail_ids = set()
    is_maximums = False
    is_has_free_refresh_count = True
    for _ in range(5):
        # 任务派遣中心
        await d.get("cmd=missionassign&subtype=0")
        S_ids = d.findall(r'-S&nbsp;所需时间.*?_id=(\d+)">接受')
        A_ids = d.findall(r'-A&nbsp;所需时间.*?_id=(\d+)">接受')
        B_ids = d.findall(r'-B&nbsp;所需时间.*?_id=(\d+)">接受')

        _ids = S_ids + B_ids

        if not is_has_free_refresh_count:
            _ids = A_ids
            if set(_ids).issubset(fail_ids):
                break

        for _id in _ids:
            # 接受
            await d.get(f"cmd=missionassign&subtype=2&mission_id={_id}")
            task_name = d.find(r"任务名称：(.*?)<")
            # 快速委派
            await d.get(f"cmd=missionassign&subtype=7&mission_id={_id}")
            if "设置佣兵成功" not in d.html:
                d.log(f"{task_name} -> {d.find(r'】<br /><br />(.*?)<')}")
                fail_ids.add(_id)
                continue
            d.log(f"{task_name} -> {d.find(r'】</p>(.*?)<')}")

            # 开始任务
            await d.get(f"cmd=missionassign&subtype=8&mission_id={_id}")
            if "当前可执行任务数已达上限" in d.html:
                d.log(f"{task_name} -> {d.find(r'】<br /><br />(.*?)<')}")
                is_maximums = True
                break
            d.log(f"{task_name} -> {d.find(r'】</p>(.*?)<')}")

            if d.html.count("查看") == 3 or "今日已领取了全部任务" in d.html:
                is_maximums = True
                break

        if is_maximums:
            break

        if not is_has_free_refresh_count:
            continue

        # 任务派遣中心
        await d.get("cmd=missionassign&subtype=0")
        if "本次消耗：0斗豆" in d.html:
            # 刷新任务
            await d.get("cmd=missionassign&subtype=3")
            d.log("刷新任务 -> 免费刷新成功")
        else:
            d.log("刷新任务 -> 没有免费刷新次数了")
            is_has_free_refresh_count = False

    # 任务派遣中心
    await d.get("cmd=missionassign&subtype=0")
    for info in d.findall(r"<br />(.*?)&nbsp;<a.*?查看"):
        d.log(f"当前任务 -> {info}")


async def c_侠士客栈(d: DaLeDou):
    """
    领取奖励: 最多3次
    黑市商人: 换取物品
    """
    # 侠士客栈
    await d.get("cmd=warriorinn")
    for t, n in d.findall(r"type=(\d+)&amp;num=(\d+)"):
        # 领取奖励
        await d.get(f"cmd=warriorinn&op=getlobbyreward&type={t}&num={n}")
        d.log(d.find(r"侠士客栈<br />(.*?)<br />"))

    for p in d.findall(r'pos=(\d+)">前来捣乱的'):
        # 与TA理论
        await d.get(f"cmd=warriorinn&op=exceptadventure&pos={p}")
        d.log(d.find(r"侠士客栈<br />(.*?)<"))

    config: list[str] = d.config("侠士客栈.黑市商人")
    if config is None:
        return
    for p in d.findall(r'pos=(\d+)">黑市商人'):
        # 与TA交换
        await d.get(f"cmd=warriorinn&op=confirmadventure&pos={p}&type=0")
        for text in config:
            if text in d.html:
                d.log(d.find(r"物品交换<br /><br />(.*?)<br />"))
                # 确认
                await d.get(f"cmd=warriorinn&op=exceptadventure&pos={p}")
                d.log(d.find(r"侠士客栈<br />(.*?)<br />"))


async def c_帮派巡礼(d: DaLeDou):
    # 领取巡游赠礼
    await d.get("cmd=abysstide&op=getfactiongift")
    d.log(d.find())


async def c_深渊秘境(d: DaLeDou):
    exchange_count: int = d.config("深渊之潮.深渊秘境.count")
    _id: int = d.config("深渊之潮.深渊秘境.id")

    for _ in range(exchange_count):
        # 兑换
        await d.get("cmd=abysstide&op=addaccess")
        d.log(d.find())
        if "无法继续兑换挑战次数" in d.html:
            break

    # 深渊秘境
    await d.get("cmd=abysstide&op=viewallabyss")
    count = d.find(r"副本次数：(\d+)")
    if count is None:
        d.log("获取副本次数失败")
        return

    for _ in range(int(count)):
        await d.get(f"cmd=abysstide&op=enterabyss&id={_id}")
        if "开始挑战" not in d.html:
            # 暂无可用挑战次数
            # 该副本需要顺序通关解锁
            break

        for _ in range(5):
            # 开始挑战
            await d.get("cmd=abysstide&op=beginfight")
            d.log(d.find())
            if "憾负于" in d.html:
                break

        # 退出副本
        await d.get("cmd=abysstide&op=endabyss")
        d.log(d.find())


async def c_龙凰论武(d: DaLeDou):
    """每月4~25号随机挑战"""
    if not (4 <= DateTime.day() <= 25):
        return

    # 龙凰之境
    await d.get("cmd=dragonphoenix&op=lunwu")
    if "已报名" in d.html:
        d.log("系统已随机报名，次日才能挑战")
        return
    elif "论武榜" not in d.html:
        d.log("进入论武异常，无法挑战")
        return

    count: int = d.config("龙凰之境.龙凰论武.count")
    for _ in range(count):
        data = d.findall(r"uin=(\d+).*?idx=(\d+)")
        uin, _idx = random.choice(data)
        # 挑战
        await d.get(f"cmd=dragonphoenix&op=pk&zone=1&uin={uin}&idx={_idx}")
        d.log(d.find(r"/\d+</a><br /><br />(.*?)<"))
        if "挑战次数不足" in d.html:
            break
        elif "冷却中" in d.html:
            break


async def c_客栈同福(d: DaLeDou):
    """出现指定字符时献酒"""
    config: list = d.config("客栈同福.献酒")
    if config is None:
        d.log("你没有设置出现字符")
        return

    # 客栈同福
    await d.get("cmd=newAct&subtype=154")
    count = d.find(r"现有黄酒数量：(\d+)")
    if count is None:
        d.log("获取黄酒数量失败")
        return
    if count == "0":
        d.log("黄酒数量不足")
        return

    is_libation = False
    for _ in range(int(count)):
        for pattern in config:
            # 客栈同福
            await d.get("cmd=newAct&subtype=154")
            if pattern not in d.html:
                continue
            is_libation = True
            # 献酒
            await d.get("cmd=newAct&subtype=155")
            d.log(d.find(r"】<br /><p>(.*?)<br />"))
            if "黄酒不足" in d.html:
                return
        if not is_libation:
            d.log("没有找到匹配，本次无操作")
            break


async def c_幸运金蛋(d: DaLeDou):
    # 幸运金蛋
    await d.get("cmd=newAct&subtype=110&op=0")
    if i := d.find(r"index=(\d+)"):
        # 砸金蛋
        await d.get(f"cmd=newAct&subtype=110&op=1&index={i}")
        d.log(d.find(r"】<br /><br />(.*?)<br />"))
    else:
        d.log("没有砸蛋次数或者时间已过")


async def c_大笨钟(d: DaLeDou):
    # 领取
    await d.get("cmd=newAct&subtype=18")
    d.log(d.find(r"<br /><br /><br />(.*?)<br />"))
