"""
测字术AI辅助验证器
使用Kimi AI验证和校正字的笔画、结构等信息
"""
import asyncio
from typing import Dict, Any, Optional, Tuple
from utils.logger import get_logger


class CeZiAIValidator:
    """测字术AI验证器"""

    def __init__(self, api_manager=None):
        """
        初始化验证器

        Args:
            api_manager: API管理器实例，如果为None则动态导入
        """
        self.logger = get_logger(__name__)
        self.api_manager = api_manager
        self._initialized = False

    def _ensure_api_manager(self):
        """确保API管理器已初始化"""
        if not self._initialized:
            if self.api_manager is None:
                from api.manager import get_api_manager
                self.api_manager = get_api_manager()
            self._initialized = True

    async def validate_character_async(
        self,
        character: str,
        code_stroke_count: int,
        code_structure: str
    ) -> Dict[str, Any]:
        """
        异步验证字符信息

        Args:
            character: 要验证的汉字
            code_stroke_count: 代码计算的笔画数
            code_structure: 代码推测的结构类型

        Returns:
            验证结果，包含AI解析和对比信息
        """
        self._ensure_api_manager()

        try:
            # 第一步：让AI解析字的信息
            ai_result = await self._get_ai_parse(character)

            if not ai_result:
                return {
                    "validation_success": False,
                    "use_code_result": True,
                    "error": "AI解析失败",
                    "final_stroke_count": code_stroke_count,
                    "final_structure": code_structure,
                    "confidence": 0.5
                }

            # 第二步：对比代码结果和AI结果
            is_consistent, differences = self._compare_results(
                code_stroke_count,
                code_structure,
                ai_result
            )

            if is_consistent:
                # 结果一致，使用代码结果（更快）
                self.logger.info(f"字'{character}'的代码解析与AI解析一致")
                return {
                    "validation_success": True,
                    "is_consistent": True,
                    "use_code_result": True,
                    "final_stroke_count": code_stroke_count,
                    "final_structure": code_structure,
                    "ai_stroke_count": ai_result.get("stroke_count"),
                    "ai_structure": ai_result.get("structure"),
                    "ai_split_parts": ai_result.get("split_parts", []),
                    "confidence": 0.9
                }
            else:
                # 结果不一致，进行第二次AI校验
                self.logger.warning(
                    f"字'{character}'的解析不一致: {differences}"
                )
                unified_result = await self._get_unified_verification(
                    character,
                    code_stroke_count,
                    code_structure,
                    ai_result,
                    differences
                )

                return {
                    "validation_success": True,
                    "is_consistent": False,
                    "use_code_result": False,
                    "differences": differences,
                    "final_stroke_count": unified_result["stroke_count"],
                    "final_structure": unified_result["structure"],
                    "final_split_parts": unified_result.get("split_parts", []),
                    "code_stroke_count": code_stroke_count,
                    "code_structure": code_structure,
                    "ai_stroke_count": ai_result.get("stroke_count"),
                    "ai_structure": ai_result.get("structure"),
                    "unified_reason": unified_result.get("reason"),
                    "confidence": unified_result.get("confidence", 0.8)
                }

        except Exception as e:
            self.logger.error(f"验证字'{character}'时出错: {e}")
            return {
                "validation_success": False,
                "use_code_result": True,
                "error": str(e),
                "final_stroke_count": code_stroke_count,
                "final_structure": code_structure,
                "confidence": 0.5
            }

    def validate_character(
        self,
        character: str,
        code_stroke_count: int,
        code_structure: str
    ) -> Dict[str, Any]:
        """
        同步验证接口（内部调用异步方法）

        Args:
            character: 要验证的汉字
            code_stroke_count: 代码计算的笔画数
            code_structure: 代码推测的结构类型

        Returns:
            验证结果
        """
        try:
            # 尝试获取当前事件循环
            loop = asyncio.get_event_loop()
            # 检查循环是否正在运行
            if loop.is_running():
                # 如果已经在事件循环中运行（如PyQt环境），使用线程池执行异步任务
                import concurrent.futures

                self.logger.info(f"字'{character}'使用线程池执行AI验证（PyQt环境）")

                def run_async_in_thread():
                    """在新线程中运行异步任务"""
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        return new_loop.run_until_complete(
                            self.validate_character_async(character, code_stroke_count, code_structure)
                        )
                    finally:
                        new_loop.close()

                # 使用线程池执行（设置超时5秒）
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(run_async_in_thread)
                    try:
                        return future.result(timeout=5.0)
                    except concurrent.futures.TimeoutError:
                        self.logger.warning(f"字'{character}'AI验证超时，使用代码结果")
                        return {
                            "validation_success": False,
                            "use_code_result": True,
                            "error": "AI验证超时",
                            "final_stroke_count": code_stroke_count,
                            "final_structure": code_structure,
                            "confidence": 0.7
                        }
            else:
                # 事件循环存在但未运行，可以使用 run_until_complete
                return loop.run_until_complete(
                    self.validate_character_async(character, code_stroke_count, code_structure)
                )
        except RuntimeError:
            # 没有事件循环，创建新的
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(
                    self.validate_character_async(character, code_stroke_count, code_structure)
                )
            finally:
                loop.close()

    async def _get_ai_parse(self, character: str) -> Optional[Dict[str, Any]]:
        """
        调用AI解析字的信息

        Args:
            character: 汉字

        Returns:
            AI解析结果
        """
        prompt = f"""你是一位精通汉字分析的专家。请分析汉字"{character}"，返回JSON格式（不要有任何额外文字）：

```json
{{
    "character": "{character}",
    "stroke_count": 笔画数(整数),
    "structure": "结构类型（从以下选择：左右、上下、包围、半包围、独体）",
    "split_parts": ["拆字部件1", "拆字部件2", ...],
    "radical": "主要部首",
    "explanation": "简要说明字形结构"
}}
```

注意：
1. stroke_count必须是准确的笔画总数
2. structure必须从5种类型中选择一个
3. split_parts是拆字的各个部件（如"好"拆为["女","子"]）
4. 只返回JSON，不要其他文字
"""

        try:
            response = await self.api_manager.call_api(
                api_name="kimi",
                prompt=prompt,
                max_tokens=500,
                temperature=0.1
            )

            # 解析JSON
            import json
            import re

            # 提取JSON部分
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                result = json.loads(json_match.group(0))
                self.logger.debug(f"AI解析字'{character}': {result}")
                return result
            else:
                self.logger.warning(f"AI返回格式不正确: {response}")
                return None

        except Exception as e:
            self.logger.error(f"调用AI解析失败: {e}")
            return None

    def _compare_results(
        self,
        code_stroke_count: int,
        code_structure: str,
        ai_result: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, str]]:
        """
        对比代码结果和AI结果

        Args:
            code_stroke_count: 代码笔画数
            code_structure: 代码结构
            ai_result: AI解析结果

        Returns:
            (是否一致, 差异说明)
        """
        differences = {}
        is_consistent = True

        ai_stroke = ai_result.get("stroke_count")
        ai_structure = ai_result.get("structure")

        # 对比笔画数（要求完全一致，不允许误差）
        if ai_stroke is not None:
            if code_stroke_count != ai_stroke:
                differences["stroke_count"] = (
                    f"代码={code_stroke_count}, AI={ai_stroke}"
                )
                is_consistent = False

        # 对比结构类型
        if ai_structure and code_structure != ai_structure:
            differences["structure"] = (
                f"代码={code_structure}, AI={ai_structure}"
            )
            is_consistent = False

        return is_consistent, differences

    async def _get_unified_verification(
        self,
        character: str,
        code_stroke_count: int,
        code_structure: str,
        ai_result: Dict[str, Any],
        differences: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        当结果不一致时，进行统一校验

        Args:
            character: 汉字
            code_stroke_count: 代码笔画数
            code_structure: 代码结构
            ai_result: AI第一次解析结果
            differences: 差异信息

        Returns:
            统一后的结果
        """
        prompt = f"""你是汉字分析专家。现在需要你对汉字"{character}"进行最终裁定。

**代码分析结果**：
- 笔画数: {code_stroke_count}
- 结构类型: {code_structure}

**AI初步分析结果**：
- 笔画数: {ai_result.get('stroke_count')}
- 结构类型: {ai_result.get('structure')}
- 拆字部件: {ai_result.get('split_parts', [])}

**发现的差异**：
{differences}

请仔细核实，给出最终的准确结果。返回JSON格式（不要有任何额外文字）：

```json
{{
    "stroke_count": 最准确的笔画数(整数),
    "structure": "最准确的结构类型",
    "split_parts": ["拆字部件"],
    "reason": "选择此结果的理由",
    "confidence": 置信度(0.7-1.0的小数)
}}
```

注意：
1. 必须给出明确的笔画数和结构类型
2. reason要说明为什么这是正确答案
3. 只返回JSON，不要其他文字
"""

        try:
            response = await self.api_manager.call_api(
                api_name="kimi",
                prompt=prompt,
                max_tokens=500,
                temperature=0.1
            )

            # 解析JSON
            import json
            import re

            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                result = json.loads(json_match.group(0))
                self.logger.info(
                    f"字'{character}'统一校验结果: "
                    f"笔画={result.get('stroke_count')}, "
                    f"结构={result.get('structure')}"
                )
                return result
            else:
                # 解析失败，使用AI第一次的结果
                self.logger.warning("统一校验JSON解析失败，使用AI初步结果")
                return {
                    "stroke_count": ai_result.get("stroke_count", code_stroke_count),
                    "structure": ai_result.get("structure", code_structure),
                    "split_parts": ai_result.get("split_parts", []),
                    "reason": "统一校验失败，采用AI初步结果",
                    "confidence": 0.7
                }

        except Exception as e:
            self.logger.error(f"统一校验失败: {e}")
            # 出错时默认使用AI结果
            return {
                "stroke_count": ai_result.get("stroke_count", code_stroke_count),
                "structure": ai_result.get("structure", code_structure),
                "split_parts": ai_result.get("split_parts", []),
                "reason": f"统一校验异常: {e}",
                "confidence": 0.6
            }


# 全局单例
_validator_instance = None


def get_cezi_validator(api_manager=None) -> CeZiAIValidator:
    """获取测字术验证器单例"""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = CeZiAIValidator(api_manager)
    return _validator_instance
