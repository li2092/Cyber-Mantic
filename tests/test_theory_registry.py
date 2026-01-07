"""
理论注册表和基类单元测试
"""
import pytest
from typing import Dict, Any, List
from theories.base import BaseTheory, TheoryRegistry
from models import UserInput


class MockTheory(BaseTheory):
    """测试用的模拟理论"""

    def __init__(self, name: str = "测试理论", required_fields: List[str] = None):
        self._name = name
        self._required_fields = required_fields or ["birth_year", "birth_month", "birth_day"]
        super().__init__()

    def get_name(self) -> str:
        return self._name

    def get_required_fields(self) -> List[str]:
        return self._required_fields

    def get_optional_fields(self) -> List[str]:
        return ["birth_hour", "question_description"]

    def get_field_weights(self) -> Dict[str, float]:
        return {
            "birth_year": 1.0,
            "birth_month": 1.0,
            "birth_day": 1.0,
            "birth_hour": 0.5,
            "question_description": 0.3
        }

    def get_min_completeness(self) -> float:
        return 0.6

    def calculate(self, user_input: UserInput) -> Dict[str, Any]:
        return {
            "result": "测试结果",
            "judgment": "吉",
            "judgment_level": 0.7,
            "confidence": 0.85
        }


class TestBaseTheory:
    """基类测试"""

    @pytest.fixture
    def mock_theory(self):
        """创建模拟理论"""
        return MockTheory()

    @pytest.fixture
    def complete_input(self):
        """完整用户输入"""
        return UserInput(
            question_type="事业",
            question_description="测试问题",
            birth_year=1990,
            birth_month=1,
            birth_day=15,
            birth_hour=12
        )

    @pytest.fixture
    def minimal_input(self):
        """最小用户输入（仅必需字段）"""
        return UserInput(
            question_type="事业",
            question_description="测试问题",
            birth_year=1990,
            birth_month=1,
            birth_day=15
        )

    def test_initialization(self, mock_theory):
        """测试初始化"""
        assert mock_theory.name == "测试理论"
        assert len(mock_theory.required_fields) == 3
        assert len(mock_theory.optional_fields) == 2
        assert mock_theory.min_completeness == 0.6

    def test_get_name(self, mock_theory):
        """测试获取名称"""
        assert mock_theory.get_name() == "测试理论"

    def test_get_required_fields(self, mock_theory):
        """测试获取必需字段"""
        required = mock_theory.get_required_fields()
        assert "birth_year" in required
        assert "birth_month" in required
        assert "birth_day" in required

    def test_get_optional_fields(self, mock_theory):
        """测试获取可选字段"""
        optional = mock_theory.get_optional_fields()
        assert "birth_hour" in optional
        assert "question_description" in optional

    def test_get_field_weights(self, mock_theory):
        """测试获取字段权重"""
        weights = mock_theory.get_field_weights()
        assert weights["birth_year"] == 1.0
        assert weights["birth_hour"] == 0.5

    def test_get_min_completeness(self, mock_theory):
        """测试获取最小完备度"""
        assert mock_theory.get_min_completeness() == 0.6

    def test_calculate(self, mock_theory, complete_input):
        """测试计算方法"""
        result = mock_theory.calculate(complete_input)
        assert "result" in result
        assert result["judgment"] == "吉"

    def test_get_info_completeness_full(self, mock_theory, complete_input):
        """测试完整信息的完备度"""
        completeness = mock_theory.get_info_completeness(complete_input)
        # 所有字段权重和: 1+1+1+0.5+0.3=3.8
        # 完整输入应该得到1.0
        assert completeness == 1.0

    def test_get_info_completeness_minimal(self, mock_theory, minimal_input):
        """测试最小信息的完备度"""
        completeness = mock_theory.get_info_completeness(minimal_input)
        # 必需字段权重和: 1+1+1=3, 总权重: 3.8
        # 完备度: 3/3.8 ≈ 0.789
        assert completeness > 0.6  # 大于最小完备度
        assert completeness < 1.0  # 小于满分

    def test_get_info_completeness_missing_required(self, mock_theory):
        """测试缺少必需字段时完备度为0"""
        incomplete_input = UserInput(
            question_type="事业",
            question_description="测试问题",
            birth_year=1990,
            birth_month=1
            # 缺少 birth_day
        )
        completeness = mock_theory.get_info_completeness(incomplete_input)
        assert completeness == 0.0

    def test_get_info_completeness_below_minimum(self):
        """测试完备度低于最小要求时返回0"""
        # 创建一个最小完备度为0.9的理论
        theory = MockTheory()
        theory.min_completeness = 0.9

        # 仅提供必需字段（完备度约0.789 < 0.9）
        minimal_input = UserInput(
            question_type="事业",
            question_description="测试问题",
            birth_year=1990,
            birth_month=1,
            birth_day=15
        )

        completeness = theory.get_info_completeness(minimal_input)
        assert completeness == 0.0

    def test_can_analyze_true(self, mock_theory, complete_input):
        """测试可以分析"""
        assert mock_theory.can_analyze(complete_input) is True

    def test_can_analyze_false(self, mock_theory):
        """测试不能分析"""
        incomplete_input = UserInput(
            question_type="事业",
            question_description="测试问题",
            birth_year=1990
            # 缺少 birth_month 和 birth_day
        )
        assert mock_theory.can_analyze(incomplete_input) is False

    def test_to_standard_answer(self, mock_theory, complete_input):
        """测试转换为标准答案"""
        result = mock_theory.calculate(complete_input)
        standard = mock_theory.to_standard_answer(result)

        assert "judgment" in standard
        assert "judgment_level" in standard
        assert "confidence" in standard
        assert standard["judgment"] == "吉"
        assert standard["judgment_level"] == 0.7

    def test_to_standard_answer_defaults(self, mock_theory):
        """测试标准答案的默认值"""
        empty_result = {}
        standard = mock_theory.to_standard_answer(empty_result)

        assert standard["judgment"] == "平"
        assert standard["judgment_level"] == 0.5
        assert standard["confidence"] == 0.8

    def test_different_required_fields(self):
        """测试不同的必需字段组合"""
        # 创建一个自定义MockTheory子类，包含numbers在field_weights中
        class CustomMockTheory(MockTheory):
            def __init__(self):
                super().__init__(required_fields=["question_description", "numbers"])

            def get_field_weights(self) -> Dict[str, float]:
                return {
                    "question_description": 1.0,
                    "numbers": 1.0
                }

        theory = CustomMockTheory()

        # 缺少必需字段
        incomplete = UserInput(
            question_type="事业",
            question_description="测试"
            # 缺少 numbers
        )
        assert theory.can_analyze(incomplete) is False

        # 包含所有必需字段
        complete = UserInput(
            question_type="事业",
            question_description="测试",
            numbers=[1, 2, 3]
        )
        assert theory.can_analyze(complete) is True


