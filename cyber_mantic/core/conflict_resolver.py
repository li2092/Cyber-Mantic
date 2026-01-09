"""
冲突解决器 - 处理多理论间的结果冲突

实现4级冲突检测和解决机制：
- Level 1: 完全一致 - 无需处理
- Level 2: 微小差异 - 简单平均
- Level 3: 显著差异 - 加权调和
- Level 4: 严重冲突 - 深度分析
"""
from typing import List, Dict, Any, Tuple, Optional
from models import TheoryAnalysisResult, ConflictInfo
from core.arbitration_system import ArbitrationSystem, ArbitrationConflictInfo, ArbitrationStatus
from .constants import (
    JUDGMENT_THRESHOLD_MINOR,
    JUDGMENT_THRESHOLD_SIGNIFICANT,
    CONFIDENCE_WEIGHT_FACTOR
)
from utils.logger import get_logger
import math


class ConflictResolver:
    """冲突解决器

    使用全局常量定义冲突阈值（来自core.constants）：
    - JUDGMENT_THRESHOLD_MINOR = 0.2 (20%差异)
    - JUDGMENT_THRESHOLD_SIGNIFICANT = 0.4 (40%差异)
    - CONFIDENCE_WEIGHT_FACTOR = 1.5 (置信度权重)
    """

    # 吉凶映射（用于数值化）
    JUDGMENT_VALUES = {
        "大吉": 1.0,
        "吉": 0.7,
        "平": 0.5,
        "凶": 0.3,
        "大凶": 0.0
    }

    def __init__(self, arbitration_system: ArbitrationSystem = None):
        """
        初始化冲突解决器
        
        Args:
            arbitration_system: 仲裁系统（可选）
        """
        self.arbitration_system = arbitration_system
        self.logger = get_logger(__name__)

    def detect_and_resolve_conflicts(
        self,
        results: List[TheoryAnalysisResult]
    ) -> ConflictInfo:
        """
        检测并解决理论间的冲突

        Args:
            results: 理论结果列表

        Returns:
            冲突信息（包含解决方案）
        """
        if len(results) < 2:
            return ConflictInfo(has_conflict=False, conflicts=[], resolution=None)

        # 1. 检测冲突
        conflicts = self._detect_all_conflicts(results)

        # 2. 分级冲突
        categorized_conflicts = self._categorize_conflicts(conflicts)

        # 3. 解决冲突
        resolution = self._resolve_conflicts(results, categorized_conflicts)

        has_conflict = len(conflicts) > 0

        return ConflictInfo(
            has_conflict=has_conflict,
            conflicts=conflicts,
            resolution=resolution
        )

    def _detect_all_conflicts(
        self,
        results: List[TheoryAnalysisResult]
    ) -> List[Dict[str, Any]]:
        """
        全面检测冲突

        Args:
            results: 理论结果列表

        Returns:
            冲突列表
        """
        conflicts = []

        for i, r1 in enumerate(results):
            for j, r2 in enumerate(results[i+1:], i+1):
                conflict = self._compare_two_results(r1, r2)
                if conflict:
                    conflicts.append(conflict)

        return conflicts

    def _compare_two_results(
        self,
        r1: TheoryAnalysisResult,
        r2: TheoryAnalysisResult
    ) -> Optional[Dict[str, Any]]:
        """
        比较两个理论结果

        Args:
            r1: 理论结果1
            r2: 理论结果2

        Returns:
            冲突信息（如果存在冲突）
        """
        # 将判断转换为数值
        v1 = self._judgment_to_value(r1.judgment, r1.judgment_level)
        v2 = self._judgment_to_value(r2.judgment, r2.judgment_level)

        # 计算差异
        diff = abs(v1 - v2)

        # 判断冲突级别
        if diff < JUDGMENT_THRESHOLD_MINOR:
            # Level 1: 完全一致或微小差异
            return None  # 不记录为冲突

        elif diff < JUDGMENT_THRESHOLD_SIGNIFICANT:
            # Level 2: 微小差异
            return {
                "level": 2,
                "severity": "微小",
                "type": "程度差异",
                "theories": [r1.theory_name, r2.theory_name],
                "values": {"理论1": v1, "理论2": v2, "差异": diff},
                "details": f"{r1.theory_name}判断倾向{self._value_to_description(v1)}，"
                          f"{r2.theory_name}判断倾向{self._value_to_description(v2)}，"
                          f"差异度{diff:.2f}",
                "resolution_strategy": "简单平均"
            }

        elif diff < 0.5:
            # Level 3: 显著差异
            return {
                "level": 3,
                "severity": "显著",
                "type": "显著差异",
                "theories": [r1.theory_name, r2.theory_name],
                "values": {"理论1": v1, "理论2": v2, "差异": diff},
                "details": f"{r1.theory_name}({r1.judgment})与{r2.theory_name}({r2.judgment})"
                          f"存在显著差异（差异度{diff:.2f}）",
                "resolution_strategy": "加权调和"
            }

        else:
            # Level 4: 严重冲突（吉凶对立）
            return {
                "level": 4,
                "severity": "严重",
                "type": "吉凶对立",
                "theories": [r1.theory_name, r2.theory_name],
                "values": {"理论1": v1, "理论2": v2, "差异": diff},
                "details": f"{r1.theory_name}判断{r1.judgment}（{v1:.2f}），"
                          f"{r2.theory_name}判断{r2.judgment}（{v2:.2f}），"
                          f"存在严重对立",
                "resolution_strategy": "深度分析"
            }

    def _judgment_to_value(self, judgment: str, level: float) -> float:
        """
        将判断转换为数值

        Args:
            judgment: 判断（吉/凶/平等）
            level: 程度（0-1）

        Returns:
            数值（0-1）
        """
        base_value = self.JUDGMENT_VALUES.get(judgment, 0.5)

        # 根据level微调
        # level越高，越接近极端值
        if judgment in ["大吉", "吉"]:
            # 吉的情况，level越高越好
            return base_value + (1.0 - base_value) * (level - 0.5) * 0.5
        elif judgment in ["大凶", "凶"]:
            # 凶的情况，level越高越凶
            return base_value - base_value * (level - 0.5) * 0.5
        else:
            # 平的情况，接近0.5
            return 0.5

    def _value_to_description(self, value: float) -> str:
        """
        将数值转换为描述

        Args:
            value: 数值（0-1）

        Returns:
            描述
        """
        if value >= 0.85:
            return "大吉"
        elif value >= 0.65:
            return "吉"
        elif value >= 0.35:
            return "平"
        elif value >= 0.15:
            return "凶"
        else:
            return "大凶"

    def _categorize_conflicts(
        self,
        conflicts: List[Dict[str, Any]]
    ) -> Dict[int, List[Dict[str, Any]]]:
        """
        分级冲突

        Args:
            conflicts: 冲突列表

        Returns:
            分级后的冲突字典
        """
        categorized = {2: [], 3: [], 4: []}

        for conflict in conflicts:
            level = conflict.get("level", 2)
            if level in categorized:
                categorized[level].append(conflict)

        return categorized

    def _resolve_conflicts(
        self,
        results: List[TheoryAnalysisResult],
        categorized_conflicts: Dict[int, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        解决冲突

        Args:
            results: 理论结果列表
            categorized_conflicts: 分级冲突

        Returns:
            解决方案
        """
        resolution = {
            "总体策略": "",
            "调和结果": {},
            "可信度评估": 0.0,
            "建议": []
        }

        # 统计冲突
        total_conflicts = sum(len(conflicts) for conflicts in categorized_conflicts.values())
        level4_count = len(categorized_conflicts.get(4, []))
        level3_count = len(categorized_conflicts.get(3, []))
        level2_count = len(categorized_conflicts.get(2, []))

        # 确定总体策略
        if level4_count > 0:
            resolution["总体策略"] = "需要仲裁"
            resolution["可信度评估"] = 0.5  # 严重冲突降低可信度
            resolution["需要仲裁"] = True
            resolution["仲裁冲突"] = categorized_conflicts.get(4, [])
            self.logger.info(f"检测到{level4_count}个严重冲突，建议启动仲裁")
        elif level3_count > 0:
            resolution["总体策略"] = "加权平均调和"
            resolution["可信度评估"] = 0.7
        elif level2_count > 0:
            resolution["总体策略"] = "简单平均调和"
            resolution["可信度评估"] = 0.85
        else:
            resolution["总体策略"] = "无冲突，结果一致"
            resolution["可信度评估"] = 0.95

        # 计算调和结果
        reconciled = self._calculate_reconciled_result(results, categorized_conflicts)
        resolution["调和结果"] = reconciled

        # 生成建议
        resolution["建议"] = self._generate_recommendations(
            results,
            categorized_conflicts,
            reconciled
        )

        return resolution

    def _calculate_reconciled_result(
        self,
        results: List[TheoryAnalysisResult],
        categorized_conflicts: Dict[int, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        计算调和后的结果

        Args:
            results: 理论结果列表
            categorized_conflicts: 分级冲突

        Returns:
            调和结果
        """
        # 计算权重
        weights = self._calculate_weights(results, categorized_conflicts)

        # 加权平均判断值
        weighted_sum = 0.0
        total_weight = 0.0

        for result, weight in zip(results, weights):
            value = self._judgment_to_value(result.judgment, result.judgment_level)
            weighted_sum += value * weight
            total_weight += weight

        if total_weight > 0:
            reconciled_value = weighted_sum / total_weight
        else:
            reconciled_value = 0.5

        # 转换为判断
        reconciled_judgment = self._value_to_description(reconciled_value)

        # 计算置信度
        confidence_values = [r.confidence * w for r, w in zip(results, weights)]
        if total_weight > 0:
            reconciled_confidence = sum(confidence_values) / total_weight
        else:
            reconciled_confidence = 0.5

        return {
            "综合判断": reconciled_judgment,
            "数值": reconciled_value,
            "置信度": reconciled_confidence,
            "理论权重": {
                r.theory_name: w for r, w in zip(results, weights)
            }
        }

    def _calculate_weights(
        self,
        results: List[TheoryAnalysisResult],
        categorized_conflicts: Dict[int, List[Dict[str, Any]]]
    ) -> List[float]:
        """
        计算各理论的权重

        Args:
            results: 理论结果列表
            categorized_conflicts: 分级冲突

        Returns:
            权重列表
        """
        weights = []

        for result in results:
            # 基础权重来自置信度
            weight = result.confidence

            # 惩罚因子：参与严重冲突的理论降低权重
            penalty = 1.0

            # 检查是否参与Level 4冲突
            for conflict in categorized_conflicts.get(4, []):
                if result.theory_name in conflict.get("theories", []):
                    penalty *= 0.7  # 降低30%权重

            # 检查是否参与Level 3冲突
            for conflict in categorized_conflicts.get(3, []):
                if result.theory_name in conflict.get("theories", []):
                    penalty *= 0.85  # 降低15%权重

            weight *= penalty
            weights.append(weight)

        # 归一化
        total = sum(weights)
        if total > 0:
            weights = [w / total for w in weights]
        else:
            # 均等权重
            weights = [1.0 / len(results)] * len(results)

        return weights

    def _generate_recommendations(
        self,
        results: List[TheoryAnalysisResult],
        categorized_conflicts: Dict[int, List[Dict[str, Any]]],
        reconciled: Dict[str, Any]
    ) -> List[str]:
        """
        生成建议

        Args:
            results: 理论结果列表
            categorized_conflicts: 分级冲突
            reconciled: 调和结果

        Returns:
            建议列表
        """
        recommendations = []

        level4_count = len(categorized_conflicts.get(4, []))
        level3_count = len(categorized_conflicts.get(3, []))

        # 严重冲突建议
        if level4_count > 0:
            recommendations.append(
                f"检测到{level4_count}个严重冲突，建议谨慎参考，"
                "可补充更多信息或咨询专业人士"
            )

            # 列出冲突的理论
            conflicting_theories = set()
            for conflict in categorized_conflicts[4]:
                conflicting_theories.update(conflict.get("theories", []))

            recommendations.append(
                f"以下理论存在显著分歧：{', '.join(conflicting_theories)}，"
                "建议重点关注置信度较高的理论"
            )

        # 显著差异建议
        elif level3_count > 0:
            recommendations.append(
                f"检测到{level3_count}个显著差异，综合结果已进行加权调和"
            )

        # 一致性建议
        else:
            recommendations.append("各理论结果较为一致，综合判断可信度较高")

        # 置信度建议
        reconciled_confidence = reconciled.get("置信度", 0.5)
        if reconciled_confidence < 0.6:
            recommendations.append(
                "综合置信度较低，建议补充更多信息以提高预测准确性"
            )
        elif reconciled_confidence >= 0.8:
            recommendations.append("综合置信度较高，预测结果较为可靠")

        # 理论权重建议
        weights = reconciled.get("理论权重", {})
        if weights:
            max_theory = max(weights.items(), key=lambda x: x[1])
            if max_theory[1] > 0.4:
                recommendations.append(
                    f"{max_theory[0]}在综合判断中权重最高({max_theory[1]:.1%})，"
                    "建议重点参考该理论的具体分析"
                )

        return recommendations

    def get_conflict_summary(self, conflict_info: ConflictInfo) -> str:
        """
        获取冲突摘要

        Args:
            conflict_info: 冲突信息

        Returns:
            冲突摘要文本
        """
        if not conflict_info.has_conflict:
            return "各理论结果一致，无显著冲突。"

        summary_parts = []

        # 统计冲突
        level_counts = {}
        for conflict in conflict_info.conflicts:
            level = conflict.get("level", 0)
            level_counts[level] = level_counts.get(level, 0) + 1

        # 生成摘要
        summary_parts.append(f"检测到{len(conflict_info.conflicts)}个冲突：")

        if level_counts.get(4, 0) > 0:
            summary_parts.append(f"- 严重冲突（Level 4）：{level_counts[4]}个")
        if level_counts.get(3, 0) > 0:
            summary_parts.append(f"- 显著差异（Level 3）：{level_counts[3]}个")
        if level_counts.get(2, 0) > 0:
            summary_parts.append(f"- 微小差异（Level 2）：{level_counts[2]}个")

        # 添加解决策略
        if conflict_info.resolution:
            strategy = conflict_info.resolution.get("总体策略", "")
            if strategy:
                summary_parts.append(f"\n解决策略：{strategy}")

            reconciled = conflict_info.resolution.get("调和结果", {})
            if reconciled:
                judgment = reconciled.get("综合判断", "")
                confidence = reconciled.get("置信度", 0)
                summary_parts.append(
                    f"调和结果：{judgment}（置信度：{confidence:.1%}）"
                )

        return "\n".join(summary_parts)
