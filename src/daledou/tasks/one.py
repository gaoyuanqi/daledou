"""
本模块为大乐斗第一轮任务
"""

import random
import re
import time

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
    c_客栈同福,
    c_幸运金蛋,
    c_乐斗大笨钟,
)


def get_doushenta_cd(d: DaLeDou) -> int:
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
    d.get("cmd=ledouvip")
    if level := d.find(r"当前级别：(\d+)"):
        return cd[level]
    else:
        # 还未成为达人
        return 10


def 斗神塔(d: DaLeDou, name: str, challenge_count: str):
    """斗神塔自动挑战（次数耗尽或到不了顶层结束）"""
    count = 0
    second = get_doushenta_cd(d)
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


def get_exchange_config(config: list[dict]):
    """返回兑换名称、兑换id和兑换数量"""
    for item in config:
        name: str = item["name"]
        _id: int = item["id"]
        exchange_quantity: int = item["exchange_quantity"]
        if exchange_quantity > 0:
            yield name, _id, exchange_quantity


# ============================================================


def 邪神秘宝(d: DaLeDou):
    c_邪神秘宝(d)


def 荣誉兑换(d: DaLeDou):
    config: list[dict] = d.config["华山论剑"]["exchange"]
    if config is None:
        return

    for name, _id, exchange_quantity in get_exchange_config(config):
        count = 0
        for _ in range(exchange_quantity // 10):
            d.get(f"cmd=knightarena&op=exchange&id={_id}&times=10")
            d.log(d.find())
            if "成功" not in d.html:
                break
            count += 10
        for _ in range(exchange_quantity - count):
            d.get(f"cmd=knightarena&op=exchange&id={_id}&times=1")
            d.log(d.find())
            if "成功" not in d.html:
                break
            count += 1
        if count:
            d.append(f"兑换{name}*{count}")


def 侠士招募(d: DaLeDou):
    # 侠士招募
    d.get("cmd=knightarena&op=viewlottery")
    number = int(d.find(r"（(\d+)）"))
    for _ in range(number // 100):
        # 招募十次
        d.get("cmd=knightarena&op=lottery&times=10")
        d.log(d.find()).append()


def 华山论剑(d: DaLeDou):
    if d.day == 26:
        # 领取赛季段位奖励
        d.get(r"cmd=knightarena&op=drawranking")
        d.log(d.find()).append()

        荣誉兑换(d)
        侠士招募(d)
        return

    knight_config: list[dict] = d.config["华山论剑"]["战阵调整"]
    if knight_config is None:
        d.log("你需要在账号配置战阵调整才能挑战").append()
        return

    # 更改侠士/选择侠士
    d.get("cmd=knightarena&op=viewsetknightlist&pos=0")
    knight_data = dict(d.findall(r">([\u4e00-\u9fff]+) \d+级.*?knightid=(\d+)"))
    if not knight_data:
        d.log("您没有至少一个侠士，无法战阵调整").append()
        return

    def 战阵调整(knights: list[str]):
        for i, knight in enumerate(knights):
            if i > 2:
                break
            if _id := knight_data.get(knight, None):
                # 出战
                d.get(f"cmd=knightarena&op=setknight&id={_id}&pos={i}&type=1")
                d.log(f"第{i + 1}战：{knight}").append()
            else:
                d.log(f"第{i + 1}战：您没有{knight}").append()

    for item in knight_config:
        challenge_count: int = item["challenge_count"]
        knights: list[str] = item["knights"]
        战阵调整(knights)
        for _ in range(challenge_count):
            # 免费挑战/开始挑战
            d.get("cmd=knightarena&op=challenge")
            d.log(d.find()).append()
            if "增加荣誉点数" not in d.html:
                # 请先设置上阵侠士后再开始战斗
                # 当前论剑队伍中有侠士耐久不足，请更换上阵！
                break


def 斗豆月卡(d: DaLeDou):
    # 领取150斗豆
    d.get("cmd=monthcard&sub=1")
    d.log(d.find(r"<p>(.*?)<br />")).append()


def 分享(d: DaLeDou):
    end = False
    second = get_doushenta_cd(d)

    # 分享
    d.get("cmd=sharegame&subtype=1")
    for _ in range(9):
        # 一键分享
        d.get("cmd=sharegame&subtype=6")
        d.log(d.find(r"】</p>(.*?)<p>"))
        if ("达到当日分享次数上限" in d.html) or end:
            d.log(d.find(r"</p><p>(.*?)<br />")).append()
            break

        for _ in range(10):
            # 开始挑战 or 挑战下一层
            d.get("cmd=towerfight&type=0")
            d.log(d.find(), "斗神塔")
            time.sleep(second)
            if "您战胜了" not in d.html:
                end = True
                break
            # 您败给了
            # 已经到了塔顶
            # 已经没有剩余的周挑战数
            # 您需要消耗斗神符才能继续挑战斗神塔

    # 自动挑战
    d.get("cmd=towerfight&type=11")
    d.log(d.find(), "斗神塔")
    time.sleep(second)
    if "结束挑战" in d.html:
        # 结束挑战
        d.get("cmd=towerfight&type=7")
        d.log(d.find(), "斗神塔")

    if d.week != 4:
        return

    # 领取奖励
    d.get("cmd=sharegame&subtype=3")
    for s in d.findall(r"sharenums=(\d+)"):
        # 领取
        d.get(f"cmd=sharegame&subtype=4&sharenums={s}")
        d.log(d.find(r"】</p>(.*?)<p>")).append()

    if d.html.count("已领取") == 14:
        # 重置分享
        d.get("cmd=sharegame&subtype=7")
        d.log(d.find(r"】</p>(.*?)<p>")).append()


def 乐斗(d: DaLeDou):
    config: dict[str, bool] = d.config["乐斗"]
    use_count: int = config["贡献药水"]
    disable_boss_uin: list[str] = config["disable_boss_uin"] or []
    is_open_auto_use: bool = config["体力药水"]
    is_ledou: bool = config["情师徒拜"]

    # 乐斗助手
    d.get("cmd=view&type=6")
    if is_open_auto_use and "开启自动使用体力药水" in d.html:
        # 开启自动使用体力药水
        d.get("cmd=set&type=0")
        d.log("开启自动使用体力药水").append()
    elif not is_open_auto_use and "取消自动使用体力药水" in d.html:
        # 取消自动使用体力药水
        d.get("cmd=set&type=0")
        d.log("取消自动使用体力药水").append()

    for _ in range(use_count):
        # 使用贡献药水*1
        d.get("cmd=use&id=3038&store_type=1&page=1")
        if "使用规则" in d.html:
            d.log(d.find(r"】</p><p>(.*?)<br />")).append()
            break
        d.log(d.find()).append()

    # 好友首页
    d.get("cmd=friendlist&page=1")
    for u in d.findall(r"侠：.*?B_UID=(\d+)"):
        if u in disable_boss_uin:
            continue
        # 乐斗
        d.get(f"cmd=fight&B_UID={u}")
        d.log(d.find(r"<br />(.*?)，")).append()
        if "体力值不足" in d.html:
            break

    # 帮友首页
    d.get("cmd=viewmem&page=1")
    for u in d.findall(r"侠：.*?B_UID=(\d+)"):
        # 乐斗
        d.get(f"cmd=fight&B_UID={u}")
        d.log(d.find(r"<br />(.*?)，")).append()

    # 侠侣
    d.get("cmd=viewxialv&page=1")
    if is_ledou:
        uin = d.findall(r"</a>\d+.*?B_UID=(\d+)")
    else:
        uin = d.findall(r"侠：.*?B_UID=(\d+)")
    for u in uin:
        # 乐斗
        d.get(f"cmd=fight&B_UID={u}")
        if "使用规则" in d.html:
            d.log(d.find(r"】</p><p>(.*?)<br />")).append()
        else:
            d.log(d.find(r"<br />(.*?)！")).append()
        if "体力值不足" in d.html:
            break


def 武林(d: DaLeDou):
    # 报名
    d.get("cmd=fastSignWulin&ifFirstSign=1")
    if "使用规则" in d.html:
        d.log(d.find(r"】</p><p>(.*?)<br />")).append()
    else:
        d.log(d.find(r"升级。<br />(.*?) ")).append()


def 设置战队(d: DaLeDou):
    knight_config: list[str] = d.config["群侠"]["设置战队"]
    if knight_config is None:
        return

    # 更改侠士/选择侠士
    d.get("cmd=knightfight&op=viewsetknightlist&pos=0")
    knight_data = dict(d.findall(r">([\u4e00-\u9fff]+) \d+级.*?knightid=(\d+)"))
    if not knight_data:
        d.log("您没有至少一个侠士，无法设置战队").append()
        return

    for i, knight in enumerate(knight_config):
        if i > 4:
            break
        if _id := knight_data.get(knight, None):
            # 出战
            d.get(f"cmd=knightfight&op=set_knight&id={_id}&pos={i}&type=1")
            d.log(f"第{i + 1}战：{knight}").append()
        else:
            d.log(f"第{i + 1}战：您没有{knight}").append()


def 群侠(d: DaLeDou):
    设置战队(d)

    # 报名
    d.get("cmd=knightfight&op=signup")
    d.log(d.find(r"侠士侠号.*?<br />(.*?)<br />")).append()


def 侠侣(d: DaLeDou):
    # 报名
    d.get("cmd=cfight&subtype=9")
    if "使用规则" in d.html:
        d.log(d.find(r"】</p><p>(.*?)<br />")).append()
    else:
        d.log(d.find(r"报名状态.*?<br />(.*?)<br />")).append()


def 结拜(d: DaLeDou):
    for _id in [1, 2, 3, 5, 4]:
        # 报名
        d.get(f"cmd=brofight&subtype=1&gidIdx={_id}")
        d.log(d.find(r"排行</a><br />(.*?)<"))
        if "请换一个赛区报名" in d.html or "你们无法报名" in d.html:
            continue
        d.append()
        break


def 巅峰之战进行中(d: DaLeDou):
    if d.week == 1:
        # 领奖
        d.get("cmd=gvg&sub=1")
        d.log(d.find(r"】</p>(.*?)<br />")).append()

        config: int = d.config["巅峰之战进行中"]
        if config is None:
            return
        # 报名
        d.get(f"cmd=gvg&sub=4&group={config}&check=1")
        d.log(d.find(r"】</p>(.*?)<br />")).append()
        return

    for _ in range(14):
        # 征战
        d.get("cmd=gvg&sub=5")
        if "战线告急" in d.html:
            d.log(d.find(r"支援！<br />(.*?)<")).append()
        else:
            d.log(d.find(r"】</p>(.*?)<")).append()

        if "你在巅峰之战中" not in d.html:
            # 冷却时间
            # 撒花祝贺
            # 请您先报名再挑战
            # 您今天已经用完复活次数了
            break


def 矿洞(d: DaLeDou):
    config: str = d.config["矿洞"]

    # 矿洞
    d.get("cmd=factionmine")
    for _ in range(5):
        if "副本挑战中" in d.html:
            # 挑战
            d.get("cmd=factionmine&op=fight")
            d.log(d.find()).append()
            if "挑战次数不足" in d.html:
                break
        elif "开启副本" in d.html:
            if config is None:
                d.log("你没有配置开启副本").append()
                return
            # 确认开启
            d.get(f"cmd=factionmine&op=start&{config}")
            d.log(d.find()).append()
            if "当前不能开启此副本" in d.html:
                return
        elif "领取奖励" in d.html:
            d.get("cmd=factionmine&op=reward")
            d.log(d.find()).append()


def 掠夺(d: DaLeDou):
    if d.week == 3:
        # 领取胜负奖励
        d.get("cmd=forage_war&subtype=6")
        d.log(d.find()).append()
        # 报名
        d.get("cmd=forage_war&subtype=1")
        d.log(d.find()).append()
        return

    # 掠夺
    d.get("cmd=forage_war")
    if ("本轮轮空" in d.html) or ("未报名" in d.html):
        d.log(d.find(r"本届战况：(.*?)<br />")).append()
        return

    data = []
    # 掠夺
    d.get("cmd=forage_war&subtype=3")
    if gra_id := d.findall(r'gra_id=(\d+)">掠夺'):
        for _id in gra_id:
            d.get(f"cmd=forage_war&subtype=3&op=1&gra_id={_id}")
            if zhanli := d.find(r"<br />1.*? (\d+)\."):
                data.append((int(zhanli), _id))
        if data:
            _, _id = min(data)
            d.get(f"cmd=forage_war&subtype=4&gra_id={_id}")
            d.log(d.find()).append()
    else:
        d.log("已占领对方全部粮仓").append()

    # 领奖
    d.get("cmd=forage_war&subtype=5")
    d.log(d.find()).append()


def 踢馆(d: DaLeDou):
    if d.week == 6:
        # 报名
        d.get("cmd=facchallenge&subtype=1")
        d.log(d.find()).append()
        # 领奖
        d.get("cmd=facchallenge&subtype=7")
        d.log(d.find()).append()
        return

    def generate_sequence():
        # 试炼、高倍转盘序列
        for t in [2, 2, 2, 2, 2, 4]:
            yield t
        # 挑战序列
        for _ in range(30):
            yield 3

    for t in generate_sequence():
        d.get(f"cmd=facchallenge&subtype={t}")
        d.log(d.find()).append()
        if "您的复活次数已耗尽" in d.html:
            break
        elif "您的挑战次数已用光" in d.html:
            break
        elif "你们帮没有报名参加这次比赛" in d.html:
            break


def 竞技场(d: DaLeDou):
    is_exchange: bool = d.config["竞技场"]
    if is_exchange:
        # 兑换10个河图洛书
        d.get("cmd=arena&op=exchange&id=5435&times=10")
        d.log(d.find()).append()

    for _ in range(10):
        # 免费挑战 or 开始挑战
        d.get("cmd=arena&op=challenge")
        d.log(d.find()).append()
        if "免费挑战次数已用完" in d.html:
            break

    # 领取奖励
    d.get("cmd=arena&op=drawdaily")
    d.log(d.find()).append()


def 十二宫(d: DaLeDou):
    _id: int = d.config["十二宫"]
    # 请猴王扫荡
    d.get(f"cmd=zodiacdungeon&op=autofight&scene_id={_id}")
    if "恭喜你" in d.html:
        d.log(d.find(r"恭喜你，(.*?)！")).append()
        return
    elif "是否复活再战" in d.html:
        d.log(d.find(r"<br.*>(.*?)，")).append()
        return

    # 你已经不幸阵亡，请复活再战！
    # 挑战次数不足
    # 当前场景进度不足以使用自动挑战功能
    d.log(d.find(r"<p>(.*?)<br />")).append()


def 许愿(d: DaLeDou):
    for sub in [5, 1, 6]:
        d.get(f"cmd=wish&sub={sub}")
        d.log(d.find()).append()


def 抢地盘(d: DaLeDou):
    """
    等级  30级以下 40级以下 ... 120级以下 无限制区
    type  1       2            10        11
    """
    d.get("cmd=recommendmanor&type=11&page=1")
    if manorid := d.findall(r'manorid=(\d+)">攻占</a>'):
        _id = random.choice(manorid)
        # 攻占
        d.get(f"cmd=manorfight&fighttype=1&manorid={_id}")
        d.log(d.find(r"</p><p>(.*?)。")).append()

    # 兑换武器
    d.get("cmd=manor&sub=0")
    d.log(d.find(r"<br /><br />(.*?)<br /><br />")).append()


def 历练(d: DaLeDou):
    config: dict[int, int] = d.config["历练"]
    if config is None:
        d.log("你没有配置历练BOSS").append()
        return

    # 乐斗助手
    d.get("cmd=view&type=6")
    if "取消自动使用活力药水" in d.html:
        # 取消自动使用活力药水
        d.get("cmd=set&type=11")
        d.log("取消自动使用活力药水").append()

    for _id, count in config.items():
        if not count:
            continue
        for _ in range(count):
            d.get(f"cmd=mappush&subtype=3&mapid=6&npcid={_id}&pageid=2")
            if "您还没有打到该历练场景" in d.html:
                d.log(d.find(r"介绍</a><br />(.*?)<br />")).append()
                break

            d.log(d.find(r"阅历值：\d+<br />(.*?)<br />")).append()
            if "活力不足" in d.html:
                return
            elif "BOSS" not in d.html:
                # 你今天和xx挑战次数已经达到上限了，请明天再来挑战吧
                # 还不能挑战
                break


def 镖行天下(d: DaLeDou):
    bodyguard: str = d.config["镖行天下"]

    # 镖行天下
    d.get("cmd=cargo")
    if "护送完成" in d.html:
        # 领取奖励
        d.get("cmd=cargo&op=16")
        d.log(d.find()).append()
    if "剩余护送次数：1" in d.html:
        # 护送押镖
        d.get("cmd=cargo&op=7")
        count = int(d.find(r"免费刷新次数：(\d+)"))
        for _ in range(count):
            if "蔡八斗" not in d.html:
                break
            # 刷新押镖
            d.get("cmd=cargo&op=8")
            d.log(d.find()).append()
        d.log("当前镖师：" + d.find(r"当前镖师：(.*?)<")).append()
        # 启程护送
        d.get("cmd=cargo&op=6")
        d.log(d.find()).append()

    not_interception_uin = set()
    for _ in range(20):
        if "剩余拦截次数：0" in d.html:
            return

        # 刷新
        d.get("cmd=cargo&op=3")
        d.log(d.find())
        uins = d.findall(rf'{bodyguard}.*?passerby_uin=(\d+)">拦截')
        if not uins or set(uins).issubset(not_interception_uin):
            time.sleep(3)

        for uin in uins:
            if uin in not_interception_uin:
                continue

            # 拦截
            d.get(f"cmd=cargo&op=14&passerby_uin={uin}")
            d.log(d.find())
            if "空手而归" in d.html:
                not_interception_uin.add(uin)
            elif "这个镖车" in d.html:
                # 这个镖车在保护期内
                # 这个镖车已经到达终点
                not_interception_uin.add(uin)
                continue
            elif "系统繁忙" in d.html:
                continue
            d.append()

            if "剩余拦截次数：0" in d.html:
                return


def 幻境(d: DaLeDou):
    # 幻境
    d.get("cmd=misty")
    if "挑战次数：0/1" in d.html:
        d.log(r"您的挑战次数已用完，请明日再战！").append()
        return
    if "【飘渺幻境】" not in d.html:
        # 返回飘渺幻境
        d.get("cmd=misty&op=return")

    _id: int = d.config["幻境"]
    d.get(f"cmd=misty&op=start&stage_id={_id}")
    if "副本未开通" in d.html:
        d.log(f"副本{_id}未开通，请选择其它副本").append()
        return

    for _ in range(5):
        # 乐斗
        d.get("cmd=misty&op=fight")
        d.log(d.find(r"星数.*?<br />(.*?)<br />")).append()
        if "尔等之才" in d.html:
            break

    # 领取奖励
    while _id := d.find(r"box_id=(\d+)"):
        d.get(f"cmd=misty&op=reward&box_id={_id}")
        d.log(d.find(r"星数.*?<br />(.*?)<br />")).append()

    # 返回飘渺幻境
    d.get("cmd=misty&op=return")


def 群雄逐鹿(d: DaLeDou):
    for op in ["signup", "drawreward"]:
        d.get(f"cmd=thronesbattle&op={op}")
        d.log(d.find(r"届群雄逐鹿<br />(.*?)<br />")).append()


def 画卷迷踪(d: DaLeDou):
    for _ in range(20):
        # 准备完成进入战斗
        d.get("cmd=scroll_dungeon&op=fight&buff=0")
        d.log(d.find(r"</a><br /><br />(.*?)<br />")).append()
        if "没有挑战次数" in d.html:
            break
        elif "征战书不足" in d.html:
            break


def 门派(d: DaLeDou):
    is_exchange: dict[str, bool] = d.config["门派"]
    if is_exchange["门派高香"]:
        d.get("cmd=exchange&subtype=2&type=1248&times=1")
        d.log(d.find()).append()
    is_exchange_success = False
    if is_exchange["门派战书"]:
        d.get("cmd=exchange&subtype=2&type=1249&times=1")
        d.log(d.find()).append()
        if "成功" in d.html:
            is_exchange_success = True

    # 万年寺
    # 普通香炉、高香香炉
    for op in ["fumigatefreeincense", "fumigatepaidincense"]:
        d.get(f"cmd=sect&op={op}")
        d.log(d.find(r"修行。<br />(.*?)<br />")).append()

    # 八叶堂
    # 进入木桩训练、进入同门切磋
    ops = ["trainingwithnpc", "trainingwithmember"]
    if is_exchange_success:
        ops.append("trainingwithmember")
    for op in ops:
        d.get(f"cmd=sect&op={op}")
        d.log(d.find()).append()

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
        d.get(f"cmd=sect&op=trainingwithcouncil&{rank}")
        d.log(d.find()).append()

    # 五花堂
    wuhuatang = d.get("cmd=sect_task")
    tasks = {
        "进入华藏寺看一看": "cmd=sect_art",
        "进入伏虎寺看一看": "cmd=sect_trump",
        "进入金顶看一看": "cmd=sect&op=showcouncil",
        "进入八叶堂看一看": "cmd=sect&op=showtraining",
        "进入万年寺看一看": "cmd=sect&op=showfumigate",
    }
    for name, url in tasks.items():
        if name in wuhuatang:
            d.get(url)
            d.log(name)
    if "查看一名" in wuhuatang:
        # 查看一名同门成员的资料 or 查看一名其他门派成员的资料
        d.log("查看好友第二页所有成员")
        # 好友第2页
        d.get("cmd=friendlist&page=2")
        for uin in d.findall(r"</a>\d+.*?B_UID=(\d+)"):
            # 查看好友
            d.get(f"cmd=totalinfo&B_UID={uin}")
            d.log(f"查看好友{uin}")
    if "进行一次心法修炼" in wuhuatang:
        for _id in range(101, 119):
            # 修炼
            d.get(f"cmd=sect_art&subtype=2&art_id={_id}&times=1")
            d.log(d.find())
            if "修炼成功" in d.html:
                break

    # 五花堂
    d.get("cmd=sect_task")
    for task_id in d.findall(r'task_id=(\d+)">完成'):
        # 完成
        d.get(f"cmd=sect_task&subtype=2&task_id={task_id}")
        d.log(d.find()).append()


def 门派邀请赛_商店兑换(d: DaLeDou):
    config: list[dict] = d.config["门派邀请赛"]["exchange"]
    if config is None:
        return

    for name, _id, exchange_quantity in get_exchange_config(config):
        count = 0
        for _ in range(exchange_quantity // 10):
            d.get(f"cmd=exchange&subtype=2&type={_id}&times=10")
            d.log(d.find())
            if "成功" not in d.html:
                break
            count += 10
        for _ in range(exchange_quantity - count):
            d.get(f"cmd=exchange&subtype=2&type={_id}&times=1")
            d.log(d.find())
            if "成功" not in d.html:
                break
            count += 1
        if count:
            d.append(f"兑换{name}*{count}")


def 门派邀请赛(d: DaLeDou):
    if d.week == 1:
        # 组队报名
        d.get("cmd=secttournament&op=signup")
        d.log(d.find()).append()
        # 领取奖励
        d.get("cmd=secttournament&op=getrankandrankingreward")
        d.log(d.find()).append()

        门派邀请赛_商店兑换(d)
        return

    for _ in range(10):
        # 开始挑战
        d.get("cmd=secttournament&op=fight")
        d.log(d.find()).append()
        if "已达最大挑战上限" in d.html:
            break
        elif "门派战书不足" in d.html:
            break


def 会武_商店兑换(d: DaLeDou):
    config: list[dict] = d.config["会武"]["exchange"]
    if config is None:
        return

    for name, _id, exchange_quantity in get_exchange_config(config):
        count = 0
        for _ in range(exchange_quantity // 10):
            d.get(f"cmd=exchange&subtype=2&type={_id}&times=10")
            d.log(d.find())
            if "成功" not in d.html:
                break
            count += 10
        for _ in range(exchange_quantity - count):
            d.get(f"cmd=exchange&subtype=2&type={_id}&times=1")
            d.log(d.find())
            if "成功" not in d.html:
                break
            count += 1
        if count:
            d.append(f"兑换{name}*{count}")


def 会武(d: DaLeDou):
    if d.week in [1, 2, 3]:
        for _ in range(21):
            # 挑战
            d.get("cmd=sectmelee&op=dotraining")
            if "试炼场】" in d.html:
                d.log(d.find(r"最高伤害：\d+<br />(.*?)<br />")).append()
                continue
            d.log(d.find(r"规则</a><br />(.*?)<br />")).append()
            if "你已达今日挑战上限" in d.html:
                break
            elif "你的试炼书不足" in d.html:
                break
    elif d.week == 4:
        # 冠军助威 丐帮
        d.get("cmd=sectmelee&op=cheer&sect=1003")
        # 冠军助威
        d.get("cmd=sectmelee&op=showcheer")
        d.log(d.find()).append()
        会武_商店兑换(d)
    elif d.week == 6:
        # 领奖
        d.get("cmd=sectmelee&op=showreward")
        d.log(d.find(r"<br />(.*?)。")).append()
        d.log(d.find(r"。<br />(.*?)。")).append()
        # 领取
        d.get("cmd=sectmelee&op=drawreward")
        if "本届已领取奖励" in d.html:
            d.log(d.find(r"规则</a><br />(.*?)<br />")).append()
        else:
            d.log(d.find()).append()


def 梦想之旅(d: DaLeDou):
    # 普通旅行
    d.get("cmd=dreamtrip&sub=2")
    d.log(d.find()).append()

    if d.week != 4:
        return

    max_consume_quantity: int = d.config["梦想之旅"]
    if max_consume_quantity < d.html.count("未去过"):
        return

    # 获取当前区域所有未去过的目的地
    if place := d.findall(r"([\u4e00-\u9fa5\s\-]+)(?=\s未去过)"):
        bmapid = d.find(r'bmapid=(\d+)">梦幻旅行')
    for name in place:
        # 梦幻旅行
        d.get(f"cmd=dreamtrip&sub=3&bmapid={bmapid}")
        s = d.find(rf"{name}.*?smapid=(\d+)")
        # 去这里
        d.get(f"cmd=dreamtrip&sub=2&smapid={s}")
        d.log(d.find()).append()

    # 领取礼包
    for _ in range(2):
        if b := d.findall(r"sub=4&amp;bmapid=(\d+)"):
            # 区域礼包 1 or 2 or 3 or 4
            # 超级礼包 0
            d.get(f"cmd=dreamtrip&sub=4&bmapid={b[0]}")
            d.log(d.find()).append()


def 问鼎天下_商店兑换(d: DaLeDou):
    def exchange():
        """问鼎天下商店兑换"""
        q, r = divmod((consume_number - possess_number), 10)
        if q:
            # 兑换10个
            d.get(f"cmd=exchange&subtype=2&type={t}&times=10&costtype=14")
            d.log(d.find(), f"{name}兑换").append()
            return
        for _ in range(r):
            # 兑换1个
            d.get(f"cmd=exchange&subtype=2&type={t}&times=1&costtype=14")
            d.log(d.find(), f"{name}兑换").append()

    data = {
        "夔牛碎片": {
            "id": 1,
            "t": 1270,
            "backpack_id": 5154,
            "name": "夔牛鼓",
        },
        "饕餮碎片": {
            "id": 2,
            "t": 1271,
            "backpack_id": 5155,
            "name": "饕餮鼎",
        },
        "烛龙碎片": {
            "id": 3,
            "t": 1268,
            "backpack_id": 5156,
            "name": "烛龙印",
        },
        "黄鸟碎片": {
            "id": 4,
            "t": 1269,
            "backpack_id": 5157,
            "name": "黄鸟伞",
        },
    }
    for name, _dict in data.items():
        _id = _dict["id"]
        t = _dict["t"]
        backpack_id = _dict["backpack_id"]
        _name = _dict["name"]

        possess_number = d.get_backpack_number(backpack_id)
        d.log(possess_number, f"{name}-拥有数量")

        # 神魔录古阵篇宝物详情
        d.get(f"cmd=ancient_gods&op=4&id={_id}")
        # 当前等级
        now_level = d.find(r"等级：(\d+)")
        d.log(now_level, f"{_name}-当前等级")
        # 最高等级
        max_level = d.find(r"最高提升至(\d+)")
        d.log(max_level, f"{_name}-最高等级")
        if now_level == max_level:
            continue
        # 碎片消耗数量
        consume_number = int(d.find(r"碎片\*(\d+)"))
        d.log(consume_number, f"{_name}碎片-消耗数量")
        if consume_number > possess_number:
            exchange()


def 问鼎天下(d: DaLeDou):
    if d.week == 1:
        # 领取奖励
        d.get("cmd=tbattle&op=drawreward")
        d.log(d.find()).append()
        问鼎天下_商店兑换(d)
    elif d.week == 6:
        # 淘汰赛助威
        _id = d.config["问鼎天下"]["淘汰赛"]
        if _id is None:
            d.log("你没有配置淘汰赛助威帮派id").append()
            return
        d.get(f"cmd=tbattle&op=cheerregionbattle&id={_id}")
        d.log(d.find()).append()
        return
    elif d.week == 7:
        # 排名赛助威
        _id = d.config["问鼎天下"]["排名赛"]
        if _id is None:
            d.log("你没有配置排名赛助威帮派id").append()
            return
        d.get(f"cmd=tbattle&op=cheerchampionbattle&id={_id}")
        d.log(d.find()).append()
        return

    # 问鼎天下
    d.get("cmd=tbattle")
    if "放弃" in d.html:
        d.log("已有占领资源点，本任务结束").append()
        return

    if "你占领的领地已经枯竭" in d.html:
        # 领取
        d.get("cmd=tbattle&op=drawreleasereward")
        d.log(d.find()).append()

    remaining_occupy_count = int(d.find(r"剩余抢占次数：(\d+)"))
    if remaining_occupy_count == 0:
        d.log("没有抢占次数了").append()
        return

    region: int = d.config["问鼎天下"]["region"]
    level1_occupy_count: int = d.config["问鼎天下"]["level1_occupy_count"]
    if level1_occupy_count >= remaining_occupy_count:
        level1_occupy_count = max(0, remaining_occupy_count - 1)

    # 区域
    d.get(f"cmd=tbattle&op=showregion&region={region}")
    for _id in d.findall(r"id=(\d+).*?攻占</a>")[:4]:
        while level1_occupy_count:
            # 攻占1级资源点
            d.get(f"cmd=tbattle&op=occupy&id={_id}&region={region}")
            d.log(d.find()).append()
            if "你主动与" in d.html:
                level1_occupy_count -= 1
                if "放弃" in d.html:
                    # 放弃
                    d.get("cmd=tbattle&op=abandon")
                    d.log(d.find()).append()
            else:
                break
        if level1_occupy_count == 0:
            break

    # 区域
    d.get(f"cmd=tbattle&op=showregion&region={region}")
    # 攻占3级资源点最后一个
    _id = d.findall(r"id=(\d+).*?攻占</a>")[-1]
    d.get(f"cmd=tbattle&op=occupy&id={_id}&region=1")
    d.log(d.find()).append()


def 帮派商会(d: DaLeDou):
    c_帮派商会(d)


def 帮派远征军_攻击(d: DaLeDou, p_id: str, u: str) -> bool:
    # 攻击
    d.get(f"cmd=factionarmy&op=fightWithUsr&point_id={p_id}&opp_uin={u}")
    if "加入帮派第一周不能参与帮派远征军" in d.html:
        return False
    if "【帮派远征军-征战结束】" in d.html:
        d.log(d.find())
        if "您未能战胜" in d.html:
            d.append()
            return False
    elif "【帮派远征军】" in d.html:
        d.log(d.find(r"<br /><br />(.*?)</p>")).append()
        if "您的血量不足" in d.html:
            return False
    return True


def 帮派远征军_领取(d: DaLeDou):
    point_ids = []
    land_ids = []
    for _id in range(5):
        d.get(f"cmd=factionarmy&op=viewIndex&island_id={_id}")
        point_ids += d.findall(r'point_id=(\d+)">领取奖励')
        if "未解锁" in d.html:
            break
        land_ids += d.findall(r'island_id=(\d+)">领取岛屿宝箱')

    # 领取奖励
    for p_id in point_ids:
        d.get(f"cmd=factionarmy&op=getPointAward&point_id={p_id}")
        d.log(d.find()).append()

    # 领取岛屿宝箱
    for i_id in land_ids:
        d.get(f"cmd=factionarmy&op=getIslandAward&island_id={i_id}")
        d.log(d.find()).append()


def 帮派远征军(d: DaLeDou):
    while True:
        # 帮派远征军
        d.get("cmd=factionarmy&op=viewIndex&island_id=-1")
        p_id = d.find(r'point_id=(\d+)">参战')
        if p_id is None:
            d.log("已经全部通关了").append()
            帮派远征军_领取(d)
            break
        # 参战
        d.get(f"cmd=factionarmy&op=viewpoint&point_id={p_id}")

        data = []
        for _ in range(20):
            data += d.findall(r'(\d+)\.\d+<a.*?opp_uin=(\d+)">攻击')
            pages = d.find(r'pages=(\d+)">下一页')
            if not data or pages is None:
                break
            # 下一页
            d.get(f"cmd=factionarmy&op=viewpoint&point_id={p_id}&page={pages}")

        for _, u in sorted(data, key=lambda x: int(x[0])):
            if not 帮派远征军_攻击(d, p_id, u):
                帮派远征军_领取(d)
                return


def 帮派黄金联赛_参战(d: DaLeDou):
    # 参战
    d.get("cmd=factionleague&op=2")
    if "opp_uin" not in d.html:
        d.log("敌人已全部阵亡").append()
        return

    data = []
    if pages := d.find(r'pages=(\d+)">末页'):
        _pages = int(pages)
    else:
        _pages = 1
    for p in range(1, _pages + 1):
        d.get(f"cmd=factionleague&op=2&pages={p}")
        data += d.findall(r"%&nbsp;&nbsp;(\d+).*?opp_uin=(\d+)")

    for _, u in sorted(data, key=lambda x: int(x[0])):
        # 攻击
        d.get(f"cmd=factionleague&op=4&opp_uin={u}")
        if "勇士，" in d.html:
            d.log(d.find())
            if "不幸战败" in d.html:
                d.append()
                return
        elif "您已阵亡" in d.html:
            d.log(d.find(r"<br /><br />(.*?)</p>")).append()
            return

    # 参战
    d.get("cmd=factionleague&op=2")
    if "opp_uin" not in d.html:
        d.log("敌人已全部阵亡").append()
        return


def 帮派黄金联赛(d: DaLeDou):
    # 帮派黄金联赛
    d.get("cmd=factionleague&op=0")
    if "领取奖励" in d.html:
        # 领取轮次奖励
        d.get("cmd=factionleague&op=5")
        d.log(d.find(r"<p>(.*?)<br /><br />")).append()
    elif "领取帮派赛季奖励" in d.html:
        # 领取帮派赛季奖励
        d.get("cmd=factionleague&op=7")
        d.log(d.find(r"<p>(.*?)<br /><br />")).append()
    elif "已参与防守" not in d.html:
        # 参与防守
        d.get("cmd=factionleague&op=1")
        d.log(d.find(r"<p>(.*?)<br /><br />")).append()
    elif "休赛期" in d.html:
        d.log("休赛期无任何操作").append()

    if "op=2" in d.html:
        帮派黄金联赛_参战(d)


def 任务派遣中心(d: DaLeDou):
    c_任务派遣中心(d)


def 武林盟主(d: DaLeDou):
    if d.week in [3, 5, 7]:
        # 武林盟主
        d.get("cmd=wlmz&op=view_index")
        if data := d.findall(r'section_id=(\d+)&amp;round_id=(\d+)">'):
            for s, r in data:
                d.get(f"cmd=wlmz&op=get_award&section_id={s}&round_id={r}")
                d.log(d.find(r"<br /><br />(.*?)</p>")).append()
        else:
            d.log("没有奖励领取").append()

    if d.week in [1, 3, 5]:
        _id: int = d.config["武林盟主"]
        if _id is None:
            d.log("你没有配置报名赛场id").append()
            return
        d.get(f"cmd=wlmz&op=signup&ground_id={_id}")
        if "总决赛周不允许报名" in d.html or "您的战力不足" in d.html:
            d.log(d.find(r"战报</a><br />(.*?)<br />")).append()
        elif "您已报名" in d.html:
            d.log(d.find(r"赛场】<br />(.*?)<br />")).append()
    elif d.week in [2, 4, 6]:
        for index in range(8):
            # 选择
            d.get(f"cmd=wlmz&op=guess_up&index={index}")
            d.log(d.find(r"规则</a><br />(.*?)<br />"))
        # 确定竞猜选择
        d.get("cmd=wlmz&op=comfirm")
        d.log(d.find(r"战报</a><br />(.*?)<br />")).append()


def 全民乱斗(d: DaLeDou):
    collect_status = False
    for t in [2, 3, 4]:
        d.get(f"cmd=luandou&op=0&acttype={t}")
        for _id in d.findall(r'.*?id=(\d+)">领取</a>'):
            collect_status = True
            # 领取
            d.get(f"cmd=luandou&op=8&id={_id}")
            d.log(d.find(r"斗】<br /><br />(.*?)<br />")).append()
    if not collect_status:
        d.log("没有礼包领取").append()


def 侠士客栈(d: DaLeDou):
    c_侠士客栈(d)

    if d.week != 4:
        return

    # 共建回馈
    d.get("cmd=notice&op=view&sub=total")
    for _id in d.findall(r"giftId=(\d+)"):
        # 领取
        d.get(f"cmd=notice&op=reqreward&giftId={_id}&sub=total")
        d.log(d.find(r"<p>.*?<br />(.*?)<")).append()


def 江湖长梦(d: DaLeDou):
    config: list[dict] = d.config["江湖长梦"]["exchange"]
    if config is None:
        return

    for name, _id, exchange_quantity in get_exchange_config(config):
        count = 0
        for _ in range(exchange_quantity):
            d.get(f"cmd=longdreamexchange&op=exchange&key_id={_id}")
            if "成功" not in d.html:
                d.log(d.find(), f"{name}*1")
                break
            d.log(d.find(r"</a><br />(.*?)<"), f"{name}*1")
            count += 1
        if count:
            d.append(f"兑换{name}*{count}")


def 大侠回归三重好礼(d: DaLeDou):
    # 大侠回归三重好礼
    d.get("cmd=newAct&subtype=173&op=1")
    if data := d.findall(r"subtype=(\d+).*?taskid=(\d+)"):
        for s, t in data:
            # 领取
            d.get(f"cmd=newAct&subtype={s}&op=2&taskid={t}")
            d.log(d.find(r"】<br /><br />(.*?)<br />")).append()
    else:
        d.log("没有礼包领取").append()


def 备战天赋(d: DaLeDou, _id: int):
    # 备战天赋
    d.get("cmd=ascendheaven&op=viewprepare")
    start_id = d.find(r"id=(\d+)")
    if start_id is None:
        return

    for i in range(int(start_id), _id + 1):
        while True:
            # 激活
            d.get(f"cmd=ascendheaven&op=activeskill&id={i}")
            d.log(d.find())
            if "激活心法失败" in d.html:
                continue
            d.append()
            if "激活心法成功" in d.html:
                break
            # 您尚未点击上一级天赋，无法点击该天赋
            # 您报名的不是排位赛，无法修改备战天赋
            return


def 飞升大作战(d: DaLeDou):
    config = d.config["飞升大作战"]
    is_exchange: bool = config["玄铁令"]
    t: int = config["type"]
    _id: int | None = config["id"]

    # 飞升大作战
    d.get("cmd=ascendheaven")
    if "赛季结算中" in d.html:
        is_exchange = False

    if is_exchange and t == 1:  # 报名单排模式之前兑换
        # 兑换玄铁令*1
        d.get("cmd=ascendheaven&op=exchange&id=2&times=1")
        d.log(d.find()).append()
    elif is_exchange and t == 3:  # 报名双排模式之前兑换
        # 兑换玄铁令*1
        d.get("cmd=ascendheaven&op=exchange&id=2&times=1")
        d.log(d.find()).append()
        # 兑换玄铁令*1
        d.get("cmd=ascendheaven&op=exchange&id=2&times=1")
        d.log(d.find()).append()

    # 报名
    d.get(f"cmd=ascendheaven&op=signup&type={t}")
    d.log(d.find()).append()
    if "你报名参加了" in d.html or "你已经报名参赛" in d.html:
        if t in {1, 3} and _id is not None:
            备战天赋(d, _id)
    else:
        # 当前为休赛期，不在报名时间、还没有入场券玄铁令
        # 报名匹配模式
        d.get("cmd=ascendheaven&op=signup&type=2")
        d.log(d.find()).append()

    if d.week != 4:
        return

    # 飞升大作战
    d.get("cmd=ascendheaven")
    if "赛季结算中" not in d.html:
        return

    # 境界修为
    d.get("cmd=ascendheaven&op=showrealm")
    for s in d.findall(r"season=(\d+)"):
        # 领取奖励
        d.get(f"cmd=ascendheaven&op=getrealmgift&season={s}")
        d.log(d.find()).append()


def 许愿帮铺(d: DaLeDou):
    config: list[dict] = d.config["深渊之潮"]["exchange"]
    if config is None:
        return

    for name, _id, exchange_quantity in get_exchange_config(config):
        count = 0
        if "之书" in name:
            quotient = exchange_quantity // 25
        else:
            quotient = 0
        for _ in range(quotient):
            d.get(f"cmd=abysstide&op=wishexchangetimes&id={_id}&times=25")
            d.log(d.find(), f"{name}*25")
            if "成功" not in d.html:
                break
            count += 25
        for _ in range(exchange_quantity - count):
            d.get(f"cmd=abysstide&op=wishexchange&id={_id}")
            d.log(d.find(), f"{name}*1")
            if "成功" not in d.html:
                break
            count += 1
        if count:
            d.append(f"兑换{name}*{count}")


def 深渊之潮(d: DaLeDou):
    c_帮派巡礼(d)
    c_深渊秘境(d)
    if d.day == 20:
        许愿帮铺(d)


def 侠客岛(d: DaLeDou):
    d.get("cmd=knight_island&op=viewmissionindex")
    pos = d.findall(r"viewmissiondetail&amp;pos=(\d+)")
    if not pos:
        for name, duration in d.findall(r"([^<>]+?)（需要.*?任务时长：([^<]+)"):
            d.log(f"{name}：{duration}").append()
        return

    config: set[str] = set(d.config["侠客岛"])
    free_refresh_count = int(d.find(r"免费刷新剩余：(\d+)"))
    for p in pos:
        for _ in range(5):
            # 侠客行
            d.get("cmd=knight_island&op=viewmissionindex")
            reward = d.find(rf'pos={p}">接受.*?任务奖励：([^<]+)')

            # 接受
            d.get(f"cmd=knight_island&op=viewmissiondetail&pos={p}")
            name = d.find(r"([^>]+?)（")
            d.log(f"任务奖励：{reward}", f"侠客岛-{name}")

            if reward not in config and free_refresh_count > 0:
                # 刷新
                d.get(f"cmd=knight_island&op=refreshmission&pos={p}")
                d.log(d.find(r"斗豆）<br />(.*?)<br />"), f"侠客岛-{name}")
                free_refresh_count -= 1
                continue

            # 快速委派
            d.get(f"cmd=knight_island&op=autoassign&pos={p}")
            d.log(d.find(r"）<br />(.*?)<br />"), f"侠客岛-{name}")

            if "快速委派成功" in d.html:
                # 开始任务
                d.get(f"cmd=knight_island&op=begin&pos={p}")
                html = d.find(r"斗豆）<br />(.*?)<br />")
                d.log(html, f"侠客岛-{name}")
                d.append(f"{name}：{html}")
                break

            if "符合条件侠士数量不足" in d.html and free_refresh_count > 0:
                # 刷新
                d.get(f"cmd=knight_island&op=refreshmission&pos={p}")
                d.log(d.find(r"斗豆）<br />(.*?)<br />"), f"侠客岛-{name}")
                free_refresh_count -= 1
                continue
            else:
                d.log("没有免费刷新次数了", f"侠客岛-{name}")
                d.append(f"{name}：符合条件侠士数量不足")
                break


def 八卦迷阵(d: DaLeDou):
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
    d.get("cmd=spacerelic&op=goosip")
    result = d.find(r"([乾坤震巽坎离艮兑]{4})")
    if result is None:
        result = d.config["时空遗迹"]["八卦迷阵"]

    for i in result:
        # 点击八卦
        d.get(f"cmd=spacerelic&op=goosip&id={_data[i]}")
        d.log(
            f"{i}：" + d.find(r"分钟<br /><br />(.*?)<br />"), "时空遗迹-八卦迷阵"
        ).append()
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
        d.get("cmd=spacerelic&op=goosipgift")
        d.log(d.find(r"分钟<br /><br />(.*?)<br />"), "时空遗迹-八卦迷阵").append()


def 遗迹商店(d: DaLeDou):
    config: dict = d.config["时空遗迹"]["exchange"]
    if config is None:
        return

    for t, _list in config.items():
        for name, _id, exchange_quantity in get_exchange_config(_list):
            count = 0
            for _ in range(exchange_quantity // 10):
                # 兑换十次
                d.get(f"cmd=spacerelic&op=buy&type={t}&id={_id}&num=10")
                d.log(
                    d.find(r"售卖区.*?<br /><br /><br />(.*?)<"),
                    f"{name}*10",
                )
                if "兑换成功" not in d.html:
                    break
                count += 10
            for _ in range(exchange_quantity - count):
                # 兑换一次
                d.get(f"cmd=spacerelic&op=buy&type={t}&id={_id}&num=1")
                d.log(
                    d.find(r"售卖区.*?<br /><br /><br />(.*?)<"),
                    f"{name}*1",
                )
                if "兑换成功" not in d.html:
                    break
                count += 1
            if count:
                d.append(f"兑换{name}*{count}")


def 异兽洞窟(d: DaLeDou):
    _ids: list = d.config["时空遗迹"]["异兽洞窟"]
    if _ids is None:
        d.log("你没有配置异兽洞窟id").append()
        return

    for _id in _ids:
        d.get(f"cmd=spacerelic&op=monsterdetail&id={_id}")
        if "剩余挑战次数：0" in d.html:
            d.log("异兽洞窟没有挑战次数", "时空遗迹-异兽洞窟").append()
            break
        if "剩余血量：0" in d.html:
            # 扫荡
            d.get(f"cmd=spacerelic&op=saodang&id={_id}")
        else:
            # 挑战
            d.get(f"cmd=spacerelic&op=monsterfight&id={_id}")
        d.log(d.find(r"次数.*?<br /><br />(.*?)&"), "时空遗迹-异兽洞窟")
        if "请按顺序挑战异兽" in d.html:
            continue
        d.append()
        break


def 悬赏任务(d: DaLeDou):
    data = []
    for t in [1, 2]:
        d.get(f"cmd=spacerelic&op=task&type={t}")
        data += d.findall(r"type=(\d+)&amp;id=(\d+)")
    for t, _id in data:
        d.get(f"cmd=spacerelic&op=task&type={t}&id={_id}")
        d.log(d.find(r"赛季任务</a><br /><br />(.*?)<"), "时空遗迹-悬赏任务")
        if "您未完成该任务" in d.html:
            continue
        d.append()


def 遗迹征伐(d: DaLeDou):
    # 遗迹征伐
    d.get("cmd=spacerelic&op=relicindex")
    year = int(d.find(r"(\d+)年"))
    month = int(d.find(r"(\d+)月"))
    day = int(d.find(r"(\d+)日"))

    # 获取当前日期和结束日期前一天
    current_date, day_before_end = DateTime.get_current_and_end_date_offset(
        year, month, day
    )
    if current_date == day_before_end:
        # 悬赏任务-登录奖励
        d.get("cmd=spacerelic&op=task&type=1&id=1")
        d.log(d.find(r"赛季任务</a><br /><br />(.*?)<"), "时空遗迹-悬赏任务").append()
        # 排行奖励
        d.get("cmd=spacerelic&op=getrank")
        d.log(d.find(r"奖励</a><br /><br />(.*?)<"), "时空遗迹-赛季排行").append()

        遗迹商店(d)
        return

    # 获取当前日期和结束日期前七天
    current_date, seven_date_before_end = DateTime.get_current_and_end_date_offset(
        year, month, day, 7
    )
    if current_date >= seven_date_before_end:
        # 第八周（结束日期上周四~本周三）
        d.log("当前处于休赛期，结束前一天领取登录奖励、赛季奖励和悬赏商店兑换").append()
        return

    异兽洞窟(d)

    # 联合征伐挑战
    d.get("cmd=spacerelic&op=bossfight")
    d.log(d.find(r"挑战</a><br />(.*?)&"), "时空遗迹-联合征伐").append()

    悬赏任务(d)


def 时空遗迹(d: DaLeDou):
    八卦迷阵(d)
    遗迹征伐(d)


def 世界树(d: DaLeDou):
    # 世界树
    d.get("cmd=worldtree")
    # 一键领取经验奖励
    d.get("cmd=worldtree&op=autoget&id=1")
    d.log(d.find(r"福宝<br /><br />(.*?)<br />")).append()

    def get_id() -> str | None:
        # 温养武器选择
        for t in range(4):
            d.get(f"cmd=worldtree&op=viewweaponpage&type={t}")
            for _id in d.findall(r"weapon_id=(\d+)"):
                # 选择
                d.get(f"cmd=worldtree&op=setweapon&weapon_id={_id}&type={t}")
                d.log(d.find(r"当前武器：(.*?)<"))
                return _id

    # 源宝树
    d.get("cmd=worldtree&op=viewexpandindex")
    if "免费温养" not in d.html:
        d.log("没有免费温养次数").append()
        return

    if "weapon_id=0" in d.html and not get_id():
        d.log("没有武器可选择").append()
        return

    # 源宝树
    d.get("cmd=worldtree&op=viewexpandindex")
    _id = d.find(r"weapon_id=(\d+)")
    # 免费温养
    d.get(f"cmd=worldtree&op=dostrengh&times=1&weapon_id={_id}")
    d.log(d.find(r"规则</a><br />(.*?)<br />")).append()
    d.log("当前进度：" + d.find(r"当前进度:(.*?)<")).append()


def 龙凰论武(d: DaLeDou):
    if d.day == 1:
        zone: int = d.config["龙凰之境"]["zone"]
        # 报名
        d.get(f"cmd=dragonphoenix&op=sign&zone={zone}")
        d.log(d.find()).append()
    elif 4 <= d.day <= 25:
        c_龙凰论武(d)
        # 每日领奖
        d.get("cmd=dragonphoenix&op=gift")
        d.log(d.find(r"/\d+</a><br /><br />(.*?)<")).append()
    elif d.day == 27:
        # 排行奖励
        d.get("cmd=dragonphoenix&op=rankreward")
        d.log(d.find(r"<br /><br /><br />(.*?)<")).append()


def 龙凰云集(d: DaLeDou):
    if d.day != 27:
        return

    # 龙凰云集
    d.get("cmd=dragonphoenix&op=yunji")
    for _id in d.findall(r"idx=(\d+)"):
        # 领奖
        d.get(f"cmd=dragonphoenix&op=reward&idx={_id}")
        d.log(d.find(r"<br /><br /><br />(.*?)<")).append()
        if "当前无可领取奖励" in d.html:
            break

    config: list[dict] = d.config["龙凰之境"]["exchange"]
    if config is None:
        return

    for name, _id, exchange_quantity in get_exchange_config(config):
        count = 0
        for _ in range(exchange_quantity // 10):
            d.get(f"cmd=dragonphoenix&op=buy&id={_id}&num=10")
            d.log(d.find(r"<br /><br /><br />(.*?)<"), f"{name}*10")
            if "成功" not in d.html:
                break
            count += 10
        for _ in range(exchange_quantity - count):
            d.get(f"cmd=dragonphoenix&op=buy&id={_id}&num=1")
            d.log(d.find(r"<br /><br /><br />(.*?)<"), f"{name}*1")
            if "成功" not in d.html:
                break
            count += 1
        if count:
            d.append(f"兑换{name}*{count}")


def 龙吟破阵(d: DaLeDou):
    if d.day != 1:
        return
    # 领取
    d.get("cmd=dragonphoenix&op=getlastreward")
    d.log(d.find(r"领取<br /><br />(.*?)<")).append()


def 龙凰之境(d: DaLeDou):
    龙凰论武(d)
    龙凰云集(d)
    龙吟破阵(d)


def 增强经脉(d: DaLeDou):
    # 经脉
    d.get("cmd=intfmerid&sub=1")
    if "关闭" in d.html:
        # 关闭合成两次确认
        d.get("cmd=intfmerid&sub=19")
        d.log(r"关闭合成两次确认", "任务-增强经脉")
    if "取消" in d.html and "doudou=0" in d.html:
        # 取消传功符不足用斗豆代替
        d.get("cmd=intfmerid&sub=21&doudou=0")
        d.log("取消传功符不足用斗豆代替", "任务-增强经脉")

    if int(d.find(r"传功符</a>:(\d+)")) < 200:
        d.log("传功符数量不足200", "任务-增强经脉")
        return

    for _ in range(12):
        # 经脉
        d.get("cmd=intfmerid&sub=1")
        _id = d.find(r'master_id=(\d+)">传功</a>')

        # 传功
        d.get(f"cmd=intfmerid&sub=2&master_id={_id}")
        d.log(d.find(r"</p>(.*?)<p>"), "任务-增强经脉")
        if "传功符不足！" in d.html:
            return

        # 一键拾取
        d.get("cmd=intfmerid&sub=5")
        d.log(d.find(r"</p>(.*?)<p>"), "任务-增强经脉")
        # 一键合成
        d.get("cmd=intfmerid&sub=10&op=4")
        d.log(d.find(r"</p>(.*?)<p>"), "任务-增强经脉")


def 助阵(d: DaLeDou):
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
            d.get(p)
            if "助阵组合所需佣兵不满足条件，不能提升助阵属性经验" in d.html:
                d.log(d.find(r"<br /><br />(.*?)。"), "任务-助阵")
                return
            elif "阅历不足" in d.html:
                d.log(d.find(r"<br /><br />(.*?)，"), "任务-助阵")
                return

            d.log(d.find(), "任务-助阵")
            if "提升成功" in d.html:
                count += 1
            elif "经验值已经达到最大" in d.html:
                break
            elif "你还没有激活该属性" in d.html:
                return


def 查看好友资料(d: DaLeDou):
    # 乐斗助手
    d.get("cmd=view&type=6")
    if "开启查看好友信息和收徒" in d.html:
        #  开启查看好友信息和收徒
        d.get("cmd=set&type=1")
        d.log("开启查看好友信息和收徒").append()
    # 好友第2页
    d.get("cmd=friendlist&page=2")
    for uin in d.findall(r"</a>\d+.*?B_UID=(\d+)"):
        d.get(f"cmd=totalinfo&B_UID={uin}")


def 徽章进阶(d: DaLeDou):
    # 关闭道具不足自动购买
    d.get("cmd=achievement&op=setautobuy&enable=0&achievement_id=12")
    for _id in range(1, 41):
        d.get(f"cmd=achievement&op=upgradelevel&achievement_id={_id}&times=1")
        if "【徽章馆】" not in d.html:
            d.log(d.find(), "任务-徽章进阶")
            break
        d.log(d.find("<br /><br />(.*?)<"), "任务-徽章进阶")


def 兵法研习(d: DaLeDou):
    """
    兵法      消耗     id    功能
    金兰之泽  孙子兵法  2544  增加生命
    雷霆一击  孙子兵法  2570  增加伤害
    残暴攻势  武穆遗书  21001 增加暴击几率
    不屈意志  武穆遗书  21032 降低受到暴击几率
    """
    for _id in [21001, 2570, 21032, 2544]:
        d.get(f"cmd=brofight&subtype=12&op=practice&baseid={_id}")
        d.log(d.find(r"武穆遗书：\d+个<br />(.*?)<br />"), "任务-兵法研习")
        if "研习成功" in d.html:
            break


def 挑战陌生人(d: DaLeDou):
    # 斗友
    d.get("cmd=friendlist&type=1")
    for u in d.findall(r"</a>\d+.*?B_UID=(\d+)")[:4]:
        d.get(f"cmd=fight&B_UID={u}&page=1&type=9")
        d.log(d.find(r"删</a><br />(.*?)！"), "任务-挑战陌生人")


def 任务(d: DaLeDou):
    """助阵每天必做"""
    助阵(d)

    # 日常任务
    task_html = d.get("cmd=task&sub=1")
    if "增强经脉" in task_html:
        增强经脉(d)
    if "查看好友资料" in task_html:
        查看好友资料(d)
    if "徽章进阶" in task_html:
        徽章进阶(d)
    if "兵法研习" in task_html:
        兵法研习(d)
    if "挑战陌生人" in task_html:
        挑战陌生人(d)

    # 一键完成任务
    d.get("cmd=task&sub=7")
    for k, v in d.findall(r'id=\d+">(.*?)</a>.*?>(.*?)</a>'):
        d.log(f"{k} {v}").append()


def 帮派供奉(d: DaLeDou):
    _ids: list = d.config["我的帮派"]
    if _ids is None:
        d.log("你没有配置帮派供奉物品id").append()
        return

    for _id in _ids:
        for _ in range(5):
            # 供奉
            d.get(f"cmd=oblation&id={_id}&page=1")
            if "供奉成功" in d.html:
                d.log(d.find()).append()
                continue
            d.log(d.find(r"】</p><p>(.*?)<br />"))
            break
        if "每天最多供奉5次" in d.html:
            break


def 帮派任务(d: DaLeDou):
    # 帮派任务
    task_html = d.get("cmd=factiontask&sub=1")
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
            d.get(url)
            d.log(name)
    if "帮派修炼" in task_html:
        count = 0
        for _id in [2727, 2758, 2505, 2536, 2437, 2442, 2377, 2399, 2429]:
            for _ in range(4):
                # 修炼
                d.get(f"cmd=factiontrain&type=2&id={_id}&num=1&i_p_w=num%7C")
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
    d.get("cmd=factiontask&sub=1")
    for _id in d.findall(r'id=(\d+)">领取奖励</a>'):
        # 领取奖励
        d.get(f"cmd=factiontask&sub=3&id={_id}")
        d.log(d.find(r"日常任务</a><br />(.*?)<br />")).append()


def 我的帮派(d: DaLeDou):
    # 我的帮派
    d.get("cmd=factionop&subtype=3&facid=0")
    if "你的职位" not in d.html:
        d.log("您还没有加入帮派").append()
        return

    帮派供奉(d)
    帮派任务(d)

    if d.week != 7:
        return

    # 领取奖励 》报名帮战 》激活祝福
    for sub in [4, 9, 6]:
        d.get(f"cmd=facwar&sub={sub}")
        d.log(d.find(r"</p>(.*?)<br /><a.*?查看上届")).append()


def 帮派祭坛(d: DaLeDou):
    # 帮派祭坛
    d.get("cmd=altar")
    for _ in range(30):
        if "转动轮盘" in d.html:
            # 转动轮盘
            d.get("cmd=altar&op=spinwheel")
            if "转动轮盘" in d.html:
                d.log(d.find()).append()
            if "转转券不足" in d.html or "已达转转券转动次数上限" in d.html:
                return
        if "【随机分配】" in d.html:
            all_disbanded = True
            data = d.findall(r"op=(.*?)&amp;id=(\d+)")
            for op, _id in data:
                # 选择
                d.get(f"cmd=altar&op={op}&id={_id}")
                if "选择路线" in d.html:
                    # 向前|向左|向右
                    d.get(f"cmd=altar&op=dosteal&id={_id}")
                if "该帮派已解散" in d.html or "系统繁忙" in d.html:
                    d.log(d.find(r"<br /><br />(.*?)<br />"))
                    continue
                all_disbanded = False
                if "转动轮盘" in d.html:
                    d.log(d.find()).append()
                    break
            if all_disbanded and data:
                d.append()
                return
        if "领取奖励" in d.html:
            d.get("cmd=altar&op=drawreward")
            d.log(d.find()).append()


def 每日奖励(d: DaLeDou):
    for key in ["login", "meridian", "daren", "wuzitianshu"]:
        # 每日奖励
        d.get(f"cmd=dailygift&op=draw&key={key}")
        d.log(d.find()).append()


def 领取徒弟经验(d: DaLeDou):
    # 领取徒弟经验
    d.get("cmd=exp")
    d.log(d.find(r"每日奖励</a><br />(.*?)<br />")).append()


def 今日活跃度(d: DaLeDou):
    # 今日活跃度
    d.get("cmd=liveness")
    d.log(d.find(r"【(.*?)】")).append()
    if "帮派总活跃" in d.html:
        d.log(d.find(r"礼包</a><br />(.*?)<")).append()

    # 领取今日活跃度礼包
    for giftbag_id in range(1, 5):
        d.get(f"cmd=liveness_getgiftbag&giftbagid={giftbag_id}&action=1")
        d.log(d.find(r"】<br />(.*?)<p>")).append()

    # 领取帮派总活跃奖励
    d.get("cmd=factionop&subtype=18")
    if "创建帮派" in d.html:
        d.log(d.find(r"帮派</a><br />(.*?)<br />")).append()
    else:
        d.log(d.find()).append()


def 仙武修真(d: DaLeDou):
    for task_id in range(1, 4):
        # 领取
        d.get(f"cmd=immortals&op=getreward&taskid={task_id}")
        d.log(d.find(r"帮助</a><br />(.*?)<br />")).append()

    challenge_count = int(d.find(r"剩余挑战次数：(\d+)"))
    for _ in range(challenge_count):
        _id = random.choice([1, 2, 3])
        # 寻访
        d.get(f"cmd=immortals&op=visitimmortals&mountainId={_id}")
        d.log(d.find(r"帮助</a><br />(.*?)<"))
        d.log(f"本次寻访：{d.find(r'本次寻访：.*?>(.*?)<')}").append()
        # 挑战
        d.get("cmd=immortals&op=fightimmortals")
        d.log(d.find(r"帮助</a><br />(.*?)<")).append()


def 乐斗黄历(d: DaLeDou):
    # 领取
    d.get("cmd=calender&op=2")
    d.log(d.find(r"<br /><br />(.*?)<br />")).append()
    # 占卜
    d.get("cmd=calender&op=4")
    d.log(d.find(r"<br /><br />(.*?)<br />")).append()

    # 乐斗黄历
    d.get("cmd=calender&op=0")
    if "斗神塔掉落，每日奖励双倍" not in d.html:
        return

    challenge_count: int = d.config["乐斗黄历"]
    if challenge_count <= 0:
        return

    斗神塔(d, "乐斗黄历-斗神塔", challenge_count)


def 器魂附魔(d: DaLeDou):
    for _id in range(1, 4):
        # 领取
        d.get(f"cmd=enchant&op=gettaskreward&task_id={_id}")
        d.log(d.find()).append()


def 兵法(d: DaLeDou):
    if d.week == 4:
        # 助威
        d.get("cmd=brofight&subtype=13")
        _id = d.find(r"teamid=(\d+).*?助威</a>")
        # 确定
        d.get(f"cmd=brofight&subtype=13&teamid={_id}&type=5&op=cheer")
        d.log(d.find(r"领奖</a><br />(.*?)<br />")).append()

    if d.week != 6:
        return

    # 领奖
    d.get("cmd=brofight&subtype=13&op=draw")
    d.log(d.find(r"领奖</a><br />(.*?)<br />")).append()

    for t in range(1, 6):
        d.get(f"cmd=brofight&subtype=10&type={t}")
        for remainder, u in d.findall(r"50000.*?(\d+).*?champion_uin=(\d+)"):
            if remainder == "0":
                continue
            # 领斗币
            d.get(f"cmd=brofight&subtype=10&op=draw&champion_uin={u}&type={t}")
            d.log(d.find(r"排行</a><br />(.*?)<br />")).append()
            return


# ============================================================


def get_boss_id():
    """返回历练高等级到低等级场景每关最后两个BOSS的id"""
    for _id in range(6394, 6013, -20):
        yield _id
        yield (_id - 1)


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


def 点亮(d: DaLeDou) -> bool:
    # 点亮南瓜灯
    d.get("cmd=hallowmas&gb_id=1")
    while True:
        if cushaw_id := d.findall(r"cushaw_id=(\d+)"):
            c_id = random.choice(cushaw_id)
            # 南瓜
            d.get(f"cmd=hallowmas&gb_id=4&cushaw_id={c_id}")
            d.log(d.find()).append()
            if "活力" in d.html:
                return True
        if "请领取今日的活跃度礼包来获得蜡烛吧" in d.html:
            break
    return False


def 点亮南瓜灯(d: DaLeDou):
    # 乐斗助手
    d.get("cmd=view&type=6")
    if "取消自动使用活力药水" in d.html:
        # 取消自动使用活力药水
        d.get("cmd=set&type=11")
        d.log("取消自动使用活力药水")
    for _id in get_boss_id():
        count = 3
        while count:
            d.get(f"cmd=mappush&subtype=3&npcid={_id}&pageid=2")
            if "您还没有打到该历练场景" in d.html:
                d.log(d.find(r"介绍</a><br />(.*?)<br />"), "历练").append()
                break
            d.log(d.find(r"\d+<br />(.*?)<"), "历练").append()
            if "活力不足" in d.html:
                if not 点亮(d):
                    return
                continue
            elif "BOSS" not in d.html:
                # 你今天和xx挑战次数已经达到上限了，请明天再来挑战吧
                # 还不能挑战
                break
            count -= 1


def 万圣节(d: DaLeDou):
    点亮南瓜灯(d)

    # 万圣节
    d.get("cmd=hallowmas")
    month, day = d.findall(r"(\d+)月(\d+)日6点")[0]
    # 获取当前日期和结束日期前一天
    current_date, day_before_end = DateTime.get_current_and_end_date_offset(
        d.year, int(month), int(day)
    )
    if current_date == day_before_end:
        # 兑换礼包B 消耗40个南瓜灯
        d.get("cmd=hallowmas&gb_id=6")
        d.log(d.find()).append()
        # 兑换礼包A 消耗20个南瓜灯
        d.get("cmd=hallowmas&gb_id=5")
        d.log(d.find()).append()


def 元宵节(d: DaLeDou):
    # 领取
    d.get("cmd=newAct&subtype=101&op=1")
    d.log(d.find(r"】</p>(.*?)<br />")).append()
    # 领取形象卡
    d.get("cmd=newAct&subtype=101&op=2&index=0")
    d.log(d.find(r"】</p>(.*?)<br />")).append()


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


def 客栈同福(d: DaLeDou):
    c_客栈同福(d)


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


def 幸运金蛋(d: DaLeDou):
    c_幸运金蛋(d)


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


def 新春拜年(d: DaLeDou):
    # 新春拜年
    d.get("cmd=newAct&subtype=147")
    if "op=1" in d.html:
        for i in random.sample(range(5), 3):
            # 选中
            d.get(f"cmd=newAct&subtype=147&op=1&index={i}")
        # 赠礼
        d.get("cmd=newAct&subtype=147&op=2")
        d.log("已赠礼").append()


def 喜从天降(d: DaLeDou):
    for _ in range(10):
        d.get("cmd=newAct&subtype=137&op=1")
        d.log(d.find()).append()
        if "燃放烟花次数不足" in d.html:
            break


def 福利_历练(d: DaLeDou, name: str):
    # 乐斗助手
    d.get("cmd=view&type=6")
    if "开启自动使用活力药水" in d.html:
        # 开启自动使用活力药水
        d.get("cmd=set&type=11")
        d.log("开启自动使用活力药水")

    for _id in get_boss_id():
        for _ in range(3):
            d.get(f"cmd=mappush&subtype=3&mapid=6&npcid={_id}&pageid=2")
            if "您还没有打到该历练场景" in d.html:
                d.log(d.find(r"介绍</a><br />(.*?)<br />"), name).append()
                break
            d.log(d.find(r"阅历值：\d+<br />(.*?)<br />"), name).append()
            if "活力不足" in d.html or "活力药水使用次数已达到每日上限" in d.html:
                return
            elif "BOSS" not in d.html:
                # 你今天和xx挑战次数已经达到上限了，请明天再来挑战吧
                # 还不能挑战
                break


def 节日福利(d: DaLeDou):
    config: dict = d.config["节日福利"]

    if config["历练"]:
        福利_历练(d, "节日福利-历练")

    if d.week != 4:
        return

    challenge_count: int = config["斗神塔"]
    if challenge_count <= 0:
        return

    斗神塔(d, "节日福利-斗神塔", challenge_count)


def 金秋福利(d: DaLeDou):
    config: dict = d.config["金秋福利"]

    if config["历练"]:
        福利_历练(d, "金秋福利-历练")

    if d.week != 4:
        return

    challenge_count: int = config["斗神塔"]
    if challenge_count <= 0:
        return

    斗神塔(d, "金秋福利-斗神塔", challenge_count)


def 双旦福利(d: DaLeDou):
    config: dict = d.config["双旦福利"]

    if config["历练"]:
        福利_历练(d, "双旦福利-历练")

    if d.week != 4:
        return

    challenge_count: int = config["斗神塔"]
    if challenge_count <= 0:
        return

    斗神塔(d, "双旦福利-斗神塔", challenge_count)


def 春节福利(d: DaLeDou):
    config: dict = d.config["春节福利"]

    if config["历练"]:
        福利_历练(d, "春节福利-历练")

    if d.week != 4:
        return

    challenge_count: int = config["斗神塔"]
    if challenge_count <= 0:
        return

    斗神塔(d, "春节福利-斗神塔", challenge_count)


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


def 微信兑换(d: DaLeDou):
    code: int = d.config["微信兑换"]
    # 兑换
    d.get(f"cmd=weixin&cdkey={code}&sub=2&zapp_sid=&style=0&channel=0&i_p_w=cdkey|")
    d.log(d.find()).append()


def 五一礼包(d: DaLeDou):
    for _id in range(3):
        # 领取
        d.get(f"cmd=newAct&subtype=113&op=1&id={_id}")
        d.log(d.find(r"】<br /><br />(.*?)<")).append()


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

    for name, _id, exchange_quantity in get_exchange_config(config):
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


def 乐斗大笨钟(d: DaLeDou):
    c_乐斗大笨钟(d)


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


def 乐斗能量棒(d: DaLeDou):
    # 乐斗能量棒
    d.get("cmd=newAct&subtype=108&op=0")
    data = d.findall(r"id=(\d+)")
    if not data:
        d.log("没有可领取的能量棒").append()
        return

    # 乐斗助手
    d.get("cmd=view&type=6")
    if "取消自动使用活力药水" in d.html:
        # 取消自动使用活力药水
        d.get("cmd=set&type=11")
        d.log("取消自动使用活力药水")

    for _id in get_boss_id():
        count = 3
        while count:
            d.get(f"cmd=mappush&subtype=3&npcid={_id}&pageid=2")
            if "您还没有打到该历练场景" in d.html:
                d.log(d.find(r"介绍</a><br />(.*?)<br />"), "历练").append()
                break
            d.log(d.find(r"\d+<br />(.*?)<"), "历练").append()
            if "活力不足" in d.html:
                if not data:
                    return
                # 领取活力能量棒
                d.get(f"cmd=newAct&subtype=108&op=1&id={data.pop()}")
                d.log(d.find(r"<br /><br />(.*?)<")).append()
                continue
            elif "BOSS" not in d.html:
                # 你今天和xx挑战次数已经达到上限了，请明天再来挑战吧
                # 还不能挑战
                break
            count -= 1


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


def 周年生日祝福(d: DaLeDou):
    for day in range(1, 8):
        d.get(f"cmd=newAct&subtype=165&op=3&day={day}")
        d.log(d.find()).append()


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
