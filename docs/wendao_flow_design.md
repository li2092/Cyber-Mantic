# 问道核心流程设计文档（V2修订版）

> 最后更新: 2026-01-09
> 状态: 大魔王审核通过，待落地

## 1. 流程概述

问道采用**5阶段8步骤**渐进式对话模式，除欢迎消息外所有系统回复由AI动态生成。

```
┌─────────────────────────────────────────────────────────────────┐
│  阶段0: 欢迎                                                     │
│  系统 → 用户: 欢迎消息 + 引导提示                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  阶段1: 破冰                                                     │
│  用户 → 系统: 咨询大类 + 3个数字                                 │
│  系统 → 用户: 小六壬初判 + 追问(具体事情+汉字)                   │
│  【记录起卦时间】                                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  阶段2: 深入（产生好奇感）                                       │
│  用户 → 系统: 具体描述 + 汉字                                    │
│  系统 → 用户: 小六壬+测字综合分析 + 追问(生辰+性别+MBTI)         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  阶段3: 信息收集                                                 │
│  用户 → 系统: 生辰+性别+MBTI(可选)                               │
│  系统 → 用户: 多理论分析 + 回溯验证问题                          │
│  【六爻自动起卦、梅花时间起卦】                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  阶段4: 验证                                                     │
│  用户 → 系统: 回答验证问题                                       │
│  系统 → 用户: 综合分析报告（AI多轮深度思考）                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  阶段5: 问答                                                     │
│  用户可以追问、保存对话                                          │
└─────────────────────────────────────────────────────────────────┘
```

## 2. 各阶段详细设计

### 2.1 阶段0: 欢迎

| 项目 | 说明 |
|------|------|
| 触发 | 用户进入问道页面 |
| 系统行为 | 发送固定欢迎模板 |
| 输出 | 欢迎消息 + 操作引导 |

**欢迎消息模板**:
```markdown
👋 欢迎使用赛博玄数 - 问道模式

请告诉我：
1. 您想咨询的事项类别（事业/感情/财运/健康/学业/决策/其他）
2. 心里想着这件事，随机说3个1-9的数字

示例："事业，3 5 7"
```

---

### 2.2 阶段1: 破冰

| 项目 | 说明 |
|------|------|
| 用户输入 | 咨询大类 + 3个数字 |
| 系统处理 | 记录起卦时间 → 小六壬计算 → AI生成回复 |
| 系统输出 | 小六壬初判 + 追问 |

**数据收集**:
```python
context.question_category = "事业"     # AI解析
context.random_numbers = [3, 5, 7]     # AI解析
context.qigua_time = datetime.now()    # 记录起卦时间
context.xiaoliu_result = {...}         # 小六壬计算结果
```

**AI生成任务**:
- 输入: 小六壬结果、咨询类别
- 输出: 初判描述(50-80字) + 追问语句

**追问内容**:
1. 请简单描述一下具体是什么事情
2. 想着这件事，脑海中浮现的第一个汉字是什么？（可以是心态、未来的憧憬、当下想做的动作等）

---

### 2.3 阶段2: 深入

| 项目 | 说明 |
|------|------|
| 用户输入 | 具体事情描述 + 汉字 |
| 系统处理 | 测字术计算 → AI综合分析 → 生成回复 |
| 系统输出 | 小六壬+测字综合分析 + 追问 |

**数据收集**:
```python
context.question_description = "想跳槽到互联网公司"  # AI解析
context.character = "变"                            # AI解析
context.cezi_result = {...}                         # 测字术计算结果
```

**AI生成任务**:
- 输入: 小六壬结果、测字术结果、事情描述
- 输出: 综合分析(100-150字) + 追问语句

**追问内容**:
1. 您的出生日期（可以说大概时间段或不记得）
2. 性别
3. MBTI类型（可选，不知道可跳过）

---

### 2.4 阶段3: 信息收集

| 项目 | 说明 |
|------|------|
| 用户输入 | 生辰八字 + 性别 + MBTI(可选) |
| 系统处理 | AI解析 → 多理论计算 → 生成回溯问题 |
| 系统输出 | 多理论分析 + 回溯验证问题 |

**数据收集**:
```python
context.birth_info = {
    "year": 1990, "month": 5, "day": 15,
    "hour": None,  # 可能为空
    "time_certainty": "unknown"  # certain/uncertain/unknown
}
context.gender = "male"
context.mbti_type = "INTJ"  # 可能为空，AI可根据卦象推算
```

