"""
ReportQADialog - 报告问答对话框

用户可以对当前查看的报告提问，AI基于报告内容回答
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QLabel, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont
from typing import Optional
import asyncio

from ui.widgets.chat_widget import ChatWidget, MessageRole
from services.report_service import ReportService
from models import ComprehensiveReport


class QAWorker(QThread):
    """问答异步工作线程"""
    finished = pyqtSignal(str)  # AI回答
    error = pyqtSignal(str)

    def __init__(self, report_service: ReportService, question: str, report: ComprehensiveReport):
        super().__init__()
        self.report_service = report_service
        self.question = question
        self.report = report

    def run(self):
        """执行异步问答"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            answer = loop.run_until_complete(
                self.report_service.answer_question(self.question, self.report)
            )

            loop.close()

            self.finished.emit(answer)

        except Exception as e:
            self.error.emit(str(e))


class ReportQADialog(QDialog):
    """报告问答对话框"""

    def __init__(self, report: ComprehensiveReport, report_service: ReportService, parent=None):
        super().__init__(parent)
        self.report = report
        self.report_service = report_service
        self._setup_ui()
        self._load_suggested_questions()

    def _setup_ui(self):
        """设置UI"""
        self.setWindowTitle("报告问答")
        self.setMinimumSize(700, 600)

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # 标题
        title_label = QLabel("💬 报告问答")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # 说明文字
        info_label = QLabel("您可以对这份报告提出疑问，AI助手会基于报告内容为您解答。")
        info_label.setStyleSheet("color: #666; font-size: 10pt;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # 建议问题区域
        suggested_frame = QFrame()
        suggested_frame.setFrameShape(QFrame.Shape.Box)
        suggested_frame.setStyleSheet("""
            QFrame {
                background-color: #FFF9E6;
                border: 1px solid #FFE082;
                border-radius: 8px;
            }
        """)

        suggested_layout = QVBoxLayout()
        suggested_layout.setContentsMargins(12, 12, 12, 12)
        suggested_layout.setSpacing(8)

        suggested_title = QLabel("💡 建议的问题（点击快速提问）：")
        suggested_title.setStyleSheet("font-weight: bold; color: #F57C00;")
        suggested_layout.addWidget(suggested_title)

        # 建议问题按钮容器
        self.suggested_buttons_layout = QVBoxLayout()
        self.suggested_buttons_layout.setSpacing(6)
        suggested_layout.addLayout(self.suggested_buttons_layout)

        suggested_frame.setLayout(suggested_layout)
        layout.addWidget(suggested_frame)

        # 聊天消息区域
        self.chat_widget = ChatWidget()
        layout.addWidget(self.chat_widget)

        # 输入区域
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)

        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("在此输入您的问题...")
        self.input_text.setMaximumHeight(80)
        self.input_text.setStyleSheet("""
            QTextEdit {
                border: 2px solid #BBDEFB;
                border-radius: 8px;
                padding: 8px;
                font-size: 10pt;
            }
            QTextEdit:focus {
                border: 2px solid #64B5F6;
            }
        """)
        input_layout.addWidget(self.input_text)

        self.send_btn = QPushButton("发送")
        self.send_btn.setFixedSize(80, 80)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #64B5F6;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 11pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #42A5F5;
            }
            QPushButton:pressed {
                background-color: #2196F3;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
            }
        """)
        self.send_btn.clicked.connect(self._on_send_clicked)
        input_layout.addWidget(self.send_btn)

        layout.addLayout(input_layout)

        # 底部按钮
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()

        export_btn = QPushButton("导出对话")
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #E0E0E0;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #BDBDBD;
            }
        """)
        export_btn.clicked.connect(self._on_export_clicked)
        bottom_layout.addWidget(export_btn)

        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #E0E0E0;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #BDBDBD;
            }
        """)
        close_btn.clicked.connect(self.accept)
        bottom_layout.addWidget(close_btn)

        layout.addLayout(bottom_layout)

        self.setLayout(layout)

        # 欢迎消息
        welcome_msg = f"""
欢迎！我已经阅读了您的分析报告。

**报告概要**：
- 问题类型：{self.report.user_input_summary.get('question_type', '未知')}
- 使用理论：{', '.join(self.report.selected_theories)}
- 综合置信度：{self.report.overall_confidence:.0%}

请随时向我提问，我会基于报告内容为您解答。
"""
        self.chat_widget.add_assistant_message(welcome_msg.strip())

    def _load_suggested_questions(self):
        """加载建议问题"""
        suggested_questions = self.report_service.get_suggested_questions(self.report)

        # 清空现有按钮
        while self.suggested_buttons_layout.count():
            item = self.suggested_buttons_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 创建建议问题按钮
        for question in suggested_questions:
            btn = QPushButton(f"• {question}")
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: none;
                    text-align: left;
                    padding: 4px;
                    color: #1976D2;
                }
                QPushButton:hover {
                    color: #0D47A1;
                    text-decoration: underline;
                }
            """)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, q=question: self._ask_suggested_question(q))
            self.suggested_buttons_layout.addWidget(btn)

    def _ask_suggested_question(self, question: str):
        """点击建议问题"""
        self.input_text.setPlainText(question)
        self._on_send_clicked()

    def _on_send_clicked(self):
        """发送按钮点击"""
        question = self.input_text.toPlainText().strip()

        if not question:
            return

        # 添加用户消息
        self.chat_widget.add_user_message(question)

        # 清空输入框
        self.input_text.clear()

        # 禁用发送按钮
        self.send_btn.setEnabled(False)
        self.send_btn.setText("思考中...")

        # 启动异步问答
        self.worker = QAWorker(self.report_service, question, self.report)
        self.worker.finished.connect(self._on_answer_finished)
        self.worker.error.connect(self._on_answer_error)
        self.worker.start()

    def _on_answer_finished(self, answer: str):
        """回答完成回调"""
        self.chat_widget.add_assistant_message(answer)

        # 恢复发送按钮
        self.send_btn.setEnabled(True)
        self.send_btn.setText("发送")

        # 聚焦到输入框
        self.input_text.setFocus()

    def _on_answer_error(self, error_msg: str):
        """回答失败回调"""
        error_response = f"抱歉，我在思考时遇到了一些问题：{error_msg}\n\n请稍后再试，或换一个问题。"
        self.chat_widget.add_assistant_message(error_response)

        # 恢复发送按钮
        self.send_btn.setEnabled(True)
        self.send_btn.setText("发送")

    def _on_export_clicked(self):
        """导出对话"""
        from PyQt6.QtWidgets import QFileDialog

        # 建议文件名
        filename = f"报告问答_{self.report.report_id[:8]}.md"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出对话",
            filename,
            "Markdown文件 (*.md);;所有文件 (*)"
        )

        if file_path:
            try:
                markdown = self.chat_widget.export_to_markdown()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(markdown)

                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(self, "导出成功", f"对话已导出到：\n{file_path}")

            except Exception as e:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "导出失败", f"导出时出错：{str(e)}")
