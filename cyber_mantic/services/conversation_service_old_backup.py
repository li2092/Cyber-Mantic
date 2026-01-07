"""
ConversationService - 纯AI对话模式服务（重构版）

实现渐进式5阶段智能交互流程：
阶段1_破冰：事项分类 + 3个随机数字 → 小六壬快速初判
阶段2_基础信息：出生年月日、性别、MBTI等 → 展示可用理论
阶段3_深度补充：针对性补充信息（时辰推断、额外占卜）
阶段4_结果确认：回溯验证（过去3-5年关键事件）
阶段5_完整报告：生成详细分析报告 + 常规问答
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from enum import Enum

from models import UserInput, ComprehensiveReport
from api.manager import APIManager
from theories.bazi.calculator import BaZiCalculator
from theories.qimen.calculator import QiMenCalculator
from theories.daliuren.calculator import DaLiuRenCalculator
from theories.xiaoliu.theory import XiaoLiuRenTheory
from theories.liuyao.theory import LiuYaoTheory
from theories.meihua.theory import MeiHuaTheory
from core.theory_selector import TheorySelector
from utils.logger import get_logger


class ConversationStage(Enum):
    """对话阶段（5阶段渐进式流程）"""
    INIT = "初始化"
    STAGE1_ICEBREAK = "阶段1_破冰"          # 事项分类 + 3个随机数字 → 小六壬
    STAGE2_BASIC_INFO = "阶段2_基础信息"    # 出生年月日、性别、MBTI
    STAGE3_SUPPLEMENT = "阶段3_深度补充"    # 时辰推断、补充占卜
    STAGE4_VERIFICATION = "阶段4_结果确认"  # 回溯验证
    STAGE5_FINAL_REPORT = "阶段5_完整报告"  # 详细报告 + 问答
    QA = "问答交互"                         # 持续问答
    COMPLETED = "完成"


class ConversationContext:
    """对话上下文（渐进式信息收集）"""
    def __init__(self):
        self.stage = ConversationStage.INIT

        # 阶段1：破冰信息
        self.question_category: Optional[str] = None  # 事业/感情/财运/健康/决策/其他
        self.random_numbers: List[int] = []  # 3个随机数字（1-9）
        self.xiaoliu_result: Optional[Dict[str, Any]] = None  # 小六壬快速判断

        # 阶段2：基础信息
        self.birth_info: Optional[Dict[str, Any]] = None  # 出生年月日时
        self.gender: Optional[str] = None  # male/female
        self.mbti_type: Optional[str] = None  # INTJ等
        self.birth_place: Optional[str] = None  # 出生地（可选）
        self.current_direction: Optional[str] = None  # 当前方位（可选）
        self.favorite_color: Optional[str] = None  # 喜欢的颜色（可选）
        self.related_character: Optional[str] = None  # 相关汉字（可选）

        # 阶段3：深度补充
        self.time_certainty: str = "unknown"  # certain/uncertain/unknown
        self.inferred_hour: Optional[int] = None  # 推断的时辰
        self.siblings_info: Optional[str] = None  # 兄弟姐妹信息（用于推时辰）
        self.face_features: Optional[str] = None  # 脸型特征（用于推时辰）
        self.sleep_habits: Optional[str] = None  # 作息习惯（用于推时辰）
        self.supplementary_numbers: List[int] = []  # 补充的随机数（用于六爻）

        # 阶段4：结果确认
        self.retrospective_events: List[Dict[str, Any]] = []  # 回溯的关键事件
        self.verification_feedback: List[Dict[str, Any]] = []  # 用户确认反馈
        self.theory_confidence_adjustment: Dict[str, float] = {}  # 理论置信度调整

        # 分析结果
        self.selected_theories: List[str] = []  # 选定的理论列表
        self.theory_results: Dict[str, Dict[str, Any]] = {}  # 各理论的计算结果
        self.bazi_result: Optional[Dict[str, Any]] = None
        self.qimen_result: Optional[Dict[str, Any]] = None
        self.liuren_result: Optional[Dict[str, Any]] = None
        self.liuyao_result: Optional[Dict[str, Any]] = None
        self.meihua_result: Optional[Dict[str, Any]] = None

        # 综合报告
        self.comprehensive_analysis: str = ""  # 详细分析
        self.retrospective_analysis: str = ""  # 回溯分析
        self.predictive_analysis: str = ""  # 预测分析
        self.actionable_advice: List[Dict[str, str]] = []  # 行动建议

        # 对话历史
        self.conversation_history: List[Dict[str, str]] = []  # {"role": "user/assistant", "content": "..."}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于保存）"""
        return {
            "stage": self.stage.value,
            "user_input_raw": self.user_input_raw,
            "birth_info": self.birth_info,
            "question": self.question,
            "bazi_result": self.bazi_result,
            "qimen_result": self.qimen_result,
            "liuren_result": self.liuren_result,
            "supplementary_results": self.supplementary_results,
            "synthesis_result": self.synthesis_result,
            "feedback_history": self.feedback_history,
            "conversation_history": self.conversation_history
        }


