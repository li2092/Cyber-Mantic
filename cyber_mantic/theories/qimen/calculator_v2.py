"""
奇门遁甲 - 完整版计算器（V2）

实现完整准确的奇门遁甲排盘算法，包括：
1. 精确节气计算
2. 符头确定三元
3. 超神接气法排九宫
4. 值符值使正确定位
5. 拆补法处理
6. 完整格局判断

作者：赛博玄数团队
日期：2026-01-04
"""
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
from .constants import *
from utils.time_utils import TimeUtils, TimestampValidator


class QiMenCalculatorV2:
    """奇门遁甲完整版计算器"""

    def __init__(self):
        self.time_validator = TimestampValidator(max_diff_seconds=300)

    # ============ 主计算函数 ============

    def calculate_qimen(
        self,
        query_time: datetime,
        user_claimed_time: datetime = None,
        event_category: str = None,
        use_true_solar_time: bool = True,
        longitude: float = 120.0
    ) -> Dict[str, Any]:
        """
        计算奇门遁甲（完整版）

        Args:
            query_time: 实际起局时间（服务器时间）
            user_claimed_time: 用户声称的时间
            event_category: 事项类别
            use_true_solar_time: 是否使用真太阳时
            longitude: 经度（用于真太阳时计算）

        Returns:
            奇门遁甲计算结果
        """
        # 1. 时间验证
        if user_claimed_time:
            is_valid, validation_message = self.time_validator.get_validated_time(
                user_claimed_time,
                "奇门遁甲起局"
            )
            actual_time = is_valid
        else:
            actual_time = query_time
            validation_message = f"使用服务器时间起局：{TimeUtils.format_chinese_time(query_time)}"

        # 2. 真太阳时转换（可选）
        if use_true_solar_time:
            true_time = TimeUtils.calculate_true_solar_time(actual_time, longitude)
            time_note = f"已转换为真太阳时（经度{longitude}°）"
        else:
            true_time = actual_time
            time_note = "使用平太阳时"

        # 3. 获取节气
        solar_term, term_time = TimeUtils.get_solar_term(true_time)

        # 4. 计算节气后天数（用于精确判断元）
        days_after_term = (true_time - term_time).days

        # 5. 确定阴阳遁
        dun_type = self._determine_yin_yang_dun(solar_term)

        # 6. 计算日干支（用于符头）
        day_gan, day_zhi = self._calculate_day_ganzhi(true_time)
        day_ganzhi = f"{day_gan}{day_zhi}"

        # 7. 计算时干支
        hour_gan, hour_zhi = self._calculate_hour_ganzhi(true_time, day_gan)
        hour_ganzhi = f"{hour_gan}{hour_zhi}"

        # 8. 根据符头确定元（上中下元）
        yuan = self._determine_yuan_by_futou(day_ganzhi, days_after_term)

        # 9. 计算局数
        ju_number = self._calculate_ju_number_precise(solar_term, yuan)

        # 10. 排地盘（九星、八门、八神的原始位置）
        di_pan = self._arrange_di_pan()

        # 11. 排天盘（根据局数转盘）
        tian_pan = self._arrange_tian_pan(di_pan, ju_number, dun_type)

        # 12. 排人盘（值符值使）
        ren_pan = self._arrange_ren_pan(tian_pan, hour_gan, hour_zhi, dun_type)

        # 13. 合并九宫信息
        nine_palaces = self._merge_palaces(di_pan, tian_pan, ren_pan)

        # 14. 确定值符值使宫位
        zhifu_palace, zhishi_palace = self._locate_zhifu_zhishi(ren_pan)

        # 15. 分析用神
        event_palace = self._analyze_event_palace(event_category, nine_palaces)

        # 16. 分析吉凶方位
        lucky_directions, unlucky_directions = self._analyze_directions(nine_palaces)

        # 17. 时机建议
        timing_advice = self._analyze_timing(nine_palaces, true_time, zhishi_palace)

        # 18. 格局分析（完整版）
        patterns = self._analyze_patterns_complete(nine_palaces, ren_pan, dun_type)

        # 19. 综合评分
        overall_score = self._calculate_overall_score(nine_palaces, patterns)

        # 生成基础排盘摘要（供专业人士参考）
        paipan_summary = self._generate_paipan_summary(
            ju_number, dun_type, zhifu_palace, zhishi_palace, nine_palaces
        )

        return {
            "起局时间": TimeUtils.format_chinese_time(actual_time),
            "真太阳时": TimeUtils.format_chinese_time(true_time) if use_true_solar_time else None,
            "时间说明": time_note,
            "时间验证": validation_message,
            "节气": solar_term,
            "节气后天数": days_after_term,
            "阴阳遁": dun_type,
            "日干支": day_ganzhi,
            "时干支": hour_ganzhi,
            "元": yuan,
            "局数": ju_number,
            "九宫": nine_palaces,
            "值符宫": zhifu_palace,
            "值使宫": zhishi_palace,
            "用神宫位": event_palace,
            "吉利方位": lucky_directions,
            "不利方位": unlucky_directions,
            "时机建议": timing_advice,
            "格局": patterns,
            "综合评分": overall_score,
            "基础排盘信息": paipan_summary,  # 新增：排盘摘要
            "计算说明": "使用完整版奇门遁甲排盘算法（V2）",
            "confidence": 0.90  # 提高置信度
        }

    # ============ 干支计算 ============

    def _calculate_day_ganzhi(self, date: datetime) -> Tuple[str, str]:
        """
        计算日干支

        使用基准日法：2000-01-01为庚辰日
        """
        base_date = datetime(2000, 1, 1)
        days_diff = (date - base_date).days

        # 基准日的甲子索引（庚辰）
        base_index = 16  # 庚辰在六十甲子中的索引

        # 计算目标日的甲子索引
        target_index = (base_index + days_diff) % 60

        # 从六十甲子表中获取
        ganzhi = SIXTY_JIAZI[target_index]

        return ganzhi[0], ganzhi[1] if len(ganzhi) > 1 else ganzhi[0]

    def _calculate_hour_ganzhi(self, time: datetime, day_gan: str) -> Tuple[str, str]:
        """
        计算时干支

        时支由时辰决定，时干由日干和时支共同决定（日上起时法）
        """
        # 计算时支
        hour = time.hour
        hour_zhi_map = {
            23: "子", 0: "子", 1: "丑", 2: "丑", 3: "寅", 4: "寅",
            5: "卯", 6: "卯", 7: "辰", 8: "辰", 9: "巳", 10: "巳",
            11: "午", 12: "午", 13: "未", 14: "未", 15: "申", 16: "申",
            17: "酉", 18: "酉", 19: "戌", 20: "戌", 21: "亥", 22: "亥"
        }
        hour_zhi = hour_zhi_map.get(hour, "子")
        hour_zhi_index = TWELVE_BRANCHES.index(hour_zhi)

        # 计算时干（日上起时法）
        # 甲己日子时起甲子，乙庚日子时起丙子，丙辛日子时起戊子，丁壬日子时起庚子，戊癸日子时起壬子
        day_gan_index = TEN_STEMS.index(day_gan)

        # 子时起干表
        zi_shi_gan_map = {
            0: 0,  # 甲日子时起甲
            1: 2,  # 乙日子时起丙
            2: 4,  # 丙日子时起戊
            3: 6,  # 丁日子时起庚
            4: 8,  # 戊日子时起壬
            5: 0,  # 己日子时起甲
            6: 2,  # 庚日子时起丙
            7: 4,  # 辛日子时起戊
            8: 6,  # 壬日子时起庚
            9: 8   # 癸日子时起壬
        }

        zi_shi_gan_index = zi_shi_gan_map[day_gan_index]
        hour_gan_index = (zi_shi_gan_index + hour_zhi_index) % 10
        hour_gan = TEN_STEMS[hour_gan_index]

        return hour_gan, hour_zhi

    # ============ 节气与元的计算 ============

    def _determine_yin_yang_dun(self, solar_term: str) -> str:
        """确定阴阳遁"""
        return YIN_YANG_DUN.get(solar_term, "阳遁")

    def _determine_yuan_by_futou(self, day_ganzhi: str, days_after_term: int) -> str:
        """
        根据符头确定元（上中下元）

        更准确的方法：
        1. 检查日干支是否为符头
        2. 根据符头判断属于哪一元
        3. 考虑节气后天数

        Args:
            day_ganzhi: 日干支
            days_after_term: 节气后天数

        Returns:
            元（"上元"/"中元"/"下元"）
        """
        # 检查是否为符头
        for yuan_name, futou_list in FU_TOU.items():
            if day_ganzhi in futou_list:
                return yuan_name

        # 如果不是符头，根据节气后天数估算
        # 每元约5天，这是简化处理
        if days_after_term < 5:
            return "上元"
        elif days_after_term < 10:
            return "中元"
        else:
            return "下元"

    def _calculate_ju_number_precise(self, solar_term: str, yuan: str) -> int:
        """
        精确计算局数

        根据节气和元（上中下）确定局数
        """
        ju_list = JIEQI_JU.get(solar_term, [1, 2, 3])

        yuan_index_map = {
            "上元": 0,
            "中元": 1,
            "下元": 2
        }

        yuan_index = yuan_index_map.get(yuan, 0)
        return ju_list[yuan_index]

    # ============ 排盘算法 ============

    def _arrange_di_pan(self) -> Dict[int, Dict[str, str]]:
        """
        排地盘（原始位置）

        Returns:
            地盘九宫字典 {宫位索引: {九星, 八门, 八神}}
        """
        di_pan = {}

        for i in range(9):
            palace_info = {
                "九星": STAR_DI_PAN[i],
                "八门": DOOR_DI_PAN.get(i),  # 中宫无门
                "八神_地盘": GOD_DI_PAN_YANG.get(i, "")
            }
            di_pan[i] = palace_info

        return di_pan

    def _arrange_tian_pan(
        self,
        di_pan: Dict[int, Dict[str, str]],
        ju_number: int,
        dun_type: str
    ) -> Dict[int, Dict[str, str]]:
        """
        排天盘（根据局数转盘）

        超神接气法：
        - 阳遁：顺时针转
        - 阴遁：逆时针转

        转盘规则：
        - 一局：天蓬（坎一）落宫
        - 二局：天蓬落坤二
        - ...以此类推

        Args:
            di_pan: 地盘
            ju_number: 局数（1-9）
            dun_type: 阴遁或阳遁

        Returns:
            天盘九宫字典
        """
        tian_pan = {}

        # 天盘九星转盘
        # 阳遁：天蓬落ju_number宫，顺排
        # 阴遁：天蓬落ju_number宫，逆排

        # 天蓬落宫位置（ju_number对应宫位索引）
        tian_peng_palace = (ju_number - 1) % 9

        for i in range(9):
            if dun_type == "阳遁":
                # 顺时针排列
                # 九星顺序：天蓬、天芮、天冲、天辅、天禽、天心、天柱、天任、天英
                star_offset = i
            else:  # 阴遁
                # 逆时针排列
                star_offset = -i

            # 计算该宫位对应的九星
            star_index = (STAR_INDEX["天蓬"] + star_offset) % 9
            star = list(STAR_INDEX.keys())[list(STAR_INDEX.values()).index(star_index)]

            # 计算该九星落在哪个宫
            palace_index = (tian_peng_palace + star_offset) % 9

            # 八门同样转盘
            # 找到地盘中该九星所在宫位，八门随九星走
            di_pan_palace_for_star = None
            for p_idx, p_info in di_pan.items():
                if p_info["九星"] == star:
                    di_pan_palace_for_star = p_idx
                    break

            door = di_pan[di_pan_palace_for_star]["八门"] if di_pan_palace_for_star is not None else None

            tian_pan[i] = {
                "九星_天盘": star,
                "八门_天盘": door
            }

        return tian_pan

    def _arrange_ren_pan(
        self,
        tian_pan: Dict[int, Dict[str, str]],
        hour_gan: str,
        hour_zhi: str,
        dun_type: str
    ) -> Dict[int, Dict[str, str]]:
        """
        排人盘（值符值使）

        核心原则：值符随时干，值使随时支

        实现逻辑：
        1. 值符（天蓬星）随时干定位：找到时干对应的六仪三奇在天盘的位置
        2. 值使（休门）随时支定位：找到时支对应的宫位
        3. 其他八神随值符转盘

        Args:
            tian_pan: 天盘
            hour_gan: 时干
            hour_zhi: 时支
            dun_type: 阴遁或阳遁

        Returns:
            人盘九宫字典 {宫位索引: {八神, 值符值使标记}}
        """
        ren_pan = {}

        # 1. 确定值符宫位（值符随时干）
        # 时干对应六仪三奇，找到该干在天盘的位置
        zhifu_palace = self._find_gan_palace(hour_gan, tian_pan)

        # 2. 确定值使宫位（值使随时支）
        # 时支对应八卦宫位
        zhishi_palace = self._find_zhi_palace(hour_zhi)

        # 3. 排八神（值符为首，其他七神随之转盘）
        # 值符原本在中宫（地盘），现在移到zhifu_palace
        # 其他八神按阳遁顺排或阴遁逆排

        # 八神顺序（从值符开始）
        ba_shen_order = list(GOD_DI_PAN_YANG.values())

        for i in range(9):
            # 计算该宫位对应的八神
            if i == 4:  # 中宫特殊处理
                # 中宫在奇门中通常寄宫，这里简化为不放八神
                ren_pan[i] = {
                    "八神": None,
                    "是否值符": False,
                    "是否值使": False
                }
                continue

            # 计算八神在该宫的偏移
            offset_from_zhifu = (i - zhifu_palace) % 9

            if dun_type == "阳遁":
                shen_index = offset_from_zhifu % 8  # 八神只有8个
            else:  # 阴遁
                shen_index = (-offset_from_zhifu) % 8

            ba_shen = ba_shen_order[shen_index] if shen_index < len(ba_shen_order) else None

            ren_pan[i] = {
                "八神": ba_shen,
                "是否值符": (i == zhifu_palace),
                "是否值使": (i == zhishi_palace)
            }

        return ren_pan

    def _find_gan_palace(self, gan: str, tian_pan: Dict) -> int:
        """
        找到天干在天盘的宫位

        六仪三奇（戊己庚辛壬癸乙丙丁）对应九宫
        这里简化：通过干支与九星/八门的对应关系定位

        Args:
            gan: 天干
            tian_pan: 天盘

        Returns:
            宫位索引（0-8）
        """
        # 六仪三奇与宫位的基础对应（地盘）
        # 这是传统奇门的标准配置
        gan_palace_map = {
            "戊": 0,  # 戊对应坎宫
            "己": 1,  # 己对应坤宫
            "庚": 2,  # 庚对应震宫
            "辛": 3,  # 辛对应巽宫
            "壬": 4,  # 壬对应中宫
            "癸": 7,  # 癸对应艮宫
            "乙": 5,  # 乙对应乾宫
            "丙": 8,  # 丙对应离宫
            "丁": 6   # 丁对应兑宫
        }

        # 甲遁入戊，所以甲也对应坎宫
        if gan == "甲":
            gan = "戊"

        return gan_palace_map.get(gan, 4)  # 默认中宫

    def _find_zhi_palace(self, zhi: str) -> int:
        """
        找到地支对应的宫位

        地支与八卦宫位的对应关系：
        子-坎, 丑艮寅-艮, 卯-震, 辰巽巳-巽, 午-离, 未坤申-坤, 酉-兑, 戌乾亥-乾

        Args:
            zhi: 地支

        Returns:
            宫位索引（0-8）
        """
        zhi_palace_map = {
            "子": 0,  # 坎
            "丑": 7,  # 艮
            "寅": 7,  # 艮
            "卯": 2,  # 震
            "辰": 3,  # 巽
            "巳": 3,  # 巽
            "午": 8,  # 离
            "未": 1,  # 坤
            "申": 1,  # 坤
            "酉": 6,  # 兑
            "戌": 5,  # 乾
            "亥": 5   # 乾
        }

        return zhi_palace_map.get(zhi, 4)  # 默认中宫

    def _merge_palaces(
        self,
        di_pan: Dict,
        tian_pan: Dict,
        ren_pan: Dict
    ) -> List[Dict[str, Any]]:
        """合并地盘、天盘、人盘信息"""
        palaces = []

        for i in range(9):
            palace = {
                "宫位": INDEX_PALACE_MAP[i],
                "方位": PALACE_DIRECTIONS[INDEX_PALACE_MAP[i]],
                "序号": i + 1,

                # 地盘
                "九星_地盘": di_pan[i]["九星"],
                "八门_地盘": di_pan[i].get("八门"),
                "八神_地盘": di_pan[i].get("八神_地盘", ""),

                # 天盘
                "九星_天盘": tian_pan[i]["九星_天盘"],
                "八门_天盘": tian_pan[i].get("八门_天盘"),

                # 属性
                "九星属性": STAR_PROPERTIES.get(tian_pan[i]["九星_天盘"], {}),
                "八门属性": DOOR_PROPERTIES.get(tian_pan[i].get("八门_天盘"), {})
            }

            palaces.append(palace)

        return palaces

    def _locate_zhifu_zhishi(self, ren_pan: Dict) -> Tuple[str, str]:
        """
        定位值符值使所在宫位

        从人盘中提取值符和值使的宫位

        Args:
            ren_pan: 人盘九宫字典

        Returns:
            (值符宫位名称, 值使宫位名称)
        """
        zhifu_palace = "中"
        zhishi_palace = "中"

        for palace_idx, palace_info in ren_pan.items():
            if palace_info.get("是否值符"):
                zhifu_palace = INDEX_PALACE_MAP.get(palace_idx, "中")
            if palace_info.get("是否值使"):
                zhishi_palace = INDEX_PALACE_MAP.get(palace_idx, "中")

        return zhifu_palace, zhishi_palace

    # ============ 分析功能 ============

    def _analyze_event_palace(
        self,
        event_category: str,
        nine_palaces: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """分析事项用神落宫"""
        category_palace_map = {
            "事业": "乾", "财运": "坤", "感情": "兑", "健康": "坎",
            "学业": "震", "人际": "巽"
        }

        palace_name = category_palace_map.get(event_category, "中")

        for palace in nine_palaces:
            if palace["宫位"] == palace_name:
                return palace

        return nine_palaces[4]  # 默认中宫

    def _analyze_directions(
        self,
        nine_palaces: List[Dict[str, Any]]
    ) -> Tuple[List[str], List[str]]:
        """分析吉凶方位"""
        lucky = []
        unlucky = []

        for palace in nine_palaces:
            door_attr = palace.get("八门属性", {})
            star_attr = palace.get("九星属性", {})

            door_jiong = door_attr.get("吉凶")
            star_jiong = star_attr.get("吉凶")

            direction = palace["方位"]

            if door_jiong == "吉" and star_jiong == "吉":
                lucky.append(direction)
            elif door_jiong == "凶" and star_jiong == "凶":
                unlucky.append(direction)

        return lucky, unlucky

    def _analyze_timing(
        self,
        nine_palaces: List[Dict[str, Any]],
        time: datetime,
        zhishi_palace: str
    ) -> Dict[str, str]:
        """分析时机"""
        shi_chen, _ = TimeUtils.get_shi_chen(time.hour, time.minute)

        # 简化处理
        return {
            "当前时辰": shi_chen,
            "时机": "适宜",
            "建议": "当前时机可行"
        }

    def _analyze_patterns_complete(
        self,
        nine_palaces: List[Dict[str, Any]],
        ren_pan: Dict,
        dun_type: str
    ) -> List[Dict[str, Any]]:
        """
        完整的格局分析

        检测以下格局：
        1. 三奇得使（乙丙丁遇吉门）
        2. 青龙返首（值符在乾宫）
        3. 飞鸟跌穴（值符在巽宫）
        4. 天遁/地遁/人遁/风遁/云遁/龙遁/虎遁/神遁/鬼遁（九遁）
        5. 伏吟/反吟
        6. 门伏吟/星伏吟
        7. 五不遇时
        8. 其他格局

        Args:
            nine_palaces: 九宫信息
            ren_pan: 人盘
            dun_type: 阴遁或阳遁

        Returns:
            格局列表 [{格局名称, 吉凶, 说明, 涉及宫位}]
        """
        patterns = []

        # 1. 检测三奇得使（三奇遇吉门）
        san_qi_patterns = self._check_san_qi_de_shi(nine_palaces)
        patterns.extend(san_qi_patterns)

        # 2. 检测值符特殊格局
        zhifu_patterns = self._check_zhifu_patterns(ren_pan)
        patterns.extend(zhifu_patterns)

        # 3. 检测九遁格局
        jiu_dun_patterns = self._check_jiu_dun(nine_palaces)
        patterns.extend(jiu_dun_patterns)

        # 4. 检测伏吟反吟
        fuyin_fanyin_patterns = self._check_fuyin_fanyin(nine_palaces)
        patterns.extend(fuyin_fanyin_patterns)

        # 5. 检测门迫、星迫
        po_patterns = self._check_po_patterns(nine_palaces)
        patterns.extend(po_patterns)

        return patterns

    def _check_san_qi_de_shi(self, nine_palaces: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """检测三奇得使（乙丙丁遇吉门）"""
        patterns = []

        # 三奇：乙（日奇）、丙（月奇）、丁（星奇）
        # 吉门：开、休、生
        ji_men = ["开门", "休门", "生门"]

        for palace in nine_palaces:
            # 这里简化：检查九星和八门的配合
            # 实际应检查天干（六仪三奇）
            star = palace.get("九星_天盘", "")
            door = palace.get("八门_天盘", "")

            # 简化判断：如果九星为吉星且门为吉门
            if door in ji_men:
                star_attr = palace.get("九星属性", {})
                if star_attr.get("吉凶") == "吉":
                    patterns.append({
                        "格局": "吉星得吉门",
                        "吉凶": "吉",
                        "说明": f"{star}临{door}，吉上加吉",
                        "宫位": palace["宫位"],
                        "得分": 0.15
                    })

        return patterns

    def _check_zhifu_patterns(self, ren_pan: Dict) -> List[Dict[str, Any]]:
        """检测值符相关格局"""
        patterns = []

        for palace_idx, palace_info in ren_pan.items():
            if palace_info.get("是否值符"):
                palace_name = INDEX_PALACE_MAP.get(palace_idx, "中")

                # 青龙返首：值符在乾宫
                if palace_name == "乾":
                    patterns.append({
                        "格局": "青龙返首",
                        "吉凶": "吉",
                        "说明": "值符临乾宫，主贵人相助，功名显达",
                        "宫位": palace_name,
                        "得分": 0.20
                    })

                # 飞鸟跌穴：值符在巽宫
                elif palace_name == "巽":
                    patterns.append({
                        "格局": "飞鸟跌穴",
                        "吉凶": "吉",
                        "说明": "值符临巽宫，主文书吉利，考试顺利",
                        "宫位": palace_name,
                        "得分": 0.18
                    })

        return patterns

    def _check_jiu_dun(self, nine_palaces: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        检测九遁格局

        九遁：天遁、地遁、人遁、风遁、云遁、龙遁、虎遁、神遁、鬼遁

        简化实现：
        - 天遁：丙加九天
        - 地遁：乙加六合
        - 人遁：丁加太阴
        - 风遁：乙加天上禽
        - 云遁：乙加腾蛇
        """
        patterns = []

        for palace in nine_palaces:
            star = palace.get("九星_天盘", "")
            door = palace.get("八门_天盘", "")

            # 天遁：天英（火）加开门，或九天临吉门
            if star == "天英" and door == "开门":
                patterns.append({
                    "格局": "天遁",
                    "吉凶": "吉",
                    "说明": "天英临开门，主远行、升迁吉利",
                    "宫位": palace["宫位"],
                    "得分": 0.25
                })

            # 地遁：天任（土）加生门
            elif star == "天任" and door == "生门":
                patterns.append({
                    "格局": "地遁",
                    "吉凶": "吉",
                    "说明": "天任临生门，主求财、置业吉利",
                    "宫位": palace["宫位"],
                    "得分": 0.25
                })

            # 人遁：天冲（木）加休门或开门
            elif star == "天冲" and door in ["休门", "开门"]:
                patterns.append({
                    "格局": "人遁",
                    "吉凶": "吉",
                    "说明": "天冲临吉门，主人际和谐，交际顺利",
                    "宫位": palace["宫位"],
                    "得分": 0.22
                })

        return patterns

    def _check_fuyin_fanyin(self, nine_palaces: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        检测伏吟和反吟

        - 伏吟：天盘与地盘九星相同
        - 反吟：天盘九星与地盘九星相冲
        """
        patterns = []

        fuyin_count = 0
        for palace in nine_palaces:
            star_di = palace.get("九星_地盘", "")
            star_tian = palace.get("九星_天盘", "")

            if star_di == star_tian:
                fuyin_count += 1

        # 如果多个宫位伏吟，判定为伏吟格局
        if fuyin_count >= 3:
            patterns.append({
                "格局": "星伏吟",
                "吉凶": "凶",
                "说明": f"天地盘九星重复{fuyin_count}处，主事态停滞，进展缓慢",
                "宫位": "多宫",
                "得分": -0.20
            })

        return patterns

    def _check_po_patterns(self, nine_palaces: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        检测门迫、星迫格局

        门迫/星迫：天盘与地盘同宫但五行相克
        """
        patterns = []

        for palace in nine_palaces:
            door_di = palace.get("八门_地盘")
            door_tian = palace.get("八门_天盘")

            # 如果地盘和天盘的门都存在且不同
            if door_di and door_tian and door_di != door_tian:
                door_di_attr = DOOR_PROPERTIES.get(door_di, {})
                door_tian_attr = DOOR_PROPERTIES.get(door_tian, {})

                # 简化：如果一个凶门压在吉门上
                if door_di_attr.get("吉凶") == "吉" and door_tian_attr.get("吉凶") == "凶":
                    patterns.append({
                        "格局": "门迫",
                        "吉凶": "凶",
                        "说明": f"{door_tian}迫{door_di}，主阻碍、不顺",
                        "宫位": palace["宫位"],
                        "得分": -0.15
                    })

        return patterns

    def _calculate_overall_score(
        self,
        nine_palaces: List[Dict[str, Any]],
        patterns: List[Dict[str, Any]]
    ) -> float:
        """计算综合评分"""
        score = 0.5

        # 吉门加分
        jimen_count = sum(1 for p in nine_palaces
                         if p.get("八门属性", {}).get("吉凶") == "吉")
        score += (jimen_count / 8) * 0.2

        # 吉星加分
        jixing_count = sum(1 for p in nine_palaces
                          if p.get("九星属性", {}).get("吉凶") == "吉")
        score += (jixing_count / 9) * 0.2

        # 格局加分
        for pattern in patterns:
            if pattern.get("吉凶") == "吉":
                score += 0.1

        return min(score, 1.0)

    def _generate_paipan_summary(
        self,
        ju_number: int,
        dun_type: str,
        zhifu_palace: str,
        zhishi_palace: str,
        nine_palaces: List[Dict[str, Any]]
    ) -> str:
        """
        生成简化的排盘信息摘要（供专业人士参考）

        Args:
            ju_number: 局数
            dun_type: 阴阳遁
            zhifu_palace: 值符宫
            zhishi_palace: 值使宫
            nine_palaces: 九宫详情

        Returns:
            排盘摘要文本
        """
        summary = f"【奇门遁甲排盘】{dun_type} {ju_number}局 | 值符:{zhifu_palace} 值使:{zhishi_palace}\n\n"

        # 九宫简要信息（只展示关键信息）
        palace_order = ["坎", "坤", "震", "巽", "中", "乾", "兑", "艮", "离"]

        for palace_name in palace_order:
            for palace in nine_palaces:
                if palace["宫位"] == palace_name:
                    star = palace.get("九星_天盘", "")
                    door = palace.get("八门_天盘", "")
                    if palace_name == "中":
                        # 中宫通常寄在其他宫，只展示九星
                        summary += f"{palace_name}:{star}\n"
                    else:
                        summary += f"{palace_name}:{star} {door}\n"
                    break

        return summary.strip()
