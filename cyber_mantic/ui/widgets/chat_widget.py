"""
ChatWidget - 聊天消息组件

支持显示用户和AI的对话消息，带有美化样式
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QTextBrowser,
    QScrollArea, QLabel, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer
from PyQt6.QtGui import QFont
from enum import Enum
from datetime import datetime
from typing import List, Optional


class AutoResizingTextBrowser(QTextBrowser):
    """自动根据内容调整高度的TextBrowser - 禁用内部滚动，让父级ScrollArea处理滚动"""

    def __init__(self, parent=None):
        super().__init__(parent)
        # 禁用滚动条
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # 监听文档内容变化
        self.document().contentsChanged.connect(self._adjust_height)

    def _adjust_height(self):
        """根据文档内容调整高度"""
        # 调整文档大小
        self.document().adjustSize()
        # 获取文档高度
        doc_height = self.document().size().height()
        # 设置控件高度（文档高度 + 边距）
        new_height = int(doc_height + 30)  # 30px for padding
        self.setFixedHeight(max(new_height, 60))  # 最小60px

    def sizeHint(self):
        """返回建议的大小"""
        doc_height = self.document().size().height()
        return QSize(self.width(), int(doc_height + 30))

    def wheelEvent(self, event):
        """
        拦截滚轮事件，转发给父级ScrollArea处理
        这样用户在消息气泡上滚动鼠标时，会滚动整个对话区域而不是单个消息
        """
        # 忽略事件，让它传递给父级widget处理
        event.ignore()


class MessageRole(Enum):
    """消息角色"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage:
    """聊天消息数据类"""
    def __init__(self, role: MessageRole, content: str, timestamp: Optional[datetime] = None):
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.now()

    def to_dict(self):
        return {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat()
        }


class ChatBubble(QFrame):
    """单条消息气泡"""

    def __init__(self, message: ChatMessage, font_size: int = 10, parent=None):
        super().__init__(parent)
        self.message = message
        self.font_size = font_size
        self.content_browser = None  # 保存内容浏览器引用
        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout()

        # 根据消息角色设置不同的边距
        # 用户消息：右对齐，左侧留更多空间
        # AI消息：左对齐，右侧留更多空间
        if self.message.role == MessageRole.USER:
            layout.setContentsMargins(60, 2, 10, 2)  # 左侧60px，右侧10px，上下减小到2px
        else:
            layout.setContentsMargins(10, 2, 60, 2)  # 左侧10px，右侧60px，上下减小到2px

        layout.setSpacing(2)

        # 消息头部（角色 + 时间）
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        # 角色图标和名称
        role_label = QLabel()
        if self.message.role == MessageRole.USER:
            role_label.setText("👤 您")
            role_label.setStyleSheet("color: #1976D2; font-weight: bold; font-size: 11pt;")
        elif self.message.role == MessageRole.ASSISTANT:
            role_label.setText("🤖 AI助手")
            role_label.setStyleSheet("color: #388E3C; font-weight: bold; font-size: 11pt;")
        else:
            role_label.setText("ℹ️ 系统")
            role_label.setStyleSheet("font-weight: bold; font-size: 11pt;")

        # 根据角色决定头像位置
        if self.message.role == MessageRole.USER:
            header_layout.addStretch()  # 用户消息靠右

        header_layout.addWidget(role_label)

        # 时间戳
        time_label = QLabel(self.message.timestamp.strftime("%H:%M:%S"))
        time_label.setStyleSheet("font-size: 10px;")
        header_layout.addWidget(time_label)

        if self.message.role != MessageRole.USER:
            header_layout.addStretch()  # AI消息靠左

        layout.addLayout(header_layout)

        # 消息内容 - 使用自动调整高度的TextBrowser
        # 支持Markdown渲染，内容完全展示，不在气泡内滚动
        self.content_browser = AutoResizingTextBrowser()
        self.content_browser.setReadOnly(True)
        self.content_browser.setFrameStyle(QFrame.Shape.NoFrame)

        # 设置字体
        font = QFont()
        font.setPointSize(self.font_size)
        self.content_browser.setFont(font)

        # 设置文档边距
        self.content_browser.document().setDocumentMargin(12)

        # 设置背景和样式 - 移除硬编码颜色，使用主题色
        self.content_browser.setStyleSheet("""
            AutoResizingTextBrowser {
                border-radius: 8px;
                padding: 12px;
            }
        """)

        # 根据角色设置内容格式和对齐方式
        if self.message.role == MessageRole.USER:
            # 用户消息：纯文本显示（保留换行符），右对齐
            # 将换行符转换为HTML格式，并设置右对齐
            escaped_content = self.message.content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            html_content = escaped_content.replace('\n', '<br>')
            self.content_browser.setHtml(f'<div style="text-align: right; white-space: pre-wrap;">{html_content}</div>')
        else:
            # AI/系统消息：Markdown渲染，左对齐
            self.content_browser.setMarkdown(self.message.content)

        layout.addWidget(self.content_browser)

        self.setLayout(layout)

        # 移除气泡背景，使用简洁样式
        self.setStyleSheet("""
            ChatBubble {
                background-color: transparent;
                border: none;
            }
        """)

    def update_font_size(self, font_size: int):
        """更新字体大小"""
        self.font_size = font_size
        if self.content_browser:
            font = QFont()
            font.setPointSize(self.font_size)
            self.content_browser.setFont(font)
            # 触发高度重新计算
            self.content_browser._adjust_height()


