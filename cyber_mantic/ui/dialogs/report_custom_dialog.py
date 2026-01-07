"""
ReportCustomDialog - 报告自定义对话框

让用户自由描述需求，AI生成自定义报告模板
支持保存5条历史模板，切换或恢复默认
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QLabel, QListWidget, QListWidgetItem,
    QGroupBox, QMessageBox, QInputDialog, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont
from typing import Optional
import asyncio

from utils.template_manager import TemplateManager, ReportTemplate
from api.manager import APIManager
from utils.logger import get_logger


class TemplateGeneratorWorker(QThread):
    """模板生成异步工作线程"""
    finished = pyqtSignal(str)  # AI生成的prompt模板
    error = pyqtSignal(str)

    def __init__(self, api_manager: APIManager, user_requirements: str):
        super().__init__()
        self.api_manager = api_manager
        self.user_requirements = user_requirements

    def run(self):
        """执行异步生成"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # 调用AI生成模板
            prompt_template = loop.run_until_complete(
                self._generate_template()
            )

            loop.close()

            self.finished.emit(prompt_template)

        except Exception as e:
            self.error.emit(str(e))

    async def _generate_template(self) -> str:
        """调用AI生成报告模板"""
        system_prompt = """你是一位专业的报告模板设计师。用户会描述他们希望的报告内容和风格，你需要生成一个详细的prompt模板。

这个模板将用于指导AI生成命理分析报告。

要求：
1. 理解用户需求（如：时间跨度、内容模块、语言风格等）
2. 生成结构化的prompt模板
3. 模板应该可以直接用于报告生成
4. 保持专业性和可读性
"""

        user_prompt = f"""用户需求描述：
{self.user_requirements}

---

请根据以上需求，生成一个报告生成的prompt模板。

模板格式示例：

```
请基于以下术数理论的分析结果，为用户生成个性化的综合分析报告。

## 报告结构要求

### 一、[模块名称]
[具体要求...]

### 二、[模块名称]
[具体要求...]

...

## 语言风格
[风格要求...]

## 输出要求
[格式要求...]
```

请直接输出完整的prompt模板，不要有其他解释文字：
"""

        response = await self.api_manager.call_api(
            task_type="简单问题解答",
            prompt=user_prompt,
            enable_dual_verification=False
        )

        return response.strip()


