"""
结果面板组件 - 显示分析结果和可视化图表
"""
from PyQt6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QWidget,
    QLabel, QPushButton, QTextEdit, QTabWidget, QScrollArea, QGridLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap
from typing import Optional, Dict, Any, List

from models import ComprehensiveReport
from utils.logger import get_logger


class ResultPanel(QGroupBox):
    """结果面板组件"""

    def __init__(self, parent=None):
        super().__init__("分析结果", parent)
        self.logger = get_logger(__name__)
        self.report_font_size = 10  # 默认字体大小
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # 字体大小调节工具栏
        self._create_font_toolbar(layout)

        # 使用TabWidget区分不同类型的结果
        self.result_tabs = QTabWidget()
        self.result_tabs.setMinimumHeight(600)

        # 摘要标签页
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setPlaceholderText("分析摘要将在此显示...")
        self.result_tabs.addTab(self.summary_text, "📊 核心摘要")

        # 详细分析标签页
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setPlaceholderText("详细分析将在此显示...")
        self.result_tabs.addTab(self.detail_text, "📝 详细分析")

        # 各理论分析标签页
        self.theories_text = QTextEdit()
        self.theories_text.setReadOnly(True)
        self.theories_text.setPlaceholderText("各理论详情将在此显示...")
        self.result_tabs.addTab(self.theories_text, "🔮 各理论分析")

        # 数据可视化标签页
        self.visualization_widget = self._create_visualization_widget()
        self.result_tabs.addTab(self.visualization_widget, "📊 数据可视化")

        # 初始化字体大小
        self._apply_report_font_size()

        layout.addWidget(self.result_tabs)
        self.setLayout(layout)

    def _create_font_toolbar(self, layout: QVBoxLayout):
        """创建字体大小调节工具栏"""
        font_toolbar = QHBoxLayout()
        font_toolbar.setSpacing(5)

        font_label = QLabel("字体大小:")
        font_toolbar.addWidget(font_label)

        # 缩小按钮
        self.font_decrease_btn = QPushButton("🔍- 缩小")
        self.font_decrease_btn.setMaximumWidth(100)
        self.font_decrease_btn.setMinimumHeight(32)
        self.font_decrease_btn.clicked.connect(self._decrease_font)
        font_toolbar.addWidget(self.font_decrease_btn)

        # 重置按钮
        self.font_reset_btn = QPushButton("↺ 重置")
        self.font_reset_btn.setMaximumWidth(80)
        self.font_reset_btn.setMinimumHeight(32)
        self.font_reset_btn.clicked.connect(self._reset_font)
        font_toolbar.addWidget(self.font_reset_btn)

        # 放大按钮
        self.font_increase_btn = QPushButton("🔍+ 放大")
        self.font_increase_btn.setMaximumWidth(100)
        self.font_increase_btn.setMinimumHeight(32)
        self.font_increase_btn.clicked.connect(self._increase_font)
        font_toolbar.addWidget(self.font_increase_btn)

        font_toolbar.addStretch()
        layout.addLayout(font_toolbar)

    def _create_visualization_widget(self) -> QWidget:
        """创建数据可视化显示组件"""
        # 创建主容器
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 创建提示标签
        hint_label = QLabel("📊 数据可视化将在分析完成后显示")
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint_label.setStyleSheet("color: gray; font-size: 14px; padding: 20px;")
        main_layout.addWidget(hint_label)
        self.viz_hint_label = hint_label

        # 创建图表容器（使用网格布局，2x2）
        charts_widget = QWidget()
        charts_layout = QGridLayout(charts_widget)
        charts_layout.setSpacing(15)
        charts_layout.setContentsMargins(0, 0, 0, 0)

        # 创建4个图表标签（初始隐藏）
        self.wuxing_chart_label = QLabel()
        self.wuxing_chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.wuxing_chart_label.setVisible(False)
        self.wuxing_chart_label.setMinimumSize(400, 400)
        charts_layout.addWidget(self.wuxing_chart_label, 0, 0)

        self.dayun_chart_label = QLabel()
        self.dayun_chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.dayun_chart_label.setVisible(False)
        self.dayun_chart_label.setMinimumSize(400, 300)
        charts_layout.addWidget(self.dayun_chart_label, 0, 1)

        self.fitness_chart_label = QLabel()
        self.fitness_chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fitness_chart_label.setVisible(False)
        self.fitness_chart_label.setMinimumSize(400, 350)
        charts_layout.addWidget(self.fitness_chart_label, 1, 0)

        self.conflict_chart_label = QLabel()
        self.conflict_chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.conflict_chart_label.setVisible(False)
        self.conflict_chart_label.setMinimumSize(400, 350)
        charts_layout.addWidget(self.conflict_chart_label, 1, 1)

        # 人生K线图（占据整行）
        self.kline_chart_label = QLabel()
        self.kline_chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.kline_chart_label.setVisible(False)
        self.kline_chart_label.setMinimumSize(800, 400)
        charts_layout.addWidget(self.kline_chart_label, 2, 0, 1, 2)  # 跨两列

        charts_widget.setVisible(False)
        self.charts_widget = charts_widget
        main_layout.addWidget(charts_widget)

        main_layout.addStretch()

        # 将主容器放入滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidget(main_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        return scroll_area

    def display_report(self, report: ComprehensiveReport):
        """显示报告内容

        Args:
            report: 综合分析报告
        """
        # 摘要
        summary_content = self._extract_summary_content(report.executive_summary)
        summary_formatted = f"""# 赛博玄数分析报告

**报告ID**: {report.report_id[:16]}
**生成时间**: {report.created_at.strftime('%Y-%m-%d %H:%M:%S')}
**问题类别**: {report.user_input_summary.get('question_type', '未知')}
**使用理论**: {', '.join(report.selected_theories)}

---

## 核心摘要

{summary_content}

---

**置信度**: {report.overall_confidence:.0%} | **局限性**: {report.limitations}
"""
        self.summary_text.setMarkdown(summary_formatted)
        self.summary_text.verticalScrollBar().setValue(0)

        # 详细分析
        detail_sections = []

        if hasattr(report, 'detailed_analysis') and report.detailed_analysis:
            detail_sections.append(f"""# 详细分析

{report.detailed_analysis}
""")

        if report.retrospective_analysis:
            detail_sections.append(f"""---

## 📊 回溯分析（过去3年）

{report.retrospective_analysis}
""")

        if report.predictive_analysis:
            detail_sections.append(f"""---

## 🔮 预测分析（未来1-2年）

{report.predictive_analysis}
""")

        detail_sections.append(f"""---

## 💡 行动建议

{self._format_advice_markdown(report.comprehensive_advice)}
""")

        if not detail_sections:
            detail = f"""# 详细分析

## 回溯分析（过去3年）

{report.retrospective_analysis if report.retrospective_analysis else '（此问题类型不适用时间回顾）'}

---

## 预测分析（未来1-2年）

{report.predictive_analysis if report.predictive_analysis else '（此问题类型不适用未来趋势）'}

---

## 行动建议

{self._format_advice_markdown(report.comprehensive_advice)}
"""
        else:
            detail = "\n".join(detail_sections)

        self.detail_text.setMarkdown(detail)
        self.detail_text.verticalScrollBar().setValue(0)

        # 各理论分析
        theories_text = f"""# 各理论分析详情

*共使用 **{len(report.theory_results)}** 个术数理论进行分析*

---

"""
        for i, result in enumerate(report.theory_results, 1):
            confidence_bar = self._create_level_bar(result.confidence)
            theories_text += f"""
## {i}. {result.theory_name}

**置信度**: {confidence_bar} `{result.confidence:.0%}`

{result.interpretation}

---

"""
        self.theories_text.setMarkdown(theories_text)
        self.theories_text.verticalScrollBar().setValue(0)

        # 更新可视化图表
        try:
            self._update_visualizations(report)
        except Exception as e:
            self.logger.error(f"更新可视化图表失败: {e}", exc_info=True)

        # 显示结果区域
        self.setVisible(True)

    def _extract_summary_content(self, executive_summary: str) -> str:
        """提取执行摘要的核心内容"""
        if not executive_summary:
            return "暂无摘要"

        lines = executive_summary.split('\n')
        cleaned_lines = []
        for line in lines:
            if line.strip().startswith('# '):
                continue
            if line.strip().startswith('## '):
                cleaned_lines.append(f"**{line.replace('##', '').strip()}**")
            else:
                cleaned_lines.append(line)

        content = '\n'.join(cleaned_lines).strip()

        if len(content) > 500:
            for i in range(400, min(500, len(content))):
                if content[i] in ['。', '！', '？', '.', '!', '?']:
                    return content[:i+1] + "\n\n（完整内容请查看详细分析标签页）"
            return content[:500] + "...\n\n（完整内容请查看详细分析标签页）"

        return content

    def _format_advice_markdown(self, advice_list) -> str:
        """格式化建议列表为Markdown"""
        if not advice_list:
            return "*暂无建议*"

        formatted = []
        for i, item in enumerate(advice_list, 1):
            if isinstance(item, dict):
                priority = item.get('priority', '中')
                content = item.get('content', '')
                formatted.append(f"**{i}. 【{priority}优先级】** {content}")
            else:
                formatted.append(f"**{i}.** {item}")

        return '\n\n'.join(formatted)

    def _create_level_bar(self, value: float) -> str:
        """创建进度条图示"""
        filled = int(value * 20)
        empty = 20 - filled
        return "█" * filled + "░" * empty

    def _update_visualizations(self, report: ComprehensiveReport):
        """更新可视化图表"""
        from utils.visualization import (
            WuxingRadarChart, DayunTimeline,
            TheoryFitnessChart, ConflictResolutionFlow,
            LifeKLineChart
        )
        from datetime import datetime

        any_chart_shown = False

        # 1. 五行雷达图
        try:
            wuxing_data = self._extract_wuxing_data(report)
            if wuxing_data:
                chart_bytes = WuxingRadarChart.to_bytes(wuxing_data)
                pixmap = QPixmap()
                pixmap.loadFromData(chart_bytes)
                self.wuxing_chart_label.setPixmap(pixmap.scaled(
                    700, 700,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                ))
                self.wuxing_chart_label.setVisible(True)
                any_chart_shown = True
        except Exception as e:
            self.logger.warning(f"五行雷达图生成失败: {e}")

        # 2. 大运时间轴
        try:
            dayun_data = self._extract_dayun_data(report)
            if dayun_data:
                chart_bytes = DayunTimeline.to_bytes(dayun_data, datetime.now().year)
                pixmap = QPixmap()
                pixmap.loadFromData(chart_bytes)
                self.dayun_chart_label.setPixmap(pixmap.scaled(
                    700, 500,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                ))
                self.dayun_chart_label.setVisible(True)
                any_chart_shown = True
        except Exception as e:
            self.logger.warning(f"大运时间轴生成失败: {e}")

        # 3. 理论适配度图
        try:
            fitness_data = self._extract_theory_fitness(report)
            if fitness_data:
                chart_bytes = TheoryFitnessChart.to_bytes(fitness_data)
                pixmap = QPixmap()
                pixmap.loadFromData(chart_bytes)
                self.fitness_chart_label.setPixmap(pixmap.scaled(
                    700, 500,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                ))
                self.fitness_chart_label.setVisible(True)
                any_chart_shown = True
        except Exception as e:
            self.logger.warning(f"理论适配度图生成失败: {e}")

        # 4. 冲突解决流程图
        try:
            conflict_data = self._extract_conflict_data(report)
            if conflict_data:
                chart_bytes = ConflictResolutionFlow.to_bytes(conflict_data)
                pixmap = QPixmap()
                pixmap.loadFromData(chart_bytes)
                self.conflict_chart_label.setPixmap(pixmap.scaled(
                    700, 500,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                ))
                self.conflict_chart_label.setVisible(True)
                any_chart_shown = True
        except Exception as e:
            self.logger.warning(f"冲突解决流程图生成失败: {e}")

        # 5. 人生K线图
        try:
            dayun_data = self._extract_dayun_data(report)
            birth_year = self._extract_birth_year(report)
            if dayun_data and birth_year:
                # 从大运数据生成K线数据
                kline_data = LifeKLineChart.from_dayun_data(dayun_data, birth_year)
                if kline_data:
                    chart_bytes = LifeKLineChart.to_bytes(kline_data, "人生运势K线图")
                    pixmap = QPixmap()
                    pixmap.loadFromData(chart_bytes)
                    self.kline_chart_label.setPixmap(pixmap.scaled(
                        1000, 500,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    ))
                    self.kline_chart_label.setVisible(True)
                    any_chart_shown = True
        except Exception as e:
            self.logger.warning(f"人生K线图生成失败: {e}")

        # 显示或隐藏图表容器
        if any_chart_shown:
            self.viz_hint_label.setVisible(False)
            self.charts_widget.setVisible(True)
        else:
            self.viz_hint_label.setText("暂无可视化数据")
            self.viz_hint_label.setVisible(True)
            self.charts_widget.setVisible(False)

    def _extract_wuxing_data(self, report: ComprehensiveReport) -> Optional[Dict[str, float]]:
        """从报告中提取五行数据"""
        for result in report.theory_results:
            if result.theory_name == "八字":
                calc_data = result.calculation_data
                if "wuxing_analysis" in calc_data:
                    wuxing = calc_data["wuxing_analysis"]
                    if "scores" in wuxing:
                        return wuxing["scores"]
                    elif "statistics" in wuxing:
                        stats = wuxing["statistics"]
                        return {
                            "木": stats.get("木", 0),
                            "火": stats.get("火", 0),
                            "土": stats.get("土", 0),
                            "金": stats.get("金", 0),
                            "水": stats.get("水", 0)
                        }
        return None

    def _extract_dayun_data(self, report: ComprehensiveReport) -> Optional[List[Dict[str, Any]]]:
        """从报告中提取大运数据"""
        for result in report.theory_results:
            if result.theory_name == "八字":
                calc_data = result.calculation_data
                if "dayun" in calc_data:
                    dayun_list = calc_data["dayun"]
                    formatted_data = []
                    for dayun in dayun_list:
                        formatted_data.append({
                            "start_age": dayun.get("start_age", 0),
                            "end_age": dayun.get("end_age", 0),
                            "gan_zhi": dayun.get("gan_zhi", ""),
                            "description": dayun.get("description", "")
                        })
                    return formatted_data if formatted_data else None
        return None

    def _extract_theory_fitness(self, report: ComprehensiveReport) -> Optional[List[Dict[str, Any]]]:
        """从报告中提取理论适配度数据"""
        fitness_data = []
        for result in report.theory_results:
            fitness_data.append({
                "theory": result.theory_name,
                "fitness": result.confidence,
                "priority": "基础" if result.theory_name in ["八字", "紫微斗数"] else "深度"
            })
        return fitness_data if fitness_data else None

    def _extract_conflict_data(self, report: ComprehensiveReport) -> Optional[List[Dict[str, Any]]]:
        """从报告中提取冲突数据"""
        if not report.conflict_info.has_conflict:
            return []

        conflicts = report.conflict_info.conflicts
        if not conflicts:
            return []

        formatted_conflicts = []
        for conflict in conflicts:
            formatted_conflicts.append({
                "level": conflict.get("level", 1),
                "theories": conflict.get("theories", []),
                "resolution": conflict.get("resolution", "")
            })
        return formatted_conflicts

    def _extract_birth_year(self, report: ComprehensiveReport) -> Optional[int]:
        """从报告中提取出生年份"""
        # 尝试从用户输入摘要中获取
        user_input = report.user_input_summary
        if user_input:
            birth_year = user_input.get("birth_year")
            if birth_year:
                return int(birth_year)

        # 尝试从八字结果中获取
        for result in report.theory_results:
            if result.theory_name == "八字":
                calc_data = result.calculation_data
                if "birth_info" in calc_data:
                    birth_info = calc_data["birth_info"]
                    if "year" in birth_info:
                        return int(birth_info["year"])

        return None

    # ===== 字体控制 =====

    def _increase_font(self):
        """放大报告字体"""
        if self.report_font_size < 20:
            self.report_font_size += 1
            self._apply_report_font_size()
            self.logger.debug(f"报告字体大小: {self.report_font_size}pt")

    def _decrease_font(self):
        """缩小报告字体"""
        if self.report_font_size > 8:
            self.report_font_size -= 1
            self._apply_report_font_size()
            self.logger.debug(f"报告字体大小: {self.report_font_size}pt")

    def _reset_font(self):
        """重置报告字体为默认大小"""
        self.report_font_size = 10
        self._apply_report_font_size()
        self.logger.debug("报告字体大小已重置为10pt")

    def _apply_report_font_size(self):
        """应用字体大小到所有报告文本框"""
        font = QFont()
        font.setPointSize(self.report_font_size)

        self.summary_text.setFont(font)
        self.detail_text.setFont(font)
        self.theories_text.setFont(font)
