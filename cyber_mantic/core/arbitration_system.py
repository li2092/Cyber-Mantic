"""
ArbitrationSystem - 仲裁系统

V2核心组件：当多个理论结果产生冲突时，引入第三方理论进行裁决
- 根据问题类型选择最适合的仲裁理论
- 避免使用已参与冲突的理论
- 综合仲裁结果给出最终判断
"""

import json
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
from utils.logger import get_logger


class ArbitrationStatus(Enum):
    """仲裁状态"""
    NOT_NEEDED = "not_needed"      # 不需要仲裁
    REQUESTED = "requested"         # 已请求仲裁
    IN_PROGRESS = "in_progress"     # 仲裁进行中
    COMPLETED = "completed"         # 仲裁完成
    FAILED = "failed"               # 仲裁失败


@dataclass
class ArbitrationConflictInfo:
    """仲裁系统的冲突信息（区别于models.ConflictInfo）"""
    theory_a: str
    theory_b: str
    judgment_a: str  # 吉/凶/平
    judgment_b: str
    reason_a: str
    reason_b: str
    conflict_level: str  # 高/中/低


@dataclass
class ArbitrationResult:
    """仲裁结果"""
    status: ArbitrationStatus
    arbitration_theory: Optional[str] = None
    arbitration_judgment: Optional[str] = None
    arbitration_reason: Optional[str] = None
    final_judgment: Optional[str] = None
    confidence: float = 0.0
    explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "arbitration_theory": self.arbitration_theory,
            "arbitration_judgment": self.arbitration_judgment,
            "arbitration_reason": self.arbitration_reason,
            "final_judgment": self.final_judgment,
            "confidence": self.confidence,
            "explanation": self.explanation
        }


