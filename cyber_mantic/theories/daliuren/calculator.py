"""
大六壬计算器
"""
from datetime import datetime
from typing import Dict, Any, List, Tuple
from .constants import *


class DaLiuRenCalculator:
    """大六壬计算器"""

    def calculate_daliuren(
        self,
        year: int,
        month: int,
        day: int,
        hour: int,
        question: str = ""
    ) -> Dict[str, Any]:
        """
        计算大六壬课式

        Args:
            year: 年
            month: 月
            day: 日
            hour: 时（0-23）
            question: 问题描述

        Returns:
            大六壬课式
        """
        # 计算日干支
        day_gan, day_zhi = self._calculate_day_ganzhi(year, month, day)

        # 计算时支
        hour_zhi = self._calculate_hour_zhi(hour)

        # 计算月将
        month_jiang = self._calculate_month_jiang(month)

        # 起四课
        si_ke = self._calculate_si_ke(day_gan, day_zhi, hour_zhi, month_jiang)

        # 取三传
        san_chuan = self._calculate_san_chuan(si_ke, day_gan, day_zhi)

        # 配天将
        tian_jiang_config = self._configure_tian_jiang(san_chuan, day_gan, hour_zhi)

        # 判断课体
        ke_ti = self._determine_ke_ti(san_chuan, day_gan, day_zhi)

        # 分析吉凶
        judgment = self._analyze_judgment(san_chuan, tian_jiang_config, ke_ti)

        return {
            "日干支": f"{day_gan}{day_zhi}",
            "时支": hour_zhi,
            "月将": month_jiang,
            "四课": si_ke,
            "三传": san_chuan,
            "天将": tian_jiang_config,
            "课体": ke_ti,
            "吉凶判断": judgment["judgment"],
            "综合评分": judgment["score"],
            "详细分析": judgment["analysis"],
            "置信度": 0.75
        }

    def _calculate_day_ganzhi(self, year: int, month: int, day: int) -> Tuple[str, str]:
        """计算日干支（简化算法）"""
        from datetime import datetime

        # 基准日：2000年1月1日为庚辰日
        base_date = datetime(2000, 1, 1)
        target_date = datetime(year, month, day)
        days_diff = (target_date - base_date).days

        # 基准日的甲子索引
        base_gan_index = 6  # 庚
        base_zhi_index = 4  # 辰

        # 计算目标日的干支
        gan_index = (base_gan_index + days_diff) % 10
        zhi_index = (base_zhi_index + days_diff) % 12

        return TIAN_GAN[gan_index], DI_ZHI[zhi_index]

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
        """计算月将（正月登明在亥）"""
        # 正月亥，二月戌，三月酉...逆行
        month_jiang_map = {
            1: "亥", 2: "戌", 3: "酉", 4: "申", 5: "未", 6: "午",
            7: "巳", 8: "辰", 9: "卯", 10: "寅", 11: "丑", 12: "子"
        }
        return month_jiang_map.get(month, "亥")

    def _calculate_si_ke(
        self,
        day_gan: str,
        day_zhi: str,
        hour_zhi: str,
        month_jiang: str
    ) -> List[Dict[str, str]]:
        """
        起四课

        四课：
        - 第一课：日干上神（干阳神）
        - 第二课：干上神之阴神
        - 第三课：日支上神（支阳神）
        - 第四课：支上神之阴神
        """
        # 获取日干日支在地支中的位置
        day_gan_index = TIAN_GAN.index(day_gan)
        day_zhi_index = DI_ZHI.index(day_zhi)

        # 计算月将加时（从月将起，顺数到时支）
        month_jiang_index = DI_ZHI.index(month_jiang)
        hour_zhi_index = DI_ZHI.index(hour_zhi)

        # 寻地盘（月将加时）
        di_pan_start = (month_jiang_index - hour_zhi_index) % 12

        # 第一课：日干上神
        # 简化：以日干配地支
        gan_shang_shen_index = (day_gan_index + di_pan_start) % 12
        gan_shang_shen = DI_ZHI[gan_shang_shen_index]

        # 第二课：干上神之冲
        gan_chong = DI_ZHI_CHONG.get(gan_shang_shen, DI_ZHI[(gan_shang_shen_index + 6) % 12])

        # 第三课：日支上神
        zhi_shang_shen_index = (day_zhi_index + di_pan_start) % 12
        zhi_shang_shen = DI_ZHI[zhi_shang_shen_index]

        # 第四课：支上神之冲
        zhi_chong = DI_ZHI_CHONG.get(zhi_shang_shen, DI_ZHI[(zhi_shang_shen_index + 6) % 12])

        si_ke = [
            {"课名": "第一课", "下": day_gan, "上": gan_shang_shen},
            {"课名": "第二课", "下": gan_shang_shen, "上": gan_chong},
            {"课名": "第三课", "下": day_zhi, "上": zhi_shang_shen},
            {"课名": "第四课", "下": zhi_shang_shen, "上": zhi_chong}
        ]

        return si_ke

    def _calculate_san_chuan(
        self,
        si_ke: List[Dict[str, str]],
        day_gan: str,
        day_zhi: str
    ) -> List[Dict[str, str]]:
        """
        取三传（简化方法）

        从四课中取三传：初传、中传、末传
        """
        # 简化取法：取四课中的上神作为三传
        # 实际大六壬有复杂的发用规则

        # 提取四课上神
        shang_shen_list = [ke["上"] for ke in si_ke]

        # 简化：取第1、3、4课的上神作为三传
        san_chuan = [
            {"传名": "初传", "地支": shang_shen_list[0]},
            {"传名": "中传", "地支": shang_shen_list[2]},
            {"传名": "末传", "地支": shang_shen_list[3]}
        ]

        return san_chuan

    def _configure_tian_jiang(
        self,
        san_chuan: List[Dict[str, str]],
        day_gan: str,
        hour_zhi: str
    ) -> List[Dict[str, Any]]:
        """
        配天将

        从贵人起，根据昼夜顺逆配置天将
        """
        # 获取贵人起始地支
        guiren_start_zhi = GUIREN_START.get(day_gan, "丑")
        guiren_index = DI_ZHI.index(guiren_start_zhi)

        # 简化：顺配（实际需要判断昼夜阴阳）
        result = []
        for i, chuan in enumerate(san_chuan):
            zhi = chuan["地支"]
            zhi_index = DI_ZHI.index(zhi)

            # 计算天将索引
            tian_jiang_index = (zhi_index - guiren_index) % 12
            tian_jiang_name = TIAN_JIANG[tian_jiang_index]

            result.append({
                "传名": chuan["传名"],
                "地支": zhi,
                "天将": tian_jiang_name,
                "属性": TIAN_JIANG_PROPERTIES[tian_jiang_name]
            })

        return result

    def _determine_ke_ti(
        self,
        san_chuan: List[Dict[str, str]],
        day_gan: str,
        day_zhi: str
    ) -> Dict[str, str]:
        """判断课体（简化）"""
        zhi_list = [c["地支"] for c in san_chuan]

        # 检查是否连茹
        zhi_indices = [DI_ZHI.index(z) for z in zhi_list]

        # 判断顺连茹
        if zhi_indices[1] == (zhi_indices[0] + 1) % 12 and \
           zhi_indices[2] == (zhi_indices[1] + 1) % 12:
            return {"名称": "顺连茹", "说明": KE_TI_SIMPLE["顺连茹"]}

        # 判断逆连茹
        if zhi_indices[1] == (zhi_indices[0] - 1) % 12 and \
           zhi_indices[2] == (zhi_indices[1] - 1) % 12:
            return {"名称": "逆连茹", "说明": KE_TI_SIMPLE["逆连茹"]}

        # 判断涉害
        has_hai = False
        for i in range(len(zhi_list) - 1):
            if DI_ZHI_HAI.get(zhi_list[i]) == zhi_list[i + 1]:
                has_hai = True
                break

        if has_hai:
            return {"名称": "涉害", "说明": KE_TI_SIMPLE["涉害"]}

        # 默认为一般课体
        return {"名称": "一般", "说明": KE_TI_SIMPLE["一般"]}

    def _analyze_judgment(
        self,
        san_chuan: List[Dict[str, str]],
        tian_jiang: List[Dict[str, Any]],
        ke_ti: Dict[str, str]
    ) -> Dict[str, Any]:
        """分析吉凶"""
        # 计算天将吉凶评分
        ji_count = 0
        xiong_count = 0

        for tj in tian_jiang:
            ji_xiong = tj["属性"]["吉凶"]
            if ji_xiong == "吉":
                ji_count += 1
            elif ji_xiong == "凶":
                xiong_count += 1

        # 计算评分
        score = 0.5 + (ji_count * 0.15) - (xiong_count * 0.15)
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

        # 课体影响
        ke_ti_desc = ke_ti["说明"]

        analysis = f"{judgment_desc}。课体为{ke_ti['名称']}，{ke_ti_desc}。"

        return {
            "judgment": judgment,
            "score": score,
            "analysis": analysis
        }
