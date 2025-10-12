from src.daledou.core.cli import run_serve


if __name__ == "__main__":
    try:
        run_serve()
    except KeyboardInterrupt:
        print("\n用户取消操作")
