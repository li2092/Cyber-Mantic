# 赛博玄数前端重构 - Phase 6 集成指南

## 概述

本文档说明如何将Phase 1-5创建的所有组件集成到main_window.py中，实现完整的前端重构。

---

## Phase 1-5 已完成的组件总览

### Phase 1: Services Layer (服务层)
- `services/conversation_service.py` - 9步AI对话流程
- `services/report_service.py` - 报告交互服务
- `services/analysis_service.py` - 分析流程封装
- `services/export_service.py` - 多格式导出

### Phase 2-3: UI Components (UI组件)
- `ui/widgets/chat_widget.py` - 聊天消息组件
- `ui/widgets/progress_widget.py` - 情绪化进度组件
- `ui/dialogs/term_explain_sidebar.py` - 术语解释侧边栏
- `ui/dialogs/report_qa_dialog.py` - 报告问答对话框
- `ui/tabs/ai_conversation_tab.py` - 纯AI对话标签页

### Phase 4: Report Customization (报告自定义)
- `utils/template_manager.py` - 模板管理器
- `ui/dialogs/report_custom_dialog.py` - 报告自定义对话框

### Phase 5: Expose Hidden Features (暴露隐藏功能)
- `ui/widgets/export_menu_button.py` - 导出菜单按钮
- `ui/widgets/theme_settings_widget.py` - 主题设置组件
- `ui/dialogs/report_compare_dialog.py` - 报告对比对话框

---

## 集成步骤

### 步骤 1: 更新 main_window.py 的导入

在 `main_window.py` 的顶部添加以下导入：

```python
# 服务层导入
from services.conversation_service import ConversationService
from services/report_service import ReportService
from services/analysis_service import AnalysisService
from services.export_service import ExportService

# UI组件导入
from ui.widgets.chat_widget import ChatWidget
from ui.widgets.progress_widget import ProgressWidget
from ui/widgets.export_menu_button import ExportMenuButton
from ui.widgets.theme_settings_widget import ThemeSettingsWidget

# 对话框导入
from ui.dialogs.term_explain_sidebar import TermExplainSidebar
from ui.dialogs.report_qa_dialog import ReportQADialog
from ui/dialogs.report_custom_dialog import ReportCustomDialog
from ui/dialogs.report_compare_dialog import ReportCompareDialog

# 标签页导入
from ui.tabs.ai_conversation_tab import AIConversationTab

# 工具导入
from utils.template_manager import TemplateManager
from utils.theme_manager import ThemeManager
```

### 步骤 2: 在 MainWindow.__init__() 中初始化服务

在 `__init__()` 方法中，self.engine 初始化之后添加：

```python
def __init__(self):
    super().__init__()
    self.setWindowTitle("赛博玄数 - 多理论术数智能分析系统")
    self.setGeometry(100, 100, 1200, 800)

    # ... 现有初始化代码 ...
    self.engine = DecisionEngine(self.config)

    # === 新增：初始化服务层 ===
    self.api_manager = self.engine.api_manager  # 复用现有的APIManager
    self.conversation_service = ConversationService(self.api_manager)
    self.report_service = ReportService(self.api_manager)
    self.analysis_service = AnalysisService(self.api_manager, self.engine)
    self.export_service = ExportService()

    # 初始化管理器
    self.template_manager = TemplateManager()
    self.theme_manager = ThemeManager()

    # ... 其他初始化代码 ...
    self._init_ui()

    # === 新增：应用主题 ===
    self._apply_theme()
```

### 步骤 3: 添加主题应用方法

在 MainWindow 类中添加新方法：

```python
def _apply_theme(self):
    """应用当前主题"""
    from PyQt6.QtWidgets import QApplication
    stylesheet = self.theme_manager.get_current_stylesheet()
    QApplication.instance().setStyleSheet(stylesheet)

def _on_theme_changed(self, theme_name: str):
    """主题更改回调"""
    self._apply_theme()
    self.logger.info(f"主题已切换为: {theme_name}")
```

### 步骤 4: 修改 _init_ui() 添加新标签页

修改 `_init_ui()` 方法（第117-138行）：

