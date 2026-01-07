"""
配置管理器单元测试
"""
import os
import tempfile
import pytest
import yaml
from pathlib import Path
from utils.config_manager import ConfigManager


class TestConfigManager:
    """配置管理器测试类"""

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def sample_system_config(self):
        """示例系统配置"""
        return {
            "api": {
                "claude_api_key": "${CLAUDE_API_KEY}",
                "gemini_api_key": "${GEMINI_API_KEY}",
                "deepseek_api_key": "system_deepseek_key",
                "kimi_api_key": ""
            },
            "analysis": {
                "max_theories": 5,
                "min_completeness": 0.6
            },
            "ui": {
                "theme": "auto",
                "font_size": 12
            }
        }

    @pytest.fixture
    def sample_user_config(self):
        """示例用户配置"""
        return {
            "api": {
                "deepseek_api_key": "user_deepseek_key"  # 覆盖系统配置
            },
            "ui": {
                "theme": "dark",  # 覆盖系统配置
                "language": "zh_CN"  # 新增配置
            }
        }

    def test_initialization(self, temp_dir):
        """测试初始化"""
        config_file = temp_dir / "config.yaml"
        user_config_file = temp_dir / "user_config.yaml"

        # 创建空配置文件
        config_file.write_text("{}", encoding="utf-8")

        manager = ConfigManager(str(config_file), str(user_config_file))

        assert manager.config_file == config_file
        assert manager.user_config_file == user_config_file
        assert isinstance(manager.config, dict)

    def test_load_yaml_file(self, temp_dir, sample_system_config):
        """测试加载YAML文件"""
        config_file = temp_dir / "config.yaml"

        # 写入配置
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(sample_system_config, f)

        manager = ConfigManager(str(config_file), str(temp_dir / "user.yaml"))
        loaded = manager._load_yaml_file(config_file)

        assert loaded["analysis"]["max_theories"] == 5
        assert loaded["ui"]["theme"] == "auto"

    def test_load_yaml_file_not_exists(self, temp_dir):
        """测试加载不存在的文件"""
        manager = ConfigManager(str(temp_dir / "config.yaml"), str(temp_dir / "user.yaml"))
        result = manager._load_yaml_file(temp_dir / "nonexistent.yaml")

        assert result == {}

    def test_replace_env_vars(self, temp_dir, sample_system_config):
        """测试环境变量替换"""
        # 设置环境变量
        os.environ["CLAUDE_API_KEY"] = "test_claude_key"
        os.environ["GEMINI_API_KEY"] = "test_gemini_key"

        config_file = temp_dir / "config.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(sample_system_config, f)

        manager = ConfigManager(str(config_file), str(temp_dir / "user.yaml"))

        # 验证环境变量被替换
        assert manager.config["api"]["claude_api_key"] == "test_claude_key"
        assert manager.config["api"]["gemini_api_key"] == "test_gemini_key"
        assert manager.config["api"]["deepseek_api_key"] == "system_deepseek_key"

        # 清理环境变量
        del os.environ["CLAUDE_API_KEY"]
        del os.environ["GEMINI_API_KEY"]

    def test_replace_env_vars_missing(self, temp_dir):
        """测试替换不存在的环境变量"""
        config = {"key": "${NONEXISTENT_ENV_VAR}"}
        config_file = temp_dir / "config.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f)

        manager = ConfigManager(str(config_file), str(temp_dir / "user.yaml"))

        # 不存在的环境变量应该被替换为空字符串
        assert manager.config["key"] == ""

    def test_deep_merge(self, temp_dir):
        """测试深度合并"""
        manager = ConfigManager(str(temp_dir / "config.yaml"), str(temp_dir / "user.yaml"))

        base = {
            "a": 1,
            "b": {"c": 2, "d": 3},
            "e": {"f": 4}
        }

        override = {
            "b": {"c": 20},  # 覆盖 b.c
            "e": {"g": 5},   # 新增 e.g
            "h": 6           # 新增 h
        }

        result = manager._deep_merge(base, override)

        assert result["a"] == 1
        assert result["b"]["c"] == 20  # 已覆盖
        assert result["b"]["d"] == 3   # 保留
        assert result["e"]["f"] == 4   # 保留
        assert result["e"]["g"] == 5   # 新增
        assert result["h"] == 6        # 新增

    def test_user_config_override(self, temp_dir, sample_system_config, sample_user_config):
        """测试用户配置覆盖系统配置"""
        config_file = temp_dir / "config.yaml"
        user_config_file = temp_dir / "user_config.yaml"

        # 写入配置文件
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(sample_system_config, f)
        with open(user_config_file, 'w', encoding='utf-8') as f:
            yaml.dump(sample_user_config, f)

        manager = ConfigManager(str(config_file), str(user_config_file))

        # 验证用户配置覆盖了系统配置
        assert manager.config["api"]["deepseek_api_key"] == "user_deepseek_key"
        assert manager.config["ui"]["theme"] == "dark"
        assert manager.config["ui"]["language"] == "zh_CN"

        # 验证未覆盖的配置保留
        assert manager.config["analysis"]["max_theories"] == 5

    def test_get_simple_path(self, temp_dir, sample_system_config):
        """测试获取简单路径的配置"""
        config_file = temp_dir / "config.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(sample_system_config, f)

        manager = ConfigManager(str(config_file), str(temp_dir / "user.yaml"))

        assert manager.get("analysis.max_theories") == 5
        assert manager.get("ui.theme") == "auto"
        assert manager.get("ui.font_size") == 12

    def test_get_nested_path(self, temp_dir, sample_system_config):
        """测试获取嵌套路径的配置"""
        config_file = temp_dir / "config.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(sample_system_config, f)

        manager = ConfigManager(str(config_file), str(temp_dir / "user.yaml"))

        assert manager.get("api.claude_api_key") == ""  # 环境变量未设置
        assert manager.get("api.deepseek_api_key") == "system_deepseek_key"

    def test_get_with_default(self, temp_dir):
        """测试获取不存在的配置时返回默认值"""
        manager = ConfigManager(str(temp_dir / "config.yaml"), str(temp_dir / "user.yaml"))

        assert manager.get("nonexistent.key", "default_value") == "default_value"
        assert manager.get("api.nonexistent_key", None) is None
        assert manager.get("completely.missing.path", 42) == 42

    def test_set_simple_path(self, temp_dir):
        """测试设置简单路径的配置"""
        manager = ConfigManager(str(temp_dir / "config.yaml"), str(temp_dir / "user.yaml"))

        manager.set("new_key", "new_value")
        assert manager.get("new_key") == "new_value"

    def test_set_nested_path(self, temp_dir):
        """测试设置嵌套路径的配置"""
        manager = ConfigManager(str(temp_dir / "config.yaml"), str(temp_dir / "user.yaml"))

        manager.set("api.new_api_key", "test_key")
        assert manager.get("api.new_api_key") == "test_key"

    def test_set_deep_nested_path(self, temp_dir):
        """测试设置深度嵌套路径的配置"""
        manager = ConfigManager(str(temp_dir / "config.yaml"), str(temp_dir / "user.yaml"))

        manager.set("level1.level2.level3.key", "deep_value")
        assert manager.get("level1.level2.level3.key") == "deep_value"

    def test_save_user_config(self, temp_dir, sample_system_config):
        """测试保存用户配置"""
        config_file = temp_dir / "config.yaml"
        user_config_file = temp_dir / "user_config.yaml"

        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(sample_system_config, f)

        manager = ConfigManager(str(config_file), str(user_config_file))

        # 保存用户配置
        user_data = {"ui": {"theme": "light", "font_size": 14}}
        result = manager.save_user_config(user_data)

        assert result is True
        assert user_config_file.exists()

        # 验证配置已更新
        assert manager.get("ui.theme") == "light"
        assert manager.get("ui.font_size") == 14

    def test_get_api_keys(self, temp_dir, sample_system_config):
        """测试获取API密钥"""
        config_file = temp_dir / "config.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(sample_system_config, f)

        manager = ConfigManager(str(config_file), str(temp_dir / "user.yaml"))
        api_keys = manager.get_api_keys()

        assert "claude" in api_keys
        assert "gemini" in api_keys
        assert "deepseek" in api_keys
        assert "kimi" in api_keys
        assert "amap" in api_keys

        assert api_keys["deepseek"] == "system_deepseek_key"

    def test_has_valid_api_key_true(self, temp_dir):
        """测试检测到有效API密钥"""
        config = {"api": {"claude_api_key": "sk-test-key"}}
        config_file = temp_dir / "config.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f)

        manager = ConfigManager(str(config_file), str(temp_dir / "user.yaml"))
        assert manager.has_valid_api_key() is True

    def test_has_valid_api_key_false(self, temp_dir):
        """测试检测到无有效API密钥"""
        config = {"api": {
            "claude_api_key": "",
            "gemini_api_key": "",
            "deepseek_api_key": "",
            "kimi_api_key": ""
        }}
        config_file = temp_dir / "config.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f)

        manager = ConfigManager(str(config_file), str(temp_dir / "user.yaml"))
        assert manager.has_valid_api_key() is False

    def test_get_all_config(self, temp_dir, sample_system_config):
        """测试获取完整配置"""
        config_file = temp_dir / "config.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(sample_system_config, f)

        manager = ConfigManager(str(config_file), str(temp_dir / "user.yaml"))
        all_config = manager.get_all_config()

        assert isinstance(all_config, dict)
        assert "api" in all_config
        assert "analysis" in all_config
        assert "ui" in all_config

        # 验证返回的是副本
        all_config["new_key"] = "new_value"
        assert "new_key" not in manager.config

    def test_config_priority(self, temp_dir):
        """测试配置优先级：用户配置 > 环境变量 > 系统配置"""
        os.environ["TEST_KEY"] = "env_value"

        system_config = {"key1": "system_value", "key2": "${TEST_KEY}"}
        user_config = {"key1": "user_value"}

        config_file = temp_dir / "config.yaml"
        user_config_file = temp_dir / "user_config.yaml"

        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(system_config, f)
        with open(user_config_file, 'w', encoding='utf-8') as f:
            yaml.dump(user_config, f)

        manager = ConfigManager(str(config_file), str(user_config_file))

        # 用户配置覆盖系统配置
        assert manager.get("key1") == "user_value"
        # 环境变量替换
        assert manager.get("key2") == "env_value"

        del os.environ["TEST_KEY"]

    def test_empty_config_files(self, temp_dir):
        """测试空配置文件"""
        config_file = temp_dir / "config.yaml"
        user_config_file = temp_dir / "user_config.yaml"

        config_file.write_text("", encoding="utf-8")
        user_config_file.write_text("", encoding="utf-8")

        manager = ConfigManager(str(config_file), str(user_config_file))

        assert manager.config == {}
        assert manager.get("any.key", "default") == "default"

    def test_malformed_yaml_handling(self, temp_dir):
        """测试处理格式错误的YAML文件"""
        config_file = temp_dir / "config.yaml"
        config_file.write_text("invalid: yaml: content: [unclosed", encoding="utf-8")

        manager = ConfigManager(str(config_file), str(temp_dir / "user.yaml"))

        # 应该返回空配置而不是崩溃
        assert manager.config == {}
