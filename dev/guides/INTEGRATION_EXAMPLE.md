# 集成示例代码

## 快速集成指南

### Step 1: 修改 main_window.py 应用主题

```python
# 在文件开头导入
from ui.themes import ThemeSystem
from ui.report_renderer import ReportRenderer

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # ... 现有初始化代码 ...

        # 应用主题（在_init_ui之后调用）
        self._apply_theme()

    def _apply_theme(self):
        """应用主题样式"""
        # 从配置获取主题，默认light
        theme_name = self.config.get("display", {}).get("theme", "light")

        # 从配置获取MBTI类型（如果用户设置过）
        saved_mbti = self.config.get("user", {}).get("mbti_type", None)

        # 生成样式表
        qss = ThemeSystem.generate_qss_stylesheet(
            theme_name=theme_name,
            mbti_type=saved_mbti
        )

        # 应用到窗口
        self.setStyleSheet(qss)
```

### Step 2: 在设置页添加主题选择器

```python
def _create_settings_tab(self) -> QWidget:
    """创建设置标签页"""
    tab = QWidget()
    layout = QVBoxLayout()

    # ... 现有设置项 ...

    # ====== 新增：显示设置 ======
    display_group = QGroupBox("🎨 显示设置")
    display_layout = QVBoxLayout()

    # 主题选择
    theme_layout = QHBoxLayout()
    theme_layout.addWidget(QLabel("界面主题:"))
    self.theme_selector = QComboBox()
    self.theme_selector.addItems([
        "清雅白 (适合白天)",
        "墨夜黑 (适合夜间)",
        "禅意灰 (护眼模式)"
    ])
    # 设置当前主题
    current_theme = self.config.get("display", {}).get("theme", "light")
    theme_index = {"light": 0, "dark": 1, "zen": 2}.get(current_theme, 0)
    self.theme_selector.setCurrentIndex(theme_index)
    self.theme_selector.currentIndexChanged.connect(self._on_theme_changed)
    theme_layout.addWidget(self.theme_selector)
    theme_layout.addStretch()
    display_layout.addLayout(theme_layout)

    # 保存MBTI偏好
    mbti_pref_layout = QHBoxLayout()
    self.save_mbti_pref = QCheckBox("记住我的MBTI类型，用于个性化显示")
    mbti_pref_layout.addWidget(self.save_mbti_pref)
    mbti_pref_layout.addStretch()
    display_layout.addLayout(mbti_pref_layout)

    display_group.setLayout(display_layout)
    layout.addWidget(display_group)

    # ... 其他设置 ...

    tab.setLayout(layout)
    return tab

def _on_theme_changed(self, index):
    """主题变更处理"""
    theme_map = {0: "light", 1: "dark", 2: "zen"}
    new_theme = theme_map.get(index, "light")

    # 保存到配置
    if "display" not in self.config:
        self.config["display"] = {}
    self.config["display"]["theme"] = new_theme
    self.config_manager.save_config(self.config)

    # 应用新主题
    self._apply_theme()

    # 提示用户
    QMessageBox.information(
        self,
        "主题已更改",
        f"主题已切换为: {self.theme_selector.currentText()}\n\n"
        "新主题已应用到所有界面元素。"
    )
```

### Step 3: 修改分析完成回调，使用智能渲染器

```python
def _on_finished(self, report):
    """分析完成 - 使用智能渲染器呈现结果"""
    self.current_report = report
    self.progress_bar.setValue(100)
    self.progress_label.setText("分析完成")

    # 保存到历史记录
    self.history_manager.save_report(report)

    # ====== 使用智能渲染器 ======

    # 获取用户MBTI类型
    mbti_type = report.user_input_summary.get('mbti_type', None)

    # 如果用户勾选了"记住MBTI"，保存到配置
    if self.save_mbti_pref.isChecked() and mbti_type:
        if "user" not in self.config:
            self.config["user"] = {}
        self.config["user"]["mbti_type"] = mbti_type
        self.config_manager.save_config(self.config)

    # 获取当前主题
    theme = self.config.get("display", {}).get("theme", "light")

    # 1. 渲染执行摘要（个性化的首页）
    summary_markdown = ReportRenderer.render_executive_summary(
        report=report,
        theme=theme,
        mbti_type=mbti_type
    )
    self.summary_text.setMarkdown(summary_markdown)

    # 2. 渲染详细分析（完整AI报告）
    self.detail_text.setMarkdown(report.executive_summary)

    # 3. 渲染各理论分析（精美卡片形式）
    theories_markdown = ReportRenderer.render_theory_details(
        theory_results=report.theory_results,
        mbti_type=mbti_type
    )
    self.theories_text.setMarkdown(theories_markdown)

    # ====== 可选：添加第四个标签页 - 冲突分析 ======
    # conflict_markdown = ReportRenderer.render_conflict_analysis(report)
    # self.conflict_text.setMarkdown(conflict_markdown)

    self.analyze_btn.setEnabled(True)
    self.save_btn.setEnabled(True)
```

