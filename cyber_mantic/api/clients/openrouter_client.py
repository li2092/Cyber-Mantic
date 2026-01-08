"""
OpenRouterClient - OpenRouter API客户端

OpenRouter是一个统一的API网关，可以访问多种AI模型：
- Claude系列
- GPT系列
- Llama系列
- Mistral系列
- 等等

API文档: https://openrouter.ai/docs
"""

import asyncio
from typing import Dict, Any, Optional, List
from utils.logger import get_logger


class OpenRouterClient:
    """OpenRouter API客户端"""

    # 热门模型列表（可通过API获取完整列表）
    POPULAR_MODELS = {
        # Claude系列
        "anthropic/claude-3.5-sonnet": "Claude 3.5 Sonnet",
        "anthropic/claude-3-opus": "Claude 3 Opus",
        "anthropic/claude-3-haiku": "Claude 3 Haiku",
        # GPT系列
        "openai/gpt-4-turbo": "GPT-4 Turbo",
        "openai/gpt-4o": "GPT-4o",
        "openai/gpt-4o-mini": "GPT-4o Mini",
        # Meta Llama
        "meta-llama/llama-3.1-405b-instruct": "Llama 3.1 405B",
        "meta-llama/llama-3.1-70b-instruct": "Llama 3.1 70B",
        "meta-llama/llama-3.1-8b-instruct": "Llama 3.1 8B",
        # Mistral
        "mistralai/mistral-large": "Mistral Large",
        "mistralai/mistral-medium": "Mistral Medium",
        "mistralai/mixtral-8x7b-instruct": "Mixtral 8x7B",
        # Google
        "google/gemini-pro-1.5": "Gemini Pro 1.5",
        "google/gemini-flash-1.5": "Gemini Flash 1.5",
        # 其他热门模型
        "qwen/qwen-2.5-72b-instruct": "Qwen 2.5 72B",
        "deepseek/deepseek-chat": "DeepSeek Chat",
        "deepseek/deepseek-r1": "DeepSeek R1",
    }

    # 免费模型
    FREE_MODELS = {
        "meta-llama/llama-3.1-8b-instruct:free": "Llama 3.1 8B (Free)",
        "mistralai/mistral-7b-instruct:free": "Mistral 7B (Free)",
        "google/gemma-2-9b-it:free": "Gemma 2 9B (Free)",
    }

    # 默认配置
    DEFAULT_MODEL = "anthropic/claude-3.5-sonnet"
    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        timeout: int = 120,
        site_url: Optional[str] = None,
        site_name: Optional[str] = None
    ):
        """
        初始化OpenRouter客户端

        Args:
            api_key: OpenRouter API密钥
            model: 模型名称（格式：provider/model-name）
            timeout: 超时时间（秒）
            site_url: 你的网站URL（用于统计）
            site_name: 你的网站名称（用于统计）
        """
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.site_url = site_url or "https://github.com/cyber-mantic"
        self.site_name = site_name or "赛博玄数"
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

        self.logger.info(f"OpenRouter API调用 - 模型: {self.model}")

        # 异步包装同步调用
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=self.timeout,
                extra_headers={
                    "HTTP-Referer": self.site_url,
                    "X-Title": self.site_name
                }
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

        self.logger.info(f"OpenRouter 流式API调用 - 模型: {self.model}")

        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
            timeout=self.timeout,
            extra_headers={
                "HTTP-Referer": self.site_url,
                "X-Title": self.site_name
            }
        )

        for chunk in response:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                if on_chunk:
                    on_chunk(content)
                yield content

    def get_available_models(self) -> Dict[str, str]:
        """获取热门模型列表"""
        all_models = {}
        all_models.update(self.POPULAR_MODELS)
        all_models.update(self.FREE_MODELS)
        return all_models

    def get_free_models(self) -> Dict[str, str]:
        """获取免费模型列表"""
        return self.FREE_MODELS.copy()

    def set_model(self, model: str):
        """设置使用的模型"""
        self.model = model
        self.logger.info(f"切换模型为: {model}")

    async def get_model_list(self) -> List[Dict[str, Any]]:
        """
        从API获取完整模型列表

        Returns:
            模型信息列表
        """
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()
                return data.get("data", [])
        except Exception as e:
            self.logger.warning(f"获取模型列表失败: {e}")
            return []

    async def get_generation_stats(self) -> Dict[str, Any]:
        """
        获取API使用统计

        Returns:
            使用统计信息
        """
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/auth/key",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=30
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            self.logger.warning(f"获取使用统计失败: {e}")
            return {}
