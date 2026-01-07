"""
赛博玄数 - API集成模块

模块结构：
- manager.py: 旧版API管理器（向后兼容）
- models.py: AI接口数据模型
- unified_client.py: 统一AI客户端（新版）
- prompt_loader.py: Prompt加载器
- prompts.py: Prompt模板（旧版，向后兼容）
"""
from .manager import APIManager
from .prompts import PromptTemplates
from .prompt_loader import PromptLoader, get_prompt_loader, load_prompt
from .models import (
    AIEndpoint,
    AIRoutingConfig,
    AIEndpointConfig,
    EndpointType,
    TaskType,
    PRESET_ENDPOINTS
)
from .unified_client import (
    UnifiedAIClient,
    AIClientManager,
    DegradedResponse,
    create_client_manager_from_config
)

__all__ = [
    # 旧版（向后兼容）
    'APIManager',
    'PromptTemplates',
    # Prompt加载
    'PromptLoader',
    'get_prompt_loader',
    'load_prompt',
    # 数据模型
    'AIEndpoint',
    'AIRoutingConfig',
    'AIEndpointConfig',
    'EndpointType',
    'TaskType',
    'PRESET_ENDPOINTS',
    # 统一客户端
    'UnifiedAIClient',
    'AIClientManager',
    'DegradedResponse',
    'create_client_manager_from_config',
]
