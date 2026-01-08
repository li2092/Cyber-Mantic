"""
简化版主题系统 - Glassmorphism风格 (墨夜黑/清雅白)

设计理念：玻璃态UI设计，现代简洁，双主题支持
"""
from typing import Dict, Any


class ThemeSystem:
    """主题系统 - Glassmorphism双主题"""

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
        },
        # 保留zen主题但更新为更现代的配色
        "zen": {
            "name": "禅意灰",
            "description": "平静沉稳，适合长时间阅读",
            "colors": {
                "background": "#fafaf9",
                "background_secondary": "#f5f5f4",
                "surface": "rgba(255,255,255,0.9)",
                "input_bg": "#ffffff",
                "primary": "#78716c",
                "secondary": "#a8a29e",
                "accent": "#57534e",
                "text_primary": "#292524",
                "text_secondary": "#57534e",
                "text_muted": "#78716c",
                "success": "#84cc16",
                "warning": "#eab308",
                "error": "#dc2626",
                "border": "rgba(0,0,0,0.06)",
                "hover_bg": "rgba(120,113,108,0.08)",
                "shadow": "rgba(0,0,0,0.05)"
            }
        }
    }

    @classmethod
    def get_theme(cls, theme_name: str = "light") -> Dict[str, Any]:
        """获取主题配置"""
        return cls.BASE_THEMES.get(theme_name, cls.BASE_THEMES["light"])

    @classmethod
    def get_theme_names(cls) -> list:
        """获取所有主题名称"""
        return list(cls.BASE_THEMES.keys())

    @classmethod
    def generate_qss_stylesheet(cls, theme_name: str = "dark") -> str:
        """
        生成Glassmorphism风格Qt样式表（QSS）

        Args:
            theme_name: 主题名称 (dark/light/zen)

        Returns:
            QSS样式字符串
        """
        theme = cls.get_theme(theme_name)
        c = theme["colors"]

        # 获取背景色
        bg = c.get('background', '#0f0f1a')
        bg_secondary = c.get('background_secondary', '#1a1a2e')
        surface = c.get('surface', 'rgba(30,30,50,0.6)')
        input_bg = c.get('input_bg', '#252542')
        hover_bg = c.get('hover_bg', 'rgba(99,102,241,0.1)')

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
            padding: 8px 12px;
            min-height: 18px;
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

        QTextEdit:read-only, QTextBrowser {{
            background-color: transparent;
            border: none;
        }}

        /* ==================== 下拉框/数值框 ==================== */
        QComboBox, QSpinBox, QDoubleSpinBox, QDateTimeEdit {{
            background-color: {input_bg};
            border: 1px solid {c['border']};
            border-radius: 8px;
            padding: 6px 12px;
            min-height: 20px;
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

        QComboBox::down-arrow {{
            width: 0;
            height: 0;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid {c['text_secondary']};
        }}

        QComboBox QAbstractItemView {{
            background-color: {bg_secondary};
            border: 1px solid {c['border']};
            border-radius: 8px;
            selection-background-color: {c['primary']};
            color: {c['text_primary']};
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
            background: {hover_bg};
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

        /* ==================== 单选框样式 ==================== */
        QRadioButton {{
            color: {c['text_primary']};
            spacing: 10px;
            font-size: 13px;
        }}

        QRadioButton::indicator {{
            width: 20px;
            height: 20px;
            border: 2px solid {c['border']};
            border-radius: 10px;
            background-color: {input_bg};
        }}

        QRadioButton::indicator:checked {{
            background-color: {c['primary']};
            border-color: {c['primary']};
        }}

        QRadioButton::indicator:hover {{
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

        QScrollBar::handle:horizontal:hover {{
            background: {c['primary']};
        }}

        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}

        /* ==================== 标签样式 ==================== */
        QLabel {{
            color: {c['text_primary']};
            font-size: 13px;
            background-color: transparent;
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
            background-color: {hover_bg};
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
            background-color: {hover_bg};
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
            background-color: {hover_bg};
        }}

        /* ==================== 对话框样式 ==================== */
        QDialog {{
            background-color: {bg};
        }}

        QMessageBox {{
            background-color: {bg_secondary};
        }}

        QMessageBox QLabel {{
            color: {c['text_primary']};
            background-color: transparent;
        }}

        QMessageBox QPushButton {{
            min-width: 80px;
        }}

        /* ==================== SpinBox样式 ==================== */
        QSpinBox {{
            padding-right: 20px;
        }}

        QSpinBox::up-button, QSpinBox::down-button {{
            background-color: {c['border']};
            border: none;
            width: 20px;
            subcontrol-origin: border;
        }}

        QSpinBox::up-button {{
            subcontrol-position: top right;
            border-top-right-radius: 8px;
        }}

        QSpinBox::down-button {{
            subcontrol-position: bottom right;
            border-bottom-right-radius: 8px;
        }}

        QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
            background-color: {c['primary']};
        }}

        QSpinBox::up-arrow {{
            width: 0;
            height: 0;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-bottom: 5px solid {c['text_secondary']};
        }}

        QSpinBox::down-arrow {{
            width: 0;
            height: 0;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid {c['text_secondary']};
        }}
        """

        return qss
