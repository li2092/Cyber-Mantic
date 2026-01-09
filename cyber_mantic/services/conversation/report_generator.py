"""
报告生成器模块

负责生成最终分析报告：
- 综合分析报告
- 分析数据摘要
- 回溯验证摘要
- 置信度计算
- 简化版报告（降级）
"""

import json
from typing import Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime

from utils.logger import get_logger
from core.timeline_analyzer import TimelineAnalyzer

if TYPE_CHECKING:
    from api.manager import APIManager
    from .context import ConversationContext


# 时辰中文名称映射
HOUR_CHINESE_NAMES = {
    0: "子", 1: "丑", 2: "丑", 3: "寅", 4: "寅", 5: "卯",
    6: "卯", 7: "辰", 8: "辰", 9: "巳", 10: "巳", 11: "午",
    12: "午", 13: "未", 14: "未", 15: "申", 16: "申", 17: "酉",
    18: "酉", 19: "戌", 20: "戌", 21: "亥", 22: "亥", 23: "子"
}


class ReportGenerator:
    """
    报告生成器

    负责生成最终分析报告，包括：
    - 调用AI生成综合报告
    - 准备各理论分析摘要
    - 计算综合置信度
    - 降级报告生成
    """

    def __init__(
        self,
        api_manager: "APIManager",
        context: "ConversationContext"
    ):
        """
        初始化报告生成器

        Args:
            api_manager: API管理器
            context: 对话上下文
        """
        self.api_manager = api_manager
        self.context = context
        self.logger = get_logger(__name__)
        self.timeline_analyzer = TimelineAnalyzer()  # 初始化时间线分析器

    async def generate_final_report(self) -> str:
        """
        生成最终详细报告（使用AI综合分析）

        Returns:
            完整的分析报告文本
        """
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        current_time_display = datetime.now().strftime("%Y年%m月%d日 %H:%M")

        # 准备分析数据摘要
        analysis_summary = self.prepare_analysis_summary()

        # 准备回溯验证摘要
        verification_summary = self.prepare_verification_summary()

        # 调用AI生成综合报告
        prompt = self._build_report_prompt(
            current_time_display,
            analysis_summary,
            verification_summary
        )

        try:
            response = await self.api_manager.call_api(
                task_type="综合报告解读",  # 使用Claude进行深度分析
                prompt=prompt,
                enable_dual_verification=False
            )

            # 保存综合分析
            self.context.comprehensive_analysis = response

            # 构建完整报告
            report_header = f"""# 🔮 赛博玄数 - 智能分析报告

## 📋 基本信息

- **分析时间**：{current_time}
- **所问事项**：{self.context.question_category} - {self.context.question_description}
- **使用理论**：{', '.join([t.get('theory', str(t)) if isinstance(t, dict) else str(t) for t in self.context.selected_theories])}
- **综合置信度**：{self.calculate_overall_confidence()}%

---

"""

            full_report = report_header + response

            return full_report.strip()

        except Exception as e:
            self.logger.error(f"生成最终报告失败: {e}")
            # 返回简化版报告
            return self.generate_simplified_report()

    # MBTI表达风格指导
    MBTI_EXPRESSION_STYLES = {
        # 分析型（NT）- 重逻辑，喜欢数据和原理
        "INTJ": {"风格": "逻辑严密、数据导向", "偏好": "系统分析、长期规划", "表达": "直接简洁，重点突出因果关系"},
        "INTP": {"风格": "理论深入、探索原理", "偏好": "原理解释、多角度分析", "表达": "可以展开理论推导，但避免空泛"},
        "ENTJ": {"风格": "结果导向、决策明确", "偏好": "行动建议、效率优先", "表达": "强调可执行性和预期收益"},
        "ENTP": {"风格": "灵活多变、可能性导向", "偏好": "多种方案、创意建议", "表达": "可以探讨多种可能，但需有主次"},

        # 外交型（NF）- 重感受，关注意义和人文
        "INFJ": {"风格": "直觉深刻、意义导向", "偏好": "深层含义、人生意义", "表达": "融入哲理思考，关注内心成长"},
        "INFP": {"风格": "感性细腻、价值导向", "偏好": "情感共鸣、个人价值", "表达": "温和包容，关注内心感受"},
        "ENFJ": {"风格": "温暖鼓励、关系导向", "偏好": "人际影响、助人建议", "表达": "积极正面，关注对他人的影响"},
        "ENFP": {"风格": "热情开放、可能性导向", "偏好": "灵感启发、成长机会", "表达": "充满热情，探索成长空间"},

        # 守护型（SJ）- 重传统，喜欢具体和可靠
        "ISTJ": {"风格": "务实稳健、事实导向", "偏好": "具体步骤、可靠方法", "表达": "条理清晰，提供明确指引"},
        "ISFJ": {"风格": "细心周到、责任导向", "偏好": "安全建议、风险提示", "表达": "温和稳重，关注安全感"},
        "ESTJ": {"风格": "效率务实、行动导向", "偏好": "明确计划、时间节点", "表达": "简洁有力，强调行动步骤"},
        "ESFJ": {"风格": "关怀实际、和谐导向", "偏好": "人际建议、情感支持", "表达": "温暖亲切，关注人际关系"},

        # 探险型（SP）- 重体验，喜欢灵活和当下
        "ISTP": {"风格": "冷静分析、实用导向", "偏好": "技术分析、实操建议", "表达": "简洁实用，直指要点"},
        "ISFP": {"风格": "感性直觉、体验导向", "偏好": "感受分享、灵活建议", "表达": "温和自然，尊重个人感受"},
        "ESTP": {"风格": "直接果断、行动导向", "偏好": "快速建议、即时效果", "表达": "简短有力，强调立即行动"},
        "ESFP": {"风格": "乐观积极、体验导向", "偏好": "有趣建议、正面反馈", "表达": "活泼积极，强调享受过程"},
    }

    def _build_report_prompt(
        self,
        current_time_display: str,
        analysis_summary: str,
        verification_summary: str
    ) -> str:
        """构建报告生成的AI prompt"""
        # 获取MBTI个性化指导
        mbti_style = self._get_mbti_style_guidance()

        # 动态生成时间线prompt（根据用户问题）
        timeline_prompt = self.timeline_analyzer.generate_timeline_prompt_section(
            question=self.context.question_description,
            question_type=self.context.question_category
        )

        return f"""你是一位经验丰富的命理分析师。请基于以下信息，生成一份专业的命理分析报告。

【当前时间】：{current_time_display}
（注：时间仅供你了解真实时刻，所有排盘数据已由程序计算完成，请直接分析下方数据，不要自行重新排盘）

## 用户信息
- **问题类别**：{self.context.question_category}
- **问题描述**：{self.context.question_description}
- **出生年份**：{self.context.birth_info.get('year') if self.context.birth_info else '未知'}年
- **性别**：{self.context.gender or '未知'}
- **MBTI**：{self.context.mbti_type or '未知'}

## 🎯 MBTI个性化表达指导
{mbti_style}

## 使用理论
{', '.join([t.get('theory', str(t)) if isinstance(t, dict) else str(t) for t in self.context.selected_theories])}

## 分析数据摘要
{analysis_summary}

## 回溯验证结果
{verification_summary}

---

请生成以下格式的详细报告（严格遵循markdown格式）：

## 🎯 核心结论（3句话版）

> 1. **总体判断**：[一句话总结当前状态和总体趋势，50字以内]
> 2. **关键时机**：[指出最佳时间窗口或需要注意的时间节点，50字以内]
> 3. **首要建议**：[最核心的一条行动建议，50字以内]

## 📊 多理论分析摘要

[针对每个使用的理论，分别说明核心结论和关键发现，每个理论100-150字]

{timeline_prompt}

## 🧭 行动建议

### 🔥 高优先级（立即行动）
1. **[领域]**：[具体建议，包括时间、方式、预期效果]
2. **[领域]**：[具体建议]

### 📌 中优先级（近期考虑）
1. **[领域]**：[具体建议]
2. **[领域]**：[具体建议]

### 💡 MBTI人格适配建议
[根据用户的MBTI类型，给出个性化的沟通方式、决策建议、注意事项]

---

**重要说明**：
1. 所有预测仅供参考，最终决定权在您手中
2. 命理分析是一种思维工具，帮助您更好地认识自己
3. 建议结合实际情况灵活运用

💬 **如有疑问，欢迎继续提问！**
"""

    def prepare_analysis_summary(self) -> str:
        """
        准备分析数据摘要

        Returns:
            分析摘要文本
        """
        summary = ""

        # 小六壬结果
        if self.context.xiaoliu_result:
            xiaoliu_summary = f"""
**小六壬快判**：
- 吉凶：{self.context.xiaoliu_result.get('吉凶判断', '未知')}
- 时落宫：{self.context.xiaoliu_result.get('时落宫', '未知')}
"""
            summary += xiaoliu_summary

        # 八字结果
        if self.context.bazi_result:
            # 四柱是列表格式，使用单独的年柱/月柱/日柱/时柱字典
            year_pillar = self.context.bazi_result.get('年柱', {}) or {}
            month_pillar = self.context.bazi_result.get('月柱', {}) or {}
            day_pillar = self.context.bazi_result.get('日柱', {}) or {}
            hour_pillar = self.context.bazi_result.get('时柱', {}) or {}
            bazi_summary = f"""
**八字命盘**：
- 年柱：{year_pillar.get('天干', '')}{year_pillar.get('地支', '')}
- 月柱：{month_pillar.get('天干', '')}{month_pillar.get('地支', '')}
- 日柱：{day_pillar.get('天干', '')}{day_pillar.get('地支', '')}
- 时柱：{hour_pillar.get('天干', '')}{hour_pillar.get('地支', '')}
- 日主：{self.context.bazi_result.get('日主', '未知')}
"""
            summary += bazi_summary

        # 奇门遁甲结果
        if self.context.qimen_result:
            qimen_summary = f"""
**奇门遁甲**：
- 值符：{self.context.qimen_result.get('值符', '未知')}
- 用神宫位：{self.context.qimen_result.get('用神宫位', '未知')}
- 格局：{self.context.qimen_result.get('格局', '未知')}
"""
            summary += qimen_summary

        # 大六壬结果
        if self.context.liuren_result:
            liuren_summary = f"""
**大六壬**：
- 课体：{self.context.liuren_result.get('课体', '未知')}
- 三传：{self.context.liuren_result.get('三传', '未知')}
- 吉凶：{self.context.liuren_result.get('吉凶', '未知')}
"""
            summary += liuren_summary

        # 六爻结果
        if self.context.liuyao_result:
            ben_gua = self.context.liuyao_result.get('本卦', {})
            bian_gua = self.context.liuyao_result.get('变卦')
            liuyao_summary = f"""
**六爻**：
- 本卦：{ben_gua.get('卦名', '未知') if isinstance(ben_gua, dict) else '未知'}
- 变卦：{bian_gua.get('卦名', '未知') if isinstance(bian_gua, dict) and bian_gua else '无'}
- 用神：{self.context.liuyao_result.get('用神', '未知')}
"""
            summary += liuyao_summary

        # 梅花易数结果
        if self.context.meihua_result:
            meihua_summary = f"""
**梅花易数**：
- 主卦：{self.context.meihua_result.get('主卦', {}).get('卦名', '未知')}
- 变卦：{self.context.meihua_result.get('变卦', {}).get('卦名', '未知')}
- 互卦：{self.context.meihua_result.get('互卦', {}).get('卦名', '未知')}
"""
            summary += meihua_summary

        # 时辰推断信息
        if self.context.time_certainty == "inferred":
            hour_name = self._hour_to_chinese(self.context.inferred_hour)
            summary += f"\n**时辰推断**：根据补充信息推断为{hour_name}时（置信度70%）\n"

        return summary if summary else "（无详细分析数据）"

    def prepare_verification_summary(self) -> str:
        """
        准备回溯验证摘要

        Returns:
            验证摘要文本
        """
        if not self.context.verification_feedback:
            return "（用户未提供回溯验证反馈）"

        latest_feedback = self.context.verification_feedback[-1]
        parsed = latest_feedback.get("parsed_feedback", {})

        match_count = parsed.get("match_count", 0)
        total_count = parsed.get("total_count", 0)

        if total_count > 0:
            accuracy = (match_count / total_count) * 100
            return f"""
**回溯验证准确率**：{accuracy:.0f}% ({match_count}/{total_count}个事件符合)

验证详情：
{json.dumps(parsed.get('matches', []), ensure_ascii=False, indent=2)[:300]}
"""
        else:
            return "（无回溯验证数据）"

    def calculate_overall_confidence(self) -> int:
        """
        计算综合置信度

        Returns:
            置信度百分比 (0-100)
        """
        base_confidence = 75  # 基础置信度

        # 根据理论数量调整
        theory_count = len(self.context.selected_theories)
        if theory_count >= 3:
            base_confidence += 10
        elif theory_count >= 2:
            base_confidence += 5

        # 根据回溯验证调整
        if self.context.verification_feedback:
            latest_feedback = self.context.verification_feedback[-1]
            parsed = latest_feedback.get("parsed_feedback", {})
            match_count = parsed.get("match_count", 0)
            total_count = parsed.get("total_count", 1)
            accuracy = match_count / total_count

            if accuracy >= 0.8:
                base_confidence += 10
            elif accuracy >= 0.5:
                base_confidence += 5
            else:
                base_confidence -= 10

        # 根据时辰确定性调整
        if self.context.time_certainty == "certain":
            base_confidence += 5
        elif self.context.time_certainty == "inferred":
            base_confidence -= 5

        # 限制在0-100范围内
        return max(0, min(100, base_confidence))

    def generate_simplified_report(self) -> str:
        """
        生成简化版报告（AI调用失败时使用）

        Returns:
            简化版报告文本
        """
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

        return f"""# 🔮 赛博玄数 - 智能分析报告

## 📋 基本信息

- **分析时间**：{current_time}
- **所问事项**：{self.context.question_category} - {self.context.question_description}
- **使用理论**：{', '.join([t.get('theory', str(t)) if isinstance(t, dict) else str(t) for t in self.context.selected_theories])}
- **综合置信度**：{self.calculate_overall_confidence()}%

---

## 🎯 核心结论

基于{', '.join([t.get('theory', str(t)) if isinstance(t, dict) else str(t) for t in self.context.selected_theories])}的综合分析，我们为您提供了以下参考建议。

## 📊 分析摘要

{self.prepare_analysis_summary()}

## ⏪ 回溯验证

{self.prepare_verification_summary()}

---

💬 **如有疑问，欢迎继续提问！我会为您详细解答。**

**注意**：由于系统繁忙，详细报告生成失败。您可以针对具体问题继续提问，我会为您详细解答。
"""

    def _hour_to_chinese(self, hour: Optional[int]) -> str:
        """
        将小时转换为中文时辰名

        Args:
            hour: 小时数 (0-23)

        Returns:
            中文时辰名
        """
        if hour is None:
            return "未知"
        return HOUR_CHINESE_NAMES.get(hour, "未知")

    def _get_mbti_style_guidance(self) -> str:
        """
        获取MBTI个性化表达指导

        Returns:
            表达风格指导文本
        """
        mbti_type = self.context.mbti_type
        if not mbti_type:
            return "用户未提供MBTI，使用标准表达风格，语气专业中性。"

        mbti_type = mbti_type.upper()
        style_info = self.MBTI_EXPRESSION_STYLES.get(mbti_type)

        if not style_info:
            return f"用户MBTI类型（{mbti_type}）未知，使用标准表达风格。"

        return f"""用户是**{mbti_type}**类型，请按以下风格调整报告表达：
- **沟通风格**：{style_info['风格']}
- **内容偏好**：{style_info['偏好']}
- **表达方式**：{style_info['表达']}

**重要**：请根据以上MBTI特点调整报告的语气、内容侧重点和建议方式，使报告更贴合用户的认知偏好。"""


