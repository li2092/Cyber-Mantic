# 资源文件说明

本文件夹存放应用程序的静态资源文件。

## Logo 文件

请将以下 logo 文件放置在此文件夹：

### 1. app_icon.png（应用图标）
- **来源**：原 logo1.png
- **规格**：圆形logo，透明背景，无文字
- **用途**：
  - 应用程序窗口图标
  - 任务栏图标
  - 系统托盘图标

### 2. app_logo_full.png（完整Logo）
- **来源**：原 logo2.png
- **规格**：正方形，白色背景，带文字
- **用途**：
  - 关于对话框中的产品logo
  - 启动界面（如有）
  - 帮助文档封面

## 文件夹结构

```
ui/resources/
├── README.md          # 本文件
├── app_icon.png       # 圆形应用图标（来自logo1.png）
└── app_logo_full.png  # 完整产品logo（来自logo2.png）
```

## 使用示例

```python
from PyQt6.QtGui import QIcon, QPixmap
from pathlib import Path

# 获取资源文件路径
RESOURCES_DIR = Path(__file__).parent / "resources"

# 设置窗口图标
icon = QIcon(str(RESOURCES_DIR / "app_icon.png"))
window.setWindowIcon(icon)

# 加载完整logo
pixmap = QPixmap(str(RESOURCES_DIR / "app_logo_full.png"))
label.setPixmap(pixmap)
```

## 注意事项

1. 确保图片文件格式为 PNG（支持透明背景）
2. 建议图标尺寸：
   - app_icon.png: 256x256px 或更高（保持正方形）
   - app_logo_full.png: 建议宽高比 1:1，至少 512x512px
3. 文件名必须与上述规范一致，否则应用程序无法加载
