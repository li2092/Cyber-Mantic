"""
数据模型序列化测试

验证所有数据模型的to_dict()和from_dict()方法正确工作
"""

import pytest
from datetime import datetime
from models import (
    UserInput, TheoryAnalysisResult, ComprehensiveReport,
    ConflictInfo
)
from ui.widgets.chat_widget import ChatMessage, MessageRole


class TestUserInputSerialization:
    """测试UserInput序列化"""

    def test_user_input_to_dict(self):
        """测试UserInput转dict"""
        user_input = UserInput(
            question_type="事业",
            question_description="未来发展如何",
            birth_year=1990,
            birth_month=5,
            birth_day=15,
            birth_hour=14,
            gender="male",
            calendar_type="solar",
            birth_place_lng=116.4074,  # 北京经度
            mbti_type="INTJ"
        )

        data = user_input.to_dict()

        # 验证关键字段
        assert data['question_type'] == "事业"
        assert data['question_description'] == "未来发展如何"
        assert data['birth_year'] == 1990
        assert data['birth_month'] == 5
        assert data['birth_day'] == 15
        assert data['birth_hour'] == 14
        assert data['gender'] == "male"
        assert data['calendar_type'] == "solar"
        assert data['birth_place_lng'] == 116.4074
        assert data['mbti_type'] == "INTJ"

    def test_user_input_from_dict(self):
        """测试从dict恢复UserInput"""
        data = {
            'question_type': "财运",
            'question_description': "投资运势",
            'birth_year': 1985,
            'birth_month': 3,
            'birth_day': 20,
            'birth_hour': 8,
            'gender': "female",
            'calendar_type': "lunar",
            'birth_place_lng': 121.4737,  # 上海经度
            'mbti_type': "ENFP"
        }

        user_input = UserInput.from_dict(data)

        assert user_input.question_type == "财运"
        assert user_input.question_description == "投资运势"
        assert user_input.birth_year == 1985
        assert user_input.birth_month == 3
        assert user_input.birth_day == 20
        assert user_input.birth_hour == 8
        assert user_input.gender == "female"
        assert user_input.calendar_type == "lunar"
        assert user_input.birth_place_lng == 121.4737
        assert user_input.mbti_type == "ENFP"

    def test_user_input_round_trip(self):
        """测试UserInput往返序列化"""
        original = UserInput(
            question_type="感情",
            question_description="桃花运",
            birth_year=1992,
            birth_month=12,
            birth_day=25,
            birth_hour=18,
            gender="女",
            calendar_type="公历"
        )

        # to_dict -> from_dict
        data = original.to_dict()
        restored = UserInput.from_dict(data)

        # 验证所有字段一致
        assert restored.question_type == original.question_type
        assert restored.question_description == original.question_description
        assert restored.birth_year == original.birth_year
        assert restored.birth_month == original.birth_month
        assert restored.birth_day == original.birth_day
        assert restored.birth_hour == original.birth_hour
        assert restored.gender == original.gender
        assert restored.calendar_type == original.calendar_type

    def test_user_input_with_additional_persons(self):
        """测试包含additional_persons的序列化"""
        from models import PersonBirthInfo

        user_input = UserInput(
            question_type="合婚",
            question_description="婚姻配对",
            birth_year=1990,
            birth_month=1,
            birth_day=1,
            birth_hour=12,
            gender="male",
            calendar_type="solar",
            additional_persons=[
                PersonBirthInfo(
                    label="配偶",
                    birth_year=1991,
                    birth_month=2,
                    birth_day=2,
                    birth_hour=14,
                    gender="female",
                    calendar_type="solar"
                )
            ]
        )

        data = user_input.to_dict()
        restored = UserInput.from_dict(data)

        assert len(restored.additional_persons) == 1
        assert restored.additional_persons[0].label == "配偶"
        assert restored.additional_persons[0].birth_year == 1991


