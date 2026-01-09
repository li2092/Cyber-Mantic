# 问道界面完善 - 任务规划书

> 更新时间：2026-01-09
> 负责人：Claude + 大魔王
> 状态：🟢 P0/P1完成，P2优化中

---

## 一、目标

完善"问道"界面的功能和用户体验，确保V2版本设计的功能真正落地到前端。

---

## 二、当前状态

### ✅ 最新进展（2026-01-09 核心功能完善）

| 任务 | 状态 | 说明 |
|------| **仲裁系统UI集成** | ✅ 完成 | QuickResultCard新增ARBITRATING状态，支持仲裁进度显示 |
| **理论选择优化** | ✅ 完成 | 动态阈值算法，确保至少选出min_theories个理论 |
| **破冰解析fallback** | ✅ 完成 | parse_icebreak_input新增代码备用解析 |
|------|------|
| **welcome.md内容修复** | ✅ 完成 | 与设计文档 `wendao_flow_design.md` 保持一致 |
| **stage1_complete.md修复** | ✅ 完成 | 追问"具体描述+汉字"而非"出生信息" |
| **stage2_complete.md修复** | ✅ 完成 | 追问"出生信息+性别+MBTI" |
| **stage3_collect_complete.md新增** | ✅ 完成 | 阶段3信息收集完成后的模板 |
| 自动化测试框架 | ✅ 完成 | 29个测试用例全部通过 |
| FlowGuard AI优先验证 | ✅ 完成 | AI提取优先，代码后备 |
| 颜色/方位提取优化 | ✅ 完成 | 复合词优先匹配（粉红→粉，西北→西北） |
| 语气词提取修复 | ✅ 完成 | 用户明确指定的语气词也可测 |
| Stage1逻辑优化 | ✅ 完成 | FlowGuard成功时跳过NLP解析 |

### ✅ P0任务已完成（文档未及时更新）

| 问题 | 严重程度 | 状态 | 说明 |
|------|---------|------|------|
| 欢迎消息硬编码 | P0 | ✅ 已修复 | 使用 `load_prompt("conversation/welcome.md")` |
| 阶段提示硬编码 | P0 | ✅ 已修复 | 各阶段均使用 `load_prompt()` |
| 回溯校验UI缺失 | P0 | ✅ 已修复 | `VerificationPanel` 已集成 |
| FlowGuard输入验证 | P0 | ✅ 已修复 | Stage1/2/3 均已启用AI验证 |
| 动态验证问题集成 | P1 | ✅ 已修复 | `DynamicVerificationGenerator` 已使用 |
| 置信度调整机制 | P1 | ✅ 已修复 | 验证反馈后调整置信度 |

### 🟡 待优化问题

| 问题 | 严重程度 | 状态 |
|------|---------|------|
| NLP解析Prompt仍为硬编码 | P2 | ✅ 已完成（使用load_prompt） |
| 理论选择数量硬编码 | P2 | ✅ 已完成（动态阈值算法） |
| FlowGuard进度显示位置 | P2 | ✅ 已修复（移到右侧面板最顶端） |
| 用户信息编辑 | P2 | ✅ 已完成（对话指令方案B） |

### 已修复的问题 (2026-01-08)

| 问题 | 位置 | 状态 |
|------|------|------|
| 优先API设置不生效 | `api/manager.py` | ✅ 已修复 |
| INIT阶段报错 | `conversation_service.py` | ✅ 已修复 |
| Worker线程安全控制 | `ai_conversation_tab.py` | ✅ 已修复 |
| 打字机效果卡顿 | `chat_widget.py` | ✅ 已修复 |
| 用户消息右对齐 | `chat_widget.py` | ✅ 已修复 |
| selected_theories字典错误 | 多处 | ✅ 已修复 |
| UI主题对比度问题 | 多处 | ✅ 已修复 |

---
### 已修复的问题 (2026-01-09)

| 问题 | 位置 | 状态 |
|------|------|------|
| 仲裁系统UI缺失 | ,  | ✅ 已完成 |
| 理论选择数量不稳定 |  | ✅ 已完成 |
| parse_icebreak_input无fallback |  | ✅ 已完成 |

---

## 三、硬编码问题清单

