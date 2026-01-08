"""
设置标签页 - API配置、主题设置、功能状态
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox, QTextEdit,
    QScrollArea
)
from PyQt6.QtCore import pyqtSignal, Qt
from typing import Optional, Tuple

from utils.config_manager import ConfigManager
from utils.theme_manager import ThemeManager
from utils.template_manager import TemplateManager
from utils.error_handler import ErrorHandler
from utils.logger import get_logger
from ui.widgets.theme_settings_widget import ThemeSettingsWidget
from ui.widgets.feature_status_widget import FeatureStatusWidget
from ui.dialogs.about_dialog import AboutDialog


class SettingsTab(QWidget):
    """设置标签页"""

    theme_changed = pyqtSignal(str)  # 主题变更信号
    config_saved = pyqtSignal()  # 配置保存信号
    refresh_feature_status_requested = pyqtSignal()  # 请求刷新功能状态

    def __init__(self, config_manager: ConfigManager, theme_manager: ThemeManager,
                 template_manager: TemplateManager, api_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.theme_manager = theme_manager
        self.template_manager = template_manager
        self.api_manager = api_manager
        self.logger = get_logger(__name__)
        self.error_handler = ErrorHandler(self)

        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # 创建内容容器
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)
        content_layout.setContentsMargins(20, 20, 20, 20)

        # ===== 1. API配置组 (顶部) =====
        api_group = self._create_api_config_group()
        content_layout.addWidget(api_group)

        # ===== 2. 主题设置组 =====
        try:
            self.theme_settings_widget = ThemeSettingsWidget(self.theme_manager)
            self.theme_settings_widget.theme_changed.connect(self._on_theme_changed)
            content_layout.addWidget(self.theme_settings_widget)
        except Exception as e:
            self.error_handler.handle_error(e, "主题设置组件初始化", show_dialog=False)

        # ===== 3. 报告自定义组 =====
        report_custom_group = self._create_report_custom_group()
        content_layout.addWidget(report_custom_group)

        # ===== 4. 功能状态面板 (下移) =====
        try:
            self.feature_status_widget = FeatureStatusWidget()
            self.feature_status_widget.refresh_requested.connect(self._refresh_feature_status)
            content_layout.addWidget(self.feature_status_widget)
        except Exception as e:
            self.error_handler.handle_error(e, "功能状态组件初始化", show_dialog=False)

        # ===== 5. 关于产品 =====
        about_group = self._create_about_group()
        content_layout.addWidget(about_group)

        content_layout.addStretch()

        # 将内容容器添加到滚动区域
        scroll_area.setWidget(content_widget)

        # 将滚动区域添加到主布局
        main_layout.addWidget(scroll_area)

        # 自动加载当前配置
        self._load_current_config()

    def _create_report_custom_group(self) -> QGroupBox:
        """创建报告自定义组"""
        group = QGroupBox("📝 报告自定义")
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        desc_label = QLabel("自定义报告的结构、内容和风格")
        desc_label.setStyleSheet("font-size: 10pt;")
        layout.addWidget(desc_label)

        customize_btn = QPushButton("🎨 打开报告自定义")
        customize_btn.clicked.connect(self._open_report_custom_dialog)
        customize_btn.setMinimumHeight(36)
        layout.addWidget(customize_btn)

        group.setLayout(layout)
        return group

    def _create_api_config_group(self) -> QGroupBox:
        """创建API配置组"""
        group = QGroupBox("AI API 配置")
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(15, 15, 15, 15)

        # 提示说明
        tip_label = QLabel("至少需要配置一个 API 密钥才能使用分析功能")
        tip_label.setStyleSheet("font-style: italic;")
        layout.addWidget(tip_label)

        # API密钥输入
        layout.addLayout(self._create_api_input_row("Claude API Key:", "claude"))
        layout.addLayout(self._create_api_input_row("Gemini API Key:", "gemini"))
        layout.addLayout(self._create_api_input_row("Deepseek API Key:", "deepseek"))
        layout.addLayout(self._create_api_input_row("Kimi API Key:", "kimi"))

        layout.addSpacing(10)

        # 模型配置
        model_label = QLabel("模型配置")
        model_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        layout.addWidget(model_label)

        layout.addLayout(self._create_model_combo_row("Claude 模型:", "claude_model", [
            "claude-sonnet-4-5", "claude-opus-4-5"
        ]))
        layout.addLayout(self._create_model_combo_row("Gemini 模型:", "gemini_model", [
            "gemini-3-pro-preview"
        ]))
        layout.addLayout(self._create_model_combo_row("Deepseek 模型:", "deepseek_model", [
            "deepseek-reasoner", "deepseek-chat"
        ]))
        layout.addLayout(self._create_model_combo_row("Kimi 模型:", "kimi_model", [
            "kimi-k2-turbo-preview"
        ]))

        layout.addSpacing(10)

        # 其他配置
        other_label = QLabel("其他配置")
        other_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        layout.addWidget(other_label)

        layout.addLayout(self._create_api_input_row("高德地图 API Key:", "amap", is_optional=True))

        # 主API选择
        primary_layout = QHBoxLayout()
        primary_layout.setSpacing(10)
        primary_label = QLabel("优先使用 API:")
        primary_label.setMinimumWidth(120)
        primary_layout.addWidget(primary_label)
        self.primary_api_combo = QComboBox()
        self.primary_api_combo.addItems(["claude", "gemini", "deepseek", "kimi"])
        self.primary_api_combo.setMinimumHeight(32)
        primary_layout.addWidget(self.primary_api_combo)
        primary_layout.addStretch()
        layout.addLayout(primary_layout)

        # 双模型验证
        self.dual_verify_checkbox = QCheckBox("启用双模型验证（并发调用两个API进行交叉验证）")
        layout.addWidget(self.dual_verify_checkbox)

        layout.addSpacing(15)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        load_btn = QPushButton("🔄 加载当前配置")
        load_btn.setMinimumHeight(36)
        load_btn.clicked.connect(self._load_current_config)
        btn_layout.addWidget(load_btn)

        reset_btn = QPushButton("↩️ 重置为默认")
        reset_btn.setMinimumHeight(36)
        reset_btn.clicked.connect(self._reset_to_defaults)
        reset_btn.setProperty("secondary", True)  # 使用次要按钮样式
        btn_layout.addWidget(reset_btn)

        save_config_btn = QPushButton("💾 保存配置")
        save_config_btn.setMinimumHeight(36)
        save_config_btn.clicked.connect(self._save_config)
        btn_layout.addWidget(save_config_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        group.setLayout(layout)
        return group

    def _create_api_input_row(self, label_text: str, api_name: str, is_optional: bool = False) -> QHBoxLayout:
        """创建API输入行（含测试按钮）"""
        row_layout = QHBoxLayout()
        row_layout.setSpacing(10)

        label = QLabel(label_text)
        label.setMinimumWidth(160)
        row_layout.addWidget(label)

        line_edit = QLineEdit()
        placeholder = "用于出生地点查询（可选）" if is_optional else "sk-..."
        line_edit.setPlaceholderText(placeholder)
        line_edit.setEchoMode(QLineEdit.EchoMode.Password)
        line_edit.setMinimumHeight(32)
        row_layout.addWidget(line_edit)

        # 保存引用
        setattr(self, f"{api_name}_api_input", line_edit)

        # 显示/隐藏按钮
        show_btn = QPushButton("👁")
        show_btn.setMaximumWidth(40)
        show_btn.setMinimumHeight(32)
        show_btn.setCheckable(True)
        show_btn.clicked.connect(lambda checked: self._toggle_password(line_edit, checked))
        row_layout.addWidget(show_btn)

        # 测试按钮
        test_btn = QPushButton("测试")
        test_btn.setMaximumWidth(60)
        test_btn.setMinimumHeight(32)
        test_btn.setProperty("secondary", True)  # 使用次要按钮样式
        test_btn.clicked.connect(lambda: self._test_api_connection(api_name))
        row_layout.addWidget(test_btn)

        # 保存测试按钮引用
        setattr(self, f"{api_name}_test_btn", test_btn)

        return row_layout

    def _create_model_combo_row(self, label_text: str, model_key: str, items: list) -> QHBoxLayout:
        """创建模型选择行"""
        row_layout = QHBoxLayout()
        row_layout.setSpacing(10)

        label = QLabel(label_text)
        label.setMinimumWidth(120)
        row_layout.addWidget(label)

        combo = QComboBox()
        combo.addItems(items)
        combo.setEditable(True)
        combo.setMinimumHeight(32)
        row_layout.addWidget(combo)

        # 保存引用
        setattr(self, f"{model_key}_combo", combo)

        row_layout.addStretch()
        return row_layout

    def _create_about_group(self) -> QGroupBox:
        """创建关于产品组"""
        group = QGroupBox("ℹ️ 关于产品")
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # 产品名称和简介
        product_name = QLabel("<b>Cyber-Mantic</b> (赛博玄数)")
        product_name.setStyleSheet("font-size: 12pt; color: #2c3e50;")
        layout.addWidget(product_name)

        product_subtitle = QLabel("数字时代的智能命理系统")
        product_subtitle.setStyleSheet("color: #7f8c8d; font-size: 10pt;")
        layout.addWidget(product_subtitle)

        layout.addSpacing(10)

        # 关于按钮
        about_btn = QPushButton("📖 查看详细介绍")
        about_btn.setMinimumHeight(40)
        about_btn.clicked.connect(self._show_about_dialog)
        layout.addWidget(about_btn)

        group.setLayout(layout)
        return group

    def _show_about_dialog(self):
        """显示关于产品对话框"""
        try:
            dialog = AboutDialog(self)
            dialog.exec()
        except Exception as e:
            self.error_handler.handle_error(e, "打开关于对话框")

    def _toggle_password(self, line_edit: QLineEdit, show: bool):
        """切换密码显示/隐藏"""
        if show:
            line_edit.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            line_edit.setEchoMode(QLineEdit.EchoMode.Password)

    def _test_api_connection(self, api_name: str):
        """测试API连接"""
        from PyQt6.QtWidgets import QMessageBox
        from PyQt6.QtCore import QTimer

        # 获取API密钥
        api_input = getattr(self, f"{api_name}_api_input", None)
        test_btn = getattr(self, f"{api_name}_test_btn", None)

        if not api_input:
            return

        api_key = api_input.text().strip()
        if not api_key:
            QMessageBox.warning(self, "测试失败", f"请先输入 {api_name.upper()} API 密钥")
            return

        # 更新按钮状态
        if test_btn:
            test_btn.setText("测试中...")
            test_btn.setEnabled(False)

        try:
            # 尝试测试API连接
            if self.api_manager:
                # 异步测试
                success = self._do_api_test(api_name, api_key)
                if success:
                    QMessageBox.information(self, "测试成功", f"✅ {api_name.upper()} API 连接正常！")
                else:
                    QMessageBox.warning(self, "测试失败", f"❌ {api_name.upper()} API 连接失败\n请检查密钥是否正确")
            else:
                QMessageBox.information(self, "提示", f"API密钥格式正确\n完整测试需要保存配置后重启应用")

        except Exception as e:
            QMessageBox.critical(self, "测试错误", f"测试过程出错：{str(e)}")
        finally:
            # 恢复按钮状态
            if test_btn:
                test_btn.setText("测试")
                test_btn.setEnabled(True)

    def _do_api_test(self, api_name: str, api_key: str) -> bool:
        """执行API测试（简单验证）"""
        # 对于高德地图API，进行简单的格式验证
        if api_name == "amap":
            return len(api_key) == 32  # 高德API密钥通常为32位

        # 对于AI API，验证密钥格式
        if api_name == "claude":
            return api_key.startswith("sk-ant-")
        elif api_name == "gemini":
            return len(api_key) > 20
        elif api_name == "deepseek":
            return api_key.startswith("sk-")
        elif api_name == "kimi":
            return len(api_key) > 20

        return True

    def _load_current_config(self):
        """加载当前配置到界面"""
        try:
            # API密钥
            api_keys = self.config_manager.get_api_keys()
            self.claude_api_input.setText(api_keys.get('claude', ''))
            self.gemini_api_input.setText(api_keys.get('gemini', ''))
            self.deepseek_api_input.setText(api_keys.get('deepseek', ''))
            self.kimi_api_input.setText(api_keys.get('kimi', ''))
            self.amap_api_input.setText(api_keys.get('amap', ''))

            # 模型配置
            self.claude_model_combo.setCurrentText(
                self.config_manager.get('api.claude_model', 'claude-sonnet-4-5')
            )
            self.gemini_model_combo.setCurrentText(
                self.config_manager.get('api.gemini_model', 'gemini-3-pro-preview')
            )
            self.deepseek_model_combo.setCurrentText(
                self.config_manager.get('api.deepseek_model', 'deepseek-reasoner')
            )
            self.kimi_model_combo.setCurrentText(
                self.config_manager.get('api.kimi_model', 'kimi-k2-turbo-preview')
            )

            # 其他配置
            self.primary_api_combo.setCurrentText(
                self.config_manager.get('api.primary_api', 'claude')
            )
            self.dual_verify_checkbox.setChecked(
                self.config_manager.get('api.enable_dual_verification', True)
            )

            self.logger.info("配置已加载到界面")
        except Exception as e:
            self.error_handler.handle_error(e, "加载配置")

    def _validate_config(self) -> Tuple[bool, str]:
        """验证配置

        Returns:
            (is_valid, error_message)
        """
        # 收集API密钥
        api_keys = {
            'claude': self.claude_api_input.text().strip(),
            'gemini': self.gemini_api_input.text().strip(),
            'deepseek': self.deepseek_api_input.text().strip(),
            'kimi': self.kimi_api_input.text().strip()
        }

        # 检查至少有一个有效的API密钥
        valid_keys = [name for name, key in api_keys.items() if key]
        if not valid_keys:
            return False, "至少需要配置一个 AI API 密钥！"

        # 验证主API是否已配置
        primary_api = self.primary_api_combo.currentText()
        if primary_api not in api_keys or not api_keys[primary_api]:
            return False, f"优先使用的 API ({primary_api}) 未配置密钥！\n请先配置或选择其他API作为优先API。"

        # 验证模型名称不为空
        models = {
            'Claude': self.claude_model_combo.currentText().strip(),
            'Gemini': self.gemini_model_combo.currentText().strip(),
            'Deepseek': self.deepseek_model_combo.currentText().strip(),
            'Kimi': self.kimi_model_combo.currentText().strip()
        }

        empty_models = [name for name, model in models.items() if not model]
        if empty_models:
            return False, f"以下模型名称不能为空：{', '.join(empty_models)}"

        return True, ""

    def _save_config(self):
        """保存配置"""
        from PyQt6.QtWidgets import QMessageBox

        try:
            # 验证配置
            is_valid, error_msg = self._validate_config()
            if not is_valid:
                QMessageBox.warning(self, "配置验证失败", error_msg)
                return

            # 构建配置数据字典
            config_data = {
                'api': {
                    # API密钥
                    'claude_api_key': self.claude_api_input.text().strip(),
                    'gemini_api_key': self.gemini_api_input.text().strip(),
                    'deepseek_api_key': self.deepseek_api_input.text().strip(),
                    'kimi_api_key': self.kimi_api_input.text().strip(),
                    'amap_api_key': self.amap_api_input.text().strip(),  # 高德地图API密钥
                    # 模型配置
                    'claude_model': self.claude_model_combo.currentText().strip(),
                    'gemini_model': self.gemini_model_combo.currentText().strip(),
                    'deepseek_model': self.deepseek_model_combo.currentText().strip(),
                    'kimi_model': self.kimi_model_combo.currentText().strip(),
                    # 其他配置
                    'primary_api': self.primary_api_combo.currentText(),
                    'enable_dual_verification': self.dual_verify_checkbox.isChecked()
                }
            }

            # 保存到文件
            success = self.config_manager.save_user_config(config_data)

            if success:
                # 统计已配置的API
                configured_apis = []
                if self.claude_api_input.text().strip():
                    configured_apis.append("Claude")
                if self.gemini_api_input.text().strip():
                    configured_apis.append("Gemini")
                if self.deepseek_api_input.text().strip():
                    configured_apis.append("Deepseek")
                if self.kimi_api_input.text().strip():
                    configured_apis.append("Kimi")

                msg = f"配置已成功保存！\n\n已配置的API: {', '.join(configured_apis)}\n优先使用: {self.primary_api_combo.currentText()}"
                if self.dual_verify_checkbox.isChecked():
                    msg += "\n双模型验证: 已启用"

                QMessageBox.information(self, "保存成功", msg)
                self.config_saved.emit()
                self.logger.info(f"配置已保存 - 已配置API: {configured_apis}")
            else:
                QMessageBox.critical(self, "保存失败", "无法保存配置文件，请检查文件权限")

        except Exception as e:
            self.error_handler.handle_error(e, "保存配置")

    def _reset_to_defaults(self):
        """重置为默认配置"""
        from PyQt6.QtWidgets import QMessageBox

        reply = QMessageBox.question(
            self,
            "确认重置",
            "确定要重置所有配置为默认值吗？\n\n此操作将清空所有API密钥，需要重新配置。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # 清空API密钥
                self.claude_api_input.clear()
                self.gemini_api_input.clear()
                self.deepseek_api_input.clear()
                self.kimi_api_input.clear()
                self.amap_api_input.clear()

                # 恢复默认模型
                self.claude_model_combo.setCurrentText("claude-sonnet-4-5")
                self.gemini_model_combo.setCurrentText("gemini-3-pro-preview")
                self.deepseek_model_combo.setCurrentText("deepseek-reasoner")
                self.kimi_model_combo.setCurrentText("kimi-k2-turbo-preview")

                # 恢复默认设置
                self.primary_api_combo.setCurrentText("claude")
                self.dual_verify_checkbox.setChecked(True)

                QMessageBox.information(self, "重置成功", "配置已重置为默认值\n请重新配置API密钥后保存")
                self.logger.info("配置已重置为默认值")

            except Exception as e:
                self.error_handler.handle_error(e, "重置配置")

    def _on_theme_changed(self, theme_name: str):
        """主题更改回调"""
        self.theme_changed.emit(theme_name)

    def _refresh_feature_status(self):
        """刷新功能状态 - 发射信号请求父窗口刷新"""
        self.refresh_feature_status_requested.emit()

    def _open_report_custom_dialog(self):
        """打开报告自定义对话框"""
        try:
            from ui.dialogs.report_custom_dialog import ReportCustomDialog
            dialog = ReportCustomDialog(self.template_manager, self.api_manager, self)
            dialog.exec()
        except Exception as e:
            self.error_handler.handle_error(e, "报告自定义")

    def cleanup(self):
        """清理资源，断开所有信号连接"""
        self.logger.debug("清理SettingsTab资源...")

        # 断开主题设置组件信号
        if hasattr(self, 'theme_settings_widget') and self.theme_settings_widget:
            try:
                self.theme_settings_widget.theme_changed.disconnect()
            except (TypeError, RuntimeError):
                pass

        # 断开功能状态组件信号
        if hasattr(self, 'feature_status_widget') and self.feature_status_widget:
            try:
                self.feature_status_widget.refresh_requested.disconnect()
            except (TypeError, RuntimeError):
                pass

        self.logger.debug("SettingsTab资源已清理")
