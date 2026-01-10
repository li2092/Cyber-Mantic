"""
ChatWidget V2 - 重构版聊天组件

核心改进：
1. 渐进式Markdown渲染（无跳变）
2. 气泡宽度自适应
3. 完整的双主题支持
4. 使用新设计系统
"""

import re
from typing import Optional, List
from enum import Enum

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QSizePolicy, QTextBrowser
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap

import os
from pathlib import Path

from ..design_system_v2 import (
    spacing, font_size, border_radius, get_colors, StyleGenerator
)


# ==================== 渐进式Markdown渲染器 ====================

class ProgressiveMarkdownRenderer:
    """
    渐进式Markdown渲染器 - 无跳变

    核心优化：打字过程中实时渲染Markdown为HTML，
    使用与最终完全一致的样式，避免渲染跳变。
    """

    def __init__(self, theme: str = "light"):
        self.theme = theme
        self.colors = get_colors(theme)

    def set_theme(self, theme: str):
        self.theme = theme
        self.colors = get_colors(theme)

    def render(self, text: str, is_complete: bool = False) -> str:
        """
        渲染Markdown为HTML

        Args:
            text: Markdown文本
            is_complete: 是否已完成输入

        Returns:
            HTML字符串
        """
        if not text:
            return ""

        # 颜色配置
        text_color = self.colors["ai_text"]
        h1_color = "#7C3AED" if self.theme == "light" else "#A78BFA"
        h2_color = "#8B5CF6" if self.theme == "light" else "#818CF8"
        h3_color = "#6366F1"
        code_bg = "#F1F5F9" if self.theme == "light" else "#1A1A28"
        code_color = "#334155" if self.theme == "light" else "#E2E8F0"
        quote_border = "#6366F1"
        quote_color = self.colors["text_secondary"]

        lines = text.split('\n')
        html_parts = []
        in_code_block = False

        for i, line in enumerate(lines):
            is_last_line = (i == len(lines) - 1) and not is_complete

            # 代码块
            if line.strip().startswith('```'):
                if in_code_block:
                    html_parts.append('</pre>')
                    in_code_block = False
                else:
                    html_parts.append(
                        f'<pre style="background: {code_bg}; color: {code_color}; '
                        f'padding: 12px; border-radius: 8px; margin: 8px 0; '
                        f'font-family: Consolas, Monaco, monospace; font-size: 13px; '
                        f'white-space: pre-wrap; word-wrap: break-word;">'
                    )
                    in_code_block = True
                continue

            if in_code_block:
                html_parts.append(self._escape_html(line) + '\n')
                continue

            # 标题
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
            # 列表
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
            # 引用
            elif line.startswith('> '):
                content = self._process_inline(line[2:])
                html_parts.append(
                    f'<p style="border-left: 3px solid {quote_border}; padding-left: 12px; '
                    f'margin: 8px 0; color: {quote_color}; font-style: italic;">{content}</p>'
                )
            # 分隔线
            elif line.strip() in ('---', '***', '___'):
                html_parts.append(
                    f'<hr style="border: none; border-top: 1px solid {self.colors["border"]}; margin: 12px 0;">'
                )
            # 普通段落
            elif line.strip():
                content = self._process_inline(line)
                if is_last_line:
                    content += '<span class="cursor">▋</span>'
                html_parts.append(
                    f'<p style="margin: 6px 0; line-height: 1.7;">{content}</p>'
                )
            else:
                html_parts.append('<p style="margin: 4px 0;"></p>')

        if in_code_block:
            html_parts.append('</pre>')

        # 闪烁光标动画
        cursor_style = """
        <style>
            .cursor {
                opacity: 0.6;
                animation: blink 1s infinite;
            }
            @keyframes blink {
                0%, 50% { opacity: 0.6; }
                51%, 100% { opacity: 0; }
            }
        </style>
        """ if not is_complete else ""

        return f'''
        {cursor_style}
        <div style="font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
                    font-size: {font_size.base}px; color: {text_color}; line-height: 1.6;">
            {''.join(html_parts)}
        </div>
        '''

    def _escape_html(self, text: str) -> str:
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
        code_bg = "#F1F5F9" if self.theme == "light" else "#1A1A28"
        code_color = "#334155" if self.theme == "light" else "#E2E8F0"
        text = re.sub(
            r'`([^`]+?)`',
            rf'<code style="background: {code_bg}; color: {code_color}; '
            rf'padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 13px;">\1</code>',
            text
        )

        return text


