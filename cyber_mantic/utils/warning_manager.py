"""
预警管理器
用于检测异常使用模式并提供关怀响应

功能：
- 异常模式检测（密集分析、深夜使用、情绪化关键词）
- 3级预警响应（关怀提示、暂停建议、强制冷却）
- 锁定状态管理

核心理念：预警是关怀而非惩罚

设计参考：docs/design/03_洞察模块设计.md
"""
import json
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
from enum import Enum
from utils.logger import get_logger


class WarningLevel(Enum):
    """预警级别"""
    NONE = "none"
    CARE = "care"           # 关怀提示 - 温和提示，不阻止使用
    PAUSE = "pause"         # 暂停建议 - 弹窗选择：继续/休息60分钟
    FORCED = "forced"       # 强制冷却 - 锁定24h + 危机指引


# 情绪化关键词
EMOTIONAL_KEYWORDS = {
    "high": ["不想活", "活着没意思", "结束一切", "自杀", "自残", "去死"],
    "medium": ["绝望", "崩溃", "受不了了", "没有出路", "活不下去"],
    "low": ["焦虑", "失眠", "压力大", "烦躁", "难过", "痛苦"]
}

# 危机热线
CRISIS_HOTLINES = [
    ("全国心理援助热线", "400-161-9995"),
    ("北京心理危机研究与干预中心", "010-82951332"),
    ("生命热线", "400-821-1215"),
    ("青少年心理热线", "12355"),
]


