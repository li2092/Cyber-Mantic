"""
赛博玄数 UI 美观Demo V2 - PyQt6

修改内容：
1. 气泡宽度自适应（百分比）
2. 使用真实Logo图片（透明背景）
3. 完整的白色/深色主题，默认白色主题
4. 修复聊天框背景色
5. 全新设计的设置界面（AI接口配置）
6. 英文字体优化

运行: python -m cyber_mantic.ui_demo_v2
"""

import sys
import os
import re
from datetime import datetime
from typing import Optional, List, Dict
from enum import Enum
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QTextBrowser, QPushButton, QLabel, QFrame,
    QScrollArea, QSplitter, QSizePolicy, QGroupBox, QStackedWidget,
    QLineEdit, QComboBox, QSpinBox, QCheckBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QDialog, QFormLayout, QMessageBox,
    QAbstractItemView
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QPixmap, QColor, QPainter, QBrush, QPen, QIcon, QFontDatabase


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

    # 颜色 - 浅色主题（默认）
    COLORS_LIGHT = {
        "bg_primary": "#FFFFFF",
        "bg_secondary": "#F8FAFC",
        "bg_tertiary": "#F1F5F9",
        "surface": "#FFFFFF",
        "surface_hover": "#F8FAFC",
        "border": "#E2E8F0",
        "border_light": "#F1F5F9",
        "text_primary": "#1E293B",
        "text_secondary": "#64748B",
        "text_muted": "#94A3B8",
        "primary": "#6366F1",
        "primary_light": "#818CF8",
        "primary_bg": "rgba(99, 102, 241, 0.08)",
        "success": "#10B981",
        "success_bg": "rgba(16, 185, 129, 0.1)",
        "warning": "#F59E0B",
        "error": "#EF4444",
        "error_bg": "rgba(239, 68, 68, 0.1)",
        # 气泡颜色
        "user_bubble": "#6366F1",
        "user_text": "#FFFFFF",
        "ai_bubble": "#FFFFFF",
        "ai_text": "#1E293B",
        "ai_border": "#E2E8F0",
        # 聊天区域背景
        "chat_bg": "#F8FAFC",
        # 输入框
        "input_bg": "#FFFFFF",
        "input_border": "#E2E8F0",
        "input_focus": "#6366F1",
    }

    # 颜色 - 深色主题
    COLORS_DARK = {
        "bg_primary": "#0F0F1A",
        "bg_secondary": "#1A1A2E",
        "bg_tertiary": "#252542",
        "surface": "#2D2D3D",
        "surface_hover": "#363648",
        "border": "#3D3D4D",
        "border_light": "#2D2D3D",
        "text_primary": "#F1F5F9",
        "text_secondary": "#94A3B8",
        "text_muted": "#64748B",
        "primary": "#6366F1",
        "primary_light": "#818CF8",
        "primary_bg": "rgba(99, 102, 241, 0.15)",
        "success": "#10B981",
        "success_bg": "rgba(16, 185, 129, 0.15)",
        "warning": "#F59E0B",
        "error": "#EF4444",
        "error_bg": "rgba(239, 68, 68, 0.15)",
        # 气泡颜色
        "user_bubble": "#6366F1",
        "user_text": "#FFFFFF",
        "ai_bubble": "#2D2D3D",
        "ai_text": "#F1F5F9",
        "ai_border": "#3D3D4D",
        # 聊天区域背景
        "chat_bg": "#1A1A2E",
        # 输入框
        "input_bg": "#2D2D3D",
        "input_border": "#3D3D4D",
        "input_focus": "#6366F1",
    }


DS = DesignSystem()


# ==================== 渐进式Markdown渲染器 ====================

