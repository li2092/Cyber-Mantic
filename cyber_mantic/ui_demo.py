"""
赛博玄数 UI 美观Demo - PyQt6

展示优化后的UI设计方案：
1. 优化的打字机效果（渐进式渲染，无跳变）
2. 美观的聊天气泡设计
3. 简洁的侧边栏（无收缩功能）
4. 统一的Emoji图标
5. 修复Logo背景色差

运行: python -m cyber_mantic.ui_demo
"""

import sys
import re
from datetime import datetime
from typing import Optional, List
from enum import Enum

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QTextBrowser, QPushButton, QLabel, QFrame,
    QScrollArea, QSplitter, QSizePolicy, QGroupBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QPixmap, QColor, QPainter, QBrush, QPen


# ==================== 设计系统常量 ====================

class DesignSystem:
    """统一设计系统"""

    # 间距 (8px基准)
    SPACING_XS = 4
    SPACING_SM = 8
    SPACING_MD = 16
    SPACING_LG = 24
    SPACING_XL = 32

    # 字号
    FONT_XS = 11
    FONT_SM = 13
    FONT_BASE = 14
    FONT_MD = 16
    FONT_LG = 18
    FONT_XL = 20
    FONT_XXL = 24

    # 圆角
    RADIUS_SM = 6
    RADIUS_MD = 10
    RADIUS_LG = 14
    RADIUS_XL = 18

    # 颜色 - 深色主题
    COLORS_DARK = {
        "bg_primary": "#0F0F1A",
        "bg_secondary": "#1A1A2E",
        "bg_tertiary": "#252542",
        "surface": "#2D2D3D",
        "border": "rgba(255, 255, 255, 0.08)",
        "text_primary": "#F1F5F9",
        "text_secondary": "#94A3B8",
        "text_muted": "#64748B",
        "primary": "#6366F1",
        "primary_light": "#818CF8",
        "success": "#10B981",
        "warning": "#F59E0B",
        "error": "#EF4444",
        # 气泡颜色
        "user_bubble": "#6366F1",
        "user_text": "#FFFFFF",
        "ai_bubble": "#2D2D3D",
        "ai_text": "#F1F5F9",
        "ai_border": "#3D3D4D",
    }

    # 颜色 - 浅色主题
    COLORS_LIGHT = {
        "bg_primary": "#F8FAFC",
        "bg_secondary": "#F1F5F9",
        "bg_tertiary": "#E2E8F0",
        "surface": "#FFFFFF",
        "border": "rgba(0, 0, 0, 0.08)",
        "text_primary": "#1E293B",
        "text_secondary": "#64748B",
        "text_muted": "#94A3B8",
        "primary": "#6366F1",
        "primary_light": "#818CF8",
        "success": "#10B981",
        "warning": "#F59E0B",
        "error": "#EF4444",
        # 气泡颜色
        "user_bubble": "#6366F1",
        "user_text": "#FFFFFF",
        "ai_bubble": "#FFFFFF",
        "ai_text": "#1E293B",
        "ai_border": "#E2E8F0",
    }

DS = DesignSystem()


# ==================== 渐进式Markdown渲染器 ====================

