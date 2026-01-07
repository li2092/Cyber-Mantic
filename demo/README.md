# 赛博玄数 UI Demo

本目录包含两个现代化UI设计Demo，供UI重构参考。

## 设计理念

### 视觉风格
- **玻璃拟态 (Glassmorphism)** - 毛玻璃效果、透明度层次
- **深色主题** - 护眼、科技感、沉浸式体验
- **柔和渐变** - 主色调紫青色系 + 强调色丹朱色系
- **流畅动画** - 微交互增强用户体验

### 配色方案
```
主色调 (玄青色系):
  - Primary: #6366f1
  - Primary Light: #818cf8
  - Primary Dark: #4f46e5

强调色 (丹朱色系):
  - Accent: #f59e0b
  - Accent Light: #fbbf24

状态色:
  - Success: #10b981
  - Warning: #f59e0b
  - Danger: #ef4444

背景色:
  - Primary BG: #0f0f1a
  - Secondary BG: #1a1a2e
  - Tertiary BG: #252542
  - Card BG: rgba(30, 30, 50, 0.6)

文字色:
  - Primary Text: #f1f5f9
  - Secondary Text: #94a3b8
  - Muted Text: #64748b
```

---

## B/S 架构 Demo (Web)

### 文件位置
```
demo/web/index.html
```

### 运行方式
直接在浏览器中打开 `index.html` 文件即可预览。

```bash
# 或者启动本地服务器
cd demo/web
python -m http.server 8080
# 然后访问 http://localhost:8080
```

### 技术栈
- HTML5 + CSS3 + JavaScript
- 响应式设计
- CSS Grid / Flexbox 布局
- CSS 动画和过渡效果
- 无需任何依赖

### 特性
- 玻璃拟态卡片效果
- 动态渐变背景
- 侧边栏导航
- 实时聊天界面
- 八字命盘展示
- 五行分布可视化
- 统计数据卡片
- 快捷操作入口

---

## C/S 架构 Demo (PyQt6 Desktop)

### 文件位置
```
demo/desktop/main.py
```

### 运行方式
```bash
# 确保已安装 PyQt6
pip install PyQt6

# 运行Demo
cd demo/desktop
python main.py
```

### 技术栈
- Python 3.8+
- PyQt6
- QSS 样式表
- 自定义组件

### 特性
- 现代化深色主题
- 自定义导航按钮组件
- 玻璃效果卡片组件
- 统计数据卡片组件
- 聊天气泡组件
- 八字柱位展示组件
- 五行指示器组件
- 快捷操作按钮组件
- 阴影效果
- 平滑过渡动画

---

## 组件架构

### 核心组件

| 组件 | 用途 | B/S | C/S |
|------|------|-----|-----|
| NavButton | 侧边栏导航按钮 | CSS类 | NavButton类 |
| GlassCard | 玻璃拟态卡片 | .card类 | GlassCard类 |
| StatCard | 统计数据卡片 | .stat-card类 | StatCard类 |
| ChatBubble | 聊天消息气泡 | .message类 | ChatBubble类 |
| BaZiPillar | 八字柱位展示 | .pillar类 | BaZiPillar类 |
| WuXingIndicator | 五行元素指示器 | .wuxing-item类 | WuXingIndicator类 |
| QuickAction | 快捷操作按钮 | .quick-action类 | QuickActionButton类 |

### 布局结构

```
App Container
├── Sidebar (固定宽度 260-280px)
│   ├── Logo Area
│   ├── Navigation Menu
│   │   ├── Section: 核心功能
│   │   │   ├── 问道
│   │   │   ├── 推演
│   │   │   └── 典籍
│   │   ├── Section: 个人中心
│   │   │   ├── 洞察
│   │   │   └── 历史记录
│   │   └── Section: 系统
│   │       ├── 设置
│   │       └── 帮助
│   └── User Card
│
└── Main Content
    ├── Top Bar
    │   ├── Page Title
    │   ├── Search Box
    │   └── Action Buttons
    │
    └── Content Area (Scrollable)
        ├── Welcome Banner
        ├── Stats Grid (4列响应式)
        └── Main Grid (2:1比例)
            ├── Left: Chat Section
            │   ├── Messages List
            │   └── Input Area
            │
            └── Right: Info Panel
                ├── BaZi Chart
                │   ├── Four Pillars
                │   └── WuXing Distribution
                ├── Quick Actions (2x2 Grid)
                └── Recent History
```

---

## 设计规范

### 间距系统
```
4px  - 最小间距
8px  - 紧凑间距
12px - 标准间距
16px - 舒适间距
24px - 区块间距
32px - 大区块间距
```

### 圆角系统
```
8px  - Small (小按钮、标签)
12px - Medium (卡片、输入框)
16px - Large (大卡片)
24px - XL (横幅、大面板)
50%  - 圆形 (头像、指示器)
```

### 阴影系统
```
Shadow SM: 0 2px 8px rgba(0, 0, 0, 0.3)
Shadow MD: 0 4px 16px rgba(0, 0, 0, 0.4)
Shadow LG: 0 8px 32px rgba(0, 0, 0, 0.5)
Shadow Glow: 0 0 40px rgba(99, 102, 241, 0.15)
```

### 字体系统
```
正文: Noto Sans SC / Microsoft YaHei
标题: Noto Serif SC (中文传统感)
代码: Monospace

字号:
  - 10px: 标签、提示
  - 12px: 次要信息
  - 13px: 辅助文字
  - 14px: 正文
  - 16px: 小标题
  - 18px: 页面标题
  - 20px: 大标题
  - 24px: 欢迎标题
  - 28-32px: 统计数字
```

---

## 交互规范

### 悬停效果
- 卡片: 轻微上移 + 边框高亮 + 阴影加深
- 按钮: 背景变亮 + 可选缩放
- 导航: 背景色变化 + 文字高亮

### 过渡时间
```
Fast: 0.15s (悬停反馈)
Normal: 0.25s (状态切换)
Slow: 0.4s (页面过渡)
```

### 动画曲线
```
ease: 通用
ease-in-out: 平滑过渡
ease-out: 弹出效果
```

---

## 后续建议

### Web版本扩展
1. 使用 Vue 3 / React 组件化重构
2. 添加 Tailwind CSS 提高开发效率
3. 集成 Chart.js 实现数据可视化
4. 添加 WebSocket 实时通信
5. PWA 支持离线访问

### Desktop版本扩展
1. 提取组件到独立模块
2. 实现主题切换功能
3. 添加动画效果 (QPropertyAnimation)
4. 集成 matplotlib 可视化
5. 优化性能和内存占用

---

*Demo 版本: v1.0*
*创建时间: 2026-01-06*
