# 主题系统集成指南

本文档说明如何在不直接修改 `ui/main_window.py` 的情况下，为赛博玄数系统添加主题切换功能。

---

## 🎨 系统概述

赛博玄数的主题系统包含三个核心组件：

1. **主题定义** (`ui/themes_simplified.py`) - 定义了3个基础主题（清雅白、墨夜黑、禅意灰）
2. **主题配置** (`config/theme_settings.json`) - 存储用户的主题选择
3. **主题管理器** (`utils/theme_manager.py`) - 处理主题加载、保存和应用

---

## 📋 快速开始

### 方法1：命令行配置（最简单）

无需修改任何代码，直接通过命令行设置主题：

```bash
# 查看当前主题
python -m utils.theme_manager current

# 列出所有可用主题
python -m utils.theme_manager list

# 切换到深色主题
python -m utils.theme_manager set dark

# 启用自动切换（白天浅色，夜间深色）
python -m utils.theme_manager auto on
```

配置会自动保存到 `config/theme_settings.json`，下次启动应用时自动生效。

---

## 🔧 方法2：在GUI中集成（推荐）

### 步骤1：导入主题管理器

在您的GUI入口文件（如 `main.py` 或 `app.py`）中：

```python
from utils.theme_manager import ThemeManager

# 创建QApplication后立即应用主题
app = QApplication(sys.argv)

# 初始化主题管理器
theme_manager = ThemeManager()

# 应用当前主题
app.setStyleSheet(theme_manager.get_current_stylesheet())

# 启动主窗口
window = MainWindow()
window.show()
```

### 步骤2：添加主题切换功能（可选）

如果您想在GUI中添加主题切换按钮或菜单，可以创建一个独立的主题设置对话框：

#### 创建 `ui/theme_settings_dialog.py`：

```python
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QRadioButton, QButtonGroup, QCheckBox, QApplication
)
from utils.theme_manager import ThemeManager


class ThemeSettingsDialog(QDialog):
    """主题设置对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme_manager = ThemeManager()
        self.setup_ui()

    def setup_ui(self):
        """初始化UI"""
        self.setWindowTitle("主题设置")
        self.setMinimumWidth(400)

        layout = QVBoxLayout()

        # 标题
        title = QLabel("选择您喜欢的主题")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        # 主题选择
        self.theme_group = QButtonGroup(self)
        current_theme = self.theme_manager.get_current_theme()

        for theme_name in self.theme_manager.get_available_themes():
            desc = self.theme_manager.get_theme_description(theme_name)
            radio = QRadioButton(desc)
            radio.setProperty("theme_name", theme_name)

            if theme_name == current_theme:
                radio.setChecked(True)

            self.theme_group.addButton(radio)
            layout.addWidget(radio)

        layout.addSpacing(20)

        # 自动切换选项
        self.auto_switch_cb = QCheckBox("启用自动切换（白天浅色，夜间深色）")
        self.auto_switch_cb.setChecked(
            self.theme_manager.settings.get("auto_switch", False)
        )
        layout.addWidget(self.auto_switch_cb)

        layout.addSpacing(20)

        # 按钮
        button_layout = QHBoxLayout()
        apply_btn = QPushButton("应用")
        apply_btn.clicked.connect(self.apply_theme)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(apply_btn)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def apply_theme(self):
        """应用主题设置"""
        # 获取选中的主题
        selected_button = self.theme_group.checkedButton()
        if selected_button:
            theme_name = selected_button.property("theme_name")
            self.theme_manager.set_theme(theme_name)

        # 设置自动切换
        self.theme_manager.enable_auto_switch(
            self.auto_switch_cb.isChecked()
        )

        # 应用到整个应用
        stylesheet = self.theme_manager.get_current_stylesheet()
        QApplication.instance().setStyleSheet(stylesheet)

        self.accept()
```

#### 在主窗口中添加入口：

在 `MainWindow` 中添加一个菜单项或按钮来打开主题设置对话框：

```python
# 在某个菜单或工具栏中添加
from ui.theme_settings_dialog import ThemeSettingsDialog

def open_theme_settings(self):
    """打开主题设置对话框"""
    dialog = ThemeSettingsDialog(self)
    if dialog.exec():
        # 用户点击了"应用"按钮
        # 主题已经在对话框中应用，这里可以添加额外的处理
        pass
```

---

## 🎯 方法3：直接修改配置文件

最简单的方法是直接编辑 `config/theme_settings.json`：