class ProgressiveMarkdownRenderer:
    """渐进式Markdown渲染器 - 无跳变"""

    def __init__(self, theme: str = "light"):
        self.theme = theme
        self.colors = DS.COLORS_LIGHT if theme == "light" else DS.COLORS_DARK

    def set_theme(self, theme: str):
        self.theme = theme
        self.colors = DS.COLORS_LIGHT if theme == "light" else DS.COLORS_DARK

    def render_progressive(self, text: str, is_complete: bool = False) -> str:
        if not text:
            return ""

        text_color = self.colors["ai_text"]
        h1_color = "#7C3AED" if self.theme == "light" else "#A78BFA"
        h2_color = "#8B5CF6" if self.theme == "light" else "#818CF8"
        h3_color = "#6366F1" if self.theme == "light" else "#6366F1"
        code_bg = "#F1F5F9" if self.theme == "light" else "#1E1E2E"
        code_color = "#334155" if self.theme == "light" else "#E2E8F0"
        quote_border = "#6366F1"
        quote_color = self.colors["text_secondary"]

        lines = text.split('\n')
        html_parts = []
        in_code_block = False

        for i, line in enumerate(lines):
            is_last_line = (i == len(lines) - 1) and not is_complete

            if line.strip().startswith('```'):
                if in_code_block:
                    html_parts.append('</pre>')
                    in_code_block = False
                else:
                    html_parts.append(
                        f'<pre style="background: {code_bg}; color: {code_color}; '
                        f'padding: 12px; border-radius: 8px; margin: 8px 0; '
                        f'font-family: Consolas, Monaco, monospace; font-size: 13px; '
                        f'overflow-x: auto; white-space: pre-wrap;">'
                    )
                    in_code_block = True
                continue

            if in_code_block:
                html_parts.append(self._escape_html(line) + '\n')
                continue

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
            elif line.startswith('> '):
                content = self._process_inline(line[2:])
                html_parts.append(
                    f'<p style="border-left: 3px solid {quote_border}; padding-left: 12px; '
                    f'margin: 8px 0; color: {quote_color}; font-style: italic;">{content}</p>'
                )
            elif line.strip() in ('---', '***', '___'):
                html_parts.append(
                    f'<hr style="border: none; border-top: 1px solid {self.colors["border"]}; margin: 12px 0;">'
                )
            elif line.strip():
                content = self._process_inline(line)
                if is_last_line:
                    content += '<span style="opacity: 0.6; animation: blink 1s infinite;">▋</span>'
                html_parts.append(
                    f'<p style="margin: 6px 0; line-height: 1.7;">{content}</p>'
                )
            else:
                html_parts.append('<p style="margin: 4px 0;"></p>')

        if in_code_block:
            html_parts.append('</pre>')

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
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    def _process_inline(self, text: str) -> str:
        text = self._escape_html(text)
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)
        text = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<em>\1</em>', text)
        text = re.sub(r'(?<!_)_([^_]+?)_(?!_)', r'<em>\1</em>', text)

        code_bg = "#F1F5F9" if self.theme == "light" else "#1E1E2E"
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
    """平滑打字机动画 - 无跳变"""

    def __init__(self, text_browser: QTextBrowser, content: str,
                 char_delay: int = 20, newline_delay: int = 260,
                 chunk_size: int = 1, theme: str = "light"):
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
        self._is_running = True
        self.current_index = 0
        self.text_browser.clear()
        self.timer.start(self.char_delay)

    def stop(self):
        self._is_running = False
        self.timer.stop()
        self._show_complete()

    def is_running(self) -> bool:
        return self._is_running

    def _type_next(self):
        if self.current_index >= len(self.full_content):
            self.timer.stop()
            self._is_running = False
            self._show_complete()
            return

        next_index = min(self.current_index + self.chunk_size, len(self.full_content))
        chunk = self.full_content[self.current_index:next_index]
        newline_pos = chunk.find('\n')
        if newline_pos != -1:
            next_index = self.current_index + newline_pos + 1
            has_newline = True
        else:
            has_newline = False

        self.current_index = next_index
        current_text = self.full_content[:self.current_index]
        html = self.renderer.render_progressive(current_text, is_complete=False)
        self.text_browser.setHtml(html)

        scrollbar = self.text_browser.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

        if has_newline:
            self.timer.setInterval(self.newline_delay)
        else:
            self.timer.setInterval(self.char_delay)

    def _show_complete(self):
        html = self.renderer.render_progressive(self.full_content, is_complete=True)
        self.text_browser.setHtml(html)


# ==================== 自适应高度TextBrowser ====================

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
        event.ignore()


# ==================== 消息气泡 ====================

class MessageRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"


