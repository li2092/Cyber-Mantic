"""
阶段处理器模块

包含5阶段对话流程的各阶段处理逻辑：
- Stage1Handler: 破冰阶段（小六壬快速判断）
- Stage2Handler: 基础信息收集（出生信息、性别、MBTI）
- Stage3Handler: 深度补充（时辰推断等）
- Stage4Handler: 结果验证（回溯验证）
"""
import json
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from abc import ABC, abstractmethod

from api.manager import APIManager
from core.constants import DEFAULT_MAX_THEORIES, DEFAULT_MIN_THEORIES
from models import UserInput
from utils.logger import get_logger

from .context import ConversationContext, ConversationStage
from .nlp_parser import NLPParser


class BaseStageHandler(ABC):
    """阶段处理器基类"""

    def __init__(
        self,
        api_manager: APIManager,
        nlp_parser: NLPParser,
        context: ConversationContext
    ):
        self.api_manager = api_manager
        self.nlp_parser = nlp_parser
        self.context = context
        self.logger = get_logger(self.__class__.__name__)

    @abstractmethod
    async def handle(
        self,
        user_message: str,
        progress_callback: Optional[Callable[[str, str, int], None]] = None
    ) -> str:
        """处理用户输入并返回响应"""
        pass


class Stage1Handler(BaseStageHandler):
    """
    阶段1：破冰阶段处理器

    功能：
    - 解析事项分类和随机数字
    - 使用小六壬进行快速判断
    - 生成初步解读
    """

    def __init__(
        self,
        api_manager: APIManager,
        nlp_parser: NLPParser,
        context: ConversationContext,
        xiaoliu_theory
    ):
        super().__init__(api_manager, nlp_parser, context)
        self.xiaoliu_theory = xiaoliu_theory

    async def handle(
        self,
        user_message: str,
        progress_callback: Optional[Callable[[str, str, int], None]] = None
    ) -> str:
        """处理破冰阶段用户输入"""
        if progress_callback:
            progress_callback("阶段1", "正在解析您的问题和随机数字...", 10)

        # 调用NLP解析
        parsed_info = await self.nlp_parser.parse_icebreak_input(user_message)

        if not parsed_info or "error" in parsed_info:
            return self._generate_retry_message()

        # 保存信息
        self.context.question_category = parsed_info.get("category")
        self.context.question_description = parsed_info.get("description", "")
        self.context.random_numbers = parsed_info.get("numbers", [])

        if progress_callback:
            progress_callback("小六壬", "正在用小六壬起卦...", 30)

        # 计算小六壬
        xiaoliu_result = self._calculate_xiaoliu()
        self.context.xiaoliu_result = xiaoliu_result

        if progress_callback:
            progress_callback("小六壬", "小六壬分析完成，正在生成初步判断...", 50)

        # 生成AI解读
        xiaoliu_interpretation = await self._interpret_xiaoliu(xiaoliu_result)

        # 进入下一阶段
        self.context.stage = ConversationStage.STAGE2_BASIC_INFO

        return self._generate_response(xiaoliu_interpretation)

    def _calculate_xiaoliu(self) -> Dict[str, Any]:
        """计算小六壬"""
        user_input = UserInput(
            question_type=self.context.question_category,
            question_description=self.context.question_description,
            numbers=self.context.random_numbers,
            current_time=datetime.now()
        )
        return self.xiaoliu_theory.calculate(user_input)

    async def _interpret_xiaoliu(self, xiaoliu_result: Dict[str, Any]) -> str:
        """用AI解读小六壬结果"""
        current_time = datetime.now().strftime("%Y年%m月%d日 %H:%M")
        prompt = f"""你是一位精通小六壬的占卜师。请根据以下小六壬卦象，给出简洁的初步判断。

【当前时间】：{current_time}

问题类别：{self.context.question_category}
问题描述：{self.context.question_description}

小六壬结果：
```json
{json.dumps(xiaoliu_result, ensure_ascii=False, indent=2)}
```

请生成简洁的解读（80-100字），包括：
1. 落宫的基本吉凶
2. 针对问题的初步建议
3. 用温和、鼓励的语气

格式示例：
```
📍 落宫：速喜（吉）

初步判断：事业运势较好，行动迅速会有喜讯。当前时机有利于主动出击，宜把握机会。

💡 提示：这只是初步判断，接下来通过详细的八字等分析提供更准确的指引。
```

请生成解读：
"""

        try:
            interpretation = await self.api_manager.call_api(
                task_type="快速交互问答",
                prompt=prompt,
                enable_dual_verification=False
            )
            return interpretation.strip()
        except Exception as e:
            self.logger.error(f"小六壬解读失败: {e}")
            gong_name = xiaoliu_result.get("时落宫", "未知")
            return f"📍 落宫：{gong_name}\n\n（系统繁忙，将在后续分析中补充详细解读）"

    def _generate_retry_message(self) -> str:
        """生成重试提示"""
        return """😅 抱歉，我没能完全理解您的信息。

请按以下格式重新输入：

**示例**：
```
我想咨询事业，最近想跳槽
数字是：7、3、5
```

请重新输入（包含事项类别和3个数字）：
"""

    def _generate_response(self, interpretation: str) -> str:
        """生成响应消息"""
        return f"""✅ **信息已收集**

📋 咨询事项：{self.context.question_category}
🔢 随机数字：{', '.join(map(str, self.context.random_numbers))}

---

## 🔮 小六壬快速判断

{interpretation}

---

## 📝 接下来，请告诉我您的出生信息

为了进行更深入的分析，我需要了解：

### 必需信息：
1. **出生年月日**（如：1990年5月20日）
2. **出生时辰**（如：下午3点，或"不记得了"）

### 可选信息（提供后分析更准确）：
3. 性别（男/女）
4. MBTI类型（如果知道的话，如：INTJ）

**💡 示例**：
```
我是1990年5月20日下午3点出生的，男，INTJ
```

请输入您的出生信息：
"""


