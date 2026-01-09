"""
数据验证模块 - 使用Pydantic确保前后端数据一致性

为关键数据模型提供验证Schema，确保：
- 类型正确性
- 值的合法性
- 必填字段完整性
- 前后端数据契约一致
"""
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator


class PersonBirthInfoSchema(BaseModel):
    """个人出生信息验证Schema"""

    label: str = Field(default="本人", description="人物标签")
    birth_year: Optional[int] = Field(None, ge=1900, le=2100, description="出生年（1900-2100）")
    birth_month: Optional[int] = Field(None, ge=1, le=12, description="出生月（1-12）")
    birth_day: Optional[int] = Field(None, ge=1, le=31, description="出生日（1-31）")
    birth_hour: Optional[int] = Field(None, ge=0, le=23, description="出生时（0-23）")
    birth_minute: Optional[int] = Field(None, ge=0, le=59, description="出生分（0-59）")
    calendar_type: Literal["solar", "lunar"] = Field("solar", description="历法类型")
    birth_time_certainty: Literal["certain", "uncertain", "unknown"] = Field(
        "certain",
        description="时辰确定性"
    )
    gender: Optional[Literal["male", "female"]] = Field(None, description="性别")
    birth_place_lng: Optional[float] = Field(None, ge=-180, le=180, description="出生地经度")
    mbti_type: Optional[str] = Field(None, pattern=r"^[IE][NS][TF][JP]$", description="MBTI类型")

    @field_validator('birth_year', 'birth_month', 'birth_day')
    @classmethod
    def check_date_validity(cls, v, info):
        """验证日期的有效性"""
        if v is not None:
            field_name = info.field_name
            if field_name == 'birth_year' and not (1900 <= v <= 2100):
                raise ValueError(f"出生年份必须在1900-2100之间，当前值：{v}")
            elif field_name == 'birth_month' and not (1 <= v <= 12):
                raise ValueError(f"月份必须在1-12之间，当前值：{v}")
            elif field_name == 'birth_day' and not (1 <= v <= 31):
                raise ValueError(f"日期必须在1-31之间，当前值：{v}")
        return v

    class Config:
        """Pydantic配置"""
        json_schema_extra = {
            "example": {
                "label": "本人",
                "birth_year": 1990,
                "birth_month": 6,
                "birth_day": 15,
                "birth_hour": 10,
                "calendar_type": "solar",
                "birth_time_certainty": "certain",
                "gender": "male",
                "mbti_type": "INTJ"
            }
        }


class UserInputSchema(BaseModel):
    """用户输入验证Schema"""

    # 问题信息（必填）
    question_type: str = Field(..., min_length=1, description="问题类别")
    question_description: str = Field(..., min_length=1, description="问题描述")

    # 时间信息
    current_time: datetime = Field(default_factory=datetime.now, description="当前时间")
    initial_inquiry_time: Optional[datetime] = Field(None, description="起卦时间")

    # 出生信息（可选，但如提供需符合规范）
    birth_year: Optional[int] = Field(None, ge=1900, le=2100, description="出生年")
    birth_month: Optional[int] = Field(None, ge=1, le=12, description="出生月")
    birth_day: Optional[int] = Field(None, ge=1, le=31, description="出生日")
    birth_hour: Optional[int] = Field(None, ge=0, le=23, description="出生时")
    birth_minute: Optional[int] = Field(None, ge=0, le=59, description="出生分")
    calendar_type: Literal["solar", "lunar"] = Field("solar", description="历法类型")
    birth_time_certainty: Literal["certain", "uncertain", "unknown"] = Field(
        "certain",
        description="时辰确定性"
    )

    # 个人信息
    gender: Optional[Literal["male", "female"]] = Field(None, description="性别")
    birth_place_lng: Optional[float] = Field(None, ge=-180, le=180, description="出生地经度")
    mbti_type: Optional[str] = Field(None, pattern=r"^[IE][NS][TF][JP]$", description="MBTI类型")

    # 多人信息
    additional_persons: List[PersonBirthInfoSchema] = Field(
        default_factory=list,
        description="其他人出生信息"
    )

    # 小六壬
    xiaoliu_numbers: Optional[List[int]] = Field(None, min_length=3, max_length=3, description="小六壬数字")

    # 六爻
    liuyao_numbers: Optional[List[int]] = Field(None, min_length=6, max_length=6, description="六爻数字")

    # 测字
    cezi_character: Optional[str] = Field(None, min_length=1, max_length=1, description="测字字符")

    @field_validator('xiaoliu_numbers')
    @classmethod
    def validate_xiaoliu_numbers(cls, v):
        """验证小六壬数字范围（1-9）"""
        if v is not None:
            if not all(1 <= n <= 9 for n in v):
                raise ValueError("小六壬数字必须在1-9之间")
        return v

    @field_validator('liuyao_numbers')
    @classmethod
    def validate_liuyao_numbers(cls, v):
        """验证六爻数字范围（6-9）"""
        if v is not None:
            if not all(6 <= n <= 9 for n in v):
                raise ValueError("六爻数字必须在6-9之间")
        return v

    @model_validator(mode='after')
    def check_birth_info_completeness(self):
        """验证出生信息的完整性"""
        # 如果提供了部分出生信息，检查必要字段
        has_any_birth_info = any([
            self.birth_year,
            self.birth_month,
            self.birth_day
        ])

        if has_any_birth_info:
            # 如果提供了出生信息，年月日必须完整
            if not all([self.birth_year, self.birth_month, self.birth_day]):
                raise ValueError("如果提供出生信息，年、月、日必须完整")

        return self

    class Config:
        """Pydantic配置"""
        json_schema_extra = {
            "example": {
                "question_type": "事业",
                "question_description": "最近是否适合跳槽？",
                "birth_year": 1990,
                "birth_month": 6,
                "birth_day": 15,
                "birth_hour": 10,
                "gender": "male",
                "mbti_type": "INTJ",
                "xiaoliu_numbers": [1, 2, 3]
            }
        }


