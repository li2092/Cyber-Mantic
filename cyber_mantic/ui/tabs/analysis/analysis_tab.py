"""
分析标签页 - 主控制器，协调输入、进度、结果面板
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from typing import Optional
from datetime import datetime

from models import UserInput, ComprehensiveReport
from services.analysis_service import AnalysisService
from services.export_service import ExportService
from utils.error_handler import ErrorHandler
from utils.logger import get_logger
from utils.history_manager import get_history_manager
from utils.usage_stats_manager import get_usage_stats_manager
from utils.warning_manager import get_warning_manager, WarningLevel
from ui.widgets.export_menu_button import ExportMenuButton
from ui.dialogs.warning_dialogs import show_warning_dialog, ForcedCoolingDialog

from .input_panel import InputPanel
from .progress_panel import ProgressPanel
from .result_panel import ResultPanel
from .workers import AnalysisWorker


class AnalysisTab(QWidget):
    """分析标签页 - 主控制器"""

    analysis_completed = pyqtSignal(object)  # 分析完成信号，传递报告

    def __init__(self, analysis_service: AnalysisService, export_service: ExportService, parent=None):
        super().__init__(parent)
        self.analysis_service = analysis_service
        self.export_service = export_service
        self.logger = get_logger(__name__)
        self.error_handler = ErrorHandler(self)
        self.history_manager = get_history_manager()

        # 当前报告
        self.current_report: Optional[ComprehensiveReport] = None

        # 工作线程
        self.worker: Optional[AnalysisWorker] = None

        # 会话追踪ID（用于洞察模块统计）
        self.current_session_id: Optional[str] = None

        # 初始化UI
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 创建内容容器
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # 输入面板
        self.input_panel = InputPanel()
        content_layout.addWidget(self.input_panel)

        # 进度面板
        self.progress_panel = ProgressPanel()
        content_layout.addWidget(self.progress_panel)

        # 结果面板
        self.result_panel = ResultPanel()
        self.result_panel.setVisible(False)
        content_layout.addWidget(self.result_panel)

        # 底部间隔
        bottom_spacer = QWidget()
        bottom_spacer.setFixedHeight(60)
        content_layout.addWidget(bottom_spacer)

        # 弹性空间
        content_layout.addStretch()

        # 滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(content_widget)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        main_layout.addWidget(self.scroll_area, 1)

        # 底部按钮
        self._create_action_bar(main_layout)

    def _create_action_bar(self, main_layout: QVBoxLayout):
        """创建底部操作按钮栏"""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        button_layout.addStretch()

        # 分析按钮
        self.analyze_btn = QPushButton("开始分析")
        self.analyze_btn.setMinimumSize(120, 40)
        self.analyze_btn.clicked.connect(self._start_analysis)
        button_layout.addWidget(self.analyze_btn)

        # 导出按钮
        try:
            self.export_btn = ExportMenuButton(self.export_service)
            self.export_btn.setMinimumSize(120, 40)
            button_layout.addWidget(self.export_btn)
        except Exception as e:
            self.error_handler.handle_error(e, "导出按钮初始化", show_dialog=False)
            # 降级方案
            self.save_btn = QPushButton("保存报告")
            self.save_btn.setMinimumSize(120, 48)
            self.save_btn.setEnabled(False)
            button_layout.addWidget(self.save_btn)

        main_layout.addLayout(button_layout, 0)

    def _start_analysis(self):
        """开始分析"""
        from utils.config_manager import get_config_manager

        config_manager = get_config_manager()
        if not config_manager.has_valid_api_key():
            QMessageBox.warning(self, "配置错误", "请先在\"设置\"标签页配置 API 密钥！")
            return

        # 检查是否处于锁定状态
        warning_manager = get_warning_manager()
        is_locked, lock_data = warning_manager.is_locked()
        if is_locked:
            care_message = warning_manager.get_care_message(WarningLevel.FORCED)
            dialog = ForcedCoolingDialog(care_message, self)
            dialog.exec()
            return

        # 获取问题描述进行关键词检查
        question_desc = self.input_panel.question_desc.text()
        if question_desc:
            warning_level, matched_keywords = warning_manager.check_text_for_keywords(question_desc)

            if warning_level != WarningLevel.NONE:
                care_message = warning_manager.get_care_message(warning_level)

                if warning_level == WarningLevel.FORCED:
                    warning_manager.set_lock(
                        reason="检测到高危情绪关键词",
                        trigger_keywords=matched_keywords
                    )
                    show_warning_dialog(warning_level, care_message, self)
                    return

                elif warning_level == WarningLevel.PAUSE:
                    should_continue = show_warning_dialog(warning_level, care_message, self)
                    if not should_continue:
                        return

                else:
                    show_warning_dialog(warning_level, care_message, self)

        # 收集用户输入
        user_input = self._collect_user_input()
        if user_input is None:
            return

        # 开始会话追踪
        try:
            stats_manager = get_usage_stats_manager()
            self.current_session_id = stats_manager.start_session(
                module='tuiyan',
                question_type=user_input.question_type,
                stage='analysis_started'
            )
        except Exception as e:
            self.logger.warning(f"开始会话追踪失败: {e}")

        # 显示进度面板
        self.progress_panel.reset()

        # 禁用分析按钮
        self.analyze_btn.setEnabled(False)

        # 启动工作线程
        self.worker = AnalysisWorker(self.analysis_service, user_input)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _collect_user_input(self) -> Optional[UserInput]:
        """收集用户输入数据

        Returns:
            用户输入对象，验证失败返回None
        """
        panel = self.input_panel

        # 起卦时间
        inquiry_time = (
            panel.inquiry_datetime.dateTime().toPyDateTime()
            if panel.use_custom_inquiry_time.isChecked()
            else datetime.now()
        )

        # 出生信息
        birth_year = None
        birth_month = None
        birth_day = None
        birth_hour = None
        birth_minute = None
        calendar_type = "solar"
        gender = None
        birth_place_lng = None
        mbti_type = None
        birth_time_certainty = "certain"

        if panel.use_birth_info.isChecked():
            birth_year = panel.birth_year.value()
            birth_month = panel.birth_month.value()
            birth_day = panel.birth_day.value()

            certainty_index = panel.birth_time_certainty.currentIndex()
            if certainty_index == 0:
                birth_time_certainty = "certain"
                birth_hour = panel.birth_hour.value()
                birth_minute = panel.birth_minute.value()
            elif certainty_index == 1:
                birth_time_certainty = "uncertain"
                birth_hour = panel.birth_hour.value()
                birth_minute = panel.birth_minute.value()
            else:
                birth_time_certainty = "unknown"

            calendar_type = "lunar" if panel.calendar_type.currentText() == "农历" else "solar"
            gender = "male" if panel.gender.currentText() == "男" else "female"

            mbti_text = panel.mbti_combo.currentText()
            if mbti_text and mbti_text != "请选择":
                mbti_type = mbti_text.split("-")[0]

            try:
                if panel.birth_lng.text():
                    birth_place_lng = float(panel.birth_lng.text())
            except ValueError:
                pass

        # 随机数
        numbers = None
        if panel.use_random_numbers.isChecked():
            numbers = [panel.num1.value(), panel.num2.value(), panel.num3.value()]

        # 问题描述
        question_desc = panel.question_desc.text()
        character = None
        if panel.character_input.text():
            character = panel.character_input.text()[:1]
            question_desc = f"测\"{character}\"字。{question_desc}"

        # 验证
        if not question_desc:
            QMessageBox.warning(self, "输入验证", "请输入问题描述")
            return None

        if panel.use_birth_info.isChecked():
            if not (birth_year and birth_month and birth_day):
                QMessageBox.warning(self, "输入验证", "请填写完整的出生年月日信息")
                return None

        has_any_info = (
            panel.use_birth_info.isChecked() or
            panel.use_random_numbers.isChecked() or
            bool(panel.character_input.text())
        )
        if not has_any_info:
            reply = QMessageBox.question(
                self,
                "提示",
                "您没有提供任何额外信息（出生信息、随机数、测字），可用的理论将会较少。\n\n是否继续分析？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return None

        return UserInput(
            question_type=panel.question_type.currentText(),
            question_description=question_desc,
            birth_year=birth_year,
            birth_month=birth_month,
            birth_day=birth_day,
            birth_hour=birth_hour,
            birth_minute=birth_minute,
            calendar_type=calendar_type,
            birth_time_certainty=birth_time_certainty,
            gender=gender,
            birth_place_lng=birth_place_lng,
            mbti_type=mbti_type,
            numbers=numbers,
            character=character,
            current_time=datetime.now(),
            initial_inquiry_time=inquiry_time,
            additional_persons=panel.get_additional_persons()
        )

    def _on_progress(self, theory: str, status: str, progress: int, detail: str = ""):
        """进度更新"""
        self.progress_panel.update_progress(theory, status, progress, detail)

    def _on_finished(self, report: ComprehensiveReport):
        """分析完成"""
        self.current_report = report
        self.progress_panel.set_completed()

        # 保存到历史记录
        self.history_manager.save_report(report)

        # 记录使用统计
        try:
            stats_manager = get_usage_stats_manager()
            # 获取主要理论（第一个理论结果）
            # 注意：theory_results 是 List[TheoryAnalysisResult]，不是字典
            primary_theory = None
            if report.theory_results and len(report.theory_results) > 0:
                first_result = report.theory_results[0]
                if hasattr(first_result, 'theory_name'):
                    primary_theory = first_result.theory_name
                elif isinstance(first_result, dict):
                    primary_theory = first_result.get('theory_name')

            # 获取问题类型
            question_type = None
            if hasattr(report, 'user_input_summary') and report.user_input_summary:
                question_type = report.user_input_summary.get('question_type')

            stats_manager.record_usage(
                module='tuiyan',
                theory=primary_theory,
                question_type=question_type
            )
            # 标记会话完成
            if self.current_session_id:
                stats_manager.complete_session(
                    session_id=self.current_session_id,
                    theory=primary_theory,
                    question_type=question_type
                )
                self.current_session_id = None  # 清除ID
        except Exception as e:
            self.logger.warning(f"记录使用统计失败: {e}")

        # 显示报告
        self.result_panel.display_report(report)
        self.result_panel.setVisible(True)

        self.analyze_btn.setEnabled(True)

        # 启用导出按钮
        if hasattr(self, 'export_btn'):
            self.export_btn.set_report(report)

        # 发射信号
        self.analysis_completed.emit(report)

        QMessageBox.information(self, "完成", "分析完成！请查看结果标签页")

    def _on_error(self, error_msg: str):
        """错误处理"""
        self.progress_panel.set_failed()
        self.analyze_btn.setEnabled(True)
        QMessageBox.critical(self, "错误", f"分析过程中发生错误:\n{error_msg}")

    def display_report(self, report: ComprehensiveReport):
        """外部调用显示报告（用于历史记录加载）"""
        self.current_report = report
        self.result_panel.display_report(report)
        self.result_panel.setVisible(True)

        if hasattr(self, 'export_btn'):
            self.export_btn.set_report(report)

        # 滚动到顶部
        if hasattr(self, 'scroll_area'):
            self.scroll_area.verticalScrollBar().setValue(0)

        self.update()
        self.repaint()

    def set_font_size(self, size: int):
        """设置全局字体大小（由主窗口调用）"""
        if hasattr(self, 'result_panel'):
            self.result_panel.set_font_size(size)

    def cleanup(self):
        """清理资源"""
        if self.worker:
            try:
                self.worker.progress.disconnect()
                self.worker.finished.disconnect()
                self.worker.error.disconnect()
            except Exception as e:
                self.logger.debug(f"清理worker信号失败: {e}")

        self.input_panel.cleanup()
