"""
SidebarWidget V2 - 重构版侧边栏组件

核心改进：
1. 简洁设计，无收缩功能
2. 使用真实Logo图片（透明背景）
3. 完整的双主题支持
4. 使用新设计系统
"""

import os
from pathlib import Path
from typing import Dict, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap

from ..design_system_v2 import (
    spacing, font_size, border_radius, get_colors, StyleGenerator
)


# 导航项配置
NAV_ITEMS = [
    {"id": "wendao", "name": "问道", "icon": "💬"},
    {"id": "tuiyan", "name": "推演", "icon": "📊"},
    {"id": "dianji", "name": "典籍", "icon": "📚"},
    {"id": "dongcha", "name": "洞察", "icon": "👁"},
    {"id": "lishi", "name": "历史", "icon": "📜"},
    {"id": "shezhi", "name": "设置", "icon": "⚙️"},
]


class SidebarWidgetV2(QWidget):
    """左侧导航栏组件 V2"""

    # 导航切换信号
    navigation_changed = pyqtSignal(str)
    # 全局字体大小变化信号
    font_size_changed = pyqtSignal(int)

    # 宽度常量
    WIDTH = 200
    # 字体大小范围
    MIN_FONT_SIZE = 10
    MAX_FONT_SIZE = 20
    DEFAULT_FONT_SIZE = 14

    def __init__(self, theme: str = "light", parent=None):
        super().__init__(parent)
        self.theme = theme
        self.colors = get_colors(theme)
        self.style_gen = StyleGenerator(theme)
        self.current_nav = "wendao"
        self.nav_buttons: Dict[str, QPushButton] = {}
        self._global_font_size = self.DEFAULT_FONT_SIZE

        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        self.setFixedWidth(self.WIDTH)
        self._apply_style()

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo区域
        logo_widget = self._create_logo_section()
        layout.addWidget(logo_widget)

        # 分隔线
        layout.addWidget(self._create_separator())

        # 导航项列表
        nav_widget = QWidget()
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(spacing.sm, spacing.md, spacing.sm, spacing.md)
        nav_layout.setSpacing(spacing.xs)

        for item in NAV_ITEMS:
            btn = self._create_nav_button(item)
            nav_layout.addWidget(btn)
            self.nav_buttons[item["id"]] = btn

        layout.addWidget(nav_widget)

        # 弹性空间
        layout.addStretch()

        # 底部分隔线
        layout.addWidget(self._create_separator())

        # 字体大小调节区域
        font_control_widget = self._create_font_size_control()
        layout.addWidget(font_control_widget)

        # 底部分隔线
        layout.addWidget(self._create_separator())

        # 底部固定项（关于）
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(spacing.sm, spacing.md, spacing.sm, spacing.md)
        bottom_layout.setSpacing(0)

        about_btn = self._create_nav_button({"id": "about", "name": "关于", "icon": "ℹ️"})
        bottom_layout.addWidget(about_btn)
        self.nav_buttons["about"] = about_btn

        layout.addWidget(bottom_widget)

        self.setLayout(layout)

        # 默认选中问道
        self._update_selection("wendao")

    def _apply_style(self):
        """应用整体样式"""
        self.setStyleSheet(f"""
            SidebarWidgetV2 {{
                background-color: {self.colors['sidebar_bg']};
                border-right: 1px solid {self.colors['sidebar_border']};
            }}
        """)

    def _create_logo_section(self) -> QWidget:
        """创建Logo区域"""
        widget = QWidget()
        widget.setFixedHeight(90)
        widget.setStyleSheet("background: transparent;")

        layout = QHBoxLayout(widget)
        layout.setContentsMargins(spacing.md, spacing.lg, spacing.md, spacing.md)
        layout.setSpacing(spacing.sm)

        # Logo图片
        self.logo_label = QLabel()
        logo_path = self._get_logo_path()
        if logo_path and os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            scaled = pixmap.scaled(
                44, 44,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.logo_label.setPixmap(scaled)
        else:
            # 使用emoji作为备用
            self.logo_label.setText("🔮")
            self.logo_label.setFont(QFont("Segoe UI Emoji", 24))
        self.logo_label.setFixedSize(48, 48)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setStyleSheet("background: transparent;")  # 确保透明
        layout.addWidget(self.logo_label)

        # 名称区域
        name_widget = QWidget()
        name_widget.setStyleSheet("background: transparent;")
        name_layout = QVBoxLayout(name_widget)
        name_layout.setContentsMargins(0, 0, 0, 0)
        name_layout.setSpacing(2)

        # 中文名
        self.cn_name = QLabel("赛博玄数")
        cn_font = QFont("Microsoft YaHei", font_size.lg)
        cn_font.setBold(True)
        self.cn_name.setFont(cn_font)
        self.cn_name.setStyleSheet(f"color: {self.colors['text_primary']}; background: transparent;")
        name_layout.addWidget(self.cn_name)

        # 英文名 - 优化字体
        self.en_name = QLabel("Cyber Mantic")
        en_font = QFont("Segoe UI", font_size.xs)
        en_font.setItalic(True)
        en_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.5)
        self.en_name.setFont(en_font)
        self.en_name.setStyleSheet(f"color: {self.colors['text_muted']}; background: transparent;")
        name_layout.addWidget(self.en_name)

        layout.addWidget(name_widget)
        layout.addStretch()

        return widget

    def _get_logo_path(self) -> Optional[str]:
        """获取Logo路径"""
        possible_paths = [
            Path(__file__).parent.parent / "resources" / "app_icon.png",
            Path(__file__).parent.parent.parent / "ui" / "resources" / "app_icon.png",
        ]
        for path in possible_paths:
            if path.exists():
                return str(path)
        return None

    def _create_font_size_control(self) -> QWidget:
        """创建字体大小调节控件"""
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(spacing.sm, spacing.sm, spacing.sm, spacing.sm)
        layout.setSpacing(spacing.xs)

        # 标签
        label = QLabel("📏 文字大小")
        label.setFont(QFont("Microsoft YaHei", font_size.xs))
        label.setStyleSheet(f"color: {self.colors['text_muted']}; background: transparent;")
        layout.addWidget(label)

        # 控制行
        control_row = QHBoxLayout()
        control_row.setSpacing(4)

        # 减小按钮
        self._font_decrease_btn = QPushButton("A-")
        self._font_decrease_btn.setFixedSize(32, 28)
        self._font_decrease_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._font_decrease_btn.clicked.connect(self._decrease_font_size)
        self._font_decrease_btn.setStyleSheet(self._get_font_btn_style())
        control_row.addWidget(self._font_decrease_btn)

        # 当前大小显示
        self._font_size_label = QLabel(str(self._global_font_size))
        self._font_size_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._font_size_label.setMinimumWidth(30)
        self._font_size_label.setStyleSheet(f"""
            color: {self.colors['text_primary']};
            font-weight: bold;
            background: transparent;
        """)
        control_row.addWidget(self._font_size_label)

        # 增大按钮
        self._font_increase_btn = QPushButton("A+")
        self._font_increase_btn.setFixedSize(32, 28)
        self._font_increase_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._font_increase_btn.clicked.connect(self._increase_font_size)
        self._font_increase_btn.setStyleSheet(self._get_font_btn_style())
        control_row.addWidget(self._font_increase_btn)

        control_row.addStretch()
        layout.addLayout(control_row)

        return widget

    def _get_font_btn_style(self) -> str:
        """获取字体调节按钮样式"""
        return f"""
            QPushButton {{
                background-color: {self.colors['bg_secondary']};
                color: {self.colors['text_primary']};
                border: 1px solid {self.colors['border']};
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {self.colors['hover_bg']};
                border-color: #6366F1;
            }}
            QPushButton:pressed {{
                background-color: {self.colors['active_bg']};
            }}
        """

    def _increase_font_size(self):
        """增大字体"""
        if self._global_font_size < self.MAX_FONT_SIZE:
            self._global_font_size += 1
            self._font_size_label.setText(str(self._global_font_size))
            self.font_size_changed.emit(self._global_font_size)

    def _decrease_font_size(self):
        """减小字体"""
        if self._global_font_size > self.MIN_FONT_SIZE:
            self._global_font_size -= 1
            self._font_size_label.setText(str(self._global_font_size))
            self.font_size_changed.emit(self._global_font_size)

    def get_font_size(self) -> int:
        """获取当前全局字体大小"""
        return self._global_font_size

    def set_font_size(self, size: int):
        """设置全局字体大小"""
        size = max(self.MIN_FONT_SIZE, min(self.MAX_FONT_SIZE, size))
        if size != self._global_font_size:
            self._global_font_size = size
            self._font_size_label.setText(str(self._global_font_size))
            self.font_size_changed.emit(self._global_font_size)

    def _create_separator(self) -> QFrame:
        """创建分隔线"""
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {self.colors['border']};")
        return sep

    def _create_nav_button(self, item: dict) -> QPushButton:
        """创建导航按钮"""
        btn = QPushButton(f"  {item['icon']}  {item['name']}")
        btn.setFixedHeight(44)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFont(QFont("Microsoft YaHei", font_size.base))
        btn.setProperty("nav_id", item["id"])
        btn.clicked.connect(lambda: self._on_nav_clicked(item["id"]))
        self._style_nav_button(btn, False)
        return btn

    def _style_nav_button(self, btn: QPushButton, selected: bool):
        """设置导航按钮样式"""
        btn.setStyleSheet(self.style_gen.nav_item(selected))

    def _on_nav_clicked(self, nav_id: str):
        """导航项点击"""
        if nav_id != self.current_nav:
            self._update_selection(nav_id)
            self.navigation_changed.emit(nav_id)

    def _update_selection(self, nav_id: str):
        """更新选中状态"""
        # 取消旧选中
        if self.current_nav in self.nav_buttons:
            self._style_nav_button(self.nav_buttons[self.current_nav], False)
        # 选中新项
        self.current_nav = nav_id
        if nav_id in self.nav_buttons:
            self._style_nav_button(self.nav_buttons[nav_id], True)

    def set_current_nav(self, nav_id: str):
        """设置当前选中的导航项"""
        self._on_nav_clicked(nav_id)

    def get_current_nav(self) -> str:
        """获取当前选中的导航项"""
        return self.current_nav

    def set_theme(self, theme: str):
        """设置主题"""
        self.theme = theme
        self.colors = get_colors(theme)
        self.style_gen.set_theme(theme)
        self._apply_style()

        # 更新文字颜色
        self.cn_name.setStyleSheet(f"color: {self.colors['text_primary']}; background: transparent;")
        self.en_name.setStyleSheet(f"color: {self.colors['text_muted']}; background: transparent;")

        # 更新所有导航按钮
        for nav_id, btn in self.nav_buttons.items():
            self._style_nav_button(btn, nav_id == self.current_nav)
