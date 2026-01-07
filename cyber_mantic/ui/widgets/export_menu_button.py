"""
ExportMenuButton - 导出菜单按钮组件

带下拉菜单的导出按钮，支持JSON/PDF/Markdown三种格式
"""

from PyQt6.QtWidgets import (
    QPushButton, QMenu, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from typing import Optional
import asyncio

from models import ComprehensiveReport
from services.export_service import ExportService
from utils.logger import get_logger


class ExportWorker(QThread):
    """导出异步工作线程"""
    finished = pyqtSignal(bool, str)  # (success, message)

    def __init__(self, export_service: ExportService, report: ComprehensiveReport,
                 file_path: str, format: str):
        super().__init__()
        self.export_service = export_service
        self.report = report
        self.file_path = file_path
        self.format = format

    def run(self):
        """执行导出"""
        try:
            if self.format == "json":
                success = self.export_service.export_to_json(self.report, self.file_path)
            elif self.format == "pdf":
                success = self.export_service.export_to_pdf(self.report, self.file_path)
            elif self.format == "markdown":
                success = self.export_service.export_to_markdown(self.report, self.file_path)
            else:
                self.finished.emit(False, f"不支持的格式: {self.format}")
                return

            if success:
                self.finished.emit(True, f"报告已成功导出为 {self.format.upper()} 格式！")
            else:
                self.finished.emit(False, "导出失败，请检查日志。")

        except Exception as e:
            self.finished.emit(False, f"导出时出错: {str(e)}")


class ExportMenuButton(QPushButton):
    """导出菜单按钮组件"""

    # 信号：导出完成
    export_finished = pyqtSignal(bool, str)  # (success, message)

    def __init__(self, export_service: ExportService, parent=None):
        super().__init__("💾 导出报告", parent)
        self.export_service = export_service
        self.current_report: Optional[ComprehensiveReport] = None
        self.logger = get_logger(__name__)
        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        # 按钮样式
        self.setStyleSheet("""
            QPushButton {
                background-color: #66BB6A;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #4CAF50;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
            }
            QPushButton::menu-indicator {
                width: 12px;
                subcontrol-position: right center;
                subcontrol-origin: padding;
                left: -5px;
            }
        """)

        # 创建下拉菜单
        self.menu = QMenu(self)

        # JSON选项
        json_action = self.menu.addAction("📄 导出为 JSON")
        json_action.triggered.connect(lambda: self._export_report("json"))

        # PDF选项
        pdf_action = self.menu.addAction("📕 导出为 PDF")
        pdf_action.triggered.connect(lambda: self._export_report("pdf"))

        # Markdown选项
        md_action = self.menu.addAction("📝 导出为 Markdown")
        md_action.triggered.connect(lambda: self._export_report("markdown"))

        # 设置菜单
        self.setMenu(self.menu)

        # 初始禁用
        self.setEnabled(False)

    def set_report(self, report: ComprehensiveReport):
        """
        设置当前报告

        Args:
            report: 要导出的报告
        """
        self.current_report = report
        self.setEnabled(True)

    def clear_report(self):
        """清空当前报告"""
        self.current_report = None
        self.setEnabled(False)

    def _export_report(self, format: str):
        """
        导出报告

        Args:
            format: 导出格式（json/pdf/markdown）
        """
        if not self.current_report:
            QMessageBox.warning(
                self,
                "无法导出",
                "当前没有可导出的报告。"
            )
            return

        # 建议文件名
        suggested_filename = self.export_service.suggest_filename(
            self.current_report,
            format
        )

        # 文件过滤器
        filters = {
            "json": "JSON文件 (*.json);;所有文件 (*)",
            "pdf": "PDF文件 (*.pdf);;所有文件 (*)",
            "markdown": "Markdown文件 (*.md);;所有文件 (*)"
        }

        # 打开保存对话框
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            f"导出为 {format.upper()}",
            suggested_filename,
            filters.get(format, "所有文件 (*)")
        )

        if not file_path:
            return

        # 禁用按钮
        self.setEnabled(False)
        original_text = self.text()
        self.setText(f"正在导出 {format.upper()}...")

        # 启动异步导出
        self.worker = ExportWorker(
            self.export_service,
            self.current_report,
            file_path,
            format
        )
        self.worker.finished.connect(self._on_export_finished)
        self.worker.start()

        # 保存原始文本，用于恢复
        self._original_text = original_text

    def _on_export_finished(self, success: bool, message: str):
        """导出完成回调"""
        # 恢复按钮
        self.setText(self._original_text)
        self.setEnabled(True)

        # 发送信号
        self.export_finished.emit(success, message)

        # 显示消息框
        if success:
            QMessageBox.information(
                self,
                "导出成功",
                message
            )
            self.logger.info(message)
        else:
            QMessageBox.warning(
                self,
                "导出失败",
                message
            )
            self.logger.error(message)
