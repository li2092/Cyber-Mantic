"""
数据可视化测试
"""
import pytest
import tempfile
import os
from pathlib import Path
from utils.visualization import (
    WuxingRadarChart,
    DayunTimeline,
    TheoryFitnessChart,
    ConflictResolutionFlow,
    VisualizationManager
)


class TestWuxingRadarChart:
    """五行雷达图测试"""

    def test_create_basic(self):
        """测试基本创建"""
        wuxing_scores = {
            "木": 3,
            "火": 2,
            "土": 4,
            "金": 1,
            "水": 3
        }

        fig = WuxingRadarChart.create(wuxing_scores)
        assert fig is not None
        # 验证是极坐标图
        assert len(fig.axes) == 1
        assert fig.axes[0].name == 'polar'

    def test_save_to_file(self):
        """测试保存到文件"""
        wuxing_scores = {"木": 3, "火": 2, "土": 4, "金": 1, "水": 3}

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test_wuxing.png")
            WuxingRadarChart.save_to_file(wuxing_scores, filepath)

            assert os.path.exists(filepath)
            assert os.path.getsize(filepath) > 1000  # 至少1KB

    def test_to_bytes(self):
        """测试转换为字节流"""
        wuxing_scores = {"木": 3, "火": 2, "土": 4, "金": 1, "水": 3}

        data = WuxingRadarChart.to_bytes(wuxing_scores)
        assert isinstance(data, bytes)
        assert len(data) > 1000
        # PNG文件头
        assert data[:8] == b'\x89PNG\r\n\x1a\n'

    def test_empty_scores(self):
        """测试空分数"""
        fig = WuxingRadarChart.create({})
        assert fig is not None


class TestDayunTimeline:
    """大运时间轴测试"""

    def test_create_basic(self):
        """测试基本创建"""
        dayun_data = [
            {"start_age": 8, "end_age": 17, "gan_zhi": "甲子", "description": "好运"},
            {"start_age": 18, "end_age": 27, "gan_zhi": "乙丑", "description": "平运"},
            {"start_age": 28, "end_age": 37, "gan_zhi": "丙寅", "description": "大运"}
        ]

        fig = DayunTimeline.create(dayun_data, 2024)
        assert fig is not None
        assert len(fig.axes) == 1

    def test_save_to_file(self):
        """测试保存到文件"""
        dayun_data = [
            {"start_age": 8, "end_age": 17, "gan_zhi": "甲子"}
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test_dayun.png")
            DayunTimeline.save_to_file(dayun_data, 2024, filepath)

            assert os.path.exists(filepath)
            assert os.path.getsize(filepath) > 1000

    def test_empty_data(self):
        """测试空数据"""
        fig = DayunTimeline.create([], 2024)
        assert fig is not None


class TestTheoryFitnessChart:
    """理论适配度图表测试"""

    def test_create_basic(self):
        """测试基本创建"""
        theory_fitness = [
            {"theory": "八字", "fitness": 0.95, "priority": "基础"},
            {"theory": "紫微斗数", "fitness": 0.88, "priority": "基础"},
            {"theory": "奇门遁甲", "fitness": 0.72, "priority": "深度"}
        ]

        fig = TheoryFitnessChart.create(theory_fitness)
        assert fig is not None
        assert len(fig.axes) == 1

    def test_save_to_file(self):
        """测试保存到文件"""
        theory_fitness = [
            {"theory": "八字", "fitness": 0.95, "priority": "基础"}
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test_fitness.png")
            TheoryFitnessChart.save_to_file(theory_fitness, filepath)

            assert os.path.exists(filepath)
            assert os.path.getsize(filepath) > 1000

    def test_empty_data(self):
        """测试空数据"""
        fig = TheoryFitnessChart.create([])
        assert fig is not None


class TestConflictResolutionFlow:
    """冲突解决流程图测试"""

    def test_create_basic(self):
        """测试基本创建"""
        conflicts = [
            {"level": 1, "theories": ["八字", "紫微"], "resolution": "可接受"},
            {"level": 2, "theories": ["奇门", "六爻"], "resolution": "需调和"},
            {"level": 3, "theories": ["梅花", "小六壬"], "resolution": "严重冲突"}
        ]

        fig = ConflictResolutionFlow.create(conflicts)
        assert fig is not None
        assert len(fig.axes) == 1

    def test_save_to_file(self):
        """测试保存到文件"""
        conflicts = [
            {"level": 1, "theories": ["八字", "紫微"], "resolution": "可接受"}
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test_conflict.png")
            ConflictResolutionFlow.save_to_file(conflicts, filepath)

            assert os.path.exists(filepath)
            assert os.path.getsize(filepath) > 1000

    def test_empty_conflicts(self):
        """测试无冲突"""
        fig = ConflictResolutionFlow.create([])
        assert fig is not None


class TestVisualizationManager:
    """可视化管理器测试"""

    def test_generate_all_charts(self):
        """测试生成所有图表"""
        analysis_result = {
            "wuxing_analysis": {
                "scores": {"木": 3, "火": 2, "土": 4, "金": 1, "水": 3}
            },
            "dayun_data": [
                {"start_age": 8, "end_age": 17, "gan_zhi": "甲子"}
            ],
            "selected_theories": ["八字", "紫微"],
            "theory_fitness": [
                {"theory": "八字", "fitness": 0.95, "priority": "基础"},
                {"theory": "紫微斗数", "fitness": 0.88, "priority": "基础"}
            ],
            "conflicts": [
                {"level": 1, "theories": ["八字", "紫微"], "resolution": "可接受"}
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            chart_paths = VisualizationManager.generate_all_charts(
                analysis_result,
                tmpdir
            )

            # 验证所有图表都生成了
            assert "wuxing_radar" in chart_paths
            assert "dayun_timeline" in chart_paths
            assert "theory_fitness" in chart_paths
            assert "conflict_resolution" in chart_paths

            # 验证文件存在
            for path in chart_paths.values():
                assert os.path.exists(path)
                assert os.path.getsize(path) > 1000

    def test_partial_data(self):
        """测试部分数据"""
        analysis_result = {
            "wuxing_analysis": {
                "scores": {"木": 3, "火": 2, "土": 4, "金": 1, "水": 3}
            }
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            chart_paths = VisualizationManager.generate_all_charts(
                analysis_result,
                tmpdir
            )

            # 只应该生成五行雷达图
            assert "wuxing_radar" in chart_paths
            assert "dayun_timeline" not in chart_paths
            assert "theory_fitness" not in chart_paths
            assert "conflict_resolution" not in chart_paths

    def test_empty_data(self):
        """测试空数据"""
        with tempfile.TemporaryDirectory() as tmpdir:
            chart_paths = VisualizationManager.generate_all_charts({}, tmpdir)

            # 应该返回空字典
            assert isinstance(chart_paths, dict)
            assert len(chart_paths) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
