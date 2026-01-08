"""
QuickResultCard - 快速结论卡片组件

V2版本核心组件，用于显示各理论分析的即时结果：
- 支持多种状态：等待中、进行中、完成（吉/凶/平）、错误
- 状态切换动画
- 点击展开详情

状态定义：
- WAITING: 等待中 - 灰色边框
- RUNNING: 进行中 - 蓝色边框 + 动画
- COMPLETED_GOOD: 吉 - 绿色边框
- COMPLETED_BAD: 凶 - 红色边框
- COMPLETED_NEUTRAL: 平 - 橙色边框
- ERROR: 错误 - 灰色边框
"""

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont
from enum import Enum
from typing import Optional


class CardStatus(Enum):
    """卡片状态枚举"""
    WAITING = "waiting"           # 等待中
    RUNNING = "running"           # 进行中
    COMPLETED_GOOD = "good"       # 完成-吉
    COMPLETED_BAD = "bad"         # 完成-凶
    COMPLETED_NEUTRAL = "neutral" # 完成-平
    ERROR = "error"               # 错误


class QuickResultCard(QFrame):
    """快速结论卡片"""

    # 信号：卡片被点击（展开详情）
    clicked = pyqtSignal(str)  # 发送theory_name

    # 状态样式配置
    STATUS_STYLES = {
        CardStatus.WAITING: {
            "border": "#4B5563",
            "bg": "#1F2937",
            "icon": "⬚",
            "text": "#9CA3AF"
        },
        CardStatus.RUNNING: {
            "border": "#3B82F6",
            "bg": "#1E3A5F",
            "icon": "⏳",
            "text": "#93C5FD"
        },
        CardStatus.COMPLETED_GOOD: {
            "border": "#10B981",
            "bg": "#064E3B",
            "icon": "✅",
            "text": "#6EE7B7"
        },
        CardStatus.COMPLETED_BAD: {
            "border": "#EF4444",
            "bg": "#7F1D1D",
            "icon": "⚠️",
            "text": "#FCA5A5"
        },
        CardStatus.COMPLETED_NEUTRAL: {
            "border": "#F59E0B",
            "bg": "#78350F",
            "icon": "➖",
            "text": "#FCD34D"
        },
        CardStatus.ERROR: {
            "border": "#6B7280",
            "bg": "#1F2937",
            "icon": "❌",
            "text": "#9CA3AF"
        },
    }

    def __init__(self, theory_name: str, theme: str = "dark", parent=None):
        super().__init__(parent)
        self.theory_name = theory_name
        self.theme = theme
        self.status = CardStatus.WAITING
        self.summary = ""
        self.judgment = ""

        # 动画相关
        self._animation_timer = None
        self._animation_frame = 0

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self):
        """设置UI"""
        self.setObjectName("quickResultCard")
        self.setMinimumHeight(60)
        self.setMaximumHeight(80)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout()
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        # 状态图标
        self.icon_label = QLabel("⬚")
        self.icon_label.setFixedWidth(24)
        icon_font = QFont()
        icon_font.setPointSize(14)
        self.icon_label.setFont(icon_font)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.icon_label)

        # 内容区域
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(2)

        # 理论名称
        self.name_label = QLabel(self.theory_name)
        name_font = QFont()
        name_font.setPointSize(11)
        name_font.setWeight(QFont.Weight.Medium)
        self.name_label.setFont(name_font)
        content_layout.addWidget(self.name_label)

        # 摘要文本
        self.summary_label = QLabel("等待分析...")
        summary_font = QFont()
        summary_font.setPointSize(9)
        self.summary_label.setFont(summary_font)
        self.summary_label.setWordWrap(True)
        content_layout.addWidget(self.summary_label)

        layout.addLayout(content_layout)
        layout.addStretch()

        self.setLayout(layout)

    def _apply_style(self):
        """应用当前状态的样式"""
        style = self.STATUS_STYLES.get(self.status, self.STATUS_STYLES[CardStatus.WAITING])

        self.setStyleSheet(f"""
            QFrame#quickResultCard {{
                background-color: {style['bg']};
                border: 2px solid {style['border']};
                border-radius: 8px;
            }}
            QFrame#quickResultCard:hover {{
                border-color: {style['border']};
                background-color: {self._lighten_color(style['bg'])};
            }}
        """)

        self.icon_label.setText(style['icon'])
        self.icon_label.setStyleSheet(f"color: {style['text']}; background: transparent;")
        self.name_label.setStyleSheet(f"color: {style['text']}; background: transparent;")
        self.summary_label.setStyleSheet(f"color: {style['text']}; opacity: 0.8; background: transparent;")

    def _lighten_color(self, hex_color: str) -> str:
        """稍微提亮颜色"""
        # 简单处理：在hex值基础上增加一点亮度
        if hex_color.startswith('#'):
            r = min(255, int(hex_color[1:3], 16) + 20)
            g = min(255, int(hex_color[3:5], 16) + 20)
            b = min(255, int(hex_color[5:7], 16) + 20)
            return f"#{r:02x}{g:02x}{b:02x}"
        return hex_color

    def set_waiting(self):
        """设置为等待状态"""
        self.status = CardStatus.WAITING
        self.summary = ""
        self.summary_label.setText("等待分析...")
        self._stop_animation()
        self._apply_style()

    def set_running(self):
        """设置为进行中状态"""
        self.status = CardStatus.RUNNING
        self.summary_label.setText("正在分析...")
        self._apply_style()
        self._start_animation()

    def set_completed(self, summary: str, judgment: str):
        """
        设置为完成状态

        Args:
            summary: 结果摘要
            judgment: 吉凶判断 ('吉', '凶', '平')
        """
        self._stop_animation()

        self.summary = summary
        self.judgment = judgment

        if judgment == "吉":
            self.status = CardStatus.COMPLETED_GOOD
        elif judgment == "凶":
            self.status = CardStatus.COMPLETED_BAD
        else:
            self.status = CardStatus.COMPLETED_NEUTRAL

        # 截断过长的摘要
        display_summary = summary[:40] + "..." if len(summary) > 40 else summary
        self.summary_label.setText(display_summary)

        self._apply_style()

    def set_error(self, error_msg: str = "分析失败"):
        """设置为错误状态"""
        self._stop_animation()
        self.status = CardStatus.ERROR
        self.summary_label.setText(error_msg)
        self._apply_style()

    def _start_animation(self):
        """开始进行中动画（图标闪烁）"""
        if self._animation_timer is None:
            self._animation_timer = QTimer()
            self._animation_timer.timeout.connect(self._animate_running)
            self._animation_timer.start(500)  # 500ms间隔

    def _stop_animation(self):
        """停止动画"""
        if self._animation_timer is not None:
            self._animation_timer.stop()
            self._animation_timer = None
            self._animation_frame = 0

    def _animate_running(self):
        """进行中动画效果"""
        self._animation_frame = (self._animation_frame + 1) % 3
        icons = ["⏳", "⌛", "⏳"]
        self.icon_label.setText(icons[self._animation_frame])

    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.theory_name)
        super().mousePressEvent(event)

    def get_status(self) -> CardStatus:
        """获取当前状态"""
        return self.status

    def get_summary(self) -> str:
        """获取摘要"""
        return self.summary

    def get_judgment(self) -> str:
        """获取吉凶判断"""
        return self.judgment


