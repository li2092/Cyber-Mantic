"""
GLMClient - 智谱清言API客户端

支持模型：
- glm-4-plus: 最强版本
- glm-4-0520: 性能均衡
- glm-4-air: 轻量快速
- glm-4-airx: 极速版
- glm-4-flash: 免费版

API文档: https://open.bigmodel.cn/dev/api
"""

import asyncio
from typing import Dict, Any, Optional
from utils.logger import get_logger


class GLMClient:
    """智谱清言API客户端"""

    # 可用模型
    MODELS = {
        "glm-4-plus": "glm-4-plus",
        "glm-4-0520": "glm-4-0520",
        "glm-4-air": "glm-4-air",
        "glm-4-airx": "glm-4-airx",
        "glm-4-flash": "glm-4-flash",
        "glm-4-flashx": "glm-4-flashx",
        "glm-4-long": "glm-4-long",  # 长文本版
        "glm-4": "glm-4",
    }

    # 默认配置
    DEFAULT_MODEL = "glm-4-flash"
    BASE_URL = "https://open.bigmodel.cn/api/paas/v4"

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        timeout: int = 60
    ):
        """
        初始化智谱清言客户端

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

        self.logger.info(f"智谱 API调用 - 模型: {self.model}")

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

        self.logger.info(f"智谱 流式API调用 - 模型: {self.model}")

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
