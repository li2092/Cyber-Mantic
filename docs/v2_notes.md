# 赛博玄数 V2 版本 - 笔记/草稿

> 更新时间：2026-01-08

---

## 阶段二进度记录（2026-01-08）

### 已完成任务

**2.1 Worker信号机制 ✅**
- ConversationWorker新增信号：
  - `theory_started(str)` - 理论开始计算
  - `theory_completed(str, dict)` - 理论完成
  - `quick_result(str, str, str)` - 快速结果（理论名, 摘要, 吉凶）
- 新增 `emit_theory_update()` 方法统一处理理论进度事件
- ConversationService中所有理论计算方法添加 `theory_callback` 参数

**2.2 快速结论卡片交互 ✅**
- 新增文件 `cyber_mantic/ui/widgets/quick_result_card.py`
- QuickResultCard组件：
  - 6种状态：WAITING/RUNNING/COMPLETED_GOOD/COMPLETED_BAD/COMPLETED_NEUTRAL/ERROR
  - 深色主题配色（与整体UI风格一致）
  - 点击展开详情功能
  - 进行中动画（⏳/⌛交替闪烁）
- QuickResultPanel面板：
  - 包含7个理论卡片（小六壬、八字、紫微斗数、奇门遁甲、大六壬、六爻、梅花易数）
  - 统一管理所有卡片状态
- 集成到AIConversationTab右侧面板

**关键代码位置：**
- `cyber_mantic/ui/widgets/quick_result_card.py` - 卡片组件
- `cyber_mantic/ui/tabs/ai_conversation_tab.py:675-685` - 信号处理器
- `cyber_mantic/services/conversation_service.py:540-624` - 深度分析中的theory_callback调用

**2.3 渐进展示逻辑 ✅**
- 补充六爻和梅花易数的导入和theory_callback
- 添加辅助方法：`_get_liuyao_summary`, `_get_liuyao_judgment`, `_get_meihua_summary`, `_get_meihua_judgment`

**2.4 MBTI矩阵数据 ✅**
- 在`theory_selector.py`添加完整16×8 MBTI适配矩阵（`MBTI_THEORY_MATRIX`）
- 按4种MBTI组别划分：分析型(NT)、外交型(NF)、守护型(SJ)、探险型(SP)
- 添加理论匹配说明（`MBTI_THEORY_RATIONALE`）

**2.5 MBTI匹配算法 ✅**
- 新增`calculate_mbti_matching(mbti_type, theory_name)`方法
- 替换`calculate_theory_fitness`中的mbti_score = 1.0为实际计算
- 未提供MBTI时返回中性值0.7

**2.6 MBTI对报告影响 ✅**
- 在`report_generator.py`添加MBTI表达风格指导（`MBTI_EXPRESSION_STYLES`）
- 新增`_get_mbti_style_guidance()`方法
- 在报告prompt中注入MBTI个性化指导，包括沟通风格、内容偏好、表达方式

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

## 三、阶段五实现记录（2026-01-08）

### 5.1 ShichenHandler 时辰处理器 ✅

**文件**: `cyber_mantic/core/shichen_handler.py` (635行)

**核心组件**:
- `ShichenStatus` 枚举：CERTAIN/KNOWN_RANGE/UNCERTAIN/UNKNOWN
- `ShichenRange` 数据类：时辰范围定义
- `ShichenInfo` 数据类：时辰信息封装
- `ShichenHandler` 类：统一时辰处理器

**关键功能**:
```python
# 时段范围映射
TIME_PERIOD_RANGES = {
    "凌晨": ShichenRange(0, 5, "凌晨"),
    "上午": ShichenRange(9, 12, "上午"),
    "下午": ShichenRange(13, 18, "下午"),
    # ...
}

# 五鼠遁日诀
HOUR_GAN_BASE = {
    "甲": 0, "己": 0,  # 从甲开始
    "乙": 2, "庚": 2,  # 从丙开始
    # ...
}
```

### 5.2 三柱分析模式 ✅

**文件**: `cyber_mantic/theories/bazi/calculator.py`

**新增方法**:
- `calculate_three_pillar()` - 无时辰时的降级计算
- 返回置信度0.65，包含局限性说明和推荐补充理论

### 5.3 并行计算模式 ✅

