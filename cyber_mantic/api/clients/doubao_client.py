"""
DoubaoClient - 字节豆包API客户端

支持模型：
- doubao-pro-32k: 专业版，32K上下文
- doubao-pro-128k: 专业版，128K上下文
- doubao-lite-32k: 轻量版，32K上下文

API文档: https://www.volcengine.com/docs/82379/1099455
"""

import asyncio
from typing import Dict, Any, Optional
from utils.logger import get_logger


class DoubaoClient:
    """字节豆包API客户端"""

    # 可用模型（需要在火山引擎创建推理接入点后获取endpoint_id）
    MODELS = {
        "doubao-pro-32k": "doubao-pro-32k",
        "doubao-pro-128k": "doubao-pro-128k",
        "doubao-lite-32k": "doubao-lite-32k",
        "doubao-lite-128k": "doubao-lite-128k",
    }

    # 默认配置
    DEFAULT_MODEL = "doubao-pro-32k"
    BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        endpoint_id: Optional[str] = None,
        timeout: int = 60
    ):
        """
        初始化豆包客户端

        Args:
            api_key: API密钥（火山引擎API Key）
            model: 模型名称
            endpoint_id: 推理接入点ID（可选，若提供则使用接入点）
            timeout: 超时时间（秒）
        """
        self.api_key = api_key
        self.model = model if model in self.MODELS else self.DEFAULT_MODEL
        self.endpoint_id = endpoint_id
        self.timeout = timeout
        self.logger = get_logger(__name__)

    async def chat(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        发送聊天请求

        Args:
            prompt: 用户消息
            system_prompt: 系统提示词
            max_tokens: 最大输出token数
            temperature: 温度参数
            **kwargs: 其他参数

        Returns:
            AI响应文本
        """
        try:
            import openai
        except ImportError:
            raise ImportError("需要安装openai库: pip install openai")

        client = openai.OpenAI(
            api_key=self.api_key,
            base_url=self.BASE_URL
        )

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # 使用endpoint_id或模型名
        model_to_use = self.endpoint_id if self.endpoint_id else self.model

        self.logger.info(f"豆包 API调用 - 模型: {model_to_use}")

        # 异步包装同步调用
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model=model_to_use,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=self.timeout
            )
        )

        return response.choices[0].message.content

    async def stream_chat(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        on_chunk=None,
        **kwargs
    ):
        """
        流式聊天请求

        Args:
            prompt: 用户消息
            system_prompt: 系统提示词
            max_tokens: 最大输出token数
            temperature: 温度参数
            on_chunk: 流式回调函数
            **kwargs: 其他参数

        Yields:
            AI响应文本块
        """
        try:
            import openai
        except ImportError:
            raise ImportError("需要安装openai库: pip install openai")

        client = openai.OpenAI(
            api_key=self.api_key,
            base_url=self.BASE_URL
        )

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        model_to_use = self.endpoint_id if self.endpoint_id else self.model

        self.logger.info(f"豆包 流式API调用 - 模型: {model_to_use}")

        response = client.chat.completions.create(
            model=model_to_use,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
            timeout=self.timeout
        )

        for chunk in response:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                if on_chunk:
                    on_chunk(content)
                yield content

    def get_available_models(self) -> Dict[str, str]:
        """获取可用模型列表"""
        return self.MODELS.copy()

    def set_model(self, model: str):
        """设置使用的模型"""
        if model in self.MODELS:
            self.model = model
        else:
            self.logger.warning(f"不支持的模型: {model}，使用默认模型: {self.DEFAULT_MODEL}")
            self.model = self.DEFAULT_MODEL

    def set_endpoint_id(self, endpoint_id: str):
        """设置推理接入点ID"""
        self.endpoint_id = endpoint_id
