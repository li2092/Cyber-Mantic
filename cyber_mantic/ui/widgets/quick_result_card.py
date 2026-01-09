"""
QuickResultCard - 快速结论卡片组件

V2版本核心组件，用于显示各理论分析的即时结果：
- 支持多种状态：等待中、进行中、完成（五级吉凶）、错误
- 状态切换动画
- 点击展开/收起详情（V2新增）

V2五级吉凶颜色系统：
- COMPLETED_DAJI: 大吉 - 红色边框 (judgment_level >= 0.8)
- COMPLETED_XIAOJI: 小吉 - 橙色边框 (0.6 <= judgment_level < 0.8)
- COMPLETED_PING: 平 - 灰色边框 (0.4 <= judgment_level < 0.6)
- COMPLETED_XIAOXIONG: 小凶 - 深绿边框 (0.2 <= judgment_level < 0.4)
- COMPLETED_DAXIONG: 大凶 - 深黑边框 (judgment_level < 0.2)
"""

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont
from enum import Enum
from typing import Optional


class CardStatus(Enum):
    """卡片状态枚举（V2五级吉凶系统）"""
    WAITING = "waiting"                   # 等待中
    RUNNING = "running"                   # 进行中
    # V2五级吉凶
    COMPLETED_DAJI = "daji"               # 大吉 (judgment_level >= 0.8)
    COMPLETED_XIAOJI = "xiaoji"           # 小吉 (0.6 <= judgment_level < 0.8)
    COMPLETED_PING = "ping"               # 平 (0.4 <= judgment_level < 0.6)
    COMPLETED_XIAOXIONG = "xiaoxiong"     # 小凶 (0.2 <= judgment_level < 0.4)
    COMPLETED_DAXIONG = "daxiong"         # 大凶 (judgment_level < 0.2)
    ERROR = "error"                       # 错误

    # 向后兼容别名
    COMPLETED_GOOD = "daji"               # 兼容旧代码
    COMPLETED_BAD = "daxiong"             # 兼容旧代码
    COMPLETED_NEUTRAL = "ping"            # 兼容旧代码


