# 问道界面完善 - 笔记/草稿

> 更新时间：2026-01-08

---

## 一、架构理解

### 问道界面数据流

```
用户输入
    ↓
AIConversationTab (UI层)
    ↓ ConversationWorker (QThread)
    ↓
ConversationService (服务层)
    ├── NLPParser          → 自然语言解析
    ├── TheorySelector     → 理论选择
    ├── 各Theory计算器     → 术数计算
    ├── QAHandler          → 问答处理
    └── ReportGenerator    → 报告生成
    ↓
APIManager (API层)
    ├── Claude API
    ├── Gemini API
    ├── Deepseek API
    └── Kimi API
```

### 5阶段流程详解

| 阶段 | 名称 | 输入 | 输出 | 关键操作 |
|------|------|------|------|----------|
| 1 | 破冰 | 咨询事项+随机数字 | 小六壬初判 | 解析问题类别，起小六壬卦 |
| 2 | 基础信息 | 出生信息 | 可用理论列表 | 解析出生时间，计算理论适配度 |
| 3 | 深度补充 | 补充问题答案 | 推断时辰 | 通过排行/脸型/作息推断时辰 |
| 4 | 结果验证 | 过去事件反馈 | 置信度调整 | 回溯验证，调整理论权重 |
| 5 | 完整报告 | - | 综合分析报告 | 多理论融合，生成报告 |

---

## 二、技术细节记录

### 2.1 selected_theories 数据结构

TheorySelector返回的可能是：
```python
# 字典列表格式
[
    {'theory': '八字', 'score': 0.85, 'reason': '...'},
    {'theory': '奇门遁甲', 'score': 0.75, 'reason': '...'},
    ...
]

# 或字符串列表格式（简化版）
['八字', '奇门遁甲', '六爻', ...]
```

**处理方式**：统一检查类型
```python
if isinstance(theory_item, dict):
    theory_name = theory_item.get('theory', str(theory_item))
else:
    theory_name = str(theory_item)
```

### 2.2 打字机效果实现

**核心类**：`TypewriterAnimation`

**参数**：
- `char_delay`: 每组字符延迟（默认15ms）
- `newline_delay`: 换行额外延迟（默认150ms）
- `chunk_size`: 每次显示字符数（默认3）

**防跳动机制**：
- `set_typing_mode(True)` 开启打字模式
- `_adjust_height_grow_only()` 只增加高度不减少
- 打字完成后 `set_typing_mode(False)` 恢复正常

### 2.3 Worker线程安全

**问题**：多次快速点击发送可能导致多个Worker同时运行

**解决**：
```python
def _stop_current_worker(self):
    if self.worker is not None and self.worker.isRunning():
        self.worker.cancel()
        self.worker.message_received.disconnect()
        self.worker.progress_updated.disconnect()
        self.worker.error.disconnect()
        self.worker.wait(2000)
        self.worker = None
```

### 2.4 API优先级

**修复后的优先级**：
1. 用户在设置中配置的 primary_api
2. API_USAGE_MAP 根据任务类型推荐
3. 第一个可用的API

---

## 三、已修复问题详解

### 3.1 INIT阶段报错

**现象**：第一次对话异常，需要点击"新对话"才正常

**原因**：`process_user_input` 没有处理 INIT 阶段

**修复**：
```python
if stage in (ConversationStage.INIT, ConversationStage.STAGE1_ICEBREAK):
    response = await self._handle_stage1(user_message, progress_callback)
```

### 3.2 用户消息右对齐

**现象**：用户消息没有靠右显示

**原因**：QTextBrowser会覆盖简单的style属性

**修复**：使用完整HTML结构
```python
full_html = f'''
<html>
<head><style>body {{ text-align: right; }}</style></head>
<body><p style="text-align: right; margin: 0; white-space: pre-wrap;">{html_content}</p></body>
</html>
'''
```

---

## 四、待探索方向

### 4.1 可能的优化点

1. **输入交互**
   - 回车键发送（Shift+Enter换行）
   - 输入框自动获取焦点
   - 输入中状态提示

2. **视觉反馈**
   - AI正在思考动画（三个点跳动）
   - 阶段切换过渡动画
   - 进度条颜色渐变

3. **功能增强**
   - 对话中途保存草稿
   - 断点续传（刷新后恢复）
   - 对话分享功能

### 4.2 潜在问题

1. **性能**
   - 长对话内存占用
   - 打字机动画CPU占用

2. **兼容性**
   - 不同API返回格式差异
   - 网络不稳定时的重试

3. **边界情况**
   - 用户输入空消息
   - API超时处理
   - 理论计算异常

---

## 五、参考资料

### 相关代码位置

- 主界面：`cyber_mantic/ui/tabs/ai_conversation_tab.py`
- 聊天组件：`cyber_mantic/ui/widgets/chat_widget.py`
- 对话服务：`cyber_mantic/services/conversation_service.py`
- NLP解析：`cyber_mantic/services/conversation/nlp_parser.py`
- API管理：`cyber_mantic/api/manager.py`

### Prompt模板位置

```
cyber_mantic/prompts/
├── conversation/       # 对话相关
│   ├── greeting.md
│   ├── followup.md
│   └── clarification.md
├── analysis/           # 分析相关
│   ├── comprehensive.md
│   └── ...
└── system/            # 系统提示
    ├── base_persona.md
    └── safety_guidelines.md
```

---

## 六、测试用例

### 正常流程测试

1. 输入：`我想咨询事业，最近想换工作。数字：3、5、7`
2. 输入：`1990年5月20日下午3点出生，男，INTJ`
3. 输入：`（如果需要补充）我是老二，方脸，通常11点睡`
4. 输入：`2023年换了工作，2024年升职了`
5. 验证：生成完整报告，进入QA阶段

### 异常流程测试

1. 空消息发送
2. 格式不正确的输入
3. 中途点击"新对话"
4. 快速连续点击发送
5. API调用失败
