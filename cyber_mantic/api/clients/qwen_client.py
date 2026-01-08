"""
QwenClient - 阿里通义千问API客户端

支持模型：
- qwen-max: 最强模型，适合复杂任务
- qwen-plus: 均衡模型，性价比高
- qwen-turbo: 快速模型，适合简单任务

API文档: https://help.aliyun.com/document_detail/611472.html
"""

import asyncio
from typing import Dict, Any, Optional
from utils.logger import get_logger


class QwenClient:
    """通义千问API客户端"""

    # 可用模型
    MODELS = {
        "qwen-max": "qwen-max",
        "qwen-max-latest": "qwen-max-latest",
        "qwen-plus": "qwen-plus",
        "qwen-plus-latest": "qwen-plus-latest",
        "qwen-turbo": "qwen-turbo",
        "qwen-turbo-latest": "qwen-turbo-latest",
    }

    # 默认配置
    DEFAULT_MODEL = "qwen-plus"
    BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        timeout: int = 60
    ):
        """
        初始化通义千问客户端

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

        self.logger.info(f"Qwen API调用 - 模型: {self.model}")

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

        self.logger.info(f"Qwen 流式API调用 - 模型: {self.model}")

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
