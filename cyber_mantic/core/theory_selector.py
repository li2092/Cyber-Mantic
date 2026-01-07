"""
理论选择器
"""
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from models import UserInput
from theories import TheoryRegistry


class TheorySelector:
    """理论选择器，负责选择最适合的理论组合"""

    # 问题类型特征向量 (8维)
    # [时间敏感性, 空间相关性, 人际关系, 财务相关, 健康相关, 决策相关, 情感强度, 复杂程度]
    QUESTION_TYPE_VECTORS = {
        "事业": [0.7, 0.3, 0.8, 0.9, 0.2, 0.9, 0.5, 0.8],
        "财运": [0.6, 0.4, 0.5, 1.0, 0.1, 0.8, 0.4, 0.7],
        "感情": [0.4, 0.2, 0.9, 0.3, 0.3, 0.6, 1.0, 0.8],
        "婚姻": [0.3, 0.3, 1.0, 0.5, 0.2, 0.7, 0.9, 0.9],
        "健康": [0.9, 0.2, 0.3, 0.4, 1.0, 0.5, 0.7, 0.6],
        "学业": [0.5, 0.2, 0.4, 0.3, 0.2, 0.6, 0.5, 0.5],
        "人际": [0.3, 0.3, 1.0, 0.2, 0.1, 0.4, 0.8, 0.6],
        "择时": [1.0, 0.8, 0.3, 0.5, 0.2, 1.0, 0.3, 0.5],
        "决策": [0.7, 0.5, 0.6, 0.7, 0.2, 1.0, 0.5, 0.8],
        "性格": [0.1, 0.1, 0.7, 0.3, 0.4, 0.2, 0.6, 0.7],
    }

    # 各理论优势特征向量
    # [时间敏感性, 空间相关性, 人际关系, 财务相关, 健康相关, 决策相关, 情感强度, 复杂程度]
    THEORY_STRENGTH_VECTORS = {
        "八字":     [0.3, 0.1, 0.8, 0.7, 0.9, 0.5, 0.6, 0.9],  # 擅长长期命理
        "奇门遁甲": [0.9, 0.8, 0.6, 0.85, 0.7, 0.9, 0.4, 0.6],  # V2版本：完整算法，恢复并提升权重
        "梅花易数": [0.7, 0.5, 0.7, 0.6, 0.5, 0.6, 0.8, 0.5],  # 简单灵活
        "小六壬":   [0.8, 0.3, 0.5, 0.7, 0.6, 0.4, 0.5, 0.3],  # 快速简单
        "测字术":   [0.6, 0.2, 0.9, 0.4, 0.3, 0.3, 0.9, 0.4],  # 简单直观
        "六爻":     [0.5, 0.4, 0.8, 0.9, 0.7, 0.8, 0.7, 0.6],  # 占卜准确
        "紫微斗数": [0.2, 0.1, 0.9, 0.8, 0.9, 0.6, 0.7, 0.9],  # 全面深入
        "大六壬":   [0.8, 0.7, 0.7, 0.7, 0.7, 0.85, 0.5, 0.8],  # V2版本：九宗门发用规则，恢复并提升权重
    }

    # 理论优先级分类
    THEORY_PRIORITY = {
        "快速": ["小六壬", "测字术", "梅花易数"],
        "基础": ["八字", "紫微斗数"],
        "深度": ["奇门遁甲", "大六壬", "六爻"]
    }

    # 权重配置
    W_INFO = 0.4       # 信息完备度权重
    W_QUESTION = 0.35  # 问题匹配度权重
    W_MBTI = 0.25      # MBTI适配度权重

    def __init__(self):
        pass

    def select_theories(
        self,
        user_input: UserInput,
        max_theories: int = 5,
        min_theories: int = 3
    ) -> Tuple[List[Dict[str, Any]], Optional[List[str]]]:
        """
        选择最适合的理论组合

        Args:
            user_input: 用户输入
            max_theories: 最多选择几个理论
            min_theories: 最少选择几个理论

        Returns:
            (选中的理论列表, 缺失信息建议)
        """
        question_type = user_input.question_type
        mbti_type = user_input.mbti_type

        all_theories = TheoryRegistry.get_all_theories()

        # 计算所有理论的适配度
        fitness_scores = []
        for theory_name, theory in all_theories.items():
            fitness = self.calculate_theory_fitness(
                user_input,
                question_type,
                theory,
                mbti_type
            )

            if fitness > 0:
                # 确定优先级
                priority = "基础"
                for p, theories in self.THEORY_PRIORITY.items():
                    if theory_name in theories:
                        priority = p
                        break

                # 获取信息完备度（用于显示）
                info_completeness = theory.get_info_completeness(user_input)

                fitness_scores.append({
                    "theory": theory_name,
                    "fitness": fitness,
                    "priority": priority,
                    "info_completeness": info_completeness,  # 新增字段
                    "reason": f"问题类型匹配度{self.calculate_question_matching(question_type, theory_name):.1%}"
                })

        # 按适配度排序
        fitness_scores.sort(key=lambda x: x["fitness"], reverse=True)

        # 选择理论组合（确保覆盖不同优先级）
        selected = []
        selected_theory_names = set()
        priority_count = {"快速": 0, "基础": 0, "深度": 0}

        # 第一轮：确保每种优先级至少有一个（如果适配度>0.3）
        for item in fitness_scores:
            if len(selected) >= max_theories:
                break
            if priority_count[item["priority"]] == 0 and item["fitness"] > 0.3:
                selected.append(item)
                selected_theory_names.add(item["theory"])
                priority_count[item["priority"]] += 1

        # 第二轮：按适配度继续添加，直到达到max_theories
        for item in fitness_scores:
            if len(selected) >= max_theories:
                break
            if item["theory"] not in selected_theory_names and item["fitness"] > 0.3:
                selected.append(item)
                selected_theory_names.add(item["theory"])
                priority_count[item["priority"]] += 1

        # 如果选中的理论少于最小数量，提示需要补充信息
        if len(selected) < min_theories:
            missing_info = self._get_missing_info_suggestions(user_input)
            return selected, missing_info

        return selected, None

    def calculate_theory_fitness(
        self,
        user_input: UserInput,
        question_type: str,
        theory,
        mbti_type: Optional[str] = None
    ) -> float:
        """
        计算某理论的综合适配度

        Args:
            user_input: 用户输入
            question_type: 问题类型
            theory: 理论对象
            mbti_type: MBTI类型

        Returns:
            适配度分数 0-1
        """
        # 计算各维度分数
        info_score = theory.get_info_completeness(user_input)
        question_score = self.calculate_question_matching(question_type, theory.name)
        mbti_score = 1.0  # MBTI匹配暂时不实现，默认为1

        # 如果信息完备度为0，整体返回0
        if info_score == 0:
            return 0.0

        # 根据时辰确定性调整依赖时辰的理论的适配度
        if user_input.birth_time_certainty == "unknown":
            # 不记得时辰：严重依赖时辰的理论降低权重
            if theory.name in ["八字", "紫微斗数"]:
                info_score *= 0.3  # 只能做简化分析，权重大幅降低
        elif user_input.birth_time_certainty == "uncertain":
            # 大概是这个时辰：依赖时辰的理论略微降低权重
            if theory.name in ["八字", "紫微斗数"]:
                info_score *= 0.8  # 需要多时辰对比，略微降低

        # 加权计算
        fitness = (
            self.W_INFO * info_score +
            self.W_QUESTION * question_score +
            self.W_MBTI * mbti_score
        )

        return fitness

    def calculate_question_matching(self, question_type: str, theory_name: str) -> float:
        """
        使用余弦相似度计算问题类型与理论的匹配度

        Args:
            question_type: 问题类型
            theory_name: 理论名称

        Returns:
            匹配度 0-1
        """
        q_vec = np.array(self.QUESTION_TYPE_VECTORS.get(question_type, [0.5] * 8))
        t_vec = np.array(self.THEORY_STRENGTH_VECTORS.get(theory_name, [0.5] * 8))

        # 余弦相似度
        similarity = np.dot(q_vec, t_vec) / (np.linalg.norm(q_vec) * np.linalg.norm(t_vec))
        return float(similarity)

    def _get_missing_info_suggestions(self, user_input: UserInput) -> List[str]:
        """
        根据当前输入，建议用户补充的信息

        Args:
            user_input: 用户输入

        Returns:
            建议补充的信息列表
        """
        suggestions = []

        if user_input.birth_hour is None:
            suggestions.append("出生时辰（可以提高八字、紫微斗数的准确性）")

        if user_input.numbers is None or len(user_input.numbers) < 3:
            suggestions.append("3个随机数字（用于六爻、梅花易数、小六壬）")

        if user_input.character is None:
            suggestions.append("一个汉字（用于测字分析）")

        return suggestions

    def determine_execution_order(self, selected_theories: List[Dict[str, Any]]) -> List[str]:
        """
        确定理论执行顺序

        原则：快速理论优先 -> 基础理论 -> 深度理论

        Args:
            selected_theories: 选中的理论列表

        Returns:
            理论名称列表（按执行顺序）
        """
        ORDER_PRIORITY = {
            "快速": 1,
            "基础": 2,
            "深度": 3
        }

        sorted_theories = sorted(
            selected_theories,
            key=lambda x: ORDER_PRIORITY[x["priority"]]
        )

        return [t["theory"] for t in sorted_theories]
