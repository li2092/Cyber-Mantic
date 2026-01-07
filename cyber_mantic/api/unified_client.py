"""
统一AI客户端

支持多种AI接口类型的统一封装，实现故障转移和降级机制

设计参考：docs/design/07_AI接口设计.md
"""
import asyncio
import random
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from utils.logger import get_logger, log_api_call, log_performance
from .models import AIEndpoint, EndpointType, TaskType, AIEndpointConfig, PRESET_ENDPOINTS


# 重试配置
INITIAL_RETRY_DELAY = 1.0
MAX_RETRY_DELAY = 32.0
RETRY_JITTER = 0.5


def calculate_retry_delay(attempt: int) -> float:
    """计算指数退避延迟"""
    delay = min(INITIAL_RETRY_DELAY * (2 ** attempt), MAX_RETRY_DELAY)
    jitter = delay * RETRY_JITTER * (2 * random.random() - 1)
    return max(0.1, delay + jitter)


@dataclass
class DegradedResponse:
    """降级响应"""
    message: str
    is_degraded: bool = True
    suggestion: str = ""


class UnifiedAIClient:
    """
    统一AI客户端

    支持：
    - OpenAI兼容接口
    - Anthropic接口
    - 自动故障转移
    - 降级模式
    """

    def __init__(self, endpoint: AIEndpoint):
        """
        初始化统一客户端

        Args:
            endpoint: AI接口配置
        """
        self.endpoint = endpoint
        self.logger = get_logger(__name__)
        self._client = None

    async def _get_client(self):
        """懒加载客户端"""
        if self._client is not None:
            return self._client

        if self.endpoint.type == EndpointType.OPENAI:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(
                    base_url=self.endpoint.base_url,
                    api_key=self.endpoint.api_key or "not-needed",
                    timeout=self.endpoint.timeout
                )
            except ImportError:
                raise ImportError("需要安装openai库: pip install openai")

        elif self.endpoint.type == EndpointType.ANTHROPIC:
            try:
                from anthropic import AsyncAnthropic
                self._client = AsyncAnthropic(
                    api_key=self.endpoint.api_key,
                    timeout=self.endpoint.timeout
                )
            except ImportError:
                raise ImportError("需要安装anthropic库: pip install anthropic")

        return self._client

    async def chat(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        统一的对话接口

        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            system: 系统提示词
            **kwargs: 其他参数

        Returns:
            AI响应文本
        """
        max_tokens = kwargs.get("max_tokens", self.endpoint.max_tokens)
        temperature = kwargs.get("temperature", self.endpoint.temperature)

        self.logger.info(f"调用 {self.endpoint.name} - 模型: {self.endpoint.model}")
        start_time = time.time()

        try:
            if self.endpoint.type == EndpointType.OPENAI:
                response = await self._chat_openai(messages, system, max_tokens, temperature)
            elif self.endpoint.type == EndpointType.ANTHROPIC:
                response = await self._chat_anthropic(messages, system, max_tokens, temperature)
            else:
                raise ValueError(f"不支持的接口类型: {self.endpoint.type}")

            duration = time.time() - start_time
            log_api_call(
                api_name=self.endpoint.id,
                endpoint=self.endpoint.model,
                request_data={"messages_count": len(messages)},
                response_data={"response_length": len(response)},
                error=None,
                duration=duration
            )

            return response

        except Exception as e:
            duration = time.time() - start_time
            log_api_call(
                api_name=self.endpoint.id,
                endpoint=self.endpoint.model,
                request_data={"messages_count": len(messages)},
                response_data=None,
                error=str(e),
                duration=duration
            )
            raise

    async def _chat_openai(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str],
        max_tokens: int,
        temperature: float
    ) -> str:
        """OpenAI兼容接口调用"""
        client = await self._get_client()

        # 构建消息列表
        full_messages = []
        if system:
            full_messages.append({"role": "system", "content": system})
        full_messages.extend(messages)

        response = await client.chat.completions.create(
            model=self.endpoint.model,
            messages=full_messages,
            max_tokens=max_tokens,
            temperature=temperature
        )

        return response.choices[0].message.content

    async def _chat_anthropic(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str],
        max_tokens: int,
        temperature: float
    ) -> str:
        """Anthropic接口调用"""
        client = await self._get_client()

        response = await client.messages.create(
            model=self.endpoint.model,
            messages=messages,
            system=system or "",
            max_tokens=max_tokens
        )

        return response.content[0].text

    async def list_models(self) -> List[str]:
        """获取可用模型列表（仅OpenAI兼容接口支持）"""
        if self.endpoint.type != EndpointType.OPENAI:
            return [self.endpoint.model]

        try:
            client = await self._get_client()
            models = await client.models.list()
            return [m.id for m in models.data]
        except Exception as e:
            self.logger.warning(f"获取模型列表失败: {e}")
            return []

    async def test_connection(self) -> Tuple[bool, str]:
        """
        测试接口连接

        Returns:
            (是否成功, 消息)
        """
        try:
            response = await self.chat(
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            return True, "连接成功"
        except Exception as e:
            return False, str(e)


class AIClientManager:
    """
    AI客户端管理器

    管理多个AI接口，实现故障转移
    """

    def __init__(self, config: AIEndpointConfig):
        """
        初始化客户端管理器

        Args:
            config: AI接口配置
        """
        self.config = config
        self.logger = get_logger(__name__)
        self._clients: Dict[str, UnifiedAIClient] = {}
        self.max_retries = 3

    def _get_client(self, endpoint_id: str) -> Optional[UnifiedAIClient]:
        """获取或创建客户端"""
        if endpoint_id in self._clients:
            return self._clients[endpoint_id]

        endpoint = self.config.get_endpoint(endpoint_id)
        if endpoint is None:
            return None

        client = UnifiedAIClient(endpoint)
        self._clients[endpoint_id] = client
        return client

    async def call(
        self,
        task_type: TaskType,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        调用AI接口（带故障转移）

        Args:
            task_type: 任务类型
            messages: 消息列表
            system: 系统提示词
            **kwargs: 其他参数

        Returns:
            AI响应文本
        """
        # 获取主接口
        primary_endpoint = self.config.get_endpoint_for_task(task_type)
        if primary_endpoint is None:
            raise ValueError(f"没有为任务类型 {task_type} 配置接口")

        # 构建故障转移列表
        fallback_ids = [primary_endpoint.id] + [
            eid for eid in self.config.fallback_order
            if eid != primary_endpoint.id
        ]

        last_error = None
        for endpoint_id in fallback_ids:
            client = self._get_client(endpoint_id)
            if client is None:
                continue

            # 对每个接口进行重试
            for attempt in range(self.max_retries):
                try:
                    if attempt > 0:
                        delay = calculate_retry_delay(attempt - 1)
                        self.logger.info(f"{endpoint_id} 重试 {attempt}/{self.max_retries}，等待 {delay:.2f}秒...")
                        await asyncio.sleep(delay)

                    return await client.chat(messages, system, **kwargs)

                except Exception as e:
                    last_error = e
                    if self._is_retryable_error(e):
                        self.logger.warning(f"{endpoint_id} 调用失败（可重试）: {e}")
                    else:
                        self.logger.warning(f"{endpoint_id} 调用失败: {e}")
                        break

        # 所有接口都失败，返回降级响应
        self.logger.error(f"所有接口调用失败，最后错误: {last_error}")
        raise Exception(f"所有AI接口调用失败: {last_error}")

    def _is_retryable_error(self, error: Exception) -> bool:
        """判断错误是否可重试"""
        error_str = str(error).lower()
        retryable_patterns = [
            'timeout', 'timed out', 'rate limit', 'rate_limit',
            'too many requests', '429', 'connection', 'network',
            'temporary', 'unavailable', '500', '502', '503', '504'
        ]
        return any(pattern in error_str for pattern in retryable_patterns)

    async def call_with_prompt(
        self,
        task_type: TaskType,
        prompt: str,
        system: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        便捷方法：使用单个prompt调用

        Args:
            task_type: 任务类型
            prompt: 用户提示词
            system: 系统提示词
            **kwargs: 其他参数

        Returns:
            AI响应文本
        """
        messages = [{"role": "user", "content": prompt}]
        return await self.call(task_type, messages, system, **kwargs)

    def get_degraded_response(self, task_type: TaskType) -> DegradedResponse:
        """
        获取降级响应

        Args:
            task_type: 任务类型

        Returns:
            降级响应对象
        """
        suggestions = {
            TaskType.WENDAO: "请检查网络连接和API配置后重试",
            TaskType.TUIYAN: "已为您生成基础排盘结果，AI解读暂不可用",
            TaskType.REPORT: "报告生成服务暂不可用，请稍后重试",
            TaskType.PROFILE: "画像分析服务暂不可用",
            TaskType.LIBRARY: "典籍问答服务暂不可用",
            TaskType.CONFLICT: "冲突解决服务暂不可用"
        }

        return DegradedResponse(
            message="AI服务暂时不可用",
            is_degraded=True,
            suggestion=suggestions.get(task_type, "请检查网络连接后重试")
        )


def create_client_manager_from_config(config: Dict[str, Any]) -> AIClientManager:
    """
    从配置字典创建客户端管理器

    Args:
        config: 配置字典

    Returns:
        AIClientManager实例
    """
    # 初始化预设接口
    presets = {}
    for preset_id, preset_config in config.get("presets", {}).items():
        if preset_id in PRESET_ENDPOINTS:
            endpoint = PRESET_ENDPOINTS[preset_id]
            # 更新配置
            if preset_config.get("api_key"):
                endpoint.api_key = preset_config["api_key"]
            if preset_config.get("model"):
                endpoint.model = preset_config["model"]
            endpoint.enabled = preset_config.get("enabled", True)
            presets[preset_id] = endpoint

    # 初始化自定义接口
    custom = []
    for custom_config in config.get("custom", []):
        custom.append(AIEndpoint.from_dict(custom_config))

    # 初始化路由配置
    routing = AIRoutingConfig.from_dict(config.get("routing", {}))

    # 创建完整配置
    endpoint_config = AIEndpointConfig(
        presets=presets,
        custom=custom,
        routing=routing,
        fallback_order=config.get("fallback", ["claude", "deepseek", "gemini", "kimi"])
    )

    return AIClientManager(endpoint_config)
