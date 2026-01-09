"""
对话上下文数据模型

包含：
- ConversationStage: 对话阶段枚举（5阶段8步骤渐进式流程）
- ConversationContext: 对话上下文数据类

V2更新：
- 新增STAGE2_DEEPEN阶段（测字术融合）
- 新增起卦时间、测字结果、六爻自动数字等字段
- 支持向后兼容（旧阶段枚举值自动映射）
"""
from enum import Enum
from datetime import datetime
from typing import Dict, Any, List, Optional


# 常量配置
MAX_CONVERSATION_HISTORY = 100  # 对话历史最大保留条数


class ConversationStage(Enum):
    """
    对话阶段（5阶段渐进式流程）

    V2流程：
    - 阶段0: 欢迎（固定模板）
    - 阶段1: 破冰（小六壬）
    - 阶段2: 深入（测字术）← 新增
    - 阶段3: 信息收集（多理论）
    - 阶段4: 验证（回溯问题）
    - 阶段5: 报告（AI多轮思考）
    """
    INIT = "初始化"
    STAGE1_ICEBREAK = "阶段1_破冰"          # 咨询类别 + 3个随机数 → 小六壬
    STAGE2_DEEPEN = "阶段2_深入"            # 具体描述 + 汉字 → 测字术（新增）
    STAGE3_COLLECT = "阶段3_信息收集"       # 生辰+性别+MBTI → 多理论
    STAGE4_VERIFY = "阶段4_验证"            # 回溯验证问题
    STAGE5_REPORT = "阶段5_报告"            # 综合报告（AI多轮思考）
    QA = "问答交互"                         # 持续问答
    COMPLETED = "完成"

    # 向后兼容映射（旧枚举值 → 新枚举值）
    # 在 from_dict 中使用
    @classmethod
    def from_legacy_value(cls, value: str) -> "ConversationStage":
        """从旧版枚举值转换（向后兼容）"""
        legacy_mapping = {
            "阶段2_基础信息": cls.STAGE3_COLLECT,  # 旧的阶段2映射到新阶段3
            "阶段3_深度补充": cls.STAGE3_COLLECT,  # 合并到阶段3
            "阶段4_结果确认": cls.STAGE4_VERIFY,
            "阶段5_完整报告": cls.STAGE5_REPORT,
        }
        if value in legacy_mapping:
            return legacy_mapping[value]
        # 尝试标准匹配
        for stage in cls:
            if stage.value == value:
                return stage
        return cls.INIT  # 默认返回初始化


