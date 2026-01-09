"""
赛博玄数 设计系统 V2

统一的设计语言：颜色、字号、间距、圆角等
"""

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class Spacing:
    """间距系统 (8px基准)"""
    xs: int = 4
    sm: int = 8
    md: int = 16
    lg: int = 24
    xl: int = 32


@dataclass(frozen=True)
class FontSize:
    """字号系统"""
    xs: int = 11
    sm: int = 13
    base: int = 14
    md: int = 16
    lg: int = 18
    xl: int = 20
    xxl: int = 24


@dataclass(frozen=True)
class BorderRadius:
    """圆角系统"""
    sm: int = 6
    md: int = 10
    lg: int = 14
    xl: int = 18


class ThemeColors:
    """主题颜色"""

    # 浅色主题
    LIGHT = {
        # 背景色
        "bg_primary": "#FFFFFF",
        "bg_secondary": "#F8FAFC",
        "bg_tertiary": "#F1F5F9",
        "surface": "#FFFFFF",
        "surface_hover": "#F8FAFC",

        # 边框
        "border": "#E2E8F0",
        "border_light": "#F1F5F9",

        # 文字
        "text_primary": "#1E293B",
        "text_secondary": "#64748B",
        "text_muted": "#94A3B8",

        # 主色调
        "primary": "#6366F1",
        "primary_light": "#818CF8",
        "primary_bg": "rgba(99, 102, 241, 0.08)",
        "accent": "#6366F1",  # 强调色（与primary相同）

        # 状态色
        "success": "#10B981",
        "success_bg": "rgba(16, 185, 129, 0.1)",
        "warning": "#F59E0B",
        "warning_bg": "rgba(245, 158, 11, 0.1)",
        "error": "#EF4444",
        "error_bg": "rgba(239, 68, 68, 0.1)",

        # 聊天气泡
        "user_bubble": "#6366F1",
        "user_text": "#FFFFFF",
        "ai_bubble": "#FFFFFF",
        "ai_text": "#1E293B",
        "ai_border": "#E2E8F0",

        # 聊天区域
        "chat_bg": "#F8FAFC",

        # 输入框
        "input_bg": "#FFFFFF",
        "input_border": "#E2E8F0",
        "input_focus": "#6366F1",

        # 侧边栏
        "sidebar_bg": "#FFFFFF",
        "sidebar_border": "#E2E8F0",
        "nav_hover": "rgba(99, 102, 241, 0.08)",
        "nav_selected": "rgba(99, 102, 241, 0.12)",

        # 卡片
        "card_bg": "#FFFFFF",
        "card_border": "#E2E8F0",

        # 表格
        "table_bg": "#FFFFFF",
        "table_header": "#F8FAFC",
        "table_border": "#E2E8F0",
        "table_row_hover": "#F8FAFC",
    }

    # 深色主题
    DARK = {
        # 背景色
        "bg_primary": "#0D0D14",
        "bg_secondary": "#13131D",
        "bg_tertiary": "#1A1A28",
        "surface": "#1E1E2E",
        "surface_hover": "#252538",

        # 边框
        "border": "#2D2D3D",
        "border_light": "#252538",

        # 文字
        "text_primary": "#F1F5F9",
        "text_secondary": "#94A3B8",
        "text_muted": "#64748B",

        # 主色调
        "primary": "#818CF8",
        "primary_light": "#A5B4FC",
        "primary_bg": "rgba(129, 140, 248, 0.15)",
        "accent": "#818CF8",  # 强调色（与primary相同）

        # 状态色
        "success": "#34D399",
        "success_bg": "rgba(52, 211, 153, 0.15)",
        "warning": "#FBBF24",
        "warning_bg": "rgba(251, 191, 36, 0.15)",
        "error": "#F87171",
        "error_bg": "rgba(248, 113, 113, 0.15)",

        # 聊天气泡
        "user_bubble": "#6366F1",
        "user_text": "#FFFFFF",
        "ai_bubble": "#1E1E2E",
        "ai_text": "#F1F5F9",
        "ai_border": "#2D2D3D",

        # 聊天区域
        "chat_bg": "#13131D",

        # 输入框
        "input_bg": "#1E1E2E",
        "input_border": "#2D2D3D",
        "input_focus": "#818CF8",

        # 侧边栏
        "sidebar_bg": "#0D0D14",
        "sidebar_border": "#1E1E2E",
        "nav_hover": "rgba(129, 140, 248, 0.1)",
        "nav_selected": "rgba(129, 140, 248, 0.2)",

        # 卡片
        "card_bg": "#1E1E2E",
        "card_border": "#2D2D3D",

        # 表格
        "table_bg": "#1A1A28",
        "table_header": "#1E1E2E",
        "table_border": "#2D2D3D",
        "table_row_hover": "#252538",
    }

    @classmethod
    def get(cls, theme: str = "light") -> Dict[str, str]:
        """获取主题颜色"""
        return cls.DARK if theme == "dark" else cls.LIGHT


