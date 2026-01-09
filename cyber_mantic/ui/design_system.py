"""
设计系统规范 - Design System

统一定义所有 UI 组件的视觉规范，确保界面一致性和美观性。

参考：
- Claude.ai 设计风格（现代、简洁、优雅）
- Material Design 3（间距、圆角、阴影）
- Tailwind CSS（色彩系统）
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class Spacing:
    """间距系统 - 8px 基准"""
    xs: int = 4      # 0.5x
    sm: int = 8      # 1x
    md: int = 16     # 2x
    lg: int = 24     # 3x
    xl: int = 32     # 4x
    xxl: int = 48    # 6x


@dataclass
class BorderRadius:
    """圆角系统"""
    sm: int = 4      # 小圆角（按钮、输入框）
    md: int = 8      # 中圆角（卡片）
    lg: int = 12     # 大圆角（弹窗）
    xl: int = 16     # 超大圆角（特殊卡片）
    full: int = 9999  # 完全圆角（头像、标签）


@dataclass
class FontSize:
    """字体大小系统"""
    xs: int = 11     # 辅助文字
    sm: int = 13     # 次要文字
    base: int = 14   # 正文
    md: int = 16     # 强调文字
    lg: int = 18     # 小标题
    xl: int = 20     # 标题
    xxl: int = 24    # 大标题
    xxxl: int = 32   # 超大标题


@dataclass
class FontWeight:
    """字重系统"""
    light: int = 300
    normal: int = 400
    medium: int = 500
    semibold: int = 600
    bold: int = 700


@dataclass
class Shadow:
    """阴影系统"""
    # 格式：offset-x offset-y blur-radius color
    sm: str = "0 1px 2px 0 rgba(0, 0, 0, 0.05)"
    base: str = "0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)"
    md: str = "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)"
    lg: str = "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)"
    xl: str = "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)"


@dataclass
class IconSet:
    """专业图标系统（使用 Unicode 字符 + Nerd Fonts）"""
    # 导航图标
    chat: str = "󰭻"          # 问道/对话
    analysis: str = "󰄬"      # 推演/分析
    library: str = "󰂺"       # 典籍/书籍
    insight: str = "󰀄"       # 洞察/眼睛
    history: str = "󰋚"       # 历史/时钟
    settings: str = "󰒓"      # 设置/齿轮
    about: str = "󰋼"         # 关于/信息

    # 功能图标
    send: str = "󰏍"          # 发送
    save: str = "󰆓"          # 保存
    export: str = "󰆏"        # 导出
    refresh: str = "󰑓"       # 刷新
    search: str = "󰍉"        # 搜索
    close: str = "󰅖"         # 关闭
    menu: str = "󰍜"          # 菜单
    expand: str = "󰁌"        # 展开
    collapse: str = "󰁍"      # 收起

    # 状态图标
    success: str = "󰄬"       # 成功/勾选
    error: str = "󰅙"         # 错误/叉号
    warning: str = "󰀪"       # 警告
    info: str = "󰋼"          # 信息
    loading: str = "󰔟"       # 加载中

    # 理论图标
    bazi: str = "󰀠"          # 八字
    ziwei: str = "󰽥"         # 紫微
    qimen: str = "󰘦"         # 奇门
    liuyao: str = "󰐿"        # 六爻
    meihua: str = "󰦔"        # 梅花
    cezi: str = "󰅐"          # 测字

    @classmethod
    def get_fallback(cls, key: str) -> str:
        """获取 fallback 图标（当字体不支持时）"""
        fallbacks = {
            "chat": "💬",
            "analysis": "📊",
            "library": "📚",
            "insight": "👁",
            "history": "📜",
            "settings": "⚙",
            "about": "ℹ",
            "send": "➤",
            "save": "💾",
            "export": "📤",
            "refresh": "🔄",
            "search": "🔍",
            "close": "✕",
        }
        return fallbacks.get(key, "●")


class Colors:
    """颜色系统"""

    # 主色调（紫色系 - 神秘、科技感）
    primary = {
        50: "#f5f3ff",
        100: "#ede9fe",
        200: "#ddd6fe",
        300: "#c4b5fd",
        400: "#a78bfa",
        500: "#8b5cf6",  # 主色
        600: "#7c3aed",
        700: "#6d28d9",
        800: "#5b21b6",
        900: "#4c1d95",
    }

    # 中性色（灰色系）
    gray = {
        50: "#f9fafb",
        100: "#f3f4f6",
        200: "#e5e7eb",
        300: "#d1d5db",
        400: "#9ca3af",
        500: "#6b7280",
        600: "#4b5563",
        700: "#374151",
        800: "#1f2937",
        900: "#111827",
    }

    # 语义色
    success = "#10b981"   # 绿色
    warning = "#f59e0b"   # 橙色
    error = "#ef4444"     # 红色
    info = "#3b82f6"      # 蓝色


class DesignTokens:
    """设计令牌 - 组件级别的样式定义"""

    # 按钮样式
    button = {
        "primary": {
            "bg": Colors.primary[500],
            "bg_hover": Colors.primary[600],
            "text": "#ffffff",
            "radius": BorderRadius.md,
            "padding": f"{Spacing.sm}px {Spacing.lg}px",
            "font_size": FontSize.base,
            "font_weight": FontWeight.medium,
            "shadow": Shadow.sm,
            "shadow_hover": Shadow.md,
        },
        "secondary": {
            "bg": Colors.gray[100],
            "bg_hover": Colors.gray[200],
            "text": Colors.gray[700],
            "radius": BorderRadius.md,
            "padding": f"{Spacing.sm}px {Spacing.lg}px",
            "font_size": FontSize.base,
            "font_weight": FontWeight.normal,
            "shadow": Shadow.sm,
        }
    }

    # 卡片样式
    card = {
        "bg": "#ffffff",
        "border": f"1px solid {Colors.gray[200]}",
        "radius": BorderRadius.lg,
        "padding": Spacing.lg,
        "shadow": Shadow.base,
        "shadow_hover": Shadow.md,
    }

    # 输入框样式
    input = {
        "bg": "#ffffff",
        "border": f"1px solid {Colors.gray[300]}",
        "border_focus": f"2px solid {Colors.primary[500]}",
        "radius": BorderRadius.md,
        "padding": f"{Spacing.sm}px {Spacing.md}px",
        "font_size": FontSize.base,
        "placeholder_color": Colors.gray[400],
    }

    # 侧边栏样式
    sidebar = {
        "bg": "#ffffff",
        "border": f"1px solid {Colors.gray[200]}",
        "width_expanded": 200,
        "width_collapsed": 64,
        "item_height": 44,
        "item_padding": Spacing.md,
        "item_radius": BorderRadius.md,
        "item_icon_size": 20,
        "item_font_size": FontSize.base,
    }

    # 聊天消息样式
    message = {
        "user": {
            "bg": Colors.primary[50],
            "text": Colors.gray[800],
            "radius": BorderRadius.lg,
            "padding": Spacing.md,
            "max_width": "70%",
        },
        "assistant": {
            "bg": "#ffffff",
            "text": Colors.gray[800],
            "radius": BorderRadius.lg,
            "padding": Spacing.md,
            "max_width": "85%",
            "border": f"1px solid {Colors.gray[200]}",
        }
    }


# 全局实例
spacing = Spacing()
border_radius = BorderRadius()
font_size = FontSize()
font_weight = FontWeight()
shadow = Shadow()
icons = IconSet()
colors = Colors()
tokens = DesignTokens()


def get_qss_variable(var_name: str) -> str:
    """
    获取 QSS 变量值

    用于在 QSS 样式表中引用设计系统变量
    """
    mappings = {
        # 间距
        "spacing-xs": spacing.xs,
        "spacing-sm": spacing.sm,
        "spacing-md": spacing.md,
        "spacing-lg": spacing.lg,
        "spacing-xl": spacing.xl,

        # 圆角
        "radius-sm": border_radius.sm,
        "radius-md": border_radius.md,
        "radius-lg": border_radius.lg,

        # 字号
        "font-xs": font_size.xs,
        "font-sm": font_size.sm,
        "font-base": font_size.base,
        "font-md": font_size.md,
        "font-lg": font_size.lg,

        # 颜色
        "color-primary": colors.primary[500],
        "color-primary-hover": colors.primary[600],
        "color-gray-50": colors.gray[50],
        "color-gray-100": colors.gray[100],
        "color-gray-200": colors.gray[200],
        "color-gray-300": colors.gray[300],
        "color-gray-700": colors.gray[700],
    }

    return str(mappings.get(var_name, ""))


def format_shadow_for_qss(shadow_str: str) -> str:
    """
    将阴影字符串转换为 QSS 格式

    输入：'0 4px 6px -1px rgba(0, 0, 0, 0.1)'
    输出：'0px 4px 6px -1px rgba(0, 0, 0, 0.1)'
    """
    parts = shadow_str.split()
    if len(parts) >= 3:
        # 确保单位为 px
        parts[0] = parts[0] if 'px' in parts[0] else parts[0] + 'px'
        parts[1] = parts[1] if 'px' in parts[1] else parts[1] + 'px'
        parts[2] = parts[2] if 'px' in parts[2] else parts[2] + 'px'
        return ' '.join(parts)
    return shadow_str
