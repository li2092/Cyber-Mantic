"""
冲突解决器测试
"""
import pytest
from models import TheoryAnalysisResult
from core.conflict_resolver import ConflictResolver


class TestConflictResolver:
    """冲突解决器测试"""

    def setup_method(self):
        """设置测试"""
        self.resolver = ConflictResolver()

    def test_no_conflict_same_judgment(self):
        """测试无冲突 - 相同判断"""
        results = [
            TheoryAnalysisResult(
                theory_name="八字",
                calculation_data={},
                interpretation="吉",
                judgment="吉",
                judgment_level=0.8,
                confidence=0.9
            ),
            TheoryAnalysisResult(
                theory_name="紫微斗数",
                calculation_data={},
                interpretation="吉",
                judgment="吉",
                judgment_level=0.75,
                confidence=0.85
            )
        ]

        conflict_info = self.resolver.detect_and_resolve_conflicts(results)

        # 微小差异不应记录为冲突
        assert not conflict_info.has_conflict or len(conflict_info.conflicts) == 0

    def test_minor_difference_level2(self):
        """测试微小差异 - Level 2"""
        results = [
            TheoryAnalysisResult(
                theory_name="八字",
                calculation_data={},
                interpretation="吉",
                judgment="吉",
                judgment_level=0.8,
                confidence=0.9
            ),
            TheoryAnalysisResult(
                theory_name="小六壬",
                calculation_data={},
                interpretation="平",
                judgment="平",
                judgment_level=0.5,
                confidence=0.7
            )
        ]

        conflict_info = self.resolver.detect_and_resolve_conflicts(results)

        assert conflict_info.has_conflict
        assert len(conflict_info.conflicts) >= 1

        # 应该是Level 2冲突
        level2_conflicts = [c for c in conflict_info.conflicts if c["level"] == 2]
        assert len(level2_conflicts) >= 1
        assert level2_conflicts[0]["severity"] == "微小"

    def test_significant_difference_level3(self):
        """测试显著差异 - Level 3"""
        results = [
            TheoryAnalysisResult(
                theory_name="八字",
                calculation_data={},
                interpretation="吉",
                judgment="吉",
                judgment_level=0.85,
                confidence=0.9
            ),
            TheoryAnalysisResult(
                theory_name="梅花易数",
                calculation_data={},
                interpretation="凶",
                judgment="凶",
                judgment_level=0.6,
                confidence=0.75
            )
        ]

        conflict_info = self.resolver.detect_and_resolve_conflicts(results)

        assert conflict_info.has_conflict
        assert len(conflict_info.conflicts) >= 1

        # 应该是Level 3或Level 4冲突
        high_level_conflicts = [c for c in conflict_info.conflicts if c["level"] >= 3]
        assert len(high_level_conflicts) >= 1

    def test_severe_conflict_level4(self):
        """测试严重冲突 - Level 4"""
        results = [
            TheoryAnalysisResult(
                theory_name="八字",
                calculation_data={},
                interpretation="大吉",
                judgment="大吉",
                judgment_level=0.95,
                confidence=0.9
            ),
            TheoryAnalysisResult(
                theory_name="六爻",
                calculation_data={},
                interpretation="大凶",
                judgment="大凶",
                judgment_level=0.9,
                confidence=0.85
            )
        ]

        conflict_info = self.resolver.detect_and_resolve_conflicts(results)

        assert conflict_info.has_conflict
        assert len(conflict_info.conflicts) >= 1

        # 应该是Level 4严重冲突
        level4_conflicts = [c for c in conflict_info.conflicts if c["level"] == 4]
        assert len(level4_conflicts) >= 1
        assert level4_conflicts[0]["severity"] == "严重"
        assert level4_conflicts[0]["type"] == "吉凶对立"

    def test_resolution_strategy_simple_average(self):
        """测试解决策略 - 简单平均"""
        results = [
            TheoryAnalysisResult(
                theory_name="八字",
                calculation_data={},
                interpretation="吉",
                judgment="吉",
                judgment_level=0.7,
                confidence=0.9
            ),
            TheoryAnalysisResult(
                theory_name="小六壬",
                calculation_data={},
                interpretation="吉",
                judgment="吉",
                judgment_level=0.65,
                confidence=0.8
            )
        ]

        conflict_info = self.resolver.detect_and_resolve_conflicts(results)

        # 即使无冲突，也应该有resolution
        if conflict_info.resolution:
            assert "总体策略" in conflict_info.resolution
            assert "调和结果" in conflict_info.resolution

    def test_resolution_strategy_weighted_average(self):
        """测试解决策略 - 加权平均"""
        results = [
            TheoryAnalysisResult(
                theory_name="八字",
                calculation_data={},
                interpretation="吉",
                judgment="吉",
                judgment_level=0.8,
                confidence=0.95
            ),
            TheoryAnalysisResult(
                theory_name="紫微斗数",
                calculation_data={},
                interpretation="平",
                judgment="平",
                judgment_level=0.5,
                confidence=0.6
            )
        ]

        conflict_info = self.resolver.detect_and_resolve_conflicts(results)

        assert conflict_info.resolution is not None
        assert "调和结果" in conflict_info.resolution

        # 高置信度的理论应该有更高的权重
        reconciled = conflict_info.resolution["调和结果"]
        weights = reconciled.get("理论权重", {})
        if weights:
            assert weights.get("八字", 0) > weights.get("紫微斗数", 0)

    def test_resolution_strategy_deep_analysis(self):
        """测试解决策略 - 深度分析"""
        results = [
            TheoryAnalysisResult(
                theory_name="八字",
                calculation_data={},
                interpretation="大吉",
                judgment="大吉",
                judgment_level=0.9,
                confidence=0.9
            ),
            TheoryAnalysisResult(
                theory_name="奇门遁甲",
                calculation_data={},
                interpretation="大凶",
                judgment="大凶",
                judgment_level=0.85,
                confidence=0.85
            )
        ]

        conflict_info = self.resolver.detect_and_resolve_conflicts(results)

        assert conflict_info.has_conflict
        assert conflict_info.resolution is not None
        assert conflict_info.resolution["总体策略"] == "深度分析调和"

        # 严重冲突应降低可信度
        assert conflict_info.resolution["可信度评估"] < 0.7

    def test_multiple_theories_complex_conflicts(self):
        """测试多理论复杂冲突"""
        results = [
            TheoryAnalysisResult(
                theory_name="八字",
                calculation_data={},
                interpretation="吉",
                judgment="吉",
                judgment_level=0.8,
                confidence=0.9
            ),
            TheoryAnalysisResult(
                theory_name="紫微斗数",
                calculation_data={},
                interpretation="吉",
                judgment="吉",
                judgment_level=0.75,
                confidence=0.85
            ),
            TheoryAnalysisResult(
                theory_name="小六壬",
                calculation_data={},
                interpretation="平",
                judgment="平",
                judgment_level=0.5,
                confidence=0.7
            ),
            TheoryAnalysisResult(
                theory_name="梅花易数",
                calculation_data={},
                interpretation="凶",
                judgment="凶",
                judgment_level=0.6,
                confidence=0.75
            )
        ]

        conflict_info = self.resolver.detect_and_resolve_conflicts(results)

        assert conflict_info.has_conflict
        # 应该检测到多个冲突
        assert len(conflict_info.conflicts) >= 2

        # 应该有解决方案
        assert conflict_info.resolution is not None
        assert "调和结果" in conflict_info.resolution

    def test_reconciled_result_structure(self):
        """测试调和结果结构"""
        results = [
            TheoryAnalysisResult(
                theory_name="八字",
                calculation_data={},
                interpretation="吉",
                judgment="吉",
                judgment_level=0.8,
                confidence=0.9
            ),
            TheoryAnalysisResult(
                theory_name="紫微斗数",
                calculation_data={},
                interpretation="平",
                judgment="平",
                judgment_level=0.5,
                confidence=0.75
            )
        ]

        conflict_info = self.resolver.detect_and_resolve_conflicts(results)

        assert conflict_info.resolution is not None
        reconciled = conflict_info.resolution["调和结果"]

        # 验证结构
        assert "综合判断" in reconciled
        assert "数值" in reconciled
        assert "置信度" in reconciled
        assert "理论权重" in reconciled

        # 验证数值范围
        assert 0 <= reconciled["数值"] <= 1
        assert 0 <= reconciled["置信度"] <= 1

    def test_conflict_summary(self):
        """测试冲突摘要"""
        results = [
            TheoryAnalysisResult(
                theory_name="八字",
                calculation_data={},
                interpretation="吉",
                judgment="吉",
                judgment_level=0.8,
                confidence=0.9
            ),
            TheoryAnalysisResult(
                theory_name="小六壬",
                calculation_data={},
                interpretation="凶",
                judgment="凶",
                judgment_level=0.6,
                confidence=0.7
            )
        ]

        conflict_info = self.resolver.detect_and_resolve_conflicts(results)
        summary = self.resolver.get_conflict_summary(conflict_info)

        assert summary is not None
        assert isinstance(summary, str)
        assert len(summary) > 0

        # 应该包含冲突数量
        if conflict_info.has_conflict:
            assert "冲突" in summary

    def test_recommendations_generation(self):
        """测试建议生成"""
        results = [
            TheoryAnalysisResult(
                theory_name="八字",
                calculation_data={},
                interpretation="大吉",
                judgment="大吉",
                judgment_level=0.9,
                confidence=0.9
            ),
            TheoryAnalysisResult(
                theory_name="六爻",
                calculation_data={},
                interpretation="大凶",
                judgment="大凶",
                judgment_level=0.85,
                confidence=0.85
            )
        ]

        conflict_info = self.resolver.detect_and_resolve_conflicts(results)

        assert conflict_info.resolution is not None
        recommendations = conflict_info.resolution.get("建议", [])

        # 严重冲突应该有建议
        assert len(recommendations) > 0
        # 应该提示谨慎参考
        assert any("谨慎" in rec or "分歧" in rec for rec in recommendations)

    def test_single_theory_no_conflict(self):
        """测试单一理论无冲突"""
        results = [
            TheoryAnalysisResult(
                theory_name="八字",
                calculation_data={},
                interpretation="吉",
                judgment="吉",
                judgment_level=0.8,
                confidence=0.9
            )
        ]

        conflict_info = self.resolver.detect_and_resolve_conflicts(results)

        assert not conflict_info.has_conflict
        assert len(conflict_info.conflicts) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
