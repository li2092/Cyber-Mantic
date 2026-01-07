"""
配置管理器 - 统一管理配置加载、保存和环境变量处理
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_file: str = "config.yaml", user_config_file: str = "user_config.yaml"):
        """
        初始化配置管理器

        Args:
            config_file: 系统配置文件路径
            user_config_file: 用户配置文件路径（存储用户在GUI中设置的配置）
        """
        self.config_file = Path(config_file)
        self.user_config_file = Path(user_config_file)

        # 加载 .env 文件
        self._load_env()

        # 加载配置
        self.config = self._load_config()

    def _load_env(self):
        """加载环境变量文件"""
        env_path = Path(".env")
        if env_path.exists():
            load_dotenv(env_path)

    def _load_config(self) -> Dict[str, Any]:
        """
        加载完整配置（系统配置 + 用户配置 + 环境变量）

        优先级：用户配置 > 环境变量 > 系统配置

        Returns:
            完整配置字典
        """
        # 1. 加载系统配置
        config = self._load_yaml_file(self.config_file)

        # 2. 替换环境变量引用
        config = self._replace_env_vars(config)

        # 3. 加载用户配置（覆盖系统配置）
        user_config = self._load_yaml_file(self.user_config_file)
        config = self._deep_merge(config, user_config)

        return config

    def _load_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        """加载 YAML 文件"""
        if not file_path.exists():
            return {}

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                return data if data else {}
        except Exception as e:
            print(f"加载配置文件 {file_path} 失败: {e}")
            return {}

    def _replace_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        递归替换配置中的环境变量引用

        支持格式: ${ENV_VAR_NAME}
        """
        if not isinstance(config, dict):
            return config

        result = {}
        for key, value in config.items():
            if isinstance(value, dict):
                result[key] = self._replace_env_vars(value)
            elif isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                env_var = value[2:-1]
                result[key] = os.getenv(env_var, '')
            else:
                result[key] = value

        return result

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        深度合并两个字典

        Args:
            base: 基础字典
            override: 覆盖字典

        Returns:
            合并后的字典
        """
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def get(self, path: str, default: Any = None) -> Any:
        """
        获取配置值（支持点号路径）

        Args:
            path: 配置路径，如 "api.claude_api_key"
            default: 默认值

        Returns:
            配置值

        Examples:
            >>> manager.get("api.claude_api_key")
            "sk-ant-..."
            >>> manager.get("analysis.max_theories", 5)
            5
        """
        keys = path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set(self, path: str, value: Any):
        """
        设置配置值（仅在内存中）

        Args:
            path: 配置路径，如 "api.claude_api_key"
            value: 配置值
        """
        keys = path.split('.')
        target = self.config

        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]

        target[keys[-1]] = value

    def save_user_config(self, config_data: Dict[str, Any]):
        """
        保存用户配置到 user_config.yaml

        Args:
            config_data: 要保存的配置数据
        """
        try:
            # 读取现有用户配置
            existing = self._load_yaml_file(self.user_config_file)

            # 合并配置
            merged = self._deep_merge(existing, config_data)

            # 保存到文件
            with open(self.user_config_file, 'w', encoding='utf-8') as f:
                yaml.dump(merged, f, allow_unicode=True, default_flow_style=False, indent=2)

            # 重新加载配置
            self.config = self._load_config()

            return True
        except Exception as e:
            print(f"保存用户配置失败: {e}")
            return False

    def get_api_keys(self) -> Dict[str, str]:
        """
        获取所有 API 密钥

        Returns:
            API 密钥字典 {"claude": "sk-...", "gemini": "...", ...}
        """
        api_config = self.config.get('api', {})
        return {
            'claude': api_config.get('claude_api_key', ''),
            'gemini': api_config.get('gemini_api_key', ''),
            'deepseek': api_config.get('deepseek_api_key', ''),
            'kimi': api_config.get('kimi_api_key', ''),
            'amap': os.getenv('AMAP_API_KEY', '')  # 地图API单独从环境变量读取
        }

    def has_valid_api_key(self) -> bool:
        """检查是否至少有一个有效的 API 密钥"""
        api_keys = self.get_api_keys()
        return any(key and len(key) > 0 for key in [
            api_keys['claude'],
            api_keys['gemini'],
            api_keys['deepseek'],
            api_keys['kimi']
        ])

    def get_all_config(self) -> Dict[str, Any]:
        """获取完整配置"""
        return self.config.copy()

    # ===== 免责声明相关方法 =====

    def is_disclaimer_accepted(self) -> bool:
        """
        检查用户是否已接受免责声明

        Returns:
            bool: 是否已接受
        """
        return self.get('user.disclaimer_accepted', False)

    def set_disclaimer_accepted(self, accepted: bool = True):
        """
        设置免责声明接受状态

        Args:
            accepted: 是否接受
        """
        from datetime import datetime
        config_data = {
            'user': {
                'disclaimer_accepted': accepted,
                'disclaimer_accepted_at': datetime.now().isoformat() if accepted else None
            }
        }
        self.save_user_config(config_data)

    def get_disclaimer_accepted_time(self) -> Optional[str]:
        """
        获取免责声明接受时间

        Returns:
            Optional[str]: 接受时间的ISO格式字符串
        """
        return self.get('user.disclaimer_accepted_at', None)

    # ===== 首次引导相关方法 =====

    def is_onboarding_completed(self) -> bool:
        """
        检查用户是否已完成首次引导

        Returns:
            bool: 是否已完成
        """
        return self.get('user.onboarding_completed', False)

    def set_onboarding_completed(self, completed: bool = True):
        """
        设置首次引导完成状态

        Args:
            completed: 是否完成
        """
        from datetime import datetime
        config_data = {
            'user': {
                'onboarding_completed': completed,
                'onboarding_completed_at': datetime.now().isoformat() if completed else None
            }
        }
        self.save_user_config(config_data)


# 全局配置管理器实例
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """获取全局配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def reload_config():
    """重新加载配置"""
    global _config_manager
    _config_manager = ConfigManager()
    return _config_manager