```json
{
  "current_theme": "dark",     // 改为 "light", "dark", 或 "zen"
  "auto_switch": false,         // 改为 true 启用自动切换
  "available_themes": ["light", "dark", "zen"],
  "theme_descriptions": {
    "light": "清雅白 - 简洁明亮，适合白天使用",
    "dark": "墨夜黑 - 护眼深色，适合夜间使用",
    "zen": "禅意灰 - 平静沉稳，适合长时间阅读"
  },
  "auto_switch_times": {
    "day_theme": "light",
    "night_theme": "dark",
    "day_start_hour": 6,       // 白天开始时间
    "night_start_hour": 18     // 夜间开始时间
  }
}
```

---

## 📚 API参考

### ThemeManager 类

#### 初始化
```python
theme_mgr = ThemeManager()  # 使用默认配置路径
theme_mgr = ThemeManager("/path/to/config.json")  # 自定义路径
```

#### 主要方法

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `get_current_theme()` | 获取当前主题名称 | str |
| `set_theme(theme_name)` | 设置主题 | bool |
| `get_current_stylesheet()` | 获取当前主题的QSS样式表 | str |
| `get_available_themes()` | 获取所有可用主题 | list |
| `get_theme_description(theme_name)` | 获取主题描述 | str |
| `enable_auto_switch(enable)` | 启用/禁用自动切换 | bool |
| `set_auto_switch_times(...)` | 设置自动切换时间 | bool |

---

## 🎨 三大主题预览

### 清雅白 (light)
- **适用场景**：白天使用、明亮环境
- **特点**：简洁明亮，专业清爽
- **主色调**：深青色 (#2E5266)

### 墨夜黑 (dark)
- **适用场景**：夜间使用、暗光环境
- **特点**：护眼深色，舒适柔和
- **主色调**：天蓝色 (#64B5F6)

### 禅意灰 (zen)
- **适用场景**：长时间阅读、专注工作
- **特点**：平静沉稳，低对比度
- **主色调**：棕灰色 (#5D4E37)

---

## 🔍 高级用法

### 自定义主题

如果需要添加新主题，编辑 `ui/themes_simplified.py`：

```python
BASE_THEMES = {
    # ... 现有主题 ...
    "custom": {
        "name": "自定义主题",
        "description": "您的描述",
        "colors": {
            "primary": "#XXXXXX",
            # ... 其他颜色配置 ...
        }
    }
}
```

然后更新 `config/theme_settings.json`：

```json
{
  "available_themes": ["light", "dark", "zen", "custom"]
}
```

### 动态主题切换

在运行时动态切换主题：

```python
# 在任何地方
from PyQt6.QtWidgets import QApplication
from utils.theme_manager import ThemeManager

theme_mgr = ThemeManager()
theme_mgr.set_theme("dark")
QApplication.instance().setStyleSheet(theme_mgr.get_current_stylesheet())
```

---

## ⚠️ 注意事项

1. **主题切换立即生效**：使用 `QApplication.instance().setStyleSheet()` 会立即应用到所有窗口
2. **配置持久化**：所有设置都自动保存到 `config/theme_settings.json`
3. **自动切换优先级**：启用自动切换时，会覆盖手动选择的主题
4. **线程安全**：ThemeManager 不是线程安全的，请在主线程中使用

---

## 📝 总结

使用主题管理器的优势：

- ✅ **无需修改现有代码**：完全独立的模块
- ✅ **配置持久化**：设置自动保存和加载
- ✅ **灵活集成**：可以通过命令行、配置文件或GUI集成
- ✅ **自动切换**：支持根据时间自动切换日/夜主题
- ✅ **易于扩展**：添加新主题只需修改配置文件

---

## 🆘 常见问题

**Q: 主题不生效怎么办？**
A: 确保在创建所有窗口之前应用主题：
```python
app = QApplication(sys.argv)
app.setStyleSheet(ThemeManager().get_current_stylesheet())  # 在这里！
window = MainWindow()
```

**Q: 如何重置为默认主题？**
A: 删除 `config/theme_settings.json` 文件，或运行：
```bash
python -m utils.theme_manager set light
```

**Q: 可以同时使用多个主题吗？**
A: 不可以，整个应用使用统一主题。但可以为不同窗口设置不同的局部样式。

---

## 📧 技术支持

如有问题，请查阅：
- `ui/themes_simplified.py` - 主题定义
- `utils/theme_manager.py` - 主题管理器实现
- `config/theme_settings.json` - 配置文件
