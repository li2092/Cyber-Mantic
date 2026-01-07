"""
赛博玄数 - 术数理论基类
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from models import UserInput, TheoryAnalysisResult
from utils.logger import get_logger


class BaseTheory(ABC):
    """术数理论基类"""

    def __init__(self):
        self.name = self.get_name()
        self.logger = get_logger(self.name)  # 添加logger初始化
        self.required_fields = self.get_required_fields()
        self.optional_fields = self.get_optional_fields()
        self.field_weights = self.get_field_weights()
        self.min_completeness = self.get_min_completeness()

    @abstractmethod
    def get_name(self) -> str:
        """获取理论名称"""
        pass

    @abstractmethod
    def get_required_fields(self) -> List[str]:
        """获取必需字段"""
        pass

    @abstractmethod
    def get_optional_fields(self) -> List[str]:
        """获取可选字段"""
        pass

    @abstractmethod
    def get_field_weights(self) -> Dict[str, float]:
        """获取字段权重"""
        pass

    @abstractmethod
    def get_min_completeness(self) -> float:
        """获取最小完备度要求"""
        pass

    @abstractmethod
    def calculate(self, user_input: UserInput) -> Dict[str, Any]:
        """
        计算排盘结果（纯代码实现，不调用LLM）

        Args:
            user_input: 用户输入数据

        Returns:
            计算结果字典
        """
        pass

    def get_info_completeness(self, user_input: UserInput) -> float:
        """
        计算用户信息对该理论的完备度

        Args:
            user_input: 用户输入数据

        Returns:
            完备度分数，范围 0-1
        """
        input_dict = user_input.to_dict()

        # 检查必需字段
        for field in self.required_fields:
            if field not in input_dict or input_dict[field] is None:
                return 0.0  # 必需字段缺失，直接返回0

        # 计算完备度分数
        total_weight = sum(self.field_weights.values())
        achieved_weight = 0.0

        for field, weight in self.field_weights.items():
            if field in input_dict and input_dict[field] is not None:
                achieved_weight += weight

        completeness = achieved_weight / total_weight
        return completeness if completeness >= self.min_completeness else 0.0

    def can_analyze(self, user_input: UserInput) -> bool:
        """
        判断是否可以对该用户输入进行分析

        Args:
            user_input: 用户输入数据

        Returns:
            是否可以分析
        """
        return self.get_info_completeness(user_input) > 0.0

    def to_standard_answer(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        将计算结果转换为标准答案格式

        Args:
            result: 计算结果

        Returns:
            标准答案字典，包含判断、程度、时机等信息
        """
        # 子类可以覆盖此方法以提供特定的转换逻辑
        return {
            'judgment': result.get('judgment', '平'),
            'judgment_level': result.get('judgment_level', 0.5),
            'timing': result.get('timing'),
            'advice': result.get('advice'),
            'confidence': result.get('confidence', 0.8)
        }


class TheoryRegistry:
    """
    理论注册表（线程安全）

    使用类级别锁保护共享的理论字典，确保多线程环境下的安全访问
    """

    _theories: Dict[str, BaseTheory] = {}
    _lock = __import__('threading').RLock()  # 类级别的线程锁

    @classmethod
    def register(cls, theory: BaseTheory):
        """
        注册理论（线程安全）

        Args:
            theory: 理论实例
        """
        with cls._lock:
            cls._theories[theory.name] = theory

    @classmethod
    def get_theory(cls, name: str) -> Optional[BaseTheory]:
        """
        获取理论（线程安全）

        Args:
            name: 理论名称

        Returns:
            理论实例，如果不存在返回None
        """
        with cls._lock:
            return cls._theories.get(name)

    @classmethod
    def get_all_theories(cls) -> Dict[str, BaseTheory]:
        """
        获取所有理论（线程安全，返回副本）

        Returns:
            理论字典的副本，避免外部修改影响注册表
        """
        with cls._lock:
            return cls._theories.copy()

    @classmethod
    def get_theory_names(cls) -> List[str]:
        """
        获取所有理论名称（线程安全）

        Returns:
            理论名称列表
        """
        with cls._lock:
            return list(cls._theories.keys())