**理论计算触发**:
| 理论 | 触发条件 | 输入 | 说明 |
|------|----------|------|------|
| 八字 | 有生辰 | birth_info | 无时辰用三柱 |
| 紫微 | 有完整生辰(含时辰) | birth_info | 无时辰则跳过 |
| 梅花 | 自动 | 颜色/方位/时间 | 先判断颜色或方位，都没有则用时间起卦 |
| 六爻 | 自动 | qigua_time生成 | 秒+微秒伪随机 |
| 奇门 | 自动 | 当前时间 | 时家奇门 |

**六爻自动起卦**:
```python
def generate_liuyao_numbers(qigua_time: datetime) -> List[int]:
    """用起卦时间生成六爻数字"""
    ts = qigua_time.timestamp()
    秒 = int(ts) % 60
    微秒 = int((ts % 1) * 1000000)

    num1 = (秒 % 9) + 1
    num2 = ((秒 + 微秒 // 1000) % 9) + 1
    num3 = ((秒 + 微秒 // 100) % 9) + 1

    return [num1, num2, num3]
```

**AI生成任务**:
- 输入: 所有理论计算结果
- 输出: 多理论综合分析 + 3个回溯验证问题

---

### 2.5 阶段4: 验证

| 项目 | 说明 |
|------|------|
| 用户输入 | 回答验证问题 |
| 系统处理 | 解析反馈 → 调整置信度 → 生成最终报告 |
| 系统输出 | 综合分析报告 |

**置信度调整**:
| 反馈类型 | 调整 |
|----------|------|
| 符合 | +0.2 |
| 部分符合 | +0.1 |
| 不符合 | -0.15 |

---

### 2.6 阶段5: 问答

用户可以：
- 追问具体解读
- 询问行动建议
- 保存对话记录

---

## 3. 数据模型

### 3.1 ConversationContext 新增/修改字段

```python
class ConversationContext:
    # 阶段1
    qigua_time: Optional[datetime] = None  # 新增：起卦时间

    # 阶段2
    character: Optional[str] = None  # 新增：测字用的汉字
    cezi_result: Optional[Dict] = None  # 新增：测字结果

    # 阶段3（部分已存在）
    favorite_color: Optional[str] = None
    current_direction: Optional[str] = None
    liuyao_numbers: List[int] = []  # 新增：六爻数字(自动生成)
```

### 3.2 ConversationStage 枚举重定义

```python
class ConversationStage(Enum):
    INIT = "初始化"
    STAGE1_ICEBREAK = "阶段1_破冰"      # 小六壬
    STAGE2_DEEPEN = "阶段2_深入"        # 新增：测字
    STAGE3_COLLECT = "阶段3_信息收集"   # 多理论
    STAGE4_VERIFY = "阶段4_验证"        # 回溯
    STAGE5_REPORT = "阶段5_报告"        # 综合报告
    QA = "问答交互"
    COMPLETED = "完成"
```

---

## 4. AI提示词模板

### 4.1 阶段1回复模板

```markdown
# 角色
你是赛博玄数的占卜师，精通小六壬。

# 任务
根据小六壬结果给出初步判断，并自然地追问更多信息。

# 输入
- 咨询类别：{{category}}
- 小六壬结果：{{xiaoliu_result}}

# 输出要求
1. 先用50-80字描述小六壬的初步判断
2. 自然过渡到追问：
   - 请简单描述一下具体是什么事情
   - 想着这件事时，脑海中浮现的第一个汉字是什么？
3. 语气温和、专业，不要过于神秘
```

### 4.2 阶段2回复模板

```markdown
# 角色
你是赛博玄数的占卜师，精通小六壬和测字术。

# 任务
综合小六壬和测字术给出分析，并追问详细信息。

# 输入
- 咨询类别：{{category}}
- 具体事情：{{description}}
- 小六壬结果：{{xiaoliu_result}}
- 测字结果：{{cezi_result}}

# 输出要求
1. 综合分析（100-150字），融合两种理论的判断
2. 自然过渡到追问详细信息：
   - 出生日期（提示可以说不记得时辰）
   - 性别
   - MBTI（说明可选）
   - 方位或颜色（说明二选一，可选）
3. 语气温和、专业
```

### 4.3 阶段3回复模板

```markdown
# 角色
你是赛博玄数的占卜师，精通多种术数理论。

# 任务
综合多理论给出详细分析，并生成回溯验证问题。

# 输入
- 咨询类别：{{category}}
- 具体事情：{{description}}
- 已计算理论：{{theory_results}}

# 输出要求
1. 多理论综合分析（200-300字）
2. 生成3个回溯验证问题：
   - 关于过去3-5年的关键事件
   - 与咨询事项相关
   - 简单的是/否问题
```

