"""
TimelineAnalyzer - 智能时间线分析器

根据用户问题动态生成个性化的时间线，而不是使用固定模板。

核心功能：
1. 从问题中识别时间跨度（今天、今年、这辈子等）
2. 根据时间跨度生成合适的预测时间线
3. 根据问题类型调整时间线粒度
"""

import re
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from utils.logger import get_logger


class TimeSpan:
    """时间跨度枚举"""
    # 短期（天-周）
    TODAY = "today"              # 今天
    THIS_WEEK = "this_week"       # 本周
    THIS_MONTH = "this_month"     # 本月

    # 中短期（月-季度）
    QUARTER = "quarter"           # 3个月/本季度
    HALF_YEAR = "half_year"       # 半年
    THIS_YEAR = "this_year"       # 今年

    # 中期（1-3年）
    NEXT_YEAR = "next_year"       # 明年
    FEW_YEARS = "few_years"       # 2-3年

    # 长期（3-10年）
    FIVE_YEARS = "five_years"     # 5年
    DECADE = "decade"             # 10年

    # 超长期（一生）
    LIFE_LONG = "life_long"       # 一生/这辈子


class TimelineTemplate:
    """时间线模板"""

    def __init__(
        self,
        periods: List[Dict[str, str]],
        description: str
    ):
        """
        初始化时间线模板

        Args:
            periods: 时间段列表，每个包含name和duration
            description: 模板描述
        """
        self.periods = periods
        self.description = description


