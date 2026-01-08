"""
AIConversationTab - 纯AI对话模式标签页

实现渐进式5阶段智能交互流程：
1. 阶段1_破冰：事项分类 + 3个随机数字 → 小六壬快速初判
2. 阶段2_基础信息：出生年月日、性别、MBTI → Kimi解析 + 八字验证 → 展示可用理论
3. 阶段3_深度补充：时辰推断（兄弟姐妹、脸型、作息）+ 补充占卜（六爻、梅花）
4. 阶段4_结果确认：回溯验证（过去3-5年关键事件）→ 置信度调整
5. 阶段5_完整报告：AI综合分析 + 行动建议 + 持续问答

特点：
- Kimi进行出生信息自然语言解析（三级时辰分类：确定/不确定/未知）
- BaZiCalculator验证八字准确性（三层回退：Kimi → 八字验证 → 代码解析）
- 多理论融合分析（八字、紫微、奇门、六壬、六爻、梅花、小六壬、测字）
- 智能问题分类（八字详情、建议、预测、理论解释、通用）
- 对话管理工具（摘要、统计、进度追踪、Markdown导出）
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QTextBrowser,
    QPushButton, QSplitter, QLabel, QGroupBox, QFrame, QMessageBox, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QEvent
from PyQt6.QtGui import QFont, QKeyEvent
from typing import Optional
import asyncio
import json

from ui.widgets.chat_widget import ChatWidget
from ui.widgets.progress_widget import ProgressWidget
from ui.widgets.quick_result_card import QuickResultPanel
from services.conversation_service import ConversationService, ConversationStage
from api.manager import APIManager
from utils.logger import get_logger
from utils.warning_manager import get_warning_manager, WarningLevel
from ui.dialogs.warning_dialogs import show_warning_dialog, ForcedCoolingDialog


class ConversationWorker(QThread):
    """对话异步工作线程"""
    # 现有信号
    message_received = pyqtSignal(str)  # AI回复消息
    progress_updated = pyqtSignal(str, str, int)  # (stage, message, progress)
    error = pyqtSignal(str)

    # V2新增信号：理论分析进度
    theory_started = pyqtSignal(str)           # 理论开始计算（theory_name）
    theory_completed = pyqtSignal(str, dict)   # 理论完成（theory_name, result）
    quick_result = pyqtSignal(str, str, str)   # 快速结果（theory_name, summary, judgment）

    def __init__(self, service: ConversationService, user_message: str, is_start: bool = False):
        super().__init__()
        self.service = service
        self.user_message = user_message
        self.is_start = is_start
        self._is_cancelled = False  # 取消标志

    def cancel(self):
        """取消任务"""
        self._is_cancelled = True

    def run(self):
        """执行异步对话"""
        try:
            # 检查是否已取消
            if self._is_cancelled:
                return

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # 如果是开始新对话，调用start_conversation
            if self.is_start:
                response = loop.run_until_complete(
                    self.service.start_conversation(
                        progress_callback=self.emit_progress,
                        theory_callback=self.emit_theory_update
                    )
                )
            else:
                response = loop.run_until_complete(
                    self.service.process_user_input(
                        self.user_message,
                        progress_callback=self.emit_progress,
                        theory_callback=self.emit_theory_update
                    )
                )

            loop.close()

            # 检查是否已取消
            if self._is_cancelled:
                return

            self.message_received.emit(response)

        except Exception as e:
            if not self._is_cancelled:
                self.error.emit(str(e))

    def emit_progress(self, stage: str, message: str, progress: int):
        """发送进度信号"""
        self.progress_updated.emit(stage, message, progress)

    def emit_theory_update(self, event_type: str, theory_name: str, data: dict = None):
        """
        发送理论分析更新信号

        Args:
            event_type: 事件类型 ('started', 'completed', 'quick_result')
            theory_name: 理论名称
            data: 附加数据（completed时为结果，quick_result时为摘要信息）
        """
        if self._is_cancelled:
            return

        if event_type == 'started':
            self.theory_started.emit(theory_name)
        elif event_type == 'completed':
            self.theory_completed.emit(theory_name, data or {})
            # 同时发送快速结果
            summary = data.get('summary', '分析完成') if data else '分析完成'
            judgment = data.get('judgment', '平') if data else '平'
            self.quick_result.emit(theory_name, summary, judgment)
        elif event_type == 'quick_result':
            summary = data.get('summary', '') if data else ''
            judgment = data.get('judgment', '平') if data else '平'
            self.quick_result.emit(theory_name, summary, judgment)


class AIConversationTab(QWidget):
    """纯AI对话模式标签页"""

    # 信号：需要保存对话
    save_requested = pyqtSignal(dict)  # 对话数据

    def __init__(self, api_manager: APIManager, parent=None):
        super().__init__(parent)
        self.api_manager = api_manager
        self.conversation_service = ConversationService(api_manager)
        self.logger = get_logger(__name__)
        self.worker = None  # 当前工作线程
        self._setup_ui()
        # 安装事件过滤器以支持回车发送
        self.input_text.installEventFilter(self)
        self._start_new_conversation()

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 分屏器：左侧对话，右侧关键信息
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧：对话区域
        left_widget = self._create_left_panel()
        splitter.addWidget(left_widget)

        # 右侧：关键信息显示
        right_widget = self._create_right_panel()
        right_widget.setMinimumWidth(280)  # 调窄右侧最小宽度
        right_widget.setMaximumWidth(380)  # 限制右侧最大宽度
        splitter.addWidget(right_widget)

        # 设置初始比例（左侧65%，右侧35%） - 给对话区域更多空间
        splitter.setStretchFactor(0, 65)
        splitter.setStretchFactor(1, 35)
        # 设置初始大小（如果窗口宽度为1200，左820右380）
        splitter.setSizes([820, 380])

        layout.addWidget(splitter)
        self.setLayout(layout)

    def _create_left_panel(self) -> QWidget:
        """创建左侧对话面板 - V2美化版"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ========== 顶部工具栏 ==========
        toolbar = QFrame()
        toolbar.setObjectName("chatToolbar")
        toolbar.setStyleSheet("""
            QFrame#chatToolbar {
                background-color: rgba(99, 102, 241, 0.08);
                border-bottom: 1px solid rgba(99, 102, 241, 0.15);
                padding: 8px 16px;
            }
        """)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(16, 10, 16, 10)
        toolbar_layout.setSpacing(12)

        # 新对话按钮（左侧，更醒目）
        self.new_conversation_btn = QPushButton("✨ 新对话")
        self.new_conversation_btn.setMinimumHeight(38)
        self.new_conversation_btn.setMinimumWidth(100)
        self.new_conversation_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.new_conversation_btn.clicked.connect(self._on_new_conversation_clicked)
        self.new_conversation_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #8B5CF6, stop:1 #6366F1);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #A78BFA, stop:1 #818CF8);
            }
            QPushButton:pressed {
                background: #6366F1;
            }
        """)
        toolbar_layout.addWidget(self.new_conversation_btn)

        # 保存对话按钮
        self.save_btn = QPushButton("💾 保存对话")
        self.save_btn.setEnabled(False)
        self.save_btn.setMinimumHeight(38)
        self.save_btn.setMinimumWidth(100)
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.clicked.connect(self._on_save_clicked)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(16, 185, 129, 0.15);
                color: #10B981;
                border: 1px solid rgba(16, 185, 129, 0.3);
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(16, 185, 129, 0.25);
                border-color: #10B981;
            }
            QPushButton:disabled {
                background-color: rgba(148, 163, 184, 0.1);
                color: #94A3B8;
                border-color: rgba(148, 163, 184, 0.2);
            }
        """)
        toolbar_layout.addWidget(self.save_btn)

        toolbar_layout.addStretch()

        # 字体调节按钮（右侧，更小巧）
        font_frame = QFrame()
        font_layout = QHBoxLayout(font_frame)
        font_layout.setContentsMargins(0, 0, 0, 0)
        font_layout.setSpacing(4)

        font_btn_style = """
            QPushButton {
                background-color: rgba(148, 163, 184, 0.1);
                color: #94A3B8;
                border: none;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(148, 163, 184, 0.2);
                color: #E2E8F0;
            }
        """

        self.chat_font_decrease_btn = QPushButton("A-")
        self.chat_font_decrease_btn.setFixedSize(32, 28)
        self.chat_font_decrease_btn.setToolTip("缩小字体")
        self.chat_font_decrease_btn.clicked.connect(self._decrease_chat_font)
        self.chat_font_decrease_btn.setStyleSheet(font_btn_style)
        font_layout.addWidget(self.chat_font_decrease_btn)

        self.chat_font_reset_btn = QPushButton("↺")
        self.chat_font_reset_btn.setFixedSize(28, 28)
        self.chat_font_reset_btn.setToolTip("重置字体")
        self.chat_font_reset_btn.clicked.connect(self._reset_chat_font)
        self.chat_font_reset_btn.setStyleSheet(font_btn_style)
        font_layout.addWidget(self.chat_font_reset_btn)

        self.chat_font_increase_btn = QPushButton("A+")
        self.chat_font_increase_btn.setFixedSize(32, 28)
        self.chat_font_increase_btn.setToolTip("放大字体")
        self.chat_font_increase_btn.clicked.connect(self._increase_chat_font)
        self.chat_font_increase_btn.setStyleSheet(font_btn_style)
        font_layout.addWidget(self.chat_font_increase_btn)

        toolbar_layout.addWidget(font_frame)

        layout.addWidget(toolbar)

        # 初始化字体大小
        self.chat_font_size = 11  # 默认11pt

        # ========== 聊天消息区域 ==========
        chat_container = QWidget()
        chat_layout = QVBoxLayout(chat_container)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)

        self.chat_widget = ChatWidget()
        chat_layout.addWidget(self.chat_widget)

        layout.addWidget(chat_container, 1)  # 占用剩余空间

        # ========== 底部输入区域 ==========
        input_container = QFrame()
        input_container.setObjectName("inputContainer")
        input_container.setStyleSheet("""
            QFrame#inputContainer {
                background-color: transparent;
                border: none;
            }
        """)
        input_main_layout = QVBoxLayout(input_container)
        input_main_layout.setContentsMargins(16, 12, 16, 12)
        input_main_layout.setSpacing(8)

        # 输入框 + 发送按钮
        input_row = QHBoxLayout()
        input_row.setSpacing(12)

        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("输入您想咨询的问题... (Enter发送，Shift+Enter换行)")
        self.input_text.setMinimumHeight(50)
        self.input_text.setMaximumHeight(120)
        self.input_text.setStyleSheet("""
            QTextEdit {
                background-color: #2D2D3D;
                border: 1px solid rgba(99, 102, 241, 0.3);
                border-radius: 12px;
                padding: 12px 16px;
                color: #F1F5F9;
                font-size: 14px;
            }
            QTextEdit:focus {
                border-color: #6366F1;
                background-color: #33334D;
            }
        """)
        input_row.addWidget(self.input_text)

        self.send_btn = QPushButton("发送")
        self.send_btn.setFixedSize(80, 50)
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.clicked.connect(self._on_send_clicked)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #6366F1, stop:1 #4F46E5);
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #818CF8, stop:1 #6366F1);
            }
            QPushButton:pressed {
                background: #4F46E5;
            }
            QPushButton:disabled {
                background: #475569;
                color: #94A3B8;
            }
        """)
        input_row.addWidget(self.send_btn)

        input_main_layout.addLayout(input_row)

        layout.addWidget(input_container)

        widget.setLayout(layout)
        return widget

    def _create_right_panel(self) -> QWidget:
        """创建右侧关键信息面板（添加滚动条，防止挤压进度条）"""
        # 创建滚动区域容器 - 保存引用以便进度更新时滚动到顶部
        self.right_panel_scroll_area = QScrollArea()
        scroll_area = self.right_panel_scroll_area
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        # 创建内容widget
        content_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # 标题
        title_label = QLabel("📊 关键信息")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # ===== 小六壬结果卡片 (顶部) =====
        xiaoliu_group = QGroupBox("🎯 小六壬快断")
        xiaoliu_layout = QVBoxLayout()
        self.xiaoliu_text = QTextBrowser()
        self.xiaoliu_text.setReadOnly(True)
        self.xiaoliu_text.setFrameStyle(QFrame.Shape.NoFrame)
        self.xiaoliu_text.setMaximumHeight(120)
        self.xiaoliu_text.setMarkdown("_等待起卦..._")
        xiaoliu_layout.addWidget(self.xiaoliu_text)
        xiaoliu_group.setLayout(xiaoliu_layout)
        layout.addWidget(xiaoliu_group)

        # ===== V2: 快速结论卡片面板 =====
        self.quick_result_panel = QuickResultPanel(theme="dark")
        self.quick_result_panel.theory_clicked.connect(self._show_theory_detail)
        layout.addWidget(self.quick_result_panel)

        # 理论详情显示区（初始隐藏）
        self.theory_detail_text = QTextBrowser()
        self.theory_detail_text.setReadOnly(True)
        self.theory_detail_text.setFrameStyle(QFrame.Shape.NoFrame)
        self.theory_detail_text.setMaximumHeight(150)
        self.theory_detail_text.setMarkdown("_点击上方卡片查看理论详情_")
        self.theory_detail_text.hide()
        layout.addWidget(self.theory_detail_text)

        # 兼容性：保留theory_buttons字典（某些地方可能还在用）
        self.theory_buttons = {}

        # ===== 八字排盘结果组 =====
        bazi_group = QGroupBox("八字命盘")
        bazi_layout = QVBoxLayout()
        self.bazi_text = QTextBrowser()
        self.bazi_text.setReadOnly(True)
        self.bazi_text.setFrameStyle(QFrame.Shape.NoFrame)
        self.bazi_text.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.bazi_text.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.bazi_text.setMaximumHeight(200)
        self.bazi_text.setMarkdown("（暂无）")
        self.bazi_text.setStyleSheet("font-size: 10pt;")
        bazi_layout.addWidget(self.bazi_text)
        bazi_group.setLayout(bazi_layout)
        layout.addWidget(bazi_group)

        # 简要分析组
        analysis_group = QGroupBox("简要分析")
        analysis_layout = QVBoxLayout()
        self.analysis_text = QTextBrowser()
        self.analysis_text.setReadOnly(True)
        self.analysis_text.setFrameStyle(QFrame.Shape.NoFrame)
        self.analysis_text.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.analysis_text.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.analysis_text.setMaximumHeight(200)
        self.analysis_text.setMarkdown("（暂无）")
        self.analysis_text.setStyleSheet("font-size: 10pt;")
        analysis_layout.addWidget(self.analysis_text)
        analysis_group.setLayout(analysis_layout)
        layout.addWidget(analysis_group)

        # 分析状态组
        status_group = QGroupBox("分析状态")
        status_layout = QVBoxLayout()
        self.status_text = QTextBrowser()
        self.status_text.setReadOnly(True)
        self.status_text.setFrameStyle(QFrame.Shape.NoFrame)
        self.status_text.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.status_text.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.status_text.setMaximumHeight(150)
        self.status_text.setMarkdown("（等待开始）")
        self.status_text.setStyleSheet("font-size: 9pt;")
        status_layout.addWidget(self.status_text)
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # 当前阶段
        stage_group = QGroupBox("当前阶段")
        stage_layout = QVBoxLayout()
        self.stage_label = QLabel("等待用户输入...")
        self.stage_label.setWordWrap(True)
        self.stage_label.setProperty("heading", True)
        stage_layout.addWidget(self.stage_label)
        stage_group.setLayout(stage_layout)
        layout.addWidget(stage_group)

        # 移除 addStretch()，改为在底部添加进度条
        # 进度显示（固定在底部，初始隐藏）
        self.progress_widget = ProgressWidget()
        self.progress_widget.hide()
        layout.addWidget(self.progress_widget)

        # 添加弹性空间，使进度条始终在可见内容之后
        layout.addStretch()

        content_widget.setLayout(layout)

        # 将内容widget放入滚动区域
        scroll_area.setWidget(content_widget)

        return scroll_area

    def _start_new_conversation(self):
        """开始新对话"""
        self.logger.info("开始新的AI对话会话")

        # 停止当前正在运行的工作线程
        self._stop_current_worker()

        # 重置服务
        self.conversation_service.reset()

        # 清空UI
        self.chat_widget.clear_messages()
        self.input_text.clear()
        self.bazi_text.setMarkdown("（暂无）")
        self.analysis_text.setMarkdown("（暂无）")
        self.status_text.setMarkdown("（等待开始）")
        self.stage_label.setText("等待用户输入...")
        self.save_btn.setEnabled(False)
        # V2: 重置快速结论面板
        if hasattr(self, 'quick_result_panel'):
            self.quick_result_panel.reset_all()

        # 启动对话 - 使用is_start=True触发start_conversation
        self.worker = ConversationWorker(
            self.conversation_service,
            "",  # 空消息
            is_start=True  # 标记为开始新对话
        )
        self.worker.message_received.connect(self._on_welcome_message)
        self.worker.error.connect(self._on_error)
        # V2: 连接理论分析信号
        self.worker.theory_started.connect(self._on_theory_started)
        self.worker.quick_result.connect(self._on_quick_result)
        self.worker.start()

    def _on_welcome_message(self, message: str):
        """接收欢迎消息"""
        self.chat_widget.add_assistant_message(message)
        self.stage_label.setText("💬 等待您的输入")
        self.input_text.setFocus()

    def _on_send_clicked(self):
        """发送按钮点击"""
        user_message = self.input_text.toPlainText().strip()

        if not user_message:
            return

        # 检查是否处于锁定状态
        warning_manager = get_warning_manager()
        is_locked, lock_data = warning_manager.is_locked()
        if is_locked:
            care_message = warning_manager.get_care_message(WarningLevel.FORCED)
            dialog = ForcedCoolingDialog(care_message, self)
            dialog.exec()
            return

        # 检查文本中的情绪化关键词
        warning_level, matched_keywords = warning_manager.check_text_for_keywords(user_message)

        if warning_level != WarningLevel.NONE:
            care_message = warning_manager.get_care_message(warning_level)

            if warning_level == WarningLevel.FORCED:
                # 高危关键词：触发强制冷却
                warning_manager.set_lock(
                    reason="检测到高危情绪关键词",
                    trigger_keywords=matched_keywords
                )
                show_warning_dialog(warning_level, care_message, self)
                return

            elif warning_level == WarningLevel.PAUSE:
                # 中危关键词：暂停建议
                should_continue = show_warning_dialog(warning_level, care_message, self)
                if not should_continue:
                    # 用户选择休息
                    return

            else:
                # 低危关键词：关怀提示（不阻止）
                show_warning_dialog(warning_level, care_message, self)

        # 添加用户消息到聊天
        self.chat_widget.add_user_message(user_message)

        # 清空输入框
        self.input_text.clear()

        # 禁用发送按钮
        self.send_btn.setEnabled(False)
        self.send_btn.setText("处理中...")

        # 显示进度条（如果正在分析）
        # 在进行深度分析的阶段显示进度条
        analysis_stages = [
            ConversationStage.STAGE2_BASIC_INFO,
            ConversationStage.STAGE3_SUPPLEMENT,
            ConversationStage.STAGE4_VERIFICATION,
            ConversationStage.STAGE5_FINAL_REPORT
        ]
        if self.conversation_service.context.stage in analysis_stages:
            self.progress_widget.show()
            self.progress_widget.reset()

        # 停止当前正在运行的工作线程（防止重复发送）
        self._stop_current_worker()

        # 启动异步处理
        self.worker = ConversationWorker(self.conversation_service, user_message)
        self.worker.message_received.connect(self._on_message_received)
        self.worker.progress_updated.connect(self._on_progress_updated)
        self.worker.error.connect(self._on_error)
        # V2: 连接理论分析信号
        self.worker.theory_started.connect(self._on_theory_started)
        self.worker.quick_result.connect(self._on_quick_result)
        self.worker.start()

    def _on_message_received(self, message: str):
        """接收AI消息"""
        # 添加AI消息到聊天
        self.chat_widget.add_assistant_message(message)

        # 更新关键信息面板
        self._update_right_panel()

        # 隐藏进度条
        if self.progress_widget.isVisible():
            self.progress_widget.show_completion()
            self.progress_widget.hide()

        # 恢复发送按钮
        self.send_btn.setEnabled(True)
        self.send_btn.setText("发送")

        # 启用保存按钮
        self.save_btn.setEnabled(True)

        # 聚焦到输入框
        self.input_text.setFocus()

    def _on_progress_updated(self, stage: str, message: str, progress: int):
        """进度更新"""
        # 更新进度条
        if not self.progress_widget.isVisible():
            self.progress_widget.show()

        # 获取问题类型（用于情绪化文字）
        question_type = self.conversation_service.context.question_category or "综合运势"

        self.progress_widget.set_stage_with_emotion(
            progress,
            stage,
            question_type,
            message
        )

        # 更新右侧面板的阶段信息
        self.stage_label.setText(f"⚙️ {stage} ({progress}%)")

        # 右侧面板滚动到顶部，让用户看到最新的进度信息
        if hasattr(self, 'right_panel_scroll_area'):
            self.right_panel_scroll_area.verticalScrollBar().setValue(0)

    def _on_theory_started(self, theory_name: str):
        """V2: 理论分析开始"""
        self.logger.debug(f"理论开始: {theory_name}")
        if hasattr(self, 'quick_result_panel'):
            self.quick_result_panel.set_theory_running(theory_name)

    def _on_quick_result(self, theory_name: str, summary: str, judgment: str):
        """V2: 理论快速结果"""
        self.logger.debug(f"理论完成: {theory_name}, 判断: {judgment}")
        if hasattr(self, 'quick_result_panel'):
            self.quick_result_panel.set_theory_completed(theory_name, summary, judgment)

    def _on_error(self, error_msg: str):
        """错误处理"""
        self.logger.error(f"AI对话出错: {error_msg}")

        error_response = f"😅 抱歉，处理时遇到了一些问题：{error_msg}\n\n请稍后再试，或重新发起对话。"
        self.chat_widget.add_assistant_message(error_response)

        # 隐藏进度条
        if self.progress_widget.isVisible():
            self.progress_widget.show_error(error_msg)

        # 恢复发送按钮
        self.send_btn.setEnabled(True)
        self.send_btn.setText("发送")

    def _update_right_panel(self):
        """更新右侧关键信息面板"""
        context = self.conversation_service.context

        # 更新小六壬卡片
        self._update_xiaoliu_card()

        # 激活已完成的理论按钮
        if context.xiaoliu_result:
            # 小六壬不在6个按钮中，但可以激活相关理论
            pass
        if context.bazi_result:
            self._activate_theory_button("八字")
        if context.ziwei_result:
            self._activate_theory_button("紫微")
        if context.qimen_result:
            self._activate_theory_button("奇门")
        if context.liuren_result:
            self._activate_theory_button("六壬")
        if context.liuyao_result:
            self._activate_theory_button("六爻")
        if context.meihua_result:
            self._activate_theory_button("梅花")

        # 更新八字信息
        if context.bazi_result:
            bazi_data = context.bazi_result

            # 正确获取四柱信息
            year_pillar = bazi_data.get("年柱")
            month_pillar = bazi_data.get("月柱")
            day_pillar = bazi_data.get("日柱")
            hour_pillar = bazi_data.get("时柱")

            # 构建专业排版的八字显示
            year_str = f"{year_pillar['天干']}{year_pillar['地支']}" if year_pillar else "未知"
            month_str = f"{month_pillar['天干']}{month_pillar['地支']}" if month_pillar else "未知"
            day_str = f"{day_pillar['天干']}{day_pillar['地支']}" if day_pillar else "未知"
            hour_str = f"{hour_pillar['天干']}{hour_pillar['地支']}" if hour_pillar else "未知"

            # 获取纳音
            year_nayin = bazi_data.get('纳音', {}).get('年柱', '')

            # 获取五行统计
            wuxing_stats = bazi_data.get('五行统计', {}).get('统计', {})
            wuxing_str = ' '.join([f"{k}:{v}" for k, v in wuxing_stats.items() if v > 0])

            # 获取用神分析
            yongshen_analysis = bazi_data.get('用神分析', {})
            yongshen = yongshen_analysis.get('用神', '未知')
            rizhu_strength = yongshen_analysis.get('日主强弱', '未知')

            bazi_display = f"""### 四柱八字

