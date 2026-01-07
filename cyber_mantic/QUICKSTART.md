# 快速开始指南

## 5分钟上手赛博玄数 (v4.0)

### 步骤1: 安装依赖

```bash
cd cyber_mantic
pip install -r requirements.txt
```

### 步骤2: 配置API密钥

1. 复制环境变量模板：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，填入你的API密钥（至少配置一个AI提供商）：
```env
# AI提供商（至少配置一个）
CLAUDE_API_KEY=sk-ant-...     # 推荐：Claude API（高质量深度解读）
GEMINI_API_KEY=...            # Google Gemini（速度快）
DEEPSEEK_API_KEY=sk-...       # Deepseek（成本优化）
KIMI_API_KEY=...              # Kimi/Moonshot（国内稳定）

# 高德地图API（可选，用于GUI地点查询）
AMAP_API_KEY=...              # 高德地图（地理编码，自动查询经纬度）
```

**如何获取API密钥：**
- Claude API: https://console.anthropic.com/
- Gemini API: https://aistudio.google.com/
- Deepseek API: https://platform.deepseek.com/
- Kimi API: https://platform.moonshot.cn/
- 高德地图API: https://console.amap.com/dev/key/app （可选，用于地点查询）

### 步骤3: 运行GUI界面（推荐）

```bash
python gui.py
```

启动PyQt6桌面界面，提供完整的可视化交互：
- ✅ 图形化输入表单（支持所有8个理论的输入需求）
- ✅ 实时分析进度显示
- ✅ 美化的报告展示（可视化进度条、格式化文本）
- ✅ 多标签页结果展示（执行摘要、详细分析、各理论结果）
- ✅ 报告保存功能

**GUI功能亮点（v3.1）：**
- 📅 起卦时间设置（自定义或使用当前时间）
- 👤 完整的出生信息（年月日时分、性别、历法类型）
- 📍 **智能地点查询**（输入"北京市朝阳区"自动获取经度）✨新增
- 🔢 随机数输入（用于梅花易数、六爻）
- 📝 测字输入（用于测字术）
- 🎚️ 可选字段系统（根据需要勾选提供）

**注意**：需要安装PyQt6：`pip install PyQt6`

**智能地点查询说明**：
- 配置高德地图API密钥后，可在GUI输入出生地点（如"上海市浦东新区"）
- 点击"查询经纬度"按钮，系统自动调用高德API获取精确经度
- 经度用于真太阳时计算，提高八字排盘准确性
- 未配置API密钥也可手动输入经度（如120.5）

### 步骤4: 命令行模式（可选）

#### 运行示例
```bash
python main.py
```

这将运行一个内置的示例分析，展示系统的完整功能。

#### 交互式使用
```bash
python main.py --interactive
```

然后根据提示输入：
1. 选择问题类别（如：1=事业，2=财运等）
2. 描述你的问题
3. 输入出生信息（可选）
4. 输入3个随机数字

系统会自动：
- 选择最适合的3-5个术数理论（从全部8个中选择）
- 进行计算和分析
- 智能冲突解决（4级冲突处理）
- 生成综合报告

## 支持的术数理论（v3.1 - 全部8个）

| 理论 | 类型 | 最低信息需求 | 适用场景 |
|-----|------|-------------|---------|
| 八字 | 命理类 | 出生年月日 | 一生运势、性格分析 |
| 小六壬 | 快速类 | 随机数字/时间 | 快速吉凶判断 |
| 奇门遁甲 | 占卜类 | 当前时间 | 具体事件决策 |
| 梅花易数 | 快速类 | 随机数/外应 | 快速吉凶判断 |
| 六爻 | 占卜类 | 随机数字 | 具体问题占断 |
| 紫微斗数 | 命理类 | 出生年月日时 | 一生格局分析 |
| **大六壬** | 占卜类 | 当前时间 | 事态过程预测 |
| **测字术** | 快速类 | 一个汉字 | 心理状态解读 |

## 编程接口示例

```python
import asyncio
from datetime import datetime
from models import UserInput
from core import DecisionEngine
import yaml

# 加载配置
with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# 创建决策引擎
engine = DecisionEngine(config)

# 创建用户输入（完整示例）
user_input = UserInput(
    question_type="事业",
    question_description="我想知道2025年的事业运势如何，是否适合换工作",
    birth_year=1990,
    birth_month=6,
    birth_day=15,
    birth_hour=10,
    birth_minute=30,
    calendar_type="solar",  # "solar" 或 "lunar"
    gender="male",  # "male" 或 "female"
    birth_place_lng=120.5,  # 出生地经度（用于真太阳时）
    numbers=[3, 7, 5],
    character="问",  # 用于测字术
    current_time=datetime.now(),
    initial_inquiry_time=datetime.now()  # 起卦时间
)

# 执行分析
async def main():
    report = await engine.analyze(user_input)

    # 查看结果
    print(f"选用理论: {', '.join(report.selected_theories)}")
    print(f"综合置信度: {report.overall_confidence:.2%}")
    print(f"\n{report.executive_summary}")

    # 查看各理论结果
    for result in report.theory_results:
        print(f"\n【{result.theory_name}】")
        print(f"判断：{result.judgment}（程度：{result.judgment_level:.2f}）")
        print(f"建议：{result.advice}")

asyncio.run(main())
```

