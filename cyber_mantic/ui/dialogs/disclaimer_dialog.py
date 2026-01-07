"""
免责声明对话框模块

包含：
- 首次启动免责声明对话框
- 简版提示对话框
- 未成年人检测与提示对话框

设计参考：docs/design/05_免责声明设计.md
"""
from datetime import date
from typing import Optional, Callable
from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QCheckBox, QPushButton, QTextEdit, QScrollArea,
    QWidget, QRadioButton, QButtonGroup, QFrame,
    QLineEdit, QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from utils.config_manager import get_config_manager


class FirstLaunchDisclaimerDialog(QDialog):
    """
    首次启动免责声明对话框

    功能：
    - 显示完整使用须知与免责声明
    - 三项勾选确认（年满18岁、已阅读同意、理解仅供参考）
    - 确认后记录到配置文件
    """

    accepted_signal = pyqtSignal()  # 用户接受协议信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("欢迎使用赛博玄数")
        self.setMinimumSize(700, 650)
        self.setModal(True)

        # 配置管理器
        self.config_manager = get_config_manager()

        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)

        # 标题
        title_label = QLabel("欢迎使用赛博玄数")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

        # 使用须知标题
        notice_title = QLabel("使用须知")
        notice_font = QFont()
        notice_font.setPointSize(12)
        notice_font.setBold(True)
        notice_title.setFont(notice_font)
        layout.addWidget(notice_title)

        # 免责声明内容（滚动区域）
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(280)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)

        disclaimer_text = self._get_disclaimer_text()
        disclaimer_label = QLabel(disclaimer_text)
        disclaimer_label.setWordWrap(True)
        disclaimer_label.setTextFormat(Qt.TextFormat.RichText)
        disclaimer_label.setStyleSheet("font-size: 13px; line-height: 1.6;")
        content_layout.addWidget(disclaimer_label)

        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)

        # 查看完整协议链接
        full_text_btn = QPushButton("查看完整协议文本...")
        full_text_btn.setFlat(True)
        full_text_btn.setStyleSheet("color: #0066cc; text-decoration: underline; border: none; text-align: left;")
        full_text_btn.clicked.connect(self._show_full_disclaimer)
        layout.addWidget(full_text_btn)

        # 分隔线
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator2)

        # 三项勾选
        self.checkbox_age = QCheckBox("我已年满18周岁")
        self.checkbox_age.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.checkbox_age)

        self.checkbox_agree = QCheckBox("我已阅读并同意上述《使用须知与免责声明》")
        self.checkbox_agree.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.checkbox_agree)

        self.checkbox_understand = QCheckBox("我理解本软件仅供参考，不会依据分析结果做重大决策")
        self.checkbox_understand.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.checkbox_understand)

        # 连接勾选状态变化
        self.checkbox_age.stateChanged.connect(self._update_button_state)
        self.checkbox_agree.stateChanged.connect(self._update_button_state)
        self.checkbox_understand.stateChanged.connect(self._update_button_state)

        # 同意并继续按钮
        self.accept_btn = QPushButton("同意并继续")
        self.accept_btn.setEnabled(False)
        self.accept_btn.setMinimumHeight(40)
        self.accept_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                background-color: #4a90d9;
                color: white;
                border-radius: 5px;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QPushButton:hover:enabled {
                background-color: #357abd;
            }
        """)
        self.accept_btn.clicked.connect(self._on_accept)
        layout.addWidget(self.accept_btn)

    def _get_disclaimer_text(self) -> str:
        """获取免责声明文本"""
        return """
        <p><b>《使用须知与免责声明》</b></p>

        <p><b>1. 参考性质</b><br/>
        本软件基于中国传统术数理论，结合AI技术开发，所有分析结果仅供参考，不构成任何专业建议。</p>

        <p><b>2. 非专业建议</b><br/>
        本软件不提供医疗、法律、财务、心理咨询等专业服务。如需专业帮助，请咨询相关持证专业人士。</p>

        <p><b>3. 决策责任</b><br/>
        用户基于本软件分析结果做出的任何决策，由用户本人承担全部责任。</p>

        <p><b>4. 数据隐私</b><br/>
        所有数据均存储于本地设备，不会上传至服务器。AI分析请求会发送至第三方API，请勿输入敏感信息。</p>

        <p><b>5. 心理健康</b><br/>
        如您正在经历心理困扰，请寻求专业心理援助。</p>

        <p><b>6. 地域适用性</b><br/>
        本系统基于中国传统术数理论开发，主要适用于北半球地区。南半球用户请知悉此局限性。</p>
        """

    def _show_full_disclaimer(self):
        """显示完整免责声明"""
        # 尝试读取完整协议文件
        legal_path = Path(__file__).parent.parent.parent.parent / "docs" / "legal" / "disclaimer_zh_CN.md"

        if legal_path.exists():
            with open(legal_path, 'r', encoding='utf-8') as f:
                full_text = f.read()
        else:
            full_text = self._get_full_disclaimer_text()

        dialog = QDialog(self)
        dialog.setWindowTitle("完整协议文本")
        dialog.setMinimumSize(600, 500)

        layout = QVBoxLayout(dialog)

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setMarkdown(full_text)
        layout.addWidget(text_edit)

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)

        dialog.exec()

    def _get_full_disclaimer_text(self) -> str:
        """获取完整免责声明文本（备用）"""
        return """# 赛博玄数使用须知与免责声明

