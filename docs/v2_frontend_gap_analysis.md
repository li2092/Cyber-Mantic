# V2版本前后端差异分析报告

> 更新时间：2026-01-09
> 问题级别：严重

## 一、核心问题概述

V2版本设计了完整的5阶段渐进式交互流程，但前端实现存在严重的**硬编码问题**和**功能缺失**：

| 问题类型 | 数量 | 影响 |
|---------|------|------|
| 硬编码对话内容 | 8处 | 无法配置、难以维护 |
| 未使用的提示词模板 | 4个 | prompts/目录白写 |
| FlowGuard集成不足 | 5项 | 流程监管形同虚设 |
| 回溯校验UI缺失 | 完全缺失 | V2核心功能未实现 |

---

## 二、硬编码问题清单

### 2.1 对话内容硬编码

#### P0 - 欢迎消息硬编码
**文件**: `conversation_service.py:130-159`

```python
# 当前代码：完全硬编码
welcome_message = """👋 欢迎使用赛博玄数 - AI智能对话模式

## 🎯 智能交互流程
...
"""
```

**问题**:
- prompts/conversation/greeting.md 模板存在但未使用
- 无法通过配置调整开场白

**应该是**:
```python
from cyber_mantic.prompts import load_prompt
welcome_message = load_prompt("conversation/greeting.md", context)
```

---

#### P0 - 阶段1完成提示硬编码
**文件**: `conversation_service.py:274-300`

```python
return f"""✅ **信息已收集**
...
## 📝 接下来，请告诉我您的出生信息

**必填信息：**
- 出生年份（如：1990）
- 出生月份（如：5）
- 出生日期（如：20）
...
"""
```

**问题**: 所有引导文字、示例格式都硬编码

---

#### P0 - 回溯验证提示硬编码
**文件**: `conversation_service.py:361-368`

```python
return f"""
## ⏪ 回溯验证

请简单回答：过去3年中，在{self.context.question_category}领域是否有重大变化？

例如：2023年换了工作 / 最近几年比较平稳
"""
```

**问题**:
- "过去3年"时间范围硬编码
- 示例只适用事业类问题
- 未使用动态验证问题生成

---

#### P1 - 补充信息提示硬编码
**文件**: `conversation_service.py:350-368`

```python
response += """
## 📝 需要补充信息

为提高分析准确度，请回答：
1. **兄弟姐妹排行？**（老大/老二/独生）
2. **脸型特征？**（圆脸/方脸/瓜子脸）
3. **通常几点入睡？**
"""
```

---

#### P1 - NLP解析Prompt硬编码
**文件**: `nlp_parser.py:84-116, 152-194`

所有AI解析的提示词都直接写在代码里，不可配置。

---

### 2.2 流程控制硬编码

#### 阶段跳转条件
**文件**: `conversation_service.py:322-325`

```python
# 硬编码的跳转逻辑
need_supplement = self.context.time_certainty in ("uncertain", "unknown")
self.context.stage = ConversationStage.STAGE3_SUPPLEMENT if need_supplement else ConversationStage.STAGE4_VERIFICATION
```

#### 理论选择数量
**文件**: `conversation_service.py:535`

```python
# 硬编码的理论数量限制
max_theories=6, min_theories=3
```

---

## 三、未使用的组件

### 3.1 提示词模板（完全未使用）

```
prompts/conversation/
├── greeting.md       ❌ 未使用
├── clarification.md  ❌ 未使用
├── followup.md       ❌ 未使用
└── summary.md        ❌ 未使用
```

### 3.2 FlowGuard能力未充分利用

| FlowGuard功能 | 设计 | 实际使用 |
|--------------|------|---------|
| 进度显示 | 显示5阶段进度 | ✅ 已实现 |
| AI增强输入验证 | validate_input_with_ai() | ❌ 未调用 |
| 阶段跳转防护 | can_skip_stage() | ❌ 未调用 |
| 错误友好提示 | generate_error_feedback() | ❌ 未调用 |
| 信息完整性检查 | is_stage_complete() | ❌ 未调用 |

**当前FlowGuard只用于显示进度，核心的输入验证功能被忽略了！**

---

## 四、回溯校验功能缺失（最严重）

### 4.1 设计要求

