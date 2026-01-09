"""
首次启动引导对话框

功能：
- 5步引导流程介绍核心功能
- 可跳过的向导式界面
- 进度指示器
"""
from typing import List, Tuple
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QWidget, QStackedWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class OnboardingDialog(QDialog):
    """首次启动引导对话框"""

    # 信号：引导完成
    completed = pyqtSignal()

    def __init__(self, theme: str = "light", parent=None):
        super().__init__(parent)
        self.theme = theme
        self.setWindowTitle("欢迎使用赛博玄数")
        self.setMinimumSize(650, 500)
        self.setModal(True)

        # 当前步骤
        self._current_step = 0

        # 引导步骤配置
        self._steps = self._define_steps()

        self._init_ui()
        self._update_step()

    def _define_steps(self) -> List[Tuple[str, str, str, str]]:
        """定义引导步骤：(icon, title, subtitle, description)"""
        return [
            (
                "💬",
                "问道",
                "对话式探索",
                "像和朋友聊天一样，通过5个阶段的对话，\n"
                "逐步深入了解自己的命理特征。\n\n"
                "• 渐进式分析，由浅入深\n"
                "• 支持多种术数理论\n"
                "• 可保存对话记录供日后参考"
            ),
            (
                "📊",
                "推演",
                "快速排盘分析",
                "输入生辰信息，快速获取多种术数的排盘结果。\n\n"
                "• 支持八字、紫微斗数、六爻等8大理论\n"
                "• 一次输入，多维分析\n"
                "• 结果可保存、比较、追问"
            ),
            (
                "📚",
                "典籍",
                "术数知识学习",
                "系统收录经典术数文献，配合AI学习助手，\n"
                "帮助您深入理解传统智慧。\n\n"
                "• 经典文献阅读与笔记\n"
                "• AI智能总结、洞察、学习方案\n"
                "• 支持导入个人资料"
            ),
            (
                "🔮",
                "洞察",
                "个人使用画像",
                "通过您的使用轨迹，生成个人画像分析，\n"
                "帮助您更好地认识自己当前的关注点。\n\n"
                "• 使用统计与习惯分析\n"
                "• AI深度画像分析\n"
                "• 所有数据仅存储在本地"
            ),
            (
                "⚙️",
                "设置",
                "个性化配置",
                "配置AI接口、主题外观、数据管理等，\n"
                "让应用更贴合您的使用习惯。\n\n"
                "• 支持多种AI服务商\n"
                "• 可配置自定义接口\n"
                "• 内置详细帮助文档"
            )
        ]

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 顶部欢迎标题
        header = self._create_header()
        layout.addWidget(header)

        # 内容区域
        self._content_stack = QStackedWidget()
        for step in self._steps:
            page = self._create_step_page(*step)
            self._content_stack.addWidget(page)
        layout.addWidget(self._content_stack, 1)

        # 底部导航
        footer = self._create_footer()
        layout.addWidget(footer)

    def _create_header(self) -> QWidget:
        """创建头部"""
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                padding: 20px;
            }
        """)

        layout = QVBoxLayout(header)
        layout.setContentsMargins(30, 25, 30, 25)

        # 欢迎文字
        welcome_label = QLabel("🎉 欢迎使用赛博玄数！")
        welcome_label.setStyleSheet("color: white; font-size: 22px; font-weight: bold;")
        layout.addWidget(welcome_label)

        subtitle_label = QLabel("让我们花1分钟了解核心功能")
        subtitle_label.setStyleSheet("color: rgba(255,255,255,0.9); font-size: 14px;")
        layout.addWidget(subtitle_label)

        return header

    def _create_step_page(self, icon: str, title: str, subtitle: str, description: str) -> QWidget:
        """创建步骤页面"""
        is_dark = self.theme == "dark"

        # 主题相关颜色
        title_color = "#E2E8F0" if is_dark else "#333"
        subtitle_color = "#94A3B8" if is_dark else "#666"
        desc_bg = "#1E293B" if is_dark else "#f8f9fa"
        desc_color = "#CBD5E1" if is_dark else "#444"

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(15)

        # 图标
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 48px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        # 标题
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"color: {title_color};")
        layout.addWidget(title_label)

        # 副标题
        subtitle_label = QLabel(subtitle)
        subtitle_label.setStyleSheet(f"color: {subtitle_color}; font-size: 16px;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)

        layout.addSpacing(10)

        # 描述
        desc_frame = QFrame()
        desc_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {desc_bg};
                border-radius: 10px;
                padding: 20px;
            }}
        """)
        desc_layout = QVBoxLayout(desc_frame)
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"color: {desc_color}; font-size: 14px; line-height: 1.6;")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        desc_layout.addWidget(desc_label)
        layout.addWidget(desc_frame)

        layout.addStretch()

        return page

    def _create_footer(self) -> QWidget:
        """创建底部导航"""
        is_dark = self.theme == "dark"
        footer_bg = "#1E293B" if is_dark else "#fff"
        footer_border = "#334155" if is_dark else "#eee"

        footer = QFrame()
        footer.setStyleSheet(f"""
            QFrame {{
                background-color: {footer_bg};
                border-top: 1px solid {footer_border};
            }}
        """)

        # 主题相关颜色 - 按钮
        dot_inactive = "#4B5563" if is_dark else "#ddd"
        skip_color = "#64748B" if is_dark else "#999"
        skip_hover = "#94A3B8" if is_dark else "#666"
        prev_border = "#4B5563" if is_dark else "#ddd"
        prev_bg = "#1E293B" if is_dark else "#fff"
        prev_color = "#94A3B8" if is_dark else "#666"
        prev_hover_bg = "#334155" if is_dark else "#f5f5f5"

        layout = QVBoxLayout(footer)
        layout.setContentsMargins(30, 15, 30, 20)
        layout.setSpacing(15)

        # 进度指示器
        progress_layout = QHBoxLayout()
        progress_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._progress_dots = []
        self._dot_inactive_color = dot_inactive
        for i in range(len(self._steps)):
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {dot_inactive}; font-size: 12px;")
            self._progress_dots.append(dot)
            progress_layout.addWidget(dot)

        layout.addLayout(progress_layout)

        # 按钮区域
        btn_layout = QHBoxLayout()

        # 跳过按钮
        self._skip_btn = QPushButton("跳过引导")
        self._skip_btn.clicked.connect(self._on_skip)
        self._skip_btn.setStyleSheet(f"""
            QPushButton {{
                padding: 10px 25px;
                border: none;
                background: transparent;
                color: {skip_color};
                font-size: 14px;
            }}
            QPushButton:hover {{
                color: {skip_hover};
            }}
        """)
        btn_layout.addWidget(self._skip_btn)

        btn_layout.addStretch()

        # 上一步按钮
        self._prev_btn = QPushButton("← 上一步")
        self._prev_btn.clicked.connect(self._on_prev)
        self._prev_btn.setStyleSheet(f"""
            QPushButton {{
                padding: 10px 25px;
                border: 1px solid {prev_border};
                border-radius: 5px;
                background: {prev_bg};
                color: {prev_color};
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {prev_hover_bg};
            }}
        """)
        btn_layout.addWidget(self._prev_btn)

        # 下一步/开始使用按钮
        self._next_btn = QPushButton("下一步 →")
        self._next_btn.clicked.connect(self._on_next)
        self._next_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 30px;
                border: none;
                border-radius: 5px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5a6fd6, stop:1 #6a4190);
            }
        """)
        btn_layout.addWidget(self._next_btn)

        layout.addLayout(btn_layout)

        return footer

    def _update_step(self):
        """更新当前步骤显示"""
        # 更新内容
        self._content_stack.setCurrentIndex(self._current_step)

        # 更新进度指示器
        for i, dot in enumerate(self._progress_dots):
            if i == self._current_step:
                dot.setStyleSheet("color: #667eea; font-size: 12px;")
            else:
                dot.setStyleSheet(f"color: {self._dot_inactive_color}; font-size: 12px;")

        # 更新按钮状态
        self._prev_btn.setVisible(self._current_step > 0)

        if self._current_step == len(self._steps) - 1:
            self._next_btn.setText("开始使用 ✨")
        else:
            self._next_btn.setText("下一步 →")

    def _on_prev(self):
        """上一步"""
        if self._current_step > 0:
            self._current_step -= 1
            self._update_step()

    def _on_next(self):
        """下一步/完成"""
        if self._current_step < len(self._steps) - 1:
            self._current_step += 1
            self._update_step()
        else:
            self.completed.emit()
            self.accept()

    def _on_skip(self):
        """跳过引导"""
        self.completed.emit()
        self.accept()