class ArbitrationSystem:
    """仲裁系统：冲突时引入第三方理论裁决"""

    # 仲裁理论优先级（按问题类型）
    ARBITRATION_PRIORITY = {
        "事业": ["六爻", "梅花易数", "小六壬", "奇门遁甲"],
        "感情": ["测字术", "梅花易数", "六爻", "紫微斗数"],
        "财运": ["六爻", "奇门遁甲", "小六壬", "梅花易数"],
        "健康": ["六爻", "小六壬", "梅花易数", "八字"],
        "决策": ["奇门遁甲", "六爻", "大六壬", "梅花易数"],
        "学业": ["梅花易数", "六爻", "八字", "紫微斗数"],
        "其他": ["六爻", "梅花易数", "小六壬", "奇门遁甲"]
    }

    # 理论可信度权重（基于历史准确性和理论完备性）
    THEORY_WEIGHTS = {
        "八字": 0.85,
        "紫微斗数": 0.85,
        "奇门遁甲": 0.80,
        "大六壬": 0.80,
        "六爻": 0.75,
        "梅花易数": 0.70,
        "小六壬": 0.65,
        "测字术": 0.60
    }

    def __init__(self, api_manager=None):
        """
        初始化仲裁系统

        Args:
            api_manager: API管理器（用于AI分析）
        """
        self.logger = get_logger(__name__)
        self.api_manager = api_manager

    def request_arbitration(
        self,
        conflict: ArbitrationConflictInfo,
        question_type: str,
        used_theories: List[str]
    ) -> Optional[str]:
        """
        请求仲裁理论

        Args:
            conflict: 冲突信息
            question_type: 问题类型
            used_theories: 已使用的理论列表

        Returns:
            推荐的仲裁理论名称，如果没有可用的返回None
        """
        # 获取该问题类型的仲裁理论优先级
        priority_list = self.ARBITRATION_PRIORITY.get(
            question_type,
            self.ARBITRATION_PRIORITY["其他"]
        )

        # 排除已使用的理论（包括冲突双方）
        excluded = set(used_theories)
        excluded.add(conflict.theory_a)
        excluded.add(conflict.theory_b)

        # 找到第一个可用的仲裁理论
        for theory in priority_list:
            if theory not in excluded:
                self.logger.info(f"选择仲裁理论: {theory} (问题类型: {question_type})")
                return theory

        self.logger.warning(f"没有可用的仲裁理论 (问题类型: {question_type})")
        return None

    async def execute_arbitration(
        self,
        conflict: ArbitrationConflictInfo,
        arbitration_theory: str,
        user_input: Dict[str, Any],
        arbitration_result: Dict[str, Any]
    ) -> ArbitrationResult:
        """
        执行仲裁分析

        Args:
            conflict: 冲突信息
            arbitration_theory: 仲裁理论名称
            user_input: 用户输入信息
            arbitration_result: 仲裁理论的计算结果

        Returns:
            仲裁结果
        """
        self.logger.info(f"开始仲裁分析: {arbitration_theory}")

        try:
            # 如果有API管理器，使用AI进行深度分析
            if self.api_manager:
                result = await self._ai_arbitration(
                    conflict, arbitration_theory, user_input, arbitration_result
                )
            else:
                # 使用规则引擎进行仲裁
                result = self._rule_based_arbitration(
                    conflict, arbitration_theory, arbitration_result
                )

            self.logger.info(f"仲裁完成: {result.final_judgment} (置信度: {result.confidence:.2f})")
            return result

        except Exception as e:
            self.logger.error(f"仲裁分析失败: {e}")
            return ArbitrationResult(
                status=ArbitrationStatus.FAILED,
                explanation=f"仲裁分析过程出错: {str(e)}"
            )

    async def _ai_arbitration(
        self,
        conflict: ArbitrationConflictInfo,
        arbitration_theory: str,
        user_input: Dict[str, Any],
        arbitration_result: Dict[str, Any]
    ) -> ArbitrationResult:
        """使用AI进行仲裁分析"""

        prompt = f"""你是一位精通中国传统术数的大师。现在有两个理论对同一问题产生了分歧，需要你作为仲裁者给出判断。

【冲突情况】
- 理论A ({conflict.theory_a}): 判断为「{conflict.judgment_a}」
  理由: {conflict.reason_a}

- 理论B ({conflict.theory_b}): 判断为「{conflict.judgment_b}」
  理由: {conflict.reason_b}

- 冲突程度: {conflict.conflict_level}

【仲裁理论】
使用 {arbitration_theory} 进行仲裁分析

【仲裁理论结果】
{json.dumps(arbitration_result, ensure_ascii=False, indent=2)}

【用户信息】
{json.dumps(user_input, ensure_ascii=False, indent=2)}

请根据仲裁理论的结果，综合分析后给出最终判断：

1. 仲裁理论本身的判断是什么？（吉/凶/平）
2. 仲裁结果更倾向于支持哪个理论？
3. 最终综合判断是什么？
4. 置信度是多少？（0-1之间）
5. 简要解释为什么做出这个判断

请以JSON格式返回：
{{
    "arbitration_judgment": "吉/凶/平",
    "supported_theory": "理论A/理论B/中立",
    "final_judgment": "吉/凶/平",
    "confidence": 0.0-1.0,
    "explanation": "解释..."
}}"""

        response = await self.api_manager.call_api(
            task_type="冲突解决分析",
            prompt=prompt,
            enable_dual_verification=False
        )

        # 解析AI响应
        try:
            # 尝试从响应中提取JSON
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
            else:
                raise ValueError("未找到JSON响应")

            return ArbitrationResult(
                status=ArbitrationStatus.COMPLETED,
                arbitration_theory=arbitration_theory,
                arbitration_judgment=data.get("arbitration_judgment"),
                arbitration_reason=data.get("explanation", ""),
                final_judgment=data.get("final_judgment"),
                confidence=float(data.get("confidence", 0.7)),
                explanation=data.get("explanation", "")
            )

        except Exception as e:
            self.logger.warning(f"解析AI仲裁响应失败: {e}")
            # 降级到规则仲裁
            return self._rule_based_arbitration(
                conflict, arbitration_theory, arbitration_result
            )

    def _rule_based_arbitration(
        self,
        conflict: ArbitrationConflictInfo,
        arbitration_theory: str,
        arbitration_result: Dict[str, Any]
    ) -> ArbitrationResult:
        """基于规则的仲裁"""

        # 从仲裁结果中提取判断
        arb_judgment = self._extract_judgment(arbitration_result)

        # 获取各理论权重
        weight_a = self.THEORY_WEIGHTS.get(conflict.theory_a, 0.7)
        weight_b = self.THEORY_WEIGHTS.get(conflict.theory_b, 0.7)
        weight_arb = self.THEORY_WEIGHTS.get(arbitration_theory, 0.7)

        # 计算加权投票
        votes = {"吉": 0, "凶": 0, "平": 0}

        # 冲突双方投票
        votes[conflict.judgment_a] += weight_a
        votes[conflict.judgment_b] += weight_b

        # 仲裁理论投票（权重加成）
        if arb_judgment:
            votes[arb_judgment] += weight_arb * 1.2  # 仲裁理论有20%加成

        # 确定最终判断
        final_judgment = max(votes, key=votes.get)
        total_weight = sum(votes.values())
        confidence = votes[final_judgment] / total_weight if total_weight > 0 else 0.5

        # 生成解释
        if arb_judgment == final_judgment:
            explanation = f"仲裁理论{arbitration_theory}的判断为「{arb_judgment}」，与{conflict.theory_a if conflict.judgment_a == arb_judgment else conflict.theory_b}一致，综合判断为「{final_judgment}」"
        else:
            explanation = f"仲裁理论{arbitration_theory}判断为「{arb_judgment}」，综合各理论权重后，最终判断为「{final_judgment}」"

        return ArbitrationResult(
            status=ArbitrationStatus.COMPLETED,
            arbitration_theory=arbitration_theory,
            arbitration_judgment=arb_judgment,
            final_judgment=final_judgment,
            confidence=confidence,
            explanation=explanation
        )

    def _extract_judgment(self, result: Dict[str, Any]) -> Optional[str]:
        """从理论结果中提取吉凶判断"""

        # 尝试多种可能的字段名
        for key in ["judgment", "吉凶", "结论", "总结"]:
            if key in result:
                value = str(result[key])
                if "吉" in value:
                    return "吉"
                elif "凶" in value:
                    return "凶"
                elif "平" in value:
                    return "平"

        # 尝试从summary中提取
        summary = result.get("summary", "") or result.get("总结", "")
        if "吉" in summary:
            return "吉"
        elif "凶" in summary:
            return "凶"
        elif "平" in summary:
            return "平"

        return "平"  # 默认返回平

    def should_arbitrate(
        self,
        conflict: ArbitrationConflictInfo,
        threshold: str = "中"
    ) -> bool:
        """
        判断是否需要仲裁

        Args:
            conflict: 冲突信息
            threshold: 仲裁阈值（高/中/低）

        Returns:
            是否需要仲裁
        """
        level_order = {"低": 1, "中": 2, "高": 3}
        conflict_level = level_order.get(conflict.conflict_level, 2)
        threshold_level = level_order.get(threshold, 2)

        return conflict_level >= threshold_level

    def get_arbitration_summary(
        self,
        result: ArbitrationResult
    ) -> str:
        """
        生成仲裁摘要（用于UI展示）

        Args:
            result: 仲裁结果

        Returns:
            摘要文本
        """
        if result.status == ArbitrationStatus.NOT_NEEDED:
            return "无需仲裁"
        elif result.status == ArbitrationStatus.FAILED:
            return f"仲裁失败: {result.explanation}"
        elif result.status == ArbitrationStatus.COMPLETED:
            confidence_text = "高" if result.confidence > 0.7 else "中" if result.confidence > 0.5 else "低"
            return f"仲裁完成 | 使用{result.arbitration_theory} | 判断: {result.final_judgment} | 置信度: {confidence_text}"
        else:
            return f"仲裁状态: {result.status.value}"


