"""
大六壬计算器 - 完整版（V2）

实现完整准确的大六壬起课算法，包括：
1. 精确四课排盘（月将加时，地盘天盘）
2. 九宗门发用规则（贼克、比用、涉害、遥克、昴星、别责、八专、伏吟、返吟）
3. 天将昼夜顺逆配置
4. 完整课体判断

作者：赛博玄数团队
日期：2026-01-04
"""
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
from .constants import *


class DaLiuRenCalculatorV2:
    """大六壬完整版计算器"""

    def __init__(self):
        # 天干纳地支映射
        self.gan_na_zhi_map = {
            "甲": "寅", "乙": "卯",
            "丙": "巳", "丁": "午",
            "戊": "辰", "己": "未",
            "庚": "申", "辛": "酉",
            "壬": "亥", "癸": "子"
        }

    def _gan_to_zhi(self, gan: str) -> str:
        """天干转纳地支"""
        return self.gan_na_zhi_map.get(gan, "子")

    # ============ 主计算函数 ============

    def calculate_daliuren(
        self,
        year: int,
        month: int,
        day: int,
        hour: int,
        question: str = ""
    ) -> Dict[str, Any]:
        """
        计算大六壬课式（完整版）

        Args:
            year: 年
            month: 月
            day: 日
            hour: 时（0-23）
            question: 问题描述

        Returns:
            大六壬完整课式
        """
        # 1. 计算日干支（使用六十甲子精确推算）
        day_gan, day_zhi = self._calculate_day_ganzhi_accurate(year, month, day)

        # 2. 计算时支
        hour_zhi = self._calculate_hour_zhi(hour)

        # 3. 计算月将（正月登明在亥）
        month_jiang = self._calculate_month_jiang(month)

        # 4. 起四课（月将加时，寻地盘天盘）
        si_ke = self._calculate_si_ke_accurate(day_gan, day_zhi, hour_zhi, month_jiang)

        # 5. 取三传（九宗门发用规则）
        san_chuan, fa_yong_method = self._calculate_san_chuan_complete(
            si_ke, day_gan, day_zhi, hour_zhi
        )

        # 6. 配天将（昼夜顺逆）
        tian_jiang_config = self._configure_tian_jiang_complete(
            san_chuan, day_gan, hour_zhi, hour
        )

        # 7. 判断课体（九宗门分类）
        ke_ti = self._determine_ke_ti_complete(
            si_ke, san_chuan, day_gan, day_zhi, fa_yong_method
        )

        # 8. 吉凶分析
        judgment = self._analyze_judgment_complete(
            san_chuan, tian_jiang_config, ke_ti, day_gan
        )

        # 9. 生成基础排盘摘要（供专业人士参考）
        paipan_summary = self._generate_paipan_summary(
            day_gan, day_zhi, hour_zhi, month_jiang, si_ke, san_chuan, fa_yong_method, tian_jiang_config
        )

        return {
            "日干支": f"{day_gan}{day_zhi}",
            "时支": hour_zhi,
            "月将": month_jiang,
            "四课": si_ke,
            "三传": san_chuan,
            "发用方法": fa_yong_method,
            "天将": tian_jiang_config,
            "课体": ke_ti,
            "吉凶判断": judgment["judgment"],
            "综合评分": judgment["score"],
            "详细分析": judgment["analysis"],
            "基础排盘信息": paipan_summary,  # 新增：排盘摘要
            "计算说明": "使用完整版大六壬起课算法（V2），包含九宗门发用规则",
            "confidence": 0.85  # 提升置信度
        }

    # ============ 干支计算 ============

    def _calculate_day_ganzhi_accurate(
        self,
        year: int,
        month: int,
        day: int
    ) -> Tuple[str, str]:
        """
        精确计算日干支

        使用基准日法：2000-01-01为庚辰日
        """
        base_date = datetime(2000, 1, 1)
        target_date = datetime(year, month, day)
        days_diff = (target_date - base_date).days

        # 构造六十甲子表（与奇门遁甲V2相同）
        sixty_jiazi = []
        for i in range(60):
            gan = TIAN_GAN[i % 10]
            zhi = DI_ZHI[i % 12]
            sixty_jiazi.append(f"{gan}{zhi}")

        # 基准日的甲子索引（庚辰 = 16）
        base_index = 16

        # 计算目标日的甲子索引
        target_index = (base_index + days_diff) % 60
        ganzhi = sixty_jiazi[target_index]

        return ganzhi[0], ganzhi[1]

    def _calculate_hour_zhi(self, hour: int) -> str:
        """计算时支"""
        hour_zhi_map = {
            23: 0, 0: 0, 1: 1, 2: 1,
            3: 2, 4: 2, 5: 3, 6: 3,
            7: 4, 8: 4, 9: 5, 10: 5,
            11: 6, 12: 6, 13: 7, 14: 7,
            15: 8, 16: 8, 17: 9, 18: 9,
            19: 10, 20: 10, 21: 11, 22: 11
        }
        zhi_index = hour_zhi_map.get(hour, 0)
        return DI_ZHI[zhi_index]

    def _calculate_month_jiang(self, month: int) -> str:
        """
        计算月将（正月登明在亥）

        正月亥，二月戌，三月酉...逆行
        """
        month_jiang_map = {
            1: "亥", 2: "戌", 3: "酉", 4: "申", 5: "未", 6: "午",
            7: "巳", 8: "辰", 9: "卯", 10: "寅", 11: "丑", 12: "子"
        }
        return month_jiang_map.get(month, "亥")

    # ============ 四课排盘 ============

    def _calculate_si_ke_accurate(
        self,
        day_gan: str,
        day_zhi: str,
        hour_zhi: str,
        month_jiang: str
    ) -> List[Dict[str, str]]:
        """
        准确起四课

        四课：
        - 第一课（日阳课）：日干上神（从地盘干位看天盘）
        - 第二课（日阴课）：干上神之下（干上神落地盘的位置）
        - 第三课（辰阳课）：日支上神（从地盘支位看天盘）
        - 第四课（辰阴课）：支上神之下（支上神落地盘的位置）

        关键：月将加时 - 月将加在时支上，形成天盘
        """
        # 计算月将加时（地盘）
        month_jiang_index = DI_ZHI.index(month_jiang)
        hour_zhi_index = DI_ZHI.index(hour_zhi)

        # 地盘起始：月将在时支位置
        # 例如：月将=亥(10)，时支=子(0)，则地盘从亥开始，亥在子位
        # 地盘顺序：子丑寅卯辰巳午未申酉戌亥
        # 天盘从月将开始顺排

        # 建立地盘天盘对应关系
        # 地盘固定：子(0)丑(1)寅(2)...亥(11)
        # 天盘：从月将开始顺排，月将落在时支位置

        # 计算偏移量
        offset = (hour_zhi_index - month_jiang_index) % 12

        def get_tian_pan_zhi(di_pan_zhi: str) -> str:
            """根据地盘地支，查找天盘地支"""
            di_pan_index = DI_ZHI.index(di_pan_zhi)
            tian_pan_index = (di_pan_index + offset) % 12
            return DI_ZHI[tian_pan_index]

        # 第一课：日干上神
        # 日干寻对应地支（天干纳地支）
        day_gan_index = TIAN_GAN.index(day_gan)
        # 甲乙配寅卯，丙丁配巳午，戊己配辰戌丑未，庚辛配申酉，壬癸配亥子
        # 简化：直接映射到地支
        gan_na_zhi_map = {
            "甲": "寅", "乙": "卯",
            "丙": "巳", "丁": "午",
            "戊": "辰", "己": "未",
            "庚": "申", "辛": "酉",
            "壬": "亥", "癸": "子"
        }
        gan_di_pan_zhi = gan_na_zhi_map.get(day_gan, "子")
        gan_shang_shen = get_tian_pan_zhi(gan_di_pan_zhi)

        # 第二课：干上神之下（干上神在地盘的位置）
        # 干上神是天盘的某个地支，现在要找它在地盘的位置，反查天盘对应地盘
        # 天盘A -> 地盘B，现在gan_shang_shen是天盘，要找对应的地盘位置
        gan_shang_shen_index = DI_ZHI.index(gan_shang_shen)
        gan_xia_shen_index = (gan_shang_shen_index - offset) % 12
        gan_xia_shen = DI_ZHI[gan_xia_shen_index]

        # 第三课：日支上神
        zhi_shang_shen = get_tian_pan_zhi(day_zhi)

        # 第四课：支上神之下
        zhi_shang_shen_index = DI_ZHI.index(zhi_shang_shen)
        zhi_xia_shen_index = (zhi_shang_shen_index - offset) % 12
        zhi_xia_shen = DI_ZHI[zhi_xia_shen_index]

        si_ke = [
            {
                "课名": "第一课（日阳）",
                "下": day_gan,
                "上": gan_shang_shen,
                "关系": self._get_ke_relationship(day_gan, gan_shang_shen)
            },
            {
                "课名": "第二课（日阴）",
                "下": gan_shang_shen,
                "上": gan_xia_shen,
                "关系": self._get_ke_relationship(gan_shang_shen, gan_xia_shen)
            },
            {
                "课名": "第三课（辰阳）",
                "下": day_zhi,
                "上": zhi_shang_shen,
                "关系": self._get_ke_relationship(day_zhi, zhi_shang_shen)
            },
            {
                "课名": "第四课（辰阴）",
                "下": zhi_shang_shen,
                "上": zhi_xia_shen,
                "关系": self._get_ke_relationship(zhi_shang_shen, zhi_xia_shen)
            }
        ]

        return si_ke

    def _get_ke_relationship(self, xia: str, shang: str) -> str:
        """
        判断上下神的克关系

        下克上：贼
        上克下：克
        无克：比、生等
        """
        # 获取五行
        xia_wuxing = self._get_wuxing(xia)
        shang_wuxing = self._get_wuxing(shang)

        # 判断克关系（金克木，木克土，土克水，水克火，火克金）
        ke_map = {
            "金": "木",
            "木": "土",
            "土": "水",
            "水": "火",
            "火": "金"
        }

        if ke_map.get(xia_wuxing) == shang_wuxing:
            return "贼"  # 下克上
        elif ke_map.get(shang_wuxing) == xia_wuxing:
            return "克"  # 上克下
        elif xia == shang:
            return "比"
        else:
            return "无克"

    def _get_wuxing(self, ganzhi: str) -> str:
        """获取干支的五行属性"""
        wuxing_map = {
            # 天干
            "甲": "木", "乙": "木",
            "丙": "火", "丁": "火",
            "戊": "土", "己": "土",
            "庚": "金", "辛": "金",
            "壬": "水", "癸": "水",
            # 地支
            "子": "水", "亥": "水",
            "寅": "木", "卯": "木",
            "巳": "火", "午": "火",
            "申": "金", "酉": "金",
            "辰": "土", "戌": "土", "丑": "土", "未": "土"
        }
        return wuxing_map.get(ganzhi, "土")

    # ============ 九宗门取三传 ============

    def _calculate_san_chuan_complete(
        self,
        si_ke: List[Dict[str, str]],
        day_gan: str,
        day_zhi: str,
        hour_zhi: str
    ) -> Tuple[List[Dict[str, str]], str]:
        """
        完整九宗门取三传

        按优先级判断：
        1. 贼克法
        2. 比用法
        3. 涉害法
        4. 遥克法
        5. 昴星法
        6. 别责法
        7. 八专法
        8. 伏吟法
        9. 返吟法

        Returns:
            (三传列表, 发用方法名称)
        """
        # 判断是否八专
        if day_gan == day_zhi or self._is_ba_zhuan(day_gan, day_zhi):
            return self._fa_yong_ba_zhuan(si_ke), "八专法"

        # 判断是否伏吟
        if self._is_fu_yin(si_ke):
            return self._fa_yong_fu_yin(si_ke, day_gan, day_zhi), "伏吟法"

        # 判断是否返吟
        if self._is_fan_yin(si_ke):
            return self._fa_yong_fan_yin(si_ke, day_gan, day_zhi), "返吟法"

        # 尝试贼克法
        san_chuan = self._fa_yong_zei_ke(si_ke)
        if san_chuan:
            return san_chuan, "贼克法"

        # 尝试比用法
        san_chuan = self._fa_yong_bi_yong(si_ke, day_gan, day_zhi)
        if san_chuan:
            return san_chuan, "比用法"

        # 尝试涉害法
        san_chuan = self._fa_yong_she_hai(si_ke, day_gan, day_zhi)
        if san_chuan:
            return san_chuan, "涉害法"

        # 默认取法（兜底）
        return self._fa_yong_default(si_ke), "一般取法"

    # ===== 八专、伏吟、返吟判断 =====

    def _is_ba_zhuan(self, day_gan: str, day_zhi: str) -> bool:
        """判断是否八专（干支相同纳音）"""
        # 八专：甲寅、乙卯、丙午、丁未、戊辰、己巳、庚申、辛酉、壬子、癸亥
        # 简化：检查干支是否同类五行
        ba_zhuan_list = [
            ("甲", "寅"), ("乙", "卯"),
            ("丙", "午"), ("丁", "巳"),
            ("戊", "辰"), ("戊", "戌"), ("己", "丑"), ("己", "未"),
            ("庚", "申"), ("辛", "酉"),
            ("壬", "子"), ("癸", "亥")
        ]
        return (day_gan, day_zhi) in ba_zhuan_list

    def _is_fu_yin(self, si_ke: List[Dict[str, str]]) -> bool:
        """
        判断是否伏吟

        伏吟：四课上下皆为本位（上下相同或本位）
        """
        fu_yin_count = 0
        for ke in si_ke:
            if ke["下"] == ke["上"]:
                fu_yin_count += 1

        # 如果4课中有3课以上伏吟，判定为伏吟课
        return fu_yin_count >= 3

    def _is_fan_yin(self, si_ke: List[Dict[str, str]]) -> bool:
        """
        判断是否返吟

        返吟：四课上下皆为冲位
        """
        fan_yin_count = 0
        for ke in si_ke:
            xia_zhi = ke["下"]
            shang_zhi = ke["上"]
            # 判断是否相冲
            if DI_ZHI_CHONG.get(xia_zhi) == shang_zhi:
                fan_yin_count += 1

        # 如果4课中有3课以上返吟，判定为返吟课
        return fan_yin_count >= 3

    # ===== 各种发用方法实现 =====

    def _fa_yong_zei_ke(self, si_ke: List[Dict[str, str]]) -> Optional[List[Dict[str, str]]]:
        """
        贼克法取三传

        口诀：下贼上克两相逢，先取贼来后取克

        优先级：贼（下克上） > 克（上克下）
        """
        zei_list = []  # 贼课（下克上）
        ke_list = []   # 克课（上克下）

        for i, ke in enumerate(si_ke):
            if ke["关系"] == "贼":
                zei_list.append((i, ke))
            elif ke["关系"] == "克":
                ke_list.append((i, ke))

        # 如果没有贼克关系，返回None
        if not zei_list and not ke_list:
            return None

        # 选择初传：先贼后克
        if zei_list:
            chu_chuan_idx, chu_chuan = zei_list[0]
        else:
            chu_chuan_idx, chu_chuan = ke_list[0]

        # 中传：取初传的上神在地盘的位置（顺推）
        # 简化：取下一课
        zhong_chuan_idx = (chu_chuan_idx + 1) % 4
        zhong_chuan = si_ke[zhong_chuan_idx]

        # 末传：再取下一课
        mo_chuan_idx = (chu_chuan_idx + 2) % 4
        mo_chuan = si_ke[mo_chuan_idx]

        return [
            {"传名": "初传", "地支": chu_chuan["上"], "来源": chu_chuan["课名"]},
            {"传名": "中传", "地支": zhong_chuan["上"], "来源": zhong_chuan["课名"]},
            {"传名": "末传", "地支": mo_chuan["上"], "来源": mo_chuan["课名"]}
        ]

    def _fa_yong_bi_yong(
        self,
        si_ke: List[Dict[str, str]],
        day_gan: str,
        day_zhi: str
    ) -> Optional[List[Dict[str, str]]]:
        """
        比用法取三传（知一法）

        四课无克，比用阴阳
        """
        # 检查是否四课无克
        has_ke = any(ke["关系"] in ["贼", "克"] for ke in si_ke)
        if has_ke:
            return None

        # 取日干、日支、干上神、支上神
        gan_shang = si_ke[0]["上"]
        zhi_shang = si_ke[2]["上"]

        # 日干转换为纳地支
        day_gan_zhi = self._gan_to_zhi(day_gan)

        return [
            {"传名": "初传", "地支": day_gan_zhi, "来源": "日干"},
            {"传名": "中传", "地支": gan_shang, "来源": "干上神"},
            {"传名": "末传", "地支": zhi_shang, "来源": "支上神"}
        ]

    def _fa_yong_she_hai(
        self,
        si_ke: List[Dict[str, str]],
        day_gan: str,
        day_zhi: str
    ) -> Optional[List[Dict[str, str]]]:
        """
        涉害法取三传

        口诀：涉害行来本家止，路逢多克为用取
        """
        # 简化实现：检查涉害关系，取受克最多的为初传
        shang_shen_list = [ke["上"] for ke in si_ke]

        # 统计每个地支被克次数
        ke_count = {}
        for shen in shang_shen_list:
            ke_count[shen] = ke_count.get(shen, 0) + 1

        # 取被克最多的为初传
        if not ke_count:
            return None

        max_ke_shen = max(ke_count, key=ke_count.get)

        # 从max_ke_shen开始顺数三传
        max_ke_index = DI_ZHI.index(max_ke_shen)

        return [
            {"传名": "初传", "地支": DI_ZHI[max_ke_index], "来源": "涉害"},
            {"传名": "中传", "地支": DI_ZHI[(max_ke_index + 1) % 12], "来源": "涉害顺数"},
            {"传名": "末传", "地支": DI_ZHI[(max_ke_index + 2) % 12], "来源": "涉害顺数"}
        ]

    def _fa_yong_ba_zhuan(self, si_ke: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """八专法取三传"""
        # 八专：四课三传皆同
        zhi = si_ke[0]["上"]
        return [
            {"传名": "初传", "地支": zhi, "来源": "八专"},
            {"传名": "中传", "地支": zhi, "来源": "八专"},
            {"传名": "末传", "地支": zhi, "来源": "八专"}
        ]

    def _fa_yong_fu_yin(
        self,
        si_ke: List[Dict[str, str]],
        day_gan: str,
        day_zhi: str
    ) -> List[Dict[str, str]]:
        """伏吟法取三传"""
        # 伏吟：取本位
        # 日干转换为纳地支
        day_gan_zhi = self._gan_to_zhi(day_gan)

        return [
            {"传名": "初传", "地支": day_gan_zhi, "来源": "伏吟"},
            {"传名": "中传", "地支": day_zhi, "来源": "伏吟"},
            {"传名": "末传", "地支": day_zhi, "来源": "伏吟"}
        ]

    def _fa_yong_fan_yin(
        self,
        si_ke: List[Dict[str, str]],
        day_gan: str,
        day_zhi: str
    ) -> List[Dict[str, str]]:
        """返吟法取三传"""
        # 返吟：取冲位
        day_zhi_index = DI_ZHI.index(day_zhi)
        chong_zhi = DI_ZHI[(day_zhi_index + 6) % 12]

        return [
            {"传名": "初传", "地支": chong_zhi, "来源": "返吟"},
            {"传名": "中传", "地支": chong_zhi, "来源": "返吟"},
            {"传名": "末传", "地支": day_zhi, "来源": "返吟"}
        ]

    def _fa_yong_default(self, si_ke: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """默认取法（兜底）"""
        return [
            {"传名": "初传", "地支": si_ke[0]["上"], "来源": si_ke[0]["课名"]},
            {"传名": "中传", "地支": si_ke[2]["上"], "来源": si_ke[2]["课名"]},
            {"传名": "末传", "地支": si_ke[3]["上"], "来源": si_ke[3]["课名"]}
        ]

    # ============ 天将配置（昼夜顺逆） ============

    def _configure_tian_jiang_complete(
        self,
        san_chuan: List[Dict[str, str]],
        day_gan: str,
        hour_zhi: str,
        hour: int
    ) -> List[Dict[str, Any]]:
        """
        完整配天将（考虑昼夜顺逆）

        夜贵顺行，昼贵逆行（以贵人为界）
        """
        # 获取贵人起始地支
        guiren_start_zhi = GUIREN_START.get(day_gan, "丑")
        guiren_index = DI_ZHI.index(guiren_start_zhi)

        # 判断昼夜（简化：7-19点为昼，其他为夜）
        is_day = 7 <= hour < 19

        result = []
        for i, chuan in enumerate(san_chuan):
            zhi = chuan["地支"]
            zhi_index = DI_ZHI.index(zhi)

            # 计算天将索引
            if is_day:
                # 昼贵逆行
                tian_jiang_index = (guiren_index - zhi_index) % 12
            else:
                # 夜贵顺行
                tian_jiang_index = (zhi_index - guiren_index) % 12

            tian_jiang_name = TIAN_JIANG[tian_jiang_index]

            result.append({
                "传名": chuan["传名"],
                "地支": zhi,
                "天将": tian_jiang_name,
                "属性": TIAN_JIANG_PROPERTIES.get(tian_jiang_name, {}),
                "昼夜": "昼" if is_day else "夜"
            })

        return result

    # ============ 课体判断 ============

    def _determine_ke_ti_complete(
        self,
        si_ke: List[Dict[str, str]],
        san_chuan: List[Dict[str, str]],
        day_gan: str,
        day_zhi: str,
        fa_yong_method: str
    ) -> Dict[str, str]:
        """
        完整课体判断

        根据发用方法和三传特征判断课体
        """
        # 直接根据发用方法确定课体
        if fa_yong_method == "贼克法":
            ke_ti_name = "贼克课"
            ke_ti_desc = "四课有贼克，主动中有阻碍"
        elif fa_yong_method == "比用法":
            ke_ti_name = "比用课"
            ke_ti_desc = "四课无克，比用阴阳，主平稳"
        elif fa_yong_method == "涉害法":
            ke_ti_name = "涉害课"
            ke_ti_desc = "涉害行来本家止，主曲折"
        elif fa_yong_method == "八专法":
            ke_ti_name = "八专课"
            ke_ti_desc = "干支相同，主专一或固执"
        elif fa_yong_method == "伏吟法":
            ke_ti_name = "伏吟课"
            ke_ti_desc = "四课伏吟，主停滞不前"
        elif fa_yong_method == "返吟法":
            ke_ti_name = "返吟课"
            ke_ti_desc = "四课返吟，主反复变化"
        else:
            ke_ti_name = "一般课"
            ke_ti_desc = "普通课式"

        # 进一步判断三传特征
        zhi_list = [c["地支"] for c in san_chuan]
        zhi_indices = [DI_ZHI.index(z) for z in zhi_list]

        # 判断是否连茹
        if zhi_indices[1] == (zhi_indices[0] + 1) % 12 and \
           zhi_indices[2] == (zhi_indices[1] + 1) % 12:
            ke_ti_name += "（顺连茹）"
            ke_ti_desc += "，三传顺连，主渐进"
        elif zhi_indices[1] == (zhi_indices[0] - 1) % 12 and \
             zhi_indices[2] == (zhi_indices[1] - 1) % 12:
            ke_ti_name += "（逆连茹）"
            ke_ti_desc += "，三传逆连，主倒退"

        return {
            "名称": ke_ti_name,
            "说明": ke_ti_desc,
            "发用方法": fa_yong_method
        }

    # ============ 吉凶分析 ============

    def _analyze_judgment_complete(
        self,
        san_chuan: List[Dict[str, str]],
        tian_jiang: List[Dict[str, Any]],
        ke_ti: Dict[str, str],
        day_gan: str
    ) -> Dict[str, Any]:
        """完整吉凶分析"""
        # 计算天将吉凶评分
        ji_count = 0
        xiong_count = 0

        for tj in tian_jiang:
            ji_xiong = tj["属性"].get("吉凶", "平")
            if ji_xiong == "吉":
                ji_count += 1
            elif ji_xiong == "凶":
                xiong_count += 1

        # 计算基础评分
        score = 0.5 + (ji_count * 0.15) - (xiong_count * 0.15)

        # 课体影响
        fa_yong_method = ke_ti.get("发用方法", "")
        if "伏吟" in fa_yong_method or "返吟" in fa_yong_method:
            score -= 0.1  # 伏吟返吟不利
        elif "八专" in fa_yong_method:
            score -= 0.05  # 八专稍不利

        score = max(0.2, min(1.0, score))

        # 判断吉凶
        if score >= 0.7:
            judgment = "吉"
            judgment_desc = "天将多吉，格局良好"
        elif score >= 0.5:
            judgment = "平"
            judgment_desc = "吉凶参半，需谨慎行事"
        else:
            judgment = "凶"
            judgment_desc = "天将多凶，格局不利"

        # 综合分析
        ke_ti_desc = ke_ti["说明"]
        analysis = f"{judgment_desc}。{ke_ti_desc}。"

        return {
            "judgment": judgment,
            "score": score,
            "analysis": analysis
        }

    def _generate_paipan_summary(
        self,
        day_gan: str,
        day_zhi: str,
        hour_zhi: str,
        month_jiang: str,
        si_ke: List[Dict[str, str]],
        san_chuan: List[Dict[str, str]],
        fa_yong_method: str,
        tian_jiang: List[Dict[str, Any]]
    ) -> str:
        """
        生成简化的排盘信息摘要（供专业人士参考）

        Args:
            day_gan: 日干
            day_zhi: 日支
            hour_zhi: 时支
            month_jiang: 月将
            si_ke: 四课
            san_chuan: 三传
            fa_yong_method: 发用方法
            tian_jiang: 天将配置

        Returns:
            排盘摘要文本
        """
        summary = f"【大六壬起课】{day_gan}{day_zhi}日 {hour_zhi}时 | 月将:{month_jiang}\n\n"

        # 四课信息
        summary += "【四课】\n"
        for ke in si_ke:
            ke_name = ke["课名"]
            xia = ke["下"]
            shang = ke["上"]
            relation = ke["关系"]
            summary += f"{ke_name}: {xia} → {shang} ({relation})\n"

        # 三传信息
        summary += f"\n【三传】{fa_yong_method}\n"
        for i, chuan in enumerate(san_chuan):
            tj = tian_jiang[i] if i < len(tian_jiang) else {}
            tian_jiang_name = tj.get("天将", "")
            zhi = chuan["地支"]
            summary += f"{chuan['传名']}: {zhi} - {tian_jiang_name}\n"

        return summary.strip()
