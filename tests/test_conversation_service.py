"""
ConversationService测试

注意：部分QA相关方法已迁移至qa_handler.py，这里只测试ConversationService核心功能
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
        """测试对话统计（V2重构版本）"""
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

        # V2版本的统计字段
        assert stats["total_messages"] == 3
        assert stats["user_messages"] == 2
        assert stats["assistant_messages"] == 1
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


class TestQAHandler:
    """QAHandler测试 - 问题类型识别和上下文准备"""

    def setup_method(self):
        """设置测试"""
        self.mock_api_manager = Mock(spec=APIManager)
        self.mock_api_manager.call_api = AsyncMock()
        self.service = ConversationService(self.mock_api_manager)

    def test_qa_handler_initialization(self):
        """测试QAHandler初始化"""
        assert hasattr(self.service, 'qa_handler')
        assert self.service.qa_handler is not None

    def test_identify_question_type_via_qa_handler(self):
        """测试通过QAHandler识别问题类型"""
        qa_handler = self.service.qa_handler

        # 测试八字详情类
        bazi_questions = ["我的八字是什么？", "能解释一下我的四柱吗？"]
        for q in bazi_questions:
            qtype = qa_handler.identify_question_type(q)
            assert qtype == "bazi_details", f"问题 '{q}' 应该识别为 bazi_details"

        # 测试理论解释类
        theory_questions = ["什么是奇门遁甲？", "为什么用这个理论？"]
        for q in theory_questions:
            qtype = qa_handler.identify_question_type(q)
            assert qtype == "theory_explanation", f"问题 '{q}' 应该识别为 theory_explanation"

    def test_prepare_context_via_qa_handler(self):
        """测试通过QAHandler准备上下文"""
        qa_handler = self.service.qa_handler

        # 设置八字结果
        self.service.context.bazi_result = {
            "四柱": {"年柱": {"天干": "甲", "地支": "子"}},
            "五行分析": {"金": 1, "木": 2, "水": 3, "火": 1, "土": 1}
        }

        context = qa_handler.prepare_context("bazi_details")
        assert "bazi" in context

    def test_generate_fallback_response_via_qa_handler(self):
        """测试通过QAHandler生成降级响应"""
        qa_handler = self.service.qa_handler

        response = qa_handler.generate_fallback_response("bazi_details")
        assert isinstance(response, str)
        assert len(response) > 0
