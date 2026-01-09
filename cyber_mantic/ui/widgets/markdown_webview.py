"""
MarkdownWebView - 基于QWebEngineView的Markdown渲染组件

使用Chromium内核渲染Markdown，效果远超QTextBrowser：
- 完整的CSS支持
- 语法高亮
- 平滑的打字动画
- 更好的排版效果
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PyQt6.QtCore import Qt, QUrl, pyqtSignal, QTimer
from PyQt6.QtGui import QColor

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import QWebEnginePage
    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False
    QWebEngineView = None
    QWebEnginePage = None


# 优雅的Markdown CSS样式
MARKDOWN_CSS = """
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 14px;
    line-height: 1.6;
    color: #E2E8F0;
    background-color: transparent;
    padding: 0;
    word-wrap: break-word;
    overflow-wrap: break-word;
}

/* 标题样式 */
h1, h2, h3, h4, h5, h6 {
    margin-top: 16px;
    margin-bottom: 8px;
    font-weight: 600;
    line-height: 1.25;
}

h1 {
    font-size: 1.5em;
    color: #DDD6FE;
    border-bottom: 1px solid #4B5563;
    padding-bottom: 8px;
}

h2 {
    font-size: 1.3em;
    color: #C4B5FD;
}

h3 {
    font-size: 1.15em;
    color: #A78BFA;
}

h4, h5, h6 {
    font-size: 1em;
    color: #8B5CF6;
}

/* 段落 */
p {
    margin-bottom: 12px;
}

/* 强调 */
strong, b {
    font-weight: 600;
    color: #F1F5F9;
}

em, i {
    font-style: italic;
    color: #CBD5E1;
}

/* 链接 */
a {
    color: #818CF8;
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}

/* 列表 */
ul, ol {
    margin-left: 20px;
    margin-bottom: 12px;
}

li {
    margin-bottom: 4px;
}

li > ul, li > ol {
    margin-top: 4px;
    margin-bottom: 4px;
}

/* 引用块 */
blockquote {
    border-left: 4px solid #6366F1;
    padding-left: 16px;
    margin: 12px 0;
    color: #94A3B8;
    font-style: italic;
    background-color: rgba(99, 102, 241, 0.1);
    border-radius: 0 8px 8px 0;
    padding: 8px 16px;
}

/* 代码 - 行内 */
code {
    font-family: "SF Mono", "Fira Code", "JetBrains Mono", Consolas, monospace;
    font-size: 0.9em;
    background-color: #1E1E2E;
    color: #A78BFA;
    padding: 2px 6px;
    border-radius: 4px;
}

/* 代码块 */
pre {
    background-color: #1E1E2E;
    border: 1px solid #374151;
    border-radius: 8px;
    padding: 12px 16px;
    margin: 12px 0;
    overflow-x: auto;
    font-family: "SF Mono", "Fira Code", "JetBrains Mono", Consolas, monospace;
    font-size: 0.9em;
    line-height: 1.5;
}

pre code {
    background-color: transparent;
    padding: 0;
    color: #E2E8F0;
}

/* 分割线 */
hr {
    border: none;
    border-top: 1px solid #4B5563;
    margin: 16px 0;
}

/* 表格 */
table {
    border-collapse: collapse;
    width: 100%;
    margin: 12px 0;
}

th, td {
    border: 1px solid #4B5563;
    padding: 8px 12px;
    text-align: left;
}

th {
    background-color: #374151;
    font-weight: 600;
}

tr:nth-child(even) {
    background-color: rgba(55, 65, 81, 0.3);
}

/* 打字光标 */
.typing-cursor {
    display: inline-block;
    width: 2px;
    height: 1em;
    background-color: #A78BFA;
    margin-left: 2px;
    animation: blink 1s infinite;
    vertical-align: text-bottom;
}

@keyframes blink {
    0%, 50% { opacity: 1; }
    51%, 100% { opacity: 0; }
}

/* 打字模式下的文本 */
.typing-text {
    white-space: pre-wrap;
    word-wrap: break-word;
}

/* 滚动条样式 */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}

::-webkit-scrollbar-track {
    background: transparent;
}

::-webkit-scrollbar-thumb {
    background: #4B5563;
    border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
    background: #6B7280;
}
"""

# HTML模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
{css}
    </style>
</head>
<body>
{content}
</body>
</html>
"""

