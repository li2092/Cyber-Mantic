"""
ChatWidget - 聊天消息组件

支持显示用户和AI的对话消息，带有美化样式
- 左侧AI气泡：显示Logo + "赛博玄数"
- 右侧用户气泡：紫色气泡，不显示头像
- 气泡宽度自适应，多行时固定宽度
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QTextBrowser,
    QScrollArea, QLabel, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer
from PyQt6.QtGui import QFont, QPixmap
from enum import Enum
from datetime import datetime
from typing import List, Optional
import os
import re

# 导入WebEngine组件（如果可用）
from .markdown_webview import (
    MarkdownWebView, MarkdownTypewriter, is_webengine_available, WEBENGINE_AVAILABLE
)


def escape_html(text: str) -> str:
    """转义HTML特殊字符"""
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def process_inline_markdown(text: str) -> str:
    """处理行内Markdown格式（加粗、斜体、代码等）"""
    # 先转义HTML
    text = escape_html(text)

    # 加粗 **text** 或 __text__
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong style="color: #E2E8F0;">\1</strong>', text)
    text = re.sub(r'__(.+?)__', r'<strong style="color: #E2E8F0;">\1</strong>', text)

    # 斜体 *text* 或 _text_（注意不要和加粗冲突）
    text = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<em>\1</em>', text)
    text = re.sub(r'(?<!_)_([^_]+?)_(?!_)', r'<em>\1</em>', text)

    # 行内代码 `code`
    text = re.sub(r'`([^`]+?)`', r'<code style="background: #1E1E2E; padding: 2px 6px; border-radius: 4px; font-family: monospace;">\1</code>', text)

    return text


def markdown_to_styled_html(content: str) -> str:
    """将Markdown转换为带样式的HTML（保持打字动画和最终效果一致）"""
    if not content:
        return ""

    lines = content.split('\n')
    html_lines = []
    in_code_block = False

    for line in lines:
        # 处理代码块
        if line.strip().startswith('```'):
            if in_code_block:
                html_lines.append('</pre>')
                in_code_block = False
            else:
                html_lines.append('<pre style="background: #1E1E2E; padding: 8px; border-radius: 6px; margin: 4px 0; overflow-x: auto; font-family: monospace; font-size: 0.9em;">')
                in_code_block = True
            continue

        if in_code_block:
            html_lines.append(escape_html(line) + '\n')
            continue

        # 处理标题
        if line.startswith('### '):
            text = line[4:]
            html_lines.append(f'<p style="font-weight: bold; font-size: 1.1em; margin: 8px 0 4px 0; color: #A78BFA;">{escape_html(text)}</p>')
        elif line.startswith('## '):
            text = line[3:]
            html_lines.append(f'<p style="font-weight: bold; font-size: 1.2em; margin: 10px 0 6px 0; color: #C4B5FD;">{escape_html(text)}</p>')
        elif line.startswith('# '):
            text = line[2:]
            html_lines.append(f'<p style="font-weight: bold; font-size: 1.3em; margin: 12px 0 8px 0; color: #DDD6FE;">{escape_html(text)}</p>')
        # 处理列表项
        elif line.strip().startswith('- ') or line.strip().startswith('* '):
            indent = len(line) - len(line.lstrip())
            text = line.strip()[2:]
            text = process_inline_markdown(text)
            margin_left = 16 + (indent // 2) * 12
            html_lines.append(f'<p style="margin: 2px 0 2px {margin_left}px;">• {text}</p>')
        elif re.match(r'^\d+\.\s', line.strip()):
            # 数字列表
            match = re.match(r'^(\d+)\.\s(.*)$', line.strip())
            if match:
                num = match.group(1)
                text = process_inline_markdown(match.group(2))
                html_lines.append(f'<p style="margin: 2px 0 2px 16px;">{num}. {text}</p>')
        # 处理引用
        elif line.startswith('> '):
            text = process_inline_markdown(line[2:])
            html_lines.append(f'<p style="border-left: 3px solid #6366F1; padding-left: 12px; margin: 4px 0; color: #94A3B8; font-style: italic;">{text}</p>')
        # 处理分割线
        elif line.strip() in ('---', '***', '___'):
            html_lines.append('<hr style="border: none; border-top: 1px solid #4B5563; margin: 8px 0;">')
        # 普通段落
        elif line.strip():
            text = process_inline_markdown(line)
            html_lines.append(f'<p style="margin: 4px 0; line-height: 1.6;">{text}</p>')
        else:
            # 空行
            html_lines.append('<p style="margin: 4px 0;"></p>')

    # 如果代码块没有关闭，强制关闭
    if in_code_block:
        html_lines.append('</pre>')

    return '<div style="line-height: 1.5;">' + ''.join(html_lines) + '</div>'


class AutoResizingTextBrowser(QTextBrowser):
    """自动根据内容调整高度的TextBrowser - 禁用内部滚动，让父级ScrollArea处理滚动"""

    def __init__(self, parent=None):
        super().__init__(parent)
        # 禁用滚动条
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # 启用自动换行
        self.setLineWrapMode(QTextBrowser.LineWrapMode.WidgetWidth)
        self.setWordWrapMode(self.document().defaultTextOption().wrapMode())
        # 监听文档内容变化
        self.document().contentsChanged.connect(self._on_content_changed)
        # 延迟调整高度，确保布局完成
        self._pending_adjust = False
        # 打字动画模式标志 - 打字时不频繁调整高度
        self._typing_mode = False
        # 最后一次调整的高度
        self._last_height = 50

    def set_typing_mode(self, enabled: bool):
        """设置打字模式（打字时减少高度调整频率）"""
        self._typing_mode = enabled
        if not enabled:
            # 退出打字模式时，调整到最终高度
            self._adjust_height()

    def _on_content_changed(self):
        """内容变化时的处理"""
        if self._typing_mode:
            # 打字模式下，只增加高度，不减少（避免跳动）
            self._adjust_height_grow_only()
        else:
            self._adjust_height()

    def _adjust_height_grow_only(self):
        """只增加高度的调整（用于打字动画）"""
        if self.width() > 0:
            self.document().setTextWidth(self.width() - 24)
        self.document().adjustSize()
        doc_height = self.document().size().height()
        new_height = int(doc_height + 40)
        # 只有当新高度大于当前高度时才调整
        if new_height > self._last_height:
            self._last_height = new_height
            self.setMinimumHeight(new_height)

    def _adjust_height(self):
        """根据文档内容调整高度"""
        # 设置文档宽度为控件宽度，确保正确换行
        if self.width() > 0:
            self.document().setTextWidth(self.width() - 24)  # 减去padding
        # 调整文档大小
        self.document().adjustSize()
        # 获取文档高度
        doc_height = self.document().size().height()
        # 设置控件高度（文档高度 + 边距），增加边距以防止截断
        new_height = int(doc_height + 40)  # 40px for padding
        self._last_height = max(new_height, 50)
        self.setMinimumHeight(self._last_height)

    def resizeEvent(self, event):
        """控件大小改变时重新计算高度"""
        super().resizeEvent(event)
        # 延迟调整，避免频繁计算
        if not self._pending_adjust and not self._typing_mode:
            self._pending_adjust = True
            QTimer.singleShot(10, self._delayed_adjust)

    def _delayed_adjust(self):
        """延迟执行高度调整"""
        self._pending_adjust = False
        self._adjust_height()

    def sizeHint(self):
        """返回建议的大小"""
        doc_height = self.document().size().height()
        return QSize(self.width(), int(doc_height + 40))

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


class TypewriterAnimation:
    """打字机动画控制器 - 平滑逐字显示，避免文字跳动

    核心优化：打字过程中使用纯文本显示，避免Markdown重新渲染导致的跳动
    只在动画结束后渲染完整Markdown
    """

    def __init__(self, text_browser, content: str, is_markdown: bool = True,
                 char_delay: int = 12, newline_delay: int = 80, chunk_size: int = 5):
        """
        初始化打字机动画

        Args:
            text_browser: 要显示内容的TextBrowser (AutoResizingTextBrowser)
            content: 要显示的完整内容
            is_markdown: 是否为Markdown格式（最终渲染时使用）
            char_delay: 每组字符的延迟（毫秒）
            newline_delay: 换行时的额外延迟（毫秒）
            chunk_size: 每次显示的字符数（减少渲染频率）
        """
        self.text_browser = text_browser
        self.full_content = content
        self.is_markdown = is_markdown
        self.char_delay = char_delay
        self.newline_delay = newline_delay
        self.chunk_size = chunk_size
        self.current_index = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self._type_next_chunk)
        self._is_running = False
        self._fixed_width = None  # 固定宽度，避免跳动

    def start(self):
        """开始打字动画"""
        self._is_running = True
        self.current_index = 0
        self.text_browser.clear()

        # 启用打字模式，减少高度调整频率
        if hasattr(self.text_browser, 'set_typing_mode'):
            self.text_browser.set_typing_mode(True)

        # 固定文本区域宽度，避免打字过程中宽度变化
        if self.text_browser.width() > 0:
            self._fixed_width = self.text_browser.width()
            self.text_browser.setFixedWidth(self._fixed_width)
            self.text_browser.document().setTextWidth(self._fixed_width - 24)

        self.timer.start(self.char_delay)

    def stop(self):
        """停止动画并显示完整内容"""
        self._is_running = False
        self.timer.stop()
        # 关闭打字模式
        if hasattr(self.text_browser, 'set_typing_mode'):
            self.text_browser.set_typing_mode(False)
        # 解除宽度固定
        self._release_fixed_width()
        self._show_full_content()

    def _release_fixed_width(self):
        """解除固定宽度"""
        if self._fixed_width:
            self.text_browser.setMinimumWidth(0)
            self.text_browser.setMaximumWidth(16777215)  # QWIDGETSIZE_MAX
            self._fixed_width = None

    def _type_next_chunk(self):
        """显示下一组字符"""
        if self.current_index >= len(self.full_content):
            self.timer.stop()
            self._is_running = False
            # 关闭打字模式
            if hasattr(self.text_browser, 'set_typing_mode'):
                self.text_browser.set_typing_mode(False)
            # 解除宽度固定
            self._release_fixed_width()
            # 最终渲染完整Markdown
            self._show_full_content()
            return

        # 计算本次显示到哪个位置
        next_index = min(self.current_index + self.chunk_size, len(self.full_content))

        # 检查是否遇到换行符，如果是则在换行处停止
        chunk = self.full_content[self.current_index:next_index]
        newline_pos = chunk.find('\n')
        if newline_pos != -1:
            next_index = self.current_index + newline_pos + 1
            has_newline = True
        else:
            has_newline = False

        self.current_index = next_index

        # 显示当前已输入的内容 - 使用纯文本HTML，避免Markdown渲染跳动
        current_text = self.full_content[:self.current_index]
        # 转义HTML特殊字符
        escaped = current_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        # 保留换行
        html = escaped.replace('\n', '<br>')
        # 使用pre-wrap保持空格和换行
        self.text_browser.setHtml(f'''
            <div style="white-space: pre-wrap; word-wrap: break-word; line-height: 1.5;">
                {html}<span style="opacity: 0.5;">▋</span>
            </div>
        ''')

        # 如果遇到换行符，增加延迟
        if has_newline:
            self.timer.setInterval(self.newline_delay)
        else:
            self.timer.setInterval(self.char_delay)

    def _show_full_content(self):
        """显示完整内容（优化的Markdown渲染）"""
        if self.is_markdown:
            # 使用全局函数进行优化的HTML渲染
            html = markdown_to_styled_html(self.full_content)
            self.text_browser.setHtml(html)
        else:
            escaped = escape_html(self.full_content)
            html = escaped.replace('\n', '<br>')
            self.text_browser.setHtml(f'<div style="white-space: pre-wrap;">{html}</div>')

    def is_running(self) -> bool:
        """返回动画是否正在运行"""
        return self._is_running


class ChatBubble(QFrame):
    """单条消息气泡 - 仿微信/常见聊天软件风格"""

    # Logo路径（类变量，只加载一次）
    _logo_pixmap = None
    _logo_path = None

    def __init__(self, message: ChatMessage, font_size: int = 11, animated: bool = False,
                 theme: str = "light", parent=None):
        super().__init__(parent)
        self.message = message
        self.font_size = font_size
        self.animated = animated
        self.theme = theme
        self.content_browser = None
        self.content_webview = None
        self.typewriter = None
        self.web_typewriter = None
        self._fixed_width = None  # 多行时固定宽度
        self._setup_ui()

    @classmethod
    def _get_logo_pixmap(cls) -> QPixmap:
        """获取Logo图片（懒加载）"""
        if cls._logo_pixmap is None:
            # 尝试多个可能的路径
            possible_paths = [
                os.path.join(os.path.dirname(__file__), '..', 'resources', 'app_icon.png'),
                os.path.join(os.path.dirname(__file__), '..', '..', 'ui', 'resources', 'app_icon.png'),
                'cyber_mantic/ui/resources/app_icon.png',
            ]
            for path in possible_paths:
                abs_path = os.path.abspath(path)
                if os.path.exists(abs_path):
                    cls._logo_path = abs_path
                    cls._logo_pixmap = QPixmap(abs_path)
                    break
            if cls._logo_pixmap is None:
                cls._logo_pixmap = QPixmap()  # 空图片
        return cls._logo_pixmap

    def _setup_ui(self):
        """设置UI - 左右分离的气泡布局"""
        # 根据主题选择颜色
        is_dark = self.theme == "dark"

        # 用户气泡颜色（紫色系）
        user_bubble_bg = "#7C3AED" if not is_dark else "#8B5CF6"  # 紫色
        user_text_color = "#FFFFFF"

        # AI气泡颜色
        ai_bubble_bg = "#FFFFFF" if not is_dark else "#2D2D3A"
        ai_text_color = "#1E293B" if not is_dark else "#F1F5F9"
        ai_border_color = "#E2E8F0" if not is_dark else "#3D3D4A"
        ai_name_color = "#64748B" if not is_dark else "#94A3B8"

        # 主布局
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(16, 4, 16, 4)  # 减少上下边距
        main_layout.setSpacing(0)

        if self.message.role == MessageRole.USER:
            # ========== 用户消息：右侧紫色气泡，不显示头像 ==========
            main_layout.addStretch()  # 左侧弹性空间，推到右边

            # 气泡容器
            bubble_widget = QFrame()
            bubble_widget.setObjectName("userBubble")
            bubble_layout = QVBoxLayout(bubble_widget)
            bubble_layout.setContentsMargins(12, 8, 12, 8)  # 减少内边距
            bubble_layout.setSpacing(0)

            # 消息内容
            self.content_browser = AutoResizingTextBrowser()
            self.content_browser.setReadOnly(True)
            self.content_browser.setFrameStyle(QFrame.Shape.NoFrame)

            font = QFont()
            font.setPointSize(self.font_size)
            self.content_browser.setFont(font)
            self.content_browser.document().setDocumentMargin(0)

            # 用户消息纯文本 - 文字左对齐
            escaped_content = self.message.content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            html_content = escaped_content.replace('\n', '<br>')
            self.content_browser.setHtml(f'''<p style="margin:0; padding:0; color:{user_text_color};">{html_content}</p>''')

            bubble_layout.addWidget(self.content_browser)

            # 设置气泡样式 - 紫色圆角
            bubble_widget.setStyleSheet(f"""
                QFrame#userBubble {{
                    background-color: {user_bubble_bg};
                    border-radius: 16px;
                    border-top-right-radius: 4px;
                }}
                AutoResizingTextBrowser {{
                    background-color: transparent;
                    color: {user_text_color};
                    border: none;
                }}
            """)

            # 设置最大宽度（不超过60%）
            bubble_widget.setMaximumWidth(500)
            bubble_widget.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)

            main_layout.addWidget(bubble_widget)

        else:
            # ========== AI消息：左侧气泡，Logo和名字在气泡上方 ==========

            # 整体容器（垂直布局：头部 + 气泡）
            ai_container = QWidget()
            ai_main_layout = QVBoxLayout(ai_container)
            ai_main_layout.setContentsMargins(0, 0, 0, 0)
            ai_main_layout.setSpacing(4)

            # 头部区域（Logo + 名字 横排）
            header_widget = QWidget()
            header_layout = QHBoxLayout(header_widget)
            header_layout.setContentsMargins(0, 0, 0, 0)
            header_layout.setSpacing(6)
            header_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

            # Logo图片（小一点）
            logo_label = QLabel()
            logo_pixmap = self._get_logo_pixmap()
            if not logo_pixmap.isNull():
                scaled_pixmap = logo_pixmap.scaled(
                    24, 24,  # 更小的Logo
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                logo_label.setPixmap(scaled_pixmap)
            else:
                logo_label.setText("🔮")
                logo_label.setStyleSheet("font-size: 16px;")
            logo_label.setFixedSize(24, 24)
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header_layout.addWidget(logo_label)

            # 名字
            name_label = QLabel("赛博玄数")
            name_label.setStyleSheet(f"""
                font-size: 11px;
                color: {ai_name_color};
                font-weight: 500;
            """)
            header_layout.addWidget(name_label)
            header_layout.addStretch()

            ai_main_layout.addWidget(header_widget)

            # 气泡容器
            bubble_widget = QFrame()
            bubble_widget.setObjectName("aiBubble")
            bubble_layout = QVBoxLayout(bubble_widget)
            bubble_layout.setContentsMargins(12, 8, 12, 8)
            bubble_layout.setSpacing(0)

            # 消息内容 - 优先使用WebEngine获得更好的渲染效果
            if WEBENGINE_AVAILABLE:
                self.content_webview = MarkdownWebView(theme=self.theme)
                self.content_browser = None  # WebEngine模式下不使用TextBrowser

                # AI消息：Markdown渲染
                if self.animated and self.message.content:
                    self.web_typewriter = MarkdownTypewriter(
                        self.content_webview,
                        self.message.content,
                        char_delay=15,
                        chunk_size=5
                    )
                    self.web_typewriter.start()
                else:
                    self.content_webview.set_markdown(self.message.content)

                bubble_layout.addWidget(self.content_webview)
            else:
                # 回退到QTextBrowser
                self.content_webview = None
                self.content_browser = AutoResizingTextBrowser()
                self.content_browser.setReadOnly(True)
                self.content_browser.setFrameStyle(QFrame.Shape.NoFrame)

                font = QFont()
                font.setPointSize(self.font_size)
                self.content_browser.setFont(font)
                self.content_browser.document().setDocumentMargin(0)

                # AI消息：Markdown渲染
                if self.animated and self.message.content:
                    self.typewriter = TypewriterAnimation(
                        self.content_browser,
                        self.message.content,
                        is_markdown=True,
                        char_delay=15,
                        newline_delay=100
                    )
                    self.typewriter.start()
                else:
                    # 使用优化的HTML渲染
                    html = markdown_to_styled_html(self.message.content)
                    self.content_browser.setHtml(html)

                bubble_layout.addWidget(self.content_browser)

            # 设置气泡样式 - 白色/深色圆角
            bubble_widget.setStyleSheet(f"""
                QFrame#aiBubble {{
                    background-color: {ai_bubble_bg};
                    border: 1px solid {ai_border_color};
                    border-radius: 16px;
                    border-top-left-radius: 4px;
                }}
                AutoResizingTextBrowser {{
                    background-color: transparent;
                    color: {ai_text_color};
                    border: none;
                }}
            """)

            # 设置最大宽度（不超过70%）
            bubble_widget.setMaximumWidth(600)
            bubble_widget.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)

            ai_main_layout.addWidget(bubble_widget)

            main_layout.addWidget(ai_container)
            main_layout.addStretch()  # 右侧弹性空间

        self.setLayout(main_layout)
        self.setStyleSheet("ChatBubble { background-color: transparent; border: none; }")

    def stop_animation(self):
        """停止打字动画，立即显示完整内容"""
        if self.typewriter and self.typewriter.is_running():
            self.typewriter.stop()
        if self.web_typewriter and self.web_typewriter.is_running():
            self.web_typewriter.stop()

    def is_animating(self) -> bool:
        """检查是否正在播放动画"""
        if self.typewriter is not None and self.typewriter.is_running():
            return True
        if self.web_typewriter is not None and self.web_typewriter.is_running():
            return True
        return False

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
        self.font_size: int = 11  # 默认字体大小
        self.theme: str = "light"  # 当前主题
        self._setup_ui()

    def set_theme(self, theme: str):
        """设置主题并刷新所有气泡"""
        self.theme = theme
        # 重新创建所有气泡以应用新主题
        self._refresh_all_bubbles()

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
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

    def add_message(self, role: MessageRole, content: str, auto_scroll: bool = True, animated: bool = False):
        """
        添加一条消息

        Args:
            role: 消息角色
            content: 消息内容（支持Markdown）
            auto_scroll: 是否自动滚动到底部
            animated: 是否使用打字机效果显示（仅对AI消息有效）
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

        # 创建气泡，传入当前字体大小、动画设置和主题
        bubble = ChatBubble(message, self.font_size, animated=animated, theme=self.theme)

        # 插入到布局中（在stretch之前）
        count = self.messages_layout.count()
        self.messages_layout.insertWidget(count - 1, bubble)

        # 自动滚动到底部
        if auto_scroll:
            self._scroll_to_bottom()

    def _refresh_all_bubbles(self):
        """刷新所有气泡以应用新主题"""
        # 保存当前消息
        messages_copy = self.messages.copy()
        # 清空
        self.clear_messages()
        # 重新添加
        for msg in messages_copy:
            self.add_message(msg.role, msg.content, auto_scroll=False, animated=False)
        self._scroll_to_bottom()

    def add_user_message(self, content: str):
        """添加用户消息"""
        self.add_message(MessageRole.USER, content)

    def add_assistant_message(self, content: str, animated: bool = True):
        """
        添加AI助手消息

        Args:
            content: 消息内容
            animated: 是否使用打字机效果，默认启用
        """
        self.add_message(MessageRole.ASSISTANT, content, animated=animated)

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
                # 重新创建气泡，传入当前字体大小和主题
                new_bubble = ChatBubble(self.messages[-1], self.font_size, theme=self.theme)
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
            self.add_message(msg.role, msg.content, auto_scroll=False, animated=False)
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

    def update_theme(self, theme: str):
        """
        更新主题（外部调用接口）

        Args:
            theme: 主题名称 ('light' 或 'dark')
        """
        self.set_theme(theme)