class ProgressiveMarkdownRenderer:
    """
    渐进式Markdown渲染器

    核心优化：打字过程中就应用HTML样式，避免最终渲染时的跳变

    策略：
    1. 打字过程中实时将当前文本渲染为HTML
    2. 使用与最终渲染一致的样式
    3. 未完成的行使用较浅的颜色提示"正在输入"
    """

    def __init__(self, theme: str = "dark"):
        self.theme = theme
        self.colors = DS.COLORS_DARK if theme == "dark" else DS.COLORS_LIGHT

    def render_progressive(self, text: str, is_complete: bool = False) -> str:
        """
        渐进式渲染 - 打字过程和完成状态使用相同的渲染逻辑

        Args:
            text: 当前已输入的文本
            is_complete: 是否已完成输入

        Returns:
            HTML字符串
        """
        if not text:
            return ""

        # 基础样式
        text_color = self.colors["ai_text"]
        h1_color = "#A78BFA" if self.theme == "dark" else "#6D28D9"
        h2_color = "#818CF8" if self.theme == "dark" else "#7C3AED"
        h3_color = "#6366F1" if self.theme == "dark" else "#8B5CF6"
        code_bg = "#1E1E2E" if self.theme == "dark" else "#F1F5F9"
        code_color = "#E2E8F0" if self.theme == "dark" else "#334155"
        quote_border = "#6366F1"
        quote_color = self.colors["text_secondary"]

        lines = text.split('\n')
        html_parts = []
        in_code_block = False

        for i, line in enumerate(lines):
            is_last_line = (i == len(lines) - 1) and not is_complete

            # 处理代码块
            if line.strip().startswith('```'):
                if in_code_block:
                    html_parts.append('</pre>')
                    in_code_block = False
                else:
                    lang = line.strip()[3:]
                    html_parts.append(
                        f'<pre style="background: {code_bg}; color: {code_color}; '
                        f'padding: 12px; border-radius: 8px; margin: 8px 0; '
                        f'font-family: \'Consolas\', \'Monaco\', monospace; font-size: 13px; '
                        f'overflow-x: auto; white-space: pre-wrap;">'
                    )
                    in_code_block = True
                continue

            if in_code_block:
                html_parts.append(self._escape_html(line) + '\n')
                continue

            # 处理标题
            if line.startswith('### '):
                content = self._process_inline(line[4:])
                html_parts.append(
                    f'<p style="font-weight: 600; font-size: 15px; margin: 12px 0 6px 0; '
                    f'color: {h3_color};">{content}</p>'
                )
            elif line.startswith('## '):
                content = self._process_inline(line[3:])
                html_parts.append(
                    f'<p style="font-weight: 600; font-size: 16px; margin: 14px 0 8px 0; '
                    f'color: {h2_color};">{content}</p>'
                )
            elif line.startswith('# '):
                content = self._process_inline(line[2:])
                html_parts.append(
                    f'<p style="font-weight: 700; font-size: 18px; margin: 16px 0 10px 0; '
                    f'color: {h1_color};">{content}</p>'
                )
            # 处理列表
            elif line.strip().startswith('- ') or line.strip().startswith('* '):
                indent = len(line) - len(line.lstrip())
                content = self._process_inline(line.strip()[2:])
                margin_left = 16 + (indent // 2) * 12
                html_parts.append(
                    f'<p style="margin: 4px 0 4px {margin_left}px; line-height: 1.6;">• {content}</p>'
                )
            elif re.match(r'^\d+\.\s', line.strip()):
                match = re.match(r'^(\d+)\.\s(.*)$', line.strip())
                if match:
                    num, content = match.groups()
                    content = self._process_inline(content)
                    html_parts.append(
                        f'<p style="margin: 4px 0 4px 16px; line-height: 1.6;">{num}. {content}</p>'
                    )
            # 处理引用
            elif line.startswith('> '):
                content = self._process_inline(line[2:])
                html_parts.append(
                    f'<p style="border-left: 3px solid {quote_border}; padding-left: 12px; '
                    f'margin: 8px 0; color: {quote_color}; font-style: italic;">{content}</p>'
                )
            # 处理分割线
            elif line.strip() in ('---', '***', '___'):
                html_parts.append(
                    f'<hr style="border: none; border-top: 1px solid {self.colors["border"]}; margin: 12px 0;">'
                )
            # 普通段落
            elif line.strip():
                content = self._process_inline(line)
                # 最后一行且未完成时，添加光标
                if is_last_line:
                    content += '<span style="opacity: 0.6; animation: blink 1s infinite;">▋</span>'
                html_parts.append(
                    f'<p style="margin: 6px 0; line-height: 1.7;">{content}</p>'
                )
            else:
                # 空行
                html_parts.append('<p style="margin: 4px 0;"></p>')

        # 关闭未闭合的代码块
        if in_code_block:
            html_parts.append('</pre>')

        # 包装在容器中
        return f'''
        <style>
            @keyframes blink {{
                0%, 50% {{ opacity: 0.6; }}
                51%, 100% {{ opacity: 0; }}
            }}
        </style>
        <div style="font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
                    font-size: {DS.FONT_BASE}px; color: {text_color}; line-height: 1.6;">
            {''.join(html_parts)}
        </div>
        '''

    def _escape_html(self, text: str) -> str:
        """转义HTML特殊字符"""
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    def _process_inline(self, text: str) -> str:
        """处理行内格式"""
        text = self._escape_html(text)

        # 加粗
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)

        # 斜体
        text = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<em>\1</em>', text)
        text = re.sub(r'(?<!_)_([^_]+?)_(?!_)', r'<em>\1</em>', text)

        # 行内代码
        code_bg = "#1E1E2E" if self.theme == "dark" else "#F1F5F9"
        code_color = "#E2E8F0" if self.theme == "dark" else "#334155"
        text = re.sub(
            r'`([^`]+?)`',
            rf'<code style="background: {code_bg}; color: {code_color}; '
            rf'padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 13px;">\1</code>',
            text
        )

        return text