---

## 5. 边界情况处理

### 5.1 用户输入不完整

| 情况 | 处理方式 |
|------|----------|
| 只说大类没给数字 | 提示补充数字 |
| 不想说汉字 | 使用时辰地支第一个字 |
| 不想给可选信息 | 跳过对应理论，使用已有信息分析 |
| 不记得时辰 | 使用三柱八字 |

### 5.2 可选信息缺失时的理论选择

| 缺失信息 | 影响 | 降级方案 |
|----------|------|----------|
| MBTI | 跳过MBTI分析 | 不影响其他理论 |
| 颜色/方位都缺 | 梅花优先级：颜色 > 方位 > 时间 | 使用时间起卦 |
| 时辰 | 紫微无法计算 | 只用八字三柱 |

---

## 6. UI交互说明

### 6.1 右侧面板显示

**组件结构**:
- FlowGuard 信息收集进度（顶部，始终显示）
- 理论分析进度卡片（中部，可展开/收起）
- 回溯验证组件（阶段4时显示）

| 阶段 | 理论卡片显示 | 说明 |
|------|--------------|------|
| 1 | 小六壬 (已完成) | 其他理论等待中 |
| 2 | 小六壬 + 测字术 (已完成) | 其他理论等待中 |
| 3 | 全部理论卡片 | 逐个从等待→进行→完成 |
| 4 | 全部理论卡片 + 回溯验证面板 | 用户回答验证问题 |
| 5 | 全部理论卡片 + 综合置信度 | 显示最终报告 |

### 6.2 进度显示

使用FlowGuard显示信息收集进度：
- 必填信息完成度
- 可选信息完成度
- 当前阶段

---

## 7. 后续优化方向

1. **智能理论推荐**: 根据咨询类型自动推荐最适合的理论组合
2. **多轮验证**: 允许用户对初步结果进行多次反馈
3. **报告导出**: 支持导出PDF/图片格式的完整报告
4. **历史对比**: 对比多次咨询的结果变化

---

## 8. UI改动设计

### 8.1 右侧面板改动

**删除的组件**:
- ❌ 小六壬快断模块 (`xiaoliu_group`)
- ❌ 八字命盘组 (`bazi_group`)
- ❌ 简要分析组 (`analysis_group`)
- ❌ 理论详情显示区 (`theory_detail_text`)

**保留/改进的组件**:
- ✅ FlowGuard信息收集进度
- ✅ 回溯验证组件（阶段4显示）
- ✅ 当前阶段状态
- ✅ 进度条

**新增/改进**:
- 🆕 测字术卡片（加入理论列表）
- 🆕 卡片点击展开/收起详情（不在底部显示）

### 8.2 理论卡片颜色方案

基于吉凶等级的五级颜色系统：

| 等级 | 判断值 | 深色主题 | 说明 |
|------|--------|----------|------|
| 大吉 | judgment_level >= 0.8 | 🔴 喜庆红 `#DC2626` / `#7F1D1D` | 边框/背景 |
| 小吉 | 0.6 <= judgment_level < 0.8 | 🟠 喜庆橙 `#EA580C` / `#7C2D12` | 边框/背景 |
| 平 | 0.4 <= judgment_level < 0.6 | ⚪ 浅灰 `#9CA3AF` / `#374151` | 边框/背景 |
| 小凶 | 0.2 <= judgment_level < 0.4 | 🟢 深绿 `#166534` / `#14532D` | 边框/背景 |
| 大凶 | judgment_level < 0.2 | ⚫ 深黑 `#1F2937` / `#111827` | 边框/背景 |

### 8.3 理论列表更新

```python
THEORIES = ["小六壬", "测字术", "八字", "紫微斗数", "奇门遁甲", "大六壬", "六爻", "梅花易数"]
```

### 8.4 卡片展开/收起交互

```
点击卡片：
  - 当前收起状态 → 展开显示详细摘要（最多150字）
  - 当前展开状态 → 收起恢复简略显示（最多40字）

注意：不在面板底部显示详情，直接在卡片内展开
```

---

## 9. 落地规划

### 9.1 后端修改清单

| 文件 | 修改内容 | 优先级 |
|------|----------|--------|
| `services/conversation/context.py` | 新增字段: `qigua_time`, `character`, `cezi_result`, `liuyao_numbers` | P0 |
| `services/conversation_service.py` | 重构阶段处理、新增STAGE2_DEEPEN阶段 | P0 |
| `core/flow_guard.py` | 新增STAGE2_DEEPEN阶段配置 | P0 |
| `prompts/conversation/*.md` | 更新追问内容模板 | P1 |