class Stage2Handler(BaseStageHandler):
    """
    阶段2：基础信息收集处理器

    功能：
    - 解析出生信息
    - 计算理论适配度
    - 判断是否需要补充信息
    """

    def __init__(
        self,
        api_manager: APIManager,
        nlp_parser: NLPParser,
        context: ConversationContext,
        theory_selector,
        config: dict = None
    ):
        super().__init__(api_manager, nlp_parser, context)
        self.theory_selector = theory_selector
        self.config = config or {}

    async def handle(
        self,
        user_message: str,
        progress_callback: Optional[Callable[[str, str, int], None]] = None
    ) -> str:
        """处理基础信息收集阶段"""
        if progress_callback:
            progress_callback("阶段2", "正在解析您的出生信息...", 60)

        # 解析出生信息
        birth_info = await self.nlp_parser.parse_birth_info(user_message)

        if not birth_info or "error" in birth_info:
            return self._generate_retry_message()

        # 保存信息
        self.context.birth_info = birth_info
        self.context.gender = birth_info.get("gender")
        self.context.mbti_type = birth_info.get("mbti")
        self.context.time_certainty = birth_info.get("time_certainty", "unknown")

        if progress_callback:
            progress_callback("理论选择", "正在计算理论适配度...", 75)

        # 计算理论适配度
        available_theories = await self._calculate_theory_fitness()

        # 判断是否需要补充
        need_supplement = self._check_need_supplement()

        return self._generate_response(birth_info, available_theories, need_supplement)

    async def _calculate_theory_fitness(self) -> str:
        """计算理论适配度"""
        user_input = UserInput(
            question_type=self.context.question_category,
            question_description=self.context.question_description,
            birth_year=self.context.birth_info.get("year"),
            birth_month=self.context.birth_info.get("month"),
            birth_day=self.context.birth_info.get("day"),
            birth_hour=self.context.birth_info.get("hour"),
            gender=self.context.gender,
            mbti_type=self.context.mbti_type,
            current_time=datetime.now()
        )

        # 从配置读取理论数量限制，默认max=5, min=3（符合产品定义"3-5个理论"）
        max_theories = self.config.get("conversation", {}).get("max_theories", DEFAULT_MAX_THEORIES)
        min_theories = self.config.get("conversation", {}).get("min_theories", DEFAULT_MIN_THEORIES)
        selected_theories, missing_info = self.theory_selector.select_theories(
            user_input,
            max_theories=max_theories,
            min_theories=min_theories
        )

        self.context.selected_theories = [t["theory"] for t in selected_theories]

        # 生成展示文本
        theory_list = []
        for i, theory_info in enumerate(selected_theories, 1):
            theory_name = theory_info["theory"]
            fitness = theory_info["fitness"]
            reason = theory_info["reason"]
            fitness_bar = "🟩" * int(fitness * 10) + "⬜" * (10 - int(fitness * 10))
            theory_list.append(
                f"{i}. **{theory_name}**（适配度：{fitness:.0%}）\n"
                f"   {fitness_bar}\n"
                f"   ℹ️ {reason}"
            )

        return "\n\n".join(theory_list)

    def _check_need_supplement(self) -> bool:
        """检查是否需要补充信息"""
        return self.context.time_certainty in ["uncertain", "unknown"]

    def _generate_retry_message(self) -> str:
        """生成重试提示"""
        return """😅 抱歉，我没能解析到出生时间。

请按以下格式重新输入：

**示例**：
```
我是1990年5月20日下午3点出生的，男
```

或简化版：
```
1990年5月20日出生，时辰不记得了
```

请重新输入：
"""

    def _generate_response(
        self,
        birth_info: Dict[str, Any],
        theories_text: str,
        need_supplement: bool
    ) -> str:
        """生成响应"""
        certainty_text = {
            "certain": "✅ 明确",
            "uncertain": "⚠️ 模糊",
            "unknown": "❓ 不记得"
        }.get(self.context.time_certainty, "未知")

        # 下一步提示
        if need_supplement:
            self.context.stage = ConversationStage.STAGE3_SUPPLEMENT
            next_prompt = self._generate_supplement_questions()
        else:
            self.context.stage = ConversationStage.STAGE4_VERIFICATION
            next_prompt = "正在进行深度分析，请稍候..."

        response = f"""✅ **出生信息已确认**

📅 出生日期：{birth_info.get('year')}年{birth_info.get('month')}月{birth_info.get('day')}日
⏰ 出生时辰：{birth_info.get('hour', '未提供')}时 （{certainty_text}）
{f"👤 性别：{'男' if self.context.gender == 'male' else '女'}" if self.context.gender else ""}
{f"🧠 MBTI：{self.context.mbti_type}" if self.context.mbti_type else ""}

---

## 📊 可用分析理论

{theories_text}

---

{next_prompt}
"""
        return response

    def _generate_supplement_questions(self) -> str:
        """生成补充问题"""
        return """## 🕐 时辰推断

由于您的出生时辰不确定，我可以通过以下信息帮您推断：

请回答以下问题：

1. **您在家中排行**：第几个孩子？兄弟姐妹共几人？
2. **面部特征**：脸型偏圆还是偏方？额头高还是低？
3. **作息习惯**：更喜欢早起还是熬夜？

**示例回答**：
```
我是家中老二，共3个孩子
脸型偏方，额头中等
喜欢熬夜，早上起不来
```

请输入：
"""


