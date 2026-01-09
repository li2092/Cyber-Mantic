"""
APISettingsWidget - API设置界面

V2核心组件：提供全局和环节级API配置UI
- 全局配置：主API、备选顺序、双模型验证
- 环节配置：每个任务可单独配置API
- 连接测试：测试各API连通性
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QGroupBox, QFormLayout, QLineEdit, QCheckBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QTabWidget, QScrollArea, QFrame, QSpinBox, QDoubleSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont
from typing import Dict, Any, Optional, List
import asyncio


class APITestWorker(QThread):
    """API连接测试工作线程"""

    test_completed = pyqtSignal(str, bool, str)  # (api_name, success, message)

    def __init__(self, api_name: str, api_key: str, model: str, parent=None):
        super().__init__(parent)
        self.api_name = api_name
        self.api_key = api_key
        self.model = model

    def run(self):
        """执行API测试"""
        try:
            # 简单的连接测试
            import httpx

            # 根据API类型选择测试方式
            success, message = self._test_api()
            self.test_completed.emit(self.api_name, success, message)

        except Exception as e:
            self.test_completed.emit(self.api_name, False, str(e))

    def _test_api(self):
        """测试API连接"""
        try:
            import openai

            # 获取API配置
            configs = {
                "claude": ("https://api.anthropic.com/v1/messages", None),
                "deepseek": ("https://api.deepseek.com", None),
                "kimi": ("https://api.moonshot.cn/v1", None),
                "gemini": (None, None),  # Gemini使用不同的库
                "qwen": ("https://dashscope.aliyuncs.com/compatible-mode/v1", None),
                "doubao": ("https://ark.cn-beijing.volces.com/api/v3", None),
                "baichuan": ("https://api.baichuan-ai.com/v1", None),
                "glm": ("https://open.bigmodel.cn/api/paas/v4", None),
                "openrouter": ("https://openrouter.ai/api/v1", None),
            }

            base_url, _ = configs.get(self.api_name, (None, None))

            if base_url:
                # 使用OpenAI兼容接口测试
                client = openai.OpenAI(
                    api_key=self.api_key,
                    base_url=base_url
                )
                # 发送简单请求
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": "测试"}],
                    max_tokens=5,
                    timeout=10
                )
                return True, f"连接成功 - 模型: {self.model}"
            else:
                return False, "不支持的API类型"

        except Exception as e:
            return False, f"连接失败: {str(e)[:100]}"


class GlobalAPISettings(QGroupBox):
    """全局API设置"""

    settings_changed = pyqtSignal()

    def __init__(self, theme: str = "dark", parent=None):
        super().__init__("全局配置", parent)
        self.theme = theme
        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        layout = QFormLayout()
        layout.setSpacing(12)

        # 主API选择
        self.primary_combo = QComboBox()
        self.primary_combo.addItems([
            "claude", "deepseek", "kimi", "gemini",
            "qwen", "doubao", "baichuan", "glm", "openrouter"
        ])
        self.primary_combo.currentTextChanged.connect(self._on_change)
        layout.addRow("主API:", self.primary_combo)

        # 双模型验证
        self.dual_verify_check = QCheckBox("启用双模型验证")
        self.dual_verify_check.stateChanged.connect(self._on_change)
        layout.addRow("", self.dual_verify_check)

        # 超时设置
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(10, 300)
        self.timeout_spin.setValue(60)
        self.timeout_spin.setSuffix(" 秒")
        self.timeout_spin.valueChanged.connect(self._on_change)
        layout.addRow("请求超时:", self.timeout_spin)

        # 最大重试
        self.retry_spin = QSpinBox()
        self.retry_spin.setRange(0, 5)
        self.retry_spin.setValue(3)
        self.retry_spin.valueChanged.connect(self._on_change)
        layout.addRow("最大重试:", self.retry_spin)

        self.setLayout(layout)

    def _on_change(self):
        self.settings_changed.emit()

    def get_settings(self) -> Dict[str, Any]:
        """获取设置"""
        return {
            "primary": self.primary_combo.currentText(),
            "enable_dual_verification": self.dual_verify_check.isChecked(),
            "timeout": self.timeout_spin.value(),
            "max_retries": self.retry_spin.value()
        }

    def set_settings(self, settings: Dict[str, Any]):
        """设置配置"""
        if "primary" in settings:
            idx = self.primary_combo.findText(settings["primary"])
            if idx >= 0:
                self.primary_combo.setCurrentIndex(idx)
        if "enable_dual_verification" in settings:
            self.dual_verify_check.setChecked(settings["enable_dual_verification"])
        if "timeout" in settings:
            self.timeout_spin.setValue(settings["timeout"])
        if "max_retries" in settings:
            self.retry_spin.setValue(settings["max_retries"])


class TaskAPISettings(QGroupBox):
    """任务级API设置"""

    settings_changed = pyqtSignal()

    # 任务类型列表
    TASK_TYPES = [
        ("综合报告解读", "生成最终报告"),
        ("单理论解读", "单个理论的AI解读"),
        ("快速交互问答", "对话中的快速问答"),
        ("出生信息解析", "解析用户输入的出生信息"),
        ("冲突解决分析", "理论冲突时的深度分析"),
        ("回溯验证生成", "生成验证问题"),
        ("输入增强验证", "AI增强验证（时辰分析/问题识别/吉凶提取等）"),
    ]

    def __init__(self, theme: str = "dark", parent=None):
        super().__init__("环节配置", parent)
        self.theme = theme
        self.task_combos: Dict[str, QComboBox] = {}
        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        is_dark = self.theme == "dark"
        desc_color = "#94A3B8" if is_dark else "#64748B"

        layout = QVBoxLayout()
        layout.setSpacing(8)

        # 说明
        desc = QLabel("为不同任务环节配置不同的API（留空表示使用全局配置）")
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {desc_color}; font-size: 12px;")
        layout.addWidget(desc)

        # 任务配置表格
        for task_type, description in self.TASK_TYPES:
            row_layout = QHBoxLayout()
            row_layout.setSpacing(8)

            # 任务名称
            name_label = QLabel(task_type)
            name_label.setFixedWidth(120)
            name_label.setToolTip(description)
            row_layout.addWidget(name_label)

            # API选择
            combo = QComboBox()
            combo.addItem("(使用全局)", None)
            combo.addItems([
                "claude", "deepseek", "kimi", "gemini",
                "qwen", "doubao", "baichuan", "glm", "openrouter"
            ])
            combo.currentTextChanged.connect(self._on_change)
            self.task_combos[task_type] = combo
            row_layout.addWidget(combo, 1)

            layout.addLayout(row_layout)

        layout.addStretch()
        self.setLayout(layout)

    def _on_change(self):
        self.settings_changed.emit()

    def get_settings(self) -> Dict[str, Optional[str]]:
        """获取设置"""
        settings = {}
        for task_type, combo in self.task_combos.items():
            text = combo.currentText()
            if text == "(使用全局)":
                settings[task_type] = None
            else:
                settings[task_type] = text
        return settings

    def set_settings(self, settings: Dict[str, Optional[str]]):
        """设置配置"""
        for task_type, api in settings.items():
            if task_type in self.task_combos:
                combo = self.task_combos[task_type]
                if api is None:
                    combo.setCurrentIndex(0)
                else:
                    idx = combo.findText(api)
                    if idx >= 0:
                        combo.setCurrentIndex(idx)


class APIKeySettings(QGroupBox):
    """API密钥设置"""

    settings_changed = pyqtSignal()

    API_LIST = [
        ("claude", "Claude (Anthropic)", "CLAUDE_API_KEY"),
        ("deepseek", "DeepSeek", "DEEPSEEK_API_KEY"),
        ("kimi", "Kimi (Moonshot)", "KIMI_API_KEY"),
        ("gemini", "Gemini (Google)", "GEMINI_API_KEY"),
        ("qwen", "通义千问 (阿里)", "QWEN_API_KEY"),
        ("doubao", "豆包 (字节)", "DOUBAO_API_KEY"),
        ("baichuan", "百川", "BAICHUAN_API_KEY"),
        ("glm", "智谱清言", "GLM_API_KEY"),
        ("openrouter", "OpenRouter", "OPENROUTER_API_KEY"),
    ]

    def __init__(self, theme: str = "dark", parent=None):
        super().__init__("API密钥", parent)
        self.theme = theme
        self.key_inputs: Dict[str, QLineEdit] = {}
        self.test_buttons: Dict[str, QPushButton] = {}
        self.status_labels: Dict[str, QLabel] = {}
        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        is_dark = self.theme == "dark"
        desc_color = "#94A3B8" if is_dark else "#64748B"

        layout = QVBoxLayout()
        layout.setSpacing(8)

        # 说明
        desc = QLabel("配置各API密钥（也可通过环境变量设置）")
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {desc_color}; font-size: 12px;")
        layout.addWidget(desc)

        for api_id, api_name, env_var in self.API_LIST:
            row_layout = QHBoxLayout()
            row_layout.setSpacing(8)

            # API名称
            name_label = QLabel(api_name)
            name_label.setFixedWidth(120)
            name_label.setToolTip(f"环境变量: {env_var}")
            row_layout.addWidget(name_label)

            # 密钥输入
            key_input = QLineEdit()
            key_input.setPlaceholderText(f"输入密钥或设置环境变量 {env_var}")
            key_input.setEchoMode(QLineEdit.EchoMode.Password)
            key_input.textChanged.connect(self._on_change)
            self.key_inputs[api_id] = key_input
            row_layout.addWidget(key_input, 1)

            # 测试按钮
            test_btn = QPushButton("测试")
            test_btn.setFixedWidth(60)
            test_btn.clicked.connect(lambda checked, aid=api_id: self._test_api(aid))
            self.test_buttons[api_id] = test_btn
            row_layout.addWidget(test_btn)

            # 状态标签
            status_label = QLabel("⬚")
            status_label.setFixedWidth(24)
            status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.status_labels[api_id] = status_label
            row_layout.addWidget(status_label)

            layout.addLayout(row_layout)

        layout.addStretch()
        self.setLayout(layout)

    def _on_change(self):
        self.settings_changed.emit()

    def _test_api(self, api_id: str):
        """测试API连接"""
        key = self.key_inputs[api_id].text().strip()
        if not key:
            self.status_labels[api_id].setText("❌")
            self.status_labels[api_id].setToolTip("请先输入API密钥")
            return

        self.status_labels[api_id].setText("⏳")
        self.status_labels[api_id].setToolTip("测试中...")
        self.test_buttons[api_id].setEnabled(False)

        # 获取默认模型
        from api.task_router import SUPPORTED_APIS
        api_info = SUPPORTED_APIS.get(api_id, {})
        model = api_info.get("default_model", "")

        # 创建测试线程
        self.test_worker = APITestWorker(api_id, key, model, self)
        self.test_worker.test_completed.connect(self._on_test_completed)
        self.test_worker.start()

    def _on_test_completed(self, api_id: str, success: bool, message: str):
        """测试完成回调"""
        self.test_buttons[api_id].setEnabled(True)
        if success:
            self.status_labels[api_id].setText("✅")
        else:
            self.status_labels[api_id].setText("❌")
        self.status_labels[api_id].setToolTip(message)

    def get_settings(self) -> Dict[str, str]:
        """获取设置"""
        return {api_id: inp.text().strip() for api_id, inp in self.key_inputs.items()}

    def set_settings(self, settings: Dict[str, str]):
        """设置配置"""
        for api_id, key in settings.items():
            if api_id in self.key_inputs:
                self.key_inputs[api_id].setText(key)


class APISettingsWidget(QWidget):
    """API设置主界面"""

    settings_changed = pyqtSignal()

    def __init__(self, theme: str = "dark", parent=None):
        super().__init__(parent)
        self.theme = theme
        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        is_dark = self.theme == "dark"
        title_color = "#C4B5FD" if is_dark else "#7C3AED"

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # 标题
        title = QLabel("🔧 API设置")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setWeight(QFont.Weight.Bold)
        title.setFont(title_font)
        title.setStyleSheet(f"color: {title_color};")
        layout.addWidget(title)

        # 创建标签页
        tabs = QTabWidget()

        # 全局设置标签页
        global_tab = QWidget()
        global_layout = QVBoxLayout(global_tab)
        self.global_settings = GlobalAPISettings(self.theme)
        self.global_settings.settings_changed.connect(self.settings_changed)
        global_layout.addWidget(self.global_settings)
        global_layout.addStretch()
        tabs.addTab(global_tab, "全局配置")

        # 环节配置标签页
        task_tab = QWidget()
        task_layout = QVBoxLayout(task_tab)
        self.task_settings = TaskAPISettings(self.theme)
        self.task_settings.settings_changed.connect(self.settings_changed)
        task_layout.addWidget(self.task_settings)
        task_layout.addStretch()
        tabs.addTab(task_tab, "环节配置")

        # API密钥标签页
        key_tab = QWidget()
        key_layout = QVBoxLayout(key_tab)
        self.key_settings = APIKeySettings(self.theme)
        self.key_settings.settings_changed.connect(self.settings_changed)
        key_layout.addWidget(self.key_settings)
        key_layout.addStretch()
        tabs.addTab(key_tab, "API密钥")

        layout.addWidget(tabs, 1)

        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        reset_btn = QPushButton("重置为默认")
        reset_btn.clicked.connect(self._reset_to_default)
        btn_layout.addWidget(reset_btn)

        save_btn = QPushButton("保存配置")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #8B5CF6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 24px;
            }
            QPushButton:hover {
                background-color: #7C3AED;
            }
        """)
        save_btn.clicked.connect(self._save_config)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def _reset_to_default(self):
        """重置为默认配置"""
        reply = QMessageBox.question(
            self,
            "确认重置",
            "确定要重置所有API设置为默认值吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            from api.task_router import get_task_router
            router = get_task_router()
            router.reset_to_default()
            self._load_config()
            QMessageBox.information(self, "成功", "已重置为默认配置")

    def _save_config(self):
        """保存配置"""
        try:
            from api.task_router import get_task_router
            router = get_task_router()

            # 保存全局配置
            global_settings = self.global_settings.get_settings()
            router.set_global_config(**global_settings)

            # 保存任务配置
            task_settings = self.task_settings.get_settings()
            for task_type, api in task_settings.items():
                router.set_task_config(task_type, api=api)

            # 保存到文件
            if router.save_config():
                QMessageBox.information(self, "成功", "配置已保存")
            else:
                QMessageBox.warning(self, "警告", "保存配置时出现问题")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存配置失败: {e}")

    def _load_config(self):
        """加载配置"""
        try:
            from api.task_router import get_task_router
            router = get_task_router()

            # 加载全局配置
            global_config = {
                "primary": router.global_config.primary,
                "enable_dual_verification": router.global_config.enable_dual_verification,
                "timeout": router.global_config.timeout,
                "max_retries": router.global_config.max_retries
            }
            self.global_settings.set_settings(global_config)

            # 加载任务配置
            task_config = {}
            for task_type, config in router.task_configs.items():
                task_config[task_type] = config.api
            self.task_settings.set_settings(task_config)

        except Exception as e:
            print(f"加载配置失败: {e}")

    def showEvent(self, event):
        """显示时加载配置"""
        super().showEvent(event)
        self._load_config()