### 9.2 前端修改清单

| 文件 | 修改内容 | 优先级 |
|------|----------|--------|
| `ui/widgets/quick_result_card.py` | 五级颜色系统、展开/收起、添加测字术 | P0 |
| `ui/tabs/ai_conversation_tab.py` | 删除旧组件、重新布局右侧面板 | P0 |

### 9.3 阶段枚举修改

```python
class ConversationStage(Enum):
    INIT = "初始化"
    STAGE1_ICEBREAK = "阶段1_破冰"      # 小六壬
    STAGE2_DEEPEN = "阶段2_深入"        # 新增: 测字
    STAGE3_COLLECT = "阶段3_信息收集"   # 多理论
    STAGE4_VERIFY = "阶段4_验证"        # 回溯
    STAGE5_REPORT = "阶段5_报告"        # 综合报告
    QA = "问答交互"
    COMPLETED = "完成"
```

### 9.4 潜在问题与解决方案

| 问题 | 影响 | 解决方案 |
|------|------|----------|
| 阶段枚举变化 | 现有保存的对话记录可能无法正确恢复 | 增加向后兼容处理 |
| 右侧面板组件删除 | 某些代码可能引用这些组件 | 全局搜索引用点 |
| FlowGuard阶段配置 | 需要新增STAGE2_DEEPEN的字段要求 | 更新STAGE_REQUIREMENTS |
| 测试用例 | 现有测试可能失败 | 更新测试用例 |

### 9.5 修改顺序

```
1. 后端数据模型 (context.py)
   ↓
2. 阶段枚举更新 (context.py)
   ↓
3. FlowGuard配置 (flow_guard.py)
   ↓
4. conversation_service阶段处理
   ↓
5. 前端UI组件 (quick_result_card.py)
   ↓
6. 前端页面 (ai_conversation_tab.py)
   ↓
7. 测试更新
   ↓
8. 文档更新
```

---

## 10. AI解析时必须附带的信息

每次调用AI解析理论结果时，必须在提示词中包含：

```python
ai_context = {
    "起卦时间": qigua_time.strftime("%Y-%m-%d %H:%M:%S"),
    "当前时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "咨询类别": question_category,
    "具体事情": question_description,
    "理论结果": theory_result
}
```

---

## 11. 回溯问题生成

回溯问题由AI根据以下信息生成：
- 用户咨询的具体事情
- 多理论计算结果
- 回溯系统设计提示词

```python
# 回溯问题生成提示词要点
回溯问题要求：
1. 针对用户咨询的具体事情
2. 基于理论计算结果中的关键判断
3. 涉及过去3-5年的重要事件
4. 简单的是/否或简短描述问题
5. 帮助验证理论分析的准确度
```

---

## 12. 报告生成（AI多轮思考）

综合报告生成流程：

```
第一轮: 收集所有理论结果，提取核心结论
   ↓
第二轮: AI深度思考用户可能的偏好和喜欢的报告形式
   - 根据提供的信息
   - 根据卦象特点
   - 根据MBTI（如有）或推算的性格
   ↓
第三轮: 生成个性化综合报告
```

---

## 13. 提示词设计与文件组织

### 13.1 提示词分类

| 类别 | 用途 | 数量 |
|------|------|------|
| 阶段回复 | 各阶段AI生成系统回复 | 5个 |
| 信息解析 | 解析用户输入中的结构化信息 | 4个 |
| 理论融合 | 综合多理论生成分析 | 2个 |
| 回溯问题 | 生成验证问题 | 1个 |
| 报告生成 | 多轮思考生成个性化报告 | 3个 |

### 13.2 提示词文件结构

```
cyber_mantic/prompts/
├── conversation/                    # 问道对话相关
│   ├── stage1_response.md          # 阶段1: 小六壬初判回复
│   ├── stage2_response.md          # 阶段2: 小六壬+测字综合回复
│   ├── stage3_response.md          # 阶段3: 多理论分析回复
│   ├── stage4_verification.md      # 阶段4: 回溯验证问题生成
│   ├── stage5_report_round1.md     # 阶段5: 报告第一轮(提取核心)
│   ├── stage5_report_round2.md     # 阶段5: 报告第二轮(用户偏好)
│   └── stage5_report_round3.md     # 阶段5: 报告第三轮(个性化)
│
├── parsing/                         # 信息解析相关
│   ├── parse_category_numbers.md   # 解析咨询类别+数字
│   ├── parse_description_char.md   # 解析具体描述+汉字
│   ├── parse_birth_info.md         # 解析生辰信息
│   └── parse_verification.md       # 解析验证问题回答
│
├── theory/                          # 理论融合相关
│   ├── combine_xiaoliu_cezi.md     # 小六壬+测字融合
│   └── combine_all_theories.md     # 全理论综合分析
│
└── common/                          # 公共模块
    ├── role_definition.md          # 角色定义(赛博玄数占卜师)
    └── output_format.md            # 输出格式规范
```

