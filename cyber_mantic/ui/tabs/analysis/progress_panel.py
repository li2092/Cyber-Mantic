"""
进度面板组件 - 显示分析进度和过程信息
"""
from PyQt6.QtWidgets import (
    QGroupBox, QVBoxLayout, QLabel, QTextEdit, QProgressBar
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class ProgressPanel(QGroupBox):
    """进度面板组件"""

    def __init__(self, parent=None):
        super().__init__("分析进度", parent)
        self._init_ui()
        self.setVisible(False)  # 初始隐藏

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # 进度标签
        self.progress_label = QLabel("等待开始分析...")
        self.progress_label.setStyleSheet("font-weight: bold; font-size: 11pt; color: #2196F3;")
        layout.addWidget(self.progress_label)

        # 过程信息显示区域（在进度条上方，显示5行）
        self.process_info_text = QTextEdit()
        self.process_info_text.setReadOnly(True)
        self.process_info_text.setPlaceholderText("分析过程信息将在此显示...")
        # 设置固定高度：约5行文本的高度（行高约20px，5行=100px + 边距）
        self.process_info_text.setFixedHeight(120)
        # 启用垂直滚动条
        self.process_info_text.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.process_info_text.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # 设置字体
        info_font = QFont("Consolas", 9)
        self.process_info_text.setFont(info_font)
        layout.addWidget(self.process_info_text)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(25)
        layout.addWidget(self.progress_bar)

        # 进度详情
        self.progress_text = QTextEdit()
        self.progress_text.setReadOnly(True)
        self.progress_text.setMaximumHeight(150)
        self.progress_text.setPlaceholderText("分析详情将在此显示...")
        layout.addWidget(self.progress_text)

        self.setLayout(layout)

    def reset(self):
        """重置进度面板"""
        self.progress_bar.setValue(0)
        self.progress_label.setText("正在分析...")
        self.progress_text.clear()
        self.process_info_text.clear()
        self.setVisible(True)

    def update_progress(self, theory: str, status: str, progress: int, detail: str = ""):
        """更新进度信息

        Args:
            theory: 理论名称
            status: 状态描述
            progress: 进度值 (0-100)
            detail: 详细信息
        """
        self.progress_label.setText(f"正在分析：{theory} - {status}")
        self.progress_bar.setValue(progress)

        # 如果有详细信息，添加到过程信息显示区域
        if detail:
            self.process_info_text.append(detail)
            # 自动滚动到最底端
            scrollbar = self.process_info_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def set_completed(self):
        """设置为完成状态"""
        self.progress_bar.setValue(100)
        self.progress_label.setText("分析完成 ✓")

    def set_failed(self):
        """设置为失败状态"""
        self.progress_label.setText("分析失败")
