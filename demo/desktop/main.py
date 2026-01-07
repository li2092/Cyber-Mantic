#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
赛博玄数 - PyQt6 桌面应用Demo
现代化玻璃拟态设计风格
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QScrollArea, QTextEdit, QLineEdit,
    QStackedWidget, QGraphicsDropShadowEffect, QSizePolicy, QSpacerItem,
    QGridLayout, QProgressBar, QComboBox, QSpinBox, QDateEdit, QTabWidget
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize, pyqtSignal, QTimer, QDate
from PyQt6.QtGui import QFont, QColor, QPalette, QLinearGradient, QPainter, QBrush, QPen, QIcon


# ============== 样式表定义 ==============
STYLE_SHEET = """
/* 全局样式 */
QMainWindow, QWidget {
    background-color: #0f0f1a;
    color: #f1f5f9;
    font-family: "Microsoft YaHei", "Noto Sans SC", sans-serif;
}

/* 侧边栏 */
#sidebar {
    background-color: rgba(26, 26, 46, 0.95);
    border-right: 1px solid rgba(255, 255, 255, 0.08);
}

/* Logo区域 */
#logoContainer {
    background: transparent;
    padding: 20px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

#logoIcon {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #6366f1, stop:1 #818cf8);
    border-radius: 12px;
    font-size: 24px;
    color: white;
}

#logoText {
    font-family: "Noto Serif SC", serif;
    font-size: 20px;
    font-weight: 600;
    color: #f1f5f9;
}

#logoSubtitle {
    font-size: 10px;
    color: #64748b;
    letter-spacing: 2px;
}

/* 导航按钮 */
NavButton {
    background: transparent;
    border: none;
    border-radius: 10px;
    padding: 12px 16px;
    text-align: left;
    color: #94a3b8;
    font-size: 14px;
}

NavButton:hover {
    background: rgba(99, 102, 241, 0.1);
    color: #f1f5f9;
}

NavButton[active="true"] {
    background: rgba(99, 102, 241, 0.15);
    color: #818cf8;
    border-left: 3px solid #6366f1;
}

/* 主内容区顶部栏 */
#topbar {
    background: rgba(26, 26, 46, 0.8);
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    padding: 12px 24px;
}

#pageTitle {
    font-size: 18px;
    font-weight: 500;
    color: #f1f5f9;
}

/* 搜索框 */
#searchBox {
    background: #252542;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 8px 16px;
    color: #f1f5f9;
    font-size: 13px;
}

#searchBox:focus {
    border-color: #6366f1;
}

/* 卡片样式 */
.card {
    background: rgba(30, 30, 50, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
}

.card:hover {
    border-color: rgba(99, 102, 241, 0.3);
}

.cardTitle {
    font-size: 14px;
    font-weight: 500;
    color: #f1f5f9;
    padding: 16px 20px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.cardBody {
    padding: 20px;
}

/* 统计卡片 */
.statCard {
    background: rgba(30, 30, 50, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 20px;
}

.statCard:hover {
    border-color: #6366f1;
    background: rgba(40, 40, 60, 0.7);
}

.statValue {
    font-size: 28px;
    font-weight: 700;
    color: #f1f5f9;
}

.statLabel {
    font-size: 13px;
    color: #64748b;
}

.statTrend {
    font-size: 11px;
    padding: 3px 8px;
    border-radius: 8px;
}

.statTrendUp {
    background: rgba(16, 185, 129, 0.15);
    color: #10b981;
}

.statTrendDown {
    background: rgba(239, 68, 68, 0.15);
    color: #ef4444;
}

/* 按钮样式 */
.btnPrimary {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #6366f1, stop:1 #4f46e5);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 12px 24px;
    font-size: 14px;
    font-weight: 500;
}

.btnPrimary:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #818cf8, stop:1 #6366f1);
}

.btnPrimary:pressed {
    background: #4f46e5;
}

.btnSecondary {
    background: rgba(255, 255, 255, 0.03);
    color: #f1f5f9;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 12px 24px;
    font-size: 14px;
}

.btnSecondary:hover {
    background: rgba(255, 255, 255, 0.06);
    border-color: #6366f1;
}

/* 聊天消息 */
.messageAI {
    background: #252542;
    border-radius: 16px;
    border-bottom-left-radius: 4px;
    padding: 12px 16px;
    color: #f1f5f9;
    font-size: 14px;
}

.messageUser {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #6366f1, stop:1 #4f46e5);
    border-radius: 16px;
    border-bottom-right-radius: 4px;
    padding: 12px 16px;
    color: white;
    font-size: 14px;
}

/* 输入框 */
.chatInput {
    background: #252542;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 12px 16px;
    color: #f1f5f9;
    font-size: 14px;
}

.chatInput:focus {
    border-color: #6366f1;
}

/* 八字命盘 */
.pillarCard {
    background: #252542;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 16px;
}

.pillarLabel {
    font-size: 11px;
    color: #64748b;
}

.pillarGan {
    font-family: "Noto Serif SC", serif;
    font-size: 24px;
    color: #818cf8;
}

.pillarZhi {
    font-family: "Noto Serif SC", serif;
    font-size: 24px;
    color: #f59e0b;
}

/* 五行元素 */
.wuxingWood { background: rgba(34, 197, 94, 0.2); color: #22c55e; }
.wuxingFire { background: rgba(239, 68, 68, 0.2); color: #ef4444; }
.wuxingEarth { background: rgba(245, 158, 11, 0.2); color: #f59e0b; }
.wuxingMetal { background: rgba(226, 232, 240, 0.2); color: #e2e8f0; }
.wuxingWater { background: rgba(59, 130, 246, 0.2); color: #3b82f6; }

/* 快捷操作按钮 */
.quickAction {
    background: #252542;
    border: 1px solid transparent;
    border-radius: 12px;
    padding: 20px;
}

.quickAction:hover {
    background: rgba(99, 102, 241, 0.1);
    border-color: #6366f1;
}

/* 历史记录项 */
.historyItem {
    background: transparent;
    border: none;
    border-radius: 10px;
    padding: 12px;
    text-align: left;
}

.historyItem:hover {
    background: #252542;
}

/* 进度条 */
QProgressBar {
    background: #252542;
    border: none;
    border-radius: 6px;
    height: 8px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #6366f1, stop:1 #f59e0b);
    border-radius: 6px;
}

/* 下拉框 */
QComboBox {
    background: #252542;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 10px 16px;
    color: #f1f5f9;
    font-size: 14px;
}

QComboBox:hover {
    border-color: #6366f1;
}

QComboBox::drop-down {
    border: none;
    width: 30px;
}

QComboBox QAbstractItemView {
    background: #1a1a2e;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    selection-background-color: rgba(99, 102, 241, 0.3);
}

/* 标签页 */
QTabWidget::pane {
    background: transparent;
    border: none;
}

QTabBar::tab {
    background: transparent;
    color: #64748b;
    padding: 12px 20px;
    margin-right: 4px;
    border-bottom: 2px solid transparent;
}

QTabBar::tab:hover {
    color: #f1f5f9;
}

QTabBar::tab:selected {
    color: #818cf8;
    border-bottom: 2px solid #6366f1;
}

/* 滚动条 */
QScrollBar:vertical {
    background: #1a1a2e;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #252542;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: #6366f1;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

/* 用户卡片 */
#userCard {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 12px;
}

#userAvatar {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #f59e0b, stop:1 #fbbf24);
    border-radius: 20px;
    color: white;
    font-weight: 600;
}

#userName {
    font-size: 14px;
    font-weight: 500;
    color: #f1f5f9;
}

#userStatus {
    font-size: 12px;
    color: #10b981;
}

/* 欢迎横幅 */
#welcomeBanner {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 rgba(99, 102, 241, 0.2),
        stop:0.5 rgba(245, 158, 11, 0.1),
        stop:1 rgba(16, 185, 129, 0.1));
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 20px;
    padding: 28px;
}

#welcomeTitle {
    font-family: "Noto Serif SC", serif;
    font-size: 24px;
    font-weight: 600;
    color: #f1f5f9;
}

#welcomeSubtitle {
    font-size: 14px;
    color: #94a3b8;
}
"""


