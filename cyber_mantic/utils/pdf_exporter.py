"""
PDF导出功能 - 使用reportlab生成专业PDF报告
"""
from typing import Optional
from datetime import datetime
from models import ComprehensiveReport
from utils.logger import get_logger


class PDFExporter:
    """PDF导出器"""

    def __init__(self):
        self.logger = get_logger()

    def export_report(
        self,
        report: ComprehensiveReport,
        output_path: str,
        include_details: bool = True
    ) -> bool:
        """
        导出报告为PDF

        Args:
            report: 综合报告
            output_path: 输出文件路径
            include_details: 是否包含详细分析

        Returns:
            是否成功
        """
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer, PageBreak,
                Table, TableStyle, Image
            )
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

        except ImportError:
            self.logger.error("reportlab未安装，无法导出PDF")
            raise ImportError(
                "PDF导出需要安装reportlab库\n\n"
                "请运行: pip install reportlab"
            )

        self.logger.info(f"开始导出PDF到: {output_path}")

        try:
            # 注册中文字体
            chinese_font = self._register_chinese_font(pdfmetrics, TTFont)

            # 创建PDF文档
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18,
            )

            # 样式
            styles = getSampleStyleSheet()

            # 自定义样式（优化字体大小和间距）
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontName=chinese_font,
                fontSize=26,  # 标题调大：24→26
                textColor=colors.HexColor('#2E5266'),
                spaceAfter=36,  # 增加标题后间距
                alignment=TA_CENTER
            )

            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontName=chinese_font,
                fontSize=18,  # 小标题调大：16→18
                textColor=colors.HexColor('#2E5266'),
                spaceAfter=16,  # 增加小标题后间距：12→16
                spaceBefore=20  # 增加小标题前间距：12→20
            )

            body_style = ParagraphStyle(
                'CustomBody',
                parent=styles['Normal'],
                fontName=chinese_font,
                fontSize=13,  # 正文调大：11→13
                leading=22,   # 增加行距：18→22（更舒适的阅读体验）
                alignment=TA_JUSTIFY,
                spaceAfter=6  # 新增：段落后间距
            )

            # 构建内容
            story = []

            # 标题
            story.append(Paragraph("赛博玄数 · 智能分析报告", title_style))
            story.append(Spacer(1, 0.2 * inch))

            # 基本信息表格
            basic_info = [
                ["报告编号", report.report_id[:16]],
                ["生成时间", report.created_at.strftime('%Y年%m月%d日 %H:%M:%S')],
                ["问题类别", report.user_input_summary.get('question_type', '未知')],
                ["使用理论", '、'.join(report.selected_theories)],
                ["综合置信度", f"{report.overall_confidence:.1%}"],
            ]

            info_table = Table(basic_info, colWidths=[2 * inch, 4 * inch])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E8E8E8')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), chinese_font),
                ('FONTSIZE', (0, 0), (-1, -1), 11),  # 基本信息表格字体调大：10→11
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),  # 增加内边距：8→10
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#D0D0D0'))
            ]))

            story.append(info_table)
            story.append(Spacer(1, 0.4 * inch))  # 增加间距：0.3→0.4

            # 执行摘要
            story.append(Paragraph("执行摘要", heading_style))
            summary_para = Paragraph(
                self._clean_text_for_pdf(report.executive_summary),
                body_style
            )
            story.append(summary_para)
            story.append(Spacer(1, 0.3 * inch))  # 增加间距：0.2→0.3

            # 详细分析（报告主要内容）
            if report.detailed_analysis:
                story.append(Paragraph("详细分析", heading_style))
                detailed_para = Paragraph(
                    self._clean_text_for_pdf(report.detailed_analysis),
                    body_style
                )
                story.append(detailed_para)
                story.append(Spacer(1, 0.3 * inch))  # 增加间距：0.2→0.3

            # 过去三年回顾（如适用）
            if report.retrospective_analysis:
                story.append(Paragraph("过去三年回顾", heading_style))
                retro_para = Paragraph(
                    self._clean_text_for_pdf(report.retrospective_analysis),
                    body_style
                )
                story.append(retro_para)
                story.append(Spacer(1, 0.3 * inch))  # 增加间距：0.2→0.3

            # 未来两年趋势（如适用）
            if report.predictive_analysis:
                story.append(Paragraph("未来两年趋势", heading_style))
                pred_para = Paragraph(
                    self._clean_text_for_pdf(report.predictive_analysis),
                    body_style
                )
                story.append(pred_para)
                story.append(Spacer(1, 0.3 * inch))  # 增加间距：0.2→0.3

            # 行动建议
            if report.comprehensive_advice:
                story.append(Paragraph("行动建议", heading_style))
                for idx, advice in enumerate(report.comprehensive_advice, 1):
                    priority = advice.get('priority', '中')
                    content = advice.get('content', '')
                    advice_text = f"{idx}. 【{priority}优先级】 {content}"
                    advice_para = Paragraph(
                        self._clean_text_for_pdf(advice_text),
                        body_style
                    )
                    story.append(advice_para)
                    story.append(Spacer(1, 0.08 * inch))  # 新增：建议条目之间的小间距
                story.append(Spacer(1, 0.2 * inch))

            # 各理论分析
            if include_details:
                story.append(PageBreak())
                story.append(Paragraph("各理论详细分析", heading_style))
                story.append(Spacer(1, 0.2 * inch))  # 增加间距：0.1→0.2

                for idx, result in enumerate(report.theory_results, 1):
                    # 理论名称
                    theory_title = f"{idx}. {result.theory_name}"
                    story.append(Paragraph(theory_title, heading_style))

                    # 核心判断表格
                    judgment_data = [
                        ["吉凶判断", result.judgment],
                        ["程度等级", f"{result.judgment_level:.2f}"],
                        ["置信度", f"{result.confidence:.1%}"]
                    ]

                    judgment_table = Table(judgment_data, colWidths=[1.5 * inch, 4.5 * inch])
                    judgment_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F0F0F0')),
                        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, -1), chinese_font),
                        ('FONTSIZE', (0, 0), (-1, -1), 10),  # 表格字体调大：9→10
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),  # 增加表格内边距：6→8
                        ('TOPPADDING', (0, 0), (-1, -1), 8),
                        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#D0D0D0'))
                    ]))

                    story.append(judgment_table)
                    story.append(Spacer(1, 0.15 * inch))  # 增加间距：0.1→0.15

                    # 详细解读
                    interpretation_para = Paragraph(
                        self._clean_text_for_pdf(result.interpretation),
                        body_style
                    )
                    story.append(interpretation_para)
                    story.append(Spacer(1, 0.3 * inch))  # 增加间距：0.2→0.3

                    # 如果不是最后一个理论，添加分隔线
                    if idx < len(report.theory_results):
                        story.append(Spacer(1, 0.15 * inch))  # 增加间距：0.1→0.15

            # 局限性说明
            if report.limitations:
                story.append(PageBreak())
                story.append(Paragraph("预测局限性说明", heading_style))
                for limitation in report.limitations:
                    limitation_para = Paragraph(
                        f"• {self._clean_text_for_pdf(limitation)}",
                        body_style
                    )
                    story.append(limitation_para)
                story.append(Spacer(1, 0.1 * inch))

            # 免责声明
            story.append(Spacer(1, 0.3 * inch))  # 增加间距：0.2→0.3
            disclaimer_style = ParagraphStyle(
                'Disclaimer',
                parent=body_style,
                fontSize=10,  # 免责声明字体调大：9→10（虽然是小字，但也要清晰）
                textColor=colors.grey,
                leading=16  # 增加行距
            )
            disclaimer_text = (
                "免责声明：本报告由AI系统生成，仅供参考。命理分析揭示的是趋势和可能性，"
                "而非绝对的宿命。请结合实际情况理性判断，不要过度依赖。"
            )
            story.append(Paragraph(disclaimer_text, disclaimer_style))

            # 生成PDF
            doc.build(story)

            self.logger.info(f"PDF导出成功: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"PDF导出失败: {e}")
            raise e

    def _clean_text_for_pdf(self, text: str) -> str:
        """
        清理文本，移除Markdown标记，准备PDF输出

        处理流程：
        1. 移除Markdown格式符号
        2. 转换列表格式
        3. 转义XML特殊字符
        4. 将换行符转换为HTML <br/>标签（关键！）
        """
        if not text:
            return ""

        # 移除Markdown标题符号
        text = text.replace('###', '').replace('##', '').replace('#', '')

        # 移除Markdown粗体符号
        text = text.replace('**', '')

        # 移除Markdown列表符号（保留缩进）
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            # 处理无序列表
            if line.strip().startswith('- '):
                cleaned_lines.append('  • ' + line.strip()[2:])
            elif line.strip().startswith('* '):
                cleaned_lines.append('  • ' + line.strip()[2:])
            # 处理有序列表
            elif line.strip() and line.strip()[0].isdigit() and '. ' in line:
                cleaned_lines.append('  ' + line.strip())
            else:
                cleaned_lines.append(line)

        text = '\n'.join(cleaned_lines)

        # 【关键修复】先将换行符转换为HTML换行标签，再转义其他特殊字符
        # 这样可以保证<br/>标签不被转义，能被reportlab正确识别
        # 步骤：
        # 1. 先将\n替换为特殊占位符（避免被后续处理影响）
        # 2. 转义XML特殊字符
        # 3. 将占位符替换为<br/>标签

        NEWLINE_PLACEHOLDER = '___NEWLINE_PLACEHOLDER___'
        text = text.replace('\n', NEWLINE_PLACEHOLDER)

        # 转义XML特殊字符（原文中的<>等会被转义为&lt;等，不会影响我们的<br/>）
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')

        # 将占位符替换为真正的<br/>标签（这些不会被转义）
        text = text.replace(NEWLINE_PLACEHOLDER, '<br/>')

        return text.strip()

    def _register_chinese_font(self, pdfmetrics, TTFont) -> str:
        """
        注册中文字体，尝试多个字体路径和字体文件

        Args:
            pdfmetrics: ReportLab的pdfmetrics模块
            TTFont: ReportLab的TTFont类

        Returns:
            str: 成功注册的字体名称，失败则返回'Helvetica'
        """
        import os
        import platform

        # 定义不同操作系统的字体路径
        system = platform.system()
        font_paths = []

        if system == "Windows":
            font_paths = [
                "C:/Windows/Fonts/",
                os.path.expanduser("~/AppData/Local/Microsoft/Windows/Fonts/")
            ]
        elif system == "Darwin":  # macOS
            font_paths = [
                "/Library/Fonts/",
                "/System/Library/Fonts/",
                os.path.expanduser("~/Library/Fonts/")
            ]
        else:  # Linux
            font_paths = [
                "/usr/share/fonts/truetype/",
                "/usr/share/fonts/opentype/",
                "/usr/local/share/fonts/",
                os.path.expanduser("~/.fonts/"),
                "/usr/share/fonts/truetype/noto/",
                "/usr/share/fonts/opentype/noto/",
                "/usr/share/fonts/truetype/wqy/",
                "/usr/share/fonts/truetype/arphic/"
            ]

        # 常见中文字体文件名（优先级从高到低）
        font_files = [
            # Windows 常用字体
            ("SimSun.ttf", "SimSun"),           # 宋体
            ("SimSun.ttc", "SimSun"),           # 宋体（TTC格式）
            ("SimHei.ttf", "SimHei"),           # 黑体
            ("msyh.ttf", "Microsoft-YaHei"),    # 微软雅黑
            ("msyhbd.ttf", "Microsoft-YaHei"),  # 微软雅黑粗体

            # macOS 常用字体
            ("PingFang.ttc", "PingFang-SC"),    # 苹方
            ("Songti.ttc", "Songti-SC"),        # 宋体-简
            ("STHeiti Light.ttc", "STHeiti"),   # 华文黑体

            # Linux 常用字体
            ("NotoSansCJK-Regular.ttc", "NotoSansCJK"),  # Noto Sans CJK
            ("NotoSerifCJK-Regular.ttc", "NotoSerifCJK"),  # Noto Serif CJK
            ("wqy-microhei.ttc", "WQY-MicroHei"),  # 文泉驿微米黑
            ("wqy-zenhei.ttc", "WQY-ZenHei"),      # 文泉驿正黑
            ("uming.ttc", "AR-PL-UMing"),          # AR PL UMing
        ]

        # 尝试注册字体
        for font_file, font_name in font_files:
            for base_path in font_paths:
                # 尝试直接路径
                font_path = os.path.join(base_path, font_file)
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont(font_name, font_path))
                        self.logger.info(f"成功注册中文字体: {font_name} ({font_path})")
                        return font_name
                    except Exception as e:
                        self.logger.debug(f"注册字体失败 {font_path}: {e}")
                        continue

                # 对于Linux，尝试递归查找子目录
                if system == "Linux" and os.path.exists(base_path):
                    for root, dirs, files in os.walk(base_path):
                        if font_file in files:
                            font_path = os.path.join(root, font_file)
                            try:
                                pdfmetrics.registerFont(TTFont(font_name, font_path))
                                self.logger.info(f"成功注册中文字体: {font_name} ({font_path})")
                                return font_name
                            except Exception as e:
                                self.logger.debug(f"注册字体失败 {font_path}: {e}")
                                continue

        # 如果都失败了，尝试不带路径直接注册（依赖系统字体配置）
        for font_file, font_name in [("SimSun", "SimSun"), ("SimHei", "SimHei")]:
            try:
                pdfmetrics.registerFont(TTFont(font_name, font_file))
                self.logger.info(f"成功注册中文字体（系统路径）: {font_name}")
                return font_name
            except Exception as e:
                self.logger.debug(f"注册字体失败 {font_file}: {e}")

        # 所有尝试都失败，使用默认字体
        self.logger.warning(
            f"未找到可用的中文字体（操作系统: {system}），PDF将使用默认字体，中文可能无法正确显示。\n"
            f"建议安装中文字体：\n"
            f"  - Windows: 系统自带宋体/黑体\n"
            f"  - macOS: 系统自带苹方/宋体\n"
            f"  - Linux: sudo apt-get install fonts-noto-cjk 或 fonts-wqy-microhei"
        )
        return "Helvetica"
