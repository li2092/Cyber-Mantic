"""
API管理器 - 支持多提供商和双模型验证

安全特性：
- 指数退避重试策略，避免API过载
- 多API故障转移机制
- 双模型验证提高结果可靠性
"""
import os
import asyncio
import random
from typing import Optional, Dict, Any, List, Tuple
from .prompts import PromptTemplates
from utils.logger import get_logger, log_api_call, log_performance
import time


# 重试配置
INITIAL_RETRY_DELAY = 1.0  # 初始重试延迟（秒）
MAX_RETRY_DELAY = 32.0  # 最大重试延迟（秒）
RETRY_JITTER = 0.5  # 抖动因子（随机化延迟，避免惊群效应）


def calculate_retry_delay(attempt: int, initial_delay: float = INITIAL_RETRY_DELAY) -> float:
    """
    计算指数退避延迟时间

    Args:
        attempt: 当前重试次数（从0开始）
        initial_delay: 初始延迟

    Returns:
        延迟时间（秒），包含随机抖动
    """
    # 指数退避：delay = initial * 2^attempt
    delay = min(initial_delay * (2 ** attempt), MAX_RETRY_DELAY)
    # 添加随机抖动：±50%
    jitter = delay * RETRY_JITTER * (2 * random.random() - 1)
    return max(0.1, delay + jitter)


