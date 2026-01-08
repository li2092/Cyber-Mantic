"""
PyQt6主窗口 - 支持分析、设置、历史记录

特性：
- GUI界面（需要PyQt6）
- 自动降级到CLI模式（当PyQt6不可用时）
"""
try:
    from PyQt6.QtWidgets import (
        QMainWindow, QWidget, QVBoxLayout,
        QLabel, QTabWidget, QMessageBox
    )
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QFont, QIcon
    HAS_PYQT6 = True
except ImportError:
    HAS_PYQT6 = False
    # 不在导入时打印，等到实际调用时再提示

from datetime import datetime
from typing import Optional

if HAS_PYQT6:
    from models import ComprehensiveReport, TheoryAnalysisResult, ConflictInfo
    from core import DecisionEngine
    from utils.config_manager import get_config_manager, reload_config
    from utils.history_manager import get_history_manager
    from utils.logger import get_logger

    # 服务层
    from services.conversation_service import ConversationService
    from services.report_service import ReportService
    from services.analysis_service import AnalysisService
    from services.export_service import ExportService

    # 标签页
    from ui.tabs import (
        AnalysisTab, AIConversationTab, SettingsTab, HistoryTab,
        LibraryTab, InsightTab
    )

    # 免责声明和引导
    from ui.dialogs import get_disclaimer_manager, OnboardingDialog
    from utils.config_manager import get_config_manager

    # 工具
    from utils.theme_manager import ThemeManager
    from utils.error_handler import ErrorHandler
    from utils.question_classifier import classify_question


    class MainWindow(QMainWindow):
        """主窗口 - 包含分析、设置、历史记录三个标签页"""

        def __init__(self):
            super().__init__()
            self.setWindowTitle("Cyber-Mantic 赛博玄数 - 多理论术数智能分析系统")
            self.setMinimumSize(1200, 800)

            # 加载配置
            self.config_manager = get_config_manager()
            self.config = self.config_manager.get_all_config()

            # 历史记录管理器
            self.history_manager = get_history_manager()

            # 创建决策引擎
            self.engine = DecisionEngine(self.config)

            # 初始化服务层和管理器
            self.logger = get_logger(__name__)
            self.error_handler = ErrorHandler(self)

            # 设置应用图标（在logger初始化之后）
            self._set_app_icon()

            # 初始化服务层
            self.api_manager = self.engine.api_manager  # 复用DecisionEngine的APIManager
            self.conversation_service = ConversationService(self.api_manager)
            self.report_service = ReportService(self.api_manager)
            self.analysis_service = AnalysisService(self.engine)
            self.export_service = ExportService()

            # 初始化管理器
            self.theme_manager = ThemeManager()

            # Tab引用（用于cleanup）
            # v4.0标签页架构：问道/推演/典籍/洞察/历史记录/设置
            self.ai_conversation_tab: Optional[AIConversationTab] = None  # 问道
            self.analysis_tab: Optional[AnalysisTab] = None  # 推演
            self.library_tab: Optional[LibraryTab] = None  # 典籍
            self.insight_tab: Optional[InsightTab] = None  # 洞察
            self.history_tab: Optional[HistoryTab] = None  # 历史记录
            self.settings_tab: Optional[SettingsTab] = None  # 设置

            # 免责声明管理器
            self.disclaimer_manager = get_disclaimer_manager()

            # 初始化UI（包含首次启动检查）
            self._init_ui()

            # 应用主题
            self._apply_theme()

            # 检查API配置
            self._check_api_config()

        def _set_app_icon(self):
            """设置应用程序图标"""
            from pathlib import Path
            icon_path = Path(__file__).parent / "resources" / "app_icon.png"
            if icon_path.exists():
                icon = QIcon(str(icon_path))
                self.setWindowIcon(icon)
                self.logger.info(f"应用图标已加载: {icon_path}")
            else:
                self.logger.warning(f"应用图标文件不存在: {icon_path}")

        def _init_ui(self):
            """初始化UI"""
            # 检查首次启动免责声明
            is_first_launch = self.disclaimer_manager.should_show_first_launch()
            if is_first_launch:
                if not self.disclaimer_manager.show_first_launch_disclaimer(self):
                    # 用户未接受协议，退出应用
                    import sys
                    sys.exit(0)

            # 检查首次引导（仅在首次启动时显示）
            config_manager = get_config_manager()
            if is_first_launch and not config_manager.is_onboarding_completed():
                self._show_onboarding()

            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            main_layout = QVBoxLayout(central_widget)

            # 标题
            title_label = QLabel("赛博玄数 - 多理论术数智能分析系统")
            title_font = QFont()
            title_font.setPointSize(16)
            title_font.setBold(True)
            title_label.setFont(title_font)
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            main_layout.addWidget(title_label)

            # 主标签页（v4.0架构：问道/推演/典籍/洞察/历史记录/设置）
            self.main_tabs = QTabWidget()

            # === 1. 问道标签页（原AI对话）===
            try:
                self.ai_conversation_tab = AIConversationTab(self.api_manager)
                self.ai_conversation_tab.save_requested.connect(self._save_conversation)
                self.main_tabs.addTab(self.ai_conversation_tab, "💬 问道")
            except Exception as e:
                self.error_handler.handle_error(e, "问道标签页初始化", show_dialog=False)
                self.logger.warning("问道标签页初始化失败，已跳过")

            # === 2. 推演标签页（原分析）===
            try:
                self.analysis_tab = AnalysisTab(
                    self.analysis_service,
                    self.export_service,
                    self
                )
                # 连接信号：分析完成后刷新历史记录
                self.analysis_tab.analysis_completed.connect(self._on_analysis_completed)
                self.main_tabs.addTab(self.analysis_tab, "📊 推演")
            except Exception as e:
                self.error_handler.handle_error(e, "推演标签页初始化", show_dialog=False)
                self.logger.error(f"推演标签页初始化失败: {e}")

            # === 3. 典籍标签页 ===
            try:
                self.library_tab = LibraryTab(api_manager=self.api_manager, parent=self)
                self.main_tabs.addTab(self.library_tab, "📚 典籍")
            except Exception as e:
                self.error_handler.handle_error(e, "典籍标签页初始化", show_dialog=False)
                self.logger.error(f"典籍标签页初始化失败: {e}")

            # === 4. 洞察标签页 ===
            try:
                self.insight_tab = InsightTab(api_manager=self.api_manager, parent=self)
                self.main_tabs.addTab(self.insight_tab, "🔮 洞察")
            except Exception as e:
                self.error_handler.handle_error(e, "洞察标签页初始化", show_dialog=False)
                self.logger.error(f"洞察标签页初始化失败: {e}")

            # === 5. 历史记录标签页 ===
            try:
                self.history_tab = HistoryTab(self.history_manager, self)
                # 连接信号：查看历史报告
                self.history_tab.report_selected.connect(self._on_history_report_selected)
                self.main_tabs.addTab(self.history_tab, "📜 历史记录")
            except Exception as e:
                self.error_handler.handle_error(e, "历史记录标签页初始化", show_dialog=False)
                self.logger.error(f"历史记录标签页初始化失败: {e}")

            # === 6. 设置标签页 ===
            try:
                from utils.template_manager import TemplateManager
                template_manager = TemplateManager()

                self.settings_tab = SettingsTab(
                    self.config_manager,
                    self.theme_manager,
                    template_manager,
                    self.api_manager,
                    self
                )
                # 连接信号
                self.settings_tab.theme_changed.connect(self._on_theme_changed)
                self.settings_tab.config_saved.connect(self._on_config_saved)
                self.settings_tab.refresh_feature_status_requested.connect(self._refresh_feature_status)
                self.main_tabs.addTab(self.settings_tab, "⚙️ 设置")
            except Exception as e:
                self.error_handler.handle_error(e, "设置标签页初始化", show_dialog=False)
                self.logger.error(f"设置标签页初始化失败: {e}")

            main_layout.addWidget(self.main_tabs)

        def _check_api_config(self):
            """检查API配置"""
            if not self.config_manager.has_valid_api_key():
                QMessageBox.warning(
                    self,
                    "配置提示",
                    "检测到尚未配置 API 密钥！\n\n"
                    "请前往\"设置\"标签页配置至少一个 AI API 密钥才能使用分析功能。\n\n"
                    "支持的 API：Claude、Gemini、Deepseek、Kimi"
                )

        def _apply_theme(self):
            """应用当前主题"""
            try:
                from PyQt6.QtWidgets import QApplication
                stylesheet = self.theme_manager.get_current_stylesheet()
                QApplication.instance().setStyleSheet(stylesheet)
                self.logger.info(f"主题已应用: {self.theme_manager.get_current_theme()}")
            except Exception as e:
                self.error_handler.handle_error(e, "主题应用", show_dialog=False)

        def _on_theme_changed(self, theme_name: str):
            """主题更改回调"""
            try:
                self._apply_theme()
                QMessageBox.information(
                    self,
                    "主题已更改",
                    f"主题已切换为：{theme_name}\n\n建议重启应用程序以完全生效。"
                )
                self.logger.info(f"主题已切换为: {theme_name}")
            except Exception as e:
                self.error_handler.handle_error(e, "主题切换")

        def _on_config_saved(self):
            """配置保存后的回调"""
            try:
                # 重新加载配置和引擎
                self.config_manager = reload_config()
                self.config = self.config_manager.get_all_config()
                self.engine = DecisionEngine(self.config)

                # 更新服务层的API Manager
                self.api_manager = self.engine.api_manager
                self.conversation_service = ConversationService(self.api_manager)
                self.report_service = ReportService(self.api_manager)
                self.analysis_service = AnalysisService(self.engine)

                # 更新Tab的服务引用
                if self.analysis_tab:
                    self.analysis_tab.analysis_service = self.analysis_service
                if self.ai_conversation_tab:
                    self.ai_conversation_tab.api_manager = self.api_manager
                    # 同时更新 conversation_service，确保使用新的 api_manager 配置
                    self.ai_conversation_tab.conversation_service = ConversationService(self.api_manager)

                self.logger.info(f"配置已重新加载，优先API: {self.api_manager.primary_api}")
            except Exception as e:
                self.error_handler.handle_error(e, "重新加载配置")

        def _on_analysis_completed(self, report: ComprehensiveReport):
            """分析完成回调 - 刷新历史记录并更新AI对话八字命盘"""
            try:
                if self.history_tab:
                    self.history_tab._refresh_history()
                # 更新AI对话标签页的八字命盘信息
                if self.ai_conversation_tab:
                    self.ai_conversation_tab.update_from_report(report)
                self.logger.info(f"分析完成，报告ID: {report.report_id}")
            except Exception as e:
                self.error_handler.handle_error(e, "处理分析完成事件", show_dialog=False)

        def _on_history_report_selected(self, report: ComprehensiveReport):
            """历史报告被选中 - 切换到推演标签页显示并更新问道八字命盘"""
            try:
                if self.analysis_tab:
                    # 设置报告到推演标签页
                    self.analysis_tab.display_report(report)
                    # 切换到推演标签页（索引1）
                    self.main_tabs.setCurrentIndex(1)
                # 更新问道标签页的八字命盘信息
                if self.ai_conversation_tab:
                    self.ai_conversation_tab.update_from_report(report)
                self.logger.info(f"查看历史报告: {report.report_id}")
            except Exception as e:
                self.error_handler.handle_error(e, "显示历史报告", show_dialog=False)

        def _refresh_feature_status(self):
            """刷新功能状态"""
            try:
                feature_status = {
                    "💬 AI对话功能": hasattr(self, 'ai_conversation_tab') and self.ai_conversation_tab is not None,
                    "📊 报告导出": hasattr(self, 'analysis_tab') and hasattr(self.analysis_tab, 'export_btn'),
                    "🎨 主题切换": hasattr(self, 'settings_tab') and hasattr(self.settings_tab, 'theme_settings_widget'),
                    "📝 报告自定义": hasattr(self, 'settings_tab') and hasattr(self.settings_tab, 'template_manager'),
                    "📈 历史记录对比": hasattr(self, 'history_tab') and self.history_tab is not None,
                    "💡 报告问答": hasattr(self, 'report_service') and self.report_service is not None,
                    "🔍 术语解释": hasattr(self, 'report_service') and self.report_service is not None,
                    "🤖 AI分析服务": hasattr(self, 'analysis_service') and self.analysis_service is not None,
                }

                if hasattr(self, 'settings_tab') and hasattr(self.settings_tab, 'feature_status_widget'):
                    self.settings_tab.feature_status_widget.update_status(feature_status)

                    # 记录日志
                    available, total = self.settings_tab.feature_status_widget.get_available_count()
                    self.logger.info(f"功能状态更新: {available}/{total} 可用")

            except Exception as e:
                self.error_handler.handle_error(e, "刷新功能状态", show_dialog=False)

        def _save_conversation(self, conversation_data: dict):
            """保存AI对话到历史记录"""
            try:
                # 将ConversationContext转换为ComprehensiveReport格式
                context = conversation_data.get('context', {})

                # 创建ComprehensiveReport对象
                import uuid

                # 提取理论分析结果
                theory_results = []

                # 八字分析结果
                if context.get('bazi_result'):
                    bazi = context['bazi_result']
                    theory_results.append(TheoryAnalysisResult(
                        theory_name="八字",
                        calculation_data=bazi,
                        interpretation=bazi.get('ai_analysis', '八字分析结果'),
                        judgment=bazi.get('judgment', '平'),
                        judgment_level=bazi.get('judgment_level', 0.5),
                        confidence=bazi.get('confidence', 0.85)
                    ))

                # 奇门分析结果
                if context.get('qimen_result'):
                    qimen = context['qimen_result']
                    theory_results.append(TheoryAnalysisResult(
                        theory_name="奇门遁甲",
                        calculation_data=qimen,
                        interpretation=qimen.get('ai_analysis', '奇门分析结果'),
                        judgment=qimen.get('吉凶判断', qimen.get('judgment', '平')),
                        judgment_level=qimen.get('综合评分', qimen.get('judgment_level', 0.5)),
                        confidence=qimen.get('confidence', 0.80)
                    ))

                # 六壬分析结果
                if context.get('liuren_result'):
                    liuren = context['liuren_result']
                    theory_results.append(TheoryAnalysisResult(
                        theory_name="大六壬",
                        calculation_data=liuren,
                        interpretation=liuren.get('ai_analysis', '六壬分析结果'),
                        judgment=liuren.get('吉凶判断', liuren.get('judgment', '平')),
                        judgment_level=liuren.get('综合评分', liuren.get('judgment_level', 0.5)),
                        confidence=liuren.get('confidence', 0.75)
                    ))

                # 补充占卜结果
                for supp in context.get('supplementary_results', []):
                    theory_results.append(TheoryAnalysisResult(
                        theory_name=supp.get('method', '占卜'),
                        calculation_data=supp,
                        interpretation=supp.get('interpretation', ''),
                        judgment=supp.get('judgment', '平'),
                        judgment_level=supp.get('judgment_level', 0.5),
                        confidence=0.70
                    ))

                # 创建报告
                report = ComprehensiveReport()
                report.report_id = str(uuid.uuid4())
                report.created_at = datetime.fromisoformat(conversation_data.get('timestamp', datetime.now().isoformat()))

                # 用户输入摘要 - 智能识别问题类型
                question_text = context.get('question', context.get('user_input_raw', ''))
                question_type = classify_question(question_text)

                report.user_input_summary = {
                    'question_type': question_type,
                    'question_desc': question_text[:100],
                    'birth_info': context.get('birth_info'),
                    'inquiry_time': conversation_data.get('timestamp')
                }

                # 使用的理论
                report.selected_theories = [r.theory_name for r in theory_results]
                report.selection_reason = "AI对话模式综合分析"

                # 理论结果
                report.theory_results = theory_results

                # 冲突信息
                report.conflict_info = ConflictInfo(
                    has_conflict=False,
                    conflicts=[],
                    resolution=None
                )

                # 综合结论
                report.executive_summary = context.get('synthesis_result', '综合分析结果')[:500]
                report.detailed_analysis = context.get('synthesis_result', '基于AI对话的详细分析')
                report.retrospective_analysis = "AI对话模式：回顾分析详见对话记录"
                report.predictive_analysis = context.get('synthesis_result', '')

                # 综合建议
                report.comprehensive_advice = [
                    {
                        'priority': '高',
                        'category': '综合建议',
                        'content': '详细建议请查看对话记录',
                        'rationale': '基于AI对话分析'
                    }
                ]

                # 元信息
                report.overall_confidence = 0.80
                report.limitations = [
                    "AI对话模式：分析基于实时交互",
                    "详细信息请查看完整对话记录"
                ]

                # 保存到历史记录
                self.history_manager.save_report(report)
                self.logger.info(f"AI对话已保存到历史记录: {report.report_id}")

                # 刷新历史记录列表
                if self.history_tab:
                    self.history_tab._refresh_history()

            except Exception as e:
                self.error_handler.handle_error(e, "保存AI对话")

        def _show_onboarding(self):
            """显示首次引导对话框"""
            try:
                dialog = OnboardingDialog(self)
                dialog.completed.connect(self._on_onboarding_completed)
                dialog.exec()
            except Exception as e:
                self.logger.warning(f"显示引导对话框失败: {e}")
                # 即使失败也标记为完成，避免每次都弹出
                self._on_onboarding_completed()

        def _on_onboarding_completed(self):
            """引导完成回调"""
            try:
                config_manager = get_config_manager()
                config_manager.set_onboarding_completed(True)
                self.logger.info("首次引导已完成")
            except Exception as e:
                self.logger.warning(f"保存引导完成状态失败: {e}")

        def closeEvent(self, event):
            """窗口关闭事件 - 清理资源，断开所有信号连接"""
            try:
                self.logger.info("正在关闭主窗口，清理资源...")

                # 清理问道标签页
                if hasattr(self, 'ai_conversation_tab') and self.ai_conversation_tab:
                    try:
                        if hasattr(self.ai_conversation_tab, 'cleanup'):
                            self.ai_conversation_tab.cleanup()
                        self.logger.debug("问道标签页已清理")
                    except Exception as e:
                        self.logger.warning(f"清理问道标签页失败: {e}")

                # 清理推演标签页
                if hasattr(self, 'analysis_tab') and self.analysis_tab:
                    try:
                        self.analysis_tab.cleanup()
                        self.logger.debug("推演标签页已清理")
                    except Exception as e:
                        self.logger.warning(f"清理推演标签页失败: {e}")

                # 清理典籍标签页
                if hasattr(self, 'library_tab') and self.library_tab:
                    try:
                        if hasattr(self.library_tab, 'cleanup'):
                            self.library_tab.cleanup()
                        self.logger.debug("典籍标签页已清理")
                    except Exception as e:
                        self.logger.warning(f"清理典籍标签页失败: {e}")

                # 清理洞察标签页
                if hasattr(self, 'insight_tab') and self.insight_tab:
                    try:
                        if hasattr(self.insight_tab, 'cleanup'):
                            self.insight_tab.cleanup()
                        self.logger.debug("洞察标签页已清理")
                    except Exception as e:
                        self.logger.warning(f"清理洞察标签页失败: {e}")

                # 清理历史记录标签页
                if hasattr(self, 'history_tab') and self.history_tab:
                    try:
                        self.history_tab.cleanup()
                        self.logger.debug("历史记录标签页已清理")
                    except Exception as e:
                        self.logger.warning(f"清理历史记录标签页失败: {e}")

                # 清理设置标签页
                if hasattr(self, 'settings_tab') and self.settings_tab:
                    try:
                        self.settings_tab.cleanup()
                        self.logger.debug("设置标签页已清理")
                    except Exception as e:
                        self.logger.warning(f"清理设置标签页失败: {e}")

                self.logger.info("资源清理完成，窗口即将关闭")
                event.accept()

            except Exception as e:
                self.logger.error(f"关闭窗口时发生错误: {e}")
                event.accept()  # 即使出错也允许关闭


def run_gui():
    """运行GUI应用"""
    if not HAS_PYQT6:
        print("=" * 60)
        print("PyQt6 未安装 - GUI界面不可用")
        print("=" * 60)
        print()
        print("解决方案:")
        print("  1. 安装PyQt6: pip install PyQt6")
        print("  2. 或使用CLI模式: python main.py --interactive")
        print()
        print("正在启动CLI模式...")
        print()
        _run_cli_fallback()
        return

    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


def _run_cli_fallback():
    """
    CLI降级模式 - 当GUI不可用时提供基本功能

    提供交互式命令行界面进行分析
    """
    import sys
    sys.path.insert(0, str(__file__).rsplit('/', 2)[0])  # 添加项目根目录

    try:
        from main import interactive_mode
        interactive_mode()
    except ImportError as e:
        print(f"无法启动CLI模式: {e}")
        print("请确保在项目根目录下运行")
    except KeyboardInterrupt:
        print("\n用户取消操作")
    except Exception as e:
        print(f"CLI模式运行出错: {e}")


if __name__ == "__main__":
    run_gui()