class TheoryAnalysisResultSchema(BaseModel):
    """理论分析结果验证Schema"""

    theory_name: str = Field(..., min_length=1, description="理论名称")
    calculation_data: Dict[str, Any] = Field(..., description="计算原始数据")
    interpretation: str = Field(..., min_length=1, description="LLM解读文本")

    judgment: Literal["大吉", "吉", "平", "凶", "大凶"] = Field(..., description="吉凶判断")
    judgment_level: float = Field(..., ge=0.0, le=1.0, description="程度（0-1）")

    timing: Optional[Dict[str, Any]] = Field(None, description="时机预测")
    advice: Optional[str] = Field(None, description="建议")

    confidence: float = Field(0.8, ge=0.0, le=1.0, description="置信度（0-1）")

    retrospective_answer: Optional[Dict[str, Any]] = Field(None, description="回溯问题答案")
    predictive_answer: Optional[Dict[str, Any]] = Field(None, description="预测问题答案")

    class Config:
        """Pydantic配置"""
        json_schema_extra = {
            "example": {
                "theory_name": "八字",
                "calculation_data": {"四柱": "..."},
                "interpretation": "命主五行平衡...",
                "judgment": "吉",
                "judgment_level": 0.75,
                "confidence": 0.85
            }
        }


class ConflictInfoSchema(BaseModel):
    """冲突信息验证Schema"""

    has_conflict: bool = Field(..., description="是否存在冲突")
    conflicts: List[Dict[str, Any]] = Field(default_factory=list, description="冲突列表")
    resolution: Optional[Dict[str, Any]] = Field(None, description="解决方案")

    @model_validator(mode='after')
    def check_conflict_consistency(self):
        """验证冲突信息的一致性"""
        if self.has_conflict and not self.conflicts:
            raise ValueError("has_conflict为True时，conflicts不能为空")
        if not self.has_conflict and self.conflicts:
            raise ValueError("has_conflict为False时，conflicts应该为空")
        return self

    class Config:
        """Pydantic配置"""
        json_schema_extra = {
            "example": {
                "has_conflict": True,
                "conflicts": [
                    {
                        "level": 3,
                        "theories": ["八字", "紫微斗数"],
                        "details": "判断存在显著差异"
                    }
                ],
                "resolution": {
                    "总体策略": "加权平均调和",
                    "可信度评估": 0.7
                }
            }
        }


class ComprehensiveReportSchema(BaseModel):
    """综合报告验证Schema"""

    report_id: str = Field(..., min_length=1, description="报告ID")
    created_at: datetime = Field(..., description="创建时间")
    user_input_summary: Dict[str, Any] = Field(..., description="用户输入摘要")

    selected_theories: List[str] = Field(
        ...,
        min_length=1,
        description="选中的理论列表"
    )
    selection_reason: str = Field(..., min_length=1, description="理论选择原因")

    theory_results: List[TheoryAnalysisResultSchema] = Field(
        ...,
        min_length=1,
        description="各理论结果"
    )

    conflict_info: ConflictInfoSchema = Field(..., description="冲突信息")

    executive_summary: str = Field(
        ...,
        min_length=50,
        description="执行摘要（至少50字）"
    )
    detailed_analysis: str = Field(
        ...,
        min_length=100,
        description="详细问题解答（至少100字）"
    )
    retrospective_analysis: str = Field("", description="回溯分析")
    predictive_analysis: str = Field("", description="预测分析")
    comprehensive_advice: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="综合建议"
    )

    overall_confidence: float = Field(..., ge=0.0, le=1.0, description="综合置信度")
    limitations: List[str] = Field(default_factory=list, description="局限性说明")

    user_feedback: Optional[Dict[str, Any]] = Field(None, description="用户反馈")

    @model_validator(mode='after')
    def check_theories_consistency(self):
        """验证理论列表与结果的一致性"""
        result_theory_names = [r.theory_name for r in self.theory_results]

        # 检查selected_theories中的理论是否都有结果
        for theory in self.selected_theories:
            if theory not in result_theory_names:
                raise ValueError(f"选中的理论 '{theory}' 没有对应的分析结果")

        return self

    class Config:
        """Pydantic配置"""
        json_schema_extra = {
            "example": {
                "report_id": "rpt_123456",
                "created_at": "2026-01-09T10:00:00",
                "user_input_summary": {"question_type": "事业"},
                "selected_theories": ["八字", "紫微斗数"],
                "selection_reason": "根据问题类型和用户信息选择",
                "theory_results": [],
                "conflict_info": {"has_conflict": False, "conflicts": []},
                "executive_summary": "综合分析表明...",
                "detailed_analysis": "详细来看，从八字角度...",
                "overall_confidence": 0.8,
                "limitations": []
            }
        }


# 导出所有Schema
__all__ = [
    'PersonBirthInfoSchema',
    'UserInputSchema',
    'TheoryAnalysisResultSchema',
    'ConflictInfoSchema',
    'ComprehensiveReportSchema'
]
