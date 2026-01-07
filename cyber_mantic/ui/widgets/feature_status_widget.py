"""
FeatureStatusWidget - 功能状态可视化组件

显示所有新增功能的初始化状态，帮助用户了解哪些功能可用
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from typing import Dict, Tuple


class FeatureStatusWidget(QWidget):
    """功能状态显示组件"""

    refresh_requested = pyqtSignal()  # 请求刷新状态

    def __init__(self, parent=None):
        super().__init__(parent)
        self.feature_status: Dict[str, bool] = {}
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 功能状态组
        status_group = QGroupBox("🔍 功能状态")
        status_layout = QVBoxLayout()

        # 标题说明
        desc_label = QLabel("显示所有新增功能的初始化状态")
        desc_label.setStyleSheet("font-size: 9pt; margin-bottom: 8px;")
        status_layout.addWidget(desc_label)

        # 状态列表容器
        self.status_list_widget = QWidget()
        self.status_list_layout = QVBoxLayout()
        self.status_list_layout.setContentsMargins(0, 0, 0, 0)
        self.status_list_layout.setSpacing(4)
        self.status_list_widget.setLayout(self.status_list_layout)

        status_layout.addWidget(self.status_list_widget)

        # 刷新按钮
        refresh_btn = QPushButton("🔄 刷新状态")
        refresh_btn.clicked.connect(self.refresh_requested.emit)
        refresh_btn.setStyleSheet("""
            QPushButton {
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 9pt;
            }
            QPushButton:hover {
            }
        """)
        status_layout.addWidget(refresh_btn)

        status_group.setLayout(status_layout)
        main_layout.addWidget(status_group)

        self.setLayout(main_layout)

    def update_status(self, feature_status: Dict[str, bool]):
        """
        更新功能状态

        Args:
            feature_status: 功能名称 -> 是否可用的映射
        """
        self.feature_status = feature_status

        # 清空现有状态项
        while self.status_list_layout.count():
            item = self.status_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 添加功能状态项
        for feature_name, is_available in feature_status.items():
            status_item = self._create_status_item(feature_name, is_available)
            self.status_list_layout.addWidget(status_item)

    def _create_status_item(self, feature_name: str, is_available: bool) -> QWidget:
        """
        创建单个状态项

        Args:
            feature_name: 功能名称
            is_available: 是否可用

        Returns:
            状态项widget
        """
        item_widget = QWidget()
        item_layout = QHBoxLayout()
        item_layout.setContentsMargins(8, 4, 8, 4)

        # 状态图标
        if is_available:
            status_icon = QLabel("✅")
            status_text = "正常"
            status_color = "#4CAF50"
        else:
            status_icon = QLabel("❌")
            status_text = "不可用"
            status_color = "#F44336"

        status_icon.setFixedWidth(30)
        item_layout.addWidget(status_icon)

        # 功能名称
        name_label = QLabel(feature_name)
        name_label.setStyleSheet("font-size: 10pt;")
        item_layout.addWidget(name_label)

        item_layout.addStretch()

        # 状态文本
        status_label = QLabel(status_text)
        status_label.setStyleSheet(f"color: {status_color}; font-size: 9pt; font-weight: bold;")
        item_layout.addWidget(status_label)

        item_widget.setLayout(item_layout)

        # 根据状态设置背景色
        if is_available:
            item_widget.setStyleSheet("""
                QWidget {
                    background-color: #F1F8E9;
                    border-radius: 4px;
                }
            """)
        else:
            item_widget.setStyleSheet("""
                QWidget {
                    background-color: #FFEBEE;
                    border-radius: 4px;
                }
            """)

        return item_widget

    def get_available_count(self) -> Tuple[int, int]:
        """
        获取可用功能数量

        Returns:
            (可用数量, 总数量)
        """
        total = len(self.feature_status)
        available = sum(1 for status in self.feature_status.values() if status)
        return available, total
