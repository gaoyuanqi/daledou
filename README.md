## 说明

乐斗等级战力不高的玩家使用脚本可能会有一些问题，建议手动提高等级战力后再使用

**为了保险起见，不要充值斗豆及鹅币，以免使用脚本时被消耗**


## Python版本

```
Python 3.11
```


## 快速开始

**1、下载脚本**
```sh
git clone https://github.com/gaoyuanqi/DaLeDou.git
```

**2、`./config/settings.yaml` 配置**

添加大乐斗Cookie（必须）：
```yaml
DALEDOU_ACCOUNT:
  - RK=xx; ptcz=xx; openId=xx; accessToken=xx; newuin=111111
  - RK=xx; ptcz=xx; openId=xx; accessToken=xx; newuin=222222
```

添加pushplus微信通知（可选）：
```yaml
PUSHPLUS_TOKEN: ""
```

**3、安装依赖**
```sh
pip3 install -r requirements.txt
```

**4、如果你第一次使用，需运行以下命令**

此命令不会执行脚本，只是做一些检查工作
```sh
python main.py
```

输出如下：
```sh
2023-12-23 21:45:32.197 | SUCCESS  | daledou.config:init_config:138 - 123456：Cookie在有效期内
2023-12-23 21:45:32.213 | SUCCESS  | daledou.config:create_yaml:83 - 创建文件 ./config/123456.yaml
```

你需要修改上面创建的 `./config/123456.yaml` 配置文件（大乐斗Cookie有效才会创建）

修改完成后再次运行 `python main.py` 命令将会检查yaml文件格式，如果没有出现错误，最终输出信息：
```sh
2023-12-23 21:59:12.179 | SUCCESS  | daledou.config:init_config:138 - 123456：Cookie在有效期内
2023-12-23 21:59:12.179 | SUCCESS  | daledou.config:create_yaml:80 - 检测到文件 ./config/123456.yaml
```

**5、手动运行指定轮次**

`13:10` 之后运行第一轮：
```sh
python main.py one
```

`20:01` 之后运行第二轮：
```sh
python main.py two
```

**6、其它说明**

脚本启动后会进入定时，默认 `13:10` 运行第一轮、`20:01` 运行第二轮

第一轮和第二轮时间间隔尽量长一些；时间不够优先运行第一轮，第一轮包括了绝大部分任务

要查看脚本会做哪些任务见：[文档](https://www.gaoyuanqi.cn/python-daledou/#more)


## 大乐斗Cookie有效期

目前测试的通过 **一键登录** 获得的Cookie有效期比较长，具体多长还不清楚，但脚本会2小时检查一次Cookie有效期

如果大乐斗Cookie失效，重新登录大乐斗即可，不需更换Cookie。也就是说，只要每隔几天打开一次大乐斗，那么Cookie有效期应该是永久的


## daledou.yaml 配置文件

- `十二宫`：选择扫荡关卡，默认 `白羊宫`
- `幻境`：选择乐斗关卡，默认 `乐斗村`
- `深渊之潮`：选择深渊秘境关卡，默认 `崎岖斗界`
- `竞技场`：选择兑换10次商店材料，默认 `不兑换`
- `门派邀请赛`：选择兑换10次商店材料，默认 `不兑换`
- `武林盟主`：选择报名赛场，默认 `青铜赛场`
- `历练`：选择乐斗BOSS优先级
- `帮派商会`：选择交易、兑换商品
- `我的帮派`：选择守护神供奉物品
- `背包`：选择要消耗的物品
- `企鹅吉利兑`：兑换材料优先级
- `神匠坊`：符石分解，默认分解 `I类`
- `江湖长梦`：选择副本，默认且仅支持 `柒承的忙碌日常`
- `问鼎天下`：选择淘汰赛、排名赛助威帮派，默认 `神阁☆圣域`
