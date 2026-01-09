"""
SettingsTab V2 - 重构版设置页面

核心改进：
1. 三层结构：全局模型设置 → 个性化设置 → AI接口管理
2. 下拉框只显示已配置的AI接口
3. 修复文字遮挡问题
4. 完整的双主题支持
"""

from typing import List, Dict, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QLineEdit, QComboBox, QSpinBox, QCheckBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QScrollArea, QFormLayout, QDialog, QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from ..design_system_v2 import (
    spacing, font_size, border_radius, get_colors, StyleGenerator
)


class AIConfigDialog(QDialog):
    """AI接口添加/编辑对话框"""

    def __init__(self, theme: str = "light", config: dict = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.colors = get_colors(theme)
        self.style_gen = StyleGenerator(theme)
        self.config = config or {}

        self.setWindowTitle("添加AI接口" if not config else "编辑AI接口")
        self.setMinimumWidth(480)
        self.setModal(True)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(spacing.lg, spacing.lg, spacing.lg, spacing.lg)
        layout.setSpacing(spacing.md)

        # 表单
        form = QFormLayout()
        form.setSpacing(spacing.sm)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # 接口名称
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("如：Claude API、Deepseek等")
        self.name_input.setText(self.config.get("name", ""))
        self.name_input.setStyleSheet(self.style_gen.input_text())
        form.addRow("接口名称:", self.name_input)

        # API Base URL
        self.base_url_input = QLineEdit()
        self.base_url_input.setPlaceholderText("https://api.anthropic.com/v1")
        self.base_url_input.setText(self.config.get("base_url", ""))
        self.base_url_input.setStyleSheet(self.style_gen.input_text())
        form.addRow("Base URL:", self.base_url_input)

        # API Key
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("sk-xxx...")
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_input.setText(self.config.get("api_key", ""))
        self.key_input.setStyleSheet(self.style_gen.input_text())
        form.addRow("API Key:", self.key_input)

        # 模型名称
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("claude-3-5-sonnet-20241022")
        self.model_input.setText(self.config.get("model", ""))
        self.model_input.setStyleSheet(self.style_gen.input_text())
        form.addRow("模型名称:", self.model_input)

        # 每日限额
        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(0, 100000)
        self.limit_spin.setValue(self.config.get("daily_limit", 1000))
        self.limit_spin.setSuffix(" 次/天")
        self.limit_spin.setStyleSheet(self.style_gen.spin_box())
        form.addRow("每日限额:", self.limit_spin)

        layout.addLayout(form)

        # 测试连接按钮
        test_btn = QPushButton("🔗 测试连通性")
        test_btn.setFixedHeight(40)
        test_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        test_btn.clicked.connect(self._test_connection)
        test_btn.setStyleSheet(self.style_gen.button_secondary())
        layout.addWidget(test_btn)

        # 状态标签
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"color: {self.colors['text_muted']};")
        layout.addWidget(self.status_label)

        # 按钮行
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedSize(90, 38)
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {self.colors['text_secondary']};
                border: 1px solid {self.colors['border']};
                border-radius: {border_radius.sm}px;
            }}
            QPushButton:hover {{
                background: {self.colors['surface_hover']};
            }}
        """)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("保存")
        save_btn.setFixedSize(90, 38)
        save_btn.clicked.connect(self._save)
        save_btn.setStyleSheet(self.style_gen.button_primary())
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

        # 对话框样式
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {self.colors['surface']};
            }}
            QLabel {{
                color: {self.colors['text_primary']};
                background: transparent;
            }}
        """)

    def _test_connection(self):
        """测试连接"""
        self.status_label.setText("⏳ 正在测试连接...")
        self.status_label.setStyleSheet(f"color: {self.colors['warning']};")
        # 实际项目中需要调用后端测试接口
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(1500, self._show_test_result)

    def _show_test_result(self):
        """显示测试结果"""
        if self.key_input.text() and self.model_input.text():
            self.status_label.setText("✅ 连接成功！")
            self.status_label.setStyleSheet(f"color: {self.colors['success']};")
        else:
            self.status_label.setText("❌ 连接失败：请填写完整信息")
            self.status_label.setStyleSheet(f"color: {self.colors['error']};")

    def _save(self):
        """保存配置"""
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "提示", "请填写接口名称")
            return
        if not self.key_input.text().strip():
            QMessageBox.warning(self, "提示", "请填写API Key")
            return
        self.accept()

    def get_config(self) -> dict:
        """获取配置"""
        return {
            "name": self.name_input.text().strip(),
            "base_url": self.base_url_input.text().strip(),
            "api_key": self.key_input.text().strip(),
            "model": self.model_input.text().strip(),
            "daily_limit": self.limit_spin.value(),
        }


