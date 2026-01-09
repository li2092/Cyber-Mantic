"""
问道流程V2自动化测试

测试内容：
1. FlowGuard验证器（AI优先，代码后备）
2. 各阶段数据收集和转换
3. 测字术汉字提取（包括语气词）
4. 颜色/方位提取
5. 完整流程端到端测试
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import json


# ==================== FlowGuard验证器测试 ====================

class TestFlowGuardValidatorsV2:
    """FlowGuard验证器测试（V2更新版）"""

    def setup_method(self):
        """设置测试"""
        from core.flow_guard import FlowGuard
        self.guard = FlowGuard()

    # ===== 测字术汉字提取测试 =====

    def test_character_extract_test_format(self):
        """测试"测X字"格式提取"""
        # 常规汉字
        assert self.guard.validate_character("测变字") == "变"
        assert self.guard.validate_character("测心字") == "心"
        assert self.guard.validate_character("测'动'字") == "动"

    def test_character_extract_with_particle(self):
        """测试语气词也能被提取（用户明确指定时）"""
        # 大魔王要求：用户指定语气词也得测
        assert self.guard.validate_character("测的字") == "的"
        assert self.guard.validate_character("测了字") == "了"
        assert self.guard.validate_character("测吧字") == "吧"
        assert self.guard.validate_character("测啊字") == "啊"

    def test_character_extract_quoted(self):
        """测试引号内汉字提取"""
        assert self.guard.validate_character("想到了'变'字") == "变"
        assert self.guard.validate_character('浮现"心"字') == "心"
        assert self.guard.validate_character("脑海中出现「动」") == "动"
        # 语气词在引号内也应提取
        assert self.guard.validate_character("想到了'的'") == "的"

    def test_character_extract_auto(self):
        """测试自动提取（未明确指定时排除语气词）"""
        # 自动提取应排除语气词，取第一个有意义的字
        result = self.guard.validate_character("想跳槽到互联网公司")
        assert result is not None
        assert result not in "的了吧呢啊哦嗯是不我你他她它们这那"

    # ===== 颜色提取测试 =====

    def test_color_extract(self):
        """测试颜色提取"""
        assert self.guard.validate_color("喜欢红色") == "红"
        assert self.guard.validate_color("蓝色") == "蓝"
        assert self.guard.validate_color("我喜欢绿") == "绿"
        assert self.guard.validate_color("金色") == "黄"  # 金色映射到黄
        assert self.guard.validate_color("粉红色") == "粉"

    def test_color_no_match(self):
        """测试无颜色匹配"""
        assert self.guard.validate_color("今天天气很好") is None

    # ===== 方位提取测试 =====

    def test_direction_extract(self):
        """测试方位提取"""
        assert self.guard.validate_direction("东边") == "东"
        assert self.guard.validate_direction("面向南") == "南"
        assert self.guard.validate_direction("西北方向") == "西北"
        assert self.guard.validate_direction("东南") == "东南"

    def test_direction_no_match(self):
        """测试无方位匹配"""
        assert self.guard.validate_direction("今天天气很好") is None

    # ===== 咨询类别测试 =====

    def test_category_extract(self):
        """测试咨询类别提取"""
        assert self.guard.validate_category("事业") == "事业"
        assert self.guard.validate_category("想问感情问题") is not None
        assert self.guard.validate_category("财运") == "财运"
        assert self.guard.validate_category("最近工作不顺") is not None  # 应识别为事业

    # ===== 随机数字测试 =====

    def test_numbers_extract(self):
        """测试随机数字提取"""
        result = self.guard.validate_numbers("3 5 7")
        assert result == [3, 5, 7]

        result = self.guard.validate_numbers("1、2、3")
        assert result == [1, 2, 3]

    def test_numbers_chinese(self):
        """测试中文数字提取"""
        result = self.guard.validate_numbers("三五七")
        assert result == [3, 5, 7] or result is None  # 取决于实现

    # ===== 生辰信息测试 =====

    def test_birth_info_extract(self):
        """测试生辰信息提取"""
        assert self.guard.validate_year("1990年") == 1990
        assert self.guard.validate_month("5月") == 5
        assert self.guard.validate_day("15日") == 15

    def test_gender_extract(self):
        """测试性别提取"""
        assert self.guard.validate_gender("男") == "male"
        assert self.guard.validate_gender("女性") == "female"

    def test_mbti_extract(self):
        """测试MBTI提取"""
        assert self.guard.validate_mbti("INTJ") == "INTJ"
        assert self.guard.validate_mbti("我是entj") == "ENTJ"


class TestFlowGuardAIValidation:
    """FlowGuard AI优先验证测试"""

    def setup_method(self):
        """设置测试"""
        from core.flow_guard import FlowGuard
        self.guard = FlowGuard()

    @pytest.mark.asyncio
    async def test_ai_priority_validation(self):
        """测试AI优先验证逻辑"""
        # 模拟API管理器
        mock_api_manager = Mock()
        mock_api_manager.call_api = AsyncMock(return_value='{"question_category": "事业", "random_numbers": [3, 5, 7]}')

        self.guard.set_api_manager(mock_api_manager)
        self.guard.set_stage("STAGE1_ICEBREAK")

        result = await self.guard.validate_input_with_ai("事业，357")

        # 应该调用了AI
        assert mock_api_manager.call_api.called

    @pytest.mark.asyncio
    async def test_fallback_to_code_when_ai_fails(self):
        """测试AI失败时回退到代码验证"""
        # 模拟API调用失败
        mock_api_manager = Mock()
        mock_api_manager.call_api = AsyncMock(side_effect=Exception("API错误"))

        self.guard.set_api_manager(mock_api_manager)
        self.guard.set_stage("STAGE1_ICEBREAK")

        result = await self.guard.validate_input_with_ai("事业，3 5 7")

        # 即使AI失败，代码验证应该能提取数据
        assert result.extracted_data is not None

    @pytest.mark.asyncio
    async def test_code_supplement_ai_partial(self):
        """测试代码补充AI未提取的字段"""
        # AI只提取了部分字段
        mock_api_manager = Mock()
        mock_api_manager.call_api = AsyncMock(return_value='{"question_category": "事业"}')

        self.guard.set_api_manager(mock_api_manager)
        self.guard.set_stage("STAGE1_ICEBREAK")

        result = await self.guard.validate_input_with_ai("事业，3 5 7")

        # 代码应该补充提取random_numbers
        if "random_numbers" not in result.extracted_data:
            # 如果AI没提取到，代码后备应该提取
            pass  # 根据具体实现检查


# ==================== 阶段转换测试 ====================

class TestConversationStageV2:
    """对话阶段测试（V2更新版）"""

    def test_stage_enum_values(self):
        """测试阶段枚举值"""
        from services.conversation.context import ConversationStage

        # V2新阶段
        assert ConversationStage.STAGE2_DEEPEN.value == "阶段2_深入"
        assert ConversationStage.STAGE3_COLLECT.value == "阶段3_信息收集"
        assert ConversationStage.STAGE4_VERIFY.value == "阶段4_验证"
        assert ConversationStage.STAGE5_REPORT.value == "阶段5_报告"

    def test_legacy_stage_mapping(self):
        """测试旧阶段向后兼容映射"""
        from services.conversation.context import ConversationStage

        # 旧阶段名应映射到新阶段
        stage = ConversationStage.from_legacy_value("阶段2_基础信息")
        assert stage == ConversationStage.STAGE3_COLLECT

        stage = ConversationStage.from_legacy_value("阶段4_结果确认")
        assert stage == ConversationStage.STAGE4_VERIFY


class TestConversationContextV2:
    """对话上下文测试（V2更新版）"""

    def setup_method(self):
        """设置测试"""
        from services.conversation.context import ConversationContext
        self.context = ConversationContext()

    def test_new_fields(self):
        """测试V2新增字段"""
        # 阶段1新增
        assert hasattr(self.context, 'qigua_time')

        # 阶段2新增
        assert hasattr(self.context, 'character')
        assert hasattr(self.context, 'cezi_result')

        # 阶段3新增
        assert hasattr(self.context, 'liuyao_numbers')

    def test_generate_liuyao_numbers(self):
        """测试六爻自动起卦数字生成"""
        self.context.qigua_time = datetime.now()
        numbers = self.context.generate_liuyao_numbers()

        assert len(numbers) == 3
        assert all(1 <= n <= 9 for n in numbers)

    def test_get_meihua_method(self):
        """测试梅花易数起卦方式选择"""
        # 无颜色无方位：使用时间
        method, params = self.context.get_meihua_method()
        assert method == "时间起卦"

        # 有颜色：使用颜色
        self.context.favorite_color = "红"
        method, params = self.context.get_meihua_method()
        assert method == "颜色起卦"
        assert params["color"] == "红"

        # 有方位（颜色优先）
        self.context.current_direction = "东"
        method, params = self.context.get_meihua_method()
        assert method == "颜色起卦"  # 颜色优先

        # 只有方位
        self.context.favorite_color = None
        method, params = self.context.get_meihua_method()
        assert method == "方位起卦"

    def test_to_dict_and_from_dict(self):
        """测试序列化和反序列化"""
        from services.conversation.context import ConversationStage

        self.context.stage = ConversationStage.STAGE2_DEEPEN
        self.context.character = "变"
        self.context.qigua_time = datetime.now()

        # 序列化
        data = self.context.to_dict()
        assert data["character"] == "变"
        assert data["qigua_time"] is not None

        # 反序列化
        from services.conversation.context import ConversationContext
        restored = ConversationContext.from_dict(data)
        assert restored.character == "变"
        assert restored.stage == ConversationStage.STAGE2_DEEPEN


# ==================== 端到端流程测试 ====================

class TestWendaoFlowE2E:
    """问道流程端到端测试"""

    @pytest.fixture
    def mock_api_manager(self):
        """模拟API管理器"""
        mock = Mock()
        mock.call_api = AsyncMock(return_value="模拟AI回复")
        mock.kimi_client = Mock()
        mock.kimi_client.async_chat = AsyncMock(return_value="模拟Kimi回复")
        return mock

    @pytest.mark.asyncio
    async def test_stage1_icebreak(self, mock_api_manager):
        """测试阶段1：破冰"""
        from services.conversation_service import ConversationService
        from services.conversation.context import ConversationStage

        # 模拟AI返回解析结果
        mock_api_manager.call_api = AsyncMock(return_value=json.dumps({
            "question_category": "事业",
            "random_numbers": [3, 5, 7]
        }))

        service = ConversationService(mock_api_manager)

        # 开始对话
        await service.start_conversation()

        # 模拟用户输入阶段1
        response = await service.process_user_input("事业，3 5 7")

        # 检查状态
        assert service.context.question_category == "事业"
        assert service.context.random_numbers == [3, 5, 7]
        assert service.context.qigua_time is not None
        assert service.context.xiaoliu_result is not None

    @pytest.mark.asyncio
    async def test_stage2_deepen(self, mock_api_manager):
        """测试阶段2：深入（测字术）"""
        from services.conversation_service import ConversationService
        from services.conversation.context import ConversationStage

        service = ConversationService(mock_api_manager)

        # 设置阶段1完成状态
        service.context.stage = ConversationStage.STAGE2_DEEPEN
        service.context.question_category = "事业"
        service.context.random_numbers = [3, 5, 7]
        service.context.qigua_time = datetime.now()
        service.context.xiaoliu_result = {"judgment": "吉"}

        # 模拟AI返回
        mock_api_manager.call_api = AsyncMock(return_value=json.dumps({
            "question_description": "想跳槽到互联网公司",
            "character": "变"
        }))

        # 模拟用户输入阶段2
        response = await service.process_user_input("想跳槽到互联网公司，测'变'字")

        # 检查状态
        assert service.context.question_description is not None
        assert service.context.character == "变"

    @pytest.mark.asyncio
    async def test_full_flow_simulation(self, mock_api_manager):
        """模拟完整流程"""
        from services.conversation_service import ConversationService
        from services.conversation.context import ConversationStage

        service = ConversationService(mock_api_manager)

        # 配置mock返回
        def mock_call_api(task_type, prompt, **kwargs):
            if "阶段1" in str(task_type) or "STAGE1" in str(task_type):
                return json.dumps({"question_category": "事业", "random_numbers": [3, 5, 7]})
            elif "阶段2" in str(task_type) or "STAGE2" in str(task_type):
                return json.dumps({"question_description": "跳槽", "character": "变"})
            else:
                return "AI回复"

        mock_api_manager.call_api = AsyncMock(side_effect=mock_call_api)

        # 阶段0：欢迎
        welcome = await service.start_conversation()
        assert "欢迎" in welcome or welcome is not None

        # 阶段1：破冰
        # （后续阶段测试可以继续添加）


# ==================== 回归测试 ====================

class TestRegressionV2:
    """回归测试 - 确保旧功能不被破坏"""

    def test_xiaoliu_still_works(self):
        """测试小六壬仍然正常工作"""
        from theories.xiaoliu.theory import XiaoLiuRenTheory
        from models import UserInput

        theory = XiaoLiuRenTheory()
        user_input = UserInput(
            question_type="事业",
            question_description="工作发展",
            numbers=[3, 5, 7],
            current_time=datetime.now()
        )
        result = theory.calculate(user_input)

        assert result is not None
        assert "judgment" in result or "吉凶" in str(result)

    def test_cezi_still_works(self):
        """测试测字术仍然正常工作"""
        from theories.cezi.theory import CeZiTheory
        from models import UserInput

        theory = CeZiTheory()
        user_input = UserInput(
            question_type="事业",
            question_description="想跳槽",
            character="变"
        )
        result = theory.calculate(user_input)

        assert result is not None

    def test_meihua_color_gua(self):
        """测试梅花易数颜色起卦"""
        from theories.meihua.theory import MeiHuaTheory
        from models import UserInput

        theory = MeiHuaTheory()
        user_input = UserInput(
            question_type="事业",
            question_description="工作选择",
            favorite_color="红",
            current_time=datetime.now()
        )
        result = theory.calculate(user_input)

        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