class QuickResultPanel(QFrame):
    """快速结论面板 - 包含多个QuickResultCard"""

    # 信号：某个理论卡片被点击
    theory_clicked = pyqtSignal(str)

    # 支持的理论列表
    THEORIES = ["小六壬", "八字", "紫微斗数", "奇门遁甲", "大六壬", "六爻", "梅花易数"]

    def __init__(self, theme: str = "dark", parent=None):
        super().__init__(parent)
        self.theme = theme
        self.cards = {}

        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # 标题
        title_label = QLabel("🔮 理论分析进度")
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setWeight(QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #E2E8F0; padding: 4px 0;")
        layout.addWidget(title_label)

        # 创建各理论卡片
        for theory in self.THEORIES:
            card = QuickResultCard(theory, self.theme)
            card.clicked.connect(self._on_card_clicked)
            layout.addWidget(card)
            self.cards[theory] = card

        layout.addStretch()
        self.setLayout(layout)

    def _on_card_clicked(self, theory_name: str):
        """卡片点击处理"""
        self.theory_clicked.emit(theory_name)

    def set_theory_running(self, theory_name: str):
        """设置理论为进行中状态"""
        if theory_name in self.cards:
            self.cards[theory_name].set_running()

    def set_theory_completed(self, theory_name: str, summary: str, judgment: str):
        """设置理论为完成状态"""
        if theory_name in self.cards:
            self.cards[theory_name].set_completed(summary, judgment)

    def set_theory_error(self, theory_name: str, error_msg: str = "分析失败"):
        """设置理论为错误状态"""
        if theory_name in self.cards:
            self.cards[theory_name].set_error(error_msg)

    def reset_all(self):
        """重置所有卡片"""
        for card in self.cards.values():
            card.set_waiting()

    def get_card(self, theory_name: str) -> Optional[QuickResultCard]:
        """获取指定理论的卡片"""
        return self.cards.get(theory_name)