## 常见问题

### Q: 我不知道出生时辰怎么办？
A: 没关系！系统会自动选择不需要时辰的理论（如小六壬、梅花易数），并降低对时辰敏感的理论（如八字）的权重。

### Q: 系统支持哪些问题类型？
A: 支持以下类型：
- 事业：工作、跳槽、晋升
- 财运：投资、理财、收入
- 感情：恋爱、关系发展
- 婚姻：结婚时机、婚姻状况
- 健康：身体状况、疾病预防
- 学业：考试、升学
- 人际：人际关系、社交
- 择时：选择最佳时机
- 决策：重要决策辅助
- 性格：性格分析

### Q: 如何提高分析的准确度？
A: 提供更多信息（GUI支持所有这些输入）：
- **出生时辰**（可提高八字、紫微斗数准确度）
- **性别**（用于排大运、确定命宫）
- **历法类型**（农历/阳历，影响八字排盘）
- **出生地点**（使用智能查询自动获取经度，用于真太阳时计算）✨推荐
- **3个随机数字**（用于梅花易数、六爻）
- **一个汉字**（用于测字术）
- **起卦时间**（用于奇门遁甲、六爻等时间敏感理论）

### Q: 什么是智能地点查询？如何使用？
A: v3.1新增功能，用于提高八字排盘的地理精度：
- **作用**：根据出生地点自动获取经度，用于真太阳时修正
- **使用方法**：
  1. 在`.env`中配置`AMAP_API_KEY`（在https://console.amap.com/申请）
  2. GUI界面勾选"提供出生信息"
  3. 在"出生地点"输入框填写地址（如"杭州市西湖区"）
  4. 点击"查询经纬度"按钮
  5. 系统自动填充经度到输入框
- **是否必须**：可选功能，不配置可手动输入经度或留空
- **为什么重要**：不同经度对应的真太阳时不同，影响时柱准确性

### Q: 分析需要多长时间？
A: 通常30-60秒，取决于：
- 选择的理论数量（3-5个）
- API响应速度
- 网络状况

## 进阶使用

### 自定义配置

编辑 `config.yaml` 可以调整：

```yaml
analysis:
  max_theories: 5      # 最多选择几个理论
  min_theories: 3      # 最少选择几个理论
  enable_quick_feedback: true  # 是否启用快速反馈

api:
  providers:           # 多API提供商配置（v3.0+）
    - claude          # 优先级1
    - gemini          # 优先级2
    - deepseek        # 优先级3
    - kimi            # 优先级4
  dual_model_verification: true  # 双模型验证
  timeout: 30               # 超时时间（秒）
  max_retries: 3            # 最大重试次数

conflict_resolution:  # 冲突解决配置（v3.0+）
  enable: true
  penalty_factor: 0.7  # Level 4冲突惩罚因子
```

### 保存分析报告

```python
# 保存为JSON
with open(f"report_{report.report_id}.json", 'w', encoding='utf-8') as f:
    f.write(report.to_json())

# 保存为纯文本
with open(f"report_{report.report_id}.txt", 'w', encoding='utf-8') as f:
    f.write(f"=== 赛博玄数分析报告 ===\n\n")
    f.write(f"报告ID: {report.report_id}\n")
    f.write(f"创建时间: {report.created_at}\n")
    f.write(f"选用理论: {', '.join(report.selected_theories)}\n\n")
    f.write(report.executive_summary)
```

## 下一步

- 📖 查看 [README.md](README.md) 了解系统架构和完整功能
- 📝 查看 [CHANGELOG.md](CHANGELOG.md) 了解版本更新历史
- 🔍 探索 `theories/` 目录了解各术数理论的实现细节
- 💻 参与开发：
  - 优化现有理论算法
  - 改进GUI界面
  - 添加测试用例
  - 完善文档

## 📚 文档说明

- **README.md** - 项目主文档，包含完整功能介绍、系统架构、安装指南
- **QUICKSTART.md**（本文档）- 快速上手指南，5分钟开始使用
- **CHANGELOG.md** - 版本更新日志，记录所有功能变更

---

有问题？欢迎提交 Issue！