class Stage3Handler(BaseStageHandler):
    """
    阶段3：深度补充处理器

    功能：
    - 推断出生时辰
    - 收集补充占卜信息
    """

    async def handle(
        self,
        user_message: str,
        progress_callback: Optional[Callable[[str, str, int], None]] = None
    ) -> str:
        """处理深度补充阶段"""
        self.context.siblings_info = user_message

        response_text = ""

        # 时辰推断
        if self.context.time_certainty in ["uncertain", "unknown"]:
            if progress_callback:
                progress_callback("阶段3", "正在根据您的信息推断时辰...", 70)

            inferred_hour = await self.nlp_parser.infer_birth_hour(user_message)

            if inferred_hour is not None:
                self.context.inferred_hour = inferred_hour
                if self.context.birth_info:
                    self.context.birth_info["hour"] = inferred_hour
                    self.context.time_certainty = "inferred"

                hour_name = self._hour_to_chinese(inferred_hour)
                response_text = f"""✅ 补充信息已收录

## 🕐 时辰推断结果

根据您提供的信息，推断出生时辰为：**{hour_name}时**（{inferred_hour}:00-{(inferred_hour+2)%24}:00）

**注意**：此为推断结果，准确度约70%。如果您想起确切时辰，可以告诉我调整。

"""
            else:
                self.context.inferred_hour = 12
                if self.context.birth_info:
                    self.context.birth_info["hour"] = 12

                response_text = """✅ 补充信息已收录

## 🕐 时辰推断

根据信息暂时无法精确推断，将使用**午时**（11:00-13:00）作为默认值。

"""
        else:
            response_text = "✅ 补充信息已收录\n\n"

        # 进入下一阶段
        self.context.stage = ConversationStage.STAGE4_VERIFICATION

        return response_text + "正在进行深度分析，请稍候..."

    def _hour_to_chinese(self, hour: int) -> str:
        """将小时转换为时辰名称"""
        shichen_map = {
            0: "子", 1: "丑", 2: "丑", 3: "寅", 4: "寅",
            5: "卯", 6: "卯", 7: "辰", 8: "辰", 9: "巳",
            10: "巳", 11: "午", 12: "午", 13: "未", 14: "未",
            15: "申", 16: "申", 17: "酉", 18: "酉", 19: "戌",
            20: "戌", 21: "亥", 22: "亥", 23: "子"
        }
        return shichen_map.get(hour, "未知")


