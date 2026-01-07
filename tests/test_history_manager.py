"""
历史记录管理器单元测试
"""
import tempfile
import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock
from utils.history_manager import HistoryManager
from models import ComprehensiveReport, TheoryAnalysisResult, ConflictInfo


class TestHistoryManager:
    """历史记录管理器测试类"""

    @pytest.fixture
    def temp_db(self):
        """创建临时数据库"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        yield db_path
        # 清理
        Path(db_path).unlink(missing_ok=True)

    @pytest.fixture
    def manager(self, temp_db):
        """创建历史管理器实例"""
        return HistoryManager(db_path=temp_db)

    @pytest.fixture
    def sample_report(self):
        """创建示例报告"""
        # 创建理论结果
        theory_result = TheoryAnalysisResult(
            theory_name="八字",
            calculation_data={"四柱": "甲子年..."},
            interpretation="八字分析...",
            judgment="吉",
            judgment_level=0.7,
            confidence=0.85
        )

        # 创建冲突信息
        conflict_info = ConflictInfo(
            has_conflict=False,
            conflicts=[],
            resolution="无冲突"
        )

        # 创建完整报告
        report = ComprehensiveReport(
            report_id="test_report_001",
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            user_input_summary={
                "question_type": "事业",
                "question_description": "今年事业运势如何",
                "birth_info": "1990-01-01 12:00"
            },
            selected_theories=["八字", "紫微斗数"],
            selection_reason="根据问题类型选择",
            theory_results=[theory_result],
            conflict_info=conflict_info,
            executive_summary="综合分析显示...",
            detailed_analysis="详细问题解答：根据八字和紫微斗数分析...",
            retrospective_analysis="过去分析...",
            predictive_analysis="未来预测...",
            comprehensive_advice=[
                {"priority": "高", "content": "仔细阅读各理论的详细分析，理解核心要点"},
                {"priority": "中", "content": "结合自身实际情况，制定具体行动计划"}
            ],
            overall_confidence=0.8,
            limitations=["时辰不确定可能影响准确性", "仅供参考，不能替代专业咨询"]
        )

        return report

    def test_initialization(self, temp_db):
        """测试初始化"""
        manager = HistoryManager(db_path=temp_db)

        assert manager.db_path == Path(temp_db)
        assert manager.db_path.exists()

    def test_database_tables_created(self, manager, temp_db):
        """测试数据库表创建"""
        import sqlite3

        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()

            # 检查表是否存在
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='analysis_history'
            """)
            assert cursor.fetchone() is not None

            # 检查索引是否存在
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='index' AND name='idx_created_at'
            """)
            assert cursor.fetchone() is not None

    def test_save_report_success(self, manager, sample_report):
        """测试保存报告成功"""
        result = manager.save_report(sample_report)

        assert result is True

        # 验证数据已保存
        history = manager.get_recent_history(limit=10)
        assert len(history) == 1
        assert history[0]['report_id'] == "test_report_001"
        assert history[0]['question_type'] == "事业"

    def test_save_report_replace_existing(self, manager, sample_report):
        """测试替换已存在的报告"""
        # 第一次保存
        manager.save_report(sample_report)

        # 修改报告内容
        sample_report.executive_summary = "更新后的摘要"

        # 再次保存（应该替换）
        result = manager.save_report(sample_report)
        assert result is True

        # 验证只有一条记录
        history = manager.get_recent_history(limit=10)
        assert len(history) == 1
        assert history[0]['executive_summary'] == "更新后的摘要"

    def test_get_recent_history(self, manager, sample_report):
        """测试获取最近历史记录"""
        # 保存3个报告
        for i in range(3):
            report = sample_report
            report.report_id = f"report_{i}"
            report.created_at = datetime(2024, 1, i+1, 12, 0, 0)
            manager.save_report(report)

        # 获取最近2条
        history = manager.get_recent_history(limit=2)

        assert len(history) == 2
        # 应该按时间倒序
        assert history[0]['report_id'] == "report_2"
        assert history[1]['report_id'] == "report_1"

    def test_get_recent_history_empty(self, manager):
        """测试空历史记录"""
        history = manager.get_recent_history(limit=10)

        assert history == []

    def test_get_report_by_id_exists(self, manager, sample_report):
        """测试根据ID获取报告（存在）"""
        manager.save_report(sample_report)

        retrieved = manager.get_report_by_id("test_report_001")

        assert retrieved is not None
        assert retrieved.report_id == "test_report_001"
        assert retrieved.executive_summary == sample_report.executive_summary
        assert len(retrieved.theory_results) == 1
        assert retrieved.theory_results[0].theory_name == "八字"

    def test_get_report_by_id_not_exists(self, manager):
        """测试根据ID获取报告（不存在）"""
        retrieved = manager.get_report_by_id("nonexistent_id")

        assert retrieved is None

    def test_search_by_question_type(self, manager, sample_report):
        """测试按问题类型搜索"""
        # 保存不同类型的报告
        sample_report.user_input_summary['question_type'] = "事业"
        sample_report.report_id = "report_1"
        manager.save_report(sample_report)

        sample_report.user_input_summary['question_type'] = "财运"
        sample_report.report_id = "report_2"
        manager.save_report(sample_report)

        sample_report.user_input_summary['question_type'] = "事业"
        sample_report.report_id = "report_3"
        manager.save_report(sample_report)

        # 搜索事业类型
        results = manager.search_by_question_type("事业")

        assert len(results) == 2
        assert all(r['question_type'] == "事业" for r in results)

    def test_search_by_question_type_no_results(self, manager):
        """测试搜索不存在的问题类型"""
        results = manager.search_by_question_type("健康")

        assert results == []

    def test_search_by_keyword(self, manager, sample_report):
        """测试按关键词搜索"""
        # 保存不同问题描述的报告
        sample_report.user_input_summary['question_description'] = "今年事业发展如何"
        sample_report.report_id = "report_1"
        manager.save_report(sample_report)

        sample_report.user_input_summary['question_description'] = "财运分析"
        sample_report.report_id = "report_2"
        manager.save_report(sample_report)

        sample_report.user_input_summary['question_description'] = "事业转行建议"
        sample_report.report_id = "report_3"
        manager.save_report(sample_report)

        # 搜索包含"事业"的记录
        results = manager.search_by_keyword("事业")

        assert len(results) == 2
        assert all("事业" in r['question_desc'] for r in results)

    def test_search_by_keyword_case_sensitive(self, manager, sample_report):
        """测试关键词搜索（大小写敏感）"""
        sample_report.user_input_summary['question_description'] = "Career Development"
        manager.save_report(sample_report)

        # SQLite默认不区分大小写
        results = manager.search_by_keyword("career")
        assert len(results) == 1

    def test_delete_report_success(self, manager, sample_report):
        """测试删除报告成功"""
        manager.save_report(sample_report)

        result = manager.delete_report("test_report_001")

        assert result is True

        # 验证已删除
        retrieved = manager.get_report_by_id("test_report_001")
        assert retrieved is None

    def test_delete_report_not_exists(self, manager):
        """测试删除不存在的报告"""
        result = manager.delete_report("nonexistent_id")

        assert result is False

    def test_get_statistics_empty(self, manager):
        """测试空数据库统计"""
        stats = manager.get_statistics()

        assert stats['total_count'] == 0
        assert stats['type_statistics'] == {}
        assert stats['last_analysis_time'] is None

    def test_get_statistics_with_data(self, manager, sample_report):
        """测试有数据的统计"""
        # 保存多个报告
        for i in range(5):
            report = sample_report
            report.report_id = f"report_{i}"
            report.user_input_summary['question_type'] = "事业" if i < 3 else "财运"
            report.created_at = datetime(2024, 1, i+1, 12, 0, 0)
            manager.save_report(report)

        stats = manager.get_statistics()

        assert stats['total_count'] == 5
        assert stats['type_statistics']['事业'] == 3
        assert stats['type_statistics']['财运'] == 2
        assert stats['last_analysis_time'] is not None

    def test_get_statistics_type_sorting(self, manager, sample_report):
        """测试统计信息按数量排序"""
        # 事业3个，财运2个，健康1个
        for i in range(6):
            report = sample_report
            report.report_id = f"report_{i}"
            if i < 3:
                report.user_input_summary['question_type'] = "事业"
            elif i < 5:
                report.user_input_summary['question_type'] = "财运"
            else:
                report.user_input_summary['question_type'] = "健康"
            manager.save_report(report)

        stats = manager.get_statistics()

        # 获取类型统计的键列表（应该按数量降序）
        types = list(stats['type_statistics'].keys())
        assert types[0] == "事业"
        assert types[1] == "财运"
        assert types[2] == "健康"

    def test_concurrent_saves(self, manager, sample_report):
        """测试并发保存"""
        # 快速保存多个报告
        for i in range(10):
            report = sample_report
            report.report_id = f"concurrent_report_{i}"
            result = manager.save_report(report)
            assert result is True

        # 验证所有报告都已保存
        history = manager.get_recent_history(limit=100)
        assert len(history) == 10

    def test_report_serialization_round_trip(self, manager, sample_report):
        """测试报告序列化和反序列化"""
        # 保存报告
        manager.save_report(sample_report)

        # 检索报告
        retrieved = manager.get_report_by_id(sample_report.report_id)

        # 验证所有字段
        assert retrieved.report_id == sample_report.report_id
        assert retrieved.created_at == sample_report.created_at
        assert retrieved.executive_summary == sample_report.executive_summary
        assert retrieved.overall_confidence == sample_report.overall_confidence
        assert len(retrieved.selected_theories) == len(sample_report.selected_theories)
        assert retrieved.conflict_info.has_conflict == sample_report.conflict_info.has_conflict

    def test_history_limit(self, manager, sample_report):
        """测试历史记录数量限制"""
        # 保存20个报告
        for i in range(20):
            report = sample_report
            report.report_id = f"report_{i}"
            manager.save_report(report)

        # 限制返回5个
        history = manager.get_recent_history(limit=5)
        assert len(history) == 5

    def test_search_limit(self, manager, sample_report):
        """测试搜索结果数量限制"""
        # 保存20个相同类型的报告
        for i in range(20):
            report = sample_report
            report.report_id = f"report_{i}"
            report.user_input_summary['question_type'] = "事业"
            manager.save_report(report)

        # 限制返回10个
        results = manager.search_by_question_type("事业", limit=10)
        assert len(results) == 10