**新增方法**:
- `calculate_parallel_bazi()` - 多时辰候选并行计算
- `_analyze_hour_differences()` - 分析时辰差异影响
- `_generate_hour_recommendation()` - 生成时辰选择建议
- `calculate_with_shichen_info()` - 根据ShichenInfo智能选择计算模式

### 5.5 NLP解析扩展 ✅

**文件**: `cyber_mantic/services/conversation/nlp_parser.py`

**新增方法**:
- `parse_birth_info_v2()` - V2增强版解析
- `_analyze_time_expression()` - 识别known_range状态
- `enhance_time_from_events()` - 基于事件增强时辰判断

### 5.6 真太阳时校正 ✅

**文件**: `cyber_mantic/utils/time_utils.py`

**新增组件**:
- `CITY_LONGITUDES` - 50+中国城市经度库
- `TrueSolarTimeCalculator` 类：
  - `get_longitude()` - 获取城市经度
  - `calculate()` - 计算真太阳时
  - `should_use_true_solar_time()` - 判断是否需要校正
  - `get_correction_for_birth()` - 出生时间校正

---

## 四、代码审查记录（2026-01-08）

### 审查范围

| 模块 | 文件 | 状态 | 备注 |
|------|------|------|------|
| 核心 | shichen_handler.py | ✅ | `narrow_by_event` 为TODO stub |
| 理论 | bazi/calculator.py | ✅ | V2增强完整 |
| 服务 | nlp_parser.py | ✅ | V2增强完整 |
| 工具 | time_utils.py | ✅ | 真太阳时完整 |
| 仲裁 | arbitration_system.py | ✅ | AI+规则双模式 |
| 路由 | task_router.py | ✅ | 支持9种API |
| UI | chat_widget.py | ✅ | 导入修复 |
| UI | verification_widget.py | ✅ | 导入修复 |
| UI | api_settings_widget.py | ✅ | 导入修复 |

### 已修复问题

1. **绝对导入错误**：
   - 问题：`from cyber_mantic.xxx` 导致启动失败
   - 原因：新创建文件使用了绝对导入
   - 修复：改为相对导入 `from .xxx` 或 `from xxx`
   - 影响文件：chat_widget.py, verification_widget.py, api_settings_widget.py

### 待完善项目

1. **事件验证推断** (5.4)：`shichen_handler.narrow_by_event()` 是TODO stub
2. **推演UI调整** (5.7)：需要添加经度输入和真太阳时提示
3. **仲裁结果展示** (4.3)：UI展示仲裁过程待完善

---

## 五、FlowGuard流程监管模块设计（2026-01-09）

### 5.1 设计背景

问道模块当前问题：
- 没有输入验证机制，用户乱回答可能导致流程崩溃
- 阶段转换逻辑分散，缺少统一管理
- 用户不清楚当前进度和缺失信息

### 5.2 FlowGuard核心功能

**文件**: `cyber_mantic/core/flow_guard.py`

```
┌─────────────────────────────────────────────────────┐
│                    FlowGuard                        │
├─────────────────────────────────────────────────────┤
│  STAGE_REQUIREMENTS    # 各阶段输入要求定义          │
│  ├── STAGE1_ICEBREAK   # 破冰：类别+描述+数字        │
│  ├── STAGE2_BASIC_INFO # 基础：年月日时+性别+MBTI    │
│  ├── STAGE3_SUPPLEMENT # 补充：时辰确定性+事件       │
│  └── STAGE4_VERIFICATION # 验证：反馈              │
├─────────────────────────────────────────────────────┤
│  validate_input()      # 验证用户输入               │
│  get_stage_progress()  # 获取阶段进度               │
│  generate_progress_display()  # 生成进度展示        │
│  generate_stage_prompt()      # 生成引导提示        │
│  handle_error_input()         # 处理错误输入        │
└─────────────────────────────────────────────────────┘
```

### 5.3 进度展示示例

类似Claude Code的todo列表，让用户清楚看到进度：

```markdown
## 📋 当前阶段：基础信息收集

**进度**：60% (3/5 必填项)

### 信息收集清单

- ✅ **出生年份**：已收集: 1990
- ✅ **出生月份**：已收集: 5
- ✅ **出生日期**：已收集: 15
- ⭕ **出生时辰**：**必填** - 下午3点 / 15点 / 不记得
- ⭕ **性别**：**必填** - 男/女
- 🔸 **历法类型**：建议 - 公历/农历
- ⚪ **MBTI类型**：可选 - INTJ/ENFP等
```

### 5.4 验证器列表

