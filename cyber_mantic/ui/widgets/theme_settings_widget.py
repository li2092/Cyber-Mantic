"""
ThemeSettingsWidget - 主题设置组件

提供主题选择和自动切换功能
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QRadioButton, QCheckBox, QLabel, QPushButton,
    QMessageBox, QButtonGroup
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from typing import Optional

from utils.theme_manager import ThemeManager
from utils.logger import get_logger


class ThemeSettingsWidget(QWidget):
    """主题设置组件"""

    # 信号：主题已更改
    theme_changed = pyqtSignal(str)  # 新主题名称

    def __init__(self, theme_manager: Optional[ThemeManager] = None, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager or ThemeManager()
        self.logger = get_logger(__name__)
        self._setup_ui()
        self._load_current_settings()

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # 主题选择组
        theme_group = QGroupBox("🎨 外观主题")
        theme_layout = QVBoxLayout()
        theme_layout.setSpacing(12)

        # 说明文字
        desc_label = QLabel("选择您喜欢的界面主题风格：")
        desc_label.setStyleSheet("font-size: 10pt;")
        theme_layout.addWidget(desc_label)

        # 主题选项按钮组（确保单选）
        self.theme_button_group = QButtonGroup(self)

        # 清雅白主题
        self.light_radio = QRadioButton("☀️ 清雅白")
        self.light_radio.setStyleSheet("""
            QRadioButton {
                font-size: 11pt;
                padding: 6px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
        """)
        self.light_radio.toggled.connect(lambda checked: self._on_theme_changed("light", checked))
        self.theme_button_group.addButton(self.light_radio)
        theme_layout.addWidget(self.light_radio)

        light_desc = QLabel("    明亮简洁的浅色主题，适合白天使用")
        light_desc.setStyleSheet("font-size: 9pt; margin-left: 28px;")
        theme_layout.addWidget(light_desc)

        # 墨夜黑主题
        self.dark_radio = QRadioButton("🌙 墨夜黑")
        self.dark_radio.setStyleSheet("""
            QRadioButton {
                font-size: 11pt;
                padding: 6px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
        """)
        self.dark_radio.toggled.connect(lambda checked: self._on_theme_changed("dark", checked))
        self.theme_button_group.addButton(self.dark_radio)
        theme_layout.addWidget(self.dark_radio)

        dark_desc = QLabel("    深邃优雅的深色主题，适合夜间使用")
        dark_desc.setStyleSheet("font-size: 9pt; margin-left: 28px;")
        theme_layout.addWidget(dark_desc)

        # 禅意灰主题
        self.zen_radio = QRadioButton("🧘 禅意灰")
        self.zen_radio.setStyleSheet("""
            QRadioButton {
                font-size: 11pt;
                padding: 6px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
        """)
        self.zen_radio.toggled.connect(lambda checked: self._on_theme_changed("zen", checked))
        self.theme_button_group.addButton(self.zen_radio)
        theme_layout.addWidget(self.zen_radio)

        zen_desc = QLabel("    平和中性的灰色主题，适合专注工作")
        zen_desc.setStyleSheet("font-size: 9pt; margin-left: 28px;")
        theme_layout.addWidget(zen_desc)

        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)

        # 自动切换组
        auto_group = QGroupBox("⏰ 自动切换")
        auto_layout = QVBoxLayout()
        auto_layout.setSpacing(8)

        self.auto_switch_checkbox = QCheckBox("启用主题自动切换")
        self.auto_switch_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 11pt;
                padding: 6px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """)
        self.auto_switch_checkbox.toggled.connect(self._on_auto_switch_changed)
        auto_layout.addWidget(self.auto_switch_checkbox)

        auto_desc = QLabel("    白天（6:00-18:00）自动使用清雅白主题\n    夜间（18:00-6:00）自动使用墨夜黑主题")
        auto_desc.setStyleSheet("font-size: 9pt; margin-left: 28px;")
        auto_desc.setWordWrap(True)
        auto_layout.addWidget(auto_desc)

        auto_group.setLayout(auto_layout)
        layout.addWidget(auto_group)

        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        apply_btn = QPushButton("💾 应用主题")
        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #64B5F6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 24px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #42A5F5;
            }
        """)
        apply_btn.clicked.connect(self._on_apply_clicked)
        button_layout.addWidget(apply_btn)

        reset_btn = QPushButton("↺ 重置为默认")
        reset_btn.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 6px;
                padding: 8px 24px;
                font-size: 10pt;
            }
        """)
        reset_btn.clicked.connect(self._on_reset_clicked)
        button_layout.addWidget(reset_btn)

        layout.addLayout(button_layout)

        layout.addStretch()

        self.setLayout(layout)

        # 整体样式
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

    def _load_current_settings(self):
        """加载当前设置"""
        # 获取当前主题
        current_theme = self.theme_manager.get_current_theme()

        # 设置单选按钮
        if current_theme == "light":
            self.light_radio.setChecked(True)
        elif current_theme == "dark":
            self.dark_radio.setChecked(True)
        elif current_theme == "zen":
            self.zen_radio.setChecked(True)
        else:
            # 默认选择清雅白
            self.light_radio.setChecked(True)

        # 设置自动切换复选框
        auto_switch = self.theme_manager.settings.get("auto_switch", False)
        self.auto_switch_checkbox.setChecked(auto_switch)

        # 如果启用了自动切换，禁用主题单选按钮
        self._update_radio_buttons_state()

    def _update_radio_buttons_state(self):
        """更新单选按钮状态"""
        auto_enabled = self.auto_switch_checkbox.isChecked()

        # 如果启用了自动切换，禁用主题选择
        self.light_radio.setEnabled(not auto_enabled)
        self.dark_radio.setEnabled(not auto_enabled)
        self.zen_radio.setEnabled(not auto_enabled)

    def _on_theme_changed(self, theme_name: str, checked: bool):
        """主题单选按钮改变"""
        if not checked:
            # 只处理选中事件
            return

        # 如果自动切换未启用，立即保存
        if not self.auto_switch_checkbox.isChecked():
            self.logger.info(f"用户选择主题: {theme_name}")

    def _on_auto_switch_changed(self, checked: bool):
        """自动切换复选框改变"""
        self._update_radio_buttons_state()
        self.logger.info(f"自动切换: {'启用' if checked else '禁用'}")

    def _on_apply_clicked(self):
        """应用按钮点击"""
        try:
            # 保存自动切换设置
            auto_enabled = self.auto_switch_checkbox.isChecked()
            self.theme_manager.enable_auto_switch(auto_enabled)

            # 保存主题选择
            if not auto_enabled:
                # 手动模式，保存用户选择的主题
                if self.light_radio.isChecked():
                    theme_name = "light"
                elif self.dark_radio.isChecked():
                    theme_name = "dark"
                elif self.zen_radio.isChecked():
                    theme_name = "zen"
                else:
                    theme_name = "light"  # 默认

                self.theme_manager.set_theme(theme_name)
            else:
                # 自动模式，设置自动切换时间（使用默认值）
                self.theme_manager.set_auto_switch_times(
                    day_start_hour=6,
                    night_start_hour=18,
                    day_theme="light",
                    night_theme="dark"
                )

            # 获取最终应用的主题
            final_theme = self.theme_manager.get_current_theme()

            # 发送主题更改信号
            self.theme_changed.emit(final_theme)

            # 显示成功消息
            if auto_enabled:
                QMessageBox.information(
                    self,
                    "设置已保存",
                    "已启用主题自动切换！\n\n白天（6:00-18:00）使用清雅白主题\n夜间（18:00-6:00）使用墨夜黑主题\n\n主题已应用，请重启应用以完全生效。"
                )
            else:
                theme_names = {
                    "light": "清雅白",
                    "dark": "墨夜黑",
                    "zen": "禅意灰"
                }
                QMessageBox.information(
                    self,
                    "设置已保存",
                    f"主题已切换为：{theme_names.get(final_theme, final_theme)}\n\n主题已应用，请重启应用以完全生效。"
                )

            self.logger.info(f"主题设置已保存并应用: {final_theme} (自动切换: {auto_enabled})")

        except Exception as e:
            self.logger.error(f"应用主题设置失败: {e}")
            QMessageBox.warning(
                self,
                "应用失败",
                f"保存设置时出错：{str(e)}"
            )

    def _on_reset_clicked(self):
        """重置按钮点击"""
        reply = QMessageBox.question(
            self,
            "确认重置",
            "确定要重置为默认设置吗？\n\n将使用清雅白主题，禁用自动切换。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 重置为默认
            self.theme_manager.set_theme("light")
            self.theme_manager.enable_auto_switch(False)

            # 更新UI
            self.light_radio.setChecked(True)
            self.auto_switch_checkbox.setChecked(False)

            # 发送信号
            self.theme_changed.emit("light")

            QMessageBox.information(
                self,
                "重置成功",
                "主题设置已重置为默认值！\n\n请重启应用以完全生效。"
            )

            self.logger.info("主题设置已重置为默认")

    def get_current_theme(self) -> str:
        """获取当前选择的主题"""
        return self.theme_manager.get_current_theme()
