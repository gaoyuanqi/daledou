"""
任务模块自动加载器

导入此包时会自动加载所有任务模块，触发任务注册
"""

import importlib
import pkgutil
import traceback
from pathlib import Path

pkg_path = Path(__file__).parent

for module_info in pkgutil.iter_modules([str(pkg_path)]):
    module_name = module_info.name

    # 跳过非任务模块
    if module_name in ("register", "common"):
        continue

    # 动态导入以触发 Registry 注册
    try:
        importlib.import_module(f".{module_name}", package=__name__)
    except Exception:
        traceback.print_exc()
