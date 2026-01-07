"""
典籍标签页 - 术数资料阅读与学习平台

功能：
- 文档阅读：支持 Markdown / 文本格式
- 笔记摘抄：选中文本添加笔记
- 资料分类：系统资料 + 用户资料
- AI学习助手：总结、洞察、学习方案、心得生成

设计参考：docs/design/02_典籍模块设计.md
"""
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QSplitter, QTreeWidget,
    QTreeWidgetItem, QTextBrowser, QSizePolicy,
    QDialog, QTextEdit, QLineEdit, QMessageBox,
    QFileDialog, QInputDialog, QMenu, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer, QObject
from PyQt6.QtGui import QFont, QWheelEvent

from utils.logger import get_logger
from utils.notes_manager import get_notes_manager
from utils.usage_stats_manager import get_usage_stats_manager
from utils.rag_manager import get_rag_manager
from ui.widgets.document_viewer import DocumentViewer
from ui.dialogs.rag_qa_dialog import RAGQADialog


class ReadingTracker(QObject):
    """
    智能阅读计时器

    功能：
    - 当用户阅读文档时自动计时
    - 页面没有滚动超过30秒自动暂停计时
    - 页面滚动后恢复计时
    - 每5秒自动保存一次（防止关闭窗口数据丢失）
    """

    IDLE_TIMEOUT = 30  # 无活动超时（秒）
    AUTO_SAVE_INTERVAL = 5  # 自动保存间隔（秒）

    def __init__(self, stats_manager, parent=None):
        super().__init__(parent)
        self._stats_manager = stats_manager
        self._logger = get_logger(__name__)

        # 当前追踪状态
        self._current_record_id: int = -1
        self._current_file_path: Optional[str] = None
        self._is_active: bool = False  # 是否处于活跃状态（有滚动）
        self._unsaved_seconds: int = 0  # 未保存的累计秒数

        # 活跃检测定时器（每秒检查）
        self._tick_timer = QTimer(self)
        self._tick_timer.setInterval(1000)  # 1秒
        self._tick_timer.timeout.connect(self._on_tick)

        # 空闲计时器（检测是否超过30秒没有滚动）
        self._idle_timer = QTimer(self)
        self._idle_timer.setInterval(self.IDLE_TIMEOUT * 1000)
        self._idle_timer.setSingleShot(True)
        self._idle_timer.timeout.connect(self._on_idle_timeout)

        # 自动保存定时器
        self._save_timer = QTimer(self)
        self._save_timer.setInterval(self.AUTO_SAVE_INTERVAL * 1000)
        self._save_timer.timeout.connect(self._auto_save)

    def start_tracking(self, file_path: str, title: Optional[str] = None, category: Optional[str] = None):
        """
        开始追踪新文档

        Args:
            file_path: 文档路径
            title: 文档标题
            category: 文档分类
        """
        # 先保存之前的数据
        self._save_current()

        self._current_file_path = file_path
        self._current_record_id = self._stats_manager.get_or_create_reading_session(
            document_path=file_path,
            document_title=title,
            category=category
        )
        self._unsaved_seconds = 0
        self._is_active = True

        # 启动定时器
        self._tick_timer.start()
        self._save_timer.start()
        self._idle_timer.start()

        self._logger.debug(f"开始追踪阅读: {title or file_path}")

    def stop_tracking(self):
        """停止追踪并保存"""
        self._save_current()
        self._tick_timer.stop()
        self._save_timer.stop()
        self._idle_timer.stop()
        self._current_record_id = -1
        self._current_file_path = None
        self._is_active = False
        self._unsaved_seconds = 0

    def on_user_activity(self):
        """
        用户活动回调（滚动、点击等）
        调用此方法表示用户有活动，重置空闲计时器
        """
        if self._current_record_id < 0:
            return

        # 如果之前是暂停状态，恢复计时
        if not self._is_active:
            self._is_active = True
            self._logger.debug("用户活动检测，恢复计时")

        # 重置空闲计时器
        self._idle_timer.stop()
        self._idle_timer.start()

    def _on_tick(self):
        """每秒触发一次，累计活跃时间"""
        if self._is_active and self._current_record_id >= 0:
            self._unsaved_seconds += 1

    def _on_idle_timeout(self):
        """空闲超时，暂停计时"""
        if self._is_active:
            self._is_active = False
            self._logger.debug(f"用户空闲超过{self.IDLE_TIMEOUT}秒，暂停计时")
            # 空闲时也保存一次
            self._auto_save()

    def _auto_save(self):
        """自动保存累计时间"""
        if self._unsaved_seconds > 0 and self._current_record_id >= 0:
            self._stats_manager.update_reading_time(
                self._current_record_id,
                self._unsaved_seconds
            )
            self._logger.debug(f"自动保存阅读时长: +{self._unsaved_seconds}s")
            self._unsaved_seconds = 0

    def _save_current(self):
        """保存当前累计时间"""
        if self._unsaved_seconds > 0 and self._current_record_id >= 0:
            self._stats_manager.update_reading_time(
                self._current_record_id,
                self._unsaved_seconds
            )
            self._logger.debug(f"保存阅读时长: +{self._unsaved_seconds}s")
            self._unsaved_seconds = 0

    def get_current_session_seconds(self) -> int:
        """获取当前会话的阅读秒数（用于UI显示）"""
        return self._unsaved_seconds

    def is_active(self) -> bool:
        """是否处于活跃计时状态"""
        return self._is_active


class AIAssistantWorker(QThread):
    """AI学习助手工作线程"""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, api_manager, prompt: str, parent=None):
        super().__init__(parent)
        self.api_manager = api_manager
        self.prompt = prompt

    def run(self):
        """执行AI分析"""
        try:
            # 使用API进行分析
            response = self.api_manager.analyze(self.prompt)
            if response:
                self.finished.emit(response)
            else:
                self.error.emit("AI返回结果为空")
        except Exception as e:
            self.error.emit(str(e))