class ChatBubble(QFrame):
    """聊天气泡组件 - 宽度自适应"""

    def __init__(self, role: MessageRole, content: str, animated: bool = False,
                 theme: str = "light", parent=None):
        super().__init__(parent)
        self.role = role
        self.content = content
        self.animated = animated
        self.theme = theme
        self.colors = DS.COLORS_LIGHT if theme == "light" else DS.COLORS_DARK
        self.typewriter: Optional[SmoothTypewriter] = None
        self._setup_ui()

    def _setup_ui(self):
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
        """用户气泡 - 右侧紫色，宽度自适应"""
        main_layout.addStretch(1)

        bubble = QFrame()
        bubble.setObjectName("userBubble")
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(DS.SPACING_MD, DS.SPACING_SM + 4, DS.SPACING_MD, DS.SPACING_SM + 4)

        content_label = QLabel(self.content)
        content_label.setWordWrap(True)
        content_label.setFont(QFont("Microsoft YaHei", DS.FONT_BASE))
        content_label.setStyleSheet(f"color: {self.colors['user_text']}; background: transparent;")
        bubble_layout.addWidget(content_label)

        bubble.setStyleSheet(f"""
            QFrame#userBubble {{
                background-color: {self.colors['user_bubble']};
                border-radius: {DS.RADIUS_LG}px;
                border-top-right-radius: {DS.RADIUS_SM}px;
            }}
        """)
        # 宽度：使用弹性策略，最大70%
        bubble.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        main_layout.addWidget(bubble, 7)  # 最大占70%
        main_layout.addSpacing(DS.SPACING_MD)

    def _setup_ai_bubble(self, main_layout: QHBoxLayout):
        """AI气泡 - 左侧，宽度自适应"""
        main_layout.addSpacing(DS.SPACING_SM)

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

        logo_label = QLabel("🔮")
        logo_label.setFont(QFont("Segoe UI Emoji", 14))
        logo_label.setFixedSize(24, 24)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setStyleSheet("background: transparent;")
        header_layout.addWidget(logo_label)

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

        if self.animated and self.content:
            self.typewriter = SmoothTypewriter(
                self.content_browser, self.content,
                char_delay=20, newline_delay=260, chunk_size=1, theme=self.theme
            )
            self.typewriter.start()
        else:
            renderer = ProgressiveMarkdownRenderer(self.theme)
            html = renderer.render_progressive(self.content, is_complete=True)
            self.content_browser.setHtml(html)

        bubble_layout.addWidget(self.content_browser)

        bubble.setStyleSheet(f"""
            QFrame#aiBubble {{
                background-color: {self.colors['ai_bubble']};
                border: 1px solid {self.colors['ai_border']};
                border-radius: {DS.RADIUS_LG}px;
                border-top-left-radius: {DS.RADIUS_SM}px;
            }}
        """)
        bubble.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        container_layout.addWidget(bubble)
        main_layout.addWidget(container, 8)  # 最大占80%
        main_layout.addStretch(2)

    def stop_animation(self):
        if self.typewriter and self.typewriter.is_running():
            self.typewriter.stop()


# ==================== 聊天区域 ====================

