"""
本模块抽离了 one.py 和 two.py 两个模块的公共任务函数
"""

import random

from ..core.daledou import DaLeDou


def c_邪神秘宝(d: DaLeDou):
    """高级秘宝和极品秘宝免费一次或者抽奖一次"""
    for i in [0, 1]:
        # 免费一次 或 抽奖一次
        d.get(f"cmd=tenlottery&op=2&type={i}")
        d.log(d.find(r"】</p>(.*?)<br />")).append()


def 帮派宝库(d: DaLeDou):
    for _ in range(20):
        # 帮派宝库
        d.get("cmd=fac_corp&op=0")
        data = d.findall(r'gift_id=(\d+)&amp;type=(\d+)">点击领取')
        if not data:
            d.log("帮派宝库没有礼包领取", "帮派商会-帮派宝库").append()
            return

        for _id, t in data:
            d.get(f"cmd=fac_corp&op=3&gift_id={_id}&type={t}")
            d.log(d.find(r"</p>(.*?)<br />"), "帮派商会-帮派宝库").append()
            if "恭喜您领取了" in d.html:
                continue
            # 领取上限
            # 入帮24小时才能领取商会礼包
            return


def 交易会所(d: DaLeDou):
    config: dict = d.config["帮派商会"]["交易会所"]
    if config is None:
        return

    # 交易会所
    d.get("cmd=fac_corp&op=1")
    if "已交易" in d.html:
        return

    data = []
    for mode in config:
        data += d.findall(rf"{mode}.*?type=(\d+)&amp;goods_id=(\d+)")
    for t, _id in data:
        # 兑换
        d.get(f"cmd=fac_corp&op=4&type={t}&goods_id={_id}")
        d.log(d.find(r"</p>(.*?)<br />"), f"帮派商会-交易-{_id}").append()


def 兑换商店(d: DaLeDou):
    config: dict = d.config["帮派商会"]["兑换商店"]
    if config is None:
        return

    # 兑换商店
    d.get("cmd=fac_corp&op=2")
    if "已兑换" in d.html:
        return

    data = []
    for mode in config:
        data += d.findall(rf"{mode}.*?type_id=(\d+)")
    for t in data:
        # 兑换
        d.get(f"cmd=fac_corp&op=5&type_id={t}")
        d.log(d.find(r"</p>(.*?)<br />"), f"帮派商会-兑换-{t}").append()


def c_帮派商会(d: DaLeDou):
    """
    帮派宝库：每天领取礼包
    交易会所：每天交易物品
    兑换商店：每天兑换物品
    """
    帮派宝库(d)
    交易会所(d)
    兑换商店(d)


def c_任务派遣中心(d: DaLeDou):
    """
    领取奖励：每天最多3次
    接受：每天最多3次；优先S、A级，如果S、A已尝试且没有免费刷新次数则选择B级
    """
    base_name = "任务派遣中心"
    # 任务派遣中心
    d.get("cmd=missionassign&subtype=0")
    for _id in d.findall(r'0时0分.*?mission_id=(.*?)">查看'):
        # 查看
        d.get(f"cmd=missionassign&subtype=1&mission_id={_id}")
        task_name = f"{base_name}-{d.find(r'任务名称：(.*?)<')}"
        # 领取奖励
        d.get(f"cmd=missionassign&subtype=5&mission_id={_id}")
        d.log(d.find(r"\[任务派遣中心\](.*?)<br />"), task_name).append()

    fail_ids = set()
    is_maximums = False
    is_has_free_refresh_count = True
    for _ in range(5):
        # 任务派遣中心
        d.get("cmd=missionassign&subtype=0")
        S_ids = d.findall(r'-S&nbsp;所需时间.*?_id=(\d+)">接受')
        A_ids = d.findall(r'-A&nbsp;所需时间.*?_id=(\d+)">接受')
        B_ids = d.findall(r'-B&nbsp;所需时间.*?_id=(\d+)">接受')

        _ids = S_ids + A_ids

        if not is_has_free_refresh_count:
            _ids = B_ids
            if set(_ids).issubset(fail_ids):
                break

        for _id in _ids:
            # 接受
            d.get(f"cmd=missionassign&subtype=2&mission_id={_id}")
            task_name = f"{base_name}-{d.find(r'任务名称：(.*?)<')}"

            # 快速委派
            d.get(f"cmd=missionassign&subtype=7&mission_id={_id}")
            if "设置佣兵成功" not in d.html:
                d.log(d.find(r"】<br /><br />(.*?)<"), task_name)
                fail_ids.add(_id)
                continue
            d.log(d.find(r"】</p>(.*?)<"), task_name)

            # 开始任务
            d.get(f"cmd=missionassign&subtype=8&mission_id={_id}")
            if "当前可执行任务数已达上限" in d.html:
                d.log(d.find(r"】<br /><br />(.*?)<"), task_name)
                is_maximums = True
                break
            d.log(d.find(r"】</p>(.*?)<"), task_name)

            if d.html.count("查看") == 3 or "今日已领取了全部任务" in d.html:
                is_maximums = True
                break

        if is_maximums:
            break

        if not is_has_free_refresh_count:
            continue

        # 任务派遣中心
        d.get("cmd=missionassign&subtype=0")
        if "本次消耗：0斗豆" in d.html:
            # 刷新任务
            d.get("cmd=missionassign&subtype=3")
            d.log("免费刷新成功", "任务派遣中心-刷新任务")
        else:
            d.log("没有免费刷新次数了", "任务派遣中心-刷新任务")
            is_has_free_refresh_count = False

    # 任务派遣中心
    d.get("cmd=missionassign&subtype=0")
    for info in d.findall(r"<br />(.*?)&nbsp;<a.*?查看"):
        d.log(info, "任务派遣中心-当前任务").append()