# ==================== 平滑打字机动画 ====================

class SmoothTypewriter:
    """
    平滑打字机动画 - 无跳变版本

    核心改进：打字过程中实时渲染Markdown为HTML，
    打字完成时无需重新渲染，因此无跳变。
    """

    def __init__(
        self,
        text_browser: QTextBrowser,
        content: str,
        char_delay: int = 20,
        newline_delay: int = 260,
        chunk_size: int = 1,
        theme: str = "light",
        scroll_callback=None
    ):
        self.text_browser = text_browser
        self.full_content = content
        self.char_delay = char_delay
        self.newline_delay = newline_delay
        self.chunk_size = chunk_size
        self.theme = theme
        self.scroll_callback = scroll_callback  # 滚动回调函数

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
        html = self.renderer.render(current_text, is_complete=False)
        self.text_browser.setHtml(html)

        # 触发父级滚动回调
        if self.scroll_callback:
            self.scroll_callback()

        # 换行时增加延迟
        if has_newline:
            self.timer.setInterval(self.newline_delay)
        else:
            self.timer.setInterval(self.char_delay)

    def _show_complete(self):
        """显示完整内容"""
        html = self.renderer.render(self.full_content, is_complete=True)
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
        if self.width() > 0:
            # 增加右侧裕量，防止文字被遮挡
            self.document().setTextWidth(self.width() - 40)
        self.document().adjustSize()
        doc_height = self.document().size().height()
        new_height = max(int(doc_height + 35), self._min_height)
        self.setMinimumHeight(new_height)
        self.setMaximumHeight(new_height)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(10, self._adjust_height)

    def wheelEvent(self, event):
        """让滚轮事件传递给父级"""
        event.ignore()


# ==================== 消息角色枚举 ====================

class MessageRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"


# ==================== 聊天气泡组件 ====================

