"""
洞察标签页 - 用户画像与状态评估

功能：
- 使用画像：使用频率、偏好理论、问题类型等统计
- AI深度分析：基于使用数据的智能分析（需≥5次使用）
- 状态评估：当前状态与预警机制（P2完成）
  - 密集分析检测（6小时内>5次）
  - 深夜使用检测（22:00-06:00）
  - 重复问题检测
  - 实时深夜提醒
- 使用统计：本周/历史使用次数
- 典籍学习：阅读次数、文档数、笔记数、学习方向

设计参考：docs/design/03_洞察模块设计.md
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QGridLayout,
    QGroupBox, QMessageBox, QDialog, QTextEdit,
    QProgressDialog, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QPixmap
import asyncio
import json
from datetime import datetime, timedelta
from io import BytesIO

# matplotlib imports
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

from utils.usage_stats_manager import get_usage_stats_manager
from utils.notes_manager import get_notes_manager
from utils.logger import get_logger


class ProfileAnalysisWorker(QThread):
    """用户画像分析工作线程"""
    finished = pyqtSignal(str)  # 分析结果
    error = pyqtSignal(str)  # 错误信息

    def __init__(self, profile_data: dict, api_manager):
        super().__init__()
        self.profile_data = profile_data
        self.api_manager = api_manager

    def run(self):
        """执行AI分析"""
        try:
            # 构建分析prompt
            prompt = self._build_analysis_prompt()

            # 调用AI API (使用APIManager的call_api方法)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.api_manager.call_api(
                    task_type="快速交互问答",  # 使用deepseek进行分析
                    prompt=prompt,
                    enable_dual_verification=False  # 禁用双模型验证以加速
                )
            )
            loop.close()

            if result:
                self.finished.emit(result)
            else:
                self.error.emit("AI分析返回为空")

        except Exception as e:
            self.error.emit(str(e))

    def _build_analysis_prompt(self) -> str:
        """构建分析提示词"""
        data = self.profile_data

        prompt = """# 赛博玄数 - 用户画像分析

## 关于赛博玄数

「赛博玄数」是一款基于多AI引擎的中国传统术数智能分析系统。它将八字命理、紫微斗数、六爻占卜、梅花易数、奇门遁甲等传统智慧与现代AI技术相结合，为用户提供文化洞察与自我反思的工具。

产品核心功能：
- **问道**：对话式渐进分析，通过5个阶段深入了解用户问题
- **推演**：快速排盘分析，支持8大术数理论
- **典籍**：术数知识学习平台，收录经典文献
- **洞察**：个人使用画像与状态评估

## 用户画像的意义

用户画像分析是赛博玄数「洞察」模块的核心功能。我们相信：

1. **自我认知**：通过观察自己的使用轨迹，用户可以更好地了解自己当前的关注点和内心状态
2. **使用反思**：术数本质是自我反思的工具，画像分析帮助用户看到自己在探索什么、思考什么
3. **个性化服务**：了解用户偏好后，可以提供更贴合需求的内容推荐
4. **关怀提醒**：通过使用模式识别，在用户可能需要休息或帮助时给予温和提示

**重要说明**：所有数据仅存储在用户本地，不会上传到任何服务器。这份画像分析是帮助用户认识自己，而非评判用户。

---

## 用户使用数据

### 咨询与分析习惯
- 使用频率: {frequency}
- 常用时段: {time_slots}
- 偏好理论: {theories}
- 关注话题: {question_types}

### 学习与积累情况
- 典籍阅读次数: {reading_count}
- 阅读文档数: {documents_read}
- 学习笔记数: {notes_count}
- 学习方向: {reading_category}

### 使用统计
- 本周问道: {week_wendao}次
- 本周推演: {week_tuiyan}次
- 历史问道总计: {total_wendao}次
- 历史推演总计: {total_tuiyan}次

---

## 分析任务

请你作为一位温和、有洞察力的分析师，基于以上数据为用户生成一份个人画像报告。

### 分析角度
1. **当前关注**：用户近期主要在思考什么？关注哪些人生领域？
2. **探索风格**：用户倾向于对话式深入探讨(问道)还是快速获取结果(推演)？这反映了什么？
3. **学习态度**：用户是否在主动学习术数知识？学习偏好什么方向？
4. **使用模式**：从时段和频率看，用户的使用习惯如何？
5. **温馨建议**：基于以上特点，给用户一些个性化的使用建议或提醒