def c_侠士客栈(d: DaLeDou):
    """
    领取奖励：每天3次
    客栈奇遇：
        前来捣乱的xx：与TA理论
        黑市商人：物品交换，详见配置文件
    """
    # 侠士客栈
    d.get("cmd=warriorinn")
    for t, n in d.findall(r"type=(\d+)&amp;num=(\d+)"):
        # 领取奖励
        d.get(f"cmd=warriorinn&op=getlobbyreward&type={t}&num={n}")
        d.log(d.find(r"侠士客栈<br />(.*?)<br />")).append()

    for p in d.findall(r'pos=(\d+)">前来捣乱的'):
        # 与TA理论
        d.get(f"cmd=warriorinn&op=exceptadventure&pos={p}")
        d.log(d.find(r"侠士客栈<br />(.*?)<")).append()

    config: list[str] = d.config["侠士客栈"]
    if config is None:
        return
    for p in d.findall(r'pos=(\d+)">黑市商人'):
        # 与TA交换
        d.get(f"cmd=warriorinn&op=confirmadventure&pos={p}&type=0")
        for text in config:
            if text in d.html:
                d.log(d.find(r"物品交换<br /><br />(.*?)<br />")).append()
                # 确认
                d.get(f"cmd=warriorinn&op=exceptadventure&pos={p}")
                d.log(d.find(r"侠士客栈<br />(.*?)<br />")).append()


def c_帮派巡礼(d: DaLeDou):
    """每天领取巡游赠礼"""
    # 领取巡游赠礼
    d.get("cmd=abysstide&op=getfactiongift")
    d.log(d.find()).append()


def c_深渊秘境(d: DaLeDou):
    """
    每天兑换副本，兑换次数详见配置文件
    每天通关副本，副本次数有多少就通关多少次，副本详见配置文件
    """
    config: dict = d.config["深渊之潮"]
    exchange_count: int = config["exchange_count"]
    _id: int = config["id"]

    for _ in range(exchange_count):
        # 兑换
        d.get("cmd=abysstide&op=addaccess")
        d.log(d.find()).append()
        if "无法继续兑换挑战次数" in d.html:
            break

    # 深渊秘境
    d.get("cmd=abysstide&op=viewallabyss")
    count = d.find(r"副本次数：(\d+)")
    for _ in range(int(count)):
        d.get(f"cmd=abysstide&op=enterabyss&id={_id}")
        if "开始挑战" not in d.html:
            # 暂无可用挑战次数
            # 该副本需要顺序通关解锁
            d.log(d.find()).append()
            break

        for _ in range(5):
            # 开始挑战
            d.get("cmd=abysstide&op=beginfight")
            d.log(d.find())
            if "憾负于" in d.html:
                break

        # 退出副本
        d.get("cmd=abysstide&op=endabyss")
        d.log(d.find()).append()


def c_龙凰论武(d: DaLeDou):
    """每月4~25号每天随机挑战，挑战次数详见配置文件"""
    # 龙凰之境
    d.get("cmd=dragonphoenix&op=lunwu")
    if "已报名" in d.html:
        d.log("系统已随机报名，次日才能挑战").append()
        return
    elif "论武榜" not in d.html:
        d.log("进入论武异常，无法挑战").append()
        return

    challenge_count: int = d.config["龙凰之境"]["challenge_count"]
    for _ in range(challenge_count):
        data = d.findall(r"uin=(\d+).*?idx=(\d+)")
        uin, _idx = random.choice(data)
        # 挑战
        d.get(f"cmd=dragonphoenix&op=pk&zone=1&uin={uin}&idx={_idx}")
        d.log(d.find(r"/\d+</a><br /><br />(.*?)<")).append()
        if "挑战次数不足" in d.html:
            break
        elif "冷却中" in d.html:
            break


def c_客栈同福(d: DaLeDou):
    """
    献酒：每天当有匹配项时献酒，详见配置文件
    """
    config: list = d.config["客栈同福"]
    if config is None:
        d.log("你没有配置匹配").append()
        return

    # 客栈同福
    d.get("cmd=newAct&subtype=154")
    count: str = d.find(r"现有黄酒数量：(\d+)")
    if count == "0":
        d.log("黄酒数量不足，本次无操作").append()
        return

    is_libation = False
    for _ in range(int(count)):
        for pattern in config:
            # 客栈同福
            d.get("cmd=newAct&subtype=154")
            if pattern not in d.html:
                continue
            is_libation = True
            # 献酒
            d.get("cmd=newAct&subtype=155")
            d.log(d.find(r"】<br /><p>(.*?)<br />")).append()
            if "黄酒不足" in d.html:
                return
        if not is_libation:
            d.log("没有找到匹配，本次无操作").append()
            break


def c_幸运金蛋(d: DaLeDou):
    """砸金蛋一次"""
    # 幸运金蛋
    d.get("cmd=newAct&subtype=110&op=0")
    if i := d.find(r"index=(\d+)"):
        # 砸金蛋
        d.get(f"cmd=newAct&subtype=110&op=1&index={i}")
        d.log(d.find(r"】<br /><br />(.*?)<br />")).append()
    else:
        d.log("没有砸蛋次数了").append()


def c_乐斗大笨钟(d: DaLeDou):
    """领取一次"""
    # 领取
    d.get("cmd=newAct&subtype=18")
    d.log(d.find(r"<br /><br /><br />(.*?)<br />")).append()