| 验证器 | 功能 | 示例输入 |
|--------|------|----------|
| validate_category | 咨询类别 | "事业"/"想咨询工作" |
| validate_numbers | 随机数字 | "7、3、5"/"七三五" |
| validate_year | 出生年份 | "1990"/"90年" |
| validate_month | 出生月份 | "5月"/"正月" |
| validate_day | 出生日期 | "15日" |
| validate_hour | 出生时辰 | "下午3点"/"不记得" |
| validate_gender | 性别 | "男"/"女" |
| validate_mbti | MBTI | "INTJ" |
| validate_place | 出生地 | "北京"/"上海市" |

### 5.5 集成方式

在ConversationService中集成：
```python
from core.flow_guard import get_flow_guard

class ConversationService:
    def __init__(self, ...):
        self.flow_guard = get_flow_guard()

    async def process_message(self, user_message):
        # 1. 先用FlowGuard验证
        result = self.flow_guard.validate_input(user_message)

        if result.status == InputStatus.INVALID:
            # 返回友好提示
            return self.flow_guard.handle_error_input("parse_failed")

        if result.status == InputStatus.INCOMPLETE:
            # 显示进度 + 引导
            progress = self.flow_guard.generate_progress_display()
            prompt = self.flow_guard.generate_stage_prompt()
            return f"{progress}\n\n{prompt}"

        # 2. 正常处理
        ...
```

---

## 六、赛博玄数判断节点完整梳理（2026-01-09）

### 6.1 判断节点总览

根据代码审查，赛博玄数共有以下关键判断节点：

| 序号 | 节点 | 位置 | 当前实现 | AI备用 | 重要性 |
|------|------|------|----------|--------|--------|
| 1 | 破冰输入解析 | NLPParser.parse_icebreak_input | AI为主 | ✅代码备用 | 高 |
| 2 | 出生信息解析 | NLPParser.parse_birth_info | AI为主 | ✅代码备用 | 高 |
| 3 | 时辰确定性识别 | NLPParser._analyze_time_expression | 代码为主 | ❌ | 高 |
| 4 | 验证反馈解析 | NLPParser.parse_verification_feedback | AI为主 | ✅代码备用 | 中 |
| 5 | 时辰推断 | NLPParser.infer_birth_hour | AI为主 | ❌ | 中 |
| 6 | 理论适配度计算 | TheorySelector.calculate_theory_fitness | 纯代码 | ❌ | 高 |
| 7 | MBTI匹配计算 | TheorySelector.calculate_mbti_matching | 纯代码 | ❌ | 中 |
| 8 | 问题类型识别 | QAHandler.identify_question_type | 纯代码 | 可加AI | 中 |
| 9 | 理论冲突检测 | create_conflict_info | 纯代码 | ❌ | 高 |
| 10 | 仲裁理论选择 | ArbitrationSystem.request_arbitration | 纯代码 | ❌ | 中 |
| 11 | 仲裁结果分析 | ArbitrationSystem.execute_arbitration | AI为主 | ✅规则备用 | 高 |
| 12 | 吉凶判断提取 | _extract_judgment | 纯代码 | 可加AI | 中 |
| 13 | 置信度计算 | ReportGenerator.calculate_overall_confidence | 纯代码 | ❌ | 中 |
| 14 | FlowGuard输入验证 | FlowGuard.validate_input | 代码为主 | ✅AI增强 | 高 |
| 15 | FlowGuard智能理解 | FlowGuard.smart_understand_input | AI为主 | ❌ | 中 |
| 16 | 时辰状态处理 | ShichenHandler.parse_time_input | 纯代码 | ❌ | 高 |
| 17 | 真太阳时计算 | TrueSolarTimeCalculator.calculate | 纯代码 | ❌ | 低 |
| 18 | 事件时辰推断 | ShichenHandler.narrow_by_event | TODO | 需AI | 中 |

### 6.2 AI+代码双重验证机制设计

**设计原则**：
1. **代码优先**：确定性高的验证用代码，快速、稳定、无成本
2. **AI备用**：代码验证失败或不完整时，调用AI增强
3. **结果合并**：AI提取的信息与代码结果合并，取并集

**已实现的双重验证**：

