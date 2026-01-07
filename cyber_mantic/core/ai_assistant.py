"""
AI智能助手 - 后台调用Kimi完成智能任务

核心理念：让AI做AI擅长的事
- 智能摘要生成（而非硬编码提取）
- 报告优化建议
- 用户问题解答
- 术语解释
- 个性化建议
"""
import asyncio
from typing import Dict, Any, List, Optional
from models import ComprehensiveReport, TheoryAnalysisResult
from api.manager import APIManager
from utils.logger import get_logger


# 统一的AI助手系统上下文（与主系统一致的核心原则）
ASSISTANT_SYSTEM_CONTEXT = """
您是赛博玄数系统的智能助手，您的核心原则：

1. **专业而不晦涩**：使用准确术语，同时提供通俗解释
2. **温和而不迎合**：如实告知，避免恐吓或过度承诺
3. **具体而不空泛**：提供可执行的建议，避免空话
4. **留有余地**：使用概率性表达（"大概率""倾向于""较为有利"），避免绝对化
5. **尊重用户**：使用"您"而非"你"，肯定用户的选择权
6. **实用导向**：分析应落地到具体建议，帮助用户做出决策
7. **概率思维**：命理提供的是概率与趋势，而非绝对命定
"""


class AIAssistant:
    """AI智能助手 - 后台调用Kimi处理智能任务"""

    def __init__(self, api_manager: APIManager):
        """
        初始化AI助手

        Args:
            api_manager: API管理器
        """
        self.api_manager = api_manager
        self.logger = get_logger()

    async def generate_executive_summary(
        self,
        full_report: str,
        theory_results: List[TheoryAnalysisResult],
        question_type: str,
        user_mbti: Optional[str] = None
    ) -> str:
        """
        智能生成执行摘要

        不再使用硬编码提取，而是让AI根据完整报告智能总结

        Args:
            full_report: 完整的AI生成报告
            theory_results: 各理论分析结果
            question_type: 问题类型
            user_mbti: 用户MBTI类型（可选）

        Returns:
            智能生成的执行摘要
        """
        self.logger.info("调用AI助手生成执行摘要...")

        # 构建各理论的核心判断摘要
        theory_summary = []
        for result in theory_results:
            theory_summary.append(
                f"- {result.theory_name}: {result.judgment}（置信度{result.confidence:.0%}）"
            )

        theory_summary_text = "\n".join(theory_summary)

        # 构建提示词
        prompt = f"""{ASSISTANT_SYSTEM_CONTEXT}

## 任务：生成执行摘要

您需要为用户的命理分析报告生成一份**精炼的执行摘要**（200-300字）。

### 用户信息
- **问题类型**: {question_type}
- **MBTI类型**: {user_mbti or '未提供'}

### 分析数据
**各理论核心判断**:
{theory_summary_text}

**完整AI分析报告**:
{full_report}

---

### 生成要求

1. **提炼核心结论** - 综合各理论，给出明确的整体判断（吉/凶/平）
2. **突出关键信息** - 抓住最重要的3-5个要点
3. **清晰易懂** - 使用通俗语言，避免术语堆砌
4. **具有指导性** - 给出实用的总体建议
5. **保持客观** - 使用概率性表达，不过度承诺
6. **尊重用户** - 使用"您"而非"你"

### 输出格式
直接输出摘要内容（200-300字），不要标题，不要"执行摘要"这样的前缀。

开始生成：
"""

        try:
            # 使用Kimi生成摘要（快速、成本低）
            summary = await self.api_manager.call_api(
                task_type="快速交互问答",
                prompt=prompt,
                enable_dual_verification=False  # 摘要不需要双模型验证
            )

            self.logger.info(f"执行摘要生成成功，长度：{len(summary)}字")
            return summary.strip()

        except Exception as e:
            self.logger.error(f"执行摘要生成失败: {e}")
            # 降级到原始报告的前300字
            return full_report[:300] + "...\n\n（完整内容请查看详细分析）"

    async def generate_detailed_analysis(
        self,
        report: ComprehensiveReport,
        question_type: str,
        question_description: str,
        user_mbti: Optional[str] = None
    ) -> str:
        """
        生成详细问题解答（报告主要内容）

        这是报告的核心部分，直接基于术数理论结果回答用户的具体问题。

        Args:
            report: 综合报告（包含各理论分析结果）
            question_type: 问题类型
            question_description: 问题描述
            user_mbti: 用户MBTI类型（可选）

        Returns:
            详细问题解答（400-600字）
        """
        self.logger.info(f"生成详细问题解答（问题类型：{question_type}）...")

        # 收集各理论的核心解读
        theory_interpretations = []
        for result in report.theory_results:
            theory_interpretations.append(
                f"### {result.theory_name}\n"
                f"- **判断**: {result.judgment}（{result.judgment_level:.0%}）\n"
                f"- **解读**: {result.interpretation[:200]}...\n"
            )

        theory_text = "\n".join(theory_interpretations)

        # 构建提示词
        prompt = f"""{ASSISTANT_SYSTEM_CONTEXT}

## 任务：生成详细问题解答

您需要基于术数理论的分析结果，**直接回答用户的问题**。这是报告的主要内容，应占据最大篇幅。

### 用户信息
- **问题类型**: {question_type}
- **问题描述**: {question_description}
- **MBTI类型**: {user_mbti or '未提供'}

### 各理论分析结果
{theory_text}

### 冲突信息
{report.conflict_info.to_dict() if report.conflict_info else '无冲突'}

---

### 生成要求

#### 1. 直接回答问题（核心原则）
**必须首先直接回答用户的问题**，而不是泛泛而谈。

**根据问题类型调整回答重点**：

- **姻缘/婚配类问题**（如"我俩配不配"、"合不合"）：
  * 重点分析：双方八字命局的匹配度、五行互补性、性格契合度
  * 给出明确结论：合拍程度如何（非常合适/基本合适/需要磨合/不太合适）
  * 具体说明：哪些方面互补、哪些方面冲突、如何相处更和谐
  * 篇幅：400-500字

- **感情发展类问题**（如"我们感情会如何发展"）：
  * 分析当前感情状态和未来发展趋势
  * 关键时间节点和注意事项
  * 篇幅：400-500字

- **事业/财运类问题**：
  * 分析当前事业/财运状况
  * 即将到来的机遇或挑战
  * 最佳行动时机和策略
  * 篇幅：500-600字

- **健康类问题**：
  * 当前健康状况分析
  * 需要注意的健康隐患
  * 调养方案和预防措施
  * 篇幅：400-500字

- **占卜/择日类问题**：
  * 直接给出吉凶判断
  * 说明吉凶的原因（基于卦象、星象等）
  * 具体时机建议（1-3个月内）
  * 篇幅：300-400字

#### 2. 综合多个理论
- 提取各理论的共识作为主要结论
- 如有冲突，说明不同视角和可能性
- 给出综合后的最终判断和置信度

#### 3. 具体而非空泛
- 避免"会有贵人相助"等空话
- 给出具体特征、方位、时间等信息
- 举例说明如何应对

#### 4. MBTI个性化（如提供）
根据用户MBTI调整语言风格：
- **NT类型**：逻辑化、分析性语言
- **NF类型**：洞察力、温暖的表述
- **SJ类型**：务实、具体的步骤
- **SP类型**：简洁、直接的建议

#### 5. 呈现格式
- 使用Markdown格式
- 用二级/三级标题组织内容
- 用加粗突出关键结论
- 保持段落简洁，每段3-5句话

### 输出要求
直接输出详细分析内容（400-600字），使用Markdown格式，不要添加"# 详细分析"等一级标题。

开始生成：
"""

        try:
            # 使用Claude生成详细分析（高质量、复杂推理）
            detailed_analysis = await self.api_manager.call_api(
                task_type="综合报告解读",
                prompt=prompt,
                enable_dual_verification=False
            )

            self.logger.info(f"详细问题解答生成成功，长度：{len(detailed_analysis)}字")
            return detailed_analysis.strip()

        except Exception as e:
            self.logger.error(f"详细问题解答生成失败: {e}")
            # 降级方案：返回各理论解读的拼接
            fallback = f"## 基于术数理论的分析\n\n"
            for result in report.theory_results:
                fallback += f"### {result.theory_name}\n{result.interpretation}\n\n"
            return fallback

    async def generate_actionable_advice(
        self,
        report: ComprehensiveReport
    ) -> List[Dict[str, str]]:
        """
        智能生成可执行的行动建议

        Args:
            report: 综合报告

        Returns:
            行动建议列表 [{"priority": "高/中/低", "content": "具体建议"}]
        """
        self.logger.info("调用AI助手生成行动建议...")

        # 收集各理论的建议
        theory_advice = []
        for result in report.theory_results:
            if result.advice:
                theory_advice.append(f"- {result.theory_name}: {result.advice}")

        theory_advice_text = "\n".join(theory_advice) if theory_advice else "无"

        prompt = f"""{ASSISTANT_SYSTEM_CONTEXT}

## 任务：生成行动建议

您需要根据命理分析结果，为用户生成**3-5条可执行的行动建议**。

### 用户信息
- **问题类型**: {report.user_input_summary.get('question_type', '未知')}
- **MBTI类型**: {report.user_input_summary.get('mbti_type', '未提供')}

### 分析数据
**各理论建议**:
{theory_advice_text}

**完整报告摘要**:
{report.executive_summary[:500]}

---

### 生成要求

生成3-5条行动建议，每条建议需要：

1. **具体可执行** - 明确的行动步骤，而非抽象概念（如"寻求东南方的人脉资源"而非"会有贵人相助"）
2. **有优先级** - 标注"高"、"中"或"低"（高=立即执行，中=近期完成，低=有条件时考虑）
3. **有时间框架** - 说明具体时间建议（如"本周内""三月木旺之时"）
4. **切实可行** - 避免过于理想化或难以实现的建议
5. **正面积极** - 即使分析结果不佳，也要给出建设性建议和化解方案
6. **尊重用户** - 使用"您"而非"你"，强调"最终决定权在您手中"

### 输出格式

严格按照以下JSON格式输出，不要有任何额外文字：

```json
[
    {{"priority": "高", "content": "立即执行的具体建议..."}},
    {{"priority": "中", "content": "本周内完成的建议..."}},
    {{"priority": "低", "content": "有条件时考虑的建议..."}}
]
```

开始生成：
"""

        try:
            response = await self.api_manager.call_api(
                task_type="快速交互问答",
                prompt=prompt,
                enable_dual_verification=False
            )

            # 尝试解析JSON
            import json
            import re

            # 提取JSON部分（可能包含在```json...```中）
            json_match = re.search(r'```json\s*(\[.*?\])\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 尝试直接解析
                json_str = response.strip()

            advice_list = json.loads(json_str)

            self.logger.info(f"行动建议生成成功，共{len(advice_list)}条")
            return advice_list

        except Exception as e:
            self.logger.error(f"行动建议生成失败: {e}，使用默认建议")
            # 降级到简单建议
            return [
                {"priority": "高", "content": "仔细阅读各理论的详细分析，理解核心要点"},
                {"priority": "中", "content": "结合自身实际情况，制定具体行动计划"},
                {"priority": "低", "content": "定期回顾分析结果，适时调整策略"}
            ]

    async def explain_terminology(
        self,
        term: str,
        context: Optional[str] = None
    ) -> str:
        """
        智能解释术语

        Args:
            term: 术语（如"用神"、"体用"）
            context: 上下文（可选，帮助更准确解释）

        Returns:
            术语解释
        """
        self.logger.info(f"解释术语: {term}")

        context_text = f"\n\n**上下文**：{context}" if context else ""

        prompt = f"""{ASSISTANT_SYSTEM_CONTEXT}

## 任务：解释术语

用户在查看命理分析报告时，遇到了不理解的术语，请用通俗语言为他们解释。

### 需要解释的术语
**{term}**{context_text}

---

### 解释要求
1. **简洁明了** - 50-100字，不要过长
2. **通俗易懂** - 避免使用更多专业术语，用日常语言解释
3. **举例说明** - 最好有具体例子帮助理解
4. **情境适配** - 如果术语有多个含义，说明在此情境下的含义
5. **尊重用户** - 使用"您"而非"你"

### 输出格式
直接输出解释内容，不要标题。

开始解释：
"""

        try:
            explanation = await self.api_manager.call_api(
                task_type="简单问题解答",
                prompt=prompt,
                enable_dual_verification=False
            )

            return explanation.strip()

        except Exception as e:
            self.logger.error(f"术语解释失败: {e}")
            return f"{term}（暂无解释）"

    async def answer_user_question(
        self,
        question: str,
        report_context: ComprehensiveReport
    ) -> str:
        """
        智能回答用户关于报告的问题

        Args:
            question: 用户问题
            report_context: 报告上下文

        Returns:
            AI回答
        """
        self.logger.info(f"回答用户问题: {question}")

        # 构建上下文摘要
        context_summary = f"""
问题类型: {report_context.user_input_summary.get('question_type')}
使用理论: {', '.join(report_context.selected_theories)}
综合置信度: {report_context.overall_confidence:.1%}

执行摘要:
{report_context.executive_summary[:500]}

各理论判断:
"""
        for result in report_context.theory_results:
            context_summary += f"\n- {result.theory_name}: {result.judgment}"

        prompt = f"""{ASSISTANT_SYSTEM_CONTEXT}

## 任务：回答用户问题

用户刚刚看完他们的命理分析报告，现在有一个问题需要您解答。

### 报告背景信息
{context_summary}

### 用户的问题
{question}

---

### 回答要求

请**简洁明了**地回答（100-200字），注意：

1. **基于事实** - 基于报告内容回答，不要编造信息
2. **诚实透明** - 如果问题超出报告范围，诚实说明
3. **友好专业** - 保持温和、专业的语气
4. **引用具体** - 如果需要，可以引用报告中的具体内容
5. **尊重用户** - 使用"您"而非"你"
6. **留有余地** - 使用概率性表达，避免绝对化

### 输出格式
直接输出回答内容，不要标题。

开始回答：
"""

        try:
            answer = await self.api_manager.call_api(
                task_type="快速交互问答",
                prompt=prompt,
                enable_dual_verification=False
            )

            return answer.strip()

        except Exception as e:
            self.logger.error(f"回答用户问题失败: {e}")
            return "抱歉，我暂时无法回答这个问题。请查看详细的分析报告或咨询人工客服。"

    async def optimize_report_for_readability(
        self,
        raw_report: str,
        max_length: int = 2000
    ) -> str:
        """
        优化报告可读性

        如果原始报告过长或格式混乱，让AI重新整理

        Args:
            raw_report: 原始报告
            max_length: 最大长度限制

        Returns:
            优化后的报告
        """
        if len(raw_report) <= max_length:
            return raw_report  # 不需要优化

        self.logger.info(f"报告过长（{len(raw_report)}字），调用AI优化...")

        prompt = f"""{ASSISTANT_SYSTEM_CONTEXT}

## 任务：优化报告可读性

以下是一份命理分析报告，但内容过长（{len(raw_report)}字）。请帮助优化为**{max_length}字以内**，同时保留所有关键信息。

### 原始报告
{raw_report}

---

### 优化要求

1. **保留核心结论** - 不能丢失重要的判断和建议
2. **精简冗余** - 删除重复、啰嗦的部分
3. **改善结构** - 使用Markdown格式，层次分明
4. **突出重点** - 用**加粗**标记关键信息
5. **控制长度** - 严格控制在{max_length}字以内
6. **保持尊重** - 使用"您"而非"你"
7. **保持专业** - 专业而不晦涩，温和而不迎合

### 输出格式
直接输出优化后的报告，使用Markdown格式。

开始优化：
"""

        try:
            optimized = await self.api_manager.call_api(
                task_type="综合报告解读",
                prompt=prompt,
                enable_dual_verification=False
            )

            self.logger.info(f"报告优化完成，从{len(raw_report)}字压缩到{len(optimized)}字")
            return optimized.strip()

        except Exception as e:
            self.logger.error(f"报告优化失败: {e}")
            # 降级到简单截断
            return raw_report[:max_length] + "\n\n（内容过长，已截断。查看详细分析获取完整内容）"

    async def generate_comparison_insights(
        self,
        current_report: ComprehensiveReport,
        previous_report: ComprehensiveReport
    ) -> str:
        """
        生成对比洞察（用于历史报告对比）

        Args:
            current_report: 当前报告
            previous_report: 之前的报告

        Returns:
            对比分析
        """
        self.logger.info("生成报告对比洞察...")

        current_summary = f"""
时间: {current_report.created_at.strftime('%Y-%m-%d')}
问题: {current_report.user_input_summary.get('question_type')}
判断: {self._get_overall_judgment(current_report)}
置信度: {current_report.overall_confidence:.1%}
"""

        previous_summary = f"""
时间: {previous_report.created_at.strftime('%Y-%m-%d')}
问题: {previous_report.user_input_summary.get('question_type')}
判断: {self._get_overall_judgment(previous_report)}
置信度: {previous_report.overall_confidence:.1%}
"""

        prompt = f"""{ASSISTANT_SYSTEM_CONTEXT}

## 任务：生成对比洞察

用户进行了两次命理分析，请对比这两次分析结果，为用户提供**趋势洞察**。

### 第一次分析（早期）
{previous_summary}
摘要: {previous_report.executive_summary[:300]}

### 第二次分析（最近）
{current_summary}
摘要: {current_report.executive_summary[:300]}

---

### 分析要求

请对比分析以下方面（控制在200字以内）：

1. **趋势变化** - 判断整体是变好、变坏还是保持稳定？
2. **关键差异** - 两次分析的主要差异在哪里？
3. **可能原因** - 变化的可能原因是什么？
4. **策略建议** - 用户应该如何调整策略？
5. **尊重用户** - 使用"您"而非"你"
6. **概率表达** - 使用"大概率""倾向于"等表达，避免绝对化

### 输出格式
直接输出对比分析结果（200字以内），不要标题。

开始分析：
"""

        try:
            insights = await self.api_manager.call_api(
                task_type="快速交互问答",
                prompt=prompt,
                enable_dual_verification=False
            )

            return insights.strip()

        except Exception as e:
            self.logger.error(f"对比洞察生成失败: {e}")
            return "对比分析暂不可用"

    async def generate_retrospective_analysis(
        self,
        report: ComprehensiveReport,
        user_birth_info: Optional[Dict[str, Any]] = None,
        question_type: str = "综合运势"
    ) -> str:
        """
        智能生成回顾性分析（过去三年相关或重点事件）

        Args:
            report: 综合报告
            user_birth_info: 用户出生信息（用于计算流年等）
            question_type: 问题类型（用于调整分析侧重点）

        Returns:
            过去三年的回顾分析
        """
        self.logger.info(f"生成过去三年回顾分析（问题类型：{question_type}）...")

        # 动态计算过去三年
        from datetime import datetime
        current_year = datetime.now().year
        past_year_1 = current_year - 3
        past_year_2 = current_year - 2
        past_year_3 = current_year - 1
        past_years = f"{past_year_1}、{past_year_2}、{past_year_3}"
        year_range = f"{past_year_1}-{past_year_3}"

        # 收集各理论的时机分析
        timing_info = []
        for result in report.theory_results:
            if result.timing:
                timing_info.append(f"- {result.theory_name}: {result.timing}")

        timing_text = "\n".join(timing_info) if timing_info else "无"

        prompt = f"""{ASSISTANT_SYSTEM_CONTEXT}

## 任务：生成回顾性分析

基于命理分析结果，为用户生成回顾性分析，帮助用户理解过往经历。

### 用户信息
- **问题类型**: {question_type}
- **出生信息**: {user_birth_info if user_birth_info else '未提供'}

### 分析数据
**各理论时机分析**:
{timing_text}

**综合报告摘要**:
{report.executive_summary[:500]}

---

### 生成要求

**重要**：请根据问题类型调整分析内容和侧重点！

#### 针对不同问题类型的处理：

1. **事业/职业/财运类问题**（200-300字）：
   - 分析过去三年（{past_years}）的职业发展轨迹
   - 重点关注工作变动、晋升、收入变化
   - 按年份分析各时间段的事业运势

2. **学业问题**（200-300字）：
   - 分析过去三年的学习成绩变化
   - 关注考试、升学等关键节点

3. **健康问题**（200-300字）：
   - 回顾过去三年的健康状况变化
   - 关注重大疾病或身体不适时期

4. **婚姻/感情类问题**：
   - **注意**：如果是询问"配不配"、"合不合"等匹配性问题，不要回顾过去三年！
   - 改为分析：两人命局的匹配度、性格互补性（50-100字即可）
   - 只有询问"感情发展如何"才回顾感情经历

5. **测字/择日/占卜类问题**：
   - 不需要回顾，直接说明"此问题侧重当下分析"（一句话即可）

#### 通用要求：
- 使用"大概率""可能""倾向于"等概率性表达
- 使用"您"而非"你"
- 如果问题类型不适合详细回顾，请简短说明即可，不要强行生成内容

### 输出格式
使用Markdown格式，直接输出分析内容。

开始生成：
"""

        try:
            retrospective = await self.api_manager.call_api(
                task_type="综合报告解读",
                prompt=prompt,
                enable_dual_verification=False
            )

            self.logger.info(f"过去三年回顾分析生成成功，长度：{len(retrospective)}字")
            return retrospective.strip()

        except Exception as e:
            self.logger.error(f"过去三年回顾分析生成失败: {e}")
            return "（回顾分析暂不可用）"

    async def generate_predictive_analysis(
        self,
        report: ComprehensiveReport,
        user_birth_info: Optional[Dict[str, Any]] = None,
        question_type: str = "综合运势"
    ) -> str:
        """
        智能生成预测性分析（未来两年趋势）

        Args:
            report: 综合报告
            user_birth_info: 用户出生信息（用于计算流年等）
            question_type: 问题类型（用于调整分析侧重点）

        Returns:
            未来两年的趋势分析
        """
        self.logger.info(f"生成未来两年趋势分析（问题类型：{question_type}）...")

        # 动态计算未来两年
        from datetime import datetime
        current_year = datetime.now().year
        future_year_1 = current_year
        future_year_2 = current_year + 1
        future_years = f"{future_year_1}、{future_year_2}"
        year_range = f"{future_year_1}-{future_year_2}"

        # 收集各理论的时机分析和建议
        timing_info = []
        for result in report.theory_results:
            if result.timing:
                timing_info.append(f"- {result.theory_name}: {result.timing}")

        timing_text = "\n".join(timing_info) if timing_info else "无"

        prompt = f"""{ASSISTANT_SYSTEM_CONTEXT}

## 任务：生成预测性分析

基于命理分析结果，为用户生成预测性分析，帮助用户做好规划。

### 用户信息
- **问题类型**: {question_type}
- **出生信息**: {user_birth_info if user_birth_info else '未提供'}

### 分析数据
**各理论时机分析**:
{timing_text}

**综合报告摘要**:
{report.executive_summary[:500]}

**行动建议**:
{str(report.comprehensive_advice)[:300] if report.comprehensive_advice else '无'}

---

### 生成要求

**重要**：请根据问题类型调整分析内容和侧重点！

#### 针对不同问题类型的处理：

1. **事业/职业/财运类问题**（200-300字）：
   - 分析未来两年（{future_years}）的职业发展趋势
   - 按年份或季度说明运势起伏（上升/平稳/下降）
   - 指出适宜跳槽、创业、投资的时机

2. **学业问题**（200-300字）：
   - 分析未来两年的学习运势
   - 关注重要考试时间和学习状态
   - 提供学习策略和时间规划建议

3. **健康问题**（200-300字）：
   - 预测未来两年的健康状况趋势
   - 指出需要特别注意的时期
   - 提供预防和调养建议

4. **婚姻/感情类问题**：
   - **注意**：如果是询问"配不配"、"合不合"等匹配性问题，不要预测未来两年！
   - 改为给出：相处建议、沟通方式、长期关系维护要点（100-150字即可）
   - 只有询问"感情发展如何"才预测未来趋势

5. **测字/择日/占卜类问题**：
   - 不需要长期预测，给出当下或近期（1-3个月）的建议即可（50-100字）
   - 侧重具体行动时机和注意事项

#### 通用要求：
- 使用"大概率""倾向于""趋势显示"等概率性表达
- 使用"您"而非"你"
- 强调"最终决定权在您手中"
- 如果问题类型不适合长期预测，请简短给出当下建议即可

### 输出格式
使用Markdown格式，直接输出分析内容。

开始生成：
"""

        try:
            predictive = await self.api_manager.call_api(
                task_type="综合报告解读",
                prompt=prompt,
                enable_dual_verification=False
            )

            self.logger.info(f"未来两年趋势分析生成成功，长度：{len(predictive)}字")
            return predictive.strip()

        except Exception as e:
            self.logger.error(f"未来两年趋势分析生成失败: {e}")
            return "（未来趋势分析暂不可用）"

    def _get_overall_judgment(self, report: ComprehensiveReport) -> str:
        """计算综合判断"""
        if not report.theory_results:
            return "未知"

        judgment_values = {"大吉": 1.0, "吉": 0.7, "平": 0.5, "凶": 0.3, "大凶": 0.0}

        total_score = 0
        total_weight = 0

        for result in report.theory_results:
            value = judgment_values.get(result.judgment, 0.5)
            weight = result.confidence
            total_score += value * weight
            total_weight += weight

        if total_weight == 0:
            return "平"

        avg_score = total_score / total_weight

        if avg_score >= 0.85:
            return "大吉"
        elif avg_score >= 0.65:
            return "吉"
        elif avg_score >= 0.35:
            return "平"
        elif avg_score >= 0.15:
            return "凶"
        else:
            return "大凶"