class ChatWidget(QWidget):
    """聊天消息区域"""

    def __init__(self, theme: str = "light", parent=None):
        super().__init__(parent)
        self.theme = theme
        self.colors = DS.COLORS_LIGHT if theme == "light" else DS.COLORS_DARK
        self.messages: List[ChatBubble] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setFrameStyle(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet(f"background-color: {self.colors['chat_bg']};")

        self.container = QWidget()
        self.container.setStyleSheet(f"background-color: {self.colors['chat_bg']};")
        self.container_layout = QVBoxLayout()
        self.container_layout.setContentsMargins(DS.SPACING_MD, DS.SPACING_SM, DS.SPACING_MD, DS.SPACING_SM)
        self.container_layout.setSpacing(DS.SPACING_SM)
        self.container_layout.addStretch()
        self.container.setLayout(self.container_layout)

        self.scroll_area.setWidget(self.container)
        layout.addWidget(self.scroll_area)
        self.setLayout(layout)

    def set_theme(self, theme: str):
        self.theme = theme
        self.colors = DS.COLORS_LIGHT if theme == "light" else DS.COLORS_DARK
        self.scroll_area.setStyleSheet(f"background-color: {self.colors['chat_bg']};")
        self.container.setStyleSheet(f"background-color: {self.colors['chat_bg']};")

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


# ==================== 侧边栏 ====================

class Sidebar(QFrame):
    """侧边栏 - 使用真实Logo"""

    nav_changed = pyqtSignal(str)

    NAV_ITEMS = [
        {"id": "wendao", "name": "问道", "icon": "💬"},
        {"id": "tuiyan", "name": "推演", "icon": "📊"},
        {"id": "dianji", "name": "典籍", "icon": "📚"},
        {"id": "dongcha", "name": "洞察", "icon": "👁"},
        {"id": "lishi", "name": "历史", "icon": "📜"},
        {"id": "shezhi", "name": "设置", "icon": "⚙️"},
    ]

    def __init__(self, theme: str = "light", parent=None):
        super().__init__(parent)
        self.theme = theme
        self.colors = DS.COLORS_LIGHT if theme == "light" else DS.COLORS_DARK
        self.current_nav = "wendao"
        self.nav_buttons = {}
        self._setup_ui()

    def _setup_ui(self):
        self.setFixedWidth(200)
        self._apply_style()

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

        # 底部
        layout.addWidget(self._create_separator())
        about_widget = QWidget()
        about_layout = QVBoxLayout(about_widget)
        about_layout.setContentsMargins(DS.SPACING_SM, DS.SPACING_MD, DS.SPACING_SM, DS.SPACING_MD)
        about_btn = self._create_nav_button({"id": "about", "name": "关于", "icon": "ℹ️"})
        about_layout.addWidget(about_btn)
        self.nav_buttons["about"] = about_btn
        layout.addWidget(about_widget)

        self.setLayout(layout)
        self._update_selection("wendao")

    def _apply_style(self):
        self.setStyleSheet(f"""
            Sidebar {{
                background-color: {self.colors['bg_primary']};
                border-right: 1px solid {self.colors['border']};
            }}
        """)

    def _create_logo_section(self) -> QWidget:
        """创建Logo区域 - 使用真实Logo图片"""
        widget = QWidget()
        widget.setFixedHeight(90)
        widget.setStyleSheet("background: transparent;")

        layout = QHBoxLayout(widget)
        layout.setContentsMargins(DS.SPACING_MD, DS.SPACING_LG, DS.SPACING_MD, DS.SPACING_MD)
        layout.setSpacing(DS.SPACING_SM)

        # Logo图片 - 透明背景
        self.logo_label = QLabel()
        logo_path = self._get_logo_path()
        if logo_path and os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            scaled = pixmap.scaled(
                44, 44,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.logo_label.setPixmap(scaled)
        else:
            self.logo_label.setText("🔮")
            self.logo_label.setFont(QFont("Segoe UI Emoji", 24))
        self.logo_label.setFixedSize(48, 48)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setStyleSheet("background: transparent;")  # 确保透明
        layout.addWidget(self.logo_label)

        # 名称区域
        name_widget = QWidget()
        name_widget.setStyleSheet("background: transparent;")
        name_layout = QVBoxLayout(name_widget)
        name_layout.setContentsMargins(0, 0, 0, 0)
        name_layout.setSpacing(2)

        self.cn_name = QLabel("赛博玄数")
        cn_font = QFont("Microsoft YaHei", DS.FONT_LG)
        cn_font.setBold(True)
        self.cn_name.setFont(cn_font)
        self.cn_name.setStyleSheet(f"color: {self.colors['text_primary']}; background: transparent;")
        name_layout.addWidget(self.cn_name)

        # 英文名 - 使用更优雅的字体
        self.en_name = QLabel("Cyber Mantic")
        en_font = QFont("Segoe UI", DS.FONT_XS)
        en_font.setItalic(True)
        en_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.5)
        self.en_name.setFont(en_font)
        self.en_name.setStyleSheet(f"color: {self.colors['text_muted']}; background: transparent;")
        name_layout.addWidget(self.en_name)

        layout.addWidget(name_widget)
        layout.addStretch()

        return widget

    def _get_logo_path(self) -> str:
        """获取Logo路径"""
        possible_paths = [
            Path(__file__).parent / "resources" / "app_icon.png",
            Path(__file__).parent / "ui" / "resources" / "app_icon.png",
        ]
        for path in possible_paths:
            if path.exists():
                return str(path)
        return None

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
                    background-color: {self.colors['primary_bg']};
                    color: {self.colors['primary']};
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
                    background-color: {self.colors['surface_hover']};
                    color: {self.colors['text_primary']};
                }}
            """)

    def _on_nav_clicked(self, nav_id: str):
        if nav_id != self.current_nav:
            self._update_selection(nav_id)
            self.nav_changed.emit(nav_id)

    def _update_selection(self, nav_id: str):
        if self.current_nav in self.nav_buttons:
            self._style_nav_button(self.nav_buttons[self.current_nav], False)
        self.current_nav = nav_id
        if nav_id in self.nav_buttons:
            self._style_nav_button(self.nav_buttons[nav_id], True)

    def set_theme(self, theme: str):
        self.theme = theme
        self.colors = DS.COLORS_LIGHT if theme == "light" else DS.COLORS_DARK
        self._apply_style()
        self.cn_name.setStyleSheet(f"color: {self.colors['text_primary']}; background: transparent;")
        self.en_name.setStyleSheet(f"color: {self.colors['text_muted']}; background: transparent;")
        for nav_id, btn in self.nav_buttons.items():
            self._style_nav_button(btn, nav_id == self.current_nav)


# ==================== 设置页面 - AI接口配置 ====================

class AIConfigDialog(QDialog):
    """AI接口添加/编辑对话框"""

    def __init__(self, theme: str = "light", config: dict = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.colors = DS.COLORS_LIGHT if theme == "light" else DS.COLORS_DARK
        self.config = config or {}
        self.setWindowTitle("添加AI接口" if not config else "编辑AI接口")
        self.setMinimumWidth(450)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(DS.SPACING_LG, DS.SPACING_LG, DS.SPACING_LG, DS.SPACING_LG)
        layout.setSpacing(DS.SPACING_MD)

        # 表单
        form = QFormLayout()
        form.setSpacing(DS.SPACING_SM)

        # 接口名称
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("如：Claude API")
        self.name_input.setText(self.config.get("name", ""))
        form.addRow("接口名称:", self.name_input)

        # API Base URL
        self.base_url_input = QLineEdit()
        self.base_url_input.setPlaceholderText("https://api.anthropic.com")
        self.base_url_input.setText(self.config.get("base_url", ""))
        form.addRow("Base URL:", self.base_url_input)

        # API Key
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("sk-xxx...")
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_input.setText(self.config.get("api_key", ""))
        form.addRow("API Key:", self.key_input)

        # 模型名称
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("claude-3-5-sonnet-20241022")
        self.model_input.setText(self.config.get("model", ""))
        form.addRow("模型名称:", self.model_input)

        # 调用限额
        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(0, 100000)
        self.limit_spin.setValue(self.config.get("daily_limit", 1000))
        self.limit_spin.setSuffix(" 次/天")
        form.addRow("每日限额:", self.limit_spin)

        layout.addLayout(form)

        # 测试按钮
        test_btn = QPushButton("🔗 测试连通性")
        test_btn.setFixedHeight(38)
        test_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        test_btn.clicked.connect(self._test_connection)
        test_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.colors['success_bg']};
                color: {self.colors['success']};
                border: 1px solid {self.colors['success']};
                border-radius: {DS.RADIUS_SM}px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {self.colors['success']};
                color: white;
            }}
        """)
        layout.addWidget(test_btn)

        # 状态标签
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"color: {self.colors['text_muted']};")
        layout.addWidget(self.status_label)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedSize(80, 36)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("保存")
        save_btn.setFixedSize(80, 36)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.colors['primary']};
                color: white;
                border: none;
                border-radius: {DS.RADIUS_SM}px;
            }}
            QPushButton:hover {{
                background-color: {self.colors['primary_light']};
            }}
        """)
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def _test_connection(self):
        self.status_label.setText("⏳ 正在测试连接...")
        self.status_label.setStyleSheet(f"color: {self.colors['warning']};")
        # 模拟测试
        QTimer.singleShot(1000, self._show_test_result)

    def _show_test_result(self):
        if self.key_input.text() and self.base_url_input.text():
            self.status_label.setText("✅ 连接成功！")
            self.status_label.setStyleSheet(f"color: {self.colors['success']};")
        else:
            self.status_label.setText("❌ 连接失败：请填写完整信息")
            self.status_label.setStyleSheet(f"color: {self.colors['error']};")

    def _save(self):
        if not self.name_input.text() or not self.key_input.text():
            QMessageBox.warning(self, "提示", "请填写接口名称和API Key")
            return
        self.accept()

    def get_config(self) -> dict:
        return {
            "name": self.name_input.text(),
            "base_url": self.base_url_input.text(),
            "api_key": self.key_input.text(),
            "model": self.model_input.text(),
            "daily_limit": self.limit_spin.value(),
        }


class SettingsPage(QWidget):
    """设置页面 - 全新设计的AI接口配置"""

    theme_changed = pyqtSignal(str)

    def __init__(self, theme: str = "light", parent=None):
        super().__init__(parent)
        self.theme = theme
        self.colors = DS.COLORS_LIGHT if theme == "light" else DS.COLORS_DARK
        # 模拟已配置的AI接口
        self.configured_apis = [
            {"name": "Claude API", "model": "claude-3-5-sonnet-20241022", "status": "正常"},
            {"name": "Deepseek", "model": "deepseek-chat", "status": "正常"},
        ]
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(DS.SPACING_LG, DS.SPACING_LG, DS.SPACING_LG, DS.SPACING_LG)
        layout.setSpacing(DS.SPACING_LG)

        # 标题
        title = QLabel("⚙️ 设置")
        title.setFont(QFont("Microsoft YaHei", DS.FONT_XL, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {self.colors['text_primary']};")
        layout.addWidget(title)

        # 使用滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameStyle(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, DS.SPACING_MD, 0)
        content_layout.setSpacing(DS.SPACING_LG)

        # 1. 全局模型设置卡片
        global_card = self._create_global_settings_card()
        content_layout.addWidget(global_card)

        # 2. 个性化设置（可展开）
        personalized_card = self._create_personalized_card()
        content_layout.addWidget(personalized_card)

        # 3. AI接口管理卡片
        api_card = self._create_api_management_card()
        content_layout.addWidget(api_card)

        # 4. 主题设置
        theme_card = self._create_theme_card()
        content_layout.addWidget(theme_card)

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        self.setLayout(layout)

    def _create_card(self, title: str) -> tuple:
        """创建卡片容器"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {self.colors['surface']};
                border: 1px solid {self.colors['border']};
                border-radius: {DS.RADIUS_MD}px;
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(DS.SPACING_LG, DS.SPACING_MD, DS.SPACING_LG, DS.SPACING_MD)
        card_layout.setSpacing(DS.SPACING_MD)

        title_label = QLabel(title)
        title_label.setFont(QFont("Microsoft YaHei", DS.FONT_MD, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {self.colors['text_primary']}; background: transparent;")
        card_layout.addWidget(title_label)

        return card, card_layout

    def _create_global_settings_card(self) -> QFrame:
        """全局模型设置"""
        card, layout = self._create_card("🎯 全局模型设置")

        form = QFormLayout()
        form.setSpacing(DS.SPACING_SM)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # 仅显示已配置的模型
        configured_models = [api["name"] for api in self.configured_apis]

        # 优先模型
        self.primary_model = QComboBox()
        self.primary_model.addItems(configured_models)
        self.primary_model.setMinimumWidth(200)
        form.addRow("优先模型:", self.primary_model)

        # 副模型
        self.secondary_model = QComboBox()
        self.secondary_model.addItems(configured_models)
        self.secondary_model.setCurrentIndex(1 if len(configured_models) > 1 else 0)
        self.secondary_model.setMinimumWidth(200)
        form.addRow("副模型:", self.secondary_model)

        # 重试设置
        retry_widget = QWidget()
        retry_layout = QHBoxLayout(retry_widget)
        retry_layout.setContentsMargins(0, 0, 0, 0)
        retry_layout.setSpacing(DS.SPACING_SM)

        self.retry_times = QSpinBox()
        self.retry_times.setRange(1, 10)
        self.retry_times.setValue(3)
        self.retry_times.setSuffix(" 次")
        retry_layout.addWidget(self.retry_times)

        retry_layout.addWidget(QLabel("间隔"))

        self.retry_interval = QSpinBox()
        self.retry_interval.setRange(1, 60)
        self.retry_interval.setValue(5)
        self.retry_interval.setSuffix(" 秒")
        retry_layout.addWidget(self.retry_interval)
        retry_layout.addStretch()

        form.addRow("重试设置:", retry_widget)

        # 双模型验证
        self.dual_verify = QCheckBox("启用双模型交叉验证")
        self.dual_verify.setChecked(True)
        self.dual_verify.setStyleSheet(f"color: {self.colors['text_primary']};")
        form.addRow("", self.dual_verify)

        layout.addLayout(form)

        # 提示
        hint = QLabel("💡 下拉框仅显示已配置的AI接口，请在下方「AI接口管理」中添加")
        hint.setStyleSheet(f"color: {self.colors['text_muted']}; font-size: {DS.FONT_XS}px; background: transparent;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        return card

    def _create_personalized_card(self) -> QFrame:
        """个性化设置（可展开）"""
        card, layout = self._create_card("🎨 个性化调用设置")

        # 开关
        self.enable_personalized = QCheckBox("启用个性化设置（为每个环节单独配置模型）")
        self.enable_personalized.setStyleSheet(f"color: {self.colors['text_primary']};")
        self.enable_personalized.toggled.connect(self._toggle_personalized)
        layout.addWidget(self.enable_personalized)

        # 详细设置区域（初始隐藏）
        self.personalized_content = QWidget()
        p_layout = QVBoxLayout(self.personalized_content)
        p_layout.setContentsMargins(DS.SPACING_MD, 0, 0, 0)
        p_layout.setSpacing(DS.SPACING_SM)

        configured_models = [api["name"] for api in self.configured_apis]

        stages = [
            ("小六壬初判", "xiaoliu"),
            ("测字术分析", "cezi"),
            ("八字分析", "bazi"),
            ("综合报告生成", "report"),
        ]

        for stage_name, stage_id in stages:
            row = QHBoxLayout()
            row.setSpacing(DS.SPACING_SM)

            label = QLabel(f"{stage_name}:")
            label.setFixedWidth(120)
            label.setStyleSheet(f"color: {self.colors['text_secondary']}; background: transparent;")
            row.addWidget(label)

            combo = QComboBox()
            combo.addItem("使用全局设置")
            combo.addItems(configured_models)
            combo.setMinimumWidth(180)
            row.addWidget(combo)

            row.addStretch()
            p_layout.addLayout(row)

        self.personalized_content.hide()
        layout.addWidget(self.personalized_content)

        return card

    def _toggle_personalized(self, checked: bool):
        self.personalized_content.setVisible(checked)

    def _create_api_management_card(self) -> QFrame:
        """AI接口管理"""
        card, layout = self._create_card("🔌 AI接口管理")

        # 接口列表表格
        self.api_table = QTableWidget()
        self.api_table.setColumnCount(4)
        self.api_table.setHorizontalHeaderLabels(["接口名称", "模型", "状态", "操作"])
        self.api_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.api_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.api_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.api_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.api_table.setColumnWidth(2, 80)
        self.api_table.setColumnWidth(3, 100)
        self.api_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.api_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.api_table.setMaximumHeight(200)
        self.api_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {self.colors['bg_secondary']};
                border: 1px solid {self.colors['border']};
                border-radius: {DS.RADIUS_SM}px;
                gridline-color: {self.colors['border']};
            }}
            QTableWidget::item {{
                padding: 8px;
                color: {self.colors['text_primary']};
            }}
            QHeaderView::section {{
                background-color: {self.colors['bg_tertiary']};
                color: {self.colors['text_secondary']};
                padding: 8px;
                border: none;
                font-weight: 500;
            }}
        """)

        self._refresh_api_table()
        layout.addWidget(self.api_table)

        # 添加按钮
        add_btn = QPushButton("➕ 添加AI接口")
        add_btn.setFixedHeight(38)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._add_api)
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.colors['primary']};
                color: white;
                border: none;
                border-radius: {DS.RADIUS_SM}px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {self.colors['primary_light']};
            }}
        """)
        layout.addWidget(add_btn)

        return card

    def _refresh_api_table(self):
        self.api_table.setRowCount(len(self.configured_apis))
        for i, api in enumerate(self.configured_apis):
            self.api_table.setItem(i, 0, QTableWidgetItem(api["name"]))
            self.api_table.setItem(i, 1, QTableWidgetItem(api["model"]))

            status_item = QTableWidgetItem(api["status"])
            status_item.setForeground(QColor(self.colors["success"]))
            self.api_table.setItem(i, 2, status_item)

            # 操作按钮
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 4, 4, 4)
            btn_layout.setSpacing(4)

            edit_btn = QPushButton("编辑")
            edit_btn.setFixedSize(40, 26)
            edit_btn.setStyleSheet(f"color: {self.colors['primary']}; background: transparent; border: none;")
            edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_layout.addWidget(edit_btn)

            del_btn = QPushButton("删除")
            del_btn.setFixedSize(40, 26)
            del_btn.setStyleSheet(f"color: {self.colors['error']}; background: transparent; border: none;")
            del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_layout.addWidget(del_btn)

            self.api_table.setCellWidget(i, 3, btn_widget)

    def _add_api(self):
        dialog = AIConfigDialog(self.theme, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            config = dialog.get_config()
            self.configured_apis.append({
                "name": config["name"],
                "model": config["model"],
                "status": "正常"
            })
            self._refresh_api_table()
            # 更新下拉框
            self._update_model_combos()

    def _update_model_combos(self):
        configured_models = [api["name"] for api in self.configured_apis]
        self.primary_model.clear()
        self.primary_model.addItems(configured_models)
        self.secondary_model.clear()
        self.secondary_model.addItems(configured_models)

    def _create_theme_card(self) -> QFrame:
        """主题设置"""
        card, layout = self._create_card("🎨 外观设置")

        row = QHBoxLayout()
        row.setSpacing(DS.SPACING_MD)

        label = QLabel("界面主题:")
        label.setStyleSheet(f"color: {self.colors['text_primary']}; background: transparent;")
        row.addWidget(label)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["浅色主题", "深色主题"])
        self.theme_combo.setCurrentIndex(0 if self.theme == "light" else 1)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        self.theme_combo.setMinimumWidth(150)
        row.addWidget(self.theme_combo)

        row.addStretch()
        layout.addLayout(row)

        return card

    def _on_theme_changed(self, index: int):
        theme = "light" if index == 0 else "dark"
        self.theme_changed.emit(theme)

    def set_theme(self, theme: str):
        self.theme = theme
        self.colors = DS.COLORS_LIGHT if theme == "light" else DS.COLORS_DARK
        # 这里需要重新渲染整个页面，简化处理