# 简单的Markdown到HTML转换（不依赖外部库）
def markdown_to_html(text: str) -> str:
    """将Markdown转换为HTML"""
    if not text:
        return ""

    import re

    # 转义HTML特殊字符（但保留我们要处理的Markdown语法）
    def escape_html(s):
        return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    lines = text.split('\n')
    html_lines = []
    in_code_block = False
    in_list = False
    list_type = None  # 'ul' or 'ol'

    for i, line in enumerate(lines):
        # 代码块处理
        if line.strip().startswith('```'):
            if in_code_block:
                html_lines.append('</code></pre>')
                in_code_block = False
            else:
                lang = line.strip()[3:].strip()
                html_lines.append(f'<pre><code class="language-{lang}">' if lang else '<pre><code>')
                in_code_block = True
            continue

        if in_code_block:
            html_lines.append(escape_html(line))
            continue

        # 关闭列表（如果当前行不是列表项）
        stripped = line.strip()
        is_ul_item = stripped.startswith('- ') or stripped.startswith('* ')
        is_ol_item = bool(re.match(r'^\d+\.\s', stripped))

        if in_list and not is_ul_item and not is_ol_item and stripped:
            html_lines.append(f'</{list_type}>')
            in_list = False
            list_type = None

        # 空行
        if not stripped:
            if in_list:
                html_lines.append(f'</{list_type}>')
                in_list = False
                list_type = None
            html_lines.append('<br>')
            continue

        # 标题
        if stripped.startswith('#### '):
            html_lines.append(f'<h4>{process_inline(escape_html(stripped[5:]))}</h4>')
        elif stripped.startswith('### '):
            html_lines.append(f'<h3>{process_inline(escape_html(stripped[4:]))}</h3>')
        elif stripped.startswith('## '):
            html_lines.append(f'<h2>{process_inline(escape_html(stripped[3:]))}</h2>')
        elif stripped.startswith('# '):
            html_lines.append(f'<h1>{process_inline(escape_html(stripped[2:]))}</h1>')
        # 引用
        elif stripped.startswith('> '):
            html_lines.append(f'<blockquote>{process_inline(escape_html(stripped[2:]))}</blockquote>')
        # 分割线
        elif stripped in ('---', '***', '___'):
            html_lines.append('<hr>')
        # 无序列表
        elif is_ul_item:
            if not in_list or list_type != 'ul':
                if in_list:
                    html_lines.append(f'</{list_type}>')
                html_lines.append('<ul>')
                in_list = True
                list_type = 'ul'
            content = stripped[2:]
            html_lines.append(f'<li>{process_inline(escape_html(content))}</li>')
        # 有序列表
        elif is_ol_item:
            if not in_list or list_type != 'ol':
                if in_list:
                    html_lines.append(f'</{list_type}>')
                html_lines.append('<ol>')
                in_list = True
                list_type = 'ol'
            match = re.match(r'^\d+\.\s(.*)$', stripped)
            if match:
                content = match.group(1)
                html_lines.append(f'<li>{process_inline(escape_html(content))}</li>')
        # 普通段落
        else:
            html_lines.append(f'<p>{process_inline(escape_html(stripped))}</p>')

    # 关闭未关闭的代码块或列表
    if in_code_block:
        html_lines.append('</code></pre>')
    if in_list:
        html_lines.append(f'</{list_type}>')

    return '\n'.join(html_lines)


def process_inline(text: str) -> str:
    """处理行内Markdown格式"""
    import re

    # 加粗 **text** 或 __text__
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)

    # 斜体 *text* 或 _text_
    text = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<em>\1</em>', text)
    text = re.sub(r'(?<!_)_([^_]+?)_(?!_)', r'<em>\1</em>', text)

    # 行内代码 `code`
    text = re.sub(r'`([^`]+?)`', r'<code>\1</code>', text)

    # 链接 [text](url)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)

    return text