class ChatBubble(QFrame):
    """聊天气泡组件 - 宽度自适应"""

    def __init__(
        self,
        role: MessageRole,
        content: str,
        animated: bool = False,
        theme: str = "light",
        scroll_callback=None,
        parent=None
    ):
        super().__init__(parent)
        self.role = role
        self.content = content
        self.animated = animated
        self.theme = theme
        self.colors = get_colors(theme)
        self.typewriter: Optional[SmoothTypewriter] = None
        self.scroll_callback = scroll_callback  # 滚动回调

        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        main_layout = QHBoxLayout()
        # 左边距小，右边距大，防止文字被遮挡
        main_layout.setContentsMargins(8, spacing.sm, 24, spacing.sm)
        main_layout.setSpacing(0)

        if self.role == MessageRole.USER:
            self._setup_user_bubble(main_layout)
        else:
            self._setup_ai_bubble(main_layout)

        self.setLayout(main_layout)
        self.setStyleSheet("background: transparent;")

    def _setup_user_bubble(self, main_layout: QHBoxLayout):
        """用户气泡 - 右侧紫色，宽度自适应，文字贴右"""
        main_layout.addStretch(1)  # 左侧弹性空间

        bubble = QFrame()
        bubble.setObjectName("userBubble")
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(spacing.md, spacing.sm + 4, spacing.md, spacing.sm + 4)

        # 内容标签 - 统一字体大小
        content_label = QLabel(self.content)
        content_label.setWordWrap(True)
        content_label.setFont(QFont("Microsoft YaHei", font_size.base))
        content_label.setStyleSheet(f"color: {self.colors['user_text']}; background: transparent;")
        content_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        content_label.setMaximumWidth(500)  # 最大宽度限制
        bubble_layout.addWidget(content_label)

        # 气泡样式
        bubble.setStyleSheet(f"""
            QFrame#userBubble {{
                background-color: {self.colors['user_bubble']};
                border-radius: {border_radius.lg}px;
                border-top-right-radius: {border_radius.sm}px;
            }}
        """)
        bubble.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)

        main_layout.addWidget(bubble)
        main_layout.addSpacing(spacing.sm)  # 右侧小间距

    def _setup_ai_bubble(self, main_layout: QHBoxLayout):
        """AI气泡 - 左侧，带logo头像，文字正确换行"""
        # 减少左侧间距
        main_layout.addSpacing(4)

        # 头像区域
        avatar_container = QWidget()
        avatar_container.setFixedWidth(40)
        avatar_layout = QVBoxLayout(avatar_container)
        avatar_layout.setContentsMargins(0, 0, 0, 0)
        avatar_layout.setSpacing(0)
        avatar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Logo头像 - 增大尺寸提升清晰度
        logo_label = QLabel()
        logo_label.setFixedSize(36, 36)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setStyleSheet("""
            background: #FFFFFF;
            border-radius: 18px;
            border: 1px solid #E5E7EB;
        """)

        # 尝试加载真实logo - 使用更大的缩放尺寸提升清晰度
        logo_path = self._get_logo_path()
        if logo_path and os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            # 使用更大的尺寸和高质量缩放
            scaled = pixmap.scaled(
                32, 32,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            logo_label.setPixmap(scaled)
        else:
            logo_label.setText("🔮")
            logo_label.setFont(QFont("Segoe UI Emoji", 16))

        avatar_layout.addWidget(logo_label)
        avatar_layout.addStretch()
        main_layout.addWidget(avatar_container)

        # 气泡容器
        bubble_container = QWidget()
        bubble_container_layout = QVBoxLayout(bubble_container)
        bubble_container_layout.setContentsMargins(6, 0, 0, 0)  # 减少左边距
        bubble_container_layout.setSpacing(4)

        # 名称标签
        name_label = QLabel("赛博玄数")
        name_label.setFont(QFont("Microsoft YaHei", font_size.xs))
        name_label.setStyleSheet(f"color: {self.colors['text_secondary']}; background: transparent;")
        bubble_container_layout.addWidget(name_label)

        # 气泡
        bubble = QFrame()
        bubble.setObjectName("aiBubble")
        bubble_layout = QVBoxLayout(bubble)
        # 增加右侧内边距，防止文字被遮挡
        bubble_layout.setContentsMargins(14, 10, 28, 10)
        bubble_layout.setSpacing(0)

        # 内容 - 使用TextBrowser支持富文本和自动换行
        self.content_browser = AutoHeightTextBrowser()
        self.content_browser.setReadOnly(True)
        self.content_browser.setFrameStyle(QFrame.Shape.NoFrame)
        self.content_browser.setOpenExternalLinks(True)
        self.content_browser.setStyleSheet(f"""
            QTextBrowser {{
                background: transparent;
                border: none;
                color: {self.colors['ai_text']};
                font-size: {font_size.base}px;
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
                theme=self.theme,
                scroll_callback=self.scroll_callback
            )
            self.typewriter.start()
        else:
            renderer = ProgressiveMarkdownRenderer(self.theme)
            html = renderer.render(self.content, is_complete=True)
            self.content_browser.setHtml(html)

        bubble_layout.addWidget(self.content_browser)

        # 气泡样式
        bubble.setStyleSheet(f"""
            QFrame#aiBubble {{
                background-color: {self.colors['ai_bubble']};
                border: 1px solid {self.colors['ai_border']};
                border-radius: {border_radius.lg}px;
                border-top-left-radius: {border_radius.sm}px;
            }}
        """)
        bubble.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        # 不设置最大宽度，让气泡自适应容器宽度

        bubble_container_layout.addWidget(bubble)
        main_layout.addWidget(bubble_container, 1)
        # 右侧留空间，防止文字被遮挡
        main_layout.addSpacing(20)

    def _get_logo_path(self) -> str:
        """获取Logo路径"""
        possible_paths = [
            Path(__file__).parent.parent / "resources" / "app_icon.png",
            Path(__file__).parent.parent.parent / "ui" / "resources" / "app_icon.png",
        ]
        for path in possible_paths:
            if path.exists():
                return str(path)
        return ""

    def stop_animation(self):
        """停止打字机动画"""
        if self.typewriter and self.typewriter.is_running():
            self.typewriter.stop()

    def set_theme(self, theme: str):
        """更新主题"""
        self.theme = theme
        self.colors = get_colors(theme)
        # 重新应用样式需要重建UI，这里简化处理


# ==================== 聊天消息区域组件 ====================

class ChatWidgetV2(QWidget):
    """聊天消息区域组件"""

    # 信号
    message_added = pyqtSignal(str, str)  # role, content

    def __init__(self, theme: str = "light", parent=None):
        super().__init__(parent)
        self.theme = theme
        self.colors = get_colors(theme)
        self.messages: List[ChatBubble] = []
        self._current_font_size = font_size.base

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
        self._apply_scroll_style()

        # 消息容器
        self.container = QWidget()
        self._apply_container_style()
        self.container_layout = QVBoxLayout()
        self.container_layout.setContentsMargins(spacing.md, spacing.sm, spacing.md, spacing.sm)
        self.container_layout.setSpacing(spacing.sm)
        self.container_layout.addStretch()
        self.container.setLayout(self.container_layout)

        self.scroll_area.setWidget(self.container)
        layout.addWidget(self.scroll_area)
        self.setLayout(layout)

    def _apply_scroll_style(self):
        self.scroll_area.setStyleSheet(f"background-color: {self.colors['chat_bg']};")

    def _apply_container_style(self):
        self.container.setStyleSheet(f"background-color: {self.colors['chat_bg']};")

    def set_theme(self, theme: str):
        """设置主题"""
        self.theme = theme
        self.colors = get_colors(theme)
        self._apply_scroll_style()
        self._apply_container_style()

    def add_user_message(self, content: str):
        """添加用户消息"""
        bubble = ChatBubble(MessageRole.USER, content, animated=False, theme=self.theme)
        self._add_bubble(bubble)
        self.message_added.emit("user", content)

    def add_assistant_message(self, content: str, animated: bool = True):
        """添加AI消息"""
        bubble = ChatBubble(
            MessageRole.ASSISTANT,
            content,
            animated=animated,
            theme=self.theme,
            scroll_callback=self._scroll_to_bottom  # 传递滚动回调
        )
        self._add_bubble(bubble)
        self.message_added.emit("assistant", content)

    def _add_bubble(self, bubble: ChatBubble):
        """添加气泡到布局"""
        self.messages.append(bubble)
        count = self.container_layout.count()
        self.container_layout.insertWidget(count - 1, bubble)
        QTimer.singleShot(50, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        """滚动到底部"""
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def clear_messages(self):
        """清空所有消息"""
        for bubble in self.messages:
            bubble.stop_animation()
        self.messages.clear()
        while self.container_layout.count() > 1:
            item = self.container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def get_messages(self) -> List[dict]:
        """获取所有消息"""
        return [
            {"role": m.role.value, "content": m.content}
            for m in self.messages
        ]

    def set_font_size(self, size: int):
        """设置字体大小"""
        self._current_font_size = size
        # 需要重新渲染所有消息，这里简化处理

    def update_theme(self, theme: str):
        """更新主题（兼容旧接口）"""
        self.set_theme(theme)