class TestTheoryAnalysisResultSerialization:
    """测试TheoryAnalysisResult序列化"""

    def test_theory_result_to_dict(self):
        """测试TheoryAnalysisResult转dict"""
        result = TheoryAnalysisResult(
            theory_name="八字",
            calculation_data={
                "四柱": ["庚午", "辛巳", "壬申", "癸酉"],
                "五行": {"金": 4, "木": 0, "水": 2, "火": 2, "土": 0}
            },
            interpretation="日主壬水生于巳月...",
            judgment="吉",
            judgment_level=0.75,
            confidence=0.85,
            advice="建议加强木元素..."
        )

        data = result.to_dict()

        assert data['theory_name'] == "八字"
        assert data['judgment'] == "吉"
        assert data['judgment_level'] == 0.75
        assert data['confidence'] == 0.85
        assert "四柱" in data['calculation_data']

    def test_theory_result_round_trip(self):
        """测试TheoryAnalysisResult往返序列化（通过dataclass）"""
        result = TheoryAnalysisResult(
            theory_name="奇门遁甲",
            calculation_data={
                "时家奇门": "阳遁一局",
                "用神": "值符"
            },
            interpretation="当前局势...",
            judgment="凶",
            judgment_level=0.3,
            confidence=0.7,
            advice="谨慎行事"
        )

        # 测试to_dict
        data = result.to_dict()
        assert data['theory_name'] == "奇门遁甲"
        assert data['judgment'] == "凶"
        assert data['judgment_level'] == 0.3
        assert data['confidence'] == 0.7


class TestConflictInfoSerialization:
    """测试ConflictInfo序列化"""

    def test_conflict_info_to_dict(self):
        """测试ConflictInfo转dict"""
        conflict = ConflictInfo(
            has_conflict=True,
            conflicts=[
                {
                    "level": 3,
                    "theories": ["八字", "紫微斗数"],
                    "description": "判断不一致"
                }
            ],
            resolution={
                "strategy": "加权调和",
                "result": "平"
            }
        )

        data = conflict.to_dict()

        assert data['has_conflict'] is True
        assert len(data['conflicts']) == 1
        assert data['conflicts'][0]['level'] == 3
        assert "resolution" in data

    def test_conflict_info_to_dict_no_conflict(self):
        """测试ConflictInfo无冲突时的序列化"""
        conflict_info = ConflictInfo(
            has_conflict=False,
            conflicts=[],
            resolution=None
        )

        data = conflict_info.to_dict()

        assert data['has_conflict'] is False
        assert len(data['conflicts']) == 0
        assert data['resolution'] is None


class TestComprehensiveReportSerialization:
    """测试ComprehensiveReport序列化"""

    def test_comprehensive_report_to_dict(self):
        """测试ComprehensiveReport转dict"""
        report = ComprehensiveReport(
            report_id="test-001",
            created_at=datetime(2026, 1, 4, 12, 0, 0),
            user_input_summary={
                "question_type": "事业",
                "birth_info": "1990-05-15 14:00"
            },
            selected_theories=["八字", "奇门遁甲"],
            selection_reason="根据问题类型和出生信息完整度选择",
            theory_results=[
                TheoryAnalysisResult(
                    theory_name="八字",
                    calculation_data={},
                    interpretation="测试",
                    judgment="吉",
                    judgment_level=0.7,
                    confidence=0.8,
                    advice="建议"
                )
            ],
            conflict_info=ConflictInfo(
                has_conflict=False,
                conflicts=[],
                resolution=None
            ),
            executive_summary="综合摘要",
            detailed_analysis="详细分析",
            retrospective_analysis="回溯分析内容",
            predictive_analysis="预测分析内容",
            comprehensive_advice=[
                {"category": "事业", "content": "建议内容"}
            ],
            overall_confidence=0.8,
            limitations=["信息不完整可能影响准确性"]
        )

        data = report.to_dict()

        # 验证关键字段
        assert data['report_id'] == "test-001"
        assert data['created_at'] == "2026-01-04T12:00:00"
        assert len(data['selected_theories']) == 2
        assert len(data['theory_results']) == 1
        assert data['overall_confidence'] == 0.8
        assert data['selection_reason'] == "根据问题类型和出生信息完整度选择"
        assert data['retrospective_analysis'] == "回溯分析内容"

    def test_comprehensive_report_serialization_complete(self):
        """测试ComprehensiveReport完整序列化"""
        report = ComprehensiveReport(
            report_id="round-trip-test",
            created_at=datetime.now(),
            user_input_summary={"type": "test"},
            selected_theories=["八字", "紫微斗数"],
            selection_reason="测试选择原因",
            theory_results=[],
            conflict_info=ConflictInfo(False, [], None),
            executive_summary="测试摘要",
            detailed_analysis="测试分析",
            retrospective_analysis="测试回溯",
            predictive_analysis="测试预测",
            comprehensive_advice=[],
            overall_confidence=0.8,
            limitations=["测试限制"]
        )

        # 测试序列化
        data = report.to_dict()

        # 验证关键字段
        assert data['report_id'] == "round-trip-test"
        assert len(data['selected_theories']) == 2
        assert data['overall_confidence'] == 0.8
        assert data['executive_summary'] == "测试摘要"
        assert data['selection_reason'] == "测试选择原因"
        assert data['retrospective_analysis'] == "测试回溯"
        assert data['predictive_analysis'] == "测试预测"
        assert len(data['limitations']) == 1


