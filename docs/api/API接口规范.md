# API接口规范

**文档版本**：1.0
**对应代码版本**：v4.0
**最后更新**：2026-01-06
**维护者**：赛博玄数API组

---

## 目录

1. [概述](#1-概述)
2. [内部API接口](#2-内部api接口)
3. [AI提供商集成](#3-ai提供商集成)
4. [数据模型定义](#4-数据模型定义)
5. [错误处理规范](#5-错误处理规范)
6. [未来Web API规划](#6-未来web-api规划)

---

## 1. 概述

### 1.1 当前架构

赛博玄数 v3.1 是**桌面应用**，没有传统意义的HTTP REST API。本文档描述的是：
- **内部Python API**：模块间的接口契约
- **AI提供商集成API**：与Claude/Gemini/Deepseek/Kimi的交互
- **未来Web版API规划**：为完整版重构提供参考

### 1.2 设计原则

| 原则 | 说明 |
|-----|------|
| **类型安全** | 所有接口使用类型注解（Python 3.8+ Type Hints） |
| **契约优先** | 接口定义先于实现，使用抽象基类 |
| **向后兼容** | 接口变更遵循语义化版本控制 |
| **错误透明** | 异常传播清晰，包含上下文信息 |

---

## 2. 内部API接口

### 2.1 核心引擎API

#### 2.1.1 DecisionEngine（决策引擎）

**类路径**：`core.decision_engine.DecisionEngine`

##### `analyze()` - 主分析方法

```python
async def analyze(
    self,
    user_input: UserInput,
    progress_callback: Optional[Callable[[str, str, int, str], None]] = None
) -> ComprehensiveReport:
    """
    执行完整分析流程

    参数：
        user_input: 用户输入数据
        progress_callback: 进度回调函数
            - 参数1 (str): 理论名称或"系统"
            - 参数2 (str): 当前状态描述
            - 参数3 (int): 进度百分比 (0-100)
            - 参数4 (str): 详细信息（可选）

    返回：
        ComprehensiveReport: 综合分析报告

    异常：
        ValueError: 输入验证失败
        APIException: AI调用失败
        TheoryCalculationException: 理论计算失败
    """
```

**调用示例**：
```python
engine = DecisionEngine(config, ai_assistant, theory_selector, conflict_resolver)

# 定义进度回调
def on_progress(theory, status, percent, detail=""):
    print(f"[{percent}%] {theory}: {status}")
    if detail:
        print(f"  详情: {detail}")

# 执行分析
report = await engine.analyze(user_input, progress_callback=on_progress)
```

**progress_callback 调用时机**：
```
[5%]  系统: 选择理论
      详情: 选中理论：八字、紫微斗数、六爻
[8%]  系统: 理论选择完成
[10%] 系统: 确定执行顺序
      详情: 执行顺序：八字 -> 紫微斗数 -> 六爻
[15%] 八字: 计算排盘
[30%] 八字: AI解读中
[40%] 八字: 分析完成
      详情: ✓ 八字 分析完成 - 判断: 吉，置信度: 85.0%
[75%] 系统: 冲突检测
      详情: 解决策略：加权平均调和
            检测到2个冲突：...
[85%] 系统: 生成报告
[100%] 完成
```

---

#### 2.1.2 TheorySelector（理论选择器）

**类路径**：`core.theory_selector.TheorySelector`

##### `select_theories()` - 选择理论

```python
def select_theories(
    self,
    user_input: UserInput,
    max_theories: int = 5,
    min_theories: int = 3
) -> Tuple[List[Dict[str, Any]], Optional[List[str]]]:
    """
    根据用户输入选择最合适的理论组合

    参数：
        user_input: 用户输入
        max_theories: 最多选择理论数
        min_theories: 最少选择理论数

    返回：
        Tuple[selected_theories, missing_info]
        - selected_theories: 选中的理论列表
          [
              {
                  "theory": "八字",
                  "fitness": 0.85,
                  "info_completeness": 0.8,
                  "reason": "适合命理类问题"
              },
              ...
          ]
        - missing_info: 缺失的关键信息字段列表
          ["birth_hour", "birth_minute"] 或 None

    异常：
        ValueError: max_theories < min_theories
    """
```

##### `determine_execution_order()` - 确定执行顺序

```python
def determine_execution_order(
    self,
    selected_theories: List[Dict[str, Any]]
) -> List[str]:
    """
    确定理论执行顺序（快速 -> 基础 -> 深度）

    参数：
        selected_theories: select_theories() 的返回结果

    返回：
        List[str]: 理论名称的执行顺序
        例如: ["小六壬", "八字", "紫微斗数", "奇门遁甲"]
    """
```

---

#### 2.1.3 ConflictResolver（冲突解决器）

**类路径**：`core.conflict_resolver.ConflictResolver`

##### `detect_and_resolve_conflicts()` - 检测并解决冲突

```python
def detect_and_resolve_conflicts(
    self,
    theory_results: List[TheoryAnalysisResult]
) -> ConflictInfo:
    """
    检测理论间冲突并自动解决

    参数：
        theory_results: 各理论的分析结果列表

    返回：
        ConflictInfo: 冲突信息对象
        {
            has_conflict: bool,
            conflicts: [
                {
                    "theory1": "八字",
                    "theory2": "六爻",
                    "field": "judgment",
                    "difference": 0.35,
                    "level": 2,
                    "description": "微小差异"
                },
                ...
            ],
            resolution: {
                "总体策略": "加权平均调和",
                "调和结果": {
                    "judgment": "吉",
                    "judgment_level": 0.72,
                    "confidence": 0.85
                }
            }
        }
    """
```

##### `get_conflict_summary()` - 获取冲突摘要

```python
def get_conflict_summary(
    self,
    conflict_info: ConflictInfo
) -> str:
    """
    生成可读的冲突摘要文本

    参数：
        conflict_info: 冲突信息对象

    返回：
        str: 格式化的冲突摘要
        例如:
        \"\"\"
        检测到4个冲突：
        - 显著差异（Level 3）：1个
        - 微小差异（Level 2）：3个

        解决策略：加权平均调和
        调和结果：平（置信度：81.9%）
        \"\"\"
    """
```

---

#### 2.1.4 AIAssistant（AI助手）

**类路径**：`core.ai_assistant.AIAssistant`

##### `generate_executive_summary()` - 生成执行摘要

```python
async def generate_executive_summary(
    self,
    user_input: UserInput,
    theory_results: List[TheoryAnalysisResult],
    conflict_info: ConflictInfo,
    question_type: str,
    user_mbti: Optional[str] = None
) -> str:
    """
    生成综合报告的执行摘要

    参数：
        user_input: 用户输入
        theory_results: 理论结果列表
        conflict_info: 冲突信息
        question_type: 问题类型
        user_mbti: MBTI类型

    返回：
        str: Markdown格式的执行摘要（200-300字）

    异常：
        APIException: AI调用失败
    """
```

##### `generate_detailed_analysis()` - 生成详细问题解答

```python
async def generate_detailed_analysis(
    self,
    report: ComprehensiveReport,
    question_type: str,
    question_description: str,
    user_mbti: Optional[str] = None
) -> str:
    """
    生成详细问题解答（报告主要内容）

    这是报告的核心部分，直接基于术数理论结果回答用户的具体问题。
    根据问题类型自动调整分析重点和写作风格。

    参数：
        report: 综合报告对象（包含理论结果）
        question_type: 问题类型（事业/感情/财运/健康等）
        question_description: 问题描述
        user_mbti: MBTI类型（用于个性化表达）

    返回：
        str: Markdown格式的详细分析（800-1500字）
        内容包括：
        - 核心结论（3-5句话）
        - 理论依据（整合各理论的核心判断）
        - 具体建议（针对问题提供可行方案）
        - 注意事项

    异常：
        APIException: AI调用失败

    示例：
        >> detailed = await ai_assistant.generate_detailed_analysis(
               report=report,
               question_type="事业",
               question_description="近期是否适合跳槽",
               user_mbti="INTJ"
           )
    """
```

##### `generate_actionable_advice()` - 生成行动建议

```python
async def generate_actionable_advice(
    self,
    report: ComprehensiveReport
) -> List[Dict[str, Any]]:
    """
    生成可执行的行动建议

    参数：
        report: 综合报告对象

    返回：
        List[Dict]: 建议列表
        [
            {
                "category": "事业发展",
                "priority": "高",
                "action": "建议在3个月内完成当前项目",
                "timing": "宜早不宜迟",
                "reason": "当前运势有利..."
            },
            ...
        ]
    """
```

##### `explain_terminology()` - 术语解释

```python
async def explain_terminology(
    self,
    term: str,
    context: str = ""
) -> str:
    """
    解释术数术语

    参数：
        term: 术语（如"天乙贵人"、"紫微"）
        context: 上下文（可选，提高解释针对性）

    返回：
        str: 术语解释（200-400字）

    示例：
        >> await ai_assistant.explain_terminology("天乙贵人", "八字分析")
        \"\"\"
        天乙贵人是八字命理中的重要吉神之一...
        \"\"\"
    """
```

---

### 2.2 理论模块API

#### 2.2.1 BaseTheory（理论基类）

**类路径**：`theories.base.BaseTheory`

##### 必须实现的抽象方法

```python
class BaseTheory(ABC):
    @abstractmethod
    def get_name(self) -> str:
        """返回理论名称，例如: "八字" """

    @abstractmethod
    def get_required_fields(self) -> List[str]:
        """
        返回必需字段列表

        返回示例：
        ["birth_year", "birth_month", "birth_day"]
        """

    @abstractmethod
    def get_optional_fields(self) -> List[str]:
        """
        返回可选字段列表

        返回示例：
        ["birth_hour", "birth_minute", "gender", "birth_place_lng"]
        """

    @abstractmethod
    def get_field_weights(self) -> Dict[str, float]:
        """
        返回字段权重字典

        返回示例：
        {
            "birth_year": 1.0,
            "birth_month": 1.0,
            "birth_day": 1.0,
            "birth_hour": 0.7,
            "birth_minute": 0.3,
            "gender": 0.5
        }
        """

    @abstractmethod
    def get_min_completeness(self) -> float:
        """
        返回最小信息完备度阈值（0-1）

        例如：0.6 表示至少需要60%的信息才能分析
        """

    @abstractmethod
    def calculate(self, user_input: UserInput) -> Dict[str, Any]:
        """
        执行理论计算（纯代码排盘）

        参数：
            user_input: 用户输入

        返回：
            Dict[str, Any]: 排盘数据，必须包含以下字段：
            {
                "judgment": "吉"/"凶"/"平",
                "judgment_level": float (0-1),
                "confidence": float (0-1),
                ... (理论特定数据)
            }

        异常：
            ValueError: 输入不足或无效
        """

    # 已实现的方法
    def get_info_completeness(self, user_input: UserInput) -> float:
        """计算信息完备度（已实现，无需重写）"""

    def can_analyze(self, user_input: UserInput) -> bool:
        """判断是否可分析（已实现，无需重写）"""
```

##### 理论注册

```python
# 在 theories/__init__.py 中自动注册
from .bazi import BaZiTheory
from .ziwei import ZiWeiTheory
# ...

# 注册所有理论
TheoryRegistry.register(BaZiTheory())
TheoryRegistry.register(ZiWeiTheory())
# ...
```

##### TheoryRegistry API

```python
class TheoryRegistry:
    @classmethod
    def register(cls, theory: BaseTheory) -> None:
        """注册理论"""

    @classmethod
    def get_theory(cls, name: str) -> Optional[BaseTheory]:
        """
        获取理论实例

        参数：
            name: 理论名称（如"八字"）

        返回：
            BaseTheory实例 或 None
        """

    @classmethod
    def get_all_theories(cls) -> Dict[str, BaseTheory]:
        """
        获取所有已注册理论

        返回：
            {
                "八字": BaZiTheory(),
                "紫微斗数": ZiWeiTheory(),
                ...
            }
        """

    @classmethod
    def get_theory_names(cls) -> List[str]:
        """
        获取所有理论名称列表

        返回：
            ["八字", "紫微斗数", "奇门遁甲", ...]
        """
```

---

### 2.3 服务层API

#### 2.3.1 AnalysisService（分析服务）

**类路径**：`services.analysis_service.AnalysisService`

```python
class AnalysisService:
    async def analyze(
        self,
        user_input: UserInput,
        progress_callback: Optional[Callable] = None
    ) -> ComprehensiveReport:
        """
        执行完整分析（包含验证和历史保存）

        内部流程：
        1. 验证输入
        2. 调用决策引擎
        3. 保存历史记录
        4. 返回报告
        """

    def validate_input(
        self,
        user_input: UserInput
    ) -> Tuple[bool, str]:
        """
        验证用户输入

        返回：
            (is_valid, error_message)
            - is_valid: True/False
            - error_message: 错误信息（valid时为空字符串）
        """
```

---

#### 2.3.2 ConversationService（对话服务）

**类路径**：`services.conversation_service.ConversationService`

```python
class ConversationService:
    async def start_conversation(
        self,
        progress_callback: Optional[Callable] = None
    ) -> str:
        """
        开始9步智能对话流程

        返回：
            str: AI欢迎消息（Markdown格式）
        """

    async def process_user_input(
        self,
        user_message: str,
        progress_callback: Optional[Callable] = None
    ) -> str:
        """
        处理用户输入（9步流程中的某一步）

        参数：
            user_message: 用户消息文本

        返回：
            str: AI回复（Markdown格式）
        """

    def get_current_stage(self) -> str:
        """
        获取当前对话阶段

        返回：
            "INIT" | "INPUT_COLLECTION" | "ANALYZING" | "COMPLETED"
        """
```

---

#### 2.3.3 ReportService（报告服务）

**类路径**：`services.report_service.ReportService`

```python
class ReportService:
    async def explain_term(
        self,
        term: str,
        report: ComprehensiveReport
    ) -> str:
        """
        解释报告中的术语

        参数：
            term: 术语
            report: 报告对象（提供上下文）

        返回：
            str: 术语解释（Markdown）
        """

    async def answer_question(
        self,
        question: str,
        report: ComprehensiveReport
    ) -> str:
        """
        回答关于报告的问题

        参数：
            question: 用户问题
            report: 报告对象

        返回：
            str: 答案（Markdown）
        """

    async def compare_reports(
        self,
        reports: List[ComprehensiveReport]
    ) -> str:
        """
        对比多个报告

        参数：
            reports: 报告列表（2-5个）

        返回：
            str: 对比分析（Markdown）
        """
```

---

#### 2.3.4 ExportService（导出服务）

**类路径**：`services.export_service.ExportService`

```python
class ExportService:
    def export_to_json(
        self,
        report: ComprehensiveReport,
        filename: Optional[str] = None
    ) -> str:
        """
        导出为JSON

        参数：
            report: 报告对象
            filename: 文件名（可选，默认自动生成）

        返回：
            str: 文件路径
        """

    def export_to_pdf(
        self,
        report: ComprehensiveReport,
        filename: Optional[str] = None,
        template: str = "default"
    ) -> str:
        """
        导出为PDF

        参数：
            report: 报告对象
            filename: 文件名
            template: 模板名称（"default"/"detailed"/"simple"）

        返回：
            str: 文件路径
        """

    def export_to_markdown(
        self,
        report: ComprehensiveReport
    ) -> str:
        """
        导出为Markdown

        返回：
            str: Markdown文本
        """
```

---

### 2.4 工具模块API

#### 2.4.1 HistoryManager（历史记录管理）

**类路径**：`utils.history_manager.HistoryManager`

```python
class HistoryManager:
    def save_report(
        self,
        report: ComprehensiveReport
    ) -> bool:
        """
        保存报告到数据库

        返回：
            bool: 是否成功
        """

    def get_report_by_id(
        self,
        report_id: str
    ) -> Optional[ComprehensiveReport]:
        """
        根据ID获取报告

        参数：
            report_id: 报告UUID

        返回：
            ComprehensiveReport 或 None
        """

    def get_all_reports(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        获取所有历史记录（摘要）

        参数：
            limit: 返回数量
            offset: 偏移量（分页）

        返回：
            List[Dict]: 报告摘要列表
            [
                {
                    "report_id": "uuid...",
                    "created_at": "2026-01-02 10:30:00",
                    "question_type": "事业",
                    "theories": ["八字", "紫微斗数"],
                    "summary": "综合判断为吉..."
                },
                ...
            ]
        """

    def delete_report(
        self,
        report_id: str
    ) -> bool:
        """删除报告"""

    def clear_old_reports(
        self,
        days: int = 30
    ) -> int:
        """
        清理超过指定天数的报告

        返回：
            int: 删除的记录数
        """
```

---

#### 2.4.2 ConfigManager（配置管理）

**类路径**：`utils.config_manager.ConfigManager`

```python
class ConfigManager:
    def get(
        self,
        key: str,
        default: Any = None
    ) -> Any:
        """
        获取配置值

        支持点号分隔的嵌套键：
        >> config.get("api.claude_model")
        "claude-sonnet-4-5"

        参数：
            key: 配置键
            default: 默认值

        返回：
            Any: 配置值
        """

    def set(
        self,
        key: str,
        value: Any
    ) -> None:
        """设置配置值"""

    def has_valid_api_key(self) -> bool:
        """检查是否至少配置了一个可用的API密钥"""

    def reload(self) -> None:
        """重新加载配置文件"""
```

---

#### 2.4.3 LunarCalendar（农历转换）

**类路径**：`utils.lunar_calendar.LunarCalendar`

```python
class LunarCalendar:
    @staticmethod
    def solar_to_lunar(
        year: int,
        month: int,
        day: int
    ) -> Dict[str, Any]:
        """
        公历转农历

        参数：
            year, month, day: 公历日期（1900-2100）

        返回：
            {
                "year": 1990,
                "month": 5,
                "day": 15,
                "is_leap": False,
                "gan_zhi_year": "庚午",
                "gan_zhi_month": "壬午",
                "gan_zhi_day": "甲子"
            }

        异常：
            ValueError: 日期超出范围或无效
        """

    @staticmethod
    def lunar_to_solar(
        year: int,
        month: int,
        day: int,
        is_leap: bool = False
    ) -> Dict[str, Any]:
        """
        农历转公历

        返回：
            {
                "year": 1990,
                "month": 6,
                "day": 15
            }
        """
```

---

## 3. AI提供商集成

### 3.1 APIManager（API管理器）

**类路径**：`api.manager.APIManager`

#### 3.1.1 故障转移调用

```python
async def call_with_fallback(
    self,
    prompt: str,
    scenario: str,
    temperature: float = 0.7,
    max_tokens: int = 2000,
    **kwargs
) -> str:
    """
    带故障转移的AI调用

    参数：
        prompt: 提示词
        scenario: 使用场景（用于智能路由）
            - "综合报告解读"
            - "单理论解读"
            - "快速交互问答"
            - "冲突解决分析"
            - "术语解释"
        temperature: 温度参数（0-1）
        max_tokens: 最大token数

    返回：
        str: AI生成的文本

    异常：
        APIException: 所有API都失败

    故障转移顺序：
    1. 根据scenario选择主API
    2. 失败则按优先级尝试：Claude -> Gemini -> Deepseek -> Kimi
    3. 每个API最多重试3次
    """
```

#### 3.1.2 双模型验证

```python
async def dual_verification(
    self,
    prompt: str,
    primary_model: str = "claude",
    secondary_model: str = "deepseek",
    **kwargs
) -> Tuple[str, str]:
    """
    双模型并发验证

    参数：
        prompt: 提示词
        primary_model: 主模型
        secondary_model: 副模型

    返回：
        (primary_response, secondary_response)

    用途：
    - 提高准确性（交叉验证）
    - 检测模型幻觉
    """
```

#### 3.1.3 API使用场景映射

```python
API_USAGE_MAP = {
    "综合报告解读": "claude",       # 高质量深度分析
    "单理论解读": "claude",         # 专业准确
    "快速交互问答": "deepseek",     # 快速响应
    "冲突解决分析": "claude",       # 复杂推理
    "术语解释": "deepseek",         # 简单查询
    "回溯分析": "claude",           # 深度分析
    "预测分析": "claude",           # 深度分析
    "行动建议": "claude"            # 实用导向
}
```

---

### 3.2 各提供商API规范

#### 3.2.1 Claude API (Anthropic)

**配置**：
```python
CLAUDE_CONFIG = {
    "api_key": os.getenv("CLAUDE_API_KEY"),
    "model": "claude-sonnet-4-5-20250929",
    "base_url": "https://api.anthropic.com/v1",
    "timeout": 30,
    "max_retries": 3
}
```

**调用方法**：
```python
from anthropic import Anthropic

client = Anthropic(api_key=CLAUDE_CONFIG["api_key"])

response = client.messages.create(
    model=CLAUDE_CONFIG["model"],
    max_tokens=2000,
    temperature=0.7,
    messages=[
        {"role": "user", "content": prompt}
    ]
)

return response.content[0].text
```

---

#### 3.2.2 Gemini API (Google)

**配置**：
```python
GEMINI_CONFIG = {
    "api_key": os.getenv("GEMINI_API_KEY"),
    "model": "gemini-3-pro-preview",
    "timeout": 30
}
```

**调用方法**：
```python
import google.generativeai as genai

genai.configure(api_key=GEMINI_CONFIG["api_key"])
model = genai.GenerativeModel(GEMINI_CONFIG["model"])

response = model.generate_content(
    prompt,
    generation_config={
        "temperature": 0.7,
        "max_output_tokens": 2000
    }
)

return response.text
```

---

#### 3.2.3 Deepseek API

**配置**：
```python
DEEPSEEK_CONFIG = {
    "api_key": os.getenv("DEEPSEEK_API_KEY"),
    "model": "deepseek-reasoner",
    "base_url": "https://api.deepseek.com/v1",
    "timeout": 30
}
```

**调用方法**（OpenAI兼容）：
```python
from openai import OpenAI

client = OpenAI(
    api_key=DEEPSEEK_CONFIG["api_key"],
    base_url=DEEPSEEK_CONFIG["base_url"]
)

response = client.chat.completions.create(
    model=DEEPSEEK_CONFIG["model"],
    messages=[
        {"role": "user", "content": prompt}
    ],
    temperature=0.7,
    max_tokens=2000
)

return response.choices[0].message.content
```

---

#### 3.2.4 Kimi API (Moonshot)

**配置**：
```python
KIMI_CONFIG = {
    "api_key": os.getenv("KIMI_API_KEY"),
    "model": "kimi-k2-turbo-preview",
    "base_url": "https://api.moonshot.cn/v1",
    "timeout": 30
}
```

**调用方法**（OpenAI兼容）：
```python
from openai import OpenAI

client = OpenAI(
    api_key=KIMI_CONFIG["api_key"],
    base_url=KIMI_CONFIG["base_url"]
)

response = client.chat.completions.create(
    model=KIMI_CONFIG["model"],
    messages=[
        {"role": "user", "content": prompt}
    ],
    temperature=0.7,
    max_tokens=2000
)

return response.choices[0].message.content
```

---

### 3.3 Prompt模板API

**类路径**：`api.prompts.PromptTemplates`

#### 主要模板

```python
class PromptTemplates:
    # 系统角色
    SYSTEM_PROMPT: str = "你是专业的中国传统术数分析师..."

    # 单理论解读
    SINGLE_THEORY_INTERPRETATION: str = """
    基于以下{theory_name}排盘数据，进行深度解读...
    """

    # 综合报告
    COMPREHENSIVE_REPORT: str = """
    综合以下{num_theories}个理论的分析结果...
    """

    # 冲突解决
    CONFLICT_RESOLUTION: str = """
    检测到理论间存在冲突，请进行调和分析...
    """

    # 执行摘要
    EXECUTIVE_SUMMARY: str = """
    为以下分析结果生成执行摘要...
    """

    # 行动建议
    ACTIONABLE_ADVICE: str = """
    基于分析结果，生成具体可执行的行动建议...
    """

    # 回溯分析
    RETROSPECTIVE_ANALYSIS: str = """
    基于出生信息，分析过去3年的主要事件和趋势...
    """

    # 预测分析
    PREDICTIVE_ANALYSIS: str = """
    基于当前运势，预测未来1-2年的趋势...
    """
```

#### 使用示例

```python
from api.prompts import PromptTemplates

# 格式化提示词
prompt = PromptTemplates.SINGLE_THEORY_INTERPRETATION.format(
    theory_name="八字",
    calculation_data=json.dumps(bazi_data, ensure_ascii=False, indent=2),
    question_type="事业",
    question_description="近期是否适合跳槽"
)

# 调用AI
response = await api_manager.call_with_fallback(
    prompt=prompt,
    scenario="单理论解读"
)
```

---

## 4. 数据模型定义

### 4.1 UserInput（用户输入）

```python
@dataclass
class UserInput:
    # 问题信息
    question_type: str                          # 必需
    question_description: str                   # 必需

    # 时间信息
    current_time: datetime = field(default_factory=datetime.now)
    initial_inquiry_time: Optional[datetime] = None
    birth_year: Optional[int] = None
    birth_month: Optional[int] = None
    birth_day: Optional[int] = None
    birth_hour: Optional[int] = None
    birth_minute: Optional[int] = None
    calendar_type: str = "solar"                # "solar" | "lunar"
    birth_time_certainty: str = "certain"       # "certain" | "uncertain"

    # 个人信息
    gender: Optional[str] = None                # "male" | "female"
    birth_place_lng: Optional[float] = None     # 经度（真太阳时）
    mbti_type: Optional[str] = None             # "INTJ" | ...

    # 外应信息
    numbers: Optional[List[int]] = None         # [1, 2, 3]
    character: Optional[str] = None             # "福"
    current_direction: Optional[str] = None     # "东" | "南" | ...
    favorite_color: Optional[str] = None        # "红" | "蓝" | ...

    def to_dict(self) -> Dict[str, Any]: ...
    @classmethod
    def from_dict(cls, data: Dict) -> 'UserInput': ...
```

---

### 4.2 TheoryAnalysisResult（理论分析结果）

```python
@dataclass
class TheoryAnalysisResult:
    theory_name: str                            # "八字"
    calculation_data: Dict[str, Any]            # 排盘数据
    interpretation: str                         # AI解读文本

    judgment: str                               # "吉" | "凶" | "平"
    judgment_level: float                       # 0-1

    timing: Optional[Dict[str, Any]] = None     # 时机预测
    advice: Optional[str] = None                # 建议
    confidence: float = 0.8                     # 置信度

    retrospective_answer: Optional[Dict] = None # 回溯答案
    predictive_answer: Optional[Dict] = None    # 预测答案

    def to_dict(self) -> Dict[str, Any]: ...
```

---

### 4.3 ConflictInfo（冲突信息）

```python
@dataclass
class ConflictInfo:
    has_conflict: bool                          # 是否存在冲突
    conflicts: List[Dict[str, Any]]             # 冲突列表
    resolution: Optional[Dict[str, Any]]        # 解决方案

    def to_dict(self) -> Dict[str, Any]: ...
```

---

### 4.4 ComprehensiveReport（综合报告）

```python
@dataclass
class ComprehensiveReport:
    # 基本信息
    report_id: str                              # UUID
    created_at: datetime                        # 创建时间
    user_input_summary: Dict[str, Any]          # 输入摘要

    # 理论选择
    selected_theories: List[str]                # ["八字", "紫微斗数"]
    selection_reason: str                       # 选择原因

    # 各理论结果
    theory_results: List[TheoryAnalysisResult]

    # 冲突处理
    conflict_info: ConflictInfo

    # 综合结论（AI生成）
    executive_summary: str                      # 执行摘要（200-300字简要总结）
    detailed_analysis: str                      # 详细问题解答（主要内容，直接回答用户问题）
    retrospective_analysis: str                 # 回溯分析（次要内容，如适用）
    predictive_analysis: str                    # 预测分析（次要内容，如适用）
    comprehensive_advice: List[Dict]            # 行动建议

    # 元信息
    overall_confidence: float                   # 综合置信度
    limitations: List[str]                      # 局限性说明

    # 用户反馈
    user_feedback: Optional[Dict] = None

    def to_dict(self) -> Dict[str, Any]: ...
    def to_json(self) -> str: ...
```

---

## 5. 错误处理规范

### 5.1 异常类层次

```python
class XuanShuException(Exception):
    """基础异常类"""
    def __init__(self, message: str, error_code: str, context: Dict = None):
        self.message = message
        self.error_code = error_code
        self.context = context or {}

class InputValidationException(XuanShuException):
    """输入验证异常"""
    # error_code: "INPUT_INVALID"

class APIException(XuanShuException):
    """AI API调用异常"""
    # error_code: "API_CALL_FAILED"

class TheoryCalculationException(XuanShuException):
    """理论计算异常"""
    # error_code: "THEORY_CALC_FAILED"

class DatabaseException(XuanShuException):
    """数据库异常"""
    # error_code: "DB_ERROR"
```

### 5.2 错误码定义

| 错误码 | HTTP状态（Web版） | 含义 | 处理建议 |
|--------|------------------|------|----------|
| `INPUT_INVALID` | 400 | 输入验证失败 | 提示用户修正输入 |
| `INSUFFICIENT_INFO` | 400 | 信息不足 | 提示缺失字段 |
| `API_CALL_FAILED` | 503 | AI调用失败 | 故障转移或降级 |
| `THEORY_CALC_FAILED` | 500 | 理论计算失败 | 记录日志，跳过该理论 |
| `DB_ERROR` | 500 | 数据库错误 | 记录日志，通知用户 |
| `CONFIG_INVALID` | 500 | 配置错误 | 检查配置文件 |
| `TIMEOUT` | 504 | 超时 | 重试或提示用户 |

### 5.3 错误响应格式

```python
{
    "success": False,
    "error_code": "API_CALL_FAILED",
    "message": "AI调用失败，已尝试所有可用提供商",
    "context": {
        "attempted_apis": ["claude", "gemini", "deepseek"],
        "last_error": "Connection timeout"
    },
    "timestamp": "2026-01-02T10:30:00Z"
}
```

---

## 6. 未来Web API规划

> **说明**：此部分为完整版Web API的设计规划，当前桌面版未实现。

### 6.1 RESTful API设计

#### 6.1.1 分析API

**POST /api/v1/analysis**

```
请求：
{
    "user_input": {
        "question_type": "事业",
        "question_description": "近期是否适合跳槽",
        "birth_year": 1990,
        "birth_month": 5,
        "birth_day": 15,
        "birth_hour": 10,
        "gender": "male"
    },
    "options": {
        "max_theories": 5,
        "enable_dual_verification": true
    }
}

响应：
{
    "success": true,
    "data": {
        "report_id": "uuid-xxx",
        "status": "completed",
        "report": { ... ComprehensiveReport ... }
    }
}
```

**GET /api/v1/analysis/:report_id**

获取历史报告

**DELETE /api/v1/analysis/:report_id**

删除报告

---

#### 6.1.2 对话API

**POST /api/v1/conversation/start**

开始对话

**POST /api/v1/conversation/:session_id/message**

发送消息

**GET /api/v1/conversation/:session_id**

获取对话历史

---

#### 6.1.3 工具API

**POST /api/v1/tools/lunar-convert**

农历转换

**POST /api/v1/tools/geocode**

地理编码

---

### 6.2 WebSocket实时通信

```javascript
// 连接WebSocket
const ws = new WebSocket('wss://api.cyber_mantic.com/ws');

// 发送分析请求
ws.send(JSON.stringify({
    action: 'analyze',
    data: { ... user_input ... }
}));

// 接收进度更新
ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);

    if (msg.type === 'progress') {
        console.log(`[${msg.percent}%] ${msg.theory}: ${msg.status}`);
    } else if (msg.type === 'completed') {
        console.log('分析完成', msg.report);
    }
};
```

---

### 6.3 认证授权（规划）

#### JWT Token

```
POST /api/v1/auth/login
{
    "username": "user@example.com",
    "password": "xxx"
}

响应：
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "...",
    "expires_in": 3600
}
```

#### API密钥

```
GET /api/v1/analysis
Authorization: Bearer {api_key}
```

---

### 6.4 限流策略

| 用户类型 | QPS限制 | 日调用量 | 并发限制 |
|---------|---------|---------|---------|
| 免费用户 | 1 req/s | 100次 | 1 |
| 高级用户 | 5 req/s | 1000次 | 3 |
| 企业用户 | 20 req/s | 无限制 | 10 |

---

## 附录

### A. 版本控制

**语义化版本**：`MAJOR.MINOR.PATCH`

- **MAJOR**：不兼容的API变更
- **MINOR**：向后兼容的功能新增
- **PATCH**：向后兼容的问题修复

**当前版本**：`3.1.0`

---

### B. API变更日志

| 版本 | 日期 | 变更内容 |
|------|------|---------|
| 3.1.1 | 2026-01-04 | - 添加`detailed_analysis`字段作为报告主要内容<br/>- 新增`AIAssistant.generate_detailed_analysis()`方法<br/>- 优化报告结构：详细分析为主，回顾预测为辅<br/>- 回顾/预测分析改为根据问题类型条件生成<br/>- 添加多人分析不支持提示（5个理论）<br/>- 优化历史记录兼容性处理<br/>- 修复PDF中文字体显示问题 |
| 3.1.0 | 2026-01-02 | - 添加高德地图API集成<br/>- 添加起卦时间字段<br/>- 优化测字术笔画算法 |
| 3.0.0 | 2025-12-15 | - 重构API管理器<br/>- 添加双模型验证<br/>- 支持4个AI提供商 |

---

**文档维护**：
- API变更需更新本文档
- 新增接口需补充示例
- 废弃接口需标注 `@deprecated`

**最后更新**：2026-01-02
**审核者**：赛博玄数API组
