"""
FlowGuard - 问道流程监管模块

V2核心组件：监控对话流程，防止用户输入错误或跳过步骤
- 定义每个阶段的输入要求
- 验证用户输入有效性（代码验证 + AI备用）
- 生成友好的错误提示和引导
- 跟踪进度，显示缺失信息
- 支持错误恢复和重试

V2更新：
- 新增 STAGE2_DEEPEN 阶段（测字术）
- 更新阶段名称映射
- 新增汉字验证器

设计理念：
类似Claude Code的todo系统，让用户清楚看到：
1. 当前在哪个阶段
2. 这个阶段需要什么
3. 已经收集到什么
4. 还缺少什么

AI+代码双重验证：
- 代码验证：快速、确定性高的规则验证
- AI验证：处理模糊输入、口语化表达、上下文理解
"""

import re
import json
from enum import Enum
from typing import Dict, Any, Optional, List, Tuple, TYPE_CHECKING
from dataclasses import dataclass, field
from utils.logger import get_logger
from api.prompt_loader import load_prompt

if TYPE_CHECKING:
    from api.manager import APIManager

# AI增强任务类型（统一使用，可在设置中配置）
TASK_TYPE_INPUT_ENHANCE = "输入增强验证"


class InputStatus(Enum):
    """输入状态"""
    VALID = "valid"           # 有效输入
    INVALID = "invalid"       # 无效输入
    INCOMPLETE = "incomplete" # 不完整
    SKIPPED = "skipped"       # 用户跳过
    RETRY = "retry"           # 需要重试


class RequirementLevel(Enum):
    """需求级别"""
    REQUIRED = "required"     # 必须提供
    RECOMMENDED = "recommended"  # 建议提供
    OPTIONAL = "optional"     # 可选


@dataclass
class StageRequirement:
    """阶段需求定义"""
    name: str                      # 需求名称
    description: str               # 需求描述
    level: RequirementLevel        # 需求级别
    validator: str                 # 验证器名称
    example: str = ""              # 示例
    error_hint: str = ""           # 错误提示
    collected: bool = False        # 是否已收集
    value: Any = None              # 收集的值


@dataclass
class StageProgress:
    """阶段进度"""
    stage_name: str
    total_required: int
    collected_required: int
    total_optional: int
    collected_optional: int
    missing_items: List[str]
    collected_items: Dict[str, Any]
    is_complete: bool
    can_proceed: bool              # 是否可以进入下一阶段
    progress_percent: float


@dataclass
class ValidationResult:
    """验证结果"""
    status: InputStatus
    message: str
    extracted_data: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)
    can_retry: bool = True