# ==================== 优化的打字机动画 ====================

class SmoothTypewriter:
    """
    平滑打字机动画 - 无跳变版本

    核心改进：
    1. 打字过程中实时渲染Markdown为HTML
    2. 使用与最终完全一致的样式
    3. 打字完成时无需重新渲染，因此无跳变
    """

    def __init__(
        self,
        text_browser: QTextBrowser,
        content: str,
        char_delay: int = 20,
        newline_delay: int = 260,
        chunk_size: int = 1,
        theme: str = "dark"
    ):
        self.text_browser = text_browser
        self.full_content = content
        self.char_delay = char_delay
        self.newline_delay = newline_delay
        self.chunk_size = chunk_size
        self.theme = theme

        self.renderer = ProgressiveMarkdownRenderer(theme)
        self.current_index = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self._type_next)
        self._is_running = False

    def start(self):
        """开始打字动画"""
        self._is_running = True
        self.current_index = 0
        self.text_browser.clear()
        self.timer.start(self.char_delay)

    def stop(self):
        """停止并显示完整内容"""
        self._is_running = False
        self.timer.stop()
        self._show_complete()

    def is_running(self) -> bool:
        return self._is_running

    def _type_next(self):
        """输入下一组字符"""
        if self.current_index >= len(self.full_content):
            self.timer.stop()
            self._is_running = False
            self._show_complete()
            return

        # 计算下一个位置
        next_index = min(self.current_index + self.chunk_size, len(self.full_content))

        # 检查换行
        chunk = self.full_content[self.current_index:next_index]
        newline_pos = chunk.find('\n')
        if newline_pos != -1:
            next_index = self.current_index + newline_pos + 1
            has_newline = True
        else:
            has_newline = False

        self.current_index = next_index

        # 渐进式渲染当前内容
        current_text = self.full_content[:self.current_index]
        html = self.renderer.render_progressive(current_text, is_complete=False)
        self.text_browser.setHtml(html)

        # 滚动到底部
        scrollbar = self.text_browser.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

        # 换行时增加延迟
        if has_newline:
            self.timer.setInterval(self.newline_delay)
        else:
            self.timer.setInterval(self.char_delay)

    def _show_complete(self):
        """显示完整内容（无跳变，因为使用相同的渲染器）"""
        html = self.renderer.render_progressive(self.full_content, is_complete=True)
        self.text_browser.setHtml(html)


# ==================== 自适应高度的TextBrowser ====================

