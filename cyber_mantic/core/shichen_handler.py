"""
ShichenHandler - 时辰智能处理器

V2核心组件：统一处理时辰相关的所有逻辑
- 时辰状态管理 (certain/uncertain/known_range/unknown)
- 三柱降级模式（无时辰时使用年月日三柱）
- 多时辰并行计算
- 事件验证缩小范围
- 真太阳时转换
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from datetime import datetime, timedelta
import math

from utils.logger import get_logger


class ShichenStatus(Enum):
    """时辰精确度状态"""
    CERTAIN = "certain"           # 确定时辰（用户明确提供）
    KNOWN_RANGE = "known_range"   # 已知范围（如"上午"、"凌晨"）
    UNCERTAIN = "uncertain"       # 不确定（用户不记得）
    UNKNOWN = "unknown"           # 完全未知


@dataclass
class ShichenRange:
    """时辰范围"""
    start_hour: int       # 起始小时（0-23）
    end_hour: int         # 结束小时（0-23）
    name: str             # 范围名称（如"上午"、"子时"）
    dizhi: Optional[str] = None   # 对应地支（如果是单个时辰）

    def contains_hour(self, hour: int) -> bool:
        """检查某小时是否在此范围内"""
        if self.start_hour <= self.end_hour:
            return self.start_hour <= hour <= self.end_hour
        else:
            # 跨午夜的情况（如子时：23-1）
            return hour >= self.start_hour or hour <= self.end_hour

    def get_candidate_hours(self) -> List[int]:
        """获取该范围内的所有候选小时"""
        if self.start_hour <= self.end_hour:
            return list(range(self.start_hour, self.end_hour + 1))
        else:
            # 跨午夜
            return list(range(self.start_hour, 24)) + list(range(0, self.end_hour + 1))


@dataclass
class ShichenInfo:
    """时辰信息"""
    status: ShichenStatus
    hour: Optional[int] = None           # 精确小时（0-23）
    minute: Optional[int] = None         # 分钟（0-59）
    range: Optional[ShichenRange] = None  # 范围
    candidates: List[int] = field(default_factory=list)  # 候选时辰列表
    confidence: float = 0.0              # 置信度
    source: str = ""                     # 来源说明

    @property
    def dizhi(self) -> Optional[str]:
        """获取地支"""
        if self.hour is not None:
            return HOUR_TO_DIZHI.get(self.hour)
        return None

    @property
    def shichen_name(self) -> Optional[str]:
        """获取时辰名称"""
        dizhi = self.dizhi
        if dizhi:
            return DIZHI_TO_SHICHEN.get(dizhi)
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "hour": self.hour,
            "minute": self.minute,
            "range": {
                "start": self.range.start_hour,
                "end": self.range.end_hour,
                "name": self.range.name
            } if self.range else None,
            "candidates": self.candidates,
            "confidence": self.confidence,
            "source": self.source,
            "dizhi": self.dizhi,
            "shichen_name": self.shichen_name
        }


# 标准时辰映射（小时 -> 地支）
HOUR_TO_DIZHI = {
    23: "子", 0: "子",
    1: "丑", 2: "丑",
    3: "寅", 4: "寅",
    5: "卯", 6: "卯",
    7: "辰", 8: "辰",
    9: "巳", 10: "巳",
    11: "午", 12: "午",
    13: "未", 14: "未",
    15: "申", 16: "申",
    17: "酉", 18: "酉",
    19: "戌", 20: "戌",
    21: "亥", 22: "亥"
}

# 地支 -> 时辰名称
DIZHI_TO_SHICHEN = {
    "子": "子时", "丑": "丑时", "寅": "寅时", "卯": "卯时",
    "辰": "辰时", "巳": "巳时", "午": "午时", "未": "未时",
    "申": "申时", "酉": "酉时", "戌": "戌时", "亥": "亥时"
}

# 时辰范围定义（标准十二时辰）
SHICHEN_RANGES = {
    "子": ShichenRange(23, 1, "子时", "子"),
    "丑": ShichenRange(1, 3, "丑时", "丑"),
    "寅": ShichenRange(3, 5, "寅时", "寅"),
    "卯": ShichenRange(5, 7, "卯时", "卯"),
    "辰": ShichenRange(7, 9, "辰时", "辰"),
    "巳": ShichenRange(9, 11, "巳时", "巳"),
    "午": ShichenRange(11, 13, "午时", "午"),
    "未": ShichenRange(13, 15, "未时", "未"),
    "申": ShichenRange(15, 17, "申时", "申"),
    "酉": ShichenRange(17, 19, "酉时", "酉"),
    "戌": ShichenRange(19, 21, "戌时", "戌"),
    "亥": ShichenRange(21, 23, "亥时", "亥"),
}

# 常用时段映射
TIME_PERIOD_RANGES = {
    "凌晨": ShichenRange(0, 5, "凌晨"),
    "早上": ShichenRange(5, 9, "早上"),
    "上午": ShichenRange(9, 12, "上午"),
    "中午": ShichenRange(11, 13, "中午"),
    "下午": ShichenRange(13, 18, "下午"),
    "傍晚": ShichenRange(17, 19, "傍晚"),
    "晚上": ShichenRange(19, 23, "晚上"),
    "深夜": ShichenRange(23, 2, "深夜"),
    "半夜": ShichenRange(23, 3, "半夜"),
}

# 五鼠遁日诀：根据日干推算时干
# 甲己日起甲子，乙庚日起丙子，丙辛日起戊子，丁壬日起庚子，戊癸日起壬子
HOUR_GAN_BASE = {
    "甲": 0, "己": 0,  # 从甲开始
    "乙": 2, "庚": 2,  # 从丙开始
    "丙": 4, "辛": 4,  # 从戊开始
    "丁": 6, "壬": 6,  # 从庚开始
    "戊": 8, "癸": 8,  # 从壬开始
}

TIANGAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
DIZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]


class ShichenHandler:
    """时辰智能处理器"""

    def __init__(self, default_longitude: float = 120.0):
        """
        初始化时辰处理器

        Args:
            default_longitude: 默认经度（东经，用于真太阳时计算）
                              中国标准时间基于东经120度
        """
        self.logger = get_logger(__name__)
        self.default_longitude = default_longitude

    def parse_time_input(
        self,
        hour: Optional[int] = None,
        minute: Optional[int] = None,
        time_text: Optional[str] = None,
        certainty: str = "unknown"
    ) -> ShichenInfo:
        """
        解析时间输入，返回时辰信息

        Args:
            hour: 小时（0-23）
            minute: 分钟（0-59）
            time_text: 时间文本描述（如"上午"、"凌晨3点左右"）
            certainty: 确定性 ("certain"/"uncertain"/"unknown")

        Returns:
            ShichenInfo对象
        """
        self.logger.debug(f"解析时间输入: hour={hour}, minute={minute}, text={time_text}, certainty={certainty}")

        # 情况1：有精确时间
        if hour is not None and certainty == "certain":
            return ShichenInfo(
                status=ShichenStatus.CERTAIN,
                hour=hour,
                minute=minute or 0,
                confidence=1.0,
                source="用户精确输入"
            )

        # 情况2：有时间但不确定
        if hour is not None and certainty == "uncertain":
            # 生成候选时辰（当前时辰±1个时辰）
            dizhi = HOUR_TO_DIZHI.get(hour)
            candidates = self._get_adjacent_hours(hour)
            return ShichenInfo(
                status=ShichenStatus.UNCERTAIN,
                hour=hour,
                minute=minute,
                candidates=candidates,
                confidence=0.6,
                source="用户输入（不确定）"
            )

        # 情况3：有文本描述
        if time_text:
            return self._parse_time_text(time_text)

        # 情况4：完全未知
        return ShichenInfo(
            status=ShichenStatus.UNKNOWN,
            candidates=list(range(24)),  # 所有小时都是候选
            confidence=0.0,
            source="未提供时间信息"
        )

    def _parse_time_text(self, text: str) -> ShichenInfo:
        """解析时间文本描述"""
        text = text.strip()

        # 尝试匹配时段名称
        for period_name, range_info in TIME_PERIOD_RANGES.items():
            if period_name in text:
                candidates = range_info.get_candidate_hours()
                return ShichenInfo(
                    status=ShichenStatus.KNOWN_RANGE,
                    range=range_info,
                    candidates=candidates,
                    confidence=0.5,
                    source=f"时段描述：{period_name}"
                )

        # 尝试匹配时辰名称
        for dizhi, range_info in SHICHEN_RANGES.items():
            shichen_name = DIZHI_TO_SHICHEN[dizhi]
            if dizhi in text or shichen_name in text:
                # 取时辰中间小时作为主要候选
                mid_hour = (range_info.start_hour + range_info.end_hour) // 2
                if range_info.start_hour > range_info.end_hour:  # 跨午夜
                    mid_hour = 0 if dizhi == "子" else (range_info.start_hour + range_info.end_hour + 24) // 2 % 24
                candidates = range_info.get_candidate_hours()
                return ShichenInfo(
                    status=ShichenStatus.KNOWN_RANGE,
                    hour=mid_hour,
                    range=range_info,
                    candidates=candidates,
                    confidence=0.7,
                    source=f"时辰名称：{shichen_name}"
                )

        # 尝试解析数字时间
        import re

        # 匹配"X点"、"X时"、"X:XX"等
        hour_patterns = [
            r'(\d{1,2})[:：](\d{2})',     # 15:30
            r'(\d{1,2})[点时](\d{1,2})?',  # 3点 / 3点30
            r'(\d{1,2})点钟',              # 3点钟
        ]

        for pattern in hour_patterns:
            match = re.search(pattern, text)
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2)) if match.group(2) else 0
                if 0 <= hour <= 23:
                    # 检查是否有"左右"、"大约"等不确定词
                    uncertain = any(w in text for w in ["左右", "大约", "大概", "差不多", "好像"])
                    if uncertain:
                        return ShichenInfo(
                            status=ShichenStatus.UNCERTAIN,
                            hour=hour,
                            minute=minute,
                            candidates=self._get_adjacent_hours(hour),
                            confidence=0.6,
                            source="文本解析（不确定）"
                        )
                    else:
                        return ShichenInfo(
                            status=ShichenStatus.CERTAIN,
                            hour=hour,
                            minute=minute,
                            confidence=0.9,
                            source="文本解析"
                        )

        # 无法解析
        return ShichenInfo(
            status=ShichenStatus.UNKNOWN,
            candidates=list(range(24)),
            confidence=0.0,
            source=f"无法解析：{text}"
        )

    def _get_adjacent_hours(self, hour: int) -> List[int]:
        """获取相邻的候选小时（当前时辰及相邻时辰）"""
        candidates = set()

        # 当前时辰的所有小时
        dizhi = HOUR_TO_DIZHI.get(hour)
        if dizhi and dizhi in SHICHEN_RANGES:
            candidates.update(SHICHEN_RANGES[dizhi].get_candidate_hours())

        # 相邻时辰（前后各一个）
        dizhi_index = DIZHI.index(dizhi) if dizhi else 0
        prev_dizhi = DIZHI[(dizhi_index - 1) % 12]
        next_dizhi = DIZHI[(dizhi_index + 1) % 12]

        for adj_dizhi in [prev_dizhi, next_dizhi]:
            if adj_dizhi in SHICHEN_RANGES:
                # 只添加边界小时
                range_info = SHICHEN_RANGES[adj_dizhi]
                candidates.add(range_info.start_hour)
                candidates.add(range_info.end_hour)

        return sorted(list(candidates))

    def calculate_hour_ganzhi(
        self,
        day_gan: str,
        hour: int,
        use_true_solar: bool = False,
        local_time: Optional[datetime] = None,
        longitude: Optional[float] = None
    ) -> Tuple[str, str]:
        """
        计算时柱干支

        Args:
            day_gan: 日干
            hour: 小时（0-23，标准时或真太阳时）
            use_true_solar: 是否使用真太阳时
            local_time: 本地时间（用于真太阳时计算）
            longitude: 经度（用于真太阳时计算）

        Returns:
            (时干, 时支)
        """
        # 如果需要转换真太阳时
        if use_true_solar and local_time is not None:
            hour = self.convert_to_true_solar_hour(
                local_time,
                longitude or self.default_longitude
            )

        # 获取时支
        dizhi = HOUR_TO_DIZHI.get(hour, "子")
        zhi_index = DIZHI.index(dizhi)

        # 根据日干计算时干
        base = HOUR_GAN_BASE.get(day_gan, 0)
        gan_index = (base + zhi_index) % 10
        tiangan = TIANGAN[gan_index]

        return (tiangan, dizhi)

    def convert_to_true_solar_hour(
        self,
        local_time: datetime,
        longitude: float
    ) -> int:
        """
        将标准时转换为真太阳时的小时

        Args:
            local_time: 本地标准时间
            longitude: 当地经度（东经为正）

        Returns:
            真太阳时的小时（0-23）
        """
        # 计算时差修正（以北京时间东经120度为基准）
        time_diff_minutes = (longitude - 120.0) * 4  # 经度差1度 = 4分钟

        # 计算时间方程修正（真太阳时 vs 平太阳时）
        eot = self._calculate_equation_of_time(local_time)

        # 总修正
        total_correction_minutes = time_diff_minutes + eot

        # 计算真太阳时
        true_solar_time = local_time + timedelta(minutes=total_correction_minutes)

        self.logger.debug(
            f"真太阳时转换: {local_time} -> {true_solar_time} "
            f"(经度修正{time_diff_minutes:.1f}分, 时差方程{eot:.1f}分)"
        )

        return true_solar_time.hour

    def _calculate_equation_of_time(self, date: datetime) -> float:
        """
        计算时间方程（equation of time）

        Args:
            date: 日期

        Returns:
            修正分钟数
        """
        # 计算一年中的天数
        day_of_year = date.timetuple().tm_yday

        # 使用简化的时差方程公式
        # B = 360/365 * (day - 81)
        B = math.radians(360 / 365 * (day_of_year - 81))

        # 时差方程 (分钟)
        # EoT = 9.87*sin(2B) - 7.53*cos(B) - 1.5*sin(B)
        eot = 9.87 * math.sin(2 * B) - 7.53 * math.cos(B) - 1.5 * math.sin(B)

        return eot

    def get_three_pillar_mode_info(self) -> Dict[str, Any]:
        """
        获取三柱模式信息（无时辰时使用）

        Returns:
            三柱模式说明
        """
        return {
            "mode": "three_pillar",
            "description": "因无法确定出生时辰，使用年柱、月柱、日柱进行分析",
            "limitations": [
                "无法计算时柱，部分分析精度降低",
                "紫微斗数命宫计算可能不准确",
                "八字分析缺少时柱信息",
                "奇门遁甲需要使用时间范围模式"
            ],
            "alternative_theories": [
                "梅花易数（不依赖时辰）",
                "小六壬（使用当前时间）",
                "测字术（不依赖时辰）"
            ],
            "suggestions": [
                "询问家人确认出生时间",
                "查看出生证明或户口本",
                "通过重大事件反推时辰"
            ]
        }

    def generate_candidate_analyses(
        self,
        shichen_info: ShichenInfo,
        max_candidates: int = 3
    ) -> List[Dict[str, Any]]:
        """
        生成候选时辰分析列表

        Args:
            shichen_info: 时辰信息
            max_candidates: 最大候选数量

        Returns:
            候选分析列表，每个包含时辰信息和权重
        """
        candidates = []

        if shichen_info.status == ShichenStatus.CERTAIN:
            # 确定时辰，只有一个候选
            candidates.append({
                "hour": shichen_info.hour,
                "dizhi": shichen_info.dizhi,
                "weight": 1.0,
                "note": "精确时辰"
            })

        elif shichen_info.status == ShichenStatus.KNOWN_RANGE:
            # 已知范围，按时辰分组
            range_hours = shichen_info.candidates
            dizhi_groups = {}

            for hour in range_hours:
                dizhi = HOUR_TO_DIZHI.get(hour)
                if dizhi not in dizhi_groups:
                    dizhi_groups[dizhi] = []
                dizhi_groups[dizhi].append(hour)

            # 为每个时辰创建候选
            total = len(dizhi_groups)
            for dizhi, hours in dizhi_groups.items():
                mid_hour = sum(hours) // len(hours)
                candidates.append({
                    "hour": mid_hour,
                    "dizhi": dizhi,
                    "weight": 1.0 / total,
                    "note": f"范围内候选：{DIZHI_TO_SHICHEN.get(dizhi, dizhi)}"
                })

        elif shichen_info.status == ShichenStatus.UNCERTAIN:
            # 不确定，以主要时辰为中心
            main_dizhi = HOUR_TO_DIZHI.get(shichen_info.hour)
            adjacent = self._get_adjacent_hours(shichen_info.hour)

            # 主要时辰权重最高
            candidates.append({
                "hour": shichen_info.hour,
                "dizhi": main_dizhi,
                "weight": 0.6,
                "note": "主要候选"
            })

            # 相邻时辰
            seen_dizhi = {main_dizhi}
            for hour in adjacent:
                dizhi = HOUR_TO_DIZHI.get(hour)
                if dizhi not in seen_dizhi:
                    seen_dizhi.add(dizhi)
                    candidates.append({
                        "hour": hour,
                        "dizhi": dizhi,
                        "weight": 0.2,
                        "note": "相邻时辰候选"
                    })
                    if len(candidates) >= max_candidates:
                        break

        else:
            # 完全未知，返回所有十二时辰
            for dizhi in DIZHI:
                range_info = SHICHEN_RANGES.get(dizhi)
                if range_info:
                    mid = (range_info.start_hour + range_info.end_hour) // 2
                    if range_info.start_hour > range_info.end_hour:
                        mid = 0
                    candidates.append({
                        "hour": mid,
                        "dizhi": dizhi,
                        "weight": 1.0 / 12,
                        "note": f"全部候选：{DIZHI_TO_SHICHEN.get(dizhi)}"
                    })

        # 限制候选数量
        candidates = sorted(candidates, key=lambda x: x["weight"], reverse=True)[:max_candidates]

        # 重新归一化权重
        total_weight = sum(c["weight"] for c in candidates)
        if total_weight > 0:
            for c in candidates:
                c["weight"] /= total_weight

        return candidates

    def narrow_by_event(
        self,
        shichen_info: ShichenInfo,
        event_description: str,
        event_year: Optional[int] = None,
        birth_info: Optional[Dict[str, Any]] = None
    ) -> ShichenInfo:
        """
        根据历史事件缩小时辰范围（同步方法，使用代码规则）

        Args:
            shichen_info: 当前时辰信息
            event_description: 事件描述
            event_year: 事件发生年份
            birth_info: 出生信息字典

        Returns:
            更新后的时辰信息
        """
        self.logger.info(f"事件验证推断: {event_description}")

        # 代码规则推断（基于事件类型的简单启发式规则）
        event_lower = event_description.lower()

        # 事件类型启发式规则
        event_hints = {
            # 早起型人的事件暗示
            "早起": [5, 6, 7, 8],
            "晨跑": [5, 6, 7],
            "早操": [6, 7],
            # 夜猫子型暗示
            "熬夜": [21, 22, 23, 0, 1],
            "夜班": [21, 22, 23, 0],
            "通宵": [23, 0, 1, 2, 3],
            # 工作相关
            "早会": [8, 9],
            "加班": [18, 19, 20, 21],
        }

        candidates = shichen_info.candidates or list(range(24))

        for hint, hours in event_hints.items():
            if hint in event_lower:
                new_candidates = [h for h in candidates if h in hours]
                if new_candidates:
                    candidates = new_candidates
                    break

        # 如果范围缩小了，更新shichen_info
        if len(candidates) < len(shichen_info.candidates or list(range(24))):
            shichen_info.candidates = candidates
            shichen_info.source = f"基于事件推断: {event_description[:20]}"

            if len(candidates) <= 2:
                shichen_info.status = ShichenStatus.UNCERTAIN
                shichen_info.hour = candidates[0]
                shichen_info.confidence = 0.6

        return shichen_info

    async def narrow_by_event_with_ai(
        self,
        shichen_info: ShichenInfo,
        event_description: str,
        event_year: Optional[int] = None,
        birth_info: Optional[Dict[str, Any]] = None,
        nlp_parser: Optional[Any] = None
    ) -> ShichenInfo:
        """
        根据历史事件缩小时辰范围（AI增强版）

        Args:
            shichen_info: 当前时辰信息
            event_description: 事件描述
            event_year: 事件发生年份
            birth_info: 出生信息字典
            nlp_parser: NLP解析器实例（用于AI调用）

        Returns:
            更新后的时辰信息
        """
        self.logger.info(f"AI增强事件验证推断: {event_description}")

        # 如果没有NLP解析器，使用代码规则
        if not nlp_parser:
            return self.narrow_by_event(shichen_info, event_description, event_year, birth_info)

        # 准备出生信息
        if not birth_info:
            birth_info = {
                "hour": shichen_info.hour,
                "candidate_hours": shichen_info.candidates or list(range(24))
            }
        else:
            birth_info["candidate_hours"] = shichen_info.candidates or list(range(24))

        try:
            # 调用NLP解析器的AI方法
            ai_result = await nlp_parser.infer_hour_from_event_with_ai(
                birth_info=birth_info,
                event_description=event_description,
                event_year=event_year
            )

            # 更新候选时辰
            if ai_result.get("updated_candidates"):
                shichen_info.candidates = ai_result["updated_candidates"]

            # 如果AI有较高置信度的推断
            if ai_result.get("confidence") in ["高", "中"] and ai_result.get("most_likely_hour") is not None:
                shichen_info.hour = ai_result["most_likely_hour"]
                shichen_info.status = ShichenStatus.UNCERTAIN
                shichen_info.confidence = 0.7 if ai_result["confidence"] == "高" else 0.55

            shichen_info.source = f"AI事件推断: {event_description[:20]}"

            self.logger.info(f"AI事件推断结果: candidates={shichen_info.candidates}, hour={shichen_info.hour}")

        except Exception as e:
            self.logger.warning(f"AI事件推断失败，回退到代码规则: {e}")
            return self.narrow_by_event(shichen_info, event_description, event_year, birth_info)

        return shichen_info

    def format_time_display(self, shichen_info: ShichenInfo) -> str:
        """
        格式化时辰显示

        Args:
            shichen_info: 时辰信息

        Returns:
            格式化的显示文本
        """
        if shichen_info.status == ShichenStatus.CERTAIN:
            hour = shichen_info.hour
            minute = shichen_info.minute or 0
            dizhi = shichen_info.dizhi
            return f"{hour:02d}:{minute:02d} ({dizhi}时)"

        elif shichen_info.status == ShichenStatus.KNOWN_RANGE:
            if shichen_info.range:
                return f"{shichen_info.range.name} ({len(shichen_info.candidates)}个候选时辰)"
            return f"时间范围：{len(shichen_info.candidates)}个候选"

        elif shichen_info.status == ShichenStatus.UNCERTAIN:
            dizhi = shichen_info.dizhi or "未知"
            return f"约{dizhi}时 (不确定)"

        else:
            return "时辰未知"


# 便捷函数
def get_shichen_handler(longitude: float = 120.0) -> ShichenHandler:
    """获取时辰处理器实例"""
    return ShichenHandler(default_longitude=longitude)


def parse_birth_time(
    hour: Optional[int] = None,
    minute: Optional[int] = None,
    time_text: Optional[str] = None,
    certainty: str = "unknown"
) -> ShichenInfo:
    """便捷函数：解析出生时间"""
    handler = ShichenHandler()
    return handler.parse_time_input(hour, minute, time_text, certainty)


def hour_to_ganzhi(day_gan: str, hour: int) -> Tuple[str, str]:
    """便捷函数：计算时柱干支"""
    handler = ShichenHandler()
    return handler.calculate_hour_ganzhi(day_gan, hour)
