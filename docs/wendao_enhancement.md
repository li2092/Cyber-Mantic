# 问道界面完善方案 - 交付物

> 版本：v2.0
> 更新时间：2026-01-09
> 状态：🔴 紧急修复中

---

## 一、功能概述

"问道"是赛博玄数的核心功能模块，采用渐进式5阶段智能交互流程。

**V2版本核心创新**：
- FlowGuard流程监管
- 动态验证问题生成
- 置信度实时调整
- MBTI适配选择
- 提示词模板化

**当前问题**：后端功能已实现，前端集成不完整。

---

## 二、交互流程

```
┌─────────────────────────────────────────────────────────┐
│                     问道界面布局                          │
├───────────────────────────────┬─────────────────────────┤
│                               │                         │
│    💬 对话区域 (65%)          │   📊 关键信息 (35%)     │
│                               │                         │
│  ┌─────────────────────────┐  │  ┌───────────────────┐  │
│  │ 欢迎消息 (模板加载)      │  │  │ 📋 进度清单        │  │
│  └─────────────────────────┘  │  │ ☑ 破冰 100%       │  │
│                               │  │ ☐ 信息收集 0%     │  │
│  ┌─────────────────────────┐  │  └───────────────────┘  │
│  │ 用户消息 (右对齐)       │  │                         │
│  └─────────────────────────┘  │  ┌───────────────────┐  │
│                               │  │ 🔮 快速结论卡片    │  │
│  ┌─────────────────────────┐  │  │ [小六壬 ✅ 吉]    │  │
│  │ AI回复 (打字机效果)     │  │  │ [八字   ⏳ 分析]  │  │
│  └─────────────────────────┘  │  │ [奇门   ⬚ 等待]  │  │
│                               │  └───────────────────┘  │
│  ┌─────────────────────────┐  │                         │
│  │ 🆕 验证问题面板         │  │  ┌───────────────────┐  │
│  │ Q1: 2023年是否换工作？  │  │  │ 置信度面板        │  │
│  │   [是] [否] [部分]      │  │  │ 八字: 85% (+5%)   │  │
│  └─────────────────────────┘  │  │ 奇门: 72% (-3%)   │  │
│                               │  └───────────────────┘  │
│  ┌─────────────────────────┐  │                         │
│  │ 输入框              [发送]│  │                         │
│  └─────────────────────────┘  │                         │
└───────────────────────────────┴─────────────────────────┘
```

---

## 三、5阶段详细设计

### 阶段1：破冰

**目标**：快速了解用户需求，提供初步判断

**输入验证**（🆕 FlowGuard）：
```python
# 调用FlowGuard验证
validation = flow_guard.validate_input_with_ai(user_input, "STAGE1")
if not validation.is_valid:
    return flow_guard.generate_error_feedback(validation)
```

**输出**：
- 小六壬快速判断
- 引导进入下一阶段（🆕 使用模板）

**模板**：`prompts/conversation/stage1_complete.md`

---

### 阶段2：基础信息收集

**目标**：收集出生信息，计算理论适配度

**输入验证**（🆕 FlowGuard）：
- 检查年月日完整性
- 验证时辰格式
- 识别时辰确定性

**时辰分类**：
| 状态 | 说明 | 后续流程 |
|------|------|----------|
| certain | 用户明确知道 | 跳过阶段3 |
| uncertain | 用户不太确定 | 进入阶段3 |
| unknown | 完全不知道 | 进入阶段3 |

**模板**：`prompts/conversation/stage2_prompt.md`

---

### 阶段3：深度补充

**目标**：通过旁证推断时辰

**补充问题**（🆕 动态生成）：
```python
# 根据缺失信息动态生成
questions = flow_guard.generate_supplement_questions(context)
```

**模板**：`prompts/conversation/supplement_prompt.md`

---

### 阶段4：结果验证 🔴 需要重构

**目标**：通过回溯验证提高准确度