V2设计了完整的回溯校验机制：

```
阶段4：结果验证（STAGE4_VERIFICATION）

1. DynamicVerification.generate_verification_questions()
   - AI分析各理论预测
   - 生成3个针对性验证问题
   - 问题类型：yes_no / year / choice / text

2. 回溯验证逻辑
   - 收集用户对过去事件的反馈
   - 根据反馈调整理论置信度
   - accurate +0.2 / partial +0.1 / inaccurate -0.15
```

### 4.2 实际实现

```python
# conversation_service.py:361-368
# 只有一个简单的文本提示，没有：
# - 动态生成的验证问题
# - 结构化的反馈收集
# - 置信度调整机制
# - 可视化的验证UI

return f"""
## ⏪ 回溯验证
请简单回答：过去3年中...
"""
```

### 4.3 缺失的UI组件

应该有但没有的组件：

```python
class RetroactiveVerificationWidget(QFrame):
    """回溯验证组件 - V2核心功能"""

    # 显示系统推断的关键事件
    # 提供"同意/不同意/部分同意"选项
    # 收集用户反馈和补充说明
    # 实时更新理论置信度
```

---

## 五、功能实现对比表

| V2设计功能 | 后端实现 | 前端实现 | 差距 |
|-----------|---------|---------|------|
| 5阶段渐进流程 | ✅ | ✅ | - |
| 小六壬快速判断 | ✅ | ✅ | - |
| FlowGuard进度显示 | ✅ | ✅ | - |
| QuickResultCard卡片 | ✅ | ✅ | - |
| 打字机效果 | ✅ | ✅ | - |
| **提示词模板** | ✅ | ❌ | 未集成 |
| **FlowGuard输入验证** | ✅ | ❌ | 未调用 |
| **动态验证问题生成** | ✅ | ❌ | 未使用 |
| **回溯验证UI** | ✅ | ❌ | 完全缺失 |
| **置信度调整机制** | ✅ | ❌ | 未集成 |
| **仲裁系统UI** | ✅ | ❌ | 未集成 |
| MBTI适配选择 | ✅ | ⚠️ | 部分实现 |
| 时辰推断 | ✅ | ⚠️ | 只有文本提示 |

---

## 六、问题根源分析

### 6.1 开发顺序问题
- 后端功能先完成，前端未跟进
- 后端代码有完整的类和方法，前端没有调用

### 6.2 集成断层
- conversation_service.py 有调用后端服务
- 但没有使用返回的结构化数据来驱动UI

### 6.3 UI组件缺失
- 只有ChatWidget和QuickResultCard
- 缺少VerificationWidget、TheoryComparisonPanel等

---

## 七、修复优先级

### P0 - 必须立即修复

1. **集成提示词模板**
   - 创建 `prompts/loader.py`
   - 替换所有硬编码的消息

2. **启用FlowGuard输入验证**
   - 在 `process_user_input()` 中调用验证
   - 显示友好的错误提示

3. **实现回溯验证UI**
   - 创建 `verification_widget.py`
   - 显示动态生成的验证问题
   - 收集结构化反馈

### P1 - 尽快修复

4. **阶段提示外部化**
   - 所有阶段引导文字移到配置

5. **集成置信度调整**
   - 显示各理论当前置信度
   - 根据反馈实时更新

6. **添加用户信息编辑**
   - 允许修改已填信息
   - 触发重新计算

### P2 - 后续优化

7. 统一Prompt管理
8. 添加仲裁结果UI
9. 实现对话导出

---

## 八、文件修改清单

需要修改的文件：

```
cyber_mantic/
├── services/
│   └── conversation_service.py    # 替换硬编码，调用FlowGuard
├── prompts/
│   └── loader.py                  # 新增：模板加载器
├── ui/
│   ├── tabs/
│   │   └── ai_conversation_tab.py # 添加验证UI调用
│   └── widgets/
│       └── verification_widget.py # 新增：回溯验证组件
└── core/
    └── flow_guard.py              # 确认功能完整
```

---

## 九、下一步行动

1. 确认修复优先级
2. 创建提示词加载器
3. 替换conversation_service.py中的硬编码
4. 实现回溯验证组件
5. 测试完整流程

---

*此报告由Claude自动生成，基于代码静态分析*
