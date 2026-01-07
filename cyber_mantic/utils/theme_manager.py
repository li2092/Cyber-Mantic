"""
主题管理器 - 无需修改main_window.py的主题配置方案

使用方法：
1. 在GUI代码中导入：from utils.theme_manager import ThemeManager
2. 初始化：theme_mgr = ThemeManager()
3. 应用主题：app.setStyleSheet(theme_mgr.get_current_stylesheet())
4. 切换主题：theme_mgr.set_theme("dark")
"""
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from ui.themes_simplified import ThemeSystem


class ThemeManager:
    """主题管理器 - 处理主题配置的加载、保存和应用"""

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化主题管理器

        Args:
            config_path: 配置文件路径，默认为 config/theme_settings.json
        """
        if config_path is None:
            # 默认配置路径
            project_root = Path(__file__).parent.parent
            config_path = project_root / "config" / "theme_settings.json"

        self.config_path = Path(config_path)
        self.settings = self._load_settings()

    def _load_settings(self) -> Dict[str, Any]:
        """加载主题配置"""
        if not self.config_path.exists():
            # 返回默认配置
            return {
                "current_theme": "light",
                "available_themes": ["light", "dark", "zen"],
                "auto_switch": False
            }

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载主题配置失败: {e}，使用默认配置")
            return {
                "current_theme": "light",
                "available_themes": ["light", "dark", "zen"],
                "auto_switch": False
            }

    def _save_settings(self) -> bool:
        """保存主题配置"""
        try:
            # 确保目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存主题配置失败: {e}")
            return False

    def get_current_theme(self) -> str:
        """
        获取当前主题名称

        如果启用了自动切换，根据时间返回日间/夜间主题

        Returns:
            主题名称 (light/dark/zen)
        """
        if self.settings.get("auto_switch", False):
            # 自动切换模式
            current_hour = datetime.now().hour
            switch_times = self.settings.get("auto_switch_times", {})

            day_start = switch_times.get("day_start_hour", 6)
            night_start = switch_times.get("night_start_hour", 18)

            if day_start <= current_hour < night_start:
                return switch_times.get("day_theme", "light")
            else:
                return switch_times.get("night_theme", "dark")
        else:
            # 手动模式，返回用户选择的主题
            return self.settings.get("current_theme", "light")

    def set_theme(self, theme_name: str) -> bool:
        """
        设置当前主题

        Args:
            theme_name: 主题名称 (light/dark/zen)

        Returns:
            是否设置成功
        """
        available = self.settings.get("available_themes", ["light", "dark", "zen"])

        if theme_name not in available:
            print(f"主题 '{theme_name}' 不存在，可用主题：{available}")
            return False

        self.settings["current_theme"] = theme_name
        return self._save_settings()

    def get_current_stylesheet(self) -> str:
        """
        获取当前主题的QSS样式表

        Returns:
            QSS样式字符串
        """
        theme_name = self.get_current_theme()
        return ThemeSystem.generate_qss_stylesheet(theme_name)

    def get_available_themes(self) -> list:
        """
        获取所有可用主题

        Returns:
            主题名称列表
        """
        return self.settings.get("available_themes", ["light", "dark", "zen"])

    def get_theme_description(self, theme_name: str) -> str:
        """
        获取主题描述

        Args:
            theme_name: 主题名称

        Returns:
            主题描述
        """
        descriptions = self.settings.get("theme_descriptions", {})
        return descriptions.get(theme_name, "未知主题")

    def enable_auto_switch(self, enable: bool = True) -> bool:
        """
        启用/禁用自动切换主题

        Args:
            enable: 是否启用

        Returns:
            是否设置成功
        """
        self.settings["auto_switch"] = enable
        return self._save_settings()

    def set_auto_switch_times(
        self,
        day_start_hour: int,
        night_start_hour: int,
        day_theme: str = "light",
        night_theme: str = "dark"
    ) -> bool:
        """
        设置自动切换时间

        Args:
            day_start_hour: 日间开始时间（0-23）
            night_start_hour: 夜间开始时间（0-23）
            day_theme: 日间主题
            night_theme: 夜间主题

        Returns:
            是否设置成功
        """
        if not (0 <= day_start_hour <= 23 and 0 <= night_start_hour <= 23):
            print("时间必须在0-23之间")
            return False

        self.settings["auto_switch_times"] = {
            "day_theme": day_theme,
            "night_theme": night_theme,
            "day_start_hour": day_start_hour,
            "night_start_hour": night_start_hour
        }
        return self._save_settings()


# ========== GUI集成示例代码 ==========

def example_integration_code():
    """
    示例：如何在GUI中集成主题管理器

    在main_window.py的MainWindow类中添加以下代码：
    """

    code_example = '''
# 在MainWindow.__init__()中添加：
from utils.theme_manager import ThemeManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # 初始化主题管理器
        self.theme_manager = ThemeManager()

        # 应用当前主题
        self.apply_current_theme()

        # ... 其他初始化代码 ...

        # 创建主题选择菜单（可选）
        self._create_theme_menu()

    def apply_current_theme(self):
        """应用当前主题"""
        stylesheet = self.theme_manager.get_current_stylesheet()
        QApplication.instance().setStyleSheet(stylesheet)

    def _create_theme_menu(self):
        """创建主题选择菜单"""
        # 在菜单栏中添加"主题"菜单
        theme_menu = self.menuBar().addMenu("主题")

        # 为每个主题创建菜单项
        for theme_name in self.theme_manager.get_available_themes():
            description = self.theme_manager.get_theme_description(theme_name)
            action = QAction(description, self)
            action.triggered.connect(lambda checked, t=theme_name: self.switch_theme(t))
            theme_menu.addAction(action)

        # 添加分隔符
        theme_menu.addSeparator()

        # 添加自动切换选项
        auto_action = QAction("自动切换（日/夜）", self)
        auto_action.setCheckable(True)
        auto_action.setChecked(self.theme_manager.settings.get("auto_switch", False))
        auto_action.triggered.connect(self.toggle_auto_switch)
        theme_menu.addAction(auto_action)

    def switch_theme(self, theme_name: str):
        """切换主题"""
        if self.theme_manager.set_theme(theme_name):
            self.apply_current_theme()
            QMessageBox.information(self, "主题切换", f"已切换到 {theme_name} 主题")

    def toggle_auto_switch(self, checked: bool):
        """切换自动主题"""
        self.theme_manager.enable_auto_switch(checked)
        if checked:
            QMessageBox.information(
                self,
                "自动切换",
                "已启用主题自动切换\\n白天（6:00-18:00）使用浅色主题\\n夜间（18:00-6:00）使用深色主题"
            )
        self.apply_current_theme()
    '''

    return code_example


# ========== 命令行工具（用于测试和配置） ==========

def cli_tool():
    """命令行工具：配置主题"""
    import sys

    if len(sys.argv) < 2:
        print("用法：")
        print("  python -m utils.theme_manager current        # 查看当前主题")
        print("  python -m utils.theme_manager list           # 列出所有主题")
        print("  python -m utils.theme_manager set <theme>    # 设置主题")
        print("  python -m utils.theme_manager auto on        # 启用自动切换")
        print("  python -m utils.theme_manager auto off       # 禁用自动切换")
        return

    manager = ThemeManager()
    command = sys.argv[1]

    if command == "current":
        theme = manager.get_current_theme()
        desc = manager.get_theme_description(theme)
        print(f"当前主题: {theme} - {desc}")

    elif command == "list":
        print("可用主题：")
        for theme in manager.get_available_themes():
            desc = manager.get_theme_description(theme)
            current = " (当前)" if theme == manager.settings.get("current_theme") else ""
            print(f"  - {theme}: {desc}{current}")

    elif command == "set" and len(sys.argv) >= 3:
        theme = sys.argv[2]
        if manager.set_theme(theme):
            print(f"主题已设置为: {theme}")
        else:
            print(f"设置失败")

    elif command == "auto" and len(sys.argv) >= 3:
        enable = sys.argv[2] == "on"
        if manager.enable_auto_switch(enable):
            print(f"自动切换已{'启用' if enable else '禁用'}")
        else:
            print("设置失败")

    else:
        print("未知命令")


if __name__ == "__main__":
    cli_tool()