**V2设计要求**：

```python
# 1. 动态生成3个验证问题
questions = DynamicVerification.generate_verification_questions(
    theory_results=context.theory_results,
    question_category=context.question_category
)

# 问题示例：
# - "2023年是否有重大工作变化？" (yes_no)
# - "最近3年感情状态如何？" (choice: 稳定/变化/波折)
# - "预测未来6个月..." (text)

# 2. 收集结构化反馈
feedback = VerificationWidget.collect_feedback()

# 3. 调整置信度
for theory, result in feedback.items():
    if result == "accurate":
        context.adjust_confidence(theory, +0.2)
    elif result == "partial":
        context.adjust_confidence(theory, +0.1)
    elif result == "inaccurate":
        context.adjust_confidence(theory, -0.15)
```

**当前问题**：只有硬编码的一句话提示

**需要的UI组件**：
```python
class VerificationWidget(QFrame):
    """回溯验证组件"""

    def set_questions(self, questions: list):
        """设置动态生成的验证问题"""

    def collect_feedback(self) -> dict:
        """收集用户反馈"""

    def update_confidence_display(self, adjustments: dict):
        """更新置信度显示"""
```

---

### 阶段5：完整报告

**目标**：生成综合分析报告

**报告结构**：
1. 概述：问题回顾、使用理论
2. 核心分析：各理论独立结论（🆕 带置信度）
3. 综合判断：融合多理论观点
4. 行动建议：具体可执行建议
5. 注意事项：局限性说明

---

## 四、新增UI组件规格

### 4.1 VerificationWidget（🆕 需要创建）

```python
class VerificationWidget(QFrame):
    """回溯验证组件"""

    # 信号
    feedback_collected = pyqtSignal(dict)

    # 样式
    STYLES = {
        "dark": {
            "bg": "#2D2D3A",
            "question_bg": "#1E293B",
            "button_active": "#7C3AED",
            "text": "#E2E8F0"
        },
        "light": {
            "bg": "#F8FAFC",
            "question_bg": "#FFFFFF",
            "button_active": "#6D28D9",
            "text": "#1E293B"
        }
    }

    # 问题类型
    QUESTION_TYPES = ["yes_no", "choice", "year", "text"]
```

**布局**：
```
┌────────────────────────────────────────┐
│ 📋 回溯验证                             │
├────────────────────────────────────────┤
│ Q1: 2023年是否有重大工作变化？          │
│ [✓ 是]  [ 否]  [ 部分符合]              │
│ 补充说明: [________________]            │
├────────────────────────────────────────┤
│ Q2: 最近3年感情状态如何？               │
│ [ 稳定]  [✓ 有变化]  [ 波折较大]        │
│ 补充说明: [________________]            │
├────────────────────────────────────────┤
│ Q3: ...                                │
├────────────────────────────────────────┤
│                          [提交验证]     │
└────────────────────────────────────────┘
```

### 4.2 ConfidencePanel（🆕 需要创建）

```python
class ConfidencePanel(QFrame):
    """置信度显示面板"""

    def update_confidence(self, theory: str, new_value: float, delta: float):
        """更新某个理论的置信度"""
        # 显示：八字 85% (+5%)
```

---

## 五、提示词模板规格

### 5.1 模板加载器

**文件**：`cyber_mantic/prompts/loader.py`

```python
def load_prompt(template_name: str, context: dict = None) -> str:
    """
    加载并渲染提示词模板

    用法：
    load_prompt("conversation/greeting.md", {"datetime": "2026-01-09"})
    """
```

### 5.2 模板变量规范

| 变量 | 说明 | 示例 |
|------|------|------|
| `$datetime` | 当前时间 | 2026-01-09 |
| `$category` | 问题类别 | 事业 |
| `$theories` | 选中理论列表 | 八字、奇门遁甲 |
| `$time_certainty` | 时辰确定性 | uncertain |