class NavButton(QPushButton):
    """自定义导航按钮"""

    def __init__(self, icon: str, text: str, parent=None):
        super().__init__(parent)
        self.setText(f"  {icon}   {text}")
        self.setFixedHeight(44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setProperty("active", False)

    def setActive(self, active: bool):
        self.setProperty("active", active)
        self.style().unpolish(self)
        self.style().polish(self)


class GlassCard(QFrame):
    """玻璃拟态卡片组件"""

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.setProperty("class", "card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        if title:
            title_label = QLabel(title)
            title_label.setProperty("class", "cardTitle")
            layout.addWidget(title_label)

        self.body = QWidget()
        self.body.setProperty("class", "cardBody")
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(20, 20, 20, 20)
        layout.addWidget(self.body)

        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)


class StatCard(QFrame):
    """统计数据卡片"""

    def __init__(self, icon: str, value: str, label: str, trend: str = "", trend_up: bool = True, parent=None):
        super().__init__(parent)
        self.setProperty("class", "statCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # 头部：图标和趋势
        header = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("""
            background: rgba(99, 102, 241, 0.15);
            color: #818cf8;
            font-size: 24px;
            padding: 12px;
            border-radius: 12px;
        """)
        icon_label.setFixedSize(48, 48)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(icon_label)
        header.addStretch()

        if trend:
            trend_label = QLabel(trend)
            trend_class = "statTrendUp" if trend_up else "statTrendDown"
            trend_label.setProperty("class", f"statTrend {trend_class}")
            trend_label.setStyleSheet(f"""
                background: {'rgba(16, 185, 129, 0.15)' if trend_up else 'rgba(239, 68, 68, 0.15)'};
                color: {'#10b981' if trend_up else '#ef4444'};
                padding: 4px 10px;
                border-radius: 8px;
                font-size: 11px;
            """)
            header.addWidget(trend_label)

        layout.addLayout(header)

        # 数值
        value_label = QLabel(value)
        value_label.setProperty("class", "statValue")
        value_label.setStyleSheet("font-size: 32px; font-weight: 700; color: #f1f5f9;")
        layout.addWidget(value_label)

        # 标签
        label_widget = QLabel(label)
        label_widget.setProperty("class", "statLabel")
        label_widget.setStyleSheet("font-size: 13px; color: #64748b;")
        layout.addWidget(label_widget)

        # 阴影
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)


class ChatBubble(QFrame):
    """聊天气泡"""

    def __init__(self, message: str, is_user: bool = False, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)

        if is_user:
            layout.addStretch()

        # 头像
        avatar = QLabel("李" if is_user else "☯")
        avatar.setFixedSize(36, 36)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(f"""
            background: {'qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #f59e0b, stop:1 #fbbf24)' if is_user else 'qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6366f1, stop:1 #818cf8)'};
            border-radius: 18px;
            color: white;
            font-weight: 600;
            font-size: 14px;
        """)

        # 消息内容
        content = QLabel(message)
        content.setWordWrap(True)
        content.setMaximumWidth(400)
        content.setProperty("class", "messageUser" if is_user else "messageAI")
        content.setStyleSheet(f"""
            background: {'qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6366f1, stop:1 #4f46e5)' if is_user else '#252542'};
            border-radius: 16px;
            {'border-bottom-right-radius: 4px;' if is_user else 'border-bottom-left-radius: 4px;'}
            padding: 12px 16px;
            color: {'white' if is_user else '#f1f5f9'};
            font-size: 14px;
            line-height: 1.5;
        """)

        if is_user:
            layout.addWidget(content)
            layout.addWidget(avatar)
        else:
            layout.addWidget(avatar)
            layout.addWidget(content)
            layout.addStretch()


class BaZiPillar(QFrame):
    """八字柱位显示"""

    def __init__(self, label: str, gan: str, zhi: str, parent=None):
        super().__init__(parent)
        self.setProperty("class", "pillarCard")
        self.setStyleSheet("""
            background: #252542;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 16px;
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(8)

        # 标签
        label_widget = QLabel(label)
        label_widget.setStyleSheet("font-size: 11px; color: #64748b;")
        label_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label_widget)

        # 天干
        gan_widget = QLabel(gan)
        gan_widget.setStyleSheet("""
            font-family: "Noto Serif SC", serif;
            font-size: 28px;
            color: #818cf8;
        """)
        gan_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(gan_widget)

        # 地支
        zhi_widget = QLabel(zhi)
        zhi_widget.setStyleSheet("""
            font-family: "Noto Serif SC", serif;
            font-size: 28px;
            color: #f59e0b;
        """)
        zhi_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(zhi_widget)


class WuXingIndicator(QFrame):
    """五行指示器"""

    COLORS = {
        "木": ("#22c55e", "rgba(34, 197, 94, 0.2)"),
        "火": ("#ef4444", "rgba(239, 68, 68, 0.2)"),
        "土": ("#f59e0b", "rgba(245, 158, 11, 0.2)"),
        "金": ("#e2e8f0", "rgba(226, 232, 240, 0.2)"),
        "水": ("#3b82f6", "rgba(59, 130, 246, 0.2)")
    }

    def __init__(self, element: str, count: int, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(8)

        color, bg = self.COLORS.get(element, ("#f1f5f9", "rgba(255,255,255,0.1)"))

        # 圆形指示器
        circle = QLabel(element)
        circle.setFixedSize(48, 48)
        circle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        circle.setStyleSheet(f"""
            background: {bg};
            color: {color};
            border-radius: 24px;
            font-size: 18px;
            font-weight: 500;
        """)
        layout.addWidget(circle, alignment=Qt.AlignmentFlag.AlignCenter)

        # 数量标签
        count_label = QLabel(str(count))
        count_label.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: 600;")
        count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(count_label)

        # 名称
        name_label = QLabel(element)
        name_label.setStyleSheet("color: #94a3b8; font-size: 12px;")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)


class QuickActionButton(QPushButton):
    """快捷操作按钮"""

    def __init__(self, icon: str, text: str, parent=None):
        super().__init__(parent)
        self.setProperty("class", "quickAction")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(8)

        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 32px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        text_label = QLabel(text)
        text_label.setStyleSheet("color: #94a3b8; font-size: 13px;")
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(text_label)

        self.setStyleSheet("""
            QPushButton {
                background: #252542;
                border: 1px solid transparent;
                border-radius: 12px;
                padding: 20px;
            }
            QPushButton:hover {
                background: rgba(99, 102, 241, 0.1);
                border-color: #6366f1;
            }
        """)


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("赛博玄数 - Cyber Mantic")
        self.setMinimumSize(1400, 900)
        self.resize(1600, 1000)

        # 设置样式
        self.setStyleSheet(STYLE_SHEET)

        # 主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 侧边栏
        sidebar = self._create_sidebar()
        main_layout.addWidget(sidebar)

        # 主内容区
        content_area = self._create_content_area()
        main_layout.addWidget(content_area, 1)

    def _create_sidebar(self) -> QWidget:
        """创建侧边栏"""
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(260)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo区域
        logo_container = QWidget()
        logo_container.setObjectName("logoContainer")
        logo_layout = QHBoxLayout(logo_container)
        logo_layout.setContentsMargins(20, 20, 20, 20)

        logo_icon = QLabel("☯")
        logo_icon.setObjectName("logoIcon")
        logo_icon.setFixedSize(48, 48)
        logo_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_icon.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6366f1, stop:1 #818cf8);
            border-radius: 12px;
            font-size: 24px;
            color: white;
        """)
        logo_layout.addWidget(logo_icon)

        logo_text_container = QVBoxLayout()
        logo_text_container.setSpacing(2)

        logo_text = QLabel("赛博玄数")
        logo_text.setObjectName("logoText")
        logo_text.setStyleSheet("""
            font-family: "Noto Serif SC", serif;
            font-size: 20px;
            font-weight: 600;
            color: #f1f5f9;
        """)
        logo_text_container.addWidget(logo_text)

        logo_subtitle = QLabel("CYBER MANTIC")
        logo_subtitle.setObjectName("logoSubtitle")
        logo_subtitle.setStyleSheet("font-size: 10px; color: #64748b; letter-spacing: 2px;")
        logo_text_container.addWidget(logo_subtitle)

        logo_layout.addLayout(logo_text_container)
        logo_layout.addStretch()
        layout.addWidget(logo_container)

        # 导航菜单
        nav_container = QWidget()
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(12, 16, 12, 16)
        nav_layout.setSpacing(4)

        # 核心功能
        section_label1 = QLabel("核心功能")
        section_label1.setStyleSheet("""
            font-size: 10px;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            padding: 8px 12px;
        """)
        nav_layout.addWidget(section_label1)

        self.nav_buttons = []
        nav_items = [
            ("💬", "问道"),
            ("🔮", "推演"),
            ("📚", "典籍"),
        ]

        for icon, text in nav_items:
            btn = NavButton(icon, text)
            btn.clicked.connect(lambda checked, t=text: self._on_nav_click(t))
            nav_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        # 设置第一个为活跃
        self.nav_buttons[0].setActive(True)

        # 个人中心
        section_label2 = QLabel("个人中心")
        section_label2.setStyleSheet("""
            font-size: 10px;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            padding: 8px 12px;
            margin-top: 16px;
        """)
        nav_layout.addWidget(section_label2)

        nav_items2 = [
            ("💡", "洞察"),
            ("📜", "历史记录"),
        ]

        for icon, text in nav_items2:
            btn = NavButton(icon, text)
            btn.clicked.connect(lambda checked, t=text: self._on_nav_click(t))
            nav_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        # 系统
        section_label3 = QLabel("系统")
        section_label3.setStyleSheet("""
            font-size: 10px;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            padding: 8px 12px;
            margin-top: 16px;
        """)
        nav_layout.addWidget(section_label3)

        nav_items3 = [
            ("⚙️", "设置"),
            ("❓", "帮助"),
        ]

        for icon, text in nav_items3:
            btn = NavButton(icon, text)
            btn.clicked.connect(lambda checked, t=text: self._on_nav_click(t))
            nav_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        nav_layout.addStretch()
        layout.addWidget(nav_container, 1)

        # 用户卡片
        user_card = QWidget()
        user_card.setObjectName("userCard")
        user_card.setStyleSheet("""
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            margin: 12px;
            padding: 12px;
        """)

        user_layout = QHBoxLayout(user_card)
        user_layout.setSpacing(12)

        avatar = QLabel("李")
        avatar.setObjectName("userAvatar")
        avatar.setFixedSize(40, 40)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #f59e0b, stop:1 #fbbf24);
            border-radius: 20px;
            color: white;
            font-weight: 600;
        """)
        user_layout.addWidget(avatar)

        user_info = QVBoxLayout()
        user_info.setSpacing(2)

        user_name = QLabel("李明")
        user_name.setObjectName("userName")
        user_name.setStyleSheet("font-size: 14px; font-weight: 500; color: #f1f5f9;")
        user_info.addWidget(user_name)

        user_status = QLabel("● API 已连接")
        user_status.setObjectName("userStatus")
        user_status.setStyleSheet("font-size: 12px; color: #10b981;")
        user_info.addWidget(user_status)

        user_layout.addLayout(user_info)
        user_layout.addStretch()

        layout.addWidget(user_card)

        return sidebar

    def _create_content_area(self) -> QWidget:
        """创建主内容区"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 顶部栏
        topbar = self._create_topbar()
        layout.addWidget(topbar)

        # 内容滚动区
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        content = self._create_main_content()
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        return container

    def _create_topbar(self) -> QWidget:
        """创建顶部栏"""
        topbar = QWidget()
        topbar.setObjectName("topbar")
        topbar.setFixedHeight(64)
        topbar.setStyleSheet("""
            background: rgba(26, 26, 46, 0.8);
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        """)

        layout = QHBoxLayout(topbar)
        layout.setContentsMargins(24, 0, 24, 0)

        # 页面标题
        title = QLabel("💬  问道 · 智能对话")
        title.setObjectName("pageTitle")
        title.setStyleSheet("font-size: 18px; font-weight: 500; color: #f1f5f9;")
        layout.addWidget(title)

        layout.addStretch()

        # 搜索框
        search = QLineEdit()
        search.setObjectName("searchBox")
        search.setPlaceholderText("🔍  搜索历史记录...")
        search.setFixedWidth(240)
        search.setStyleSheet("""
            background: #252542;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 8px 16px;
            color: #f1f5f9;
            font-size: 13px;
        """)
        layout.addWidget(search)

        # 图标按钮
        for icon in ["🔔", "🌙"]:
            btn = QPushButton(icon)
            btn.setFixedSize(40, 40)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.03);
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    border-radius: 10px;
                    font-size: 16px;
                }
                QPushButton:hover {
                    background: #252542;
                }
            """)
            layout.addWidget(btn)

        return topbar

    def _create_main_content(self) -> QWidget:
        """创建主内容"""
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)

        # 欢迎横幅
        welcome = self._create_welcome_banner()
        layout.addWidget(welcome)

        # 统计卡片
        stats = self._create_stats_section()
        layout.addLayout(stats)

        # 主内容网格
        main_grid = QHBoxLayout()
        main_grid.setSpacing(24)

        # 左侧：对话区
        chat_card = self._create_chat_section()
        main_grid.addWidget(chat_card, 2)

        # 右侧：信息面板
        right_panel = self._create_right_panel()
        main_grid.addLayout(right_panel, 1)

        layout.addLayout(main_grid, 1)

        return content

    def _create_welcome_banner(self) -> QWidget:
        """创建欢迎横幅"""
        banner = QFrame()
        banner.setObjectName("welcomeBanner")
        banner.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 rgba(99, 102, 241, 0.2),
                stop:0.5 rgba(245, 158, 11, 0.1),
                stop:1 rgba(16, 185, 129, 0.1));
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 20px;
            padding: 28px;
        """)

        layout = QVBoxLayout(banner)
        layout.setSpacing(12)

        title = QLabel("欢迎回来，李明")
        title.setObjectName("welcomeTitle")
        title.setStyleSheet("""
            font-family: "Noto Serif SC", serif;
            font-size: 24px;
            font-weight: 600;
            color: #f1f5f9;
        """)
        layout.addWidget(title)

        subtitle = QLabel("今日宜：问事、出行、签约 | 紫气东来，万事可期")
        subtitle.setObjectName("welcomeSubtitle")
        subtitle.setStyleSheet("font-size: 14px; color: #94a3b8;")
        layout.addWidget(subtitle)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        btn_primary = QPushButton("✨  开始新对话")
        btn_primary.setProperty("class", "btnPrimary")
        btn_primary.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_primary.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6366f1, stop:1 #4f46e5);
            color: white;
            border: none;
            border-radius: 10px;
            padding: 12px 24px;
            font-size: 14px;
            font-weight: 500;
        """)
        btn_layout.addWidget(btn_primary)

        btn_secondary = QPushButton("📊  查看今日运势")
        btn_secondary.setProperty("class", "btnSecondary")
        btn_secondary.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_secondary.setStyleSheet("""
            background: rgba(255, 255, 255, 0.03);
            color: #f1f5f9;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 10px;
            padding: 12px 24px;
            font-size: 14px;
        """)
        btn_layout.addWidget(btn_secondary)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        return banner

    def _create_stats_section(self) -> QHBoxLayout:
        """创建统计卡片区"""
        layout = QHBoxLayout()
        layout.setSpacing(24)

        stats = [
            ("📊", "128", "本月分析次数", "↑ 12%", True),
            ("⏱️", "24.5h", "学习总时长", "↑ 8%", True),
            ("📝", "56", "笔记数量", "↑ 5%", True),
            ("🎯", "87%", "分析准确率", "↓ 3%", False),
        ]

        for icon, value, label, trend, trend_up in stats:
            card = StatCard(icon, value, label, trend, trend_up)
            layout.addWidget(card)

        return layout

    def _create_chat_section(self) -> QWidget:
        """创建对话区"""
        card = GlassCard("💬  智能问答")

        # 消息列表
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setMinimumHeight(350)
        scroll.setStyleSheet("background: transparent;")

        messages_widget = QWidget()
        messages_layout = QVBoxLayout(messages_widget)
        messages_layout.setContentsMargins(0, 0, 0, 0)
        messages_layout.setSpacing(16)

        # 示例消息
        messages = [
            ("您好！我是赛博玄数智能助手。请问今天您想咨询什么事项？我可以为您提供八字、紫微斗数、奇门遁甲等多种术数分析。", False),
            ("我想问一下2025年的事业运势如何", True),
            ("好的，为了给您更准确的分析，我需要了解一些基本信息。请问您的出生年月日和时辰是？另外，如果方便的话，可以给我3个随机数字（1-9），用于辅助分析。", False),
        ]

        for msg, is_user in messages:
            bubble = ChatBubble(msg, is_user)
            messages_layout.addWidget(bubble)

        messages_layout.addStretch()
        scroll.setWidget(messages_widget)
        card.body_layout.addWidget(scroll)

        # 输入区
        input_container = QHBoxLayout()
        input_container.setSpacing(12)

        chat_input = QTextEdit()
        chat_input.setPlaceholderText("输入您的问题...")
        chat_input.setMaximumHeight(48)
        chat_input.setStyleSheet("""
            background: #252542;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 12px 16px;
            color: #f1f5f9;
            font-size: 14px;
        """)
        input_container.addWidget(chat_input)

        send_btn = QPushButton("➤")
        send_btn.setFixedSize(48, 48)
        send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        send_btn.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6366f1, stop:1 #4f46e5);
            border: none;
            border-radius: 12px;
            color: white;
            font-size: 18px;
        """)
        input_container.addWidget(send_btn)

        card.body_layout.addLayout(input_container)

        return card

    def _create_right_panel(self) -> QVBoxLayout:
        """创建右侧面板"""
        layout = QVBoxLayout()
        layout.setSpacing(24)

        # 八字命盘
        bazi_card = GlassCard("🎴  八字命盘")

        pillars_layout = QHBoxLayout()
        pillars_layout.setSpacing(12)

        pillars = [("年柱", "甲", "子"), ("月柱", "丙", "寅"), ("日柱", "戊", "辰"), ("时柱", "庚", "午")]
        for label, gan, zhi in pillars:
            pillar = BaZiPillar(label, gan, zhi)
            pillars_layout.addWidget(pillar)

        bazi_card.body_layout.addLayout(pillars_layout)

        # 五行分布
        wuxing_layout = QHBoxLayout()
        wuxing_layout.setSpacing(8)

        for element, count in [("木", 2), ("火", 3), ("土", 2), ("金", 1), ("水", 0)]:
            indicator = WuXingIndicator(element, count)
            wuxing_layout.addWidget(indicator)

        bazi_card.body_layout.addLayout(wuxing_layout)
        layout.addWidget(bazi_card)

        # 快捷操作
        quick_card = GlassCard("⚡  快捷操作")

        quick_grid = QGridLayout()
        quick_grid.setSpacing(12)

        actions = [("🎲", "小六壬"), ("✍️", "测字"), ("🌸", "梅花易数"), ("⚔️", "六爻")]
        for i, (icon, text) in enumerate(actions):
            btn = QuickActionButton(icon, text)
            quick_grid.addWidget(btn, i // 2, i % 2)

        quick_card.body_layout.addLayout(quick_grid)
        layout.addWidget(quick_card)

        # 最近历史
        history_card = GlassCard("📜  最近分析")

        history_items = [
            ("🟢", "2025年事业运势分析", "八字 · 2小时前"),
            ("🔵", "感情姻缘咨询", "紫微斗数 · 昨天"),
            ("🟡", "投资决策分析", "奇门遁甲 · 3天前"),
        ]

        for dot, title, meta in history_items:
            item_layout = QHBoxLayout()
            item_layout.setSpacing(12)

            dot_label = QLabel(dot)
            dot_label.setStyleSheet("font-size: 8px;")
            item_layout.addWidget(dot_label)

            info_layout = QVBoxLayout()
            info_layout.setSpacing(2)

            title_label = QLabel(title)
            title_label.setStyleSheet("font-size: 13px; color: #f1f5f9;")
            info_layout.addWidget(title_label)

            meta_label = QLabel(meta)
            meta_label.setStyleSheet("font-size: 11px; color: #64748b;")
            info_layout.addWidget(meta_label)

            item_layout.addLayout(info_layout)
            item_layout.addStretch()

            history_card.body_layout.addLayout(item_layout)

        layout.addWidget(history_card)
        layout.addStretch()

        return layout

    def _on_nav_click(self, tab_name: str):
        """导航点击处理"""
        for btn in self.nav_buttons:
            btn.setActive(btn.text().strip().endswith(tab_name))


def main():
    app = QApplication(sys.argv)

    # 设置应用属性
    app.setStyle("Fusion")

    # 设置全局字体
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