class TestChatMessageSerialization:
    """测试ChatMessage序列化"""

    def test_chat_message_to_dict(self):
        """测试ChatMessage转dict"""
        message = ChatMessage(
            role=MessageRole.USER,
            content="用户提问内容",
            timestamp=datetime(2026, 1, 4, 14, 0, 0)
        )

        data = message.to_dict()

        assert data['role'] == "user"
        assert data['content'] == "用户提问内容"
        assert data['timestamp'] == "2026-01-04T14:00:00"

    def test_chat_message_assistant(self):
        """测试助手消息序列化"""
        message = ChatMessage(
            role=MessageRole.ASSISTANT,
            content="AI回复内容",
            timestamp=datetime(2026, 1, 4, 14, 1, 0)
        )

        data = message.to_dict()

        assert data['role'] == "assistant"
        assert data['content'] == "AI回复内容"
        assert data['timestamp'] == "2026-01-04T14:01:00"


class TestEdgeCasesSerialization:
    """测试边界情况的序列化"""

    def test_none_values_serialization(self):
        """测试None值的序列化"""
        user_input = UserInput(
            question_type="测试",
            question_description="测试描述",
            birth_year=1990,
            birth_month=1,
            birth_day=1,
            birth_hour=None,  # None值
            gender="male",
            calendar_type="solar",
            birth_place_lng=None,  # None值
            mbti_type=None  # None值
        )

        data = user_input.to_dict()
        restored = UserInput.from_dict(data)

        # None值应该被保留或不出现在dict中
        assert restored.birth_hour is None
        assert restored.birth_place_lng is None
        assert restored.mbti_type is None

    def test_empty_lists_serialization(self):
        """测试空列表的序列化"""
        report = ComprehensiveReport(
            report_id="empty-test",
            created_at=datetime.now(),
            user_input_summary={},
            selected_theories=[],  # 空列表
            selection_reason="测试",
            theory_results=[],  # 空列表
            conflict_info=ConflictInfo(False, [], None),
            executive_summary="",
            detailed_analysis="",
            retrospective_analysis="",
            predictive_analysis="",
            comprehensive_advice=[],  # 空列表
            overall_confidence=0.0,
            limitations=[]
        )

        data = report.to_dict()

        assert len(data['selected_theories']) == 0
        assert len(data['theory_results']) == 0
        assert len(data['comprehensive_advice']) == 0
        assert len(data['limitations']) == 0

    def test_unicode_content_serialization(self):
        """测试Unicode内容的序列化"""
        user_input = UserInput(
            question_type="测试",
            question_description="包含特殊字符：🔮✨💫🌟",
            birth_year=1990,
            birth_month=1,
            birth_day=1,
            birth_hour=12,
            gender="male",
            calendar_type="solar"
        )

        data = user_input.to_dict()
        restored = UserInput.from_dict(data)

        # Unicode字符应该被正确保留
        assert "🔮" in restored.question_description
        assert restored.question_description == user_input.question_description


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
