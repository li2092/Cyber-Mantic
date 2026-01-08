"""
问答处理器模块

处理对话QA阶段的所有问答逻辑：
- 问题类型识别
- 上下文数据准备
- 智能prompt构建
- 降级回答生成
"""

import json
from typing import Dict, Any, Optional, Callable, TYPE_CHECKING
from datetime import datetime

from utils.logger import get_logger

if TYPE_CHECKING:
    from api.manager import APIManager
    from .context import ConversationContext


# 默认问题分类关键词
DEFAULT_QA_KEYWORDS = {
    "bazi_details": ["八字", "四柱", "天干", "地支", "日主", "用神", "大运", "流年", "命盘"],
    "compatibility": ["合婚", "配对", "合不合", "适不适合", "匹配", "缘分", "两个人", "我们俩", "对方", "她/他"],
    "career_choice": ["跳槽", "换工作", "转行", "职业", "工作选择", "选哪个公司", "offer", "晋升", "升职"],
    "health_concern": ["健康", "身体", "病", "疾病", "养生", "保健", "体检", "医院", "治疗"],
    "financial_planning": ["投资", "理财", "股票", "基金", "买房", "置业", "创业", "赚钱", "财富", "收益"],
    "timing_selection": ["择吉", "选日子", "哪天好", "什么时候合适", "吉日", "良辰", "时机", "开业", "搬家", "结婚日期"],
    "education": ["考试", "学业", "学习", "考研", "高考", "公务员", "升学", "留学", "成绩"],
    "relationship_advice": ["感情", "恋爱", "婚姻", "桃花", "脱单", "分手", "复合", "表白", "追求"],
    "personal_growth": ["成长", "提升", "发展", "规划", "目标", "方向", "迷茫", "瓶颈", "突破"],
    "prediction": ["什么时候", "何时", "未来", "今年", "明年", "近期", "会不会", "能不能", "有没有机会"],
    "theory_explanation": ["什么是", "为什么", "怎么理解", "解释", "原理", "依据", "奇门", "六壬", "六爻", "梅花", "紫微"],
    "advice": ["建议", "怎么做", "如何", "应该", "该不该", "要不要", "方法", "指点"],
    "other": ["其他", "别的", "不知道怎么问", "随便问问", "闲聊"]
}

# 问题类型优先级顺序（从具体到通用）
QUESTION_TYPE_PRIORITY = [
    "bazi_details",
    "compatibility",
    "career_choice",
    "health_concern",
    "financial_planning",
    "timing_selection",
    "education",
    "relationship_advice",
    "personal_growth",
    "prediction",
    "theory_explanation",
    "advice",
    "other"
]

# 降级回答模板
FALLBACK_RESPONSES = {
    "bazi_details": """感谢您的提问。关于八字的详细信息，您可以：
1. 查看完整分析报告中的"多理论分析摘要"部分
2. 重新提问，我会尽力为您解答
3. 如需深入了解，建议咨询专业命理师

如有其他问题，欢迎继续提问。""",

    "compatibility": """关于合婚/人际关系的问题，建议您：
1. 查看报告中的五行匹配分析
2. 如需详细合婚分析，请提供对方的出生信息
3. 人际关系中，沟通和理解最重要

最终的相处之道在于双方的包容和努力。""",

    "career_choice": """关于职业选择的问题，建议您：
1. 参考报告中的事业运势分析
2. 结合自身兴趣和实际情况综合考虑
3. 重要决策建议咨询职业规划师

机遇很重要，但更重要的是您的努力和坚持。""",

    "health_concern": """关于健康的问题，建议您：
1. 参考报告中的五行健康分析
2. 注意作息规律和饮食均衡
3. 如有不适，请及时就医检查

命理分析仅供参考，健康问题请遵医嘱。""",

    "financial_planning": """关于理财投资的问题，建议您：
1. 参考报告中的财运分析
2. 理性投资，注意风险控制
3. 重要投资决策建议咨询专业理财顾问

财运有起伏，理性规划最重要。投资需谨慎。""",

    "timing_selection": """关于择吉选日的问题，建议您：
1. 参考报告中的时机分析
2. 选择自己方便的时间也很重要
3. 心诚则灵，保持积极心态

吉日只是锦上添花，关键在于准备充分。""",

    "education": """关于学业考试的问题，建议您：
1. 参考报告中的学业运势分析
2. 保持良好的学习习惯和心态
3. 勤奋努力是成功的关键

运势有助力，但最终靠的是您的付出和坚持。""",

    "relationship_advice": """关于感情的问题，建议您：
1. 参考报告中的桃花运势分析
2. 感情需要用心经营和理解
3. 保持真诚，顺其自然

缘分天注定，但相处靠经营。祝您早日找到幸福。""",

    "personal_growth": """关于个人成长的问题，建议您：
1. 参考报告中的发展方向分析
2. 明确目标，制定可行的计划
3. 持续学习，不断提升自己

每个人都有无限潜力，关键是找对方向并坚持努力。""",

    "advice": """关于您的疑问，建议您：
1. 参考报告中的"行动建议"部分
2. 结合自己的实际情况灵活运用
3. 最终决定权在您手中

如需更具体的建议，请提供更多情境细节，我会尽力帮助您。""",

    "prediction": """关于未来趋势的预测，建议您：
1. 查看报告中的"预测分析"部分
2. 注意关键时间节点
3. 保持积极心态，顺势而为

所有预测仅供参考，最终走向取决于您的选择和努力。""",

    "theory_explanation": """关于术数理论的问题，我建议：
1. 查看报告中使用的理论列表
2. 每种理论都有其独特的分析角度
3. 多理论交叉验证可提高准确度

如需了解具体理论，欢迎继续提问。""",

    "other": """感谢您的提问。关于您的问题，建议：
1. 查看完整分析报告获取全面信息
2. 重新表述问题，我会尽力解答
3. 如有特殊需求，欢迎详细说明

我会尽力为您提供有价值的参考信息。""",

    "general": """非常抱歉，系统繁忙无法立即回答您的问题。建议：
1. 查看完整分析报告
2. 重新表述问题再次提问
3. 如有紧急需求，可咨询专业命理师

感谢您的理解，欢迎继续交流。"""
}


