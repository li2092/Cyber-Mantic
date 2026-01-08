# 问道界面完善 - 任务规划书

> 更新时间：2026-01-08
> 负责人：Claude + 大魔王
> 状态：进行中

---

## 一、目标

完善"问道"界面的功能和用户体验，确保渐进式5阶段智能交互流程能够稳定运行、用户体验流畅。

---

## 二、当前状态

### 已修复的问题 (2026-01-08)

| 问题 | 位置 | 状态 |
|------|------|------|
| 优先API设置不生效 | `api/manager.py` | ✅ 已修复 |
| INIT阶段报错 | `services/conversation_service.py` | ✅ 已修复 |
| parse_verification_feedback参数缺失 | `services/conversation_service.py` | ✅ 已修复 |
| Worker线程安全控制 | `ui/tabs/ai_conversation_tab.py` | ✅ 已修复 |
| 对话框滚动条问题 | `ui/widgets/chat_widget.py` | ✅ 已修复 |
| 气泡遮挡文字 | `ui/widgets/chat_widget.py` | ✅ 已修复 |
| AI回复打字机效果 | `ui/widgets/chat_widget.py` | ✅ 已修复 |
| 打字效果卡顿 | `ui/widgets/chat_widget.py` | ✅ 已修复 |
| 用户消息右对齐 | `ui/widgets/chat_widget.py` | ✅ 已修复 |
| 右侧面板过宽 | `ui/tabs/ai_conversation_tab.py` | ✅ 已修复 |
| selected_theories字典列表join错误 | `ai_conversation_tab.py` | ✅ 已修复 |
| unhashable type: 'dict' | `conversation_service.py` | ✅ 已修复 |

### 待测试验证

- [ ] 完整5阶段流程跑通
- [ ] 打字机效果平滑度
- [ ] 用户消息右对齐效果
- [ ] 各API接口调用正确性

---

## 三、阶段规划

### 阶段1：稳定性修复 ✅ 完成

- 修复流程中断问题
- 修复UI显示问题
- 添加Worker线程安全控制

### 阶段2：用户体验优化 (当前)

**优先级 P0 - 核心功能**

- [ ] 验证5阶段流程完整运行
- [ ] 确保各阶段过渡平滑
- [ ] 错误提示友好化

**优先级 P1 - 体验提升**

- [ ] 输入框回车发送
- [ ] 加载状态动画优化
- [ ] 进度条更细腻的阶段反馈

**优先级 P2 - 功能增强**

- [ ] 对话保存/导出功能验证
- [ ] 历史对话加载
- [ ] Markdown导出美化

### 阶段3：功能完善 (后续)

- [ ] 理论详情弹窗优化
- [ ] 八字命盘可视化
- [ ] 报告PDF导出
- [ ] 多轮QA持续优化

---

## 四、关键文件清单

### 核心服务层

```
cyber_mantic/services/
├── conversation_service.py         # 对话服务主控
└── conversation/
    ├── context.py                  # 对话上下文
    ├── nlp_parser.py               # NLP解析器
    ├── qa_handler.py               # QA处理器
    └── report_generator.py         # 报告生成器
```

### UI层

```
cyber_mantic/ui/
├── tabs/
│   └── ai_conversation_tab.py      # 问道主界面
└── widgets/
    ├── chat_widget.py              # 聊天组件
    └── progress_widget.py          # 进度组件
```

### API层

```
cyber_mantic/api/
├── manager.py                      # API管理器
└── providers/                      # 各API提供商
```

---

## 五、错误日志

### 已解决

1. **TypeError: sequence item 0: expected str instance, dict found**
   - 原因：`selected_theories`是字典列表，直接join报错
   - 修复：检查类型并提取theory字段

2. **unhashable type: 'dict'**
   - 原因：`_adjust_confidence`用字典作为dict键
   - 修复：从字典中提取theory字段

### 待关注

（待用户测试反馈补充）

---

## 六、下一步行动

1. 等待大魔王测试反馈
2. 根据反馈继续修复问题
3. 逐步推进P1/P2优先级任务

---

## 七、备注

- 遵循"最小信息输入"原则
- 保持打字机效果流畅
- 确保多API故障转移正常
