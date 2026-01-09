"""
UI主题系统 - 支持多主题和MBTI个性化配色
"""
from typing import Dict, Any


class ThemeSystem:
    """主题系统"""

    # ==================== 基础主题 ====================

    # ==================== Glassmorphism风格配色 ====================

    BASE_THEMES = {
        "light": {
            "name": "清雅白",
            "description": "现代简洁的玻璃态风格",
            "colors": {
                # 背景色系
                "background": "#f8fafc",           # 主背景
                "background_secondary": "#f1f5f9", # 次背景
                "surface": "rgba(255,255,255,0.8)", # 卡片/表面（玻璃态）
                "input_bg": "#ffffff",             # 输入框背景

                # 品牌色（共用）
                "primary": "#6366f1",              # 玄青紫 - 主强调
                "secondary": "#f59e0b",            # 丹朱橙 - 辅强调
                "accent": "#06b6d4",               # 青蓝 - 科技色

                # 文字色
                "text_primary": "#1e293b",         # 主文字
                "text_secondary": "#64748b",       # 次要文字
                "text_muted": "#94a3b8",           # 灰色文字

                # 功能色
                "success": "#10b981",              # 成功/吉
                "warning": "#f59e0b",              # 警告/平
                "error": "#ef4444",                # 错误/凶

                # 边框和阴影
                "border": "rgba(0,0,0,0.08)",      # 边框
                "hover_bg": "rgba(99,102,241,0.08)", # 悬停背景
                "shadow": "rgba(0,0,0,0.1)"        # 阴影
            }
        },
        "dark": {
            "name": "墨夜黑",
            "description": "护眼的玻璃态深色主题",
            "colors": {
                # 背景色系
                "background": "#0f0f1a",           # 主背景
                "background_secondary": "#1a1a2e", # 次背景
                "surface": "rgba(30,30,50,0.6)",   # 卡片/表面（玻璃态）
                "input_bg": "#252542",             # 输入框背景

                # 品牌色（共用）
                "primary": "#6366f1",              # 玄青紫 - 主强调
                "secondary": "#f59e0b",            # 丹朱橙 - 辅强调
                "accent": "#06b6d4",               # 青蓝 - 科技色

                # 文字色
                "text_primary": "#f1f5f9",         # 主文字
                "text_secondary": "#94a3b8",       # 次要文字
                "text_muted": "#64748b",           # 灰色文字

                # 功能色
                "success": "#10b981",              # 成功/吉
                "warning": "#f59e0b",              # 警告/平
                "error": "#ef4444",                # 错误/凶

                # 边框和阴影
                "border": "rgba(255,255,255,0.08)", # 边框
                "hover_bg": "rgba(99,102,241,0.1)", # 悬停背景
                "shadow": "rgba(0,0,0,0.3)"        # 阴影
            }
        }
    }

    # ==================== MBTI个性化配色 ====================

    MBTI_COLOR_SCHEMES = {
        # NT类型 - 理性分析师（冷色调，高对比）
        "INTJ": {
            "accent": "#5E35B1",      # 深紫色 - 战略性
            "gradient": ["#5E35B1", "#3949AB"],
            "card_bg": "#F3E5F5"
        },
        "INTP": {
            "accent": "#1976D2",      # 深蓝色 - 逻辑性
            "gradient": ["#1976D2", "#0288D1"],
            "card_bg": "#E3F2FD"
        },
        "ENTJ": {
            "accent": "#D32F2F",      # 红色 - 果断性
            "gradient": ["#D32F2F", "#C62828"],
            "card_bg": "#FFEBEE"
        },
        "ENTP": {
            "accent": "#0097A7",      # 青色 - 创新性
            "gradient": ["#0097A7", "#00838F"],
            "card_bg": "#E0F7FA"
        },

        # NF类型 - 理想主义外交官（暖色调，柔和）
        "INFJ": {
            "accent": "#7B1FA2",      # 紫色 - 深邃性
            "gradient": ["#7B1FA2", "#6A1B9A"],
            "card_bg": "#F3E5F5"
        },
        "INFP": {
            "accent": "#5C6BC0",      # 靛蓝色 - 理想性
            "gradient": ["#5C6BC0", "#3F51B5"],
            "card_bg": "#E8EAF6"
        },
        "ENFJ": {
            "accent": "#E91E63",      # 粉红色 - 热情性
            "gradient": ["#E91E63", "#C2185B"],
            "card_bg": "#FCE4EC"
        },
        "ENFP": {
            "accent": "#FF6F00",      # 橙色 - 活力性
            "gradient": ["#FF6F00", "#F57C00"],
            "card_bg": "#FFF3E0"
        },

        # SJ类型 - 传统守护者（稳重色调）
        "ISTJ": {
            "accent": "#455A64",      # 蓝灰色 - 可靠性
            "gradient": ["#455A64", "#37474F"],
            "card_bg": "#ECEFF1"
        },
        "ISFJ": {
            "accent": "#6D4C41",      # 棕色 - 温和性
            "gradient": ["#6D4C41", "#5D4037"],
            "card_bg": "#EFEBE9"
        },
        "ESTJ": {
            "accent": "#1565C0",      # 蓝色 - 执行力
            "gradient": ["#1565C0", "#0D47A1"],
            "card_bg": "#E3F2FD"
        },
        "ESFJ": {
            "accent": "#C2185B",      # 玫红色 - 和谐性
            "gradient": ["#C2185B", "#AD1457"],
            "card_bg": "#FCE4EC"
        },

        # SP类型 - 灵活探险家（鲜明色调）
        "ISTP": {
            "accent": "#00695C",      # 绿松石 - 实用性
            "gradient": ["#00695C", "#004D40"],
            "card_bg": "#E0F2F1"
        },
        "ISFP": {
            "accent": "#8E24AA",      # 紫罗兰 - 艺术性
            "gradient": ["#8E24AA", "#7B1FA2"],
            "card_bg": "#F3E5F5"
        },
        "ESTP": {
            "accent": "#EF6C00",      # 深橙色 - 冒险性
            "gradient": ["#EF6C00", "#E65100"],
            "card_bg": "#FFF3E0"
        },
        "ESFP": {
            "accent": "#F4511E",      # 亮橙色 - 表演性
            "gradient": ["#F4511E", "#E64A19"],
            "card_bg": "#FBE9E7"
        }
    }

    # ==================== 吉凶配色方案 ====================

    JUDGMENT_COLORS = {
        "大吉": {
            "color": "#2E7D32",
            "bg": "#E8F5E9",
            "icon": "🌟",
            "gradient": ["#43A047", "#2E7D32"]
        },
        "吉": {
            "color": "#388E3C",
            "bg": "#F1F8E9",
            "icon": "✨",
            "gradient": ["#66BB6A", "#388E3C"]
        },
        "平": {
            "color": "#F57C00",
            "bg": "#FFF3E0",
            "icon": "⚖️",
            "gradient": ["#FFA726", "#F57C00"]
        },
        "凶": {
            "color": "#D32F2F",
            "bg": "#FFEBEE",
            "icon": "⚠️",
            "gradient": ["#E57373", "#D32F2F"]
        },
        "大凶": {
            "color": "#B71C1C",
            "bg": "#FFCDD2",
            "icon": "🚫",
            "gradient": ["#EF5350", "#B71C1C"]
        }
    }

    @classmethod
    def get_theme(cls, theme_name: str = "light") -> Dict[str, Any]:
        """获取主题配置"""
        return cls.BASE_THEMES.get(theme_name, cls.BASE_THEMES["light"])

    @classmethod
    def get_mbti_colors(cls, mbti_type: str) -> Dict[str, Any]:
        """获取MBTI个性化配色"""
        return cls.MBTI_COLOR_SCHEMES.get(mbti_type, {
            "accent": "#2E5266",
            "gradient": ["#2E5266", "#6E8898"],
            "card_bg": "#F5F5F5"
        })

    @classmethod
    def get_judgment_style(cls, judgment: str) -> Dict[str, Any]:
        """获取吉凶判断的样式"""
        return cls.JUDGMENT_COLORS.get(judgment, cls.JUDGMENT_COLORS["平"])

    @classmethod
    def generate_qss_stylesheet(cls, theme_name: str = "dark", mbti_type: str = None) -> str:
        """
        生成Glassmorphism风格Qt样式表（QSS）

        Args:
            theme_name: 主题名称 (dark/light)
            mbti_type: MBTI类型（可选，用于个性化）

        Returns:
            QSS样式字符串
        """
        theme = cls.get_theme(theme_name)
        c = theme["colors"]

        # 获取背景色（兼容旧字段）
        bg = c.get('background', '#0f0f1a')
        bg_secondary = c.get('background_secondary', c.get('surface', '#1a1a2e'))
        surface = c.get('surface', 'rgba(30,30,50,0.6)')
        input_bg = c.get('input_bg', '#252542')

        qss = f"""
        /* ==================== Glassmorphism全局样式 ==================== */
        QMainWindow, QWidget {{
            background-color: {bg};
            color: {c['text_primary']};
            font-family: "Microsoft YaHei", "Noto Sans SC", sans-serif;
        }}

        /* ==================== 玻璃态卡片 (GlassCard) ==================== */
        QGroupBox {{
            background-color: {surface};
            border: 1px solid {c['border']};
            border-radius: 16px;
            margin-top: 16px;
            padding: 20px;
            font-weight: 500;
            color: {c['text_primary']};
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 6px 16px;
            background-color: {c['primary']};
            color: white;
            border-radius: 8px;
            margin-left: 12px;
            font-size: 14px;
        }}

        /* ==================== 主按钮样式 ==================== */
        QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                        stop:0 {c['primary']}, stop:1 #4f46e5);
            color: white;
            border: none;
            border-radius: 10px;
            padding: 10px 20px;
            font-size: 14px;
            font-weight: 500;
        }}

        QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                        stop:0 #818cf8, stop:1 {c['primary']});
        }}

        QPushButton:pressed {{
            background-color: #4f46e5;
        }}

        QPushButton:disabled {{
            background-color: {c['border']};
            color: {c['text_muted']};
        }}

        /* 次要按钮 */
        QPushButton[secondary="true"] {{
            background-color: {surface};
            color: {c['text_primary']};
            border: 1px solid {c['border']};
        }}

        QPushButton[secondary="true"]:hover {{
            border-color: {c['primary']};
        }}

        /* ==================== 输入框样式 ==================== */
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {input_bg};
            border: 1px solid {c['border']};
            border-radius: 10px;
            padding: 10px 14px;
            color: {c['text_primary']};
            font-size: 14px;
            selection-background-color: {c['primary']};
        }}

        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border-color: {c['primary']};
        }}

        QLineEdit:disabled, QTextEdit:disabled {{
            background-color: {bg_secondary};
            color: {c['text_muted']};
        }}

        /* ==================== 下拉框/数值框 ==================== */
        QComboBox, QSpinBox, QDoubleSpinBox, QDateTimeEdit {{
            background-color: {input_bg};
            border: 1px solid {c['border']};
            border-radius: 8px;
            padding: 8px 12px;
            color: {c['text_primary']};
            font-size: 13px;
        }}

        QComboBox:focus, QSpinBox:focus {{
            border-color: {c['primary']};
        }}

        QComboBox::drop-down {{
            border: none;
            width: 24px;
        }}

        QComboBox QAbstractItemView {{
            background-color: {surface};
            border: 1px solid {c['border']};
            border-radius: 8px;
            padding: 4px;
            outline: none;
        }}

        QComboBox QAbstractItemView::item {{
            background-color: {surface};
            color: {c['text_primary']};
            padding: 8px 12px;
            min-height: 24px;
        }}

        QComboBox QAbstractItemView::item:hover {{
            background-color: {c['surface_hover']};
            color: {c['text_primary']};
        }}

        QComboBox QAbstractItemView::item:selected {{
            background-color: {c['primary']};
            color: white;
        }}

        /* ==================== 标签页样式 ==================== */
        QTabWidget::pane {{
            border: 1px solid {c['border']};
            border-radius: 12px;
            background-color: {surface};
            padding: 16px;
        }}

        QTabBar::tab {{
            background: {input_bg};
            color: {c['text_secondary']};
            border: none;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            padding: 10px 20px;
            margin-right: 4px;
            font-size: 13px;
        }}

        QTabBar::tab:selected {{
            background: {c['primary']};
            color: white;
        }}

        QTabBar::tab:hover:!selected {{
            background: {c.get('hover_bg', 'rgba(99,102,241,0.1)')};
            color: {c['text_primary']};
        }}

        /* ==================== 进度条样式 ==================== */
        QProgressBar {{
            border: none;
            border-radius: 4px;
            text-align: center;
            background-color: {input_bg};
            color: {c['text_primary']};
            font-size: 12px;
            height: 8px;
        }}

        QProgressBar::chunk {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                        stop:0 {c['accent']}, stop:1 {c['primary']});
            border-radius: 4px;
        }}

        /* ==================== 复选框样式 ==================== */
        QCheckBox {{
            color: {c['text_primary']};
            spacing: 10px;
            font-size: 13px;
        }}

        QCheckBox::indicator {{
            width: 20px;
            height: 20px;
            border: 2px solid {c['border']};
            border-radius: 6px;
            background-color: {input_bg};
        }}

        QCheckBox::indicator:checked {{
            background-color: {c['primary']};
            border-color: {c['primary']};
        }}

        QCheckBox::indicator:hover {{
            border-color: {c['primary']};
        }}

        /* ==================== 滚动条样式 ==================== */
        QScrollBar:vertical {{
            background: {bg_secondary};
            width: 8px;
            border-radius: 4px;
        }}

        QScrollBar::handle:vertical {{
            background: {input_bg};
            border-radius: 4px;
            min-height: 30px;
        }}

        QScrollBar::handle:vertical:hover {{
            background: {c['primary']};
        }}

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}

        QScrollBar:horizontal {{
            background: {bg_secondary};
            height: 8px;
            border-radius: 4px;
        }}

        QScrollBar::handle:horizontal {{
            background: {input_bg};
            border-radius: 4px;
            min-width: 30px;
        }}

        /* ==================== 标签样式 ==================== */
        QLabel {{
            color: {c['text_primary']};
            font-size: 13px;
        }}

        QLabel[heading="true"] {{
            font-size: 16px;
            font-weight: 600;
        }}

        QLabel[muted="true"] {{
            color: {c['text_muted']};
            font-size: 12px;
        }}

        /* ==================== 表格样式 ==================== */
        QTableWidget, QTableView {{
            background-color: {surface};
            alternate-background-color: {bg_secondary};
            border: 1px solid {c['border']};
            border-radius: 12px;
            gridline-color: {c['border']};
            font-size: 13px;
        }}

        QTableWidget::item {{
            padding: 8px 12px;
        }}

        QTableWidget::item:selected {{
            background-color: {c['primary']};
            color: white;
        }}

        QTableWidget::item:hover {{
            background-color: {c.get('hover_bg', 'rgba(99,102,241,0.1)')};
        }}

        QHeaderView::section {{
            background-color: {input_bg};
            color: {c['text_muted']};
            padding: 10px 12px;
            border: none;
            border-bottom: 1px solid {c['border']};
            font-weight: 500;
            font-size: 12px;
        }}

        /* ==================== 列表样式 ==================== */
        QListWidget {{
            background-color: {surface};
            border: 1px solid {c['border']};
            border-radius: 12px;
            padding: 8px;
        }}

        QListWidget::item {{
            padding: 10px 12px;
            border-radius: 8px;
            margin: 2px 0;
        }}

        QListWidget::item:selected {{
            background-color: rgba(99,102,241,0.15);
            color: {c['primary']};
        }}

        QListWidget::item:hover {{
            background-color: {c.get('hover_bg', 'rgba(99,102,241,0.1)')};
        }}

        /* ==================== 树形控件样式 ==================== */
        QTreeWidget, QTreeView {{
            background-color: {surface};
            border: 1px solid {c['border']};
            border-radius: 12px;
        }}

        QTreeWidget::item {{
            padding: 6px 8px;
            border-radius: 6px;
        }}

        QTreeWidget::item:selected {{
            background-color: rgba(99,102,241,0.15);
            color: {c['primary']};
        }}

        /* ==================== 分割线 ==================== */
        QFrame[frameShape="4"], QFrame[frameShape="5"] {{
            background-color: {c['border']};
        }}

        /* ==================== 工具提示 ==================== */
        QToolTip {{
            background-color: {bg_secondary};
            color: {c['text_primary']};
            border: 1px solid {c['border']};
            border-radius: 8px;
            padding: 8px 12px;
            font-size: 12px;
        }}

        /* ==================== 菜单样式 ==================== */
        QMenu {{
            background-color: {bg_secondary};
            border: 1px solid {c['border']};
            border-radius: 12px;
            padding: 8px;
        }}

        QMenu::item {{
            padding: 8px 24px;
            border-radius: 6px;
        }}

        QMenu::item:selected {{
            background-color: {c.get('hover_bg', 'rgba(99,102,241,0.1)')};
        }}

        /* ==================== 对话框样式 ==================== */
        QDialog {{
            background-color: {bg};
        }}

        QMessageBox {{
            background-color: {bg_secondary};
        }}
        """

        return qss