### Step 4: 添加导出功能增强（可选）

```python
def _save_report(self):
    """保存报告 - 支持多种格式"""
    if not self.current_report:
        QMessageBox.warning(self, "提示", "没有可保存的报告")
        return

    # 弹出格式选择对话框
    format_dialog = QDialog(self)
    format_dialog.setWindowTitle("选择导出格式")
    layout = QVBoxLayout()

    format_group = QGroupBox("导出格式")
    format_layout = QVBoxLayout()

    format_radio = {}
    for fmt in ["Markdown", "HTML", "PDF"]:
        radio = QRadioButton(fmt)
        format_radio[fmt] = radio
        format_layout.addWidget(radio)

    format_radio["Markdown"].setChecked(True)  # 默认选中
    format_group.setLayout(format_layout)
    layout.addWidget(format_group)

    # 确定和取消按钮
    button_layout = QHBoxLayout()
    ok_btn = QPushButton("确定")
    cancel_btn = QPushButton("取消")
    button_layout.addWidget(ok_btn)
    button_layout.addWidget(cancel_btn)
    layout.addLayout(button_layout)

    format_dialog.setLayout(layout)

    # 按钮事件
    ok_btn.clicked.connect(format_dialog.accept)
    cancel_btn.clicked.connect(format_dialog.reject)

    if format_dialog.exec() == QDialog.DialogCode.Accepted:
        # 获取选中的格式
        selected_format = None
        for fmt, radio in format_radio.items():
            if radio.isChecked():
                selected_format = fmt
                break

        # 根据格式选择文件保存路径
        ext_map = {"Markdown": "md", "HTML": "html", "PDF": "pdf"}
        ext = ext_map.get(selected_format, "md")

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存报告",
            f"报告_{self.current_report.created_at.strftime('%Y%m%d_%H%M%S')}.{ext}",
            f"{selected_format}文件 (*.{ext})"
        )

        if file_path:
            self._export_report(file_path, selected_format)

def _export_report(self, file_path: str, format: str):
    """导出报告到文件"""
    try:
        mbti_type = self.current_report.user_input_summary.get('mbti_type')
        theme = self.config.get("display", {}).get("theme", "light")

        if format == "Markdown":
            # 合并所有内容
            full_markdown = ReportRenderer.render_executive_summary(
                self.current_report, theme, mbti_type
            )
            full_markdown += "\n\n" + ReportRenderer.render_theory_details(
                self.current_report.theory_results, mbti_type
            )
            full_markdown += "\n\n" + ReportRenderer.render_conflict_analysis(
                self.current_report
            )

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(full_markdown)

        elif format == "HTML":
            # 将Markdown转为HTML（需要markdown库）
            try:
                import markdown
                full_markdown = # ... 同上 ...
                html = markdown.markdown(
                    full_markdown,
                    extensions=['tables', 'fenced_code', 'nl2br']
                )

                # 添加HTML头部和样式
                html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>赛博玄数分析报告</title>
    <style>
        body {{
            font-family: "Microsoft YaHei", Arial, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #667eea;
            color: white;
        }}
        /* 更多样式... */
    </style>
</head>
<body>
{html}
</body>
</html>
                """

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(html_template)

            except ImportError:
                QMessageBox.warning(
                    self, "提示",
                    "HTML导出需要安装markdown库\n\n"
                    "请运行: pip install markdown"
                )
                return

        elif format == "PDF":
            # PDF导出（需要额外库，如reportlab或weasyprint）
            QMessageBox.information(
                self, "提示",
                "PDF导出功能需要安装额外依赖\n\n"
                "推荐方案：\n"
                "1. 导出为HTML后，使用浏览器打印为PDF\n"
                "2. 安装weasyprint: pip install weasyprint"
            )
            return

        QMessageBox.information(
            self,
            "保存成功",
            f"报告已保存到:\n{file_path}"
        )

    except Exception as e:
        QMessageBox.critical(
            self,
            "保存失败",
            f"保存报告时出错:\n{str(e)}"
        )
```

