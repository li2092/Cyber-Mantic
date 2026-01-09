"""
测字术理论封装
"""
from typing import Dict, Any, List
from theories.base import BaseTheory
from models import UserInput
from .calculator import CeZiCalculator
import re


class CeZiTheory(BaseTheory):
    """测字术理论"""

    def __init__(self):
        self.calculator = CeZiCalculator()
        super().__init__()

    def get_name(self) -> str:
        return "测字术"

    def get_category(self) -> str:
        return "占卜类"

    def get_required_fields(self) -> List[str]:
        return ["question_description", "character"]  # 测字必须提供字

    def get_optional_fields(self) -> List[str]:
        return ["birth_time", "current_time"]

    def get_field_weights(self) -> Dict[str, float]:
        return {
            "question_description": 0.3,
            "character": 0.7,  # 字是最重要的
            "birth_time": 0.0,
            "current_time": 0.0
        }

    def get_min_completeness(self) -> float:
        return 0.7  # 必须有字才能测字

    def calculate(self, user_input: UserInput) -> Dict[str, Any]:
        """执行测字分析"""
        # 检查是否有多人分析请求
        if hasattr(user_input, 'additional_persons') and user_input.additional_persons:
            self.logger.warning(
                f"{self.get_name()}暂不支持多人分析，将仅分析主要咨询者，"
                f"忽略其他{len(user_input.additional_persons)}人的信息"
            )

        # 从问题描述中提取汉字
        question = user_input.question_description or ""
        character = self._extract_character(question, user_input)

        # 执行测字分析
        result = self.calculator.analyze_character(
            character=character,
            question=question,
            context=""
        )

        return result

    def to_standard_answer(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """转换为标准答案格式"""
        # 提取吉凶判断
        judgment = result.get("吉凶判断", result.get("judgment", "平"))
        judgment_level = result.get("综合评分", result.get("judgment_level", 0.5))

        # 提取建议（测字主要给建议，没有具体时机）
        advice = result.get("advice", result.get("建议", result.get("解读")))

        return {
            "judgment": judgment,
            "judgment_level": judgment_level,
            "timing": None,  # 测字主要看吉凶和解读，不特别论时机
            "advice": advice,
            "confidence": result.get("confidence", result.get("置信度", 0.65))
        }

    def _extract_character(self, question: str, user_input: UserInput) -> str:
        """
        从问题中提取要测的字

        优先级：
        0. **优先使用FlowGuard已提取的字符（user_input.character）** - AI 智能提取最准确
        1. 问题中明确说"测XX字"
        2. 问题中的引号字符
        3. 句尾单独出现的字（逗号/句号后）
        4. 第一个有意义的汉字
        5. 使用当前时辰地支
        """
        # 方法0: 优先使用FlowGuard验证过的字符（AI 已智能分析）
        if user_input.character and len(user_input.character) > 0:
            self.logger.info(f"使用FlowGuard提取的字符: {user_input.character}")
            return user_input.character[0]

        # 方法1: 检测"测X字"模式
        match = re.search(r'测[""\"]?([^""\"\s]{1,3})[""\"]?字', question)
        if match:
            return match.group(1)[0]

        # 方法2: 检测引号中的字
        match = re.search(r'[""\'"\']([^""\'"\'\s]+)[""\'"\']', question)
        if match:
            chinese_chars = re.findall(r'[\u4e00-\u9fff]', match.group(1))
            if chinese_chars:
                return chinese_chars[0]

        # 方法3: 提取句尾单字（逗号/句号/问号后的单个汉字）
        # 如："就像知道这辈子能不能升官发财，望" → 提取"望"
        match = re.search(r'[，。！？,.\!?]\s*([\u4e00-\u9fff])[\s，。！？,.\!?]*$', question)
        if match:
            char = match.group(1)
            # 排除语气词
            if char not in ['啊', '吧', '呢', '吗', '哦', '嗯']:
                self.logger.info(f"提取句尾单字: {char}")
                return char

        # 方法4: 提取第一个有意义的汉字
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', question)
        if chinese_chars:
            # 跳过常见的问题词和语气词
            skip_words = ['问', '请', '想', '能', '会', '吗', '呢', '啊', '的', '了', '是', '有', '我', '你', '他', '这', '那']
            for char in chinese_chars:
                if char not in skip_words:
                    return char
            # 如果都是常见词，取第一个
            return chinese_chars[0]

        # 方法5: 使用时辰地支
        from theories.bazi.constants import DI_ZHI

        # 时辰到地支索引的映射
        HOUR_ZHI_MAP = {
            23: 0, 0: 0, 1: 1, 2: 1,
            3: 2, 4: 2, 5: 3, 6: 3,
            7: 4, 8: 4, 9: 5, 10: 5,
            11: 6, 12: 6, 13: 7, 14: 7,
            15: 8, 16: 8, 17: 9, 18: 9,
            19: 10, 20: 10, 21: 11, 22: 11
        }

        # 优先使用出生时辰
        if user_input.birth_hour is not None:
            hour = user_input.birth_hour
            zhi_index = HOUR_ZHI_MAP.get(hour, 0)
            return DI_ZHI[zhi_index]
        # 其次使用当前时间
        elif user_input.current_time:
            hour = user_input.current_time.hour
            zhi_index = HOUR_ZHI_MAP.get(hour, 0)
            return DI_ZHI[zhi_index]

        # 默认值
        return "问"
