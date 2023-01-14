'''
竞技场
'''
from src.daledou.daledou import DaLeDou
from src.daledou._set import _readyaml,_getenvqq


class JingJiChang(DaLeDou):

    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def get(params: str):
        global html
        html = DaLeDou.get(params)

    def 挑战(self):
        '''
        至多挑战10次（免费挑战和开始挑战）
        '''
        for _ in range(10):
            # 免费挑战 》开始挑战
            JingJiChang.get('cmd=arena&op=challenge')
            self.msg += DaLeDou.findall(r'更新提示</a><br />(.*?)。')
            if '免费挑战次数已用完' in html:
                # 领取奖励
                JingJiChang.get('cmd=arena&op=drawdaily')
                self.msg += DaLeDou.findall(r'更新提示</a><br />(.*?)<br />')
                break

    def 兑换(self):
        data: dict = _readyaml('竞技场', _getenvqq())
        id: int = data['id']
        times: int = data['times']
        if id:
            # 兑换 or 兑换10个
            JingJiChang.get(f'cmd=arena&op=exchange&id={id}&times={times}')
            self.msg += DaLeDou.findall(r'竞技场</a><br />(.*?)<br />')

    def main(self) -> list:
        if int(self.date) <= 25:
            self.msg += DaLeDou.conversion('竞技场')
            self.挑战()
            self.兑换()
            return self.msg

        return []
