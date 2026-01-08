"""
TaskRouter - API任务路由器

V2核心组件：实现环节级API配置
- 支持每个AI调用环节独立配置API
- 支持全局配置和环节覆盖
- 支持配置持久化
"""

import json
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from enum import Enum
from utils.logger import get_logger


class TaskType(Enum):
    """任务类型枚举"""
    COMPREHENSIVE_REPORT = "综合报告解读"
    SINGLE_THEORY = "单理论解读"
    QUICK_INTERACTION = "快速交互问答"
    QUICK_INTERPRETATION = "快速解读"
    SIMPLE_QA = "简单问题解答"
    BIRTH_INFO_PARSE = "出生信息解析"
    CONFLICT_RESOLUTION = "冲突解决分析"
    USER_FEEDBACK = "用户反馈处理"
    VERIFICATION_GEN = "回溯验证生成"


@dataclass
class APIConfig:
    """单个API配置"""
    api_name: str
    model: str
    enabled: bool = True
    priority: int = 0
    max_tokens: int = 4096
    temperature: float = 0.7


@dataclass
class TaskConfig:
    """单个任务的API配置"""
    task_type: str
    api: Optional[str] = None  # None表示使用全局配置
    model: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskConfig":
        return cls(**data)


@dataclass
class GlobalAPIConfig:
    """全局API配置"""
    primary: str = "claude"
    fallback_order: List[str] = field(default_factory=lambda: ["deepseek", "kimi", "gemini"])
    enable_dual_verification: bool = True
    timeout: int = 60
    max_retries: int = 3


# 支持的API厂商配置
SUPPORTED_APIS = {
    "claude": {
        "vendor": "Anthropic",
        "models": ["claude-3-opus-latest", "claude-sonnet-4-20250514", "claude-3-haiku-20240307"],
        "default_model": "claude-sonnet-4-20250514"
    },
    "deepseek": {
        "vendor": "DeepSeek",
        "models": ["deepseek-chat", "deepseek-reasoner"],
        "default_model": "deepseek-reasoner"
    },
    "kimi": {
        "vendor": "Moonshot",
        "models": ["kimi-k2", "kimi-k2-turbo", "kimi-k2-turbo-preview"],
        "default_model": "kimi-k2-turbo"
    },
    "gemini": {
        "vendor": "Google",
        "models": ["gemini-pro", "gemini-2.0-flash-exp"],
        "default_model": "gemini-2.0-flash-exp"
    },
    "qwen": {
        "vendor": "阿里通义",
        "models": ["qwen-max", "qwen-plus", "qwen-turbo"],
        "default_model": "qwen-plus"
    },
    "doubao": {
        "vendor": "字节豆包",
        "models": ["doubao-pro-32k", "doubao-pro-128k", "doubao-lite-32k"],
        "default_model": "doubao-pro-32k"
    },
    "baichuan": {
        "vendor": "百川",
        "models": ["Baichuan4", "Baichuan3-Turbo", "Baichuan3-Turbo-128k"],
        "default_model": "Baichuan3-Turbo"
    },
    "glm": {
        "vendor": "智谱清言",
        "models": ["glm-4-plus", "glm-4", "glm-4-flash"],
        "default_model": "glm-4-flash"
    },
    "openrouter": {
        "vendor": "OpenRouter",
        "models": [
            "anthropic/claude-3.5-sonnet",
            "anthropic/claude-3-opus",
            "openai/gpt-4-turbo",
            "openai/gpt-4o",
            "meta-llama/llama-3.1-405b-instruct",
            "meta-llama/llama-3.1-70b-instruct",
            "mistralai/mistral-large",
            "google/gemini-pro-1.5",
            "deepseek/deepseek-r1"
        ],
        "default_model": "anthropic/claude-3.5-sonnet"
    }
}

# 默认任务配置
DEFAULT_TASK_CONFIG = {
    TaskType.COMPREHENSIVE_REPORT.value: {
        "api": "claude",
        "model": "claude-3-opus-latest",
        "max_tokens": 8192,
        "temperature": 0.7
    },
    TaskType.SINGLE_THEORY.value: {
        "api": None,  # 使用全局配置
        "model": None,
        "max_tokens": 4096,
        "temperature": 0.7
    },
    TaskType.QUICK_INTERACTION.value: {
        "api": "deepseek",
        "model": "deepseek-chat",
        "max_tokens": 2048,
        "temperature": 0.8
    },
    TaskType.BIRTH_INFO_PARSE.value: {
        "api": "kimi",
        "model": "kimi-k2-turbo-preview",
        "max_tokens": 2048,
        "temperature": 0.5
    },
    TaskType.CONFLICT_RESOLUTION.value: {
        "api": "deepseek",
        "model": "deepseek-reasoner",
        "max_tokens": 4096,
        "temperature": 0.6
    },
    TaskType.VERIFICATION_GEN.value: {
        "api": "gemini",
        "model": "gemini-2.0-flash-exp",
        "max_tokens": 2048,
        "temperature": 0.7
    }
}


