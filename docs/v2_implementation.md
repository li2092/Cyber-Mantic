# 赛博玄数 V2 版本 - 实现交付物

> 更新时间：2026-01-08
> 版本：V2.0
> 状态：阶段一至五已完成

---

## 一、功能概述

V2版本对赛博玄数进行了全面升级，主要包括：

1. **界面重构**：左侧导航栏替代顶部标签页，问道右侧面板优化
2. **时辰智能处理**：支持四种时辰状态，三柱/并行计算模式
3. **仲裁系统**：理论冲突时引入第三方裁决
4. **API拓展**：支持9种AI厂商，环节级配置
5. **动态验证**：AI生成验证问题，提高分析准确度
6. **真太阳时**：根据出生地经度校正时辰

---

## 二、核心模块说明

### 2.1 时辰智能处理系统

**入口文件**: `cyber_mantic/core/shichen_handler.py`

**时辰状态**:
| 状态 | 说明 | 处理方式 |
|------|------|----------|
| CERTAIN | 用户明确提供 | 完整四柱计算 |
| KNOWN_RANGE | 知道范围（上午/凌晨） | 范围内并行计算 |
| UNCERTAIN | 不确定是否准确 | 主时辰+相邻候选 |
| UNKNOWN | 完全不知道 | 三柱降级模式 |

**数据流**:
```
用户输入 → NLPParser.parse_birth_info_v2()
         → ShichenHandler.parse_time_input()
         → ShichenInfo

ShichenInfo → BaziCalculator.calculate_with_shichen_info()
           ├─ CERTAIN → calculate_full_bazi()
           ├─ KNOWN_RANGE/UNCERTAIN → calculate_parallel_bazi()
           └─ UNKNOWN → calculate_three_pillar()
```

### 2.2 仲裁系统

**入口文件**: `cyber_mantic/core/arbitration_system.py`

**工作流程**:
```
理论结果冲突 → ConflictInfo
            → ArbitrationSystem.should_arbitrate()
            → request_arbitration() 选择仲裁理论
            → execute_arbitration() 执行仲裁
            → ArbitrationResult
```

**仲裁理论优先级**（按问题类型）:
- 事业：六爻 > 梅花易数 > 小六壬 > 奇门遁甲
- 感情：测字术 > 梅花易数 > 六爻 > 紫微斗数
- 财运：六爻 > 奇门遁甲 > 小六壬 > 梅花易数
- 决策：奇门遁甲 > 六爻 > 大六壬 > 梅花易数

### 2.3 任务路由系统

**入口文件**: `cyber_mantic/api/task_router.py`

**支持的API厂商**:
| API | 厂商 | 默认模型 |
|-----|------|----------|
| claude | Anthropic | claude-sonnet-4-20250514 |
| deepseek | DeepSeek | deepseek-reasoner |
| kimi | Moonshot | kimi-k2-turbo |
| gemini | Google | gemini-2.0-flash-exp |
| qwen | 阿里通义 | qwen-plus |
| doubao | 字节豆包 | doubao-pro-32k |
| baichuan | 百川 | Baichuan3-Turbo |
| glm | 智谱清言 | glm-4-flash |
| openrouter | OpenRouter | anthropic/claude-3.5-sonnet |

**任务类型配置**:
- 综合报告解读 → claude/claude-3-opus
- 快速交互问答 → deepseek/deepseek-chat
- 出生信息解析 → kimi/kimi-k2-turbo-preview
- 冲突解决分析 → deepseek/deepseek-reasoner
- 回溯验证生成 → gemini/gemini-2.0-flash-exp

### 2.4 FlowGuard流程监管模块

**入口文件**: `cyber_mantic/core/flow_guard.py`

**核心功能**:
- 各阶段输入要求定义（STAGE_REQUIREMENTS）
- 输入验证器（正则+关键词）
- AI增强验证（代码优先、AI备用）
- 进度展示（类似Claude Code todo）
- 阶段引导提示生成

**验证流程**:
```
用户输入 → validate_input()（代码验证）
        ├─ VALID → 直接通过
        └─ INVALID/INCOMPLETE → validate_input_with_ai()（AI增强）
                              → 合并结果 → 返回ValidationResult
```