class QAHandler:
    """
    问答处理器

    负责处理对话QA阶段的所有问答逻辑，包括：
    - 问题类型识别
    - 上下文数据准备
    - 智能prompt构建
    - AI调用和降级处理
    """

    def __init__(
        self,
        api_manager: "APIManager",
        context: "ConversationContext",
        qa_keywords: Optional[Dict[str, list]] = None
    ):
        """
        初始化问答处理器

        Args:
            api_manager: API管理器
            context: 对话上下文
            qa_keywords: 问题分类关键词（可选，使用默认值）
        """
        self.api_manager = api_manager
        self.context = context
        self.qa_keywords = qa_keywords or DEFAULT_QA_KEYWORDS
        self.logger = get_logger(__name__)

    async def handle(
        self,
        user_message: str,
        progress_callback: Optional[Callable[[str, str, int], None]] = None
    ) -> str:
        """
        处理问答阶段（增强版）

        智能识别问题类型并提供针对性回答：
        - 询问八字详情 -> 提供完整八字分析数据
        - 询问建议 -> 引用行动建议部分
        - 询问预测 -> 引用预测分析部分
        - 询问理论解释 -> 提供术数知识科普
        - 其他问题 -> 基于完整报告回答

        Args:
            user_message: 用户消息
            progress_callback: 进度回调函数

        Returns:
            AI回答内容
        """
        # 识别问题类型
        question_type = self.identify_question_type(user_message)

        # 准备上下文数据
        context_data = self.prepare_context(question_type)

        # 构建智能prompt
        prompt = self.build_prompt(user_message, question_type, context_data)

        # 调用AI获取回答
        try:
            if progress_callback:
                progress_callback("问答", "正在思考您的问题...", 50)

            answer = await self.api_manager.call_api(
                task_type="快速交互问答",
                prompt=prompt,
                enable_dual_verification=False
            )

            # 保存对话历史
            self.context.conversation_history.append({
                "role": "assistant",
                "content": answer
            })

            self.logger.info(f"QA回答成功，问题类型: {question_type}")
            return answer

        except Exception as e:
            self.logger.error(f"QA回答失败: {e}")
            return self.generate_fallback_response(question_type)

    def identify_question_type(self, user_message: str) -> str:
        """
        识别用户问题类型（配置化版本 - 支持自定义关键词）

        Args:
            user_message: 用户消息

        Returns:
            问题类型：
            - bazi_details: 八字详情查询
            - compatibility: 合婚/人际关系
            - career_choice: 职业选择/转职
            - health_concern: 健康问题
            - financial_planning: 理财投资
            - timing_selection: 择吉/时机选择
            - education: 学业考试
            - relationship_advice: 感情指导
            - personal_growth: 个人成长
            - prediction: 未来预测
            - theory_explanation: 理论解释
            - advice: 一般建议
            - other: 其他类型
            - general: 通用（兜底）
        """
        # 按优先级检查每种问题类型
        for qtype in QUESTION_TYPE_PRIORITY:
            keywords = self.qa_keywords.get(qtype, [])
            if any(kw in user_message for kw in keywords):
                return qtype

        # 默认为一般咨询（如果都不匹配）
        return "general"

    def prepare_context(self, question_type: str) -> Dict[str, Any]:
        """
        根据问题类型准备相关上下文数据

        Args:
            question_type: 问题类型

        Returns:
            上下文数据字典
        """
        context_data: Dict[str, Any] = {}

        if question_type == "bazi_details":
            # 提供完整八字数据
            if self.context.bazi_result:
                context_data["bazi"] = {
                    "四柱": self.context.bazi_result.get("四柱", {}),
                    "五行": self.context.bazi_result.get("五行分析", {}),
                    "十神": self.context.bazi_result.get("十神", {}),
                    "大运": self.context.bazi_result.get("大运", [])[:3],  # 前3步大运
                    "流年": self.context.bazi_result.get("流年分析", {})
                }

            # 其他理论结果
            if self.context.qimen_result:
                context_data["qimen_summary"] = {
                    "值符": self.context.qimen_result.get("值符"),
                    "用神宫位": self.context.qimen_result.get("用神宫位")
                }

        elif question_type == "advice":
            # 提供行动建议
            context_data["actionable_advice"] = self.context.actionable_advice
            context_data["comprehensive_analysis"] = self.context.comprehensive_analysis[:1000]

        elif question_type == "prediction":
            # 提供预测分析
            context_data["predictive_analysis"] = self.context.predictive_analysis
            context_data["retrospective_analysis"] = self.context.retrospective_analysis

        elif question_type == "compatibility":
            # 合婚/人际关系 - 提供命理匹配分析
            context_data["user_bazi"] = {
                "八字": self.context.bazi_result.get("四柱", {}) if self.context.bazi_result else None,
                "五行": self.context.bazi_result.get("五行分析", {}) if self.context.bazi_result else None
            }
            context_data["advice_for_relationship"] = self.context.actionable_advice

        elif question_type == "career_choice":
            # 职业选择 - 提供事业运势分析
            context_data["career_analysis"] = self.context.predictive_analysis
            context_data["professional_advice"] = self.context.actionable_advice
            if self.context.bazi_result:
                context_data["favorable_industries"] = self.context.bazi_result.get("适合行业", [])

        elif question_type == "health_concern":
            # 健康问题 - 提供五行健康分析
            if self.context.bazi_result:
                context_data["wuxing_health"] = self.context.bazi_result.get("五行分析", {})
                context_data["health_advice"] = "基于五行平衡的健康建议"

        elif question_type == "financial_planning":
            # 理财投资 - 提供财运分析
            context_data["wealth_analysis"] = self.context.predictive_analysis
            context_data["financial_advice"] = self.context.actionable_advice
            if self.context.bazi_result:
                context_data["wealth_stars"] = self.context.bazi_result.get("财星", {})

        elif question_type == "timing_selection":
            # 择吉时机 - 提供时间选择建议
            context_data["favorable_times"] = self.context.predictive_analysis
            if self.context.qimen_result:
                context_data["qimen_timing"] = self.context.qimen_result.get("吉时分析", {})

        elif question_type == "education":
            # 学业考试 - 提供学业运势
            context_data["academic_fortune"] = self.context.predictive_analysis
            context_data["study_advice"] = self.context.actionable_advice

        elif question_type == "relationship_advice":
            # 感情指导 - 提供桃花运势
            context_data["love_fortune"] = self.context.predictive_analysis
            if self.context.bazi_result:
                context_data["peach_blossom"] = self.context.bazi_result.get("桃花星", {})

        elif question_type == "personal_growth":
            # 个人成长 - 提供发展方向建议
            context_data["growth_direction"] = self.context.comprehensive_analysis[:800]
            context_data["development_advice"] = self.context.actionable_advice

        elif question_type == "theory_explanation":
            # 提供理论信息
            context_data["selected_theories"] = self.context.selected_theories
            xiaoliu_judgment = None
            if self.context.xiaoliu_result:
                xiaoliu_judgment = self.context.xiaoliu_result.get("judgment", self.context.xiaoliu_result.get("吉凶判断"))
            context_data["theory_results_summary"] = {
                "小六壬": xiaoliu_judgment,
                "八字": "已分析" if self.context.bazi_result else "未分析",
                "奇门": "已分析" if self.context.qimen_result else "未分析",
                "六壬": "已分析" if self.context.liuren_result else "未分析",
                "六爻": "已分析" if self.context.liuyao_result else "未分析",
                "梅花": "已分析" if self.context.meihua_result else "未分析"
            }

        elif question_type == "other":
            # 其他类型 - 提供全面的分析摘要
            context_data["full_analysis"] = self.context.comprehensive_analysis[:1200]
            context_data["general_advice"] = self.context.actionable_advice
            context_data["question_category"] = self.context.question_category

        else:  # general
            # 提供完整报告摘要
            context_data["full_analysis"] = self.context.comprehensive_analysis[:1500]
            context_data["question_info"] = {
                "category": self.context.question_category,
                "description": self.context.question_description
            }

        # 始终包含的通用信息
        context_data["recent_conversation"] = self.context.conversation_history[-5:]

        return context_data

    def build_prompt(
        self,
        user_message: str,
        question_type: str,
        context_data: Dict[str, Any]
    ) -> str:
        """
        根据问题类型构建智能prompt

        Args:
            user_message: 用户问题
            question_type: 问题类型
            context_data: 上下文数据

        Returns:
            构建好的prompt
        """
        current_time = datetime.now().strftime("%Y年%m月%d日 %H:%M")
        base_prompt = f"""你是一位温和专业的命理咨询师。用户刚刚看完分析报告，现在有疑问。

【当前时间】：{current_time}
（注：时间仅供你了解真实时刻，排盘数据已由程序计算完成，请基于已有分析数据回答，不要自行重新排盘）

用户问题：{user_message}

问题类型：{question_type}
"""

        # 根据问题类型添加特定上下文和指令
        prompt = base_prompt + self._build_type_specific_prompt(question_type, context_data)

        prompt += """
重要提示：
- 如果信息不足，诚实说明并建议如何获取更多信息
- 避免过度承诺或绝对化表述
- 保持专业、客观、友善的态度
"""

        return prompt

    def _build_type_specific_prompt(
        self,
        question_type: str,
        context_data: Dict[str, Any]
    ) -> str:
        """根据问题类型构建特定的prompt部分"""

        if question_type == "bazi_details":
            return f"""
相关八字数据：
```json
{json.dumps(context_data.get('bazi', {}), ensure_ascii=False, indent=2)[:800]}
```

其他理论摘要：
{json.dumps(context_data.get('qimen_summary', {}), ensure_ascii=False)}

请详细解释八字相关的内容（200-300字），要求：
1. 用通俗易懂的语言解释专业术数概念
2. 结合具体命盘数据说明
3. 指出对用户的实际影响
4. 温和、专业的语气，使用"您"
"""

        elif question_type == "advice":
            return f"""
行动建议：
{json.dumps(context_data.get('actionable_advice', []), ensure_ascii=False, indent=2)[:500]}

综合分析：
{context_data.get('comprehensive_analysis', '')[:500]}

请基于分析给出具体建议（150-200字），要求：
1. 从行动建议中提炼关键点
2. 提供可操作的具体步骤
3. 强调"最终决定权在您手中"
4. 温和、鼓励的语气
"""

        elif question_type == "prediction":
            return f"""
预测分析：
{context_data.get('predictive_analysis', '（暂无）')}

回溯验证：
{context_data.get('retrospective_analysis', '（暂无）')}

请基于预测数据回答（150-200字），要求：
1. 提供具体时间节点或时间段
2. 说明可能的趋势和影响
3. 给出应对建议
4. 强调"仅供参考"
"""

        elif question_type == "compatibility":
            return f"""
用户命盘信息：
{json.dumps(context_data.get('user_bazi', {}), ensure_ascii=False, indent=2)[:600]}

关系建议：
{json.dumps(context_data.get('advice_for_relationship', []), ensure_ascii=False)[:400]}

请提供合婚/人际关系分析（150-200字），要求：
1. 分析双方五行匹配度
2. 指出相处中可能的问题和优势
3. 给出调和建议
4. 强调"需要对方信息才能更准确分析"
"""

        elif question_type == "career_choice":
            return f"""
事业运势分析：
{context_data.get('career_analysis', '（暂无）')[:500]}

职业建议：
{json.dumps(context_data.get('professional_advice', []), ensure_ascii=False)[:400]}

请提供职业选择建议（150-200字），要求：
1. 分析当前运势适合的发展方向
2. 对比不同选择的利弊
3. 给出具体的决策建议
4. 强调"结合实际情况综合判断"
"""

        elif question_type == "health_concern":
            return f"""
五行健康分析：
{json.dumps(context_data.get('wuxing_health', {}), ensure_ascii=False, indent=2)[:500]}

请提供健康建议（100-150字），要求：
1. 基于五行平衡分析健康弱点
2. 给出养生调理建议
3. 强调"仅供参考，请遵医嘱"
4. 温和、关怀的语气
"""

        elif question_type == "financial_planning":
            return f"""
财运分析：
{context_data.get('wealth_analysis', '（暂无）')[:500]}

理财建议：
{json.dumps(context_data.get('financial_advice', []), ensure_ascii=False)[:400]}

请提供理财投资建议（150-200字），要求：
1. 分析当前财运趋势
2. 给出投资方向建议
3. 提醒风险控制
4. 强调"投资需谨慎，不构成投资建议"
"""

        elif question_type == "timing_selection":
            return f"""
吉时分析：
{context_data.get('favorable_times', '（暂无）')[:500]}

奇门时机：
{json.dumps(context_data.get('qimen_timing', {}), ensure_ascii=False)[:400]}

请提供择吉建议（150-200字），要求：
1. 推荐具体的时间段
2. 说明选择依据
3. 给出替代方案
4. 强调"吉凶参考，心诚则灵"
"""

        elif question_type == "education":
            return f"""
学业运势：
{context_data.get('academic_fortune', '（暂无）')[:500]}

学习建议：
{json.dumps(context_data.get('study_advice', []), ensure_ascii=False)[:400]}

请提供学业建议（150-200字），要求：
1. 分析考试运势
2. 给出学习方法建议
3. 推荐努力方向
4. 鼓励、积极的语气
"""

        elif question_type == "relationship_advice":
            return f"""
感情运势：
{context_data.get('love_fortune', '（暂无）')[:500]}

桃花分析：
{json.dumps(context_data.get('peach_blossom', {}), ensure_ascii=False)[:400]}

请提供感情建议（150-200字），要求：
1. 分析桃花运势
2. 给出脱单/维护感情建议
3. 提醒感情中的注意事项
4. 温暖、理解的语气
"""

        elif question_type == "personal_growth":
            return f"""
发展方向分析：
{context_data.get('growth_direction', '（暂无）')[:600]}

成长建议：
{json.dumps(context_data.get('development_advice', []), ensure_ascii=False)[:400]}

请提供个人成长建议（150-200字），要求：
1. 分析当前瓶颈和机遇
2. 给出突破方向
3. 提供具体行动建议
4. 激励、赋能的语气
"""

        elif question_type == "theory_explanation":
            return f"""
使用的理论：{', '.join(context_data.get('selected_theories', []))}

理论分析状态：
{json.dumps(context_data.get('theory_results_summary', {}), ensure_ascii=False, indent=2)}

请用通俗易懂的语言解释（200-250字），要求：
1. 科普术数理论的基本原理
2. 说明为什么选择这个理论
3. 理论如何应用到具体分析中
4. 避免过于深奥的术语
"""

        elif question_type == "other":
            return f"""
综合分析摘要：
{context_data.get('full_analysis', '（暂无）')[:800]}

一般建议：
{json.dumps(context_data.get('general_advice', []), ensure_ascii=False)[:400]}

问题类别：{context_data.get('question_category')}

请回答用户的问题（150-200字），要求：
1. 基于已有分析回答
2. 如果问题超出范围，诚实说明
3. 温和、友善的语气
4. 提供有价值的参考信息
"""

        else:  # general
            return f"""
完整分析报告（摘要）：
{context_data.get('full_analysis', '（报告未生成）')}

用户问题背景：
- 类别：{context_data.get('question_info', {}).get('category')}
- 描述：{context_data.get('question_info', {}).get('description')}

最近对话：
{json.dumps(context_data.get('recent_conversation', [])[-3:], ensure_ascii=False)}

请回答用户的问题（150-200字），要求：
1. 基于报告内容回答
2. 温和、专业
3. 使用"您"
4. 结合用户的具体情况
"""

    def generate_fallback_response(self, question_type: str) -> str:
        """
        AI调用失败时的降级回答

        Args:
            question_type: 问题类型

        Returns:
            降级回答文本
        """
        return FALLBACK_RESPONSES.get(question_type, FALLBACK_RESPONSES["general"])