### 5.3 需要的模板列表

```
prompts/conversation/
├── greeting.md            # 欢迎消息 ✅ 存在
├── stage1_complete.md     # 阶段1完成 🆕
├── stage2_prompt.md       # 阶段2引导 🆕
├── supplement_prompt.md   # 补充信息 🆕
├── verification_prompt.md # 验证问题 🆕
├── clarification.md       # 澄清追问 ✅ 存在
└── summary.md             # 总结模板 ✅ 存在
```

---

## 六、FlowGuard集成规格

### 6.1 输入验证流程

```python
async def process_user_input(self, user_message: str):
    # 1. 同步阶段状态
    self._sync_flow_guard_stage(self.context.stage)

    # 2. 🆕 调用验证
    validation = await self.flow_guard.validate_input_with_ai(
        user_message,
        stage=self.context.stage
    )

    # 3. 🆕 处理验证结果
    if validation.status == InputStatus.INVALID:
        return self.flow_guard.generate_error_feedback(validation)

    if validation.status == InputStatus.INCOMPLETE:
        # 提取已有信息，追问缺失部分
        self._update_context_partial(validation.extracted_data)
        return self.flow_guard.generate_followup_prompt(validation)

    # 4. 继续正常流程
    ...
```

### 6.2 错误反馈规格

```python
def generate_error_feedback(self, validation_result) -> str:
    """
    生成友好的错误提示

    示例输出：
    "😊 您输入的数字格式不太对呢~

    请输入3个1-9的数字，用于小六壬占卜
    例如：3、5、7 或 三五七

    💡 小提示：心中默念问题，随意写下3个数字即可"
    """
```

---

## 七、数据流规格

### 7.1 验证问题生成

```
用户完成阶段3
    ↓
调用 DynamicVerification.generate_verification_questions()
    ↓
AI分析各理论预测结果
    ↓
生成3个针对性问题
    ↓
返回结构化问题列表
    ↓
VerificationWidget.set_questions(questions)
    ↓
用户填写反馈
    ↓
收集结构化反馈
    ↓
调整各理论置信度
    ↓
更新 ConfidencePanel 显示
```

### 7.2 置信度调整

```python
CONFIDENCE_ADJUSTMENTS = {
    "accurate": +0.2,    # 完全准确
    "partial": +0.1,     # 部分准确
    "inaccurate": -0.15  # 不准确
}
```

---

## 八、测试清单

### 功能测试

- [ ] 5阶段完整流程
- [ ] 🆕 FlowGuard输入验证生效
- [ ] 🆕 验证问题动态生成
- [ ] 🆕 置信度实时调整
- [ ] 🆕 提示词模板正确加载
- [ ] 各API切换正常
- [ ] 打字机效果流畅

### FlowGuard测试

- [ ] 格式错误输入 → 友好提示
- [ ] 信息不完整 → 追问缺失
- [ ] 跳过必填 → 阻止并提示
- [ ] 口语化表达 → AI正确解析

### 验证问题测试

- [ ] 问题与用户问题相关
- [ ] 问题类型正确（yes_no/choice/text）
- [ ] 反馈影响置信度
- [ ] 置信度变化UI显示

---

## 九、修复优先级

### P0 - 必须立即修复

1. ✅ 创建提示词加载器
2. ⏳ 替换硬编码消息
3. ⏳ 启用FlowGuard验证
4. ⏳ 实现回溯验证UI

### P1 - 尽快修复

5. 创建阶段提示模板
6. 集成置信度调整UI
7. 添加用户信息编辑

### P2 - 后续优化

8. 统一Prompt管理
9. 添加仲裁结果UI
10. 实现对话导出优化

---

## 十、参考文档

- `docs/v2_frontend_gap_analysis.md` - 前后端差异分析
- `docs/wendao_task_plan.md` - 任务规划
- `docs/wendao_notes.md` - 技术笔记
