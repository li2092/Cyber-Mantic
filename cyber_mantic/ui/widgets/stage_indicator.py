"""
StageIndicatorBar - 五阶段指示条组件

显示问道流程的5个阶段状态：
- 当前阶段：绿色渐变
- 已执行阶段：橙色渐变
- 未执行阶段：浅灰色

点击显示阶段介绍
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QFrame, QToolTip, QVBoxLayout, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QCursor, QFont
from typing import Optional
from enum import IntEnum


class StageStatus(IntEnum):
    """阶段状态"""
    PENDING = 0      # 未执行（灰色）
    CURRENT = 1      # 当前（绿色）
    COMPLETED = 2    # 已执行（橙色）


class StageIndicatorItem(QPushButton):
    """单个阶段指示项 - 紧凑单行设计"""

    stage_clicked = pyqtSignal(int)  # 点击信号，传递阶段索引

    # 阶段介绍
    STAGE_DESCRIPTIONS = {
        1: "【破冰阶段】\n\n快速了解您的问题类型，通过小六壬进行初步判断。\n\n需要提供：\n• 咨询类别（事业/感情/财运等）\n• 3个随机数字（1-9）",
        2: "【深入阶段】\n\n通过测字术深入分析问题本质，建立更深层次的理解。\n\n需要提供：\n• 具体问题描述\n• 一个汉字（心中所想）",
        3: "【信息收集】\n\n收集出生信息，为多理论分析做准备。\n\n需要提供：\n• 出生年月日时\n• 性别\n• MBTI类型（可选）",
        4: "【回溯验证】\n\n通过回溯问题验证分析准确性，调整置信度。\n\n需要回答：\n• 3个验证问题\n• 可选择跳过",
        5: "【生成报告】\n\n综合多理论分析结果，生成个性化报告。\n\n包含：\n• 综合判断\n• 各理论分析\n• 行动建议"
    }

    # 阶段中文数字
    STAGE_NUMBERS = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五"}

    def __init__(self, index: int, name: str, theme: str = "light", parent=None):
        super().__init__(parent)
        self.index = index
        self.name = name
        self.theme = theme
        self.status = StageStatus.PENDING

        self._setup_ui()
        self._apply_style()

        # 连接点击信号
        self.clicked.connect(self._on_clicked)

    def _setup_ui(self):
        """设置UI"""
        self.setFixedHeight(32)
        self.setMinimumWidth(100)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        # 设置按钮文本：单行显示
        num = self.STAGE_NUMBERS.get(self.index, str(self.index))
        self.setText(f"阶段{num} {self.name}")

        # 设置字体
        font = QFont("Microsoft YaHei", 9)
        font.setBold(True)
        self.setFont(font)

    def set_status(self, status: StageStatus):
        """设置状态"""
        self.status = status
        self._apply_style()

    def set_theme(self, theme: str):
        """设置主题"""
        self.theme = theme
        self._apply_style()

    def _apply_style(self):
        """应用样式 - 美化渐变效果"""
        is_dark = self.theme == "dark"

        if self.status == StageStatus.CURRENT:
            # 当前阶段 - 绿色渐变
            self.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #34D399, stop:1 #10B981);
                    color: #FFFFFF;
                    border: none;
                    border-radius: 6px;
                    padding: 6px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #10B981, stop:1 #059669);
                }
                QPushButton:pressed {
                    background: #059669;
                }
            """)
        elif self.status == StageStatus.COMPLETED:
            # 已执行 - 橙色渐变
            self.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #FB923C, stop:1 #EA580C);
                    color: #FFFFFF;
                    border: none;
                    border-radius: 6px;
                    padding: 6px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #EA580C, stop:1 #C2410C);
                }
                QPushButton:pressed {
                    background: #C2410C;
                }
            """)
        else:
            # 未执行 - 灰色
            if is_dark:
                self.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #4B5563, stop:1 #374151);
                        color: #9CA3AF;
                        border: none;
                        border-radius: 6px;
                        padding: 6px 16px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #6B7280, stop:1 #4B5563);
                        color: #D1D5DB;
                    }
                    QPushButton:pressed {
                        background: #374151;
                    }
                """)
            else:
                self.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #F3F4F6, stop:1 #E5E7EB);
                        color: #6B7280;
                        border: none;
                        border-radius: 6px;
                        padding: 6px 16px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #E5E7EB, stop:1 #D1D5DB);
                        color: #374151;
                    }
                    QPushButton:pressed {
                        background: #D1D5DB;
                    }
                """)

    def _on_clicked(self):
        """点击处理"""
        self.stage_clicked.emit(self.index)
        self._show_description()

    def _show_description(self):
        """显示阶段介绍"""
        description = self.STAGE_DESCRIPTIONS.get(self.index, "暂无介绍")
        # 使用QToolTip显示，位置在组件下方
        global_pos = self.mapToGlobal(QPoint(self.width() // 2, self.height()))
        QToolTip.showText(global_pos, description, self, self.rect(), 8000)


class StageIndicatorBar(QWidget):
    """五阶段指示条 - 紧凑版"""

    stage_clicked = pyqtSignal(int)  # 阶段点击信号

    # 阶段定义
    STAGES = [
        (1, "破冰"),
        (2, "深入"),
        (3, "收集"),
        (4, "验证"),
        (5, "报告"),
    ]

    def __init__(self, theme: str = "light", parent=None):
        super().__init__(parent)
        self.theme = theme
        self.current_stage = 1  # 当前阶段（1-5）
        self.stage_items = {}

        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        self.setFixedHeight(44)

        # 设置背景
        self.setAutoFillBackground(True)

        layout = QHBoxLayout()
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)

        # 创建5个阶段指示项
        for index, name in self.STAGES:
            item = StageIndicatorItem(index, name, self.theme)
            item.stage_clicked.connect(self._on_item_clicked)
            self.stage_items[index] = item
            layout.addWidget(item, 1)  # 等比例分配空间

        self.setLayout(layout)

        # 设置容器样式
        self._apply_container_style()

        # 初始化状态（第1阶段为当前）
        self._update_all_status()

    def _apply_container_style(self):
        """应用容器样式"""
        is_dark = self.theme == "dark"
        if is_dark:
            bg = "rgba(30, 41, 59, 0.95)"
            border = "rgba(71, 85, 105, 0.6)"
        else:
            bg = "rgba(255, 255, 255, 0.98)"
            border = "rgba(229, 231, 235, 1)"

        self.setStyleSheet(f"""
            StageIndicatorBar {{
                background-color: {bg};
                border-bottom: 1px solid {border};
            }}
        """)

    def set_current_stage(self, stage: int):
        """
        设置当前阶段

        Args:
            stage: 阶段编号（1-5）
        """
        if 1 <= stage <= 5:
            self.current_stage = stage
            self._update_all_status()

    def set_theme(self, theme: str):
        """设置主题"""
        self.theme = theme
        self._apply_container_style()
        for item in self.stage_items.values():
            item.set_theme(theme)

    def _update_all_status(self):
        """更新所有阶段状态"""
        for index, item in self.stage_items.items():
            if index < self.current_stage:
                item.set_status(StageStatus.COMPLETED)
            elif index == self.current_stage:
                item.set_status(StageStatus.CURRENT)
            else:
                item.set_status(StageStatus.PENDING)

    def _on_item_clicked(self, index: int):
        """阶段项点击"""
        self.stage_clicked.emit(index)

    def reset(self):
        """重置到初始状态"""
        self.current_stage = 1
        self._update_all_status()
