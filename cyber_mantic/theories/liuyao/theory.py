"""
六爻理论类
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from models import UserInput
from theories.base import BaseTheory


class LiuYaoTheory(BaseTheory):
    """六爻理论"""

    # 八卦基本属性
    BA_GUA = {
        "乾": {"五行": "金", "序号": 0},
        "兑": {"五行": "金", "序号": 1},
        "离": {"五行": "火", "序号": 2},
        "震": {"五行": "木", "序号": 3},
        "巽": {"五行": "木", "序号": 4},
        "坎": {"五行": "水", "序号": 5},
        "艮": {"五行": "土", "序号": 6},
        "坤": {"五行": "土", "序号": 7},
    }

    # 六十四卦世应表（简化版）
    SHI_YING_MAP = {
        # 八纯卦：世在上爻
        ("乾", "乾"): 6, ("坤", "坤"): 6, ("震", "震"): 6, ("巽", "巽"): 6,
        ("坎", "坎"): 6, ("离", "离"): 6, ("艮", "艮"): 6, ("兑", "兑"): 6,
    }

    # 六亲关系（简化）
    LIU_QIN_MAP = {
        "父母": {"主事": "文书、房屋、长辈", "旺衰影响": "文书有利"},
        "兄弟": {"主事": "朋友、竞争、阻碍", "旺衰影响": "竞争激烈"},
        "子孙": {"主事": "子女、下属、解忧", "旺衰影响": "解除忧虑"},
        "妻财": {"主事": "钱财、妻子、利益", "旺衰影响": "财运亨通"},
        "官鬼": {"主事": "官职、丈夫、压力", "旺衰影响": "官运或压力"},
    }

    # 六神（简化）
    LIU_SHEN = ["青龙", "朱雀", "勾陈", "腾蛇", "白虎", "玄武"]

    def __init__(self):
        super().__init__()

    def get_name(self) -> str:
        return "六爻"

    def get_required_fields(self) -> List[str]:
        return ["numbers"]  # 需要6个数字或铜钱结果

    def get_optional_fields(self) -> List[str]:
        return ["current_time", "question_description"]

    def get_field_weights(self) -> Dict[str, float]:
        return {
            "numbers": 0.7,
            "current_time": 0.2,
            "question_description": 0.1
        }

    def get_min_completeness(self) -> float:
        return 0.6  # 至少需要数字起卦

    def calculate(self, user_input: UserInput) -> Dict[str, Any]:
        """
        计算六爻

        Args:
            user_input: 用户输入

        Returns:
            六爻计算结果
        """
        # 起卦
        yao_list = self._get_yao_list(user_input.numbers)

        # 求本卦和变卦
        ben_gua, bian_gua = self._get_hexagrams(yao_list)

        # 装卦（装世应、六亲、六神）
        装卦_result = self._zhuang_gua(ben_gua, yao_list)

        # 分析用神
        用神_analysis = self._analyze_yong_shen(user_input.question_type, 装卦_result)

        # 判断吉凶
        judgment_result = self._judge_result(装卦_result, 用神_analysis, yao_list)

        # 应期分析
        response_time = self._analyze_response_time(yao_list, 用神_analysis)

        result = {
            "起卦数字": user_input.numbers,
            "六爻": yao_list,
            "本卦": ben_gua,
            "变卦": bian_gua,
            "世爻": 装卦_result["世爻"],
            "应爻": 装卦_result["应爻"],
            "六爻详情": 装卦_result["六爻详情"],
            "用神": 用神_analysis,
            "动爻": [i + 1 for i, yao in enumerate(yao_list) if yao["动静"] == "动"],
            "judgment": judgment_result["judgment"],
            "judgment_level": judgment_result["judgment_level"],
            "判断依据": judgment_result["依据"],
            "应期": response_time,
            "advice": judgment_result["建议"],
            "confidence": 0.7
        }

        # 如果有额外人物信息（代人问事），添加说明
        if user_input.additional_persons and len(user_input.additional_persons) > 0:
            result["代问信息"] = self._analyze_proxy_inquiry(user_input)

        return result

    def _analyze_proxy_inquiry(self, user_input: UserInput) -> Dict[str, Any]:
        """
        分析代人问事的情况

        Args:
            user_input: 用户输入

        Returns:
            代问分析结果
        """
        proxy_info = {
            "问卦人": user_input.name or "本人",
            "代问人数": len(user_input.additional_persons),
            "代问说明": []
        }

        for person in user_input.additional_persons:
            # 根据问题类型调整用神选择
            yongshen_hint = self._get_proxy_yongshen_hint(person.label, user_input.question_type)

            person_info = {
                "姓名/标签": person.label,
                "关系说明": f"{user_input.name or '问卦人'}为{person.label}代问{user_input.question_type}事",
                "用神提示": yongshen_hint,
                "注意事项": [
                    "六爻以世爻代表问卦人，应爻通常代表所问之事或对方",
                    f"此卦为代{person.label}询问，解卦时需以{person.label}的立场进行分析",
                    "代问卦的灵验度取决于代问人与当事人的关系亲疏"
                ]
            }

            proxy_info["代问说明"].append(person_info)

        return proxy_info

    def _get_proxy_yongshen_hint(self, person_label: str, question_type: str) -> str:
        """
        根据代问人物和问题类型给出用神选择提示

        Args:
            person_label: 人物标签
            question_type: 问题类型

        Returns:
            用神提示
        """
        # 判断人物关系
        if any(kw in person_label for kw in ["父", "母", "爸", "妈", "爷", "奶"]):
            relation = "父母长辈"
            basic_yongshen = "父母爻"
        elif any(kw in person_label for kw in ["儿", "女", "子", "孩"]):
            relation = "子女晚辈"
            basic_yongshen = "子孙爻"
        elif any(kw in person_label for kw in ["配偶", "老公", "老婆", "丈夫", "妻子"]):
            relation = "配偶"
            basic_yongshen = "妻财爻（男测）或官鬼爻（女测）"
        elif any(kw in person_label for kw in ["兄", "弟", "姐", "妹"]):
            relation = "兄弟姐妹"
            basic_yongshen = "兄弟爻"
        else:
            relation = "其他人物"
            basic_yongshen = "需根据具体问题选择"

        # 根据问题类型调整
        if question_type == "事业":
            hint = f"代{relation}问事业，主要看官鬼爻，兼看{basic_yongshen}的旺衰"
        elif question_type == "财运":
            hint = f"代{relation}问财运，主要看妻财爻，兼看{basic_yongshen}的旺衰"
        elif question_type == "健康":
            hint = f"代{relation}问健康，主要看{basic_yongshen}，官鬼爻为病"
        elif question_type in ["婚姻", "感情"]:
            hint = f"代{relation}问婚姻，男看妻财爻，女看官鬼爻"
        else:
            hint = f"代{relation}问事，用神为{basic_yongshen}，需结合具体问题综合判断"

        return hint

    def _get_yao_list(self, numbers: List[int]) -> List[Dict[str, Any]]:
        """
        根据数字获取爻列表

        Args:
            numbers: 6个数字（1-6），代表6次摇卦

        Returns:
            爻列表
        """
        yao_list = []

        for i, num in enumerate(numbers[:6]):
            # 简化处理：1-2为老阳（动阳），3-4为少阴（静阴），5-6为少阳（静阳）
            if num <= 2:
                yao_type = "阳"
                dong_jing = "动"
            elif num <= 4:
                yao_type = "阴"
                dong_jing = "静"
            else:
                yao_type = "阳"
                dong_jing = "静"

            yao_list.append({
                "位置": i + 1,
                "阴阳": yao_type,
                "动静": dong_jing,
                "数字": num
            })

        return yao_list

    def _get_hexagrams(self, yao_list: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
        """
        获取本卦和变卦

        Args:
            yao_list: 爻列表

        Returns:
            (本卦, 变卦)
        """
        # 本卦：根据六爻的阴阳组成
        ben_gua_binary = ''.join(['1' if yao["阴阳"] == "阳" else '0' for yao in yao_list])

        # 简化处理：根据下三爻和上三爻确定卦名
        lower_gua = self._binary_to_gua(ben_gua_binary[:3])
        upper_gua = self._binary_to_gua(ben_gua_binary[3:])

        ben_gua = {
            "上卦": upper_gua,
            "下卦": lower_gua,
            "名称": f"{upper_gua}{lower_gua}"
        }

        # 变卦：如果有动爻，则计算变卦
        has_dong_yao = any(yao["动静"] == "动" for yao in yao_list)

        if has_dong_yao:
            bian_yao_list = []
            for yao in yao_list:
                if yao["动静"] == "动":
                    # 动爻变化（阳变阴，阴变阳）
                    bian_yao_list.append("阴" if yao["阴阳"] == "阳" else "阳")
                else:
                    bian_yao_list.append(yao["阴阳"])

            bian_binary = ''.join(['1' if y == "阳" else '0' for y in bian_yao_list])
            bian_lower_gua = self._binary_to_gua(bian_binary[:3])
            bian_upper_gua = self._binary_to_gua(bian_binary[3:])

            bian_gua = {
                "上卦": bian_upper_gua,
                "下卦": bian_lower_gua,
                "名称": f"{bian_upper_gua}{bian_lower_gua}"
            }
        else:
            bian_gua = None

        return ben_gua, bian_gua

    def _binary_to_gua(self, binary: str) -> str:
        """
        将三位二进制转换为卦名

        Args:
            binary: 三位二进制字符串

        Returns:
            卦名
        """
        gua_map = {
            "111": "乾", "110": "兑", "101": "离", "100": "震",
            "011": "巽", "010": "坎", "001": "艮", "000": "坤"
        }
        return gua_map.get(binary, "乾")

    def _zhuang_gua(self, ben_gua: Dict[str, Any], yao_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        装卦（装世应、六亲、六神）

        Args:
            ben_gua: 本卦
            yao_list: 爻列表

        Returns:
            装卦结果
        """
        # 确定世应（简化处理）
        shi_yao = self.SHI_YING_MAP.get((ben_gua["上卦"], ben_gua["下卦"]), 5)
        ying_yao = (shi_yao + 3) % 6
        ying_yao = ying_yao if ying_yao > 0 else 6

        # 装六亲（简化处理：根据位置循环）
        liu_qin_order = ["父母", "兄弟", "子孙", "妻财", "官鬼"]

        # 装六神（从初爻开始按顺序装）
        liu_yao_details = []
        for i, yao in enumerate(yao_list):
            liu_qin = liu_qin_order[i % 5]
            liu_shen = self.LIU_SHEN[i % 6]

            liu_yao_details.append({
                "位置": yao["位置"],
                "阴阳": yao["阴阳"],
                "动静": yao["动静"],
                "六亲": liu_qin,
                "六神": liu_shen
            })

        return {
            "世爻": shi_yao,
            "应爻": ying_yao,
            "六爻详情": liu_yao_details
        }

    def _analyze_yong_shen(self, question_type: str, zhuang_gua: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析用神

        Args:
            question_type: 问题类型
            zhuang_gua: 装卦结果

        Returns:
            用神分析
        """
        # 根据问题类型确定用神（简化处理）
        yong_shen_map = {
            "事业": "官鬼",
            "财运": "妻财",
            "感情": "妻财",  # 男测
            "婚姻": "妻财",
            "健康": "子孙",
            "学业": "父母",
            "人际": "兄弟",
            "决策": "官鬼"
        }

        yong_shen_liu_qin = yong_shen_map.get(question_type, "官鬼")

        # 找到用神所在的爻
        yong_shen_yao = None
        for yao in zhuang_gua["六爻详情"]:
            if yao["六亲"] == yong_shen_liu_qin:
                yong_shen_yao = yao
                break

        if yong_shen_yao is None:
            yong_shen_yao = zhuang_gua["六爻详情"][0]  # 默认取初爻

        return {
            "六亲": yong_shen_liu_qin,
            "位置": yong_shen_yao["位置"],
            "阴阳": yong_shen_yao["阴阳"],
            "动静": yong_shen_yao["动静"],
            "旺衰": "旺" if yong_shen_yao["动静"] == "动" else "静"
        }

    def _judge_result(
        self,
        zhuang_gua: Dict[str, Any],
        yong_shen: Dict[str, Any],
        yao_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        判断吉凶

        Args:
            zhuang_gua: 装卦结果
            yong_shen: 用神
            yao_list: 爻列表

        Returns:
            判断结果
        """
        # 简化判断逻辑
        # 1. 用神动则吉
        # 2. 用神静但旺相也吉
        # 3. 用神休囚则凶

        if yong_shen["动静"] == "动":
            judgment = "吉"
            judgment_level = 0.75
            reason = f"用神{yong_shen['六亲']}发动，主事有变化，倾向吉利"
        elif yong_shen["旺衰"] == "旺":
            judgment = "吉"
            judgment_level = 0.65
            reason = f"用神{yong_shen['六亲']}旺相，主事顺利"
        else:
            judgment = "平"
            judgment_level = 0.5
            reason = f"用神{yong_shen['六亲']}安静，主事平稳"

        # 检查是否有多个动爻（乱动则凶）
        dong_yao_count = sum(1 for yao in yao_list if yao["动静"] == "动")
        if dong_yao_count >= 4:
            judgment = "凶"
            judgment_level = 0.3
            reason = "动爻过多，主事多变，易生波折"

        # 生成建议
        advice = self._generate_liu_yao_advice(judgment, yong_shen)

        return {
            "judgment": judgment,
            "judgment_level": judgment_level,
            "依据": reason,
            "建议": advice
        }

    def _generate_liu_yao_advice(self, judgment: str, yong_shen: Dict[str, Any]) -> str:
        """生成六爻建议"""
        if judgment == "吉":
            return f"用神{yong_shen['六亲']}有力，可以积极推进此事，把握时机"
        elif judgment == "凶":
            return f"用神{yong_shen['六亲']}不利，建议谨慎行事，等待时机成熟"
        else:
            return f"用神{yong_shen['六亲']}平稳，可以按计划进行，不宜冒进"

    def _analyze_response_time(self, yao_list: List[Dict[str, Any]], yong_shen: Dict[str, Any]) -> Dict[str, str]:
        """
        分析应期

        Args:
            yao_list: 爻列表
            yong_shen: 用神

        Returns:
            应期信息
        """
        # 简化处理：根据用神位置判断应期
        position = yong_shen["位置"]

        position_time_map = {
            1: "近期（数日内）",
            2: "本月内",
            3: "季度内",
            4: "半年内",
            5: "年内",
            6: "较长时间"
        }

        time_range = position_time_map.get(position, "待定")

        return {
            "时间": time_range,
            "依据": f"用神在第{position}爻"
        }

    def to_standard_answer(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """转换为标准答案格式"""
        return {
            'judgment': result.get('judgment', '平'),
            'judgment_level': result.get('judgment_level', 0.5),
            'timing': result.get('应期'),
            'advice': result.get('advice'),
            'confidence': result.get('confidence', 0.7)
        }