class ConversationContext:
    """
    对话上下文（渐进式信息收集）

    存储整个对话过程中收集的所有信息，包括：
    - 各阶段收集的用户信息
    - 各理论的分析结果
    - 综合报告内容
    - 对话历史
    """

    def __init__(self):
        self.stage = ConversationStage.INIT

        # 会话追踪ID（用于洞察模块统计）
        self.session_id: Optional[str] = None

        # ===== 阶段1：破冰信息 =====
        self.question_category: Optional[str] = None  # 事业/感情/财运/健康/决策/其他
        self.random_numbers: List[int] = []           # 3个随机数字（1-9）
        self.qigua_time: Optional[datetime] = None    # V2新增：起卦时间（用于六爻、梅花）
        self.xiaoliu_result: Optional[Dict[str, Any]] = None  # 小六壬快速判断

        # ===== 阶段2：深入（V2新增） =====
        self.question_description: str = ""           # 具体问题描述
        self.character: Optional[str] = None          # V2新增：测字用的汉字
        self.cezi_result: Optional[Dict[str, Any]] = None  # V2新增：测字术计算结果

        # ===== 阶段3：信息收集 =====
        self.birth_info: Optional[Dict[str, Any]] = None  # 出生年月日时
        self.gender: Optional[str] = None             # male/female
        self.mbti_type: Optional[str] = None          # INTJ等
        self.birth_place: Optional[str] = None        # 出生地（可选）
        self.current_direction: Optional[str] = None  # 当前方位（梅花起卦用）
        self.favorite_color: Optional[str] = None     # 喜欢的颜色（梅花起卦用）
        self.time_certainty: str = "unknown"          # certain/uncertain/unknown
        self.inferred_hour: Optional[int] = None      # 推断的时辰

        # 六爻自动起卦数字（V2新增：基于起卦时间自动生成）
        self.liuyao_numbers: List[int] = []

        # 向后兼容字段（保留但已废弃）
        self.related_character: Optional[str] = None  # 已移至 character
        self.siblings_info: Optional[str] = None      # 已废弃
        self.face_features: Optional[str] = None      # 已废弃
        self.sleep_habits: Optional[str] = None       # 已废弃
        self.supplementary_numbers: List[int] = []    # 已移至 liuyao_numbers

        # 阶段4：结果确认
        self.retrospective_events: List[Dict[str, Any]] = []  # 回溯的关键事件
        self.verification_feedback: List[Dict[str, Any]] = []  # 用户确认反馈
        self.theory_confidence_adjustment: Dict[str, float] = {}  # 理论置信度调整
        self.verification_questions: List[Any] = []  # V2: 动态生成的验证问题

        # 分析结果
        self.selected_theories: List[str] = []  # 选定的理论列表
        self.theory_results: Dict[str, Dict[str, Any]] = {}  # 各理论的计算结果
        self.bazi_result: Optional[Dict[str, Any]] = None
        self.ziwei_result: Optional[Dict[str, Any]] = None  # 紫微斗数结果
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

            # ===== 阶段1：破冰信息 =====
            "question_category": self.question_category,
            "random_numbers": self.random_numbers,
            "qigua_time": self.qigua_time.isoformat() if self.qigua_time else None,  # V2新增
            "xiaoliu_result": self.xiaoliu_result,

            # ===== 阶段2：深入（V2新增）=====
            "question_description": self.question_description,
            "character": self.character,      # V2新增
            "cezi_result": self.cezi_result,  # V2新增

            # ===== 阶段3：信息收集 =====
            "birth_info": self.birth_info,
            "gender": self.gender,
            "mbti_type": self.mbti_type,
            "birth_place": self.birth_place,
            "current_direction": self.current_direction,
            "favorite_color": self.favorite_color,
            "time_certainty": self.time_certainty,
            "inferred_hour": self.inferred_hour,
            "liuyao_numbers": self.liuyao_numbers,  # V2新增

            # 向后兼容字段
            "related_character": self.related_character,
            "siblings_info": self.siblings_info,
            "face_features": self.face_features,
            "sleep_habits": self.sleep_habits,
            "supplementary_numbers": self.supplementary_numbers,

            # ===== 阶段4：验证 =====
            "retrospective_events": self.retrospective_events,
            "verification_feedback": self.verification_feedback,
            "theory_confidence_adjustment": self.theory_confidence_adjustment,
            "verification_questions": [q.to_dict() if hasattr(q, 'to_dict') else q for q in self.verification_questions],

            # ===== 分析结果 =====
            "selected_theories": self.selected_theories,
            "theory_results": self.theory_results,
            "bazi_result": self.bazi_result,
            "ziwei_result": self.ziwei_result,
            "qimen_result": self.qimen_result,
            "liuren_result": self.liuren_result,
            "liuyao_result": self.liuyao_result,
            "meihua_result": self.meihua_result,

            # ===== 综合报告 =====
            "comprehensive_analysis": self.comprehensive_analysis,
            "retrospective_analysis": self.retrospective_analysis,
            "predictive_analysis": self.predictive_analysis,
            "actionable_advice": self.actionable_advice,

            # ===== 对话历史 =====
            "conversation_history": self.conversation_history
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationContext":
        """从字典恢复上下文（支持向后兼容）"""
        context = cls()

        # 恢复阶段（使用向后兼容映射）
        stage_value = data.get("stage", "初始化")
        context.stage = ConversationStage.from_legacy_value(stage_value)

        # ===== 恢复阶段1数据 =====
        context.question_category = data.get("question_category")
        context.random_numbers = data.get("random_numbers", [])
        context.xiaoliu_result = data.get("xiaoliu_result")

        # V2新增：起卦时间
        qigua_time_str = data.get("qigua_time")
        if qigua_time_str:
            try:
                context.qigua_time = datetime.fromisoformat(qigua_time_str)
            except (ValueError, TypeError):
                context.qigua_time = None

        # ===== 恢复阶段2数据（V2新增） =====
        context.question_description = data.get("question_description", "")
        # 向后兼容：优先用新字段，否则用旧字段
        context.character = data.get("character") or data.get("related_character")
        context.cezi_result = data.get("cezi_result")

        # ===== 恢复阶段3数据 =====
        context.birth_info = data.get("birth_info")
        context.gender = data.get("gender")
        context.mbti_type = data.get("mbti_type")
        context.birth_place = data.get("birth_place")
        context.current_direction = data.get("current_direction")
        context.favorite_color = data.get("favorite_color")
        context.time_certainty = data.get("time_certainty", "unknown")
        context.inferred_hour = data.get("inferred_hour")

        # V2新增：六爻自动数字（向后兼容：优先用新字段）
        context.liuyao_numbers = data.get("liuyao_numbers") or data.get("supplementary_numbers", [])

        # 向后兼容字段
        context.related_character = data.get("related_character")
        context.siblings_info = data.get("siblings_info")
        context.face_features = data.get("face_features")
        context.sleep_habits = data.get("sleep_habits")
        context.supplementary_numbers = data.get("supplementary_numbers", [])

        # ===== 恢复阶段4数据 =====
        context.retrospective_events = data.get("retrospective_events", [])
        context.verification_feedback = data.get("verification_feedback", [])
        context.theory_confidence_adjustment = data.get("theory_confidence_adjustment", {})
        context.verification_questions = data.get("verification_questions", [])

        # ===== 恢复分析结果 =====
        context.selected_theories = data.get("selected_theories", [])
        context.theory_results = data.get("theory_results", {})
        context.bazi_result = data.get("bazi_result")
        context.ziwei_result = data.get("ziwei_result")
        context.qimen_result = data.get("qimen_result")
        context.liuren_result = data.get("liuren_result")
        context.liuyao_result = data.get("liuyao_result")
        context.meihua_result = data.get("meihua_result")

        # ===== 恢复综合报告 =====
        context.comprehensive_analysis = data.get("comprehensive_analysis", "")
        context.retrospective_analysis = data.get("retrospective_analysis", "")
        context.predictive_analysis = data.get("predictive_analysis", "")
        context.actionable_advice = data.get("actionable_advice", [])

        # ===== 恢复对话历史 =====
        context.conversation_history = data.get("conversation_history", [])

        return context

    def add_message(self, role: str, content: str):
        """
        添加消息到对话历史

        Args:
            role: 角色（user/assistant）
            content: 消息内容
        """
        self.conversation_history.append({
            "role": role,
            "content": content
        })

        # 限制对话历史长度
        if len(self.conversation_history) > MAX_CONVERSATION_HISTORY:
            # 保留最近的消息
            self.conversation_history = self.conversation_history[-MAX_CONVERSATION_HISTORY:]

    def get_recent_history(self, count: int = 10) -> List[Dict[str, str]]:
        """获取最近的对话历史"""
        return self.conversation_history[-count:]

    def has_birth_info(self) -> bool:
        """检查是否已有出生信息"""
        return self.birth_info is not None

    def has_complete_birth_info(self) -> bool:
        """检查出生信息是否完整（包含时辰）"""
        if not self.birth_info:
            return False
        return all([
            self.birth_info.get("year"),
            self.birth_info.get("month"),
            self.birth_info.get("day"),
            self.birth_info.get("hour") is not None or self.inferred_hour is not None
        ])

    def get_effective_hour(self) -> Optional[int]:
        """获取有效的出生时辰（优先使用明确的，其次用推断的）"""
        if self.birth_info and self.birth_info.get("hour") is not None:
            return self.birth_info["hour"]
        return self.inferred_hour

    def clear(self):
        """清空上下文，开始新对话"""
        self.__init__()

    def generate_liuyao_numbers(self) -> List[int]:
        """
        V2新增：用起卦时间生成六爻数字

        算法：使用起卦时间的秒+微秒生成3个1-9的伪随机数
        如果没有起卦时间，使用当前时间

        Returns:
            3个1-9的数字列表
        """
        time_to_use = self.qigua_time or datetime.now()
        ts = time_to_use.timestamp()

        # 提取秒和微秒部分
        seconds = int(ts) % 60
        microseconds = int((ts % 1) * 1000000)

        # 生成3个伪随机数（1-9）
        num1 = (seconds % 9) + 1
        num2 = ((seconds + microseconds // 1000) % 9) + 1
        num3 = ((seconds + microseconds // 100) % 9) + 1

        self.liuyao_numbers = [num1, num2, num3]
        return self.liuyao_numbers

    def get_meihua_method(self) -> tuple:
        """
        V2新增：确定梅花易数起卦方式

        优先级：颜色 > 方位 > 时间

        Returns:
            (起卦方式名称, 起卦参数字典)
        """
        if self.favorite_color:
            return ("颜色起卦", {"color": self.favorite_color})
        elif self.current_direction:
            return ("方位起卦", {"direction": self.current_direction})
        else:
            time_to_use = self.qigua_time or datetime.now()
            return ("时间起卦", {"time": time_to_use})