class ConversationExporter:
    """
    对话导出器

    负责将对话内容导出为各种格式
    """

    def __init__(self, context: "ConversationContext"):
        """
        初始化导出器

        Args:
            context: 对话上下文
        """
        self.context = context

    def export_to_markdown(self) -> str:
        """
        将对话导出为Markdown格式

        Returns:
            Markdown格式的对话内容
        """
        md_content = f"""# 赛博玄数 - 对话记录

**导出时间**：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**对话阶段**：{self.context.stage.value}

---

## 📋 基本信息

**问题类别**：{self.context.question_category or '未填写'}
**问题描述**：{self.context.question_description or '未填写'}

**出生信息**：
"""

        if self.context.birth_info:
            birth = self.context.birth_info
            md_content += f"""- 年份：{birth.get('year')}年
- 月份：{birth.get('month')}月
- 日期：{birth.get('day')}日
- 时辰：{birth.get('hour', '未知')}时
- 历法：{'农历' if birth.get('calendar_type') == 'lunar' else '阳历'}
- 时辰确定性：{self.context.time_certainty}
"""
        else:
            md_content += "- 未填写\n"

        md_content += f"""
**其他信息**：
- 性别：{self.context.gender or '未填写'}
- MBTI：{self.context.mbti_type or '未填写'}

---

## 🔮 分析概况

**使用理论**：{', '.join([t.get('theory', str(t)) if isinstance(t, dict) else str(t) for t in self.context.selected_theories]) if self.context.selected_theories else '未选择'}

**分析状态**：
- 小六壬：{'✓ 已分析' if self.context.xiaoliu_result else '✗ 未分析'}
- 八字：{'✓ 已分析' if self.context.bazi_result else '✗ 未分析'}
- 奇门遁甲：{'✓ 已分析' if self.context.qimen_result else '✗ 未分析'}
- 大六壬：{'✓ 已分析' if self.context.liuren_result else '✗ 未分析'}
- 六爻：{'✓ 已分析' if self.context.liuyao_result else '✗ 未分析'}
- 梅花易数：{'✓ 已分析' if self.context.meihua_result else '✗ 未分析'}

---

## 💬 对话历史

"""

        # 添加对话历史
        for msg in self.context.conversation_history:
            role = "👤 **用户**" if msg.get("role") == "user" else "🤖 **助手**"
            content = msg.get("content", "")
            md_content += f"{role}：\n\n{content}\n\n---\n\n"

        if self.context.comprehensive_analysis:
            md_content += f"""## 📊 综合分析报告

{self.context.comprehensive_analysis}

---
"""

        md_content += """
*本报告由赛博玄数AI系统生成，仅供参考*
"""

        return md_content

    def to_save_dict(self) -> Dict[str, Any]:
        """
        生成用于保存的字典

        Returns:
            包含完整对话数据的字典
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "session_id": id(self.context),
            "context": self.context.to_dict(),
            "full_conversation": self.context.conversation_history,
            "summary": self.get_summary(),
            "statistics": self.get_statistics()
        }

    def get_summary(self) -> Dict[str, Any]:
        """
        生成对话摘要

        Returns:
            对话摘要字典
        """
        return {
            "stage": self.context.stage.value,
            "question": {
                "category": self.context.question_category,
                "description": self.context.question_description[:100] + "..."
                if len(self.context.question_description) > 100
                else self.context.question_description
            },
            "user_info": {
                "birth_year": self.context.birth_info.get("year") if self.context.birth_info else None,
                "gender": self.context.gender,
                "mbti": self.context.mbti_type,
                "time_certainty": self.context.time_certainty
            },
            "analysis_status": {
                "theories_used": self.context.selected_theories,
                "bazi_analyzed": self.context.bazi_result is not None,
                "qimen_analyzed": self.context.qimen_result is not None,
                "liuren_analyzed": self.context.liuren_result is not None,
                "report_generated": bool(self.context.comprehensive_analysis)
            },
            "verification": {
                "retrospective_events_count": len(self.context.retrospective_events),
                "feedback_provided": len(self.context.verification_feedback) > 0,
                "confidence_adjusted": bool(self.context.theory_confidence_adjustment)
            }
        }

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取对话统计信息

        Returns:
            统计信息字典
        """
        return {
            "total_messages": len(self.context.conversation_history),
            "user_messages": len([m for m in self.context.conversation_history if m.get("role") == "user"]),
            "assistant_messages": len([m for m in self.context.conversation_history if m.get("role") == "assistant"]),
            "theories_count": len(self.context.selected_theories),
            "has_xiaoliu": self.context.xiaoliu_result is not None,
            "has_bazi": self.context.bazi_result is not None,
            "has_report": bool(self.context.comprehensive_analysis)
        }