class TestTheoryRegistry:
    """理论注册表测试"""

    def setup_method(self):
        """每个测试前保存并清空注册表"""
        self._saved_theories = TheoryRegistry._theories.copy()
        TheoryRegistry._theories = {}

    def teardown_method(self):
        """每个测试后恢复注册表"""
        TheoryRegistry._theories = self._saved_theories

    def test_register_theory(self):
        """测试注册理论"""
        theory = MockTheory(name="八字")
        TheoryRegistry.register(theory)

        assert "八字" in TheoryRegistry._theories
        assert TheoryRegistry._theories["八字"] == theory

    def test_register_multiple_theories(self):
        """测试注册多个理论"""
        theory1 = MockTheory(name="八字")
        theory2 = MockTheory(name="紫微斗数")
        theory3 = MockTheory(name="六爻")

        TheoryRegistry.register(theory1)
        TheoryRegistry.register(theory2)
        TheoryRegistry.register(theory3)

        assert len(TheoryRegistry._theories) == 3
        assert "八字" in TheoryRegistry._theories
        assert "紫微斗数" in TheoryRegistry._theories
        assert "六爻" in TheoryRegistry._theories

    def test_get_theory_exists(self):
        """测试获取存在的理论"""
        theory = MockTheory(name="八字")
        TheoryRegistry.register(theory)

        retrieved = TheoryRegistry.get_theory("八字")
        assert retrieved is not None
        assert retrieved.name == "八字"

    def test_get_theory_not_exists(self):
        """测试获取不存在的理论"""
        retrieved = TheoryRegistry.get_theory("不存在的理论")
        assert retrieved is None

    def test_get_all_theories(self):
        """测试获取所有理论"""
        theory1 = MockTheory(name="八字")
        theory2 = MockTheory(name="紫微斗数")

        TheoryRegistry.register(theory1)
        TheoryRegistry.register(theory2)

        all_theories = TheoryRegistry.get_all_theories()

        assert len(all_theories) == 2
        assert "八字" in all_theories
        assert "紫微斗数" in all_theories

    def test_get_all_theories_returns_copy(self):
        """测试get_all_theories返回副本"""
        theory = MockTheory(name="八字")
        TheoryRegistry.register(theory)

        all_theories = TheoryRegistry.get_all_theories()
        all_theories["新理论"] = MockTheory(name="新理论")

        # 修改返回值不应影响原注册表
        assert "新理论" not in TheoryRegistry._theories

    def test_get_theory_names(self):
        """测试获取所有理论名称"""
        theory1 = MockTheory(name="八字")
        theory2 = MockTheory(name="紫微斗数")
        theory3 = MockTheory(name="六爻")

        TheoryRegistry.register(theory1)
        TheoryRegistry.register(theory2)
        TheoryRegistry.register(theory3)

        names = TheoryRegistry.get_theory_names()

        assert len(names) == 3
        assert "八字" in names
        assert "紫微斗数" in names
        assert "六爻" in names

    def test_get_theory_names_empty(self):
        """测试空注册表时获取理论名称"""
        names = TheoryRegistry.get_theory_names()
        assert names == []

    def test_register_same_name_overwrites(self):
        """测试注册同名理论会覆盖"""
        theory1 = MockTheory(name="八字")
        theory1.version = "v1"

        theory2 = MockTheory(name="八字")
        theory2.version = "v2"

        TheoryRegistry.register(theory1)
        TheoryRegistry.register(theory2)

        # 应该被覆盖
        retrieved = TheoryRegistry.get_theory("八字")
        assert hasattr(retrieved, 'version')
        assert retrieved.version == "v2"

    def test_registry_persistence(self):
        """测试注册表在多次调用间保持状态"""
        theory = MockTheory(name="八字")
        TheoryRegistry.register(theory)

        # 第一次获取
        retrieved1 = TheoryRegistry.get_theory("八字")
        assert retrieved1 is not None

        # 第二次获取应该返回相同对象
        retrieved2 = TheoryRegistry.get_theory("八字")
        assert retrieved2 is retrieved1