class LibraryTab(QWidget):
    """
    典籍标签页

    提供文档阅读、笔记管理、AI辅助学习功能
    """

    def __init__(self, api_manager=None, parent=None):
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self._api_manager = api_manager
        self._notes_manager = get_notes_manager()
        self._stats_manager = get_usage_stats_manager()
        self._rag_manager = get_rag_manager()

        # 资料目录
        self._system_library_path = self._get_system_library_path()
        self._user_library_path = self._get_user_library_path()

        # 当前状态
        self._current_file_path: Optional[str] = None
        self._current_content: str = ""
        self._ai_worker: Optional[AIAssistantWorker] = None

        # 阅读计时器
        self._reading_tracker = ReadingTracker(self._stats_manager, self)

        self._init_ui()
        self._load_library_tree()

        # 初始化RAG索引（后台执行）
        self._init_rag_index()

    def _get_system_library_path(self) -> Path:
        """获取系统资料目录"""
        # 尝试从安装目录找
        app_dir = Path(__file__).parent.parent.parent.parent
        system_path = app_dir / "resources" / "library"

        if not system_path.exists():
            system_path.mkdir(parents=True, exist_ok=True)

        return system_path

    def _get_user_library_path(self) -> Path:
        """获取用户资料目录"""
        user_path = Path.home() / ".cyber_mantic" / "documents"
        user_path.mkdir(parents=True, exist_ok=True)
        return user_path

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 主内容区域（分割器）- 占满整个空间
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧：标题 + 资料分类树 + AI按钮
        left_panel = self._create_category_panel()
        splitter.addWidget(left_panel)

        # 右侧：文档查看 + 笔记（占满高度）
        right_panel = self._create_content_panel()
        splitter.addWidget(right_panel)

        # 设置分割比例
        splitter.setSizes([280, 720])

        layout.addWidget(splitter)

    def _create_category_panel(self) -> QWidget:
        """创建资料分类面板（左侧）"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 10, 15)
        layout.setSpacing(10)

        # 顶部：标题 + 导入按钮
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        title_label = QLabel("典籍")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)

        # 导入资料按钮
        import_btn = QPushButton("导入")
        import_btn.clicked.connect(self._on_import_file)
        import_btn.setStyleSheet("""
            QPushButton {
                padding: 5px 12px;
                border: 1px solid #1976d2;
                border-radius: 4px;
                background-color: #fff;
                color: #1976d2;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e3f2fd;
            }
        """)
        header_layout.addWidget(import_btn)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # 搜索框
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("🔍 搜索文档...")
        self._search_input.textChanged.connect(self._on_search_text_changed)
        self._search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #6366f1;
            }
        """)
        layout.addWidget(self._search_input)

        # 分类树
        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._on_tree_context_menu)
        self._tree.itemClicked.connect(self._on_tree_item_clicked)
        self._tree.setStyleSheet("""
            QTreeWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px;
            }
            QTreeWidget::item {
                padding: 5px;
            }
            QTreeWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
        """)
        layout.addWidget(self._tree)

        # 底部按钮区
        bottom_btns_layout = QVBoxLayout()
        bottom_btns_layout.setSpacing(8)

        # 笔记摘要按钮
        notes_summary_btn = QPushButton("📋 笔记摘要")
        notes_summary_btn.clicked.connect(self._on_notes_summary)
        notes_summary_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 15px;
                border: 1px solid #f59e0b;
                border-radius: 5px;
                background-color: #fff;
                color: #f59e0b;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #fef3c7;
            }
        """)
        bottom_btns_layout.addWidget(notes_summary_btn)

        # AI学习助手按钮
        ai_btn = QPushButton("🤖 AI学习助手")
        ai_btn.clicked.connect(self._on_open_ai_assistant)
        ai_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 15px;
                border: 1px solid #6366f1;
                border-radius: 5px;
                background-color: #6366f1;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4f46e5;
            }
            QPushButton:disabled {
                background-color: #ccc;
                border-color: #ccc;
            }
        """)
        bottom_btns_layout.addWidget(ai_btn)

        layout.addLayout(bottom_btns_layout)

        return panel

    def _create_content_panel(self) -> QWidget:
        """创建内容面板（文档查看器，占满右侧空间）"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ===== 阅读控制栏 =====
        reading_toolbar = QWidget()
        toolbar_layout = QHBoxLayout(reading_toolbar)
        toolbar_layout.setContentsMargins(10, 8, 10, 8)
        toolbar_layout.setSpacing(15)

        # 字体大小控制
        font_label = QLabel("字体:")
        toolbar_layout.addWidget(font_label)

        self._font_decrease_btn = QPushButton("A-")
        self._font_decrease_btn.setMaximumWidth(40)
        self._font_decrease_btn.setMinimumHeight(28)
        self._font_decrease_btn.setToolTip("缩小字体")
        self._font_decrease_btn.clicked.connect(self._decrease_font_size)
        toolbar_layout.addWidget(self._font_decrease_btn)

        self._font_size_label = QLabel("14")
        self._font_size_label.setMinimumWidth(25)
        toolbar_layout.addWidget(self._font_size_label)

        self._font_increase_btn = QPushButton("A+")
        self._font_increase_btn.setMaximumWidth(40)
        self._font_increase_btn.setMinimumHeight(28)
        self._font_increase_btn.setToolTip("放大字体")
        self._font_increase_btn.clicked.connect(self._increase_font_size)
        toolbar_layout.addWidget(self._font_increase_btn)

        toolbar_layout.addSpacing(20)

        # 背景颜色设置
        bg_label = QLabel("背景:")
        toolbar_layout.addWidget(bg_label)

        self._bg_light_btn = QPushButton("浅色")
        self._bg_light_btn.setMaximumWidth(50)
        self._bg_light_btn.setMinimumHeight(28)
        self._bg_light_btn.setProperty("secondary", True)
        self._bg_light_btn.clicked.connect(lambda: self._set_reading_background("light"))
        toolbar_layout.addWidget(self._bg_light_btn)

        self._bg_sepia_btn = QPushButton("护眼")
        self._bg_sepia_btn.setMaximumWidth(50)
        self._bg_sepia_btn.setMinimumHeight(28)
        self._bg_sepia_btn.setProperty("secondary", True)
        self._bg_sepia_btn.clicked.connect(lambda: self._set_reading_background("sepia"))
        toolbar_layout.addWidget(self._bg_sepia_btn)

        self._bg_dark_btn = QPushButton("深色")
        self._bg_dark_btn.setMaximumWidth(50)
        self._bg_dark_btn.setMinimumHeight(28)
        self._bg_dark_btn.setProperty("secondary", True)
        self._bg_dark_btn.clicked.connect(lambda: self._set_reading_background("dark"))
        toolbar_layout.addWidget(self._bg_dark_btn)

        toolbar_layout.addStretch()

        layout.addWidget(reading_toolbar)

        # 文档查看器 - 占满整个面板
        self._viewer = DocumentViewer()
        self._viewer.note_requested.connect(self._on_note_requested)
        self._viewer.question_requested.connect(self._on_question_requested)
        self._viewer.show_welcome()
        layout.addWidget(self._viewer)

        # 连接滚动事件用于阅读计时
        self._viewer.scroll_detected.connect(self._on_viewer_scroll)

        # 初始化字体大小
        self._reading_font_size = 14

        return panel

    def _on_open_ai_assistant(self):
        """打开AI学习助手弹窗"""
        if not self._api_manager:
            QMessageBox.warning(self, "提示", "请先在设置中配置AI接口")
            return

        dialog = AIAssistantDialog(
            api_manager=self._api_manager,
            current_content=self._current_content,
            current_file_path=self._current_file_path,
            notes_manager=self._notes_manager,
            stats_manager=self._stats_manager,
            parent=self
        )
        dialog.exec()

    def _load_library_tree(self):
        """加载资料目录树"""
        self._tree.clear()

        # 系统资料
        system_item = QTreeWidgetItem(["📁 系统资料"])
        system_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "folder", "path": str(self._system_library_path)})
        self._load_folder_items(system_item, self._system_library_path)
        self._tree.addTopLevelItem(system_item)
        system_item.setExpanded(True)

        # 用户资料
        user_item = QTreeWidgetItem(["📁 我的资料"])
        user_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "folder", "path": str(self._user_library_path)})
        self._load_folder_items(user_item, self._user_library_path)
        self._tree.addTopLevelItem(user_item)
        user_item.setExpanded(True)

        # 我的笔记（按标签分类）
        notes_item = QTreeWidgetItem(["📝 我的笔记"])
        notes_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "notes_root"})
        self._load_notes_tags(notes_item)
        self._tree.addTopLevelItem(notes_item)

    def _load_folder_items(self, parent_item: QTreeWidgetItem, folder_path: Path, category: Optional[str] = None):
        """递归加载文件夹内容"""
        if not folder_path.exists():
            return

        # 获取所有文件和文件夹
        items = sorted(folder_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))

        for item in items:
            if item.name.startswith('.'):
                continue

            if item.is_dir():
                child = QTreeWidgetItem([f"📁 {item.name}"])
                child.setData(0, Qt.ItemDataRole.UserRole, {"type": "folder", "path": str(item)})
                # 使用文件夹名作为分类
                self._load_folder_items(child, item, category=item.name)
                parent_item.addChild(child)

            elif item.suffix.lower() in ('.md', '.txt', '.doc', '.docx', '.pdf'):
                icon = self._get_file_icon(item.suffix)
                child = QTreeWidgetItem([f"{icon} {item.stem}"])
                child.setData(0, Qt.ItemDataRole.UserRole, {
                    "type": "file",
                    "path": str(item),
                    "category": category or folder_path.name
                })
                parent_item.addChild(child)

    def _get_file_icon(self, suffix: str) -> str:
        """获取文件图标"""
        icons = {
            '.md': '📄',
            '.txt': '📝',
            '.doc': '📘',
            '.docx': '📘',
            '.pdf': '📕'
        }
        return icons.get(suffix.lower(), '📄')

    def _load_notes_tags(self, parent_item: QTreeWidgetItem):
        """加载笔记标签分类"""
        tags = self._notes_manager.get_all_tags()

        if not tags:
            child = QTreeWidgetItem(["（暂无标签）"])
            child.setData(0, Qt.ItemDataRole.UserRole, {"type": "notes_empty"})
            parent_item.addChild(child)
        else:
            # 全部笔记
            all_item = QTreeWidgetItem(["📋 全部笔记"])
            all_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "notes_all"})
            parent_item.addChild(all_item)

            for tag in tags:
                child = QTreeWidgetItem([f"🏷️ #{tag['name']}"])
                child.setData(0, Qt.ItemDataRole.UserRole, {"type": "notes_tag", "tag": tag['name']})
                parent_item.addChild(child)

    def _on_tree_item_clicked(self, item: QTreeWidgetItem, column: int):
        """树节点点击事件"""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return

        item_type = data.get("type")

        if item_type == "file":
            file_path = data.get("path")
            if file_path:
                self._viewer.load_file(file_path)
                self._refresh_notes_for_file(file_path)

                # 获取文档信息
                path = Path(file_path)
                title = path.stem
                category = data.get("category")

                # 启动智能阅读计时
                self._reading_tracker.start_tracking(file_path, title, category)

                # 保存当前文件信息
                self._current_file_path = file_path
                self._current_content = self._load_file_content(file_path)

        elif item_type == "notes_all":
            self._show_all_notes()

        elif item_type == "notes_tag":
            tag = data.get("tag")
            if tag:
                self._show_notes_by_tag(tag)

    def _on_tree_context_menu(self, pos):
        """树右键菜单"""
        item = self._tree.itemAt(pos)
        if not item:
            return

        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return

        item_type = data.get("type")
        menu = QMenu(self)

        if item_type == "file":
            # 文件右键菜单
            file_path = data.get("path")

            open_action = menu.addAction("打开")
            open_action.triggered.connect(lambda: self._viewer.load_file(file_path))

            # 如果是用户文件，可以删除
            if str(self._user_library_path) in file_path:
                menu.addSeparator()
                delete_action = menu.addAction("删除")
                delete_action.triggered.connect(lambda: self._delete_user_file(file_path))

        elif item_type == "notes_tag":
            # 标签右键菜单
            tag = data.get("tag")
            delete_action = menu.addAction("删除标签")
            delete_action.triggered.connect(lambda: self._delete_tag(tag))

        if menu.actions():
            menu.exec(self._tree.mapToGlobal(pos))

    def _on_viewer_scroll(self):
        """文档查看器滚动事件"""
        self._reading_tracker.on_user_activity()

    def _on_search_text_changed(self, text: str):
        """搜索文本变化时过滤文档树"""
        search_text = text.strip().lower()

        def filter_tree_item(item: QTreeWidgetItem, parent_visible: bool = False) -> bool:
            """递归过滤树节点，返回是否可见"""
            data = item.data(0, Qt.ItemDataRole.UserRole)
            item_type = data.get("type", "") if data else ""

            # 获取显示文本（去掉图标）
            display_text = item.text(0).lower()

            # 检查当前项是否匹配
            matches = search_text in display_text if search_text else True

            # 递归检查子项
            child_visible = False
            for i in range(item.childCount()):
                child = item.child(i)
                if filter_tree_item(child, matches):
                    child_visible = True

            # 决定当前项是否显示
            should_show = matches or child_visible or parent_visible
            item.setHidden(not should_show)

            # 如果有匹配的子项，展开父项
            if child_visible and search_text:
                item.setExpanded(True)

            return matches or child_visible

        # 遍历所有顶级项
        for i in range(self._tree.topLevelItemCount()):
            top_item = self._tree.topLevelItem(i)
            filter_tree_item(top_item)

    def _on_notes_summary(self):
        """显示笔记摘要弹窗"""
        notes = self._notes_manager.get_all_notes(limit=100)

        if not notes:
            QMessageBox.information(self, "提示", "您还没有任何笔记，请先在阅读时添加笔记")
            return

        # 统计信息
        tags_count = {}
        sources_count = {}

        for note in notes:
            # 统计标签
            for tag in note.get('tags', []):
                tags_count[tag] = tags_count.get(tag, 0) + 1
            # 统计来源
            source = Path(note.get('source_file', '')).stem if note.get('source_file') else '未知'
            sources_count[source] = sources_count.get(source, 0) + 1

        # 排序
        top_tags = sorted(tags_count.items(), key=lambda x: x[1], reverse=True)[:10]
        top_sources = sorted(sources_count.items(), key=lambda x: x[1], reverse=True)[:10]

        # 构建摘要对话框
        dialog = NotesSummaryDialog(
            total_notes=len(notes),
            top_tags=top_tags,
            top_sources=top_sources,
            notes=notes,
            notes_manager=self._notes_manager,
            parent=self
        )
        dialog.exec()

    def _load_file_content(self, file_path: str) -> str:
        """加载文件内容"""
        try:
            path = Path(file_path)
            if path.suffix.lower() in ('.md', '.txt'):
                return path.read_text(encoding='utf-8')
            else:
                # 对于其他格式，返回空（未来可扩展）
                return ""
        except Exception as e:
            self.logger.warning(f"读取文件内容失败: {e}")
            return ""

    def _on_import_file(self):
        """导入文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择要导入的文件",
            "",
            "文档文件 (*.md *.txt *.doc *.docx *.pdf);;所有文件 (*)"
        )

        if file_path:
            import shutil
            source = Path(file_path)
            dest = self._user_library_path / source.name

            try:
                shutil.copy2(source, dest)
                self._load_library_tree()
                QMessageBox.information(self, "导入成功", f"文件已导入到我的资料")
            except Exception as e:
                QMessageBox.critical(self, "导入失败", str(e))

    def _delete_user_file(self, file_path: str):
        """删除用户文件"""
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除此文件吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                Path(file_path).unlink()
                self._load_library_tree()
            except Exception as e:
                QMessageBox.critical(self, "删除失败", str(e))

    def _delete_tag(self, tag: str):
        """删除标签"""
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除标签 #{tag} 吗？\n（笔记中的此标签不会被删除）",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._notes_manager.delete_tag(tag)
            self._load_library_tree()

    def _on_note_requested(self, content: str, source_file: str, position: str):
        """处理添加笔记请求"""
        dialog = NoteEditDialog(content, source_file, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            user_note, tags = dialog.get_values()

            note_id = self._notes_manager.create_note(
                content=content,
                source_file=source_file,
                source_position=position,
                user_note=user_note,
                tags=tags
            )

            if note_id > 0:
                QMessageBox.information(self, "成功", "笔记已保存")
                self._load_library_tree()  # 刷新标签
                self._refresh_notes_for_file(source_file)

    def _on_question_requested(self, selected_text: str):
        """处理提问请求 - 打开RAG问答对话框"""
        if not self._api_manager:
            QMessageBox.warning(self, "提示", "请先在设置中配置AI接口")
            return

        dialog = RAGQADialog(
            api_manager=self._api_manager,
            selected_text=selected_text,
            parent=self
        )
        dialog.exec()

    def _init_rag_index(self):
        """初始化RAG索引（索引系统资料和用户资料）"""
        try:
            # 索引系统资料
            if self._system_library_path.exists():
                self._rag_manager.index_directory(
                    str(self._system_library_path),
                    category="系统资料"
                )

            # 索引用户资料
            if self._user_library_path.exists():
                self._rag_manager.index_directory(
                    str(self._user_library_path),
                    category="用户资料"
                )

            stats = self._rag_manager.get_stats()
            self.logger.info(f"RAG索引初始化完成: {stats['total_chunks']} 个片段, {stats['total_documents']} 个文档")
        except Exception as e:
            self.logger.warning(f"RAG索引初始化失败: {e}")

    def _refresh_notes_for_file(self, file_path: str):
        """刷新当前文件的笔记（现在是空操作，笔记通过弹窗查看）"""
        pass

    def _show_all_notes(self):
        """显示所有笔记"""
        notes = self._notes_manager.get_all_notes(limit=100)
        self._display_notes_dialog("全部笔记", notes)

    def _show_notes_by_tag(self, tag: str):
        """按标签显示笔记"""
        notes = self._notes_manager.get_all_notes(tag=tag, limit=100)
        self._display_notes_dialog(f"标签：#{tag}", notes)

    def _display_notes_dialog(self, title: str, notes: List[Dict[str, Any]]):
        """在弹窗中显示笔记列表"""
        dialog = NotesViewDialog(title, notes, self._notes_manager, self)
        dialog.exec()

    # ===== 阅读体验控制 =====

    def _increase_font_size(self):
        """增大字体"""
        if self._reading_font_size < 24:
            self._reading_font_size += 2
            self._apply_font_size()

    def _decrease_font_size(self):
        """减小字体"""
        if self._reading_font_size > 10:
            self._reading_font_size -= 2
            self._apply_font_size()

    def _apply_font_size(self):
        """应用字体大小到文档查看器"""
        self._font_size_label.setText(str(self._reading_font_size))
        # 通过样式调整字体大小
        if hasattr(self._viewer, '_content_browser'):
            self._viewer._content_browser.setStyleSheet(f"""
                QTextBrowser {{
                    font-size: {self._reading_font_size}px;
                    line-height: 1.6;
                }}
            """)

    def _set_reading_background(self, mode: str):
        """设置阅读背景"""
        bg_colors = {
            "light": {"bg": "#ffffff", "text": "#1e293b"},
            "sepia": {"bg": "#f5f0e1", "text": "#5c4a32"},  # 护眼色
            "dark": {"bg": "#1a1a2e", "text": "#f1f5f9"}
        }
        colors = bg_colors.get(mode, bg_colors["light"])

        if hasattr(self._viewer, '_content_browser'):
            self._viewer._content_browser.setStyleSheet(f"""
                QTextBrowser {{
                    background-color: {colors['bg']};
                    color: {colors['text']};
                    font-size: {self._reading_font_size}px;
                    line-height: 1.6;
                    padding: 20px;
                }}
            """)

    def cleanup(self):
        """清理资源"""
        # 停止阅读计时并保存
        self._reading_tracker.stop_tracking()


class NoteEditDialog(QDialog):
    """笔记编辑对话框"""

    def __init__(self, content: str, source_file: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加笔记")
        self.setMinimumSize(500, 400)

        self._content = content
        self._source_file = source_file

        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 摘录内容
        content_label = QLabel("摘录内容：")
        content_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(content_label)

        content_display = QTextBrowser()
        content_display.setMaximumHeight(100)
        content_display.setText(self._content)
        content_display.setStyleSheet("""
            QTextBrowser {
                background-color: #f9f9f9;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        layout.addWidget(content_display)

        # 我的笔记
        note_label = QLabel("我的笔记：")
        note_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(note_label)

        self._note_edit = QTextEdit()
        self._note_edit.setPlaceholderText("写下您的理解、感悟或补充...")
        self._note_edit.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        layout.addWidget(self._note_edit)

        # 标签
        tags_label = QLabel("标签（用空格分隔）：")
        tags_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(tags_label)

        self._tags_edit = QLineEdit()
        self._tags_edit.setPlaceholderText("例如：八字 入门 重要")
        self._tags_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 8px;
            }
        """)
        layout.addWidget(self._tags_edit)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
            }
        """)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("保存笔记")
        save_btn.clicked.connect(self.accept)
        save_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                border: none;
                border-radius: 5px;
                background-color: #1976d2;
                color: white;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
        """)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def get_values(self):
        """获取输入值"""
        user_note = self._note_edit.toPlainText().strip()
        tags_text = self._tags_edit.text().strip()
        tags = [t.strip().lstrip('#') for t in tags_text.split() if t.strip()]
        return user_note, tags


