"""
梅花易数理论类
"""
from typing import Dict, Any, List, Optional, Tuple
from models import UserInput
from theories.base import BaseTheory
from .constants import *


class MeiHuaTheory(BaseTheory):
    """梅花易数理论"""

    def __init__(self):
        super().__init__()

    def get_name(self) -> str:
        return "梅花易数"

    def get_required_fields(self) -> List[str]:
        return []  # 梅花易数支持多种起卦方式

    def get_optional_fields(self) -> List[str]:
        return ["numbers", "character", "favorite_color", "current_direction", "current_time"]

    def get_field_weights(self) -> Dict[str, float]:
        return {
            "numbers": 0.3,
            "character": 0.2,
            "favorite_color": 0.2,
            "current_direction": 0.2,
            "current_time": 0.1
        }

    def get_min_completeness(self) -> float:
        return 0.0  # 至少有一种起卦方式即可

    def calculate(self, user_input: UserInput) -> Dict[str, Any]:
        """
        计算梅花易数

        Args:
            user_input: 用户输入

        Returns:
            梅花易数计算结果
        """
        # 检查是否有多人分析请求
        if hasattr(user_input, 'additional_persons') and user_input.additional_persons:
            self.logger.warning(
                f"{self.get_name()}暂不支持多人分析，将仅分析主要咨询者，"
                f"忽略其他{len(user_input.additional_persons)}人的信息"
            )

        # 确定起卦方式
        upper_num, lower_num, dong_yao = self._get_numbers(user_input)

        # 起卦
        upper_gua = self._number_to_gua(upper_num)
        lower_gua = self._number_to_gua(lower_num)

        # 本卦
        original_gua = self._create_gua(upper_gua, lower_gua)

        # 互卦
        mutual_gua = self._get_mutual_gua(upper_gua, lower_gua)

        # 变卦
        changed_gua = self._get_changed_gua(upper_gua, lower_gua, dong_yao)

        # 体用分析
        ti_yong = self._analyze_ti_yong(dong_yao, upper_gua, lower_gua)

        # 吉凶判断
        judgment_result = self._judge_result(ti_yong)

        # 应期分析
        response_time = self._analyze_response_time(ti_yong, dong_yao)

        return {
            "起卦方式": self._get_qigua_method(user_input),
            "起卦数字": [upper_num, lower_num, dong_yao],
            "本卦": original_gua,
            "互卦": mutual_gua,
            "变卦": changed_gua,
            "体卦": ti_yong["体卦"],
            "用卦": ti_yong["用卦"],
            "体用关系": ti_yong["关系"],
            "体用五行": ti_yong["五行"],
            "动爻": dong_yao,
            "judgment": judgment_result["judgment"],
            "judgment_level": judgment_result["judgment_level"],
            "判断说明": judgment_result["说明"],
            "应期": response_time,
            "advice": judgment_result["建议"],
            "confidence": 0.75
        }

    def _get_numbers(self, user_input: UserInput) -> Tuple[int, int, int]:
        """
        获取起卦数字

        Returns:
            (上卦数, 下卦数, 动爻数)
        """
        if user_input.numbers and len(user_input.numbers) >= 2:
            # 数字起卦
            upper_num = user_input.numbers[0]
            lower_num = user_input.numbers[1]
            dong_yao = user_input.numbers[2] if len(user_input.numbers) >= 3 else (upper_num + lower_num)
            return upper_num, lower_num, dong_yao

        elif user_input.favorite_color:
            # 颜色起卦
            gua_name = COLOR_TO_GUA.get(user_input.favorite_color, "震")
            gua_num = BA_GUA[gua_name]["序号"]
            current_time = user_input.current_time
            time_num = current_time.hour + current_time.minute
            return gua_num, time_num % 8 + 1, (gua_num + time_num) % 6 + 1

        elif user_input.current_direction:
            # 方位起卦
            gua_name = DIRECTION_TO_GUA.get(user_input.current_direction, "震")
            gua_num = BA_GUA[gua_name]["序号"]
            current_time = user_input.current_time
            time_num = current_time.hour + current_time.minute
            return gua_num, time_num % 8 + 1, (gua_num + time_num) % 6 + 1

        else:
            # 时间起卦
            current_time = user_input.current_time
            upper_num = (current_time.month + current_time.day) % 8
            lower_num = (current_time.month + current_time.day + current_time.hour) % 8
            dong_yao = (current_time.month + current_time.day + current_time.hour) % 6
            # 确保数字在1-8之间
            upper_num = upper_num if upper_num > 0 else 8
            lower_num = lower_num if lower_num > 0 else 8
            dong_yao = dong_yao if dong_yao > 0 else 6
            return upper_num, lower_num, dong_yao

    def _number_to_gua(self, num: int) -> str:
        """将数字转换为卦名"""
        index = (num - 1) % 8
        return BA_GUA_ORDER[index]

    def _create_gua(self, upper_gua: str, lower_gua: str) -> Dict[str, Any]:
        """
        创建卦象

        Args:
            upper_gua: 上卦
            lower_gua: 下卦

        Returns:
            卦象信息
        """
        gua_name = GUA_64_NAMES.get((upper_gua, lower_gua), f"{upper_gua}{lower_gua}")
        return {
            "名称": gua_name,
            "上卦": upper_gua,
            "下卦": lower_gua,
            "卦象": f"{BA_GUA[upper_gua]['卦象']}{BA_GUA[lower_gua]['卦象']}",
            "上卦五行": BA_GUA[upper_gua]["五行"],
            "下卦五行": BA_GUA[lower_gua]["五行"]
        }

    def _get_mutual_gua(self, upper_gua: str, lower_gua: str) -> Dict[str, Any]:
        """
        求互卦

        互卦取法：本卦2、3、4爻为下卦，3、4、5爻为上卦
        简化处理：根据上下卦的五行属性推算
        """
        # 简化实现：根据上下卦序号计算
        upper_num = BA_GUA[upper_gua]["序号"]
        lower_num = BA_GUA[lower_gua]["序号"]

        # 互卦上卦
        mutual_upper_num = ((upper_num + lower_num) // 2) % 8
        mutual_upper_num = mutual_upper_num if mutual_upper_num > 0 else 8
        mutual_upper = BA_GUA_ORDER[mutual_upper_num - 1]

        # 互卦下卦
        mutual_lower_num = ((upper_num + lower_num + 1) // 2) % 8
        mutual_lower_num = mutual_lower_num if mutual_lower_num > 0 else 8
        mutual_lower = BA_GUA_ORDER[mutual_lower_num - 1]

        return self._create_gua(mutual_upper, mutual_lower)

    def _get_changed_gua(self, upper_gua: str, lower_gua: str, dong_yao: int) -> Dict[str, Any]:
        """
        求变卦

        变卦：动爻所在的卦变化
        """
        # 动爻在下卦（1-3爻）
        if dong_yao <= 3:
            # 下卦变化
            lower_num = BA_GUA[lower_gua]["序号"]
            changed_lower_num = (lower_num + dong_yao) % 8
            changed_lower_num = changed_lower_num if changed_lower_num > 0 else 8
            changed_lower = BA_GUA_ORDER[changed_lower_num - 1]
            return self._create_gua(upper_gua, changed_lower)
        else:
            # 上卦变化
            upper_num = BA_GUA[upper_gua]["序号"]
            changed_upper_num = (upper_num + dong_yao) % 8
            changed_upper_num = changed_upper_num if changed_upper_num > 0 else 8
            changed_upper = BA_GUA_ORDER[changed_upper_num - 1]
            return self._create_gua(changed_upper, lower_gua)

    def _analyze_ti_yong(self, dong_yao: int, upper_gua: str, lower_gua: str) -> Dict[str, Any]:
        """
        分析体用关系

        体用取法：
        - 动爻在上卦，则上卦为用卦，下卦为体卦
        - 动爻在下卦，则下卦为用卦，上卦为体卦
        """
        if dong_yao <= 3:
            # 动爻在下卦
            ti_gua = upper_gua
            yong_gua = lower_gua
        else:
            # 动爻在上卦
            ti_gua = lower_gua
            yong_gua = upper_gua

        # 五行
        ti_wuxing = BA_GUA[ti_gua]["五行"]
        yong_wuxing = BA_GUA[yong_gua]["五行"]

        # 体用关系
        relation = self._get_ti_yong_relation(ti_wuxing, yong_wuxing)

        return {
            "体卦": ti_gua,
            "用卦": yong_gua,
            "五行": {"体": ti_wuxing, "用": yong_wuxing},
            "关系": relation
        }

    def _get_ti_yong_relation(self, ti_wuxing: str, yong_wuxing: str) -> str:
        """
        获取体用关系

        Args:
            ti_wuxing: 体卦五行
            yong_wuxing: 用卦五行

        Returns:
            体用关系
        """
        if ti_wuxing == yong_wuxing:
            return "比和"
        elif WUXING_SHENG[ti_wuxing] == yong_wuxing:
            return "体生用"
        elif WUXING_SHENG[yong_wuxing] == ti_wuxing:
            return "用生体"
        elif WUXING_KE[ti_wuxing] == yong_wuxing:
            return "体克用"
        elif WUXING_KE[yong_wuxing] == ti_wuxing:
            return "用克体"
        else:
            return "比和"

    def _judge_result(self, ti_yong: Dict[str, Any]) -> Dict[str, Any]:
        """
        判断吉凶

        Args:
            ti_yong: 体用分析结果

        Returns:
            判断结果
        """
        relation = ti_yong["关系"]
        relation_info = TI_YONG_RELATION[relation]

        judgment = relation_info["吉凶"]
        judgment_level = relation_info["程度"]
        explanation = relation_info["说明"]

        # 生成建议
        advice = self._generate_advice(relation, ti_yong)

        return {
            "judgment": judgment,
            "judgment_level": judgment_level,
            "说明": explanation,
            "建议": advice
        }

    def _generate_advice(self, relation: str, ti_yong: Dict[str, Any]) -> str:
        """生成建议"""
        advice_map = {
            "用生体": "此事有贵人相助，可顺势而为，积极推进",
            "体克用": "此事在我掌控之中，可以主动出击，把握机会",
            "比和": "此事平稳发展，保持现状即可，不宜冒进",
            "体生用": "此事耗费精力，建议谨慎行事，量力而行",
            "用克体": "此事困难重重，宜退守观望，等待时机"
        }
        return advice_map.get(relation, "请谨慎决策")

    def _analyze_response_time(self, ti_yong: Dict[str, Any], dong_yao: int) -> Dict[str, str]:
        """
        分析应期

        Args:
            ti_yong: 体用分析
            dong_yao: 动爻

        Returns:
            应期信息
        """
        # 简化处理：根据动爻位置判断应期
        yao_time_map = {
            1: "数日内", 2: "本月内", 3: "季度内",
            4: "半年内", 5: "本年内", 6: "年底前"
        }

        time_range = yao_time_map.get(dong_yao, "近期")

        return {
            "时间": time_range,
            "依据": f"动爻在第{dong_yao}爻"
        }

    def _get_qigua_method(self, user_input: UserInput) -> str:
        """获取起卦方式说明"""
        if user_input.numbers:
            return "数字起卦"
        elif user_input.favorite_color:
            return "颜色起卦"
        elif user_input.current_direction:
            return "方位起卦"
        else:
            return "时间起卦"

    def to_standard_answer(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """转换为标准答案格式"""
        return {
            'judgment': result.get('judgment', '平'),
            'judgment_level': result.get('judgment_level', 0.5),
            'timing': result.get('应期'),
            'advice': result.get('advice'),
            'confidence': result.get('confidence', 0.75)
        }
