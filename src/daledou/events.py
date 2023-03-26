'''
活动
'''
import random

from src.daledou.daledou import DaLeDou


class Events(DaLeDou):

    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def get(params: str):
        global html
        html = DaLeDou.get(params)

    def 神魔转盘(self):
        Events.get('cmd=newAct&subtype=88&op=1')
        self.msg += DaLeDou.findall(r'【神魔转盘】<br />(.*?)<br />')

    def 乐斗驿站(self):
        Events.get('cmd=newAct&subtype=167&op=2')
        self.msg += DaLeDou.findall(r'【乐斗驿站】<br />(.*?)<br />')

    def 开心娃娃机(self):
        Events.get('cmd=newAct&subtype=124&op=1')
        self.msg += DaLeDou.findall(r'【开心娃娃机】<br />(.*?)<br />')

    def 好礼步步升(self):
        Events.get('cmd=newAct&subtype=43&op=get')
        self.msg += DaLeDou.findall(r'【好礼步步升】<br />(.*?)<br />')

    def 浩劫宝箱(self):
        Events.get('cmd=newAct&subtype=152')
        self.msg += DaLeDou.findall(r'浩劫宝箱<br />(.*?)<br />')

    def 幸运金蛋(self):
        # 幸运金蛋
        Events.get('cmd=newAct&subtype=110&op=0')
        index: list = DaLeDou.findall(r'index=(\d+)')
        for i in index:
            # 砸金蛋
            Events.get(f'cmd=newAct&subtype=110&op=1&index={i}')
            self.msg += DaLeDou.findall(r'【幸运金蛋】<br /><br />(.*?)<br />')

    def 幸运转盘(self):
        Events.get('cmd=newAct&subtype=57&op=roll')
        self.msg += DaLeDou.findall(r'0<br /><br />(.*?)<br />')

    def 惊喜刮刮卡(self):
        for i in range(3):
            Events.get(f'cmd=newAct&subtype=148&op=2&id={i}')
            self.msg += DaLeDou.findall(
                r'奖池预览</a><br /><br />(.*?)<br /><br />')

    def 甜蜜夫妻(self):
        for i in range(1, 4):
            # 领取
            Events.get(f'cmd=newAct&subtype=129&op=1&flag={i}')

    def 乐斗菜单(self):
        Events.get('cmd=menuact')
        # 乐斗菜单
        gift: list = DaLeDou.findall(r'套餐.*?gift=(\d+).*?点单</a>')
        if gift:
            # 点单
            Events.get(f'cmd=menuact&sub=1&gift={gift[0]}')
            self.msg += DaLeDou.findall(r'每日只能点取一份套餐哦！<br /></p>(.*?)<br />')
        else:
            self.msg += ['点单已领取完']

    def 客栈同福(self):
        for _ in range(3):
            # 献酒
            Events.get('cmd=newAct&subtype=155')
            self.msg += DaLeDou.findall(r'【客栈同福】<br /><p>(.*?)<br />')
            if '黄酒不足' in html:
                break

    def 周周礼包(self):
        # 周周礼包
        Events.get('cmd=weekgiftbag&sub=0')
        id: list = DaLeDou.findall(r';id=(\d+)">领取')
        if id:
            # 点单
            Events.get(f'cmd=weekgiftbag&sub=1&id={id[0]}')
            self.msg += DaLeDou.findall(r'【周周礼包】<br />(.*?)<br />')

    def 登录有礼(self):
        # 登录有礼
        Events.get('cmd=newAct&subtype=56')
        index: list = DaLeDou.findall(r'gift_index=(\d+)">领取')
        # 领取
        if index:
            Events.get(
                f'cmd=newAct&subtype=56&op=draw&gift_type=1&gift_index={index[-1]}')
            self.msg += DaLeDou.findall(r'】<br />(.*?)<br />')

    def 活跃礼包(self):
        Events.get('cmd=newAct&subtype=94&op=1')
        self.msg += DaLeDou.findall(r'【活跃礼包】.*?<br />(.*?)<br />')
        Events.get('cmd=newAct&subtype=94&op=2')
        self.msg += DaLeDou.findall(r'【活跃礼包】.*?<br />(.*?)<br />')

    def 猜单双(self):
        # 猜单双
        Events.get('cmd=oddeven')
        for _ in range(5):
            value: list = DaLeDou.findall(r'value=(\d+)">.*?数')
            if value:
                value = random.choice(value)
                # 单数1 双数2
                Events.get(f'cmd=oddeven&value={value}')
                self.msg += DaLeDou.findall(r'【猜单双】<br />(.*?)<br />')
            else:
                break

    def 上香活动(self):
        for _ in range(2):
            # 檀木香
            Events.get('cmd=newAct&subtype=142&op=1&id=1')
            self.msg += DaLeDou.findall(r'【缅怀金庸先生上香】<br />(.*?)<br />')
            # 龙涎香
            Events.get('cmd=newAct&subtype=142&op=1&id=2')
            self.msg += DaLeDou.findall(r'【缅怀金庸先生上香】<br />(.*?)<br />')

    def 徽章战令(self):
        # 每日礼包
        Events.get('cmd=badge&op=1')
        self.msg += DaLeDou.findall(r'【徽章战令】<br />(.*?)<br />')

    def 生肖福卡(self):
        # 领取
        Events.get('cmd=newAct&subtype=174&op=7&task_id=1')
        self.msg += DaLeDou.findall(r'~<br /><br />(.*?)<br />活跃度80')

    def 长安盛会(self):
        # 【盛会豪礼】 点击领取
        Events.get('cmd=newAct&subtype=118&op=1&id=1')
        self.msg += DaLeDou.findall(r'【长安盛会】<br />(.*?)<br />')
        # 【签到宝箱】 点击领取
        Events.get('cmd=newAct&subtype=118&op=1&id=2')
        self.msg += DaLeDou.findall(r'【长安盛会】<br />(.*?)<br />')
        # 点击参与
        for _ in range(3):
            Events.get('cmd=newAct&subtype=118&op=1&id=5')
            self.msg += DaLeDou.findall(r'【长安盛会】<br />(.*?)<br />')
            if '剩余次数不足' in html:
                break

    def 深渊秘宝(self):
        '''
        三魂秘宝 免费抽奖
        七魄秘宝 免费抽奖
        '''
        # 深渊秘宝
        Events.get('cmd=newAct&subtype=175')
        number: int = html.count('免费抽奖')
        if number == 2:
            for type in range(1, 3):
                Events.get(f'cmd=newAct&subtype=175&op=1&type={type}&times=1')
                self.msg += DaLeDou.findall(r'深渊秘宝<br />(.*?)<br />')
        else:
            self.msg += [f'免费抽奖次数为 {number}，不足两次时该任务不执行']

    def 登录商店(self):
        for _ in range(5):
            # 兑换5次 黄金卷轴*5
            Events.get('cmd=newAct&op=exchange&subtype=52&type=1223&times=5')
            self.msg += DaLeDou.findall(r'<br /><br />(.*?)<br /><br />')
        for _ in range(3):
            # 兑换3次 黄金卷轴*1
            Events.get('cmd=newAct&op=exchange&subtype=52&type=1223&times=1')
            self.msg += DaLeDou.findall(r'<br /><br />(.*?)<br /><br />')

    def 盛世巡礼(self):
        '''
        对话		cmd=newAct&subtype=150&op=3&itemId=0
        点击继续	cmd=newAct&subtype=150&op=4&itemId=0
        收下礼物	cmd=newAct&subtype=150&op=5&itemId=0
        '''
        for itemId in [0, 4, 6, 9, 11, 14, 17]:
            # 收下礼物
            Events.get(f'cmd=newAct&subtype=150&op=5&itemId={itemId}')
            self.msg += DaLeDou.findall(r'礼物<br />(.*?)<br />')

    def 十二周年生日祝福(self):
        for day in range(1, 8):
            Events.get(f'cmd=newAct&subtype=165&op=3&day={day}')
            self.msg += DaLeDou.findall(r'【乐斗生日祝福】<br />(.*?)<br />')

    def 中秋礼盒(self):
        for _ in range(3):
            # 中秋礼盒
            Events.get('cmd=midautumngiftbag&sub=0')
            ids: list = DaLeDou.findall(r'amp;id=(\d+)')
            if not ids:
                self.msg.append('没有可领取的了')
                break
            for id in ids:
                # 领取
                Events.get(f'cmd=midautumngiftbag&sub=1&id={id}')
                if '已领取完该系列任务所有奖励' in html:
                    continue
                self.msg += DaLeDou.findall(r'【中秋礼盒】<br />(.*?)<br />')

    def 企鹅吉利兑(self):
        '''
        id  消耗
        1   180 泯灭·苍玉IV
        2   180 破坏·银光IV
        3   180 洞悉·异炎IV
        4   180 破坏·锦月IV
        5   20  V级万能碎片
        6   2   熔炼乌金
        7   2   玄铁令
        8   1   挑战书
        '''
        # 企鹅吉利兑
        Events.get('cmd=geelyexchange')

        # 修炼任务 》每日任务
        ids: list = DaLeDou.findall(r'id=(\d+)">领取</a>')
        for id in ids:
            # 领取
            Events.get(f'cmd=geelyexchange&op=GetTaskReward&id={id}')
            self.msg += DaLeDou.findall(r'】<br /><br />(.*?)<br /><br />')

        # 限时兑换
        date: str = DaLeDou.findall(r'至\d+月(\d+)日')[0]
        if int(self.date) == int(date) - 1:
            data: dict = DaLeDou.readyaml('活动')
            duihuan_name: list = data['企鹅吉利兑']
            for name in duihuan_name:
                id = DaLeDou.findall(
                    f'{name}.*?op=ExchangeProps&amp;id=(\d+)')[0]
                # used/total 0/1
                used, total = DaLeDou.findall(f'{name}.*?(\d+)/(\d+)')[0]
                if used == total:
                    continue
                for _ in range(int(total)):
                    # 兑换
                    Events.get(f'cmd=geelyexchange&op=ExchangeProps&id={id}')
                    if '你的精魄不足，快去完成任务吧~' in html:
                        break
                    elif '该物品已达兑换上限~' in html:
                        break
                    self.msg += DaLeDou.findall(r'】<br /><br />(.*?)<br />')
                if DaLeDou.findall(r'当前精魄：(\d+)')[0] == '0':
                    break

        # 当前精魄
        self.msg += DaLeDou.findall(r'喔~<br />(.*?)<br /><br />')

    def 乐斗游记(self):
        # 乐斗游记
        Events.get('cmd=newAct&subtype=176')

        # 今日游记任务
        task_id: list = DaLeDou.findall(r'task_id=(\d+)')
        for id in task_id:
            # 领取
            Events.get(f'cmd=newAct&subtype=176&op=1&task_id={id}')
            self.msg += DaLeDou.findall(r'积分。<br /><br />(.*?)<br />')

        if self.week == '4':
            # 一键领取
            Events.get('cmd=newAct&subtype=176&op=5')
            self.msg += DaLeDou.findall(r'积分。<br /><br />(.*?)<br />')
            self.msg += DaLeDou.findall(r'十次</a><br />(.*?)<br />乐斗')
            # 兑换
            num_list: list = DaLeDou.findall(r'溢出积分：(\d+)')
            if (num := int(num_list[0])) != 0:
                num10 = int(num / 10)
                num1 = num - (num10 * 10)
                for _ in range(num10):
                    # 兑换十次
                    Events.get('cmd=newAct&subtype=176&op=2&num=10')
                    self.msg += DaLeDou.findall(r'积分。<br /><br />(.*?)<br />')
                for _ in range(num1):
                    # 兑换一次
                    Events.get('cmd=newAct&subtype=176&op=2&num=1')
                    self.msg += DaLeDou.findall(r'积分。<br /><br />(.*?)<br />')

    def 万圣节(self):
        # 点亮南瓜灯
        Events.get('cmd=hallowmas&gb_id=1')
        while True:
            cushaw_id: list = DaLeDou.findall(r'cushaw_id=(\d+)')
            id: str = random.choice(cushaw_id)
            # 南瓜
            Events.get(f'cmd=hallowmas&gb_id=4&cushaw_id={id}')
            self.msg += DaLeDou.findall(r'】<br />(.*?)<br />')
            # 恭喜您获得10体力和南瓜灯一个！
            # 恭喜您获得20体力和南瓜灯一个！南瓜灯已刷新
            # 请领取今日的活跃度礼包来获得蜡烛吧！
            if '请领取' in html:
                break

        # 兑换奖励
        Events.get('cmd=hallowmas&gb_id=0')
        date: str = DaLeDou.findall(r'~\d+月(\d+)日')[0]
        if int(self.date) == int(date) - 1:
            num: str = DaLeDou.findall(r'南瓜灯：(\d+)个')[0]
            B = int(num) / 40
            A = (int(num) - int(B) * 40) / 20
            for _ in range(int(B)):
                # 礼包B 消耗40个南瓜灯
                Events.get('cmd=hallowmas&gb_id=6')
                self.msg += DaLeDou.findall(r'】<br />(.*?)<br />')
            for _ in range(int(A)):
                # 礼包A 消耗20个南瓜灯
                Events.get('cmd=hallowmas&gb_id=5')
                self.msg += DaLeDou.findall(r'】<br />(.*?)<br />')

    def 双节签到(self):
        # 双节签到
        Events.get('cmd=newAct&subtype=144')
        date: str = DaLeDou.findall(r'至\d+月(\d+)日')[0]
        if 'op=1' in html:
            # 领取
            Events.get('cmd=newAct&subtype=144&op=1')
            self.msg += DaLeDou.findall(r'【双节签到】<br />(.*?)<br />')
        if int(self.date) == int(date) - 1:
            # 奖励金
            Events.get('cmd=newAct&subtype=144&op=3')
            self.msg += DaLeDou.findall(r'【双节签到】<br />(.*?)<br />')

    def 圣诞有礼(self):
        # 圣诞有礼
        Events.get('cmd=newAct&subtype=145')
        task_id: list = DaLeDou.findall(r'task_id=(\d+)')
        for id in task_id:
            # 任务描述：领取奖励
            Events.get(f'cmd=newAct&subtype=145&op=1&task_id={id}')
            self.msg += DaLeDou.findall(r'】<br />(.*?)<br />')
        # 连线奖励
        index_list: list = DaLeDou.findall(r'index=(\d+)')
        for index in index_list:
            Events.get(f'cmd=newAct&subtype=145&op=2&index={index}')
            self.msg += DaLeDou.findall(r'】<br />(.*?)<br />')

    def 乐斗回忆录(self):
        for id in [1, 3, 5, 7, 9]:
            # 回忆礼包
            Events.get(f'cmd=newAct&subtype=171&op=3&id={id}')
            self.msg += DaLeDou.findall(r'6点<br />(.*?)<br />')

    def 新春礼包(self):
        # 新春礼包
        Events.get('cmd=xinChunGift&subtype=1')
        date_list: list = DaLeDou.findall(r'~\d+月(\d+)日')
        giftid: list = DaLeDou.findall(r'giftid=(\d+)')
        for date, id in zip(date_list, giftid):
            if int(self.date) == int(date) - 1:
                Events.get(f'cmd=xinChunGift&subtype=2&giftid={id}')
                self.msg += DaLeDou.findall(r'【迎新大礼包】<br />(.*?)<br />')

    def 乐斗大笨钟(self):
        # 领取
        Events.get('cmd=newAct&subtype=18')
        self.msg += DaLeDou.findall(r'<br /><br /><br />(.*?)<br />')

    def 新春拜年(self):
        '''
        第一轮赠礼
        第二轮收礼
        '''
        # 新春拜年
        Events.get('cmd=newAct&subtype=147')
        if 'op=1' in html:
            for index in random.sample(range(5), 3):
                # 选中
                Events.get(f'cmd=newAct&subtype=147&op=1&index={index}')
            # 赠礼
            Events.get('cmd=newAct&subtype=147&op=2')
            self.msg += ['已赠礼']
        elif 'op=3' in html:
            # 收取礼物
            Events.get('cmd=newAct&subtype=147&op=3')
            self.msg += DaLeDou.findall(r'祝您：.*?<br /><br />(.*?)<br />')

    def 新春登录礼(self):
        # 新春登录礼
        Events.get('cmd=newAct&subtype=99&op=0')
        day_list: list = DaLeDou.findall(r'day=(\d+)')
        for day in day_list:
            # 领取
            Events.get(f'cmd=newAct&subtype=99&op=1&day={day}')
            self.msg += DaLeDou.findall(r'】<br />(.*?)<br />')

    def 喜从天降(self):
        # 点燃烟花
        Events.get('cmd=newAct&subtype=137&op=1')
        self.msg += DaLeDou.findall(r'【喜从天降】<br />(.*?)<br />')

    def 春联大赛(self):
        # 开始答题
        Events.get('cmd=newAct&subtype=146&op=1')
        if '您的活跃度不足' in html:
            self.msg += ['您的活跃度不足50']
            return
        elif '今日答题已结束' in html:
            self.msg += ['今日答题已结束']
            return

        chunlian = {
            '虎年腾大步': '兔岁展宏图',
            '虎辟长安道': '兔开大吉春',
            '虎跃前程去': '兔携好运来',
            '虎去雄风在': '兔来喜气浓',
            '虎带祥云去': '兔铺锦绣来',
            '虎蹄留胜迹': '兔角搏青云',
            '虎留英雄气': '兔会世纪风',
            '金虎辞旧岁': '银兔贺新春',
            '虎威惊盛世': '兔翰绘新春',
            '虎驰金世界': '兔唤玉乾坤',
            '虎声传捷报': '兔影抖春晖',
            '虎嘶飞雪里': '兔舞画图中',
            '兔归皓月亮': '花绽春光妍',
            '兔俊千山秀': '春暖万水清',
            '兔毫抒壮志': '燕梭织春光',
            '玉兔迎春至': '黄莺报喜来',
            '玉兔迎春到': '红梅祝福来',
            '玉兔蟾宫笑': '红梅五岭香',
            '卯时春入户': '兔岁喜盈门',
            '卯门生紫气': '兔岁报新春',
            '卯来四季美': '兔献百家福',
            '红梅迎春笑': '玉兔出月欢',
            '红梅赠虎岁': '彩烛耀兔年',
            '红梅迎雪放': '玉兔踏春来',
            '丁年歌盛世': '卯兔耀中华',
            '寅年春锦绣': '卯序业辉煌',
            '燕舞春光丽': '兔奔曙光新',
            '笙歌辞旧岁': '兔酒庆新春',
            '瑞雪兆丰年': '迎得玉兔归',
            '雪消狮子瘦': '月满兔儿肥',
        }
        for _ in range(3):
            shanglian: list = DaLeDou.findall(r'上联：(.*?) 下联：')
            for s in shanglian:
                x = chunlian.get(s)
                if x is None:
                    # 上联在字库中不存在，将随机选择
                    xialian: int = [random.choice(range(3))]
                else:
                    xialian: list = DaLeDou.findall(f'{x}<a.*?index=(\d+)')
                if xialian:
                    # 选择
                    # index 0 1 2
                    Events.get(
                        f'cmd=newAct&subtype=146&op=3&index={xialian[0]}')
                    self.msg += DaLeDou.findall(r'剩余\d+题<br />(.*?)<br />')
                    # 确定选择
                    Events.get('cmd=newAct&subtype=146&op=2')
                    self.msg += DaLeDou.findall(r'】<br />(.*?)<br />')

        # 领取
        for id in range(1, 4):
            Events.get(f'cmd=newAct&subtype=146&op=4&id={id}')
            self.msg += DaLeDou.findall(r'】<br />(.*?)<br />')

    def 年兽大作战(self):
        # 年兽大作战
        Events.get('cmd=newAct&subtype=170&op=0')
        if '等级不够' in html:
            self.msg += ['等级不够，还未开启年兽大作战哦！']
            return
        n: list = DaLeDou.findall(r'剩余免费随机次数：(\d+)')
        for _ in n:
            # 随机武技库 免费一次
            Events.get('cmd=newAct&subtype=170&op=6')
            self.msg += DaLeDou.findall(r'帮助</a><br />(.*?)<br />')

        # 自选武技库
        # 从大、中、小、投、技各随机选择一个
        if '暂未选择' in html:
            for t in range(5):
                Events.get(f'cmd=newAct&subtype=170&op=4&type={t}')
                if '取消选择' in html:
                    continue
                ids: list = DaLeDou.findall(r'id=(\d+)">选择')
                id: str = random.choice(ids)
                # 选择
                Events.get(f'cmd=newAct&subtype=170&op=7&id={id}')
                if '自选武技列表已满' in html:
                    break

        # 挑战
        for _ in range(3):
            Events.get('cmd=newAct&subtype=170&op=8')
            self.msg += DaLeDou.findall(r'帮助</a><br />(.*?)。')

    def 冰雪企缘(self):
        # 冰雪企缘
        Events.get('cmd=newAct&subtype=158&op=0')
        type: list = DaLeDou.findall(r'gift_type=(\d+)')
        for t in type:
            # 领取
            Events.get(f'cmd=newAct&subtype=158&op=2&gift_type={t}')
            self.msg += DaLeDou.findall(r'】<br />(.*?)<br />')

    def 煮元宵(self):
        # 煮元宵
        Events.get('cmd=yuanxiao2014')
        # number: list = DaLeDou.findall(r'今日剩余烹饪次数：(\d+)')
        for _ in range(4):
            # 开始烹饪
            Events.get('cmd=yuanxiao2014&op=1')
            if '领取烹饪次数' in html:
                self.msg.append('没有烹饪次数了')
                break
            for _ in range(20):
                maturity: list = DaLeDou.findall(r'当前元宵成熟度：(\d+)')
                if int(maturity[0]) >= 96:
                    # 赶紧出锅
                    Events.get('cmd=yuanxiao2014&op=3')
                    self.msg += DaLeDou.findall(r'活动规则</a><br /><br />(.*?)。')
                    break
                # 继续加柴
                Events.get('cmd=yuanxiao2014&op=2')

    def 元宵节(self):
        # 领取
        Events.get('cmd=newAct&subtype=101&op=1')
        self.msg += DaLeDou.findall(r'】</p>(.*?)<br />')
        # 领取月桂兔
        Events.get('cmd=newAct&subtype=101&op=2&index=0')
        self.msg += DaLeDou.findall(r'】</p>(.*?)<br />')

    def main_one(self) -> list:
        # 首页
        Events.get('cmd=index')
        events_missions: str = html

        func_name = {
            '幸运金蛋',
            '乐斗大笨钟',
            '新春拜年',
        }

        for func in func_name:
            if func in events_missions:
                self.msg += DaLeDou.conversion(func)
                getattr(self, func)()

        return self.msg

    def main_two(self) -> list:
        # 首页
        Events.get('cmd=index')
        events_missions: str = html

        # 每天要执行的任务
        daily_func_name = {
            '神魔转盘',
            '乐斗驿站',
            '开心娃娃机',
            '好礼步步升',
            '浩劫宝箱',
            '幸运金蛋',
            '幸运转盘',
            '惊喜刮刮卡',
            '甜蜜夫妻',
            '乐斗菜单',
            '客栈同福',
            '周周礼包',
            '登录有礼',
            '活跃礼包',
            '猜单双',
            '上香活动',
            '徽章战令',
            '生肖福卡',
            '长安盛会',
            '深渊秘宝',
            '中秋礼盒',
            '企鹅吉利兑',
            '乐斗游记',
            '万圣节',
            '双节签到',
            '乐斗大笨钟',
            '新春拜年',
            '新春登录礼',
            '喜从天降',
            '春联大赛',
            '年兽大作战',
            '冰雪企缘',
            '煮元宵',
        }

        # 周四要执行的任务
        thursday_func_name = {
            '登录商店',
            '盛世巡礼',
            '十二周年生日祝福',
            '圣诞有礼',
            '乐斗回忆录',
            '新春礼包',
            '元宵节',
        }

        if self.week == '4':
            func_name: set = daily_func_name | thursday_func_name
        else:
            func_name: set = daily_func_name

        for func in func_name:
            if func in events_missions:
                self.msg += DaLeDou.conversion(func)
                getattr(self, func)()

        return self.msg