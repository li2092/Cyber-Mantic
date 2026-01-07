"""
配置验证器 - 验证应用配置的完整性和正确性
"""
import os
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path


class ConfigValidator:
    """配置验证器"""

    # 必需的配置项
    REQUIRED_CONFIGS = {
        "analysis": {
            "max_theories": int,
            "min_theories": int,
        }
    }

    # 可选配置项及默认值
    OPTIONAL_CONFIGS = {
        "api": {
            "claude_api_key": None,
            "gemini_api_key": None,
            "deepseek_api_key": None,
            "kimi_api_key": None,
            "primary_api": "claude",
            "timeout": 30,
            "max_retries": 3,
            "enable_dual_verification": True,
        },
        "analysis": {
            "enable_quick_feedback": True,
        },
        "ui": {
            "language": "zh_CN",
            "theme": "light",
        },
        "privacy": {
            "auto_delete_after_days": 30,
            "encrypt_local_data": True,
        },
        "logging": {
            "level": "INFO",
            "log_calculations": True,
            "log_to_file": True,
            "log_dir": "logs",
            "max_file_size": "10MB",
            "backup_count": 5,
        }
    }

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """
        验证配置

        Args:
            config: 配置字典

        Returns:
            (是否有效, 错误列表, 警告列表)
        """
        self.errors = []
        self.warnings = []

        # 验证必需配置
        self._validate_required_configs(config)

        # 验证配置值
        self._validate_config_values(config)

        # 验证API密钥
        self._validate_api_keys(config)

        # 验证文件路径
        self._validate_file_paths(config)

        is_valid = len(self.errors) == 0
        return is_valid, self.errors.copy(), self.warnings.copy()

    def _validate_required_configs(self, config: Dict[str, Any]):
        """验证必需配置项"""
        for section, items in self.REQUIRED_CONFIGS.items():
            if section not in config:
                self.errors.append(f"缺少配置节: {section}")
                continue

            section_config = config[section]
            for key, expected_type in items.items():
                if key not in section_config:
                    self.errors.append(f"缺少必需配置: {section}.{key}")
                elif not isinstance(section_config[key], expected_type):
                    self.errors.append(
                        f"配置类型错误: {section}.{key} 应为 {expected_type.__name__}，"
                        f"实际为 {type(section_config[key]).__name__}"
                    )

    def _validate_config_values(self, config: Dict[str, Any]):
        """验证配置值的合理性"""
        # 验证分析配置
        if "analysis" in config:
            analysis = config["analysis"]

            # 验证理论数量
            max_theories = analysis.get("max_theories")
            min_theories = analysis.get("min_theories")

            if max_theories is not None and min_theories is not None:
                if max_theories < min_theories:
                    self.errors.append(
                        f"max_theories ({max_theories}) 不能小于 min_theories ({min_theories})"
                    )

                if min_theories < 1:
                    self.errors.append("min_theories 不能小于 1")

                if max_theories > 10:
                    self.warnings.append("max_theories 过大可能影响性能，建议不超过10")

        # 验证API配置
        if "api" in config:
            api = config["api"]

            # 验证主API选择
            primary_api = api.get("primary_api")
            if primary_api and primary_api not in ["claude", "gemini", "deepseek", "kimi"]:
                self.errors.append(
                    f"primary_api 必须是 'claude', 'gemini', 'deepseek' 或 'kimi'，当前值: {primary_api}"
                )

            # 验证超时时间
            timeout = api.get("timeout")
            if timeout is not None:
                if not isinstance(timeout, (int, float)) or timeout <= 0:
                    self.errors.append("timeout 必须是正数")
                elif timeout < 10:
                    self.warnings.append("timeout 过小可能导致请求失败，建议至少10秒")

            # 验证重试次数
            max_retries = api.get("max_retries")
            if max_retries is not None:
                if not isinstance(max_retries, int) or max_retries < 0:
                    self.errors.append("max_retries 必须是非负整数")
                elif max_retries > 5:
                    self.warnings.append("max_retries 过大可能导致等待时间过长")

        # 验证隐私配置
        if "privacy" in config:
            privacy = config["privacy"]

            # 验证自动删除天数
            auto_delete = privacy.get("auto_delete_after_days")
            if auto_delete is not None:
                if not isinstance(auto_delete, int) or auto_delete < 0:
                    self.errors.append("auto_delete_after_days 必须是非负整数")
                elif auto_delete > 0 and auto_delete < 7:
                    self.warnings.append("auto_delete_after_days 过短可能导致数据过早删除")

        # 验证日志配置
        if "logging" in config:
            logging = config["logging"]

            # 验证日志级别
            level = logging.get("level")
            valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            if level and level not in valid_levels:
                self.errors.append(
                    f"logging.level 必须是以下之一: {', '.join(valid_levels)}，当前值: {level}"
                )

            # 验证备份数量
            backup_count = logging.get("backup_count")
            if backup_count is not None:
                if not isinstance(backup_count, int) or backup_count < 0:
                    self.errors.append("logging.backup_count 必须是非负整数")

    def _validate_api_keys(self, config: Dict[str, Any]):
        """验证API密钥"""
        if "api" not in config:
            return

        api = config["api"]

        # 检查至少有一个API密钥可用
        available_keys = []

        # 验证Claude API密钥
        claude_key = api.get("claude_api_key", "") or os.getenv("CLAUDE_API_KEY", "")
        if claude_key and not claude_key.startswith("${"):
            available_keys.append("claude")
            if claude_key and not claude_key.startswith("sk-ant-"):
                self.warnings.append("claude_api_key 格式可能不正确（通常以 'sk-ant-' 开头）")

        # 验证Gemini API密钥
        gemini_key = api.get("gemini_api_key", "") or os.getenv("GEMINI_API_KEY", "")
        if gemini_key and not gemini_key.startswith("${"):
            available_keys.append("gemini")

        # 验证Deepseek API密钥
        deepseek_key = api.get("deepseek_api_key", "") or os.getenv("DEEPSEEK_API_KEY", "")
        if deepseek_key and not deepseek_key.startswith("${"):
            available_keys.append("deepseek")

        # 验证Kimi API密钥
        kimi_key = api.get("kimi_api_key", "") or os.getenv("KIMI_API_KEY", "")
        if kimi_key and not kimi_key.startswith("${"):
            available_keys.append("kimi")

        # 确保至少有一个API可用
        if not available_keys:
            self.errors.append(
                "至少需要配置一个API密钥（claude/gemini/deepseek/kimi）"
            )
        else:
            self.warnings.append(f"可用的API: {', '.join(available_keys)}")

    def _validate_file_paths(self, config: Dict[str, Any]):
        """验证文件路径"""
        if "logging" not in config:
            return

        logging = config["logging"]

        # 验证日志目录
        log_dir = logging.get("log_dir")
        if log_dir:
            log_path = Path(log_dir)
            if not log_path.exists():
                self.warnings.append(f"日志目录不存在: {log_dir}，将自动创建")

    def apply_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        应用默认配置

        Args:
            config: 原始配置

        Returns:
            应用默认值后的配置
        """
        result = config.copy()

        for section, defaults in self.OPTIONAL_CONFIGS.items():
            if section not in result:
                result[section] = {}

            for key, default_value in defaults.items():
                if key not in result[section]:
                    result[section][key] = default_value

        return result

    def get_validation_summary(
        self,
        is_valid: bool,
        errors: List[str],
        warnings: List[str]
    ) -> str:
        """
        获取验证摘要

        Args:
            is_valid: 是否有效
            errors: 错误列表
            warnings: 警告列表

        Returns:
            摘要文本
        """
        lines = []

        if is_valid:
            lines.append("✓ 配置验证通过")
        else:
            lines.append("✗ 配置验证失败")

        if errors:
            lines.append(f"\n错误 ({len(errors)}):")
            for i, error in enumerate(errors, 1):
                lines.append(f"  {i}. {error}")

        if warnings:
            lines.append(f"\n警告 ({len(warnings)}):")
            for i, warning in enumerate(warnings, 1):
                lines.append(f"  {i}. {warning}")

        if is_valid and not warnings:
            lines.append("配置完整且无警告")

        return "\n".join(lines)


def validate_and_load_config(config: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], str]:
    """
    验证并加载配置

    Args:
        config: 配置字典

    Returns:
        (是否有效, 处理后的配置, 摘要信息)
    """
    validator = ConfigValidator()

    # 应用默认值
    config = validator.apply_defaults(config)

    # 验证配置
    is_valid, errors, warnings = validator.validate_config(config)

    # 生成摘要
    summary = validator.get_validation_summary(is_valid, errors, warnings)

    return is_valid, config, summary
