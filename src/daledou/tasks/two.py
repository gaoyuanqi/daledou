"""
本模块为大乐斗第二轮任务
"""

from collections import Counter

from ..core.daledou import DaLeDou
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


def 深渊之潮(d: DaLeDou):
    c_帮派巡礼(d)
    c_深渊秘境(d)


def 侠客岛(d: DaLeDou):
    """侠客行最多领取3次任务奖励"""
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
    """使用背包物品"""
    use: list[str] = d.config["背包"]["use"]
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
    """周四镶嵌魂珠升级（碎 -> 1 -> 2 -> 3 -> 4）"""

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
    config: list[int] = d.config["神匠坊"]["符石分解"]
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
    """
    普通合成：每月20号合成
    符石分解：每月20号分解，分解类型详见配置文件
    符石打造：每月20号打造
    """
    普通合成(d)
    符石分解(d)
    符石打造(d)


def 每日宝箱(d: DaLeDou):
    """每月20号打开所有的铜质、银质、金质宝箱"""
    counter = Counter()
    # 每日宝箱
    d.get("cmd=dailychest")
    while t := d.find(r'type=(\d+)">打开'):
        # 打开
        d.get(f"cmd=dailychest&op=open&type={t}")
        msg = d.find(r"说明</a><br />(.*?)<")
        d.log(msg)
        counter.update({msg: 1})
        if "今日开宝箱次数已达上限" in d.html:
            break

    for k, v in counter.items():
        d.append(f"{v}次{k}")


def 商店(d: DaLeDou):
    """每天查询商店积分"""
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
    """收取礼物"""
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
