"""
预警对话框
用于显示关怀提示、暂停建议、强制冷却界面

核心理念：预警是关怀而非惩罚

设计参考：docs/design/03_洞察模块设计.md
"""
from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QRadioButton, QCheckBox,
    QLineEdit, QButtonGroup, QMessageBox, QTextBrowser
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from utils.warning_manager import get_warning_manager, WarningLevel, CRISIS_HOTLINES


class CareDialog(QDialog):
    """
    关怀提示对话框

    温和提示，不阻止使用
    """

    def __init__(self, message: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("温馨提示")
        self.setFixedSize(400, 200)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self._init_ui(message)

    def _init_ui(self, message: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # 消息
        msg_label = QLabel(message)
        msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg_label.setStyleSheet("font-size: 16px; color: #333;")
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)

        layout.addStretch()

        # 确定按钮
        ok_btn = QPushButton("好的，我知道了")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 30px;
                border: none;
                border-radius: 5px;
                background-color: #1976d2;
                color: white;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
        """)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)


class PauseDialog(QDialog):
    """
    暂停建议对话框

    弹窗选择：继续使用 / 休息60分钟
    """

    def __init__(self, message: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("暂停建议")
        self.setFixedSize(450, 250)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self._continue_chosen = False
        self._init_ui(message)

    def _init_ui(self, message: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # 图标和消息
        icon_label = QLabel("💙")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 48px;")
        layout.addWidget(icon_label)

        msg_label = QLabel(message)
        msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg_label.setStyleSheet("font-size: 16px; color: #333;")
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)

        layout.addStretch()

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20)

        continue_btn = QPushButton("继续使用")
        continue_btn.clicked.connect(self._on_continue)
        continue_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 25px;
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: #fff;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
            }
        """)
        btn_layout.addWidget(continue_btn)

        rest_btn = QPushButton("休息60分钟")
        rest_btn.clicked.connect(self._on_rest)
        rest_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 25px;
                border: none;
                border-radius: 5px;
                background-color: #4caf50;
                color: white;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #43a047;
            }
        """)
        btn_layout.addWidget(rest_btn)

        layout.addLayout(btn_layout)

    def _on_continue(self):
        self._continue_chosen = True
        self.accept()

    def _on_rest(self):
        self._continue_chosen = False
        self.accept()

    def chose_continue(self) -> bool:
        """用户是否选择继续使用"""
        return self._continue_chosen


class ForcedCoolingDialog(QDialog):
    """
    强制冷却对话框

    锁定24h + 危机指引 + AI关怀话语
    """

    def __init__(self, message: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("请稍作休息")
        self.setMinimumSize(500, 450)
        self.setWindowFlags(
            self.windowFlags() &
            ~Qt.WindowType.WindowContextHelpButtonHint &
            ~Qt.WindowType.WindowCloseButtonHint
        )

        self._warning_manager = get_warning_manager()
        self._init_ui(message)

        # 定时更新倒计时
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_countdown)
        self._timer.start(1000)

    def _init_ui(self, message: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # 图标
        icon_label = QLabel("💙")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 48px;")
        layout.addWidget(icon_label)

        # 关怀消息
        msg_label = QLabel(message)
        msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg_label.setStyleSheet("font-size: 15px; color: #333; line-height: 1.6;")
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)

        # 危机热线
        hotline_frame = QFrame()
        hotline_frame.setStyleSheet("""
            QFrame {
                background-color: #e3f2fd;
                border: 1px solid #90caf9;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        hotline_layout = QVBoxLayout(hotline_frame)

        hotline_title = QLabel("如果您需要专业支持：")
        hotline_title.setStyleSheet("font-weight: bold; color: #1976d2;")
        hotline_layout.addWidget(hotline_title)

        for name, number in CRISIS_HOTLINES:
            line = QLabel(f"📞 {name}：{number}")
            line.setStyleSheet("color: #333; font-size: 13px;")
            line.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            hotline_layout.addWidget(line)

        layout.addWidget(hotline_frame)

        # 倒计时
        self._countdown_label = QLabel("系统将在 --:--:-- 后恢复使用")
        self._countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._countdown_label.setStyleSheet("color: #666; font-size: 13px;")
        layout.addWidget(self._countdown_label)

        layout.addStretch()

        # "我只是随便说说"按钮
        unlock_btn = QPushButton("我只是随便说说，申请解除")
        unlock_btn.clicked.connect(self._on_request_unlock)
        unlock_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                border: 1px solid #999;
                border-radius: 5px;
                background-color: #fff;
                color: #666;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
            }
        """)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(unlock_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self._update_countdown()

    def _update_countdown(self):
        """更新倒计时显示"""
        remaining = self._warning_manager.get_remaining_lock_time()
        if remaining:
            self._countdown_label.setText(f"系统将在 {remaining} 后恢复使用")
        else:
            self._countdown_label.setText("锁定已解除")
            self._timer.stop()
            self.accept()

    def _on_request_unlock(self):
        """请求解除锁定"""
        dialog = UnlockRequestDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 解除成功
            self.accept()


class UnlockRequestDialog(QDialog):
    """
    解除锁定申请对话框

    "我只是随便说说"免责流程
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("确认状态")
        self.setMinimumSize(500, 500)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self._warning_manager = get_warning_manager()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # 标题
        title = QLabel("💙 我们需要确认您目前的状态")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        layout.addWidget(title)

        # 问题1：是否有伤害自己的想法
        q1_frame = QFrame()
        q1_frame.setStyleSheet("QFrame { background-color: #f9f9f9; border-radius: 5px; padding: 10px; }")
        q1_layout = QVBoxLayout(q1_frame)

        q1_label = QLabel("1. 您现在是否有伤害自己的想法？")
        q1_label.setStyleSheet("font-weight: bold;")
        q1_layout.addWidget(q1_label)

        self._q1_group = QButtonGroup(self)
        self._q1_no = QRadioButton("没有，我只是情绪发泄")
        self._q1_little = QRadioButton("有一点，但不会付诸行动")
        self._q1_help = QRadioButton("我需要帮助")

        self._q1_group.addButton(self._q1_no, 0)
        self._q1_group.addButton(self._q1_little, 1)
        self._q1_group.addButton(self._q1_help, 2)

        q1_layout.addWidget(self._q1_no)
        q1_layout.addWidget(self._q1_little)
        q1_layout.addWidget(self._q1_help)

        layout.addWidget(q1_frame)

        # 问题2：是否愿意尝试缓解方式
        q2_frame = QFrame()
        q2_frame.setStyleSheet("QFrame { background-color: #f9f9f9; border-radius: 5px; padding: 10px; }")
        q2_layout = QVBoxLayout(q2_frame)

        q2_label = QLabel("2. 您是否愿意尝试以下方式缓解情绪？")
        q2_label.setStyleSheet("font-weight: bold;")
        q2_layout.addWidget(q2_label)

        self._breathe_check = QCheckBox("深呼吸3分钟")
        self._talk_check = QCheckBox("和朋友/家人聊聊")
        self._walk_check = QCheckBox("出门散步")
        self._better_check = QCheckBox("我已经好多了")

        q2_layout.addWidget(self._breathe_check)
        q2_layout.addWidget(self._talk_check)
        q2_layout.addWidget(self._walk_check)
        q2_layout.addWidget(self._better_check)

        layout.addWidget(q2_frame)

        # 问题3：确认文本
        q3_frame = QFrame()
        q3_frame.setStyleSheet("QFrame { background-color: #f9f9f9; border-radius: 5px; padding: 10px; }")
        q3_layout = QVBoxLayout(q3_frame)

        q3_label = QLabel('3. 请输入"我确认当前状态良好"以解除限制')
        q3_label.setStyleSheet("font-weight: bold;")
        q3_layout.addWidget(q3_label)

        self._confirm_input = QLineEdit()
        self._confirm_input.setPlaceholderText("请在此输入确认文本...")
        self._confirm_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
        """)
        q3_layout.addWidget(self._confirm_input)

        layout.addWidget(q3_frame)

        # 提示
        hint = QLabel("⚠️ 此记录将被保存用于产品改进（不含个人信息）")
        hint.setStyleSheet("color: #999; font-size: 12px;")
        layout.addWidget(hint)

        layout.addStretch()

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 25px;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
            }
        """)
        btn_layout.addWidget(cancel_btn)

        submit_btn = QPushButton("提交并解除限制")
        submit_btn.clicked.connect(self._on_submit)
        submit_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 25px;
                border: none;
                border-radius: 5px;
                background-color: #1976d2;
                color: white;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
        """)
        btn_layout.addWidget(submit_btn)

        layout.addLayout(btn_layout)

    def _on_submit(self):
        """提交解除申请"""
        # 检查问题1
        if self._q1_help.isChecked():
            # 用户选择需要帮助，显示热线信息
            QMessageBox.information(
                self,
                "专业支持",
                "如果您需要帮助，请拨打以下热线：\n\n"
                "📞 全国心理援助热线：400-161-9995\n"
                "📞 生命热线：400-821-1215\n"
                "📞 青少年心理热线：12355\n\n"
                "专业的心理咨询师会帮助您。"
            )
            return

        if not self._q1_group.checkedButton():
            QMessageBox.warning(self, "请完成问卷", "请回答问题1")
            return

        # 收集自评信息
        assessment = {
            "q1_answer": self._q1_group.checkedId(),
            "needs_help": self._q1_help.isChecked(),
            "coping_methods": {
                "breathe": self._breathe_check.isChecked(),
                "talk": self._talk_check.isChecked(),
                "walk": self._walk_check.isChecked(),
                "better": self._better_check.isChecked()
            }
        }

        # 验证确认文本
        confirmation = self._confirm_input.text().strip()

        if self._warning_manager.request_unlock(confirmation, assessment):
            QMessageBox.information(self, "解除成功", "限制已解除，请保重。💙")
            self.accept()
        else:
            QMessageBox.warning(
                self,
                "确认失败",
                '请正确输入"我确认当前状态良好"'
            )


def show_warning_dialog(level: WarningLevel, message: str, parent=None) -> bool:
    """
    显示预警对话框

    Args:
        level: 预警级别
        message: 消息内容
        parent: 父窗口

    Returns:
        用户是否选择继续使用（仅对 PAUSE 级别有意义）
    """
    if level == WarningLevel.CARE:
        dialog = CareDialog(message, parent)
        dialog.exec()
        return True

    elif level == WarningLevel.PAUSE:
        dialog = PauseDialog(message, parent)
        dialog.exec()
        return dialog.chose_continue()

    elif level == WarningLevel.FORCED:
        dialog = ForcedCoolingDialog(message, parent)
        dialog.exec()
        return False

    return True
