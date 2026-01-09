# 问道界面完善 - 任务规划书

> 更新时间：2026-01-09
> 负责人：Claude + 大魔王
> 状态：🔴 紧急修复中

---

## 一、目标

完善"问道"界面的功能和用户体验，确保V2版本设计的功能真正落地到前端。

**当前紧急问题**：V2后端功能已实现，但前端大量硬编码，未正确集成！

---

## 二、当前状态

### 🔴 紧急问题（2026-01-09发现）

| 问题 | 严重程度 | 状态 |
|------|---------|------|
| 欢迎消息硬编码 | P0 | ❌ 待修复 |
| 阶段提示硬编码 | P0 | ❌ 待修复 |
| 回溯校验UI缺失 | P0 | ❌ 待修复 |
| FlowGuard输入验证未调用 | P0 | ❌ 待修复 |
| prompts/模板未使用 | P0 | ❌ 待修复 |
| 动态验证问题未集成 | P1 | ❌ 待修复 |
| 置信度调整机制未集成 | P1 | ❌ 待修复 |

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

### 3.3 FlowGuard功能未使用

| 功能 | 后端实现 | 前端调用 |
|------|---------|---------|
| 进度显示 | ✅ | ✅ |
| AI增强输入验证 | ✅ | ❌ |
| 阶段跳转防护 | ✅ | ❌ |
| 错误友好提示 | ✅ | ❌ |
| 信息完整性检查 | ✅ | ❌ |

---

## 四、修复计划

### Phase 1: P0紧急修复

**目标**：让V2核心功能真正工作

#### 任务1.1：创建提示词加载器
```
文件：cyber_mantic/prompts/loader.py
功能：统一加载和渲染提示词模板
```

#### 任务1.2：替换硬编码消息
```
修改：conversation_service.py
- 欢迎消息 → load_prompt("conversation/greeting.md")
- 阶段提示 → load_prompt("conversation/stage_*.md")
```

#### 任务1.3：启用FlowGuard验证
```
修改：conversation_service.py
- 在process_user_input()中调用validate_input_with_ai()
- 显示友好的错误提示
```

#### 任务1.4：实现回溯验证UI
```
新增：ui/widgets/verification_widget.py
- 显示动态生成的验证问题
- 收集结构化反馈
- 实时更新置信度
```

### Phase 2: P1重要修复

#### 任务2.1：阶段提示模板化
```
新增模板：
- prompts/conversation/stage1_complete.md
- prompts/conversation/stage2_prompt.md
- prompts/conversation/supplement_prompt.md
- prompts/conversation/verification_prompt.md
```

#### 任务2.2：集成置信度调整
```
修改：ai_conversation_tab.py
- 显示各理论当前置信度
- 验证反馈后实时更新
```

### Phase 3: P2优化修复

- 统一Prompt管理
- 添加仲裁结果UI
- 实现用户信息编辑

---

## 五、关键文件清单

### 需要修改的文件

```
cyber_mantic/
├── services/
│   └── conversation_service.py    # 🔴 替换硬编码，调用FlowGuard
├── prompts/
│   └── loader.py                  # 🆕 新增：模板加载器
├── ui/
│   ├── tabs/
│   │   └── ai_conversation_tab.py # 🟡 添加验证UI调用
│   └── widgets/
│       └── verification_widget.py # 🆕 新增：回溯验证组件
└── core/
    └── flow_guard.py              # ✅ 确认功能完整
```

### 需要补充的模板

```
prompts/conversation/
├── greeting.md          ✅ 存在（需要被使用）
├── stage1_complete.md   🆕 需要创建
├── stage2_prompt.md     🆕 需要创建
├── supplement_prompt.md 🆕 需要创建
├── verification_prompt.md 🆕 需要创建
└── clarification.md     ✅ 存在（需要被使用）
```

---

## 六、错误日志

### 已解决

1. **TypeError: sequence item 0: expected str instance, dict found**
   - 修复完成

2. **UI颜色对比度不足**
   - WAITING/ERROR/NEUTRAL浅色主题文字加深
   - H1标题颜色调整

### 待解决

1. **回溯校验三个问题未显示**
   - 后端有DynamicVerification.generate_verification_questions()
   - 前端只显示一句话提示

2. **FlowGuard验证未生效**
   - 后端有完整的验证逻辑
   - 前端没有调用

---

## 七、下一步行动

1. ~~更新三文件~~ ✅
2. 创建prompts/loader.py
3. 替换conversation_service.py硬编码
4. 启用FlowGuard输入验证
5. 实现回溯验证UI组件
6. 测试完整流程

---

## 八、参考文档

- `docs/v2_frontend_gap_analysis.md` - 详细差异分析报告
- `docs/wendao_notes.md` - 技术笔记
- `docs/wendao_enhancement.md` - 交付物规格
