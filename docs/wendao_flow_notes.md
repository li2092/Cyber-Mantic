# 问道核心流程重构 - 笔记

## 理论模块分析

### 1. 测字术 (CeZiTheory)

**位置**: `theories/cezi/theory.py`

**输入要求**:
- 必须: `question_description`, `character`（字）
- 可选: `birth_time`, `current_time`

**字的提取方式**（优先级）:
1. "测X字" 模式匹配
2. 引号中的字
3. 第一个非常见汉字
4. 时辰地支

**输出**:
```python
{
    "吉凶判断": "...",
    "综合评分": 0.5,
    "建议": "...",
    "置信度": 0.65
}
```

### 2. 梅花易数 (MeiHuaTheory)

**位置**: `theories/meihua/theory.py`

**起卦方式**:
| 方式 | 输入字段 | 说明 |
|------|----------|------|
| 数字起卦 | `numbers` | 2-3个数字 |
| 颜色起卦 | `favorite_color` | 配合当前时间 |
| 方位起卦 | `current_direction` | 配合当前时间 |
| 时间起卦 | `current_time` | 默认方式 |

**颜色映射** (`COLOR_TO_GUA`):
- 红色 → 离卦
- 蓝色 → 坎卦
- 等等...

**方位映射** (`DIRECTION_TO_GUA`):
- 东 → 震卦
- 西 → 兑卦
- 等等...

**输出**:
```python
{
    "起卦方式": "颜色起卦",
    "本卦": {...},
    "互卦": {...},
    "变卦": {...},
    "体用关系": "用生体",
    "judgment": "吉",
    "advice": "..."
}
```

### 3. 六爻 (LiuYaoTheory)

**需要确认**: 自动起卦方式

**方案A实现思路**:
```python
import time
from datetime import datetime

def generate_liuyao_numbers(起卦时间: datetime) -> list:
    """
    用起卦时间生成六爻数字

    方法：
    - 时间戳的各部分组合
    - 秒数 % 8 + 1 作为基数
    """
    ts = 起卦时间.timestamp()
    秒 = int(ts) % 60
    微秒 = int((ts % 1) * 1000000)

    # 生成3个1-9的数字
    num1 = (秒 % 9) + 1
    num2 = ((秒 + 微秒 // 1000) % 9) + 1
    num3 = ((秒 + 微秒 // 100) % 9) + 1

    return [num1, num2, num3]
```

## 数据流设计

### ConversationContext 新增字段

```python
# 阶段2新增
self.character: Optional[str] = None  # 测字用的汉字

# 阶段3新增（已有部分）
self.current_direction: Optional[str] = None  # 方位
self.favorite_color: Optional[str] = None  # 颜色
self.liuyao_numbers: List[int] = []  # 六爻起卦数字（自动生成）
```

### 各阶段数据收集

| 阶段 | 收集数据 | 用途 |
|------|----------|------|
| 1 | 咨询大类、3数字、起卦时间 | 小六壬 |
| 2 | 具体描述、汉字 | 测字术 |
| 3 | 生辰、性别、MBTI、颜色/方位 | 八字、梅花 |
| 4 | 验证问题回答 | 置信度调整 |
| 5 | - | 综合报告 |

## AI提示词设计思路

### 阶段2系统回复（小六壬初判后）

```
角色：你是赛博玄数的占卜师
任务：根据小六壬结果给出初步判断，并追问具体信息

小六壬结果：{{xiaoliu_result}}
咨询类别：{{category}}

请生成回复：
1. 简述小六壬的初步判断（50-80字）
2. 自然地追问：
   - 请简单描述一下具体是什么事情
   - 请想一个与这件事相关的汉字
```

### 阶段4系统回复（综合分析后）

```
角色：你是赛博玄数的占卜师
任务：综合多理论给出详细分析，并追问详细信息

已有分析：
- 小六壬：{{xiaoliu_result}}
- 测字术：{{cezi_result}}

请生成回复：
1. 综合小六壬和测字术的分析（100-150字）
2. 自然地追问详细信息：
   - 生辰八字（可模糊/不知道时辰）
   - 性别
   - MBTI（可选）
   - 颜色/方位（二选一，可选）
```

