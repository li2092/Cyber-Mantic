# 问道核心流程重构 - 任务规划书

## 目标

重构问道对话流程，实现正确的5阶段8步骤交互：
- 除欢迎消息外，所有系统回复由AI动态生成
- 集成测字术、梅花易数等理论
- 实现回溯验证问题

## 当前状态

### 已完成
- [x] 探索测字术模块 (`theories/cezi/`)
- [x] 探索梅花易数模块 (`theories/meihua/`)
- [x] 确认六爻使用方案A（起卦时间生成伪随机）
- [x] 确认梅花易数支持颜色/方位起卦

### 已完成
- [x] 设计文档编写 (`wendao_flow_design.md` 大魔王审核通过)

### 待处理
- [ ] 重新定义ConversationStage枚举
- [ ] 修改conversation_service.py阶段处理
- [ ] 集成测字术到阶段2
- [ ] 集成梅花易数到阶段3
- [ ] 实现六爻自动起卦

## 阶段规划

### P0: 核心流程重构（必须）
1. 重新设计阶段枚举和数据流
2. 修改各阶段处理逻辑
3. 集成测字术
4. 集成梅花易数（颜色/方位二选一）
5. 实现六爻自动起卦

### P1: AI回复优化
1. 为每个阶段设计AI提示词模板
2. 确保追问内容自然流畅

### P2: 边界处理
1. 用户输入不完整时的处理
2. 可选信息缺失时的降级处理

## 关键文件清单

| 文件 | 作用 | 修改内容 |
|------|------|----------|
| `services/conversation/context.py` | 数据模型 | 添加character字段 |
| `services/conversation_service.py` | 核心服务 | 重构阶段处理 |
| `theories/cezi/theory.py` | 测字术 | 已有，无需修改 |
| `theories/meihua/theory.py` | 梅花易数 | 已有，无需修改 |
| `theories/liuyao/theory.py` | 六爻 | 确认自动起卦方式 |

## 错误日志

（暂无）

## 下一步行动

~~1. 完成 `wendao_flow_design.md` 设计文档~~  ✅
~~2. 大魔王审核设计文档~~ ✅

3. 按以下顺序开始代码实现：
   - 后端数据模型 (`context.py`)
   - 阶段枚举更新
   - FlowGuard配置 (`flow_guard.py`)
   - `conversation_service.py` 阶段处理
   - 前端UI组件 (`quick_result_card.py`)
   - 前端页面 (`ai_conversation_tab.py`)
   - 提示词模板文件创建
   - 测试更新