### 写作要求
- 使用第二人称（"您"）
- 语气温和、关怀，像一位懂您的朋友在分享观察
- 字数300-500字
- 避免说教，重在呈现观察和启发
- 如果某些数据为0或"暂无"，可以温和地鼓励用户去探索
- 结尾可以给一句温暖的话""".format(
            frequency=data.get('frequency', '暂无'),
            time_slots=data.get('time_slots', '暂无'),
            theories=data.get('theories', '暂无'),
            question_types=data.get('question_types', '暂无'),
            reading_count=data.get('reading_count', 0),
            documents_read=data.get('documents_read', 0),
            notes_count=data.get('notes_count', 0),
            reading_category=data.get('reading_category', '暂无'),
            week_wendao=data.get('week_wendao', 0),
            week_tuiyan=data.get('week_tuiyan', 0),
            total_wendao=data.get('total_wendao', 0),
            total_tuiyan=data.get('total_tuiyan', 0)
        )

        return prompt


class InsightTab(QWidget):
    """
    洞察标签页

    显示用户使用画像、AI分析、状态评估和使用统计
    """

    def __init__(self, api_manager=None, parent=None):
        super().__init__(parent)
        self._stats_manager = get_usage_stats_manager()
        self._notes_manager = get_notes_manager()
        self._api_manager = api_manager
        self.logger = get_logger(__name__)

        # 保存对值标签的引用，用于刷新
        self._profile_values = {}
        self._stats_values = {}
        self._library_values = {}
        self._ai_placeholder = None
        self._ai_refresh_btn = None
        self._ai_update_label = None
        self._analysis_worker = None

        # 状态评估相关
        self._status_value_label = None
        self._status_evaluation = None

        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        # 使用滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # 标题
        title_label = QLabel("洞察")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

        # 使用画像卡片
        profile_card = self._create_profile_card()
        layout.addWidget(profile_card)

        # 统计卡片 (4个指标)
        stats_card = self._create_stats_card()
        layout.addWidget(stats_card)

        # AI深度分析卡片 (上移)
        ai_analysis_card = self._create_ai_analysis_card()
        layout.addWidget(ai_analysis_card)

        # 趋势图表卡片 (新增)
        trend_card = self._create_trend_card()
        layout.addWidget(trend_card)

        # 状态评估卡片
        status_card = self._create_status_card()
        layout.addWidget(status_card)

        # 典籍学习卡片
        library_card = self._create_library_card()
        layout.addWidget(library_card)

        # 数据管理按钮
        data_btn = QPushButton("查看/删除我的数据")
        data_btn.clicked.connect(self._on_data_management)
        data_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                border: 1px solid #ccc;
                border-radius: 5px;
                color: #666;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
                border-color: #999;
            }
        """)
        layout.addWidget(data_btn)

        layout.addStretch()

        scroll.setWidget(content_widget)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        # 初始加载数据
        self.refresh_data()

    def _create_card(self, title: str) -> QGroupBox:
        """创建卡片容器"""
        card = QGroupBox(title)
        card.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 16px;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
                margin-top: 14px;
                padding-top: 20px;
                background-color: #fff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 4px 12px;
                color: #1E293B;
                background-color: #F1F5F9;
                border-radius: 6px;
            }
        """)
        return card

    def _create_profile_card(self) -> QGroupBox:
        """创建使用画像卡片"""
        card = self._create_card("使用画像")
        layout = QGridLayout(card)
        layout.setContentsMargins(15, 20, 15, 15)
        layout.setSpacing(15)

        # 画像数据
        profile_items = [
            ("frequency", "📊 使用频率"),
            ("time_slots", "⏰ 常用时段"),
            ("theories", "🎯 偏好理论"),
            ("question_types", "💬 问题类型"),
        ]

        for i, (key, label) in enumerate(profile_items):
            row = i // 2
            col = i % 2

            item_widget = QWidget()
            item_layout = QVBoxLayout(item_widget)
            item_layout.setContentsMargins(0, 0, 0, 0)
            item_layout.setSpacing(5)

            label_widget = QLabel(label)
            label_widget.setStyleSheet("font-size: 14px; color: #64748B;")
            item_layout.addWidget(label_widget)

            value_widget = QLabel("加载中...")
            value_widget.setStyleSheet("font-size: 15px; color: #1E293B;")
            value_widget.setWordWrap(True)
            item_layout.addWidget(value_widget)

            # 保存引用
            self._profile_values[key] = value_widget

            layout.addWidget(item_widget, row, col)

        # 提示信息
        hint_label = QLabel("使用问道/推演功能后，将自动收集使用数据")
        hint_label.setStyleSheet("font-size: 12px; color: #888; margin-top: 10px;")
        layout.addWidget(hint_label, 2, 0, 1, 2)

        return card

    def _create_library_card(self) -> QGroupBox:
        """创建典籍学习卡片"""
        card = self._create_card("典籍学习")
        layout = QGridLayout(card)
        layout.setContentsMargins(15, 20, 15, 15)
        layout.setSpacing(15)

        # 学习数据项
        library_items = [
            ("reading_count", "📖 阅读次数"),
            ("documents_read", "📚 阅读文档数"),
            ("notes_count", "📝 笔记数量"),
            ("reading_category", "🏷️ 学习方向"),
        ]

        for i, (key, label) in enumerate(library_items):
            row = i // 2
            col = i % 2

            item_widget = QWidget()
            item_layout = QVBoxLayout(item_widget)
            item_layout.setContentsMargins(0, 0, 0, 0)
            item_layout.setSpacing(5)

            label_widget = QLabel(label)
            label_widget.setStyleSheet("font-size: 14px; color: #64748B;")
            item_layout.addWidget(label_widget)

            value_widget = QLabel("加载中...")
            value_widget.setStyleSheet("font-size: 15px; color: #1E293B;")
            value_widget.setWordWrap(True)
            item_layout.addWidget(value_widget)

            # 保存引用
            self._library_values[key] = value_widget

            layout.addWidget(item_widget, row, col)

        # 提示信息
        hint_label = QLabel("阅读典籍文档后，将自动记录学习轨迹")
        hint_label.setStyleSheet("font-size: 12px; color: #888; margin-top: 10px;")
        layout.addWidget(hint_label, 2, 0, 1, 2)

        return card

    def _create_ai_analysis_card(self) -> QGroupBox:
        """创建AI深度分析卡片"""
        card = self._create_card("AI深度分析")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 20, 15, 15)
        layout.setSpacing(10)

        # AI分析内容
        ai_label = QLabel("🧠 基于您的使用数据，分析如下：")
        ai_label.setStyleSheet("font-size: 14px; color: #64748B;")
        layout.addWidget(ai_label)

        self._ai_placeholder = QLabel(
            "暂无足够数据进行分析\n\n"
            "当问道 + 推演总次数 ≥ 5 时，将启用AI深度分析功能"
        )
        self._ai_placeholder.setStyleSheet("""
            font-size: 13px;
            color: #999;
            font-style: italic;
            padding: 20px;
            background-color: #f9f9f9;
            border-radius: 5px;
        """)
        self._ai_placeholder.setWordWrap(True)
        layout.addWidget(self._ai_placeholder)

        # 刷新按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._ai_refresh_btn = QPushButton("刷新分析")
        self._ai_refresh_btn.setEnabled(False)
        self._ai_refresh_btn.clicked.connect(self._on_refresh_ai_analysis)
        self._ai_refresh_btn.setStyleSheet("""
            QPushButton {
                padding: 5px 15px;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
            QPushButton:disabled {
                color: #999;
                background-color: #f0f0f0;
            }
            QPushButton:enabled:hover {
                background-color: #e0e0e0;
            }
        """)
        btn_layout.addWidget(self._ai_refresh_btn)

        self._ai_update_label = QLabel("更新于 --")
        self._ai_update_label.setStyleSheet("font-size: 12px; color: #999;")
        btn_layout.addWidget(self._ai_update_label)

        layout.addLayout(btn_layout)

        return card

    def _create_status_card(self) -> QGroupBox:
        """创建状态评估卡片"""
        card = self._create_card("状态评估")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(15, 20, 15, 15)
        layout.setSpacing(15)

        # 当前状态
        status_widget = QWidget()
        status_layout = QVBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(5)

        status_label = QLabel("当前状态")
        status_label.setStyleSheet("font-size: 14px; color: #64748B;")
        status_layout.addWidget(status_label)

        self._status_value_label = QLabel("😊 正常")
        self._status_value_label.setStyleSheet("font-size: 16px; color: #22c55e; font-weight: bold;")
        status_layout.addWidget(self._status_value_label)

        layout.addWidget(status_widget)

        layout.addStretch()

        # 查看详情按钮
        detail_btn = QPushButton("查看详情")
        detail_btn.clicked.connect(self._on_view_status_detail)
        detail_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        """)
        layout.addWidget(detail_btn)

        return card

    def _create_stats_card(self) -> QGroupBox:
        """创建使用统计卡片"""
        card = self._create_card("使用统计")
        layout = QGridLayout(card)
        layout.setContentsMargins(15, 20, 15, 15)
        layout.setSpacing(15)

        # 统计数据
        stats_items = [
            ("week_wendao", "本周问道"),
            ("week_tuiyan", "本周推演"),
            ("total_wendao", "历史问道"),
            ("total_tuiyan", "历史推演"),
        ]

        for i, (key, label) in enumerate(stats_items):
            row = i // 2
            col = i % 2

            item_widget = QWidget()
            item_layout = QVBoxLayout(item_widget)
            item_layout.setContentsMargins(0, 0, 0, 0)
            item_layout.setSpacing(5)

            label_widget = QLabel(label)
            label_widget.setStyleSheet("font-size: 14px; color: #64748B;")
            item_layout.addWidget(label_widget)

            value_widget = QLabel("0 次")
            value_widget.setStyleSheet("font-size: 18px; color: #333; font-weight: bold;")
            item_layout.addWidget(value_widget)

            # 保存引用
            self._stats_values[key] = value_widget

            layout.addWidget(item_widget, row, col)

        return card

    def _create_trend_card(self) -> QGroupBox:
        """创建趋势图表卡片"""
        card = self._create_card("趋势图表")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 20, 15, 15)
        layout.setSpacing(10)

        if not HAS_MATPLOTLIB:
            no_chart_label = QLabel("图表功能需要安装 matplotlib\n请运行: pip install matplotlib")
            no_chart_label.setStyleSheet("font-size: 13px; color: #999; padding: 20px;")
            no_chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(no_chart_label)
            return card

        # 图表切换按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self._trend_7d_btn = QPushButton("7天趋势")
        self._trend_7d_btn.setCheckable(True)
        self._trend_7d_btn.setChecked(True)
        self._trend_7d_btn.clicked.connect(lambda: self._switch_trend_view("7d"))
        self._trend_7d_btn.setStyleSheet(self._get_trend_btn_style(True))
        btn_layout.addWidget(self._trend_7d_btn)

        self._trend_30d_btn = QPushButton("30天趋势")
        self._trend_30d_btn.setCheckable(True)
        self._trend_30d_btn.clicked.connect(lambda: self._switch_trend_view("30d"))
        self._trend_30d_btn.setStyleSheet(self._get_trend_btn_style(False))
        btn_layout.addWidget(self._trend_30d_btn)

        self._trend_dist_btn = QPushButton("类型分布")
        self._trend_dist_btn.setCheckable(True)
        self._trend_dist_btn.clicked.connect(lambda: self._switch_trend_view("dist"))
        self._trend_dist_btn.setStyleSheet(self._get_trend_btn_style(False))
        btn_layout.addWidget(self._trend_dist_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # 图表显示区域
        self._trend_chart_label = QLabel()
        self._trend_chart_label.setMinimumHeight(200)
        self._trend_chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._trend_chart_label.setStyleSheet("""
            background-color: #fafafa;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
        """)
        layout.addWidget(self._trend_chart_label)

        # 当前视图类型
        self._current_trend_view = "7d"

        return card

    def _get_trend_btn_style(self, active: bool) -> str:
        """获取趋势按钮样式"""
        if active:
            return """
                QPushButton {
                    padding: 6px 15px;
                    border: 1px solid #6366f1;
                    border-radius: 15px;
                    background-color: #6366f1;
                    color: white;
                    font-size: 12px;
                }
            """
        return """
            QPushButton {
                padding: 6px 15px;
                border: 1px solid #e2e8f0;
                border-radius: 15px;
                background-color: #f8fafc;
                color: #64748b;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #f1f5f9;
                border-color: #cbd5e1;
            }
        """

    def _switch_trend_view(self, view_type: str):
        """切换趋势视图"""
        self._current_trend_view = view_type

        # 更新按钮状态
        self._trend_7d_btn.setChecked(view_type == "7d")
        self._trend_30d_btn.setChecked(view_type == "30d")
        self._trend_dist_btn.setChecked(view_type == "dist")

        self._trend_7d_btn.setStyleSheet(self._get_trend_btn_style(view_type == "7d"))
        self._trend_30d_btn.setStyleSheet(self._get_trend_btn_style(view_type == "30d"))
        self._trend_dist_btn.setStyleSheet(self._get_trend_btn_style(view_type == "dist"))

        # 刷新图表
        self._refresh_trend_chart()

    def _refresh_trend_chart(self):
        """刷新趋势图表"""
        if not HAS_MATPLOTLIB:
            return

        try:
            if self._current_trend_view == "7d":
                pixmap = self._create_usage_trend_chart(days=7)
            elif self._current_trend_view == "30d":
                pixmap = self._create_usage_trend_chart(days=30)
            else:
                pixmap = self._create_distribution_chart()

            if pixmap:
                self._trend_chart_label.setPixmap(pixmap)
            else:
                self._trend_chart_label.setText("暂无数据\n开始使用问道/推演后将显示趋势图")
                self._trend_chart_label.setStyleSheet("""
                    background-color: #fafafa;
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                    color: #999;
                    font-size: 13px;
                """)
        except Exception as e:
            self.logger.warning(f"生成图表失败: {e}")
            self._trend_chart_label.setText(f"图表生成失败")

    def _create_usage_trend_chart(self, days: int = 7) -> QPixmap:
        """创建使用趋势折线图"""
        # 获取趋势数据
        trend_data = self._stats_manager.get_usage_trend(days=days)

        if not trend_data or all(d['wendao'] == 0 and d['tuiyan'] == 0 for d in trend_data):
            return None

        # 创建图表
        fig = Figure(figsize=(6, 2.5), dpi=100)
        fig.patch.set_facecolor('#fafafa')
        ax = fig.add_subplot(111)
        ax.set_facecolor('#fafafa')

        # 准备数据
        dates = [d['date'] for d in trend_data]
        wendao = [d['wendao'] for d in trend_data]
        tuiyan = [d['tuiyan'] for d in trend_data]

        # 绘制折线
        ax.plot(dates, wendao, marker='o', markersize=4, linewidth=2,
                color='#6366f1', label='问道')
        ax.plot(dates, tuiyan, marker='s', markersize=4, linewidth=2,
                color='#f59e0b', label='推演')

        # 填充区域
        ax.fill_between(dates, wendao, alpha=0.2, color='#6366f1')
        ax.fill_between(dates, tuiyan, alpha=0.2, color='#f59e0b')

        # 设置样式
        ax.set_ylabel('使用次数', fontsize=10, color='#64748b')
        ax.tick_params(axis='x', rotation=45, labelsize=8, colors='#64748b')
        ax.tick_params(axis='y', labelsize=9, colors='#64748b')
        ax.legend(loc='upper left', fontsize=9, frameon=False)
        ax.grid(True, linestyle='--', alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#e2e8f0')
        ax.spines['bottom'].set_color('#e2e8f0')

        # 只显示整数刻度
        ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))

        fig.tight_layout()

        # 转换为 QPixmap
        return self._fig_to_pixmap(fig)

    def _create_distribution_chart(self) -> QPixmap:
        """创建类型分布饼图"""
        # 获取分布数据
        profile = self._stats_manager.get_usage_profile()
        question_types_str = profile.get('question_types', '暂无数据')

        if question_types_str == '暂无数据':
            return None

        # 解析问题类型数据 (格式: "事业运, 感情, 财运")
        # 这里需要从统计管理器获取更详细的分布
        summary = self._stats_manager.get_usage_stats_summary()

        # 简单分布：问道 vs 推演
        wendao = summary.get('total_wendao', 0)
        tuiyan = summary.get('total_tuiyan', 0)

        if wendao == 0 and tuiyan == 0:
            return None

        # 创建饼图
        fig = Figure(figsize=(6, 2.5), dpi=100)
        fig.patch.set_facecolor('#fafafa')
        ax = fig.add_subplot(111)
        ax.set_facecolor('#fafafa')

        # 数据
        sizes = [wendao, tuiyan]
        labels = [f'问道\n({wendao}次)', f'推演\n({tuiyan}次)']
        colors = ['#6366f1', '#f59e0b']
        explode = (0.02, 0.02)

        # 绘制饼图
        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, colors=colors, explode=explode,
            autopct='%1.1f%%', startangle=90,
            textprops={'fontsize': 10, 'color': '#334155'},
            pctdistance=0.6
        )

        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(9)
            autotext.set_fontweight('bold')

        ax.axis('equal')

        fig.tight_layout()

        return self._fig_to_pixmap(fig)

    def _fig_to_pixmap(self, fig: Figure) -> QPixmap:
        """将matplotlib图形转换为QPixmap"""
        canvas = FigureCanvasAgg(fig)
        canvas.draw()

        # 获取图像数据
        buf = BytesIO()
        fig.savefig(buf, format='png', facecolor=fig.get_facecolor(),
                    bbox_inches='tight', pad_inches=0.1)
        buf.seek(0)

        pixmap = QPixmap()
        pixmap.loadFromData(buf.getvalue())

        plt.close(fig)
        buf.close()

        return pixmap

    def refresh_data(self):
        """刷新所有数据"""
        self._refresh_profile()
        self._refresh_library()
        self._refresh_stats()
        self._refresh_status_evaluation()
        self._check_ai_availability()
        # 刷新趋势图表
        if HAS_MATPLOTLIB and hasattr(self, '_trend_chart_label'):
            self._refresh_trend_chart()

    def _refresh_profile(self):
        """刷新使用画像"""
        profile = self._stats_manager.get_usage_profile()

        for key, value in profile.items():
            if key in self._profile_values:
                label = self._profile_values[key]
                if isinstance(value, str):
                    if value == "暂无数据":
                        label.setStyleSheet("font-size: 14px; color: #999; font-style: italic;")
                    else:
                        label.setStyleSheet("font-size: 15px; color: #1E293B;")
                    label.setText(value)

    def _refresh_library(self):
        """刷新典籍学习数据"""
        reading_stats = self._stats_manager.get_reading_stats()
        notes_count = self._notes_manager.get_notes_count()

        # 阅读次数
        if 'reading_count' in self._library_values:
            count = reading_stats.get('total_count', 0)
            self._library_values['reading_count'].setText(f"{count} 次")

        # 阅读文档数
        if 'documents_read' in self._library_values:
            docs = reading_stats.get('documents_read', 0)
            self._library_values['documents_read'].setText(f"{docs} 篇")

        # 笔记数量
        if 'notes_count' in self._library_values:
            self._library_values['notes_count'].setText(f"{notes_count} 条")

        # 学习方向（按分类统计）
        if 'reading_category' in self._library_values:
            category_dist = reading_stats.get('category_distribution', {})
            if category_dist:
                # 获取阅读最多的分类
                top_categories = sorted(category_dist.items(), key=lambda x: x[1], reverse=True)[:2]
                category_text = "、".join([cat for cat, _ in top_categories])
                self._library_values['reading_category'].setText(category_text)
                self._library_values['reading_category'].setStyleSheet("font-size: 15px; color: #1E293B;")
            else:
                self._library_values['reading_category'].setText("暂无记录")
                self._library_values['reading_category'].setStyleSheet("font-size: 14px; color: #999; font-style: italic;")

    def _refresh_stats(self):
        """刷新使用统计"""
        summary = self._stats_manager.get_usage_stats_summary()

        for key, value in summary.items():
            if key in self._stats_values:
                self._stats_values[key].setText(f"{value} 次")

    def _refresh_status_evaluation(self):
        """刷新状态评估"""
        self._status_evaluation = self._stats_manager.get_status_evaluation()

        if self._status_value_label:
            emoji = self._status_evaluation['status_emoji']
            text = self._status_evaluation['status_text']
            status = self._status_evaluation['status']

            # 根据状态设置颜色
            if status == 'warning':
                color = '#f59e0b'  # 橙色
            elif status == 'attention':
                color = '#eab308'  # 黄色
            else:
                color = '#22c55e'  # 绿色

            self._status_value_label.setText(f"{emoji} {text}")
            self._status_value_label.setStyleSheet(f"font-size: 16px; color: {color}; font-weight: bold;")

    def _check_ai_availability(self):
        """检查AI分析是否可用"""
        summary = self._stats_manager.get_usage_stats_summary()
        reading_stats = self._stats_manager.get_reading_stats()
        notes_count = self._notes_manager.get_notes_count()

        usage_total = summary.get('total', 0)
        reading_total = reading_stats.get('total_count', 0)
        total_activity = usage_total + reading_total + notes_count

        if total_activity >= 5:
            self._ai_refresh_btn.setEnabled(True)
            self._ai_placeholder.setText(
                "您的使用数据已满足分析条件\n\n"
                "点击「刷新分析」获取AI深度分析\n\n"
                f"（数据来源：问道/推演 {usage_total}次，阅读 {reading_total}次，笔记 {notes_count}条）"
            )
            self._ai_placeholder.setStyleSheet("""
                font-size: 13px;
                color: #666;
                padding: 20px;
                background-color: #f0f7ff;
                border-radius: 5px;
                border: 1px solid #d0e0f0;
            """)
        else:
            self._ai_refresh_btn.setEnabled(False)
            remaining = 5 - total_activity
            self._ai_placeholder.setText(
                f"暂无足够数据进行分析\n\n"
                f"当总活动次数 ≥ 5 时，将启用AI深度分析功能\n"
                f"（当前: {total_activity}次，还需 {remaining} 次）\n\n"
                f"活动包括：问道/推演使用、典籍阅读、添加笔记"
            )

    def _on_refresh_ai_analysis(self):
        """刷新AI分析"""
        if not self._api_manager:
            QMessageBox.warning(
                self,
                "配置错误",
                "API管理器未初始化，无法进行AI分析。\n请确保已配置API密钥。"
            )
            return

        # 收集用户数据
        profile = self._stats_manager.get_usage_profile()
        reading_stats = self._stats_manager.get_reading_stats()
        summary = self._stats_manager.get_usage_stats_summary()
        notes_count = self._notes_manager.get_notes_count()

        profile_data = {
            'frequency': profile.get('frequency', '暂无'),
            'time_slots': profile.get('time_slots', '暂无'),
            'theories': profile.get('theories', '暂无'),
            'question_types': profile.get('question_types', '暂无'),
            'reading_count': reading_stats.get('total_count', 0),
            'documents_read': reading_stats.get('documents_read', 0),
            'notes_count': notes_count,
            'reading_category': self._get_top_category(reading_stats),
            'week_wendao': summary.get('week_wendao', 0),
            'week_tuiyan': summary.get('week_tuiyan', 0),
            'total_wendao': summary.get('total_wendao', 0),
            'total_tuiyan': summary.get('total_tuiyan', 0)
        }

        # 禁用按钮，显示加载状态
        self._ai_refresh_btn.setEnabled(False)
        self._ai_refresh_btn.setText("分析中...")
        self._ai_placeholder.setText("正在生成您的专属画像分析...\n\n请稍候...")
        self._ai_placeholder.setStyleSheet("""
            font-size: 13px;
            color: #666;
            padding: 20px;
            background-color: #fff8e1;
            border-radius: 5px;
            border: 1px solid #ffe082;
        """)

        # 启动分析线程
        self._analysis_worker = ProfileAnalysisWorker(profile_data, self._api_manager)
        self._analysis_worker.finished.connect(self._on_analysis_finished)
        self._analysis_worker.error.connect(self._on_analysis_error)
        self._analysis_worker.start()

    def _get_top_category(self, reading_stats: dict) -> str:
        """获取阅读最多的分类"""
        category_dist = reading_stats.get('category_distribution', {})
        if category_dist:
            top = max(category_dist.items(), key=lambda x: x[1])
            return top[0]
        return '暂无'

    def _on_analysis_finished(self, result: str):
        """AI分析完成"""
        self._ai_placeholder.setText(result)
        self._ai_placeholder.setStyleSheet("""
            font-size: 13px;
            color: #333;
            padding: 20px;
            background-color: #e8f5e9;
            border-radius: 5px;
            border: 1px solid #a5d6a7;
            line-height: 1.6;
        """)

        # 恢复按钮
        self._ai_refresh_btn.setEnabled(True)
        self._ai_refresh_btn.setText("刷新分析")

        # 更新时间
        from datetime import datetime
        self._ai_update_label.setText(f"更新于 {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    def _on_analysis_error(self, error_msg: str):
        """AI分析出错"""
        self.logger.error(f"AI分析失败: {error_msg}")
        self._ai_placeholder.setText(
            f"分析暂时不可用\n\n"
            f"原因: {error_msg}\n\n"
            f"请稍后重试，或检查API配置是否正确。"
        )
        self._ai_placeholder.setStyleSheet("""
            font-size: 13px;
            color: #d32f2f;
            padding: 20px;
            background-color: #ffebee;
            border-radius: 5px;
            border: 1px solid #ef9a9a;
        """)

        # 恢复按钮
        self._ai_refresh_btn.setEnabled(True)
        self._ai_refresh_btn.setText("重试分析")

    def _on_view_status_detail(self):
        """查看状态详情"""
        # 获取最新评估（如果没有则刷新）
        if not self._status_evaluation:
            self._refresh_status_evaluation()

        evaluation = self._status_evaluation
        alerts = evaluation.get('alerts', [])
        details = evaluation.get('details', {})

        # 构建详情内容
        content_parts = []

        # 当前状态
        status_text = evaluation.get('status_text', '正常')
        status_emoji = evaluation.get('status_emoji', '😊')
        content_parts.append(f"当前状态：{status_emoji} {status_text}\n")

        # 使用数据
        content_parts.append("─" * 30 + "\n")
        content_parts.append("📊 使用数据统计\n\n")
        content_parts.append(f"• 最近6小时使用：{details.get('recent_6h', 0)} 次\n")
        content_parts.append(f"• 最近7天深夜使用：{details.get('late_night_7d', 0)} 次\n")

        repeated = details.get('repeated_questions', [])
        if repeated:
            content_parts.append(f"• 重复查询问题：{', '.join([f'{q[0]}({q[1]}次)' for q in repeated[:3]])}\n")

        # 预警信息
        if alerts:
            content_parts.append("\n" + "─" * 30 + "\n")
            content_parts.append("💡 温馨提示\n\n")
            for alert in alerts:
                level_icon = '⚠️' if alert['level'] == 'warning' else '💛'
                content_parts.append(f"{level_icon} {alert['message']}\n")
        else:
            content_parts.append("\n" + "─" * 30 + "\n")
            content_parts.append("✨ 一切正常\n\n")
            content_parts.append("您的使用状态良好，继续保持！\n")

        # 监测说明
        content_parts.append("\n" + "─" * 30 + "\n")
        content_parts.append("🔍 系统监测项目\n\n")
        content_parts.append("• 密集分析：6小时内使用>5次\n")
        content_parts.append("• 深夜沉迷：一周深夜使用>3次\n")
        content_parts.append("• 重复验证：同一问题反复查询>4次\n")
        content_parts.append("• 深夜时段：23:00-05:00 使用提醒\n")
        content_parts.append("\n预警是关怀，不是惩罚 💕")

        # 显示对话框
        dialog = StatusDetailDialog("".join(content_parts), self)
        dialog.exec()

    def _on_data_management(self):
        """数据管理"""
        dialog = DataManagementDialog(self._stats_manager, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 数据已更改，刷新界面
            self.refresh_data()

    def cleanup(self):
        """清理资源"""
        pass


class StatusDetailDialog(QDialog):
    """状态评估详情对话框"""

    def __init__(self, content: str, parent=None):
        super().__init__(parent)
        self._content = content
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("状态评估详情")
        self.setMinimumSize(450, 400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 内容区域
        content_text = QTextEdit()
        content_text.setPlainText(self._content)
        content_text.setReadOnly(True)
        content_text.setStyleSheet("""
            QTextEdit {
                font-size: 13px;
                line-height: 1.6;
                padding: 15px;
                background-color: #fafafa;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
        """)
        layout.addWidget(content_text)

        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 30px;
                border: 1px solid #ccc;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)


class DataManagementDialog(QDialog):
    """数据管理对话框"""

    def __init__(self, stats_manager, parent=None):
        super().__init__(parent)
        self._stats_manager = stats_manager
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("我的数据")
        self.setMinimumSize(500, 400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 标题
        title = QLabel("使用数据管理")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # 数据摘要
        summary = self._stats_manager.get_usage_stats_summary()
        summary_text = (
            f"使用统计摘要：\n\n"
            f"• 本周问道：{summary['week_wendao']} 次\n"
            f"• 本周推演：{summary['week_tuiyan']} 次\n"
            f"• 历史问道：{summary['total_wendao']} 次\n"
            f"• 历史推演：{summary['total_tuiyan']} 次\n"
            f"• 总计：{summary['total']} 次"
        )

        summary_label = QLabel(summary_text)
        summary_label.setStyleSheet("""
            padding: 15px;
            background-color: #f9f9f9;
            border-radius: 5px;
            font-size: 13px;
        """)
        layout.addWidget(summary_label)

        # 隐私说明
        privacy_label = QLabel(
            "隐私说明：\n"
            "• 所有数据仅存储在您的本地设备\n"
            "• 敏感关键词检测在本地进行，不上传服务器\n"
            "• 您可以随时删除所有使用数据"
        )
        privacy_label.setStyleSheet("font-size: 12px; color: #666;")
        privacy_label.setWordWrap(True)
        layout.addWidget(privacy_label)

        layout.addStretch()

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        delete_btn = QPushButton("删除所有数据")
        delete_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                background-color: #ef4444;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
        """)
        delete_btn.clicked.connect(self._on_delete_all)
        btn_layout.addWidget(delete_btn)

        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        """)
        close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def _on_delete_all(self):
        """删除所有数据"""
        reply = QMessageBox.warning(
            self,
            "确认删除",
            "确定要删除所有使用数据吗？\n\n"
            "此操作不可撤销，将清除：\n"
            "• 所有使用统计\n"
            "• 行为日志\n"
            "• 风险事件记录",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self._stats_manager.clear_all_data():
                QMessageBox.information(self, "删除成功", "所有使用数据已删除。")
                self.accept()
            else:
                QMessageBox.critical(self, "删除失败", "删除数据时发生错误。")
