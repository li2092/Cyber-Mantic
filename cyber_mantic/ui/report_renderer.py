"""
智能报告渲染器 - 支持MBTI个性化和专业视觉呈现
"""
from typing import Dict, Any, List, Optional
from models import ComprehensiveReport, TheoryAnalysisResult
from ui.themes import ThemeSystem


class ReportRenderer:
    """报告渲染器 - 将分析结果渲染为精美的Markdown"""

    # MBTI个性化呈现风格
    MBTI_PRESENTATION_STYLES = {
        # NT类型 - 逻辑结构化
        "NT": {
            "structure": "logic_tree",      # 逻辑树状结构
            "icons": "minimal",             # 简约图标
            "emphasis": "data",             # 强调数据
            "section_style": "numbered"     # 数字编号
        },
        # NF类型 - 叙事性
        "NF": {
            "structure": "narrative",       # 叙事结构
            "icons": "rich",                # 丰富图标
            "emphasis": "meaning",          # 强调意义
            "section_style": "story"        # 故事章节
        },
        # SJ类型 - 传统规范
        "SJ": {
            "structure": "traditional",     # 传统结构
            "icons": "standard",            # 标准图标
            "emphasis": "details",          # 强调细节
            "section_style": "formal"       # 正式标题
        },
        # SP类型 - 简洁直接
        "SP": {
            "structure": "bullet",          # 要点式
            "icons": "emoji",               # 表情图标
            "emphasis": "action",           # 强调行动
            "section_style": "casual"       # 轻松标题
        }
    }

    @classmethod
    def get_mbti_group(cls, mbti_type: str) -> str:
        """获取MBTI组别"""
        if not mbti_type or len(mbti_type) < 4:
            return "SJ"  # 默认

        temperament = mbti_type[1:3]  # 提取第2、3个字母

        if temperament in ["NT"]:
            return "NT"
        elif temperament in ["NF"]:
            return "NF"
        elif temperament[0] == "S" and mbti_type[3] == "J":
            return "SJ"
        elif temperament[0] == "S" and mbti_type[3] == "P":
            return "SP"
        else:
            return "SJ"

    @classmethod
    def render_executive_summary(
        cls,
        report: ComprehensiveReport,
        theme: str = "light",
        mbti_type: Optional[str] = None
    ) -> str:
        """
        渲染执行摘要（个性化呈现）

        Args:
            report: 综合报告
            theme: 主题名称
            mbti_type: MBTI类型

        Returns:
            格式化的Markdown文本
        """
        mbti_group = cls.get_mbti_group(mbti_type) if mbti_type else "SJ"
        style = cls.MBTI_PRESENTATION_STYLES[mbti_group]

        # 获取主题配色
        judgment_style = ThemeSystem.get_judgment_style(
            report.theory_results[0].judgment if report.theory_results else "平"
        )

        # 计算综合判断
        overall_judgment = cls._calculate_overall_judgment(report.theory_results)
        overall_style = ThemeSystem.get_judgment_style(overall_judgment)

        markdown = f"""# {overall_style['icon']} 赛博玄数 · 智能分析报告

<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 12px; color: white; margin-bottom: 20px;">

## 📋 报告基本信息

| 项目 | 内容 |
|------|------|
| 📅 **生成时间** | {report.created_at.strftime('%Y年%m月%d日 %H:%M:%S')} |
| 🎯 **问题类别** | {report.user_input_summary.get('question_type', '未知')} |
| 🔮 **使用理论** | {' · '.join(report.selected_theories)} |
| 📊 **综合置信度** | {report.overall_confidence:.1%} {'🟢' if report.overall_confidence >= 0.8 else '🟡' if report.overall_confidence >= 0.6 else '🔴'} |
| 🎭 **个性化设置** | {mbti_type if mbti_type else '通用模式'} |

</div>

---

## {overall_style['icon']} 核心结论

<div style="background-color: {overall_style['bg']}; border-left: 5px solid {overall_style['color']}; padding: 15px; border-radius: 8px; margin: 15px 0;">

### 综合判断：**{overall_judgment}** {overall_style['icon']}

{report.executive_summary}

</div>

"""

        # 根据MBTI个性化添加不同的补充信息
        if style["emphasis"] == "data":
            # NT类型 - 强调数据分析
            markdown += cls._render_data_analysis(report)
        elif style["emphasis"] == "meaning":
            # NF类型 - 强调深层含义
            markdown += cls._render_meaning_insights(report)
        elif style["emphasis"] == "details":
            # SJ类型 - 强调详细信息
            markdown += cls._render_detailed_breakdown(report)
        elif style["emphasis"] == "action":
            # SP类型 - 强调行动要点
            markdown += cls._render_action_points(report)

        # 添加局限性说明
        if report.limitations:
            markdown += f"""
---

## ⚠️ 预测局限性说明

"""
            for limitation in report.limitations:
                markdown += f"- {limitation}\n"

        return markdown

    @classmethod
    def _calculate_overall_judgment(cls, theory_results: List[TheoryAnalysisResult]) -> str:
        """计算综合判断"""
        if not theory_results:
            return "平"

        # 加权平均
        total_score = 0
        total_weight = 0

        judgment_values = {"大吉": 1.0, "吉": 0.7, "平": 0.5, "凶": 0.3, "大凶": 0.0}

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
    def _render_data_analysis(cls, report: ComprehensiveReport) -> str:
        """NT类型 - 数据分析视图"""
        markdown = """
---

## 📊 量化分析视图

<div style="background-color: #F3F4F6; padding: 15px; border-radius: 8px;">

### 理论结果分布

"""
        # 统计各理论的判断分布
        judgment_dist = {}
        for result in report.theory_results:
            judgment_dist[result.judgment] = judgment_dist.get(result.judgment, 0) + 1

        total = len(report.theory_results)
        for judgment, count in sorted(judgment_dist.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total) * 100
            style = ThemeSystem.get_judgment_style(judgment)
            bar = "█" * int(percentage / 5)  # 每5%一个方块
            markdown += f"- **{judgment}** {style['icon']}: {count}个理论 ({percentage:.0f}%) `{bar}`\n"

        markdown += """
### 置信度分析

"""
        # 计算置信度统计
        confidences = [r.confidence for r in report.theory_results]
        if confidences:
            avg_conf = sum(confidences) / len(confidences)
            max_conf = max(confidences)
            min_conf = min(confidences)

            markdown += f"""
- **平均置信度**: {avg_conf:.1%}
- **最高置信度**: {max_conf:.1%}
- **最低置信度**: {min_conf:.1%}
- **标准差**: {cls._calculate_std(confidences):.3f}
"""

        markdown += "\n</div>\n"
        return markdown

    @classmethod
    def _render_meaning_insights(cls, report: ComprehensiveReport) -> str:
        """NF类型 - 深层洞察视图"""
        markdown = """
---

## 💫 深层洞察

<div style="background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%); padding: 15px; border-radius: 8px; border: 2px solid #667eea30;">

### 🌟 共识与分歧

"""
        # 分析理论间的共识
        if report.conflict_info and not report.conflict_info.has_conflict:
            markdown += """
各理论结果达成高度共识，这暗示着命运的趋势较为明确。当多个理论从不同角度得出相似结论时，其预示性更为可靠。

"""
        elif report.conflict_info and report.conflict_info.has_conflict:
            markdown += f"""
检测到{len(report.conflict_info.conflicts)}处理论分歧，这反映了事物发展的多面性。不同理论从各自视角揭示了不同的可能性，建议综合考量。

"""

        # 添加哲学性思考
        markdown += """
### 🔮 哲学思考

命理分析揭示的是可能性与趋势，而非绝对的宿命。每个人都拥有通过自身努力改变命运走向的力量。这份分析旨在提供洞察，帮助您做出更明智的选择。

</div>

"""
        return markdown

    @classmethod
    def _render_detailed_breakdown(cls, report: ComprehensiveReport) -> str:
        """SJ类型 - 详细分解视图"""
        markdown = """
---

## 📋 详细信息分解

<div style="background-color: #FAFAFA; padding: 15px; border-radius: 8px; border: 1px solid #E0E0E0;">

### 理论分析明细表

| 序号 | 理论名称 | 判断结果 | 程度 | 置信度 |
|:----:|:--------|:--------:|:----:|:------:|
"""
        for idx, result in enumerate(report.theory_results, 1):
            style = ThemeSystem.get_judgment_style(result.judgment)
            level_bar = "●" * int(result.judgment_level * 5)  # 5颗星制
            conf_bar = "▰" * int(result.confidence * 10)  # 10格制

            markdown += f"| {idx} | {result.theory_name} | {result.judgment} {style['icon']} | {level_bar} | {conf_bar} |\n"

        markdown += """
### 关键信息汇总

"""
        # 汇总各理论的关键建议
        for result in report.theory_results:
            if result.advice:
                markdown += f"- **{result.theory_name}**: {result.advice}\n"

        markdown += "\n</div>\n"
        return markdown

    @classmethod
    def _render_action_points(cls, report: ComprehensiveReport) -> str:
        """SP类型 - 行动要点视图"""
        markdown = """
---

## 🎯 核心要点速览

<div style="background-color: #FFF8E1; padding: 15px; border-radius: 8px; border-left: 5px solid #FFC107;">

### ⚡ 立即可行的建议

"""
        # 提取可行动的建议
        action_count = 0
        for result in report.theory_results:
            if result.advice and action_count < 5:  # 最多显示5条
                markdown += f"{action_count + 1}. **{result.theory_name}**: {result.advice}\n\n"
                action_count += 1

        if action_count == 0:
            markdown += "各理论的详细建议请参见完整分析报告。\n\n"

        markdown += """
### ✅ 行动清单

- [ ] 仔细阅读各理论的详细分析
- [ ] 根据建议制定具体行动计划
- [ ] 定期回顾并调整策略
- [ ] 保持积极心态，主动创造机会

</div>

"""
        return markdown

    @classmethod
    def render_theory_details(
        cls,
        theory_results: List[TheoryAnalysisResult],
        mbti_type: Optional[str] = None
    ) -> str:
        """
        渲染各理论详细分析

        Args:
            theory_results: 理论结果列表
            mbti_type: MBTI类型

        Returns:
            格式化的Markdown文本
        """
        mbti_group = cls.get_mbti_group(mbti_type) if mbti_type else "SJ"

        markdown = "# 🔮 各理论详细分析\n\n"

        for idx, result in enumerate(theory_results, 1):
            style = ThemeSystem.get_judgment_style(result.judgment)

            markdown += f"""
---

## {idx}. {result.theory_name} {style['icon']}

<div style="background-color: {style['bg']}; border-left: 5px solid {style['color']}; padding: 15px; border-radius: 8px; margin: 15px 0;">

### 📊 核心判断

| 项目 | 结果 |
|------|------|
| **吉凶判断** | **{result.judgment}** {style['icon']} |
| **程度等级** | {'★' * int(result.judgment_level * 5)}{'☆' * (5 - int(result.judgment_level * 5))} ({result.judgment_level:.2f}) |
| **置信度** | {'▰' * int(result.confidence * 10)}{'▱' * (10 - int(result.confidence * 10))} ({result.confidence:.1%}) |

</div>

### 📖 详细解读

{result.interpretation}

"""
            # 如果有时机预测
            if result.timing:
                markdown += f"""
### ⏰ 时机分析

{result.timing}

"""

            # 分隔线
            if idx < len(theory_results):
                markdown += "\n"

        return markdown

    @classmethod
    def render_conflict_analysis(cls, report: ComprehensiveReport) -> str:
        """渲染冲突分析"""
        if not report.conflict_info or not report.conflict_info.has_conflict:
            return """
# ✅ 理论一致性分析

<div style="background-color: #E8F5E9; border-left: 5px solid #4CAF50; padding: 15px; border-radius: 8px;">

## 🎉 高度共识

各理论分析结果达成高度一致，未检测到显著冲突。这表明预测结果的可靠性较高。

</div>
"""

        markdown = f"""
# ⚖️ 理论差异分析

<div style="background-color: #FFF3E0; border-left: 5px solid #FF9800; padding: 15px; border-radius: 8px;">

## 📊 冲突概览

检测到 **{len(report.conflict_info.conflicts)}** 处理论差异。

"""

        # 按级别分类冲突
        level_groups = {}
        for conflict in report.conflict_info.conflicts:
            level = conflict.get("level", 2)
            if level not in level_groups:
                level_groups[level] = []
            level_groups[level].append(conflict)

        for level in sorted(level_groups.keys(), reverse=True):
            conflicts = level_groups[level]
            level_name = {4: "严重冲突", 3: "显著差异", 2: "微小差异"}.get(level, "差异")
            level_icon = {4: "🔴", 3: "🟡", 2: "🟢"}.get(level, "⚪")

            markdown += f"\n### {level_icon} {level_name} ({len(conflicts)}处)\n\n"

            for conflict in conflicts:
                markdown += f"- {conflict.get('details', '未知冲突')}\n"

        markdown += "\n</div>\n"

        # 添加解决方案
        if report.conflict_info.resolution:
            resolution = report.conflict_info.resolution
            markdown += f"""

## 🔧 调和方案

**策略**: {resolution.get('总体策略', '综合分析')}

**建议**:

"""
            for recommendation in resolution.get('建议', []):
                markdown += f"- {recommendation}\n"

        return markdown

    @classmethod
    def _calculate_std(cls, values: List[float]) -> float:
        """计算标准差"""
        if not values:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
