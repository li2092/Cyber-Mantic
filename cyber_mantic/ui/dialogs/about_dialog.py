"""
关于产品对话框
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QScrollArea, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QFont
from pathlib import Path


class AboutDialog(QDialog):
    """关于 Cyber-Mantic 产品对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("关于 Cyber-Mantic")
        self.setMinimumSize(700, 600)
        self.setMaximumSize(900, 800)

        self._init_ui()

    def _init_ui(self):
        """初始化UI（添加全局滚动条）"""
        # 创建主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 创建全局滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)

        # 创建内容容器
        content_widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Logo 区域
        logo_layout = QHBoxLayout()
        logo_layout.addStretch()

        logo_label = QLabel()
        logo_path = Path(__file__).parent.parent / "resources" / "app_logo_full.png"

        if logo_path.exists():
            pixmap = QPixmap(str(logo_path))
            # 缩放到合适大小，保持宽高比
            scaled_pixmap = pixmap.scaled(
                200, 200,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            logo_label.setPixmap(scaled_pixmap)
        else:
            # Logo 文件不存在时显示文字
            logo_label.setText("Cyber-Mantic")
            logo_label.setStyleSheet("""
                QLabel {
                    font-size: 32px;
                    font-weight: bold;
                    color: #2c3e50;
                }
            """)

        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(logo_label)
        logo_layout.addStretch()
        layout.addLayout(logo_layout)

        # 副标题
        subtitle = QLabel("数字时代的智能命理系统")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_font = QFont()
        subtitle_font.setPointSize(12)
        subtitle.setFont(subtitle_font)
        subtitle.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(subtitle)

        # 英文名称
        en_name = QLabel("The Intelligent Divination System for the Digital Age")
        en_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        en_name.setStyleSheet("color: #95a5a6; font-style: italic;")
        layout.addWidget(en_name)

        # 分隔线
        separator1 = QLabel()
        separator1.setFixedHeight(1)
        separator1.setStyleSheet("background-color: #bdc3c7;")
        layout.addWidget(separator1)

        # 简短介绍（英文）
        brief_intro = QLabel(
            '<b>Brief Introduction:</b><br/>'
            'Cyber-Mantic is an AI-powered divination system that integrates eight Chinese '
            'metaphysical traditions with modern algorithms. It provides intelligent, '
            'multi-theory validated insights for life guidance in the digital age—balancing '
            'ancient wisdom with ethical technology.'
        )
        brief_intro.setWordWrap(True)
        brief_intro.setStyleSheet("""
            QLabel {
                padding: 15px;
                border-radius: 8px;
                font-size: 10pt;
                line-height: 1.5;
            }
        """)
        layout.addWidget(brief_intro)

        # 详细介绍标题
        detail_title = QLabel("详细介绍 | Detailed Introduction")
        detail_title.setStyleSheet("font-weight: bold; font-size: 11pt;")
        layout.addWidget(detail_title)

        # 详细介绍内容容器（移除独立滚动条，直接显示）
        detail_container = QWidget()
        detail_container.setStyleSheet("""
            QWidget {
                border-radius: 8px;
                padding: 15px;
            }
        """)
        detail_layout = QVBoxLayout(detail_container)
        detail_layout.setSpacing(15)
        detail_layout.setContentsMargins(15, 15, 15, 15)

        # 中文版介绍
        zh_title = QLabel("【中文版】")
        zh_title.setStyleSheet("font-weight: bold; color: #e74c3c;")
        detail_layout.addWidget(zh_title)

        zh_content = QLabel(self._get_chinese_intro())
        zh_content.setWordWrap(True)
        zh_content.setTextFormat(Qt.TextFormat.RichText)
        zh_content.setStyleSheet("line-height: 1.6; font-size: 10pt;")
        detail_layout.addWidget(zh_content)

        # 分隔线
        separator2 = QLabel()
        separator2.setFixedHeight(1)
        separator2.setStyleSheet("margin: 10px 0;")
        detail_layout.addWidget(separator2)

        # 英文版介绍
        en_title = QLabel("【English Version】")
        en_title.setStyleSheet("font-weight: bold; color: #3498db;")
        detail_layout.addWidget(en_title)

        en_content = QLabel(self._get_english_intro())
        en_content.setWordWrap(True)
        en_content.setTextFormat(Qt.TextFormat.RichText)
        en_content.setStyleSheet("line-height: 1.6; font-size: 10pt;")
        detail_layout.addWidget(en_content)

        layout.addWidget(detail_container)

        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_btn = QPushButton("关闭 (Close)")
        close_btn.setMinimumWidth(120)
        close_btn.setMinimumHeight(36)
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11pt;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)

        button_layout.addWidget(close_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        # 将内容容器设置为滚动区域的widget
        content_widget.setLayout(layout)
        scroll_area.setWidget(content_widget)

        # 将滚动区域添加到主布局
        main_layout.addWidget(scroll_area)

        self.setLayout(main_layout)

    def _get_chinese_intro(self) -> str:
        """获取中文介绍内容"""
        return """
<h3 style="color: #2c3e50;">赛博玄数（Cyber-Mantic）：数字时代的智能命理系统</h3>

<p style="text-indent: 2em; line-height: 1.8;">
赛博玄数是一个融合传统文化智慧与人工智能技术的创新命理分析平台。我们整合了<b>八字、奇门遁甲、梅花易数、紫微斗数</b>等<b>八种中国传统术数理论</b>，通过先进算法实现多理论交叉验证与智能冲突解决。
</p>

<p style="text-indent: 2em; line-height: 1.8;">
系统采用<b>"最小输入、最大洞察"</b>的设计理念，用户仅需提供基本信息即可获得精准的回溯与预测分析。我们内置多层伦理保护机制，尊重用户隐私，强调理性参考，平衡传统文化中的"天机不可尽泄"智慧与现代科技的便利性。
</p>

<p style="text-indent: 2em; line-height: 1.8;">
无论是对个人发展的探寻，还是重要决策的参考，赛博玄数都以<b>科学严谨的态度</b>，为您提供传统智慧与现代算法相结合的全新洞察体验。
</p>
"""

    def _get_english_intro(self) -> str:
        """获取英文介绍内容"""
        return """
<h3 style="color: #2c3e50;">Cyber-Mantic: The Intelligent Divination System for the Digital Age</h3>

<p style="line-height: 1.8;">
Cyber-Mantic is an innovative platform that bridges traditional wisdom with artificial intelligence technology. We integrate <b>eight major Chinese metaphysical systems</b>—including <b>Bazi, Qimen Dunjia, Plum Blossom Numerology, and Ziwei Doushu</b>—leveraging advanced algorithms for cross-validation and intelligent conflict resolution.
</p>

<p style="line-height: 1.8;">
Adopting a <b>"minimum input, maximum insight"</b> design philosophy, the system provides precise retrospective and predictive analyses based on essential user information. With built-in multi-layered ethical safeguards, we prioritize user privacy and promote rational decision-making, balancing the traditional wisdom of "heaven's secrets should not be fully revealed" with modern technological convenience.
</p>

<p style="line-height: 1.8;">
Whether for personal growth exploration or important decision-making references, Cyber-Mantic offers a unique perspective that combines ancient wisdom with modern algorithmic intelligence—all approached with <b>scientific rigor and cultural respect</b>.
</p>
"""
