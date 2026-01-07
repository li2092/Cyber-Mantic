"""
赛博玄数 - GUI启动脚本
"""
import sys

try:
    from ui.main_window import run_gui
    run_gui()
except ImportError as e:
    print("错误：无法启动GUI界面")
    print(f"原因：{e}")
    print("\n请确保已安装PyQt6：")
    print("  pip install PyQt6")
    sys.exit(1)