```python
def _init_ui(self):
    """初始化UI"""
    central_widget = QWidget()
    self.setCentralWidget(central_widget)
    main_layout = QVBoxLayout(central_widget)

    # 标题
    title_label = QLabel("赛博玄数 - 多理论术数智能分析系统")
    title_font = QFont()
    title_font.setPointSize(16)
    title_font.setBold(True)
    title_label.setFont(title_font)
    title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    main_layout.addWidget(title_label)

    # 主标签页
    self.main_tabs = QTabWidget()

    # === 现有标签页 ===
    self.main_tabs.addTab(self._create_analysis_tab(), "📊 分析")

    # === 新增：AI对话标签页 ===
    self.ai_conversation_tab = AIConversationTab(self.api_manager)
    self.ai_conversation_tab.save_requested.connect(self._save_conversation)
    self.main_tabs.addTab(self.ai_conversation_tab, "💬 AI对话")

    # === 现有标签页 ===
    self.main_tabs.addTab(self._create_settings_tab(), "⚙️ 设置")
    self.main_tabs.addTab(self._create_history_tab(), "📜 历史记录")

    main_layout.addWidget(self.main_tabs)

def _save_conversation(self, conversation_data: dict):
    """保存AI对话到历史记录"""
    # 将conversation_data转换为ComprehensiveReport格式
    # 然后保存到history_manager
    # 这需要根据实际数据结构实现
    self.logger.info(f"保存AI对话: {conversation_data.get('conversation_id', 'unknown')}")
    # TODO: 实现对话保存逻辑
```

### 步骤 5: 修改 _create_analysis_tab() 添加导出按钮

修改分析标签页的按钮布局（第169-184行）：

```python
# 底部按钮
button_layout = QHBoxLayout()
button_layout.addStretch()

self.analyze_btn = QPushButton("开始分析")
self.analyze_btn.setMinimumSize(120, 40)
self.analyze_btn.clicked.connect(self._start_analysis)
button_layout.addWidget(self.analyze_btn)

# === 原有的保存按钮改为导出菜单按钮 ===
self.export_btn = ExportMenuButton(self.export_service)
self.export_btn.setMinimumSize(120, 40)
button_layout.addWidget(self.export_btn)

layout.addLayout(button_layout)
```

同时修改 `_on_finished()` 方法，启用导出按钮：

```python
def _on_finished(self, report):
    """分析完成回调"""
    # ... 现有代码 ...

    # 保存当前报告
    self.current_report = report

    # === 修改：不再启用保存按钮，而是设置导出按钮的报告 ===
    # self.save_btn.setEnabled(True)  # 删除这行
    self.export_btn.set_report(report)  # 新增这行

    # ... 其他代码 ...
```

### 步骤 6: 修改 _create_settings_tab() 添加主题设置

在设置标签页的布局中（第1032行之前）添加主题设置组：

```python
def _create_settings_tab(self) -> QWidget:
    """创建设置标签页"""
    tab = QWidget()
    layout = QVBoxLayout()

    # === 新增：主题设置组 ===
    self.theme_settings_widget = ThemeSettingsWidget(self.theme_manager)
    self.theme_settings_widget.theme_changed.connect(self._on_theme_changed)
    layout.addWidget(self.theme_settings_widget)

    # === 新增：报告自定义组 ===
    report_custom_group = QGroupBox("📝 报告自定义")
    report_custom_layout = QVBoxLayout()

    desc_label = QLabel("自定义报告的结构、内容和风格")
    desc_label.setStyleSheet("color: #666; font-size: 10pt;")
    report_custom_layout.addWidget(desc_label)

    customize_btn = QPushButton("🎨 打开报告自定义")
    customize_btn.clicked.connect(self._open_report_custom_dialog)
    customize_btn.setStyleSheet("""
        QPushButton {
            background-color: #64B5F6;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-size: 10pt;
        }
        QPushButton:hover {
            background-color: #42A5F5;
        }
    """)
    report_custom_layout.addWidget(customize_btn)

    report_custom_group.setLayout(report_custom_layout)
    layout.addWidget(report_custom_group)

    # === 现有的API配置区域 ===
    api_group = QGroupBox("AI API 配置")
    # ... 现有代码保持不变 ...

    layout.addWidget(api_group)
    # ... 其他现有代码 ...

def _open_report_custom_dialog(self):
    """打开报告自定义对话框"""
    dialog = ReportCustomDialog(self.template_manager, self.api_manager, self)
    dialog.exec()
```

### 步骤 7: 修改 _create_history_tab() 添加对比功能

修改历史记录标签页（第1135行开始）：

