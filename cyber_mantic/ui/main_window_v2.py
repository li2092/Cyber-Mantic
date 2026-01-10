"""
MainWindow V2 - 重构版主窗口

核心改进：
1. 使用新设计系统
2. 默认白色主题
3. 整合所有V2组件
4. 保持与后端服务的兼容性
"""

try:
    from PyQt6.QtWidgets import (
        QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFrame,
        QLabel, QStackedWidget, QMessageBox, QTextEdit, QPushButton,
        QApplication, QProgressBar
    )
    from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
    from PyQt6.QtGui import QFont, QIcon
    HAS_PYQT6 = True
except ImportError:
    HAS_PYQT6 = False

import asyncio

from datetime import datetime
from typing import Optional
from pathlib import Path

if HAS_PYQT6:
    # 导入后端服务
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

    # V2组件
    from ui.design_system_v2 import (
        spacing, font_size, border_radius, get_colors, StyleGenerator
    )
    from ui.components.sidebar_v2 import SidebarWidgetV2
    from ui.widgets.chat_widget_v2 import ChatWidgetV2
    from ui.widgets.stage_indicator import StageIndicatorBar
    from ui.widgets.theory_card_panel import TheoryCardPanel
    from ui.tabs.settings_tab_v2 import SettingsTabV2

    # 原有标签页（暂时保留）
    from ui.tabs import (
        AnalysisTab, HistoryTab, LibraryTab, InsightTab
    )

    # 免责声明
    from ui.dialogs import get_disclaimer_manager, OnboardingDialog


    class ChatInputEdit(QTextEdit):
        """支持Enter发送的输入框"""
        enter_pressed = pyqtSignal()

        def keyPressEvent(self, event):
            # Enter键发送（非Shift+Enter）
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                    self.enter_pressed.emit()
                    return
            super().keyPressEvent(event)


    class ConversationWorker(QThread):
        """异步对话工作线程"""
        # 信号
        response_ready = pyqtSignal(str)
        progress_updated = pyqtSignal(str, str, int)  # stage, message, progress
        theory_updated = pyqtSignal(str, str, dict)   # event_type, theory_name, data
        error_occurred = pyqtSignal(str)

        def __init__(self, conversation_service, user_message: str, is_start: bool = False):
            super().__init__()
            self.conversation_service = conversation_service
            self.user_message = user_message
            self.is_start = is_start
            self._loop = None

        def run(self):
            """执行异步操作"""
            try:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)

                if self.is_start:
                    # 开始新对话
                    result = self._loop.run_until_complete(
                        self.conversation_service.start_conversation(
                            progress_callback=self._progress_callback,
                            theory_callback=self._theory_callback
                        )
                    )
                else:
                    # 处理用户输入
                    result = self._loop.run_until_complete(
                        self.conversation_service.process_user_input(
                            self.user_message,
                            progress_callback=self._progress_callback,
                            theory_callback=self._theory_callback
                        )
                    )
                self.response_ready.emit(result)
            except Exception as e:
                self.error_occurred.emit(str(e))
            finally:
                if self._loop:
                    self._loop.close()

        def _progress_callback(self, stage: str, message: str, progress: int):
            """进度回调"""
            self.progress_updated.emit(stage, message, progress)

        def _theory_callback(self, event_type: str, theory_name: str, data: dict):
            """理论状态回调"""
            self.theory_updated.emit(event_type, theory_name, data or {})


    class MainWindowV2(QMainWindow):
        """主窗口 V2 - 默认白色主题"""

        def __init__(self):
            super().__init__()
            self.setWindowTitle("Cyber-Mantic 赛博玄数 - 多理论术数智能分析系统")
            self.setMinimumSize(1200, 800)

            # 主题设置 - 默认白色
            self.theme = "light"
            self.colors = get_colors(self.theme)
            self.style_gen = StyleGenerator(self.theme)

            # 加载配置
            self.config_manager = get_config_manager()
            self.config = self.config_manager.get_all_config()

            # 历史记录管理器
            self.history_manager = get_history_manager()

            # 创建决策引擎
            self.engine = DecisionEngine(self.config)

            # 初始化服务层
            self.logger = get_logger(__name__)
            self.api_manager = self.engine.api_manager
            self.conversation_service = ConversationService(self.api_manager)
            self.report_service = ReportService(self.api_manager)
            self.analysis_service = AnalysisService(self.engine)
            self.export_service = ExportService()

            # 免责声明管理器
            self.disclaimer_manager = get_disclaimer_manager()

            # Tab引用
            self.ai_conversation_widget: Optional[QWidget] = None
            self.analysis_tab: Optional[AnalysisTab] = None
            self.library_tab: Optional[LibraryTab] = None
            self.insight_tab: Optional[InsightTab] = None
            self.history_tab: Optional[HistoryTab] = None
            self.settings_tab: Optional[SettingsTabV2] = None

            # 对话状态
            self.conversation_worker: Optional[ConversationWorker] = None
            self.is_processing = False

            # 信息面板引用
            self.progress_bar: Optional[QProgressBar] = None
            self.progress_label: Optional[QLabel] = None
            self.theory_card_panel: Optional[TheoryCardPanel] = None
            self.stage_indicator: Optional[StageIndicatorBar] = None

            # 设置应用图标
            self._set_app_icon()

            # 初始化UI
            self._init_ui()

            # 应用主题
            self._apply_theme()

            # 检查API配置
            self._check_api_config()

        def _set_app_icon(self):
            """设置应用图标"""
            icon_path = Path(__file__).parent / "resources" / "app_icon.png"
            if icon_path.exists():
                icon = QIcon(str(icon_path))
                self.setWindowIcon(icon)
                self.logger.info(f"应用图标已加载: {icon_path}")

        def _init_ui(self):
            """初始化UI"""
            # 检查首次启动
            is_first_launch = self.disclaimer_manager.should_show_first_launch()
            if is_first_launch:
                if not self.disclaimer_manager.show_first_launch_disclaimer(self):
                    import sys
                    sys.exit(0)

            if is_first_launch and not self.config_manager.is_onboarding_completed():
                self._show_onboarding()

            # 主布局
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            main_layout = QHBoxLayout(central_widget)
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.setSpacing(0)

            # 左侧导航栏
            self.sidebar = SidebarWidgetV2(theme=self.theme)
            self.sidebar.navigation_changed.connect(self._on_navigation_changed)
            self.sidebar.font_size_changed.connect(self._on_global_font_size_changed)
            main_layout.addWidget(self.sidebar)

            # 右侧内容区
            self.content_stack = QStackedWidget()
            self.content_stack.setObjectName("contentStack")
            main_layout.addWidget(self.content_stack)

            # 页面映射
            self.nav_to_index = {}

            # 创建各页面
            self._create_pages()

            # 默认显示问道页面
            if "wendao" in self.nav_to_index:
                self.content_stack.setCurrentIndex(self.nav_to_index["wendao"])

        def _create_pages(self):
            """创建所有页面"""
            # 1. 问道页面（AI对话）
            try:
                self.ai_conversation_widget = self._create_wendao_page()
                idx = self.content_stack.addWidget(self.ai_conversation_widget)
                self.nav_to_index["wendao"] = idx
            except Exception as e:
                self.logger.error(f"问道页面初始化失败: {e}")
                self._add_placeholder_page("wendao", "问道")

            # 2. 推演页面
            try:
                self.analysis_tab = AnalysisTab(
                    self.analysis_service,
                    self.export_service,
                    self
                )
                self.analysis_tab.analysis_completed.connect(self._on_analysis_completed)
                idx = self.content_stack.addWidget(self.analysis_tab)
                self.nav_to_index["tuiyan"] = idx
            except Exception as e:
                self.logger.error(f"推演页面初始化失败: {e}")
                self._add_placeholder_page("tuiyan", "推演")

            # 3. 典籍页面
            try:
                self.library_tab = LibraryTab(api_manager=self.api_manager, parent=self)
                idx = self.content_stack.addWidget(self.library_tab)
                self.nav_to_index["dianji"] = idx
            except Exception as e:
                self.logger.error(f"典籍页面初始化失败: {e}")
                self._add_placeholder_page("dianji", "典籍")

            # 4. 洞察页面
            try:
                self.insight_tab = InsightTab(api_manager=self.api_manager, parent=self)
                idx = self.content_stack.addWidget(self.insight_tab)
                self.nav_to_index["dongcha"] = idx
            except Exception as e:
                self.logger.error(f"洞察页面初始化失败: {e}")
                self._add_placeholder_page("dongcha", "洞察")

            # 5. 历史记录页面
            try:
                self.history_tab = HistoryTab(self.history_manager, self)
                self.history_tab.report_selected.connect(self._on_history_report_selected)
                idx = self.content_stack.addWidget(self.history_tab)
                self.nav_to_index["lishi"] = idx
            except Exception as e:
                self.logger.error(f"历史记录页面初始化失败: {e}")
                self._add_placeholder_page("lishi", "历史记录")

            # 6. 设置页面 - 使用V2版本
            try:
                self.settings_tab = SettingsTabV2(
                    config_manager=self.config_manager,
                    api_manager=self.api_manager,
                    theme=self.theme,
                    parent=self
                )
                self.settings_tab.theme_changed.connect(self._on_theme_changed)
                self.settings_tab.config_saved.connect(self._on_config_saved)
                idx = self.content_stack.addWidget(self.settings_tab)
                self.nav_to_index["shezhi"] = idx
            except Exception as e:
                self.logger.error(f"设置页面初始化失败: {e}")
                self._add_placeholder_page("shezhi", "设置")

            # 7. 关于页面
            self._add_about_page()

        def _create_wendao_page(self) -> QWidget:
            """创建问道页面（聊天界面）"""
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)

            # 左侧：聊天区域
            chat_container = QWidget()
            chat_layout = QVBoxLayout(chat_container)
            chat_layout.setContentsMargins(0, 0, 0, 0)
            chat_layout.setSpacing(0)

            # 顶部工具栏
            toolbar = self._create_chat_toolbar()
            chat_layout.addWidget(toolbar)

            # 五阶段指示条
            self.stage_indicator = StageIndicatorBar(theme=self.theme)
            self.stage_indicator.stage_clicked.connect(self._on_stage_indicator_clicked)
            chat_layout.addWidget(self.stage_indicator)

            # 聊天消息区域
            self.chat_widget = ChatWidgetV2(theme=self.theme)
            chat_layout.addWidget(self.chat_widget, 1)

            # 底部输入区域
            input_area = self._create_input_area()
            chat_layout.addWidget(input_area)

            layout.addWidget(chat_container, 7)

            # 右侧：信息面板
            info_panel = self._create_info_panel()
            layout.addWidget(info_panel, 3)

            return widget

        def _create_chat_toolbar(self) -> QFrame:
            """创建聊天工具栏"""
            toolbar = QFrame()
            toolbar.setFixedHeight(56)
            toolbar.setStyleSheet(f"""
                QFrame {{
                    background-color: {self.colors['primary_bg']};
                    border-bottom: 1px solid {self.colors['border']};
                }}
            """)

            layout = QHBoxLayout(toolbar)
            layout.setContentsMargins(spacing.md, spacing.sm, spacing.md, spacing.sm)
            layout.setSpacing(spacing.sm)

            # 新对话按钮
            new_btn = QPushButton("✨ 新对话")
            new_btn.setFixedHeight(38)
            new_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            new_btn.clicked.connect(self._on_new_conversation)
            new_btn.setStyleSheet(self.style_gen.button_primary())
            layout.addWidget(new_btn)

            # 保存按钮
            self.save_btn = QPushButton("💾 保存对话")
            self.save_btn.setEnabled(False)
            self.save_btn.setFixedHeight(38)
            self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.save_btn.clicked.connect(self._on_save_conversation)
            self.save_btn.setStyleSheet(self.style_gen.button_secondary())
            layout.addWidget(self.save_btn)

            layout.addStretch()

            return toolbar

        def _create_input_area(self) -> QFrame:
            """创建输入区域"""
            container = QFrame()
            container.setStyleSheet(f"background-color: {self.colors['bg_secondary']};")

            layout = QVBoxLayout(container)
            layout.setContentsMargins(spacing.md, spacing.sm, spacing.md, spacing.md)
            layout.setSpacing(spacing.sm)

            row = QHBoxLayout()
            row.setSpacing(spacing.sm)

            # 输入框（使用自定义类支持Enter发送）
            self.input_text = ChatInputEdit(self)
            self.input_text.setPlaceholderText("输入您想咨询的问题... (Enter发送，Shift+Enter换行)")
            self.input_text.setFixedHeight(60)
            self.input_text.setStyleSheet(self.style_gen.input_text())
            self.input_text.enter_pressed.connect(self._on_send_message)
            row.addWidget(self.input_text)

            # 发送按钮
            self.send_btn = QPushButton("发送")
            self.send_btn.setFixedSize(80, 60)
            self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.send_btn.clicked.connect(self._on_send_message)
            self.send_btn.setStyleSheet(self.style_gen.button_primary())
            row.addWidget(self.send_btn)

            layout.addLayout(row)
            return container

        def _create_info_panel(self) -> QFrame:
            """创建右侧信息面板"""
            panel = QFrame()
            panel.setMinimumWidth(280)
            panel.setMaximumWidth(350)
            panel.setStyleSheet(f"""
                QFrame {{
                    background-color: {self.colors['bg_secondary']};
                    border-left: 1px solid {self.colors['border']};
                }}
            """)

            layout = QVBoxLayout(panel)
            layout.setContentsMargins(spacing.md, spacing.md, spacing.md, spacing.md)
            layout.setSpacing(spacing.md)

            # 进度条卡片
            progress_card = self._create_progress_card()
            layout.addWidget(progress_card)

            # 理论分析卡片面板（新版）
            self.theory_card_panel = TheoryCardPanel(theme=self.theme)
            layout.addWidget(self.theory_card_panel)

            layout.addStretch()

            return panel

        def _create_progress_card(self) -> QFrame:
            """创建进度卡片"""
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: {self.colors['card_bg']};
                    border: 1px solid {self.colors['card_border']};
                    border-radius: {border_radius.md}px;
                }}
            """)

            layout = QVBoxLayout(card)
            layout.setContentsMargins(spacing.md, spacing.sm, spacing.md, spacing.sm)
            layout.setSpacing(spacing.sm)

            title_label = QLabel("📊 分析进度")
            title_label.setFont(QFont("Microsoft YaHei", font_size.sm, QFont.Weight.Bold))
            title_label.setStyleSheet(f"color: {self.colors['text_primary']}; background: transparent; border: none;")
            layout.addWidget(title_label)

            # 进度条
            self.progress_bar = QProgressBar()
            self.progress_bar.setMinimum(0)
            self.progress_bar.setMaximum(100)
            self.progress_bar.setValue(0)
            self.progress_bar.setFixedHeight(8)
            self.progress_bar.setTextVisible(False)
            self.progress_bar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: {self.colors['border']};
                    border: none;
                    border-radius: 4px;
                }}
                QProgressBar::chunk {{
                    background-color: {self.colors['accent']};
                    border-radius: 4px;
                }}
            """)
            layout.addWidget(self.progress_bar)

            # 进度文字
            self.progress_label = QLabel("等待开始...")
            self.progress_label.setWordWrap(True)
            self.progress_label.setStyleSheet(f"color: {self.colors['text_secondary']}; background: transparent; border: none;")
            layout.addWidget(self.progress_label)

            return card

        def _on_stage_indicator_clicked(self, stage: int):
            """阶段指示条点击回调"""
            self.logger.debug(f"阶段指示条点击: 阶段 {stage}")

        def _create_info_card(self, title: str, content: str) -> QFrame:
            """创建信息卡片"""
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: {self.colors['card_bg']};
                    border: 1px solid {self.colors['card_border']};
                    border-radius: {border_radius.md}px;
                }}
            """)

            layout = QVBoxLayout(card)
            layout.setContentsMargins(spacing.md, spacing.sm, spacing.md, spacing.sm)
            layout.setSpacing(spacing.sm)

            title_label = QLabel(title)
            title_label.setFont(QFont("Microsoft YaHei", font_size.sm, QFont.Weight.Bold))
            title_label.setStyleSheet(f"color: {self.colors['text_primary']}; background: transparent;")
            layout.addWidget(title_label)

            content_label = QLabel(content)
            content_label.setWordWrap(True)
            content_label.setStyleSheet(f"color: {self.colors['text_secondary']}; background: transparent;")
            layout.addWidget(content_label)

            return card

        def _add_placeholder_page(self, nav_id: str, name: str):
            """添加占位页面"""
            placeholder = QWidget()
            layout = QVBoxLayout(placeholder)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            label = QLabel(f"📋 {name}页面加载失败")
            label.setStyleSheet(f"font-size: 18px; color: {self.colors['text_muted']};")
            layout.addWidget(label)

            hint = QLabel("请检查日志获取详细错误信息")
            hint.setStyleSheet(f"font-size: 12px; color: {self.colors['text_muted']};")
            layout.addWidget(hint)

            idx = self.content_stack.addWidget(placeholder)
            self.nav_to_index[nav_id] = idx

        def _add_about_page(self):
            """添加关于页面"""
            from PyQt6.QtGui import QPixmap

            about_widget = QWidget()
            about_widget.setStyleSheet(f"background-color: {self.colors['bg_primary']};")

            layout = QVBoxLayout(about_widget)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.setSpacing(16)
            layout.setContentsMargins(40, 40, 40, 40)

            # Logo - 使用真实图片
            logo_label = QLabel()
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            logo_label.setFixedSize(120, 120)
            logo_path = Path(__file__).parent / "resources" / "app_icon.png"
            if logo_path.exists():
                pixmap = QPixmap(str(logo_path))
                scaled = pixmap.scaled(
                    100, 100,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                logo_label.setPixmap(scaled)
            else:
                logo_label.setText("🔮")
                logo_label.setFont(QFont("Segoe UI Emoji", 48))
            layout.addWidget(logo_label)

            # 名称
            name_label = QLabel("赛博玄数")
            name_label.setFont(QFont("Microsoft YaHei", 28, QFont.Weight.Bold))
            name_label.setStyleSheet(f"color: {self.colors['text_primary']}; background: transparent;")
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(name_label)

            # 英文名
            en_label = QLabel("Cyber Mantic")
            en_font = QFont("Segoe UI", 14)
            en_font.setItalic(True)
            en_label.setFont(en_font)
            en_label.setStyleSheet(f"color: {self.colors['text_muted']}; background: transparent;")
            en_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(en_label)

            # 版本
            version_label = QLabel("V2.0")
            version_label.setStyleSheet(f"color: {self.colors['text_muted']}; font-size: 12px; background: transparent;")
            version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(version_label)

            layout.addSpacing(20)

            # 描述
            desc_label = QLabel("多理论术数智能分析系统")
            desc_label.setStyleSheet(f"color: {self.colors['text_secondary']}; font-size: 14px; background: transparent;")
            desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(desc_label)

            layout.addSpacing(10)

            # 详细介绍卡片
            intro_card = QFrame()
            intro_card.setStyleSheet(f"""
                QFrame {{
                    background-color: {self.colors['card_bg']};
                    border: 1px solid {self.colors['card_border']};
                    border-radius: {border_radius.md}px;
                }}
            """)
            intro_layout = QVBoxLayout(intro_card)
            intro_layout.setContentsMargins(20, 16, 20, 16)
            intro_layout.setSpacing(12)

            intro_title = QLabel("📖 系统介绍")
            intro_title.setFont(QFont("Microsoft YaHei", font_size.md, QFont.Weight.Bold))
            intro_title.setStyleSheet(f"color: {self.colors['text_primary']}; background: transparent;")
            intro_layout.addWidget(intro_title)

            intro_text = QLabel(
                "赛博玄数是一款融合传统术数智慧与现代AI技术的智能分析系统。\n\n"
                "支持的术数理论：\n"
                "• 小六壬 - 快速起卦，简洁明了\n"
                "• 测字术 - 字形字义，洞察玄机\n"
                "• 八字命理 - 四柱八字，命运分析\n"
                "• 紫微斗数 - 星曜格局，人生蓝图\n"
                "• 奇门遁甲 - 时空奥秘，决策参考\n"
                "• 大六壬 - 课传变化，事理推演\n"
                "• 六爻 - 周易占卜，吉凶判断\n"
                "• 梅花易数 - 象数结合，灵活应用"
            )
            intro_text.setWordWrap(True)
            intro_text.setStyleSheet(f"color: {self.colors['text_secondary']}; font-size: 13px; line-height: 1.6; background: transparent;")
            intro_layout.addWidget(intro_text)

            layout.addWidget(intro_card)

            layout.addSpacing(20)

            # 免责声明
            disclaimer = QLabel("⚠️ 仅供参考，不构成任何决策建议")
            disclaimer.setStyleSheet(f"color: {self.colors['warning']}; font-size: 12px; background: transparent;")
            disclaimer.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(disclaimer)

            layout.addStretch()

            idx = self.content_stack.addWidget(about_widget)
            self.nav_to_index["about"] = idx

        def _apply_theme(self):
            """应用主题"""
            try:
                # 应用全局样式
                self.setStyleSheet(f"""
                    QMainWindow {{
                        background-color: {self.colors['bg_secondary']};
                    }}
                    {self.style_gen.global_stylesheet()}
                """)
                self.logger.info(f"主题已应用: {self.theme}")
            except Exception as e:
                self.logger.error(f"主题应用失败: {e}")

        def _on_navigation_changed(self, nav_id: str):
            """导航切换"""
            if nav_id in self.nav_to_index:
                self.content_stack.setCurrentIndex(self.nav_to_index[nav_id])
                self.logger.debug(f"切换到页面: {nav_id}")

        def _on_global_font_size_changed(self, size: int):
            """全局字体大小变化"""
            self.logger.debug(f"全局字体大小调整为: {size}px")

            # 更新问道对话界面
            if hasattr(self, 'ai_conversation_tab') and self.ai_conversation_tab:
                if hasattr(self.ai_conversation_tab, 'set_font_size'):
                    self.ai_conversation_tab.set_font_size(size)

            # 更新推演报告界面
            if hasattr(self, 'analysis_tab') and self.analysis_tab:
                if hasattr(self.analysis_tab, 'set_font_size'):
                    self.analysis_tab.set_font_size(size)

            # 更新洞察界面
            if hasattr(self, 'insight_tab') and self.insight_tab:
                if hasattr(self.insight_tab, 'set_font_size'):
                    self.insight_tab.set_font_size(size)

            # 更新历史记录界面
            if hasattr(self, 'history_tab') and self.history_tab:
                if hasattr(self.history_tab, 'set_font_size'):
                    self.history_tab.set_font_size(size)

        def _on_theme_changed(self, theme: str):
            """主题切换"""
            self.theme = theme
            self.colors = get_colors(theme)
            self.style_gen.set_theme(theme)
            self._apply_theme()

            # 更新各组件主题
            self.sidebar.set_theme(theme)
            if hasattr(self, 'chat_widget'):
                self.chat_widget.set_theme(theme)
            if hasattr(self, 'stage_indicator') and self.stage_indicator:
                self.stage_indicator.set_theme(theme)
            if hasattr(self, 'theory_card_panel') and self.theory_card_panel:
                self.theory_card_panel.set_theme(theme)

            QMessageBox.information(
                self, "主题已更改",
                f"主题已切换为：{'浅色' if theme == 'light' else '深色'}\n\n部分组件可能需要重启应用程序才能完全生效。"
            )

        def _on_config_saved(self):
            """配置保存后刷新"""
            try:
                self.config_manager = reload_config()
                self.config = self.config_manager.get_all_config()
                self.engine = DecisionEngine(self.config)
                self.api_manager = self.engine.api_manager
                self.conversation_service = ConversationService(self.api_manager)
                self.logger.info("配置已重新加载")
            except Exception as e:
                self.logger.error(f"重新加载配置失败: {e}")

        def _on_new_conversation(self):
            """新对话"""
            if self.is_processing:
                QMessageBox.warning(self, "提示", "正在处理中，请稍候...")
                return

            if self.chat_widget.get_messages():
                reply = QMessageBox.question(
                    self, "确认",
                    "开始新对话将清空当前内容。是否继续？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return

            # 清空界面
            self.chat_widget.clear_messages()
            self.conversation_service.reset()
            self.save_btn.setEnabled(False)

            # 重置信息面板
            self._reset_info_panel()
            if self.theory_card_panel:
                self.theory_card_panel.reset_all()

            # 启动新对话
            self._start_conversation()

        def _start_conversation(self):
            """启动新对话（调用后端服务）"""
            self.is_processing = True
            self._update_ui_state(processing=True)

            self.conversation_worker = ConversationWorker(
                self.conversation_service,
                user_message="",
                is_start=True
            )
            self.conversation_worker.response_ready.connect(self._on_conversation_response)
            self.conversation_worker.progress_updated.connect(self._on_progress_updated)
            self.conversation_worker.theory_updated.connect(self._on_theory_updated)
            self.conversation_worker.error_occurred.connect(self._on_conversation_error)
            self.conversation_worker.finished.connect(self._on_worker_finished)
            self.conversation_worker.start()

        def _on_send_message(self):
            """发送消息"""
            text = self.input_text.toPlainText().strip()
            if not text:
                return

            if self.is_processing:
                QMessageBox.warning(self, "提示", "正在处理中，请稍候...")
                return

            # 显示用户消息
            self.chat_widget.add_user_message(text)
            self.input_text.clear()
            self.save_btn.setEnabled(True)

            # 调用后端服务
            self._process_user_message(text)

        def _process_user_message(self, message: str):
            """处理用户消息（调用后端服务）"""
            self.is_processing = True
            self._update_ui_state(processing=True)

            self.conversation_worker = ConversationWorker(
                self.conversation_service,
                user_message=message,
                is_start=False
            )
            self.conversation_worker.response_ready.connect(self._on_conversation_response)
            self.conversation_worker.progress_updated.connect(self._on_progress_updated)
            self.conversation_worker.theory_updated.connect(self._on_theory_updated)
            self.conversation_worker.error_occurred.connect(self._on_conversation_error)
            self.conversation_worker.finished.connect(self._on_worker_finished)
            self.conversation_worker.start()

        def _on_conversation_response(self, response: str):
            """处理对话响应"""
            self.chat_widget.add_assistant_message(response, animated=True)
            self.logger.debug(f"对话响应: {response[:100]}...")

        def _on_progress_updated(self, stage: str, message: str, progress: int):
            """处理进度更新"""
            if self.progress_bar:
                self.progress_bar.setValue(progress)
            if self.progress_label:
                self.progress_label.setText(f"{stage}: {message}")

            # 同步阶段指示条
            if self.stage_indicator:
                stage_map = {
                    "破冰阶段": 1, "阶段1": 1, "小六壬": 1,
                    "深入阶段": 2, "阶段2": 2, "测字术": 2,
                    "信息收集": 3, "阶段3": 3, "收集信息": 3,
                    "回溯验证": 4, "阶段4": 4, "验证": 4,
                    "生成报告": 5, "阶段5": 5, "报告": 5,
                }
                for key, stage_num in stage_map.items():
                    if key in stage:
                        self.stage_indicator.set_current_stage(stage_num)
                        break

        def _on_theory_updated(self, event_type: str, theory_name: str, data: dict):
            """处理理论状态更新"""
            if self.theory_card_panel:
                self.theory_card_panel.update_theory_status(theory_name, event_type, data)

        def _on_conversation_error(self, error_msg: str):
            """处理对话错误"""
            self.logger.error(f"对话错误: {error_msg}")
            self.chat_widget.add_assistant_message(
                f"⚠️ 抱歉，处理过程中遇到问题：{error_msg}\n\n请重试或检查网络连接。",
                animated=False
            )

        def _on_worker_finished(self):
            """工作线程完成"""
            self.is_processing = False
            self._update_ui_state(processing=False)
            self.conversation_worker = None

        def _update_ui_state(self, processing: bool):
            """更新UI状态"""
            self.send_btn.setEnabled(not processing)
            self.input_text.setEnabled(not processing)
            if processing:
                self.send_btn.setText("处理中...")
            else:
                self.send_btn.setText("发送")

        def _reset_info_panel(self):
            """重置信息面板"""
            if self.progress_bar:
                self.progress_bar.setValue(0)
            if self.progress_label:
                self.progress_label.setText("等待开始...")
            if self.stage_indicator:
                self.stage_indicator.reset()

        def _on_save_conversation(self):
            """保存对话"""
            try:
                # 获取对话数据
                conversation_data = self.conversation_service.save_conversation()

                if conversation_data:
                    # 保存到JSON文件
                    import json
                    save_dir = Path("data/user/conversations")
                    save_dir.mkdir(parents=True, exist_ok=True)

                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    question_type = conversation_data.get("summary", {}).get("question_category", "unknown")
                    filename = f"conversation_{timestamp}_{question_type}.json"
                    save_path = save_dir / filename

                    with open(save_path, "w", encoding="utf-8") as f:
                        json.dump(conversation_data, f, ensure_ascii=False, indent=2)

                    QMessageBox.information(
                        self, "保存成功",
                        f"对话已保存！\n\n保存路径：{save_path}"
                    )
                    self.save_btn.setEnabled(False)
                    self.logger.info(f"对话已保存到: {save_path}")
                else:
                    QMessageBox.warning(self, "保存失败", "没有可保存的对话内容。")

            except Exception as e:
                self.logger.error(f"保存对话失败: {e}")
                QMessageBox.warning(self, "保存失败", f"保存对话时出错：{str(e)}")

        def _on_analysis_completed(self, report: ComprehensiveReport):
            """分析完成"""
            if self.history_tab:
                self.history_tab._refresh_history()
            self.logger.info(f"分析完成，报告ID: {report.report_id}")

        def _on_history_report_selected(self, report: ComprehensiveReport):
            """查看历史报告"""
            if self.analysis_tab:
                self.analysis_tab.display_report(report)
                if "tuiyan" in self.nav_to_index:
                    self.content_stack.setCurrentIndex(self.nav_to_index["tuiyan"])
                    self.sidebar.set_current_nav("tuiyan")

        def _check_api_config(self):
            """检查API配置"""
            if not self.config_manager.has_valid_api_key():
                QMessageBox.warning(
                    self, "配置提示",
                    "检测到尚未配置 API 密钥！\n\n"
                    "请前往\"设置\"页面配置至少一个 AI API 密钥才能使用分析功能。"
                )

        def _show_onboarding(self):
            """显示引导"""
            try:
                dialog = OnboardingDialog(self)
                dialog.completed.connect(lambda: self.config_manager.set_onboarding_completed(True))
                dialog.exec()
            except Exception as e:
                self.logger.warning(f"显示引导对话框失败: {e}")

        def closeEvent(self, event):
            """关闭事件"""
            self.logger.info("正在关闭主窗口...")

            # 清理各标签页
            for tab in [self.analysis_tab, self.history_tab, self.library_tab,
                       self.insight_tab, self.settings_tab]:
                if tab and hasattr(tab, 'cleanup'):
                    try:
                        tab.cleanup()
                    except Exception as e:
                        self.logger.warning(f"清理标签页失败: {e}")

            event.accept()


def run_gui_v2():
    """运行V2版GUI"""
    if not HAS_PYQT6:
        print("PyQt6 未安装 - GUI界面不可用")
        return

    import sys
    app = QApplication(sys.argv)

    # 设置全局字体
    font = QFont("Microsoft YaHei", font_size.base)
    app.setFont(font)

    window = MainWindowV2()
    window.show()

    # 自动开始新对话
    QTimer.singleShot(500, window._on_new_conversation)

    sys.exit(app.exec())


if __name__ == "__main__":
    run_gui_v2()
