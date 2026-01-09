"""
八字模块 - 计算器
纯代码实现，不调用LLM

V2增强：
- 三柱分析模式（无时辰时的降级计算）
- 多时辰并行计算
- 时辰处理器集成
"""
from datetime import datetime, timedelta
from typing import Tuple, Dict, List, Any, Optional
from .constants import *
from utils.lunar_calendar import LunarCalendar
from utils.cache_manager import cached, performance_monitor


class BaZiCalculator:
    """八字计算器"""

    def __init__(self):
        pass

    @cached(cache_name="bazi_calculation", max_size=1000, ttl=86400)
    @performance_monitor(log_threshold_ms=100.0)
    def calculate_full_bazi(
        self,
        year: int,
        month: int,
        day: int,
        hour: Optional[int] = None,
        gender: Optional[str] = None,
        calendar_type: str = "solar"
    ) -> Dict[str, Any]:
        """
        计算完整八字（带缓存）

        Args:
            year: 出生年
            month: 出生月
            day: 出生日
            hour: 出生时（0-23）
            gender: 性别 "male"/"female"
            calendar_type: 历法类型 "solar"/"lunar"

        Returns:
            完整八字信息
        """
        # 如果是农历，需要转换为公历
        if calendar_type == "lunar":
            try:
                solar_date = LunarCalendar.lunar_to_solar(year, month, day, is_leap_month=False)
                year = solar_date.year
                month = solar_date.month
                day = solar_date.day
            except ValueError as e:
                raise ValueError(f"农历日期转换失败：{e}")

        # 计算四柱
        year_pillar = self.calculate_year_pillar(year, month, day)
        month_pillar = self.calculate_month_pillar(year, month, day)
        day_pillar = self.calculate_day_pillar(year, month, day)
        hour_pillar = None
        if hour is not None:
            hour_pillar = self.calculate_hour_pillar(day_pillar[0], hour)

        # 构建四柱列表
        four_pillars = [
            f"{year_pillar[0]}{year_pillar[1]}",
            f"{month_pillar[0]}{month_pillar[1]}",
            f"{day_pillar[0]}{day_pillar[1]}"
        ]
        if hour_pillar:
            four_pillars.append(f"{hour_pillar[0]}{hour_pillar[1]}")

        # 日主
        day_master = day_pillar[0]

        # 计算十神
        ten_gods = self.calculate_ten_gods(day_master, year_pillar[0], month_pillar[0], day_pillar[0], hour_pillar[0] if hour_pillar else None)

        # 计算五行
        wuxing_count = self.calculate_wuxing_count([year_pillar, month_pillar, day_pillar, hour_pillar] if hour_pillar else [year_pillar, month_pillar, day_pillar])

        # 分析用神
        useful_god_analysis = self.analyze_useful_god(day_master, wuxing_count)

        # 计算纳音
        nayin = {
            "年柱": NA_YIN.get(f"{year_pillar[0]}{year_pillar[1]}", "未知"),
            "月柱": NA_YIN.get(f"{month_pillar[0]}{month_pillar[1]}", "未知"),
            "日柱": NA_YIN.get(f"{day_pillar[0]}{day_pillar[1]}", "未知")
        }
        if hour_pillar:
            nayin["时柱"] = NA_YIN.get(f"{hour_pillar[0]}{hour_pillar[1]}", "未知")

        # 计算大运（如果有性别）
        dayun_list = []
        if gender:
            dayun_list = self.calculate_dayun(year_pillar, month_pillar, gender, year, month, day)

        # 计算神煞
        shensha = self.calculate_shensha(
            year_gan=year_pillar[0],
            year_zhi=year_pillar[1],
            month_zhi=month_pillar[1],
            day_gan=day_pillar[0],
            day_zhi=day_pillar[1],
            hour_zhi=hour_pillar[1] if hour_pillar else None
        )

        # 分析神煞影响
        shensha_analysis = self.analyze_shensha_influence(shensha)

        # 计算置信度
        confidence = 1.0 if hour is not None else 0.75

        return {
            "四柱": four_pillars,
            "年柱": {"天干": year_pillar[0], "地支": year_pillar[1], "纳音": nayin["年柱"]},
            "月柱": {"天干": month_pillar[0], "地支": month_pillar[1], "纳音": nayin["月柱"]},
            "日柱": {"天干": day_pillar[0], "地支": day_pillar[1], "纳音": nayin["日柱"]},
            "时柱": {"天干": hour_pillar[0], "地支": hour_pillar[1], "纳音": nayin.get("时柱")} if hour_pillar else None,
            "日主": day_master,
            "十神": ten_gods,
            "五行统计": wuxing_count,
            "用神分析": useful_god_analysis,
            "神煞": shensha,
            "神煞分析": shensha_analysis,
            "大运": dayun_list,
            "置信度": confidence
        }

    def calculate_year_pillar(self, year: int, month: int, day: int) -> Tuple[str, str]:
        """
        计算年柱（注意立春换年）

        Args:
            year: 年份
            month: 月份
            day: 日期

        Returns:
            (年干, 年支)
        """
        # 简化处理：立春一般在2月4-5日
        # 如果在立春前，年份减1
        actual_year = year
        if month < 2 or (month == 2 and day < 4):
            actual_year -= 1

        # 计算年干（从甲子年1984年开始）
        year_gan_index = (actual_year - 4) % 10
        year_zhi_index = (actual_year - 4) % 12

        return (TIAN_GAN[year_gan_index], DI_ZHI[year_zhi_index])

    def calculate_month_pillar(self, year: int, month: int, day: int) -> Tuple[str, str]:
        """
        计算月柱（注意节气换月）

        Args:
            year: 年份
            month: 月份
            day: 日期

        Returns:
            (月干, 月支)
        """
        # 简化处理：根据公历月份大致确定月支
        # 实际应该根据节气精确计算
        month_zhi_index = (month + 1) % 12  # 正月从寅开始

        # 获取年干
        year_pillar = self.calculate_year_pillar(year, month, day)
        year_gan = year_pillar[0]

        # 根据年干起月干
        month_gan_base = MONTH_GAN_BASE.get(year_gan, "丙")
        month_gan_base_index = TIAN_GAN.index(month_gan_base)
        month_gan_index = (month_gan_base_index + month_zhi_index) % 10

        month_zhi = MONTH_ZHI[month_zhi_index]
        month_gan = TIAN_GAN[month_gan_index]

        return (month_gan, month_zhi)

    def calculate_day_pillar(self, year: int, month: int, day: int) -> Tuple[str, str]:
        """
        计算日柱（使用公式计算）

        Args:
            year: 年份
            month: 月份
            day: 日期

        Returns:
            (日干, 日支)
        """
        # 使用蔡勒公式的变体计算日柱
        # 基准日：2000年1月1日为庚辰日（JIA_ZI_60中的索引16）

        base_date = datetime(2000, 1, 1)
        target_date = datetime(year, month, day)
        days_diff = (target_date - base_date).days

        # 基准日的甲子索引（庚辰）
        base_index = 16

        # 计算目标日的甲子索引
        target_index = (base_index + days_diff) % 60

        jiazi = JIA_ZI_60[target_index]
        return (jiazi[0], jiazi[1])

    def calculate_hour_pillar(self, day_gan: str, hour: int) -> Tuple[str, str]:
        """
        计算时柱

        Args:
            day_gan: 日干
            hour: 小时（0-23）

        Returns:
            (时干, 时支)
        """
        # 确定时支
        hour_zhi = HOUR_ZHI_MAP.get(hour, "子")
        hour_zhi_index = DI_ZHI.index(hour_zhi)

        # 根据日干起时干
        hour_gan_base = HOUR_GAN_BASE.get(day_gan, "甲")
        hour_gan_base_index = TIAN_GAN.index(hour_gan_base)
        hour_gan_index = (hour_gan_base_index + hour_zhi_index) % 10

        hour_gan = TIAN_GAN[hour_gan_index]

        return (hour_gan, hour_zhi)

    def calculate_ten_gods(
        self,
        day_master: str,
        year_gan: str,
        month_gan: str,
        day_gan: str,
        hour_gan: Optional[str]
    ) -> Dict[str, str]:
        """
        计算十神

        Args:
            day_master: 日主
            year_gan: 年干
            month_gan: 月干
            day_gan: 日干
            hour_gan: 时干

        Returns:
            十神字典
        """
        result = {
            "年干": SHI_SHEN[day_master][year_gan],
            "月干": SHI_SHEN[day_master][month_gan],
            "日干": SHI_SHEN[day_master][day_gan]
        }

        if hour_gan:
            result["时干"] = SHI_SHEN[day_master][hour_gan]

        return result

    def calculate_wuxing_count(self, pillars: List[Tuple[str, str]]) -> Dict[str, Any]:
        """
        计算五行统计

        Args:
            pillars: 四柱列表 [(天干, 地支), ...]

        Returns:
            五行统计信息
        """
        wuxing_count = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}

        for gan, zhi in pillars:
            if gan and gan in TIAN_GAN_WUXING:
                wuxing_count[TIAN_GAN_WUXING[gan]] += 1
            if zhi and zhi in DI_ZHI_WUXING:
                wuxing_count[DI_ZHI_WUXING[zhi]] += 1

        # 找出最旺和最弱
        max_wuxing = max(wuxing_count, key=wuxing_count.get)
        min_wuxing = min(wuxing_count, key=wuxing_count.get)

        return {
            "统计": wuxing_count,
            "最旺": max_wuxing,
            "最弱": min_wuxing
        }

    def analyze_useful_god(self, day_master: str, wuxing_count: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析用神喜忌

        Args:
            day_master: 日主
            wuxing_count: 五行统计

        Returns:
            用神分析结果
        """
        day_master_wuxing = TIAN_GAN_WUXING[day_master]
        count = wuxing_count["统计"]

        # 简化判断：日主五行过旺则身强，过弱则身弱
        day_master_count = count[day_master_wuxing]

        if day_master_count >= 4:
            strength = "身强"
            # 身强需要克泄耗
            ke_wuxing = WUXING_KE[day_master_wuxing]
            xie_wuxing = WUXING_SHENG[day_master_wuxing]
            useful_god = ke_wuxing
            favorable = [ke_wuxing, xie_wuxing]
        elif day_master_count <= 1:
            strength = "身弱"
            # 身弱需要生扶
            sheng_wuxing = [w for w, v in WUXING_SHENG.items() if v == day_master_wuxing][0]
            useful_god = sheng_wuxing
            favorable = [sheng_wuxing, day_master_wuxing]
        else:
            strength = "中和"
            useful_god = day_master_wuxing
            favorable = [day_master_wuxing]

        # 忌神为用神所克的五行
        unfavorable = [WUXING_KE[useful_god]] if useful_god in WUXING_KE else []

        return {
            "日主强弱": strength,
            "用神": useful_god,
            "喜神": favorable,
            "忌神": unfavorable
        }

    def calculate_dayun(
        self,
        year_pillar: Tuple[str, str],
        month_pillar: Tuple[str, str],
        gender: str,
        birth_year: int,
        birth_month: int,
        birth_day: int
    ) -> List[Dict[str, Any]]:
        """
        计算大运

        Args:
            year_pillar: 年柱
            month_pillar: 月柱
            gender: 性别
            birth_year: 出生年
            birth_month: 出生月
            birth_day: 出生日

        Returns:
            大运列表
        """
        # 判断顺逆（阳男阴女顺排，阴男阳女逆排）
        year_gan_yinyang = TIAN_GAN_YINYANG[year_pillar[0]]
        is_forward = (year_gan_yinyang == "阳" and gender == "male") or \
                    (year_gan_yinyang == "阴" and gender == "female")

        # 获取月柱的甲子索引
        month_jiazi = f"{month_pillar[0]}{month_pillar[1]}"
        month_index = JIA_ZI_60.index(month_jiazi)

        # 计算起运年龄（简化为8岁）
        start_age = 8

        # 排大运（每步大运10年）
        dayun_list = []
        for i in range(8):  # 排8步大运
            if is_forward:
                dayun_index = (month_index + i + 1) % 60
            else:
                dayun_index = (month_index - i - 1) % 60

            dayun_jiazi = JIA_ZI_60[dayun_index]
            dayun_gan = dayun_jiazi[0]
            dayun_zhi = dayun_jiazi[1]

            dayun_list.append({
                "大运": dayun_jiazi,
                "天干": dayun_gan,
                "地支": dayun_zhi,
                "起始年龄": start_age + i * 10,
                "结束年龄": start_age + (i + 1) * 10 - 1,
                "五行": TIAN_GAN_WUXING[dayun_gan]
            })

        return dayun_list

    def calculate_shensha(
        self,
        year_gan: str,
        year_zhi: str,
        month_zhi: str,
        day_gan: str,
        day_zhi: str,
        hour_zhi: Optional[str] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        计算神煞

        Args:
            year_gan: 年干
            year_zhi: 年支
            month_zhi: 月支
            day_gan: 日干
            day_zhi: 日支
            hour_zhi: 时支

        Returns:
            神煞字典（按吉凶分类）
        """
        # 构建四柱地支列表
        pillars_zhi = [year_zhi, month_zhi, day_zhi]
        if hour_zhi:
            pillars_zhi.append(hour_zhi)

        # 构建四柱天干列表（用于天德月德查询）
        # 这里只需要年干和日干
        pillars_gan = [year_gan, None, day_gan]  # 月干和时干在此不需要
        if hour_zhi:
            pillars_gan.append(None)

        shensha_found = {
            "贵人": [],
            "吉星": [],
            "中性": [],
            "凶星": []
        }

        # 1. 天乙贵人（日干查四柱地支）
        tianyi_zhi_list = TIANYI_GUIREN.get(day_gan, [])
        for zhi in tianyi_zhi_list:
            if zhi in pillars_zhi:
                position = self._get_pillar_position(zhi, pillars_zhi)
                shensha_found["贵人"].append({
                    "名称": "天乙贵人",
                    "位置": position,
                    "地支": zhi,
                    "属性": SHENSHA_PROPERTIES["天乙贵人"]
                })

        # 2. 文昌贵人（日干查四柱地支）
        wenchang_zhi = WENCHANG_GUIREN.get(day_gan)
        if wenchang_zhi and wenchang_zhi in pillars_zhi:
            position = self._get_pillar_position(wenchang_zhi, pillars_zhi)
            shensha_found["贵人"].append({
                "名称": "文昌贵人",
                "位置": position,
                "地支": wenchang_zhi,
                "属性": SHENSHA_PROPERTIES["文昌贵人"]
            })

        # 3. 天德贵人（月支查四柱天干或地支）
        tiande = TIANDE_GUIREN.get(month_zhi)
        if tiande:
            # 天德可能是天干或地支
            if tiande in TIAN_GAN:
                # 查天干
                if tiande == year_gan:
                    shensha_found["贵人"].append({
                        "名称": "天德贵人",
                        "位置": "年柱",
                        "天干": tiande,
                        "属性": SHENSHA_PROPERTIES["天德贵人"]
                    })
                elif tiande == day_gan:
                    shensha_found["贵人"].append({
                        "名称": "天德贵人",
                        "位置": "日柱",
                        "天干": tiande,
                        "属性": SHENSHA_PROPERTIES["天德贵人"]
                    })
            else:
                # 查地支
                if tiande in pillars_zhi:
                    position = self._get_pillar_position(tiande, pillars_zhi)
                    shensha_found["贵人"].append({
                        "名称": "天德贵人",
                        "位置": position,
                        "地支": tiande,
                        "属性": SHENSHA_PROPERTIES["天德贵人"]
                    })

        # 4. 月德贵人（月支查四柱天干或地支）
        yuede = YUEDE_GUIREN.get(month_zhi)
        if yuede:
            # 月德可能是天干或地支
            if yuede in TIAN_GAN:
                # 查天干
                if yuede == year_gan:
                    shensha_found["贵人"].append({
                        "名称": "月德贵人",
                        "位置": "年柱",
                        "天干": yuede,
                        "属性": SHENSHA_PROPERTIES["月德贵人"]
                    })
                elif yuede == day_gan:
                    shensha_found["贵人"].append({
                        "名称": "月德贵人",
                        "位置": "日柱",
                        "天干": yuede,
                        "属性": SHENSHA_PROPERTIES["月德贵人"]
                    })
            else:
                # 查地支
                if yuede in pillars_zhi:
                    position = self._get_pillar_position(yuede, pillars_zhi)
                    shensha_found["贵人"].append({
                        "名称": "月德贵人",
                        "位置": position,
                        "地支": yuede,
                        "属性": SHENSHA_PROPERTIES["月德贵人"]
                    })

        # 5. 将星（年支查四柱地支）
        jiangxing_zhi = JIANGXING.get(year_zhi)
        if jiangxing_zhi and jiangxing_zhi in pillars_zhi:
            position = self._get_pillar_position(jiangxing_zhi, pillars_zhi)
            shensha_found["吉星"].append({
                "名称": "将星",
                "位置": position,
                "地支": jiangxing_zhi,
                "属性": SHENSHA_PROPERTIES["将星"]
            })

        # 6. 金舆（年支查四柱地支）
        jinyu_zhi = JINYU.get(year_zhi)
        if jinyu_zhi and jinyu_zhi in pillars_zhi:
            position = self._get_pillar_position(jinyu_zhi, pillars_zhi)
            shensha_found["吉星"].append({
                "名称": "金舆",
                "位置": position,
                "地支": jinyu_zhi,
                "属性": SHENSHA_PROPERTIES["金舆"]
            })

        # 7. 桃花（年支查四柱地支）
        taohua_zhi = TAOHUA.get(year_zhi)
        if taohua_zhi and taohua_zhi in pillars_zhi:
            position = self._get_pillar_position(taohua_zhi, pillars_zhi)
            shensha_found["中性"].append({
                "名称": "桃花",
                "位置": position,
                "地支": taohua_zhi,
                "属性": SHENSHA_PROPERTIES["桃花"]
            })

        # 8. 驿马（年支查四柱地支）
        yima_zhi = YIMA.get(year_zhi)
        if yima_zhi and yima_zhi in pillars_zhi:
            position = self._get_pillar_position(yima_zhi, pillars_zhi)
            shensha_found["中性"].append({
                "名称": "驿马",
                "位置": position,
                "地支": yima_zhi,
                "属性": SHENSHA_PROPERTIES["驿马"]
            })

        # 9. 华盖（年支查四柱地支）
        huagai_zhi = HUAGAI.get(year_zhi)
        if huagai_zhi and huagai_zhi in pillars_zhi:
            position = self._get_pillar_position(huagai_zhi, pillars_zhi)
            shensha_found["中性"].append({
                "名称": "华盖",
                "位置": position,
                "地支": huagai_zhi,
                "属性": SHENSHA_PROPERTIES["华盖"]
            })

        # 10. 羊刃（日干查四柱地支）
        yangren_zhi = YANGREN.get(day_gan)
        if yangren_zhi and yangren_zhi in pillars_zhi:
            position = self._get_pillar_position(yangren_zhi, pillars_zhi)
            shensha_found["凶星"].append({
                "名称": "羊刃",
                "位置": position,
                "地支": yangren_zhi,
                "属性": SHENSHA_PROPERTIES["羊刃"]
            })

        # 11. 劫煞（年支查四柱地支）
        jiesha_zhi = JIESHA.get(year_zhi)
        if jiesha_zhi and jiesha_zhi in pillars_zhi:
            position = self._get_pillar_position(jiesha_zhi, pillars_zhi)
            shensha_found["凶星"].append({
                "名称": "劫煞",
                "位置": position,
                "地支": jiesha_zhi,
                "属性": SHENSHA_PROPERTIES["劫煞"]
            })

        # 12. 灾煞（年支查四柱地支）
        zaisha_zhi = ZAISHA.get(year_zhi)
        if zaisha_zhi and zaisha_zhi in pillars_zhi:
            position = self._get_pillar_position(zaisha_zhi, pillars_zhi)
            shensha_found["凶星"].append({
                "名称": "灾煞",
                "位置": position,
                "地支": zaisha_zhi,
                "属性": SHENSHA_PROPERTIES["灾煞"]
            })

        return shensha_found

    def _get_pillar_position(self, target_zhi: str, pillars_zhi: List[str]) -> str:
        """
        获取地支在四柱中的位置

        Args:
            target_zhi: 目标地支
            pillars_zhi: 四柱地支列表

        Returns:
            位置描述
        """
        positions = ["年柱", "月柱", "日柱", "时柱"]
        for i, zhi in enumerate(pillars_zhi):
            if zhi == target_zhi:
                return positions[i] if i < len(positions) else "未知"
        return "未知"

    def analyze_shensha_influence(self, shensha: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        分析神煞影响

        Args:
            shensha: 神煞字典

        Returns:
            神煞影响分析
        """
        # 统计各类神煞数量
        guiren_count = len(shensha.get("贵人", []))
        jixing_count = len(shensha.get("吉星", []))
        zhongxing_count = len(shensha.get("中性", []))
        xiongxing_count = len(shensha.get("凶星", []))

        # 计算吉凶评分（0-1范围）
        # 贵人权重最高，吉星次之，凶星负分
        score = (guiren_count * 0.15 + jixing_count * 0.1 - xiongxing_count * 0.08) + 0.5
        score = max(0.3, min(1.0, score))

        # 综合评价
        if score >= 0.8:
            overall_assessment = "神煞配置极佳，贵人多助，吉星高照"
        elif score >= 0.65:
            overall_assessment = "神煞配置良好，多有吉神庇佑"
        elif score >= 0.5:
            overall_assessment = "神煞配置平衡，吉凶参半"
        elif score >= 0.35:
            overall_assessment = "神煞配置欠佳，需注意凶星影响"
        else:
            overall_assessment = "神煞配置不利，凶星较多，宜谨慎"

        # 特殊组合判断
        special_combinations = []

        # 查找天乙贵人
        tianyi_found = any(s["名称"] == "天乙贵人" for s in shensha.get("贵人", []))
        tiande_found = any(s["名称"] == "天德贵人" for s in shensha.get("贵人", []))
        yuede_found = any(s["名称"] == "月德贵人" for s in shensha.get("贵人", []))

        if tianyi_found and tiande_found:
            special_combinations.append("天乙天德同现，福德深厚，逢凶化吉")

        if tiande_found and yuede_found:
            special_combinations.append("天月德合，德行兼备，一生安稳")

        # 查找文昌
        wenchang_found = any(s["名称"] == "文昌贵人" for s in shensha.get("贵人", []))
        if wenchang_found:
            special_combinations.append("文昌入命，聪明好学，利于文职考试")

        # 查找桃花
        taohua_found = any(s["名称"] == "桃花" for s in shensha.get("中性", []))
        if taohua_found:
            # 判断桃花位置
            taohua_items = [s for s in shensha.get("中性", []) if s["名称"] == "桃花"]
            for item in taohua_items:
                if item["位置"] == "时柱":
                    special_combinations.append("桃花在时柱，晚年桃花旺，子女有魅力")
                elif item["位置"] == "日柱":
                    special_combinations.append("桃花在日柱，本人魅力强，异性缘佳")

        # 查找驿马
        yima_found = any(s["名称"] == "驿马" for s in shensha.get("中性", []))
        if yima_found:
            special_combinations.append("驿马入命，一生多动，适合外出发展")

        # 查找羊刃
        yangren_found = any(s["名称"] == "羊刃" for s in shensha.get("凶星", []))
        if yangren_found:
            special_combinations.append("羊刃入命，性格刚强，需防意外血光")

        return {
            "统计": {
                "贵人数": guiren_count,
                "吉星数": jixing_count,
                "中性星数": zhongxing_count,
                "凶星数": xiongxing_count
            },
            "吉凶评分": score,
            "综合评价": overall_assessment,
            "特殊组合": special_combinations if special_combinations else ["无特殊神煞组合"]
        }

    def calculate_marriage_compatibility(
        self,
        person1_bazi: Dict[str, Any],
        person2_bazi: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        计算两人八字姻缘匹配度（合婚）

        Args:
            person1_bazi: 第一个人的八字完整信息
            person2_bazi: 第二个人的八字完整信息

        Returns:
            姻缘匹配度分析结果
        """
        # 提取关键信息
        p1_year_zhi = person1_bazi["年柱"]["地支"]
        p2_year_zhi = person2_bazi["年柱"]["地支"]
        p1_day_gan = person1_bazi["日主"]
        p2_day_gan = person2_bazi["日主"]
        p1_day_zhi = person1_bazi["日柱"]["地支"]
        p2_day_zhi = person2_bazi["日柱"]["地支"]

        # 初始化评分
        total_score = 0
        max_score = 0
        details = []

        # 1. 生肖相合相冲分析（30分）
        max_score += 30
        zodiac_score, zodiac_detail = self._analyze_zodiac_compatibility(p1_year_zhi, p2_year_zhi)
        total_score += zodiac_score
        details.append(zodiac_detail)

        # 2. 日主天干合化分析（25分）
        max_score += 25
        day_gan_score, day_gan_detail = self._analyze_day_gan_compatibility(p1_day_gan, p2_day_gan)
        total_score += day_gan_score
        details.append(day_gan_detail)

        # 3. 五行互补分析（20分）
        max_score += 20
        wuxing_score, wuxing_detail = self._analyze_wuxing_compatibility(
            person1_bazi["五行统计"]["统计"],
            person2_bazi["五行统计"]["统计"]
        )
        total_score += wuxing_score
        details.append(wuxing_detail)

        # 4. 纳音相生相克分析（15分）
        max_score += 15
        nayin_score, nayin_detail = self._analyze_nayin_compatibility(
            person1_bazi["纳音"]["年柱"],
            person2_bazi["纳音"]["年柱"]
        )
        total_score += nayin_score
        details.append(nayin_detail)

        # 5. 神煞相配分析（10分）
        max_score += 10
        shensha_score, shensha_detail = self._analyze_shensha_compatibility(
            person1_bazi.get("神煞", {}),
            person2_bazi.get("神煞", {})
        )
        total_score += shensha_score
        details.append(shensha_detail)

        # 计算总分百分比
        compatibility_percentage = (total_score / max_score) * 100 if max_score > 0 else 0

        # 综合评价
        if compatibility_percentage >= 85:
            overall_rating = "极佳"
            overall_comment = "两人八字非常相配，五行互补，姻缘极佳，宜结连理"
        elif compatibility_percentage >= 70:
            overall_rating = "良好"
            overall_comment = "两人八字较为相配，虽有小瑕疵，但整体和谐，婚姻可成"
        elif compatibility_percentage >= 55:
            overall_rating = "中等"
            overall_comment = "两人八字基本相合，需要互相包容理解，经营得当可白头偕老"
        elif compatibility_percentage >= 40:
            overall_rating = "一般"
            overall_comment = "两人八字略有冲克，需要更多沟通和调和，婚姻需谨慎考虑"
        else:
            overall_rating = "不佳"
            overall_comment = "两人八字冲克较多，建议慎重考虑，或通过其他方式化解"

        return {
            "匹配度评分": round(compatibility_percentage, 2),
            "总得分": total_score,
            "满分": max_score,
            "综合评级": overall_rating,
            "综合评价": overall_comment,
            "详细分析": details,
            "建议": self._generate_compatibility_advice(compatibility_percentage, details)
        }

    def _analyze_zodiac_compatibility(self, zhi1: str, zhi2: str) -> Tuple[float, str]:
        """分析生肖相合相冲"""
        # 地支六合
        liu_he = {
            "子": "丑", "丑": "子",
            "寅": "亥", "亥": "寅",
            "卯": "戌", "戌": "卯",
            "辰": "酉", "酉": "辰",
            "巳": "申", "申": "巳",
            "午": "未", "未": "午"
        }

        # 地支三合
        san_he = {
            ("申", "子", "辰"): "水",
            ("亥", "卯", "未"): "木",
            ("寅", "午", "戌"): "火",
            ("巳", "酉", "丑"): "金"
        }

        # 地支六冲
        liu_chong = {
            "子": "午", "午": "子",
            "丑": "未", "未": "丑",
            "寅": "申", "申": "寅",
            "卯": "酉", "酉": "卯",
            "辰": "戌", "戌": "辰",
            "巳": "亥", "亥": "巳"
        }

        # 地支六害
        liu_hai = {
            "子": "未", "未": "子",
            "丑": "午", "午": "丑",
            "寅": "巳", "巳": "寅",
            "卯": "辰", "辰": "卯",
            "申": "亥", "亥": "申",
            "酉": "戌", "戌": "酉"
        }

        # 判断关系
        if liu_he.get(zhi1) == zhi2:
            return 30, f"✅ 生肖六合：{zhi1}与{zhi2}为六合，天生一对，感情深厚（30分）"

        # 检查三合
        for he_set, element in san_he.items():
            if zhi1 in he_set and zhi2 in he_set:
                return 25, f"✅ 生肖三合：{zhi1}与{zhi2}为三合{element}局，相处和谐（25分）"

        if liu_chong.get(zhi1) == zhi2:
            return 5, f"⚠️ 生肖六冲：{zhi1}与{zhi2}相冲，性格差异大，需多包容（5分）"

        if liu_hai.get(zhi1) == zhi2:
            return 10, f"⚠️ 生肖六害：{zhi1}与{zhi2}相害，易生矛盾，需注意沟通（10分）"

        # 普通关系
        return 18, f"○ 生肖关系：{zhi1}与{zhi2}无特殊相合相冲，属于普通配对（18分）"

    def _analyze_day_gan_compatibility(self, gan1: str, gan2: str) -> Tuple[float, str]:
        """分析日主天干合化"""
        # 天干五合
        wu_he = {
            ("甲", "己"): "土",
            ("乙", "庚"): "金",
            ("丙", "辛"): "水",
            ("丁", "壬"): "木",
            ("戊", "癸"): "火"
        }

        # 天干相克
        ke_relation = {
            "甲": "戊", "乙": "己",
            "丙": "庚", "丁": "辛",
            "戊": "壬", "己": "癸",
            "庚": "甲", "辛": "乙",
            "壬": "丙", "癸": "丁"
        }

        # 检查五合
        for he_pair, element in wu_he.items():
            if (gan1 in he_pair and gan2 in he_pair):
                return 25, f"✅ 日主合化：{gan1}与{gan2}天干五合化{element}，夫妻恩爱和合（25分）"

        # 检查相克
        if ke_relation.get(gan1) == gan2:
            return 8, f"⚠️ 日主相克：{gan1}克{gan2}，一方强势，需学会妥协（8分）"
        if ke_relation.get(gan2) == gan1:
            return 8, f"⚠️ 日主相克：{gan2}克{gan1}，一方强势，需学会妥协（8分）"

        # 同五行
        gan_wuxing = {
            "甲": "木", "乙": "木",
            "丙": "火", "丁": "火",
            "戊": "土", "己": "土",
            "庚": "金", "辛": "金",
            "壬": "水", "癸": "水"
        }

        if gan_wuxing.get(gan1) == gan_wuxing.get(gan2):
            return 15, f"○ 日主同性：{gan1}与{gan2}同属{gan_wuxing.get(gan1)}，志同道合但需避免竞争（15分）"

        # 普通关系
        return 12, f"○ 日主关系：{gan1}与{gan2}关系平和，无特殊合克（12分）"

    def _analyze_wuxing_compatibility(self, wuxing1: Dict[str, int], wuxing2: Dict[str, int]) -> Tuple[float, str]:
        """分析五行互补"""
        # 计算各自缺失的五行
        wuxing_list = ["金", "木", "水", "火", "土"]
        p1_weak = [w for w in wuxing_list if wuxing1.get(w, 0) <= 1]
        p2_weak = [w for w in wuxing_list if wuxing2.get(w, 0) <= 1]

        # 互补分析
        p1_补p2 = [w for w in p1_weak if wuxing2.get(w, 0) >= 2]
        p2_补p1 = [w for w in p2_weak if wuxing1.get(w, 0) >= 2]

        complement_count = len(p1_补p2) + len(p2_补p1)

        if complement_count >= 4:
            score = 20
            detail = f"✅ 五行互补：双方五行高度互补（{complement_count}项），相辅相成（20分）"
        elif complement_count >= 2:
            score = 15
            detail = f"✅ 五行互补：双方五行较好互补（{complement_count}项），互相补益（15分）"
        elif complement_count >= 1:
            score = 10
            detail = f"○ 五行互补：双方有一定互补（{complement_count}项），需注意平衡（10分）"
        else:
            score = 6
            detail = f"⚠️ 五行互补：双方五行互补较少，需要后天调和（6分）"

        return score, detail

    def _analyze_nayin_compatibility(self, nayin1: str, nayin2: str) -> Tuple[float, str]:
        """分析纳音相生相克"""
        # 纳音五行提取
        nayin_wuxing_map = {
            "金": ["海中金", "金箔金", "白蜡金", "砂石金", "剑锋金", "钗钏金"],
            "木": ["桑柘木", "大林木", "杨柳木", "石榴木", "松柏木", "平地木"],
            "水": ["涧下水", "大溪水", "长流水", "天河水", "泉中水", "大海水"],
            "火": ["炉中火", "山头火", "霹雳火", "山下火", "覆灯火", "天上火"],
            "土": ["路旁土", "城头土", "屋上土", "壁上土", "大驿土", "砂石土"]
        }

        # 找到纳音对应的五行
        ny1_wuxing = None
        ny2_wuxing = None
        for wuxing, nayin_list in nayin_wuxing_map.items():
            if nayin1 in nayin_list:
                ny1_wuxing = wuxing
            if nayin2 in nayin_list:
                ny2_wuxing = wuxing

        if not ny1_wuxing or not ny2_wuxing:
            return 8, f"○ 纳音关系：{nayin1}与{nayin2}无法判断（8分）"

        # 五行相生相克关系
        sheng = {
            "金": "水", "水": "木", "木": "火", "火": "土", "土": "金"
        }
        ke = {
            "金": "木", "木": "土", "土": "水", "水": "火", "火": "金"
        }

        if sheng.get(ny1_wuxing) == ny2_wuxing or sheng.get(ny2_wuxing) == ny1_wuxing:
            return 15, f"✅ 纳音相生：{nayin1}（{ny1_wuxing}）与{nayin2}（{ny2_wuxing}）相生，互相滋养（15分）"
        elif ke.get(ny1_wuxing) == ny2_wuxing or ke.get(ny2_wuxing) == ny1_wuxing:
            return 5, f"⚠️ 纳音相克：{nayin1}（{ny1_wuxing}）与{nayin2}（{ny2_wuxing}）相克，易生摩擦（5分）"
        elif ny1_wuxing == ny2_wuxing:
            return 10, f"○ 纳音同性：{nayin1}与{nayin2}同属{ny1_wuxing}，性格相似（10分）"
        else:
            return 8, f"○ 纳音关系：{nayin1}与{nayin2}关系平和（8分）"

    def _analyze_shensha_compatibility(self, shensha1: Dict, shensha2: Dict) -> Tuple[float, str]:
        """分析神煞相配"""
        # 提取关键神煞
        def extract_shensha_names(shensha_dict):
            names = set()
            for category in ["贵人", "吉星", "中性", "凶星"]:
                for item in shensha_dict.get(category, []):
                    names.add(item.get("名称", ""))
            return names

        ss1_names = extract_shensha_names(shensha1)
        ss2_names = extract_shensha_names(shensha2)

        # 共同的吉神
        common_jixing = set()
        for name in ["天乙贵人", "文昌", "天德", "月德", "福星", "禄神"]:
            if name in ss1_names and name in ss2_names:
                common_jixing.add(name)

        # 共同的凶神
        common_xiongxing = set()
        for name in ["羊刃", "劫煞", "孤辰", "寡宿", "亡神"]:
            if name in ss1_names and name in ss2_names:
                common_xiongxing.add(name)

        if len(common_jixing) >= 2:
            return 10, f"✅ 神煞相配：双方共有{len(common_jixing)}个吉神（{','.join(common_jixing)}），贵人相助（10分）"
        elif len(common_jixing) == 1:
            return 8, f"✅ 神煞相配：双方共有吉神{','.join(common_jixing)}，有助婚姻（8分）"
        elif len(common_xiongxing) >= 2:
            return 3, f"⚠️ 神煞相配：双方共有{len(common_xiongxing)}个凶神，需多化解（3分）"
        else:
            return 6, f"○ 神煞相配：双方神煞无特殊共鸣（6分）"

    def _generate_compatibility_advice(self, score: float, details: List[str]) -> str:
        """生成姻缘建议"""
        advice_parts = []

        if score >= 70:
            advice_parts.append("你们的八字配对非常理想，建议：")
            advice_parts.append("1. 珍惜这段缘分，互相尊重理解")
            advice_parts.append("2. 选择吉日良辰举办婚礼")
            advice_parts.append("3. 婚后互相扶持，共创美好未来")
        elif score >= 55:
            advice_parts.append("你们的八字配对基本和谐，建议：")
            advice_parts.append("1. 重视婚前的沟通和了解")
            advice_parts.append("2. 学会包容对方的不同")
            advice_parts.append("3. 遇到问题时多从对方角度考虑")
        else:
            advice_parts.append("你们的八字配对存在一些挑战，建议：")
            advice_parts.append("1. 慎重考虑这段婚姻关系")
            advice_parts.append("2. 如决定继续，需要更多的沟通和理解")
            advice_parts.append("3. 可考虑通过风水、佩戴吉祥物等方式化解")
            advice_parts.append("4. 婚前务必寻求专业命理师的详细指导")

        return "\n".join(advice_parts)

    # ==================== V2增强：三柱分析与并行计算 ====================

    def calculate_three_pillar(
        self,
        year: int,
        month: int,
        day: int,
        gender: Optional[str] = None,
        calendar_type: str = "solar"
    ) -> Dict[str, Any]:
        """
        三柱分析模式（无时辰时的降级计算）

        当用户不记得出生时辰时，使用年月日三柱进行分析
        提供特殊的三柱解读视角

        Args:
            year: 出生年
            month: 出生月
            day: 出生日
            gender: 性别
            calendar_type: 历法类型

        Returns:
            三柱分析结果
        """
        # 农历转换
        if calendar_type == "lunar":
            try:
                solar_date = LunarCalendar.lunar_to_solar(year, month, day, is_leap_month=False)
                year = solar_date.year
                month = solar_date.month
                day = solar_date.day
            except ValueError as e:
                raise ValueError(f"农历日期转换失败：{e}")

        # 计算三柱
        year_pillar = self.calculate_year_pillar(year, month, day)
        month_pillar = self.calculate_month_pillar(year, month, day)
        day_pillar = self.calculate_day_pillar(year, month, day)

        # 日主
        day_master = day_pillar[0]

        # 三柱列表
        three_pillars = [
            f"{year_pillar[0]}{year_pillar[1]}",
            f"{month_pillar[0]}{month_pillar[1]}",
            f"{day_pillar[0]}{day_pillar[1]}"
        ]

        # 三柱十神
        ten_gods = {
            "年干": SHI_SHEN[day_master][year_pillar[0]],
            "月干": SHI_SHEN[day_master][month_pillar[0]],
            "日干": SHI_SHEN[day_master][day_pillar[0]]
        }

        # 三柱五行（6个元素）
        wuxing_count = self.calculate_wuxing_count([year_pillar, month_pillar, day_pillar])

        # 纳音
        nayin = {
            "年柱": NA_YIN.get(f"{year_pillar[0]}{year_pillar[1]}", "未知"),
            "月柱": NA_YIN.get(f"{month_pillar[0]}{month_pillar[1]}", "未知"),
            "日柱": NA_YIN.get(f"{day_pillar[0]}{day_pillar[1]}", "未知")
        }

        # 简化用神分析
        useful_god_analysis = self.analyze_useful_god(day_master, wuxing_count)

        # 大运（可能不够准确因为缺少时柱）
        dayun_list = []
        if gender:
            dayun_list = self.calculate_dayun(year_pillar, month_pillar, gender, year, month, day)

        # 三柱神煞（无时支）
        shensha = self.calculate_shensha(
            year_gan=year_pillar[0],
            year_zhi=year_pillar[1],
            month_zhi=month_pillar[1],
            day_gan=day_pillar[0],
            day_zhi=day_pillar[1],
            hour_zhi=None
        )

        shensha_analysis = self.analyze_shensha_influence(shensha)

        # 三柱模式特殊说明
        limitations = [
            "无时柱：部分格局分析无法进行",
            "时柱十神未知，人际关系分析受限",
            "晚年运势分析精度降低",
            "子女宫信息缺失"
        ]

        # 三柱模式推荐理论
        recommended_theories = [
            "梅花易数（不依赖时辰）",
            "小六壬（可用当前时间）",
            "测字术（不依赖时辰）"
        ]

        return {
            "mode": "three_pillar",
            "三柱": three_pillars,
            "年柱": {"天干": year_pillar[0], "地支": year_pillar[1], "纳音": nayin["年柱"]},
            "月柱": {"天干": month_pillar[0], "地支": month_pillar[1], "纳音": nayin["月柱"]},
            "日柱": {"天干": day_pillar[0], "地支": day_pillar[1], "纳音": nayin["日柱"]},
            "时柱": None,
            "日主": day_master,
            "十神": ten_gods,
            "五行统计": wuxing_count,
            "用神分析": useful_god_analysis,
            "神煞": shensha,
            "神煞分析": shensha_analysis,
            "大运": dayun_list,
            "置信度": 0.65,  # 三柱模式置信度较低
            "局限性": limitations,
            "推荐补充理论": recommended_theories
        }

    def calculate_parallel_bazi(
        self,
        year: int,
        month: int,
        day: int,
        candidate_hours: List[int],
        gender: Optional[str] = None,
        calendar_type: str = "solar"
    ) -> Dict[str, Any]:
        """
        并行计算多个候选时辰的八字

        当用户时辰不确定但有范围时，并行计算所有候选

        Args:
            year: 出生年
            month: 出生月
            day: 出生日
            candidate_hours: 候选时辰列表
            gender: 性别
            calendar_type: 历法类型

        Returns:
            包含所有候选八字分析的结果
        """
        results = []
        base_result = None

        for hour in candidate_hours:
            try:
                # 计算该时辰的完整八字
                bazi_result = self.calculate_full_bazi(
                    year, month, day, hour, gender, calendar_type
                )

                # 保存第一个作为基准对比
                if base_result is None:
                    base_result = bazi_result

                # 标记该时辰的八字
                bazi_result["candidate_hour"] = hour
                bazi_result["hour_zhi"] = HOUR_ZHI_MAP.get(hour, "子")

                results.append(bazi_result)

            except Exception as e:
                results.append({
                    "candidate_hour": hour,
                    "error": str(e)
                })

        # 分析不同时辰之间的差异
        differences = self._analyze_hour_differences(results) if len(results) > 1 else []

        # 计算整体置信度（基于候选数量反推）
        overall_confidence = max(0.5, 1.0 - (len(candidate_hours) - 1) * 0.1)

        return {
            "mode": "parallel_calculation",
            "candidate_count": len(candidate_hours),
            "results": results,
            "differences": differences,
            "overall_confidence": overall_confidence,
            "recommendation": self._generate_hour_recommendation(results, differences)
        }

    def _analyze_hour_differences(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """分析不同时辰八字之间的差异"""
        differences = []

        if len(results) < 2:
            return differences

        # 比较时柱干支
        hour_pillars = [(r.get("candidate_hour"), r.get("时柱")) for r in results if r.get("时柱")]

        # 比较十神
        ten_gods_list = [(r.get("candidate_hour"), r.get("十神", {}).get("时干")) for r in results if r.get("十神")]

        unique_hour_ganzhi = set(f"{p[1]['天干']}{p[1]['地支']}" for p in hour_pillars if p[1])
        unique_ten_gods = set(t[1] for t in ten_gods_list if t[1])

        differences.append({
            "aspect": "时柱干支",
            "variations": list(unique_hour_ganzhi),
            "count": len(unique_hour_ganzhi),
            "impact": "高" if len(unique_hour_ganzhi) > 3 else "中" if len(unique_hour_ganzhi) > 1 else "低"
        })

        differences.append({
            "aspect": "时干十神",
            "variations": list(unique_ten_gods),
            "count": len(unique_ten_gods),
            "impact": "高" if len(unique_ten_gods) > 3 else "中" if len(unique_ten_gods) > 1 else "低"
        })

        # 比较用神分析是否一致
        strength_list = [r.get("用神分析", {}).get("日主强弱") for r in results if r.get("用神分析")]
        unique_strength = set(s for s in strength_list if s)

        differences.append({
            "aspect": "日主强弱",
            "variations": list(unique_strength),
            "count": len(unique_strength),
            "impact": "极高" if len(unique_strength) > 1 else "低"
        })

        return differences

    def _generate_hour_recommendation(
        self,
        results: List[Dict[str, Any]],
        differences: List[Dict[str, Any]]
    ) -> str:
        """生成时辰选择建议"""
        # 检查差异程度
        high_impact = sum(1 for d in differences if d.get("impact") in ["高", "极高"])

        if high_impact >= 2:
            return "各候选时辰分析结果差异较大，建议通过以下方式确定时辰：\n" \
                   "1. 询问家人确认出生时间\n" \
                   "2. 查看出生证明或户口本\n" \
                   "3. 提供重大生活事件进行反推验证"
        elif high_impact == 1:
            return "各候选时辰有一定差异，但核心分析相近。\n" \
                   "建议参考共同特征，保守解读差异部分。"
        else:
            return "各候选时辰分析结果相近，可综合参考所有分析。\n" \
                   "时辰差异对本次分析影响较小。"

    def calculate_with_shichen_info(
        self,
        year: int,
        month: int,
        day: int,
        shichen_info: Any,  # ShichenInfo from shichen_handler
        gender: Optional[str] = None,
        calendar_type: str = "solar"
    ) -> Dict[str, Any]:
        """
        使用ShichenInfo进行智能八字计算

        根据时辰信息的状态自动选择计算模式

        Args:
            year, month, day: 出生日期
            shichen_info: ShichenInfo对象
            gender: 性别
            calendar_type: 历法类型

        Returns:
            八字分析结果
        """
        # 延迟导入避免循环依赖
        try:
            from core.shichen_handler import ShichenStatus
        except ImportError:
            # 回退到普通计算
            return self.calculate_full_bazi(year, month, day, None, gender, calendar_type)

        status = shichen_info.status

        if status == ShichenStatus.CERTAIN:
            # 确定时辰：正常四柱计算
            return self.calculate_full_bazi(
                year, month, day, shichen_info.hour, gender, calendar_type
            )

        elif status == ShichenStatus.UNKNOWN:
            # 完全未知：使用三柱模式
            result = self.calculate_three_pillar(year, month, day, gender, calendar_type)
            result["shichen_status"] = "unknown"
            return result

        else:
            # KNOWN_RANGE 或 UNCERTAIN：并行计算
            candidates = shichen_info.candidates
            if not candidates:
                candidates = list(range(24))

            # 限制候选数量以避免计算过多
            if len(candidates) > 6:
                # 按时辰分组，每个时辰取代表小时
                dizhi_hours = {}
                for h in candidates:
                    dizhi = HOUR_ZHI_MAP.get(h, "子")
                    if dizhi not in dizhi_hours:
                        dizhi_hours[dizhi] = h
                candidates = list(dizhi_hours.values())

            result = self.calculate_parallel_bazi(
                year, month, day, candidates, gender, calendar_type
            )
            result["shichen_status"] = status.value if hasattr(status, 'value') else str(status)
            result["shichen_confidence"] = shichen_info.confidence

            return result