| 时柱 | 日柱 | 月柱 | 年柱 |
|:---:|:---:|:---:|:---:|
| **{hour_str}** | **{day_str}** | **{month_str}** | **{year_str}** |

---

**日主**: {bazi_data.get('日主', '未知')} （{rizhu_strength}）
**用神**: {yongshen}
**年柱纳音**: {year_nayin}

**五行**: {wuxing_str if wuxing_str else '未知'}
"""
            self.bazi_text.setMarkdown(bazi_display.strip())

            # 更新简要分析
            if "ai_analysis" in bazi_data:
                analysis = bazi_data["ai_analysis"]
                # 提取前200字
                summary = analysis[:200] + ("..." if len(analysis) > 200 else "")
                self.analysis_text.setMarkdown(summary)

        # 更新阶段
        stage_text = {
            ConversationStage.INIT: "初始化",
            ConversationStage.STAGE1_ICEBREAK: "破冰阶段",
            ConversationStage.STAGE2_BASIC_INFO: "收集信息",
            ConversationStage.STAGE3_SUPPLEMENT: "深度补充",
            ConversationStage.STAGE4_VERIFICATION: "结果确认",
            ConversationStage.STAGE5_FINAL_REPORT: "生成报告",
            ConversationStage.QA: "问答交互",
            ConversationStage.COMPLETED: "已完成"
        }.get(context.stage, "未知")

        self.stage_label.setText(f"📍 {stage_text}")

        # 更新分析状态
        status_parts = []

        # 问题类别和描述
        if context.question_category:
            category_emoji = {
                "事业": "💼", "感情": "💕", "财运": "💰",
                "健康": "🏥", "学业": "📚", "决策": "🤔", "其他": "🔮"
            }.get(context.question_category, "📋")
            status_parts.append(f"**咨询事项**: {category_emoji} {context.question_category}")
            if context.question_description:
                desc_short = context.question_description[:50] + ("..." if len(context.question_description) > 50 else "")
                status_parts.append(f"_\"{desc_short}\"_")

        # 时辰确定性
        if context.time_certainty and context.time_certainty != "unknown":
            certainty_map = {
                "certain": "✅ 确定",
                "uncertain": "⚠️ 不确定",
                "unknown": "❓ 未知"
            }
            status_parts.append(f"**时辰**: {certainty_map.get(context.time_certainty, context.time_certainty)}")

        # 已选理论
        if context.selected_theories:
            # selected_theories 可能是字典列表或字符串列表
            if context.selected_theories and isinstance(context.selected_theories[0], dict):
                theories_str = "、".join([t.get('theory', str(t)) for t in context.selected_theories])
            else:
                theories_str = "、".join(str(t) for t in context.selected_theories)
            status_parts.append(f"**已选理论**: {theories_str}")

        # 已完成的分析
        completed_analyses = []
        if context.xiaoliu_result:
            completed_analyses.append("✓ 小六壬")
        if context.bazi_result:
            completed_analyses.append("✓ 八字")
        if context.qimen_result:
            completed_analyses.append("✓ 奇门")
        if context.liuren_result:
            completed_analyses.append("✓ 六壬")
        if context.liuyao_result:
            completed_analyses.append("✓ 六爻")
        if context.meihua_result:
            completed_analyses.append("✓ 梅花")

        if completed_analyses:
            status_parts.append(f"**已完成**: {' '.join(completed_analyses)}")

        # 整体进度
        progress = self.conversation_service.get_progress_percentage()
        status_parts.append(f"**进度**: {progress}%")

        # 验证反馈（如果有）
        if context.verification_feedback:
            feedback_count = len(context.verification_feedback)
            status_parts.append(f"**已反馈**: {feedback_count}次")

        status_md = "\n\n".join(status_parts) if status_parts else "（等待开始）"
        self.status_text.setMarkdown(status_md)

    def _on_save_clicked(self):
        """保存对话"""
        conversation_data = self.conversation_service.save_conversation()

        # 发送信号（由主窗口处理保存逻辑）
        self.save_requested.emit(conversation_data)

        QMessageBox.information(
            self,
            "保存成功",
            "对话已保存到历史记录！"
        )

        self.save_btn.setEnabled(False)

    def _on_new_conversation_clicked(self):
        """新对话按钮点击"""
        # 确认对话框
        if len(self.chat_widget.get_messages()) > 1:
            reply = QMessageBox.question(
                self,
                "确认",
                "开始新对话将清空当前内容。是否继续？\n\n建议先保存当前对话。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.No:
                return

        self._start_new_conversation()

    def _increase_chat_font(self):
        """放大对话字体"""
        if self.chat_font_size < 18:  # 最大18pt
            self.chat_font_size += 1
            self._apply_chat_font_size()
            self.logger.debug(f"对话字体大小: {self.chat_font_size}pt")

    def _decrease_chat_font(self):
        """缩小对话字体"""
        if self.chat_font_size > 9:  # 最小9pt
            self.chat_font_size -= 1
            self._apply_chat_font_size()
            self.logger.debug(f"对话字体大小: {self.chat_font_size}pt")

    def _reset_chat_font(self):
        """重置对话字体为默认大小"""
        self.chat_font_size = 11
        self._apply_chat_font_size()
        self.logger.debug("对话字体大小已重置为11pt")

    def _apply_chat_font_size(self):
        """应用字体大小到对话组件"""
        if hasattr(self, 'chat_widget'):
            self.chat_widget.set_font_size(self.chat_font_size)

    def update_from_report(self, report):
        """
        从分析报告更新八字命盘信息

        Args:
            report: ComprehensiveReport对象
        """
        try:
            # 更新conversation_service的context中的bazi_result
            if hasattr(report, 'theory_results') and '八字' in report.theory_results:
                self.conversation_service.context.bazi_result = report.theory_results['八字']
                # 更新右侧面板显示
                self._update_right_panel()
                self.logger.info("八字命盘信息已更新")
        except Exception as e:
            self.logger.error(f"更新八字命盘信息失败: {e}")

    def _show_theory_detail(self, theory_name: str):
        """显示理论详情"""
        context = self.conversation_service.context

        # 获取对应理论的结果
        theory_result = None
        if theory_name == "八字" and context.bazi_result:
            theory_result = context.bazi_result
        elif theory_name == "紫微" and context.ziwei_result:
            theory_result = context.ziwei_result
        elif theory_name == "奇门" and context.qimen_result:
            theory_result = context.qimen_result
        elif theory_name == "六壬" and context.liuren_result:
            theory_result = context.liuren_result
        elif theory_name == "六爻" and context.liuyao_result:
            theory_result = context.liuyao_result
        elif theory_name == "梅花" and context.meihua_result:
            theory_result = context.meihua_result

        if theory_result:
            # 显示理论详情
            self.theory_detail_text.show()

            # 提取关键信息
            detail_md = f"### {theory_name}分析结果\n\n"

            if isinstance(theory_result, dict):
                # 提取独立结论
                if 'judgment' in theory_result:
                    detail_md += f"**判断**: {theory_result['judgment']}\n\n"
                if 'conclusion' in theory_result:
                    detail_md += f"**结论**: {theory_result['conclusion']}\n\n"
                if 'advice' in theory_result:
                    detail_md += f"**建议**: {theory_result['advice']}\n"
                if 'ai_analysis' in theory_result:
                    analysis = theory_result['ai_analysis']
                    short_analysis = analysis[:150] + "..." if len(analysis) > 150 else analysis
                    detail_md += f"\n{short_analysis}"

            self.theory_detail_text.setMarkdown(detail_md)
        else:
            self.theory_detail_text.setMarkdown(f"_{theory_name}分析尚未完成_")
            self.theory_detail_text.show()

    def _activate_theory_button(self, theory_name: str):
        """激活理论按钮"""
        if theory_name in self.theory_buttons:
            btn = self.theory_buttons[theory_name]
            btn.setText(theory_name)
            btn.setEnabled(True)
            btn.setProperty("activated", True)
            btn.setToolTip(f"点击查看{theory_name}分析结果")
            # 刷新样式
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _update_xiaoliu_card(self):
        """更新小六壬卡片"""
        context = self.conversation_service.context

        if context.xiaoliu_result:
            result = context.xiaoliu_result
            # 构建小六壬显示
            judgment = result.get('判断', result.get('judgment', ''))
            gong = result.get('宫位', result.get('position', ''))
            advice = result.get('建议', result.get('advice', ''))

            xiaoliu_md = f"""**{gong}** - {judgment}