class QuickResultCard(QFrame):
    """快速结论卡片"""

    # 信号：卡片被点击（展开详情）
    clicked = pyqtSignal(str)  # 发送theory_name

    # V2: 五级吉凶颜色配置 - 深色主题
    # 重构：移除圆形图标，改为吉凶等级文字，背景色更鲜明
    STATUS_STYLES_DARK = {
        CardStatus.WAITING: {
            "border": "#4B5563",
            "bg": "#1F2937",
            "label": "",  # 无标签
            "text": "#9CA3AF"
        },
        CardStatus.RUNNING: {
            "border": "#3B82F6",
            "bg": "#1E3A5F",
            "label": "⏳",  # 进行中动画
            "text": "#93C5FD"
        },
        # V2: 五级吉凶 - 鲜明背景色
        CardStatus.COMPLETED_DAJI: {          # 大吉 - 喜庆红
            "border": "#EF4444",
            "bg": "#991B1B",  # 更深的红色背景
            "label": "大吉",
            "text": "#FECACA"
        },
        CardStatus.COMPLETED_XIAOJI: {        # 小吉 - 喜庆橙
            "border": "#F97316",
            "bg": "#9A3412",  # 更深的橙色背景
            "label": "小吉",
            "text": "#FED7AA"
        },
        CardStatus.COMPLETED_PING: {          # 平 - 中性灰
            "border": "#9CA3AF",
            "bg": "#374151",
            "label": "平",
            "text": "#E5E7EB"
        },
        CardStatus.COMPLETED_XIAOXIONG: {     # 小凶 - 暗绿
            "border": "#22C55E",
            "bg": "#14532D",
            "label": "小凶",
            "text": "#BBF7D0"
        },
        CardStatus.COMPLETED_DAXIONG: {       # 大凶 - 深黑
            "border": "#4B5563",
            "bg": "#111827",
            "label": "大凶",
            "text": "#9CA3AF"
        },
        CardStatus.ERROR: {
            "border": "#6B7280",
            "bg": "#1F2937",
            "label": "❌",
            "text": "#9CA3AF"
        },
    }

    # V2: 五级吉凶颜色配置 - 浅色主题（鲜明背景色）
    STATUS_STYLES_LIGHT = {
        CardStatus.WAITING: {
            "border": "#E5E7EB",
            "bg": "#FFFFFF",  # 纯白背景
            "label": "",
            "text": "#6B7280"
        },
        CardStatus.RUNNING: {
            "border": "#3B82F6",
            "bg": "#DBEAFE",  # 浅蓝背景
            "label": "⏳",
            "text": "#1D4ED8"
        },
        # V2: 五级吉凶 - 鲜明背景色
        CardStatus.COMPLETED_DAJI: {          # 大吉 - 喜庆红
            "border": "#EF4444",
            "bg": "#FEE2E2",  # 浅红背景
            "label": "大吉",
            "text": "#B91C1C"
        },
        CardStatus.COMPLETED_XIAOJI: {        # 小吉 - 喜庆橙
            "border": "#F97316",
            "bg": "#FFEDD5",  # 浅橙背景
            "label": "小吉",
            "text": "#C2410C"
        },
        CardStatus.COMPLETED_PING: {          # 平 - 中性灰
            "border": "#9CA3AF",
            "bg": "#F3F4F6",  # 浅灰背景
            "label": "平",
            "text": "#374151"
        },
        CardStatus.COMPLETED_XIAOXIONG: {     # 小凶 - 浅绿
            "border": "#22C55E",
            "bg": "#DCFCE7",  # 浅绿背景
            "label": "小凶",
            "text": "#166534"
        },
        CardStatus.COMPLETED_DAXIONG: {       # 大凶 - 灰黑
            "border": "#4B5563",
            "bg": "#E5E7EB",  # 深灰背景
            "label": "大凶",
            "text": "#1F2937"
        },
        CardStatus.ERROR: {
            "border": "#9CA3AF",
            "bg": "#F3F4F6",
            "label": "❌",
            "text": "#4B5563"
        },
    }

    @classmethod
    def get_status_styles(cls, theme: str = "dark"):
        """根据主题获取状态样式"""
        if theme == "light":
            return cls.STATUS_STYLES_LIGHT
        return cls.STATUS_STYLES_DARK

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
        """应用当前状态的样式（V2重构：整体底色变化）"""
        styles = self.get_status_styles(self.theme)
        style = styles.get(self.status, styles[CardStatus.WAITING])

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

        # V2: 使用 label 替代 icon，显示吉凶等级文字
        label_text = style.get('label', '')
        self.icon_label.setText(label_text)
        self.icon_label.setStyleSheet(f"color: {style['text']}; background: transparent; font-weight: bold;")
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

    def set_theme(self, theme: str):
        """设置主题并重新应用样式"""
        self.theme = theme
        self._apply_style()

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

    def set_completed(self, summary: str, judgment: str, judgment_level: float = 0.5):
        """
        设置为完成状态（V2五级吉凶系统）

        Args:
            summary: 结果摘要
            judgment: 吉凶判断 ('大吉', '小吉', '平', '小凶', '大凶', '吉', '凶')
            judgment_level: 吉凶等级 (0.0-1.0)，用于精确判断
        """
        self._stop_animation()

        self.summary = summary
        self.judgment = judgment

        # V2: 五级吉凶判断
        # 优先使用 judgment_level，其次使用文字判断
        if judgment_level >= 0.8 or judgment in ("大吉", "吉"):
            self.status = CardStatus.COMPLETED_DAJI
        elif judgment_level >= 0.6 or judgment == "小吉":
            self.status = CardStatus.COMPLETED_XIAOJI
        elif judgment_level >= 0.4 or judgment == "平":
            self.status = CardStatus.COMPLETED_PING
        elif judgment_level >= 0.2 or judgment == "小凶":
            self.status = CardStatus.COMPLETED_XIAOXIONG
        else:  # judgment_level < 0.2 or judgment in ("大凶", "凶")
            self.status = CardStatus.COMPLETED_DAXIONG

        # 截断过长的摘要（收起状态显示40字，展开状态显示150字）
        self._expanded = getattr(self, '_expanded', False)
        max_len = 150 if self._expanded else 40
        display_summary = summary[:max_len] + "..." if len(summary) > max_len else summary
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
        """鼠标点击事件 - V2: 展开/收起详情"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_expand()
            self.clicked.emit(self.theory_name)
        super().mousePressEvent(event)

    def toggle_expand(self):
        """V2新增：切换展开/收起状态（仅已完成的理论可展开）"""
        # V2: 只有已完成分析的理论才能展开
        completed_statuses = [
            CardStatus.COMPLETED_DAJI,
            CardStatus.COMPLETED_XIAOJI,
            CardStatus.COMPLETED_PING,
            CardStatus.COMPLETED_XIAOXIONG,
            CardStatus.COMPLETED_DAXIONG,
        ]
        if self.status not in completed_statuses:
            return  # 未分析完成的理论不能展开

        self._expanded = not getattr(self, '_expanded', False)

        if self._expanded:
            # 展开状态：显示完整摘要（最多150字）
            self.setMinimumHeight(100)
            self.setMaximumHeight(150)
            max_len = 150
        else:
            # 收起状态：显示简短摘要（最多40字）
            self.setMinimumHeight(60)
            self.setMaximumHeight(80)
            max_len = 40

        # 重新设置摘要显示
        if self.summary:
            display_summary = self.summary[:max_len] + "..." if len(self.summary) > max_len else self.summary
            self.summary_label.setText(display_summary)

    def is_expanded(self) -> bool:
        """V2新增：获取展开状态"""
        return getattr(self, '_expanded', False)

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

    # V2: 支持的理论列表（新增测字术）
    THEORIES = ["小六壬", "测字术", "八字", "紫微斗数", "奇门遁甲", "大六壬", "六爻", "梅花易数"]

    def __init__(self, theme: str = "dark", parent=None):
        super().__init__(parent)
        self.theme = theme
        self.cards = {}

        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        self.setStyleSheet("background-color: transparent;")

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # 标题 - 根据主题设置颜色
        self.title_label = QLabel("🔮 理论分析进度")
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setWeight(QFont.Weight.Bold)
        self.title_label.setFont(title_font)
        self._apply_title_style()
        layout.addWidget(self.title_label)

        # 创建各理论卡片
        for theory in self.THEORIES:
            card = QuickResultCard(theory, self.theme)
            card.clicked.connect(self._on_card_clicked)
            layout.addWidget(card)
            self.cards[theory] = card

        layout.addStretch()
        self.setLayout(layout)

    def _apply_title_style(self):
        """应用标题样式"""
        title_color = "#1e293b" if self.theme == "light" else "#E2E8F0"
        self.title_label.setStyleSheet(f"color: {title_color}; padding: 4px 0; background: transparent;")

    def set_theme(self, theme: str):
        """设置主题并更新所有卡片"""
        self.theme = theme
        self._apply_title_style()
        for card in self.cards.values():
            card.set_theme(theme)

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