```
┌─────────────────────────────────────────────────────┐
│           AI+代码双重验证流程                        │
├─────────────────────────────────────────────────────┤
│  用户输入                                            │
│      │                                              │
│      ▼                                              │
│  ┌──────────────┐                                   │
│  │ 代码验证器    │ ← 正则、关键词、规则              │
│  └──────┬───────┘                                   │
│         │                                           │
│   ┌─────┴─────┐                                     │
│   │ 是否成功？  │                                     │
│   └─────┬─────┘                                     │
│     ↙      ↘                                        │
│   是        否                                       │
│   │          │                                      │
│   │    ┌─────▼─────┐                                │
│   │    │ AI验证器   │ ← LLM信息提取                  │
│   │    └─────┬─────┘                                │
│   │          │                                      │
│   │    ┌─────▼─────┐                                │
│   │    │ 合并结果   │                                │
│   │    └─────┬─────┘                                │
│   │          │                                      │
│   ▼          ▼                                      │
│  ┌───────────────────┐                              │
│  │   返回验证结果      │                              │
│  └───────────────────┘                              │
└─────────────────────────────────────────────────────┘
```

**FlowGuard中的实现示例**：

```python
async def validate_input_with_ai(self, user_message, stage):
    # 1. 代码验证（快速）
    code_result = self.validate_input(user_message, stage)

    if code_result.status == InputStatus.VALID:
        return code_result  # 代码搞定，不用AI

    # 2. AI验证（备用）
    if self.ai_validation_enabled:
        ai_extracted = await self._ai_validate(user_message, stage)

        if ai_extracted:
            # 合并结果
            merged_data = {**code_result.extracted_data, **ai_extracted}
            # 重新检查是否满足要求
            ...

    return result
```

### 6.3 需要加强AI能力的节点

**高优先级**（建议增加AI备用）：

1. **时辰确定性识别** (`_analyze_time_expression`)
   - 当前：纯正则/关键词
   - 问题：无法处理复杂口语表达如"应该是快中午的时候吧"
   - 建议：AI识别不确定性程度

2. **问题类型识别** (`identify_question_type`)
   - 当前：关键词匹配
   - 问题：用户表述可能跨类别或模糊
   - 建议：AI判断主要意图

3. **吉凶判断提取** (`_extract_judgment`)
   - 当前：关键词检查
   - 问题：某些理论结果表述复杂
   - 建议：AI理解语义判断

4. **事件时辰推断** (`narrow_by_event`)
   - 当前：TODO stub
   - 需求：根据用户历史事件缩小时辰范围
   - 建议：必须用AI

**低优先级**（代码足够）：

1. 理论适配度计算 - 向量计算，无需AI
2. MBTI匹配 - 查表即可
3. 置信度计算 - 规则计算
4. 真太阳时计算 - 数学公式

### 6.4 FlowGuard集成完成记录

**集成位置**：`conversation_service.py`

**集成方式**：
```python
# 导入
from core.flow_guard import get_flow_guard, InputStatus

# 初始化（注入API管理器）
def _init_handlers(self):
    self.flow_guard = get_flow_guard(self.api_manager)

# 阶段同步
def _sync_flow_guard_stage(self, stage: ConversationStage):
    stage_mapping = {
        ConversationStage.INIT: "STAGE1_ICEBREAK",
        ConversationStage.STAGE1_ICEBREAK: "STAGE1_ICEBREAK",
        ConversationStage.STAGE2_BASIC_INFO: "STAGE2_BASIC_INFO",
        # ...
    }
    flow_guard_stage = stage_mapping.get(stage)
    if flow_guard_stage:
        self.flow_guard.set_stage(flow_guard_stage)

# 重试提示使用FlowGuard进度展示
def _retry_msg(self, stage: str) -> str:
    progress_display = self.flow_guard.generate_progress_display()
    stage_prompt = self.flow_guard.generate_stage_prompt()
    return f"...\n{progress_display}\n---\n{stage_prompt}"
```

---

## 七、待探索问题

1. **左侧导航栏动画效果**：收起/展开动画如何实现最流畅？
2. **快速结论卡片进行中动画**：用QPropertyAnimation还是CSS动画？
3. **API厂商差异**：各厂商错误码、限流策略差异较大，需要统一处理
4. **时辰并行计算成本**：多时辰候选会增加API调用，需要评估成本

---

## 六、参考资料

1. PRD文档：`docs/prd_cyber_mantic.md`
2. 当前问道任务规划：`docs/wendao_task_plan.md`
3. PyQt6 Animation文档
4. 各API厂商官方文档

---

*此文档随开发进度持续更新*
