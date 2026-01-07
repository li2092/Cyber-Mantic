"""
ReportCompareDialog - 报告对比对话框

对比两份报告，显示差异和变化趋势
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QTextEdit, QPushButton, QFrame,
    QSplitter, QScrollArea, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont
from typing import Optional
import asyncio

from models import ComprehensiveReport
from services.report_service import ReportService
from utils.logger import get_logger


class CompareWorker(QThread):
    """对比异步工作线程"""
    finished = pyqtSignal(str)  # AI对比分析结果
    error = pyqtSignal(str)

    def __init__(self, report_service: ReportService,
                 report1: ComprehensiveReport,
                 report2: ComprehensiveReport):
        super().__init__()
        self.report_service = report_service
        self.report1 = report1
        self.report2 = report2

    def run(self):
        """执行异步对比"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # 调用对比服务
            comparison = loop.run_until_complete(
                self.report_service.compare_reports(self.report1, self.report2)
            )

            loop.close()

            self.finished.emit(comparison)

        except Exception as e:
            self.error.emit(str(e))


class ReportCompareDialog(QDialog):
    """报告对比对话框"""

    def __init__(self, report1: ComprehensiveReport, report2: ComprehensiveReport,
                 report_service: ReportService, parent=None):
        super().__init__(parent)
        self.report1 = report1
        self.report2 = report2
        self.report_service = report_service
        self.logger = get_logger(__name__)
        self._setup_ui()
        self._load_comparison()

    def _setup_ui(self):
        """设置UI"""
        self.setWindowTitle("报告对比")
        self.setMinimumSize(900, 700)

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # 标题
        title_label = QLabel("📊 报告对比分析")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # 说明文字
        info_label = QLabel("对比两份报告，分析变化趋势和差异。")
        info_label.setStyleSheet("color: #666; font-size: 10pt;")
        layout.addWidget(info_label)

        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #E0E0E0;")
        layout.addWidget(separator)

        # 分屏器：左右两个报告
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧：报告1
        left_panel = self._create_report_panel(self.report1, "报告 A")
        splitter.addWidget(left_panel)

        # 右侧：报告2
        right_panel = self._create_report_panel(self.report2, "报告 B")
        splitter.addWidget(right_panel)

        # 设置比例
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter)

        # 对比分析结果区域
        compare_group = QGroupBox("🔍 AI对比分析")
        compare_layout = QVBoxLayout()

        self.compare_text = QTextEdit()
        self.compare_text.setReadOnly(True)
        self.compare_text.setPlaceholderText("正在加载对比分析...")
        self.compare_text.setStyleSheet("""
            QTextEdit {
                background-color: #FFF9E6;
                border: 2px solid #FFE082;
                border-radius: 8px;
                padding: 12px;
                font-size: 11pt;
                line-height: 1.6;
            }
        """)
        self.compare_text.setMinimumHeight(150)
        compare_layout.addWidget(self.compare_text)

        compare_group.setLayout(compare_layout)
        layout.addWidget(compare_group)

        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        export_btn = QPushButton("📄 导出对比结果")
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #64B5F6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #42A5F5;
            }
        """)
        export_btn.clicked.connect(self._on_export_clicked)
        button_layout.addWidget(export_btn)

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
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

        # 整体样式
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

    def _create_report_panel(self, report: ComprehensiveReport, title: str) -> QWidget:
        """
        创建单个报告面板

        Args:
            report: 报告对象
            title: 面板标题

        Returns:
            报告面板组件
        """
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        # 标题
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameStyle(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # 内容容器
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)

        # 基本信息
        info_text = f"""
