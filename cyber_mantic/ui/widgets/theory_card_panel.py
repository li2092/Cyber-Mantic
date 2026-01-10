"""
TheoryCardPanel - 理论分析卡片面板

显示8种术数理论的分析状态：
- 初始状态：浅灰色
- 分析中：蓝色边框动画
- 分析完成：根据吉凶显示不同颜色
  - 大凶：深黑色
  - 小凶：深绿色
  - 平：浅灰色
  - 小吉：喜庆橙色
  - 大吉：喜庆红色

点击显示详细分析结果
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGridLayout, QPushButton, QToolTip
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QTimer
from PyQt6.QtGui import QCursor, QFont
from typing import Optional, Dict
from enum import Enum


class TheoryStatus(Enum):
    """理论状态"""
    PENDING = "pending"      # 待分析（浅灰）
    ANALYZING = "analyzing"  # 分析中（蓝色边框）
    COMPLETED = "completed"  # 已完成（根据吉凶显示颜色）
    ERROR = "error"          # 错误（红色边框）


class JudgmentLevel(Enum):
    """吉凶级别"""
    DA_XIONG = "大凶"   # 深黑背景
    XIAO_XIONG = "小凶"  # 深绿背景
    PING = "平"         # 浅灰背景
    XIAO_JI = "小吉"    # 喜庆橙背景
    DA_JI = "大吉"      # 喜庆红背景


class TheoryCard(QPushButton):
    """单个理论卡片"""

    # 吉凶颜色映射
    JUDGMENT_COLORS = {
        JudgmentLevel.DA_XIONG: {
            "bg": "#1F2937",      # 深灰黑
            "text": "#F9FAFB",    # 亮白
            "border": "#374151",
        },
        JudgmentLevel.XIAO_XIONG: {
            "bg": "#064E3B",      # 深绿
            "text": "#D1FAE5",    # 浅绿
            "border": "#065F46",
        },
        JudgmentLevel.PING: {
            "bg": "#F3F4F6",      # 浅灰
            "text": "#4B5563",    # 深灰
            "border": "#E5E7EB",
        },
        JudgmentLevel.XIAO_JI: {
            "bg": "#EA580C",      # 喜庆橙
            "text": "#FFFFFF",    # 白色
            "border": "#C2410C",
        },
        JudgmentLevel.DA_JI: {
            "bg": "#DC2626",      # 喜庆红
            "text": "#FFFFFF",    # 白色
            "border": "#B91C1C",
        },
    }

    # 理论图标
    THEORY_ICONS = {
        "小六壬": "🎲",
        "测字术": "✍️",
        "八字": "📅",
        "紫微斗数": "⭐",
        "奇门遁甲": "🧭",
        "大六壬": "📊",
        "六爻": "☰",
        "梅花易数": "🌸",
    }

    clicked_with_data = pyqtSignal(str, dict)  # theory_name, result_data

    def __init__(self, theory_name: str, theme: str = "light", parent=None):
        super().__init__(parent)
        self.theory_name = theory_name
        self.theme = theme
        self.status = TheoryStatus.PENDING
        self.judgment: Optional[JudgmentLevel] = None
        self.result_data: Dict = {}
        self.summary_text: str = ""

        self._setup_ui()
        self._apply_style()

        self.clicked.connect(self._on_clicked)

    def _setup_ui(self):
        """设置UI"""
        self.setFixedHeight(36)
        self.setMinimumWidth(120)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        # 显示理论名称和图标
        icon = self.THEORY_ICONS.get(self.theory_name, "🔮")
        self.setText(f"{icon} {self.theory_name}")

        font = QFont("Microsoft YaHei", 9)
        font.setBold(True)
        self.setFont(font)

    def set_status(self, status: TheoryStatus):
        """设置状态"""
        self.status = status
        self._apply_style()

    def set_result(self, judgment_text: str, summary: str, data: dict = None):
        """设置分析结果"""
        self.status = TheoryStatus.COMPLETED
        self.summary_text = summary
        self.result_data = data or {}

        # 解析吉凶级别
        if "大凶" in judgment_text:
            self.judgment = JudgmentLevel.DA_XIONG
        elif "小凶" in judgment_text or "凶" in judgment_text:
            self.judgment = JudgmentLevel.XIAO_XIONG
        elif "大吉" in judgment_text:
            self.judgment = JudgmentLevel.DA_JI
        elif "小吉" in judgment_text or "吉" in judgment_text:
            self.judgment = JudgmentLevel.XIAO_JI
        else:
            self.judgment = JudgmentLevel.PING

        self._apply_style()

    def set_error(self):
        """设置错误状态"""
        self.status = TheoryStatus.ERROR
        self._apply_style()

    def set_theme(self, theme: str):
        """设置主题"""
        self.theme = theme
        self._apply_style()

    def _apply_style(self):
        """应用样式"""
        is_dark = self.theme == "dark"

        if self.status == TheoryStatus.PENDING:
            # 待分析 - 淡蓝紫色调，与"平"的浅灰区分
            if is_dark:
                bg, text, border = "#1E1B4B", "#A5B4FC", "#3730A3"  # 深紫蓝底
            else:
                bg, text, border = "#EEF2FF", "#4338CA", "#C7D2FE"  # 浅紫蓝底
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg};
                    color: {text};
                    border: 1px solid {border};
                    border-radius: 6px;
                    padding: 6px 10px;
                    text-align: left;
                }}
                QPushButton:hover {{
                    border-color: #6366F1;
                    background-color: {"#312E81" if is_dark else "#E0E7FF"};
                }}
            """)

        elif self.status == TheoryStatus.ANALYZING:
            # 分析中 - 蓝色边框脉冲
            self.setStyleSheet("""
                QPushButton {
                    background-color: #EEF2FF;
                    color: #4F46E5;
                    border: 2px solid #6366F1;
                    border-radius: 6px;
                    padding: 6px 10px;
                    text-align: left;
                }
            """)
            icon = self.THEORY_ICONS.get(self.theory_name, "🔮")
            self.setText(f"⏳ {self.theory_name} 分析中...")

        elif self.status == TheoryStatus.COMPLETED and self.judgment:
            # 完成 - 根据吉凶显示颜色
            colors = self.JUDGMENT_COLORS.get(self.judgment, self.JUDGMENT_COLORS[JudgmentLevel.PING])
            bg, text, border = colors["bg"], colors["text"], colors["border"]

            # 显示简短结果
            icon = self.THEORY_ICONS.get(self.theory_name, "🔮")
            short_summary = self.summary_text[:10] + "..." if len(self.summary_text) > 10 else self.summary_text
            self.setText(f"{icon} {self.theory_name}  {short_summary}")

            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg};
                    color: {text};
                    border: 1px solid {border};
                    border-radius: 6px;
                    padding: 6px 10px;
                    text-align: left;
                }}
                QPushButton:hover {{
                    opacity: 0.9;
                    border-color: #6366F1;
                }}
            """)

        elif self.status == TheoryStatus.ERROR:
            # 错误 - 红色边框
            self.setStyleSheet("""
                QPushButton {
                    background-color: #FEF2F2;
                    color: #991B1B;
                    border: 1px solid #F87171;
                    border-radius: 6px;
                    padding: 6px 10px;
                    text-align: left;
                }
            """)
            icon = self.THEORY_ICONS.get(self.theory_name, "🔮")
            self.setText(f"❌ {self.theory_name} 失败")

    def _on_clicked(self):
        """点击处理"""
        self.clicked_with_data.emit(self.theory_name, self.result_data)
        self._show_details()

    def _show_details(self):
        """显示详细信息"""
        if self.status == TheoryStatus.COMPLETED:
            detail_text = f"【{self.theory_name}】\n\n"
            if self.judgment:
                detail_text += f"判断: {self.judgment.value}\n\n"
            if self.summary_text:
                detail_text += f"分析: {self.summary_text}\n"
            if self.result_data:
                # 添加更多详细信息
                for key, value in self.result_data.items():
                    if key not in ['summary', 'judgment'] and value:
                        detail_text += f"\n{key}: {value}"
        elif self.status == TheoryStatus.ANALYZING:
            detail_text = f"【{self.theory_name}】\n\n正在分析中，请稍候..."
        elif self.status == TheoryStatus.ERROR:
            detail_text = f"【{self.theory_name}】\n\n分析失败，请重试"
        else:
            detail_text = f"【{self.theory_name}】\n\n等待分析..."

        global_pos = self.mapToGlobal(QPoint(self.width() // 2, self.height()))
        QToolTip.showText(global_pos, detail_text, self, self.rect(), 10000)

    def reset(self):
        """重置状态"""
        self.status = TheoryStatus.PENDING
        self.judgment = None
        self.result_data = {}
        self.summary_text = ""
        icon = self.THEORY_ICONS.get(self.theory_name, "🔮")
        self.setText(f"{icon} {self.theory_name}")
        self._apply_style()


class TheoryCardPanel(QFrame):
    """理论分析卡片面板"""

    theory_clicked = pyqtSignal(str, dict)  # theory_name, result_data

    # 所有支持的理论
    THEORIES = ["小六壬", "测字术", "八字", "紫微斗数", "奇门遁甲", "大六壬", "六爻", "梅花易数"]

    def __init__(self, theme: str = "light", parent=None):
        super().__init__(parent)
        self.theme = theme
        self.theory_cards: Dict[str, TheoryCard] = {}

        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {"#FFFFFF" if self.theme == "light" else "#1E293B"};
                border: 1px solid {"#E5E7EB" if self.theme == "light" else "#374151"};
                border-radius: 8px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        # 标题
        title = QLabel("🔮 理论分析")
        title.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {'#1E293B' if self.theme == 'light' else '#F1F5F9'}; background: transparent; border: none;")
        layout.addWidget(title)

        # 卡片网格 - 2列布局
        grid = QGridLayout()
        grid.setSpacing(6)

        for i, theory in enumerate(self.THEORIES):
            card = TheoryCard(theory, self.theme)
            card.clicked_with_data.connect(self._on_card_clicked)
            self.theory_cards[theory] = card
            grid.addWidget(card, i // 2, i % 2)

        layout.addLayout(grid)

    def set_theme(self, theme: str):
        """设置主题"""
        self.theme = theme
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {"#FFFFFF" if theme == "light" else "#1E293B"};
                border: 1px solid {"#E5E7EB" if theme == "light" else "#374151"};
                border-radius: 8px;
            }}
        """)
        for card in self.theory_cards.values():
            card.set_theme(theme)

    def update_theory_status(self, theory_name: str, status: str, data: dict = None):
        """
        更新理论状态

        Args:
            theory_name: 理论名称
            status: 状态 ('started', 'completed', 'error')
            data: 结果数据 (包含 judgment, summary 等)
        """
        if theory_name not in self.theory_cards:
            return

        card = self.theory_cards[theory_name]

        if status == 'started':
            card.set_status(TheoryStatus.ANALYZING)
        elif status == 'completed':
            judgment = data.get('judgment', '平') if data else '平'
            summary = data.get('summary', '') if data else ''
            card.set_result(judgment, summary, data)
        elif status == 'error':
            card.set_error()

    def reset_all(self):
        """重置所有卡片"""
        for card in self.theory_cards.values():
            card.reset()

    def _on_card_clicked(self, theory_name: str, data: dict):
        """卡片点击"""
        self.theory_clicked.emit(theory_name, data)