## 第一条 产品性质与定位
本软件（以下简称"赛博玄数"）是一款基于中国传统术数理论开发的文化洞察与个人反思工具。
本软件不是占卜工具，不提供算命服务，也不是心理咨询平台。

## 第二条 使用限制
1. 年龄限制：建议18周岁及以上用户使用
2. 地域适用性：本系统基于中国传统术数理论，主要适用于北半球地区

## 第三条 免责条款
1. 所有分析结果仅供参考，不构成任何专业建议
2. 用户基于分析结果做出的任何决策，由用户本人承担全部责任
3. 本软件不提供医疗、法律、财务、心理咨询等专业服务

## 第四条 数据隐私
1. 所有用户数据均存储于本地设备
2. AI分析请求会发送至第三方API服务提供商
3. 请勿输入真实姓名、身份证号等敏感个人信息

## 第五条 知识产权
本软件的所有内容、算法、设计均受知识产权法律保护。

## 第六条 服务变更与终止
开发者保留随时修改、暂停或终止服务的权利。

## 第七条 争议解决
因使用本软件产生的争议，适用中华人民共和国法律。

## 第八条 其他条款
1. 本协议的最终解释权归开发者所有
2. 如本协议中任何条款被认定无效，不影响其他条款的效力
"""

    def _update_button_state(self):
        """更新按钮状态"""
        all_checked = (
            self.checkbox_age.isChecked() and
            self.checkbox_agree.isChecked() and
            self.checkbox_understand.isChecked()
        )
        self.accept_btn.setEnabled(all_checked)

    def _on_accept(self):
        """用户接受协议"""
        # 记录接受时间到配置
        self.config_manager.set_disclaimer_accepted(True)
        self.accepted_signal.emit()
        self.accept()


class SimpleDisclaimerDialog(QDialog):
    """
    简版提示对话框

    在问道/推演功能使用时（每次会话首次）显示
    """

    def __init__(self, parent=None, show_dont_remind: bool = True):
        super().__init__(parent)
        self.setWindowTitle("温馨提示")
        self.setFixedSize(400, 200)
        self.setModal(True)

        self.dont_remind_checked = False
        self._show_dont_remind = show_dont_remind

        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

        # 图标和标题
        title_label = QLabel("温馨提示")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # 提示内容
        content_label = QLabel(
            "分析结果仅供参考，不构成专业建议。\n"
            "重大决策请咨询相关专业人士。"
        )
        content_label.setWordWrap(True)
        content_label.setStyleSheet("font-size: 13px; color: #333;")
        layout.addWidget(content_label)

        # 本次会话不再提示
        if self._show_dont_remind:
            self.dont_remind_checkbox = QCheckBox("本次会话不再提示")
            self.dont_remind_checkbox.setStyleSheet("font-size: 12px; color: #666;")
            layout.addWidget(self.dont_remind_checkbox)

        # 确认按钮
        confirm_btn = QPushButton("我已了解，继续")
        confirm_btn.setMinimumHeight(35)
        confirm_btn.setStyleSheet("""
            QPushButton {
                font-size: 13px;
                background-color: #4a90d9;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
        """)
        confirm_btn.clicked.connect(self._on_confirm)
        layout.addWidget(confirm_btn)

    def _on_confirm(self):
        """确认按钮点击"""
        if self._show_dont_remind:
            self.dont_remind_checked = self.dont_remind_checkbox.isChecked()
        self.accept()

    def should_not_remind(self) -> bool:
        """返回是否勾选了不再提示"""
        return self.dont_remind_checked


class MinorDetectionDialog(QDialog):
    """
    未成年人检测提示对话框

    当检测到用户输入的出生日期对应未满18周岁时显示
    """

    IDENTITY_GUARDIAN = "guardian"      # 监护人
    IDENTITY_ADULT_STUDY = "adult"      # 成年人研究学习
    IDENTITY_MINOR = "minor"            # 未成年人本人

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("未成年人使用提示")
        self.setMinimumSize(480, 380)
        self.setModal(True)

        self.selected_identity = None

        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

        # 警告标题
        title_label = QLabel("未成年人使用提示")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #d97706;")
        layout.addWidget(title_label)

        # 提示内容
        notice_text = QLabel(
            "检测到您输入的出生信息对应未满18周岁。\n\n"
            "请注意：\n"
            "• 本软件建议由成年人监护下使用\n"
            "• 青少年心智尚在发展，请勿过度解读分析结果\n"
            "• 任何困惑建议与家长、老师或专业人士沟通"
        )
        notice_text.setWordWrap(True)
        notice_text.setStyleSheet("font-size: 13px; line-height: 1.6;")
        layout.addWidget(notice_text)

        # 身份选择
        identity_label = QLabel("请确认您的身份：")
        identity_label.setStyleSheet("font-size: 13px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(identity_label)

        self.identity_group = QButtonGroup(self)

        self.radio_guardian = QRadioButton("我是该未成年人的监护人，代为查询")
        self.radio_adult = QRadioButton("我是成年用户，正在研究学习")
        self.radio_minor = QRadioButton("我是未成年人本人")

        self.identity_group.addButton(self.radio_guardian, 1)
        self.identity_group.addButton(self.radio_adult, 2)
        self.identity_group.addButton(self.radio_minor, 3)

        for radio in [self.radio_guardian, self.radio_adult, self.radio_minor]:
            radio.setStyleSheet("font-size: 13px;")
            layout.addWidget(radio)

        # 按钮区域
        btn_layout = QHBoxLayout()

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setMinimumHeight(35)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.confirm_btn = QPushButton("确认并继续")
        self.confirm_btn.setMinimumHeight(35)
        self.confirm_btn.setEnabled(False)
        self.confirm_btn.setStyleSheet("""
            QPushButton {
                font-size: 13px;
                background-color: #4a90d9;
                color: white;
                border-radius: 5px;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QPushButton:hover:enabled {
                background-color: #357abd;
            }
        """)
        self.confirm_btn.clicked.connect(self._on_confirm)
        btn_layout.addWidget(self.confirm_btn)

        layout.addLayout(btn_layout)

        # 连接信号
        self.identity_group.buttonClicked.connect(self._on_identity_selected)

    def _on_identity_selected(self, button):
        """身份选择变化"""
        self.confirm_btn.setEnabled(True)

    def _on_confirm(self):
        """确认按钮点击"""
        checked_id = self.identity_group.checkedId()
        if checked_id == 1:
            self.selected_identity = self.IDENTITY_GUARDIAN
            self.accept()
        elif checked_id == 2:
            self.selected_identity = self.IDENTITY_ADULT_STUDY
            self.accept()
        elif checked_id == 3:
            self.selected_identity = self.IDENTITY_MINOR
            # 显示未成年人额外确认对话框
            self._show_minor_extra_confirmation()

    def _show_minor_extra_confirmation(self):
        """显示未成年人额外确认对话框"""
        dialog = MinorExtraConfirmDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.accept()

    def get_selected_identity(self) -> Optional[str]:
        """获取选择的身份"""
        return self.selected_identity


class MinorExtraConfirmDialog(QDialog):
    """
    未成年人本人的额外确认对话框
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("给你的一些话")
        self.setMinimumSize(480, 400)
        self.setModal(True)

        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

        # 标题
        title_label = QLabel("给你的一些话")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #3b82f6;")
        layout.addWidget(title_label)

        # 鼓励内容
        content_text = QLabel(
            "命运掌握在自己手中，任何预测都只是参考。\n\n"
            "你正处于人生最有可能性的阶段，未来充满无限可能。\n"
            "不要让任何分析结果限制你的想象力和努力。\n\n"
            "如果有任何烦恼，建议和信任的大人聊聊：\n"
            "• 父母、老师、学校心理咨询师\n"
            "• 青少年心理热线：12355"
        )
        content_text.setWordWrap(True)
        content_text.setStyleSheet("font-size: 13px; line-height: 1.8;")
        layout.addWidget(content_text)

        # 两项勾选
        self.checkbox_understand = QCheckBox("我理解以上内容，仅将结果作为参考")
        self.checkbox_understand.setStyleSheet("font-size: 13px;")
        layout.addWidget(self.checkbox_understand)

        self.checkbox_promise = QCheckBox("我承诺不会因分析结果产生负面情绪")
        self.checkbox_promise.setStyleSheet("font-size: 13px;")
        layout.addWidget(self.checkbox_promise)

        # 连接信号
        self.checkbox_understand.stateChanged.connect(self._update_button_state)
        self.checkbox_promise.stateChanged.connect(self._update_button_state)

        # 确认按钮
        self.confirm_btn = QPushButton("我明白了，继续")
        self.confirm_btn.setMinimumHeight(35)
        self.confirm_btn.setEnabled(False)
        self.confirm_btn.setStyleSheet("""
            QPushButton {
                font-size: 13px;
                background-color: #3b82f6;
                color: white;
                border-radius: 5px;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QPushButton:hover:enabled {
                background-color: #2563eb;
            }
        """)
        self.confirm_btn.clicked.connect(self.accept)
        layout.addWidget(self.confirm_btn)

    def _update_button_state(self):
        """更新按钮状态"""
        all_checked = (
            self.checkbox_understand.isChecked() and
            self.checkbox_promise.isChecked()
        )
        self.confirm_btn.setEnabled(all_checked)


class DisclaimerManager:
    """
    免责声明管理器

    统一管理各种免责声明的显示逻辑
    """

    def __init__(self):
        self.config_manager = get_config_manager()
        self._session_disclaimer_shown = False  # 本次会话是否已显示简版提示

    def should_show_first_launch(self) -> bool:
        """是否需要显示首次启动免责声明"""
        return not self.config_manager.is_disclaimer_accepted()

    def show_first_launch_disclaimer(self, parent=None) -> bool:
        """
        显示首次启动免责声明

        Returns:
            bool: 用户是否接受
        """
        dialog = FirstLaunchDisclaimerDialog(parent)
        result = dialog.exec()
        return result == QDialog.DialogCode.Accepted

    def show_simple_disclaimer(self, parent=None) -> bool:
        """
        显示简版提示

        Returns:
            bool: 是否继续
        """
        if self._session_disclaimer_shown:
            return True

        dialog = SimpleDisclaimerDialog(parent)
        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            if dialog.should_not_remind():
                self._session_disclaimer_shown = True
            return True
        return False

    def check_and_show_minor_disclaimer(
        self,
        birth_date: date,
        parent=None
    ) -> tuple[bool, Optional[str]]:
        """
        检查并显示未成年人提示

        Args:
            birth_date: 出生日期
            parent: 父窗口

        Returns:
            tuple: (是否继续, 身份类型)
        """
        if self._is_minor(birth_date):
            dialog = MinorDetectionDialog(parent)
            result = dialog.exec()

            if result == QDialog.DialogCode.Accepted:
                return True, dialog.get_selected_identity()
            return False, None

        return True, None

    def _is_minor(self, birth_date: date) -> bool:
        """判断是否未成年"""
        today = date.today()
        age = today.year - birth_date.year

        # 检查是否已过生日
        if (today.month, today.day) < (birth_date.month, birth_date.day):
            age -= 1

        return age < 18

    def reset_session(self):
        """重置会话状态（新会话开始时调用）"""
        self._session_disclaimer_shown = False


# 全局单例
_disclaimer_manager: Optional[DisclaimerManager] = None


def get_disclaimer_manager() -> DisclaimerManager:
    """获取免责声明管理器单例"""
    global _disclaimer_manager
    if _disclaimer_manager is None:
        _disclaimer_manager = DisclaimerManager()
    return _disclaimer_manager