class TimelineAnalyzer:
    """智能时间线分析器"""

    # 时间关键词映射
    TIME_KEYWORDS = {
        # 短期
        TimeSpan.TODAY: ["今天", "今日", "当天", "今天的"],
        TimeSpan.THIS_WEEK: ["本周", "这周", "这星期", "最近几天"],
        TimeSpan.THIS_MONTH: ["本月", "这个月", "月内"],

        # 中短期
        TimeSpan.QUARTER: ["本季度", "这季度", "最近3个月", "近期"],
        TimeSpan.HALF_YEAR: ["半年", "上半年", "下半年"],
        TimeSpan.THIS_YEAR: ["今年", "本年", "年内", "全年"],

        # 中期
        TimeSpan.NEXT_YEAR: ["明年", "下一年", "来年"],
        TimeSpan.FEW_YEARS: ["几年", "2-3年", "两三年", "未来几年"],

        # 长期
        TimeSpan.FIVE_YEARS: ["5年", "五年", "未来5年"],
        TimeSpan.DECADE: ["10年", "十年", "未来10年"],

        # 超长期
        TimeSpan.LIFE_LONG: ["一生", "这辈子", "此生", "终生", "一世", "整个人生", "人生"]
    }

    # 时间线模板库
    TIMELINE_TEMPLATES = {
        # 超短期：今天/本周
        TimeSpan.TODAY: TimelineTemplate(
            periods=[
                {"name": "上午", "duration": "今天上午（9:00-12:00）"},
                {"name": "下午", "duration": "今天下午（14:00-18:00）"},
                {"name": "晚上", "duration": "今天晚上（19:00-22:00）"}
            ],
            description="日内时段"
        ),

        TimeSpan.THIS_WEEK: TimelineTemplate(
            periods=[
                {"name": "本周前半", "duration": "本周前半（周一至周三）"},
                {"name": "本周后半", "duration": "本周后半（周四至周日）"},
                {"name": "下周", "duration": "下周（7天后）"}
            ],
            description="周内时段"
        ),

        # 短期：本月
        TimeSpan.THIS_MONTH: TimelineTemplate(
            periods=[
                {"name": "本月剩余", "duration": "本月剩余时间"},
                {"name": "下月", "duration": "下个月"},
                {"name": "未来3个月", "duration": "未来3个月"}
            ],
            description="月度时段"
        ),

        # 中短期：季度/半年/今年
        TimeSpan.QUARTER: TimelineTemplate(
            periods=[
                {"name": "近期", "duration": "近期（1-3个月）"},
                {"name": "中期", "duration": "中期（3-6个月）"},
                {"name": "远期", "duration": "远期（6-12个月）"}
            ],
            description="季度时段"
        ),

        TimeSpan.THIS_YEAR: TimelineTemplate(
            periods=[
                {"name": "近1-3个月", "duration": "近1-3个月"},
                {"name": "今年上半年", "duration": "今年剩余上半年时间"},
                {"name": "今年下半年", "duration": "今年下半年"}
            ],
            description="年度时段"
        ),

        # 中期：2-3年
        TimeSpan.FEW_YEARS: TimelineTemplate(
            periods=[
                {"name": "近期", "duration": "近期（1-6个月）"},
                {"name": "中期", "duration": "中期（半年-2年）"},
                {"name": "远期", "duration": "远期（2-3年）"}
            ],
            description="中期时段"
        ),

        # 长期：5年+
        TimeSpan.FIVE_YEARS: TimelineTemplate(
            periods=[
                {"name": "近期", "duration": "近期（1-2年）"},
                {"name": "中期", "duration": "中期（2-4年）"},
                {"name": "长期", "duration": "长期（4-5年）"}
            ],
            description="五年时段"
        ),

        # 超长期：一生
        TimeSpan.LIFE_LONG: TimelineTemplate(
            periods=[
                {"name": "近期", "duration": "近期（1-2年）"},
                {"name": "中期", "duration": "中期（3-5年）"},
                {"name": "长期", "duration": "长期（5-10年）"},
                {"name": "远期", "duration": "远期（10年以后）"}
            ],
            description="人生时段"
        ),
    }

    # 默认时间线（当无法识别时间跨度时）
    DEFAULT_TIMESPAN = TimeSpan.FEW_YEARS

    def __init__(self):
        self.logger = get_logger(__name__)

    def analyze_question_timespan(self, question: str) -> str:
        """
        分析问题的时间跨度

        Args:
            question: 用户问题描述

        Returns:
            时间跨度标识（TimeSpan常量）
        """
        question_lower = question.lower()

        # 按优先级从长到短匹配（避免"今年"匹配到"年"）
        priority_order = [
            TimeSpan.LIFE_LONG,
            TimeSpan.DECADE,
            TimeSpan.FIVE_YEARS,
            TimeSpan.FEW_YEARS,
            TimeSpan.NEXT_YEAR,
            TimeSpan.THIS_YEAR,
            TimeSpan.HALF_YEAR,
            TimeSpan.QUARTER,
            TimeSpan.THIS_MONTH,
            TimeSpan.THIS_WEEK,
            TimeSpan.TODAY,
        ]

        for timespan in priority_order:
            keywords = self.TIME_KEYWORDS.get(timespan, [])
            for keyword in keywords:
                if keyword in question:
                    self.logger.info(f"识别到时间跨度关键词'{keyword}' → {timespan}")
                    return timespan

        # 未识别到关键词，使用默认值
        self.logger.info(f"未识别到明确时间跨度，使用默认值: {self.DEFAULT_TIMESPAN}")
        return self.DEFAULT_TIMESPAN

    def get_timeline_template(self, timespan: str) -> TimelineTemplate:
        """
        获取时间线模板

        Args:
            timespan: 时间跨度标识

        Returns:
            时间线模板
        """
        template = self.TIMELINE_TEMPLATES.get(timespan)

        if not template:
            # 回退到默认模板
            self.logger.warning(f"未找到时间跨度'{timespan}'的模板，使用默认模板")
            template = self.TIMELINE_TEMPLATES[self.DEFAULT_TIMESPAN]

        return template

    def generate_timeline_prompt_section(
        self,
        question: str,
        question_type: str = "综合"
    ) -> str:
        """
        生成时间线prompt片段

        Args:
            question: 用户问题
            question_type: 问题类型

        Returns:
            时间线prompt文本
        """
        # 分析时间跨度
        timespan = self.analyze_question_timespan(question)

        # 获取模板
        template = self.get_timeline_template(timespan)

        # 生成prompt
        prompt = "## 🔮 预测分析（时间线视图）\n\n"

        # 根据时间跨度调整说明
        if timespan in [TimeSpan.TODAY, TimeSpan.THIS_WEEK]:
            prompt += "**时间粒度**：短期分析（天/周）\n\n"
        elif timespan in [TimeSpan.THIS_MONTH, TimeSpan.QUARTER, TimeSpan.THIS_YEAR]:
            prompt += "**时间粒度**：中短期分析（月/季度/年）\n\n"
        elif timespan in [TimeSpan.FEW_YEARS, TimeSpan.FIVE_YEARS]:
            prompt += "**时间粒度**：中长期分析（2-5年）\n\n"
        elif timespan in [TimeSpan.DECADE, TimeSpan.LIFE_LONG]:
            prompt += "**时间粒度**：长期分析（5年+/人生）\n\n"

        # 生成各时间段
        for period in template.periods:
            prompt += f"### {period['name']}\n"
            prompt += f"**时间范围**：{period['duration']}\n\n"
            prompt += f"- **整体趋势**：[描述该时期的总体走势]\n"
            prompt += f"- **关键节点**：[重要时间点或事件]\n"
            prompt += f"- **注意事项**：[需要留意的方面]\n\n"

        # 针对长期问题的特殊说明
        if timespan in [TimeSpan.LIFE_LONG, TimeSpan.DECADE]:
            prompt += """
**长期分析说明**：
- 命理分析侧重于大趋势和关键转折点
- 具体事件受个人选择和外部环境影响
- 建议重点关注"近期"和"中期"的actionable建议
- 长期展望作为方向参考，不宜过分依赖

"""

        return prompt

    def get_timespan_display_name(self, timespan: str) -> str:
        """获取时间跨度的显示名称"""
        display_names = {
            TimeSpan.TODAY: "今日",
            TimeSpan.THIS_WEEK: "本周",
            TimeSpan.THIS_MONTH: "本月",
            TimeSpan.QUARTER: "本季度",
            TimeSpan.HALF_YEAR: "半年",
            TimeSpan.THIS_YEAR: "今年",
            TimeSpan.NEXT_YEAR: "明年",
            TimeSpan.FEW_YEARS: "2-3年",
            TimeSpan.FIVE_YEARS: "5年",
            TimeSpan.DECADE: "10年",
            TimeSpan.LIFE_LONG: "人生长期"
        }
        return display_names.get(timespan, "中期")

    def format_timeline_for_display(
        self,
        question: str,
        analysis_result: str
    ) -> Dict[str, Any]:
        """
        格式化时间线用于显示

        Args:
            question: 用户问题
            analysis_result: AI生成的分析结果

        Returns:
            格式化的时间线数据
        """
        timespan = self.analyze_question_timespan(question)
        template = self.get_timeline_template(timespan)

        return {
            "timespan": timespan,
            "timespan_display": self.get_timespan_display_name(timespan),
            "template_description": template.description,
            "periods": template.periods,
            "analysis": analysis_result
        }


# 便捷函数
def analyze_question_timespan(question: str) -> str:
    """便捷函数：分析问题的时间跨度"""
    analyzer = TimelineAnalyzer()
    return analyzer.analyze_question_timespan(question)


def generate_timeline_prompt(question: str, question_type: str = "综合") -> str:
    """便捷函数：生成时间线prompt"""
    analyzer = TimelineAnalyzer()
    return analyzer.generate_timeline_prompt_section(question, question_type)