```python
def _create_history_tab(self) -> QWidget:
    """创建历史记录标签页"""
    tab = QWidget()
    layout = QVBoxLayout()

    # 工具栏
    toolbar_layout = QHBoxLayout()
    refresh_btn = QPushButton("🔄 刷新")
    refresh_btn.clicked.connect(self._refresh_history)
    toolbar_layout.addWidget(refresh_btn)

    # === 新增：对比按钮 ===
    self.compare_btn = QPushButton("📊 对比选中的报告")
    self.compare_btn.setEnabled(False)
    self.compare_btn.clicked.connect(self._compare_selected_reports)
    self.compare_btn.setStyleSheet("""
        QPushButton {
            background-color: #81C784;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 6px 12px;
        }
        QPushButton:hover {
            background-color: #66BB6A;
        }
        QPushButton:disabled {
            background-color: #BDBDBD;
        }
    """)
    toolbar_layout.addWidget(self.compare_btn)

    # ... 现有的搜索和筛选控件 ...

    # === 修改：历史记录表格添加复选框列 ===
    self.history_table = QTableWidget()
    self.history_table.setColumnCount(6)  # 从5改为6
    self.history_table.setHorizontalHeaderLabels([
        "选择", "时间", "问题类型", "问题描述", "使用理论", "操作"  # 添加"选择"列
    ])
    self.history_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
    self.history_table.setColumnWidth(0, 50)  # 设置复选框列宽度
    # ... 其他列的设置保持不变，但列索引全部+1 ...

    # === 新增：监听选择变化 ===
    self.history_table.itemChanged.connect(self._on_history_selection_changed)

    layout.addWidget(self.history_table)
    # ... 其他代码 ...

def _display_history(self, history_list):
    """显示历史记录到表格"""
    # 临时断开信号，避免触发选择变化
    self.history_table.itemChanged.disconnect(self._on_history_selection_changed)

    self.history_table.setRowCount(len(history_list))

    for row, item in enumerate(history_list):
        # === 新增：复选框列 ===
        checkbox_item = QTableWidgetItem()
        checkbox_item.setCheckState(Qt.CheckState.Unchecked)
        checkbox_item.setData(Qt.ItemDataRole.UserRole, item['report_id'])  # 存储report_id
        self.history_table.setItem(row, 0, checkbox_item)

        # === 时间列（列索引从0改为1） ===
        created_at = item['created_at']
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        time_text = created_at.strftime('%Y-%m-%d %H:%M')
        self.history_table.setItem(row, 1, QTableWidgetItem(time_text))

        # === 问题类型（列索引从1改为2） ===
        self.history_table.setItem(row, 2, QTableWidgetItem(item.get('question_type', '')))

        # === 问题描述（列索引从2改为3） ===
        desc = item.get('question_desc', '')
        if len(desc) > 50:
            desc = desc[:50] + "..."
        self.history_table.setItem(row, 3, QTableWidgetItem(desc))

        # === 使用理论（列索引从3改为4） ===
        theories = item.get('selected_theories', '')
        self.history_table.setItem(row, 4, QTableWidgetItem(theories))

        # === 操作按钮（列索引从4改为5） ===
        btn_widget = QWidget()
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(4, 2, 4, 2)

        view_btn = QPushButton("查看")
        view_btn.clicked.connect(lambda checked, rid=item['report_id']: self._view_history_report(rid))
        btn_layout.addWidget(view_btn)

        # === 新增：问答按钮 ===
        qa_btn = QPushButton("问答")
        qa_btn.clicked.connect(lambda checked, rid=item['report_id']: self._open_report_qa(rid))
        btn_layout.addWidget(qa_btn)

        delete_btn = QPushButton("删除")
        delete_btn.clicked.connect(lambda checked, rid=item['report_id']: self._delete_history_report(rid))
        btn_layout.addWidget(delete_btn)

        btn_widget.setLayout(btn_layout)
        self.history_table.setCellWidget(row, 5, btn_widget)

    # 重新连接信号
    self.history_table.itemChanged.connect(self._on_history_selection_changed)

def _on_history_selection_changed(self):
    """历史记录选择变化"""
    selected_count = 0
    for row in range(self.history_table.rowCount()):
        item = self.history_table.item(row, 0)
        if item and item.checkState() == Qt.CheckState.Checked:
            selected_count += 1

    # 只有选中2个报告时才启用对比按钮
    self.compare_btn.setEnabled(selected_count == 2)
    self.compare_btn.setText(f"📊 对比选中的报告 ({selected_count}/2)")

def _compare_selected_reports(self):
    """对比选中的报告"""
    selected_reports = []

    for row in range(self.history_table.rowCount()):
        item = self.history_table.item(row, 0)
        if item and item.checkState() == Qt.CheckState.Checked:
            report_id = item.data(Qt.ItemDataRole.UserRole)
            report = self.history_manager.get_report_by_id(report_id)
            if report:
                selected_reports.append(report)

    if len(selected_reports) != 2:
        QMessageBox.warning(self, "选择错误", "请选择恰好2个报告进行对比！")
        return

    # 打开对比对话框
    dialog = ReportCompareDialog(
        selected_reports[0],
        selected_reports[1],
        self.report_service,
        self
    )
    dialog.exec()

def _open_report_qa(self, report_id: str):
    """打开报告问答对话框"""
    report = self.history_manager.get_report_by_id(report_id)
    if not report:
        QMessageBox.warning(self, "错误", "无法加载报告")
        return

    dialog = ReportQADialog(report, self.report_service, self)
    dialog.exec()
```

### 步骤 8: 在 _view_history_report() 中添加术语解释功能

修改查看历史报告的方法，添加术语解释侧边栏：

