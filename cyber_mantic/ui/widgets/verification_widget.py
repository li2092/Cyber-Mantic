"""
VerificationWidget - 验证问题展示组件

V2核心组件：在对话中展示验证问题，收集用户答案
支持多种问题类型：是/否、年份选择、事件描述
"""

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QButtonGroup, QRadioButton, QLineEdit, QWidget, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from typing import List, Optional, Callable
from core.dynamic_verification import VerificationQuestion, VerificationResult


class SingleQuestionWidget(QFrame):
    """单个验证问题组件"""

    # 信号：用户回答了问题
    answered = pyqtSignal(int, str)  # (question_index, answer)

    def __init__(
        self,
        question: VerificationQuestion,
        index: int,
        theme: str = "dark",
        parent=None
    ):
        super().__init__(parent)
        self.question = question
        self.index = index
        self.theme = theme
        self._answer = None

        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        is_dark = self.theme == "dark"

        # 样式配置
        bg_color = "#2D2D3A" if is_dark else "#F8FAFC"
        text_color = "#E2E8F0" if is_dark else "#1E293B"
        border_color = "#4B5563" if is_dark else "#E2E8F0"
        accent_color = "#8B5CF6"

        self.setObjectName("verificationQuestion")
        self.setStyleSheet(f"""
            QFrame#verificationQuestion {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 12px;
                padding: 8px;
            }}
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # 问题序号和文本
        question_layout = QHBoxLayout()
        question_layout.setSpacing(8)

        # 序号标签
        index_label = QLabel(f"Q{self.index + 1}")
        index_label.setFixedWidth(32)
        index_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        index_label.setStyleSheet(f"""
            background-color: {accent_color};
            color: white;
            border-radius: 16px;
            font-weight: bold;
            font-size: 12px;
            padding: 4px;
        """)
        question_layout.addWidget(index_label)

        # 问题文本
        question_label = QLabel(self.question.question)
        question_label.setWordWrap(True)
        question_label.setStyleSheet(f"color: {text_color}; font-size: 14px;")
        question_layout.addWidget(question_label, 1)

        layout.addLayout(question_layout)

        # 根据问题类型显示不同的答题控件
        if self.question.question_type == "yes_no":
            self._setup_yes_no_buttons(layout, is_dark)
        elif self.question.question_type == "year":
            self._setup_year_input(layout, is_dark)
        elif self.question.question_type == "choice":
            self._setup_choice_buttons(layout, is_dark)
        else:
            self._setup_text_input(layout, is_dark)

        self.setLayout(layout)

    def _setup_yes_no_buttons(self, layout: QVBoxLayout, is_dark: bool):
        """设置是/否按钮"""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)

        btn_style = self._get_button_style(is_dark)

        self.yes_btn = QPushButton("✓ 是")
        self.yes_btn.setStyleSheet(btn_style)
        self.yes_btn.setCheckable(True)
        self.yes_btn.clicked.connect(lambda: self._on_answer("是"))
        button_layout.addWidget(self.yes_btn)

        self.no_btn = QPushButton("✗ 否")
        self.no_btn.setStyleSheet(btn_style)
        self.no_btn.setCheckable(True)
        self.no_btn.clicked.connect(lambda: self._on_answer("否"))
        button_layout.addWidget(self.no_btn)

        self.skip_btn = QPushButton("跳过")
        self.skip_btn.setStyleSheet(self._get_skip_button_style(is_dark))
        self.skip_btn.clicked.connect(lambda: self._on_answer("跳过"))
        button_layout.addWidget(self.skip_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

    def _setup_year_input(self, layout: QVBoxLayout, is_dark: bool):
        """设置年份输入"""
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)

        self.year_input = QLineEdit()
        self.year_input.setPlaceholderText("请输入年份，如：2023")
        self.year_input.setMaximumWidth(150)
        self.year_input.setStyleSheet(self._get_input_style(is_dark))
        input_layout.addWidget(self.year_input)

        submit_btn = QPushButton("确认")
        submit_btn.setStyleSheet(self._get_button_style(is_dark))
        submit_btn.clicked.connect(lambda: self._on_answer(self.year_input.text()))
        input_layout.addWidget(submit_btn)

        skip_btn = QPushButton("跳过")
        skip_btn.setStyleSheet(self._get_skip_button_style(is_dark))
        skip_btn.clicked.connect(lambda: self._on_answer("跳过"))
        input_layout.addWidget(skip_btn)

        input_layout.addStretch()
        layout.addLayout(input_layout)

    def _setup_choice_buttons(self, layout: QVBoxLayout, is_dark: bool):
        """设置选择题按钮"""
        choices = self.question.expected_answers if self.question.expected_answers else ["选项A", "选项B", "选项C"]

        for choice in choices:
            btn = QPushButton(choice)
            btn.setStyleSheet(self._get_button_style(is_dark))
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, c=choice: self._on_answer(c))
            layout.addWidget(btn)

        skip_btn = QPushButton("跳过")
        skip_btn.setStyleSheet(self._get_skip_button_style(is_dark))
        skip_btn.clicked.connect(lambda: self._on_answer("跳过"))
        layout.addWidget(skip_btn)

    def _setup_text_input(self, layout: QVBoxLayout, is_dark: bool):
        """设置文本输入"""
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)

        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("请输入您的答案...")
        self.text_input.setStyleSheet(self._get_input_style(is_dark))
        input_layout.addWidget(self.text_input, 1)

        submit_btn = QPushButton("确认")
        submit_btn.setStyleSheet(self._get_button_style(is_dark))
        submit_btn.clicked.connect(lambda: self._on_answer(self.text_input.text()))
        input_layout.addWidget(submit_btn)

        skip_btn = QPushButton("跳过")
        skip_btn.setStyleSheet(self._get_skip_button_style(is_dark))
        skip_btn.clicked.connect(lambda: self._on_answer("跳过"))
        input_layout.addWidget(skip_btn)

        layout.addLayout(input_layout)

    def _get_button_style(self, is_dark: bool) -> str:
        """获取按钮样式"""
        bg = "#3B3B4F" if is_dark else "#E2E8F0"
        bg_hover = "#4B4B5F" if is_dark else "#CBD5E1"
        bg_checked = "#8B5CF6"
        text = "#E2E8F0" if is_dark else "#1E293B"

        return f"""
            QPushButton {{
                background-color: {bg};
                color: {text};
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {bg_hover};
            }}
            QPushButton:checked {{
                background-color: {bg_checked};
                color: white;
            }}
        """

    def _get_skip_button_style(self, is_dark: bool) -> str:
        """获取跳过按钮样式"""
        text = "#94A3B8" if is_dark else "#64748B"

        return f"""
            QPushButton {{
                background-color: transparent;
                color: {text};
                border: 1px solid {text};
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: rgba(148, 163, 184, 0.1);
            }}
        """

    def _get_input_style(self, is_dark: bool) -> str:
        """获取输入框样式"""
        bg = "#1E1E2E" if is_dark else "#FFFFFF"
        text = "#E2E8F0" if is_dark else "#1E293B"
        border = "#4B5563" if is_dark else "#E2E8F0"

        return f"""
            QLineEdit {{
                background-color: {bg};
                color: {text};
                border: 1px solid {border};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border-color: #8B5CF6;
            }}
        """

    def _on_answer(self, answer: str):
        """处理用户答案"""
        self._answer = answer
        self.answered.emit(self.index, answer)

        # 禁用控件，显示已回答状态
        self.setEnabled(False)
        self.setStyleSheet(self.styleSheet() + "opacity: 0.7;")

    def get_answer(self) -> Optional[str]:
        """获取用户答案"""
        return self._answer


class VerificationPanel(QFrame):
    """验证问题面板 - 包含多个验证问题"""

    # 信号：所有问题已回答
    all_answered = pyqtSignal(VerificationResult)
    # 信号：单个问题已回答
    question_answered = pyqtSignal(int, str, bool)  # (index, answer, is_verified)

    def __init__(
        self,
        questions: List[VerificationQuestion],
        theme: str = "dark",
        parent=None
    ):
        super().__init__(parent)
        self.questions = questions
        self.theme = theme
        self.question_widgets: List[SingleQuestionWidget] = []
        self.result = VerificationResult(questions)

        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        is_dark = self.theme == "dark"

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # 标题
        title_label = QLabel("🔍 回溯验证")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setWeight(QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {'#C4B5FD' if is_dark else '#7C3AED'}; margin-bottom: 4px;")
        layout.addWidget(title_label)

        # 说明文本
        desc_label = QLabel("请回答以下问题，帮助我们验证分析的准确性：")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"color: {'#94A3B8' if is_dark else '#64748B'}; font-size: 12px; margin-bottom: 8px;")
        layout.addWidget(desc_label)

        # 问题列表
        for i, question in enumerate(self.questions):
            widget = SingleQuestionWidget(question, i, self.theme)
            widget.answered.connect(self._on_question_answered)
            self.question_widgets.append(widget)
            layout.addWidget(widget)

        # 底部提示
        tip_label = QLabel("💡 您的回答将帮助我们改进分析准确性")
        tip_label.setStyleSheet(f"color: {'#6B7280' if is_dark else '#9CA3AF'}; font-size: 11px; font-style: italic;")
        layout.addWidget(tip_label)

        self.setLayout(layout)

    def _on_question_answered(self, index: int, answer: str):
        """处理问题回答"""
        if answer == "跳过":
            # 跳过的问题不计入验证
            self.questions[index].user_answer = None
            self.questions[index].is_verified = None
        else:
            # 评估答案
            from core.dynamic_verification import DynamicVerificationGenerator
            generator = DynamicVerificationGenerator()
            is_verified = generator.evaluate_answer(self.questions[index], answer)

            self.result.update_answer(index, answer, is_verified)
            self.question_answered.emit(index, answer, is_verified)

        # 检查是否所有问题都已回答
        answered_count = sum(1 for w in self.question_widgets if w.get_answer() is not None)
        if answered_count == len(self.questions):
            self.all_answered.emit(self.result)

    def get_result(self) -> VerificationResult:
        """获取验证结果"""
        return self.result


class VerificationBubble(QFrame):
    """验证问题气泡 - 用于在聊天中显示"""

    # 信号：验证完成
    verification_completed = pyqtSignal(VerificationResult)

    def __init__(
        self,
        questions: List[VerificationQuestion],
        theme: str = "dark",
        parent=None
    ):
        super().__init__(parent)
        self.questions = questions
        self.theme = theme

        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        is_dark = self.theme == "dark"

        # 整体样式
        bg_color = "#2D2D3A" if is_dark else "#FFFFFF"
        border_color = "#6366F1"

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 16px;
            }}
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(0)

        # 验证面板
        self.panel = VerificationPanel(self.questions, self.theme)
        self.panel.all_answered.connect(self._on_all_answered)
        layout.addWidget(self.panel)

        self.setLayout(layout)

    def _on_all_answered(self, result: VerificationResult):
        """所有问题回答完成"""
        self.verification_completed.emit(result)

    def get_result(self) -> VerificationResult:
        """获取验证结果"""
        return self.panel.get_result()
