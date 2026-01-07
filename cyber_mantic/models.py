"""
赛博玄数 - 数据模型定义
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
import json


@dataclass
class PersonBirthInfo:
    """个人出生信息（用于多人八字分析）"""
    label: str = "本人"                             # 人物标签（如"本人"、"配偶"、"父亲"等）
    birth_year: Optional[int] = None                # 出生年
    birth_month: Optional[int] = None               # 出生月
    birth_day: Optional[int] = None                 # 出生日
    birth_hour: Optional[int] = None                # 出生时（0-23）
    birth_minute: Optional[int] = None              # 出生分
    calendar_type: str = "solar"                    # 历法类型 "solar"/"lunar"
    birth_time_certainty: str = "certain"           # 时辰确定性 "certain"/"uncertain"/"unknown"
    gender: Optional[str] = None                    # 性别 "male"/"female"
    birth_place_lng: Optional[float] = None         # 出生地经度
    mbti_type: Optional[str] = None                 # MBTI类型

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {k: v for k, v in self.__dict__.items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PersonBirthInfo':
        """从字典创建"""
        return cls(**data)


@dataclass
class UserInput:
    """用户输入数据"""
    # 问题信息
    question_type: str                          # 问题类别
    question_description: str                   # 问题描述

    # 时间信息
    current_time: datetime = field(default_factory=datetime.now)  # 当前时间
    initial_inquiry_time: Optional[datetime] = None  # 起卦时间（用户第一次发送请求的时间）
    birth_year: Optional[int] = None            # 出生年
    birth_month: Optional[int] = None           # 出生月
    birth_day: Optional[int] = None             # 出生日
    birth_hour: Optional[int] = None            # 出生时（0-23）
    birth_minute: Optional[int] = None          # 出生分
    calendar_type: str = "solar"                # 历法类型 "solar"/"lunar"
    birth_time_certainty: str = "certain"       # 时辰确定性 "certain"(记得)/"uncertain"(大概)/"unknown"(不记得)

    # 个人信息
    name: Optional[str] = None                  # 姓名/标签（用于多人分析时区分）
    gender: Optional[str] = None                # 性别 "male"/"female"
    birth_place_lng: Optional[float] = None     # 出生地经度
    mbti_type: Optional[str] = None             # MBTI类型

    # 外应信息
    numbers: Optional[List[int]] = None         # 随机数字
    character: Optional[str] = None             # 汉字
    current_direction: Optional[str] = None     # 当前方位
    favorite_color: Optional[str] = None        # 喜欢的颜色

    # 多人八字信息（用于姻缘、帮亲人问事等场景）
    additional_persons: List[PersonBirthInfo] = field(default_factory=list)  # 额外的人物信息

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {}
        for key, value in self.__dict__.items():
            if value is not None:
                if isinstance(value, datetime):
                    result[key] = value.isoformat()
                elif isinstance(value, list):
                    # 处理PersonBirthInfo列表
                    if len(value) > 0 and isinstance(value[0], PersonBirthInfo):
                        result[key] = [person.to_dict() for person in value]
                    elif len(value) == 0 and key == 'additional_persons':
                        # 空的additional_persons列表也要保存
                        result[key] = []
                    else:
                        result[key] = value
                else:
                    result[key] = value
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserInput':
        """从字典创建"""
        if 'current_time' in data and isinstance(data['current_time'], str):
            data['current_time'] = datetime.fromisoformat(data['current_time'])
        if 'initial_inquiry_time' in data and isinstance(data['initial_inquiry_time'], str):
            data['initial_inquiry_time'] = datetime.fromisoformat(data['initial_inquiry_time'])
        if 'additional_persons' in data and isinstance(data['additional_persons'], list):
            data['additional_persons'] = [PersonBirthInfo.from_dict(p) for p in data['additional_persons']]
        return cls(**data)


@dataclass
class TheoryAnalysisResult:
    """单个理论分析结果"""
    theory_name: str                            # 理论名称
    calculation_data: Dict[str, Any]            # 计算原始数据
    interpretation: str                         # LLM解读文本

    judgment: str                               # 吉凶判断 "吉"/"凶"/"平"
    judgment_level: float                       # 程度 0-1

    timing: Optional[Dict[str, Any]] = None     # 时机预测
    advice: Optional[str] = None                # 建议

    confidence: float = 0.8                     # 置信度

    # 标准问题回答
    retrospective_answer: Optional[Dict[str, Any]] = None  # 回溯问题答案
    predictive_answer: Optional[Dict[str, Any]] = None     # 预测问题答案

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'theory_name': self.theory_name,
            'calculation_data': self.calculation_data,
            'interpretation': self.interpretation,
            'judgment': self.judgment,
            'judgment_level': self.judgment_level,
            'timing': self.timing,
            'advice': self.advice,
            'confidence': self.confidence,
            'retrospective_answer': self.retrospective_answer,
            'predictive_answer': self.predictive_answer
        }


@dataclass
class ConflictInfo:
    """冲突信息"""
    has_conflict: bool
    conflicts: List[Dict[str, Any]]
    resolution: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'has_conflict': self.has_conflict,
            'conflicts': self.conflicts,
            'resolution': self.resolution
        }


@dataclass
class ComprehensiveReport:
    """综合报告"""
    # 基本信息
    report_id: str
    created_at: datetime
    user_input_summary: Dict[str, Any]

    # 理论选择
    selected_theories: List[str]
    selection_reason: str

    # 各理论结果
    theory_results: List[TheoryAnalysisResult]

    # 冲突处理
    conflict_info: ConflictInfo

    # 综合结论
    executive_summary: str                      # 执行摘要（200-300字简要总结）
    detailed_analysis: str                      # 详细问题解答（主要内容，直接回答用户问题）
    retrospective_analysis: str                 # 回溯分析（次要内容，如适用）
    predictive_analysis: str                    # 预测分析（次要内容，如适用）
    comprehensive_advice: List[Dict[str, Any]]  # 综合建议

    # 元信息
    overall_confidence: float                   # 综合置信度
    limitations: List[str]                      # 局限性说明

    # 用户反馈（后续填充）
    user_feedback: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'report_id': self.report_id,
            'created_at': self.created_at.isoformat(),
            'user_input_summary': self.user_input_summary,
            'selected_theories': self.selected_theories,
            'selection_reason': self.selection_reason,
            'theory_results': [r.to_dict() for r in self.theory_results],
            'conflict_info': self.conflict_info.to_dict(),
            'executive_summary': self.executive_summary,
            'detailed_analysis': self.detailed_analysis,
            'retrospective_analysis': self.retrospective_analysis,
            'predictive_analysis': self.predictive_analysis,
            'comprehensive_advice': self.comprehensive_advice,
            'overall_confidence': self.overall_confidence,
            'limitations': self.limitations,
            'user_feedback': self.user_feedback
        }

    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


@dataclass
class AppConfig:
    """应用配置"""
    # API配置
    claude_api_key: str
    deepseek_api_key: str
    primary_api: str = "claude"

    # 分析配置
    max_theories: int = 5
    min_theories: int = 3
    enable_quick_feedback: bool = True

    # 界面配置
    language: str = "zh_CN"
    theme: str = "light"

    # 隐私配置
    auto_delete_after_days: int = 30
    encrypt_local_data: bool = True

    # 日志配置
    log_level: str = "INFO"
    log_calculations: bool = True

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppConfig':
        """从字典创建配置"""
        return cls(**data)