class ReportCustomDialog(QDialog):
    """报告自定义对话框"""

    # 信号：模板已应用
    template_applied = pyqtSignal(str)  # template_id

    def __init__(self, template_manager: TemplateManager, api_manager: APIManager, parent=None):
        super().__init__(parent)
        self.template_manager = template_manager
        self.api_manager = api_manager
        self.logger = get_logger(__name__)
        self._setup_ui()
        self._load_templates()

    def _setup_ui(self):
        """设置UI"""
        self.setWindowTitle("报告自定义设置")
        self.setMinimumSize(900, 700)

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # 标题
        title_label = QLabel("📝 报告自定义设置")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # 说明文字
        info_label = QLabel(
            "描述您希望的报告内容、结构和风格，AI将为您生成专属的报告模板。\n"
            "系统最多保存5条自定义模板，超过后将自动删除最旧的模板。"
        )
        info_label.setStyleSheet("color: #666; font-size: 10pt;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # 分隔线
        separator = self._create_separator()
        layout.addWidget(separator)

        # 分屏器：左侧模板列表，右侧编辑区域
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧：模板列表
        left_widget = self._create_template_list_panel()
        splitter.addWidget(left_widget)

        # 右侧：编辑区域
        right_widget = self._create_editor_panel()
        splitter.addWidget(right_widget)

        # 设置初始比例
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 7)

        layout.addWidget(splitter)

        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.apply_btn = QPushButton("应用模板")
        self.apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #64B5F6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #42A5F5;
            }
        """)
        self.apply_btn.clicked.connect(self._on_apply_clicked)
        button_layout.addWidget(self.apply_btn)

        reset_btn = QPushButton("恢复默认")
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFA726;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #FF9800;
            }
        """)
        reset_btn.clicked.connect(self._on_reset_clicked)
        button_layout.addWidget(reset_btn)

        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #E0E0E0;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #BDBDBD;
            }
        """)
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _create_template_list_panel(self) -> QGroupBox:
        """创建模板列表面板"""
        group = QGroupBox("我的模板")

        layout = QVBoxLayout()
        layout.setSpacing(8)

        # 模板列表
        self.template_list = QListWidget()
        self.template_list.currentItemChanged.connect(self._on_template_selected)
        layout.addWidget(self.template_list)

        # 删除按钮
        delete_btn = QPushButton("删除选中模板")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #EF5350;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #E53935;
            }
        """)
        delete_btn.clicked.connect(self._on_delete_clicked)
        layout.addWidget(delete_btn)

        group.setLayout(layout)
        return group

    def _create_editor_panel(self) -> QGroupBox:
        """创建编辑面板"""
        group = QGroupBox("创建新模板")

        layout = QVBoxLayout()
        layout.setSpacing(12)

        # 需求描述输入
        desc_label = QLabel("描述您的需求：")
        desc_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(desc_label)

        self.requirements_input = QTextEdit()
        self.requirements_input.setPlaceholderText(
            "示例：\n"
            "我希望报告包含：\n"
            "1. 过去5年的回顾\n"
            "2. 未来3年的预测\n"
            "3. 每个月的运势变化\n"
            "4. 使用白话文，少用专业术语\n"
            "5. 突出财运和事业方面的分析"
        )
        self.requirements_input.setStyleSheet("""
            QTextEdit {
                border: 2px solid #BBDEFB;
                border-radius: 8px;
                padding: 12px;
                font-size: 10pt;
                line-height: 1.6;
            }
        """)
        self.requirements_input.setMinimumHeight(150)
        layout.addWidget(self.requirements_input)

        # 生成按钮
        generate_btn = QPushButton("🤖 让AI生成模板")
        generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #81C784;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px;
                font-size: 11pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #66BB6A;
            }
        """)
        generate_btn.clicked.connect(self._on_generate_clicked)
        layout.addWidget(generate_btn)

        # 分隔线
        separator = self._create_separator()
        layout.addWidget(separator)

        # 预览区域
        preview_label = QLabel("模板预览：")
        preview_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(preview_label)

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setPlaceholderText("生成的模板将在这里显示...")
        self.preview_text.setStyleSheet("""
            QTextEdit {
                background-color: #F5F5F5;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                padding: 12px;
                font-size: 10pt;
            }
        """)
        layout.addWidget(self.preview_text)

        # 保存按钮
        save_btn = QPushButton("💾 保存为新模板")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #42A5F5;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #2196F3;
            }
        """)
        save_btn.clicked.connect(self._on_save_clicked)
        layout.addWidget(save_btn)

        group.setLayout(layout)
        return group

    def _create_separator(self):
        """创建分隔线"""
        from PyQt6.QtWidgets import QFrame
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #E0E0E0;")
        return separator

    def _load_templates(self):
        """加载模板列表"""
        self.template_list.clear()

        templates = self.template_manager.get_all_templates()
        current_template = self.template_manager.get_current_template()

        for template in templates:
            item = QListWidgetItem()

            # 显示文本
            text = template.name
            if template.is_default:
                text += " [默认]"
            if template.template_id == current_template.template_id:
                text += " ✓"

            item.setText(text)
            item.setData(Qt.ItemDataRole.UserRole, template.template_id)

            self.template_list.addItem(item)

    def _on_template_selected(self, current, previous):
        """模板选择变化"""
        if current is None:
            return

        template_id = current.data(Qt.ItemDataRole.UserRole)
        template = self.template_manager.get_template(template_id)

        if template:
            # 显示模板预览
            preview = self.template_manager.get_template_preview(template)
            self.preview_text.setPlainText(preview)

            if template.generated_prompt:
                self.preview_text.append("\n---\n\n**生成的Prompt模板**：\n\n")
                self.preview_text.append(template.generated_prompt)

    def _on_generate_clicked(self):
        """生成模板按钮点击"""
        requirements = self.requirements_input.toPlainText().strip()

        if not requirements:
            QMessageBox.warning(self, "提示", "请先描述您的需求")
            return

        # 禁用按钮
        sender_btn = self.sender()
        sender_btn.setEnabled(False)
        sender_btn.setText("生成中...")

        # 显示进度提示
        self.preview_text.setPlainText("⏳ AI正在为您生成模板，请稍候...\n\n这可能需要10-20秒。")

        # 启动异步生成
        self.worker = TemplateGeneratorWorker(self.api_manager, requirements)
        self.worker.finished.connect(lambda template: self._on_generate_finished(template, sender_btn))
        self.worker.error.connect(lambda error: self._on_generate_error(error, sender_btn))
        self.worker.start()

    def _on_generate_finished(self, template: str, button: QPushButton):
        """生成完成"""
        self.preview_text.setPlainText("✅ 模板生成成功！\n\n")
        self.preview_text.append(template)

        # 保存到临时变量
        self.generated_template = template

        # 恢复按钮
        button.setEnabled(True)
        button.setText("🤖 让AI生成模板")

    def _on_generate_error(self, error: str, button: QPushButton):
        """生成失败"""
        self.preview_text.setPlainText(f"❌ 生成失败：{error}\n\n请检查网络连接或重试。")

        # 恢复按钮
        button.setEnabled(True)
        button.setText("🤖 让AI生成模板")

    def _on_save_clicked(self):
        """保存模板按钮点击"""
        requirements = self.requirements_input.toPlainText().strip()

        if not requirements:
            QMessageBox.warning(self, "提示", "请先描述您的需求")
            return

        if not hasattr(self, 'generated_template') or not self.generated_template:
            QMessageBox.warning(self, "提示", "请先生成模板")
            return

        # 询问模板名称
        name, ok = QInputDialog.getText(
            self,
            "保存模板",
            "请输入模板名称：",
            text=f"自定义模板 {len(self.template_manager.get_custom_templates()) + 1}"
        )

        if not ok or not name:
            return

        # 保存模板
        template = self.template_manager.add_template(
            name=name,
            user_requirements=requirements,
            generated_prompt=self.generated_template
        )

        QMessageBox.information(self, "保存成功", f"模板 '{name}' 已保存！")

        # 刷新列表
        self._load_templates()

        # 清空输入
        self.requirements_input.clear()
        self.preview_text.clear()
        if hasattr(self, 'generated_template'):
            delattr(self, 'generated_template')

    def _on_delete_clicked(self):
        """删除模板按钮点击"""
        current_item = self.template_list.currentItem()

        if current_item is None:
            QMessageBox.warning(self, "提示", "请先选择要删除的模板")
            return

        template_id = current_item.data(Qt.ItemDataRole.UserRole)
        template = self.template_manager.get_template(template_id)

        if template is None:
            return

        if template.is_default:
            QMessageBox.warning(self, "提示", "不能删除默认模板")
            return

        # 确认删除
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除模板 '{template.name}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.template_manager.delete_template(template_id)
            self._load_templates()
            QMessageBox.information(self, "删除成功", "模板已删除")

    def _on_apply_clicked(self):
        """应用模板按钮点击"""
        current_item = self.template_list.currentItem()

        if current_item is None:
            QMessageBox.warning(self, "提示", "请先选择要应用的模板")
            return

        template_id = current_item.data(Qt.ItemDataRole.UserRole)

        if self.template_manager.set_current_template(template_id):
            QMessageBox.information(self, "应用成功", "模板已应用，后续分析将使用此模板")
            self.template_applied.emit(template_id)
            self._load_templates()  # 刷新列表显示

    def _on_reset_clicked(self):
        """恢复默认按钮点击"""
        reply = QMessageBox.question(
            self,
            "确认恢复",
            "确定要恢复为默认模板吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.template_manager.reset_to_default()
            self._load_templates()
            QMessageBox.information(self, "恢复成功", "已恢复为默认模板")
            self.template_applied.emit("default")
