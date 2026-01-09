"""
BaichuanClient - 百川API客户端

支持模型：
- Baichuan4: 最新一代模型
- Baichuan3-Turbo: 快速版
- Baichuan3-Turbo-128k: 长上下文版

API文档: https://platform.baichuan-ai.com/docs/api
"""

import asyncio
from typing import Dict, Any, Optional
from utils.logger import get_logger


class BaichuanClient:
    """百川API客户端"""

    # 可用模型
    MODELS = {
        "Baichuan4": "Baichuan4",
        "Baichuan4-Air": "Baichuan4-Air",
        "Baichuan3-Turbo": "Baichuan3-Turbo",
        "Baichuan3-Turbo-128k": "Baichuan3-Turbo-128k",
    }

    # 默认配置
    DEFAULT_MODEL = "Baichuan3-Turbo"
    BASE_URL = "https://api.baichuan-ai.com/v1"

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        timeout: int = 60
    ):
        """
        初始化百川客户端

        Args:
            api_key: API密钥
            model: 模型名称
            timeout: 超时时间（秒）
        """
        self.api_key = api_key
        self.model = model if model in self.MODELS else self.DEFAULT_MODEL
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

        self.logger.info(f"百川 API调用 - 模型: {self.model}")

        # 异步包装同步调用
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model=self.model,
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

        self.logger.info(f"百川 流式API调用 - 模型: {self.model}")

        response = client.chat.completions.create(
            model=self.model,
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
