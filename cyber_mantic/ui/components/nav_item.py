"""
NavItem - 导航项组件

现代化的导航项，支持：
- 图标 + 文字
- 选中/悬停状态
- 收起模式（只显示图标）
- 流畅的过渡动画
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QSize
from PyQt6.QtGui import QFont, QIcon, QPixmap, QPainter, QColor

from ..design_system import spacing, font_size, border_radius, tokens


class NavItem(QWidget):
    """导航项组件"""

    # 点击信号
    clicked = pyqtSignal(str)  # 发送nav_id

    def __init__(self, nav_id: str, name: str, icon: str,
                 theme: str = "dark", parent=None):
        super().__init__(parent)
        self.nav_id = nav_id
        self.name = name
        self.icon = icon
        self.theme = theme
        self.is_selected = False
        self.is_expanded = True  # 展开状态

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self):
        """设置UI - 使用设计系统规范"""
        self.setFixedHeight(tokens.sidebar["item_height"])
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout()
        layout.setContentsMargins(tokens.sidebar["item_padding"], 0, tokens.sidebar["item_padding"], 0)
        layout.setSpacing(spacing.md)

        # 图标 - 使用专业Unicode图标
        self.icon_label = QLabel(self.icon)
        self.icon_label.setFixedSize(tokens.sidebar["item_icon_size"], tokens.sidebar["item_icon_size"])
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_font = QFont()
        icon_font.setPointSize(font_size.md)
        self.icon_label.setFont(icon_font)
        layout.addWidget(self.icon_label)

        # 文字
        self.text_label = QLabel(self.name)
        text_font = QFont()
        text_font.setPointSize(tokens.sidebar["item_font_size"])
        text_font.setWeight(QFont.Weight.Medium)
        self.text_label.setFont(text_font)
        self.text_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(self.text_label)

        self.setLayout(layout)

    def _apply_style(self):
        """应用样式"""
        is_dark = self.theme == "dark"

        # 颜色定义
        if is_dark:
            bg_normal = "transparent"
            bg_hover = "rgba(99, 102, 241, 0.15)"
            bg_selected = "rgba(99, 102, 241, 0.25)"
            text_normal = "#94A3B8"
            text_hover = "#E2E8F0"
            text_selected = "#A5B4FC"
            border_selected = "#6366F1"
        else:
            bg_normal = "transparent"
            bg_hover = "rgba(99, 102, 241, 0.08)"
            bg_selected = "rgba(99, 102, 241, 0.12)"
            text_normal = "#64748B"
            text_hover = "#334155"
            text_selected = "#6366F1"
            border_selected = "#6366F1"

        if self.is_selected:
            bg = bg_selected
            text_color = text_selected
            border_left = f"3px solid {border_selected}"
        else:
            bg = bg_normal
            text_color = text_normal
            border_left = "3px solid transparent"

        self.setStyleSheet(f"""
            NavItem {{
                background-color: {bg};
                border-radius: {tokens.sidebar["item_radius"]}px;
                border-left: {border_left};
                margin: {spacing.xs}px {spacing.sm}px;
            }}
            NavItem:hover {{
                background-color: {bg_hover};
            }}
            QLabel {{
                color: {text_color};
                background: transparent;
            }}
        """)

    def set_selected(self, selected: bool):
        """设置选中状态"""
        self.is_selected = selected
        self._apply_style()

    def set_expanded(self, expanded: bool):
        """设置展开/收起状态"""
        self.is_expanded = expanded
        self.text_label.setVisible(expanded)

    def set_theme(self, theme: str):
        """设置主题"""
        self.theme = theme
        self._apply_style()

    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.nav_id)
        super().mousePressEvent(event)

    def enterEvent(self, event):
        """鼠标进入"""
        if not self.is_selected:
            is_dark = self.theme == "dark"
            hover_color = "#E2E8F0" if is_dark else "#334155"
            self.icon_label.setStyleSheet(f"color: {hover_color}; background: transparent;")
            self.text_label.setStyleSheet(f"color: {hover_color}; background: transparent;")
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开"""
        self._apply_style()
        super().leaveEvent(event)
