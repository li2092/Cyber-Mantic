"""
个人信息档案管理器
用于保存和加载常用的出生信息（最多3个）
"""
import sqlite3
import json
from typing import List, Optional, Dict, Any
from pathlib import Path
from models import PersonBirthInfo
from utils.logger import get_logger


class ProfileManager:
    """个人信息档案管理器"""

    MAX_PROFILES = 3  # 最多保存3个档案

    def __init__(self, db_path: Optional[str] = None):
        """
        初始化档案管理器

        Args:
            db_path: 数据库路径，默认使用 ~/.cyber_mantic/profiles.db
        """
        self.logger = get_logger(__name__)

        if db_path is None:
            app_dir = Path.home() / ".cyber_mantic"
            app_dir.mkdir(exist_ok=True)
            db_path = str(app_dir / "profiles.db")

        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT NOT NULL UNIQUE,
                birth_year INTEGER,
                birth_month INTEGER,
                birth_day INTEGER,
                birth_hour INTEGER,
                birth_minute INTEGER,
                calendar_type TEXT,
                birth_time_certainty TEXT,
                gender TEXT,
                birth_place_lng REAL,
                mbti_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()
        self.logger.info(f"档案数据库初始化完成: {self.db_path}")

    def save_profile(self, profile: PersonBirthInfo) -> bool:
        """
        保存档案

        Args:
            profile: 个人信息对象

        Returns:
            是否保存成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 检查是否已存在同名档案
            cursor.execute("SELECT id FROM profiles WHERE label = ?", (profile.label,))
            existing = cursor.fetchone()

            if existing:
                # 更新现有档案
                cursor.execute("""
                    UPDATE profiles SET
                        birth_year = ?,
                        birth_month = ?,
                        birth_day = ?,
                        birth_hour = ?,
                        birth_minute = ?,
                        calendar_type = ?,
                        birth_time_certainty = ?,
                        gender = ?,
                        birth_place_lng = ?,
                        mbti_type = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE label = ?
                """, (
                    profile.birth_year,
                    profile.birth_month,
                    profile.birth_day,
                    profile.birth_hour,
                    profile.birth_minute,
                    profile.calendar_type,
                    profile.birth_time_certainty,
                    profile.gender,
                    profile.birth_place_lng,
                    profile.mbti_type,
                    profile.label
                ))
                self.logger.info(f"更新档案: {profile.label}")
            else:
                # 检查档案数量限制
                cursor.execute("SELECT COUNT(*) FROM profiles")
                count = cursor.fetchone()[0]

                if count >= self.MAX_PROFILES:
                    self.logger.warning(f"档案数量已达上限({self.MAX_PROFILES})，无法保存新档案")
                    conn.close()
                    return False

                # 插入新档案
                cursor.execute("""
                    INSERT INTO profiles (
                        label, birth_year, birth_month, birth_day,
                        birth_hour, birth_minute, calendar_type,
                        birth_time_certainty, gender, birth_place_lng, mbti_type
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    profile.label,
                    profile.birth_year,
                    profile.birth_month,
                    profile.birth_day,
                    profile.birth_hour,
                    profile.birth_minute,
                    profile.calendar_type,
                    profile.birth_time_certainty,
                    profile.gender,
                    profile.birth_place_lng,
                    profile.mbti_type
                ))
                self.logger.info(f"保存新档案: {profile.label}")

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            self.logger.error(f"保存档案失败: {e}")
            return False

    def load_profile(self, label: str) -> Optional[PersonBirthInfo]:
        """
        加载档案

        Args:
            label: 档案标签

        Returns:
            个人信息对象，如果不存在则返回None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT label, birth_year, birth_month, birth_day,
                       birth_hour, birth_minute, calendar_type,
                       birth_time_certainty, gender, birth_place_lng, mbti_type
                FROM profiles
                WHERE label = ?
            """, (label,))

            row = cursor.fetchone()
            conn.close()

            if row:
                profile = PersonBirthInfo(
                    label=row[0],
                    birth_year=row[1],
                    birth_month=row[2],
                    birth_day=row[3],
                    birth_hour=row[4],
                    birth_minute=row[5],
                    calendar_type=row[6] or "solar",
                    birth_time_certainty=row[7] or "certain",
                    gender=row[8],
                    birth_place_lng=row[9],
                    mbti_type=row[10]
                )
                self.logger.info(f"加载档案: {label}")
                return profile
            else:
                self.logger.warning(f"档案不存在: {label}")
                return None

        except Exception as e:
            self.logger.error(f"加载档案失败: {e}")
            return None

    def delete_profile(self, label: str) -> bool:
        """
        删除档案

        Args:
            label: 档案标签

        Returns:
            是否删除成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("DELETE FROM profiles WHERE label = ?", (label,))
            deleted_count = cursor.rowcount

            conn.commit()
            conn.close()

            if deleted_count > 0:
                self.logger.info(f"删除档案: {label}")
                return True
            else:
                self.logger.warning(f"档案不存在: {label}")
                return False

        except Exception as e:
            self.logger.error(f"删除档案失败: {e}")
            return False

    def list_profiles(self) -> List[Dict[str, Any]]:
        """
        列出所有档案

        Returns:
            档案列表，每个元素包含 label 和创建/更新时间
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT label, created_at, updated_at
                FROM profiles
                ORDER BY updated_at DESC
            """)

            rows = cursor.fetchall()
            conn.close()

            profiles = [
                {
                    'label': row[0],
                    'created_at': row[1],
                    'updated_at': row[2]
                }
                for row in rows
            ]

            return profiles

        except Exception as e:
            self.logger.error(f"列出档案失败: {e}")
            return []

    def get_profile_count(self) -> int:
        """获取当前档案数量"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM profiles")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            self.logger.error(f"获取档案数量失败: {e}")
            return 0

    def can_add_profile(self) -> bool:
        """检查是否可以添加新档案"""
        return self.get_profile_count() < self.MAX_PROFILES


# 全局单例
_profile_manager = None


def get_profile_manager() -> ProfileManager:
    """获取档案管理器单例"""
    global _profile_manager
    if _profile_manager is None:
        _profile_manager = ProfileManager()
    return _profile_manager
