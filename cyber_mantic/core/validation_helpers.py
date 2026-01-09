"""
数据验证辅助函数 - Dataclass与Pydantic Schema之间的转换

提供便捷的验证和转换函数，确保：
- Dataclass对象可以被验证
- 验证后的数据可以创建Dataclass对象
- 前后端数据传输的一致性
"""
from typing import TypeVar, Type, Dict, Any, Union
from pydantic import BaseModel, ValidationError

from models import (
    UserInput,
    PersonBirthInfo,
    TheoryAnalysisResult,
    ConflictInfo,
    ComprehensiveReport
)
from .validation import (
    UserInputSchema,
    PersonBirthInfoSchema,
    TheoryAnalysisResultSchema,
    ConflictInfoSchema,
    ComprehensiveReportSchema
)
from .exceptions import ValidationError as CustomValidationError


T = TypeVar('T')
S = TypeVar('S', bound=BaseModel)


def validate_user_input(data: Dict[str, Any]) -> UserInput:
    """
    验证并创建UserInput对象

    Args:
        data: 用户输入字典

    Returns:
        验证后的UserInput对象

    Raises:
        CustomValidationError: 验证失败时抛出
    """
    try:
        # 使用Pydantic验证
        schema = UserInputSchema(**data)

        # 转换为dataclass（移除Pydantic特有字段）
        validated_data = schema.model_dump()

        # 转换additional_persons
        if 'additional_persons' in validated_data:
            validated_data['additional_persons'] = [
                PersonBirthInfo(**p) for p in validated_data['additional_persons']
            ]

        return UserInput.from_dict(validated_data)

    except ValidationError as e:
        # 转换Pydantic ValidationError为自定义异常
        error_messages = []
        for error in e.errors():
            field = '.'.join(str(x) for x in error['loc'])
            msg = error['msg']
            error_messages.append(f"{field}: {msg}")

        raise CustomValidationError(
            "user_input",
            "; ".join(error_messages)
        )


def validate_person_birth_info(data: Dict[str, Any]) -> PersonBirthInfo:
    """
    验证并创建PersonBirthInfo对象

    Args:
        data: 个人出生信息字典

    Returns:
        验证后的PersonBirthInfo对象

    Raises:
        CustomValidationError: 验证失败时抛出
    """
    try:
        schema = PersonBirthInfoSchema(**data)
        validated_data = schema.model_dump()
        return PersonBirthInfo.from_dict(validated_data)

    except ValidationError as e:
        error_messages = []
        for error in e.errors():
            field = '.'.join(str(x) for x in error['loc'])
            msg = error['msg']
            error_messages.append(f"{field}: {msg}")

        raise CustomValidationError(
            "person_birth_info",
            "; ".join(error_messages)
        )


def validate_theory_result(data: Dict[str, Any]) -> TheoryAnalysisResult:
    """
    验证理论分析结果

    Args:
        data: 理论分析结果字典

    Returns:
        验证后的TheoryAnalysisResult对象

    Raises:
        CustomValidationError: 验证失败时抛出
    """
    try:
        schema = TheoryAnalysisResultSchema(**data)
        validated_data = schema.model_dump()
        return TheoryAnalysisResult(**validated_data)

    except ValidationError as e:
        error_messages = []
        for error in e.errors():
            field = '.'.join(str(x) for x in error['loc'])
            msg = error['msg']
            error_messages.append(f"{field}: {msg}")

        raise CustomValidationError(
            "theory_result",
            "; ".join(error_messages)
        )


def validate_conflict_info(data: Dict[str, Any]) -> ConflictInfo:
    """
    验证冲突信息

    Args:
        data: 冲突信息字典

    Returns:
        验证后的ConflictInfo对象

    Raises:
        CustomValidationError: 验证失败时抛出
    """
    try:
        schema = ConflictInfoSchema(**data)
        validated_data = schema.model_dump()
        return ConflictInfo(**validated_data)

    except ValidationError as e:
        error_messages = []
        for error in e.errors():
            field = '.'.join(str(x) for x in error['loc'])
            msg = error['msg']
            error_messages.append(f"{field}: {msg}")

        raise CustomValidationError(
            "conflict_info",
            "; ".join(error_messages)
        )


def validate_comprehensive_report(data: Dict[str, Any]) -> ComprehensiveReport:
    """
    验证综合报告

    Args:
        data: 综合报告字典

    Returns:
        验证后的ComprehensiveReport对象

    Raises:
        CustomValidationError: 验证失败时抛出
    """
    try:
        schema = ComprehensiveReportSchema(**data)
        validated_data = schema.model_dump()

        # 转换嵌套对象
        if 'theory_results' in validated_data:
            validated_data['theory_results'] = [
                TheoryAnalysisResult(**r) for r in validated_data['theory_results']
            ]

        if 'conflict_info' in validated_data:
            validated_data['conflict_info'] = ConflictInfo(**validated_data['conflict_info'])

        return ComprehensiveReport(**validated_data)

    except ValidationError as e:
        error_messages = []
        for error in e.errors():
            field = '.'.join(str(x) for x in error['loc'])
            msg = error['msg']
            error_messages.append(f"{field}: {msg}")

        raise CustomValidationError(
            "comprehensive_report",
            "; ".join(error_messages)
        )


def safe_validate(
    schema_class: Type[S],
    data: Dict[str, Any],
    field_name: str = "data"
) -> Union[S, None]:
    """
    安全验证数据，失败时返回None而不抛出异常

    Args:
        schema_class: Pydantic Schema类
        data: 要验证的数据
        field_name: 字段名（用于日志）

    Returns:
        验证成功返回Schema对象，失败返回None
    """
    try:
        return schema_class(**data)
    except ValidationError:
        # 静默失败，返回None
        return None


def get_validation_errors(
    schema_class: Type[S],
    data: Dict[str, Any]
) -> Dict[str, str]:
    """
    获取验证错误详情（不抛出异常）

    Args:
        schema_class: Pydantic Schema类
        data: 要验证的数据

    Returns:
        错误字典，格式为 {字段: 错误消息}
    """
    try:
        schema_class(**data)
        return {}
    except ValidationError as e:
        errors = {}
        for error in e.errors():
            field = '.'.join(str(x) for x in error['loc'])
            errors[field] = error['msg']
        return errors


# 导出公共接口
__all__ = [
    'validate_user_input',
    'validate_person_birth_info',
    'validate_theory_result',
    'validate_conflict_info',
    'validate_comprehensive_report',
    'safe_validate',
    'get_validation_errors'
]
