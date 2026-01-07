"""
TermExplainSidebar - 术语解释侧边栏

点击报告中带下划线的术语后，在侧边栏显示解释
支持专业解释+通俗解释的结构
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea,
    QPushButton, QFrame, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont
from typing import Optional, Tuple
import asyncio

from services.report_service import ReportService
from models import ComprehensiveReport


class ExplainWorker(QThread):
    """术语解释异步工作线程"""
    finished = pyqtSignal(str, str)  # (professional_explain, simple_explain)
    error = pyqtSignal(str)

    def __init__(self, report_service: ReportService, term: str, report: Optional[ComprehensiveReport]):
        super().__init__()
        self.report_service = report_service
        self.term = term
        self.report = report

    def run(self):
        """执行异步解释"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # 调用AI获取解释
            explanation = loop.run_until_complete(
                self.report_service.explain_term(self.term, self.report)
            )

            loop.close()

            # 解析专业+通俗解释
            professional, simple = self._parse_explanation(explanation)

            self.finished.emit(professional, simple)

        except Exception as e:
            self.error.emit(str(e))

    def _parse_explanation(self, explanation: str) -> Tuple[str, str]:
        """
        解析AI返回的解释，分离专业和通俗部分

        Args:
            explanation: AI返回的完整解释

        Returns:
            (专业解释, 通俗解释)
        """
        # 尝试分离专业和通俗解释
        # 如果AI返回包含标记，则分离；否则全部作为通俗解释

        if "【专业】" in explanation and "【通俗】" in explanation:
            parts = explanation.split("【通俗】")
            professional = parts[0].replace("【专业】", "").strip()
            simple = parts[1].strip() if len(parts) > 1 else ""
        elif "专业解释" in explanation and "通俗解释" in explanation:
            parts = explanation.split("通俗解释")
            professional = parts[0].replace("专业解释", "").replace("：", "").strip()
            simple = parts[1].replace("：", "").strip() if len(parts) > 1 else ""
        else:
            # 没有明确分离，使用默认策略
            # 前半部分作为专业解释，后半部分作为通俗解释
            lines = explanation.split("。")
            if len(lines) >= 2:
                mid = len(lines) // 2
                professional = "。".join(lines[:mid]) + "。"
                simple = "。".join(lines[mid:])
            else:
                professional = ""
                simple = explanation

        return professional, simple


class TermExplainSidebar(QWidget):
    """术语解释侧边栏"""

    # 信号：关闭侧边栏
    closed = pyqtSignal()

    def __init__(self, report_service: ReportService, parent=None):
        super().__init__(parent)
        self.report_service = report_service
        self.current_report: Optional[ComprehensiveReport] = None
        self.current_term = ""
        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # 顶部工具栏
        toolbar_layout = QVBoxLayout()
        toolbar_layout.setSpacing(8)

        # 标题
        title_label = QLabel("📖 术语解释")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        toolbar_layout.addWidget(title_label)

        # 当前术语
        self.term_label = QLabel("")
        term_font = QFont()
        term_font.setPointSize(12)
        self.term_label.setFont(term_font)
        self.term_label.setStyleSheet("color: #2E5266; font-weight: bold;")
        toolbar_layout.addWidget(self.term_label)

        layout.addLayout(toolbar_layout)

        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #E0E0E0;")
        layout.addWidget(separator)

        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameStyle(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # 内容容器
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)

        # 专业解释区域
        professional_label = QLabel("📚 专业解释")
        prof_font = QFont()
        prof_font.setPointSize(11)
        prof_font.setBold(True)
        professional_label.setFont(prof_font)
        professional_label.setStyleSheet("color: #5E9EA0;")
        content_layout.addWidget(professional_label)

        self.professional_text = QTextEdit()
        self.professional_text.setReadOnly(True)
        self.professional_text.setFrameStyle(QFrame.Shape.Box)
        self.professional_text.setStyleSheet("""
            QTextEdit {
                background-color: #F0F8FF;
                border: 1px solid #BBDEFB;
                border-radius: 8px;
                padding: 12px;
                font-size: 10pt;
                line-height: 1.6;
            }
        """)
        self.professional_text.setMinimumHeight(120)
        content_layout.addWidget(self.professional_text)

        # 通俗解释区域
        simple_label = QLabel("💡 通俗解释")
        simple_font = QFont()
        simple_font.setPointSize(11)
        simple_font.setBold(True)
        simple_label.setFont(simple_font)
        simple_label.setStyleSheet("color: #81C784;")
        content_layout.addWidget(simple_label)

        self.simple_text = QTextEdit()
        self.simple_text.setReadOnly(True)
        self.simple_text.setFrameStyle(QFrame.Shape.Box)
        self.simple_text.setStyleSheet("""
            QTextEdit {
                background-color: #F1F8E9;
                border: 1px solid #C8E6C9;
                border-radius: 8px;
                padding: 12px;
                font-size: 10pt;
                line-height: 1.6;
            }
        """)
        self.simple_text.setMinimumHeight(120)
        content_layout.addWidget(self.simple_text)

        # 加载提示
        self.loading_label = QLabel("⏳ 正在查询解释...")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setStyleSheet("color: #999; font-size: 10pt;")
        self.loading_label.hide()
        content_layout.addWidget(self.loading_label)

        content_layout.addStretch()

        content_widget.setLayout(content_layout)
        scroll_area.setWidget(content_widget)

        layout.addWidget(scroll_area)

        # 底部按钮
        button_layout = QVBoxLayout()
        button_layout.setSpacing(8)

        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close_sidebar)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #E0E0E0;
                border: none;
                border-radius: 6px;
                padding: 10px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #BDBDBD;
            }
        """)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

        # 整体样式
        self.setStyleSheet("""
            TermExplainSidebar {
                background-color: white;
                border-left: 2px solid #E0E0E0;
            }
        """)

        # 设置固定宽度
        self.setFixedWidth(350)

    def explain_term(self, term: str, report: Optional[ComprehensiveReport] = None):
        """
        解释术语

        Args:
            term: 术语名称
            report: 报告上下文（可选）
        """
        self.current_term = term
        self.current_report = report
        self.term_label.setText(f"「{term}」")

        # 显示加载状态
        self.loading_label.show()
        self.professional_text.hide()
        self.simple_text.hide()

        # 启动异步解释
        self.worker = ExplainWorker(self.report_service, term, report)
        self.worker.finished.connect(self._on_explain_finished)
        self.worker.error.connect(self._on_explain_error)
        self.worker.start()

    def _on_explain_finished(self, professional: str, simple: str):
        """解释完成回调"""
        self.loading_label.hide()
        self.professional_text.show()
        self.simple_text.show()

        # 设置解释内容
        if professional:
            self.professional_text.setPlainText(professional)
        else:
            self.professional_text.setPlainText("（暂无专业解释）")

        if simple:
            self.simple_text.setPlainText(simple)
        else:
            self.simple_text.setPlainText("（暂无通俗解释）")

    def _on_explain_error(self, error_msg: str):
        """解释失败回调"""
        self.loading_label.hide()
        self.professional_text.show()
        self.simple_text.show()

        self.professional_text.setPlainText("解释获取失败")
        self.simple_text.setPlainText(f"错误信息：{error_msg}")

    def close_sidebar(self):
        """关闭侧边栏"""
        self.closed.emit()
        self.hide()

    def set_report_context(self, report: ComprehensiveReport):
        """设置报告上下文"""
        self.current_report = report