# 便捷函数
def create_conflict_info(
    theory_a: str,
    theory_b: str,
    result_a: Dict[str, Any],
    result_b: Dict[str, Any]
) -> ArbitrationConflictInfo:
    """
    从理论结果创建冲突信息

    Args:
        theory_a: 理论A名称
        theory_b: 理论B名称
        result_a: 理论A的结果
        result_b: 理论B的结果

    Returns:
        冲突信息对象
    """
    def extract_judgment(result):
        for key in ["judgment", "吉凶", "结论"]:
            if key in result:
                value = str(result[key])
                if "吉" in value:
                    return "吉"
                elif "凶" in value:
                    return "凶"
        return "平"

    def extract_reason(result):
        for key in ["summary", "reason", "总结", "理由"]:
            if key in result:
                return str(result[key])[:200]
        return "未提供详细理由"

    judgment_a = extract_judgment(result_a)
    judgment_b = extract_judgment(result_b)

    # 判断冲突程度
    if judgment_a == judgment_b:
        conflict_level = "低"
    elif (judgment_a == "吉" and judgment_b == "凶") or (judgment_a == "凶" and judgment_b == "吉"):
        conflict_level = "高"
    else:
        conflict_level = "中"

    return ArbitrationConflictInfo(
        theory_a=theory_a,
        theory_b=theory_b,
        judgment_a=judgment_a,
        judgment_b=judgment_b,
        reason_a=extract_reason(result_a),
        reason_b=extract_reason(result_b),
        conflict_level=conflict_level
    )
