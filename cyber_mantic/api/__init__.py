"""
赛博玄数 - API集成模块

模块结构：
- manager.py: 旧版API管理器（向后兼容）
- models.py: AI接口数据模型
- unified_client.py: 统一AI客户端（新版）
- prompt_loader.py: Prompt加载器
- prompts.py: Prompt模板（旧版，向后兼容）
- task_router.py: 任务路由器（V2环节级配置）
- clients/: 各厂商API客户端
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
from .task_router import (
    TaskRouter,
    TaskConfig,
    GlobalAPIConfig,
    SUPPORTED_APIS,
    get_task_router
)
from .clients import (
    QwenClient,
    DoubaoClient,
    BaichuanClient,
    GLMClient,
    OpenRouterClient
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
    # 任务路由器（V2）
    'TaskRouter',
    'TaskConfig',
    'GlobalAPIConfig',
    'SUPPORTED_APIS',
    'get_task_router',
    # 新厂商客户端
    'QwenClient',
    'DoubaoClient',
    'BaichuanClient',
    'GLMClient',
    'OpenRouterClient',
]