class Stage4Handler(BaseStageHandler):
    """
    阶段4：结果验证处理器

    功能：
    - 解析用户验证反馈
    - 调整理论置信度
    """

    async def handle(
        self,
        user_message: str,
        progress_callback: Optional[Callable[[str, str, int], None]] = None
    ) -> str:
        """处理结果验证阶段"""
        if progress_callback:
            progress_callback("阶段4", "正在分析您的反馈...", 90)

        # 解析验证反馈
        feedback = await self.nlp_parser.parse_verification_feedback(
            user_message,
            self.context.retrospective_events
        )

        # 保存反馈
        self.context.verification_feedback.append(feedback)

        # 调整理论置信度
        self._adjust_theory_confidence(feedback)

        # 进入问答阶段
        self.context.stage = ConversationStage.QA

        return self._generate_response(feedback)

    def _adjust_theory_confidence(self, feedback: Dict[str, Any]):
        """根据反馈调整理论置信度"""
        accuracy_score = feedback.get("accuracy_score", 0.5)

        # 如果准确度高，提升相关理论置信度
        if accuracy_score > 0.7:
            for theory in self.context.selected_theories:
                current = self.context.theory_confidence_adjustment.get(theory, 1.0)
                self.context.theory_confidence_adjustment[theory] = min(current * 1.1, 1.5)
        elif accuracy_score < 0.3:
            for theory in self.context.selected_theories:
                current = self.context.theory_confidence_adjustment.get(theory, 1.0)
                self.context.theory_confidence_adjustment[theory] = max(current * 0.9, 0.5)

    def _generate_response(self, feedback: Dict[str, Any]) -> str:
        """生成响应"""
        accuracy = feedback.get("overall_accuracy", "部分准确")
        sentiment = feedback.get("user_sentiment", "中性")

        if accuracy == "准确":
            emoji = "🎯"
            message = "感谢您的反馈！分析结果与您的实际经历高度吻合，这增强了我们对分析准确性的信心。"
        elif accuracy == "不准确":
            emoji = "🔄"
            message = "感谢您的反馈！我们已记录这些差异，并会在后续分析中进行调整。"
        else:
            emoji = "💡"
            message = "感谢您的反馈！部分验证正确，我们会综合考虑这些信息。"

        return f"""{emoji} **验证反馈已收录**

{message}

---

## 🎉 分析完成！

现在您可以：
1. **继续提问** - 问任何关于分析结果的问题
2. **查看详细报告** - 输入"查看报告"
3. **询问建议** - 输入"给我建议"

请输入您的问题：
"""