class CustomPromptDialog(QDialog):
    """自定义Prompt对话框"""

    def __init__(self, current_content: str = "", current_file: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("自定义AI分析")
        self.setMinimumSize(600, 500)

        self._current_content = current_content
        self._current_file = current_file
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 说明
        info_label = QLabel("请输入您希望AI分析的指令。您可以使用 {content} 引用当前文档内容，使用 {title} 引用文档标题。")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(info_label)

        # 预设模板
        templates_label = QLabel("快速模板：")
        templates_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(templates_label)

        templates_layout = QHBoxLayout()
        templates = [
            ("翻译成白话文", "请将以下术数古文翻译成现代白话文，保持术语准确：\n\n{content}"),
            ("解释术语", "请解释以下内容中出现的所有术数专业术语：\n\n{content}"),
            ("举例说明", "请结合实际案例，说明以下理论的应用：\n\n{content}"),
            ("对比分析", "请分析以下内容与其他术数流派的异同：\n\n{content}")
        ]

        for name, template in templates:
            btn = QPushButton(name)
            btn.setStyleSheet("""
                QPushButton {
                    padding: 5px 10px;
                    border: 1px solid #ddd;
                    border-radius: 3px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #e3f2fd;
                }
            """)
            btn.clicked.connect(lambda _, t=template: self._apply_template(t))
            templates_layout.addWidget(btn)

        templates_layout.addStretch()
        layout.addLayout(templates_layout)

        # Prompt输入
        prompt_label = QLabel("您的指令：")
        prompt_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(prompt_label)

        self._prompt_edit = QTextEdit()
        self._prompt_edit.setPlaceholderText("请输入您的分析指令...\n\n例如：请分析这篇文章的核心思想，并结合现代心理学解读其智慧")
        self._prompt_edit.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        layout.addWidget(self._prompt_edit)

        # 是否包含文档内容
        self._include_content_check = QPushButton("✓ 包含当前文档内容")
        self._include_content_check.setCheckable(True)
        self._include_content_check.setChecked(True)
        self._include_content_check.setStyleSheet("""
            QPushButton {
                padding: 5px 15px;
                border: 1px solid #1976d2;
                border-radius: 3px;
                color: #1976d2;
            }
            QPushButton:checked {
                background-color: #1976d2;
                color: white;
            }
        """)
        layout.addWidget(self._include_content_check)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
            }
        """)
        btn_layout.addWidget(cancel_btn)

        analyze_btn = QPushButton("开始分析")
        analyze_btn.clicked.connect(self.accept)
        analyze_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                border: none;
                border-radius: 5px;
                background-color: #1976d2;
                color: white;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
        """)
        btn_layout.addWidget(analyze_btn)

        layout.addLayout(btn_layout)

    def _apply_template(self, template: str):
        """应用模板"""
        self._prompt_edit.setText(template)

    def get_prompt(self) -> str:
        """获取完整的Prompt"""
        user_prompt = self._prompt_edit.toPlainText().strip()

        if not user_prompt:
            return ""

        # 替换变量
        title = Path(self._current_file).stem if self._current_file else "未知文档"
        content = self._current_content[:4000] if self._current_content else "（无内容）"

        prompt = user_prompt.replace("{title}", title).replace("{content}", content)

        # 如果用户勾选了包含文档内容，且prompt中没有引用content
        if self._include_content_check.isChecked() and "{content}" not in user_prompt:
            prompt = f"""文档标题：{title}

文档内容：
{content}

---

用户指令：
{user_prompt}
"""

        return prompt