class TaskRouter:
    """API任务路由器"""

    CONFIG_FILE = "api_task_config.json"

    def __init__(self, config_dir: Optional[str] = None):
        """
        初始化任务路由器

        Args:
            config_dir: 配置文件目录，默认使用用户配置目录
        """
        self.logger = get_logger(__name__)

        # 配置目录
        if config_dir:
            self.config_dir = config_dir
        else:
            # 默认使用用户配置目录
            home = os.path.expanduser("~")
            self.config_dir = os.path.join(home, ".cyber_mantic")

        os.makedirs(self.config_dir, exist_ok=True)
        self.config_path = os.path.join(self.config_dir, self.CONFIG_FILE)

        # 初始化配置
        self.global_config = GlobalAPIConfig()
        self.task_configs: Dict[str, TaskConfig] = {}

        # 加载配置
        self._load_config()

    def _load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # 加载全局配置
                global_data = data.get("global", {})
                self.global_config = GlobalAPIConfig(
                    primary=global_data.get("primary", "claude"),
                    fallback_order=global_data.get("fallback_order", ["deepseek", "kimi", "gemini"]),
                    enable_dual_verification=global_data.get("enable_dual_verification", True),
                    timeout=global_data.get("timeout", 60),
                    max_retries=global_data.get("max_retries", 3)
                )

                # 加载任务配置
                task_overrides = data.get("task_overrides", {})
                for task_type, config in task_overrides.items():
                    if config:
                        self.task_configs[task_type] = TaskConfig(
                            task_type=task_type,
                            api=config.get("api"),
                            model=config.get("model"),
                            max_tokens=config.get("max_tokens", 4096),
                            temperature=config.get("temperature", 0.7)
                        )

                self.logger.info(f"已加载API任务配置: {self.config_path}")

            except Exception as e:
                self.logger.warning(f"加载配置文件失败: {e}，使用默认配置")
                self._use_default_config()
        else:
            self.logger.info("配置文件不存在，使用默认配置")
            self._use_default_config()

    def _use_default_config(self):
        """使用默认配置"""
        for task_type, config in DEFAULT_TASK_CONFIG.items():
            self.task_configs[task_type] = TaskConfig(
                task_type=task_type,
                api=config.get("api"),
                model=config.get("model"),
                max_tokens=config.get("max_tokens", 4096),
                temperature=config.get("temperature", 0.7)
            )

    def save_config(self):
        """保存配置到文件"""
        try:
            data = {
                "global": {
                    "primary": self.global_config.primary,
                    "fallback_order": self.global_config.fallback_order,
                    "enable_dual_verification": self.global_config.enable_dual_verification,
                    "timeout": self.global_config.timeout,
                    "max_retries": self.global_config.max_retries
                },
                "task_overrides": {
                    task_type: config.to_dict() if config else None
                    for task_type, config in self.task_configs.items()
                }
            }

            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            self.logger.info(f"已保存API任务配置: {self.config_path}")
            return True

        except Exception as e:
            self.logger.error(f"保存配置文件失败: {e}")
            return False

    def get_config_for_task(self, task_type: str) -> Dict[str, Any]:
        """
        获取指定任务的API配置

        Args:
            task_type: 任务类型

        Returns:
            配置字典 {api, model, max_tokens, temperature}
        """
        # 查找任务配置
        task_config = self.task_configs.get(task_type)

        if task_config and task_config.api:
            # 使用任务特定配置
            return {
                "api": task_config.api,
                "model": task_config.model or self._get_default_model(task_config.api),
                "max_tokens": task_config.max_tokens,
                "temperature": task_config.temperature
            }
        else:
            # 使用全局配置
            return {
                "api": self.global_config.primary,
                "model": self._get_default_model(self.global_config.primary),
                "max_tokens": task_config.max_tokens if task_config else 4096,
                "temperature": task_config.temperature if task_config else 0.7
            }

    def _get_default_model(self, api_name: str) -> str:
        """获取API的默认模型"""
        api_info = SUPPORTED_APIS.get(api_name, {})
        return api_info.get("default_model", "")

    def set_task_config(
        self,
        task_type: str,
        api: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ):
        """
        设置任务配置

        Args:
            task_type: 任务类型
            api: API名称（None表示使用全局）
            model: 模型名称
            max_tokens: 最大token数
            temperature: 温度参数
        """
        existing = self.task_configs.get(task_type)

        if existing:
            if api is not None:
                existing.api = api
            if model is not None:
                existing.model = model
            if max_tokens is not None:
                existing.max_tokens = max_tokens
            if temperature is not None:
                existing.temperature = temperature
        else:
            self.task_configs[task_type] = TaskConfig(
                task_type=task_type,
                api=api,
                model=model,
                max_tokens=max_tokens or 4096,
                temperature=temperature or 0.7
            )

    def set_global_config(
        self,
        primary: Optional[str] = None,
        fallback_order: Optional[List[str]] = None,
        enable_dual_verification: Optional[bool] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None
    ):
        """
        设置全局配置

        Args:
            primary: 主API
            fallback_order: 备选API顺序
            enable_dual_verification: 是否启用双模型验证
            timeout: 超时时间
            max_retries: 最大重试次数
        """
        if primary is not None:
            self.global_config.primary = primary
        if fallback_order is not None:
            self.global_config.fallback_order = fallback_order
        if enable_dual_verification is not None:
            self.global_config.enable_dual_verification = enable_dual_verification
        if timeout is not None:
            self.global_config.timeout = timeout
        if max_retries is not None:
            self.global_config.max_retries = max_retries

    def get_supported_apis(self) -> Dict[str, Dict[str, Any]]:
        """获取支持的API列表"""
        return SUPPORTED_APIS.copy()

    def get_all_task_types(self) -> List[str]:
        """获取所有任务类型"""
        return [t.value for t in TaskType]

    def reset_to_default(self):
        """重置为默认配置"""
        self.global_config = GlobalAPIConfig()
        self._use_default_config()
        self.save_config()


# 单例实例
_router_instance: Optional[TaskRouter] = None


def get_task_router(config_dir: Optional[str] = None) -> TaskRouter:
    """获取任务路由器单例"""
    global _router_instance
    if _router_instance is None:
        _router_instance = TaskRouter(config_dir)
    return _router_instance
