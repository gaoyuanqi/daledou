## ⚠️ 免责声明

**本项目仅供学习交流，按“原样”提供，使用者需自行承担所有风险**

**本项目按 MIT 许可证授权，详情请参阅 [LICENSE](LICENSE) 文件**


## 快速开始

### 环境要求

**Python版本**：Python 3.12+

### 下载项目

方式一：使用 `Git` 克隆

```sh
git clone https://github.com/gaoyuanqi/daledou.git
cd daledou
```

方式二：下载压缩包

访问 [Tags页面](https://github.com/gaoyuanqi/daledou/tags) 下载最新版压缩包

### 安装依赖

使用 [uv](https://hellowac.github.io/uv-zh-cn/) 快速安装（推荐）

```sh
uv sync
```

使用 `pip` 一键安装

```sh
pip install -r requirements.txt
```

手动安装依赖

```sh
pip install loguru
pip install pytz
pip install pyyaml
pip install questionary
pip install requests
pip install schedule
```

### 启动程序命令

```sh
uv run main.py
```

或者

```sh
python main.py
```


## 大乐斗任务文档

- [第一轮任务](docs/one.md)
- [第二轮任务](docs/two.md)
- [其它任务](docs/other.md)


## 配置文件说明

```
config/
├── accounts/              # 账号配置目录
│   ├── 123456.yaml       # QQ号命名的账号配置文件
│   ├── 234567.yaml
│   └── ...
├── merged/               # 合并配置目录（自动生成）
│   ├── 123456.yaml      # 账号配置与全局配置合并后的最终配置
│   ├── 234567.yaml
│   └── ...
├── global.yaml           # 全局配置文件
└── default.yaml          # 默认配置模板
```
