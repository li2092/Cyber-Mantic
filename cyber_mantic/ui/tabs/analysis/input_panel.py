"""
输入面板组件 - 用户输入信息的表单界面
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QComboBox, QSpinBox, QCheckBox,
    QPushButton, QDateTimeEdit, QListWidget, QListWidgetItem,
    QInputDialog, QDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QDateTime, pyqtSignal
from typing import Optional, List

from models import PersonBirthInfo
from utils.logger import get_logger
from utils.profile_manager import get_profile_manager
from ui.dialogs.person_birth_info_dialog import PersonBirthInfoDialog
from ui.dialogs.profile_manager_dialog import ProfileManagerDialog

from .workers import GeocodeWorker


class InputPanel(QGroupBox):
    """输入面板组件"""

    # 信号
    location_query_started = pyqtSignal()
    location_query_finished = pyqtSignal(object)  # 结果字典
    location_query_error = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__("输入信息", parent)
        self.logger = get_logger(__name__)
        self.profile_manager = get_profile_manager()

        # 多人八字信息
        self.additional_persons: List[PersonBirthInfo] = []

        # 地理编码工作线程
        self.geocode_worker: Optional[GeocodeWorker] = None

        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # 问题信息
        self._create_question_section(layout)

        # 起卦时间
        layout.addSpacing(10)
        self._create_inquiry_time_section(layout)

        # 出生信息
        layout.addSpacing(15)
        self._create_birth_info_section(layout)

        # 多人八字管理
        layout.addSpacing(15)
        self._create_multi_person_section(layout)

        # 出生地点
        layout.addSpacing(10)
        self._create_birthplace_section(layout)

        # 随机数
        layout.addSpacing(15)
        self._create_random_numbers_section(layout)

        self.setLayout(layout)

    def _create_question_section(self, layout: QVBoxLayout):
        """创建问题信息区域"""
        # 问题类别
        question_layout = QHBoxLayout()
        question_layout.setSpacing(10)
        question_label = QLabel("问题类别:")
        question_label.setMinimumWidth(100)
        question_layout.addWidget(question_label)
        self.question_type = QComboBox()
        self.question_type.addItems([
            "事业", "财运", "感情", "婚姻", "健康",
            "学业", "人际", "择时", "决策", "性格"
        ])
        self.question_type.setMinimumWidth(150)
        self.question_type.setMinimumHeight(32)
        question_layout.addWidget(self.question_type)
        question_layout.addStretch()
        layout.addLayout(question_layout)

        # 问题描述
        desc_layout = QHBoxLayout()
        desc_layout.setSpacing(10)
        desc_label = QLabel("问题描述:")
        desc_label.setMinimumWidth(100)
        desc_layout.addWidget(desc_label)
        self.question_desc = QLineEdit()
        self.question_desc.setPlaceholderText("请详细描述您的问题...")
        self.question_desc.setMinimumHeight(32)
        desc_layout.addWidget(self.question_desc, 1)
        layout.addLayout(desc_layout)

        # 测字输入
        cezi_layout = QHBoxLayout()
        cezi_layout.setSpacing(10)
        cezi_label = QLabel("测字输入:")
        cezi_label.setMinimumWidth(100)
        cezi_layout.addWidget(cezi_label)
        self.character_input = QLineEdit()
        self.character_input.setPlaceholderText("仅输入一个汉字用于测字分析")
        self.character_input.setMaxLength(1)
        self.character_input.setMinimumWidth(150)
        self.character_input.setMaximumWidth(200)
        self.character_input.setMinimumHeight(32)
        cezi_layout.addWidget(self.character_input)
        hint_label = QLabel("（填写后将使用测字术分析）")
        hint_label.setStyleSheet("color: gray; font-size: 11px;")
        cezi_layout.addWidget(hint_label)
        cezi_layout.addStretch()
        layout.addLayout(cezi_layout)

    def _create_inquiry_time_section(self, layout: QVBoxLayout):
        """创建起卦时间区域"""
        inquiry_time_layout = QHBoxLayout()
        inquiry_time_layout.setSpacing(10)
        self.use_custom_inquiry_time = QCheckBox("使用自定义起卦时间")
        self.use_custom_inquiry_time.stateChanged.connect(self._toggle_inquiry_time)
        self.use_custom_inquiry_time.setMinimumWidth(150)
        inquiry_time_layout.addWidget(self.use_custom_inquiry_time)
        inquiry_time_layout.addWidget(QLabel("起卦时间:"))
        self.inquiry_datetime = QDateTimeEdit()
        self.inquiry_datetime.setDateTime(QDateTime.currentDateTime())
        self.inquiry_datetime.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.inquiry_datetime.setEnabled(False)
        self.inquiry_datetime.setMinimumWidth(150)
        self.inquiry_datetime.setMinimumHeight(32)
        inquiry_time_layout.addWidget(self.inquiry_datetime)
        inquiry_time_layout.addStretch()
        layout.addLayout(inquiry_time_layout)

    def _create_birth_info_section(self, layout: QVBoxLayout):
        """创建出生信息区域"""
        # 出生信息启用复选框
        self.use_birth_info = QCheckBox("提供出生信息（用于八字、紫微斗数等）")
        self.use_birth_info.stateChanged.connect(self._toggle_birth_info)
        layout.addWidget(self.use_birth_info)

        # 出生日期
        birth_datetime_layout = QHBoxLayout()
        birth_datetime_layout.setSpacing(10)
        birth_date_label = QLabel("出生日期:")
        birth_date_label.setMinimumWidth(100)
        birth_datetime_layout.addWidget(birth_date_label)

        self.birth_year = QSpinBox()
        self.birth_year.setRange(1900, 2030)
        self.birth_year.setValue(1990)
        self.birth_year.setEnabled(False)
        self.birth_year.setMinimumWidth(90)
        self.birth_year.setMinimumHeight(32)
        birth_datetime_layout.addWidget(self.birth_year)
        birth_datetime_layout.addWidget(QLabel("年"))

        self.birth_month = QSpinBox()
        self.birth_month.setRange(1, 12)
        self.birth_month.setValue(1)
        self.birth_month.setEnabled(False)
        self.birth_month.setMinimumWidth(70)
        self.birth_month.setMinimumHeight(32)
        birth_datetime_layout.addWidget(self.birth_month)
        birth_datetime_layout.addWidget(QLabel("月"))

        self.birth_day = QSpinBox()
        self.birth_day.setRange(1, 31)
        self.birth_day.setValue(1)
        self.birth_day.setEnabled(False)
        self.birth_day.setMinimumWidth(70)
        self.birth_day.setMinimumHeight(32)
        birth_datetime_layout.addWidget(self.birth_day)
        birth_datetime_layout.addWidget(QLabel("日"))
        birth_datetime_layout.addStretch()
        layout.addLayout(birth_datetime_layout)

        # 时辰确定性
        birth_time_certainty_layout = QHBoxLayout()
        birth_time_certainty_layout.setSpacing(10)
        certainty_label = QLabel("时辰确定性:")
        certainty_label.setMinimumWidth(100)
        birth_time_certainty_layout.addWidget(certainty_label)
        self.birth_time_certainty = QComboBox()
        self.birth_time_certainty.addItems([
            "记得时辰",
            "大概是这个时辰",
            "不记得时辰"
        ])
        self.birth_time_certainty.setEnabled(False)
        self.birth_time_certainty.setMinimumWidth(150)
        self.birth_time_certainty.setMinimumHeight(32)
        self.birth_time_certainty.currentIndexChanged.connect(self._toggle_birth_time_inputs)
        birth_time_certainty_layout.addWidget(self.birth_time_certainty)
        certainty_hint = QLabel("（影响理论选择和分析策略）")
        certainty_hint.setStyleSheet("color: gray; font-size: 11px;")
        birth_time_certainty_layout.addWidget(certainty_hint)
        birth_time_certainty_layout.addStretch()
        layout.addLayout(birth_time_certainty_layout)

        # 出生时间
        birth_time_layout = QHBoxLayout()
        birth_time_layout.setSpacing(10)
        birth_time_label = QLabel("出生时间:")
        birth_time_label.setMinimumWidth(100)
        birth_time_layout.addWidget(birth_time_label)

        self.birth_hour = QSpinBox()
        self.birth_hour.setRange(0, 23)
        self.birth_hour.setValue(12)
        self.birth_hour.setEnabled(False)
        self.birth_hour.setMinimumWidth(70)
        self.birth_hour.setMinimumHeight(32)
        birth_time_layout.addWidget(self.birth_hour)
        birth_time_layout.addWidget(QLabel("时"))

        self.birth_minute = QSpinBox()
        self.birth_minute.setRange(0, 59)
        self.birth_minute.setValue(0)
        self.birth_minute.setEnabled(False)
        self.birth_minute.setMinimumWidth(70)
        self.birth_minute.setMinimumHeight(32)
        birth_time_layout.addWidget(self.birth_minute)
        birth_time_layout.addWidget(QLabel("分"))
        birth_time_layout.addStretch()
        layout.addLayout(birth_time_layout)

        # 历法和性别
        birth_info_layout = QHBoxLayout()
        birth_info_layout.setSpacing(10)
        calendar_label = QLabel("历法:")
        calendar_label.setMinimumWidth(100)
        birth_info_layout.addWidget(calendar_label)
        self.calendar_type = QComboBox()
        self.calendar_type.addItems(["阳历", "农历"])
        self.calendar_type.setEnabled(False)
        self.calendar_type.setMinimumWidth(100)
        self.calendar_type.setMinimumHeight(32)
        birth_info_layout.addWidget(self.calendar_type)

        birth_info_layout.addSpacing(30)

        birth_info_layout.addWidget(QLabel("性别:"))
        self.gender = QComboBox()
        self.gender.addItems(["男", "女"])
        self.gender.setEnabled(False)
        self.gender.setMinimumWidth(80)
        self.gender.setMinimumHeight(32)
        birth_info_layout.addWidget(self.gender)
        birth_info_layout.addStretch()
        layout.addLayout(birth_info_layout)

        # MBTI性格类型
        mbti_layout = QHBoxLayout()
        mbti_layout.setSpacing(10)
        mbti_label = QLabel("MBTI类型:")
        mbti_label.setMinimumWidth(100)
        mbti_layout.addWidget(mbti_label)
        self.mbti_combo = QComboBox()
        self.mbti_combo.addItems([
            "请选择",
            "INTJ-建筑师", "INTP-逻辑学家", "ENTJ-指挥官", "ENTP-辩论家",
            "INFJ-提倡者", "INFP-调停者", "ENFJ-主人公", "ENFP-竞选者",
            "ISTJ-物流师", "ISFJ-守卫者", "ESTJ-总经理", "ESFJ-执政官",
            "ISTP-鉴赏家", "ISFP-探险家", "ESTP-企业家", "ESFP-表演者"
        ])
        self.mbti_combo.setEnabled(False)
        self.mbti_combo.setMinimumWidth(200)
        self.mbti_combo.setMinimumHeight(32)
        mbti_layout.addWidget(self.mbti_combo)
        mbti_hint = QLabel("（可选，用于个性化建议）")
        mbti_hint.setStyleSheet("color: gray; font-size: 11px;")
        mbti_layout.addWidget(mbti_hint)
        mbti_layout.addStretch()
        layout.addLayout(mbti_layout)

        # 常用档案管理
        layout.addSpacing(10)
        profile_layout = QHBoxLayout()
        profile_layout.setSpacing(10)
        profile_label = QLabel("常用档案:")
        profile_label.setMinimumWidth(100)
        profile_layout.addWidget(profile_label)

        self.save_profile_btn = QPushButton("保存为常用档案")
        self.save_profile_btn.setMinimumHeight(32)
        self.save_profile_btn.setEnabled(False)
        self.save_profile_btn.clicked.connect(self._save_profile)
        profile_layout.addWidget(self.save_profile_btn)

        self.load_profile_btn = QPushButton("加载常用档案")
        self.load_profile_btn.setMinimumHeight(32)
        self.load_profile_btn.clicked.connect(self._load_profile)
        profile_layout.addWidget(self.load_profile_btn)

        profile_layout.addStretch()
        layout.addLayout(profile_layout)

    def _create_multi_person_section(self, layout: QVBoxLayout):
        """创建多人八字管理区域"""
        self.use_additional_persons = QCheckBox("添加相关人八字（配偶、亲人、帮人问事等）")
        self.use_additional_persons.stateChanged.connect(self._toggle_additional_persons)
        layout.addWidget(self.use_additional_persons)

        # 多人八字管理区域（默认隐藏）
        self.multi_person_widget = QWidget()
        multi_person_layout = QVBoxLayout()
        multi_person_layout.setContentsMargins(20, 10, 0, 0)
        multi_person_layout.setSpacing(10)

        # 额外人物列表
        self.additional_persons_list = QListWidget()
        self.additional_persons_list.setMaximumHeight(100)
        multi_person_layout.addWidget(self.additional_persons_list)

        # 人物管理按钮
        person_btn_layout = QHBoxLayout()
        person_btn_layout.setSpacing(10)

        self.add_person_btn = QPushButton("添加人物")
        self.add_person_btn.setMinimumHeight(32)
        self.add_person_btn.clicked.connect(self._add_person)
        person_btn_layout.addWidget(self.add_person_btn)

        self.edit_person_btn = QPushButton("编辑选中人物")
        self.edit_person_btn.setMinimumHeight(32)
        self.edit_person_btn.setEnabled(False)
        self.edit_person_btn.clicked.connect(self._edit_person)
        person_btn_layout.addWidget(self.edit_person_btn)

        self.remove_person_btn = QPushButton("删除选中人物")
        self.remove_person_btn.setMinimumHeight(32)
        self.remove_person_btn.setEnabled(False)
        self.remove_person_btn.clicked.connect(self._remove_person)
        person_btn_layout.addWidget(self.remove_person_btn)

        person_btn_layout.addStretch()
        multi_person_layout.addLayout(person_btn_layout)

        self.multi_person_widget.setLayout(multi_person_layout)
        self.multi_person_widget.setVisible(False)
        layout.addWidget(self.multi_person_widget)

        # 连接列表选择信号
        self.additional_persons_list.itemSelectionChanged.connect(self._on_person_selection_changed)

    def _create_birthplace_section(self, layout: QVBoxLayout):
        """创建出生地点区域"""
        birthplace_layout = QHBoxLayout()
        birthplace_layout.setSpacing(10)
        place_label = QLabel("出生地点:")
        place_label.setMinimumWidth(100)
        birthplace_layout.addWidget(place_label)
        self.birth_place = QLineEdit()
        self.birth_place.setPlaceholderText("如\"北京市朝阳区\"（用于查询经度）")
        self.birth_place.setEnabled(False)
        self.birth_place.setMinimumHeight(32)
        birthplace_layout.addWidget(self.birth_place, 1)

        self.query_location_btn = QPushButton("查询经纬度")
        self.query_location_btn.setMinimumWidth(100)
        self.query_location_btn.setMinimumHeight(32)
        self.query_location_btn.setEnabled(False)
        self.query_location_btn.clicked.connect(self._query_location)
        birthplace_layout.addWidget(self.query_location_btn)

        birthplace_layout.addWidget(QLabel("经度:"))
        self.birth_lng = QLineEdit()
        self.birth_lng.setPlaceholderText("如120.5")
        self.birth_lng.setMaximumWidth(100)
        self.birth_lng.setMinimumHeight(32)
        self.birth_lng.setEnabled(False)
        birthplace_layout.addWidget(self.birth_lng)
        layout.addLayout(birthplace_layout)

    def _create_random_numbers_section(self, layout: QVBoxLayout):
        """创建随机数区域"""
        self.use_random_numbers = QCheckBox("提供随机数（用于梅花易数、六爻等）")
        self.use_random_numbers.stateChanged.connect(self._toggle_random_numbers)
        layout.addWidget(self.use_random_numbers)

        numbers_layout = QHBoxLayout()
        numbers_layout.setSpacing(10)
        numbers_label = QLabel("随机数字（1-9）:")
        numbers_label.setMinimumWidth(120)
        numbers_layout.addWidget(numbers_label)

        self.num1 = QSpinBox()
        self.num1.setRange(1, 9)
        self.num1.setValue(3)
        self.num1.setEnabled(False)
        self.num1.setMinimumWidth(70)
        self.num1.setMinimumHeight(32)
        numbers_layout.addWidget(self.num1)
        numbers_layout.addSpacing(15)

        self.num2 = QSpinBox()
        self.num2.setRange(1, 9)
        self.num2.setValue(5)
        self.num2.setEnabled(False)
        self.num2.setMinimumWidth(70)
        self.num2.setMinimumHeight(32)
        numbers_layout.addWidget(self.num2)
        numbers_layout.addSpacing(15)

        self.num3 = QSpinBox()
        self.num3.setRange(1, 9)
        self.num3.setValue(7)
        self.num3.setEnabled(False)
        self.num3.setMinimumWidth(70)
        self.num3.setMinimumHeight(32)
        numbers_layout.addWidget(self.num3)
        numbers_layout.addStretch()
        layout.addLayout(numbers_layout)

    # ===== 槽函数 =====

    def _toggle_inquiry_time(self, state):
        """切换起卦时间输入"""
        self.inquiry_datetime.setEnabled(state == Qt.CheckState.Checked.value)

    def _toggle_birth_info(self, state):
        """切换出生信息输入"""
        enabled = state == Qt.CheckState.Checked.value
        self.birth_year.setEnabled(enabled)
        self.birth_month.setEnabled(enabled)
        self.birth_day.setEnabled(enabled)
        self.birth_time_certainty.setEnabled(enabled)

        if enabled:
            self._toggle_birth_time_inputs(self.birth_time_certainty.currentIndex())
        else:
            self.birth_hour.setEnabled(False)
            self.birth_minute.setEnabled(False)

        self.calendar_type.setEnabled(enabled)
        self.gender.setEnabled(enabled)
        self.mbti_combo.setEnabled(enabled)
        self.birth_place.setEnabled(enabled)
        self.query_location_btn.setEnabled(enabled)
        self.birth_lng.setEnabled(enabled)
        self.save_profile_btn.setEnabled(enabled)

    def _toggle_birth_time_inputs(self, index):
        """根据时辰确定性切换时分输入框"""
        if index == 2:  # 不记得时辰
            self.birth_hour.setEnabled(False)
            self.birth_minute.setEnabled(False)
        else:
            self.birth_hour.setEnabled(True)
            self.birth_minute.setEnabled(True)

    def _toggle_additional_persons(self, state):
        """切换相关人八字输入区域的显示/隐藏"""
        visible = state == Qt.CheckState.Checked.value
        self.multi_person_widget.setVisible(visible)

    def _toggle_random_numbers(self, state):
        """切换随机数输入"""
        enabled = state == Qt.CheckState.Checked.value
        self.num1.setEnabled(enabled)
        self.num2.setEnabled(enabled)
        self.num3.setEnabled(enabled)

    def _save_profile(self):
        """保存当前出生信息为常用档案"""
        # 检查档案数量限制
        if not self.profile_manager.can_add_profile():
            reply = QMessageBox.question(
                self,
                "档案已满",
                f"已达到最大档案数量({self.profile_manager.MAX_PROFILES})。\n\n是否更新现有档案？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return

        # 获取档案标签
        label, ok = QInputDialog.getText(
            self,
            "保存档案",
            "请输入档案标签（如: 本人、配偶、父亲等）:"
        )

        if not ok or not label.strip():
            return

        # 收集当前出生信息
        profile = self._collect_birth_info(label.strip())

        # 保存档案
        if self.profile_manager.save_profile(profile):
            QMessageBox.information(self, "成功", f"档案 \"{label.strip()}\" 已保存")
        else:
            QMessageBox.warning(self, "失败", "保存档案失败，请查看日志")

    def _collect_birth_info(self, label: str) -> PersonBirthInfo:
        """收集当前表单的出生信息"""
        certainty_index = self.birth_time_certainty.currentIndex()
        certainty_map = {0: "certain", 1: "uncertain", 2: "unknown"}
        birth_time_certainty = certainty_map[certainty_index]

        birth_hour = None
        birth_minute = None
        if certainty_index != 2:
            birth_hour = self.birth_hour.value()
            birth_minute = self.birth_minute.value()

        calendar_type = "lunar" if self.calendar_type.currentText() == "农历" else "solar"
        gender = "female" if self.gender.currentText() == "女" else "male"

        birth_place_lng = None
        if self.birth_lng.text().strip():
            try:
                birth_place_lng = float(self.birth_lng.text())
            except ValueError:
                pass

        mbti_type = None
        mbti_text = self.mbti_combo.currentText()
        if mbti_text and mbti_text != "请选择":
            mbti_type = mbti_text.split("-")[0]

        return PersonBirthInfo(
            label=label,
            birth_year=self.birth_year.value(),
            birth_month=self.birth_month.value(),
            birth_day=self.birth_day.value(),
            birth_hour=birth_hour,
            birth_minute=birth_minute,
            calendar_type=calendar_type,
            birth_time_certainty=birth_time_certainty,
            gender=gender,
            birth_place_lng=birth_place_lng,
            mbti_type=mbti_type
        )

    def _load_profile(self):
        """加载常用档案"""
        dialog = ProfileManagerDialog(self)
        dialog.profile_selected.connect(self._apply_profile)
        dialog.exec()

    def _apply_profile(self, profile: PersonBirthInfo):
        """将档案数据应用到表单"""
        # 勾选"提供出生信息"
        self.use_birth_info.setChecked(True)

        # 填充数据
        if profile.birth_year:
            self.birth_year.setValue(profile.birth_year)
        if profile.birth_month:
            self.birth_month.setValue(profile.birth_month)
        if profile.birth_day:
            self.birth_day.setValue(profile.birth_day)

        # 时辰确定性
        certainty_map = {"certain": 0, "uncertain": 1, "unknown": 2}
        self.birth_time_certainty.setCurrentIndex(
            certainty_map.get(profile.birth_time_certainty, 0)
        )

        if profile.birth_hour is not None:
            self.birth_hour.setValue(profile.birth_hour)
        if profile.birth_minute is not None:
            self.birth_minute.setValue(profile.birth_minute)

        # 历法
        if profile.calendar_type == "lunar":
            self.calendar_type.setCurrentIndex(1)
        else:
            self.calendar_type.setCurrentIndex(0)

        # 性别
        if profile.gender == "female":
            self.gender.setCurrentIndex(1)
        else:
            self.gender.setCurrentIndex(0)

        # 经度
        if profile.birth_place_lng is not None:
            self.birth_lng.setText(str(profile.birth_place_lng))

        # MBTI
        if profile.mbti_type:
            for i in range(self.mbti_combo.count()):
                if self.mbti_combo.itemText(i).startswith(profile.mbti_type):
                    self.mbti_combo.setCurrentIndex(i)
                    break

    def _add_person(self):
        """添加额外人物"""
        try:
            dialog = PersonBirthInfoDialog(parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                person = dialog.get_person()
                if person:
                    self.additional_persons.append(person)
                    self._refresh_persons_list()
                    self.logger.info(f"成功添加人物: {person.label}")
        except Exception as e:
            self.logger.error(f"添加人物时出错: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "添加失败", f"添加人物时发生错误：\n\n{str(e)}")

    def _edit_person(self):
        """编辑选中的人物"""
        try:
            current_item = self.additional_persons_list.currentItem()
            if not current_item:
                QMessageBox.information(self, "提示", "请先选择要编辑的人物")
                return

            index = self.additional_persons_list.currentRow()
            person = self.additional_persons[index]

            dialog = PersonBirthInfoDialog(person=person, parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                updated_person = dialog.get_person()
                if updated_person:
                    self.additional_persons[index] = updated_person
                    self._refresh_persons_list()
                    self.logger.info(f"成功编辑人物: {updated_person.label}")
        except Exception as e:
            self.logger.error(f"编辑人物时出错: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "编辑失败", f"编辑人物时发生错误：\n\n{str(e)}")

    def _remove_person(self):
        """删除选中的人物"""
        try:
            current_item = self.additional_persons_list.currentItem()
            if not current_item:
                QMessageBox.information(self, "提示", "请先选择要删除的人物")
                return

            index = self.additional_persons_list.currentRow()
            person = self.additional_persons[index]

            reply = QMessageBox.question(
                self,
                "确认删除",
                f"确定要删除人物 \"{person.label}\" 吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                del self.additional_persons[index]
                self._refresh_persons_list()
                self.logger.info(f"成功删除人物: {person.label}")
        except Exception as e:
            self.logger.error(f"删除人物时出错: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "删除失败", f"删除人物时发生错误：\n\n{str(e)}")

    def _on_person_selection_changed(self):
        """人物列表选择改变"""
        has_selection = len(self.additional_persons_list.selectedItems()) > 0
        self.edit_person_btn.setEnabled(has_selection)
        self.remove_person_btn.setEnabled(has_selection)

    def _refresh_persons_list(self):
        """刷新人物列表显示"""
        self.additional_persons_list.clear()

        if not self.additional_persons:
            item = QListWidgetItem("暂无添加的人物")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.additional_persons_list.addItem(item)
        else:
            for person in self.additional_persons:
                birth_date = f"{person.birth_year}年{person.birth_month}月{person.birth_day}日"
                time_info = ""
                if person.birth_hour is not None:
                    time_info = f" {person.birth_hour}:{person.birth_minute:02d}"
                elif person.birth_time_certainty == "unknown":
                    time_info = " (时辰不详)"

                item_text = f"{person.label}: {birth_date}{time_info}"
                self.additional_persons_list.addItem(item_text)

    def _query_location(self):
        """查询出生地点经纬度"""
        address = self.birth_place.text().strip()
        if not address:
            QMessageBox.warning(self, "提示", "请输入出生地点")
            return

        self.query_location_btn.setEnabled(False)
        self.query_location_btn.setText("查询中...")

        self.geocode_worker = GeocodeWorker(address)
        self.geocode_worker.finished.connect(self._on_geocode_finished)
        self.geocode_worker.error.connect(self._on_geocode_error)
        self.geocode_worker.start()

    def _on_geocode_finished(self, result):
        """地理编码查询完成"""
        self.query_location_btn.setEnabled(True)
        self.query_location_btn.setText("查询经纬度")
        longitude = result['longitude']
        self.birth_lng.setText(str(longitude))
        formatted_address = result.get('formatted_address', '')
        QMessageBox.information(
            self, "查询成功",
            f"地址：{formatted_address}\n经度：{longitude}"
        )

    def _on_geocode_error(self, error_msg):
        """地理编码查询失败"""
        self.query_location_btn.setEnabled(True)
        self.query_location_btn.setText("查询经纬度")
        QMessageBox.warning(self, "查询失败", error_msg)

    def get_additional_persons(self) -> List[PersonBirthInfo]:
        """获取额外人物列表"""
        return self.additional_persons.copy()

    def cleanup(self):
        """清理资源"""
        if self.geocode_worker:
            try:
                self.geocode_worker.finished.disconnect()
                self.geocode_worker.error.disconnect()
            except Exception as e:
                self.logger.debug(f"清理geocode_worker信号失败: {e}")
