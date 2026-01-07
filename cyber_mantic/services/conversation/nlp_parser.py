"""
NLP解析器 - 使用AI进行自然语言解析

包含：
- 破冰阶段输入解析
- 出生信息解析
- 验证反馈解析
- JSON提取工具
"""
import re
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

from api.manager import APIManager
from utils.logger import get_logger


class NLPParser:
    """
    NLP解析器

    使用AI（主要是Kimi）进行自然语言解析，
    并提供代码备用解析方案
    """

    def __init__(self, api_manager: APIManager):
        self.api_manager = api_manager
        self.logger = get_logger(__name__)

    def extract_json_from_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        从AI响应中提取JSON（支持多种格式）

        Args:
            response: AI的原始响应文本

        Returns:
            解析后的字典，失败返回None
        """
        # 策略1: 尝试从markdown代码块中提取
        code_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if code_block_match:
            try:
                return json.loads(code_block_match.group(1))
            except json.JSONDecodeError as e:
                self.logger.warning(f"代码块中的JSON解析失败: {e}")

        # 策略2: 尝试提取原始JSON（支持嵌套对象）
        json_match = re.search(r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError as e:
                self.logger.warning(f"原始JSON解析失败: {e}")

        # 策略3: 查找第一个 { 和最后一个 }
        first_brace = response.find('{')
        last_brace = response.rfind('}')
        if first_brace != -1 and last_brace != -1 and first_brace < last_brace:
            try:
                json_str = response[first_brace:last_brace + 1]
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                self.logger.warning(f"完整JSON提取解析失败: {e}")

        self.logger.error(f"无法从AI响应中提取有效JSON。响应内容: {response[:200]}...")
        return None

    async def parse_icebreak_input(self, user_message: str) -> Dict[str, Any]:
        """
        解析破冰阶段的用户输入（事项分类 + 3个随机数字）

        Args:
            user_message: 用户输入

        Returns:
            解析结果字典，包含category, description, numbers
        """
        prompt = f"""你是一个智能解析助手。请从用户输入中提取：1. 事项分类 2. 3个随机数字

用户输入：
{user_message}

请分析并返回JSON格式（严格遵循格式，不要有任何额外文字）：

```json
{{
    "category": "事业|感情|财运|健康|学业|决策|其他",
    "description": "用户的具体问题描述",
    "numbers": [数字1, 数字2, 数字3]
}}
```

**提取规则**：
1. category: 根据用户提到的关键词判断类别
   - 提到"工作"、"职业"、"跳槽"、"升职"、"创业" → "事业"
   - 提到"感情"、"恋爱"、"婚姻"、"桃花"、"分手" → "感情"
   - 提到"财运"、"赚钱"、"投资"、"理财" → "财运"
   - 提到"健康"、"身体"、"疾病" → "健康"
   - 提到"学业"、"考试"、"学习" → "学业"
   - 提到"选择"、"决定"、"是否" → "决策"
   - 其他情况 → "其他"

2. numbers: 提取3个1-9的数字
   - 用户可能说"7、3、5"或"7 3 5"或"七三五"
   - 如果提供的数字不是3个，或不在1-9范围，返回error

3. description: 提取用户的具体问题描述

只返回JSON，不要有其他文字：
"""

        try:
            response = await self.api_manager.call_api(
                task_type="简单问题解答",
                prompt=prompt,
                enable_dual_verification=False
            )

            parsed = self.extract_json_from_response(response)

            if parsed:
                numbers = parsed.get("numbers", [])
                if len(numbers) != 3 or not all(1 <= n <= 9 for n in numbers):
                    self.logger.error(f"随机数字无效: {numbers}")
                    return {"error": "随机数字无效"}

                self.logger.info(f"破冰输入解析成功: {parsed}")
                return parsed
            else:
                self.logger.error(f"AI返回格式错误: {response[:200]}...")
                return {"error": "解析失败"}

        except Exception as e:
            self.logger.error(f"破冰输入解析失败: {e}")
            return {"error": str(e)}

    async def parse_birth_info(self, user_message: str) -> Dict[str, Any]:
        """
        解析出生信息

        流程：
        1. 使用Kimi进行自然语言解析
        2. 进行基本合法性验证
        3. 如果失败，使用代码备用解析
        """
        prompt = f"""你是一个专业的出生信息解析助手，精通中国传统命理学。请从用户的输入中提取出生信息。

