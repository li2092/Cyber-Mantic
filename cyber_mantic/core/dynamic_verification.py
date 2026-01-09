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

    # 问题类型模板
    QUESTION_TEMPLATES = {
        "事业": [
            "在过去3年内，您是否经历过工作变动（换工作、升职、降职等）？",
            "您最近一次重要的事业决策是在哪一年？",
            "在2020-2024年间，您的收入是否有明显增长？"
        ],
        "感情": [
            "在过去3年内，您的感情状态是否发生过重大变化？",
            "您是否在2020年后开始/结束一段重要的感情关系？",
            "您目前的感情状态与3年前相比如何？"
        ],
        "财运": [
            "在过去3年内，您是否有过重大投资或理财决策？",
            "您的财务状况在2022年前后是否有明显变化？",
            "您是否经历过意外的财务收入或损失？"
        ],
        "健康": [
            "在过去3年内，您或家人是否有过健康问题？",
            "您的身体状况与3年前相比如何？",
            "您是否在最近几年养成了新的健康习惯？"
        ],
        "决策": [
            "您最近一次重大人生决策是什么时候做出的？",
            "这个决策的结果是否符合您当时的预期？",
            "如果有机会，您会改变当时的决定吗？"
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

        # 使用提示词模板
        prompt = load_prompt(
            "verification", "questions_gen",
            question_count=question_count,
            question_type=question_type,
            age=age if age else '未知',
            gender=gender,
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
            # 尝试从响应中提取JSON数组
            json_match = re.search(r'\[[\s\S]*?\]', response)
            if json_match:
                try:
                    data = json.loads(json_match.group())
                except json.JSONDecodeError:
                    self.logger.warning("无法解析AI响应为JSON")
                    return questions
            else:
                self.logger.warning("AI响应中未找到JSON数组")
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
        """从模板生成验证问题（回退方案）"""

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

        for idx, q_text in enumerate(selected):
            q = VerificationQuestion(
                question=q_text,
                question_type="yes_no" if "是否" in q_text else "year" if "哪一年" in q_text else "event",
                purpose=f"验证{question_type}相关分析",
                expected_answers=[],
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
        评估用户答案是否验证通过

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
        answer_normalized = answer.strip().lower()

        # 检查是否匹配预期答案
        for expected in question.expected_answers:
            expected_normalized = str(expected).strip().lower()

            # 精确匹配
            if answer_normalized == expected_normalized:
                return True

            # 包含匹配（对于年份等）
            if expected_normalized in answer_normalized or answer_normalized in expected_normalized:
                return True

            # 是/否问题的变体
            if question.question_type == "yes_no":
                positive = ["是", "yes", "对", "有", "确实", "没错", "正确"]
                negative = ["否", "no", "不", "没有", "没", "错", "不对"]

                if expected_normalized in positive and answer_normalized in positive:
                    return True
                if expected_normalized in negative and answer_normalized in negative:
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