class WarningManager:
    """预警管理器"""

    def __init__(self, db_path: Optional[str] = None):
        """
        初始化预警管理器

        Args:
            db_path: 配置目录路径
        """
        self.logger = get_logger(__name__)

        if db_path is None:
            self._config_dir = Path.home() / ".cyber_mantic"
        else:
            self._config_dir = Path(db_path)

        self._config_dir.mkdir(exist_ok=True)
        self._lock_file = self._config_dir / "lock_status.json"

    # ==================== 模式检测 ====================

    def check_text_for_keywords(self, text: str) -> Tuple[WarningLevel, List[str]]:
        """
        检查文本中的情绪化关键词

        Args:
            text: 要检查的文本

        Returns:
            (预警级别, 匹配到的关键词列表)
        """
        text_lower = text.lower()
        matched_keywords = []

        # 检查高危关键词
        for keyword in EMOTIONAL_KEYWORDS["high"]:
            if keyword in text_lower:
                matched_keywords.append(keyword)

        if matched_keywords:
            return WarningLevel.FORCED, matched_keywords

        # 检查中危关键词
        for keyword in EMOTIONAL_KEYWORDS["medium"]:
            if keyword in text_lower:
                matched_keywords.append(keyword)

        if matched_keywords:
            return WarningLevel.PAUSE, matched_keywords

        # 检查低危关键词
        for keyword in EMOTIONAL_KEYWORDS["low"]:
            if keyword in text_lower:
                matched_keywords.append(keyword)

        if matched_keywords:
            return WarningLevel.CARE, matched_keywords

        return WarningLevel.NONE, []

    def check_usage_pattern(
        self,
        recent_usage: List[Dict[str, Any]],
        current_time: Optional[datetime] = None
    ) -> Tuple[WarningLevel, str]:
        """
        检查使用模式异常

        Args:
            recent_usage: 最近的使用记录列表，每条包含 {created_at, module, question_type}
            current_time: 当前时间（用于测试）

        Returns:
            (预警级别, 异常描述)
        """
        if current_time is None:
            current_time = datetime.now()

        # 1. 检查密集分析（6小时内分析>5次，同一问题类型）
        six_hours_ago = current_time - timedelta(hours=6)
        recent_six_hours = [
            u for u in recent_usage
            if self._parse_timestamp(u.get('created_at')) >= six_hours_ago
        ]

        if len(recent_six_hours) > 5:
            # 检查是否同一问题类型
            question_types = [u.get('question_type') for u in recent_six_hours if u.get('question_type')]
            if question_types:
                most_common = max(set(question_types), key=question_types.count)
                if question_types.count(most_common) > 5:
                    return WarningLevel.PAUSE, f"6小时内对「{most_common}」问题分析超过5次"

        # 2. 检查深夜使用（凌晨1-5点）
        if 1 <= current_time.hour < 5:
            # 检查最近7天凌晨使用频率
            seven_days_ago = current_time - timedelta(days=7)
            late_night_count = 0

            for usage in recent_usage:
                ts = self._parse_timestamp(usage.get('created_at'))
                if ts and ts >= seven_days_ago:
                    if 1 <= ts.hour < 5:
                        late_night_count += 1

            if late_night_count >= 3:
                return WarningLevel.CARE, "近7天凌晨使用超过3次"

        return WarningLevel.NONE, ""

    def _parse_timestamp(self, ts_str: Optional[str]) -> Optional[datetime]:
        """解析时间戳字符串"""
        if not ts_str:
            return None
        try:
            # 尝试多种格式
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d']:
                try:
                    return datetime.strptime(ts_str[:19], fmt)
                except ValueError:
                    continue
            return None
        except Exception:
            return None

    # ==================== 锁定状态管理 ====================

    def is_locked(self) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        检查是否处于锁定状态

        Returns:
            (是否锁定, 锁定信息)
        """
        if not self._lock_file.exists():
            return False, None

        try:
            lock_data = json.loads(self._lock_file.read_text())

            if not lock_data.get('is_locked'):
                return False, None

            # 检查是否已过期
            lock_until_str = lock_data.get('lock_until')
            if lock_until_str:
                lock_until = datetime.fromisoformat(lock_until_str)
                if datetime.now() >= lock_until:
                    self._clear_lock()
                    return False, None

            return True, lock_data

        except Exception as e:
            self.logger.error(f"读取锁定状态失败: {e}")
            return False, None

    def set_lock(
        self,
        reason: str,
        duration_hours: int = 24,
        trigger_keywords: Optional[List[str]] = None
    ) -> bool:
        """
        设置锁定

        Args:
            reason: 锁定原因
            duration_hours: 锁定时长（小时）
            trigger_keywords: 触发的关键词

        Returns:
            是否成功
        """
        try:
            lock_data = {
                "is_locked": True,
                "lock_until": (datetime.now() + timedelta(hours=duration_hours)).isoformat(),
                "lock_reason": reason,
                "trigger_keywords": trigger_keywords or [],
                "created_at": datetime.now().isoformat()
            }

            self._lock_file.write_text(json.dumps(lock_data, ensure_ascii=False, indent=2))
            self.logger.info(f"设置锁定: {reason}, 时长: {duration_hours}小时")
            return True

        except Exception as e:
            self.logger.error(f"设置锁定失败: {e}")
            return False

    def _clear_lock(self):
        """清除锁定"""
        try:
            if self._lock_file.exists():
                self._lock_file.unlink()
        except Exception as e:
            self.logger.error(f"清除锁定失败: {e}")

    def get_remaining_lock_time(self) -> Optional[str]:
        """
        获取剩余锁定时间

        Returns:
            格式化的剩余时间，如 "23:45:32"
        """
        is_locked, lock_data = self.is_locked()
        if not is_locked or not lock_data:
            return None

        lock_until_str = lock_data.get('lock_until')
        if not lock_until_str:
            return None

        try:
            lock_until = datetime.fromisoformat(lock_until_str)
            remaining = lock_until - datetime.now()

            if remaining.total_seconds() <= 0:
                return None

            hours, remainder = divmod(int(remaining.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        except Exception:
            return None

    def request_unlock(self, confirmation: str, self_assessment: Dict[str, Any]) -> bool:
        """
        请求解除锁定（"我只是随便说说"流程）

        Args:
            confirmation: 用户输入的确认文本（应为"我确认当前状态良好"）
            self_assessment: 用户自评信息

        Returns:
            是否解除成功
        """
        expected = "我确认当前状态良好"

        if confirmation.strip() != expected:
            self.logger.warning("解除锁定确认文本不匹配")
            return False

        # 检查自评答案
        if self_assessment.get('needs_help'):
            # 用户选择"我需要帮助"，不解除锁定
            self.logger.info("用户表示需要帮助，保持锁定")
            return False

        # 记录解除事件（可用于后续分析）
        self._log_unlock_request(self_assessment)

        # 解除锁定
        self._clear_lock()
        self.logger.info("用户确认状态良好，解除锁定")
        return True

    def _log_unlock_request(self, assessment: Dict[str, Any]):
        """记录解除请求（用于产品改进）"""
        try:
            from utils.usage_stats_manager import get_usage_stats_manager
            stats = get_usage_stats_manager()
            stats.record_risk_event(
                risk_level='unlock_request',
                trigger_pattern='user_request',
                user_response=json.dumps(assessment, ensure_ascii=False)
            )
        except Exception as e:
            self.logger.warning(f"记录解除请求失败: {e}")

    # ==================== 关怀消息 ====================

    def get_care_message(self, level: WarningLevel, context: str = "") -> str:
        """
        获取关怀消息

        Args:
            level: 预警级别
            context: 上下文信息

        Returns:
            关怀消息文本
        """
        if level == WarningLevel.CARE:
            messages = [
                "您今天使用时间较长，记得休息哦 💙",
                "深夜了，要不要先休息一下？💙",
                "看起来您在思考一些重要的事情，记得照顾好自己 💙"
            ]
            return messages[hash(context) % len(messages)]

        elif level == WarningLevel.PAUSE:
            return "您似乎比较焦虑，要不要喝杯茶休息一下？💙"

        elif level == WarningLevel.FORCED:
            return (
                "我们注意到您可能正在经历一些困难。\n\n"
                "请记住，无论发生什么，都有人在乎您。\n"
                "如果您需要倾诉，专业的心理援助热线随时为您服务。"
            )

        return ""

    def get_crisis_hotlines(self) -> List[Tuple[str, str]]:
        """获取危机热线列表"""
        return CRISIS_HOTLINES


# 全局单例
_warning_manager = None


def get_warning_manager() -> WarningManager:
    """获取预警管理器单例"""
    global _warning_manager
    if _warning_manager is None:
        _warning_manager = WarningManager()
    return _warning_manager
