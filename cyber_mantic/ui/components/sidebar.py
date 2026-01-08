"""
SidebarWidget - 左侧导航栏组件

V2版本核心组件，包含：
- Logo区域（图标+中英文名）
- 导航项列表（问道、推演、典籍、洞察、历史、设置）
- 底部固定项（关于）
- 收起/展开功能

设计规范（来自v2_task_plan.md）：
- 展开宽度：180px
- 收起宽度：60px（只显示图标）
- Logo区域高度：80-100px
- 切换按钮：Logo区域右下角
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QSize
from PyQt6.QtGui import QFont, QPixmap
import os

from .nav_item import NavItem


# 导航项配置
NAV_ITEMS = [
    {"id": "wendao", "name": "问道", "icon": "💬"},
    {"id": "tuiyan", "name": "推演", "icon": "📊"},
    {"id": "dianji", "name": "典籍", "icon": "📚"},
    {"id": "dongcha", "name": "洞察", "icon": "👁"},
    {"id": "lishi", "name": "历史", "icon": "📜"},
    {"id": "shezhi", "name": "设置", "icon": "⚙️"},
]


class SidebarWidget(QWidget):
    """左侧导航栏组件"""

    # 导航切换信号
    navigation_changed = pyqtSignal(str)  # 发送nav_id

    # 尺寸常量
    EXPANDED_WIDTH = 180
    COLLAPSED_WIDTH = 60
    LOGO_HEIGHT = 90

    def __init__(self, theme: str = "dark", parent=None):
        super().__init__(parent)
        self.theme = theme
        self.is_expanded = True
        self.current_nav = "wendao"  # 默认选中问道
        self.nav_items = {}

        self._setup_ui()
        self._apply_theme()

    def _setup_ui(self):
        """设置UI"""
        self.setFixedWidth(self.EXPANDED_WIDTH)
        self.setMinimumHeight(500)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ========== Logo区域 ==========
        self.logo_widget = self._create_logo_section()
        layout.addWidget(self.logo_widget)

        # 分隔线
        layout.addWidget(self._create_separator())

        # ========== 导航项列表 ==========
        nav_widget = QWidget()
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(0, 8, 0, 8)
        nav_layout.setSpacing(4)

        for item in NAV_ITEMS:
            nav_item = NavItem(item["id"], item["name"], item["icon"], self.theme)
            nav_item.clicked.connect(self._on_nav_clicked)
            nav_layout.addWidget(nav_item)
            self.nav_items[item["id"]] = nav_item

        # 默认选中第一个
        self.nav_items["wendao"].set_selected(True)

        layout.addWidget(nav_widget)

        # 弹性空间
        layout.addStretch()

        # 分隔线
        layout.addWidget(self._create_separator())

        # ========== 底部固定项（关于） ==========
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 8, 0, 16)
        bottom_layout.setSpacing(0)

        self.about_item = NavItem("about", "关于", "ℹ️", self.theme)
        self.about_item.clicked.connect(self._on_nav_clicked)
        bottom_layout.addWidget(self.about_item)
        self.nav_items["about"] = self.about_item

        layout.addWidget(bottom_widget)

        self.setLayout(layout)

    def _create_logo_section(self) -> QWidget:
        """创建Logo区域"""
        widget = QWidget()
        widget.setFixedHeight(self.LOGO_HEIGHT)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 16, 12, 8)
        layout.setSpacing(4)

        # Logo + 名字容器
        content_layout = QHBoxLayout()
        content_layout.setSpacing(10)

        # Logo图标
        self.logo_label = QLabel()
        logo_path = self._get_logo_path()
        if logo_path and os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            scaled = pixmap.scaled(
                40, 40,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.logo_label.setPixmap(scaled)
        else:
            self.logo_label.setText("🔮")
            logo_font = QFont()
            logo_font.setPointSize(24)
            self.logo_label.setFont(logo_font)
        self.logo_label.setFixedSize(40, 40)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(self.logo_label)

        # 名字区域（中文+英文）
        self.name_widget = QWidget()
        name_layout = QVBoxLayout(self.name_widget)
        name_layout.setContentsMargins(0, 0, 0, 0)
        name_layout.setSpacing(0)

        # 中文名
        self.cn_name = QLabel("赛博玄数")
        cn_font = QFont()
        cn_font.setPointSize(14)
        cn_font.setWeight(QFont.Weight.Bold)
        self.cn_name.setFont(cn_font)
        name_layout.addWidget(self.cn_name)

        # 英文名
        self.en_name = QLabel("Cyber Mantic")
        en_font = QFont()
        en_font.setPointSize(9)
        self.en_name.setFont(en_font)
        name_layout.addWidget(self.en_name)

        content_layout.addWidget(self.name_widget)
        content_layout.addStretch()

        layout.addLayout(content_layout)

        # 收起/展开按钮（汉堡菜单样式）
        toggle_layout = QHBoxLayout()
        toggle_layout.addStretch()

        self.toggle_btn = QPushButton("☰")  # 汉堡菜单图标
        self.toggle_btn.setFixedSize(28, 28)
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.clicked.connect(self._toggle_expand)
        self.toggle_btn.setToolTip("收起/展开侧边栏")
        toggle_layout.addWidget(self.toggle_btn)

        layout.addLayout(toggle_layout)

        return widget

    def _create_separator(self) -> QFrame:
        """创建分隔线"""
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFixedHeight(1)
        return separator

    def _get_logo_path(self) -> str:
        """获取Logo路径"""
        possible_paths = [
            os.path.join(os.path.dirname(__file__), '..', 'resources', 'app_icon.png'),
            os.path.join(os.path.dirname(__file__), '..', '..', 'ui', 'resources', 'app_icon.png'),
        ]
        for path in possible_paths:
            abs_path = os.path.abspath(path)
            if os.path.exists(abs_path):
                return abs_path
        return None

    def _apply_theme(self):
        """应用主题样式"""
        is_dark = self.theme == "dark"

        if is_dark:
            bg_color = "#0F0F1A"
            border_color = "rgba(255, 255, 255, 0.08)"
            text_primary = "#F1F5F9"
            text_secondary = "#94A3B8"
            toggle_bg = "#1E1E2E"
            toggle_hover = "#2D2D3D"
        else:
            bg_color = "#FFFFFF"
            border_color = "rgba(0, 0, 0, 0.08)"
            text_primary = "#1E293B"
            text_secondary = "#64748B"
            toggle_bg = "#F1F5F9"
            toggle_hover = "#E2E8F0"

        self.setStyleSheet(f"""
            SidebarWidget {{
                background-color: {bg_color};
                border-right: 1px solid {border_color};
            }}
            QFrame {{
                background-color: {border_color};
                border: none;
            }}
        """)

        self.cn_name.setStyleSheet(f"color: {text_primary}; background: transparent;")
        self.en_name.setStyleSheet(f"color: {text_secondary}; background: transparent;")

        self.toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {toggle_bg};
                border: none;
                border-radius: 6px;
                color: {text_secondary};
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {toggle_hover};
                color: {text_primary};
            }}
        """)

        # 更新所有导航项主题
        for nav_item in self.nav_items.values():
            nav_item.set_theme(self.theme)

    def _toggle_expand(self):
        """切换展开/收起状态"""
        self.is_expanded = not self.is_expanded

        if self.is_expanded:
            self.setFixedWidth(self.EXPANDED_WIDTH)
            self.name_widget.show()
        else:
            self.setFixedWidth(self.COLLAPSED_WIDTH)
            self.name_widget.hide()

        # 汉堡菜单图标保持不变（☰）

        # 更新所有导航项
        for nav_item in self.nav_items.values():
            nav_item.set_expanded(self.is_expanded)

    def _on_nav_clicked(self, nav_id: str):
        """导航项点击"""
        if nav_id == self.current_nav:
            return

        # 取消之前选中
        if self.current_nav in self.nav_items:
            self.nav_items[self.current_nav].set_selected(False)

        # 选中新项
        self.current_nav = nav_id
        self.nav_items[nav_id].set_selected(True)

        # 发送信号
        self.navigation_changed.emit(nav_id)

    def set_current_nav(self, nav_id: str):
        """设置当前选中的导航项"""
        self._on_nav_clicked(nav_id)

    def set_theme(self, theme: str):
        """设置主题"""
        self.theme = theme
        self._apply_theme()

    def get_current_nav(self) -> str:
        """获取当前选中的导航项"""
        return self.current_nav
