"""
ConversationService - 纯AI对话模式服务（委托重构版）

实现渐进式5阶段智能交互流程：
阶段1_破冰：事项分类 + 3个随机数字 → 小六壬快速初判
阶段2_基础信息：出生年月日、性别、MBTI等 → 展示可用理论
阶段3_深度补充：针对性补充信息（时辰推断、额外占卜）
阶段4_结果确认：回溯验证（过去3-5年关键事件）
阶段5_完整报告：生成详细分析报告 + 常规问答

架构说明：
本模块采用委托模式，将具体逻辑委托给专门的处理器：
- NLPParser: 自然语言解析
- QAHandler: 问答处理
- ReportGenerator: 报告生成
"""

import json
from typing import Dict, Any, Optional, Callable
from datetime import datetime

from api.manager import APIManager
from models import UserInput
from theories.bazi.theory import BaZiTheory
from theories.qimen.theory import QiMenTheory
from theories.daliuren.theory import DaLiuRenTheory
from theories.xiaoliu.theory import XiaoLiuRenTheory
from core.theory_selector import TheorySelector
from utils.logger import get_logger

# 从新模块导入（委托目标）
from services.conversation.context import (
    ConversationStage,
    ConversationContext,
    MAX_CONVERSATION_HISTORY
)
from services.conversation.nlp_parser import NLPParser
from services.conversation.qa_handler import QAHandler, DEFAULT_QA_KEYWORDS
from services.conversation.report_generator import ReportGenerator, ConversationExporter
from utils.usage_stats_manager import get_usage_stats_manager


# 导出公共接口（向后兼容）
__all__ = [
    'ConversationStage',
    'ConversationContext',
    'ConversationService',
    'MAX_CONVERSATION_HISTORY',
]


