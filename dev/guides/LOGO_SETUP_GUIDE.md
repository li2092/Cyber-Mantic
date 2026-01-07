# Logo 文件放置指南

## 📁 文件位置

请将您的 logo 文件放置到以下位置：

```
cyber_mantic/ui/resources/
```

## 📝 文件命名规范

### 1. app_icon.png（应用图标）

**来源**：原 `logo1.png`
**描述**：圆形logo，透明背景，无文字
**用途**：
- 应用程序窗口图标（Windows/Mac/Linux任务栏）
- 应用程序标题栏图标

**重命名步骤**：
```bash
# 如果您的文件在 cyber_mantic/ui/ 目录下
mv cyber_mantic/ui/logo1.png cyber_mantic/ui/resources/app_icon.png
```

### 2. app_logo_full.png（完整Logo）

**来源**：原 `logo2.png`
**描述**：正方形，白色背景，带文字
**用途**：
- 关于产品对话框中的产品logo展示
- 未来可能的启动界面
- 帮助文档封面

**重命名步骤**：
```bash
# 如果您的文件在 cyber_mantic/ui/ 目录下
mv cyber_mantic/ui/logo2.png cyber_mantic/ui/resources/app_logo_full.png
```

## 🎯 完整操作流程

### 方式一：使用命令行（推荐）

```bash
# 1. 进入项目根目录
cd /path/to/your/project

# 2. 确保 resources 文件夹存在（已自动创建）
ls cyber_mantic/ui/resources/

# 3. 将 logo1.png 重命名为 app_icon.png 并移动到 resources 文件夹
mv cyber_mantic/ui/logo1.png cyber_mantic/ui/resources/app_icon.png

# 4. 将 logo2.png 重命名为 app_logo_full.png 并移动到 resources 文件夹
mv cyber_mantic/ui/logo2.png cyber_mantic/ui/resources/app_logo_full.png

# 5. 验证文件已正确放置
ls -lh cyber_mantic/ui/resources/*.png
```

### 方式二：手动操作

1. 打开文件管理器
2. 找到您的 `logo1.png` 和 `logo2.png` 文件
3. 将它们移动/复制到 `cyber_mantic/ui/resources/` 文件夹
4. 分别重命名为：
   - `logo1.png` → `app_icon.png`
   - `logo2.png` → `app_logo_full.png`

## ✅ 验证是否成功

### 检查文件结构

最终的文件结构应该是：

```
cyber_mantic/ui/resources/
├── README.md            # 资源说明文档
├── app_icon.png         # 应用图标（来自logo1.png）
└── app_logo_full.png    # 完整logo（来自logo2.png）
```

### 启动应用测试

1. 启动应用程序：
   ```bash
   python gui.py
   ```

2. 检查窗口图标：
   - Windows：查看任务栏和窗口标题栏
   - Mac：查看Dock和窗口标题栏
   - Linux：查看任务栏和窗口标题栏

3. 打开"关于产品"对话框：
   - 点击"设置"标签页
   - 滚动到底部找到"ℹ️ 关于产品"部分
   - 点击"📖 查看详细介绍"按钮
   - 应该能看到完整的产品logo展示

## 🎨 建议的图片规格

### app_icon.png
- **尺寸**：256x256px 或更高（保持正方形）
- **格式**：PNG（支持透明背景）
- **背景**：透明
- **内容**：仅图形，无文字

### app_logo_full.png
- **尺寸**：至少 512x512px
- **宽高比**：建议 1:1（正方形）
- **格式**：PNG
- **背景**：白色或透明
- **内容**：完整logo + 产品名称文字

## ❓ 常见问题

### Q1: 我的logo文件不在 cyber_mantic/ui/ 文件夹下怎么办？

**答**：使用绝对路径移动文件，例如：
```bash
mv /path/to/your/logo1.png /path/to/project/cyber_mantic/ui/resources/app_icon.png
```

### Q2: 如果不放置logo文件会怎样？

**答**：应用程序仍可正常运行，只是：
- 窗口图标会使用系统默认图标
- 关于对话框中会显示文字"Cyber-Mantic"而非logo图片

### Q3: 我可以使用其他格式的图片吗？

**答**：建议使用PNG格式以获得最佳兼容性和透明度支持。如果使用JPG，需要确保背景不透明。

### Q4: logo文件可以在运行时更换吗？

**答**：可以，但需要重启应用程序才能看到新的logo。

## 📞 需要帮助？

如果遇到问题，请检查：
1. 文件路径是否正确
2. 文件名是否完全匹配（区分大小写）
3. 文件权限是否允许读取
4. 查看应用日志：`logs/cyber_mantic.log`

---

**最后更新**：2026-01-03
**版本**：v1.0