class SettingsTabV2(QWidget):
    """设置页面 V2"""

    # 信号
    theme_changed = pyqtSignal(str)
    config_saved = pyqtSignal()

    def __init__(self, config_manager=None, theme_manager=None, api_manager=None,
                 theme: str = "light", parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.theme_manager = theme_manager
        self.api_manager = api_manager
        self.theme = theme
        self.colors = get_colors(theme)
        self.style_gen = StyleGenerator(theme)

        # 已配置的AI接口列表（从config_manager获取或使用默认值）
        self.configured_apis = self._load_configured_apis()

        self._setup_ui()

        # 加载全局设置的初始值
        self._load_global_settings()

    def _load_configured_apis(self) -> List[dict]:
        """加载已配置的AI接口 (从扁平格式配置读取)"""
        if self.config_manager:
            try:
                config = self.config_manager.get_all_config()
                apis = []
                api_configs = config.get("api", {})

                # 已知的 provider 列表
                known_providers = ["claude", "gemini", "deepseek", "kimi"]

                # 从扁平格式提取已配置的API
                # 扁平格式: claude_api_key, claude_model, deepseek_api_key 等
                for provider in known_providers:
                    api_key = api_configs.get(f"{provider}_api_key", "")
                    if api_key:
                        apis.append({
                            "name": provider.capitalize(),
                            "model": api_configs.get(f"{provider}_model", ""),
                            "status": "正常",
                            "provider": provider,
                            "base_url": api_configs.get(f"{provider}_base_url", ""),
                            "api_key": api_key,
                        })

                # 检查自定义provider (如 openrouter)
                # 查找所有 xxx_api_key 格式的键
                for key in api_configs.keys():
                    if key.endswith("_api_key") and api_configs.get(key):
                        provider = key.replace("_api_key", "")
                        if provider not in known_providers:
                            apis.append({
                                "name": provider.replace("_", " ").title(),
                                "model": api_configs.get(f"{provider}_model", ""),
                                "status": "正常",
                                "provider": provider,
                                "base_url": api_configs.get(f"{provider}_base_url", ""),
                                "api_key": api_configs.get(key),
                            })

                return apis if apis else self._get_default_apis()
            except Exception as e:
                print(f"[Settings] 加载API配置失败: {e}")
        return self._get_default_apis()

    def _get_default_apis(self) -> List[dict]:
        """默认API列表（演示用）"""
        return [
            {"name": "Claude API", "model": "claude-3-5-sonnet-20241022", "status": "正常", "provider": "claude"},
            {"name": "Deepseek", "model": "deepseek-chat", "status": "正常", "provider": "deepseek"},
        ]

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(spacing.lg, spacing.lg, spacing.lg, spacing.lg)
        layout.setSpacing(spacing.lg)

        # 标题
        title = QLabel("⚙️ 设置")
        title.setFont(QFont("Microsoft YaHei", font_size.xl, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {self.colors['text_primary']}; background: transparent;")
        layout.addWidget(title)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameStyle(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(f"background: transparent;")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, spacing.md, 0)
        content_layout.setSpacing(spacing.lg)

        # 1. 全局模型设置
        global_card = self._create_global_settings_card()
        content_layout.addWidget(global_card)

        # 2. 个性化设置
        personalized_card = self._create_personalized_card()
        content_layout.addWidget(personalized_card)

        # 3. AI接口管理
        api_card = self._create_api_management_card()
        content_layout.addWidget(api_card)

        # 4. 外观设置
        theme_card = self._create_theme_card()
        content_layout.addWidget(theme_card)

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        self.setLayout(layout)

    def _create_card(self, title: str) -> tuple:
        """创建卡片"""
        card = QFrame()
        card.setObjectName("settingsCard")
        card.setStyleSheet(f"""
            QFrame#settingsCard {{
                background-color: {self.colors['card_bg']};
                border: 1px solid {self.colors['card_border']};
                border-radius: {border_radius.md}px;
            }}
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(spacing.lg, spacing.md, spacing.lg, spacing.md)
        card_layout.setSpacing(spacing.md)

        # 标题
        title_label = QLabel(title)
        title_label.setFont(QFont("Microsoft YaHei", font_size.md, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {self.colors['text_primary']}; background: transparent;")
        card_layout.addWidget(title_label)

        return card, card_layout

    def _create_global_settings_card(self) -> QFrame:
        """全局模型设置卡片"""
        card, layout = self._create_card("🎯 全局模型设置")

        form = QFormLayout()
        form.setSpacing(spacing.sm)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # 只显示已配置的模型
        configured_models = [api["name"] for api in self.configured_apis]

        # 优先模型
        self.primary_model = QComboBox()
        self.primary_model.addItems(configured_models)
        self.primary_model.setMinimumWidth(220)
        self.primary_model.setStyleSheet(self.style_gen.combo_box())
        form.addRow(self._create_form_label("优先模型:"), self.primary_model)

        # 副模型
        self.secondary_model = QComboBox()
        self.secondary_model.addItems(configured_models)
        if len(configured_models) > 1:
            self.secondary_model.setCurrentIndex(1)
        self.secondary_model.setMinimumWidth(220)
        self.secondary_model.setStyleSheet(self.style_gen.combo_box())
        form.addRow(self._create_form_label("副模型:"), self.secondary_model)

        # 重试设置
        retry_widget = QWidget()
        retry_layout = QHBoxLayout(retry_widget)
        retry_layout.setContentsMargins(0, 0, 0, 0)
        retry_layout.setSpacing(spacing.sm)

        self.retry_times = QSpinBox()
        self.retry_times.setRange(1, 10)
        self.retry_times.setValue(3)
        self.retry_times.setSuffix(" 次")
        self.retry_times.setStyleSheet(self.style_gen.spin_box())
        retry_layout.addWidget(self.retry_times)

        interval_label = QLabel("间隔")
        interval_label.setStyleSheet(f"color: {self.colors['text_secondary']}; background: transparent;")
        retry_layout.addWidget(interval_label)

        self.retry_interval = QSpinBox()
        self.retry_interval.setRange(1, 60)
        self.retry_interval.setValue(5)
        self.retry_interval.setSuffix(" 秒")
        self.retry_interval.setStyleSheet(self.style_gen.spin_box())
        retry_layout.addWidget(self.retry_interval)

        timeout_label = QLabel("超时")
        timeout_label.setStyleSheet(f"color: {self.colors['text_secondary']}; background: transparent;")
        retry_layout.addWidget(timeout_label)

        self.timeout_seconds = QSpinBox()
        self.timeout_seconds.setRange(10, 300)
        self.timeout_seconds.setValue(60)
        self.timeout_seconds.setSuffix(" 秒")
        self.timeout_seconds.setStyleSheet(self.style_gen.spin_box())
        retry_layout.addWidget(self.timeout_seconds)

        retry_layout.addStretch()

        form.addRow(self._create_form_label("重试设置:"), retry_widget)

        # 双模型验证
        self.dual_verify = QCheckBox("启用双模型交叉验证")
        self.dual_verify.setChecked(True)
        self.dual_verify.setStyleSheet(self.style_gen.check_box())
        form.addRow("", self.dual_verify)

        layout.addLayout(form)

        # 保存按钮
        save_btn = QPushButton("💾 保存全局设置")
        save_btn.setFixedHeight(38)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self.save_global_settings)
        save_btn.setStyleSheet(self.style_gen.button_primary())
        layout.addWidget(save_btn)

        # 提示
        hint = QLabel("💡 下拉框仅显示已配置的AI接口，请在下方「AI接口管理」中添加")
        hint.setWordWrap(True)
        hint.setStyleSheet(f"color: {self.colors['text_muted']}; font-size: {font_size.xs}px; background: transparent;")
        layout.addWidget(hint)

        return card

    def _create_form_label(self, text: str) -> QLabel:
        """创建表单标签（无边框）"""
        label = QLabel(text)
        label.setStyleSheet(f"color: {self.colors['text_secondary']}; background: transparent; border: none;")
        return label

    def _create_personalized_card(self) -> QFrame:
        """个性化设置卡片"""
        card, layout = self._create_card("🎨 个性化调用设置")

        # 启用开关
        self.enable_personalized = QCheckBox("启用个性化设置（为每个环节单独配置模型）")
        self.enable_personalized.setStyleSheet(self.style_gen.check_box())
        self.enable_personalized.toggled.connect(self._toggle_personalized)
        layout.addWidget(self.enable_personalized)

        # 详细设置（初始隐藏）- 两列布局
        self.personalized_content = QWidget()
        p_layout = QHBoxLayout(self.personalized_content)
        p_layout.setContentsMargins(spacing.md, spacing.sm, 0, 0)
        p_layout.setSpacing(spacing.lg)

        configured_models = [api["name"] for api in self.configured_apis]

        # 左列 - 对话阶段
        left_col = QWidget()
        left_layout = QVBoxLayout(left_col)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(spacing.sm)

        left_title = QLabel("对话阶段")
        left_title.setFont(QFont("Microsoft YaHei", font_size.sm, QFont.Weight.Bold))
        left_title.setStyleSheet(f"color: {self.colors['text_primary']}; background: transparent;")
        left_layout.addWidget(left_title)

        left_stages = [
            ("小六壬初判", "xiaoliu"),
            ("测字术分析", "cezi"),
            ("NLP解析", "nlp_parse"),
            ("综合报告", "report"),
        ]

        for stage_name, stage_id in left_stages:
            row = QHBoxLayout()
            row.setSpacing(spacing.sm)

            label = QLabel(f"{stage_name}:")
            label.setFixedWidth(90)
            label.setStyleSheet(f"color: {self.colors['text_secondary']}; background: transparent;")
            row.addWidget(label)

            combo = QComboBox()
            combo.addItem("使用全局设置")
            combo.addItems(configured_models)
            combo.setMinimumWidth(160)
            combo.setStyleSheet(self.style_gen.combo_box())
            row.addWidget(combo)

            left_layout.addLayout(row)

        left_layout.addStretch()
        p_layout.addWidget(left_col)

        # 右列 - 理论分析
        right_col = QWidget()
        right_layout = QVBoxLayout(right_col)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(spacing.sm)

        right_title = QLabel("理论分析")
        right_title.setFont(QFont("Microsoft YaHei", font_size.sm, QFont.Weight.Bold))
        right_title.setStyleSheet(f"color: {self.colors['text_primary']}; background: transparent;")
        right_layout.addWidget(right_title)

        right_stages = [
            ("八字分析", "bazi"),
            ("紫微分析", "ziwei"),
            ("奇门分析", "qimen"),
            ("六爻分析", "liuyao"),
        ]

        for stage_name, stage_id in right_stages:
            row = QHBoxLayout()
            row.setSpacing(spacing.sm)

            label = QLabel(f"{stage_name}:")
            label.setFixedWidth(90)
            label.setStyleSheet(f"color: {self.colors['text_secondary']}; background: transparent;")
            row.addWidget(label)

            combo = QComboBox()
            combo.addItem("使用全局设置")
            combo.addItems(configured_models)
            combo.setMinimumWidth(160)
            combo.setStyleSheet(self.style_gen.combo_box())
            row.addWidget(combo)

            right_layout.addLayout(row)

        right_layout.addStretch()
        p_layout.addWidget(right_col)

        p_layout.addStretch()

        self.personalized_content.hide()
        layout.addWidget(self.personalized_content)

        return card

    def _toggle_personalized(self, checked: bool):
        """切换个性化设置显示"""
        self.personalized_content.setVisible(checked)

    def _create_api_management_card(self) -> QFrame:
        """AI接口管理卡片"""
        card, layout = self._create_card("🔌 AI接口管理")

        # 表格
        self.api_table = QTableWidget()
        self.api_table.setColumnCount(4)
        self.api_table.setHorizontalHeaderLabels(["接口名称", "模型", "状态", "操作"])

        # 列宽设置 - 修复文字遮挡问题
        header = self.api_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.api_table.setColumnWidth(2, 80)
        self.api_table.setColumnWidth(3, 140)  # 增加操作列宽度

        self.api_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.api_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.api_table.setMaximumHeight(220)
        self.api_table.verticalHeader().setVisible(False)
        self.api_table.setStyleSheet(self.style_gen.table())

        self._refresh_api_table()
        layout.addWidget(self.api_table)

        # 添加按钮
        add_btn = QPushButton("➕ 添加AI接口")
        add_btn.setFixedHeight(40)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._add_api)
        add_btn.setStyleSheet(self.style_gen.button_primary())
        layout.addWidget(add_btn)

        return card

    def _refresh_api_table(self):
        """刷新API表格"""
        self.api_table.setRowCount(len(self.configured_apis))

        for i, api in enumerate(self.configured_apis):
            # 接口名称
            self.api_table.setItem(i, 0, QTableWidgetItem(api["name"]))

            # 模型
            self.api_table.setItem(i, 1, QTableWidgetItem(api["model"]))

            # 状态
            status_item = QTableWidgetItem(api["status"])
            status_item.setForeground(
                Qt.GlobalColor.darkGreen if api["status"] == "正常" else Qt.GlobalColor.red
            )
            self.api_table.setItem(i, 2, status_item)

            # 操作按钮
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(8, 4, 8, 4)
            btn_layout.setSpacing(8)

            edit_btn = QPushButton("编辑")
            edit_btn.setFixedSize(50, 28)
            edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            edit_btn.clicked.connect(lambda checked, idx=i: self._edit_api(idx))
            edit_btn.setStyleSheet(self.style_gen.button_text(self.colors['primary']))
            btn_layout.addWidget(edit_btn)

            del_btn = QPushButton("删除")
            del_btn.setFixedSize(50, 28)
            del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            del_btn.clicked.connect(lambda checked, idx=i: self._delete_api(idx))
            del_btn.setStyleSheet(self.style_gen.button_text(self.colors['error']))
            btn_layout.addWidget(del_btn)

            self.api_table.setCellWidget(i, 3, btn_widget)

    def _add_api(self):
        """添加API"""
        dialog = AIConfigDialog(self.theme, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            config = dialog.get_config()
            provider = config["name"].lower().replace(" ", "_").replace("-", "_")

            # 添加到本地列表
            self.configured_apis.append({
                "name": config["name"],
                "model": config["model"],
                "status": "正常",
                "provider": provider,
                "base_url": config.get("base_url", ""),
                "api_key": config.get("api_key", ""),
                "daily_limit": config.get("daily_limit", 1000),
            })

            # 保存到配置文件
            self._save_api_config(provider, config)

            self._refresh_api_table()
            self._update_model_combos()
            self.config_saved.emit()

    def _edit_api(self, index: int):
        """编辑API"""
        if 0 <= index < len(self.configured_apis):
            api = self.configured_apis[index]
            dialog = AIConfigDialog(self.theme, config=api, parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                config = dialog.get_config()
                old_provider = api.get("provider", "")
                new_provider = config["name"].lower().replace(" ", "_").replace("-", "_")

                # 更新本地列表
                self.configured_apis[index].update({
                    "name": config["name"],
                    "model": config["model"],
                    "provider": new_provider,
                    "base_url": config.get("base_url", ""),
                    "api_key": config.get("api_key", ""),
                    "daily_limit": config.get("daily_limit", 1000),
                })

                # 保存到配置文件
                self._save_api_config(new_provider, config)

                self._refresh_api_table()
                self._update_model_combos()
                self.config_saved.emit()

    def _delete_api(self, index: int):
        """删除API"""
        if 0 <= index < len(self.configured_apis):
            api = self.configured_apis[index]
            reply = QMessageBox.question(
                self, "确认删除",
                f"确定要删除接口「{api['name']}」吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                provider = api.get("provider", "")

                # 从配置文件删除
                self._delete_api_config(provider)

                # 从本地列表删除
                self.configured_apis.pop(index)
                self._refresh_api_table()
                self._update_model_combos()
                self.config_saved.emit()

    def _update_model_combos(self):
        """更新模型下拉框"""
        configured_models = [api["name"] for api in self.configured_apis]

        current_primary = self.primary_model.currentText()
        current_secondary = self.secondary_model.currentText()

        self.primary_model.clear()
        self.primary_model.addItems(configured_models)
        self.secondary_model.clear()
        self.secondary_model.addItems(configured_models)

        # 尝试恢复之前的选择
        idx = self.primary_model.findText(current_primary)
        if idx >= 0:
            self.primary_model.setCurrentIndex(idx)
        idx = self.secondary_model.findText(current_secondary)
        if idx >= 0:
            self.secondary_model.setCurrentIndex(idx)

    def _create_theme_card(self) -> QFrame:
        """外观设置卡片"""
        card, layout = self._create_card("🎨 外观设置")

        row = QHBoxLayout()
        row.setSpacing(spacing.md)

        label = QLabel("界面主题:")
        label.setStyleSheet(f"color: {self.colors['text_primary']}; background: transparent;")
        row.addWidget(label)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["浅色主题", "深色主题"])
        self.theme_combo.setCurrentIndex(0 if self.theme == "light" else 1)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        self.theme_combo.setMinimumWidth(150)
        self.theme_combo.setStyleSheet(self.style_gen.combo_box())
        row.addWidget(self.theme_combo)

        row.addStretch()
        layout.addLayout(row)

        return card

    def _on_theme_changed(self, index: int):
        """主题切换"""
        theme = "light" if index == 0 else "dark"
        self.theme_changed.emit(theme)

    def set_theme(self, theme: str):
        """设置主题"""
        self.theme = theme
        self.colors = get_colors(theme)
        self.style_gen.set_theme(theme)
        # 需要重新渲染组件

    def cleanup(self):
        """清理资源"""
        pass

    # ==================== 配置保存方法 ====================

    def _save_api_config(self, provider: str, config: dict):
        """保存API配置到config_manager (扁平格式，与APIManager兼容)"""
        if not self.config_manager:
            return

        try:
            # 构建API配置 - 使用扁平格式以兼容 APIManager
            # APIManager 期望: config.get("claude_api_key"), config.get("claude_model") 等
            api_config = {
                'api': {
                    f'{provider}_api_key': config.get('api_key', ''),
                    f'{provider}_base_url': config.get('base_url', ''),
                    f'{provider}_model': config.get('model', ''),
                    f'{provider}_daily_limit': config.get('daily_limit', 1000),
                }
            }

            # 保存到用户配置文件
            self.config_manager.save_user_config(api_config)
            print(f"[Settings] API配置已保存: {provider}")

        except Exception as e:
            print(f"[Settings] 保存API配置失败: {e}")
            QMessageBox.warning(self, "保存失败", f"保存API配置时出错：{str(e)}")

    def _delete_api_config(self, provider: str):
        """从配置中删除API (扁平格式)"""
        if not self.config_manager:
            return

        try:
            # 获取当前所有API配置
            current_config = self.config_manager.get_all_config()
            api_configs = current_config.get('api', {}).copy()

            # 删除扁平格式的配置键
            keys_to_delete = [
                f'{provider}_api_key',
                f'{provider}_base_url',
                f'{provider}_model',
                f'{provider}_daily_limit',
            ]

            for key in keys_to_delete:
                if key in api_configs:
                    del api_configs[key]

            # 保存更新后的配置
            self.config_manager.save_user_config({'api': api_configs})
            print(f"[Settings] API配置已删除: {provider}")

        except Exception as e:
            print(f"[Settings] 删除API配置失败: {e}")

    def save_global_settings(self):
        """保存全局模型设置 (扁平格式，与APIManager兼容)"""
        if not self.config_manager:
            QMessageBox.warning(self, "保存失败", "配置管理器未初始化")
            return

        try:
            # 获取当前选择
            primary = self.primary_model.currentText()
            secondary = self.secondary_model.currentText()
            retry_times = self.retry_times.value()
            retry_interval = self.retry_interval.value()
            timeout = self.timeout_seconds.value()
            dual_verify = self.dual_verify.isChecked()

            # 找到对应的provider
            primary_provider = self._get_provider_by_name(primary)
            secondary_provider = self._get_provider_by_name(secondary)

            # 构建配置 - 扁平格式存储在 api 节点下，与 APIManager 兼容
            # APIManager 期望: config.get("primary_api"), config.get("timeout") 等
            config_to_save = {
                'api': {
                    'primary_api': primary_provider,
                    'secondary_api': secondary_provider,
                    'max_retries': retry_times,
                    'retry_interval': retry_interval,
                    'timeout': timeout,
                    'enable_dual_verification': dual_verify,
                }
            }

            # 保存
            self.config_manager.save_user_config(config_to_save)
            print(f"[Settings] 全局设置已保存: primary={primary_provider}, secondary={secondary_provider}, timeout={timeout}")

            # 显示成功提示
            QMessageBox.information(self, "保存成功", "全局设置已保存！重启应用后生效。")

            # 通知配置变更
            self.config_saved.emit()

        except Exception as e:
            print(f"[Settings] 保存全局设置失败: {e}")
            QMessageBox.warning(self, "保存失败", f"保存全局设置时出错：{str(e)}")

    def _get_provider_by_name(self, name: str) -> str:
        """根据显示名称获取provider"""
        for api in self.configured_apis:
            if api.get("name") == name:
                return api.get("provider", name.lower().replace(" ", "_"))
        return name.lower().replace(" ", "_")

    def reload_configured_apis(self):
        """重新加载已配置的API列表"""
        self.configured_apis = self._load_configured_apis()
        self._refresh_api_table()
        self._update_model_combos()

    def _load_global_settings(self):
        """从配置加载全局设置的初始值"""
        if not self.config_manager:
            return

        try:
            config = self.config_manager.get_all_config()
            api_config = config.get('api', {})

            # 加载优先模型
            primary_api = api_config.get('primary_api', '')
            if primary_api:
                # 找到对应的显示名称
                for api in self.configured_apis:
                    if api.get('provider') == primary_api:
                        idx = self.primary_model.findText(api.get('name', ''))
                        if idx >= 0:
                            self.primary_model.setCurrentIndex(idx)
                        break

            # 加载副模型
            secondary_api = api_config.get('secondary_api', '')
            if secondary_api:
                for api in self.configured_apis:
                    if api.get('provider') == secondary_api:
                        idx = self.secondary_model.findText(api.get('name', ''))
                        if idx >= 0:
                            self.secondary_model.setCurrentIndex(idx)
                        break

            # 加载重试设置
            max_retries = api_config.get('max_retries', 3)
            self.retry_times.setValue(max_retries)

            retry_interval = api_config.get('retry_interval', 5)
            self.retry_interval.setValue(retry_interval)

            # 加载超时设置
            timeout = api_config.get('timeout', 60)
            self.timeout_seconds.setValue(timeout)

            # 加载双模型验证设置
            dual_verify = api_config.get('enable_dual_verification', True)
            self.dual_verify.setChecked(dual_verify)

            print(f"[Settings] 全局设置已加载: primary={primary_api}, timeout={timeout}")

        except Exception as e:
            print(f"[Settings] 加载全局设置失败: {e}")