class MarkdownWebView(QWidget):
    """基于QWebEngineView的Markdown渲染组件"""

    # 信号：内容高度变化
    heightChanged = pyqtSignal(int)
    # 信号：内容加载完成
    loadFinished = pyqtSignal()

    def __init__(self, parent=None, theme: str = "dark"):
        super().__init__(parent)
        self.theme = theme
        self._content = ""
        self._is_typing = False
        self._target_height = 50

        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        if WEBENGINE_AVAILABLE:
            self.web_view = QWebEngineView()
            self.web_view.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)

            # 设置透明背景
            self.web_view.page().setBackgroundColor(QColor(0, 0, 0, 0))

            # 监听内容大小变化
            self.web_view.loadFinished.connect(self._on_load_finished)

            layout.addWidget(self.web_view)
        else:
            # 回退到QLabel
            from PyQt6.QtWidgets import QLabel
            self.fallback_label = QLabel("QWebEngineView不可用")
            self.fallback_label.setWordWrap(True)
            self.fallback_label.setStyleSheet("color: #E2E8F0;")
            layout.addWidget(self.fallback_label)

        self.setLayout(layout)
        self.setMinimumHeight(50)

    def _on_load_finished(self, ok):
        """内容加载完成"""
        if ok:
            # 获取内容高度并调整widget大小
            self._update_height()
            self.loadFinished.emit()

    def _update_height(self):
        """更新widget高度以匹配内容"""
        if not WEBENGINE_AVAILABLE:
            return

        # 通过JavaScript获取内容高度
        self.web_view.page().runJavaScript(
            "document.body.scrollHeight",
            self._set_height
        )

    def _set_height(self, height):
        """设置高度"""
        if height and height > 0:
            new_height = int(height) + 16  # 添加一点边距
            self._target_height = new_height
            self.setMinimumHeight(new_height)
            self.setMaximumHeight(new_height + 50)
            self.heightChanged.emit(new_height)

    def set_markdown(self, content: str, animated: bool = False):
        """
        设置Markdown内容

        Args:
            content: Markdown文本
            animated: 是否使用打字动画
        """
        self._content = content
        self._is_typing = animated

        if not WEBENGINE_AVAILABLE:
            if hasattr(self, 'fallback_label'):
                self.fallback_label.setText(content)
            return

        # 转换Markdown到HTML
        html_content = markdown_to_html(content)

        # 生成完整HTML
        full_html = HTML_TEMPLATE.format(css=MARKDOWN_CSS, content=html_content)

        # 加载HTML
        self.web_view.setHtml(full_html)

    def set_typing_text(self, text: str):
        """
        设置打字中的文本（纯文本，带光标）

        Args:
            text: 当前已输入的文本
        """
        if not WEBENGINE_AVAILABLE:
            if hasattr(self, 'fallback_label'):
                self.fallback_label.setText(text)
            return

        # 转义HTML
        escaped = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        # 保留换行
        escaped = escaped.replace('\n', '<br>')

        html_content = f'<div class="typing-text">{escaped}<span class="typing-cursor"></span></div>'
        full_html = HTML_TEMPLATE.format(css=MARKDOWN_CSS, content=html_content)

        self.web_view.setHtml(full_html)

    def get_content(self) -> str:
        """获取原始Markdown内容"""
        return self._content

    def clear(self):
        """清空内容"""
        self._content = ""
        if WEBENGINE_AVAILABLE:
            self.web_view.setHtml("")
        elif hasattr(self, 'fallback_label'):
            self.fallback_label.setText("")


class MarkdownTypewriter:
    """Markdown打字机动画 - 配合MarkdownWebView使用"""

    def __init__(self, web_view: MarkdownWebView, content: str,
                 char_delay: int = 12, chunk_size: int = 5):
        """
        初始化打字机动画

        Args:
            web_view: MarkdownWebView实例
            content: 完整Markdown内容
            char_delay: 字符间延迟（毫秒）
            chunk_size: 每次显示的字符数
        """
        self.web_view = web_view
        self.full_content = content
        self.char_delay = char_delay
        self.chunk_size = chunk_size
        self.current_index = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self._type_next_chunk)
        self._is_running = False
        self._on_complete = None

    def start(self, on_complete=None):
        """开始打字动画"""
        self._is_running = True
        self._on_complete = on_complete
        self.current_index = 0
        self.web_view.clear()
        self.timer.start(self.char_delay)

    def stop(self):
        """停止动画并显示完整内容"""
        self._is_running = False
        self.timer.stop()
        self._show_full_content()

    def _type_next_chunk(self):
        """显示下一组字符"""
        if self.current_index >= len(self.full_content):
            self.timer.stop()
            self._is_running = False
            self._show_full_content()
            if self._on_complete:
                self._on_complete()
            return

        # 计算本次显示到哪个位置
        next_index = min(self.current_index + self.chunk_size, len(self.full_content))

        # 检查换行符
        chunk = self.full_content[self.current_index:next_index]
        newline_pos = chunk.find('\n')
        if newline_pos != -1:
            next_index = self.current_index + newline_pos + 1

        self.current_index = next_index

        # 显示当前文本
        current_text = self.full_content[:self.current_index]
        self.web_view.set_typing_text(current_text)

    def _show_full_content(self):
        """显示完整渲染的Markdown"""
        self.web_view.set_markdown(self.full_content)

    def is_running(self) -> bool:
        """检查是否正在运行"""
        return self._is_running


def is_webengine_available() -> bool:
    """检查QWebEngineView是否可用"""
    return WEBENGINE_AVAILABLE