### 13.3 提示词模板规范

每个提示词文件遵循统一格式：

```markdown
---
name: stage1_response
version: 1.0
description: 阶段1小六壬初判后的系统回复生成
inputs:
  - category: 咨询类别
  - xiaoliu_result: 小六壬计算结果
  - qigua_time: 起卦时间
  - current_time: 当前时间
outputs:
  - response: 系统回复文本(含追问)
---

# 角色
{{include: common/role_definition.md}}

# 任务
根据小六壬结果给出初步判断，并自然地追问更多信息。

# 输入信息
- 咨询类别：{{category}}
- 起卦时间：{{qigua_time}}
- 当前时间：{{current_time}}
- 小六壬结果：
  - 宫位：{{xiaoliu_result.gong}}
  - 吉凶：{{xiaoliu_result.judgment}}
  - 说明：{{xiaoliu_result.explanation}}

# 输出要求
{{include: common/output_format.md}}

1. 先用50-80字描述小六壬的初步判断
2. 自然过渡到追问：
   - 请简单描述一下具体是什么事情
   - 想着这件事时，脑海中浮现的第一个汉字是什么？（可以是心态、未来的憧憬、当下想做的动作等）
3. 语气温和、专业，不要过于神秘
```

### 13.4 提示词加载器设计

```python
# prompts/loader.py 增强版

class PromptLoader:
    """提示词模板加载器"""

    def __init__(self, base_path: str = "prompts/"):
        self.base_path = Path(base_path)
        self._cache = {}

    def load(self, template_name: str, **variables) -> str:
        """
        加载并渲染模板

        Args:
            template_name: 模板名称，如 "conversation/stage1_response"
            **variables: 模板变量

        Returns:
            渲染后的提示词
        """
        template = self._get_template(template_name)
        return self._render(template, variables)

    def _get_template(self, name: str) -> str:
        """获取模板内容（带缓存）"""
        if name not in self._cache:
            path = self.base_path / f"{name}.md"
            self._cache[name] = path.read_text(encoding='utf-8')
        return self._cache[name]

    def _render(self, template: str, variables: dict) -> str:
        """渲染模板，支持include和变量替换"""
        # 处理 {{include: xxx.md}}
        template = self._process_includes(template)
        # 处理 {{variable}} 和 {{obj.field}}
        template = self._process_variables(template, variables)
        return template
```

### 13.5 提示词调用示例

```python
# conversation_service.py 中的使用

from prompts.loader import PromptLoader

class ConversationService:
    def __init__(self):
        self.prompt_loader = PromptLoader()

    def _generate_stage1_response(self, context):
        """生成阶段1的AI回复"""
        prompt = self.prompt_loader.load(
            "conversation/stage1_response",
            category=context.question_category,
            qigua_time=context.qigua_time.strftime("%Y-%m-%d %H:%M:%S"),
            current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            xiaoliu_result=context.xiaoliu_result
        )
        return self._call_ai(prompt)
```

### 13.6 梅花易数起卦逻辑

```python
def get_meihua_method(context) -> tuple[str, dict]:
    """
    确定梅花易数起卦方式

    优先级：颜色 > 方位 > 时间

    Returns:
        (起卦方式名称, 起卦参数)
    """
    if context.favorite_color:
        return ("颜色起卦", {"color": context.favorite_color})
    elif context.current_direction:
        return ("方位起卦", {"direction": context.current_direction})
    else:
        return ("时间起卦", {"time": context.qigua_time or datetime.now()})
```

---

## 14. 审核状态

✅ 大魔王审核通过的内容：
- [x] 流程步骤
- [x] 阶段划分
- [x] 六爻自动起卦（秒+微秒）
- [x] 梅花起卦（颜色 > 方位 > 时间）
- [x] 可选信息缺失时的降级方案
- [x] 追问内容修改
- [x] UI改动方案
- [x] 卡片颜色方案（小凶=深绿）
- [x] 报告多轮AI思考
- [x] 右侧面板显示（理论卡片）
- [x] 提示词设计与文件组织