class FlowGuard:
    """
    流程监管器

    功能：
    1. 定义每个阶段的输入要求
    2. 验证用户输入
    3. 跟踪收集进度
    4. 生成引导提示
    5. 错误恢复
    """

    # 各阶段的输入要求定义（V2更新）
    STAGE_REQUIREMENTS = {
        # ===== 阶段1：破冰（小六壬）=====
        "STAGE1_ICEBREAK": [
            StageRequirement(
                name="question_category",
                description="咨询事项类别",
                level=RequirementLevel.REQUIRED,
                validator="validate_category",
                example="事业/感情/财运/健康/学业/决策",
                error_hint="请告诉我您想咨询什么类型的问题"
            ),
            StageRequirement(
                name="random_numbers",
                description="3个随机数字(1-9)",
                level=RequirementLevel.REQUIRED,
                validator="validate_numbers",
                example="7、3、5",
                error_hint="请提供3个1-9之间的随机数字，用于小六壬起卦"
            ),
        ],

        # ===== 阶段2：深入（测字术）- V2新增 =====
        "STAGE2_DEEPEN": [
            StageRequirement(
                name="question_description",
                description="具体问题描述",
                level=RequirementLevel.REQUIRED,
                validator="validate_description",
                example="想跳槽到互联网公司",
                error_hint="请简单描述一下具体是什么事情"
            ),
            StageRequirement(
                name="character",
                description="测字用的汉字",
                level=RequirementLevel.REQUIRED,
                validator="validate_character",
                example="变/心/动",
                error_hint="想着这件事，脑海中浮现的第一个汉字是什么？（可以是心态、未来的憧憬、当下想做的动作等）"
            ),
        ],

        # ===== 阶段3：信息收集（多理论）=====
        "STAGE3_COLLECT": [
            StageRequirement(
                name="birth_year",
                description="出生年份",
                level=RequirementLevel.REQUIRED,
                validator="validate_year",
                example="1990",
                error_hint="请提供出生年份（如1990）或说大概时间段"
            ),
            StageRequirement(
                name="birth_month",
                description="出生月份",
                level=RequirementLevel.REQUIRED,
                validator="validate_month",
                example="5",
                error_hint="请提供出生月份（1-12）"
            ),
            StageRequirement(
                name="birth_day",
                description="出生日期",
                level=RequirementLevel.REQUIRED,
                validator="validate_day",
                example="15",
                error_hint="请提供出生日期（1-31）"
            ),
            StageRequirement(
                name="birth_hour",
                description="出生时辰",
                level=RequirementLevel.OPTIONAL,  # V2改为可选：可以说大概时间段或不记得
                validator="validate_hour",
                example="下午3点 / 15点 / 不记得",
                error_hint="可以说大概时间段或不记得"
            ),
            StageRequirement(
                name="gender",
                description="性别",
                level=RequirementLevel.REQUIRED,
                validator="validate_gender",
                example="男/女",
                error_hint="请提供性别"
            ),
            StageRequirement(
                name="mbti_type",
                description="MBTI类型",
                level=RequirementLevel.OPTIONAL,
                validator="validate_mbti",
                example="INTJ/ENFP等",
                error_hint="如果知道您的MBTI类型可以提供，不知道可跳过"
            ),
            StageRequirement(
                name="favorite_color",
                description="喜欢的颜色",
                level=RequirementLevel.OPTIONAL,
                validator="validate_color",
                example="红/蓝/绿",
                error_hint="您喜欢什么颜色？（用于梅花易数起卦，可选）"
            ),
            StageRequirement(
                name="current_direction",
                description="当前方位",
                level=RequirementLevel.OPTIONAL,
                validator="validate_direction",
                example="东/南/西/北",
                error_hint="您现在面向什么方位？（用于梅花易数起卦，可选）"
            ),
        ],

        # ===== 阶段4：验证（回溯问题）=====
        "STAGE4_VERIFY": [
            StageRequirement(
                name="verification_feedback",
                description="验证问题反馈",
                level=RequirementLevel.REQUIRED,
                validator="validate_feedback",
                example="是的/不对/部分准确",
                error_hint="请回答验证问题，帮助我们提高分析准确度"
            ),
        ],

        # ===== 向后兼容：旧阶段名映射 =====
        "STAGE2_BASIC_INFO": [],  # 已移至 STAGE3_COLLECT
        "STAGE3_SUPPLEMENT": [],  # 已合并
        "STAGE4_VERIFICATION": [],  # 已移至 STAGE4_VERIFY
    }

    # 类别关键词映射
    CATEGORY_KEYWORDS = {
        "事业": ["工作", "职业", "事业", "跳槽", "升职", "创业", "公司", "老板"],
        "感情": ["感情", "恋爱", "婚姻", "姻缘", "桃花", "分手", "对象", "另一半"],
        "财运": ["财运", "财富", "赚钱", "投资", "理财", "收入", "亏损", "股票"],
        "健康": ["健康", "身体", "疾病", "养生", "生病", "医院"],
        "学业": ["学业", "考试", "学习", "升学", "考研", "高考"],
        "决策": ["决定", "选择", "是否", "要不要", "该不该"],
    }

    def __init__(self, api_manager: Optional["APIManager"] = None):
        """
        初始化流程监管器

        Args:
            api_manager: API管理器（用于AI增强验证）
        """
        self.logger = get_logger(__name__)
        self.api_manager = api_manager
        self.current_stage = "STAGE1_ICEBREAK"
        self.collected_data: Dict[str, Any] = {}
        self.stage_history: List[Dict[str, Any]] = []
        self.retry_count: Dict[str, int] = {}
        self.max_retries = 3
        self.ai_validation_enabled = api_manager is not None

    def set_api_manager(self, api_manager: "APIManager"):
        """设置API管理器（延迟注入）"""
        self.api_manager = api_manager
        self.ai_validation_enabled = True

    def set_stage(self, stage: str):
        """设置当前阶段"""
        self.current_stage = stage
        self.logger.info(f"FlowGuard: 进入阶段 {stage}")

    def validate_input(
        self,
        user_message: str,
        stage: Optional[str] = None
    ) -> ValidationResult:
        """
        验证用户输入

        Args:
            user_message: 用户消息
            stage: 阶段名称（默认使用当前阶段）

        Returns:
            ValidationResult
        """
        stage = stage or self.current_stage
        requirements = self.STAGE_REQUIREMENTS.get(stage, [])

        if not requirements:
            return ValidationResult(
                status=InputStatus.VALID,
                message="当前阶段无特定要求"
            )

        # 执行验证
        extracted = {}
        missing = []
        suggestions = []

        for req in requirements:
            validator = getattr(self, req.validator, None)
            if validator:
                value = validator(user_message)
                if value is not None:
                    extracted[req.name] = value
                    req.collected = True
                    req.value = value
                elif req.level == RequirementLevel.REQUIRED:
                    missing.append(req)
                    suggestions.append(f"💡 {req.error_hint}（示例：{req.example}）")

        # 更新收集的数据
        self.collected_data.update(extracted)

        # 判断状态
        if missing:
            if extracted:
                status = InputStatus.INCOMPLETE
                message = f"已收集部分信息，还需要：{', '.join([m.description for m in missing])}"
            else:
                status = InputStatus.INVALID
                message = "未能识别有效信息，请按照提示重新输入"
        else:
            status = InputStatus.VALID
            message = "信息收集完成"

        return ValidationResult(
            status=status,
            message=message,
            extracted_data=extracted,
            suggestions=suggestions,
            can_retry=True
        )

    async def validate_input_with_ai(
        self,
        user_message: str,
        stage: Optional[str] = None
    ) -> ValidationResult:
        """
        V2重构：使用AI优先的验证（AI优先，代码后备）

        流程：
        1. 如果有AI能力，先用AI验证
        2. AI失败或提取不完整时，用代码验证补充
        3. 如果没有AI能力，直接用代码验证

        Args:
            user_message: 用户消息
            stage: 阶段名称

        Returns:
            ValidationResult
        """
        stage = stage or self.current_stage
        requirements = self.STAGE_REQUIREMENTS.get(stage, [])

        if not requirements:
            return ValidationResult(
                status=InputStatus.VALID,
                message="当前阶段无特定要求"
            )

        # ===== AI优先验证 =====
        ai_extracted = {}
        if self.ai_validation_enabled and self.api_manager:
            try:
                self.logger.debug(f"[FlowGuard] 使用AI验证用户输入: {user_message[:50]}...")
                ai_extracted = await self._ai_validate(user_message, stage) or {}
                if ai_extracted:
                    self.logger.info(f"[FlowGuard] AI成功提取: {list(ai_extracted.keys())}")
            except Exception as e:
                self.logger.warning(f"[FlowGuard] AI验证失败，回退到代码验证: {e}")

        # ===== 代码后备验证（补充AI未提取的字段） =====
        code_extracted = {}
        for req in requirements:
            # 如果AI已提取该字段，跳过代码验证
            if req.name in ai_extracted:
                continue

            # 使用代码验证器尝试提取
            validator = getattr(self, req.validator, None)
            if validator:
                value = validator(user_message)
                if value is not None:
                    code_extracted[req.name] = value
                    self.logger.debug(f"[FlowGuard] 代码后备提取: {req.name} = {value}")

        # ===== 合并结果 =====
        merged_data = {**code_extracted, **ai_extracted}  # AI结果优先
        self.collected_data.update(merged_data)

        # 更新需求状态
        for req in requirements:
            if req.name in merged_data:
                req.collected = True
                req.value = merged_data[req.name]

        # ===== 检查是否满足要求 =====
        required = [r for r in requirements if r.level == RequirementLevel.REQUIRED]
        missing = [r for r in required if r.name not in self.collected_data]

        if not missing:
            source = "AI" if ai_extracted else "代码"
            return ValidationResult(
                status=InputStatus.VALID,
                message=f"信息收集完成（{source}识别）",
                extracted_data=merged_data,
                suggestions=[],
                can_retry=True
            )
        elif merged_data:
            return ValidationResult(
                status=InputStatus.INCOMPLETE,
                message=f"已收集部分信息，还需要：{', '.join([m.description for m in missing])}",
                extracted_data=merged_data,
                suggestions=[f"💡 {m.error_hint}（示例：{m.example}）" for m in missing],
                can_retry=True
            )
        else:
            return ValidationResult(
                status=InputStatus.INVALID,
                message="未能识别有效信息，请按照提示重新输入",
                extracted_data={},
                suggestions=[f"💡 {r.error_hint}（示例：{r.example}）" for r in required],
                can_retry=True
            )

    async def _ai_validate(
        self,
        user_message: str,
        stage: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        使用AI提取信息

        Args:
            user_message: 用户消息
            stage: 阶段名称

        Returns:
            提取的数据字典
        """
        stage = stage or self.current_stage
        requirements = self.STAGE_REQUIREMENTS.get(stage, [])

        if not requirements:
            return None

        # 构建提取要求说明
        req_descriptions = []
        for req in requirements:
            level_text = "必填" if req.level == RequirementLevel.REQUIRED else "可选"
            req_descriptions.append(f"- {req.name}: {req.description} ({level_text})，示例：{req.example}")

        prompt = load_prompt(
            "enhance", "input_validate",
            user_input=user_message,
            requirements="\n".join(req_descriptions)
        )

        try:
            response = await self.api_manager.call_api(
                task_type=TASK_TYPE_INPUT_ENHANCE,  # 使用统一的AI增强任务类型
                prompt=prompt,
                enable_dual_verification=False
            )

            # 解析JSON
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())

                # 转换和验证数据
                validated = {}
                for key, value in data.items():
                    if key in [r.name for r in requirements]:
                        validated[key] = value

                self.logger.info(f"AI提取信息: {validated}")
                return validated if validated else None

        except Exception as e:
            self.logger.warning(f"AI信息提取失败: {e}")

        return None

    async def smart_understand_input(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        智能理解用户输入（用于复杂/模糊输入）

        处理场景：
        - 用户口语化表达
        - 多信息混合输入
        - 上下文相关的省略表达

        Args:
            user_message: 用户消息
            context: 上下文信息

        Returns:
            理解结果
        """
        if not self.ai_validation_enabled or not self.api_manager:
            return {"understood": False, "reason": "AI未启用"}

        context_str = json.dumps(context, ensure_ascii=False) if context else "无"

        prompt = load_prompt(
            "enhance", "smart_understand",
            stage_name=self._get_stage_display_name(self.current_stage),
            collected_data=json.dumps(self.collected_data, ensure_ascii=False),
            context=context_str,
            user_input=user_message
        )

        try:
            response = await self.api_manager.call_api(
                task_type=TASK_TYPE_INPUT_ENHANCE,  # 使用统一的AI增强任务类型
                prompt=prompt,
                enable_dual_verification=False
            )

            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())

        except Exception as e:
            self.logger.warning(f"智能理解失败: {e}")

        return {"understood": False, "reason": "解析失败"}

    def get_stage_progress(self, stage: Optional[str] = None) -> StageProgress:
        """
        获取阶段进度

        Returns:
            StageProgress 进度对象
        """
        stage = stage or self.current_stage
        requirements = self.STAGE_REQUIREMENTS.get(stage, [])

        required = [r for r in requirements if r.level == RequirementLevel.REQUIRED]
        optional = [r for r in requirements if r.level != RequirementLevel.REQUIRED]

        collected_required = sum(1 for r in required if r.name in self.collected_data)
        collected_optional = sum(1 for r in optional if r.name in self.collected_data)

        missing = [r.description for r in required if r.name not in self.collected_data]
        collected = {r.name: self.collected_data.get(r.name) for r in requirements if r.name in self.collected_data}

        total = len(required)
        progress = (collected_required / total * 100) if total > 0 else 100

        return StageProgress(
            stage_name=stage,
            total_required=len(required),
            collected_required=collected_required,
            total_optional=len(optional),
            collected_optional=collected_optional,
            missing_items=missing,
            collected_items=collected,
            is_complete=collected_required == len(required),
            can_proceed=collected_required == len(required),
            progress_percent=progress
        )

    def generate_progress_display(self, stage: Optional[str] = None) -> str:
        """
        生成进度展示（类似todo list）

        Returns:
            Markdown格式的进度展示
        """
        stage = stage or self.current_stage
        progress = self.get_stage_progress(stage)
        requirements = self.STAGE_REQUIREMENTS.get(stage, [])

        lines = [
            f"## 📋 当前阶段：{self._get_stage_display_name(stage)}",
            "",
            f"**进度**：{progress.progress_percent:.0f}% ({progress.collected_required}/{progress.total_required} 必填项)",
            "",
            "### 信息收集清单",
            ""
        ]

        for req in requirements:
            collected = req.name in self.collected_data
            value = self.collected_data.get(req.name, "")

            if collected:
                icon = "✅"
                status = f"已收集: {value}"
            elif req.level == RequirementLevel.REQUIRED:
                icon = "⭕"
                status = f"**必填** - {req.example}"
            elif req.level == RequirementLevel.RECOMMENDED:
                icon = "🔸"
                status = f"建议 - {req.example}"
            else:
                icon = "⚪"
                status = f"可选 - {req.example}"

            lines.append(f"- {icon} **{req.description}**：{status}")

        if not progress.can_proceed:
            lines.extend([
                "",
                "---",
                "### ⚠️ 还需要提供：",
                ""
            ])
            for item in progress.missing_items:
                lines.append(f"- {item}")

        return "\n".join(lines)

    def generate_stage_prompt(self, stage: Optional[str] = None) -> str:
        """
        生成阶段引导提示

        Returns:
            引导用户输入的提示文本
        """
        stage = stage or self.current_stage
        requirements = self.STAGE_REQUIREMENTS.get(stage, [])
        missing = [r for r in requirements if r.level == RequirementLevel.REQUIRED and r.name not in self.collected_data]

        if not missing:
            return "信息已收集完整，可以继续下一步。"

        lines = ["请提供以下信息：", ""]

        for i, req in enumerate(missing, 1):
            lines.append(f"{i}. **{req.description}**")
            if req.example:
                lines.append(f"   示例：{req.example}")
            lines.append("")

        # 添加整合示例（V2更新）
        if stage == "STAGE1_ICEBREAK":
            lines.extend([
                "---",
                "💡 **您可以这样说**：",
                "```",
                "我想咨询事业，数字是：7、3、5",
                "```"
            ])
        elif stage == "STAGE2_DEEPEN":
            lines.extend([
                "---",
                "💡 **您可以这样说**：",
                "```",
                "最近在考虑是否要跳槽到互联网公司",
                "想到的字是'变'",
                "```"
            ])
        elif stage == "STAGE3_COLLECT":
            lines.extend([
                "---",
                "💡 **您可以这样说**：",
                "```",
                "我是1990年5月15日出生的，男，时辰不太记得了",
                "MBTI是INTJ，喜欢蓝色",
                "```",
                "（时辰、MBTI、颜色都是可选的）"
            ])
        elif stage == "STAGE4_VERIFY":
            lines.extend([
                "---",
                "💡 **请回答验证问题**：",
                "直接回答 是/否/部分准确 即可"
            ])
        # 向后兼容
        elif stage == "STAGE2_BASIC_INFO":
            lines.extend([
                "---",
                "💡 **您可以这样说**：",
                "```",
                "我是1990年5月15日下午3点出生的，男，公历",
                "```",
                "或者分开说也可以"
            ])

        return "\n".join(lines)

    def can_skip_stage(self, stage: Optional[str] = None) -> Tuple[bool, str]:
        """
        检查是否可以跳过当前阶段

        Returns:
            (是否可以跳过, 原因)
        """
        stage = stage or self.current_stage
        progress = self.get_stage_progress(stage)

        if progress.can_proceed:
            return True, "必填信息已完成，可以进入下一阶段"
        else:
            return False, f"还缺少必填信息：{', '.join(progress.missing_items)}"

    def handle_error_input(self, error_type: str) -> str:
        """
        处理错误输入，生成友好提示

        Args:
            error_type: 错误类型

        Returns:
            友好的错误提示
        """
        error_messages = {
            "parse_failed": "抱歉，我没能理解您的输入。请按照示例格式重新输入。",
            "invalid_numbers": "随机数字需要是3个1-9之间的数字，例如：7、3、5",
            "invalid_date": "日期格式不正确，请使用类似'1990年5月15日'的格式",
            "missing_required": "还缺少一些必要信息，请查看上方的清单补充",
            "api_error": "系统遇到了一点问题，请稍后重试",
        }

        base_message = error_messages.get(error_type, "输入有误，请重试")

        # 增加重试计数
        self.retry_count[error_type] = self.retry_count.get(error_type, 0) + 1

        if self.retry_count[error_type] >= self.max_retries:
            base_message += "\n\n如果持续遇到问题，您可以输入'帮助'查看详细指南。"

        return base_message

    def reset_stage(self, stage: Optional[str] = None):
        """重置阶段数据"""
        stage = stage or self.current_stage
        requirements = self.STAGE_REQUIREMENTS.get(stage, [])

        for req in requirements:
            if req.name in self.collected_data:
                del self.collected_data[req.name]
            req.collected = False
            req.value = None

        self.retry_count.clear()
        self.logger.info(f"FlowGuard: 重置阶段 {stage}")

    # ==================== 验证器 ====================

    def validate_category(self, text: str) -> Optional[str]:
        """验证并提取咨询类别"""
        text_lower = text.lower()

        for category, keywords in self.CATEGORY_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                return category

        # 直接匹配类别名
        for category in self.CATEGORY_KEYWORDS.keys():
            if category in text:
                return category

        return None

    def validate_description(self, text: str) -> Optional[str]:
        """验证问题描述"""
        # 如果文本长度超过5个字符，认为有描述
        if len(text.strip()) > 5:
            return text.strip()[:200]  # 限制200字
        return None

    def validate_numbers(self, text: str) -> Optional[List[int]]:
        """验证并提取3个随机数字"""
        # 中文数字映射
        chinese_nums = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
                       "六": 6, "七": 7, "八": 8, "九": 9}

        # 替换中文数字
        for cn, num in chinese_nums.items():
            text = text.replace(cn, str(num))

        # 提取所有1-9的数字
        numbers = re.findall(r'[1-9]', text)

        if len(numbers) >= 3:
            result = [int(n) for n in numbers[:3]]
            return result

        return None

    def validate_year(self, text: str) -> Optional[int]:
        """验证出生年份"""
        # 匹配4位年份
        match = re.search(r'(19[5-9]\d|20[0-2]\d)', text)
        if match:
            return int(match.group(1))

        # 匹配2位年份
        match = re.search(r'(\d{2})年', text)
        if match:
            year = int(match.group(1))
            return 1900 + year if year >= 30 else 2000 + year

        return None

    def validate_month(self, text: str) -> Optional[int]:
        """验证月份"""
        # 匹配月份
        match = re.search(r'(\d{1,2})月', text)
        if match:
            month = int(match.group(1))
            if 1 <= month <= 12:
                return month

        # 匹配正月等
        lunar_months = {"正月": 1, "腊月": 12}
        for name, num in lunar_months.items():
            if name in text:
                return num

        return None

    def validate_day(self, text: str) -> Optional[int]:
        """验证日期"""
        match = re.search(r'(\d{1,2})[日号]', text)
        if match:
            day = int(match.group(1))
            if 1 <= day <= 31:
                return day
        return None

    def validate_hour(self, text: str) -> Optional[int]:
        """验证时辰"""
        # 不记得/不知道
        if any(kw in text for kw in ["不记得", "忘了", "不知道", "不确定"]):
            return -1  # 特殊值表示不知道

        # 匹配小时
        match = re.search(r'(\d{1,2})点', text)
        if match:
            hour = int(match.group(1))
            if 0 <= hour <= 23:
                return hour

        # 时段映射
        time_periods = {
            "凌晨": 3, "早上": 7, "上午": 10,
            "中午": 12, "下午": 15, "傍晚": 18,
            "晚上": 20, "深夜": 23
        }
        for period, hour in time_periods.items():
            if period in text:
                return hour

        return None

    def validate_gender(self, text: str) -> Optional[str]:
        """验证性别"""
        if any(kw in text for kw in ["男", "先生", "男性"]):
            return "male"
        if any(kw in text for kw in ["女", "女士", "女性"]):
            return "female"
        return None

    def validate_calendar(self, text: str) -> Optional[str]:
        """验证历法类型"""
        if any(kw in text for kw in ["农历", "阴历", "正月"]):
            return "lunar"
        if any(kw in text for kw in ["公历", "阳历", "新历"]):
            return "solar"
        return "solar"  # 默认公历

    def validate_mbti(self, text: str) -> Optional[str]:
        """验证MBTI类型"""
        match = re.search(r'([IE][NS][TF][JP])', text.upper())
        if match:
            return match.group(1)
        return None

    def validate_place(self, text: str) -> Optional[str]:
        """验证出生地"""
        # 简单提取城市名
        cities = ["北京", "上海", "广州", "深圳", "成都", "杭州", "武汉", "西安",
                 "南京", "重庆", "天津", "苏州", "郑州", "长沙", "沈阳", "青岛",
                 "大连", "厦门", "福州", "哈尔滨", "济南", "昆明", "乌鲁木齐"]

        for city in cities:
            if city in text:
                return city

        # 匹配"XX市"或"XX省"
        match = re.search(r'([\u4e00-\u9fa5]{2,4})[市省]', text)
        if match:
            return match.group(1)

        return None

    def validate_certainty(self, text: str) -> Optional[str]:
        """验证时辰确定性"""
        if any(kw in text for kw in ["确定", "肯定", "准确", "精确"]):
            return "certain"
        if any(kw in text for kw in ["大概", "大约", "可能", "好像"]):
            return "uncertain"
        if any(kw in text for kw in ["不确定", "不知道", "不记得"]):
            return "unknown"
        return None

    def validate_events(self, text: str) -> Optional[str]:
        """验证生活事件描述"""
        if len(text) > 10:
            return text[:500]
        return None

    def validate_feedback(self, text: str) -> Optional[str]:
        """验证反馈"""
        if any(kw in text for kw in ["是", "对", "准", "正确", "没错"]):
            return "accurate"
        if any(kw in text for kw in ["不是", "不对", "错", "不准"]):
            return "inaccurate"
        if any(kw in text for kw in ["部分", "有些", "一半"]):
            return "partial"
        return None

    def validate_character(self, text: str) -> Optional[str]:
        """
        V2新增：验证测字用的汉字（代码后备验证器）

        提取优先级：
        1. "测X字" 格式 - 用户明确指定
        2. 引号内的单字 - 用户明确指定
        3. 句尾单字 - 逗号/句号后的单个汉字（如"升官发财，望"）
        4. 自动提取第一个有意义的汉字

        注意：此为代码后备验证器，AI验证器优先使用
        """
        # 1. 匹配 "测X字" 格式（用户明确指定）
        match = re.search(r'测[「「\'\""]?([\u4e00-\u9fa5])[」」\'\""]?字', text)
        if match:
            return match.group(1)

        # 2. 匹配引号内的汉字（用户明确指定）
        match = re.search(r'[「「\'\""]+([\u4e00-\u9fa5])[」」\'\""]+', text)
        if match:
            return match.group(1)

        # 3. 匹配句尾单字（逗号/句号/问号后的单个汉字）
        # 如："就像知道这辈子能不能升官发财，望" → 提取"望"
        match = re.search(r'[，。！？,.\!?]\s*([\u4e00-\u9fa5])[\s，。！？,.\!?]*$', text)
        if match:
            char = match.group(1)
            # 排除语气词
            if char not in ['啊', '吧', '呢', '吗', '哦', '嗯']:
                return char

        # 4. 自动提取第一个有意义的汉字
        exclude_chars = set("的了吧呢啊哦嗯是不我你他她它们这那问请想能会")
        for char in text:
            if '\u4e00' <= char <= '\u9fa5' and char not in exclude_chars:
                return char

        return None

    def validate_color(self, text: str) -> Optional[str]:
        """
        V2新增：验证颜色（用于梅花易数起卦）

        注意：按关键词长度降序匹配，确保 "粉红色" 匹配到 "粉" 而非 "红"
        """
        # 颜色关键词映射（按长度优先匹配）
        color_keywords = {
            "粉": ["粉红色", "粉红", "粉色", "粉"],  # 粉红优先于红
            "紫": ["紫红", "紫色", "紫"],  # 紫红优先于红
            "红": ["大红", "朱红", "红色", "红", "赤"],
            "橙": ["橘色", "橙色", "橙"],
            "黄": ["金黄", "金色", "黄色", "黄"],
            "绿": ["青色", "绿色", "绿"],
            "蓝": ["湛蓝", "蓝色", "蓝"],
            "白": ["白色", "白"],
            "黑": ["黑色", "黑"],
            "灰": ["灰色", "灰"],
        }

        text_lower = text.lower()
        # 按关键词长度降序检查，更长的匹配优先
        all_matches = []
        for color, keywords in color_keywords.items():
            for kw in keywords:
                if kw in text_lower:
                    all_matches.append((len(kw), color))

        if all_matches:
            # 返回最长匹配对应的颜色
            all_matches.sort(key=lambda x: -x[0])
            return all_matches[0][1]

        return None

    def validate_direction(self, text: str) -> Optional[str]:
        """
        V2新增：验证方位（用于梅花易数起卦）

        注意：复合方位（东南/东北/西南/西北）优先匹配
        """
        # 复合方位优先检查（长度更长）
        compound_directions = ["东南", "东北", "西南", "西北"]
        for direction in compound_directions:
            if direction in text:
                return direction

        # 然后检查单一方位
        simple_direction_keywords = {
            "东": ["东", "东方", "东边", "东面"],
            "南": ["南", "南方", "南边", "南面"],
            "西": ["西", "西方", "西边", "西面"],
            "北": ["北", "北方", "北边", "北面"],
        }

        for direction, keywords in simple_direction_keywords.items():
            if any(kw in text for kw in keywords):
                return direction

        return None

    # ==================== 用户信息修改（方案B：对话指令） ====================

    # 修改关键词映射
    MODIFY_KEYWORDS = ["修改", "更改", "改成", "改为", "纠正", "更正", "其实是", "应该是", "写错了"]

    # 字段关键词映射
    FIELD_KEYWORDS = {
        "birth_year": ["出生年", "年份", "生于", "出生在"],
        "birth_month": ["月份", "生日", "月"],
        "birth_day": ["日期", "日", "号"],
        "birth_hour": ["时辰", "时间", "点", "几点"],
        "gender": ["性别", "男", "女"],
        "mbti_type": ["mbti", "性格类型", "人格"],
        "question_category": ["类别", "咨询", "问题类型"],
        "character": ["汉字", "测字", "字"],
    }

    def detect_modification_intent(self, user_message: str) -> bool:
        """
        检测用户是否想修改已收集的信息

        Returns:
            True 如果用户想修改信息
        """
        text = user_message.lower()
        return any(kw in text for kw in self.MODIFY_KEYWORDS)

    async def process_modification(
        self,
        user_message: str,
        context: Any
    ) -> Optional[Dict[str, Any]]:
        """
        处理用户的修改请求

        Args:
            user_message: 用户消息
            context: ConversationContext 对象

        Returns:
            修改结果字典，包含修改的字段和值；如果无法解析则返回None
        """
        if not self.detect_modification_intent(user_message):
            return None

        modifications = {}

        # 尝试用AI解析修改意图
        if self.ai_validation_enabled and self.api_manager:
            try:
                ai_mods = await self._ai_parse_modification(user_message)
                if ai_mods:
                    modifications.update(ai_mods)
            except Exception as e:
                self.logger.warning(f"AI解析修改意图失败: {e}")

        # 代码后备解析
        if not modifications:
            modifications = self._code_parse_modification(user_message)

        if modifications:
            # 更新 context
            for field, value in modifications.items():
                if hasattr(context, field):
                    old_value = getattr(context, field)
                    setattr(context, field, value)
                    self.logger.info(f"[FlowGuard] 修改 {field}: {old_value} -> {value}")

                    # 同步更新 collected_data
                    self.collected_data[field] = value

                # 特殊处理 birth_info
                if field.startswith("birth_") and hasattr(context, "birth_info"):
                    if context.birth_info is None:
                        context.birth_info = {}
                    field_name = field.replace("birth_", "")
                    context.birth_info[field_name] = value

            return {"modified": modifications, "message": self._format_modification_message(modifications)}

        return None

    async def _ai_parse_modification(self, user_message: str) -> Optional[Dict[str, Any]]:
        """使用AI解析修改意图"""
        prompt = f"""用户想修改之前提供的信息。请解析用户想修改什么字段以及新值。

用户消息："{user_message}"

可修改的字段：
- birth_year: 出生年份（整数，如1990）
- birth_month: 出生月份（整数1-12）
- birth_day: 出生日期（整数1-31）
- birth_hour: 出生时辰（整数0-23，-1表示不记得）
- gender: 性别（"男"或"女"）
- mbti_type: MBTI类型（如"INTJ"）
- question_category: 咨询类别（事业/感情/财运/健康/学业/决策）
- character: 测字用的汉字（单个汉字）

请返回JSON格式，只包含用户想修改的字段：
{{"field_name": "new_value", ...}}

如果无法解析，返回空对象 {{}}
"""
        try:
            response = await self.api_manager.call_api(
                task_type=TASK_TYPE_INPUT_ENHANCE,
                prompt=prompt,
                enable_dual_verification=False
            )

            # 提取JSON
            json_match = re.search(r'\{[^}]+\}', response)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            self.logger.error(f"AI解析修改失败: {e}")

        return None

    def _code_parse_modification(self, user_message: str) -> Dict[str, Any]:
        """代码后备解析修改意图"""
        modifications = {}
        text = user_message

        # 尝试识别要修改的字段和新值
        for field, keywords in self.FIELD_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                # 根据字段类型提取新值
                if field == "birth_year":
                    value = self.validate_year(text)
                elif field == "birth_month":
                    value = self.validate_month(text)
                elif field == "birth_day":
                    value = self.validate_day(text)
                elif field == "birth_hour":
                    value = self.validate_hour(text)
                elif field == "gender":
                    value = self.validate_gender(text)
                elif field == "mbti_type":
                    value = self.validate_mbti(text)
                elif field == "question_category":
                    value = self.validate_category(text)
                elif field == "character":
                    value = self.validate_character(text)
                else:
                    value = None

                if value is not None:
                    modifications[field] = value

        return modifications

    def _format_modification_message(self, modifications: Dict[str, Any]) -> str:
        """格式化修改确认消息"""
        field_names = {
            "birth_year": "出生年份",
            "birth_month": "出生月份",
            "birth_day": "出生日期",
            "birth_hour": "出生时辰",
            "gender": "性别",
            "mbti_type": "MBTI类型",
            "question_category": "咨询类别",
            "character": "测字汉字",
        }

        lines = ["✅ 已更新您的信息："]
        for field, value in modifications.items():
            name = field_names.get(field, field)
            lines.append(f"- {name}: {value}")

        return "\n".join(lines)

    # ==================== 辅助方法 ====================

    def _get_stage_display_name(self, stage: str) -> str:
        """获取阶段显示名称（V2更新）"""
        names = {
            # V2新阶段名称
            "STAGE1_ICEBREAK": "阶段1：破冰",
            "STAGE2_DEEPEN": "阶段2：深入",
            "STAGE3_COLLECT": "阶段3：信息收集",
            "STAGE4_VERIFY": "阶段4：验证",
            "STAGE5_REPORT": "阶段5：报告",
            # 向后兼容旧阶段名
            "STAGE2_BASIC_INFO": "基础信息收集",
            "STAGE3_SUPPLEMENT": "深度补充",
            "STAGE4_VERIFICATION": "结果验证",
            "STAGE5_FINAL_REPORT": "完整报告",
        }
        return names.get(stage, stage)


# 单例
_flow_guard_instance: Optional[FlowGuard] = None


def get_flow_guard(api_manager: Optional["APIManager"] = None) -> FlowGuard:
    """
    获取FlowGuard单例

    Args:
        api_manager: API管理器（首次调用时设置，后续调用可忽略）

    Returns:
        FlowGuard实例
    """
    global _flow_guard_instance
    if _flow_guard_instance is None:
        _flow_guard_instance = FlowGuard(api_manager)
    elif api_manager and not _flow_guard_instance.api_manager:
        # 延迟注入API管理器
        _flow_guard_instance.set_api_manager(api_manager)
    return _flow_guard_instance


def reset_flow_guard():
    """重置FlowGuard单例（用于测试）"""
    global _flow_guard_instance
    _flow_guard_instance = None
