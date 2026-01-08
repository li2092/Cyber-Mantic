# 赛博玄数 V2 版本 - 笔记/草稿

> 更新时间：2026-01-08

---

## 零、阶段一完成记录（2026-01-08）

### 已完成的文件

**新增文件：**
- `cyber_mantic/ui/components/__init__.py` - 组件模块初始化
- `cyber_mantic/ui/components/sidebar.py` - 左侧导航栏组件（SidebarWidget）
- `cyber_mantic/ui/components/nav_item.py` - 导航项组件（NavItem）

**修改文件：**
- `cyber_mantic/ui/main_window.py` - 从TabWidget改为左侧导航栏布局
- `cyber_mantic/ui/tabs/ai_conversation_tab.py` - 新增工具栏（新对话、保存按钮）、优化输入框配色
- `cyber_mantic/ui/widgets/chat_widget.py` - 重构聊天气泡样式、优化打字动画

### 关键实现细节

**1. 左侧导航栏**
- 展开宽度：180px，收起宽度：60px
- Logo区域高度：90px
- 收起/展开按钮：汉堡菜单样式（☰）
- 导航项：问道💬、推演📊、典籍📚、洞察👁、历史📜、设置⚙️、关于ℹ️

**2. 聊天气泡设计**
- AI消息：Logo(24x24) + "赛博玄数" 在气泡上方，白色/深色背景
- 用户消息：紫色气泡(#8B5CF6)，无头像，右对齐
- 气泡最大宽度：AI 600px，用户 500px

**3. 打字动画优化**
- 打字过程使用纯文本HTML，避免Markdown渲染跳动
- 固定文本区域宽度，动画结束后解除
- 添加闪烁光标效果（▋）
- 只在动画结束后渲染完整Markdown

**4. 输入框配色（深色主题）**
- 背景色：#2D2D3D
- 边框：rgba(99, 102, 241, 0.3)
- 聚焦时：边框#6366F1，背景#33334D

---

## 一、设计决策记录

### 1.1 界面布局决策

**决策**：采用左侧导航栏替代顶部标签页

**原因**：
- 更现代的应用界面风格
- 为右侧面板腾出更多垂直空间
- 便于后续功能扩展

**细节确认**：
- 左侧导航栏支持收起/展开（展开180px，收起60px只显示图标）
- Logo区域高度80-100px，以美观为准
- 导航项需要图标（使用emoji或SVG）
- 右侧面板可拖拽调整宽度

### 1.2 问道右侧面板决策

**决策**：顺序调整为 进度条 → 快速结论 → 基本信息

**原因**：
- 进度最重要，放最上
- 快速结论是新增核心功能
- 基本信息相对静态，放最下

**不采用顶部卡片区的原因**：
- 大魔王明确表示不想要顶部栏
- 保持对话区域的完整性

### 1.3 时辰选项决策

**决策**：
- 问道模块：自然语言自动识别4种状态（known_exact/known_range/uncertain/unknown）
- 推演模块：保持3选项（确切知道/大概知道/完全不记得），不改为4个

**原因**：
- 推演是表单式一次提交，没有后续验证环节
- 加入known_range对推演模块意义不大
- 问道通过对话可以进一步验证和缩小范围

### 1.4 birth_minute决策

**决策**：
- 推演模块保留收集（用于真太阳时校正）
- 问道模块不收集
- 真太阳时校正只在推演模块实现

**当前使用情况**：
- 目前没有理论计算使用birth_minute
- 奇门遁甲/梅花易数用的是current_time.minute（起卦时间），不是出生分钟
- 是预留字段，用于未来真太阳时校正功能

---

## 二、技术架构笔记

### 2.1 左侧导航栏实现

```python
# sidebar.py 关键结构

class SidebarWidget(QWidget):
    """左侧导航栏"""

    navigation_changed = pyqtSignal(str)  # 导航切换信号

    def __init__(self):
        self.is_expanded = True  # 展开状态
        self.current_nav = "wendao"  # 当前选中

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo区域
        self.logo_header = LogoHeader()
        self.logo_header.toggle_clicked.connect(self._toggle_expand)
        layout.addWidget(self.logo_header)

        # 分隔线
        layout.addWidget(self._create_separator())

        # 导航项列表
        self.nav_list = QWidget()
        nav_layout = QVBoxLayout(self.nav_list)
        nav_layout.setSpacing(4)

        self.nav_items = {}
        for item in NAV_ITEMS:
            nav_item = NavItem(item["id"], item["name"], item["icon"])
            nav_item.clicked.connect(self._on_nav_clicked)
            nav_layout.addWidget(nav_item)
            self.nav_items[item["id"]] = nav_item

        layout.addWidget(self.nav_list)

        # 弹性空间
        layout.addStretch()

        # 分隔线
        layout.addWidget(self._create_separator())

        # 底部固定项（关于）
        self.about_item = NavItem("about", "关于", "ℹ️")
        self.about_item.clicked.connect(self._on_nav_clicked)
        layout.addWidget(self.about_item)

        self.setLayout(layout)

    def _toggle_expand(self):
        self.is_expanded = not self.is_expanded
        self._update_width()
        # 通知所有NavItem更新显示模式

    def _update_width(self):
        if self.is_expanded:
            self.setFixedWidth(180)
        else:
            self.setFixedWidth(60)

# 导航项定义
NAV_ITEMS = [
    {"id": "wendao", "name": "问道", "icon": "💬"},
    {"id": "tuiyan", "name": "推演", "icon": "📊"},
    {"id": "dianji", "name": "典籍", "icon": "📚"},
    {"id": "dongcha", "name": "洞察", "icon": "👁"},
    {"id": "lishi", "name": "历史", "icon": "📜"},
    {"id": "shezhi", "name": "设置", "icon": "⚙️"},
]
```

### 2.2 快速结论卡片实现

```python
# quick_result_card.py

class QuickResultCard(QFrame):
    """快速结论卡片"""

    expanded = pyqtSignal(str)  # 展开详情信号

    class Status(Enum):
        WAITING = "waiting"
        RUNNING = "running"
        COMPLETED_GOOD = "completed_good"  # 吉
        COMPLETED_BAD = "completed_bad"    # 凶
        COMPLETED_NEUTRAL = "completed_neutral"  # 平
        ERROR = "error"

    STATUS_STYLES = {
        Status.WAITING: {"border": "#E0E0E0", "bg": "#FAFAFA", "icon": "⬚"},
        Status.RUNNING: {"border": "#2196F3", "bg": "#E3F2FD", "icon": "⏳"},
        Status.COMPLETED_GOOD: {"border": "#4CAF50", "bg": "#E8F5E9", "icon": "✅"},
        Status.COMPLETED_BAD: {"border": "#F44336", "bg": "#FFEBEE", "icon": "⚠️"},
        Status.COMPLETED_NEUTRAL: {"border": "#FF9800", "bg": "#FFF3E0", "icon": "➖"},
        Status.ERROR: {"border": "#9E9E9E", "bg": "#F5F5F5", "icon": "❌"},
    }

    def __init__(self, theory_name: str):
        super().__init__()
        self.theory_name = theory_name
        self.status = self.Status.WAITING
        self.summary = ""
        self.judgment = None  # "吉"/"凶"/"平"
        self.is_expanded = False

        self._setup_ui()

    def set_running(self):
        self.status = self.Status.RUNNING
        self._update_style()
        self._start_animation()

    def set_completed(self, summary: str, judgment: str):
        self.summary = summary
        self.judgment = judgment

        if judgment == "吉":
            self.status = self.Status.COMPLETED_GOOD
        elif judgment == "凶":
            self.status = self.Status.COMPLETED_BAD
        else:
            self.status = self.Status.COMPLETED_NEUTRAL

        self._stop_animation()
        self._update_style()
        self._show_summary()
```

### 2.3 Worker信号机制改造

```python
# ai_conversation_tab.py

class ConversationWorker(QThread):
    """对话异步工作线程"""

    # 现有信号
    message_received = pyqtSignal(str)
    progress_updated = pyqtSignal(str, str, int)
    error = pyqtSignal(str)

    # 新增信号
    theory_started = pyqtSignal(str)           # 理论开始计算
    theory_completed = pyqtSignal(str, dict)   # 理论完成（名称, 结果摘要）
    quick_result = pyqtSignal(str, str, str)   # 快速结果（理论, 摘要, 吉凶）

    def emit_theory_started(self, theory_name: str):
        self.theory_started.emit(theory_name)

    def emit_theory_completed(self, theory_name: str, result: dict):
        # 提取摘要和吉凶判断
        summary = result.get("summary", "分析完成")
        judgment = result.get("judgment", "平")
        self.theory_completed.emit(theory_name, result)
        self.quick_result.emit(theory_name, summary, judgment)


# 在AIConversationTab中连接信号
def _connect_worker_signals(self, worker):
    worker.theory_started.connect(self._on_theory_started)
    worker.theory_completed.connect(self._on_theory_completed)
    worker.quick_result.connect(self._on_quick_result)

def _on_theory_started(self, theory_name):
    self.right_panel.set_theory_running(theory_name)

def _on_quick_result(self, theory_name, summary, judgment):
    self.right_panel.set_theory_completed(theory_name, summary, judgment)
```

### 2.4 MBTI完整矩阵

```python
# theory_selector.py 中添加

MBTI_THEORY_MATRIX = {
    # 分析型（NT）
    "INTJ": {"八字": 0.8, "奇门遁甲": 0.9, "梅花易数": 0.7, "小六壬": 0.6, "测字术": 0.5, "六爻": 0.7, "紫微斗数": 0.8, "大六壬": 0.7},
    "INTP": {"八字": 0.9, "奇门遁甲": 0.7, "梅花易数": 0.8, "小六壬": 0.5, "测字术": 0.6, "六爻": 0.8, "紫微斗数": 0.9, "大六壬": 0.6},
    "ENTJ": {"八字": 0.7, "奇门遁甲": 0.9, "梅花易数": 0.6, "小六壬": 0.7, "测字术": 0.4, "六爻": 0.6, "紫微斗数": 0.7, "大六壬": 0.8},
    "ENTP": {"八字": 0.6, "奇门遁甲": 0.8, "梅花易数": 0.9, "小六壬": 0.6, "测字术": 0.7, "六爻": 0.7, "紫微斗数": 0.6, "大六壬": 0.7},

    # 外交型（NF）
    "INFJ": {"八字": 0.8, "奇门遁甲": 0.6, "梅花易数": 0.9, "小六壬": 0.5, "测字术": 0.9, "六爻": 0.7, "紫微斗数": 0.8, "大六壬": 0.6},
    "INFP": {"八字": 0.9, "奇门遁甲": 0.5, "梅花易数": 0.8, "小六壬": 0.4, "测字术": 0.9, "六爻": 0.6, "紫微斗数": 0.9, "大六壬": 0.5},
    "ENFJ": {"八字": 0.7, "奇门遁甲": 0.7, "梅花易数": 0.7, "小六壬": 0.6, "测字术": 0.8, "六爻": 0.5, "紫微斗数": 0.7, "大六壬": 0.7},
    "ENFP": {"八字": 0.6, "奇门遁甲": 0.6, "梅花易数": 0.9, "小六壬": 0.7, "测字术": 0.9, "六爻": 0.6, "紫微斗数": 0.6, "大六壬": 0.6},

    # 守护型（SJ）
    "ISTJ": {"八字": 0.8, "奇门遁甲": 0.8, "梅花易数": 0.5, "小六壬": 0.9, "测字术": 0.4, "六爻": 0.8, "紫微斗数": 0.8, "大六壬": 0.8},
    "ISFJ": {"八字": 0.9, "奇门遁甲": 0.6, "梅花易数": 0.6, "小六壬": 0.8, "测字术": 0.7, "六爻": 0.7, "紫微斗数": 0.9, "大六壬": 0.6},
    "ESTJ": {"八字": 0.7, "奇门遁甲": 0.9, "梅花易数": 0.5, "小六壬": 0.9, "测字术": 0.3, "六爻": 0.7, "紫微斗数": 0.7, "大六壬": 0.9},
    "ESFJ": {"八字": 0.8, "奇门遁甲": 0.7, "梅花易数": 0.6, "小六壬": 0.8, "测字术": 0.8, "六爻": 0.6, "紫微斗数": 0.8, "大六壬": 0.7},

    # 探险型（SP）
    "ISTP": {"八字": 0.7, "奇门遁甲": 0.8, "梅花易数": 0.7, "小六壬": 0.6, "测字术": 0.5, "六爻": 0.9, "紫微斗数": 0.7, "大六壬": 0.7},
    "ISFP": {"八字": 0.8, "奇门遁甲": 0.5, "梅花易数": 0.8, "小六壬": 0.5, "测字术": 0.9, "六爻": 0.7, "紫微斗数": 0.8, "大六壬": 0.5},
    "ESTP": {"八字": 0.6, "奇门遁甲": 0.9, "梅花易数": 0.6, "小六壬": 0.7, "测字术": 0.4, "六爻": 0.8, "紫微斗数": 0.6, "大六壬": 0.8},
    "ESFP": {"八字": 0.7, "奇门遁甲": 0.6, "梅花易数": 0.8, "小六壬": 0.6, "测字术": 0.9, "六爻": 0.6, "紫微斗数": 0.7, "大六壬": 0.6},
}

# MBTI特征说明（用于理解匹配逻辑）
MBTI_THEORY_RATIONALE = {
    "八字": "适合需要系统性分析的类型（高J倾向）",
    "紫微斗数": "适合注重细节和完整性的类型（高S或高J）",
    "奇门遁甲": "适合喜欢策略和行动的类型（高T和高E）",
    "大六壬": "适合善于分析过程的类型（高T）",
    "六爻": "适合实用主义者（高S和高T）",
    "梅花易数": "适合直觉型和灵活型（高N和高P）",
    "小六壬": "适合喜欢快速结论的类型（高E或高J）",
    "测字术": "适合感性和创意型（高F和高N）",
}
```

### 2.5 仲裁系统实现

```python
# arbitration_system.py

class ArbitrationSystem:
    """仲裁系统：冲突时引入第三方理论裁决"""

    # 仲裁理论优先级（按问题类型）
    ARBITRATION_PRIORITY = {
        "事业": ["六爻", "梅花易数", "小六壬"],
        "财运": ["六爻", "奇门遁甲", "小六壬"],
        "感情": ["测字术", "梅花易数", "六爻"],
        "婚姻": ["八字", "六爻", "梅花易数"],
        "健康": ["六爻", "小六壬", "梅花易数"],
        "学业": ["六爻", "梅花易数", "小六壬"],
        "人际": ["测字术", "梅花易数", "六爻"],
        "择时": ["奇门遁甲", "六爻", "大六壬"],
        "决策": ["奇门遁甲", "六爻", "大六壬"],
        "性格": ["八字", "紫微斗数", "测字术"],
    }

    # 仲裁规则
    ARBITRATION_RULES = {
        "majority": "多数一致原则：仲裁结果与冲突中一方一致，则采纳该方",
        "weighted": "加权原则：根据仲裁理论与问题的匹配度加权",
        "conservative": "保守原则：冲突无法解决时，取较谨慎的判断",
    }

    def __init__(self, api_manager, theory_selector):
        self.api_manager = api_manager
        self.theory_selector = theory_selector
        self.logger = get_logger(__name__)

    def should_arbitrate(self, conflict: dict) -> bool:
        """判断是否需要仲裁"""
        # Level 4（严重冲突：吉凶对立）需要仲裁
        return conflict.get("level") == 4

    def select_arbitration_theory(
        self,
        question_type: str,
        used_theories: List[str]
    ) -> Optional[str]:
        """选择仲裁理论"""
        priority_list = self.ARBITRATION_PRIORITY.get(
            question_type,
            ["六爻", "梅花易数", "小六壬"]
        )

        for theory in priority_list:
            if theory not in used_theories:
                return theory

        return None

    async def execute_arbitration(
        self,
        arbitration_theory: str,
        conflict: dict,
        user_input: dict,
        progress_callback=None
    ) -> dict:
        """执行仲裁"""
        if progress_callback:
            progress_callback("仲裁", f"正在使用{arbitration_theory}进行仲裁分析...", 85)

        # 1. 计算仲裁理论
        theory_module = self._get_theory_module(arbitration_theory)
        arbitration_result = await theory_module.analyze(user_input)

        # 2. 比较仲裁结果与冲突双方
        conflict_theories = conflict["theories"]
        comparison = self._compare_results(
            arbitration_result,
            conflict["theory_results"]
        )

        # 3. 生成仲裁结论
        resolution = self._generate_resolution(
            arbitration_theory,
            arbitration_result,
            comparison,
            conflict
        )

        return {
            "arbitration_theory": arbitration_theory,
            "arbitration_result": arbitration_result,
            "comparison": comparison,
            "resolution": resolution,
            "final_judgment": resolution["judgment"],
            "confidence": resolution["confidence"],
            "explanation": resolution["explanation"]
        }

    def _compare_results(self, arbitration, conflict_results):
        """比较仲裁结果与冲突双方"""
        arb_judgment = arbitration.get("judgment")

        matches = []
        for theory_name, result in conflict_results.items():
            if result.get("judgment") == arb_judgment:
                matches.append(theory_name)

        return {
            "arbitration_judgment": arb_judgment,
            "matching_theories": matches,
            "is_decisive": len(matches) == 1  # 只有一方匹配，裁决明确
        }

    def _generate_resolution(self, arb_theory, arb_result, comparison, conflict):
        """生成仲裁结论"""
        if comparison["is_decisive"]:
            # 明确裁决
            winner = comparison["matching_theories"][0]
            return {
                "judgment": comparison["arbitration_judgment"],
                "confidence": 0.75,
                "winner": winner,
                "explanation": f"仲裁理论{arb_theory}的判断与{winner}一致，采纳{comparison['arbitration_judgment']}判断"
            }
        elif len(comparison["matching_theories"]) == 0:
            # 三方都不一致，取保守判断
            return {
                "judgment": "平",
                "confidence": 0.5,
                "winner": None,
                "explanation": "三个理论判断各异，建议谨慎决策"
            }
        else:
            # 与两方都一致（不太可能，因为冲突是吉凶对立）
            return {
                "judgment": comparison["arbitration_judgment"],
                "confidence": 0.8,
                "winner": "majority",
                "explanation": f"多数理论判断一致，采纳{comparison['arbitration_judgment']}"
            }
```

### 2.6 真太阳时校正

```python
# utils/solar_time.py

from datetime import datetime, timedelta
from math import sin, cos, radians

class TrueSolarTimeCalculator:
    """真太阳时校正计算器"""

    # 北京时区经度（东八区中央经线）
    BEIJING_LONGITUDE = 120.0

    @classmethod
    def calculate(
        cls,
        local_time: datetime,
        longitude: float
    ) -> datetime:
        """
        计算真太阳时

        Args:
            local_time: 本地时间（北京时间）
            longitude: 出生地经度（东经为正）

        Returns:
            真太阳时
        """
        # 1. 经度时差校正
        # 每度经度差4分钟
        lng_diff = longitude - cls.BEIJING_LONGITUDE
        lng_correction_minutes = lng_diff * 4

        # 2. 时差方程校正（Equation of Time）
        day_of_year = local_time.timetuple().tm_yday
        eot_minutes = cls._equation_of_time(day_of_year)

        # 3. 总校正量
        total_correction = lng_correction_minutes + eot_minutes

        # 4. 应用校正
        true_solar_time = local_time + timedelta(minutes=total_correction)

        return true_solar_time

    @classmethod
    def _equation_of_time(cls, day_of_year: int) -> float:
        """
        时差方程：太阳运行不均匀导致的时间差

        Args:
            day_of_year: 一年中的第几天

        Returns:
            时差（分钟）
        """
        # 简化公式
        B = radians(360 * (day_of_year - 81) / 365)
        eot = 9.87 * sin(2 * B) - 7.53 * cos(B) - 1.5 * sin(B)
        return eot

    @classmethod
    def get_corrected_hour(
        cls,
        birth_hour: int,
        birth_minute: int,
        longitude: float,
        birth_date: datetime
    ) -> int:
        """
        获取校正后的时辰

        Args:
            birth_hour: 出生小时（0-23）
            birth_minute: 出生分钟（0-59）
            longitude: 出生地经度
            birth_date: 出生日期

        Returns:
            校正后的小时数（0-23）
        """
        local_time = birth_date.replace(hour=birth_hour, minute=birth_minute)
        true_time = cls.calculate(local_time, longitude)
        return true_time.hour


# 在八字计算中使用
# theories/bazi/calculator.py

def calculate_with_true_solar_time(
    birth_year, birth_month, birth_day,
    birth_hour, birth_minute,
    longitude, gender
):
    """使用真太阳时计算八字"""
    birth_date = datetime(birth_year, birth_month, birth_day)

    # 如果提供了经度和分钟，使用真太阳时
    if longitude and birth_minute is not None:
        corrected_hour = TrueSolarTimeCalculator.get_corrected_hour(
            birth_hour, birth_minute, longitude, birth_date
        )
    else:
        corrected_hour = birth_hour

    # 使用校正后的时辰计算
    return calculate_full_bazi(
        birth_year, birth_month, birth_day,
        corrected_hour, gender
    )
```

---

## 三、待探索问题

1. **左侧导航栏动画效果**：收起/展开动画如何实现最流畅？
2. **快速结论卡片进行中动画**：用QPropertyAnimation还是CSS动画？
3. **API厂商差异**：各厂商错误码、限流策略差异较大，需要统一处理
4. **时辰并行计算成本**：多时辰候选会增加API调用，需要评估成本

---

## 四、参考资料

1. PRD文档：`docs/prd_cyber_mantic.md`
2. 当前问道任务规划：`docs/wendao_task_plan.md`
3. PyQt6 Animation文档
4. 各API厂商官方文档

---

*此文档随开发进度持续更新*
