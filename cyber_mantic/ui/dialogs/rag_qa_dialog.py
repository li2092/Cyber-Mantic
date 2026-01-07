"""
RAG问答对话框

功能：
- 基于典籍内容的智能问答
- 显示检索来源和引用
- 支持追问和继续对话
"""
from typing import Optional, List
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QTextBrowser, QFrame,
    QMessageBox, QSplitter, QWidget, QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from utils.logger import get_logger
from utils.rag_manager import get_rag_manager, RetrievalResult


class RAGWorker(QThread):
    """RAG问答工作线程"""
    finished = pyqtSignal(str, list)  # (answer, sources)
    error = pyqtSignal(str)

    def __init__(self, question: str, api_manager, context: str = "", parent=None):
        super().__init__(parent)
        self.question = question
        self.api_manager = api_manager
        self.context = context  # 可选的额外上下文（如选中的文本）

    def run(self):
        """执行问答"""
        try:
            rag_manager = get_rag_manager()

            # 如果有额外上下文，将其与问题结合
            query = self.question
            if self.context:
                query = f"关于这段内容：{self.context[:500]}...\n\n问题：{self.question}"

            answer, results = rag_manager.answer_question(
                query,
                self.api_manager,
                top_k=3
            )
            self.finished.emit(answer, results)
        except Exception as e:
            self.error.emit(str(e))


