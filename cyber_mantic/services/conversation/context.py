"""
对话上下文数据模型

包含：
- ConversationStage: 对话阶段枚举
- ConversationContext: 对话上下文数据类
"""
from enum import Enum
from typing import Dict, Any, List, Optional


# 常量配置
MAX_CONVERSATION_HISTORY = 100  # 对话历史最大保留条数


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

        # 阶段1：破冰信息
        self.question_category: Optional[str] = None  # 事业/感情/财运/健康/决策/其他
        self.question_description: str = ""  # 问题描述
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
            # 阶段1：破冰信息
            "question_category": self.question_category,
            "question_description": self.question_description,
            "random_numbers": self.random_numbers,
            "xiaoliu_result": self.xiaoliu_result,
            # 阶段2：基础信息
            "birth_info": self.birth_info,
            "gender": self.gender,
            "mbti_type": self.mbti_type,
            "birth_place": self.birth_place,
            "current_direction": self.current_direction,
            "favorite_color": self.favorite_color,
            "related_character": self.related_character,
            # 阶段3：深度补充
            "time_certainty": self.time_certainty,
            "inferred_hour": self.inferred_hour,
            "siblings_info": self.siblings_info,
            "face_features": self.face_features,
            "sleep_habits": self.sleep_habits,
            "supplementary_numbers": self.supplementary_numbers,
            # 阶段4：结果确认
            "retrospective_events": self.retrospective_events,
            "verification_feedback": self.verification_feedback,
            "theory_confidence_adjustment": self.theory_confidence_adjustment,
            # 分析结果
            "selected_theories": self.selected_theories,
            "theory_results": self.theory_results,
            "bazi_result": self.bazi_result,
            "ziwei_result": self.ziwei_result,
            "qimen_result": self.qimen_result,
            "liuren_result": self.liuren_result,
            "liuyao_result": self.liuyao_result,
            "meihua_result": self.meihua_result,
            # 综合报告
            "comprehensive_analysis": self.comprehensive_analysis,
            "retrospective_analysis": self.retrospective_analysis,
            "predictive_analysis": self.predictive_analysis,
            "actionable_advice": self.actionable_advice,
            # 对话历史
            "conversation_history": self.conversation_history
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationContext":
        """从字典恢复上下文"""
        context = cls()

        # 恢复阶段
        stage_value = data.get("stage", "初始化")
        for stage in ConversationStage:
            if stage.value == stage_value:
                context.stage = stage
                break

        # 恢复阶段1数据
        context.question_category = data.get("question_category")
        context.question_description = data.get("question_description", "")
        context.random_numbers = data.get("random_numbers", [])
        context.xiaoliu_result = data.get("xiaoliu_result")

        # 恢复阶段2数据
        context.birth_info = data.get("birth_info")
        context.gender = data.get("gender")
        context.mbti_type = data.get("mbti_type")
        context.birth_place = data.get("birth_place")
        context.current_direction = data.get("current_direction")
        context.favorite_color = data.get("favorite_color")
        context.related_character = data.get("related_character")

        # 恢复阶段3数据
        context.time_certainty = data.get("time_certainty", "unknown")
        context.inferred_hour = data.get("inferred_hour")
        context.siblings_info = data.get("siblings_info")
        context.face_features = data.get("face_features")
        context.sleep_habits = data.get("sleep_habits")
        context.supplementary_numbers = data.get("supplementary_numbers", [])

        # 恢复阶段4数据
        context.retrospective_events = data.get("retrospective_events", [])
        context.verification_feedback = data.get("verification_feedback", [])
        context.theory_confidence_adjustment = data.get("theory_confidence_adjustment", {})

        # 恢复分析结果
        context.selected_theories = data.get("selected_theories", [])
        context.theory_results = data.get("theory_results", {})
        context.bazi_result = data.get("bazi_result")
        context.ziwei_result = data.get("ziwei_result")
        context.qimen_result = data.get("qimen_result")
        context.liuren_result = data.get("liuren_result")
        context.liuyao_result = data.get("liuyao_result")
        context.meihua_result = data.get("meihua_result")

        # 恢复综合报告
        context.comprehensive_analysis = data.get("comprehensive_analysis", "")
        context.retrospective_analysis = data.get("retrospective_analysis", "")
        context.predictive_analysis = data.get("predictive_analysis", "")
        context.actionable_advice = data.get("actionable_advice", [])

        # 恢复对话历史
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