<div style="background-color: #F5F5F5; padding: 10px; border-radius: 6px;">
<p><b>📅 生成时间:</b> {report.created_at.strftime('%Y年%m月%d日 %H:%M')}</p>
<p><b>❓ 问题类型:</b> {report.user_input_summary.get('question_type', '未知')}</p>
<p><b>🔮 使用理论:</b> {', '.join(report.selected_theories)}</p>
<p><b>🎯 置信度:</b> {report.overall_confidence:.0%}</p>
</div>
"""
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        info_label.setTextFormat(Qt.TextFormat.RichText)
        content_layout.addWidget(info_label)

        # 执行摘要
        summary_group = QGroupBox("📝 执行摘要")
        summary_layout = QVBoxLayout()

        summary_text = QLabel(report.executive_summary[:200] + "..." if len(report.executive_summary) > 200 else report.executive_summary)
        summary_text.setWordWrap(True)
        summary_text.setStyleSheet("color: #333; font-size: 10pt; padding: 8px;")
        summary_layout.addWidget(summary_text)

        summary_group.setLayout(summary_layout)
        content_layout.addWidget(summary_group)

        # 行动建议
        if report.comprehensive_advice:
            advice_group = QGroupBox("💡 行动建议")
            advice_layout = QVBoxLayout()

            advice_text = ""
            for i, advice in enumerate(report.comprehensive_advice[:3], 1):  # 只显示前3条
                priority = advice.get('priority', '中')
                content = advice.get('content', '')
                advice_text += f"<p><b>{i}. {priority}优先级:</b> {content}</p>"

            advice_label = QLabel(advice_text)
            advice_label.setWordWrap(True)
            advice_label.setTextFormat(Qt.TextFormat.RichText)
            advice_label.setStyleSheet("color: #333; font-size: 10pt; padding: 8px;")
            advice_layout.addWidget(advice_label)

            advice_group.setLayout(advice_layout)
            content_layout.addWidget(advice_group)

        content_layout.addStretch()

        content_widget.setLayout(content_layout)
        scroll_area.setWidget(content_widget)

        layout.addWidget(scroll_area)

        widget.setLayout(layout)
        widget.setStyleSheet("""
            QWidget {
                background-color: white;
            }
        """)

        return widget

    def _load_comparison(self):
        """加载对比分析"""
        self.compare_text.setPlainText("⏳ 正在分析两份报告的差异...")

        # 启动异步对比
        self.worker = CompareWorker(
            self.report_service,
            self.report1,
            self.report2
        )
        self.worker.finished.connect(self._on_comparison_finished)
        self.worker.error.connect(self._on_comparison_error)
        self.worker.start()

    def _on_comparison_finished(self, comparison: str):
        """对比完成回调"""
        self.compare_text.setPlainText(comparison)

    def _on_comparison_error(self, error_msg: str):
        """对比失败回调"""
        error_text = f"对比分析时出错：{error_msg}\n\n请稍后再试。"
        self.compare_text.setPlainText(error_text)
        self.logger.error(f"报告对比失败: {error_msg}")

    def _on_export_clicked(self):
        """导出对比结果"""
        from PyQt6.QtWidgets import QFileDialog

        # 建议文件名
        filename = f"报告对比_{self.report1.report_id[:8]}_vs_{self.report2.report_id[:8]}.md"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出对比结果",
            filename,
            "Markdown文件 (*.md);;所有文件 (*)"
        )

        if file_path:
            try:
                # 生成Markdown内容
                markdown = self._generate_comparison_markdown()

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(markdown)

                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(self, "导出成功", f"对比结果已导出到：\n{file_path}")

            except Exception as e:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "导出失败", f"导出时出错：{str(e)}")

    def _generate_comparison_markdown(self) -> str:
        """生成对比Markdown"""
        markdown = f"""# 报告对比分析

**生成时间**: {self.report1.created_at.strftime('%Y年%m月%d日 %H:%M')}

---

## 报告 A

- **报告ID**: {self.report1.report_id}
- **生成时间**: {self.report1.created_at.strftime('%Y年%m月%d日 %H:%M:%S')}
- **问题类型**: {self.report1.user_input_summary.get('question_type', '未知')}
- **使用理论**: {', '.join(self.report1.selected_theories)}
- **置信度**: {self.report1.overall_confidence:.0%}

**执行摘要**:
{self.report1.executive_summary}

---

## 报告 B

- **报告ID**: {self.report2.report_id}
- **生成时间**: {self.report2.created_at.strftime('%Y年%m月%d日 %H:%M:%S')}
- **问题类型**: {self.report2.user_input_summary.get('question_type', '未知')}
- **使用理论**: {', '.join(self.report2.selected_theories)}
- **置信度**: {self.report2.overall_confidence:.0%}

**执行摘要**:
{self.report2.executive_summary}

---

## 🔍 AI对比分析

{self.compare_text.toPlainText()}

---

*此对比由赛博玄数系统生成，仅供参考。*
"""
        return markdown