---

## 完整示例：最小化集成

如果只想快速体验效果，只需修改以下几行代码：

```python
# 在 main_window.py 顶部添加导入
from ui.themes import ThemeSystem
from ui.report_renderer import ReportRenderer

# 在 __init__ 方法的最后添加
def __init__(self):
    # ... 所有现有代码 ...

    # 应用主题
    qss = ThemeSystem.generate_qss_stylesheet("light")
    self.setStyleSheet(qss)

# 在 _on_finished 方法中，替换现有的报告呈现代码
def _on_finished(self, report):
    # ... 前面的代码保持不变 ...

    # 使用智能渲染器（只需三行）
    mbti = report.user_input_summary.get('mbti_type')
    self.summary_text.setMarkdown(
        ReportRenderer.render_executive_summary(report, "light", mbti)
    )
    self.theories_text.setMarkdown(
        ReportRenderer.render_theory_details(report.theory_results, mbti)
    )

    # ... 后面的代码保持不变 ...
```

就这么简单！🎉

---

## 效果对比截图（文字版预览）

### 优化前
```
赛博玄数分析报告

报告ID: a1b2c3d4
生成时间: 2024-12-31 14:30
问题类型: 事业

执行摘要:
从八字来看，日主丙火生于巳月，火势当令...
[纯文本，无格式]
```

### 优化后（INTJ用户视角 - NT类型）
```
🌟 赛博玄数 · 智能分析报告
╔════════════════════════════════════════╗
║  📋 报告基本信息                        ║
║  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓  ║
║  ┃ 📅 生成时间    2024-12-31 14:30 ┃  ║
║  ┃ 🎯 问题类别    事业               ┃  ║
║  ┃ 🔮 使用理论    八字·梅花·小六壬   ┃  ║
║  ┃ 📊 综合置信度  85.3% 🟢          ┃  ║
║  ┃ 🎭 个性化      INTJ              ┃  ║
║  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛  ║
╚════════════════════════════════════════╝

✨ 核心结论
┌────────────────────────────────────────┐
│ 综合判断：吉 ✨                        │
│                                        │
│ 从八字来看，日主丙火生于巳月...        │
│ [完整AI内容，精美格式化]               │
└────────────────────────────────────────┘

📊 量化分析视图  ← NT类型专属板块
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

理论结果分布:
- 吉 ✨: 3个理论 (60%) ████████████
- 平 ⚖️: 2个理论 (40%) ████████

置信度分析:
- 平均置信度: 83.5%
- 最高置信度: 92.0%
- 标准差: 0.086
```

### 优化后（ENFP用户视角 - NF类型）
```
🌟 赛博玄数 · 智能分析报告
[相同的头部信息]

✨ 核心结论
[相同的综合判断]

💫 深层洞察  ← NF类型专属板块
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌟 共识与分歧

各理论结果达成高度共识，这暗示着命运的趋势较为明确。
当多个理论从不同角度得出相似结论时，其预示性更为可靠。

🔮 哲学思考

命理分析揭示的是可能性与趋势，而非绝对的宿命。
每个人都拥有通过自身努力改变命运走向的力量...
```

---

## 常见问题

### Q1: 如何添加新主题？

在 `ui/themes.py` 的 `BASE_THEMES` 字典中添加：

```python
"mystic": {
    "name": "神秘紫",
    "description": "神秘感的紫色主题",
    "colors": {
        "primary": "#6A1B9A",
        "secondary": "#8E24AA",
        # ... 其他颜色
    }
}
```

### Q2: 如何自定义MBTI配色？

在 `ui/themes.py` 的 `MBTI_COLOR_SCHEMES` 中修改对应类型的配色。

### Q3: 如何禁用MBTI个性化？

在调用渲染器时不传递 `mbti_type` 参数即可：

```python
ReportRenderer.render_executive_summary(report, theme="light", mbti_type=None)
```

### Q4: 性能会受影响吗？

不会。Markdown渲染是Qt原生支持的，性能优秀。生成样式表只需毫秒级时间。

---

## 技术支持

如有问题或建议，请查阅：
- 完整优化方案: `docs/REPORT_OPTIMIZATION_GUIDE.md`
- 主题系统源码: `ui/themes.py`
- 渲染器源码: `ui/report_renderer.py`
