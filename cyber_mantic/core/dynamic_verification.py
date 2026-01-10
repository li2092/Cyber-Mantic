"""
DynamicVerificationGenerator - 动态回溯验证问题生成器

V2核心功能：基于用户信息和分析结果，AI生成3个针对性验证问题
用于验证理论分析的准确性，提高用户信任度

策略：
1. 基于用户年龄计算关键年份（婚姻、事业转折等）
2. 基于问题类别选择相关领域
3. 基于理论预测的"应验年"生成验证
"""

import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from utils.logger import get_logger
from api.prompt_loader import load_prompt


class VerificationQuestion:
    """验证问题数据类"""

    def __init__(
        self,
        question: str,
        question_type: str,
        purpose: str,
        expected_answers: Optional[List[str]] = None,
        weight: float = 1.0
    ):
        """
        初始化验证问题

        Args:
            question: 问题文本
            question_type: 问题类型 (yes_no/year/event/choice)
            purpose: 问题目的（用于验证哪个预测）
            expected_answers: 预期答案列表（用于计算匹配度）
            weight: 权重（影响置信度调整幅度）
        """
        self.question = question
        self.question_type = question_type
        self.purpose = purpose
        self.expected_answers = expected_answers or []
        self.weight = weight
        self.user_answer = None
        self.is_verified = None  # True=验证通过, False=验证失败, None=未回答

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "question": self.question,
            "type": self.question_type,
            "purpose": self.purpose,
            "expected_answers": self.expected_answers,
            "weight": self.weight,
            "user_answer": self.user_answer,
            "is_verified": self.is_verified
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VerificationQuestion":
        """从字典创建"""
        q = cls(
            question=data.get("question", ""),
            question_type=data.get("type", "yes_no"),
            purpose=data.get("purpose", ""),
            expected_answers=data.get("expected_answers", []),
            weight=data.get("weight", 1.0)
        )
        q.user_answer = data.get("user_answer")
        q.is_verified = data.get("is_verified")
        return q


class VerificationResult:
    """验证结果"""

    def __init__(self, questions: List[VerificationQuestion]):
        self.questions = questions
        self.answered_count = 0
        self.verified_count = 0
        self.confidence_adjustment = 0.0

    def update_answer(self, index: int, answer: str, is_verified: bool):
        """更新某个问题的答案"""
        if 0 <= index < len(self.questions):
            q = self.questions[index]
            q.user_answer = answer
            q.is_verified = is_verified
            self._recalculate()

    def _recalculate(self):
        """重新计算统计数据"""
        self.answered_count = sum(1 for q in self.questions if q.user_answer is not None)
        self.verified_count = sum(1 for q in self.questions if q.is_verified is True)

        # 计算置信度调整
        if self.answered_count > 0:
            total_weight = sum(q.weight for q in self.questions if q.user_answer is not None)
            verified_weight = sum(q.weight for q in self.questions if q.is_verified is True)
            failed_weight = sum(q.weight for q in self.questions if q.is_verified is False)

            # 验证通过增加置信度，验证失败减少置信度
            if total_weight > 0:
                self.confidence_adjustment = (verified_weight - failed_weight * 0.5) / total_weight * 0.15

    def get_summary(self) -> Dict[str, Any]:
        """获取验证摘要"""
        return {
            "total_questions": len(self.questions),
            "answered_count": self.answered_count,
            "verified_count": self.verified_count,
            "accuracy_rate": self.verified_count / self.answered_count if self.answered_count > 0 else 0,
            "confidence_adjustment": self.confidence_adjustment
        }


