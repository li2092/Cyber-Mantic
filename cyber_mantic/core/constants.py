"""
核心常量定义 - 提取魔法字符串为枚举类型

提供类型安全的常量定义，避免硬编码字符串
"""
from enum import Enum
from typing import Tuple


class JudgmentType(Enum):
    """
    吉凶判断类型枚举

    用于统一各理论的吉凶判断结果
    """
    DA_JI = ("大吉", 1.0, "极为吉利，事事顺遂")
    JI = ("吉", 0.75, "总体吉利，可以进行")
    XIAO_JI = ("小吉", 0.6, "略有吉象，谨慎行事")
    PING = ("平", 0.5, "吉凶参半，需要权衡")
    XIAO_XIONG = ("小凶", 0.4, "略有不利，多加注意")
    XIONG = ("凶", 0.25, "总体不利，建议规避")
    DA_XIONG = ("大凶", 0.0, "极为不利，务必谨慎")

    @property
    def text(self) -> str:
        """获取判断文本"""
        return self.value[0]

    @property
    def score(self) -> float:
        """获取判断分数 (0-1)"""
        return self.value[1]

    @property
    def description(self) -> str:
        """获取判断描述"""
        return self.value[2]

    @classmethod
    def from_score(cls, score: float) -> 'JudgmentType':
        """
        根据分数获取判断类型

        Args:
            score: 0-1之间的分数

        Returns:
            对应的判断类型
        """
        if score >= 0.9:
            return cls.DA_JI
        elif score >= 0.7:
            return cls.JI
        elif score >= 0.55:
            return cls.XIAO_JI
        elif score >= 0.45:
            return cls.PING
        elif score >= 0.3:
            return cls.XIAO_XIONG
        elif score >= 0.1:
            return cls.XIONG
        else:
            return cls.DA_XIONG

    @classmethod
    def from_text(cls, text: str) -> 'JudgmentType':
        """
        根据文本获取判断类型

        Args:
            text: 判断文本

        Returns:
            对应的判断类型，默认返回PING
        """
        text_map = {j.text: j for j in cls}
        return text_map.get(text, cls.PING)


class QuestionCategory(Enum):
    """
    问题类别枚举

    用于分类用户的咨询问题
    """
    CAREER = ("事业", "career", "职业发展、工作变动、升迁机会")
    WEALTH = ("财运", "wealth", "投资理财、收入变化、财务决策")
    LOVE = ("感情", "love", "恋爱关系、情感发展、桃花运势")
    MARRIAGE = ("婚姻", "marriage", "婚姻状况、配偶关系、家庭和谐")
    HEALTH = ("健康", "health", "身体状况、疾病预防、养生建议")
    STUDY = ("学业", "study", "学习进展、考试运势、学术发展")
    RELATIONSHIP = ("人际", "relationship", "社交关系、贵人运、人脉发展")
    TIMING = ("择时", "timing", "吉日选择、时机把握、出行择日")
    DECISION = ("决策", "decision", "重大决定、方向选择、策略分析")
    PERSONALITY = ("性格", "personality", "性格分析、优势劣势、自我认知")

    @property
    def chinese_name(self) -> str:
        """获取中文名称"""
        return self.value[0]

    @property
    def english_name(self) -> str:
        """获取英文名称"""
        return self.value[1]

    @property
    def description(self) -> str:
        """获取类别描述"""
        return self.value[2]

    @classmethod
    def from_chinese(cls, name: str) -> 'QuestionCategory':
        """根据中文名称获取类别"""
        name_map = {q.chinese_name: q for q in cls}
        return name_map.get(name, cls.DECISION)

    @classmethod
    def all_chinese_names(cls) -> Tuple[str, ...]:
        """获取所有中文名称"""
        return tuple(q.chinese_name for q in cls)


