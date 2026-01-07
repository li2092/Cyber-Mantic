"""
决策引擎测试
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from models import UserInput, TheoryAnalysisResult
from core.decision_engine import DecisionEngine


class TestDecisionEngine:
    """决策引擎测试"""

    def setup_method(self):
        """设置测试"""
        self.config = {
            "api": {
                "claude_api_key": "test_key",
                "timeout": 30
            },
            "analysis": {
                "max_theories": 5,
                "min_theories": 3
            }
        }

    def test_init(self):
        """测试初始化"""
        engine = DecisionEngine(self.config)

        assert engine.config == self.config
        assert engine.theory_selector is not None
        assert engine.api_manager is not None
        assert engine.conflict_resolver is not None
        assert engine.ai_assistant is not None

    def test_init_with_empty_config(self):
        """测试空配置初始化"""
        engine = DecisionEngine({})

        assert engine.config == {}
        # 应该使用默认配置
        assert engine.theory_selector is not None

    @pytest.mark.skip(reason="需要完整mock整个分析流程，复杂度高，留待集成测试")
    @pytest.mark.asyncio
    async def test_analyze_basic_flow(self):
        """测试基本分析流程（集成测试）"""
        pass

    def test_config_max_theories(self):
        """测试最大理论数配置"""
        custom_config = {
            "api": {"claude_api_key": "test_key"},
            "analysis": {"max_theories": 8}
        }
        engine = DecisionEngine(custom_config)

        max_theories = engine.config.get("analysis", {}).get("max_theories", 5)
        assert max_theories == 8

    def test_config_min_theories(self):
        """测试最小理论数配置"""
        custom_config = {
            "api": {"claude_api_key": "test_key"},
            "analysis": {"min_theories": 2}
        }
        engine = DecisionEngine(custom_config)

        min_theories = engine.config.get("analysis", {}).get("min_theories", 3)
        assert min_theories == 2

    @pytest.mark.skip(reason="需要完整mock整个分析流程，复杂度高，留待集成测试")
    @pytest.mark.asyncio
    async def test_analyze_with_progress_callback(self):
        """测试带进度回调的分析（集成测试）"""
        pass

    def test_components_initialized(self):
        """测试所有组件都被初始化"""
        engine = DecisionEngine(self.config)

        # 验证所有组件都不为None
        assert engine.theory_selector is not None
        assert engine.api_manager is not None
        assert engine.conflict_resolver is not None
        assert engine.ai_assistant is not None
        assert engine.logger is not None

    def test_config_preserved(self):
        """测试配置被保留"""
        engine = DecisionEngine(self.config)

        assert engine.config == self.config
        assert engine.config["api"]["claude_api_key"] == "test_key"
        assert engine.config["analysis"]["max_theories"] == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