用户输入：
{user_message}

**重要任务**：准确识别时辰的三种情况（certain/uncertain/unknown）

请分析并返回JSON格式（严格遵循格式，不要有任何额外文字）：

```json
{{
    "year": 年份(整数),
    "month": 月份(整数1-12),
    "day": 日期(整数1-31),
    "hour": 时辰(整数0-23, 没提供则为null),
    "minute": 分钟(整数0-59, 没提供则为0),
    "calendar_type": "solar"或"lunar",
    "time_certainty": "certain"或"uncertain"或"unknown",
    "gender": "male"或"female"(如果提供),
    "mbti": "INTJ"等四位字母(如果提供),
    "birth_place": "城市名称"(如果提供)
}}
```

**时辰确定性分类规则**：

1. **certain（确定）**：
   - 明确说"下午3点"、"15点"、"晚上8点半" → hour=对应小时, time_certainty="certain"

2. **uncertain（不确定）**：
   - 只说"下午"、"早上"、"傍晚"、"晚上" → hour=大致时间, time_certainty="uncertain"
   - 说"大概"、"好像"、"可能" → time_certainty="uncertain"

3. **unknown（未知）**：
   - 明确说"不记得"、"忘了"、"不知道" → hour=null, time_certainty="unknown"
   - 完全未提及时辰 → hour=null, time_certainty="unknown"

**其他提取规则**：
- 历法：明确说"农历"、"阴历"、"正月" → "lunar"；否则 → "solar"
- 性别：提到"男" → "male"；提到"女" → "female"；未说明 → null
- MBTI：提取4位字母组合，否则为null