class ConversationService:
    """纯AI对话模式服务"""

    def __init__(self, api_manager: APIManager):
        self.api_manager = api_manager
        self.logger = get_logger(__name__)
        self.context = ConversationContext()

    async def start_conversation(
        self,
        progress_callback: Optional[Callable[[str, str, int], None]] = None
    ) -> str:
        """
        开始对话会话

        Args:
            progress_callback: 进度回调函数(stage, message, progress)

        Returns:
            欢迎消息
        """
        self.context = ConversationContext()
        self.context.stage = ConversationStage.INPUT_COLLECTION

        welcome_message = """
👋 欢迎使用赛博玄数 - AI智能对话模式

## 🎯 功能介绍

本模式采用**智能交互流程**，为您提供深度命理分析：

1️⃣ 收集您的出生信息和问题
2️⃣ 智能解析时间（AI自动识别）
3️⃣ 八字排盘 + 运势分析
4️⃣ 奇门遁甲 + 方位策略
5️⃣ 大六壬 + 事件过程
6️⃣ 生成综合分析和个性化建议
7️⃣ 补充占卜（如需要）
8️⃣ 常规问答对话

## 📝 请按以下格式输入信息

**必须包含以下两项**：

1. **您的出生时间**
   - ✅ 推荐格式：`我是1990年5月20日下午3点出生的`
   - ✅ 农历格式：`农历1985年三月初五早上出生`
   - ✅ 不确定时辰：`1990年5月20日出生，不记得具体时辰了`

2. **您想咨询的问题**
   - ✅ 示例：`想问问今年事业发展如何`
   - ✅ 示例：`最近财运怎么样`

**一句话示例**：`我是1990年5月20日下午3点出生的，想问问今年事业运势如何`

## ⚠️ 重要提醒

- ❌ **格式不正确会导致解析失败**，需要重新开启新对话
- ❌ 不要只发"你好"、"测一下"等无效信息
- ⏱️ 分析过程需要1-2分钟，请耐心等待
- 📊 系统会实时显示当前分析进度

💡 **提示**：信息越详细（包含出生时辰、性别、出生地等），分析结果越准确！

请在下方输入您的完整信息开始分析：
"""
        self.context.conversation_history.append({
            "role": "assistant",
            "content": welcome_message
        })

        return welcome_message

    async def process_user_input(
        self,
        user_message: str,
        progress_callback: Optional[Callable[[str, str, int], None]] = None
    ) -> str:
        """
        处理用户输入

        Args:
            user_message: 用户消息
            progress_callback: 进度回调

        Returns:
            AI回复消息
        """
        self.context.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # 根据当前阶段处理用户输入
        if self.context.stage == ConversationStage.INPUT_COLLECTION:
            return await self._handle_input_collection(user_message, progress_callback)

        elif self.context.stage == ConversationStage.FEEDBACK:
            return await self._handle_feedback(user_message, progress_callback)

        elif self.context.stage == ConversationStage.QA:
            return await self._handle_qa(user_message, progress_callback)

        else:
            return "系统正在处理中，请稍候..."

    async def _handle_input_collection(
        self,
        user_message: str,
        progress_callback: Optional[Callable[[str, str, int], None]] = None
    ) -> str:
        """处理输入收集阶段"""
        self.context.user_input_raw = user_message

        # 步骤2：调用Kimi解析时间信息
        if progress_callback:
            progress_callback("解析输入", "正在智能解析您的出生时间和问题...", 10)

        birth_info = await self._parse_birth_info(user_message)

        if not birth_info or "error" in birth_info:
            # 解析失败，要求重新输入
            return """
😅 抱歉，我没能完全理解您的信息。

请按以下格式重新输入：

**示例1**：我是1990年5月20日下午3点出生的，想问问今年事业运势如何

**示例2**：农历1985年三月初五早上出生，不记得具体时辰了，想看看最近财运

请重新输入：
"""

        self.context.birth_info = birth_info
        self.context.question = birth_info.get("question", "")
        self.context.stage = ConversationStage.TIME_PARSING

        # 确认信息
        certainty = birth_info.get("time_certainty", "uncertain")
        certainty_text = {
            "certain": "✅ 明确",
            "uncertain": "⚠️ 模糊",
            "unknown": "❓ 不记得"
        }.get(certainty, "未知")

        confirmation = f"""
📊 **信息确认**

✅ 出生日期：{birth_info.get('year')}年{birth_info.get('month')}月{birth_info.get('day')}日
⏰ 出生时辰：{birth_info.get('hour', '未提供')}时 （{certainty_text}）
📝 咨询问题：{self.context.question}

---

🔮 系统正在为您进行深度分析，请稍候...

进度：[步骤1/9] 正在排八字命盘...
"""
        self.context.conversation_history.append({
            "role": "assistant",
            "content": confirmation
        })

        # 自动进入下一阶段
        await self._run_analysis_pipeline(progress_callback)

        # 生成完整分析报告
        final_report = self._generate_final_report()

        # 添加到对话历史
        self.context.conversation_history.append({
            "role": "assistant",
            "content": final_report
        })

        # 返回确认消息 + 完整报告
        return confirmation + "\n\n" + final_report

    async def _parse_birth_info(self, user_message: str) -> Dict[str, Any]:
        """
        调用Kimi解析出生信息

        Returns:
            {"year": 1990, "month": 5, "day": 20, "hour": 15, "time_certainty": "certain", "question": "..."}
        """
        prompt = f"""你是一个智能时间解析助手。请从用户的输入中提取出生时间和问题。

用户输入：
{user_message}

请分析并返回JSON格式（严格遵循格式，不要有任何额外文字）：

```json
{{
    "year": 年份(整数),
    "month": 月份(整数1-12),
    "day": 日期(整数1-31),
    "hour": 时辰(整数0-23, 如果用户说"下午3点"则为15, 如果没提供则为null),
    "minute": 分钟(整数0-59, 没提供则为0),
    "calendar_type": "solar"或"lunar",
    "time_certainty": "certain"(明确)或"uncertain"(模糊，如"大概下午")或"unknown"(不记得),
    "gender": "male"或"female"(如果用户提供性别信息),
    "question": "用户的问题描述"
}}
```

**重要提取规则（请严格遵守）**：

1. **明确时辰（time_certainty="certain"）**：
   - 用户说"下午3点"、"15点"、"下午三点"等 → hour为15，time_certainty为"certain"
   - 用户说"早上8点"、"上午10点" → hour为具体时间，time_certainty为"certain"

2. **模糊时辰（time_certainty="uncertain"）**：
   - 用户说"早上"、"上午"但没具体时间 → hour为9，time_certainty为"uncertain"
   - 用户说"中午" → hour为12，time_certainty为"uncertain"
   - 用户说"下午" → hour为15，time_certainty为"uncertain"
   - 用户说"晚上"、"夜里" → hour为20，time_certainty为"uncertain"
   - 用户说"大概下午"、"大约中午" → 对应时间，time_certainty为"uncertain"

3. **不记得时辰（time_certainty="unknown"）**：
   - 用户说"不记得时辰"、"忘了具体时间"、"时辰不确定"、"不知道时间" → hour为null，time_certainty为"unknown"
   - 用户完全没提供任何时间相关信息 → hour为null，time_certainty为"unknown"

4. **历法类型**：
   - 默认为阳历(solar)
   - 用户明确说"农历"、"阴历"、"农历日期"、"农历生日" → calendar_type为"lunar"

5. **性别信息**：
   - 如果用户提到"男"、"女"、"女生"、"男性"等性别信息，提取gender字段
   - 未提及则gender不填（null）

6. **问题描述**：
   - 提取用户想咨询的事项，如"事业运势"、"财运如何"、"婚姻"等

只返回JSON，不要有其他任何文字：
"""

        try:
            response = await self.api_manager.call_api(
                task_type="简单问题解答",
                prompt=prompt,
                enable_dual_verification=False
            )

            # 提取JSON
            import re
            json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
            if json_match:
                birth_info = json.loads(json_match.group())
                self.logger.info(f"成功解析出生信息: {birth_info}")
                return birth_info
            else:
                self.logger.error(f"Kimi返回格式错误: {response}")
                return {"error": "解析失败"}

        except Exception as e:
            self.logger.error(f"解析出生信息失败: {e}")
            return {"error": str(e)}

    async def _run_analysis_pipeline(
        self,
        progress_callback: Optional[Callable[[str, str, int], None]] = None
    ):
        """
        运行完整的9步分析流程
        """
        try:
            # 步骤3：排八字 + Deepseek分析
            if progress_callback:
                progress_callback("八字分析", "正在排四柱命盘并分析运势...", 20)
            await self._step_bazi_analysis(progress_callback)

            # 步骤4：起奇门局 + Deepseek分析
            if progress_callback:
                progress_callback("奇门分析", "正在排奇门遁甲局盘，分析方位策略...", 40)
            await self._step_qimen_analysis(progress_callback)

            # 步骤5：起六壬课 + Deepseek分析
            if progress_callback:
                progress_callback("六壬分析", "正在排大六壬课体，细化事件过程...", 60)
            await self._step_liuren_analysis(progress_callback)

            # 步骤6：综合生成回溯和预测
            if progress_callback:
                progress_callback("综合分析", "正在综合多个术数理论，生成完整报告...", 80)
            await self._step_synthesis(progress_callback)

            # 步骤7：检查是否需要补充占卜
            if await self._check_need_supplementary():
                if progress_callback:
                    progress_callback("补充占卜", "信息不足，启动补充占卜...", 85)
                await self._step_supplementary(progress_callback)

            # 步骤8：进入反馈确认阶段
            self.context.stage = ConversationStage.FEEDBACK
            if progress_callback:
                progress_callback("完成分析", "分析完成，正在为您呈现结果...", 100)

        except Exception as e:
            self.logger.error(f"分析流程出错: {e}")
            raise

    async def _step_bazi_analysis(self, progress_callback):
        """步骤3：八字分析"""
        # 创建UserInput对象
        user_input = UserInput(
            question_type="综合运势",
            question_description=self.context.question,
            birth_year=self.context.birth_info.get("year"),
            birth_month=self.context.birth_info.get("month"),
            birth_day=self.context.birth_info.get("day"),
            birth_hour=self.context.birth_info.get("hour"),
            calendar_type=self.context.birth_info.get("calendar_type", "solar"),
            birth_time_certainty=self.context.birth_info.get("time_certainty", "uncertain")
        )

        # 排八字
        calculator = BaZiCalculator()
        bazi_data = calculator.calculate_full_bazi(
            year=self.context.birth_info.get("year"),
            month=self.context.birth_info.get("month"),
            day=self.context.birth_info.get("day"),
            hour=self.context.birth_info.get("hour"),
            gender=self.context.birth_info.get("gender"),
            calendar_type=self.context.birth_info.get("calendar_type", "solar")
        )

        self.context.bazi_result = bazi_data

        # 调用Deepseek分析
        prompt = f"""你是一位精通八字命理的专家。请根据以下八字命盘，分析用户的运势。

用户问题：{self.context.question}

八字命盘：
```json
{json.dumps(bazi_data, ensure_ascii=False, indent=2)}
```

请提取以下关键信息（100-150字）：
1. 用神（最重要的五行）
2. 当前运势特点（如"今年财运不佳，但有贵人"）
3. 关键词（3-5个，如"财运弱"、"有贵人"、"驿马动"）

格式：
**用神**：X
**运势**：...
**关键词**：A、B、C
"""

        analysis = await self.api_manager.call_api(
            task_type="快速交互问答",
            prompt=prompt,
            enable_dual_verification=False
        )

        self.context.bazi_result["ai_analysis"] = analysis
        self.logger.info("八字分析完成")

    async def _step_qimen_analysis(self, progress_callback):
        """步骤4：奇门分析"""
        # 使用当前时间起奇门局
        calculator = QiMenCalculator()
        current_time = datetime.now()

        qimen_data = calculator.calculate_qimen(current_time)
        self.context.qimen_result = qimen_data

        # 调用Deepseek分析
        bazi_yongshen = self._extract_yongshen_from_bazi()

        prompt = f"""你是一位精通奇门遁甲的专家。请根据以下奇门局盘，结合八字用神和用户问题，分析方位策略。

用户问题：{self.context.question}
八字用神：{bazi_yongshen}

奇门局盘：
```json
{json.dumps(qimen_data, ensure_ascii=False, indent=2)}
```

请提取以下关键信息（100字）：
1. 吉凶方位（如"东南方吉，西北方凶"）
2. 行动策略（如"宜主动出击"、"宜守不宜攻"）
3. 时机建议

格式：
**方位**：...
**策略**：...
**时机**：...
"""

        analysis = await self.api_manager.call_api(
            task_type="快速交互问答",
            prompt=prompt,
            enable_dual_verification=False
        )

        self.context.qimen_result["ai_analysis"] = analysis
        self.logger.info("奇门分析完成")

    async def _step_liuren_analysis(self, progress_callback):
        """步骤5：六壬分析"""
        calculator = DaLiuRenCalculator()
        current_time = datetime.now()

        liuren_data = calculator.calculate_daliuren(
            year=current_time.year,
            month=current_time.month,
            day=current_time.day,
            hour=current_time.hour,
            question=self.context.question
        )
        self.context.liuren_result = liuren_data

        # 调用Deepseek分析
        prompt = f"""你是一位精通大六壬的专家。请根据以下六壬课体，细化事件发展过程。

用户问题：{self.context.question}

六壬课体：
```json
{json.dumps(liuren_data, ensure_ascii=False, indent=2)}
```

请提取以下关键信息（100字）：
1. 事件发展阶段（如"初期、中期、后期"）
2. 关键转折点
3. 最终结果倾向

格式：
**发展过程**：...
**转折点**：...
**结果倾向**：...
"""

        analysis = await self.api_manager.call_api(
            task_type="快速交互问答",
            prompt=prompt,
            enable_dual_verification=False
        )

        self.context.liuren_result["ai_analysis"] = analysis
        self.logger.info("六壬分析完成")

    async def _step_synthesis(self, progress_callback):
        """步骤6：综合分析"""
        # 动态计算时间范围
        current_year = datetime.now().year
        past_years = f"{current_year-3}至{current_year-1}"
        future_months = 6

        prompt = f"""你是一位综合命理大师。请基于八字、奇门、六壬三种术数的分析结果，为用户生成完整的分析报告。

用户问题：{self.context.question}

## 八字分析
{self.context.bazi_result.get('ai_analysis', '')}

## 奇门分析
{self.context.qimen_result.get('ai_analysis', '')}

## 六壬分析
{self.context.liuren_result.get('ai_analysis', '')}

---

请生成完整报告（300-400字），包含：

### 一、过去回溯（{past_years}年）
分析过去几年的运势走势，指出关键转折点

### 二、当前状况
综合三个理论，说明当前运势特点

### 三、未来预测（未来{future_months}个月）
给出具体的时间建议和行动方案

### 四、综合建议
3-5条可执行的建议

请使用Markdown格式，语气温和专业，使用"您"而非"你"。
"""

        synthesis = await self.api_manager.call_api(
            task_type="综合报告解读",
            prompt=prompt,
            enable_dual_verification=False
        )

        self.context.synthesis_result = synthesis
        self.logger.info("综合分析完成")

    async def _check_need_supplementary(self) -> bool:
        """检查是否需要补充占卜"""
        # 检查八字中是否时辰不明确
        if self.context.birth_info.get("time_certainty") in ["uncertain", "unknown"]:
            return True

        # 检查分析结果是否有不确定性
        # 这里简化处理，实际可以用AI判断
        return False

    async def _step_supplementary(self, progress_callback):
        """步骤7：补充占卜"""
        # 这里需要用户提供随机数或摇卦
        # 暂时标记为待实现
        self.logger.info("补充占卜（待用户提供随机数）")
        pass

    def _generate_final_report(self) -> str:
        """生成最终分析报告"""
        report = f"""
## 🎯 智能分析报告

{self.context.synthesis_result if self.context.synthesis_result else ""}

---

### 📊 八字命盘

{self.context.bazi_result.get('ai_analysis', '（未分析）') if self.context.bazi_result else '（未分析）'}

---

### 🧭 奇门遁甲

{self.context.qimen_result.get('ai_analysis', '（未分析）') if self.context.qimen_result else '（未分析）'}

---

### 🔮 大六壬

{self.context.liuren_result.get('ai_analysis', '（未分析）') if self.context.liuren_result else '（未分析）'}

---

💬 **如有疑问，欢迎继续提问！**
"""
        return report.strip()

    async def _handle_feedback(self, user_message: str, progress_callback) -> str:
        """处理反馈确认阶段"""
        # 步骤8：向用户呈现部分结果并确认

        # 生成确认问题
        confirmation_question = await self._generate_confirmation_question()

        # 记录用户反馈
        self.context.feedback_history.append({
            "question": confirmation_question,
            "answer": user_message
        })

        # 根据反馈调整分析
        # （这里可以调用AI重新分析）

        # 如果确认完成，进入QA阶段
        if len(self.context.feedback_history) >= 2:  # 确认2-3个关键点
            self.context.stage = ConversationStage.QA

            final_report = f"""
## 🎯 完整分析报告

{self.context.synthesis_result}

---

✅ **分析已完成！**

您可以继续提问，我会为您详细解答。例如：
- "为什么说我2019年有财务损失？"
- "如何化解不利的影响？"
- "具体应该什么时候行动？"

请输入您的问题：
"""
            self.context.conversation_history.append({
                "role": "assistant",
                "content": final_report
            })
            return final_report

        # 继续确认下一个关键点
        return await self._generate_confirmation_question()

    async def _generate_confirmation_question(self) -> str:
        """生成确认问题"""
        # 从分析结果中提取关键点进行确认
        prompt = f"""基于以下分析结果，生成一个关键确认问题（一句话）。

分析结果：
{self.context.synthesis_result[:500]}

要求：
1. 问题应该是可以验证的事实（如"您是否在2019年经历过财务损失？"）
2. 一句话，简洁明了
3. 不要问太私密的问题

只返回问题，不要其他文字：
"""

        question = await self.api_manager.call_api(
            task_type="简单问题解答",
            prompt=prompt,
            enable_dual_verification=False
        )

        return question.strip()

    async def _handle_qa(self, user_message: str, progress_callback) -> str:
        """处理问答阶段"""
        # 步骤9：常规答疑对话

        # 调用AI回答用户问题，基于分析结果
        prompt = f"""你是一位温和专业的命理咨询师。用户刚刚看完分析报告，现在有疑问。

完整分析报告：
{self.context.synthesis_result}

八字分析：
{self.context.bazi_result.get('ai_analysis', '')}

奇门分析：
{self.context.qimen_result.get('ai_analysis', '')}

六壬分析：
{self.context.liuren_result.get('ai_analysis', '')}

历史对话：
{json.dumps(self.context.conversation_history[-5:], ensure_ascii=False, indent=2)}

用户问题：{user_message}

---

请回答用户的问题（150-200字），要求：
1. 基于报告内容回答，不要编造
2. 温和、专业，给予情绪支持
3. 使用"您"而非"你"
4. 如果涉及心理问题，给予积极引导
5. 强调"最终决定权在您手中"

请回答：
"""

        answer = await self.api_manager.call_api(
            task_type="快速交互问答",
            prompt=prompt,
            enable_dual_verification=False
        )

        self.context.conversation_history.append({
            "role": "assistant",
            "content": answer
        })

        return answer

    def _extract_yongshen_from_bazi(self) -> str:
        """从八字分析中提取用神"""
        if self.context.bazi_result and "ai_analysis" in self.context.bazi_result:
            analysis = self.context.bazi_result["ai_analysis"]
            # 简单提取
            import re
            match = re.search(r'\*\*用神\*\*[：:]\s*(\S+)', analysis)
            if match:
                return match.group(1)
        return "未知"

    def save_conversation(self) -> Dict[str, Any]:
        """保存对话内容（用于历史记录）"""
        return {
            "timestamp": datetime.now().isoformat(),
            "context": self.context.to_dict(),
            "full_conversation": self.context.conversation_history
        }

    def reset(self):
        """重置对话（发起新对话）"""
        self.context = ConversationContext()
        self.logger.info("对话已重置")