class TheoryType(Enum):
    """
    术数理论类型枚举

    定义系统支持的所有术数理论
    """
    BAZI = ("八字", "bazi", "命理类", "基于出生时间的命理分析")
    ZIWEI = ("紫微斗数", "ziwei", "命理类", "基于星曜排盘的命理分析")
    QIMEN = ("奇门遁甲", "qimen", "占卜类", "时空能量场的预测术")
    LIUYAO = ("六爻", "liuyao", "占卜类", "基于六爻卦象的占卜术")
    DALIUREN = ("大六壬", "daliuren", "占卜类", "古老的时间预测术")
    XIAOLIU = ("小六壬", "xiaoliu", "快速类", "简便快速的占卜法")
    MEIHUA = ("梅花易数", "meihua", "快速类", "心易感应的占卜术")
    CEZI = ("测字", "cezi", "快速类", "汉字拆解的占卜术")

    @property
    def chinese_name(self) -> str:
        """获取中文名称"""
        return self.value[0]

    @property
    def english_name(self) -> str:
        """获取英文标识"""
        return self.value[1]

    @property
    def category(self) -> str:
        """获取理论分类"""
        return self.value[2]

    @property
    def description(self) -> str:
        """获取理论描述"""
        return self.value[3]

    @classmethod
    def from_chinese(cls, name: str) -> 'TheoryType':
        """根据中文名称获取理论类型"""
        name_map = {t.chinese_name: t for t in cls}
        return name_map.get(name)

    @classmethod
    def get_by_category(cls, category: str) -> Tuple['TheoryType', ...]:
        """获取指定分类的所有理论"""
        return tuple(t for t in cls if t.category == category)


class ConflictLevel(Enum):
    """
    冲突等级枚举

    用于分类理论间的结论冲突程度
    """
    NONE = (0, "无冲突", 0.0, 0.2, "结论高度一致")
    MINOR = (1, "微小差异", 0.2, 0.4, "结论基本一致，细节略有不同")
    MODERATE = (2, "显著差异", 0.4, 0.5, "结论存在分歧，需要权衡")
    MAJOR = (3, "严重冲突", 0.5, 1.0, "结论相互矛盾，需要深度分析")

    @property
    def level(self) -> int:
        """获取冲突等级数值"""
        return self.value[0]

    @property
    def name_cn(self) -> str:
        """获取中文名称"""
        return self.value[1]

    @property
    def threshold_low(self) -> float:
        """获取下限阈值"""
        return self.value[2]

    @property
    def threshold_high(self) -> float:
        """获取上限阈值"""
        return self.value[3]

    @property
    def description(self) -> str:
        """获取描述"""
        return self.value[4]

    @classmethod
    def from_difference(cls, difference: float) -> 'ConflictLevel':
        """
        根据差异值获取冲突等级

        Args:
            difference: 0-1之间的差异值

        Returns:
            对应的冲突等级
        """
        for level in cls:
            if level.threshold_low <= difference < level.threshold_high:
                return level
        return cls.MAJOR


# 常用判断关键词（用于文本分析）
JUDGMENT_KEYWORDS = {
    "positive": ["吉", "利", "顺", "旺", "好", "宜", "佳", "喜", "福"],
    "negative": ["凶", "不利", "忌", "损", "害", "灾", "煞", "破", "败"],
    "neutral": ["平", "一般", "中等", "普通", "待定"]
}

# 时辰对照表
SHICHEN_MAP = {
    (23, 1): "子时",
    (1, 3): "丑时",
    (3, 5): "寅时",
    (5, 7): "卯时",
    (7, 9): "辰时",
    (9, 11): "巳时",
    (11, 13): "午时",
    (13, 15): "未时",
    (15, 17): "申时",
    (17, 19): "酉时",
    (19, 21): "戌时",
    (21, 23): "亥时",
}


def get_shichen(hour: int) -> str:
    """
    根据小时获取时辰名称

    Args:
        hour: 0-23之间的小时数

    Returns:
        时辰名称
    """
    for (start, end), name in SHICHEN_MAP.items():
        if start <= hour < end or (start == 23 and (hour >= 23 or hour < 1)):
            return name
    return "子时"  # 默认
