"""
HistoryReportViewerDialog - 历史报告查看对话框

用于查看问道/推演模块生成的历史报告，独立于推演页面
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextBrowser, QTextEdit,
    QPushButton, QLabel, QFrame, QScrollArea, QWidget,
    QMessageBox, QFileDialog, QSplitter, QTabWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from typing import Optional, List
from datetime import datetime

from models import ComprehensiveReport, TheoryAnalysisResult


class HistoryReportViewerDialog(QDialog):
    """历史报告查看对话框"""

    def __init__(self, report: ComprehensiveReport, parent=None):
        super().__init__(parent)
        self.report = report
        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        self.setWindowTitle("查看历史报告")
        self.setMinimumSize(900, 700)
        self.resize(1000, 800)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 顶部工具栏
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # 报告内容区域
        content_area = self._create_content_area()
        layout.addWidget(content_area, 1)

        self.setLayout(layout)

    def _create_toolbar(self) -> QFrame:
        """创建顶部工具栏"""
        toolbar = QFrame()
        toolbar.setFixedHeight(56)
        toolbar.setStyleSheet("""
            QFrame {
                background-color: #F8FAFC;
                border-bottom: 1px solid #E2E8F0;
            }
        """)

        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(12)

        # 标题
        title = QLabel("📜 历史报告")
        title.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #1E293B;")
        layout.addWidget(title)

        # 报告时间
        if hasattr(self.report, 'created_at') and self.report.created_at:
            time_str = self.report.created_at.strftime('%Y-%m-%d %H:%M')
            time_label = QLabel(f"创建于: {time_str}")
            time_label.setStyleSheet("color: #64748B; font-size: 11pt;")
            layout.addWidget(time_label)

        layout.addStretch()

        # 导出按钮
        export_md_btn = QPushButton("📄 导出Markdown")
        export_md_btn.setFixedHeight(36)
        export_md_btn.clicked.connect(self._export_markdown)
        export_md_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366F1;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4F46E5;
            }
        """)
        layout.addWidget(export_md_btn)

        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.setFixedHeight(36)
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #E5E7EB;
                color: #374151;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #D1D5DB;
            }
        """)
        layout.addWidget(close_btn)

        return toolbar

    def _create_content_area(self) -> QWidget:
        """创建报告内容区域 - 使用分栏显示"""
        container = QWidget()
        container.setStyleSheet("background-color: #FFFFFF;")

        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 使用TabWidget分栏显示
        self.result_tabs = QTabWidget()
        self.result_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                background: white;
            }
            QTabBar::tab {
                background: #F1F5F9;
                border: 1px solid #E5E7EB;
                border-bottom: none;
                padding: 8px 16px;
                margin-right: 2px;
                border-radius: 6px 6px 0 0;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom: 1px solid white;
            }
            QTabBar::tab:hover:!selected {
                background: #E2E8F0;
            }
        """)

        # Tab 1: 核心摘要
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self._apply_text_style(self.summary_text)
        self.result_tabs.addTab(self.summary_text, "📊 核心摘要")

        # Tab 2: 详细分析
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self._apply_text_style(self.detail_text)
        self.result_tabs.addTab(self.detail_text, "📝 详细分析")

        # Tab 3: 各理论分析
        self.theories_text = QTextEdit()
        self.theories_text.setReadOnly(True)
        self._apply_text_style(self.theories_text)
        self.result_tabs.addTab(self.theories_text, "🔮 各理论分析")

        # Tab 4: 建议与置信度
        self.advice_text = QTextEdit()
        self.advice_text.setReadOnly(True)
        self._apply_text_style(self.advice_text)
        self.result_tabs.addTab(self.advice_text, "💡 行动建议")

        # 填充内容
        self._populate_tabs()

        layout.addWidget(self.result_tabs)

        return container

    def _apply_text_style(self, text_widget: QTextEdit):
        """应用统一的文本样式"""
        text_widget.setStyleSheet("""
            QTextEdit {
                background-color: #FFFFFF;
                border: none;
                padding: 16px;
                font-size: 11pt;
                line-height: 1.8;
            }
        """)

    def _populate_tabs(self):
        """填充各标签页内容"""
        report = self.report

        # Tab 1: 核心摘要
        summary_md = f"""# 赛博玄数分析报告

**报告ID**: {report.report_id[:16] if report.report_id else '未知'}
**生成时间**: {report.created_at.strftime('%Y-%m-%d %H:%M:%S') if report.created_at else '未知'}
**问题类别**: {report.user_input_summary.get('question_type', '未知') if report.user_input_summary else '未知'}
**使用理论**: {', '.join(report.selected_theories) if report.selected_theories else '未知'}

---

## 核心摘要

{report.executive_summary if report.executive_summary else '暂无摘要'}

---

**置信度**: {report.overall_confidence:.0%} | **局限性**: {', '.join(report.limitations) if report.limitations else '无'}
"""
        self.summary_text.setMarkdown(summary_md)

        # Tab 2: 详细分析
        detail_md = "# 详细分析\n\n"
        if report.detailed_analysis:
            detail_md += f"{report.detailed_analysis}\n\n"

        if report.retrospective_analysis:
            detail_md += f"---\n\n## 📊 回溯分析（过去经历）\n\n{report.retrospective_analysis}\n\n"

        if report.predictive_analysis:
            detail_md += f"---\n\n## 🔮 预测分析（未来趋势）\n\n{report.predictive_analysis}\n\n"

        self.detail_text.setMarkdown(detail_md)

        # Tab 3: 各理论分析
        theories_md = f"# 各理论分析详情\n\n*共使用 **{len(report.theory_results)}** 个术数理论进行分析*\n\n---\n\n"

        for i, result in enumerate(report.theory_results, 1):
            if isinstance(result, TheoryAnalysisResult):
                theories_md += f"## {i}. {result.theory_name}\n\n"
                theories_md += f"**置信度**: {self._create_progress_bar(result.confidence)} `{result.confidence:.0%}`\n\n"
                theories_md += f"**判断**: {result.judgment}\n\n"
                theories_md += f"{result.interpretation}\n\n"
                if result.advice:
                    theories_md += f"**建议**: {result.advice}\n\n"
                theories_md += "---\n\n"
            elif isinstance(result, dict):
                # 兼容字典格式
                theories_md += f"## {i}. {result.get('theory_name', '未知理论')}\n\n"
                theories_md += f"**置信度**: {self._create_progress_bar(result.get('confidence', 0.8))} `{result.get('confidence', 0.8):.0%}`\n\n"
                theories_md += f"**判断**: {result.get('judgment', '平')}\n\n"
                theories_md += f"{result.get('interpretation', '')}\n\n"
                if result.get('advice'):
                    theories_md += f"**建议**: {result.get('advice')}\n\n"
                theories_md += "---\n\n"

        self.theories_text.setMarkdown(theories_md)

        # Tab 4: 行动建议
        advice_md = "# 行动建议\n\n"
        if report.comprehensive_advice:
            for i, item in enumerate(report.comprehensive_advice, 1):
                if isinstance(item, dict):
                    priority = item.get('priority', '中')
                    content = item.get('content', '')
                    advice_md += f"**{i}. 【{priority}优先级】** {content}\n\n"
                else:
                    advice_md += f"**{i}.** {item}\n\n"
        else:
            advice_md += "*暂无建议*\n"

        self.advice_text.setMarkdown(advice_md)

    def _create_progress_bar(self, value: float) -> str:
        """创建文本进度条"""
        filled = int(value * 20)
        empty = 20 - filled
        return "█" * filled + "░" * empty

    def _generate_report_html(self) -> str:
        """生成报告的HTML内容"""
        report = self.report

        # 基本样式
        style = """
        <style>
            body { font-family: 'Microsoft YaHei', sans-serif; line-height: 1.8; color: #1E293B; }
            h1 { color: #6366F1; font-size: 20pt; margin-bottom: 16px; border-bottom: 2px solid #E5E7EB; padding-bottom: 8px; }
            h2 { color: #0F172A; font-size: 16pt; margin-top: 24px; margin-bottom: 12px; }
            h3 { color: #334155; font-size: 13pt; margin-top: 16px; margin-bottom: 8px; }
            .meta { color: #64748B; font-size: 10pt; margin-bottom: 20px; padding: 12px; background: #F8FAFC; border-radius: 8px; }
            .meta-item { margin: 4px 0; }
            .section { margin: 16px 0; padding: 16px; background: #FAFAFA; border-radius: 8px; border-left: 4px solid #6366F1; }
            .theory-card { margin: 12px 0; padding: 12px; background: #FFF; border: 1px solid #E5E7EB; border-radius: 6px; }
            .theory-name { font-weight: bold; color: #6366F1; }
            .judgment-good { color: #10B981; font-weight: bold; }
            .judgment-bad { color: #EF4444; font-weight: bold; }
            .judgment-neutral { color: #6B7280; }
            .summary { font-size: 12pt; padding: 16px; background: linear-gradient(135deg, #EEF2FF, #FDF4FF); border-radius: 8px; margin: 16px 0; }
            ul { padding-left: 20px; }
            li { margin: 6px 0; }
        </style>
        """

        html = f"<html><head>{style}</head><body>"

        # 标题
        html += "<h1>综合分析报告</h1>"

        # 元信息
        html += '<div class="meta">'
        if hasattr(report, 'user_input_summary') and report.user_input_summary:
            summary = report.user_input_summary
            if isinstance(summary, dict):
                if 'question_type' in summary:
                    html += f'<div class="meta-item"><strong>问题类型:</strong> {summary.get("question_type", "未知")}</div>'
                if 'question_description' in summary:
                    html += f'<div class="meta-item"><strong>问题描述:</strong> {summary.get("question_description", "")}</div>'

        if hasattr(report, 'selected_theories') and report.selected_theories:
            theories_str = ', '.join(report.selected_theories) if isinstance(report.selected_theories, list) else str(report.selected_theories)
            html += f'<div class="meta-item"><strong>使用理论:</strong> {theories_str}</div>'
        html += '</div>'

        # 执行摘要
        if hasattr(report, 'executive_summary') and report.executive_summary:
            html += '<div class="summary">'
            html += f'<h2>核心结论</h2>'
            html += f'<p>{report.executive_summary}</p>'
            html += '</div>'

        # 综合分析
        if hasattr(report, 'comprehensive_analysis') and report.comprehensive_analysis:
            html += '<div class="section">'
            html += f'<h2>详细分析</h2>'
            # 处理换行
            analysis_text = report.comprehensive_analysis.replace('\n', '<br>')
            html += f'<p>{analysis_text}</p>'
            html += '</div>'

        # 各理论分析结果
        theory_analyses = []
        theory_attrs = [
            ('xiaoliu_analysis', '小六壬'),
            ('cezi_analysis', '测字术'),
            ('bazi_analysis', '八字'),
            ('ziwei_analysis', '紫微斗数'),
            ('qimen_analysis', '奇门遁甲'),
            ('liuren_analysis', '大六壬'),
            ('liuyao_analysis', '六爻'),
            ('meihua_analysis', '梅花易数'),
        ]

        for attr, name in theory_attrs:
            if hasattr(report, attr):
                analysis = getattr(report, attr)
                if analysis:
                    theory_analyses.append((name, analysis))

        if theory_analyses:
            html += '<h2>各理论分析详情</h2>'
            for name, analysis in theory_analyses:
                html += f'<div class="theory-card">'
                html += f'<div class="theory-name">{name}</div>'
                if isinstance(analysis, dict):
                    if 'judgment' in analysis:
                        judgment = analysis['judgment']
                        judgment_class = 'judgment-good' if '吉' in str(judgment) else ('judgment-bad' if '凶' in str(judgment) else 'judgment-neutral')
                        html += f'<div class="{judgment_class}">判断: {judgment}</div>'
                    if 'summary' in analysis:
                        html += f'<div>{analysis["summary"]}</div>'
                    if 'details' in analysis:
                        html += f'<div style="color:#64748B;font-size:10pt;margin-top:8px;">{analysis["details"]}</div>'
                elif isinstance(analysis, str):
                    html += f'<div>{analysis}</div>'
                html += '</div>'

        # 建议
        if hasattr(report, 'recommendations') and report.recommendations:
            html += '<div class="section">'
            html += '<h2>行动建议</h2>'
            rec_text = report.recommendations.replace('\n', '<br>')
            html += f'<p>{rec_text}</p>'
            html += '</div>'

        # 置信度
        if hasattr(report, 'confidence_score') and report.confidence_score:
            html += f'<p style="color:#64748B;font-size:10pt;margin-top:24px;">综合置信度: {report.confidence_score:.1%}</p>'

        html += "</body></html>"
        return html

    def _export_markdown(self):
        """导出为Markdown文件"""
        try:
            # 选择保存路径
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "导出Markdown",
                f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                "Markdown Files (*.md)"
            )

            if not file_path:
                return

            # 生成Markdown内容
            md_content = self._generate_markdown()

            # 保存文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(md_content)

            QMessageBox.information(self, "导出成功", f"报告已导出到:\n{file_path}")

        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出时出错: {str(e)}")

    def _generate_markdown(self) -> str:
        """生成Markdown格式的报告"""
        report = self.report
        md = "# 综合分析报告\n\n"

        # 元信息
        if hasattr(report, 'created_at') and report.created_at:
            md += f"**创建时间:** {report.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"

        if hasattr(report, 'user_input_summary') and report.user_input_summary:
            summary = report.user_input_summary
            if isinstance(summary, dict):
                if 'question_type' in summary:
                    md += f"**问题类型:** {summary.get('question_type', '未知')}\n\n"
                if 'question_description' in summary:
                    md += f"**问题描述:** {summary.get('question_description', '')}\n\n"

        if hasattr(report, 'selected_theories') and report.selected_theories:
            theories_str = ', '.join(report.selected_theories) if isinstance(report.selected_theories, list) else str(report.selected_theories)
            md += f"**使用理论:** {theories_str}\n\n"

        md += "---\n\n"

        # 执行摘要
        if hasattr(report, 'executive_summary') and report.executive_summary:
            md += "## 核心结论\n\n"
            md += f"{report.executive_summary}\n\n"

        # 综合分析
        if hasattr(report, 'comprehensive_analysis') and report.comprehensive_analysis:
            md += "## 详细分析\n\n"
            md += f"{report.comprehensive_analysis}\n\n"

        # 各理论分析
        theory_attrs = [
            ('xiaoliu_analysis', '小六壬'),
            ('cezi_analysis', '测字术'),
            ('bazi_analysis', '八字'),
            ('ziwei_analysis', '紫微斗数'),
            ('qimen_analysis', '奇门遁甲'),
            ('liuren_analysis', '大六壬'),
            ('liuyao_analysis', '六爻'),
            ('meihua_analysis', '梅花易数'),
        ]

        has_theory = False
        for attr, name in theory_attrs:
            if hasattr(report, attr):
                analysis = getattr(report, attr)
                if analysis:
                    if not has_theory:
                        md += "## 各理论分析详情\n\n"
                        has_theory = True
                    md += f"### {name}\n\n"
                    if isinstance(analysis, dict):
                        if 'judgment' in analysis:
                            md += f"**判断:** {analysis['judgment']}\n\n"
                        if 'summary' in analysis:
                            md += f"{analysis['summary']}\n\n"
                        if 'details' in analysis:
                            md += f"*{analysis['details']}*\n\n"
                    elif isinstance(analysis, str):
                        md += f"{analysis}\n\n"

        # 建议
        if hasattr(report, 'recommendations') and report.recommendations:
            md += "## 行动建议\n\n"
            md += f"{report.recommendations}\n\n"

        # 置信度
        if hasattr(report, 'confidence_score') and report.confidence_score:
            md += f"\n---\n\n*综合置信度: {report.confidence_score:.1%}*\n"

        return md
