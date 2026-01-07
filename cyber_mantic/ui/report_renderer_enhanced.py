"""
增强版报告渲染器 - 充实基础内容，专注专业性

取消MBTI个性化和吉凶配色，专注于：
1. 完整的信息呈现
2. 清晰的结构组织
3. 专业的数据可视化
4. 实用的行动建议
"""
from typing import List, Optional
from models import ComprehensiveReport, TheoryAnalysisResult


class ReportRenderer:
    """增强版报告渲染器"""

    @classmethod
    def render_executive_summary(
        cls,
        report: ComprehensiveReport,
        ai_generated_summary: str
    ) -> str:
        """
        渲染执行摘要（使用AI生成的摘要）

        Args:
            report: 综合报告
            ai_generated_summary: AI智能助手生成的摘要

        Returns:
            格式化的Markdown文本
        """
        # 计算综合判断
        overall_judgment = cls._calculate_overall_judgment(report.theory_results)

        markdown = f"""# 📊 赛博玄数 · 智能分析报告

---

## 基本信息

| 项目 | 内容 |
|------|------|
| **📅 生成时间** | {report.created_at.strftime('%Y年%m月%d日 %H:%M:%S')} |
| **🎯 问题类别** | {report.user_input_summary.get('question_type', '未知')} |
| **🔮 使用理论** | {' · '.join(report.selected_theories)} ({len(report.selected_theories)}个) |
| **📊 综合置信度** | {report.overall_confidence:.1%} {cls._get_confidence_indicator(report.overall_confidence)} |
| **⚖️ 综合判断** | **{overall_judgment}** |

---

## 核心摘要

{ai_generated_summary}

---

## 理论共识度分析

{cls._render_theory_consensus(report.theory_results)}

"""

        # 添加局限性说明（如果有）
        if report.limitations:
            markdown += f"""
---

## ⚠️ 预测局限性说明

"""
            for limitation in report.limitations:
                markdown += f"- {limitation}\n"

        # 添加免责声明
        markdown += """
---

## 📋 使用说明

1. 本报告由AI系统基于传统命理理论生成，仅供参考
2. 命理分析揭示的是趋势和可能性，而非绝对宿命
3. 请结合实际情况理性判断，不要过度依赖
4. 建议将报告作为决策参考之一，而非唯一依据
5. 如有疑问，欢迎咨询专业人士

"""

        return markdown

    @classmethod
    def render_theory_details(
        cls,
        theory_results: List[TheoryAnalysisResult]
    ) -> str:
        """
        渲染各理论详细分析

        Args:
            theory_results: 理论结果列表

        Returns:
            格式化的Markdown文本
        """
        markdown = "# 🔮 各理论详细分析\n\n"

        for idx, result in enumerate(theory_results, 1):
            markdown += f"""
---

## {idx}. {result.theory_name}

### 核心判断

| 项目 | 结果 |
|------|------|
| **吉凶判断** | **{result.judgment}** |
| **程度等级** | {cls._render_level_stars(result.judgment_level)} ({result.judgment_level:.2f}) |
| **置信度** | {cls._render_confidence_bar(result.confidence)} ({result.confidence:.1%}) |

### 详细解读

{result.interpretation}

"""
            # 如果有时机分析
            if result.timing:
                markdown += f"""
### ⏰ 时机分析

{result.timing}

"""

            # 如果有建议
            if result.advice:
                markdown += f"""
### 💡 专业建议

{result.advice}

"""

        return markdown

    @classmethod
    def render_actionable_advice(
        cls,
        advice_list: List[dict]
    ) -> str:
        """
        渲染可执行的行动建议

        Args:
            advice_list: AI生成的建议列表

        Returns:
            格式化的Markdown文本
        """
        if not advice_list:
            return ""

        markdown = """# 🎯 行动建议

以下是根据分析结果生成的具体行动建议：

---

"""

        # 按优先级分组
        priority_groups = {"高": [], "中": [], "低": []}
        for advice in advice_list:
            priority = advice.get("priority", "中")
            if priority in priority_groups:
                priority_groups[priority].append(advice["content"])

        # 渲染高优先级
        if priority_groups["高"]:
            markdown += "## 🔴 高优先级（立即执行）\n\n"
            for content in priority_groups["高"]:
                markdown += f"- {content}\n"
            markdown += "\n"

        # 渲染中优先级
        if priority_groups["中"]:
            markdown += "## 🟡 中优先级（近期完成）\n\n"
            for content in priority_groups["中"]:
                markdown += f"- {content}\n"
            markdown += "\n"

        # 渲染低优先级
        if priority_groups["低"]:
            markdown += "## 🟢 低优先级（有条件时考虑）\n\n"
            for content in priority_groups["低"]:
                markdown += f"- {content}\n"
            markdown += "\n"

        # 添加执行建议
        markdown += """
---

## 📝 执行建议

1. **先从高优先级开始**：优先完成标记为"高优先级"的行动
2. **制定具体计划**：为每条建议设定明确的时间节点和成功标准
3. **定期回顾**：每周回顾进展，及时调整策略
4. **保持记录**：记录执行过程和结果，方便后续对比分析
5. **灵活应变**：根据实际情况调整，不必拘泥于原计划

"""

        return markdown

    @classmethod
    def render_conflict_analysis(cls, report: ComprehensiveReport) -> str:
        """渲染冲突分析"""
        if not report.conflict_info or not report.conflict_info.has_conflict:
            return """
# ✅ 理论一致性分析

## 高度共识

各理论分析结果达成高度一致，未检测到显著冲突。这表明预测结果的可靠性较高。

### 一致性指标

- ✅ 理论共识度：高
- ✅ 结果可信度：高
- ✅ 预测稳定性：好

"""

        markdown = f"""
# ⚖️ 理论差异分析

## 差异概览

检测到 **{len(report.conflict_info.conflicts)}** 处理论差异，这是正常现象。不同理论从各自的视角分析问题，出现差异反映了事物的多面性。

"""

        # 按级别分类冲突
        level_groups = {4: [], 3: [], 2: []}
        for conflict in report.conflict_info.conflicts:
            level = conflict.get("level", 2)
            if level in level_groups:
                level_groups[level].append(conflict)

        # 渲染严重冲突
        if level_groups[4]:
            markdown += f"\n### 🔴 严重差异 ({len(level_groups[4])}处)\n\n"
            for conflict in level_groups[4]:
                markdown += f"- {conflict.get('details', '未知冲突')}\n"

        # 渲染显著差异
        if level_groups[3]:
            markdown += f"\n### 🟡 显著差异 ({len(level_groups[3])}处)\n\n"
            for conflict in level_groups[3]:
                markdown += f"- {conflict.get('details', '未知冲突')}\n"

        # 渲染微小差异
        if level_groups[2]:
            markdown += f"\n### 🟢 微小差异 ({len(level_groups[2])}处)\n\n"
            for conflict in level_groups[2]:
                markdown += f"- {conflict.get('details', '未知冲突')}\n"

        # 添加解决方案
        if report.conflict_info.resolution:
            resolution = report.conflict_info.resolution
            markdown += f"""

---

## 调和方案

**策略**: {resolution.get('总体策略', '综合分析')}

### 处理建议

"""
            for recommendation in resolution.get('建议', []):
                markdown += f"- {recommendation}\n"

        markdown += """

---

## 如何看待差异

1. **差异是正常的**：不同理论有不同侧重点，差异反映多元视角
2. **重视共识**：多个理论一致的结论往往更可靠
3. **综合判断**：参考调和方案，做出平衡的决策
4. **动态调整**：随着情况变化，可以重新分析

"""

        return markdown

    @classmethod
    def _calculate_overall_judgment(cls, theory_results: List[TheoryAnalysisResult]) -> str:
        """计算综合判断"""
        if not theory_results:
            return "未知"

        judgment_values = {"大吉": 1.0, "吉": 0.7, "平": 0.5, "凶": 0.3, "大凶": 0.0}

        total_score = 0
        total_weight = 0

        for result in theory_results:
            value = judgment_values.get(result.judgment, 0.5)
            weight = result.confidence
            total_score += value * weight
            total_weight += weight

        if total_weight == 0:
            return "平"

        avg_score = total_score / total_weight

        if avg_score >= 0.85:
            return "大吉"
        elif avg_score >= 0.65:
            return "吉"
        elif avg_score >= 0.35:
            return "平"
        elif avg_score >= 0.15:
            return "凶"
        else:
            return "大凶"

    @classmethod
    def _render_theory_consensus(cls, theory_results: List[TheoryAnalysisResult]) -> str:
        """渲染理论共识度分析"""
        if not theory_results:
            return "无理论结果"

        # 统计各判断的数量
        judgment_count = {}
        for result in theory_results:
            judgment = result.judgment
            judgment_count[judgment] = judgment_count.get(judgment, 0) + 1

        total = len(theory_results)

        # 生成分布文本
        markdown = "各理论判断分布：\n\n"

        for judgment in ["大吉", "吉", "平", "凶", "大凶"]:
            if judgment in judgment_count:
                count = judgment_count[judgment]
                percentage = (count / total) * 100
                bar_length = int(percentage / 5)  # 每5%一个方块
                bar = "█" * bar_length
                markdown += f"- **{judgment}**: {count}个理论 ({percentage:.0f}%) `{bar}`\n"

        # 计算共识度
        if judgment_count:
            max_count = max(judgment_count.values())
            consensus_rate = (max_count / total) * 100
            markdown += f"\n**共识度**: {consensus_rate:.0f}% "

            if consensus_rate >= 80:
                markdown += "（高度共识 ✅）"
            elif consensus_rate >= 60:
                markdown += "（基本共识 🟡）"
            else:
                markdown += "（存在分歧 ⚠️）"

        return markdown

    @classmethod
    def _render_level_stars(cls, level: float) -> str:
        """渲染程度星级"""
        stars = int(level * 5)
        return "★" * stars + "☆" * (5 - stars)

    @classmethod
    def _render_confidence_bar(cls, confidence: float) -> str:
        """渲染置信度进度条"""
        bars = int(confidence * 10)
        return "▰" * bars + "▱" * (10 - bars)

    @classmethod
    def _get_confidence_indicator(cls, confidence: float) -> str:
        """获取置信度指示器"""
        if confidence >= 0.8:
            return "🟢 高"
        elif confidence >= 0.6:
            return "🟡 中"
        else:
            return "🔴 低"

    @classmethod
    def render_retrospective_analysis(cls, retrospective_text: str) -> str:
        """
        渲染过去三年回顾分析

        Args:
            retrospective_text: AI生成的回顾分析文本

        Returns:
            格式化的Markdown文本
        """
        if not retrospective_text:
            return ""

        # 动态计算过去三年
        from datetime import datetime
        current_year = datetime.now().year
        year_range = f"{current_year - 3}-{current_year - 1}"

        markdown = f"""# ⏮️ 过去三年回顾（{year_range}）

{retrospective_text}

---

## 📌 回顾说明

1. **验证性质**：此回顾分析旨在验证命理分析的准确性
2. **记忆对照**：请回想过去三年的实际经历，对照分析结果
3. **趋势理解**：通过回顾帮助您更好地理解命理趋势规律
4. **参考价值**：如果回顾与实际经历吻合度高，可增强对未来预测的参考价值

"""
        return markdown

    @classmethod
    def render_predictive_analysis(cls, predictive_text: str) -> str:
        """
        渲染未来两年趋势分析

        Args:
            predictive_text: AI生成的趋势分析文本

        Returns:
            格式化的Markdown文本
        """
        if not predictive_text:
            return ""

        # 动态计算未来两年
        from datetime import datetime
        current_year = datetime.now().year
        year_range = f"{current_year}-{current_year + 1}"

        markdown = f"""# ⏭️ 未来两年趋势（{year_range}）

{predictive_text}

---

## ⚠️ 预测说明

1. **趋势性质**：此为趋势分析，而非确定性预测
2. **概率思维**：预测显示的是可能性和倾向，而非绝对结果
3. **主动性**：您的选择和行动会影响最终结果
4. **灵活调整**：根据实际情况灵活调整策略，不必拘泥
5. **决定权**：最终决定权始终在您手中

"""
        return markdown