**主要方法**:
| 方法 | 功能 |
|------|------|
| `validate_input()` | 代码验证器 |
| `validate_input_with_ai()` | AI增强验证 |
| `smart_understand_input()` | 智能理解复杂输入 |
| `generate_progress_display()` | 生成进度展示 |
| `generate_stage_prompt()` | 生成阶段引导 |
| `handle_error_input()` | 处理错误输入 |

### 2.5 真太阳时计算器

**入口文件**: `cyber_mantic/utils/time_utils.py`

**功能**:
- 50+中国城市经度库
- 时差方程（Equation of Time）计算
- 出生时间校正，判断是否跨时辰

**使用示例**:
```python
from utils.time_utils import TrueSolarTimeCalculator

calculator = TrueSolarTimeCalculator()
result = calculator.get_correction_for_birth(
    birth_year=1990,
    birth_month=5,
    birth_day=15,
    birth_hour=23,
    birth_minute=30,
    city="乌鲁木齐"  # 经度87.6°，与北京时差大
)

# result包含:
# - true_solar_time: 真太阳时
# - shichen_changed: 是否跨时辰
# - recommendation: 建议使用的时辰
```

---

## 三、UI组件说明

### 3.1 左侧导航栏

**文件**: `cyber_mantic/ui/components/sidebar.py`

- 展开宽度：180px
- 收起宽度：60px
- 导航项：问道、推演、典籍、洞察、历史、设置、关于

### 3.2 快速结论卡片

**文件**: `cyber_mantic/ui/widgets/quick_result_card.py`

**状态**:
- WAITING（等待中）：灰色边框
- RUNNING（进行中）：蓝色边框+动画
- COMPLETED_GOOD（吉）：绿色边框
- COMPLETED_BAD（凶）：红色边框
- COMPLETED_NEUTRAL（平）：橙色边框
- ERROR（错误）：灰色+错误图标

### 3.3 验证问题组件

**文件**: `cyber_mantic/ui/widgets/verification_widget.py`

**问题类型**:
- yes_no：是/否选择
- year：年份选择
- choice：多选
- text：文本输入

### 3.4 API设置界面

**文件**: `cyber_mantic/ui/widgets/api_settings_widget.py`

**功能**:
- 全局配置：主API、备选顺序、双模型验证
- 环节配置：每个任务独立配置
- 连接测试：测试API连通性

---

## 四、MBTI适配矩阵

**文件**: `cyber_mantic/core/theory_selector.py`

完整16×8矩阵，按MBTI类型组别划分：

- **分析型(NT)**: INTJ/INTP/ENTJ/ENTP - 偏好逻辑分析类理论
- **外交型(NF)**: INFJ/INFP/ENFJ/ENFP - 偏好直觉感性类理论
- **守护型(SJ)**: ISTJ/ISFJ/ESTJ/ESFJ - 偏好系统规范类理论
- **探险型(SP)**: ISTP/ISFP/ESTP/ESFP - 偏好灵活多变类理论

---

## 五、待完善功能

| 功能 | 状态 | 说明 |
|------|------|------|
| 事件验证推断 | TODO | `narrow_by_event()` 需要实现 |
| 推演UI真太阳时 | TODO | 需要添加经度输入界面 |
| 仲裁结果UI | 待优化 | 需要更好的可视化展示 |
| 时辰确定性AI增强 | 建议 | `_analyze_time_expression` 增加AI备用 |
| 问题类型AI识别 | 建议 | `identify_question_type` 增加AI备用 |
| 阶段六测试 | 未开始 | 完整功能测试 |

---

## 六、技术栈

- **UI框架**: PyQt6 + QWebEngineView
- **AI接口**: OpenAI兼容API
- **日历**: 农历/公历转换
- **日志**: Loguru
- **缓存**: LRU缓存 + 文件持久化

---

## 七、配置文件

| 文件 | 路径 | 说明 |
|------|------|------|
| API任务配置 | `~/.cyber_mantic/api_task_config.json` | 环节级API配置 |
| 主配置 | `~/.cyber_mantic/config.json` | 应用主配置 |
| 历史记录 | `~/.cyber_mantic/history/` | 对话历史 |

---

*此文档为V2版本实现交付物，随版本更新持续完善*
