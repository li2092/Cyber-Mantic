"""
奇门遁甲 - 理论实现
"""
from typing import Dict, Any, List
from datetime import datetime
from theories.base import BaseTheory
from models import UserInput
from .calculator_v2 import QiMenCalculatorV2  # 使用完整版V2计算器


class QiMenTheory(BaseTheory):
    """奇门遁甲理论"""

    def __init__(self):
        self.calculator = QiMenCalculatorV2()  # 使用V2版本
        super().__init__()

    def get_name(self) -> str:
        """获取理论名称"""
        return "奇门遁甲"

    def get_required_fields(self) -> List[str]:
        """获取必需字段"""
        return [
            "question_type",
            "question_description",
            "current_time"  # 服务器时间，用于准确起局
        ]

    def get_optional_fields(self) -> List[str]:
        """获取可选字段"""
        return [
            "user_claimed_time",  # 用户声称的时间，用于验证
            "event_category",  # 事项类别（事业、财运等）
            "birth_year",  # 出生年（用于进一步分析）
            "birth_month",
            "birth_day"
        ]

    def get_field_weights(self) -> Dict[str, float]:
        """获取字段权重"""
        return {
            "question_type": 0.3,
            "question_description": 0.3,
            "current_time": 0.3,  # 起局时间非常重要
            "user_claimed_time": 0.05,  # 时间验证
            "event_category": 0.05  # 额外的事项分类
        }

    def get_min_completeness(self) -> float:
        """获取最小完备度要求"""
        return 0.7  # 奇门遁甲需要较高的信息完备度

    def calculate(self, user_input: UserInput) -> Dict[str, Any]:
        """
        计算奇门遁甲排盘

        Args:
            user_input: 用户输入数据

        Returns:
            奇门遁甲计算结果
        """
        # 准备参数
        query_time = user_input.current_time
        user_claimed_time = getattr(user_input, 'user_claimed_time', None)
        event_category = user_input.question_type  # 使用问题类型作为事项类别

        # 执行奇门遁甲计算
        result = self.calculator.calculate_qimen(
            query_time=query_time,
            user_claimed_time=user_claimed_time,
            event_category=event_category
        )

        # 添加基础信息
        result['问题类型'] = user_input.question_type
        result['问题描述'] = user_input.question_description

        # V2版本已包含计算说明，无需重复添加
        # 如果V2未提供，则添加默认说明
        if '计算说明' not in result:
            result['计算说明'] = "使用完整版奇门遁甲排盘算法（V2）"

        # 如果有额外人物信息（代人问事），添加说明
        if user_input.additional_persons and len(user_input.additional_persons) > 0:
            result["代问信息"] = self._analyze_proxy_inquiry(user_input)

        return result

    def _analyze_proxy_inquiry(self, user_input: UserInput) -> Dict[str, Any]:
        """
        分析代人问事的情况（奇门遁甲）

        Args:
            user_input: 用户输入

        Returns:
            代问分析结果
        """
        proxy_info = {
            "问卦人": user_input.name or "本人",
            "代问人数": len(user_input.additional_persons),
            "代问说明": []
        }

        for person in user_input.additional_persons:
            # 根据问题类型给出用神宫位提示
            yongshen_hint = self._get_qimen_yongshen_hint(person.label, user_input.question_type)

            person_info = {
                "姓名/标签": person.label,
                "关系说明": f"{user_input.name or '问卦人'}为{person.label}代问{user_input.question_type}事",
                "用神宫位提示": yongshen_hint,
                "注意事项": [
                    "奇门遁甲以日干代表问卦人，时干代表所问之事",
                    f"此局为代{person.label}询问，解盘时需以{person.label}的立场进行分析",
                    "代问需要问卦人心诚意专，最好能与当事人有强烈的感应联系",
                    "解析时应重点关注用神所在宫位的吉凶、生克制化关系"
                ]
            }

            proxy_info["代问说明"].append(person_info)

        return proxy_info

    def _get_qimen_yongshen_hint(self, person_label: str, question_type: str) -> str:
        """
        根据代问人物和问题类型给出奇门遁甲用神宫位提示

        Args:
            person_label: 人物标签
            question_type: 问题类型

        Returns:
            用神提示
        """
        # 判断人物关系
        if any(kw in person_label for kw in ["父", "母", "爸", "妈", "爷", "奶"]):
            relation = "父母长辈"
            basic_yongshen = "年干或月干宫位"
        elif any(kw in person_label for kw in ["儿", "女", "子", "孩"]):
            relation = "子女晚辈"
            basic_yongshen = "时干宫位"
        elif any(kw in person_label for kw in ["配偶", "老公", "老婆", "丈夫", "妻子"]):
            relation = "配偶"
            basic_yongshen = "六合所在宫位"
        elif any(kw in person_label for kw in ["兄", "弟", "姐", "妹"]):
            relation = "兄弟姐妹"
            basic_yongshen = "比肩宫位"
        else:
            relation = "其他人物"
            basic_yongshen = "需根据具体关系确定"

        # 根据问题类型调整
        if question_type == "事业":
            hint = f"代{relation}问事业，主要看值符、天辅星宫位，兼看{basic_yongshen}"
        elif question_type == "财运":
            hint = f"代{relation}问财运，主要看生门、天财星宫位，兼看{basic_yongshen}"
        elif question_type == "健康":
            hint = f"代{relation}问健康，主要看{basic_yongshen}，兼看天芳星、杜门"
        elif question_type in ["婚姻", "感情"]:
            hint = f"代{relation}问婚姻，主要看六合、天禽星宫位"
        elif question_type == "学业":
            hint = f"代{relation}问学业，主要看天辅星、开门宫位"
        elif question_type == "出行":
            hint = f"代{relation}问出行，主要看值使门、天马星宫位"
        else:
            hint = f"代{relation}问事，用神为{basic_yongshen}，需结合具体问题综合判断"

        return hint

    def to_standard_answer(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        将奇门遁甲结果转换为标准答案格式

        Args:
            result: 计算结果

        Returns:
            标准答案字典
        """
        # 从综合评分提取判断
        overall_score = result.get('综合评分', 0.5)

        if overall_score >= 0.75:
            judgment = '大吉'
            judgment_level = overall_score
        elif overall_score >= 0.6:
            judgment = '吉'
            judgment_level = overall_score
        elif overall_score >= 0.4:
            judgment = '平'
            judgment_level = overall_score
        elif overall_score >= 0.25:
            judgment = '凶'
            judgment_level = overall_score
        else:
            judgment = '大凶'
            judgment_level = overall_score

        # 提取时机建议
        timing_advice = result.get('时机建议', {})
        timing = timing_advice.get('时机', '不明')

        # 综合建议
        advice_parts = []

        # 添加时机建议
        if timing_advice.get('建议'):
            advice_parts.append(timing_advice['建议'])

        # 添加吉利方位
        lucky_directions = result.get('吉利方位', [])
        if lucky_directions:
            advice_parts.append(f"吉利方位：{' '.join(lucky_directions)}")

        # 添加不利方位
        unlucky_directions = result.get('不利方位', [])
        if unlucky_directions:
            advice_parts.append(f"不利方位：{' '.join(unlucky_directions)}")

        # 添加格局信息
        patterns = result.get('格局', [])
        for pattern in patterns:
            advice_parts.append(f"{pattern['格局']}：{pattern['说明']}")

        advice = '\n'.join(advice_parts) if advice_parts else "请根据具体情况谨慎决策"

        return {
            'judgment': judgment,
            'judgment_level': judgment_level,
            'timing': timing,
            'advice': advice,
            'confidence': result.get('confidence', 0.75),
            'detailed_result': result  # 保留完整结果供LLM解读
        }