class AIAssistantDialog(QDialog):
    """AI学习助手弹窗"""

    def __init__(self, api_manager, current_content: str = "", current_file_path: str = None,
                 notes_manager=None, stats_manager=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI学习助手")
        self.setMinimumSize(650, 550)

        self._api_manager = api_manager
        self._current_content = current_content
        self._current_file_path = current_file_path
        self._notes_manager = notes_manager or get_notes_manager()
        self._stats_manager = stats_manager or get_usage_stats_manager()
        self._ai_worker: Optional[AIAssistantWorker] = None

        self._init_ui()
        self._update_button_state()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 标题
        title_label = QLabel("🤖 AI学习助手")
        title_font = title_label.font()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # 当前文档信息
        if self._current_file_path:
            doc_name = Path(self._current_file_path).stem
            doc_label = QLabel(f"当前文档：{doc_name}")
            doc_label.setStyleSheet("color: #666; font-size: 12px;")
            layout.addWidget(doc_label)
        else:
            doc_label = QLabel("当前无打开文档")
            doc_label.setStyleSheet("color: #999; font-size: 12px;")
            layout.addWidget(doc_label)

        # 功能按钮区域
        func_frame = QFrame()
        func_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                background-color: #fafafa;
            }
        """)
        func_layout = QVBoxLayout(func_frame)
        func_layout.setContentsMargins(15, 15, 15, 15)
        func_layout.setSpacing(10)

        # 功能按钮
        self._ai_buttons = {}
        ai_functions = [
            ("summarize", "📝 总结", "提炼文档核心要点", self._on_summarize),
            ("insight", "💡 洞察", "深度分析与知识关联", self._on_insight),
            ("study_plan", "📚 学习方案", "个性化学习建议", self._on_study_plan),
            ("reflection", "✨ 心得生成", "基于笔记生成心得", self._on_reflection),
            ("custom", "🎯 自定义", "自定义分析指令", self._on_custom),
        ]

        for key, name, desc, handler in ai_functions:
            btn_layout = QHBoxLayout()

            btn = QPushButton(name)
            btn.setMinimumWidth(120)
            btn.clicked.connect(handler)
            btn.setStyleSheet("""
                QPushButton {
                    padding: 10px 20px;
                    border: 1px solid #1976d2;
                    border-radius: 5px;
                    background-color: white;
                    color: #1976d2;
                    font-weight: bold;
                    text-align: center;
                }
                QPushButton:hover {
                    background-color: #e3f2fd;
                }
                QPushButton:disabled {
                    border-color: #ccc;
                    color: #ccc;
                }
            """)
            self._ai_buttons[key] = btn
            btn_layout.addWidget(btn)

            desc_label = QLabel(desc)
            desc_label.setStyleSheet("color: #666; font-size: 12px;")
            btn_layout.addWidget(desc_label)
            btn_layout.addStretch()

            func_layout.addLayout(btn_layout)

        layout.addWidget(func_frame)

        # 状态标签
        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: #1976d2; font-size: 12px;")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._status_label)

        layout.addStretch()

        # 关闭按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 30px;
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: white;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
            }
        """)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _update_button_state(self):
        """更新按钮状态"""
        has_content = bool(self._current_content)

        # 需要文档内容的功能
        for key in ["summarize", "insight", "study_plan", "custom"]:
            if key in self._ai_buttons:
                self._ai_buttons[key].setEnabled(has_content)

        # 心得生成只需要有笔记
        notes = self._notes_manager.get_all_notes(limit=1)
        self._ai_buttons["reflection"].setEnabled(len(notes) > 0)

    def _set_loading(self, loading: bool, task_name: str = ""):
        """设置加载状态"""
        for btn in self._ai_buttons.values():
            btn.setEnabled(not loading)

        if loading:
            self._status_label.setText(f"正在{task_name}...")
        else:
            self._status_label.setText("")
            self._update_button_state()

    def _on_summarize(self):
        """总结功能"""
        if not self._current_content:
            return

        prompt = f"""请对以下术数典籍内容进行总结，要求：
1. 提炼核心要点（3-5条）
2. 概括主要论述
3. 指出实践意义
4. 语言简洁精炼

---
文档标题：{Path(self._current_file_path).stem if self._current_file_path else '未知'}

内容：
{self._current_content[:4000]}
"""
        self._run_analysis("总结", prompt)

    def _on_insight(self):
        """洞察功能"""
        if not self._current_content:
            return

        prompt = f"""请对以下术数典籍内容进行深度洞察分析，要求：
1. 提取关键知识点和术语
2. 分析内容的深层含义和智慧
3. 找出与其他术数理论的关联
4. 指出现代应用价值
5. 提出值得深入研究的问题

---
文档标题：{Path(self._current_file_path).stem if self._current_file_path else '未知'}

内容：
{self._current_content[:4000]}
"""
        self._run_analysis("洞察", prompt)

    def _on_study_plan(self):
        """学习方案功能"""
        if not self._current_content:
            return

        reading_stats = self._stats_manager.get_reading_stats()
        notes_count = len(self._notes_manager.get_all_notes(limit=100))

        prompt = f"""请根据以下术数典籍内容，为学习者制定个性化学习方案：

## 学习者背景
- 已阅读文档数：{reading_stats.get('documents_read', 0)}
- 已做笔记数：{notes_count}
- 学习偏好方向：{reading_stats.get('top_category', '暂无')}

## 当前学习内容
文档标题：{Path(self._current_file_path).stem if self._current_file_path else '未知'}

内容摘要：
{self._current_content[:3000]}

---

请提供：
1. **学习目标**：本文档应掌握的核心内容
2. **学习步骤**：分阶段的学习建议（初读→精读→实践）
3. **重点难点**：需要特别注意的概念
4. **拓展阅读**：推荐的相关术数知识
5. **练习建议**：如何将所学应用于实践
"""
        self._run_analysis("学习方案", prompt)

    def _on_reflection(self):
        """心得生成功能"""
        notes = self._notes_manager.get_all_notes(limit=50)

        if not notes:
            QMessageBox.information(self, "提示", "您还没有任何笔记，请先添加一些学习笔记")
            return

        notes_text = ""
        for note in notes[:20]:
            source_file = note.get('source_file', '')
            source = Path(source_file).stem if source_file else '未知'
            tags = ", ".join(note.get('tags', []))
            notes_text += f"【来源：{source}】\n"
            notes_text += f"摘录：{note.get('content', '无内容')}\n"
            if note.get('user_note'):
                notes_text += f"笔记：{note.get('user_note', '')}\n"
            if tags:
                notes_text += f"标签：{tags}\n"
            notes_text += "\n---\n\n"

        prompt = f"""请根据以下学习笔记，为用户生成一份学习心得报告：

## 用户笔记（共{len(notes)}条）

{notes_text}

---

请生成一份学习心得，包括：
1. **学习主题概览**：用户主要在学习什么
2. **知识点串联**：将零散笔记中的知识点联系起来
3. **理解深度评估**：从笔记内容判断用户的理解程度
4. **学习建议**：基于笔记内容的进一步学习方向
5. **感悟总结**：一段有深度的学习心得

语气要像一位有智慧的老师在与学生交流。
"""
        self._run_analysis("心得", prompt)

    def _on_custom(self):
        """自定义Prompt功能"""
        dialog = CustomPromptDialog(
            current_content=self._current_content,
            current_file=self._current_file_path,
            parent=self
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            prompt = dialog.get_prompt()
            if prompt:
                self._run_analysis("自定义分析", prompt)

    def _run_analysis(self, task_name: str, prompt: str):
        """执行AI分析"""
        self._set_loading(True, task_name)

        self._ai_worker = AIAssistantWorker(self._api_manager, prompt, self)
        self._ai_worker.finished.connect(lambda result: self._on_finished(task_name, result))
        self._ai_worker.error.connect(self._on_error)
        self._ai_worker.start()

    def _on_finished(self, task_name: str, result: str):
        """分析完成"""
        self._set_loading(False)

        dialog = AIResultDialog(task_name, result, self)
        dialog.exec()

    def _on_error(self, error_msg: str):
        """分析出错"""
        self._set_loading(False)
        QMessageBox.warning(self, "AI分析失败", f"分析过程中出现错误：\n{error_msg}")


class AIResultDialog(QDialog):
    """AI分析结果对话框"""

    def __init__(self, task_name: str, result: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"AI{task_name}结果")
        self.setMinimumSize(700, 500)

        self._task_name = task_name
        self._result = result
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 标题
        title_label = QLabel(f"🤖 AI{self._task_name}")
        title_font = title_label.font()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # 结果展示
        result_browser = QTextBrowser()
        result_browser.setMarkdown(self._result)
        result_browser.setStyleSheet("""
            QTextBrowser {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 15px;
                background-color: #fafafa;
            }
        """)
        layout.addWidget(result_browser)

        # 按钮区域
        btn_layout = QHBoxLayout()

        copy_btn = QPushButton("复制内容")
        copy_btn.clicked.connect(self._copy_result)
        copy_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
            }
        """)
        btn_layout.addWidget(copy_btn)

        save_btn = QPushButton("保存为笔记")
        save_btn.clicked.connect(self._save_as_note)
        save_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                border: 1px solid #1976d2;
                border-radius: 5px;
                color: #1976d2;
            }
            QPushButton:hover {
                background-color: #e3f2fd;
            }
        """)
        btn_layout.addWidget(save_btn)

        btn_layout.addStretch()

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                border: none;
                border-radius: 5px;
                background-color: #1976d2;
                color: white;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
        """)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def _copy_result(self):
        """复制结果到剪贴板"""
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self._result)
        QMessageBox.information(self, "已复制", "内容已复制到剪贴板")

    def _save_as_note(self):
        """保存为笔记"""
        notes_manager = get_notes_manager()

        note_id = notes_manager.create_note(
            content=f"AI{self._task_name}结果",
            source_file="AI学习助手",
            source_position="",
            user_note=self._result,
            tags=[f"AI{self._task_name}"]
        )

        if note_id > 0:
            QMessageBox.information(self, "已保存", "分析结果已保存到笔记")
        else:
            QMessageBox.warning(self, "保存失败", "保存笔记时出现错误")


class NotesViewDialog(QDialog):
    """笔记查看弹窗"""

    def __init__(self, title: str, notes: List[Dict[str, Any]], notes_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(700, 500)

        self._notes = notes
        self._notes_manager = notes_manager
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 标题和数量
        header_layout = QHBoxLayout()

        title_label = QLabel(f"📝 {self.windowTitle()}")
        title_font = title_label.font()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        count_label = QLabel(f"{len(self._notes)} 条笔记")
        count_label.setStyleSheet("color: #666;")
        header_layout.addWidget(count_label)

        layout.addLayout(header_layout)

        # 笔记内容区域
        notes_browser = QTextBrowser()
        notes_browser.setStyleSheet("""
            QTextBrowser {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 15px;
                background-color: #fafafa;
            }
        """)

        if not self._notes:
            notes_browser.setHtml("""
                <div style="text-align: center; color: #999; padding: 30px;">
                    暂无笔记
                </div>
            """)
        else:
            html_parts = []
            for note in self._notes:
                source_file = note.get('source_file', '')
                source_name = Path(source_file).stem if source_file else "未知来源"
                tags_html = " ".join([
                    f'<span style="background: #e3f2fd; color: #1976d2; padding: 2px 8px; border-radius: 10px; font-size: 11px;">#{t}</span>'
                    for t in note.get('tags', [])
                ])
                content = note.get('content', '')
                user_note = note.get('user_note', '')

                html_parts.append(f'''
                    <div style="border-bottom: 1px solid #eee; padding: 15px 0; margin-bottom: 10px;">
                        <div style="color: #666; font-size: 12px; margin-bottom: 8px;">
                            📖 来自《{source_name}》
                        </div>
                        <div style="color: #333; font-style: italic; margin-bottom: 8px; background: #f5f5f5; padding: 10px; border-radius: 5px;">
                            "{content}"
                        </div>
                        {f'<div style="color: #555; margin-bottom: 8px;"><b>笔记：</b>{user_note}</div>' if user_note else ''}
                        <div>{tags_html}</div>
                    </div>
                ''')

            notes_browser.setHtml(f'''
                <div style="font-family: sans-serif;">
                    {"".join(html_parts)}
                </div>
            ''')

        layout.addWidget(notes_browser)

        # 按钮区域
        btn_layout = QHBoxLayout()

        export_btn = QPushButton("导出笔记")
        export_btn.clicked.connect(self._on_export)
        export_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                border: 1px solid #1976d2;
                border-radius: 5px;
                color: #1976d2;
            }
            QPushButton:hover {
                background-color: #e3f2fd;
            }
        """)
        btn_layout.addWidget(export_btn)

        btn_layout.addStretch()

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 30px;
                border: none;
                border-radius: 5px;
                background-color: #1976d2;
                color: white;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
        """)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def _on_export(self):
        """导出笔记"""
        markdown = self._notes_manager.export_notes_markdown()

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出笔记",
            "我的笔记.md",
            "Markdown文件 (*.md);;所有文件 (*)"
        )

        if file_path:
            try:
                Path(file_path).write_text(markdown, encoding='utf-8')
                QMessageBox.information(self, "导出成功", f"笔记已导出到:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", str(e))


class NotesSummaryDialog(QDialog):
    """笔记摘要对话框"""

    def __init__(self, total_notes: int, top_tags: list, top_sources: list,
                 notes: list, notes_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("笔记摘要")
        self.setMinimumSize(650, 500)

        self._total_notes = total_notes
        self._top_tags = top_tags
        self._top_sources = top_sources
        self._notes = notes
        self._notes_manager = notes_manager
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 标题
        title_label = QLabel("📋 笔记摘要")
        title_font = title_label.font()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # 统计卡片区域
        stats_frame = QFrame()
        stats_frame.setStyleSheet("""
            QFrame {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
        """)
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setContentsMargins(15, 15, 15, 15)

        # 总数统计
        total_card = self._create_stat_card("笔记总数", str(self._total_notes), "#6366f1")
        stats_layout.addWidget(total_card)

        # 标签数
        tag_count = len(self._top_tags)
        tags_card = self._create_stat_card("标签数", str(tag_count), "#f59e0b")
        stats_layout.addWidget(tags_card)

        # 来源数
        source_count = len(self._top_sources)
        sources_card = self._create_stat_card("文档来源", str(source_count), "#06b6d4")
        stats_layout.addWidget(sources_card)

        layout.addWidget(stats_frame)

        # 热门标签
        if self._top_tags:
            tags_label = QLabel("热门标签：")
            tags_label.setStyleSheet("font-weight: bold; font-size: 13px;")
            layout.addWidget(tags_label)

            tags_flow = QHBoxLayout()
            tags_flow.setSpacing(8)
            for tag, count in self._top_tags[:8]:
                tag_btn = QPushButton(f"#{tag} ({count})")
                tag_btn.setStyleSheet("""
                    QPushButton {
                        padding: 5px 12px;
                        border: 1px solid #e2e8f0;
                        border-radius: 15px;
                        background-color: #f1f5f9;
                        color: #475569;
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background-color: #e2e8f0;
                    }
                """)
                tags_flow.addWidget(tag_btn)
            tags_flow.addStretch()
            layout.addLayout(tags_flow)

        # 热门来源
        if self._top_sources:
            sources_label = QLabel("笔记来源TOP5：")
            sources_label.setStyleSheet("font-weight: bold; font-size: 13px; margin-top: 10px;")
            layout.addWidget(sources_label)

            for source, count in self._top_sources[:5]:
                source_row = QHBoxLayout()
                source_name = QLabel(f"📄 {source}")
                source_name.setStyleSheet("color: #475569;")
                source_row.addWidget(source_name)
                source_row.addStretch()
                count_label = QLabel(f"{count} 条")
                count_label.setStyleSheet("color: #94a3b8;")
                source_row.addWidget(count_label)
                layout.addLayout(source_row)

        layout.addStretch()

        # 按钮区域
        btn_layout = QHBoxLayout()

        view_all_btn = QPushButton("查看全部笔记")
        view_all_btn.clicked.connect(self._on_view_all)
        view_all_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                border: 1px solid #6366f1;
                border-radius: 5px;
                color: #6366f1;
            }
            QPushButton:hover {
                background-color: #eef2ff;
            }
        """)
        btn_layout.addWidget(view_all_btn)

        export_btn = QPushButton("导出笔记")
        export_btn.clicked.connect(self._on_export)
        export_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                border: 1px solid #f59e0b;
                border-radius: 5px;
                color: #f59e0b;
            }
            QPushButton:hover {
                background-color: #fef3c7;
            }
        """)
        btn_layout.addWidget(export_btn)

        btn_layout.addStretch()

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 30px;
                border: none;
                border-radius: 5px;
                background-color: #6366f1;
                color: white;
            }
            QPushButton:hover {
                background-color: #4f46e5;
            }
        """)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def _create_stat_card(self, title: str, value: str, color: str) -> QFrame:
        """创建统计卡片"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                border-left: 4px solid {color};
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(15, 10, 15, 10)

        value_label = QLabel(value)
        value_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color};")
        card_layout.addWidget(value_label)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px; color: #64748b;")
        card_layout.addWidget(title_label)

        return card

    def _on_view_all(self):
        """查看全部笔记"""
        dialog = NotesViewDialog("全部笔记", self._notes, self._notes_manager, self)
        dialog.exec()

    def _on_export(self):
        """导出笔记"""
        markdown = self._notes_manager.export_notes_markdown()

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出笔记",
            "我的笔记.md",
            "Markdown文件 (*.md);;所有文件 (*)"
        )

        if file_path:
            try:
                Path(file_path).write_text(markdown, encoding='utf-8')
                QMessageBox.information(self, "导出成功", f"笔记已导出到:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", str(e))