class RAGQADialog(QDialog):
    """RAG问答对话框"""

    def __init__(self, api_manager, selected_text: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("典籍问答")
        self.setMinimumSize(800, 600)

        self.logger = get_logger(__name__)
        self._api_manager = api_manager
        self._selected_text = selected_text
        self._worker: Optional[RAGWorker] = None
        self._current_sources: List[RetrievalResult] = []

        self._init_ui()

        # 如果有选中文本，显示上下文
        if selected_text:
            self._context_display.setText(selected_text)
            self._context_frame.setVisible(True)
        else:
            self._context_frame.setVisible(False)

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 标题
        title_label = QLabel("📚 典籍智能问答")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # 说明
        info_label = QLabel("基于典籍内容回答您的问题，答案会标注引用来源")
        info_label.setStyleSheet("color: #666; font-size: 13px;")
        layout.addWidget(info_label)

        # 选中内容上下文（可选）
        self._context_frame = QFrame()
        self._context_frame.setStyleSheet("""
            QFrame {
                background-color: #fff9e6;
                border: 1px solid #ffd54f;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        context_layout = QVBoxLayout(self._context_frame)
        context_layout.setContentsMargins(10, 10, 10, 10)

        context_header = QLabel("📌 选中的内容：")
        context_header.setStyleSheet("font-weight: bold; color: #f57c00;")
        context_layout.addWidget(context_header)

        self._context_display = QLabel()
        self._context_display.setWordWrap(True)
        self._context_display.setStyleSheet("color: #555;")
        context_layout.addWidget(self._context_display)

        layout.addWidget(self._context_frame)

        # 主内容区：分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧：问答区
        left_panel = self._create_qa_panel()
        splitter.addWidget(left_panel)

        # 右侧：来源引用
        right_panel = self._create_sources_panel()
        splitter.addWidget(right_panel)

        splitter.setSizes([500, 300])
        layout.addWidget(splitter, 1)

        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 25px;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
            }
        """)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def _create_qa_panel(self) -> QWidget:
        """创建问答面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 10, 0)

        # 问题输入
        question_label = QLabel("您的问题：")
        question_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(question_label)

        self._question_edit = QTextEdit()
        self._question_edit.setMaximumHeight(100)
        self._question_edit.setPlaceholderText("请输入您想了解的问题，如：什么是八字？天干地支的含义是什么？")
        self._question_edit.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        layout.addWidget(self._question_edit)

        # 提问按钮
        ask_layout = QHBoxLayout()
        ask_layout.addStretch()

        self._ask_btn = QPushButton("🔍 搜索并回答")
        self._ask_btn.clicked.connect(self._on_ask)
        self._ask_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 25px;
                border: none;
                border-radius: 5px;
                background-color: #1976d2;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        ask_layout.addWidget(self._ask_btn)
        layout.addLayout(ask_layout)

        # 状态提示
        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: #1976d2; font-size: 12px;")
        layout.addWidget(self._status_label)

        # 答案显示
        answer_label = QLabel("答案：")
        answer_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(answer_label)

        self._answer_browser = QTextBrowser()
        self._answer_browser.setStyleSheet("""
            QTextBrowser {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 15px;
                background-color: #fafafa;
            }
        """)
        self._answer_browser.setPlaceholderText("答案将显示在这里...")
        layout.addWidget(self._answer_browser, 1)

        return panel

    def _create_sources_panel(self) -> QWidget:
        """创建来源引用面板"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
        """)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)

        # 标题
        sources_label = QLabel("📖 引用来源")
        sources_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(sources_label)

        # 来源列表
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)

        self._sources_container = QWidget()
        self._sources_layout = QVBoxLayout(self._sources_container)
        self._sources_layout.setSpacing(10)
        self._sources_layout.addStretch()

        scroll.setWidget(self._sources_container)
        layout.addWidget(scroll, 1)

        return panel

    def _on_ask(self):
        """提问"""
        question = self._question_edit.toPlainText().strip()

        if not question:
            QMessageBox.information(self, "提示", "请输入您的问题")
            return

        if not self._api_manager:
            QMessageBox.warning(self, "提示", "请先在设置中配置AI接口")
            return

        # 禁用按钮
        self._ask_btn.setEnabled(False)
        self._status_label.setText("正在搜索相关内容...")
        self._answer_browser.setPlainText("")

        # 清空来源
        self._clear_sources()

        # 启动工作线程
        self._worker = RAGWorker(
            question,
            self._api_manager,
            context=self._selected_text,
            parent=self
        )
        self._worker.finished.connect(self._on_answer_finished)
        self._worker.error.connect(self._on_answer_error)
        self._worker.start()

    def _on_answer_finished(self, answer: str, sources: List[RetrievalResult]):
        """回答完成"""
        self._ask_btn.setEnabled(True)
        self._status_label.setText("")

        # 显示答案
        self._answer_browser.setMarkdown(answer)

        # 显示来源
        self._current_sources = sources
        self._display_sources(sources)

    def _on_answer_error(self, error_msg: str):
        """回答出错"""
        self._ask_btn.setEnabled(True)
        self._status_label.setText("")

        QMessageBox.warning(self, "错误", f"生成回答时出错：\n{error_msg}")

    def _clear_sources(self):
        """清空来源显示"""
        while self._sources_layout.count() > 1:  # 保留stretch
            item = self._sources_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _display_sources(self, sources: List[RetrievalResult]):
        """显示来源引用"""
        self._clear_sources()

        if not sources:
            no_source_label = QLabel("未找到相关来源")
            no_source_label.setStyleSheet("color: #999;")
            self._sources_layout.insertWidget(0, no_source_label)
            return

        for i, result in enumerate(sources):
            source_frame = QFrame()
            source_frame.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border: 1px solid #e0e0e0;
                    border-radius: 5px;
                    padding: 10px;
                }
            """)

            source_layout = QVBoxLayout(source_frame)
            source_layout.setSpacing(5)

            # 来源标题
            title_label = QLabel(f"📄 {result.chunk.document_title}")
            title_label.setStyleSheet("font-weight: bold; color: #1976d2;")
            source_layout.addWidget(title_label)

            # 分类
            if result.chunk.category:
                category_label = QLabel(f"分类：{result.chunk.category}")
                category_label.setStyleSheet("color: #888; font-size: 11px;")
                source_layout.addWidget(category_label)

            # 内容预览
            preview = result.chunk.content[:200] + "..." if len(result.chunk.content) > 200 else result.chunk.content
            content_label = QLabel(preview)
            content_label.setWordWrap(True)
            content_label.setStyleSheet("color: #555; font-size: 12px;")
            source_layout.addWidget(content_label)

            # 匹配分数
            score_label = QLabel(f"相关度: {result.score:.2f}")
            score_label.setStyleSheet("color: #888; font-size: 11px;")
            source_layout.addWidget(score_label)

            self._sources_layout.insertWidget(i, source_frame)
