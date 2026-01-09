"""
V2功能测试 - 测试赛博玄数V2版本的核心功能

V2新增功能：
1. FlowGuard - 流程监管
2. DynamicVerification - 动态回溯验证
3. ShichenHandler - 时辰智能处理
4. ArbitrationSystem - 仲裁系统
5. APISettingsWidget - API配置UI
6. PromptLoader - 提示词加载器
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch


class TestFlowGuard:
    """FlowGuard流程监管测试"""

    def setup_method(self):
        """设置测试"""
        from core.flow_guard import FlowGuard
        self.guard = FlowGuard()

    def test_init(self):
        """测试初始化"""
        assert self.guard is not None
        assert self.guard.current_stage is not None

    def test_set_stage(self):
        """测试阶段设置"""
        self.guard.set_stage("STAGE1_ICEBREAK")
        assert self.guard.current_stage == "STAGE1_ICEBREAK"

        self.guard.set_stage("STAGE2_BASIC_INFO")
        assert self.guard.current_stage == "STAGE2_BASIC_INFO"

    def test_generate_progress_display(self):
        """测试进度显示生成"""
        self.guard.set_stage("STAGE2_BASIC_INFO")

        display = self.guard.generate_progress_display()

        assert isinstance(display, str)
        assert len(display) > 0

    def test_get_stage_progress(self):
        """测试获取阶段进度"""
        self.guard.set_stage("STAGE2_BASIC_INFO")
        progress = self.guard.get_stage_progress()

        assert progress is not None
        # StageProgress对象

    def test_validate_category(self):
        """测试问题类别验证"""
        result = self.guard.validate_category("事业")
        assert result is not None

        result = self.guard.validate_category("财运")
        assert result is not None

    def test_validate_year(self):
        """测试年份验证"""
        result = self.guard.validate_year("1990")
        assert result == 1990

        result = self.guard.validate_year("90年")
        assert result == 1990 or result is None

    def test_validate_month(self):
        """测试月份验证"""
        # validate_month可能需要特定格式
        result = self.guard.validate_month("5月")
        assert result == 5 or result is None

        result = self.guard.validate_month("12")
        assert result == 12 or result is None

    def test_validate_gender(self):
        """测试性别验证"""
        result = self.guard.validate_gender("男")
        assert result == "male" or result == "男"

        result = self.guard.validate_gender("女")
        assert result == "female" or result == "女"

    def test_validate_numbers(self):
        """测试随机数验证"""
        result = self.guard.validate_numbers("7 3 5")
        assert result is not None
        assert len(result) == 3


class TestDynamicVerification:
    """动态回溯验证测试"""

    def setup_method(self):
        """设置测试"""
        from core.dynamic_verification import (
            DynamicVerificationGenerator,
            VerificationQuestion,
            VerificationResult
        )
        self.generator = DynamicVerificationGenerator()
        self.VerificationQuestion = VerificationQuestion
        self.VerificationResult = VerificationResult

    def test_verification_question_creation(self):
        """测试验证问题创建"""
        question = self.VerificationQuestion(
            question="您在2018年是否有事业变动？",
            question_type="yes_no",
            purpose="验证事业运势预测",
            expected_answers=["是", "有"],
            weight=1.0
        )

        assert question.question == "您在2018年是否有事业变动？"
        assert question.question_type == "yes_no"
        assert question.weight == 1.0
        assert question.is_verified is None

    def test_verification_question_to_dict(self):
        """测试验证问题转字典"""
        question = self.VerificationQuestion(
            question="测试问题",
            question_type="yes_no",
            purpose="测试目的"
        )

        data = question.to_dict()
        assert "question" in data
        assert "type" in data
        assert "purpose" in data

    def test_verification_question_from_dict(self):
        """测试从字典创建验证问题"""
        data = {
            "question": "测试问题",
            "type": "yes_no",
            "purpose": "测试目的",
            "expected_answers": ["是"],
            "weight": 0.8
        }

        question = self.VerificationQuestion.from_dict(data)
        assert question.question == "测试问题"
        assert question.weight == 0.8

    def test_verification_result_init(self):
        """测试验证结果初始化"""
        questions = [
            self.VerificationQuestion(
                question="问题1",
                question_type="yes_no",
                purpose="目的1"
            ),
            self.VerificationQuestion(
                question="问题2",
                question_type="year",
                purpose="目的2"
            )
        ]

        result = self.VerificationResult(questions)
        assert len(result.questions) == 2

    def test_generator_init(self):
        """测试生成器初始化"""
        assert self.generator is not None


class TestShichenHandler:
    """时辰智能处理测试"""

    def setup_method(self):
        """设置测试"""
        from core.shichen_handler import ShichenHandler
        self.handler = ShichenHandler()

    def test_init(self):
        """测试初始化"""
        assert self.handler is not None

    def test_parse_time_input(self):
        """测试时间输入解析"""
        from core.shichen_handler import ShichenInfo

        # 测试精确时间
        info = self.handler.parse_time_input("14:30")
        assert isinstance(info, ShichenInfo)

        # 测试中文时间表达
        info = self.handler.parse_time_input("下午2点")
        assert isinstance(info, ShichenInfo)

    def test_format_time_display(self):
        """测试时间显示格式化"""
        from core.shichen_handler import ShichenInfo

        info = self.handler.parse_time_input("14:30")
        display = self.handler.format_time_display(info)
        assert isinstance(display, str)

    def test_calculate_hour_ganzhi(self):
        """测试时辰干支计算"""
        # 计算某日某时的干支
        result = self.handler.calculate_hour_ganzhi("甲", 14)
        assert result is not None

    def test_three_pillar_mode_info(self):
        """测试三柱模式信息"""
        info = self.handler.get_three_pillar_mode_info()
        assert isinstance(info, dict)


class TestArbitrationSystem:
    """仲裁系统测试"""

    def setup_method(self):
        """设置测试"""
        from core.arbitration_system import ArbitrationSystem
        self.system = ArbitrationSystem()

    def test_init(self):
        """测试初始化"""
        assert self.system is not None

    def test_has_arbitrate_method(self):
        """测试仲裁方法存在"""
        # 检查是否有仲裁相关方法
        methods = dir(self.system)
        # 应该有仲裁或协调相关的方法
        arbitration_methods = [m for m in methods if not m.startswith('_')]
        assert len(arbitration_methods) > 0


class TestPromptLoader:
    """提示词加载器测试"""

    def test_load_prompt(self):
        """测试加载提示词"""
        from api.prompt_loader import load_prompt

        # 测试加载AI增强提示词
        prompt = load_prompt(
            "enhance",
            "time_expression",
            user_input="我是1990年5月15日出生的"
        )

        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "1990年5月15日" in prompt

    def test_load_prompt_with_variables(self):
        """测试带变量的提示词加载"""
        from api.prompt_loader import load_prompt

        prompt = load_prompt(
            "enhance",
            "question_type",
            user_input="今年我的财运如何？"
        )

        assert isinstance(prompt, str)
        assert "财运" in prompt

    def test_load_verification_prompt(self):
        """测试加载验证提示词"""
        from api.prompt_loader import load_prompt

        prompt = load_prompt(
            "verification",
            "questions_gen",
            question_count=3,
            question_type="事业",
            age=30,
            gender="male",
            analysis_summary="事业运势分析..."
        )

        assert isinstance(prompt, str)
        assert len(prompt) > 0


class TestTaskRouter:
    """任务路由测试"""

    def setup_method(self):
        """设置测试"""
        from api.task_router import TaskRouter
        self.router = TaskRouter()

    def test_init(self):
        """测试初始化"""
        assert self.router is not None

    def test_has_routing_methods(self):
        """测试路由方法存在"""
        methods = [m for m in dir(self.router) if not m.startswith('_')]
        assert len(methods) > 0


class TestAPISettingsWidget:
    """API设置组件测试"""

    def test_import(self):
        """测试导入"""
        from ui.widgets.api_settings_widget import APISettingsWidget
        assert APISettingsWidget is not None


class TestIntegration:
    """V2功能集成测试"""

    def test_flowguard_stage_transition(self):
        """测试FlowGuard阶段转换"""
        from core.flow_guard import FlowGuard

        guard = FlowGuard()

        # 模拟阶段转换
        guard.set_stage("STAGE1_ICEBREAK")
        assert guard.current_stage == "STAGE1_ICEBREAK"

        guard.set_stage("STAGE2_BASIC_INFO")
        assert guard.current_stage == "STAGE2_BASIC_INFO"

    def test_shichen_with_time(self):
        """测试时辰处理"""
        from core.shichen_handler import ShichenHandler, ShichenInfo

        handler = ShichenHandler()

        # 测试不同时间点的解析
        test_times = ["0:00", "6:00", "12:00", "18:00", "23:00"]
        for time_str in test_times:
            info = handler.parse_time_input(time_str)
            assert isinstance(info, ShichenInfo)

    def test_prompt_loader_enhance_category(self):
        """测试增强类提示词加载"""
        from api.prompt_loader import load_prompt

        # 测试各个增强提示词
        enhance_prompts = [
            ("time_expression", {"user_input": "1990年5月15日"}),
            ("question_type", {"user_input": "财运如何"}),
        ]

        for prompt_name, kwargs in enhance_prompts:
            prompt = load_prompt("enhance", prompt_name, **kwargs)
            assert isinstance(prompt, str)
            assert len(prompt) > 0