class AutoHeightTextBrowser(QTextBrowser):
    """自动调整高度的TextBrowser"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setLineWrapMode(QTextBrowser.LineWrapMode.WidgetWidth)
        self.document().contentsChanged.connect(self._adjust_height)
        self._min_height = 40

    def _adjust_height(self):
        """调整高度"""
        if self.width() > 0:
            self.document().setTextWidth(self.width() - 20)
        self.document().adjustSize()
        doc_height = self.document().size().height()
        new_height = max(int(doc_height + 30), self._min_height)
        self.setMinimumHeight(new_height)
        self.setMaximumHeight(new_height)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(10, self._adjust_height)

    def wheelEvent(self, event):
        """让滚轮事件传递给父级"""
        event.ignore()


# ==================== 消息气泡 ====================

class MessageRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"


class ChatBubble(QFrame):
    """聊天气泡组件"""

    def __init__(self, role: MessageRole, content: str, animated: bool = False, theme: str = "dark", parent=None):
        super().__init__(parent)
        self.role = role
        self.content = content
        self.animated = animated
        self.theme = theme
        self.colors = DS.COLORS_DARK if theme == "dark" else DS.COLORS_LIGHT
        self.typewriter: Optional[SmoothTypewriter] = None
        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(DS.SPACING_MD, DS.SPACING_SM, DS.SPACING_MD, DS.SPACING_SM)
        main_layout.setSpacing(0)

        if self.role == MessageRole.USER:
            self._setup_user_bubble(main_layout)
        else:
            self._setup_ai_bubble(main_layout)

        self.setLayout(main_layout)
        self.setStyleSheet("background: transparent;")

    def _setup_user_bubble(self, main_layout: QHBoxLayout):
        """用户气泡 - 右侧紫色"""
        main_layout.addStretch()

        bubble = QFrame()
        bubble.setObjectName("userBubble")
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(DS.SPACING_MD, DS.SPACING_SM + 4, DS.SPACING_MD, DS.SPACING_SM + 4)

        # 内容
        content_label = QLabel(self.content)
        content_label.setWordWrap(True)
        content_label.setFont(QFont("Microsoft YaHei", DS.FONT_BASE))
        content_label.setStyleSheet(f"color: {self.colors['user_text']}; background: transparent;")
        bubble_layout.addWidget(content_label)

        # 气泡样式
        bubble.setStyleSheet(f"""
            QFrame#userBubble {{
                background-color: {self.colors['user_bubble']};
                border-radius: {DS.RADIUS_LG}px;
                border-top-right-radius: {DS.RADIUS_SM}px;
            }}
        """)
        bubble.setMaximumWidth(500)
        bubble.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)

        main_layout.addWidget(bubble)

    def _setup_ai_bubble(self, main_layout: QHBoxLayout):
        """AI气泡 - 左侧带头像"""
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(6)

        # 头部：Logo + 名称
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Logo（使用emoji代替，避免背景色差问题）
        logo_label = QLabel("🔮")
        logo_label.setFont(QFont("Segoe UI Emoji", 16))
        logo_label.setFixedSize(28, 28)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setStyleSheet("background: transparent;")
        header_layout.addWidget(logo_label)

        # 名称
        name_label = QLabel("赛博玄数")
        name_label.setFont(QFont("Microsoft YaHei", DS.FONT_XS))
        name_label.setStyleSheet(f"color: {self.colors['text_secondary']}; background: transparent;")
        header_layout.addWidget(name_label)
        header_layout.addStretch()

        container_layout.addWidget(header)

        # 气泡
        bubble = QFrame()
        bubble.setObjectName("aiBubble")
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(DS.SPACING_MD, DS.SPACING_SM + 4, DS.SPACING_MD, DS.SPACING_SM + 4)
        bubble_layout.setSpacing(0)

        # 内容 - 使用TextBrowser支持富文本
        self.content_browser = AutoHeightTextBrowser()
        self.content_browser.setReadOnly(True)
        self.content_browser.setFrameStyle(QFrame.Shape.NoFrame)
        self.content_browser.setStyleSheet(f"""
            QTextBrowser {{
                background: transparent;
                border: none;
                color: {self.colors['ai_text']};
            }}
        """)
        self.content_browser.document().setDocumentMargin(0)

        # 显示内容
        if self.animated and self.content:
            self.typewriter = SmoothTypewriter(
                self.content_browser,
                self.content,
                char_delay=20,
                newline_delay=260,
                chunk_size=1,
                theme=self.theme
            )
            self.typewriter.start()
        else:
            renderer = ProgressiveMarkdownRenderer(self.theme)
            html = renderer.render_progressive(self.content, is_complete=True)
            self.content_browser.setHtml(html)

        bubble_layout.addWidget(self.content_browser)

        # 气泡样式
        bubble.setStyleSheet(f"""
            QFrame#aiBubble {{
                background-color: {self.colors['ai_bubble']};
                border: 1px solid {self.colors['ai_border']};
                border-radius: {DS.RADIUS_LG}px;
                border-top-left-radius: {DS.RADIUS_SM}px;
            }}
        """)
        bubble.setMaximumWidth(650)
        bubble.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        container_layout.addWidget(bubble)
        main_layout.addWidget(container)
        main_layout.addStretch()

    def stop_animation(self):
        if self.typewriter and self.typewriter.is_running():
            self.typewriter.stop()


# ==================== 聊天区域 ====================

class ChatWidget(QWidget):
    """聊天消息区域"""

    def __init__(self, theme: str = "dark", parent=None):
        super().__init__(parent)
        self.theme = theme
        self.messages: List[ChatBubble] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setFrameStyle(QFrame.Shape.NoFrame)

        # 消息容器
        self.container = QWidget()
        self.container_layout = QVBoxLayout()
        self.container_layout.setContentsMargins(DS.SPACING_MD, DS.SPACING_SM, DS.SPACING_MD, DS.SPACING_SM)
        self.container_layout.setSpacing(DS.SPACING_SM)
        self.container_layout.addStretch()
        self.container.setLayout(self.container_layout)

        self.scroll_area.setWidget(self.container)
        layout.addWidget(self.scroll_area)
        self.setLayout(layout)

    def add_user_message(self, content: str):
        bubble = ChatBubble(MessageRole.USER, content, animated=False, theme=self.theme)
        self._add_bubble(bubble)

    def add_ai_message(self, content: str, animated: bool = True):
        bubble = ChatBubble(MessageRole.ASSISTANT, content, animated=animated, theme=self.theme)
        self._add_bubble(bubble)

    def _add_bubble(self, bubble: ChatBubble):
        self.messages.append(bubble)
        count = self.container_layout.count()
        self.container_layout.insertWidget(count - 1, bubble)
        QTimer.singleShot(50, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def clear(self):
        self.messages.clear()
        while self.container_layout.count() > 1:
            item = self.container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


# ==================== 简洁侧边栏（无收缩功能） ====================

class SimpleSidebar(QFrame):
    """简洁侧边栏 - 固定宽度，无收缩"""

    nav_changed = pyqtSignal(str)

    NAV_ITEMS = [
        {"id": "wendao", "name": "问道", "icon": "💬"},
        {"id": "tuiyan", "name": "推演", "icon": "📊"},
        {"id": "dianji", "name": "典籍", "icon": "📚"},
        {"id": "dongcha", "name": "洞察", "icon": "👁"},
        {"id": "lishi", "name": "历史", "icon": "📜"},
        {"id": "shezhi", "name": "设置", "icon": "⚙️"},
    ]

    def __init__(self, theme: str = "dark", parent=None):
        super().__init__(parent)
        self.theme = theme
        self.colors = DS.COLORS_DARK if theme == "dark" else DS.COLORS_LIGHT
        self.current_nav = "wendao"
        self.nav_buttons = {}
        self._setup_ui()

    def _setup_ui(self):
        self.setFixedWidth(200)
        self.setStyleSheet(f"""
            SimpleSidebar {{
                background-color: {self.colors['bg_primary']};
                border-right: 1px solid {self.colors['border']};
            }}
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo区域
        logo_widget = self._create_logo_section()
        layout.addWidget(logo_widget)

        # 分隔线
        layout.addWidget(self._create_separator())

        # 导航项
        nav_widget = QWidget()
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(DS.SPACING_SM, DS.SPACING_MD, DS.SPACING_SM, DS.SPACING_MD)
        nav_layout.setSpacing(DS.SPACING_XS)

        for item in self.NAV_ITEMS:
            btn = self._create_nav_button(item)
            nav_layout.addWidget(btn)
            self.nav_buttons[item["id"]] = btn

        layout.addWidget(nav_widget)
        layout.addStretch()

        # 底部分隔线和关于
        layout.addWidget(self._create_separator())

        about_widget = QWidget()
        about_layout = QVBoxLayout(about_widget)
        about_layout.setContentsMargins(DS.SPACING_SM, DS.SPACING_MD, DS.SPACING_SM, DS.SPACING_MD)
        about_btn = self._create_nav_button({"id": "about", "name": "关于", "icon": "ℹ️"})
        about_layout.addWidget(about_btn)
        self.nav_buttons["about"] = about_btn
        layout.addWidget(about_widget)

        self.setLayout(layout)

        # 默认选中
        self._update_selection("wendao")

    def _create_logo_section(self) -> QWidget:
        """创建Logo区域 - 修复背景色差"""
        widget = QWidget()
        widget.setFixedHeight(90)
        widget.setStyleSheet("background: transparent;")

        layout = QHBoxLayout(widget)
        layout.setContentsMargins(DS.SPACING_MD, DS.SPACING_LG, DS.SPACING_MD, DS.SPACING_MD)
        layout.setSpacing(DS.SPACING_SM)

        # Logo（使用emoji，完全透明背景）
        logo_label = QLabel("🔮")
        logo_label.setFont(QFont("Segoe UI Emoji", 28))
        logo_label.setFixedSize(48, 48)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setStyleSheet("background: transparent;")
        layout.addWidget(logo_label)

        # 名称区域
        name_widget = QWidget()
        name_widget.setStyleSheet("background: transparent;")
        name_layout = QVBoxLayout(name_widget)
        name_layout.setContentsMargins(0, 0, 0, 0)
        name_layout.setSpacing(2)

        cn_name = QLabel("赛博玄数")
        cn_font = QFont("Microsoft YaHei", DS.FONT_LG)
        cn_font.setBold(True)
        cn_name.setFont(cn_font)
        cn_name.setStyleSheet(f"color: {self.colors['text_primary']}; background: transparent;")
        name_layout.addWidget(cn_name)

        en_name = QLabel("Cyber Mantic")
        en_name.setFont(QFont("Microsoft YaHei", DS.FONT_XS))
        en_name.setStyleSheet(f"color: {self.colors['text_secondary']}; background: transparent;")
        name_layout.addWidget(en_name)

        layout.addWidget(name_widget)
        layout.addStretch()

        return widget

    def _create_separator(self) -> QFrame:
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {self.colors['border']};")
        return sep

    def _create_nav_button(self, item: dict) -> QPushButton:
        btn = QPushButton(f"  {item['icon']}  {item['name']}")
        btn.setFixedHeight(44)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFont(QFont("Microsoft YaHei", DS.FONT_BASE))
        btn.setProperty("nav_id", item["id"])
        btn.clicked.connect(lambda: self._on_nav_clicked(item["id"]))
        self._style_nav_button(btn, False)
        return btn

    def _style_nav_button(self, btn: QPushButton, selected: bool):
        if selected:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba(99, 102, 241, 0.2);
                    color: {self.colors['primary_light']};
                    border: none;
                    border-left: 3px solid {self.colors['primary']};
                    border-radius: 0;
                    text-align: left;
                    padding-left: 12px;
                    font-weight: 500;
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {self.colors['text_secondary']};
                    border: none;
                    border-left: 3px solid transparent;
                    border-radius: 0;
                    text-align: left;
                    padding-left: 12px;
                }}
                QPushButton:hover {{
                    background-color: rgba(99, 102, 241, 0.1);
                    color: {self.colors['text_primary']};
                }}
            """)

    def _on_nav_clicked(self, nav_id: str):
        if nav_id != self.current_nav:
            self._update_selection(nav_id)
            self.nav_changed.emit(nav_id)

    def _update_selection(self, nav_id: str):
        # 取消旧选中
        if self.current_nav in self.nav_buttons:
            self._style_nav_button(self.nav_buttons[self.current_nav], False)
        # 选中新项
        self.current_nav = nav_id
        if nav_id in self.nav_buttons:
            self._style_nav_button(self.nav_buttons[nav_id], True)


# ==================== 右侧信息面板 ====================

class InfoPanel(QFrame):
    """右侧信息面板"""

    def __init__(self, theme: str = "dark", parent=None):
        super().__init__(parent)
        self.theme = theme
        self.colors = DS.COLORS_DARK if theme == "dark" else DS.COLORS_LIGHT
        self._setup_ui()

    def _setup_ui(self):
        self.setMinimumWidth(280)
        self.setMaximumWidth(350)

        layout = QVBoxLayout()
        layout.setContentsMargins(DS.SPACING_MD, DS.SPACING_MD, DS.SPACING_MD, DS.SPACING_MD)
        layout.setSpacing(DS.SPACING_MD)

        # 进度卡片
        progress_card = self._create_card("📊 分析进度", "等待开始...")
        layout.addWidget(progress_card)

        # 理论状态
        theories_card = self._create_theories_card()
        layout.addWidget(theories_card)

        # 当前阶段
        stage_card = self._create_card("📍 当前阶段", "💬 等待输入问题")
        layout.addWidget(stage_card)

        layout.addStretch()
        self.setLayout(layout)

    def _create_card(self, title: str, content: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {self.colors['surface']};
                border: 1px solid {self.colors['border']};
                border-radius: {DS.RADIUS_MD}px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(DS.SPACING_MD, DS.SPACING_SM, DS.SPACING_MD, DS.SPACING_SM)
        layout.setSpacing(DS.SPACING_SM)

        title_label = QLabel(title)
        title_font = QFont("Microsoft YaHei", DS.FONT_SM)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {self.colors['text_primary']}; background: transparent;")
        layout.addWidget(title_label)

        content_label = QLabel(content)
        content_label.setFont(QFont("Microsoft YaHei", DS.FONT_SM))
        content_label.setWordWrap(True)
        content_label.setStyleSheet(f"color: {self.colors['text_secondary']}; background: transparent;")
        layout.addWidget(content_label)

        return card

    def _create_theories_card(self) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {self.colors['surface']};
                border: 1px solid {self.colors['border']};
                border-radius: {DS.RADIUS_MD}px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(DS.SPACING_MD, DS.SPACING_SM, DS.SPACING_MD, DS.SPACING_SM)
        layout.setSpacing(DS.SPACING_XS)

        title = QLabel("🔮 理论分析")
        title_font = QFont("Microsoft YaHei", DS.FONT_SM)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet(f"color: {self.colors['text_primary']}; background: transparent;")
        layout.addWidget(title)

        theories = ["小六壬", "测字术", "八字", "紫微斗数", "奇门遁甲", "大六壬"]
        for t in theories:
            item = QLabel(f"  ⬚  {t}")
            item.setFont(QFont("Microsoft YaHei", DS.FONT_SM))
            item.setStyleSheet(f"color: {self.colors['text_muted']}; background: transparent;")
            layout.addWidget(item)

        return card


# ==================== 主窗口 ====================

class DemoMainWindow(QMainWindow):
    """Demo主窗口"""

    def __init__(self):
        super().__init__()
        self.theme = "dark"
        self.colors = DS.COLORS_DARK
        self._setup_ui()
        self._apply_theme()

    def _setup_ui(self):
        self.setWindowTitle("赛博玄数 - UI美观Demo")
        self.setMinimumSize(1200, 800)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 左侧导航栏
        self.sidebar = SimpleSidebar(self.theme)
        main_layout.addWidget(self.sidebar)

        # 中间内容区（聊天）
        content_widget = self._create_content_area()
        main_layout.addWidget(content_widget, 1)

        # 右侧信息面板
        self.info_panel = InfoPanel(self.theme)
        main_layout.addWidget(self.info_panel)

    def _create_content_area(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 顶部工具栏
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # 聊天区域
        self.chat_widget = ChatWidget(self.theme)
        layout.addWidget(self.chat_widget, 1)

        # 输入区域
        input_area = self._create_input_area()
        layout.addWidget(input_area)

        return widget

    def _create_toolbar(self) -> QFrame:
        toolbar = QFrame()
        toolbar.setFixedHeight(56)
        toolbar.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(99, 102, 241, 0.08);
                border-bottom: 1px solid rgba(99, 102, 241, 0.15);
            }}
        """)

        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(DS.SPACING_MD, DS.SPACING_SM, DS.SPACING_MD, DS.SPACING_SM)
        layout.setSpacing(DS.SPACING_SM)

        # 新对话按钮
        new_btn = QPushButton("✨ 新对话")
        new_btn.setFixedHeight(38)
        new_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        new_btn.clicked.connect(self._on_new_conversation)
        new_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #8B5CF6, stop:1 #6366F1);
                color: white;
                border: none;
                border-radius: {DS.RADIUS_SM}px;
                padding: 0 {DS.SPACING_MD}px;
                font-size: {DS.FONT_SM}px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #A78BFA, stop:1 #818CF8);
            }}
        """)
        layout.addWidget(new_btn)

        # Demo按钮
        demo_btn = QPushButton("🎬 演示打字机效果")
        demo_btn.setFixedHeight(38)
        demo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        demo_btn.clicked.connect(self._demo_typewriter)
        demo_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(16, 185, 129, 0.15);
                color: #10B981;
                border: 1px solid rgba(16, 185, 129, 0.3);
                border-radius: {DS.RADIUS_SM}px;
                padding: 0 {DS.SPACING_MD}px;
                font-size: {DS.FONT_SM}px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: rgba(16, 185, 129, 0.25);
            }}
        """)
        layout.addWidget(demo_btn)

        layout.addStretch()

        return toolbar

    def _create_input_area(self) -> QFrame:
        container = QFrame()
        container.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(container)
        layout.setContentsMargins(DS.SPACING_MD, DS.SPACING_SM, DS.SPACING_MD, DS.SPACING_MD)
        layout.setSpacing(DS.SPACING_SM)

        row = QHBoxLayout()
        row.setSpacing(DS.SPACING_SM)

        # 输入框
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("输入您想咨询的问题... (Enter发送，Shift+Enter换行)")
        self.input_text.setFixedHeight(60)
        self.input_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.colors['surface']};
                border: 1px solid {self.colors['border']};
                border-radius: {DS.RADIUS_MD}px;
                padding: {DS.SPACING_SM}px {DS.SPACING_MD}px;
                color: {self.colors['text_primary']};
                font-size: {DS.FONT_BASE}px;
            }}
            QTextEdit:focus {{
                border-color: {self.colors['primary']};
            }}
        """)
        row.addWidget(self.input_text)

        # 发送按钮
        send_btn = QPushButton("发送")
        send_btn.setFixedSize(80, 60)
        send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        send_btn.clicked.connect(self._on_send)
        send_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #6366F1, stop:1 #4F46E5);
                color: white;
                border: none;
                border-radius: {DS.RADIUS_MD}px;
                font-size: {DS.FONT_BASE}px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #818CF8, stop:1 #6366F1);
            }}
        """)
        row.addWidget(send_btn)

        layout.addLayout(row)
        return container

    def _apply_theme(self):
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {self.colors['bg_secondary']};
            }}
        """)

    def _on_new_conversation(self):
        self.chat_widget.clear()
        # 添加欢迎消息
        welcome = """## 👋 欢迎使用赛博玄数

