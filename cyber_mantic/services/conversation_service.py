"""
ConversationService - 纯AI对话模式服务（V2重构版）

实现渐进式5阶段8步骤智能交互流程：

V2流程（5阶段8步骤）：
- 阶段0: 欢迎 - 固定欢迎模板
- 阶段1: 破冰 - 咨询类别 + 3个随机数 → 小六壬
- 阶段2: 深入 - 具体描述 + 汉字 → 测字术（V2新增）
- 阶段3: 信息收集 - 生辰+性别+MBTI → 多理论
- 阶段4: 验证 - 回溯验证问题
- 阶段5: 报告 - 综合报告（AI多轮思考）
- 问答: 持续问答

架构说明：
本模块采用委托模式，将具体逻辑委托给专门的处理器：
- NLPParser: 自然语言解析
- QAHandler: 问答处理
- ReportGenerator: 报告生成
- FlowGuard: 流程监管（V2）
- DynamicVerificationGenerator: 回溯问题生成（V2）
"""

import json
from typing import Dict, Any, Optional, Callable
from core.constants import DEFAULT_MAX_THEORIES, DEFAULT_MIN_THEORIES
from datetime import datetime

from api.manager import APIManager
from models import UserInput
from theories.bazi.theory import BaZiTheory
from theories.ziwei.theory import ZiWeiTheory
from theories.qimen.theory import QiMenTheory
from theories.daliuren.theory import DaLiuRenTheory
from theories.xiaoliu.theory import XiaoLiuRenTheory
from theories.liuyao.theory import LiuYaoTheory
from theories.meihua.theory import MeiHuaTheory
from theories.cezi.theory import CeZiTheory  # V2新增：测字术
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

# V2: FlowGuard流程监管
from core.flow_guard import get_flow_guard, InputStatus

# V2: 提示词模板加载器
from prompts.loader import load_prompt, prompt_exists