# 全局实例
spacing = Spacing()
font_size = FontSize()
border_radius = BorderRadius()


def get_colors(theme: str = "light") -> Dict[str, str]:
    """获取主题颜色的便捷函数"""
    return ThemeColors.get(theme)


# ==================== 组件样式生成器 ====================

class StyleGenerator:
    """样式生成器 - 根据主题生成组件样式"""

    def __init__(self, theme: str = "light"):
        self.theme = theme
        self.colors = get_colors(theme)

    def set_theme(self, theme: str):
        self.theme = theme
        self.colors = get_colors(theme)

    # ---------- 按钮样式 ----------

    def button_primary(self) -> str:
        return f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #8B5CF6, stop:1 #6366F1);
                color: white;
                border: none;
                border-radius: {border_radius.sm}px;
                padding: 10px 20px;
                font-size: {font_size.base}px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #A78BFA, stop:1 #818CF8);
            }}
            QPushButton:pressed {{
                background: #6366F1;
            }}
            QPushButton:disabled {{
                background: {self.colors['border']};
                color: {self.colors['text_muted']};
            }}
        """

    def button_secondary(self) -> str:
        return f"""
            QPushButton {{
                background-color: {self.colors['success_bg']};
                color: {self.colors['success']};
                border: 1px solid {self.colors['success']};
                border-radius: {border_radius.sm}px;
                padding: 8px 16px;
                font-size: {font_size.sm}px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {self.colors['success']};
                color: white;
            }}
            QPushButton:disabled {{
                background-color: {self.colors['bg_tertiary']};
                color: {self.colors['text_muted']};
                border-color: {self.colors['border']};
            }}
        """

    def button_text(self, color: str = None) -> str:
        """文字按钮（带轻背景）"""
        c = color or self.colors['primary']
        return f"""
            QPushButton {{
                background: {self.colors['surface']};
                color: {c};
                border: 1px solid {self.colors['border']};
                border-radius: {border_radius.sm}px;
                padding: 4px 8px;
                font-size: {font_size.sm}px;
            }}
            QPushButton:hover {{
                background: {self.colors['surface_hover']};
                border-color: {c};
            }}
        """

    # ---------- 输入框样式 ----------

    def input_text(self) -> str:
        return f"""
            QLineEdit, QTextEdit {{
                background-color: {self.colors['input_bg']};
                border: 1px solid {self.colors['input_border']};
                border-radius: {border_radius.md}px;
                padding: {spacing.sm}px {spacing.md}px;
                color: {self.colors['text_primary']};
                font-size: {font_size.base}px;
            }}
            QLineEdit:focus, QTextEdit:focus {{
                border-color: {self.colors['input_focus']};
            }}
        """

    def combo_box(self) -> str:
        return f"""
            QComboBox {{
                background-color: {self.colors['input_bg']};
                border: 1px solid {self.colors['input_border']};
                border-radius: {border_radius.sm}px;
                padding: 8px 12px;
                color: {self.colors['text_primary']};
                font-size: {font_size.base}px;
                min-height: 20px;
            }}
            QComboBox:focus {{
                border-color: {self.colors['input_focus']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid {self.colors['text_secondary']};
                margin-right: 8px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {self.colors['surface']};
                border: 1px solid {self.colors['border']};
                border-radius: {border_radius.sm}px;
                selection-background-color: {self.colors['primary_bg']};
                selection-color: {self.colors['primary']};
            }}
        """

    def spin_box(self) -> str:
        return f"""
            QSpinBox {{
                background-color: {self.colors['input_bg']};
                border: 1px solid {self.colors['input_border']};
                border-radius: {border_radius.sm}px;
                padding: 6px 10px;
                color: {self.colors['text_primary']};
                font-size: {font_size.base}px;
            }}
            QSpinBox:focus {{
                border-color: {self.colors['input_focus']};
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                background: transparent;
                border: none;
                width: 16px;
            }}
        """

    def check_box(self) -> str:
        return f"""
            QCheckBox {{
                color: {self.colors['text_primary']};
                font-size: {font_size.base}px;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {self.colors['border']};
                border-radius: 4px;
                background: {self.colors['input_bg']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {self.colors['primary']};
                border-color: {self.colors['primary']};
            }}
            QCheckBox::indicator:hover {{
                border-color: {self.colors['primary']};
            }}
        """

    # ---------- 标签样式 ----------

    def label_primary(self) -> str:
        return f"""
            QLabel {{
                color: {self.colors['text_primary']};
                background: transparent;
                font-size: {font_size.base}px;
            }}
        """

    def label_secondary(self) -> str:
        return f"""
            QLabel {{
                color: {self.colors['text_secondary']};
                background: transparent;
                font-size: {font_size.sm}px;
            }}
        """

    def label_muted(self) -> str:
        return f"""
            QLabel {{
                color: {self.colors['text_muted']};
                background: transparent;
                font-size: {font_size.xs}px;
            }}
        """

    # ---------- 卡片样式 ----------

    def card(self) -> str:
        return f"""
            QFrame {{
                background-color: {self.colors['card_bg']};
                border: 1px solid {self.colors['card_border']};
                border-radius: {border_radius.md}px;
            }}
        """

    # ---------- 表格样式 ----------

    def table(self) -> str:
        return f"""
            QTableWidget {{
                background-color: {self.colors['table_bg']};
                border: 1px solid {self.colors['table_border']};
                border-radius: {border_radius.sm}px;
                gridline-color: {self.colors['table_border']};
                color: {self.colors['text_primary']};
                outline: none;
            }}
            QTableWidget::item {{
                padding: 10px;
                border: none;
                outline: none;
            }}
            QTableWidget::item:selected {{
                background-color: {self.colors['primary_bg']};
                color: {self.colors['text_primary']};
                outline: none;
            }}
            QTableWidget::item:focus {{
                outline: none;
                border: none;
            }}
            QTableWidget::item:hover {{
                background-color: {self.colors['table_row_hover']};
            }}
            QHeaderView::section {{
                background-color: {self.colors['table_header']};
                color: {self.colors['text_secondary']};
                padding: 10px;
                border: none;
                border-bottom: 1px solid {self.colors['table_border']};
                font-weight: 500;
            }}
            QTableWidget:focus {{
                outline: none;
                border: 1px solid {self.colors['table_border']};
            }}
        """

    # ---------- 滚动条样式 ----------

    def scrollbar(self) -> str:
        return f"""
            QScrollBar:vertical {{
                background: transparent;
                width: 8px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {self.colors['border']};
                border-radius: 4px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {self.colors['text_muted']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: transparent;
            }}
            QScrollBar:horizontal {{
                background: transparent;
                height: 8px;
                margin: 0;
            }}
            QScrollBar::handle:horizontal {{
                background: {self.colors['border']};
                border-radius: 4px;
                min-width: 30px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: {self.colors['text_muted']};
            }}
        """

    # ---------- 导航项样式 ----------

    def nav_item(self, selected: bool = False) -> str:
        if selected:
            return f"""
                QPushButton {{
                    background-color: {self.colors['nav_selected']};
                    color: {self.colors['primary']};
                    border: none;
                    border-left: 3px solid {self.colors['primary']};
                    border-radius: 0;
                    text-align: left;
                    padding-left: 12px;
                    font-weight: 500;
                }}
            """
        else:
            return f"""
                QPushButton {{
                    background-color: transparent;
                    color: {self.colors['text_secondary']};
                    border: none;
                    border-left: 3px solid transparent;
                    border-radius: 0;
                    text-align: left;
                    padding-left: 12px;
                }}
                QPushButton:hover {{
                    background-color: {self.colors['nav_hover']};
                    color: {self.colors['text_primary']};
                }}
            """

    # ---------- 聊天气泡样式 ----------

    def user_bubble(self) -> str:
        return f"""
            QFrame#userBubble {{
                background-color: {self.colors['user_bubble']};
                border-radius: {border_radius.lg}px;
                border-top-right-radius: {border_radius.sm}px;
            }}
        """

    def ai_bubble(self) -> str:
        return f"""
            QFrame#aiBubble {{
                background-color: {self.colors['ai_bubble']};
                border: 1px solid {self.colors['ai_border']};
                border-radius: {border_radius.lg}px;
                border-top-left-radius: {border_radius.sm}px;
            }}
        """

    # ---------- 全局应用样式 ----------

    def global_stylesheet(self) -> str:
        """全局样式表"""
        return f"""
            QWidget {{
                font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
            }}

            QScrollArea {{
                border: none;
                background: transparent;
            }}

            QFrame {{
                border: none;
            }}

            QGroupBox {{
                font-weight: 500;
                font-size: {font_size.md}px;
                color: {self.colors['text_primary']};
                border: 1px solid {self.colors['border']};
                border-radius: {border_radius.md}px;
                margin-top: 12px;
                padding-top: 16px;
                background: {self.colors['card_bg']};
            }}

            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 16px;
                padding: 0 8px;
                background: {self.colors['card_bg']};
            }}

            {self.scrollbar()}
        """
