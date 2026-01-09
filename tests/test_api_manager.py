"""
API管理器测试
"""
import pytest
import os
from unittest.mock import Mock, patch, AsyncMock
from api.manager import APIManager


class TestAPIManager:
    """API管理器测试"""

    def setup_method(self):
        """设置测试"""
        # 基础配置
        self.config = {
            "claude_api_key": "test_claude_key",
            "gemini_api_key": "test_gemini_key",
            "deepseek_api_key": "test_deepseek_key",
            "kimi_api_key": "test_kimi_key",
            "timeout": 30,
            "max_retries": 3,
            "enable_dual_verification": True,
            "primary_api": "claude"
        }

    def test_init_with_config(self):
        """测试使用配置初始化"""
        manager = APIManager(self.config)

        assert manager.timeout == 30
        assert manager.max_retries == 3
        assert manager.enable_dual_verification is True
        assert manager.primary_api == "claude"

    def test_available_apis_detection(self):
        """测试可用API检测"""
        manager = APIManager(self.config)

        assert "claude" in manager.available_apis
        assert "gemini" in manager.available_apis
        assert "deepseek" in manager.available_apis
        assert "kimi" in manager.available_apis

    def test_init_without_api_keys(self):
        """测试没有API密钥的初始化"""
        empty_config = {}
        manager = APIManager(empty_config)

        # 没有密钥，可用API应该为空
        assert len(manager.available_apis) == 0

    def test_get_api_for_task_comprehensive_report(self):
        """测试综合报告任务选择API"""
        manager = APIManager(self.config)

        api = manager.get_api_for_task("综合报告解读")
        assert api == "claude"

    def test_get_api_for_task_quick_interaction(self):
        """测试快速交互任务选择API（V2版本：优先使用primary_api）"""
        manager = APIManager(self.config)

        # V2: 由于primary_api是claude且可用，所以返回claude
        # 这是预期行为，用户设置优先于任务类型映射
        api = manager.get_api_for_task("快速交互问答")
        assert api == "claude"  # primary_api优先

    def test_get_api_for_task_uses_task_mapping_when_no_primary(self):
        """测试primary_api不可用时使用任务类型映射"""
        # claude和deepseek都有API key，但primary_api设为不存在的API
        config_no_primary = {
            "claude_api_key": "test-key",
            "deepseek_api_key": "test-key",
            "primary_api": "nonexistent"  # 不存在的API
        }
        manager = APIManager(config_no_primary)

        # primary_api不可用，使用任务映射
        api = manager.get_api_for_task("快速交互问答")
        assert api == "deepseek"  # 按任务映射应选deepseek

    def test_get_api_for_task_conflict_resolution(self):
        """测试冲突解决任务选择API"""
        manager = APIManager(self.config)

        api = manager.get_api_for_task("冲突解决分析")
        assert api == "claude"

    def test_get_api_for_task_fallback_to_primary(self):
        """测试未知任务类型回退到主API"""
        manager = APIManager(self.config)

        api = manager.get_api_for_task("未知任务类型")
        assert api == "claude"  # 应该回退到primary_api

    def test_get_api_for_task_unavailable_recommended(self):
        """测试推荐API不可用时的回退"""
        # 只有deepseek可用
        limited_config = {
            "deepseek_api_key": "test_key",
            "primary_api": "claude"
        }
        manager = APIManager(limited_config)

        # 综合报告推荐claude，但不可用，应该回退
        api = manager.get_api_for_task("综合报告解读")
        assert api == "deepseek"  # 第一个可用的API

    def test_api_priority_order(self):
        """测试API优先级顺序"""
        manager = APIManager(self.config)

        assert manager.API_PRIORITY == ["claude", "gemini", "deepseek", "kimi"]

    def test_api_usage_map_exists(self):
        """测试API使用场景映射存在"""
        manager = APIManager(self.config)

        assert "综合报告解读" in manager.API_USAGE_MAP
        assert "单理论解读" in manager.API_USAGE_MAP
        assert "快速交互问答" in manager.API_USAGE_MAP
        assert "冲突解决分析" in manager.API_USAGE_MAP

    def test_models_configuration(self):
        """测试模型配置"""
        manager = APIManager(self.config)

        assert "claude" in manager.models
        assert "gemini" in manager.models
        assert "deepseek" in manager.models
        assert "kimi" in manager.models

    def test_custom_model_configuration(self):
        """测试自定义模型配置"""
        custom_config = {
            "claude_api_key": "test_key",
            "claude_model": "custom-claude-model"
        }
        manager = APIManager(custom_config)

        assert manager.models["claude"] == "custom-claude-model"

    def test_timeout_configuration(self):
        """测试超时配置"""
        custom_config = {
            "claude_api_key": "test_key",
            "timeout": 60
        }
        manager = APIManager(custom_config)

        assert manager.timeout == 60

    def test_max_retries_configuration(self):
        """测试最大重试次数配置"""
        custom_config = {
            "claude_api_key": "test_key",
            "max_retries": 5
        }
        manager = APIManager(custom_config)

        assert manager.max_retries == 5

    def test_dual_verification_configuration(self):
        """测试双模型验证配置"""
        # 启用双模型验证
        config_enabled = {
            "claude_api_key": "test_key",
            "enable_dual_verification": True
        }
        manager_enabled = APIManager(config_enabled)
        assert manager_enabled.enable_dual_verification is True

        # 禁用双模型验证
        config_disabled = {
            "claude_api_key": "test_key",
            "enable_dual_verification": False
        }
        manager_disabled = APIManager(config_disabled)
        assert manager_disabled.enable_dual_verification is False

    def test_primary_api_configuration(self):
        """测试主API配置"""
        custom_config = {
            "deepseek_api_key": "test_key",
            "primary_api": "deepseek"
        }
        manager = APIManager(custom_config)

        assert manager.primary_api == "deepseek"

    def test_env_variable_api_keys(self):
        """测试从环境变量读取API密钥"""
        with patch.dict(os.environ, {
            "CLAUDE_API_KEY": "env_claude_key",
            "GEMINI_API_KEY": "env_gemini_key"
        }):
            manager = APIManager({})

            assert manager.api_keys["claude"] == "env_claude_key"
            assert manager.api_keys["gemini"] == "env_gemini_key"

    def test_config_overrides_env(self):
        """测试配置优先于环境变量"""
        with patch.dict(os.environ, {
            "CLAUDE_API_KEY": "env_key"
        }):
            config = {"claude_api_key": "config_key"}
            manager = APIManager(config)

            assert manager.api_keys["claude"] == "config_key"

    def test_multiple_available_apis(self):
        """测试多个可用API"""
        config = {
            "claude_api_key": "key1",
            "deepseek_api_key": "key2"
        }
        manager = APIManager(config)

        assert len(manager.available_apis) == 2
        assert "claude" in manager.available_apis
        assert "deepseek" in manager.available_apis

    def test_single_available_api(self):
        """测试只有一个可用API"""
        config = {
            "kimi_api_key": "key1"
        }
        manager = APIManager(config)

        assert len(manager.available_apis) == 1
        assert "kimi" in manager.available_apis


class TestAPIManagerCallAPI:
    """API调用测试（需要mock）"""

    def setup_method(self):
        """设置测试"""
        self.config = {
            "claude_api_key": "test_key",
            "deepseek_api_key": "test_key",
            "timeout": 30,
            "max_retries": 3
        }

    @pytest.mark.asyncio
    async def test_call_api_with_failover(self):
        """测试故障转移机制"""
        manager = APIManager(self.config)

        # Mock _call_api_by_name方法
        with patch.object(manager, '_call_api_by_name', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = "测试响应"

            result = await manager.call_api(
                task_type="综合报告解读",
                prompt="测试提示",
                enable_dual_verification=False
            )

            assert result == "测试响应"

    @pytest.mark.asyncio
    async def test_call_api_dual_verification_disabled(self):
        """测试禁用双模型验证"""
        config = {
            "claude_api_key": "test_key",
            "enable_dual_verification": False
        }
        manager = APIManager(config)

        with patch.object(manager, '_call_api_by_name', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = "测试响应"

            result = await manager.call_api(
                task_type="快速交互问答",
                prompt="测试提示"
            )

            assert result == "测试响应"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