class DynamicVerificationGenerator:
    """动态生成验证问题"""

    # 问题类型模板（三选项格式 - 备用方案）
    QUESTION_TEMPLATES = {
        "事业": [
            ("2023年下半年（7-12月），工作上是否经历过明显的挫折或不顺利？", "验证事业运势"),
            ("2024年上半年（1-6月），是否有过跳槽、换岗位或工作内容调整的情况？", "验证事业变动"),
            ("2022-2023年间，是否遇到过对工作有重要帮助的贵人（领导/同事/合作伙伴）？", "验证贵人运")
        ],
        "感情": [
            ("2023年全年，感情关系是否出现过争吵、冷战或短暂分离？", "验证感情波折"),
            ("2024年春季（3-5月），是否有过新的感情机会或桃花出现？", "验证桃花运"),
            ("2022-2023年间，感情状态是否经历过从单身到恋爱、或从恋爱到分手的转变？", "验证感情变化")
        ],
        "财运": [
            ("2023年，是否有过意外的财务支出或投资亏损？", "验证财运波折"),
            ("2024年上半年，是否有过额外收入或意外之财（奖金/项目分红/理财收益）？", "验证财运机会"),
            ("2022-2023年间，收入是否有明显增长（涨薪/换高薪工作/副业收入）？", "验证收入增长")
        ],
        "健康": [
            ("2023年，是否经历过身体不适、生病或体检指标异常？", "验证健康状况"),
            ("2024年，是否开始了新的健康习惯（运动/饮食调整/作息改善）？", "验证健康意识"),
            ("2022-2023年间，家人是否有过健康问题需要照顾？", "验证家人健康")
        ],
        "决策": [
            ("2023年，是否做过重要的人生决策（换工作/搬家/重大投资）？", "验证决策时机"),
            ("您2023年做出的重要决策，事后来看是否符合预期？", "验证决策结果"),
            ("2024年上半年，是否因为犹豫不决而错过某个机会？", "验证决策果断度")
        ]
    }

    def __init__(self, api_manager=None):
        """
        初始化验证问题生成器

        Args:
            api_manager: API管理器实例（用于调用AI生成问题）
        """
        self.logger = get_logger(__name__)
        self.api_manager = api_manager

    async def generate_questions(
        self,
        user_info: Dict[str, Any],
        analysis_results: Dict[str, Any],
        question_count: int = 3
    ) -> List[VerificationQuestion]:
        """
        根据用户信息和分析结果生成验证问题

        Args:
            user_info: 用户信息（包含年龄、性别、问题类别等）
            analysis_results: 理论分析结果
            question_count: 生成的问题数量

        Returns:
            验证问题列表
        """
        self.logger.info(f"开始生成 {question_count} 个验证问题")

        # 如果有API管理器，使用AI生成
        if self.api_manager:
            try:
                return await self._generate_with_ai(user_info, analysis_results, question_count)
            except Exception as e:
                self.logger.warning(f"AI生成验证问题失败，使用模板: {e}")

        # 回退到模板生成
        return self._generate_from_template(user_info, analysis_results, question_count)

    async def _generate_with_ai(
        self,
        user_info: Dict[str, Any],
        analysis_results: Dict[str, Any],
        question_count: int
    ) -> List[VerificationQuestion]:
        """使用AI生成验证问题"""

        # 提取关键信息
        question_type = user_info.get("question_type", "综合")
        age = user_info.get("age")
        gender = user_info.get("gender", "未知")

        # 当前日期信息
        now = datetime.now()
        current_year = now.year
        current_date = now.strftime("%Y年%m月%d日")

        # 使用提示词模板
        prompt = load_prompt(
            "verification", "questions_gen",
            question_count=question_count,
            question_type=question_type,
            age=age if age else '未知',
            gender=gender,
            current_year=current_year,
            current_date=current_date,
            analysis_summary=self._format_analysis_summary(analysis_results)
        )

        # 调用API
        response = await self.api_manager.call_api(
            task_type="回溯验证生成",
            prompt=prompt,
            enable_dual_verification=False  # 验证问题生成不需要双模型
        )

        # 解析响应
        return self._parse_ai_response(response)

    def _format_analysis_summary(self, analysis_results: Dict[str, Any]) -> str:
        """格式化分析结果摘要"""
        if not analysis_results:
            return "暂无分析结果"

        lines = []
        for theory, result in analysis_results.items():
            if isinstance(result, dict):
                summary = result.get("summary", result.get("judgment", ""))
                judgment = result.get("judgment", "")
                if summary or judgment:
                    lines.append(f"- {theory}: {judgment} - {summary[:50]}..." if len(summary) > 50 else f"- {theory}: {judgment} - {summary}")
            elif isinstance(result, str):
                lines.append(f"- {theory}: {result[:100]}...")

        return "\n".join(lines) if lines else "暂无分析结果"

    def _parse_ai_response(self, response: str) -> List[VerificationQuestion]:
        """解析AI响应"""
        questions = []

        try:
            # 尝试直接解析JSON
            data = json.loads(response)
        except json.JSONDecodeError:
            # 尝试从 ```json ``` 代码块中提取
            code_block_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', response)
            if code_block_match:
                try:
                    data = json.loads(code_block_match.group(1).strip())
                    self.logger.info("从代码块中成功提取JSON")
                except json.JSONDecodeError:
                    pass
                else:
                    # 成功解析，跳过后续处理
                    pass

            # 如果代码块提取失败，尝试从响应中提取JSON数组（贪婪匹配）
            if 'data' not in locals():
                # 使用贪婪匹配找最长的JSON数组
                json_match = re.search(r'\[[\s\S]*\]', response)
                if json_match:
                    try:
                        data = json.loads(json_match.group())
                        self.logger.info("从响应中提取JSON数组成功")
                    except json.JSONDecodeError:
                        self.logger.warning("无法解析AI响应为JSON")
                        self.logger.debug(f"AI响应内容: {response[:500]}...")
                        return questions
                else:
                    self.logger.warning("AI响应中未找到JSON数组")
                    self.logger.debug(f"AI响应内容: {response[:500]}...")
                    return questions

        # 转换为VerificationQuestion对象
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    q = VerificationQuestion(
                        question=item.get("question", ""),
                        question_type=item.get("type", "yes_no"),
                        purpose=item.get("purpose", ""),
                        expected_answers=item.get("expected_answers", []),
                        weight=item.get("weight", 1.0)
                    )
                    if q.question:
                        questions.append(q)

        self.logger.info(f"成功解析 {len(questions)} 个验证问题")
        return questions

    def _generate_from_template(
        self,
        user_info: Dict[str, Any],
        analysis_results: Dict[str, Any],
        question_count: int
    ) -> List[VerificationQuestion]:
        """从模板生成验证问题（回退方案）- 三选项格式"""

        question_type = user_info.get("question_type", "综合")
        questions = []

        # 获取对应类别的模板问题
        templates = self.QUESTION_TEMPLATES.get(question_type, [])

        # 如果类别没有模板，使用综合模板
        if not templates:
            # 从所有模板中随机选择
            all_templates = []
            for t_list in self.QUESTION_TEMPLATES.values():
                all_templates.extend(t_list)
            templates = all_templates

        # 选择问题
        import random
        selected = random.sample(templates, min(question_count, len(templates)))

        for idx, (q_text, purpose_text) in enumerate(selected):
            q = VerificationQuestion(
                question=q_text,
                question_type="three_choice",  # 固定为三选项
                purpose=purpose_text,
                expected_answers=["符合", "部分符合"],  # 预期答案（用于验证准确性）
                weight=1.0
            )
            questions.append(q)

        return questions

    def evaluate_answer(
        self,
        question: VerificationQuestion,
        answer: str
    ) -> bool:
        """
        评估用户答案是否验证通过（支持三选项格式）

        Args:
            question: 验证问题
            answer: 用户答案

        Returns:
            是否验证通过
        """
        # 如果没有预期答案，默认通过（无法验证）
        if not question.expected_answers:
            return True

        # 标准化答案
        answer_normalized = answer.strip()

        # 三选项验证逻辑
        if question.question_type == "three_choice":
            # "符合"和"部分符合"都算验证通过
            if answer_normalized in ["符合", "部分符合"]:
                return "符合" in question.expected_answers or "部分符合" in question.expected_answers
            # "不符合"算验证失败
            elif answer_normalized == "不符合":
                return False
            # 其他答案（如文本描述）尝试模糊匹配
            else:
                # 如果答案包含积极关键词，视为"符合"
                positive_keywords = ["是的", "确实", "有过", "经历过", "发生过"]
                if any(kw in answer_normalized for kw in positive_keywords):
                    return True
                # 如果答案包含消极关键词，视为"不符合"
                negative_keywords = ["没有", "不是", "未曾", "没经历"]
                if any(kw in answer_normalized for kw in negative_keywords):
                    return False
                # 默认视为部分符合
                return True

        # 检查是否匹配预期答案（通用逻辑，保留向后兼容）
        for expected in question.expected_answers:
            expected_normalized = str(expected).strip().lower()
            answer_lower = answer_normalized.lower()

            # 精确匹配
            if answer_lower == expected_normalized:
                return True

            # 包含匹配
            if expected_normalized in answer_lower or answer_lower in expected_normalized:
                return True

        return False

    def calculate_confidence_adjustment(
        self,
        verification_result: VerificationResult
    ) -> float:
        """
        根据验证结果计算置信度调整值

        Args:
            verification_result: 验证结果

        Returns:
            置信度调整值 (-0.15 到 +0.15)
        """
        summary = verification_result.get_summary()

        # 基于准确率调整
        accuracy = summary["accuracy_rate"]
        answered = summary["answered_count"]

        if answered == 0:
            return 0.0

        # 调整公式：
        # - 100%准确：+0.15
        # - 50%准确：0
        # - 0%准确：-0.10
        base_adjustment = (accuracy - 0.5) * 0.3

        # 回答的问题越多，调整幅度越大
        scale = min(answered / 3, 1.0)

        return base_adjustment * scale


# 便捷函数
async def generate_verification_questions(
    api_manager,
    user_info: Dict[str, Any],
    analysis_results: Dict[str, Any],
    question_count: int = 3
) -> List[VerificationQuestion]:
    """
    便捷函数：生成验证问题

    Args:
        api_manager: API管理器
        user_info: 用户信息
        analysis_results: 分析结果
        question_count: 问题数量

    Returns:
        验证问题列表
    """
    generator = DynamicVerificationGenerator(api_manager)
    return await generator.generate_questions(user_info, analysis_results, question_count)
