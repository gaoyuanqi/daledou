"""
支持以下命令启动脚本:
    >>> # 定时运行第一轮和第二轮
    >>> python main.py --timing

    >>> # 立即运行第一轮所有任务
    >>> python main.py --one
    >>> # 调用 one.py 中的某个函数
    >>> python main.py --one 邪神秘宝

    >>> # 立即运行第二轮所有任务
    >>> python main.py --two
    >>> # 调用 two.py 中的某个函数
    >>> python main.py --two 邪神秘宝

    >>> # 运行 other.py 中的任务
    >>> python main.py --other

如果使用 uv 包管理器，则将上面 python 替换为 uv run
"""

from src.daledou.core.cli import run_serve


if __name__ == "__main__":
    try:
        run_serve()
    except KeyboardInterrupt:
        print("\n用户取消了操作")