{advice[:100] + '...' if len(advice) > 100 else advice}
"""
            self.xiaoliu_text.setMarkdown(xiaoliu_md)
        else:
            self.xiaoliu_text.setMarkdown("_等待起卦..._")

    def _stop_current_worker(self):
        """停止当前正在运行的工作线程"""
        if self.worker is not None and self.worker.isRunning():
            self.logger.debug("正在停止当前工作线程...")
            self.worker.cancel()
            # 断开信号连接，防止后续触发
            try:
                self.worker.message_received.disconnect()
                self.worker.progress_updated.disconnect()
                self.worker.error.disconnect()
            except TypeError:
                pass  # 信号未连接时忽略
            # 等待线程结束（最多2秒）
            if not self.worker.wait(2000):
                self.logger.warning("工作线程未能在2秒内结束")
            self.worker = None

    def eventFilter(self, obj, event):
        """
        事件过滤器：实现回车发送功能

        - Enter/Return：发送消息
        - Shift+Enter：换行
        """
        if obj == self.input_text and event.type() == QEvent.Type.KeyPress:
            key_event = event
            if key_event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                # Shift+Enter 换行，普通 Enter 发送
                if key_event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    return False  # 允许换行
                else:
                    # 检查发送按钮是否启用
                    if self.send_btn.isEnabled():
                        self._on_send_clicked()
                    return True  # 阻止默认行为
        return super().eventFilter(obj, event)

    def cleanup(self):
        """清理资源（窗口关闭时调用）"""
        self.logger.debug("AIConversationTab 清理资源")
        self._stop_current_worker()
