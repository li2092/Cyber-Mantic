"""
常用档案管理对话框
用于保存、加载、删除常用的出生信息档案
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QListWidget, QPushButton, QMessageBox, QListWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal
from typing import Optional
from models import PersonBirthInfo
from utils.profile_manager import get_profile_manager


class ProfileManagerDialog(QDialog):
    """常用档案管理对话框"""

    profile_selected = pyqtSignal(PersonBirthInfo)  # 选择档案信号

    def __init__(self, parent=None):
        """初始化对话框"""
        super().__init__(parent)
        self.profile_manager = get_profile_manager()
        self.selected_profile: Optional[PersonBirthInfo] = None

        self.setWindowTitle("常用档案管理")
        self.setModal(True)
        self.setMinimumSize(500, 400)

        self._init_ui()
        self._refresh_profile_list()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title_label = QLabel(f"常用档案管理（最多保存{self.profile_manager.MAX_PROFILES}个）")
        title_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        layout.addWidget(title_label)

        # 档案列表
        self.profile_list = QListWidget()
        self.profile_list.setMinimumHeight(250)
        self.profile_list.itemDoubleClicked.connect(self._load_selected_profile)
        layout.addWidget(self.profile_list)

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.load_btn = QPushButton("加载选中档案")
        self.load_btn.setMinimumHeight(36)
        self.load_btn.clicked.connect(self._load_selected_profile)
        self.load_btn.setEnabled(False)
        button_layout.addWidget(self.load_btn)

        self.delete_btn = QPushButton("删除选中档案")
        self.delete_btn.setMinimumHeight(36)
        self.delete_btn.clicked.connect(self._delete_selected_profile)
        self.delete_btn.setEnabled(False)
        button_layout.addWidget(self.delete_btn)

        button_layout.addStretch()

        close_btn = QPushButton("关闭")
        close_btn.setMinimumSize(100, 36)
        close_btn.clicked.connect(self.reject)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        # 连接列表选择信号
        self.profile_list.itemSelectionChanged.connect(self._on_selection_changed)

    def _refresh_profile_list(self):
        """刷新档案列表"""
        self.profile_list.clear()
        profiles = self.profile_manager.list_profiles()

        if not profiles:
            item = QListWidgetItem("暂无保存的档案")
            item.setFlags(Qt.ItemFlag.NoItemFlags)  # 不可选择
            self.profile_list.addItem(item)
        else:
            for profile_info in profiles:
                label = profile_info['label']
                updated_at = profile_info['updated_at']
                item_text = f"{label}  (更新: {updated_at})"
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, label)  # 存储label
                self.profile_list.addItem(item)

    def _on_selection_changed(self):
        """列表选择改变"""
        has_selection = len(self.profile_list.selectedItems()) > 0
        selected_item = self.profile_list.currentItem()

        # 检查是否是空提示项
        is_valid = has_selection and selected_item.data(Qt.ItemDataRole.UserRole) is not None

        self.load_btn.setEnabled(is_valid)
        self.delete_btn.setEnabled(is_valid)

    def _load_selected_profile(self):
        """加载选中的档案"""
        selected_item = self.profile_list.currentItem()
        if not selected_item:
            return

        label = selected_item.data(Qt.ItemDataRole.UserRole)
        if not label:
            return

        profile = self.profile_manager.load_profile(label)
        if profile:
            self.selected_profile = profile
            self.profile_selected.emit(profile)
            self.accept()
        else:
            QMessageBox.warning(self, "错误", f"加载档案失败: {label}")

    def _delete_selected_profile(self):
        """删除选中的档案"""
        selected_item = self.profile_list.currentItem()
        if not selected_item:
            return

        label = selected_item.data(Qt.ItemDataRole.UserRole)
        if not label:
            return

        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除档案 \"{label}\" 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.profile_manager.delete_profile(label):
                QMessageBox.information(self, "成功", f"档案 \"{label}\" 已删除")
                self._refresh_profile_list()
            else:
                QMessageBox.warning(self, "错误", f"删除档案失败: {label}")

    def get_selected_profile(self) -> Optional[PersonBirthInfo]:
        """获取选中的档案"""
        return self.selected_profile
