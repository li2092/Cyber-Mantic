"""
历史记录标签页 - 查看、搜索、对比历史报告
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from typing import Optional, List
from datetime import datetime

from utils.history_manager import HistoryManager
from utils.error_handler import ErrorHandler
from utils.logger import get_logger


class HistoryTab(QWidget):
    """历史记录标签页"""
    
    report_selected = pyqtSignal(object)  # 报告被选中信号

    def __init__(self, history_manager: HistoryManager, parent=None):
        super().__init__(parent)
        self.history_manager = history_manager
        self.logger = get_logger(__name__)
        self.error_handler = ErrorHandler(self)
        
        # 已选中的报告ID列表
        self.selected_report_ids: List[str] = []

        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 工具栏
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(10)

        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.setMinimumHeight(36)
        refresh_btn.clicked.connect(self._refresh_history)
        toolbar_layout.addWidget(refresh_btn)

        # 清空历史按钮
        clear_btn = QPushButton("🗑️ 清空历史")
        clear_btn.setMinimumHeight(36)
        clear_btn.clicked.connect(self._clear_all_history)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #E57373;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #EF5350;
            }
            QPushButton:pressed {
                background-color: #E53935;
            }
        """)
        toolbar_layout.addWidget(clear_btn)

        # 对比按钮
        self.compare_btn = QPushButton("📊 对比选中的报告 (0/2)")
        self.compare_btn.setEnabled(False)
        self.compare_btn.setMinimumHeight(36)
        self.compare_btn.clicked.connect(self._compare_selected_reports)
        self.compare_btn.setStyleSheet("""
            QPushButton {
                background-color: #81C784;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #66BB6A;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
            }
        """)
        toolbar_layout.addWidget(self.compare_btn)

        # 搜索
        search_label = QLabel("搜索:")
        toolbar_layout.addWidget(search_label)
        self.history_search = QLineEdit()
        self.history_search.setPlaceholderText("输入关键词搜索...")
        self.history_search.setMinimumHeight(32)
        self.history_search.textChanged.connect(self._search_history)
        toolbar_layout.addWidget(self.history_search)

        # 模块筛选 (问道/推演)
        module_label = QLabel("模块:")
        toolbar_layout.addWidget(module_label)
        self.history_module_filter = QComboBox()
        self.history_module_filter.addItems(["全部", "问道", "推演"])
        self.history_module_filter.setMinimumHeight(32)
        self.history_module_filter.currentTextChanged.connect(self._filter_by_module)
        toolbar_layout.addWidget(self.history_module_filter)

        # 问题类型筛选
        type_label = QLabel("类型:")
        toolbar_layout.addWidget(type_label)
        self.history_type_filter = QComboBox()
        self.history_type_filter.addItems([
            "全部", "事业", "财运", "感情", "婚姻", "健康",
            "学业", "人际", "择时", "决策", "性格"
        ])
        self.history_type_filter.setMinimumHeight(32)
        self.history_type_filter.currentTextChanged.connect(self._filter_history)
        toolbar_layout.addWidget(self.history_type_filter)

        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)

        # 历史记录表格
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels([
            "选择", "时间", "问题类型", "问题描述", "使用理论", "操作"
        ])
        
        # 设置列宽
        self.history_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.history_table.setColumnWidth(0, 60)
        self.history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.history_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        # 监听选择变化
        self.history_table.itemChanged.connect(self._on_history_selection_changed)

        layout.addWidget(self.history_table)

        # 统计信息
        self.history_stats_label = QLabel()
        layout.addWidget(self.history_stats_label)

        # 加载历史记录
        self._refresh_history()

    def _refresh_history(self):
        """刷新历史记录列表"""
        try:
            history_list = self.history_manager.get_recent_history(100)
            self._display_history(history_list)

            # 更新统计信息
            stats = self.history_manager.get_statistics()
            self.history_stats_label.setText(
                f"总记录数: {stats['total_count']} | "
                f"最近分析: {stats['last_analysis_time'] or '无'}"
            )
        except Exception as e:
            self.error_handler.handle_error(e, "刷新历史记录")

    def _clear_all_history(self):
        """清空所有历史记录"""
        # 确认对话框
        reply = QMessageBox.question(
            self,
            "确认清空",
            "⚠️ 您确定要清空所有历史记录吗？\n\n此操作不可恢复！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # 获取当前记录数
                stats = self.history_manager.get_statistics()
                count = stats.get('total_count', 0)

                # 清空数据库
                import sqlite3
                with sqlite3.connect(self.history_manager.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM analysis_history")
                    conn.commit()

                # 刷新显示
                self._refresh_history()

                # 提示成功
                QMessageBox.information(
                    self,
                    "清空成功",
                    f"✅ 已清空 {count} 条历史记录"
                )

                self.logger.info(f"用户清空了 {count} 条历史记录")

            except Exception as e:
                self.error_handler.handle_error(e, "清空历史记录")
                QMessageBox.critical(
                    self,
                    "清空失败",
                    f"❌ 清空历史记录失败：{str(e)}"
                )

    def _search_history(self, keyword: str):
        """搜索历史记录"""
        try:
            if keyword.strip():
                history_list = self.history_manager.search_by_keyword(keyword, 100)
            else:
                history_list = self.history_manager.get_recent_history(100)
            self._display_history(history_list)
        except Exception as e:
            self.error_handler.handle_error(e, "搜索历史记录")

    def _filter_history(self, question_type: str):
        """按问题类型筛选历史记录"""
        try:
            module_filter = self.history_module_filter.currentText()
            if question_type == "全部" and module_filter == "全部":
                history_list = self.history_manager.get_recent_history(100)
            elif question_type == "全部":
                history_list = self.history_manager.search_by_module(module_filter, 100)
            elif module_filter == "全部":
                history_list = self.history_manager.search_by_question_type(question_type, 100)
            else:
                # 同时筛选模块和问题类型
                history_list = self.history_manager.search_by_module_and_type(module_filter, question_type, 100)
            self._display_history(history_list)
        except Exception as e:
            self.error_handler.handle_error(e, "筛选历史记录")

    def _filter_by_module(self, module: str):
        """按模块筛选历史记录（问道/推演）"""
        try:
            type_filter = self.history_type_filter.currentText()
            if module == "全部" and type_filter == "全部":
                history_list = self.history_manager.get_recent_history(100)
            elif module == "全部":
                history_list = self.history_manager.search_by_question_type(type_filter, 100)
            elif type_filter == "全部":
                history_list = self.history_manager.search_by_module(module, 100)
            else:
                history_list = self.history_manager.search_by_module_and_type(module, type_filter, 100)
            self._display_history(history_list)
        except Exception as e:
            self.error_handler.handle_error(e, "筛选历史记录")

    def _display_history(self, history_list):
        """显示历史记录到表格"""
        # 临时断开信号，避免触发选择变化
        try:
            self.history_table.itemChanged.disconnect(self._on_history_selection_changed)
        except Exception as e:
            # 信号可能未连接，忽略错误
            self.logger.debug(f"断开信号失败（可能未连接）: {e}")

        self.history_table.setRowCount(len(history_list))

        for row, item in enumerate(history_list):
            # 复选框列（列0）
            checkbox_item = QTableWidgetItem()
            checkbox_item.setCheckState(Qt.CheckState.Unchecked)
            checkbox_item.setFlags(checkbox_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            checkbox_item.setData(Qt.ItemDataRole.UserRole, item['report_id'])
            checkbox_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            # 添加视觉提示文本
            checkbox_item.setText("")  # 确保没有文本干扰
            self.history_table.setItem(row, 0, checkbox_item)

            # 时间（列1）
            created_at = item['created_at']
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at)
            time_text = created_at.strftime('%Y-%m-%d %H:%M')
            self.history_table.setItem(row, 1, QTableWidgetItem(time_text))

            # 问题类型（列2）
            self.history_table.setItem(row, 2, QTableWidgetItem(item.get('question_type', '')))

            # 问题描述（列3）
            desc = item.get('question_desc', '')
            if len(desc) > 50:
                desc = desc[:50] + "..."
            self.history_table.setItem(row, 3, QTableWidgetItem(desc))

            # 使用理论（列4）
            theories = item.get('selected_theories', '')
            self.history_table.setItem(row, 4, QTableWidgetItem(theories))

            # 操作按钮（列5）
            btn_widget = QWidget()
            btn_layout = QHBoxLayout()
            btn_layout.setContentsMargins(10, 6, 10, 6)
            btn_layout.setSpacing(10)

            view_btn = QPushButton("查看")
            view_btn.setMinimumSize(70, 36)
            view_btn.setMaximumSize(70, 36)
            view_btn.clicked.connect(lambda checked, rid=item['report_id']: self._view_history_report(rid))
            btn_layout.addWidget(view_btn)

            qa_btn = QPushButton("问答")
            qa_btn.setMinimumSize(70, 36)
            qa_btn.setMaximumSize(70, 36)
            qa_btn.clicked.connect(lambda checked, rid=item['report_id']: self._open_report_qa(rid))
            btn_layout.addWidget(qa_btn)

            delete_btn = QPushButton("删除")
            delete_btn.setMinimumSize(70, 36)
            delete_btn.setMaximumSize(70, 36)
            delete_btn.clicked.connect(lambda checked, rid=item['report_id']: self._delete_history_report(rid))
            btn_layout.addWidget(delete_btn)

            btn_widget.setLayout(btn_layout)
            self.history_table.setCellWidget(row, 5, btn_widget)

            # 设置行高以容纳按钮，增加到65px确保按钮不被遮挡
            self.history_table.setRowHeight(row, 65)

        # 重新连接信号
        self.history_table.itemChanged.connect(self._on_history_selection_changed)

    def _on_history_selection_changed(self, item: QTableWidgetItem):
        """历史记录选择变化"""
        if item.column() != 0:  # 只处理复选框列
            return

        # 更新选中列表
        self.selected_report_ids = []
        for row in range(self.history_table.rowCount()):
            checkbox_item = self.history_table.item(row, 0)
            if checkbox_item and checkbox_item.checkState() == Qt.CheckState.Checked:
                report_id = checkbox_item.data(Qt.ItemDataRole.UserRole)
                self.selected_report_ids.append(report_id)

        # 更新对比按钮状态
        count = len(self.selected_report_ids)
        self.compare_btn.setText(f"📊 对比选中的报告 ({count}/2)")
        self.compare_btn.setEnabled(count == 2)

    def _view_history_report(self, report_id: str):
        """查看历史报告"""
        try:
            report = self.history_manager.get_report_by_id(report_id)
            if not report:
                QMessageBox.warning(self, "错误", "无法加载报告")
                return

            # 发射信号通知主窗口
            self.report_selected.emit(report)
        except Exception as e:
            self.error_handler.handle_error(e, "查看历史报告")

    def _delete_history_report(self, report_id: str):
        """删除历史报告"""
        reply = QMessageBox.question(
            self, "确认删除",
            "确定要删除这条历史记录吗？\n此操作不可恢复！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.history_manager.delete_report(report_id):
                    QMessageBox.information(self, "成功", "历史记录已删除")
                    self._refresh_history()
                else:
                    QMessageBox.critical(self, "错误", "删除失败")
            except Exception as e:
                self.error_handler.handle_error(e, "删除历史记录")

    def _compare_selected_reports(self):
        """对比选中的报告"""
        if len(self.selected_report_ids) != 2:
            QMessageBox.warning(self, "提示", "请选择2个报告进行对比")
            return

        try:
            from ui.dialogs.report_compare_dialog import ReportCompareDialog
            from utils.config_manager import get_config_manager
            from services.report_service import ReportService
            from api.manager import APIManager

            report1 = self.history_manager.get_report_by_id(self.selected_report_ids[0])
            report2 = self.history_manager.get_report_by_id(self.selected_report_ids[1])

            if not report1 or not report2:
                QMessageBox.warning(self, "错误", "无法加载报告")
                return

            # 创建ReportService实例
            config = get_config_manager().get_all_config()
            api_manager = APIManager(config.get("api", {}))
            report_service = ReportService(api_manager)

            # 正确传递参数：report1, report2, report_service, parent
            dialog = ReportCompareDialog(report1, report2, report_service, self)
            dialog.exec()
        except Exception as e:
            self.error_handler.handle_error(e, "对比报告")

    def _open_report_qa(self, report_id: str):
        """打开报告问答对话框"""
        try:
            from ui.dialogs.report_qa_dialog import ReportQADialog
            from api.manager import APIManager
            
            report = self.history_manager.get_report_by_id(report_id)
            if not report:
                QMessageBox.warning(self, "错误", "无法加载报告")
                return

            # 需要ReportService实例
            from utils.config_manager import get_config_manager
            from services.report_service import ReportService
            config = get_config_manager().get_all_config()
            api_manager = APIManager(config.get("api", {}))
            report_service = ReportService(api_manager)

            dialog = ReportQADialog(report, report_service, self)
            dialog.exec()
        except Exception as e:
            self.error_handler.handle_error(e, "报告问答")

    def cleanup(self):
        """清理资源，断开信号连接"""
        try:
            self.history_table.itemChanged.disconnect()
        except Exception as e:
            # 信号可能已断开，忽略错误
            self.logger.debug(f"清理时断开信号失败: {e}")