## 待解决问题

### 1. 颜色/方位二选一如何实现？

**方案A**: 在提示词中说明"选择颜色或方位其一"
**方案B**: UI上提供单选按钮

建议采用方案A，让用户自然输入。

### 2. 六爻数字如何展示给用户？

**方案A**: 不展示，后台自动完成
**方案B**: 展示"天机所定"的三个数字

建议方案B，增加神秘感和仪式感。

### 3. 可选信息缺失时如何处理？

- MBTI缺失：跳过MBTI相关分析
- 颜色/方位都缺失：梅花易数使用时间起卦
- 时辰缺失：使用三柱八字分析

## 已实现功能（2026-01-09）

### 后端核心更新

| 文件 | 改动 | 状态 |
|------|------|------|
| `context.py` | 新增阶段枚举、字段、辅助方法 | ✅ |
| `flow_guard.py` | 新增STAGE2_DEEPEN、验证器 | ✅ |
| `conversation_service.py` | 重构阶段处理逻辑 | ✅ |
| `quick_result_card.py` | 五级颜色、测字术、展开收起 | ✅ |

### 关键代码片段

**context.py 新增字段**:
```python
# 阶段1
self.qigua_time: Optional[datetime] = None    # 起卦时间

# 阶段2（V2新增）
self.character: Optional[str] = None          # 测字用的汉字
self.cezi_result: Optional[Dict] = None       # 测字结果

# 阶段3
self.liuyao_numbers: List[int] = []           # 六爻自动数字
```

**五级颜色系统**:
```python
# 设计文档 wendao_flow_design.md 第8.2节
大吉 (>=0.8): #DC2626 / #7F1D1D  # 喜庆红
小吉 (0.6-0.8): #EA580C / #7C2D12  # 喜庆橙
平 (0.4-0.6): #9CA3AF / #374151  # 浅灰
小凶 (0.2-0.4): #166534 / #14532D  # 深绿
大凶 (<0.2): #1F2937 / #111827  # 深黑
```

### 待完成功能

| 任务 | 状态 |
|------|------|
| ai_conversation_tab.py 删除旧组件 | ✅ 已完成 |
| 提示词模板文件创建 | 待处理 |
| 三文件系统更新 | ✅ 已完成 |

### ai_conversation_tab.py 修改记录 (2026-01-09)

**删除的组件**:
- `xiaoliu_group` (小六壬快断卡片)
- `bazi_group` (八字命盘组)
- `analysis_group` (简要分析组)
- `status_group` (分析状态组)
- `theory_detail_text` (理论详情显示区)

**更新的阶段枚举**:
```python
# 旧 → 新
STAGE2_BASIC_INFO → STAGE2_DEEPEN
STAGE3_SUPPLEMENT → STAGE3_COLLECT
STAGE4_VERIFICATION → STAGE4_VERIFY
STAGE5_FINAL_REPORT → STAGE5_REPORT
```

**简化的方法**:
- `_update_right_panel()`: 删除旧组件引用，保留阶段显示、FlowGuard进度、验证面板
- `_show_theory_detail()`: 简化为日志记录（详情通过卡片展开显示）
- `_start_new_conversation()`: 移除旧组件重置代码

**删除的方法**:
- `_update_xiaoliu_card()`: 小六壬已整合到 quick_result_panel

---

## 测试用例设计

### 正常流程

```
用户: 事业，3 5 7
系统: [小六壬初判] + 追问具体事情和汉字
用户: 想跳槽，"变"字
系统: [小六壬+测字综合] + 追问详细信息
用户: 1990年5月15日，男，不记得时辰，INTJ，红色
系统: [多理论分析] + 回溯验证问题
用户: 是的，去年确实换了工作
系统: [综合报告]
```

### 边界情况

1. 用户只说大类不给数字
2. 用户不想说汉字
3. 用户不想提供任何可选信息
4. 用户中途想换话题