# V2: 动态验证问题生成
from core.dynamic_verification import DynamicVerificationGenerator, VerificationResult as DynVerificationResult


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

    # 理论配置映射（用于消除重复代码）
    THEORY_CONFIGS = {
        "八字": {
            "display_name": "八字",
            "progress_name": "八字",
            "progress_text": "正在计算八字命盘...",
            "progress_value": 91,
            "theory_class": BaZiTheory,
            "context_attr": "bazi_result",
            "has_summary": True,
            "has_judgment": True,
        },
        "紫微斗数": {
            "display_name": "紫微斗数",
            "progress_name": "紫微",
            "progress_text": "正在排紫微斗数命盘...",
            "progress_value": 93,
            "theory_class": ZiWeiTheory,
            "context_attr": "ziwei_result",
            "has_summary": False,
            "default_summary": "命盘排布完成",
            "has_judgment": False,
            "default_judgment": "平",
        },
        "奇门遁甲": {
            "display_name": "奇门遁甲",
            "progress_name": "奇门",
            "progress_text": "正在起奇门局...",
            "progress_value": 94,
            "theory_class": QiMenTheory,
            "context_attr": "qimen_result",
            "has_summary": True,
            "has_judgment": True,
        },
        "大六壬": {
            "display_name": "大六壬",
            "progress_name": "六壬",
            "progress_text": "正在起六壬课...",
            "progress_value": 95,
            "theory_class": DaLiuRenTheory,
            "context_attr": "liuren_result",
            "has_summary": False,
            "default_summary": "六壬课起成",
            "has_judgment": False,
            "default_judgment": "平",
        },
        "六爻": {
            "display_name": "六爻",
            "progress_name": "六爻",
            "progress_text": "正在起六爻卦...",
            "progress_value": 96,
            "theory_class": LiuYaoTheory,
            "context_attr": "liuyao_result",
            "has_summary": True,
            "has_judgment": True,
        },
        "梅花易数": {
            "display_name": "梅花易数",
            "progress_name": "梅花",
            "progress_text": "正在起梅花卦...",
            "progress_value": 97,
            "theory_class": MeiHuaTheory,
            "context_attr": "meihua_result",
            "has_summary": True,
            "has_judgment": True,
        },
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
        self.cezi_theory = CeZiTheory()  # V2新增：测字术

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

        # V2: 初始化FlowGuard流程监管（注入API管理器）
        self.flow_guard = get_flow_guard(self.api_manager)

        # V2: 初始化动态验证问题生成器
        self.verification_generator = DynamicVerificationGenerator(self.api_manager)

    # ==================== 公共API ====================

    async def start_conversation(
        self,
        progress_callback: Optional[Callable[[str, str, int], None]] = None,
        theory_callback: Optional[Callable[[str, str, dict], None]] = None
    ) -> str:
        """开始对话会话 - 阶段1破冰

        Args:
            progress_callback: 进度回调 (stage, message, progress)
            theory_callback: 理论分析回调 (event_type, theory_name, data)
                event_type: 'started' | 'completed' | 'quick_result'
        """
        self.context = ConversationContext()
        self.context.stage = ConversationStage.STAGE1_ICEBREAK
        self._init_handlers()

        # V2: 使用模板加载欢迎消息
        try:
            welcome_message = load_prompt("conversation/welcome.md")
        except FileNotFoundError:
            self.logger.warning("欢迎消息模板不存在，使用默认消息")
            welcome_message = "👋 欢迎使用赛博玄数！请告诉我您想咨询什么问题，并提供3个随机数字。"
        self._add_message("assistant", welcome_message)
        return welcome_message

    async def process_user_input(
        self,
        user_message: str,
        progress_callback: Optional[Callable[[str, str, int], None]] = None,
        theory_callback: Optional[Callable[[str, str, dict], None]] = None
    ) -> str:
        """处理用户输入（路由到对应阶段）

        Args:
            user_message: 用户输入
            progress_callback: 进度回调 (stage, message, progress)
            theory_callback: 理论分析回调 (event_type, theory_name, data)
        """
        self._add_message("user", user_message)
        stage = self.context.stage

        # V2: 同步FlowGuard阶段状态
        self._sync_flow_guard_stage(stage)

        try:
            # V2: 检测用户是否想修改已收集的信息
            if self.flow_guard.detect_modification_intent(user_message):
                mod_result = await self.flow_guard.process_modification(user_message, self.context)
                if mod_result:
                    self.logger.info(f"用户修改信息: {mod_result['modified']}")
                    response = mod_result["message"] + "\n\n请继续对话，或告诉我您还需要修改什么。"
                    self._add_message("assistant", response)
                    return response

            # V2: 新的阶段路由逻辑
            # INIT 阶段也当作破冰阶段处理（用户可能在欢迎消息之前就发送了消息）
            if stage in (ConversationStage.INIT, ConversationStage.STAGE1_ICEBREAK):
                response = await self._handle_stage1(user_message, progress_callback, theory_callback)

            # V2新增：阶段2 深入（测字术）
            elif stage == ConversationStage.STAGE2_DEEPEN:
                response = await self._handle_stage2_deepen(user_message, progress_callback, theory_callback)

            # V2: 阶段3 信息收集（原阶段2+3合并）
            elif stage == ConversationStage.STAGE3_COLLECT:
                response = await self._handle_stage3_collect(user_message, progress_callback, theory_callback)

            # V2: 阶段4 验证
            elif stage == ConversationStage.STAGE4_VERIFY:
                response = await self._handle_stage4_verify(user_message, progress_callback, theory_callback)

            # V2: 阶段5 报告
            elif stage == ConversationStage.STAGE5_REPORT:
                response = await self._handle_stage5_report(progress_callback, theory_callback)

            # 问答阶段
            elif stage in (ConversationStage.QA, ConversationStage.COMPLETED):
                response = await self._handle_qa(user_message, progress_callback)

            # 向后兼容：旧阶段枚举（可能来自旧的保存数据）
            elif hasattr(ConversationStage, 'STAGE2_BASIC_INFO') and stage == ConversationStage.STAGE2_BASIC_INFO:
                response = await self._handle_stage3_collect(user_message, progress_callback, theory_callback)
            elif hasattr(ConversationStage, 'STAGE3_SUPPLEMENT') and stage == ConversationStage.STAGE3_SUPPLEMENT:
                response = await self._handle_stage3_collect(user_message, progress_callback, theory_callback)
            elif hasattr(ConversationStage, 'STAGE4_VERIFICATION') and stage == ConversationStage.STAGE4_VERIFICATION:
                response = await self._handle_stage4_verify(user_message, progress_callback, theory_callback)
            elif hasattr(ConversationStage, 'STAGE5_FINAL_REPORT') and stage == ConversationStage.STAGE5_FINAL_REPORT:
                response = await self._handle_stage5_report(progress_callback, theory_callback)

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

    def _sync_flow_guard_stage(self, stage: ConversationStage):
        """同步FlowGuard阶段状态（V2更新）"""
        stage_mapping = {
            # V2新阶段映射
            ConversationStage.INIT: "STAGE1_ICEBREAK",
            ConversationStage.STAGE1_ICEBREAK: "STAGE1_ICEBREAK",
            ConversationStage.STAGE2_DEEPEN: "STAGE2_DEEPEN",      # V2新增
            ConversationStage.STAGE3_COLLECT: "STAGE3_COLLECT",    # V2重命名
            ConversationStage.STAGE4_VERIFY: "STAGE4_VERIFY",      # V2重命名
            ConversationStage.STAGE5_REPORT: "STAGE5_REPORT",      # V2重命名
        }
        flow_guard_stage = stage_mapping.get(stage)
        if flow_guard_stage:
            self.flow_guard.set_stage(flow_guard_stage)

    # ==================== 阶段处理 ====================

    async def _handle_stage1(self, user_message: str, progress_callback, theory_callback=None) -> str:
        """
        阶段1：破冰 - 解析问题类别和随机数字，小六壬起卦

        V2更新：
        - 记录起卦时间（用于后续六爻、梅花）
        - 转到阶段2深入（测字术）而不是直接收集出生信息
        """
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

        # V2: 记录起卦时间（关键！用于六爻、梅花时间起卦）
        self.context.qigua_time = datetime.now()

        # V2: FlowGuard输入验证（AI优先，代码后备）
        validation_result = await self.flow_guard.validate_input_with_ai(user_message, "STAGE1_ICEBREAK")

        if validation_result.status == InputStatus.VALID:
            # FlowGuard成功提取，使用提取的数据
            self.context.question_category = validation_result.extracted_data.get("question_category")
            self.context.random_numbers = validation_result.extracted_data.get("random_numbers", [])
            self.logger.debug(f"FlowGuard验证成功: {validation_result.extracted_data}")
        else:
            # FlowGuard验证失败，回退到NLP解析
            self.logger.debug(f"FlowGuard验证: {validation_result.status}, 使用NLP解析")

            # NLP解析作为备用
            parsed_info = await self.nlp_parser.parse_icebreak_input(user_message)
            if not parsed_info or "error" in parsed_info:
                return self._retry_msg("stage1")

            # 使用NLP解析的数据
            self.context.question_category = parsed_info.get("category")
            self.context.random_numbers = parsed_info.get("numbers", [])

        if progress_callback:
            progress_callback("小六壬", "正在用小六壬起卦...", 30)

        # V2: 通知理论开始
        if theory_callback:
            theory_callback('started', '小六壬', None)

        xiaoliu_result = self._calculate_xiaoliu()
        self.context.xiaoliu_result = xiaoliu_result

        # V2: 通知理论完成
        if theory_callback:
            theory_callback('completed', '小六壬', {
                'summary': xiaoliu_result.get('判断', '初步判断完成'),
                'judgment': self._get_xiaoliu_judgment(xiaoliu_result)
            })

        if progress_callback:
            progress_callback("小六壬", "正在生成初步判断...", 50)

        interpretation = await self._interpret_xiaoliu(xiaoliu_result)

        # V2: 转到阶段2深入（测字术），而不是直接收集出生信息
        self.context.stage = ConversationStage.STAGE2_DEEPEN

        if progress_callback:
            progress_callback("阶段1", "破冰阶段完成", 100)

        # V2: 生成阶段1完成消息（追问具体描述+汉字）
        try:
            return load_prompt("conversation/stage1_complete.md", {
                "category": self.context.question_category,
                "numbers": ', '.join(map(str, self.context.random_numbers)),
                "interpretation": interpretation
            })
        except FileNotFoundError:
            # 兜底：返回简单消息
            return f"""✅ 已收集：{self.context.question_category}，数字：{', '.join(map(str, self.context.random_numbers))}

{interpretation}

---

请告诉我：
1. 具体是什么事情？（简单描述即可）
2. 想着这件事，脑海中浮现的第一个汉字是什么？（可以是心态、未来的憧憬、当下想做的动作等）"""

    async def _handle_stage2_deepen(self, user_message: str, progress_callback, theory_callback=None) -> str:
        """
        V2新增：阶段2 深入 - 解析具体描述和汉字，测字术分析

        输入：具体事情描述 + 汉字
        输出：小六壬+测字术综合分析 + 追问生辰信息
        """
        # 更新会话阶段
        self._update_session_stage('stage2_deepen')

        if progress_callback:
            progress_callback("阶段2", "正在解析您的描述和汉字...", 20)

        # V2: FlowGuard输入验证
        validation_result = await self.flow_guard.validate_input_with_ai(user_message, "STAGE2_DEEPEN")
        if validation_result.status == InputStatus.VALID:
            self.context.question_description = validation_result.extracted_data.get("question_description", "")
            self.context.character = validation_result.extracted_data.get("character")
        else:
            self.logger.debug(f"FlowGuard验证: {validation_result.status}")

        # 如果FlowGuard没有提取到，尝试从消息中简单提取
        if not self.context.question_description:
            # 假设整条消息是描述
            self.context.question_description = user_message[:200]

        if not self.context.character:
            # 尝试提取第一个汉字
            self.context.character = self.flow_guard.validate_character(user_message)

        # 如果仍然没有汉字，提示用户
        if not self.context.character:
            return """😅 抱歉，我没有找到您想测的汉字。

请告诉我：想着这件事，脑海中浮现的第一个汉字是什么？

例如：
- "变" - 想要改变
- "心" - 关于内心
- "进" - 想要前进

您也可以这样说："我想测'变'字" 或 "想到的字是变"""

        if progress_callback:
            progress_callback("测字术", "正在进行测字分析...", 40)

        # V2: 通知理论开始
        if theory_callback:
            theory_callback('started', '测字术', None)

        # V2: 执行测字术计算
        try:
            cezi_user_input = UserInput(
                question_type=self.context.question_category,
                question_description=self.context.question_description,
                current_time=self.context.qigua_time or datetime.now()
            )
            # 测字术需要 character 字段
            cezi_user_input.character = self.context.character

            cezi_result = self.cezi_theory.calculate(cezi_user_input)
            self.context.cezi_result = cezi_result

            # V2: 通知理论完成
            if theory_callback:
                theory_callback('completed', '测字术', {
                    'summary': cezi_result.get('简析', f"测'{self.context.character}'字完成"),
                    'judgment': cezi_result.get('judgment', '平')
                })
        except Exception as e:
            self.logger.error(f"测字术计算失败: {e}")
            self.context.cezi_result = {"error": str(e), "character": self.context.character}
            if theory_callback:
                theory_callback('completed', '测字术', {
                    'summary': f"测'{self.context.character}'字",
                    'judgment': '平'
                })

        if progress_callback:
            progress_callback("综合分析", "正在生成综合分析...", 60)

        # V2: 生成小六壬+测字综合分析（AI生成）
        combined_analysis = await self._generate_combined_analysis()

        # V2: 转到阶段3信息收集
        self.context.stage = ConversationStage.STAGE3_COLLECT

        if progress_callback:
            progress_callback("阶段2", "深入阶段完成", 100)

        # V2: 生成阶段2完成消息（追问生辰信息）
        try:
            return load_prompt("conversation/stage2_complete.md", {
                "character": self.context.character,
                "description": self.context.question_description,
                "combined_analysis": combined_analysis
            })
        except FileNotFoundError:
            # 兜底：返回简单消息
            return f"""✅ 已收集：测"{self.context.character}"字

{combined_analysis}

---

请提供您的出生信息：
1. 出生日期（可以说大概时间段或不记得）
2. 性别
3. MBTI类型（可选，不知道可跳过）"""

    async def _generate_combined_analysis(self) -> str:
        """V2新增：生成小六壬+测字综合分析"""
        prompt = f"""你是一位精通小六壬和测字术的占卜师。请根据以下两种理论的结果，给出综合分析。

问题类别：{self.context.question_category}
具体事情：{self.context.question_description}

【小六壬结果】
{json.dumps(self.context.xiaoliu_result, ensure_ascii=False, indent=2)}

【测字结果】
测字：{self.context.character}
{json.dumps(self.context.cezi_result, ensure_ascii=False, indent=2)}

请生成综合分析（100-150字），融合两种理论的判断，给出初步建议。语气温和专业。
"""
        try:
            return (await self.api_manager.call_api(
                task_type="快速交互问答",
                prompt=prompt,
                enable_dual_verification=False
            )).strip()
        except Exception as e:
            self.logger.error(f"综合分析生成失败: {e}")
            return f"📍 小六壬落宫：{self.context.xiaoliu_result.get('时落宫', '未知')}，测字：{self.context.character}\n\n（系统繁忙，将在后续分析中补充详细解读）"

    # ==================== 向后兼容：旧阶段处理器 ====================

    async def _handle_stage2(self, user_message: str, progress_callback, theory_callback=None) -> str:
        """[已废弃] 阶段2：基础信息收集 - 已合并到 _handle_stage3_collect"""
        return await self._handle_stage3_collect(user_message, progress_callback, theory_callback)

    async def _handle_stage3(self, user_message: str, progress_callback, theory_callback=None) -> str:
        """[已废弃] 阶段3：深度补充 - 已合并到 _handle_stage3_collect"""
        return await self._handle_stage3_collect(user_message, progress_callback, theory_callback)

    async def _handle_stage4(self, user_message: str, progress_callback, theory_callback=None) -> str:
        """[已废弃] 阶段4：结果验证 - 已重命名为 _handle_stage4_verify"""
        return await self._handle_stage4_verify(user_message, progress_callback, theory_callback)

    async def _handle_stage5(self, progress_callback, theory_callback=None) -> str:
        """[已废弃] 阶段5：最终报告 - 已重命名为 _handle_stage5_report"""
        return await self._handle_stage5_report(progress_callback, theory_callback)

    # ==================== V2：新阶段处理器 ====================

    async def _handle_stage3_collect(self, user_message: str, progress_callback, theory_callback=None) -> str:
        """
        V2：阶段3 信息收集 - 收集生辰+性别+MBTI，运行多理论分析

        V2更新：
        - 使用 STAGE3_COLLECT FlowGuard验证
        - 生成六爻自动起卦数字
        - 直接转到 STAGE4_VERIFY（不再有补充阶段）
        """
        # 更新会话阶段
        self._update_session_stage('stage3_collect')

        if progress_callback:
            progress_callback("阶段3", "正在解析您的出生信息...", 60)

        # V2: FlowGuard输入验证
        validation_result = await self.flow_guard.validate_input_with_ai(user_message, "STAGE3_COLLECT")
        if validation_result.status == InputStatus.VALID:
            self.logger.info(f"FlowGuard验证通过，提取数据: {validation_result.extracted_data}")
            # 提取颜色/方位（用于梅花易数）
            if validation_result.extracted_data.get("favorite_color"):
                self.context.favorite_color = validation_result.extracted_data["favorite_color"]
            if validation_result.extracted_data.get("current_direction"):
                self.context.current_direction = validation_result.extracted_data["current_direction"]

        birth_info = await self.nlp_parser.parse_birth_info(user_message)
        if not birth_info or "error" in birth_info:
            return self._retry_msg("stage3")

        self.context.birth_info = birth_info
        self.context.gender = birth_info.get("gender")
        self.context.mbti_type = birth_info.get("mbti")
        self.context.time_certainty = birth_info.get("time_certainty", "unknown")

        # V2: 生成六爻自动起卦数字
        self.context.generate_liuyao_numbers()
        self.logger.info(f"六爻自动起卦数字: {self.context.liuyao_numbers}")

        if progress_callback:
            progress_callback("多理论分析", "正在计算多理论结果...", 75)

        # 运行多理论分析
        await self._run_deep_analysis(progress_callback, theory_callback)

        # V2: 生成回溯验证问题
        if progress_callback:
            progress_callback("验证问题", "正在生成回溯验证问题...", 85)

        verification_questions = await self._generate_verification_questions()
        self.context.verification_questions = verification_questions

        # V2: 直接转到阶段4验证
        self.context.stage = ConversationStage.STAGE4_VERIFY

        # 构建响应
        birth_str = f"{birth_info.get('year')}年{birth_info.get('month')}月{birth_info.get('day')}日"
        if birth_info.get('hour') is not None:
            birth_str += f" {birth_info.get('hour')}时"

        time_status = {"certain": "✅ 确定", "uncertain": "⚠️ 不确定", "unknown": "❓ 未知"}.get(self.context.time_certainty, "未知")

        # V2: 格式化验证问题
        questions_md = self._format_verification_questions(verification_questions)

        # V2: 使用模板加载阶段3完成消息
        try:
            response = load_prompt("conversation/stage3_collect_complete.md", {
                "birth_str": birth_str,
                "time_status": time_status,
                "gender": self.context.gender or '未提供',
                "mbti": self.context.mbti_type or '未提供',
                "questions": questions_md
            })
        except FileNotFoundError:
            response = f"""✅ 出生信息：{birth_str}，时辰：{time_status}
性别：{self.context.gender or '未提供'}
MBTI：{self.context.mbti_type or '未提供'}

---

多理论分析已完成。

{questions_md}"""

        return response

    async def _handle_stage4_verify(self, user_message: str, progress_callback, theory_callback=None) -> str:
        """
        V2：阶段4 验证 - 处理回溯验证问题回答

        V2更新：
        - 使用 STAGE4_VERIFY FlowGuard验证
        - 直接转到 STAGE5_REPORT
        """
        # 更新会话阶段
        self._update_session_stage('stage4_verify')

        if progress_callback:
            progress_callback("阶段4", "正在分析验证反馈...", 85)

        feedback = await self.nlp_parser.parse_verification_feedback(
            user_message,
            self.context.retrospective_events
        )
        if feedback:
            self.context.verification_feedback.append({
                "raw_message": user_message,
                "parsed_feedback": feedback
            })
            self._adjust_confidence(feedback)

        # V2: 转到阶段5报告
        self.context.stage = ConversationStage.STAGE5_REPORT

        return await self._handle_stage5_report(progress_callback, theory_callback)

    async def _handle_stage5_report(self, progress_callback, theory_callback=None) -> str:
        """
        V2：阶段5 报告 - 生成综合分析报告

        V2更新：
        - 支持多轮AI思考生成个性化报告
        """
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
            # 从字典中提取理论名称
            primary_theory = None
            if self.context.selected_theories:
                first_theory = self.context.selected_theories[0]
                if isinstance(first_theory, dict):
                    primary_theory = first_theory.get('theory', str(first_theory))
                else:
                    primary_theory = str(first_theory)
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

    async def _generate_verification_questions(self):
        """V2: 生成回溯验证问题"""
        try:
            # 准备用户信息
            user_info = {
                "question_type": self.context.question_category,
                "age": self._calculate_age(),
                "gender": self.context.gender or "未知"
            }

            # 准备分析结果（已有的理论分析）
            analysis_results = {}
            if self.context.xiaoliu_result:
                analysis_results["小六壬"] = self.context.xiaoliu_result

            # 生成3个验证问题
            questions = await self.verification_generator.generate_questions(
                user_info=user_info,
                analysis_results=analysis_results,
                question_count=3
            )

            self.logger.info(f"生成了 {len(questions)} 个回溯验证问题")
            return questions

        except Exception as e:
            self.logger.error(f"生成验证问题失败: {e}")
            return []

    def _format_verification_questions(self, questions) -> str:
        """V2: 格式化验证问题为Markdown"""
        if not questions:
            # 没有生成问题时使用默认问题
            return f"""## ⏪ 回溯验证

请简单回答以下问题，帮助我们验证分析准确度：

1. 过去3年中，在**{self.context.question_category}**领域是否有重大变化？
2. 您最近一次重要决策是在什么时候？
3. 过去一年的发展是否符合您的预期？

请简单描述："""

        # 格式化问题列表
        lines = ["## ⏪ 回溯验证\n", "请简单回答以下问题，帮助我们验证分析准确度：\n"]

        for i, q in enumerate(questions, 1):
            lines.append(f"{i}. {q.question}")

        lines.append("\n请简单回答（可以一起回答，也可以逐个回答）：")

        return "\n".join(lines)

    def _calculate_age(self) -> int:
        """计算用户年龄"""
        if self.context.birth_info and self.context.birth_info.get("year"):
            birth_year = self.context.birth_info["year"]
            current_year = datetime.now().year
            return current_year - birth_year
        return 0

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

    async def _calculate_theory_fitness(self, theory_callback=None) -> str:
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
        # 从配置读取理论数量限制，默认max=5, min=3（符合产品定义"3-5个理论"）
        max_theories = self.config.get("conversation", {}).get("max_theories", DEFAULT_MAX_THEORIES)
        min_theories = self.config.get("conversation", {}).get("min_theories", DEFAULT_MIN_THEORIES)
        selected, _ = self.theory_selector.select_theories(user_input, max_theories=max_theories, min_theories=min_theories)
        self.context.selected_theories = selected

        # 格式化理论列表（支持字典列表和字符串列表）
        theory_lines = []
        for i, t in enumerate(selected, 1):
            if isinstance(t, dict):
                theory_name = t.get('theory', '未知')
                fitness = t.get('fitness', 0)
                info_comp = t.get('info_completeness', 0)
                theory_lines.append(f"{i}. **{theory_name}** (适配度: {fitness:.0%}, 信息完备度: {info_comp:.0%})")
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

    def _process_theory(
        self,
        theory_name: str,
        user_input: UserInput,
        progress_callback: Optional[Callable] = None,
        theory_callback: Optional[Callable] = None
    ) -> None:
        """
        统一处理单个理论的计算流程（消除重复代码）

        Args:
            theory_name: 理论名称
            user_input: 用户输入
            progress_callback: 进度回调
            theory_callback: 理论状态回调
        """
        if theory_name not in self.THEORY_CONFIGS:
            self.logger.warning(f"未知理论: {theory_name}")
            return

        config = self.THEORY_CONFIGS[theory_name]

        # 1. 进度回调
        if progress_callback:
            progress_callback(
                config["progress_name"],
                config["progress_text"],
                config["progress_value"]
            )

        # 2. 开始回调
        if theory_callback:
            theory_callback('started', config["display_name"], None)

        # 3. 执行计算
        try:
            theory_instance = config["theory_class"]()
            result = theory_instance.calculate(user_input)

            # 保存结果到上下文
            setattr(self.context, config["context_attr"], result)

            # 4. 完成回调
            if theory_callback:
                # 获取summary和judgment
                if config.get("has_summary"):
                    summary_method_name = f"_get_{config['context_attr'].replace('_result', '')}_summary"
                    summary = getattr(self, summary_method_name)(result)
                else:
                    summary = config.get("default_summary", "计算完成")

                if config.get("has_judgment"):
                    judgment_method_name = f"_get_{config['context_attr'].replace('_result', '')}_judgment"
                    judgment = getattr(self, judgment_method_name)(result)
                else:
                    judgment = config.get("default_judgment", "平")

                theory_callback('completed', config["display_name"], {
                    'summary': summary,
                    'judgment': judgment
                })

        except Exception as e:
            self.logger.error(f"{theory_name}计算失败: {e}")
            if theory_callback:
                theory_callback('error', config["display_name"], {
                    'error': str(e)
                })

    async def _run_deep_analysis(self, progress_callback, theory_callback=None):
        """执行深度分析（重构版：使用统一的理论处理函数）"""
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

        # 提取理论名称列表（支持字典列表和字符串列表）
        selected_theory_names = []
        for t in self.context.selected_theories:
            if isinstance(t, dict):
                selected_theory_names.append(t.get('theory', ''))
            else:
                selected_theory_names.append(str(t))

        # 使用统一方法处理所有理论
        for theory_name in selected_theory_names:
            if theory_name in self.THEORY_CONFIGS:
                self._process_theory(
                    theory_name,
                    user_input,
                    progress_callback,
                    theory_callback
                )

    def _retry_msg(self, stage: str) -> str:
        """生成重试提示（V2: 使用FlowGuard显示进度）"""

        # V2: 使用FlowGuard生成进度展示
        progress_display = self.flow_guard.generate_progress_display()
        stage_prompt = self.flow_guard.generate_stage_prompt()

        if stage == "stage1":
            return f"""😅 抱歉，我没能完全理解您的信息。

{progress_display}

---

{stage_prompt}
"""
        else:
            return f"""😅 抱歉，我没能理解您的出生信息。

{progress_display}

---

{stage_prompt}
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

    # ==================== V2: 理论结果摘要辅助方法 ====================

    def _get_xiaoliu_judgment(self, result: dict) -> str:
        """从小六壬结果提取吉凶判断"""
        if not result:
            return "平"
        gong = result.get('时落宫', '')
        # 大安、速喜为吉；赤口、小吉为平；空亡、留连为凶
        if gong in ('大安', '速喜'):
            return "吉"
        elif gong in ('赤口', '空亡', '留连'):
            return "凶"
        return "平"

    def _get_bazi_summary(self, result: dict) -> str:
        """从八字结果提取摘要"""
        if not result:
            return "八字分析完成"
        day_master = result.get('日主', '')
        strength = result.get('用神分析', {}).get('日主强弱', '')
        if day_master and strength:
            return f"日主{day_master}，{strength}"
        return "八字命盘已排布"

    def _get_bazi_judgment(self, result: dict) -> str:
        """从八字结果提取吉凶判断"""
        # 八字分析通常较复杂，默认返回平
        return "平"

    def _get_qimen_summary(self, result: dict) -> str:
        """从奇门遁甲结果提取摘要"""
        if not result:
            return "奇门局起成"
        # 尝试提取关键信息
        if isinstance(result, dict):
            if 'judgment' in result:
                return result['judgment'][:50] if len(result.get('judgment', '')) > 50 else result.get('judgment', '奇门分析完成')
        return "奇门局起成"

    def _get_qimen_judgment(self, result: dict) -> str:
        """从奇门遁甲结果提取吉凶判断"""
        if not result:
            return "平"
        # 尝试从结果中提取判断
        if isinstance(result, dict):
            judgment_text = result.get('judgment', result.get('判断', ''))
            if '吉' in judgment_text:
                return "吉"
            elif '凶' in judgment_text:
                return "凶"
        return "平"

    def _get_liuyao_summary(self, result: dict) -> str:
        """从六爻结果提取摘要"""
        if not result:
            return "六爻卦起成"
        ben_gua = result.get('本卦', {})
        yong_shen = result.get('用神', {})
        if ben_gua and yong_shen:
            gua_name = ben_gua.get('名称', '')
            liu_qin = yong_shen.get('六亲', '')
            return f"{gua_name}，用神{liu_qin}"
        return "六爻卦起成"

    def _get_liuyao_judgment(self, result: dict) -> str:
        """从六爻结果提取吉凶判断"""
        if not result:
            return "平"
        judgment = result.get('judgment', '')
        if judgment == '吉':
            return "吉"
        elif judgment == '凶':
            return "凶"
        return "平"

    def _get_meihua_summary(self, result: dict) -> str:
        """从梅花易数结果提取摘要"""
        if not result:
            return "梅花卦起成"
        ben_gua = result.get('本卦', {})
        ti_yong = result.get('体用关系', '')
        if ben_gua:
            gua_name = ben_gua.get('名称', '')
            return f"{gua_name}，{ti_yong}"
        return "梅花卦起成"

    def _get_meihua_judgment(self, result: dict) -> str:
        """从梅花易数结果提取吉凶判断"""
        if not result:
            return "平"
        judgment = result.get('judgment', '')
        if judgment == '吉':
            return "吉"
        elif judgment == '凶':
            return "凶"
        return "平"

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