class ChatWidget(QWidget):
    """聊天消息组件"""

    # 信号：用户滚动到底部时触发（用于加载更多历史消息）
    scrolled_to_top = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.messages: List[ChatMessage] = []
        self.font_size: int = 10  # 默认字体大小
        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setFrameStyle(QFrame.Shape.NoFrame)

        # 消息容器
        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout()
        self.messages_layout.setContentsMargins(16, 8, 16, 8)
        self.messages_layout.setSpacing(4)  # 减小消息间距，让对话更紧凑
        self.messages_layout.addStretch()  # 底部伸展，保持消息从下往上堆叠
        self.messages_container.setLayout(self.messages_layout)

        self.scroll_area.setWidget(self.messages_container)

        # 监听滚动事件
        self.scroll_area.verticalScrollBar().valueChanged.connect(
            self._on_scroll_changed
        )

        layout.addWidget(self.scroll_area)
        self.setLayout(layout)

        # 样式 - 移除硬编码颜色，使用主题色
        self.setStyleSheet("""
            QScrollArea {
                border: none;
            }
        """)

    def add_message(self, role: MessageRole, content: str, auto_scroll: bool = True):
        """
        添加一条消息

        Args:
            role: 消息角色
            content: 消息内容（支持Markdown）
            auto_scroll: 是否自动滚动到底部
        """
        # 调试：记录消息内容
        from utils.logger import get_logger
        logger = get_logger(__name__)
        logger.debug(f"添加消息 - 角色: {role.value}, 内容长度: {len(content) if content else 0}, 内容预览: {content[:100] if content else '(空)'}")

        # 确保content不为None
        if content is None:
            content = ""

        message = ChatMessage(role, content)
        self.messages.append(message)

        # 创建气泡，传入当前字体大小
        bubble = ChatBubble(message, self.font_size)

        # 插入到布局中（在stretch之前）
        count = self.messages_layout.count()
        self.messages_layout.insertWidget(count - 1, bubble)

        # 自动滚动到底部
        if auto_scroll:
            self._scroll_to_bottom()

    def add_user_message(self, content: str):
        """添加用户消息"""
        self.add_message(MessageRole.USER, content)

    def add_assistant_message(self, content: str):
        """添加AI助手消息"""
        self.add_message(MessageRole.ASSISTANT, content)

    def add_system_message(self, content: str):
        """添加系统消息"""
        self.add_message(MessageRole.SYSTEM, content)

    def update_last_message(self, content: str):
        """
        更新最后一条消息的内容（用于流式输出）

        Args:
            content: 新的消息内容
        """
        if not self.messages:
            return

        # 更新消息内容
        self.messages[-1].content = content

        # 更新UI
        count = self.messages_layout.count()
        if count > 1:  # 至少有1个widget（bubble）+ 1个stretch
            bubble_widget = self.messages_layout.itemAt(count - 2).widget()
            if isinstance(bubble_widget, ChatBubble):
                # 重新创建气泡，传入当前字体大小
                new_bubble = ChatBubble(self.messages[-1], self.font_size)
                self.messages_layout.replaceWidget(bubble_widget, new_bubble)
                bubble_widget.deleteLater()
                self._scroll_to_bottom()

    def clear_messages(self):
        """清空所有消息"""
        self.messages.clear()

        # 清空UI
        while self.messages_layout.count() > 1:  # 保留最后的stretch
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def get_messages(self) -> List[ChatMessage]:
        """获取所有消息"""
        return self.messages.copy()

    def load_messages(self, messages: List[ChatMessage]):
        """
        加载历史消息

        Args:
            messages: 消息列表
        """
        self.clear_messages()
        for msg in messages:
            self.add_message(msg.role, msg.content, auto_scroll=False)
        self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        """滚动到底部（使用延迟确保布局更新完成）"""
        # 使用短延迟确保布局已更新，否则滚动可能在内容渲染前执行
        QTimer.singleShot(10, self._do_scroll_to_bottom)

    def _do_scroll_to_bottom(self):
        """实际执行滚动到底部"""
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _on_scroll_changed(self, value):
        """滚动位置变化时触发"""
        scrollbar = self.scroll_area.verticalScrollBar()
        # 如果滚动到顶部，触发信号
        if value == scrollbar.minimum() and value < scrollbar.maximum():
            self.scrolled_to_top.emit()

    def export_to_markdown(self) -> str:
        """
        导出对话为Markdown格式

        Returns:
            Markdown文本
        """
        lines = ["# 对话记录\n"]

        for msg in self.messages:
            time_str = msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            role_str = {
                MessageRole.USER: "**用户**",
                MessageRole.ASSISTANT: "**AI助手**",
                MessageRole.SYSTEM: "*系统*"
            }.get(msg.role, "未知")

            lines.append(f"## {role_str} - {time_str}\n")
            lines.append(f"{msg.content}\n")
            lines.append("---\n")

        return "\n".join(lines)

    def set_font_size(self, font_size: int):
        """
        设置字体大小并应用到所有消息

        Args:
            font_size: 字体大小（pt）
        """
        self.font_size = font_size

        # 更新所有现有的气泡
        count = self.messages_layout.count()
        for i in range(count - 1):  # 排除最后的stretch
            item = self.messages_layout.itemAt(i)
            if item and item.widget():
                bubble = item.widget()
                if isinstance(bubble, ChatBubble):
                    bubble.update_font_size(font_size)
