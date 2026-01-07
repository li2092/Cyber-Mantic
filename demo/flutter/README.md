# 赛博玄数 Flutter Desktop Demo

一个使用 Flutter 构建的跨平台桌面应用 Demo，采用现代化玻璃拟态设计风格。

## 特性

- **跨平台**: 一套代码支持 Windows、macOS、Linux、Web、iOS、Android
- **玻璃拟态设计**: 毛玻璃效果、透明度层次、柔和渐变
- **深色主题**: 护眼设计，科技感强
- **响应式布局**: 自适应不同屏幕尺寸
- **流畅动画**: 微交互增强用户体验

## 环境要求

- Flutter SDK >= 3.0.0
- Dart SDK >= 3.0.0

## 快速开始

### 1. 安装 Flutter

参考官方文档: https://docs.flutter.dev/get-started/install

### 2. 启用桌面支持

```bash
# Windows
flutter config --enable-windows-desktop

# macOS
flutter config --enable-macos-desktop

# Linux
flutter config --enable-linux-desktop
```

### 3. 安装依赖

```bash
cd demo/flutter
flutter pub get
```

### 4. 运行应用

```bash
# 桌面运行
flutter run -d windows    # Windows
flutter run -d macos      # macOS
flutter run -d linux      # Linux

# Web运行
flutter run -d chrome

# 列出可用设备
flutter devices
```

## 项目结构

```
lib/
├── main.dart                 # 应用入口
├── theme/
│   └── app_theme.dart       # 主题配置（颜色、字体、样式）
├── widgets/
│   ├── widgets.dart         # 组件导出
│   ├── glass_card.dart      # 玻璃卡片组件
│   ├── nav_button.dart      # 导航按钮组件
│   ├── chat_widgets.dart    # 聊天相关组件
│   ├── bazi_widgets.dart    # 八字命盘组件
│   └── quick_action.dart    # 快捷操作组件
├── pages/
│   └── home_page.dart       # 主页面
└── models/                  # 数据模型（待扩展）
```

## 核心组件

### GlassCard
玻璃拟态卡片容器，支持标题、尾部操作、悬停效果。

```dart
GlassCard(
  title: '💬  智能问答',
  trailing: Widget?,
  child: YourContent(),
)
```

### StatCard
统计数据展示卡片，支持图标、数值、趋势指示。

```dart
StatCard(
  icon: '📊',
  value: '128',
  label: '本月分析次数',
  trend: '↑ 12%',
  trendUp: true,
)
```

### NavButton
侧边栏导航按钮，支持图标、标签、徽章、激活状态。

```dart
NavButton(
  icon: '💬',
  label: '问道',
  badge: 'New',
  isActive: true,
  onTap: () {},
)
```

### ChatBubble
聊天消息气泡，自动区分用户/AI消息样式。

```dart
ChatBubble(
  message: ChatMessage(
    content: '消息内容',
    isUser: false,
  ),
)
```

### BaZiFourPillars
八字四柱展示组件。

```dart
BaZiFourPillars(
  pillars: [
    {'label': '年柱', 'gan': '甲', 'zhi': '子'},
    // ...
  ],
)
```

### WuXingDistribution
五行分布可视化组件。

```dart
WuXingDistribution(
  distribution: {'木': 2, '火': 3, '土': 2, '金': 1, '水': 0},
)
```

## 主题配置

主题在 `lib/theme/app_theme.dart` 中定义：

```dart
// 主色调
AppTheme.primary        // #6366F1 玄青紫
AppTheme.primaryLight   // #818CF8
AppTheme.primaryDark    // #4F46E5

// 强调色
AppTheme.accent         // #F59E0B 丹朱橙
AppTheme.accentLight    // #FBBF24

// 背景色
AppTheme.bgPrimary      // #0F0F1A
AppTheme.bgSecondary    // #1A1A2E
AppTheme.bgTertiary     // #252542
AppTheme.bgCard         // rgba(30, 30, 50, 0.6)

// 文字色
AppTheme.textPrimary    // #F1F5F9
AppTheme.textSecondary  // #94A3B8
AppTheme.textMuted      // #64748B
```

## 构建发布

```bash
# Windows
flutter build windows

# macOS
flutter build macos

# Linux
flutter build linux

# Web
flutter build web
```

构建产物位于 `build/` 目录。

## 扩展建议

1. **状态管理**: 集成 Provider/Riverpod/Bloc
2. **路由管理**: 使用 go_router 实现页面导航
3. **本地存储**: 集成 Hive/SharedPreferences
4. **网络请求**: 使用 Dio 实现 API 调用
5. **国际化**: 使用 flutter_localizations

## 依赖说明

```yaml
dependencies:
  google_fonts: ^6.1.0      # Google字体
  flutter_animate: ^4.3.0   # 动画增强
  glassmorphism: ^3.0.0     # 玻璃效果
  provider: ^6.1.1          # 状态管理
  intl: ^0.18.1             # 国际化
```

---

*Demo 版本: v1.0*
*创建时间: 2026-01-06*
