"""
ConversationService测试
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from services.conversation_service import (
    ConversationService, ConversationStage, ConversationContext
)
from api.manager import APIManager


class TestConversationContext:
    """ConversationContext测试"""

    def test_init(self):
        """测试初始化"""
        context = ConversationContext()

        assert context.stage == ConversationStage.INIT
        assert context.question_category is None
        assert context.question_description == ""
        assert context.random_numbers == []
        assert context.conversation_history == []

    def test_to_dict(self):
        """测试转换为字典"""
        context = ConversationContext()
        context.question_category = "事业"
        context.question_description = "想知道今年是否适合跳槽"
        context.random_numbers = [7, 3, 5]

        data = context.to_dict()

        assert data["question_category"] == "事业"
        assert data["question_description"] == "想知道今年是否适合跳槽"
        assert data["random_numbers"] == [7, 3, 5]
        assert "stage" in data


class TestConversationService:
    """ConversationService测试"""

    def setup_method(self):
        """设置测试"""
        # Mock APIManager
        self.mock_api_manager = Mock(spec=APIManager)
        self.mock_api_manager.call_api = AsyncMock()

        self.service = ConversationService(self.mock_api_manager)

    def test_init(self):
        """测试初始化"""
        assert self.service.api_manager == self.mock_api_manager
        assert isinstance(self.service.context, ConversationContext)

    def test_reset(self):
        """测试重置"""
        # 修改上下文
        self.service.context.question_category = "事业"
        self.service.context.stage = ConversationStage.STAGE2_BASIC_INFO

        # 重置
        self.service.reset()

        # 验证重置
        assert self.service.context.stage == ConversationStage.INIT
        assert self.service.context.question_category is None

    # ==================== 问题类型识别测试 ====================

    def test_identify_question_type_bazi_details(self):
        """测试识别八字详情类问题"""
        questions = [
            "我的八字是什么？",
            "能解释一下我的四柱吗？",
            "日主是什么意思？",
            "我的用神是什么？"
        ]

        for q in questions:
            qtype = self.service._identify_question_type(q)
            assert qtype == "bazi_details", f"问题 '{q}' 应该识别为 bazi_details"

    def test_identify_question_type_advice(self):
        """测试识别建议类问题"""
        questions = [
            ("有什么建议？", "advice"),
            ("该怎么做？", "advice"),
            ("如何改善财运？", "advice"),
            ("我应该跳槽吗？", "career_choice"),  # 更specific的分类
        ]

        for q, expected_type in questions:
            qtype = self.service._identify_question_type(q)
            assert qtype == expected_type, f"问题 '{q}' 应该识别为 {expected_type}"

    def test_identify_question_type_prediction(self):
        """测试识别预测类问题"""
        questions = [
            ("未来会不会成功？", "prediction"),
            ("明年财运怎样？", "prediction"),
            ("什么时候能升职？", "career_choice"),  # 更specific的分类（升职属于career_choice）
            ("近期会有桃花吗？", "relationship_advice"),  # 更specific的分类（桃花属于relationship_advice）
        ]

        for q, expected_type in questions:
            qtype = self.service._identify_question_type(q)
            assert qtype == expected_type, f"问题 '{q}' 应该识别为 {expected_type}"

    def test_identify_question_type_theory_explanation(self):
        """测试识别理论解释类问题"""
        questions = [
            "什么是奇门遁甲？",
            "为什么用这个理论？",
            "解释一下六壬",
            "这个原理是什么？"
        ]

        for q in questions:
            qtype = self.service._identify_question_type(q)
            assert qtype == "theory_explanation", f"问题 '{q}' 应该识别为 theory_explanation"

    def test_identify_question_type_general(self):
        """测试识别通用类问题"""
        questions = [
            "这是什么意思？",
            "能详细说说吗？",
            "我不太明白"
        ]

        for q in questions:
            qtype = self.service._identify_question_type(q)
            assert qtype == "general", f"问题 '{q}' 应该识别为 general"

    # ==================== 上下文准备测试 ====================

    def test_prepare_qa_context_bazi_details(self):
        """测试为八字详情类问题准备上下文"""
        # 设置八字结果
        self.service.context.bazi_result = {
            "四柱": {"年柱": {"天干": "甲", "地支": "子"}},
            "五行分析": {"金": 1, "木": 2, "水": 3, "火": 1, "土": 1},
            "十神": {"正官": 1, "偏财": 2},
            "大运": [{"起运年龄": 5, "干支": "乙丑"}],
            "流年分析": {"2024": "财运旺"}
        }

        context = self.service._prepare_qa_context("bazi_details")

        assert "bazi" in context
        assert "四柱" in context["bazi"]
        assert "五行" in context["bazi"]
        assert "十神" in context["bazi"]

    def test_prepare_qa_context_advice(self):
        """测试为建议类问题准备上下文"""
        # 设置建议数据
        self.service.context.actionable_advice = [
            {"category": "事业", "advice": "把握机会"}
        ]
        self.service.context.comprehensive_analysis = "综合分析内容"

        context = self.service._prepare_qa_context("advice")

        assert "actionable_advice" in context
        assert "comprehensive_analysis" in context
        assert context["actionable_advice"] == [{"category": "事业", "advice": "把握机会"}]

    def test_prepare_qa_context_prediction(self):
        """测试为预测类问题准备上下文"""
        # 设置预测数据
        self.service.context.predictive_analysis = "未来财运旺盛"
        self.service.context.retrospective_analysis = "过去三年稳定"

        context = self.service._prepare_qa_context("prediction")

        assert "predictive_analysis" in context
        assert "retrospective_analysis" in context
        assert context["predictive_analysis"] == "未来财运旺盛"

    def test_prepare_qa_context_theory_explanation(self):
        """测试为理论解释类问题准备上下文"""
        self.service.context.selected_theories = ["八字", "奇门"]
        self.service.context.bazi_result = {"四柱": {}}
        self.service.context.qimen_result = {"局": "休门"}

        context = self.service._prepare_qa_context("theory_explanation")

        assert "selected_theories" in context
        assert "theory_results_summary" in context
        assert context["selected_theories"] == ["八字", "奇门"]
        assert context["theory_results_summary"]["八字"] == "已分析"
        assert context["theory_results_summary"]["奇门"] == "已分析"

    # ==================== 对话管理工具测试 ====================

    def test_get_progress_percentage_init(self):
        """测试初始阶段进度"""
        self.service.context.stage = ConversationStage.INIT
        progress = self.service.get_progress_percentage()
        assert progress == 0

    def test_get_progress_percentage_stage1(self):
        """测试阶段1进度"""
        self.service.context.stage = ConversationStage.STAGE1_ICEBREAK
        progress = self.service.get_progress_percentage()
        assert progress == 20

    def test_get_progress_percentage_stage2(self):
        """测试阶段2进度"""
        self.service.context.stage = ConversationStage.STAGE2_BASIC_INFO
        progress = self.service.get_progress_percentage()
        assert progress == 40

    def test_get_progress_percentage_completed(self):
        """测试完成阶段进度"""
        self.service.context.stage = ConversationStage.COMPLETED
        progress = self.service.get_progress_percentage()
        assert progress == 100

    def test_get_stage_description(self):
        """测试阶段描述"""
        self.service.context.stage = ConversationStage.STAGE1_ICEBREAK
        desc = self.service.get_stage_description()
        assert "破冰" in desc or "阶段1" in desc

        self.service.context.stage = ConversationStage.STAGE2_BASIC_INFO
        desc = self.service.get_stage_description()
        assert "信息" in desc or "阶段2" in desc

    def test_get_conversation_summary(self):
        """测试对话摘要"""
        # 设置上下文
        self.service.context.stage = ConversationStage.STAGE2_BASIC_INFO
        self.service.context.question_category = "事业"
        self.service.context.question_description = "想知道今年是否适合跳槽"
        self.service.context.birth_info = {"year": 1990}
        self.service.context.gender = "male"
        self.service.context.time_certainty = "certain"
        self.service.context.selected_theories = ["八字", "奇门"]
        self.service.context.bazi_result = {"四柱": {}}

        summary = self.service.get_conversation_summary()

        assert summary["stage"] == ConversationStage.STAGE2_BASIC_INFO.value
        assert summary["question"]["category"] == "事业"
        assert summary["user_info"]["birth_year"] == 1990
        assert summary["user_info"]["gender"] == "male"
        assert summary["user_info"]["time_certainty"] == "certain"
        assert summary["analysis_status"]["theories_used"] == ["八字", "奇门"]
        assert summary["analysis_status"]["bazi_analyzed"] is True

    def test_get_conversation_statistics(self):
        """测试对话统计"""
        # 设置对话历史
        self.service.context.conversation_history = [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "您好"},
            {"role": "user", "content": "我想咨询事业"}
        ]
        self.service.context.stage = ConversationStage.STAGE3_SUPPLEMENT
        self.service.context.selected_theories = ["八字", "奇门", "六壬"]
        self.service.context.bazi_result = {"四柱": {}}
        self.service.context.qimen_result = {"局": {}}

        stats = self.service.get_conversation_statistics()

        assert stats["total_messages"] == 3
        assert stats["user_messages"] == 2
        assert stats["assistant_messages"] == 1
        assert stats["stages_completed"] == 3  # STAGE3 = 3
        assert stats["theories_count"] == 3
        assert stats["has_bazi"] is True

    def test_can_skip_to_stage_stage2(self):
        """测试是否可以跳转到阶段2"""
        # 没有问题类别，不能跳转
        result = self.service.can_skip_to_stage(ConversationStage.STAGE2_BASIC_INFO)
        assert result is False

        # 有问题类别，可以跳转
        self.service.context.question_category = "事业"
        result = self.service.can_skip_to_stage(ConversationStage.STAGE2_BASIC_INFO)
        assert result is True

    def test_can_skip_to_stage_stage3(self):
        """测试是否可以跳转到阶段3"""
        # 没有出生信息，不能跳转
        result = self.service.can_skip_to_stage(ConversationStage.STAGE3_SUPPLEMENT)
        assert result is False

        # 有出生信息，可以跳转
        self.service.context.birth_info = {"year": 1990, "month": 1, "day": 1}
        result = self.service.can_skip_to_stage(ConversationStage.STAGE3_SUPPLEMENT)
        assert result is True

    def test_can_skip_to_stage_qa(self):
        """测试是否可以跳转到问答阶段"""
        # 没有综合分析，不能跳转
        result = self.service.can_skip_to_stage(ConversationStage.QA)
        assert result is False

        # 有综合分析，可以跳转
        self.service.context.comprehensive_analysis = "综合分析内容"
        result = self.service.can_skip_to_stage(ConversationStage.QA)
        assert result is True

    def test_save_conversation(self):
        """测试保存对话"""
        self.service.context.question_category = "事业"
        self.service.context.conversation_history = [
            {"role": "user", "content": "你好"}
        ]

        saved_data = self.service.save_conversation()

        assert "timestamp" in saved_data
        assert "session_id" in saved_data
        assert "context" in saved_data
        assert "full_conversation" in saved_data
        assert "summary" in saved_data
        assert "statistics" in saved_data

        # 验证摘要和统计信息存在
        assert saved_data["summary"]["question"]["category"] == "事业"
        assert saved_data["statistics"]["total_messages"] == 1

    def test_export_to_markdown(self):
        """测试导出为Markdown"""
        self.service.context.stage = ConversationStage.QA
        self.service.context.question_category = "事业"
        self.service.context.conversation_history = [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "您好"}
        ]
        self.service.context.comprehensive_analysis = "综合分析内容"

        md_content = self.service.export_to_markdown()

        # 验证Markdown内容
        assert "# 赛博玄数 - 对话记录" in md_content
        assert "导出时间" in md_content
        assert "对话阶段" in md_content
        assert "## 💬 对话历史" in md_content
        assert "你好" in md_content
        assert "您好" in md_content
        assert "## 📊 综合分析报告" in md_content

    # ==================== 生成降级响应测试 ====================

    def test_generate_fallback_qa_response_bazi_details(self):
        """测试八字详情类问题的降级响应"""
        response = self.service._generate_fallback_qa_response("bazi_details")

        assert "八字" in response or "命盘" in response

    def test_generate_fallback_qa_response_advice(self):
        """测试建议类问题的降级响应"""
        response = self.service._generate_fallback_qa_response("advice")

        assert "建议" in response or "行动" in response

    def test_generate_fallback_qa_response_prediction(self):
        """测试预测类问题的降级响应"""
        response = self.service._generate_fallback_qa_response("prediction")

        assert "预测" in response or "未来" in response

    def test_generate_fallback_qa_response_general(self):
        """测试通用问题的降级响应"""
        response = self.service._generate_fallback_qa_response("general")

        assert "抱歉" in response or "暂时" in response


class TestConversationServiceIntegration:
    """ConversationService集成测试"""

    @pytest.mark.asyncio
    async def test_start_conversation(self):
        """测试开始对话"""
        mock_api_manager = Mock(spec=APIManager)
        service = ConversationService(mock_api_manager)

        welcome = await service.start_conversation()

        # 验证欢迎消息
        assert "赛博玄数" in welcome
        assert "阶段1" in welcome or "破冰" in welcome
        assert service.context.stage == ConversationStage.STAGE1_ICEBREAK
        assert len(service.context.conversation_history) == 1
        assert service.context.conversation_history[0]["role"] == "assistant"

    def test_count_completed_stages(self):
        """测试阶段完成数计算"""
        service = ConversationService(Mock(spec=APIManager))

        # 测试不同阶段
        stages_and_counts = [
            (ConversationStage.INIT, 0),
            (ConversationStage.STAGE1_ICEBREAK, 1),
            (ConversationStage.STAGE2_BASIC_INFO, 2),
            (ConversationStage.STAGE3_SUPPLEMENT, 3),
            (ConversationStage.STAGE4_VERIFICATION, 4),
            (ConversationStage.STAGE5_FINAL_REPORT, 5),
            (ConversationStage.QA, 5),
            (ConversationStage.COMPLETED, 5)
        ]

        for stage, expected_count in stages_and_counts:
            service.context.stage = stage
            count = service._count_completed_stages()
            assert count == expected_count, f"阶段 {stage.value} 应该返回 {expected_count}"
