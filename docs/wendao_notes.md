# 问道界面完善 - 笔记/草稿

> 更新时间：2026-01-09

---

## 一、架构理解

### 问道界面数据流

```
用户输入
    ↓
AIConversationTab (UI层)
    ↓ ConversationWorker (QThread)
    ↓
ConversationService (服务层)
    ├── FlowGuard          → 流程监管 ⚠️ 未充分使用
    ├── NLPParser          → 自然语言解析
    ├── TheorySelector     → 理论选择
    ├── 各Theory计算器     → 术数计算
    ├── QAHandler          → 问答处理
    └── ReportGenerator    → 报告生成
    ↓
APIManager (API层)
    ├── Claude API
    ├── Gemini API
    ├── Deepseek API
    └── Kimi API
```

### V2版本核心创新（后端已实现）

| 功能 | 后端文件 | 前端集成 |
|------|---------|---------|
| FlowGuard流程监管 | `core/flow_guard.py` | ⚠️ 只用显示，未用验证 |
| 动态验证问题生成 | `conversation/dynamic_verification.py` | ❌ 完全未使用 |
| 置信度调整 | `conversation_service.py` | ❌ 未集成到UI |
| 提示词模板 | `prompts/conversation/*.md` | ❌ 未加载使用 |

---

## 二、技术细节记录

### 2.1 硬编码问题详解

#### 欢迎消息（最严重）

**位置**：`conversation_service.py:130-159`

```python
# 当前硬编码
welcome_message = """👋 欢迎使用赛博玄数 - AI智能对话模式

## 🎯 智能交互流程

本模式采用**渐进式5阶段**深度对话...
"""
```

**问题**：
- 完全硬编码，无法配置
- `prompts/conversation/greeting.md` 模板存在但未使用
- 修改需要改代码

**修复方案**：
```python
from cyber_mantic.prompts.loader import load_prompt
welcome_message = load_prompt("conversation/greeting.md", {
    "datetime": datetime.now()
})
```

#### 阶段提示（多处）

| 位置 | 内容 | 问题 |
|------|------|------|
| `conversation_service.py:274-300` | 阶段1完成后的引导 | 硬编码示例格式 |
| `conversation_service.py:350-368` | 补充信息提示 | 硬编码3个问题 |
| `conversation_service.py:361-368` | 回溯验证提示 | 硬编码"过去3年" |

### 2.2 FlowGuard集成现状

**设计功能**（`flow_guard.py`中已实现）：

```python
class FlowGuard:
    def validate_input_with_ai(self, user_input, stage):
        """AI增强的输入验证"""
        # 1. 代码验证（快速、稳定）
        # 2. AI验证（处理口语化表达）
        # 3. 返回ValidationResult

    def generate_error_feedback(self, validation_result):
        """生成友好的错误提示"""

    def can_skip_stage(self, current_stage, collected_info):
        """判断是否可以跳过当前阶段"""

    def is_stage_complete(self, stage):
        """检查阶段信息是否完整"""
```

**实际使用**（`conversation_service.py`）：

```python
# 只用了进度显示
flow_guard.generate_progress_display()

# 从未调用
# flow_guard.validate_input_with_ai()  ❌
# flow_guard.generate_error_feedback()  ❌
# flow_guard.can_skip_stage()  ❌
# flow_guard.is_stage_complete()  ❌
```

### 2.3 回溯校验缺失分析

**V2设计**：

```
阶段4：结果验证
1. DynamicVerification.generate_verification_questions()
   - AI分析各理论预测
   - 生成3个针对性验证问题
   - 问题类型：yes_no / year / choice / text

2. 收集用户反馈
   - 准确(accurate): 置信度 +0.2
   - 部分准确(partial): 置信度 +0.1
   - 不准确(inaccurate): 置信度 -0.15

3. 更新理论权重
```

**实际代码**：

```python
# conversation_service.py:361-368
return f"""
## ⏪ 回溯验证

请简单回答：过去3年中，在{self.context.question_category}领域是否有重大变化？

例如：2023年换了工作 / 最近几年比较平稳
"""
# 完全是硬编码的一句话！
```

**缺失的UI组件**：

```python
class VerificationWidget(QFrame):
    """回溯验证UI组件 - 需要新建"""

    def __init__(self):
        # 显示动态生成的3个验证问题
        # 每个问题有选项（是/否/部分）
        # 收集用户补充说明
        # 实时计算置信度变化
```

### 2.4 提示词模板结构

**已存在的模板**（未使用）：

```
prompts/conversation/
├── greeting.md          # 开场白模板
├── clarification.md     # 澄清追问模板
├── followup.md          # 后续问题模板
└── summary.md           # 总结模板
```

**需要新增的模板**：

```
prompts/conversation/
├── stage1_complete.md   # 阶段1完成提示
├── stage2_prompt.md     # 阶段2信息收集引导
├── supplement_prompt.md # 阶段3补充信息引导
└── verification_prompt.md # 阶段4验证问题（动态生成基础）
```

---

## 三、修复方案设计

### 3.1 提示词加载器

**文件**：`cyber_mantic/prompts/loader.py`

```python
import os
from pathlib import Path
from string import Template

PROMPTS_DIR = Path(__file__).parent

def load_prompt(template_name: str, context: dict = None) -> str:
    """
    加载并渲染提示词模板

    Args:
        template_name: 模板名（如 "conversation/greeting.md"）
        context: 模板变量（如 {"datetime": "2026-01-09"}）

    Returns:
        渲染后的提示词字符串
    """
    template_path = PROMPTS_DIR / template_name

    if not template_path.exists():
        raise FileNotFoundError(f"模板不存在: {template_name}")

    content = template_path.read_text(encoding='utf-8')

    if context:
        # 使用$variable语法
        template = Template(content)
        content = template.safe_substitute(context)

    return content
```

