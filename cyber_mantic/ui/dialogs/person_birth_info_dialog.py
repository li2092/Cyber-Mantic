"""
个人出生信息输入对话框
用于添加/编辑多人八字信息
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QSpinBox, QComboBox, QPushButton,
    QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt
from typing import Optional
from models import PersonBirthInfo


class PersonBirthInfoDialog(QDialog):
    """个人出生信息输入对话框"""

    def __init__(self, person: Optional[PersonBirthInfo] = None, parent=None):
        """
        初始化对话框

        Args:
            person: 要编辑的个人信息，None表示新建
            parent: 父窗口
        """
        super().__init__(parent)
        self.person = person
        self.is_edit_mode = person is not None

        self.setWindowTitle("编辑人物信息" if self.is_edit_mode else "添加人物信息")
        self.setModal(True)
        self.setMinimumWidth(500)

        self._init_ui()
        if self.is_edit_mode:
            self._load_person_data()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 人物标签
        label_layout = QHBoxLayout()
        label_layout.addWidget(QLabel("人物标签:"))
        self.label_input = QLineEdit()
        self.label_input.setPlaceholderText("如: 本人、配偶、父亲、母亲等")
        self.label_input.setMinimumHeight(32)
        label_layout.addWidget(self.label_input, 1)
        layout.addLayout(label_layout)

        # 出生日期
        birth_group = QGroupBox("出生日期")
        birth_layout = QFormLayout()
        birth_layout.setSpacing(10)

        # 年月日
        date_layout = QHBoxLayout()
        self.birth_year = QSpinBox()
        self.birth_year.setRange(1900, 2030)
        self.birth_year.setValue(1990)
        self.birth_year.setMinimumHeight(32)
        date_layout.addWidget(self.birth_year)
        date_layout.addWidget(QLabel("年"))

        self.birth_month = QSpinBox()
        self.birth_month.setRange(1, 12)
        self.birth_month.setValue(1)
        self.birth_month.setMinimumHeight(32)
        date_layout.addWidget(self.birth_month)
        date_layout.addWidget(QLabel("月"))

        self.birth_day = QSpinBox()
        self.birth_day.setRange(1, 31)
        self.birth_day.setValue(1)
        self.birth_day.setMinimumHeight(32)
        date_layout.addWidget(self.birth_day)
        date_layout.addWidget(QLabel("日"))
        date_layout.addStretch()

        birth_layout.addRow("日期:", date_layout)

        # 时辰确定性
        certainty_layout = QHBoxLayout()
        self.birth_time_certainty = QComboBox()
        self.birth_time_certainty.addItems([
            "记得时辰",
            "大概是这个时辰",
            "不记得时辰"
        ])
        self.birth_time_certainty.setMinimumHeight(32)
        self.birth_time_certainty.currentIndexChanged.connect(self._toggle_time_inputs)
        certainty_layout.addWidget(self.birth_time_certainty)
        certainty_layout.addStretch()
        birth_layout.addRow("时辰确定性:", certainty_layout)

        # 时分
        time_layout = QHBoxLayout()
        self.birth_hour = QSpinBox()
        self.birth_hour.setRange(0, 23)
        self.birth_hour.setValue(12)
        self.birth_hour.setMinimumHeight(32)
        time_layout.addWidget(self.birth_hour)
        time_layout.addWidget(QLabel("时"))

        self.birth_minute = QSpinBox()
        self.birth_minute.setRange(0, 59)
        self.birth_minute.setValue(0)
        self.birth_minute.setMinimumHeight(32)
        time_layout.addWidget(self.birth_minute)
        time_layout.addWidget(QLabel("分"))
        time_layout.addStretch()

        birth_layout.addRow("时间:", time_layout)

        # 历法
        calendar_layout = QHBoxLayout()
        self.calendar_type = QComboBox()
        self.calendar_type.addItems(["阳历", "农历"])
        self.calendar_type.setMinimumHeight(32)
        calendar_layout.addWidget(self.calendar_type)
        calendar_layout.addStretch()
        birth_layout.addRow("历法:", calendar_layout)

        birth_group.setLayout(birth_layout)
        layout.addWidget(birth_group)

        # 个人信息
        info_group = QGroupBox("个人信息")
        info_layout = QFormLayout()
        info_layout.setSpacing(10)

        # 性别
        gender_layout = QHBoxLayout()
        self.gender = QComboBox()
        self.gender.addItems(["男", "女"])
        self.gender.setMinimumHeight(32)
        gender_layout.addWidget(self.gender)
        gender_layout.addStretch()
        info_layout.addRow("性别:", gender_layout)

        # 经度（可选）
        lng_layout = QHBoxLayout()
        self.birth_lng = QLineEdit()
        self.birth_lng.setPlaceholderText("如: 120.5 (可选)")
        self.birth_lng.setMinimumHeight(32)
        lng_layout.addWidget(self.birth_lng)
        lng_layout.addStretch()
        info_layout.addRow("出生地经度:", lng_layout)

        # MBTI（可选）
        mbti_layout = QHBoxLayout()
        self.mbti_combo = QComboBox()
        self.mbti_combo.addItems([
            "请选择",
            "INTJ-建筑师", "INTP-逻辑学家", "ENTJ-指挥官", "ENTP-辩论家",
            "INFJ-提倡者", "INFP-调停者", "ENFJ-主人公", "ENFP-竞选者",
            "ISTJ-物流师", "ISFJ-守卫者", "ESTJ-总经理", "ESFJ-执政官",
            "ISTP-鉴赏家", "ISFP-探险家", "ESTP-企业家", "ESFP-表演者"
        ])
        self.mbti_combo.setMinimumHeight(32)
        mbti_layout.addWidget(self.mbti_combo)
        mbti_layout.addStretch()
        info_layout.addRow("MBTI类型:", mbti_layout)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setMinimumSize(100, 36)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("保存" if self.is_edit_mode else "添加")
        save_btn.setMinimumSize(100, 36)
        save_btn.clicked.connect(self._save)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def _toggle_time_inputs(self, index):
        """根据时辰确定性切换时分输入框"""
        enabled = index != 2  # 不记得时辰时禁用
        self.birth_hour.setEnabled(enabled)
        self.birth_minute.setEnabled(enabled)

    def _load_person_data(self):
        """加载人物数据到表单"""
        if not self.person:
            return

        self.label_input.setText(self.person.label)

        if self.person.birth_year:
            self.birth_year.setValue(self.person.birth_year)
        if self.person.birth_month:
            self.birth_month.setValue(self.person.birth_month)
        if self.person.birth_day:
            self.birth_day.setValue(self.person.birth_day)

        # 时辰确定性
        certainty_map = {"certain": 0, "uncertain": 1, "unknown": 2}
        self.birth_time_certainty.setCurrentIndex(
            certainty_map.get(self.person.birth_time_certainty, 0)
        )

        if self.person.birth_hour is not None:
            self.birth_hour.setValue(self.person.birth_hour)
        if self.person.birth_minute is not None:
            self.birth_minute.setValue(self.person.birth_minute)

        # 历法
        if self.person.calendar_type == "lunar":
            self.calendar_type.setCurrentIndex(1)

        # 性别
        if self.person.gender == "female":
            self.gender.setCurrentIndex(1)

        # 经度
        if self.person.birth_place_lng is not None:
            self.birth_lng.setText(str(self.person.birth_place_lng))

        # MBTI
        if self.person.mbti_type:
            for i in range(self.mbti_combo.count()):
                if self.mbti_combo.itemText(i).startswith(self.person.mbti_type):
                    self.mbti_combo.setCurrentIndex(i)
                    break

    def _save(self):
        """保存数据"""
        label = self.label_input.text().strip()
        if not label:
            QMessageBox.warning(self, "验证错误", "请输入人物标签")
            return

        # 获取时辰确定性
        certainty_index = self.birth_time_certainty.currentIndex()
        certainty_map = {0: "certain", 1: "uncertain", 2: "unknown"}
        birth_time_certainty = certainty_map[certainty_index]

        # 获取时分
        birth_hour = None
        birth_minute = None
        if certainty_index != 2:  # 不是"不记得时辰"
            birth_hour = self.birth_hour.value()
            birth_minute = self.birth_minute.value()

        # 获取历法
        calendar_type = "lunar" if self.calendar_type.currentText() == "农历" else "solar"

        # 获取性别
        gender = "female" if self.gender.currentText() == "女" else "male"

        # 获取经度
        birth_place_lng = None
        if self.birth_lng.text().strip():
            try:
                birth_place_lng = float(self.birth_lng.text())
            except ValueError:
                QMessageBox.warning(self, "验证错误", "经度格式不正确")
                return

        # 获取MBTI
        mbti_type = None
        mbti_text = self.mbti_combo.currentText()
        if mbti_text and mbti_text != "请选择":
            mbti_type = mbti_text.split("-")[0]

        # 创建PersonBirthInfo对象
        self.person = PersonBirthInfo(
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

        self.accept()

    def get_person(self) -> Optional[PersonBirthInfo]:
        """获取人物信息"""
        return self.person