我是您的智能问道助手，可以帮您分析人生中的困惑与选择。

### 🎯 我能帮您做什么？
- **事业发展** - 职业规划、跳槽时机、创业方向
- **感情婚姻** - 姻缘分析、感情走向、桃花运势
- **财富运势** - 投资建议、财运分析、理财方向
- **健康养生** - 体质分析、养生建议、注意事项

### 📝 开始方式
请先告诉我：**您想咨询什么问题？**

> 例如：最近在考虑要不要跳槽，想了解一下我的事业发展方向。"""
        self.chat_widget.add_ai_message(welcome, animated=True)

    def _demo_typewriter(self):
        """演示打字机效果"""
        demo_text = """## 🔮 八字分析结果

根据您提供的出生信息，我为您进行了详细的八字分析：

### 命盘格局
您的八字为：**甲子年 丙寅月 戊辰日 壬戌时**

日主戊土，生于寅月木旺之时，地支子辰半合水局，形成**财官印三奇格**。

### 性格特点
- 为人忠厚老实，做事踏实稳重
- 具有较强的领导能力和组织才能
- 注重实际，善于理财和投资

### 事业运势
目前正值**偏财运旺盛**的时期：
1. 2024年有贵人相助，适合拓展人脉
2. 2025年财运亨通，可考虑投资理财
3. 2026年事业上升期，把握晋升机会

> 💡 建议：当前是事业发展的黄金期，建议稳中求进，不宜冒进。

---
*以上分析仅供参考，具体情况需结合实际。*"""

        self.chat_widget.add_user_message("帮我分析一下我的八字运势")
        # 延迟添加AI回复，模拟思考过程
        QTimer.singleShot(500, lambda: self.chat_widget.add_ai_message(demo_text, animated=True))

    def _on_send(self):
        text = self.input_text.toPlainText().strip()
        if text:
            self.chat_widget.add_user_message(text)
            self.input_text.clear()

            # 模拟回复
            response = f"感谢您的问题！您问的是：**{text}**\n\n让我为您分析一下..."
            QTimer.singleShot(300, lambda: self.chat_widget.add_ai_message(response, animated=True))


# ==================== 程序入口 ====================

def main():
    app = QApplication(sys.argv)

    # 设置全局字体
    font = QFont("Microsoft YaHei", DS.FONT_BASE)
    app.setFont(font)

    window = DemoMainWindow()
    window.show()

    # 自动演示
    QTimer.singleShot(500, window._on_new_conversation)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