### 3.2 FlowGuard集成方案

**在`conversation_service.py`中添加**：

```python
async def process_user_input(self, user_message: str, ...):
    # 1. 同步FlowGuard阶段
    self._sync_flow_guard_stage(self.context.stage)

    # 2. 🆕 调用FlowGuard验证
    validation = await self.flow_guard.validate_input_with_ai(
        user_message,
        stage=self.context.stage
    )

    # 3. 🆕 如果验证失败，返回友好提示
    if validation.status != InputStatus.VALID:
        return self.flow_guard.generate_error_feedback(validation)

    # 4. 继续正常流程...
```

### 3.3 回溯验证UI设计

```python
class VerificationWidget(QFrame):
    """回溯验证组件"""

    feedback_collected = pyqtSignal(dict)  # 反馈收集完成信号

    def __init__(self, theme: str = "dark"):
        super().__init__()
        self.questions = []  # 动态生成的问题
        self.feedback = {}   # 用户反馈

    def set_questions(self, questions: list):
        """设置验证问题（从DynamicVerification获取）"""
        self.questions = questions
        self._render_questions()

    def _render_questions(self):
        """渲染问题UI"""
        for i, q in enumerate(self.questions):
            # 问题文本
            # 选项按钮（是/否/部分）
            # 补充说明输入框

    def _on_submit(self):
        """提交反馈"""
        self.feedback_collected.emit(self.feedback)
```

---

## 四、已修复问题详解

### 4.1 UI主题对比度（2026-01-09）

**问题**：浅色主题下某些状态文字对比度不足

**修复**：
| 状态 | 原颜色 | 新颜色 | 对比度提升 |
|------|--------|--------|-----------|
| WAITING | #6B7280 | #4B5563 | 2.03→2.79 |
| NEUTRAL | #B45309 | #92400E | 2.26→2.67 |
| H1标题 | #6D28D9 | #5B21B6 | 2.86→3.4 |

### 4.2 selected_theories字典问题（2026-01-08）

**问题**：TheorySelector返回字典列表，直接join报错

**修复**：
```python
# 统一提取theory字段
theory_names = [
    t.get('theory', str(t)) if isinstance(t, dict) else str(t)
    for t in selected_theories
]
```

---

## 五、测试用例

### 正常流程测试

1. 输入：`我想咨询事业，最近想换工作。数字：3、5、7`
2. 输入：`1990年5月20日下午3点出生，男，INTJ`
3. 输入：`（如果需要补充）我是老二，方脸，通常11点睡`
4. **🆕 验证**：应显示3个动态生成的验证问题，而非硬编码提示
5. 验证：生成完整报告，进入QA阶段

### FlowGuard验证测试

1. 输入格式错误的数字（如"abc"）→ 应显示友好提示
2. 输入不完整的出生信息 → 应提示缺少哪些信息
3. 跳过必填阶段 → 应阻止并提示

### 回溯校验测试

1. 验证问题应该是动态生成的（与用户问题相关）
2. 选择不同的反馈应该影响理论置信度
3. 置信度变化应该在UI上有反映

---

## 六、参考资料

### 相关代码位置

- 主界面：`cyber_mantic/ui/tabs/ai_conversation_tab.py`
- 聊天组件：`cyber_mantic/ui/widgets/chat_widget.py`
- 对话服务：`cyber_mantic/services/conversation_service.py`
- FlowGuard：`cyber_mantic/core/flow_guard.py`
- 动态验证：`cyber_mantic/services/conversation/dynamic_verification.py`
- NLP解析：`cyber_mantic/services/conversation/nlp_parser.py`

### 关键类和方法

```python
# FlowGuard核心方法
FlowGuard.validate_input_with_ai()
FlowGuard.generate_error_feedback()
FlowGuard.generate_progress_display()

# DynamicVerification核心方法
DynamicVerification.generate_verification_questions()

# NLPParser核心方法
NLPParser.parse_icebreak_input()
NLPParser.parse_birth_info()
NLPParser.parse_verification_feedback()
```

---

## 七、开发日志

### 2026-01-09（下午会话）

**模板内容修复**：
- 发现 `welcome.md` 内容与设计文档 `wendao_flow_design.md` 不匹配
- 原因：模板文件从未按照设计文档更新
- 修复：
  - `welcome.md` → 简洁版（"问道模式" + 类别 + 3个数字）
  - `stage1_complete.md` → 追问"具体描述+汉字"（原错误追问出生信息）
  - `stage2_complete.md` → 追问"出生信息+性别+MBTI"
  - 新增 `stage3_collect_complete.md`

**UI布局修复**：
- 进度条(ProgressWidget 0-100%)移到右侧面板最顶端显示
- 原来在底部，用户反馈每次都要滚动才能看到

**用户信息编辑功能（方案B：对话指令）**：
- FlowGuard 新增 `detect_modification_intent()` 检测修改意图
- FlowGuard 新增 `process_modification()` 处理修改请求
- 支持修改：出生日期/性别/MBTI/咨询类别/测字汉字
- 用法示例："修改出生日期为1990年5月"

**P2待优化确认**：
- NLP解析Prompt外部化 → ✅ 已完成（使用load_prompt）
- 理论选择数量硬编码 → ❌ 待修复
- 回溯校验三个问题 → 已调整prompt让AI生成

### 2026-01-09（上午会话）

- 发现严重问题：V2功能前端未正确集成
- 创建 `v2_frontend_gap_analysis.md` 详细分析
- 更新三文件系统
- 开始P0修复

### 2026-01-08

- 修复UI显示问题
- 修复selected_theories类型错误
- 完成基础稳定性修复
