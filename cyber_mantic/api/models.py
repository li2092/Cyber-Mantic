"""
AI接口数据模型

定义AI接口配置相关的数据类

设计参考：docs/design/07_AI接口设计.md
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, List
from enum import Enum


class EndpointType(Enum):
    """接口类型"""
    OPENAI = "openai"           # OpenAI兼容接口
    ANTHROPIC = "anthropic"     # Anthropic接口
    CUSTOM = "custom"           # 自定义接口


class TaskType(Enum):
    """任务类型（用于接口分配）"""
    WENDAO = "wendao"           # 问道对话
    TUIYAN = "tuiyan"           # 推演分析
    REPORT = "report"           # 报告生成
    PROFILE = "profile"         # 画像分析
    LIBRARY = "library"         # 典籍问答
    CONFLICT = "conflict"       # 冲突解决


@dataclass
class AIEndpoint:
    """
    AI接口配置

    Attributes:
        id: 唯一标识
        name: 显示名称
        type: 接口类型
        base_url: API地址
        api_key: API密钥（加密存储）
        model: 模型名称
        max_tokens: 最大Token数
        temperature: 温度参数
        timeout: 超时秒数
        headers: 自定义Headers
        is_preset: 是否预设接口
        enabled: 是否启用
    """
    id: str
    name: str
    type: EndpointType
    base_url: str
    model: str
    api_key: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: int = 60
    headers: Optional[Dict[str, str]] = None
    is_preset: bool = False
    enabled: bool = True

    def to_dict(self) -> Dict:
        """转换为字典（不包含敏感信息）"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "base_url": self.base_url,
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "timeout": self.timeout,
            "is_preset": self.is_preset,
            "enabled": self.enabled,
            "has_api_key": bool(self.api_key)
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "AIEndpoint":
        """从字典创建"""
        return cls(
            id=data["id"],
            name=data["name"],
            type=EndpointType(data.get("type", "openai")),
            base_url=data["base_url"],
            model=data["model"],
            api_key=data.get("api_key"),
            max_tokens=data.get("max_tokens", 4096),
            temperature=data.get("temperature", 0.7),
            timeout=data.get("timeout", 60),
            headers=data.get("headers"),
            is_preset=data.get("is_preset", False),
            enabled=data.get("enabled", True)
        )


@dataclass
class AIRoutingConfig:
    """
    接口分配配置

    定义不同任务类型使用哪个AI接口

    Attributes:
        wendao: 问道对话使用的接口ID
        tuiyan: 推演分析使用的接口ID
        report: 报告生成使用的接口ID
        profile: 画像分析使用的接口ID
        library: 典籍问答使用的接口ID
        conflict: 冲突解决使用的接口ID
    """
    wendao: str = "deepseek"
    tuiyan: str = "claude"
    report: str = "claude"
    profile: str = "deepseek-reasoner"
    library: str = "deepseek"
    conflict: str = "claude"

    def get_endpoint_for_task(self, task_type: TaskType) -> str:
        """获取指定任务类型对应的接口ID"""
        return getattr(self, task_type.value, "claude")

    def set_endpoint_for_task(self, task_type: TaskType, endpoint_id: str):
        """设置指定任务类型使用的接口"""
        setattr(self, task_type.value, endpoint_id)

    def to_dict(self) -> Dict[str, str]:
        """转换为字典"""
        return {
            "wendao": self.wendao,
            "tuiyan": self.tuiyan,
            "report": self.report,
            "profile": self.profile,
            "library": self.library,
            "conflict": self.conflict
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "AIRoutingConfig":
        """从字典创建"""
        return cls(
            wendao=data.get("wendao", "deepseek"),
            tuiyan=data.get("tuiyan", "claude"),
            report=data.get("report", "claude"),
            profile=data.get("profile", "deepseek-reasoner"),
            library=data.get("library", "deepseek"),
            conflict=data.get("conflict", "claude")
        )


@dataclass
class AIEndpointConfig:
    """
    完整的AI接口配置

    包含预设接口、自定义接口和路由配置
    """
    presets: Dict[str, AIEndpoint] = field(default_factory=dict)
    custom: List[AIEndpoint] = field(default_factory=list)
    routing: AIRoutingConfig = field(default_factory=AIRoutingConfig)
    fallback_order: List[str] = field(default_factory=lambda: ["claude", "deepseek", "gemini", "kimi"])

    def get_endpoint(self, endpoint_id: str) -> Optional[AIEndpoint]:
        """获取指定ID的接口配置"""
        # 先查预设
        if endpoint_id in self.presets:
            return self.presets[endpoint_id]
        # 再查自定义
        for endpoint in self.custom:
            if endpoint.id == endpoint_id:
                return endpoint
        return None

    def get_available_endpoints(self) -> List[AIEndpoint]:
        """获取所有已启用的接口"""
        endpoints = []
        # 预设接口
        for endpoint in self.presets.values():
            if endpoint.enabled and endpoint.api_key:
                endpoints.append(endpoint)
        # 自定义接口
        for endpoint in self.custom:
            if endpoint.enabled:
                endpoints.append(endpoint)
        return endpoints

    def get_endpoint_for_task(self, task_type: TaskType) -> Optional[AIEndpoint]:
        """获取指定任务类型的接口"""
        endpoint_id = self.routing.get_endpoint_for_task(task_type)
        return self.get_endpoint(endpoint_id)

    def add_custom_endpoint(self, endpoint: AIEndpoint):
        """添加自定义接口"""
        # 确保ID唯一
        existing_ids = {e.id for e in self.custom}
        if endpoint.id in existing_ids:
            raise ValueError(f"接口ID已存在: {endpoint.id}")
        self.custom.append(endpoint)

    def remove_custom_endpoint(self, endpoint_id: str) -> bool:
        """移除自定义接口"""
        for i, endpoint in enumerate(self.custom):
            if endpoint.id == endpoint_id:
                self.custom.pop(i)
                return True
        return False


# 预设接口模板
PRESET_ENDPOINTS = {
    "claude": AIEndpoint(
        id="claude",
        name="Claude (Anthropic)",
        type=EndpointType.ANTHROPIC,
        base_url="https://api.anthropic.com",
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        is_preset=True
    ),
    "gemini": AIEndpoint(
        id="gemini",
        name="Gemini (Google)",
        type=EndpointType.CUSTOM,  # Gemini使用自己的SDK
        base_url="https://generativelanguage.googleapis.com",
        model="gemini-2.0-flash-exp",
        max_tokens=4096,
        is_preset=True
    ),
    "deepseek": AIEndpoint(
        id="deepseek",
        name="DeepSeek",
        type=EndpointType.OPENAI,
        base_url="https://api.deepseek.com",
        model="deepseek-chat",
        max_tokens=4096,
        is_preset=True
    ),
    "deepseek-reasoner": AIEndpoint(
        id="deepseek-reasoner",
        name="DeepSeek Reasoner",
        type=EndpointType.OPENAI,
        base_url="https://api.deepseek.com",
        model="deepseek-reasoner",
        max_tokens=8192,
        timeout=120,  # 深度思考需要更多时间
        is_preset=True
    ),
    "kimi": AIEndpoint(
        id="kimi",
        name="Kimi (Moonshot)",
        type=EndpointType.OPENAI,
        base_url="https://api.moonshot.cn/v1",
        model="moonshot-v1-128k",
        max_tokens=4096,
        is_preset=True
    )
}