只返回JSON，不要有任何解释：
"""

        try:
            self.logger.info("使用Kimi进行出生信息解析")
            response = await self.api_manager.call_api(
                task_type="出生信息解析",
                prompt=prompt,
                enable_dual_verification=False
            )

            birth_info = self.extract_json_from_response(response)

            if not birth_info:
                self.logger.error(f"Kimi返回格式错误: {response[:200]}...")
                return await self._parse_birth_info_fallback(user_message)

            # 验证必要字段
            required_fields = ["year", "month", "day", "calendar_type", "time_certainty"]
            for field in required_fields:
                if field not in birth_info:
                    self.logger.error(f"缺少必要字段: {field}")
                    return await self._parse_birth_info_fallback(user_message)

            # 基本合法性验证
            validation = self._validate_birth_info_basic(birth_info)
            if not validation["valid"]:
                self.logger.warning(f"验证失败: {validation['error']}")
                return await self._parse_birth_info_fallback(user_message)

            self.logger.info(f"出生信息解析成功: {birth_info}")
            return birth_info

        except Exception as e:
            self.logger.error(f"出生信息解析失败: {e}")
            return await self._parse_birth_info_fallback(user_message)

    def _validate_birth_info_basic(self, birth_info: Dict[str, Any]) -> Dict[str, Any]:
        """基本合法性验证"""
        try:
            year = birth_info.get("year")
            month = birth_info.get("month")
            day = birth_info.get("day")
            hour = birth_info.get("hour")
            calendar_type = birth_info.get("calendar_type", "solar")

            if not year or not (1900 <= year <= 2100):
                return {"valid": False, "error": f"年份不合法: {year}"}

            if not month or not (1 <= month <= 12):
                return {"valid": False, "error": f"月份不合法: {month}"}

            if not day or not (1 <= day <= 31):
                return {"valid": False, "error": f"日期不合法: {day}"}

            if hour is not None and not (0 <= hour <= 23):
                return {"valid": False, "error": f"小时不合法: {hour}"}

            if calendar_type not in ["solar", "lunar"]:
                return {"valid": False, "error": f"历法类型不合法: {calendar_type}"}

            return {"valid": True}

        except Exception as e:
            return {"valid": False, "error": f"验证异常: {str(e)}"}

    async def _parse_birth_info_fallback(self, user_message: str) -> Dict[str, Any]:
        """代码备用解析方案"""
        self.logger.info("使用代码备用解析方案")

        birth_info = {
            "year": None,
            "month": None,
            "day": None,
            "hour": None,
            "minute": 0,
            "calendar_type": "solar",
            "time_certainty": "unknown",
            "gender": None,
            "mbti": None,
            "birth_place": None
        }

        try:
            # 提取年份
            year_match = re.search(r'(19\d{2}|20\d{2})', user_message)
            if year_match:
                birth_info["year"] = int(year_match.group(1))
            else:
                year_match_short = re.search(r'(\d{2})年', user_message)
                if year_match_short:
                    short_year = int(year_match_short.group(1))
                    birth_info["year"] = 1900 + short_year if short_year >= 30 else 2000 + short_year

            # 提取月日
            date_match1 = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', user_message)
            if date_match1:
                birth_info["year"] = int(date_match1.group(1))
                birth_info["month"] = int(date_match1.group(2))
                birth_info["day"] = int(date_match1.group(3))
            else:
                date_match2 = re.search(r'(\d{1,2})月(\d{1,2})日', user_message)
                if date_match2:
                    birth_info["month"] = int(date_match2.group(1))
                    birth_info["day"] = int(date_match2.group(2))
                else:
                    year_md_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})', user_message)
                    if year_md_match:
                        birth_info["year"] = int(year_md_match.group(1))
                        birth_info["month"] = int(year_md_match.group(2))
                        birth_info["day"] = int(year_md_match.group(3))

            # 提取小时
            hour_match = re.search(r'(\d{1,2})点', user_message)
            if hour_match:
                birth_info["hour"] = int(hour_match.group(1))
                if "点多" in user_message or "点左右" in user_message:
                    birth_info["time_certainty"] = "uncertain"
                else:
                    birth_info["time_certainty"] = "certain"
            else:
                time_mappings = {
                    "凌晨": (3, "uncertain"),
                    "早上": (8, "uncertain"),
                    "早晨": (8, "uncertain"),
                    "上午": (10, "uncertain"),
                    "中午": (12, "uncertain"),
                    "下午": (15, "uncertain"),
                    "傍晚": (18, "uncertain"),
                    "晚上": (20, "uncertain"),
                }
                for keyword, (hour, certainty) in time_mappings.items():
                    if keyword in user_message:
                        birth_info["hour"] = hour
                        birth_info["time_certainty"] = certainty
                        break

                if any(kw in user_message for kw in ["不记得", "忘了", "不知道", "不确定"]):
                    birth_info["hour"] = None
                    birth_info["time_certainty"] = "unknown"

            # 提取历法
            if any(kw in user_message for kw in ["农历", "阴历", "正月"]):
                birth_info["calendar_type"] = "lunar"

            # 提取性别
            if "男" in user_message or "先生" in user_message:
                birth_info["gender"] = "male"
            elif "女" in user_message or "女士" in user_message:
                birth_info["gender"] = "female"

            # 提取MBTI
            mbti_match = re.search(r'([IE][NS][TF][JP])', user_message.upper())
            if mbti_match:
                birth_info["mbti"] = mbti_match.group(1)

            # 验证必要字段
            if not all([birth_info["year"], birth_info["month"], birth_info["day"]]):
                return {"error": "代码解析失败：缺少必要的年月日信息"}

            self.logger.info(f"代码备用解析成功: {birth_info}")
            return birth_info

        except Exception as e:
            self.logger.error(f"代码备用解析异常: {e}")
            return {"error": f"代码解析失败: {str(e)}"}

    async def parse_verification_feedback(
        self,
        user_message: str,
        retrospective_events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        解析用户对回溯验证的反馈

        Args:
            user_message: 用户反馈
            retrospective_events: 回溯的事件列表

        Returns:
            解析结果
        """
        events_text = "\n".join([
            f"- {e.get('year', '?')}年: {e.get('event', '?')}"
            for e in retrospective_events
        ])

        prompt = f"""你是一个反馈解析助手。请分析用户对以下历史事件预测的反馈。

**预测的历史事件**：
{events_text}

**用户反馈**：
{user_message}

请返回JSON格式：

```json
{{
    "overall_accuracy": "准确|部分准确|不准确",
    "accuracy_score": 0.0-1.0之间的数值,
    "event_feedback": [
        {{"year": 年份, "accurate": true/false, "comment": "用户评价"}}
    ],
    "user_sentiment": "满意|中性|不满意",
    "specific_corrections": ["用户提到的具体纠正..."]
}}
```

只返回JSON：
"""

        try:
            response = await self.api_manager.call_api(
                task_type="简单问题解答",
                prompt=prompt,
                enable_dual_verification=False
            )

            parsed = self.extract_json_from_response(response)

            if parsed:
                self.logger.info(f"验证反馈解析成功: {parsed}")
                return parsed
            else:
                return self._parse_verification_feedback_fallback(user_message)

        except Exception as e:
            self.logger.error(f"验证反馈解析失败: {e}")
            return self._parse_verification_feedback_fallback(user_message)

    def _parse_verification_feedback_fallback(self, user_message: str) -> Dict[str, Any]:
        """验证反馈的备用解析"""
        positive_keywords = ["准", "对", "是的", "确实", "没错", "准确"]
        negative_keywords = ["不准", "不对", "错", "不是", "偏差"]

        positive_count = sum(1 for kw in positive_keywords if kw in user_message)
        negative_count = sum(1 for kw in negative_keywords if kw in user_message)

        if positive_count > negative_count:
            return {
                "overall_accuracy": "准确",
                "accuracy_score": 0.8,
                "user_sentiment": "满意",
                "event_feedback": [],
                "specific_corrections": []
            }
        elif negative_count > positive_count:
            return {
                "overall_accuracy": "不准确",
                "accuracy_score": 0.3,
                "user_sentiment": "不满意",
                "event_feedback": [],
                "specific_corrections": []
            }
        else:
            return {
                "overall_accuracy": "部分准确",
                "accuracy_score": 0.5,
                "user_sentiment": "中性",
                "event_feedback": [],
                "specific_corrections": []
            }

    async def infer_birth_hour(self, user_message: str) -> Optional[int]:
        """
        根据用户描述推断出生时辰

        Args:
            user_message: 用户的描述（兄弟姐妹、脸型、作息等）

        Returns:
            推断的小时（0-23），失败返回None
        """
        prompt = f"""你是一位经验丰富的命理师，擅长根据生活习惯和特征推断出生时辰。

用户描述：
{user_message}

请根据中国传统命理中的时辰推断方法，分析并返回JSON：

```json
{{
    "inferred_hour": 0-23的整数,
    "confidence": "高|中|低",
    "reasoning": "推断依据说明",
    "shichen": "子时|丑时|寅时|卯时|辰时|巳时|午时|未时|申时|酉时|戌时|亥时"
}}
```

**时辰对应**：
- 子时(23-1点): 深夜型、喜静
- 丑时(1-3点): 踏实稳重
- 寅时(3-5点): 早起型、有活力
- 卯时(5-7点): 规律作息
- 辰时(7-9点): 精力充沛
- 巳时(9-11点): 社交型
- 午时(11-13点): 外向活泼
- 未时(13-15点): 温和内敛
- 申时(15-17点): 灵活多变
- 酉时(17-19点): 艺术气质
- 戌时(19-21点): 忠诚稳重
- 亥时(21-23点): 感性细腻

只返回JSON：
"""

        try:
            response = await self.api_manager.call_api(
                task_type="简单问题解答",
                prompt=prompt,
                enable_dual_verification=False
            )

            parsed = self.extract_json_from_response(response)

            if parsed and "inferred_hour" in parsed:
                hour = parsed["inferred_hour"]
                if 0 <= hour <= 23:
                    self.logger.info(f"时辰推断成功: {hour}点 ({parsed.get('shichen', '未知')})")
                    return hour

            return None

        except Exception as e:
            self.logger.error(f"时辰推断失败: {e}")
            return None
