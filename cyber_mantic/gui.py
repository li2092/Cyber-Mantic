"""
赛博玄数 - GUI启动脚本

V2版本：使用重构后的前端组件
"""
import sys

# 默认使用V2版本
USE_V2 = True

try:
    if USE_V2:
        from ui.main_window_v2 import run_gui_v2
        run_gui_v2()
    else:
        from ui.main_window import run_gui
        run_gui()
except ImportError as e:
    print("错误：无法启动GUI界面")
    print(f"原因：{e}")
    print("\n请确保已安装PyQt6：")
    print("  pip install PyQt6")
    sys.exit(1)
