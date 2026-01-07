"""
ReportService - 报告交互服务

提供报告相关的智能功能：
- 术语解释
- 报告问答
- 报告对比
- 格式化和渲染
"""

import re
from typing import Dict, Any, List, Optional, Set
from models import ComprehensiveReport
from core.ai_assistant import AIAssistant
from api.manager import APIManager
from utils.logger import get_logger


class ReportService:
    """报告服务"""

    def __init__(self, api_manager: APIManager):
        self.api_manager = api_manager
        self.ai_assistant = AIAssistant(api_manager)
        self.logger = get_logger(__name__)

    async def explain_term(
        self,
        term: str,
        report_context: Optional[ComprehensiveReport] = None
    ) -> str:
        """
        解释术语

        Args:
            term: 术语（如"用神"、"财星"）
            report_context: 报告上下文（可选，提供更准确的解释）

        Returns:
            术语解释（50-100字）
        """
        context_text = ""
        if report_context:
            context_text = f"报告上下文：{report_context.executive_summary[:200]}"

        return await self.ai_assistant.explain_terminology(term, context_text)

    async def answer_question(
        self,
        question: str,
        report: ComprehensiveReport
    ) -> str:
        """
        回答用户关于报告的问题

        Args:
            question: 用户问题
            report: 报告对象

        Returns:
            AI回答（100-200字）
        """
        return await self.ai_assistant.answer_user_question(question, report)

    async def compare_reports(
        self,
        current_report: ComprehensiveReport,
        previous_report: ComprehensiveReport
    ) -> str:
        """
        对比两份报告

        Args:
            current_report: 当前报告
            previous_report: 历史报告

        Returns:
            对比分析结果（200字）
        """
        return await self.ai_assistant.generate_comparison_insights(
            current_report,
            previous_report
        )

    def extract_terms(self, report_text: str) -> List[Dict[str, Any]]:
        """
        从报告中提取可能需要解释的术语

        Args:
            report_text: 报告文本

        Returns:
            术语列表 [{"term": "用神", "position": 123}, ...]
        """
        # 常见术语词典
        common_terms = {
            # 八字术语
            "用神", "喜神", "忌神", "财星", "官星", "印星", "食伤", "比劫",
            "四柱", "年柱", "月柱", "日柱", "时柱", "天干", "地支",
            "十神", "七杀", "正官", "偏财", "正财", "偏印", "正印",
            "食神", "伤官", "劫财", "比肩",
            "大运", "流年", "小运", "命宫", "胎元",
            "五行", "金", "木", "水", "火", "土",
            "旺相休囚死", "旺", "相", "休", "囚", "死",

            # 奇门术语
            "值符", "值使", "年命", "本命", "时干", "日干",
            "开门", "休门", "生门", "伤门", "杜门", "景门", "死门", "惊门",
            "天蓬", "天任", "天冲", "天辅", "天英", "天芮", "天柱", "天心",
            "直符", "腾蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天",
            "伏吟", "反吟", "击刑", "入墓",

            # 六壬术语
            "三传", "四课", "天将", "贵人", "龙", "青龙", "朱雀", "勾陈",
            "初传", "中传", "末传", "发用", "神将",

            # 六爻术语
            "世爻", "应爻", "用神", "元神", "忌神", "仇神", "原神",
            "动爻", "变爻", "日辰", "月建", "卦身",
            "旬空", "月破", "六兽", "六神",
            "进神", "退神", "伏神", "飞神",

            # 紫微术语
            "命宫", "身宫", "兄弟宫", "夫妻宫", "子女宫",
            "财帛宫", "疾厄宫", "迁移宫", "奴仆宫", "官禄宫",
            "田宅宫", "福德宫", "父母宫",
            "紫微星", "天机星", "太阳星", "武曲星", "天同星",
            "廉贞星", "天府星", "太阴星", "贪狼星", "巨门星",
            "天相星", "天梁星", "七杀星", "破军星",
            "左辅", "右弼", "文昌", "文曲", "禄存",
            "天魁", "天钺", "擎羊", "陀罗", "火星", "铃星",
            "化禄", "化权", "化科", "化忌"
        }

        found_terms = []
        for term in common_terms:
            # 查找术语在文本中的所有位置
            for match in re.finditer(re.escape(term), report_text):
                found_terms.append({
                    "term": term,
                    "position": match.start(),
                    "end_position": match.end()
                })

        # 按位置排序
        found_terms.sort(key=lambda x: x["position"])

        return found_terms

    def format_report_with_term_markers(self, report_text: str) -> str:
        """
        在报告文本中为术语添加标记（用于前端高亮显示）

        Args:
            report_text: 原始报告文本

        Returns:
            带术语标记的文本（Markdown格式）
        """
        terms = self.extract_terms(report_text)

        # 去重：同一个术语只标记第一次出现
        seen_terms = set()
        unique_terms = []
        for term_info in terms:
            if term_info["term"] not in seen_terms:
                unique_terms.append(term_info)
                seen_terms.add(term_info["term"])

        # 从后往前替换，避免位置偏移
        unique_terms.reverse()

        result = report_text
        for term_info in unique_terms:
            term = term_info["term"]
            start = term_info["position"]
            end = term_info["end_position"]

            # 添加标记：使用<span>标签（或自定义标记）
            # 前端可以识别这个标记并添加点击事件
            marked_term = f'<term data-term="{term}">{term}</term>'

            result = result[:start] + marked_term + result[end:]

        return result

    def get_suggested_questions(self, report: ComprehensiveReport) -> List[str]:
        """
        根据报告内容生成建议的提问

        Args:
            report: 报告对象

        Returns:
            建议问题列表（3-5个）
        """
        questions = []

        # 基于问题类型生成
        question_type = report.user_input_summary.get("question_type", "")

        if question_type == "事业发展":
            questions = [
                "为什么说我当前适合/不适合跳槽？",
                "哪个方向的发展机会更好？",
                "大概什么时候会有晋升机会？"
            ]
        elif question_type == "财富运势":
            questions = [
                "为什么说我今年财运好/不好？",
                "哪种投资方式更适合我？",
                "什么时候是投资的好时机？"
            ]
        elif question_type == "感情婚姻":
            questions = [
                "为什么说我与对方合适/不合适？",
                "感情中需要注意什么问题？",
                "什么时候容易遇到合适的人？"
            ]
        else:
            # 通用问题
            questions = [
                "为什么会有这样的结论？",
                "如何化解不利的影响？",
                "具体应该什么时候行动？"
            ]

        # 基于置信度添加问题
        if report.overall_confidence < 0.7:
            questions.append("为什么这次分析的置信度不高？")

        # 基于冲突添加问题
        if report.conflict_info.has_conflict:
            questions.append("为什么不同理论的结论不一致？")

        return questions[:5]  # 返回最多5个

    async def optimize_report_length(
        self,
        report_text: str,
        max_length: int = 2000
    ) -> str:
        """
        优化报告长度

        Args:
            report_text: 原始报告
            max_length: 最大字数

        Returns:
            优化后的报告
        """
        if len(report_text) <= max_length:
            return report_text

        return await self.ai_assistant.optimize_report_for_readability(
            report_text,
            max_length
        )

    def generate_report_summary_for_list(self, report: ComprehensiveReport) -> str:
        """
        生成报告列表显示的摘要（一句话）

        Args:
            report: 报告对象

        Returns:
            摘要文本（30-50字）
        """
        # 提取核心判断
        judgments = [r.judgment for r in report.theory_results]
        favorable_count = sum(1 for j in judgments if j in ["吉", "大吉"])
        unfavorable_count = sum(1 for j in judgments if j in ["凶", "大凶"])

        if favorable_count > unfavorable_count:
            overall = "整体偏吉"
        elif unfavorable_count > favorable_count:
            overall = "整体偏凶"
        else:
            overall = "吉凶参半"

        # 提取关键建议
        advice_preview = ""
        if report.comprehensive_advice:
            first_advice = report.comprehensive_advice[0]
            advice_preview = first_advice.get("content", "")[:20] + "..."

        summary = f"{overall}，{len(report.theory_results)}个理论分析。建议：{advice_preview}"

        return summary[:50]
