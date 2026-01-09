# 问道核心流程重构 - 任务规划书

> 最后更新: 2026-01-09
> 状态: V2代码实现完成，待测试

## 目标

重构问道对话流程，实现正确的5阶段8步骤交互：
- 除欢迎消息外，所有系统回复由AI动态生成
- 集成测字术、梅花易数等理论
- 实现回溯验证问题

## 当前状态

### 已完成 ✅

#### 设计阶段
- [x] 探索测字术模块 (`theories/cezi/`)
- [x] 探索梅花易数模块 (`theories/meihua/`)
- [x] 确认六爻使用方案A（起卦时间生成伪随机）
- [x] 确认梅花易数支持颜色/方位起卦
- [x] 设计文档编写 (`wendao_flow_design.md` 大魔王审核通过)

#### 后端实现 (P0)
- [x] `context.py` - 新增字段: `qigua_time`, `character`, `cezi_result`, `liuyao_numbers`
- [x] `context.py` - 新增阶段枚举: `STAGE2_DEEPEN`, `STAGE3_COLLECT`, `STAGE4_VERIFY`, `STAGE5_REPORT`
- [x] `context.py` - 新增方法: `generate_liuyao_numbers()`, `get_meihua_method()`
- [x] `context.py` - 向后兼容映射: `from_legacy_value()`
- [x] `flow_guard.py` - 新增STAGE2_DEEPEN阶段配置
- [x] `flow_guard.py` - 新增验证器: `validate_character`, `validate_color`, `validate_direction`
- [x] `conversation_service.py` - 重构阶段处理逻辑
- [x] `conversation_service.py` - 新增 `_handle_stage2_deepen` 方法

#### 前端实现 (P0)
- [x] `quick_result_card.py` - 五级吉凶颜色系统
- [x] `quick_result_card.py` - 添加测字术到理论列表
- [x] `quick_result_card.py` - 卡片展开/收起功能
- [x] `ai_conversation_tab.py` - 删除旧组件
- [x] `ai_conversation_tab.py` - 更新阶段枚举引用
- [x] `ai_conversation_tab.py` - 简化右侧面板

### 已完成 ✅ (P1)

#### P1: 提示词模板
- [x] 创建阶段1回复模板 (`prompts/conversation/stage1_response.md`)
- [x] 创建阶段2回复模板 (`prompts/conversation/stage2_response.md`)
- [x] 创建阶段3回复模板 (`prompts/conversation/stage3_response.md`)
- [x] 创建阶段4验证模板 (`prompts/conversation/stage4_verification.md`)
- [x] 创建阶段5报告模板（三轮）
  - `prompts/conversation/stage5_report_round1.md`
  - `prompts/conversation/stage5_report_round2.md`
  - `prompts/conversation/stage5_report_round3.md`
- [x] 创建公共模块
  - `prompts/common/role_definition.md`
  - `prompts/common/output_format.md`

#### P2: 测试与优化
- [ ] 端到端测试完整流程
- [ ] 边界情况测试（用户输入不完整）
- [ ] 可选信息缺失时的降级处理测试

## 关键文件清单

| 文件 | 作用 | 状态 |
|------|------|------|
| `services/conversation/context.py` | 对话上下文数据模型 | ✅ 已更新 |
| `services/conversation_service.py` | 对话核心服务 | ✅ 已更新 |
| `core/flow_guard.py` | 信息收集验证 | ✅ 已更新 |
| `ui/widgets/quick_result_card.py` | 理论结果卡片 | ✅ 已更新 |
| `ui/tabs/ai_conversation_tab.py` | 问道对话页面 | ✅ 已更新 |
| `prompts/conversation/*.md` | AI提示词模板 | ✅ 已创建 |
| `prompts/common/*.md` | 公共模块 | ✅ 已创建 |

## 提交记录

| 日期 | 提交 | 内容 |
|------|------|------|
| 2026-01-09 | fd7eae5 | docs: 完善问道流程设计文档（大魔王4项修正） |
| 2026-01-09 | - | feat(V2): 集成FlowGuard验证 + DynamicVerification问题生成 + 验证UI |
| 2026-01-09 | - | feat(V2): 重构问道对话流程 - 后端核心更新 |
| 2026-01-09 | - | feat(V2): 更新前端理论卡片组件 - 五级颜色系统 |
| 2026-01-09 | 91999d8 | feat(V2): 重构问道对话页面 - 删除旧组件更新阶段枚举 |

## 错误日志

（暂无）

## 下一步行动

1. ~~完成 `wendao_flow_design.md` 设计文档~~ ✅
2. ~~大魔王审核设计文档~~ ✅
3. ~~后端代码实现~~ ✅
4. ~~前端代码实现~~ ✅
5. ~~创建提示词模板文件~~ ✅
6. **端到端测试** ← 当前任务
7. 修复发现的问题
