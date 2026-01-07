"""
AnalysisService - 分析流程服务

封装分析流程，将业务逻辑从UI层分离
"""

from typing import Optional, Callable, Tuple
from models import UserInput, ComprehensiveReport
from core.decision_engine import DecisionEngine
from utils.logger import get_logger


class AnalysisService:
    """分析服务"""

    def __init__(self, engine: DecisionEngine):
        self.engine = engine
        self.logger = get_logger(__name__)

    async def analyze(
        self,
        user_input: UserInput,
        progress_callback: Optional[Callable[[str, str, int], None]] = None
    ) -> ComprehensiveReport:
        """
        执行分析

        Args:
            user_input: 用户输入
            progress_callback: 进度回调函数(theory_name, message, progress)

        Returns:
            综合报告
        """
        self.logger.info(f"开始分析: {user_input.question_description[:50]}")

        report = await self.engine.analyze(user_input, progress_callback)

        self.logger.info(f"分析完成: 报告ID={report.report_id}")

        return report

    def validate_input(self, user_input: UserInput) -> Tuple[bool, str]:
        """
        验证用户输入

        Args:
            user_input: 用户输入

        Returns:
            (是否有效, 错误信息)
        """
        # 必填字段检查
        if not user_input.question_description:
            return False, "请输入问题描述"

        if not user_input.question_type:
            return False, "请选择问题类别"

        # 检查是否有足够的信息
        has_birth_info = (
            user_input.birth_year and
            user_input.birth_month and
            user_input.birth_day
        )

        has_numbers = user_input.numbers and len(user_input.numbers) >= 3

        has_character = user_input.character and len(user_input.character) == 1

        if not any([has_birth_info, has_numbers, has_character]):
            return False, "请至少提供出生信息、随机数字或测字汉字之一"

        return True, ""

    def estimate_duration(self, user_input: UserInput) -> int:
        """
        估算分析时长（秒）

        Args:
            user_input: 用户输入

        Returns:
            预计时长（秒）
        """
        # 基础时长：30秒
        base_duration = 30

        # 根据可用理论数量调整
        has_birth_info = user_input.birth_year is not None
        has_numbers = user_input.numbers is not None
        has_character = user_input.character is not None

        available_theories = 0
        if has_birth_info:
            available_theories += 4  # 八字、紫微、奇门、六壬
        if has_numbers:
            available_theories += 2  # 六爻、梅花
        if has_character:
            available_theories += 1  # 测字

        # 每个理论约10秒
        theory_duration = available_theories * 10

        return base_duration + theory_duration
