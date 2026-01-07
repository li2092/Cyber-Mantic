"""
ExportService - 导出服务

支持多种格式的报告导出
"""

import json
from pathlib import Path
from typing import Optional, List
from models import ComprehensiveReport
from utils.pdf_exporter import PDFExporter
from utils.logger import get_logger


class ExportService:
    """导出服务"""

    def __init__(self):
        self.pdf_exporter = PDFExporter()
        self.logger = get_logger(__name__)

    def export_to_json(
        self,
        report: ComprehensiveReport,
        output_path: str
    ) -> bool:
        """
        导出为JSON格式

        Args:
            report: 报告对象
            output_path: 输出路径

        Returns:
            是否成功
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)

            self.logger.info(f"JSON导出成功: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"JSON导出失败: {e}")
            return False

    def export_to_pdf(
        self,
        report: ComprehensiveReport,
        output_path: str,
        include_details: bool = True
    ) -> bool:
        """
        导出为PDF格式

        Args:
            report: 报告对象
            output_path: 输出路径
            include_details: 是否包含详细分析

        Returns:
            是否成功
        """
        try:
            success = self.pdf_exporter.export_report(
                report,
                output_path,
                include_details
            )

            if success:
                self.logger.info(f"PDF导出成功: {output_path}")
            else:
                self.logger.error("PDF导出失败")

            return success

        except Exception as e:
            self.logger.error(f"PDF导出失败: {e}")
            return False

    def export_to_markdown(
        self,
        report: ComprehensiveReport,
        output_path: str
    ) -> bool:
        """
        导出为Markdown格式

        Args:
            report: 报告对象
            output_path: 输出路径

        Returns:
            是否成功
        """
        try:
            # 生成Markdown内容
            markdown = self._generate_markdown(report)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown)

            self.logger.info(f"Markdown导出成功: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Markdown导出失败: {e}")
            return False

    def _generate_markdown(self, report: ComprehensiveReport) -> str:
        """生成Markdown格式报告"""
        markdown = f"""# 赛博玄数分析报告

**报告ID**: {report.report_id}
**生成时间**: {report.created_at.strftime('%Y年%m月%d日 %H:%M:%S')}

---

## 📋 基本信息

- **问题类型**: {report.user_input_summary.get('question_type', '未知')}
- **问题描述**: {report.user_input_summary.get('question_description', '')}
- **使用理论**: {', '.join(report.selected_theories)}
- **综合置信度**: {report.overall_confidence:.0%}

---

## 📊 执行摘要

{report.executive_summary}

---

## 📝 详细分析

{report.detailed_analysis if report.detailed_analysis else '（无）'}

---

## ⏮️ 过去三年回顾

{report.retrospective_analysis if report.retrospective_analysis else '（无）'}

---

## ⏭️ 未来两年趋势

{report.predictive_analysis if report.predictive_analysis else '（无）'}

---

## 💡 行动建议

"""

        # 添加建议列表
        if report.comprehensive_advice:
            for i, advice in enumerate(report.comprehensive_advice, 1):
                priority = advice.get('priority', '中')
                content = advice.get('content', '')
                markdown += f"{i}. **{priority}优先级**: {content}\n"
        else:
            markdown += "（无）\n"

        markdown += "\n---\n\n## 🔍 各理论详细分析\n\n"

        # 添加各理论结果
        for i, result in enumerate(report.theory_results, 1):
            markdown += f"""### {i}. {result.theory_name}

**判断**: {result.judgment} （置信度: {result.confidence:.0%}）

{result.interpretation}

---

"""

        # 添加局限性
        markdown += "## ⚠️ 局限性说明\n\n"
        for i, limitation in enumerate(report.limitations, 1):
            markdown += f"{i}. {limitation}\n"

        markdown += "\n---\n\n*此报告由赛博玄数系统生成，仅供参考。*\n"

        return markdown

    def get_supported_formats(self) -> List[str]:
        """获取支持的导出格式"""
        return ["json", "pdf", "markdown"]

    def suggest_filename(
        self,
        report: ComprehensiveReport,
        format: str = "pdf"
    ) -> str:
        """
        建议文件名

        Args:
            report: 报告对象
            format: 格式（json/pdf/markdown）

        Returns:
            建议的文件名
        """
        # 生成时间戳
        timestamp = report.created_at.strftime('%Y%m%d_%H%M%S')

        # 问题类型
        question_type = report.user_input_summary.get('question_type', '分析')

        # 报告ID前8位
        report_id_short = report.report_id[:8]

        filename = f"赛博玄数_{question_type}_{timestamp}_{report_id_short}.{format}"

        return filename
