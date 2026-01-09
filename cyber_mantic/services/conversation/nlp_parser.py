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
from api.prompt_loader import load_prompt
from core.exceptions import APIError, APITimeoutError, DataParsingError
from utils.logger import get_logger

# AI增强任务类型（与TaskRouter统一）
TASK_TYPE_INPUT_ENHANCE = "输入增强验证"


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

    def _fallback_parse_icebreak(self, user_message: str) -> Dict[str, Any]:
        """
        破冰输入的代码备用解析（AI失败时使用）
        
        Args:
            user_message: 用户输入
            
        Returns:
            解析结果或错误
        """
        self.logger.info("使用备用解析器解析破冰输入")
        
        # 中文数字映射
        chinese_to_digit = {
            '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
            '六': 6, '七': 7, '八': 8, '九': 9,
            '壹': 1, '贰': 2, '叁': 3, '肆': 4, '伍': 5,
            '陆': 6, '柒': 7, '捌': 8, '玖': 9
        }
        
        # 提取数字
        numbers = []
        
        # 1. 提取阿拉伯数字（1-9）
        arabic_numbers = re.findall(r'[1-9]', user_message)
        for n in arabic_numbers:
            num = int(n)
            if 1 <= num <= 9 and num not in numbers:
                numbers.append(num)
                if len(numbers) >= 3:
                    break
        
        # 2. 如果不足3个，尝试提取中文数字
        if len(numbers) < 3:
            for char in user_message:
                if char in chinese_to_digit:
                    num = chinese_to_digit[char]
                    if num not in numbers:
                        numbers.append(num)
                        if len(numbers) >= 3:
                            break
        
        # 验证数字数量
        if len(numbers) < 3:
            return {"error": "未能提取到3个有效数字，请确保输入包含3个1-9的数字"}
        
        numbers = numbers[:3]  # 只取前3个
        
        # 分类关键词映射
        category_keywords = {
            "事业": ["工作", "职业", "跳槽", "升职", "创业", "面试", "岗位"],
            "感情": ["感情", "恋爱", "婚姻", "桃花", "分手", "复合", "结婚", "对象"],
            "财运": ["财运", "赚钱", "投资", "理财", "收入", "金钱"],
            "健康": ["健康", "身体", "疾病", "病"],
            "学业": ["学业", "考试", "学习", "成绩", "升学"],
            "决策": ["选择", "决定", "是否", "要不要", "该不该"]
        }
        
        # 识别分类
        category = "其他"
        for cat, keywords in category_keywords.items():
            if any(keyword in user_message for keyword in keywords):
                category = cat
                break
        
        # 提取描述（简化版：去掉数字后的剩余内容）
        description = user_message
        for num_str in [str(n) for n in numbers]:
            description = description.replace(num_str, '')
        for char in user_message:
            if char in chinese_to_digit:
                description = description.replace(char, '')
        description = re.sub(r'[、，,\s]+', ' ', description).strip()
        
        if not description:
            description = user_message
        
        result = {
            "category": category,
            "description": description,
            "numbers": numbers
        }
        
        self.logger.info(f"备用解析成功: {result}")
        return result

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
                self.logger.warning(f"AI返回格式错误: {response[:200]}...，尝试备用解析")
                return self._fallback_parse_icebreak(user_message)

        except (APIError, APITimeoutError, json.JSONDecodeError) as e:
            self.logger.warning(f"AI破冰解析失败: {e}，尝试备用解析")
            return self._fallback_parse_icebreak(user_message)
        except Exception as e:
            self.logger.exception("破冰解析时发生未预期的错误")
            # 仍然尝试使用备用解析，但记录完整堆栈
            return self._fallback_parse_icebreak(user_message)

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

        except (APIError, APITimeoutError, json.JSONDecodeError) as e:
            self.logger.error(f"出生信息解析失败: {e}")
            return await self._parse_birth_info_fallback(user_message)
        except Exception as e:
            self.logger.exception("出生信息解析时发生未预期的错误")
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

        except (APIError, APITimeoutError, json.JSONDecodeError) as e:
            self.logger.error(f"验证反馈解析失败: {e}")
            return self._parse_verification_feedback_fallback(user_message)
        except Exception as e:
            self.logger.exception("验证反馈解析时发生未预期的错误")
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

    # ==================== V2增强：ShichenHandler集成 ====================

    async def parse_birth_info_v2(self, user_message: str) -> Dict[str, Any]:
        """
        V2增强版出生信息解析

        增强功能：
        1. 识别 known_range 状态（如"上午"、"凌晨"）
        2. 返回候选时辰列表
        3. 集成ShichenHandler进行智能时间处理

        Args:
            user_message: 用户输入

        Returns:
            增强版解析结果，包含shichen_info字段
        """
        # 首先使用原有方法解析基本信息
        birth_info = await self.parse_birth_info(user_message)

        if "error" in birth_info:
            return birth_info

        # V2增强：分析时间表达，识别known_range
        time_analysis = self._analyze_time_expression(user_message)

        # 更新time_certainty为V2版本
        if time_analysis["status"] == "known_range":
            birth_info["time_certainty"] = "known_range"
            birth_info["time_range"] = time_analysis["range"]
            birth_info["candidate_hours"] = time_analysis["candidates"]
        elif time_analysis["status"] == "certain":
            birth_info["time_certainty"] = "certain"
        elif time_analysis["status"] == "uncertain":
            birth_info["time_certainty"] = "uncertain"
            birth_info["candidate_hours"] = time_analysis.get("candidates", [])

        # 集成ShichenHandler
        try:
            from core.shichen_handler import ShichenHandler, ShichenInfo

            handler = ShichenHandler()
            shichen_info = handler.parse_time_input(
                hour=birth_info.get("hour"),
                minute=birth_info.get("minute"),
                time_text=time_analysis.get("time_text"),
                certainty=birth_info.get("time_certainty", "unknown")
            )

            birth_info["shichen_info"] = shichen_info.to_dict()
            birth_info["shichen_display"] = handler.format_time_display(shichen_info)

        except ImportError:
            self.logger.warning("ShichenHandler not available, skipping integration")

        self.logger.info(f"V2出生信息解析成功: {birth_info}")
        return birth_info

    def _analyze_time_expression(self, text: str) -> Dict[str, Any]:
        """
        分析时间表达方式，识别时间状态

        Args:
            text: 用户输入文本

        Returns:
            时间分析结果
        """
        result = {
            "status": "unknown",
            "time_text": None,
            "range": None,
            "candidates": []
        }

        # 时段范围定义
        time_ranges = {
            "凌晨": {"start": 0, "end": 5, "status": "known_range"},
            "早上": {"start": 5, "end": 9, "status": "known_range"},
            "早晨": {"start": 5, "end": 8, "status": "known_range"},
            "上午": {"start": 9, "end": 12, "status": "known_range"},
            "中午": {"start": 11, "end": 13, "status": "known_range"},
            "下午": {"start": 13, "end": 18, "status": "known_range"},
            "傍晚": {"start": 17, "end": 19, "status": "known_range"},
            "黄昏": {"start": 17, "end": 19, "status": "known_range"},
            "晚上": {"start": 19, "end": 23, "status": "known_range"},
            "夜里": {"start": 21, "end": 24, "status": "known_range"},
            "深夜": {"start": 23, "end": 2, "status": "known_range"},
            "半夜": {"start": 23, "end": 3, "status": "known_range"},
        }

        # 模糊词（触发uncertain状态）
        uncertain_words = ["大概", "大约", "左右", "可能", "好像", "差不多", "前后"]

        # 精确时间模式
        precise_patterns = [
            r'(\d{1,2})[:：](\d{2})',     # 15:30
            r'(\d{1,2})点(\d{1,2})分?(?!左右|多)',  # 3点30分（但不是3点左右）
            r'(\d{1,2})点钟(?!左右)',      # 3点钟
            r'(\d{1,2})点整',              # 3点整
        ]

        # 1. 检查是否是精确时间
        for pattern in precise_patterns:
            match = re.search(pattern, text)
            if match:
                hour = int(match.group(1))
                if 0 <= hour <= 23:
                    # 检查是否有模糊词
                    has_uncertain = any(w in text for w in uncertain_words)
                    if has_uncertain:
                        result["status"] = "uncertain"
                        result["candidates"] = self._get_adjacent_hours(hour)
                    else:
                        result["status"] = "certain"
                    return result

        # 2. 检查时段表达
        for period, info in time_ranges.items():
            if period in text:
                result["status"] = info["status"]
                result["time_text"] = period
                result["range"] = {"start": info["start"], "end": info["end"], "name": period}

                # 生成候选小时
                if info["start"] <= info["end"]:
                    result["candidates"] = list(range(info["start"], info["end"] + 1))
                else:
                    # 跨午夜
                    result["candidates"] = list(range(info["start"], 24)) + list(range(0, info["end"] + 1))

                # 检查是否有附加的精确时间（如"上午10点"）
                hour_match = re.search(r'(\d{1,2})点', text)
                if hour_match:
                    hour = int(hour_match.group(1))
                    if hour in result["candidates"]:
                        # 时段+精确时间，检查是否有模糊词
                        has_uncertain = any(w in text for w in uncertain_words)
                        if has_uncertain:
                            result["status"] = "uncertain"
                        else:
                            result["status"] = "certain"
                return result

        # 3. 检查普通小时表达（没有时段限定）
        hour_match = re.search(r'(\d{1,2})点', text)
        if hour_match:
            hour = int(hour_match.group(1))
            if 0 <= hour <= 23:
                has_uncertain = any(w in text for w in uncertain_words)
                if has_uncertain:
                    result["status"] = "uncertain"
                    result["candidates"] = self._get_adjacent_hours(hour)
                else:
                    result["status"] = "certain"
                return result

        # 4. 检查"不记得"等未知表达
        unknown_words = ["不记得", "忘了", "不知道", "不确定", "没印象", "不清楚"]
        if any(w in text for w in unknown_words):
            result["status"] = "unknown"
            return result

        # 5. 默认未知
        return result

    def _get_adjacent_hours(self, hour: int) -> List[int]:
        """获取相邻的候选小时"""
        # 时辰是2小时制，返回当前时辰及相邻时辰的小时
        candidates = set()

        # 当前时辰（2小时块）
        shichen_start = (hour // 2) * 2 - 1
        if shichen_start < 0:
            shichen_start = 23

        for i in range(3):  # 当前及相邻
            h = (shichen_start + i * 2) % 24
            candidates.add(h)
            candidates.add((h + 1) % 24)

        return sorted(list(candidates))

    async def enhance_time_from_events(
        self,
        birth_info: Dict[str, Any],
        event_description: str,
        event_year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        根据历史事件增强时辰判断

        通过用户提供的重大生活事件，尝试缩小时辰范围

        Args:
            birth_info: 当前解析的出生信息
            event_description: 事件描述
            event_year: 事件发生年份

        Returns:
            增强后的出生信息
        """
        if birth_info.get("time_certainty") == "certain":
            # 已经确定，不需要增强
            return birth_info

        prompt = f"""你是一位经验丰富的命理师，擅长根据人生重大事件反推出生时辰。

用户出生年月日: {birth_info.get('year')}年{birth_info.get('month')}月{birth_info.get('day')}日
当前时辰范围: {birth_info.get('candidate_hours', '未知')}

用户提供的事件：
- 事件描述: {event_description}
- 发生年份: {event_year if event_year else '未提供'}

请分析这个事件与可能的出生时辰的关联，返回JSON：

```json
{{
    "analysis": "事件分析",
    "likely_hours": [最可能的小时列表],
    "excluded_hours": [可以排除的小时列表],
    "confidence": "高|中|低",
    "reasoning": "推理依据"
}}
```

命理推断参考：
- 重大变动（搬家、换工作）常与驿马星相关
- 婚恋事件与桃花、红鸾星相关
- 财运变化与财星、禄神相关
- 学业成就与文昌星相关
- 健康问题与官煞、病符相关

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
                likely_hours = parsed.get("likely_hours", [])
                excluded_hours = parsed.get("excluded_hours", [])
                current_candidates = birth_info.get("candidate_hours", list(range(24)))

                # 如果有可能的小时，取交集
                if likely_hours:
                    new_candidates = [h for h in current_candidates if h in likely_hours]
                    if new_candidates:
                        current_candidates = new_candidates

                # 排除不可能的小时
                if excluded_hours:
                    current_candidates = [h for h in current_candidates if h not in excluded_hours]

                # 更新birth_info
                if current_candidates:
                    birth_info["candidate_hours"] = current_candidates
                    birth_info["event_inference"] = {
                        "event": event_description,
                        "year": event_year,
                        "analysis": parsed.get("analysis"),
                        "confidence": parsed.get("confidence"),
                        "reasoning": parsed.get("reasoning")
                    }

                    # 如果范围缩小到1-2个小时，提高置信度
                    if len(current_candidates) <= 2:
                        birth_info["time_certainty"] = "uncertain"  # 从unknown升级
                        birth_info["hour"] = current_candidates[0]

                self.logger.info(f"事件推断完成，候选时辰: {current_candidates}")

        except Exception as e:
            self.logger.error(f"事件时辰推断失败: {e}")

        return birth_info

    # ==================== V2增强：AI备用验证方法 ====================

    async def analyze_time_expression_with_ai(self, text: str) -> Dict[str, Any]:
        """
        AI增强：分析时间表达的确定性（代码识别失败时使用）

        处理复杂口语表达如：
        - "应该是快中午的时候吧"
        - "好像是天还没亮那会儿"
        - "记得是吃完午饭的时候"

        Args:
            text: 用户输入文本

        Returns:
            AI分析结果
        """
        # 先用代码分析
        code_result = self._analyze_time_expression(text)

        # 如果代码已经能确定，直接返回
        if code_result["status"] in ["certain", "known_range"]:
            return code_result

        # 代码无法确定时，使用AI
        prompt = load_prompt("enhance", "time_expression", user_input=text)

        try:
            response = await self.api_manager.call_api(
                task_type=TASK_TYPE_INPUT_ENHANCE,
                prompt=prompt,
                enable_dual_verification=False
            )

            parsed = self.extract_json_from_response(response)

            if parsed:
                # 合并AI结果
                code_result["status"] = parsed.get("status", code_result["status"])

                if parsed.get("hour") is not None:
                    # AI识别出了小时
                    pass  # 会在调用方处理

                if parsed.get("candidates"):
                    code_result["candidates"] = parsed["candidates"]

                if parsed.get("range_name"):
                    code_result["time_text"] = parsed["range_name"]

                code_result["ai_analysis"] = {
                    "confidence_level": parsed.get("confidence_level"),
                    "reasoning": parsed.get("reasoning")
                }

                self.logger.info(f"AI时间分析成功: {code_result}")
                return code_result

        except Exception as e:
            self.logger.warning(f"AI时间分析失败: {e}")

        return code_result

    async def identify_question_type_with_ai(self, text: str) -> Dict[str, Any]:
        """
        AI增强：识别用户问题类型

        处理复杂/跨类别/模糊的问题表述

        Args:
            text: 用户问题描述

        Returns:
            问题类型识别结果
        """
        prompt = load_prompt("enhance", "question_type", user_input=text)

        try:
            response = await self.api_manager.call_api(
                task_type=TASK_TYPE_INPUT_ENHANCE,
                prompt=prompt,
                enable_dual_verification=False
            )

            parsed = self.extract_json_from_response(response)

            if parsed:
                self.logger.info(f"AI问题类型识别: {parsed}")
                return parsed

        except Exception as e:
            self.logger.warning(f"AI问题类型识别失败: {e}")

        return {"primary_type": "其他", "confidence": 0.5}

    async def extract_judgment_with_ai(self, theory_result: str, theory_name: str) -> Dict[str, Any]:
        """
        AI增强：从理论分析结果中提取吉凶判断

        处理复杂表述如：
        - "虽有阻碍但终能成事"
        - "先难后易，需耐心等待"
        - "短期不利，长期看好"

        Args:
            theory_result: 理论分析结果文本
            theory_name: 理论名称

        Returns:
            吉凶判断结果
        """
        prompt = load_prompt(
            "enhance", "judgment_extract",
            theory_name=theory_name,
            theory_result=theory_result[:1000]
        )

        try:
            response = await self.api_manager.call_api(
                task_type=TASK_TYPE_INPUT_ENHANCE,
                prompt=prompt,
                enable_dual_verification=False
            )

            parsed = self.extract_json_from_response(response)

            if parsed:
                self.logger.info(f"AI吉凶判断: {theory_name} -> {parsed.get('judgment')}")
                return parsed

        except Exception as e:
            self.logger.warning(f"AI吉凶判断失败: {e}")

        return {"judgment": "平", "confidence": 0.5}

    async def infer_hour_from_event_with_ai(
        self,
        birth_info: Dict[str, Any],
        event_description: str,
        event_year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        AI增强：根据历史事件推断出生时辰

        这是narrow_by_event的AI实现

        Args:
            birth_info: 当前出生信息
            event_description: 事件描述
            event_year: 事件年份

        Returns:
            推断结果
        """
        year = birth_info.get("year")
        month = birth_info.get("month")
        day = birth_info.get("day")
        current_candidates = birth_info.get("candidate_hours", list(range(24)))

        prompt = load_prompt(
            "enhance", "event_hour_infer",
            year=year,
            month=month,
            day=day,
            current_candidates=current_candidates,
            event_description=event_description,
            event_year=event_year if event_year else '未提供'
        )

        try:
            response = await self.api_manager.call_api(
                task_type=TASK_TYPE_INPUT_ENHANCE,
                prompt=prompt,
                enable_dual_verification=False
            )

            parsed = self.extract_json_from_response(response)

            if parsed:
                result = {
                    "likely_hours": parsed.get("likely_hours", []),
                    "most_likely_hour": parsed.get("most_likely_hour"),
                    "excluded_hours": parsed.get("excluded_hours", []),
                    "confidence": parsed.get("confidence", "低"),
                    "analysis": parsed.get("analysis", {}),
                    "suggestions": parsed.get("suggestions", [])
                }

                # 更新候选小时
                if result["likely_hours"]:
                    new_candidates = [h for h in current_candidates if h in result["likely_hours"]]
                    if new_candidates:
                        result["updated_candidates"] = new_candidates
                    else:
                        result["updated_candidates"] = result["likely_hours"]
                elif result["excluded_hours"]:
                    result["updated_candidates"] = [h for h in current_candidates if h not in result["excluded_hours"]]
                else:
                    result["updated_candidates"] = current_candidates

                self.logger.info(f"AI事件时辰推断: {result}")
                return result

        except Exception as e:
            self.logger.error(f"AI事件时辰推断失败: {e}")

        return {
            "likely_hours": [],
            "confidence": "低",
            "updated_candidates": current_candidates
        }