# ==================== 右侧信息面板 ====================

class InfoPanel(QFrame):
    """右侧信息面板"""

    def __init__(self, theme: str = "light", parent=None):
        super().__init__(parent)
        self.theme = theme
        self.colors = DS.COLORS_LIGHT if theme == "light" else DS.COLORS_DARK
        self._setup_ui()

    def _setup_ui(self):
        self.setMinimumWidth(280)
        self.setMaximumWidth(350)

        layout = QVBoxLayout()
        layout.setContentsMargins(DS.SPACING_MD, DS.SPACING_MD, DS.SPACING_MD, DS.SPACING_MD)
        layout.setSpacing(DS.SPACING_MD)

        progress_card = self._create_card("📊 分析进度", "等待开始...")
        layout.addWidget(progress_card)

        theories_card = self._create_theories_card()
        layout.addWidget(theories_card)

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

    def set_theme(self, theme: str):
        self.theme = theme
        self.colors = DS.COLORS_LIGHT if theme == "light" else DS.COLORS_DARK


# ==================== 主窗口 ====================

class DemoMainWindow(QMainWindow):
    """Demo主窗口 - 默认白色主题"""

    def __init__(self):
        super().__init__()
        self.theme = "light"  # 默认白色主题
        self.colors = DS.COLORS_LIGHT
        self._setup_ui()
        self._apply_theme()

    def _setup_ui(self):
        self.setWindowTitle("赛博玄数 - UI美观Demo V2")
        self.setMinimumSize(1200, 800)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 侧边栏
        self.sidebar = Sidebar(self.theme)
        self.sidebar.nav_changed.connect(self._on_nav_changed)
        main_layout.addWidget(self.sidebar)

        # 内容区域（使用StackedWidget切换页面）
        self.content_stack = QStackedWidget()

        # 问道页面（聊天）
        self.chat_page = self._create_chat_page()
        self.content_stack.addWidget(self.chat_page)

        # 设置页面
        self.settings_page = SettingsPage(self.theme)
        self.settings_page.theme_changed.connect(self._change_theme)
        self.content_stack.addWidget(self.settings_page)

        # 占位页面
        for page_name in ["推演", "典籍", "洞察", "历史", "关于"]:
            placeholder = self._create_placeholder(page_name)
            self.content_stack.addWidget(placeholder)

        main_layout.addWidget(self.content_stack, 1)

        # 右侧面板（仅在聊天页面显示）
        self.info_panel = InfoPanel(self.theme)
        main_layout.addWidget(self.info_panel)

        # 页面映射
        self.page_map = {
            "wendao": 0,
            "shezhi": 1,
            "tuiyan": 2,
            "dianji": 3,
            "dongcha": 4,
            "lishi": 5,
            "about": 6,
        }

    def _create_chat_page(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        self.chat_widget = ChatWidget(self.theme)
        layout.addWidget(self.chat_widget, 1)

        input_area = self._create_input_area()
        layout.addWidget(input_area)

        return widget

    def _create_toolbar(self) -> QFrame:
        toolbar = QFrame()
        toolbar.setFixedHeight(56)
        toolbar.setStyleSheet(f"""
            QFrame {{
                background-color: {self.colors['primary_bg']};
                border-bottom: 1px solid {self.colors['border']};
            }}
        """)

        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(DS.SPACING_MD, DS.SPACING_SM, DS.SPACING_MD, DS.SPACING_SM)
        layout.setSpacing(DS.SPACING_SM)

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

        demo_btn = QPushButton("🎬 演示打字机效果")
        demo_btn.setFixedHeight(38)
        demo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        demo_btn.clicked.connect(self._demo_typewriter)
        demo_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.colors['success_bg']};
                color: {self.colors['success']};
                border: 1px solid {self.colors['success']};
                border-radius: {DS.RADIUS_SM}px;
                padding: 0 {DS.SPACING_MD}px;
                font-size: {DS.FONT_SM}px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {self.colors['success']};
                color: white;
            }}
        """)
        layout.addWidget(demo_btn)

        layout.addStretch()

        return toolbar

    def _create_input_area(self) -> QFrame:
        container = QFrame()
        container.setStyleSheet(f"background-color: {self.colors['bg_secondary']};")

        layout = QVBoxLayout(container)
        layout.setContentsMargins(DS.SPACING_MD, DS.SPACING_SM, DS.SPACING_MD, DS.SPACING_MD)
        layout.setSpacing(DS.SPACING_SM)

        row = QHBoxLayout()
        row.setSpacing(DS.SPACING_SM)

        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("输入您想咨询的问题... (Enter发送，Shift+Enter换行)")
        self.input_text.setFixedHeight(60)
        self.input_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.colors['input_bg']};
                border: 1px solid {self.colors['input_border']};
                border-radius: {DS.RADIUS_MD}px;
                padding: {DS.SPACING_SM}px {DS.SPACING_MD}px;
                color: {self.colors['text_primary']};
                font-size: {DS.FONT_BASE}px;
            }}
            QTextEdit:focus {{
                border-color: {self.colors['input_focus']};
            }}
        """)
        row.addWidget(self.input_text)

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

    def _create_placeholder(self, name: str) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        label = QLabel(f"📋 {name}页面")
        label.setFont(QFont("Microsoft YaHei", DS.FONT_XL))
        label.setStyleSheet(f"color: {self.colors['text_muted']};")
        layout.addWidget(label)

        hint = QLabel("此页面正在开发中...")
        hint.setStyleSheet(f"color: {self.colors['text_muted']};")
        layout.addWidget(hint)

        return widget

    def _apply_theme(self):
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {self.colors['bg_secondary']};
            }}
        """)

    def _change_theme(self, theme: str):
        self.theme = theme
        self.colors = DS.COLORS_LIGHT if theme == "light" else DS.COLORS_DARK
        self._apply_theme()
        self.sidebar.set_theme(theme)
        self.chat_widget.set_theme(theme)
        # 简化：实际项目中需要更新所有组件

    def _on_nav_changed(self, nav_id: str):
        if nav_id in self.page_map:
            self.content_stack.setCurrentIndex(self.page_map[nav_id])
            # 仅在聊天页显示右侧面板
            self.info_panel.setVisible(nav_id == "wendao")

    def _on_new_conversation(self):
        self.chat_widget.clear()
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
        QTimer.singleShot(500, lambda: self.chat_widget.add_ai_message(demo_text, animated=True))

    def _on_send(self):
        text = self.input_text.toPlainText().strip()
        if text:
            self.chat_widget.add_user_message(text)
            self.input_text.clear()
            response = f"感谢您的问题！您问的是：**{text}**\n\n让我为您分析一下..."
            QTimer.singleShot(300, lambda: self.chat_widget.add_ai_message(response, animated=True))


# ==================== 程序入口 ====================

def main():
    app = QApplication(sys.argv)

    font = QFont("Microsoft YaHei", DS.FONT_BASE)
    app.setFont(font)

    window = DemoMainWindow()
    window.show()

    QTimer.singleShot(500, window._on_new_conversation)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