### 3.1 对话内容硬编码

| 位置 | 硬编码内容 | 应该使用 |
|------|-----------|---------|
| `conversation_service.py:130-159` | 欢迎消息 | `prompts/conversation/greeting.md` |
| `conversation_service.py:274-300` | 阶段1完成提示 | 配置化模板 |
| `conversation_service.py:350-368` | 补充信息提示 | 配置化模板 |
| `conversation_service.py:361-368` | 回溯验证提示 | 动态生成 |
| `nlp_parser.py:84-116` | 破冰解析Prompt | 外部模板 |
| `nlp_parser.py:152-194` | 出生信息解析Prompt | 外部模板 |

### 3.2 流程控制硬编码

| 位置 | 硬编码内容 |
|------|-----------|
| `conversation_service.py:322-325` | 阶段跳转条件 |
| `conversation_service.py:535` | 理论选择数量 (max=6, min=3) |
| `conversation_service.py:363` | 回溯验证时间范围 ("过去3年") |

### 3.3 FlowGuard功能集成状态

| 功能 | 后端实现 | 前端调用 | 状态 |
|------|---------|---------|------|
| 进度显示 | ✅ | ✅ | ✅ 完成 |
| AI增强输入验证 | ✅ | ✅ | ✅ 完成（Stage1/2/3） |
| 阶段跳转防护 | ✅ | ✅ | ✅ 完成（ConversationStage枚举） |
| 错误友好提示 | ✅ | ✅ | ✅ 完成（ValidationResult） |
| 信息完整性检查 | ✅ | ✅ | ✅ 完成（required字段验证） |

---

## 四、修复计划

### Phase 1: P0紧急修复 ✅ 已完成

**目标**：让V2核心功能真正工作

#### 任务1.1：创建提示词加载器 ✅
- 文件：`cyber_mantic/prompts/loader.py` 已创建
- 功能：`load_prompt()` 统一加载和渲染模板

#### 任务1.2：替换硬编码消息 ✅
- 欢迎消息 → `load_prompt("conversation/welcome.md")`
- Stage1完成 → `load_prompt("conversation/stage1_complete.md")`
- Stage2完成 → `load_prompt("conversation/stage2_complete.md")`
- Stage3完成 → `load_prompt("conversation/stage3_collect_complete.md")`

#### 任务1.3：启用FlowGuard验证 ✅
- Stage1: `validate_input_with_ai("STAGE1_ICEBREAK")`
- Stage2: `validate_input_with_ai("STAGE2_DEEPEN")`
- Stage3: `validate_input_with_ai("STAGE3_COLLECT")`

#### 任务1.4：实现回溯验证UI ✅
- 文件：`ui/widgets/verification_widget.py` 已创建
- 组件：`VerificationPanel` 已集成到 `ai_conversation_tab.py`
- 功能：动态验证问题、结构化反馈、置信度更新

### Phase 2: P1重要修复 ✅ 已完成

#### 任务2.1：阶段提示模板化 ✅
已创建模板：
- `prompts/conversation/stage1_complete.md` ✅
- `prompts/conversation/stage2_complete.md` ✅
- `prompts/conversation/stage3_complete.md` ✅
- `prompts/conversation/supplement_prompt.md` ✅
- `prompts/conversation/verification_prompt.md` ✅
- 以及7个stage响应模板

#### 任务2.2：集成置信度调整 ✅
- 验证完成后调用 `result.confidence_adjustment`
- 日志记录置信度变化

### Phase 3: P2优化修复 🟡 进行中

- [x] 统一Prompt管理（loader.py已完成）
- [ ] NLP解析Prompt外部化
- [ ] 理论选择数量配置化
- [ ] 添加仲裁结果UI
- [ ] 实现用户信息编辑

---

## 五、关键文件清单

### 已完成的文件

```
cyber_mantic/
├── services/
│   └── conversation_service.py    # ✅ 已使用load_prompt和FlowGuard
├── prompts/
│   └── loader.py                  # ✅ 模板加载器已创建
├── ui/
│   ├── tabs/
│   │   └── ai_conversation_tab.py # ✅ 已集成VerificationPanel
│   └── widgets/
│       └── verification_widget.py # ✅ 回溯验证组件已创建
└── core/
    └── flow_guard.py              # ✅ 功能完整，测试通过
```