class APIManager:
    """API管理器，支持多提供商故障转移和双模型验证"""

    # 默认API优先级顺序
    DEFAULT_API_PRIORITY = ["claude", "gemini", "deepseek", "kimi"]

    # 内置API的默认base_url
    BUILTIN_BASE_URLS = {
        "deepseek": "https://api.deepseek.com",
        "kimi": "https://api.moonshot.cn/v1",
    }

    # API使用场景映射
    API_USAGE_MAP = {
        "综合报告解读": "claude",      # 高质量解读
        "单理论解读": "claude",         # 专业解读
        "快速交互问答": "deepseek",     # 快速响应
        "快速解读": "deepseek",         # 快速响应
        "简单问题解答": "deepseek",     # 成本优化
        "出生信息解析": "kimi",         # 自然语言理解，时辰分类
        "冲突解决分析": "claude",       # 复杂推理
        "用户反馈处理": "deepseek",     # 快速响应
    }

    def __init__(self, config: Dict[str, Any]):
        """
        初始化API管理器

        Args:
            config: 配置字典，包含API密钥等信息 (扁平格式)
                   例如: claude_api_key, claude_model, openrouter_api_key 等
        """
        self.logger = get_logger()
        self.config = config

        # 从配置动态发现所有已配置的API
        self.api_keys = {}
        self.models = {}
        self.base_urls = {}

        # 1. 先加载内置的API (claude, gemini, deepseek, kimi)
        builtin_apis = ["claude", "gemini", "deepseek", "kimi"]
        for api in builtin_apis:
            api_key = config.get(f"{api}_api_key") or os.getenv(f"{api.upper()}_API_KEY")
            if api_key:
                self.api_keys[api] = api_key
                self.models[api] = config.get(f"{api}_model", self._get_default_model(api))
                self.base_urls[api] = config.get(f"{api}_base_url", self.BUILTIN_BASE_URLS.get(api, ""))

        # 2. 动态发现自定义API (如 openrouter, together 等)
        for key in config.keys():
            if key.endswith("_api_key") and config.get(key):
                provider = key.replace("_api_key", "")
                if provider not in builtin_apis:
                    self.api_keys[provider] = config.get(key)
                    self.models[provider] = config.get(f"{provider}_model", "")
                    self.base_urls[provider] = config.get(f"{provider}_base_url", "")

        # 其他配置
        self.timeout = config.get("timeout", 30)
        self.max_retries = config.get("max_retries", 3)
        self.enable_dual_verification = config.get("enable_dual_verification", True)
        self.primary_api = config.get("primary_api", "claude")

        # API优先级：用户设置的优先API排第一，其余按默认顺序
        self.API_PRIORITY = self._build_api_priority()

        # 检查可用的API
        self.available_apis = [api for api, key in self.api_keys.items() if key]
        self.logger.info(f"可用API: {', '.join(self.available_apis)}")

        # 记录模型配置
        for api in self.available_apis:
            self.logger.info(f"{api} 使用模型: {self.models.get(api, 'N/A')}")

    def _get_default_model(self, api: str) -> str:
        """获取API的默认模型"""
        defaults = {
            "claude": "claude-sonnet-4-20250514",
            "gemini": "gemini-2.0-flash-exp",
            "deepseek": "deepseek-reasoner",
            "kimi": "kimi-k2-turbo-preview",
        }
        return defaults.get(api, "")

    def _build_api_priority(self) -> List[str]:
        """构建API优先级列表"""
        priority = []

        # 用户设置的优先API排第一
        if self.primary_api and self.primary_api in self.api_keys:
            priority.append(self.primary_api)

        # 然后是默认优先级中的API
        for api in self.DEFAULT_API_PRIORITY:
            if api not in priority and api in self.api_keys:
                priority.append(api)

        # 最后是其他自定义API
        for api in self.api_keys.keys():
            if api not in priority:
                priority.append(api)

        return priority

    def _get_endpoint_name(self, api_name: str) -> str:
        """
        根据API名称和模型获取日志用的endpoint名称

        Args:
            api_name: API名称 (claude/gemini/deepseek/kimi)

        Returns:
            endpoint标识字符串
        """
        model = self.models.get(api_name, "")

        # 提取模型的关键标识
        if "reasoner" in model:
            return "reasoner"
        elif "chat" in model:
            return "chat"
        elif "sonnet" in model:
            return "sonnet"
        elif "opus" in model:
            return "opus"
        elif "flash" in model:
            return "flash"
        elif "pro" in model:
            return "pro"
        else:
            return "chat"  # 默认

    def get_api_for_task(self, task_type: str) -> str:
        """
        根据任务类型获取推荐的API

        优先级：
        1. 用户设置的 primary_api（如果可用）
        2. API_USAGE_MAP 中的推荐（如果可用）
        3. 第一个可用的API

        Args:
            task_type: 任务类型

        Returns:
            推荐的API名称
        """
        # 优先使用用户设置的 primary_api
        if self.primary_api in self.available_apis:
            return self.primary_api

        # 其次使用任务类型映射的推荐
        recommended = self.API_USAGE_MAP.get(task_type)
        if recommended and recommended in self.available_apis:
            return recommended

        # 最后返回第一个可用的API
        return self.available_apis[0] if self.available_apis else None

    async def call_api(
        self,
        task_type: str,
        prompt: str,
        enable_dual_verification: Optional[bool] = None,
        **kwargs
    ) -> str:
        """
        调用API，自动处理故障转移

        Args:
            task_type: 任务类型
            prompt: 提示词
            enable_dual_verification: 是否启用双模型验证（可选，默认使用配置）
            **kwargs: 其他参数

        Returns:
            API响应文本
        """
        # 如果启用了双模型验证
        use_dual = enable_dual_verification if enable_dual_verification is not None else self.enable_dual_verification

        if use_dual and len(self.available_apis) >= 2:
            return await self._call_with_dual_verification(task_type, prompt, **kwargs)
        else:
            return await self._call_with_failover(task_type, prompt, **kwargs)

    async def _call_with_failover(
        self,
        task_type: str,
        prompt: str,
        **kwargs
    ) -> str:
        """
        使用故障转移机制调用API（带指数退避重试）

        Args:
            task_type: 任务类型
            prompt: 提示词
            **kwargs: 其他参数

        Returns:
            API响应文本
        """
        # 获取推荐的API
        primary_api = self.get_api_for_task(task_type)

        if not primary_api:
            raise ValueError("没有可用的API")

        # 按优先级排序可用的API
        apis_to_try = self._get_apis_by_priority(primary_api)

        last_error = None
        for api in apis_to_try:
            # 对每个API进行指数退避重试
            for attempt in range(self.max_retries):
                try:
                    if attempt > 0:
                        delay = calculate_retry_delay(attempt - 1)
                        self.logger.info(f"{api} API 重试 {attempt}/{self.max_retries}，等待 {delay:.2f}秒...")
                        await asyncio.sleep(delay)

                    self.logger.info(f"尝试使用 {api} API" + (f" (第{attempt + 1}次)" if attempt > 0 else ""))
                    start_time = time.time()

                    response = await self._call_api_by_name(api, prompt, **kwargs)

                    duration = time.time() - start_time
                    log_api_call(
                        api_name=api,
                        endpoint=self._get_endpoint_name(api),
                        request_data={"task_type": task_type, "prompt_length": len(prompt)},
                        response_data={"response_length": len(response)},
                        error=None,
                        duration=duration
                    )

                    self.logger.info(f"{api} API 调用成功 (耗时: {duration:.2f}秒)")
                    return response

                except Exception as e:
                    last_error = e
                    is_retryable = self._is_retryable_error(e)

                    if attempt < self.max_retries - 1 and is_retryable:
                        self.logger.warning(f"{api} API 调用失败（可重试）: {e}")
                    else:
                        self.logger.warning(f"{api} API 调用失败: {e}")
                        log_api_call(
                            api_name=api,
                            endpoint=self._get_endpoint_name(api),
                            request_data={"task_type": task_type},
                            response_data=None,
                            error=str(e),
                            duration=0
                        )
                        break  # 不可重试或重试次数用尽，尝试下一个API

        # 所有API都失败了
        error_msg = f"所有API调用都失败了。最后一个错误: {last_error}"
        self.logger.error(error_msg)
        raise Exception(error_msg)

    def _is_retryable_error(self, error: Exception) -> bool:
        """
        判断错误是否可重试

        Args:
            error: 异常对象

        Returns:
            是否可重试
        """
        error_str = str(error).lower()
        # 可重试的错误类型
        retryable_patterns = [
            'timeout', 'timed out',
            'rate limit', 'rate_limit', 'ratelimit',
            'too many requests', '429',
            'connection', 'network',
            'temporary', 'unavailable',
            '500', '502', '503', '504'
        ]
        return any(pattern in error_str for pattern in retryable_patterns)

    async def _call_with_dual_verification(
        self,
        task_type: str,
        prompt: str,
        **kwargs
    ) -> str:
        """
        使用双模型验证机制调用API

        Args:
            task_type: 任务类型
            prompt: 提示词
            **kwargs: 其他参数

        Returns:
            主模型响应文本（附带验证信息）
        """
        self.logger.info("启用双模型验证")

        # 获取主副模型
        primary_api = self.get_api_for_task(task_type)
        available = [api for api in self.API_PRIORITY if api in self.available_apis and api != primary_api]

        if not available:
            self.logger.warning("无法进行双模型验证，只有一个可用API")
            return await self._call_with_failover(task_type, prompt, **kwargs)

        secondary_api = available[0]

        self.logger.info(f"主模型: {primary_api}, 副模型: {secondary_api}")

        # 并发调用两个模型
        try:
            start_time = time.time()

            primary_task = self._call_api_by_name(primary_api, prompt, **kwargs)
            secondary_task = self._call_api_by_name(secondary_api, prompt, **kwargs)

            # 等待两个任务完成
            results = await asyncio.gather(primary_task, secondary_task, return_exceptions=True)

            duration = time.time() - start_time
            log_performance(
                operation="双模型验证",
                duration=duration,
                details={"primary": primary_api, "secondary": secondary_api}
            )

            primary_response = results[0] if not isinstance(results[0], Exception) else None
            secondary_response = results[1] if not isinstance(results[1], Exception) else None

            # 验证结果
            if primary_response and secondary_response:
                # 两个模型都成功 - 进行结果对比和裁判
                self.logger.info("双模型验证完成，两个模型都成功响应，开始对比分析")

                # 智能裁判：分析两个结果的一致性
                comparison_result = self._compare_responses(
                    primary_response, secondary_response, primary_api, secondary_api
                )

                # 构造验证信息
                verification_note = f"\n\n【双模型验证】\n"
                verification_note += f"• 主模型: {primary_api}\n"
                verification_note += f"• 副模型: {secondary_api}\n"
                verification_note += f"• 一致性: {comparison_result['consistency_level']}\n"
                verification_note += f"• 分析: {comparison_result['analysis']}"

                # 如果一致性高，返回主模型结果+验证信息
                # 如果一致性低，返回两个结果的融合或警告
                if comparison_result['consistency_level'] in ['高', '中']:
                    return primary_response + verification_note
                else:
                    # 一致性低，展示两个结果供用户参考
                    verification_note += f"\n\n⚠️ 注意：两个模型的结果存在差异，建议谨慎参考\n"
                    verification_note += f"\n【主模型结果】\n{primary_response}\n"
                    verification_note += f"\n【副模型结果】\n{secondary_response}"
                    return verification_note

            elif primary_response:
                # 主模型成功，副模型失败
                self.logger.warning(f"主模型成功，副模型失败: {results[1]}")
                return primary_response

            elif secondary_response:
                # 主模型失败，副模型成功
                self.logger.warning(f"主模型失败: {results[0]}，使用副模型结果")
                return secondary_response

            else:
                # 两个都失败，尝试故障转移
                self.logger.error("主副模型都失败，尝试故障转移")
                return await self._call_with_failover(task_type, prompt, **kwargs)

        except Exception as e:
            self.logger.error(f"双模型验证过程出错: {e}")
            # 降级到单模型故障转移
            return await self._call_with_failover(task_type, prompt, **kwargs)

    def _compare_responses(
        self,
        primary_response: str,
        secondary_response: str,
        primary_api: str,
        secondary_api: str
    ) -> Dict[str, Any]:
        """
        智能裁判：对比两个模型的响应结果

        通过关键词、结构、长度等维度分析一致性

        Args:
            primary_response: 主模型响应
            secondary_response: 副模型响应
            primary_api: 主模型名称
            secondary_api: 副模型名称

        Returns:
            对比结果 {consistency_level, analysis, differences}
        """
        # 1. 长度对比
        len_ratio = min(len(primary_response), len(secondary_response)) / max(len(primary_response), len(secondary_response))

        # 2. 关键词重叠度（吉凶、建议等关键判断）
        keywords = ['吉', '凶', '平', '大吉', '大凶', '建议', '不宜', '适合', '有利', '不利']
        primary_keywords = [kw for kw in keywords if kw in primary_response]
        secondary_keywords = [kw for kw in keywords if kw in secondary_response]

        common_keywords = set(primary_keywords) & set(secondary_keywords)
        all_keywords = set(primary_keywords) | set(secondary_keywords)

        keyword_overlap = len(common_keywords) / len(all_keywords) if all_keywords else 0

        # 3. 综合一致性评分
        consistency_score = (len_ratio * 0.3 + keyword_overlap * 0.7)

        # 4. 判断一致性等级
        if consistency_score >= 0.8:
            consistency_level = "高"
            analysis = "两个模型的分析结果高度一致，结论可信度高"
        elif consistency_score >= 0.6:
            consistency_level = "中"
            analysis = "两个模型的分析结果基本一致，存在细微差异"
        else:
            consistency_level = "低"
            analysis = "两个模型的分析结果存在明显差异，建议综合参考"

        # 5. 识别差异点
        differences = []
        if '吉' in primary_keywords and '凶' in secondary_keywords:
            differences.append("主模型判断为吉，副模型判断为凶")
        elif '凶' in primary_keywords and '吉' in secondary_keywords:
            differences.append("主模型判断为凶，副模型判断为吉")

        if len_ratio < 0.5:
            differences.append(f"响应长度差异大（{primary_api}:{len(primary_response)}字 vs {secondary_api}:{len(secondary_response)}字）")

        return {
            "consistency_level": consistency_level,
            "analysis": analysis,
            "consistency_score": consistency_score,
            "differences": differences,
            "common_keywords": list(common_keywords)
        }

    def _get_apis_by_priority(self, primary_api: str) -> List[str]:
        """
        按优先级获取API列表

        Args:
            primary_api: 主API

        Returns:
            按优先级排序的API列表
        """
        # 先尝试主API
        result = [primary_api]

        # 然后按优先级顺序添加其他可用API
        for api in self.API_PRIORITY:
            if api in self.available_apis and api != primary_api:
                result.append(api)

        return result

    async def _call_api_by_name(self, api_name: str, prompt: str, **kwargs) -> str:
        """
        按名称调用API

        Args:
            api_name: API名称
            prompt: 提示词
            **kwargs: 其他参数

        Returns:
            响应文本
        """
        if api_name == "claude":
            return await self._call_claude(prompt, **kwargs)
        elif api_name == "gemini":
            return await self._call_gemini(prompt, **kwargs)
        elif api_name == "deepseek":
            return await self._call_deepseek(prompt, **kwargs)
        elif api_name == "kimi":
            return await self._call_kimi(prompt, **kwargs)
        elif api_name in self.api_keys:
            # 自定义API - 使用OpenAI兼容格式调用
            return await self._call_openai_compatible(api_name, prompt, **kwargs)
        else:
            raise ValueError(f"不支持的API: {api_name}")

    async def _call_claude(self, prompt: str, **kwargs) -> str:
        """
        调用Claude API

        Args:
            prompt: 提示词
            **kwargs: 其他参数

        Returns:
            响应文本
        """
        try:
            import anthropic
        except ImportError:
            raise ImportError("需要安装anthropic库: pip install anthropic")

        client = anthropic.Anthropic(api_key=self.api_keys["claude"])

        system_prompt = kwargs.get("system", PromptTemplates.SYSTEM_PROMPT)
        max_tokens = kwargs.get("max_tokens", 4096)

        # 记录使用的模型
        self.logger.info(f"Claude API调用 - 模型: {self.models['claude']}")

        # 异步调用（使用run_in_executor包装同步调用）
        loop = asyncio.get_event_loop()
        message = await loop.run_in_executor(
            None,
            lambda: client.messages.create(
                model=self.models["claude"],
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}],
                timeout=self.timeout
            )
        )

        return message.content[0].text

    async def _call_gemini(self, prompt: str, **kwargs) -> str:
        """
        调用Google Gemini API

        Args:
            prompt: 提示词
            **kwargs: 其他参数

        Returns:
            响应文本
        """
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError("需要安装google-generativeai库: pip install google-generativeai")

        genai.configure(api_key=self.api_keys["gemini"])

        system_prompt = kwargs.get("system", PromptTemplates.SYSTEM_PROMPT)
        max_tokens = kwargs.get("max_tokens", 4096)

        # 记录使用的模型
        self.logger.info(f"Gemini API调用 - 模型: {self.models['gemini']}")

        # 构建完整提示词
        full_prompt = f"{system_prompt}\n\n{prompt}"

        model = genai.GenerativeModel(self.models["gemini"])

        # 异步调用
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                )
            )
        )

        return response.text

    async def _call_deepseek(self, prompt: str, **kwargs) -> str:
        """
        调用Deepseek API

        针对deepseek-reasoner深度思考模型进行了优化：
        - 增强推理引导
        - 鼓励分步思考
        - 优化思考链提示

        Args:
            prompt: 提示词
            **kwargs: 其他参数

        Returns:
            响应文本
        """
        try:
            import openai
        except ImportError:
            raise ImportError("需要安装openai库: pip install openai")

        client = openai.OpenAI(
            api_key=self.api_keys["deepseek"],
            base_url="https://api.deepseek.com"
        )

        system_prompt = kwargs.get("system", PromptTemplates.SYSTEM_PROMPT)
        max_tokens = kwargs.get("max_tokens", 8192)  # deepseek-reasoner支持更长输出

        # 记录使用的模型
        self.logger.info(f"Deepseek API调用 - 模型: {self.models['deepseek']}")

        # 针对deepseek-reasoner深度思考模型优化提示词
        is_reasoner_model = "reasoner" in self.models["deepseek"].lower()

        if is_reasoner_model:
            # 深度思考模型：增强推理引导
            enhanced_prompt = f"""请使用深度推理能力，按照以下步骤仔细分析：

1. 【信息提取】首先从提供的数据中提取关键信息
2. 【逻辑分析】基于术数理论的核心原理进行逻辑推导
3. 【多角度验证】从不同维度验证结论的合理性
4. 【综合判断】整合各方面信息，给出最终结论
5. 【实用建议】提供具体可行的行动指导

{prompt}

请深入思考每个步骤，确保分析的严谨性和准确性。"""
        else:
            # 普通模型：使用原始提示词
            enhanced_prompt = prompt

        # 异步调用（使用run_in_executor包装同步调用）
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model=self.models["deepseek"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": enhanced_prompt}
                ],
                max_tokens=max_tokens,
                timeout=self.timeout * 2 if is_reasoner_model else self.timeout  # 深度思考需要更多时间
            )
        )

        return response.choices[0].message.content

    async def _call_kimi(self, prompt: str, **kwargs) -> str:
        """
        调用Kimi (Moonshot) API

        Args:
            prompt: 提示词
            **kwargs: 其他参数

        Returns:
            响应文本
        """
        try:
            import openai
        except ImportError:
            raise ImportError("需要安装openai库: pip install openai")

        client = openai.OpenAI(
            api_key=self.api_keys["kimi"],
            base_url="https://api.moonshot.cn/v1"
        )

        system_prompt = kwargs.get("system", PromptTemplates.SYSTEM_PROMPT)
        max_tokens = kwargs.get("max_tokens", 4096)

        # 记录使用的模型
        self.logger.info(f"Kimi API调用 - 模型: {self.models['kimi']}")

        # 异步调用（使用run_in_executor包装同步调用）
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model=self.models["kimi"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                timeout=self.timeout
            )
        )

        return response.choices[0].message.content

    async def _call_openai_compatible(self, api_name: str, prompt: str, **kwargs) -> str:
        """
        调用OpenAI兼容格式的API（用于自定义provider如OpenRouter等）

        Args:
            api_name: API名称
            prompt: 提示词
            **kwargs: 其他参数

        Returns:
            响应文本
        """
        try:
            import openai
        except ImportError:
            raise ImportError("需要安装openai库: pip install openai")

        api_key = self.api_keys.get(api_name)
        base_url = self.base_urls.get(api_name)
        model = self.models.get(api_name)

        if not api_key:
            raise ValueError(f"API密钥未配置: {api_name}")
        if not base_url:
            raise ValueError(f"Base URL未配置: {api_name}")
        if not model:
            raise ValueError(f"模型未配置: {api_name}")

        client = openai.OpenAI(
            api_key=api_key,
            base_url=base_url
        )

        system_prompt = kwargs.get("system", PromptTemplates.SYSTEM_PROMPT)
        max_tokens = kwargs.get("max_tokens", 4096)

        # 记录使用的模型
        self.logger.info(f"{api_name} API调用 - 模型: {model}, Base URL: {base_url}")

        # 异步调用（使用run_in_executor包装同步调用）
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                timeout=self.timeout
            )
        )

        return response.choices[0].message.content
