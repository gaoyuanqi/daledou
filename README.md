## Q宠大乐斗自动化助手

一个平民鹅日常周常任务自动化脚本，支持定时调度、多账号并发

## Python版本

推荐 **Python 3.13** 或更高版本

## 快速开始

**1、获取项目**

方式一：使用 `Git` 克隆

```bash
git clone https://github.com/gaoyuanqi/daledou.git
cd daledou
```

方式二：下载压缩包

访问 [Tags页面](https://github.com/gaoyuanqi/daledou/tags) 下载最新版压缩包

**2、安装依赖**

使用 [uv](https://hellowac.github.io/uv-zh-cn/) 安装:

```bash
uv sync
```

**3、配置 Cookie**

创建 `config/dld_cookie.yaml` 配置文件，添加你的大乐斗Cookie:

```yaml
# 大乐斗Cookie，每行一个账号
DALEDOU_COOKIES:
  # - openId=..; accessToken=..; newuin=..
  # - openId=..; accessToken=..; newuin=..
```

**4、验证安装**

```bash
# 测试单个任务
uv run main.py noon.邪神秘宝

# 查看帮助
uv run main.py -h
```

**5、启动定时任务（可选）**

```bash
uv run main.py
```

> 你需要确保系统时间是上海时间（Asia/Shanghai，UTC+8）

## 命名约定

**任务注册名 = 首页链接文本**

任务必须通过 `@register()` 装饰器注册，**注册名必须与大乐斗老版首页的链接文本完全一致**

> 严格来说是 `>` 和 `<` 括起来的文本，比如 `>邪神秘宝<`

脚本执行时会：

1. 抓取大乐斗老版首页HTML
2. 检查首页是否存在该注册名的链接文本
3. **若存在** → 执行对应任务函数
4. **若不存在** → 跳过该任务（静默，不报错）

**两种注册方式**

| 方式                 | 适用场景                                     | 示例                                   |
| -------------------- | -------------------------------------------- | -------------------------------------- |
| **隐式注册**（推荐） | 链接文本是合法的 Python 标识符               | `@register()` + `async def 邪神秘宝()` |
| **显式注册**         | 链接文本含特殊字符（如数字开头、空格、符号） | `@register("5.1礼包")`                 |

```python
# ✅ 隐式注册：函数名 = 链接文本 = "邪神秘宝"
@register()
async def 邪神秘宝(d: DaLeDou):
    await c_邪神秘宝(d)

# ✅ 显式注册：链接文本 "5.1礼包" 不能作为函数名（Python 语法限制）
@register("5.1礼包")
async def 五一礼包(d: DaLeDou):
    ...

# ❌ 错误：注册名与首页文本不一致，任务永远不会执行
@register("邪神宝藏")  # 实际首页是"邪神秘宝"
async def 邪神秘宝(d: DaLeDou):
    ...

# 没有被 register 装饰的函数不会执行，除非被其他函数调用
async def 邪神秘宝(d: DaLeDou):
    ...
```

**配置键命名**

YAML 配置中的 **任务键名** 必须与 **注册名** 保持一致

## 配置说明文档

**配置文件位置**

```
config/
├── accounts/             # 账号配置目录
│   ├── 123456.yaml      # QQ号命名的账号配置文件
│   ├── 234567.yaml
│   └── ...
├── default.yaml          # 全局默认配置文件
└── dld_cookie.yaml       # 大乐斗Cookie配置文件（需手动创建）
```

**配置优先级规则**

```
账号配置 (config/accounts/<qq>.yaml)
    ↓ 未找到
默认配置 (config/default.yaml)
    ↓ 未找到
抛出 ConfigKeyError 异常
```

**在代码中使用配置**

通过 `d.config()` 方法读取，键路径使用 `.` 分隔：

```python
# 读取单层键
value = d.config("矿洞")

# 读取嵌套键（支持任意层级）
floor = d.config("矿洞.floor")  # → 获取矿洞配置下的 floor 值
enabled = d.config("门派.门派高香.enabled")  # → 获取多层嵌套值
```

键路径禁止包含模块名称前缀（`noon` / `evening`）

```python
# ✅ 正确：查询当前模块（noon）下的矿洞配置
d.config("矿洞")  # 底层实际查询 noon.矿洞
d.config("矿洞.floor")  # 底层实际查询 noon.矿洞.floor

# ❌ 错误：键路径包含模块名称，将抛出 ConfigKeyError
d.config("noon.矿洞")  # 异常：配置键 'noon.noon.矿洞' 未找到
d.config("evening.矿洞")  # 异常：配置键 'noon.evening.矿洞' 未找到
```

## 许可证

本项目采用 [MIT License](LICENSE) 开源许可证

## 常见问题

**Q:大乐斗文字版链接**

**A:** https://dld.qzapp.z.qq.com/qpet/cgi-bin/phonepk?cmd=index&style=1

**Q:如何获取大乐斗Cookie**

**A:** 以安卓为例

1、首先应用商店安装 **Via浏览器** 并将其设为默认浏览器

2、然后使用Via访问大乐斗文字版链接，选择一键登录，不要选择账号密码登录

3、成功登录后等待5秒，Via左上角会出现一个类似 ✓ 的图标，点击它

4、可以看到一个 **查看cookies**，复制里面的cookie即可

**Q:大乐斗Cookie有效期**

**A:** 很长，一年是有的

**Q:脚本是否会扣除鹅币/斗豆/斗币**

**A:** 不会。对于娃娃机、神魔转盘、深渊秘宝等可能会扣除斗豆的任务会进行前置判断，但不排除因页面更新而失效

如果你发现脚本有扣除行为或者其他漏洞，[欢迎提交 Issue](../../issues)
