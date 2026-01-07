"""
ProgressWidget - 进度显示组件

结合文字描述和进度条，提供有情绪价值的进度反馈
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QProgressBar, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from typing import Optional, List
import random


class ProgressWidget(QWidget):
    """进度显示组件"""

    # 信号：进度完成
    completed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_progress = 0
        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 主标题
        self.title_label = QLabel("正在分析中...")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)

        # 阶段描述
        self.stage_label = QLabel("")
        stage_font = QFont()
        stage_font.setPointSize(10)
        self.stage_label.setFont(stage_font)
        self.stage_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stage_label.setStyleSheet("color: #5E9EA0;")
        layout.addWidget(self.stage_label)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #BBDEFB;
                border-radius: 8px;
                text-align: center;
                height: 28px;
                background-color: #F5F5F5;
            }
            QProgressBar::chunk {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #64B5F6,
                    stop:1 #81C784
                );
                border-radius: 6px;
            }
        """)
        layout.addWidget(self.progress_bar)

        # 详细描述（带情绪价值）
        self.detail_label = QLabel("")
        detail_font = QFont()
        detail_font.setPointSize(9)
        self.detail_label.setFont(detail_font)
        self.detail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detail_label.setWordWrap(True)
        layout.addWidget(self.detail_label)

        # 预估时间
        self.time_label = QLabel("")
        time_font = QFont()
        time_font.setPointSize(9)
        self.time_label.setFont(time_font)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.time_label)

        layout.addStretch()

        self.setLayout(layout)

        # 样式 - 移除硬编码颜色，使用主题色
        self.setStyleSheet("""
            ProgressWidget {
                border-radius: 8px;
            }
        """)

    def set_progress(
        self,
        progress: int,
        stage: str = "",
        detail: str = "",
        estimated_seconds: Optional[int] = None
    ):
        """
        设置进度

        Args:
            progress: 进度值（0-100）
            stage: 阶段名称（如"八字分析"）
            detail: 详细描述（带情绪价值的文字）
            estimated_seconds: 预估剩余秒数
        """
        self.current_progress = progress
        self.progress_bar.setValue(progress)

        # 更新阶段
        if stage:
            self.stage_label.setText(f"[步骤 {progress}%] {stage}")

        # 更新详细描述
        if detail:
            self.detail_label.setText(detail)

        # 更新预估时间
        if estimated_seconds is not None:
            if estimated_seconds > 0:
                time_text = self._format_time(estimated_seconds)
                self.time_label.setText(f"⏱️ 预计还需 {time_text}")
            else:
                self.time_label.setText("⏱️ 即将完成...")

        # 如果完成，触发信号
        if progress >= 100:
            self.completed.emit()

    def set_stage_with_emotion(
        self,
        progress: int,
        stage: str,
        question_type: str,
        base_message: str
    ):
        """
        设置带情绪价值的阶段描述

        Args:
            progress: 进度值
            stage: 阶段名称
            question_type: 用户问题类型（用于个性化文字）
            base_message: 基础消息
        """
        # 根据问题类型生成个性化的情绪文字
        emotional_messages = self._generate_emotional_message(question_type, stage)

        # 随机选择一条
        detail = random.choice(emotional_messages) if emotional_messages else base_message

        self.set_progress(progress, stage, detail)

    def _generate_emotional_message(self, question_type: str, stage: str) -> List[str]:
        """
        生成带情绪价值的文字

        Args:
            question_type: 问题类型
            stage: 当前阶段

        Returns:
            可能的情绪文字列表
        """
        messages = {
            "事业发展": {
                "八字分析": [
                    "正在为您解读事业命盘，分析您的职场优势和发展方向... 🌟",
                    "仔细查看您的事业宫位，寻找最佳的晋升时机... 📈",
                    "分析您的天赋特质，发现最适合您的职业道路... 💼"
                ],
                "奇门分析": [
                    "正在排奇门局，为您寻找事业发展的吉利方位... 🧭",
                    "分析当前时空能量，找到助力您事业的贵人方向... ✨"
                ],
                "六壬分析": [
                    "推演事业发展的关键节点，助您把握先机... 🎯",
                    "细化您的职场运势走向，让您做出明智决策... 📊"
                ]
            },
            "财富运势": {
                "八字分析": [
                    "正在分析您的财帛宫，解读财运密码... 💰",
                    "查看您的财星配置，寻找生财之道... 💎",
                    "解析您的财富格局，发现增收机会... 📈"
                ],
                "奇门分析": [
                    "定位财源方位，为您指明投资方向... 🧭",
                    "分析当前财运趋势，找到最佳理财时机... ⏰"
                ],
                "六壬分析": [
                    "推演财运发展脉络，助您规避风险... 🛡️",
                    "细化财富增长路径，让机会不再错过... 🎯"
                ]
            },
            "感情婚姻": {
                "八字分析": [
                    "正在解读您的感情宫位，分析情感状况... 💕",
                    "查看您的感情格局，理解情感走势... 💑",
                    "分析感情能量配置，为您提供参考... 🌸"
                ],
                "奇门分析": [
                    "分析感情方位能量，寻找有利因素... 🧭",
                    "解读感情时空格局，提供策略建议... ✨"
                ],
                "六壬分析": [
                    "推演感情发展趋势，让您心中有数... 💝",
                    "细化情感变化过程，助您做出决策... 🎯"
                ]
            },
            "健康养生": {
                "八字分析": [
                    "正在分析您的身体能量场，关注健康隐患... 🏥",
                    "查看五行平衡状态，给出养生建议... 🌿",
                    "解读体质特点，制定调理方案... 💊"
                ],
                "奇门分析": [
                    "寻找有利健康的方位和时机... 🧭",
                    "分析当前气场，提示注意事项... ⚠️"
                ],
                "六壬分析": [
                    "推演健康趋势，提前预防疾病... 🛡️",
                    "细化调养时机，助您恢复元气... 💪"
                ]
            }
        }

        # 默认通用消息
        default_messages = {
            "八字分析": [
                "正在排四柱命盘，深入分析您的命运密码... 🔮",
                "仔细查看您的命理格局，寻找关键信息... 📜"
            ],
            "奇门分析": [
                "正在排奇门遁甲局，分析时空能量... 🧭",
                "解读奇门格局，为您指引方向... ✨"
            ],
            "六壬分析": [
                "正在起大六壬课，推演事态发展... 🎯",
                "分析六壬课体，细化过程变化... 📊"
            ],
            "综合分析": [
                "正在综合多个理论的智慧，为您生成完整报告... 📝",
                "融合古今智慧，为您提供最有价值的建议... 💡"
            ]
        }

        # 尝试获取个性化消息
        if question_type in messages and stage in messages[question_type]:
            return messages[question_type][stage]

        # 回退到默认消息
        if stage in default_messages:
            return default_messages[stage]

        return ["努力分析中，请稍候..."]

    def _format_time(self, seconds: int) -> str:
        """格式化时间显示"""
        if seconds < 60:
            return f"{seconds}秒"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}分{secs}秒"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}小时{minutes}分"

    def reset(self):
        """重置进度"""
        self.current_progress = 0
        self.progress_bar.setValue(0)
        self.title_label.setText("正在分析中...")
        self.stage_label.setText("")
        self.detail_label.setText("")
        self.time_label.setText("")

    def show_completion(self, message: str = "分析完成！"):
        """显示完成状态"""
        self.progress_bar.setValue(100)
        self.title_label.setText("✅ " + message)
        self.stage_label.setText("")
        self.detail_label.setText("感谢您的耐心等待，现在为您呈现完整的分析结果。")
        self.time_label.setText("")

    def show_error(self, error_message: str):
        """显示错误状态"""
        self.title_label.setText("❌ 分析失败")
        self.stage_label.setText("")
        self.detail_label.setText(error_message)
        self.time_label.setText("")
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #FFCDD2;
                border-radius: 8px;
                text-align: center;
                height: 28px;
                background-color: #F5F5F5;
            }
            QProgressBar::chunk {
                background-color: #EF5350;
                border-radius: 6px;
            }
        """)
