# Prompt 模板目录

> **版本**: v4.0
> **更新日期**: 2026-01-05

---

## 目录结构

```
docs/prompts/
├── README.md                    # 本说明文件
├── system/                      # 系统级
│   ├── base_persona.md          # AI人设基础
│   └── safety_guidelines.md     # 安全准则
│
├── analysis/                    # 分析类（推演）
│   ├── bazi/                    # 八字（支持多版本）
│   │   ├── default.md           # 默认版本
│   │   ├── variant_a.md         # 变体A：简洁风格
│   │   └── variant_b.md         # 变体B：详细风格
│   ├── ziwei.md                 # 紫微斗数
│   ├── qimen.md                 # 奇门遁甲
│   ├── liuyao.md                # 六爻
│   ├── meihua.md                # 梅花易数
│   ├── xiaoliu.md               # 小六壬
│   ├── daliuren.md              # 大六壬
│   ├── cezi.md                  # 测字
│   └── comprehensive.md         # 综合报告
│
├── conversation/                # 对话类（问道）
│   ├── greeting.md              # 开场白
│   ├── clarification.md         # 追问澄清
│   ├── followup.md              # 追问深入
│   └── summary.md               # 对话总结
│
├── conflict/                    # 冲突解决
│   └── resolution.md            # 多理论冲突调和
│
├── insight/                     # 洞察模块
│   ├── profile_analysis.md      # 画像分析（DeepSeek-R1）
│   └── care_response.md         # 关怀话语生成
│
└── library/                     # 典籍模块
    ├── summarize.md             # 总结
    ├── insight.md               # 洞察
    ├── study_plan.md            # 学习方案
    └── reflection.md            # 心得生成
```

---

## 变量语法

使用双花括号 `{{variable_name}}` 定义变量。

### 示例

```markdown
# 八字分析 Prompt

你是一位专业的八字分析师。

## 用户信息
- 出生时间：{{birth_info}}
- 性别：{{gender}}
- 问题：{{question}}

## 排盘结果
{{bazi_chart}}
```

---

## 支持的变量

### 通用变量

| 变量名 | 说明 |
|--------|------|
| `{{current_time}}` | 当前时间 |
| `{{current_year}}` | 当前年份 |
| `{{user_name}}` | 用户姓名（如有） |

### 出生信息

| 变量名 | 说明 |
|--------|------|
| `{{birth_info}}` | 完整出生信息 |
| `{{gender}}` | 性别 |
| `{{mbti_type}}` | MBTI类型 |

### 问题相关

| 变量名 | 说明 |
|--------|------|
| `{{question_type}}` | 问题类别 |
| `{{question}}` | 具体问题 |
| `{{inquiry_time}}` | 起卦/起课时间 |

### 排盘结果

| 变量名 | 说明 |
|--------|------|
| `{{bazi_chart}}` | 八字排盘结果 |
| `{{ziwei_chart}}` | 紫微排盘结果 |
| `{{qimen_chart}}` | 奇门盘 |
| `{{liuyao_chart}}` | 六爻卦象 |
| `{{meihua_chart}}` | 梅花卦象 |
| `{{xiaoliu_chart}}` | 小六壬结果 |
| `{{daliuren_chart}}` | 大六壬课式 |
| `{{theory_results}}` | 多理论结果汇总 |

### 对话相关

| 变量名 | 说明 |
|--------|------|
| `{{conversation_history}}` | 对话历史 |
| `{{user_input}}` | 用户输入 |
| `{{previous_analysis}}` | 之前的分析结果 |

---

## A/B测试

### 目录变体

对于需要多版本的 Prompt，使用目录方式：

```
analysis/bazi/
├── default.md      # 默认版本
├── variant_a.md    # 变体A
└── variant_b.md    # 变体B
```

### 配置方式

在 `config.yaml` 中配置变体：

```yaml
prompts:
  variants:
    analysis/bazi: "variant_a"      # 八字用变体A
    conversation/greeting: "default" # 开场白用默认
```

### 设置界面

用户可在"设置 > 高级设置 > Prompt配置"中切换变体。

---

## 使用方法

```python
from api.prompt_loader import get_prompt_loader

loader = get_prompt_loader()

# 加载分析类 Prompt
prompt = loader.get(
    "analysis", "bazi",
    birth_info="1990年5月20日 午时",
    gender="男",
    question_type="事业",
    question="今年是否适合跳槽？",
    bazi_chart="...",
    current_year="2026"
)

# 加载对话类 Prompt
greeting = loader.get(
    "conversation", "greeting",
    current_time="下午好"
)

# 列出可用变体
variants = loader.list_variants("analysis", "bazi")
# ['default', 'variant_a', 'variant_b']

# 切换变体
loader.set_variant("analysis/bazi", "variant_b")
```

---

## Review 流程

| 阶段 | 方式 |
|------|------|
| 开发期 | Git PR审核，每次Prompt修改需Review |
| 运行期 | 设置页提供"预览当前Prompt"功能（只读） |
| 版本管理 | Prompt文件纳入Git版本控制 |

---

## 注意事项

1. **变量名区分大小写**
2. **未替换的变量会保留原样**
3. **修改Prompt后可调用 `loader.reload()` 热重载**
4. **Prompt文件使用 UTF-8 编码**