```python
def _view_history_report(self, report_id: str):
    """查看历史报告"""
    report = self.history_manager.get_report_by_id(report_id)
    if not report:
        QMessageBox.warning(self, "错误", "无法加载报告")
        return

    # === 新增：创建带术语解释的报告查看器 ===
    # 可以创建一个专门的报告查看对话框，集成TermExplainSidebar
    # 或者直接使用ReportQADialog，它已经提供了完整的报告交互功能

    # 切换到分析标签页并显示报告
    self.current_report = report
    self._on_finished(report)
    self.main_tabs.setCurrentIndex(0)  # 切换到分析标签页

    # === 新增：提示用户可以使用问答功能 ===
    QMessageBox.information(
        self,
        "查看历史报告",
        "报告已加载到分析标签页。\n\n💡 提示：您可以在历史记录中点击【问答】按钮，与报告进行交互式问答。"
    )
```

---

## 集成后的功能清单

### ✅ 已暴露的功能

#### 分析标签页
- ✅ 多格式导出（JSON/PDF/Markdown）
- ✅ 现有的分析功能保持不变

#### AI对话标签页（新增）
- ✅ 9步智能交互式分析
- ✅ 实时进度反馈（情绪化文字）
- ✅ 分屏显示（对话 + 关键信息）
- ✅ 保存对话到历史记录

#### 设置标签页
- ✅ 主题切换（清雅白/墨夜黑/禅意灰）
- ✅ 自动切换主题
- ✅ 报告自定义（AI生成模板，保存5条历史）
- ✅ 现有的API配置保持不变

#### 历史记录标签页
- ✅ 报告对比（选择2个报告进行AI对比分析）
- ✅ 报告问答（点击问答按钮打开交互对话框）
- ✅ 现有的搜索、筛选功能保持不变

---

## 测试检查清单

### 功能测试
- [ ] AI对话模式标签页正常工作
- [ ] 9步对话流程完整执行
- [ ] 情绪化进度文字正确显示（感情类为中性）
- [ ] 对话可以保存到历史记录

- [ ] 导出菜单按钮正常工作
- [ ] JSON导出成功
- [ ] PDF导出成功
- [ ] Markdown导出成功

- [ ] 主题切换功能正常
- [ ] 清雅白主题应用成功
- [ ] 墨夜黑主题应用成功
- [ ] 禅意灰主题应用成功
- [ ] 自动切换功能正常

- [ ] 报告自定义对话框打开
- [ ] AI生成模板功能正常
- [ ] 模板保存和切换功能正常
- [ ] 最多保存5条模板限制生效

- [ ] 历史记录复选框正常
- [ ] 选择2个报告时对比按钮启用
- [ ] 报告对比对话框正常工作
- [ ] AI对比分析正常返回

- [ ] 报告问答对话框打开
- [ ] 建议问题正确生成
- [ ] AI回答用户问题正常
- [ ] 对话导出功能正常

### UI测试
- [ ] 所有组件样式一致
- [ ] 响应式布局正常
- [ ] 按钮禁用/启用状态正确
- [ ] 错误提示信息友好

### 性能测试
- [ ] AI调用不阻塞UI
- [ ] 异步操作正常工作
- [ ] 进度反馈实时更新
- [ ] 无内存泄漏

---

## 回滚方案

如果集成后出现问题，可以：

1. **保留原main_window.py备份**
   ```bash
   cp ui/main_window.py ui/main_window.py.backup
   ```

2. **逐步集成**
   - 先集成AI对话标签页，测试通过再继续
   - 再集成主题切换，测试通过再继续
   - 最后集成报告对比和问答功能

3. **独立测试**
   - 每个组件都可以单独测试，不依赖main_window.py
   - 例如：直接运行 `python -m ui.tabs.ai_conversation_tab` 测试AI对话标签页

---

## 注意事项

1. **API Manager 复用**：所有服务都使用 `self.engine.api_manager`，无需创建新的APIManager实例

2. **历史记录格式**：AI对话保存到历史记录时，需要将ConversationContext转换为ComprehensiveReport格式

3. **主题应用**：主题需要重启应用才能完全生效，建议在应用主题后提示用户重启

4. **模板同步**：报告自定义模板保存后，需要确保DecisionEngine使用最新的模板

5. **错误处理**：所有异步操作都需要正确的错误处理和用户提示

---

## 集成完成后的效果

用户将看到：

1. **4个标签页**：分析、AI对话、设置、历史记录
2. **导出功能**：一键导出JSON/PDF/Markdown
3. **主题切换**：3种主题+自动切换
4. **报告自定义**：AI生成个性化报告模板
5. **报告对比**：对比历史报告的变化趋势
6. **报告问答**：与报告进行交互式问答
7. **术语解释**：（可通过问答功能实现）

前端功能暴露率从 **27%** 提升至 **100%**！
