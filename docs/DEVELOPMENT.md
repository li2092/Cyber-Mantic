# 开发指南

> 从 dev/ 文件夹 27 个文件中精炼的核心内容

---

## 系统架构

```
用户输入 → 理论选择器 → 并行计算 → AI解读 → 冲突检测 → 报告生成
              ↓
     选3-5个最匹配的理论
              ↓
    ┌────────────────────────────────────────┐
    │  八字  紫微  奇门  六壬  六爻  梅花  小六壬  测字  │
    │   ↓     ↓     ↓     ↓     ↓     ↓      ↓      ↓   │
    │        calculator.py (纯算法，无LLM)              │
    └────────────────────────────────────────┘
              ↓
     Claude/Gemini/Deepseek/Kimi 解读计算结果
              ↓
     4级冲突解决（一致/微小差异/显著差异/严重冲突）
              ↓
     综合报告 + AI摘要 + 行动建议
```

**核心原则**：计算与解读分离。所有干支排盘由代码实现，AI只负责"翻译成人话"。

---

## 目录结构

```
cyber_mantic/
├── main.py / gui.py     # 入口
├── models.py            # 数据模型
├── core/
│   ├── decision_engine.py    # 主引擎，串联整个流程
│   ├── theory_selector.py    # 8维特征向量+余弦相似度选理论
│   └── conflict_resolver.py  # 4级冲突检测
├── theories/
│   ├── base.py               # 基类，定义calculate()接口
│   ├── bazi/calculator.py    # 八字（含神煞）
│   ├── ziwei/calculator.py   # 紫微斗数
│   ├── qimen/calculator_v2.py   # 奇门遁甲 V2（完整算法）
│   ├── daliuren/calculator_v2.py # 大六壬 V2（完整发用规则）
│   ├── liuyao/theory.py      # 六爻
│   ├── meihua/theory.py      # 梅花易数
│   ├── xiaoliu/theory.py     # 小六壬
│   └── cezi/calculator.py    # 测字术
├── services/
│   ├── conversation_service.py  # 5阶段AI对话（问道模式）
│   └── analysis_service.py      # 直接分析（推演模式）
├── api/
│   └── manager.py            # 多AI提供商管理（自动降级）
└── ui/
    └── main_window.py        # PyQt6界面
```

---

## 两种使用模式

### 问道（对话模式）
5阶段渐进收集信息：
1. **破冰**：事件分类 + 小六壬快速判断
2. **基础信息**：出生年月日、性别、MBTI
3. **深度补充**：出生时辰、额外起卦
4. **结果确认**：回溯验证过去3-5年
5. **完整报告**：综合分析 + 持续问答

### 推演（直接模式）
一次性输入 → 自动选择理论 → 并行计算 → 综合报告

---

## 已知问题

### 需要关注
1. **农历转换**：第三方库 lunardate 有 bug，影响准确性
2. **理论选择数量**：有时只选 1 个而非 3-5 个，需检查阈值
3. **对话历史无上限**：长对话可能内存占用过大

### 已解决（V2 版本）
- 奇门遁甲：V2 实现了完整的超神接气法、九宫排布、值符值使
- 大六壬：V2 实现了九宗门发用规则、天将昼夜顺逆配置

---

## 测试状态

最近一次测试（2026-01-04）：
- 总测试：362 个
- 通过率：97.8%（354/362）
- 失败：4 个（农历转换、理论选择相关）

运行测试：`pytest tests/`

---

## 扩展指南

### 添加新术数理论

1. 创建目录 `theories/新理论/`
2. 实现 `calculator.py`（纯算法）
3. 实现 `theory.py`（继承 BaseTheory）
4. 在 `theories/__init__.py` 注册

```python
# theories/新理论/theory.py
from theories.base import BaseTheory

class XxxTheory(BaseTheory):
    name = "新理论"

    def get_required_fields(self):
        return ["birth_year", "birth_month"]

    def calculate(self, user_input):
        # 调用 calculator 计算
        result = XxxCalculator().calculate(...)
        return {"raw_data": result, "calculation_log": [...]}
```

### 添加新 AI 提供商

修改 `api/manager.py`，按优先级添加（claude > gemini > deepseek > kimi）。

---

## 配置

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env，至少配置一个 API 密钥
CLAUDE_API_KEY=xxx
GEMINI_API_KEY=xxx
DEEPSEEK_API_KEY=xxx
KIMI_API_KEY=xxx
```

---

## 开发历程摘要

| 阶段 | 完成内容 |
|------|---------|
| Phase 1 | 服务层分离（conversation/report/analysis/export） |
| Phase 2-3 | UI 组件（chat/progress/export/theme） |
| Phase 4 | 报告自定义（模板管理器） |
| Phase 5 | 报告对比功能 |
| Phase 6 | 主窗口集成 + 统一错误处理 |

功能暴露率：27% → 100%

---

## 下一步建议

1. **修复农历转换**：考虑换用 cnlunar 或自研
2. **优化理论选择**：调整适配度阈值
3. **性能监控**：添加耗时日志
4. **对话历史限制**：设置最大 100 条