### 模板状态

```
prompts/conversation/
├── welcome.md               ✅ 已更新（与设计文档一致）
├── greeting.md              ✅ 存在且被使用
├── stage1_complete.md       ✅ 已更新（追问具体描述+汉字）
├── stage2_complete.md       ✅ 已更新（追问出生信息）
├── stage3_complete.md       ✅ 存在（旧版补充信息用）
├── stage3_collect_complete.md ✅ 新增（阶段3收集完成）
├── supplement_prompt.md     ✅ 存在
├── verification_prompt.md   ✅ 存在
├── clarification.md         ✅ 存在
└── stage*_response.md       ✅ 7个响应模板已创建
```

---

## 六、错误日志

### 已解决

1. **TypeError: sequence item 0: expected str instance, dict found**
   - 修复完成

2. **UI颜色对比度不足**
   - WAITING/ERROR/NEUTRAL浅色主题文字加深
   - H1标题颜色调整

3. **FlowGuard语法错误 (2026-01-09)**
   - 问题：`"想到的字是"变""` 中文引号嵌套导致SyntaxError
   - 修复：改为 `"想到的字是'变'"`

4. **颜色提取错误 (2026-01-09)**
   - 问题：`"粉红色"` 错误匹配到 `"红"` 而非 `"粉"`
   - 原因：字典遍历顺序导致短词先被匹配
   - 修复：按关键词长度降序匹配，长匹配优先

5. **方位提取错误 (2026-01-09)**
   - 问题：`"西北方向"` 错误匹配到 `"西"` 而非 `"西北"`
   - 修复：复合方位优先检查

6. **Stage1 xiaoliu_result为None (2026-01-09)**
   - 问题：FlowGuard验证成功后仍调用NLP解析，NLP返回error导致提前返回
   - 修复：FlowGuard成功时跳过NLP解析

7. **模板内容与设计文档不匹配 (2026-01-09)**
   - 问题：`welcome.md` 内容是旧版长格式，与 `wendao_flow_design.md` 第58-67行规格不符
   - 原因：模板文件内容从未按照设计文档更新
   - 修复：
     - `welcome.md` → 简洁版（"问道模式" + 类别 + 3个数字）
     - `stage1_complete.md` → 追问"具体描述+汉字"（原错误追问出生信息）
     - `stage2_complete.md` → 追问"出生信息+性别+MBTI"
     - 新增 `stage3_collect_complete.md`

8. **FlowGuard进度显示位置 (2026-01-09)**
   - 问题：进度条在右侧面板底部显示
   - 修复：调整布局顺序，FlowGuard信息收集进度移到最顶端

9. **用户信息编辑功能 (2026-01-09)**
   - 方案：对话指令（方案B）
   - 实现：
     - FlowGuard新增 `detect_modification_intent()` 检测修改意图
     - FlowGuard新增 `process_modification()` 处理修改请求
     - conversation_service 集成修改检测
   - 用法：用户输入"修改出生日期为1990年"即可更新

### 待解决

1. **回溯校验三个问题未显示**
   - 后端有DynamicVerification.generate_verification_questions()
   - 前端只显示一句话提示（已调整prompt让AI生成）

---

## 七、下一步行动

### 已完成 ✅
1. ~~更新三文件~~ ✅
2. ~~创建prompts/loader.py~~ ✅
3. ~~替换conversation_service.py硬编码~~ ✅
4. ~~启用FlowGuard输入验证~~ ✅
5. ~~实现回溯验证UI组件~~ ✅
6. ~~建立自动化测试框架~~ ✅ (29个测试全部通过)

### 下一步（P2优化）
1. **NLP解析Prompt外部化** - 将 `nlp_parser.py` 中的硬编码Prompt移到模板
2. **理论选择数量配置化** - 移除 `max=6, min=3` 硬编码
3. **端到端功能测试** - 手动测试完整问道流程

---

## 八、参考文档

- `docs/v2_frontend_gap_analysis.md` - 详细差异分析报告
- `docs/wendao_notes.md` - 技术笔记
- `docs/wendao_enhancement.md` - 交付物规格