class ConversationService:
    """
    纯AI对话模式服务（委托重构版）

    采用委托模式，将具体处理逻辑分发给专门的处理器，
    保持公共API不变以确保向后兼容。
    """

    # 问题类别映射
    QUESTION_CATEGORIES = {
        "事业": ["工作", "职业", "事业", "跳槽", "升职", "创业"],
        "感情": ["感情", "恋爱", "婚姻", "姻缘", "桃花", "分手"],
        "财运": ["财运", "财富", "赚钱", "投资", "理财", "收入"],
        "健康": ["健康", "身体", "疾病", "养生"],
        "学业": ["学业", "考试", "学习", "升学"],
        "决策": ["决定", "选择", "是否"],
        "其他": []
    }

    def __init__(self, api_manager: APIManager, config: Optional[Dict[str, Any]] = None):
        self.api_manager = api_manager
        self.logger = get_logger(__name__)
        self.config = config or {}

        # 初始化上下文
        self.context = ConversationContext()

        # 初始化理论组件
        self.theory_selector = TheorySelector()
        self.xiaoliu_theory = XiaoLiuRenTheory()

        # 加载配置
        self._load_config()

        # 初始化委托处理器
        self._init_handlers()

    def _load_config(self):
        """加载配置"""
        conversation_config = self.config.get("conversation", {})
        qa_keywords_config = conversation_config.get("qa_keywords", {})
        self.qa_keywords = qa_keywords_config if qa_keywords_config else DEFAULT_QA_KEYWORDS
        self.max_history = conversation_config.get("max_history", MAX_CONVERSATION_HISTORY)

    def _init_handlers(self):
        """初始化委托处理器"""
        self.nlp_parser = NLPParser(self.api_manager)
        self.qa_handler = QAHandler(self.api_manager, self.context, self.qa_keywords)
        self.report_generator = ReportGenerator(self.api_manager, self.context)
        self.exporter = ConversationExporter(self.context)

    # ==================== 公共API ====================

    async def start_conversation(
        self,
        progress_callback: Optional[Callable[[str, str, int], None]] = None
    ) -> str:
        """开始对话会话 - 阶段1破冰"""
        self.context = ConversationContext()
        self.context.stage = ConversationStage.STAGE1_ICEBREAK
        self._init_handlers()

        welcome_message = """👋 欢迎使用赛博玄数 - AI智能对话模式

## 🎯 智能交互流程

本模式采用**渐进式5阶段**深度对话，为您提供专业命理分析：

1️⃣ **破冰阶段**：快速了解您的需求，提供初步判断
2️⃣ **信息收集**：详细收集出生信息，展示可用理论
3️⃣ **深度分析**：针对性补充信息，提升准确度
4️⃣ **结果验证**：回顾过去事件，确认分析方向
5️⃣ **完整报告**：生成详细报告，持续答疑解惑

---

## 📝 请告诉我您想咨询什么

### 请提供以下信息：

1. **咨询事项**：您想咨询什么？（事业/感情/财运/健康/学业/决策/其他）
2. **问题描述**：简单描述您的具体问题
3. **随机数字**：请提供3个1-9的随机数字（用于小六壬起卦）

**💡 示例**：
```
我想咨询事业，最近在考虑是否要跳槽
数字是：7、3、5
```

请输入您的咨询内容：
"""
        self._add_message("assistant", welcome_message)
        return welcome_message

    async def process_user_input(
        self,
        user_message: str,
        progress_callback: Optional[Callable[[str, str, int], None]] = None
    ) -> str:
        """处理用户输入（路由到对应阶段）"""
        self._add_message("user", user_message)
        stage = self.context.stage

        try:
            # INIT 阶段也当作破冰阶段处理（用户可能在欢迎消息之前就发送了消息）
            if stage in (ConversationStage.INIT, ConversationStage.STAGE1_ICEBREAK):
                response = await self._handle_stage1(user_message, progress_callback)
            elif stage == ConversationStage.STAGE2_BASIC_INFO:
                response = await self._handle_stage2(user_message, progress_callback)
            elif stage == ConversationStage.STAGE3_SUPPLEMENT:
                response = await self._handle_stage3(user_message, progress_callback)
            elif stage == ConversationStage.STAGE4_VERIFICATION:
                response = await self._handle_stage4(user_message, progress_callback)
            elif stage == ConversationStage.STAGE5_FINAL_REPORT:
                response = await self._handle_stage5(progress_callback)
            elif stage in (ConversationStage.QA, ConversationStage.COMPLETED):
                response = await self._handle_qa(user_message, progress_callback)
            else:
                response = "系统错误：未知的对话阶段"
                self.logger.error(f"未知对话阶段: {stage}")

            self._add_message("assistant", response)
            return response

        except Exception as e:
            self.logger.error(f"处理用户输入失败: {e}")
            error_msg = f"抱歉，处理您的输入时遇到问题：{str(e)}\n请重试或换个方式表达。"
            self._add_message("assistant", error_msg)
            return error_msg

    # ==================== 阶段处理 ====================

    async def _handle_stage1(self, user_message: str, progress_callback) -> str:
        """阶段1：破冰 - 解析问题和随机数字，小六壬起卦"""
        # 开始会话追踪
        try:
            stats_manager = get_usage_stats_manager()
            session_id = stats_manager.start_session(
                module='wendao',
                stage='stage1_icebreak'
            )
            self.context.session_id = session_id
        except Exception as e:
            self.logger.warning(f"开始会话追踪失败: {e}")

        if progress_callback:
            progress_callback("阶段1", "正在解析您的问题和随机数字...", 10)

        parsed_info = await self.nlp_parser.parse_icebreak_input(user_message)
        if not parsed_info or "error" in parsed_info:
            return self._retry_msg("stage1")

        self.context.question_category = parsed_info.get("category")
        self.context.question_description = parsed_info.get("description", "")
        self.context.random_numbers = parsed_info.get("numbers", [])

        if progress_callback:
            progress_callback("小六壬", "正在用小六壬起卦...", 30)

        xiaoliu_result = self._calculate_xiaoliu()
        self.context.xiaoliu_result = xiaoliu_result

        if progress_callback:
            progress_callback("小六壬", "正在生成初步判断...", 50)

        interpretation = await self._interpret_xiaoliu(xiaoliu_result)
        self.context.stage = ConversationStage.STAGE2_BASIC_INFO

        if progress_callback:
            progress_callback("阶段1", "破冰阶段完成", 100)

        return f"""✅ **信息已收集**

📋 咨询事项：{self.context.question_category}
🔢 随机数字：{', '.join(map(str, self.context.random_numbers))}

---

## 🔮 小六壬快速判断

{interpretation}

---

## 📝 接下来，请告诉我您的出生信息

### 必需信息：
1. **出生年月日**（如：1990年5月20日）
2. **出生时辰**（如：下午3点，或"不记得了"）

### 可选信息：
3. 性别（男/女）
4. MBTI类型（如：INTJ）

**💡 示例**：`我是1990年5月20日下午3点出生的，男，INTJ`

请输入您的出生信息：
"""

    async def _handle_stage2(self, user_message: str, progress_callback) -> str:
        """阶段2：基础信息收集"""
        # 更新会话阶段
        self._update_session_stage('stage2_basic_info')

        if progress_callback:
            progress_callback("阶段2", "正在解析您的出生信息...", 60)

        birth_info = await self.nlp_parser.parse_birth_info(user_message)
        if not birth_info or "error" in birth_info:
            return self._retry_msg("stage2")

        self.context.birth_info = birth_info
        self.context.gender = birth_info.get("gender")
        self.context.mbti_type = birth_info.get("mbti")
        self.context.time_certainty = birth_info.get("time_certainty", "unknown")

        if progress_callback:
            progress_callback("理论选择", "正在计算理论适配度...", 75)

        theories_display = await self._calculate_theory_fitness()
        need_supplement = self.context.time_certainty in ("uncertain", "unknown")

        self.context.stage = ConversationStage.STAGE3_SUPPLEMENT if need_supplement else ConversationStage.STAGE4_VERIFICATION

        birth_str = f"{birth_info.get('year')}年{birth_info.get('month')}月{birth_info.get('day')}日"
        if birth_info.get('hour') is not None:
            birth_str += f" {birth_info.get('hour')}时"

        time_status = {"certain": "✅ 确定", "uncertain": "⚠️ 不确定", "unknown": "❓ 未知"}.get(self.context.time_certainty, "未知")

        response = f"""✅ **出生信息已收集**

📅 出生时间：{birth_str}
⏰ 时辰确定性：{time_status}
👤 性别：{self.context.gender or '未提供'}
🧠 MBTI：{self.context.mbti_type or '未提供'}

---

## 📊 可用分析理论

{theories_display}

---
"""
        if need_supplement:
            response += """
## 📝 需要补充信息

为提高分析准确度，请回答：
1. **兄弟姐妹排行？**（老大/老二/独生）
2. **脸型特征？**（圆脸/方脸/瓜子脸）
3. **通常几点入睡？**

请回答以上问题：
"""
        else:
            response += f"""
## ⏪ 回溯验证

请简单回答：过去3年中，在{self.context.question_category}领域是否有重大变化？

例如：2023年换了工作 / 最近几年比较平稳

请简单描述：
"""
        return response

    async def _handle_stage3(self, user_message: str, progress_callback) -> str:
        """阶段3：深度补充 - 时辰推断"""
        # 更新会话阶段
        self._update_session_stage('stage3_supplement')

        if progress_callback:
            progress_callback("阶段3", "正在分析补充信息...", 80)

        if self.context.time_certainty in ("uncertain", "unknown"):
            inferred_hour = await self.nlp_parser.infer_birth_hour(user_message)
            if inferred_hour is not None:
                self.context.inferred_hour = inferred_hour
                self.context.time_certainty = "inferred"
                if self.context.birth_info:
                    self.context.birth_info["hour"] = inferred_hour

        self.context.stage = ConversationStage.STAGE4_VERIFICATION

        hour_info = ""
        if self.context.inferred_hour is not None:
            hour_names = {0: "子", 1: "丑", 3: "寅", 5: "卯", 7: "辰", 9: "巳", 11: "午", 13: "未", 15: "申", 17: "酉", 19: "戌", 21: "亥", 23: "子"}
            hour_name = hour_names.get(self.context.inferred_hour, "未知")
            hour_info = f"\n\n🔮 **推断时辰**：{hour_name}时（{self.context.inferred_hour}点）"

        return f"""✅ **补充信息已收集**{hour_info}

---

## ⏪ 回溯验证

请简单回答：过去3年中，在{self.context.question_category}领域是否有重大变化？

请简单描述：
"""

    async def _handle_stage4(self, user_message: str, progress_callback) -> str:
        """阶段4：结果验证"""
        # 更新会话阶段
        self._update_session_stage('stage4_verification')

        if progress_callback:
            progress_callback("阶段4", "正在分析验证反馈...", 85)

        feedback = await self.nlp_parser.parse_verification_feedback(
            user_message,
            self.context.retrospective_events  # 传入回溯事件列表
        )
        if feedback:
            self.context.verification_feedback.append({"raw_message": user_message, "parsed_feedback": feedback})
            self._adjust_confidence(feedback)

        if progress_callback:
            progress_callback("深度分析", "正在进行深度分析...", 90)

        await self._run_deep_analysis(progress_callback)
        self.context.stage = ConversationStage.STAGE5_FINAL_REPORT

        return await self._handle_stage5(progress_callback)

    async def _handle_stage5(self, progress_callback) -> str:
        """阶段5：生成最终报告"""
        if progress_callback:
            progress_callback("报告生成", "正在生成综合分析报告...", 95)

        self.report_generator.context = self.context
        report = await self.report_generator.generate_final_report()
        self.context.stage = ConversationStage.QA

        if progress_callback:
            progress_callback("完成", "报告生成完成", 100)

        # 记录使用统计
        try:
            stats_manager = get_usage_stats_manager()
            primary_theory = self.context.selected_theories[0] if self.context.selected_theories else None
            stats_manager.record_usage(
                module='wendao',
                theory=primary_theory,
                question_type=self.context.question_category
            )
            # 标记会话完成
            if self.context.session_id:
                stats_manager.complete_session(
                    session_id=self.context.session_id,
                    theory=primary_theory,
                    question_type=self.context.question_category
                )
        except Exception as e:
            self.logger.warning(f"记录使用统计失败: {e}")

        return report

    async def _handle_qa(self, user_message: str, progress_callback) -> str:
        """处理问答阶段"""
        self.qa_handler.context = self.context
        return await self.qa_handler.handle(user_message, progress_callback)

    # ==================== 辅助方法 ====================

    def _add_message(self, role: str, content: str):
        """添加消息到对话历史"""
        self.context.conversation_history.append({"role": role, "content": content})
        if len(self.context.conversation_history) > self.max_history:
            self.context.conversation_history = self.context.conversation_history[-self.max_history:]

    def _update_session_stage(self, stage: str):
        """更新会话阶段（用于追踪流失点）"""
        if self.context.session_id:
            try:
                stats_manager = get_usage_stats_manager()
                stats_manager.update_session_stage(self.context.session_id, stage)
            except Exception as e:
                self.logger.warning(f"更新会话阶段失败: {e}")

    def _calculate_xiaoliu(self) -> Dict[str, Any]:
        """计算小六壬"""
        user_input = UserInput(
            question_type=self.context.question_category,
            question_description=self.context.question_description,
            numbers=self.context.random_numbers,
            current_time=datetime.now()
        )
        return self.xiaoliu_theory.calculate(user_input)

    async def _interpret_xiaoliu(self, result: Dict[str, Any]) -> str:
        """用AI解读小六壬结果"""
        prompt = f"""你是一位精通小六壬的占卜师。请根据以下小六壬卦象，给出简洁的初步判断。

问题类别：{self.context.question_category}
问题描述：{self.context.question_description}

小六壬结果：
```json
{json.dumps(result, ensure_ascii=False, indent=2)}
```

请生成简洁的解读（80-100字），包括落宫吉凶和初步建议。
"""
        try:
            return (await self.api_manager.call_api(task_type="快速交互问答", prompt=prompt, enable_dual_verification=False)).strip()
        except Exception as e:
            self.logger.error(f"小六壬解读失败: {e}")
            return f"📍 落宫：{result.get('时落宫', '未知')}\n\n（系统繁忙，将在后续分析中补充详细解读）"

    async def _calculate_theory_fitness(self) -> str:
        """计算理论适配度"""
        user_input = UserInput(
            question_type=self.context.question_category,
            question_description=self.context.question_description,
            birth_year=self.context.birth_info.get("year") if self.context.birth_info else None,
            birth_month=self.context.birth_info.get("month") if self.context.birth_info else None,
            birth_day=self.context.birth_info.get("day") if self.context.birth_info else None,
            birth_hour=self.context.birth_info.get("hour") if self.context.birth_info else None,
            gender=self.context.gender,
            mbti_type=self.context.mbti_type,
            current_time=datetime.now()
        )
        selected, _ = self.theory_selector.select_theories(user_input, max_theories=6, min_theories=3)
        self.context.selected_theories = selected

        # 格式化理论列表（支持字典列表和字符串列表）
        theory_lines = []
        for i, t in enumerate(selected, 1):
            if isinstance(t, dict):
                theory_lines.append(f"{i}. **{t}**")
            else:
                theory_lines.append(f"{i}. **{t}**")
        return "\n".join(theory_lines)

    def _adjust_confidence(self, feedback: Dict[str, Any]):
        """调整理论置信度"""
        # 使用 accuracy_score 字段（0-1之间）
        accuracy_score = feedback.get("accuracy_score", 0.5)
        adj = 1.1 if accuracy_score >= 0.8 else (1.0 if accuracy_score >= 0.5 else 0.9)

        for theory_item in self.context.selected_theories:
            # selected_theories 可能是字典列表或字符串列表
            if isinstance(theory_item, dict):
                theory_name = theory_item.get('theory', str(theory_item))
            else:
                theory_name = str(theory_item)
            self.context.theory_confidence_adjustment[theory_name] = adj

    async def _run_deep_analysis(self, progress_callback):
        """执行深度分析"""
        if not self.context.birth_info:
            return

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

        if "八字" in self.context.selected_theories:
            if progress_callback:
                progress_callback("八字", "正在计算八字命盘...", 92)
            try:
                self.context.bazi_result = BaZiTheory().calculate(user_input)
            except Exception as e:
                self.logger.error(f"八字计算失败: {e}")

        if "奇门遁甲" in self.context.selected_theories:
            if progress_callback:
                progress_callback("奇门", "正在起奇门局...", 94)
            try:
                self.context.qimen_result = QiMenTheory().calculate(user_input)
            except Exception as e:
                self.logger.error(f"奇门计算失败: {e}")

        if "大六壬" in self.context.selected_theories:
            if progress_callback:
                progress_callback("六壬", "正在起六壬课...", 96)
            try:
                self.context.liuren_result = DaLiuRenTheory().calculate(user_input)
            except Exception as e:
                self.logger.error(f"六壬计算失败: {e}")

    def _retry_msg(self, stage: str) -> str:
        """生成重试提示"""
        if stage == "stage1":
            return """😅 抱歉，我没能完全理解您的信息。

请按以下格式重新输入：
```
我想咨询事业，最近想跳槽
数字是：7、3、5
```
"""
        else:
            return """😅 抱歉，我没能理解您的出生信息。

请按以下格式重新输入：
```
1990年5月20日下午3点，男，INTJ
```
"""

    # ==================== 工具方法 ====================

    def save_conversation(self) -> Dict[str, Any]:
        """保存对话内容"""
        self.exporter.context = self.context
        return self.exporter.to_save_dict()

    def get_conversation_summary(self) -> Dict[str, Any]:
        """获取对话摘要"""
        self.exporter.context = self.context
        return self.exporter.get_summary()

    def get_conversation_statistics(self) -> Dict[str, Any]:
        """获取对话统计信息"""
        self.exporter.context = self.context
        return self.exporter.get_statistics()

    def get_progress_percentage(self) -> int:
        """获取对话进度百分比"""
        progress = {
            ConversationStage.INIT: 0, ConversationStage.STAGE1_ICEBREAK: 20,
            ConversationStage.STAGE2_BASIC_INFO: 40, ConversationStage.STAGE3_SUPPLEMENT: 60,
            ConversationStage.STAGE4_VERIFICATION: 80, ConversationStage.STAGE5_FINAL_REPORT: 95,
            ConversationStage.QA: 100, ConversationStage.COMPLETED: 100
        }
        return progress.get(self.context.stage, 0)

    def reset(self):
        """重置对话"""
        self.context = ConversationContext()
        self._init_handlers()
        self.logger.info("对话已重置")

    def get_current_stage(self) -> str:
        """获取当前对话阶段"""
        return self.context.stage.value

    def get_stage_description(self) -> str:
        """获取当前阶段描述"""
        desc = {
            ConversationStage.INIT: "对话初始化",
            ConversationStage.STAGE1_ICEBREAK: "阶段1：破冰 - 快速了解您的问题",
            ConversationStage.STAGE2_BASIC_INFO: "阶段2：信息收集 - 获取出生信息和理论适配度",
            ConversationStage.STAGE3_SUPPLEMENT: "阶段3：深度补充 - 完善时辰等关键信息",
            ConversationStage.STAGE4_VERIFICATION: "阶段4：结果确认 - 回溯验证提高准确度",
            ConversationStage.STAGE5_FINAL_REPORT: "阶段5：生成报告 - 综合分析和建议",
            ConversationStage.QA: "问答交互 - 随时为您答疑解惑",
            ConversationStage.COMPLETED: "对话已完成"
        }
        return desc.get(self.context.stage, "未知阶段")

    def export_to_markdown(self) -> str:
        """将对话导出为Markdown格式"""
        self.exporter.context = self.context
        return self.exporter.export_to_markdown()

    def can_skip_to_stage(self, target_stage: ConversationStage) -> bool:
        """检查是否可以跳转到指定阶段"""
        order = [
            ConversationStage.INIT, ConversationStage.STAGE1_ICEBREAK,
            ConversationStage.STAGE2_BASIC_INFO, ConversationStage.STAGE3_SUPPLEMENT,
            ConversationStage.STAGE4_VERIFICATION, ConversationStage.STAGE5_FINAL_REPORT,
            ConversationStage.QA
        ]
        try:
            curr_idx = order.index(self.context.stage)
            tgt_idx = order.index(target_stage)
            if tgt_idx <= curr_idx:
                return False
            if target_stage == ConversationStage.STAGE2_BASIC_INFO:
                return self.context.question_category is not None
            if target_stage in (ConversationStage.STAGE3_SUPPLEMENT, ConversationStage.STAGE4_VERIFICATION):
                return self.context.birth_info is not None
            if target_stage == ConversationStage.STAGE5_FINAL_REPORT:
                return len(self.context.selected_theories) > 0
            if target_stage == ConversationStage.QA:
                return bool(self.context.comprehensive_analysis)
            return True
        except ValueError:
            return False
