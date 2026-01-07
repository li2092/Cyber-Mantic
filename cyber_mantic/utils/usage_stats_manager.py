"""
使用统计管理器
用于收集和管理用户使用数据，支持洞察模块功能

功能：
- usage_stats: 记录每次问道/推演的使用情况
- session_tracking: 追踪会话开始与完成（计算完成率）
- behavior_log: 记录用户行为事件
- risk_events: 记录风险事件与用户响应
- library_reading: 记录典籍阅读情况

设计参考：docs/design/03_洞察模块设计.md
"""
import sqlite3
import json
import uuid
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
from collections import Counter
from utils.logger import get_logger


class UsageStatsManager:
    """使用统计管理器"""

    def __init__(self, db_path: Optional[str] = None):
        """
        初始化使用统计管理器

        Args:
            db_path: 数据库路径，默认使用 ~/.cyber_mantic/profile.db
        """
        self.logger = get_logger(__name__)

        if db_path is None:
            app_dir = Path.home() / ".cyber_mantic"
            app_dir.mkdir(exist_ok=True)
            db_path = str(app_dir / "profile.db")

        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 使用统计表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usage_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                module TEXT NOT NULL,
                theory TEXT,
                question_type TEXT,
                duration_seconds INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 行为日志表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS behavior_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                event_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 风险事件表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS risk_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                risk_level TEXT NOT NULL,
                trigger_pattern TEXT,
                user_response TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 会话追踪表 - 用于计算完成率
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS session_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                module TEXT NOT NULL,
                theory TEXT,
                question_type TEXT,
                stage TEXT,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                is_completed BOOLEAN DEFAULT 0
            )
        """)

        # 典籍阅读记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS library_reading (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_path TEXT NOT NULL,
                document_title TEXT,
                category TEXT,
                reading_seconds INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建索引以提高查询效率
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_usage_stats_date
            ON usage_stats(date)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_usage_stats_module
            ON usage_stats(module)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_behavior_log_created
            ON behavior_log(created_at)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_tracking_module
            ON session_tracking(module)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_tracking_started
            ON session_tracking(started_at)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_library_reading_created
            ON library_reading(created_at)
        """)

        conn.commit()
        conn.close()
        self.logger.info(f"使用统计数据库初始化完成: {self.db_path}")

    # ==================== 使用统计 ====================

    def record_usage(
        self,
        module: str,
        theory: Optional[str] = None,
        question_type: Optional[str] = None,
        duration_seconds: Optional[int] = None
    ) -> bool:
        """
        记录一次使用

        Args:
            module: 模块名称 ('wendao' | 'tuiyan')
            theory: 使用的术数理论
            question_type: 问题类型
            duration_seconds: 使用时长（秒）

        Returns:
            是否记录成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO usage_stats (date, module, theory, question_type, duration_seconds)
                VALUES (?, ?, ?, ?, ?)
            """, (
                date.today().isoformat(),
                module,
                theory,
                question_type,
                duration_seconds
            ))

            conn.commit()
            conn.close()
            self.logger.debug(f"记录使用: module={module}, theory={theory}")
            return True

        except Exception as e:
            self.logger.error(f"记录使用失败: {e}")
            return False

    # ==================== 会话追踪 ====================

    def start_session(
        self,
        module: str,
        theory: Optional[str] = None,
        question_type: Optional[str] = None,
        stage: Optional[str] = None
    ) -> str:
        """
        开始一个新会话（用户开始问道或推演时调用）

        Args:
            module: 模块名称 ('wendao' | 'tuiyan')
            theory: 使用的术数理论
            question_type: 问题类型
            stage: 当前阶段

        Returns:
            会话ID（用于后续标记完成）
        """
        session_id = str(uuid.uuid4())
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO session_tracking
                (session_id, module, theory, question_type, stage)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, module, theory, question_type, stage))

            conn.commit()
            conn.close()
            self.logger.debug(f"开始会话: session_id={session_id}, module={module}")
            return session_id

        except Exception as e:
            self.logger.error(f"开始会话失败: {e}")
            return session_id  # 即使失败也返回ID，避免下游错误

    def complete_session(
        self,
        session_id: str,
        theory: Optional[str] = None,
        question_type: Optional[str] = None
    ) -> bool:
        """
        标记会话完成

        Args:
            session_id: 会话ID
            theory: 最终使用的理论（可更新）
            question_type: 最终问题类型（可更新）

        Returns:
            是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 更新会话为已完成
            if theory or question_type:
                cursor.execute("""
                    UPDATE session_tracking
                    SET is_completed = 1,
                        completed_at = CURRENT_TIMESTAMP,
                        theory = COALESCE(?, theory),
                        question_type = COALESCE(?, question_type)
                    WHERE session_id = ?
                """, (theory, question_type, session_id))
            else:
                cursor.execute("""
                    UPDATE session_tracking
                    SET is_completed = 1, completed_at = CURRENT_TIMESTAMP
                    WHERE session_id = ?
                """, (session_id,))

            conn.commit()
            conn.close()
            self.logger.debug(f"完成会话: session_id={session_id}")
            return True

        except Exception as e:
            self.logger.error(f"完成会话失败: {e}")
            return False

    def update_session_stage(self, session_id: str, stage: str) -> bool:
        """
        更新会话阶段（用于追踪用户在哪个阶段流失）

        Args:
            session_id: 会话ID
            stage: 当前阶段

        Returns:
            是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE session_tracking SET stage = ? WHERE session_id = ?
            """, (stage, session_id))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            self.logger.error(f"更新会话阶段失败: {e}")
            return False

    def get_completion_rate(
        self,
        module: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        获取完成率统计

        Args:
            module: 模块名称（可选，不指定则返回所有）
            days: 统计天数

        Returns:
            完成率统计 {started, completed, rate, by_stage}
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            start_date = (datetime.now() - timedelta(days=days)).isoformat()

            # 基础查询条件
            where_clause = "WHERE started_at >= ?"
            params = [start_date]

            if module:
                where_clause += " AND module = ?"
                params.append(module)

            # 获取总开始数和完成数
            cursor.execute(f"""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN is_completed = 1 THEN 1 ELSE 0 END) as completed
                FROM session_tracking
                {where_clause}
            """, params)

            row = cursor.fetchone()
            total = row[0] or 0
            completed = row[1] or 0
            rate = (completed / total * 100) if total > 0 else 0

            # 获取各阶段流失情况（未完成的会话）
            cursor.execute(f"""
                SELECT stage, COUNT(*) as cnt
                FROM session_tracking
                {where_clause} AND is_completed = 0 AND stage IS NOT NULL
                GROUP BY stage
                ORDER BY cnt DESC
            """, params)

            stage_dropout = {row[0]: row[1] for row in cursor.fetchall()}

            conn.close()

            return {
                'started': total,
                'completed': completed,
                'abandoned': total - completed,
                'rate': round(rate, 1),
                'stage_dropout': stage_dropout
            }

        except Exception as e:
            self.logger.error(f"获取完成率失败: {e}")
            return {
                'started': 0,
                'completed': 0,
                'abandoned': 0,
                'rate': 0,
                'stage_dropout': {}
            }

    def get_completion_summary(self, days: int = 30) -> Dict[str, Dict[str, Any]]:
        """
        获取完成率摘要（包含问道和推演）

        Args:
            days: 统计天数

        Returns:
            {wendao: {...}, tuiyan: {...}, overall: {...}}
        """
        wendao_stats = self.get_completion_rate(module='wendao', days=days)
        tuiyan_stats = self.get_completion_rate(module='tuiyan', days=days)

        # 计算整体
        total_started = wendao_stats['started'] + tuiyan_stats['started']
        total_completed = wendao_stats['completed'] + tuiyan_stats['completed']
        overall_rate = (total_completed / total_started * 100) if total_started > 0 else 0

        return {
            'wendao': wendao_stats,
            'tuiyan': tuiyan_stats,
            'overall': {
                'started': total_started,
                'completed': total_completed,
                'abandoned': total_started - total_completed,
                'rate': round(overall_rate, 1)
            }
        }

    # ==================== 典籍阅读追踪 ====================

    def get_or_create_reading_session(
        self,
        document_path: str,
        document_title: Optional[str] = None,
        category: Optional[str] = None
    ) -> int:
        """
        获取或创建今天的阅读会话记录

        Args:
            document_path: 文档路径
            document_title: 文档标题
            category: 文档分类

        Returns:
            记录ID
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            today = date.today().isoformat()

            # 查找今天是否已有该文档的阅读记录
            cursor.execute("""
                SELECT id FROM library_reading
                WHERE document_path = ? AND DATE(created_at) = ?
                ORDER BY created_at DESC LIMIT 1
            """, (document_path, today))

            row = cursor.fetchone()

            if row:
                record_id = row[0]
            else:
                # 创建新记录
                cursor.execute("""
                    INSERT INTO library_reading (document_path, document_title, category, reading_seconds)
                    VALUES (?, ?, ?, 0)
                """, (document_path, document_title, category))
                record_id = cursor.lastrowid
                conn.commit()

            conn.close()
            return record_id

        except Exception as e:
            self.logger.error(f"获取或创建阅读会话失败: {e}")
            return -1

    def update_reading_time(self, record_id: int, additional_seconds: int) -> bool:
        """
        增量更新阅读时长

        Args:
            record_id: 记录ID
            additional_seconds: 增加的秒数

        Returns:
            是否更新成功
        """
        if record_id < 0 or additional_seconds <= 0:
            return False

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE library_reading
                SET reading_seconds = reading_seconds + ?
                WHERE id = ?
            """, (additional_seconds, record_id))

            conn.commit()
            conn.close()
            self.logger.debug(f"更新阅读时长: record_id={record_id}, +{additional_seconds}s")
            return True

        except Exception as e:
            self.logger.error(f"更新阅读时长失败: {e}")
            return False

    def record_reading(
        self,
        document_path: str,
        document_title: Optional[str] = None,
        category: Optional[str] = None,
        reading_seconds: int = 0
    ) -> bool:
        """
        记录一次典籍阅读

        Args:
            document_path: 文档路径
            document_title: 文档标题
            category: 文档分类（如：八字、紫微、六爻等）
            reading_seconds: 阅读时长（秒）

        Returns:
            是否记录成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO library_reading (document_path, document_title, category, reading_seconds)
                VALUES (?, ?, ?, ?)
            """, (document_path, document_title, category, reading_seconds))

            conn.commit()
            conn.close()
            self.logger.debug(f"记录阅读: {document_title or document_path}")
            return True

        except Exception as e:
            self.logger.error(f"记录阅读失败: {e}")
            return False

    def get_reading_stats(self, days: int = 30) -> Dict[str, Any]:
        """
        获取阅读统计

        Args:
            days: 统计天数

        Returns:
            阅读统计 {total_count, total_seconds, documents_read, category_distribution}
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            start_date = (datetime.now() - timedelta(days=days)).isoformat()

            # 总阅读次数和时长
            cursor.execute("""
                SELECT COUNT(*), COALESCE(SUM(reading_seconds), 0)
                FROM library_reading
                WHERE created_at >= ?
            """, (start_date,))
            row = cursor.fetchone()
            total_count = row[0] or 0
            total_seconds = row[1] or 0

            # 阅读的文档数（去重）
            cursor.execute("""
                SELECT COUNT(DISTINCT document_path)
                FROM library_reading
                WHERE created_at >= ?
            """, (start_date,))
            documents_read = cursor.fetchone()[0] or 0

            # 按分类统计
            cursor.execute("""
                SELECT category, COUNT(*) as cnt
                FROM library_reading
                WHERE created_at >= ? AND category IS NOT NULL
                GROUP BY category
                ORDER BY cnt DESC
            """, (start_date,))
            category_dist = {row[0]: row[1] for row in cursor.fetchall()}

            # 最常阅读的文档
            cursor.execute("""
                SELECT document_title, COUNT(*) as cnt
                FROM library_reading
                WHERE created_at >= ? AND document_title IS NOT NULL
                GROUP BY document_path
                ORDER BY cnt DESC
                LIMIT 5
            """, (start_date,))
            top_documents = [(row[0], row[1]) for row in cursor.fetchall()]

            conn.close()

            return {
                'total_count': total_count,
                'total_seconds': total_seconds,
                'total_minutes': round(total_seconds / 60, 1),
                'documents_read': documents_read,
                'category_distribution': category_dist,
                'top_documents': top_documents
            }

        except Exception as e:
            self.logger.error(f"获取阅读统计失败: {e}")
            return {
                'total_count': 0,
                'total_seconds': 0,
                'total_minutes': 0,
                'documents_read': 0,
                'category_distribution': {},
                'top_documents': []
            }

    def get_reading_preferences(self, days: int = 30) -> str:
        """
        获取阅读偏好描述

        Args:
            days: 统计天数

        Returns:
            阅读偏好描述
        """
        stats = self.get_reading_stats(days)

        if stats['total_count'] == 0:
            return "暂无阅读记录"

        # 构建描述
        parts = []

        # 阅读量
        if stats['documents_read'] > 0:
            parts.append(f"阅读{stats['documents_read']}篇文档")

        # 主要分类
        if stats['category_distribution']:
            top_category = max(stats['category_distribution'].items(), key=lambda x: x[1])
            parts.append(f"偏好{top_category[0]}")

        return "，".join(parts) if parts else "暂无阅读记录"

    def get_usage_count(
        self,
        module: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> int:
        """
        获取使用次数

        Args:
            module: 模块名称（可选）
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）

        Returns:
            使用次数
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            query = "SELECT COUNT(*) FROM usage_stats WHERE 1=1"
            params = []

            if module:
                query += " AND module = ?"
                params.append(module)
            if start_date:
                query += " AND date >= ?"
                params.append(start_date.isoformat())
            if end_date:
                query += " AND date <= ?"
                params.append(end_date.isoformat())

            cursor.execute(query, params)
            count = cursor.fetchone()[0]
            conn.close()
            return count

        except Exception as e:
            self.logger.error(f"获取使用次数失败: {e}")
            return 0

    def get_total_usage_count(self) -> Tuple[int, int]:
        """
        获取总使用次数

        Returns:
            (问道次数, 推演次数)
        """
        wendao = self.get_usage_count(module='wendao')
        tuiyan = self.get_usage_count(module='tuiyan')
        return wendao, tuiyan

    def get_weekly_usage_count(self) -> Tuple[int, int]:
        """
        获取本周使用次数

        Returns:
            (问道次数, 推演次数)
        """
        today = date.today()
        # 获取本周一
        week_start = today - timedelta(days=today.weekday())

        wendao = self.get_usage_count(module='wendao', start_date=week_start)
        tuiyan = self.get_usage_count(module='tuiyan', start_date=week_start)
        return wendao, tuiyan

    def get_usage_frequency(self, days: int = 30) -> str:
        """
        获取使用频率描述

        Args:
            days: 统计天数

        Returns:
            使用频率描述（周活跃/月活跃/偶尔使用/暂无数据）
        """
        try:
            start_date = date.today() - timedelta(days=days)
            count = self.get_usage_count(start_date=start_date)

            if count == 0:
                return "暂无数据"
            elif count >= 7:
                return "周活跃用户"
            elif count >= 3:
                return "月活跃用户"
            else:
                return "偶尔使用"

        except Exception as e:
            self.logger.error(f"获取使用频率失败: {e}")
            return "暂无数据"

    def get_preferred_time_slots(self, days: int = 30) -> str:
        """
        获取常用时段

        Args:
            days: 统计天数

        Returns:
            常用时段描述
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            start_date = (date.today() - timedelta(days=days)).isoformat()
            cursor.execute("""
                SELECT strftime('%H', created_at) as hour, COUNT(*) as cnt
                FROM usage_stats
                WHERE date >= ?
                GROUP BY hour
                ORDER BY cnt DESC
                LIMIT 3
            """, (start_date,))

            rows = cursor.fetchall()
            conn.close()

            if not rows:
                return "暂无数据"

            # 分析时段
            hours = [int(row[0]) for row in rows if row[0]]
            if not hours:
                return "暂无数据"

            # 判断主要时段
            avg_hour = sum(hours) / len(hours)
            if avg_hour >= 6 and avg_hour < 12:
                return "上午 06:00-12:00"
            elif avg_hour >= 12 and avg_hour < 18:
                return "下午 12:00-18:00"
            elif avg_hour >= 18 and avg_hour < 22:
                return "晚间 18:00-22:00"
            else:
                return "深夜 22:00-06:00"

        except Exception as e:
            self.logger.error(f"获取常用时段失败: {e}")
            return "暂无数据"

    def get_theory_preferences(self, days: int = 30) -> str:
        """
        获取偏好理论

        Args:
            days: 统计天数

        Returns:
            偏好理论描述
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            start_date = (date.today() - timedelta(days=days)).isoformat()
            cursor.execute("""
                SELECT theory, COUNT(*) as cnt
                FROM usage_stats
                WHERE date >= ? AND theory IS NOT NULL
                GROUP BY theory
                ORDER BY cnt DESC
            """, (start_date,))

            rows = cursor.fetchall()
            conn.close()

            if not rows:
                return "暂无数据"

            total = sum(row[1] for row in rows)
            if total == 0:
                return "暂无数据"

            # 格式化输出（最多显示3个）
            result_parts = []
            for theory, cnt in rows[:3]:
                percentage = int(cnt / total * 100)
                result_parts.append(f"{theory}({percentage}%)")

            return " ".join(result_parts)

        except Exception as e:
            self.logger.error(f"获取偏好理论失败: {e}")
            return "暂无数据"

    def get_question_type_preferences(self, days: int = 30) -> str:
        """
        获取问题类型偏好

        Args:
            days: 统计天数

        Returns:
            问题类型偏好描述
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            start_date = (date.today() - timedelta(days=days)).isoformat()
            cursor.execute("""
                SELECT question_type, COUNT(*) as cnt
                FROM usage_stats
                WHERE date >= ? AND question_type IS NOT NULL
                GROUP BY question_type
                ORDER BY cnt DESC
            """, (start_date,))

            rows = cursor.fetchall()
            conn.close()

            if not rows:
                return "暂无数据"

            total = sum(row[1] for row in rows)
            if total == 0:
                return "暂无数据"

            # 格式化输出（最多显示3个）
            result_parts = []
            for q_type, cnt in rows[:3]:
                percentage = int(cnt / total * 100)
                result_parts.append(f"{q_type}({percentage}%)")

            return " ".join(result_parts)

        except Exception as e:
            self.logger.error(f"获取问题类型偏好失败: {e}")
            return "暂无数据"

    def get_usage_profile(self, days: int = 30) -> Dict[str, Any]:
        """
        获取完整的使用画像

        Args:
            days: 统计天数

        Returns:
            使用画像字典
        """
        return {
            'frequency': self.get_usage_frequency(days),
            'time_slots': self.get_preferred_time_slots(days),
            'theories': self.get_theory_preferences(days),
            'question_types': self.get_question_type_preferences(days),
            'reading': self.get_reading_preferences(days),
            'reading_stats': self.get_reading_stats(days)
        }

    def get_usage_stats_summary(self) -> Dict[str, int]:
        """
        获取使用统计摘要

        Returns:
            统计摘要字典
        """
        week_wendao, week_tuiyan = self.get_weekly_usage_count()
        total_wendao, total_tuiyan = self.get_total_usage_count()

        return {
            'week_wendao': week_wendao,
            'week_tuiyan': week_tuiyan,
            'total_wendao': total_wendao,
            'total_tuiyan': total_tuiyan,
            'total': total_wendao + total_tuiyan
        }

    def get_usage_trend(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        获取每日使用趋势数据

        Args:
            days: 统计天数

        Returns:
            每日使用趋势列表 [{'date': 'MM-DD', 'wendao': N, 'tuiyan': N}, ...]
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 生成日期范围
            end_date = date.today()
            start_date = end_date - timedelta(days=days - 1)

            # 查询每日统计
            cursor.execute("""
                SELECT date, module, COUNT(*) as cnt
                FROM usage_stats
                WHERE date >= ? AND date <= ?
                GROUP BY date, module
                ORDER BY date
            """, (start_date.isoformat(), end_date.isoformat()))

            rows = cursor.fetchall()
            conn.close()

            # 构建结果字典
            daily_stats = {}
            current = start_date
            while current <= end_date:
                date_str = current.strftime('%m-%d')
                daily_stats[current.isoformat()] = {
                    'date': date_str,
                    'wendao': 0,
                    'tuiyan': 0
                }
                current += timedelta(days=1)

            # 填充查询结果
            for row in rows:
                date_key = row[0]
                module = row[1]
                count = row[2]
                if date_key in daily_stats:
                    if module == 'wendao':
                        daily_stats[date_key]['wendao'] = count
                    elif module == 'tuiyan':
                        daily_stats[date_key]['tuiyan'] = count

            # 按日期排序返回列表
            return [daily_stats[k] for k in sorted(daily_stats.keys())]

        except Exception as e:
            self.logger.error(f"获取使用趋势失败: {e}")
            return []

    # ==================== 行为日志 ====================

    def log_behavior(self, event_type: str, event_data: Optional[Dict] = None) -> bool:
        """
        记录行为事件

        Args:
            event_type: 事件类型
            event_data: 事件数据（可选）

        Returns:
            是否记录成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO behavior_log (event_type, event_data)
                VALUES (?, ?)
            """, (
                event_type,
                json.dumps(event_data) if event_data else None
            ))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            self.logger.error(f"记录行为失败: {e}")
            return False

    # ==================== 风险事件 ====================

    def record_risk_event(
        self,
        risk_level: str,
        trigger_pattern: Optional[str] = None,
        user_response: Optional[str] = None
    ) -> bool:
        """
        记录风险事件

        Args:
            risk_level: 风险级别 ('low' | 'medium' | 'high')
            trigger_pattern: 触发模式
            user_response: 用户响应

        Returns:
            是否记录成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO risk_events (risk_level, trigger_pattern, user_response)
                VALUES (?, ?, ?)
            """, (risk_level, trigger_pattern, user_response))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            self.logger.error(f"记录风险事件失败: {e}")
            return False

    # ==================== 状态评估（P2功能） ====================

    def get_recent_usage_count(self, hours: int = 6) -> int:
        """
        获取最近N小时的使用次数（用于密集分析检测）

        Args:
            hours: 小时数

        Returns:
            使用次数
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            threshold = (datetime.now() - timedelta(hours=hours)).isoformat()
            cursor.execute("""
                SELECT COUNT(*) FROM usage_stats
                WHERE created_at >= ?
            """, (threshold,))

            count = cursor.fetchone()[0]
            conn.close()
            return count

        except Exception as e:
            self.logger.error(f"获取最近使用次数失败: {e}")
            return 0

    def get_late_night_usage_count(self, days: int = 7) -> int:
        """
        获取最近N天深夜使用次数（22:00-06:00）

        Args:
            days: 天数

        Returns:
            深夜使用次数
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            cursor.execute("""
                SELECT COUNT(*) FROM usage_stats
                WHERE created_at >= ?
                AND (
                    CAST(strftime('%H', created_at) AS INTEGER) >= 22
                    OR CAST(strftime('%H', created_at) AS INTEGER) < 6
                )
            """, (start_date,))

            count = cursor.fetchone()[0]
            conn.close()
            return count

        except Exception as e:
            self.logger.error(f"获取深夜使用次数失败: {e}")
            return 0

    def check_repeated_questions(self, days: int = 7, threshold: int = 3) -> List[Tuple[str, int]]:
        """
        检查重复的问题类型（同一问题类型反复查询）

        Args:
            days: 检查天数
            threshold: 重复阈值

        Returns:
            重复的问题类型列表 [(question_type, count), ...]
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            cursor.execute("""
                SELECT question_type, COUNT(*) as cnt
                FROM usage_stats
                WHERE created_at >= ? AND question_type IS NOT NULL
                GROUP BY question_type
                HAVING cnt >= ?
                ORDER BY cnt DESC
            """, (start_date, threshold))

            results = [(row[0], row[1]) for row in cursor.fetchall()]
            conn.close()
            return results

        except Exception as e:
            self.logger.error(f"检查重复问题失败: {e}")
            return []

    def get_status_evaluation(self) -> Dict[str, Any]:
        """
        获取状态评估结果

        Returns:
            状态评估 {
                status: 'normal' | 'attention' | 'warning',
                status_text: str,
                status_emoji: str,
                alerts: [{type, message, level}, ...],
                details: {...}
            }
        """
        alerts = []
        details = {}

        # 检查1：密集分析（6小时内>5次）
        recent_count = self.get_recent_usage_count(hours=6)
        details['recent_6h'] = recent_count
        if recent_count > 5:
            alerts.append({
                'type': 'intensive_use',
                'message': f'最近6小时使用了{recent_count}次，建议适当休息',
                'level': 'warning' if recent_count > 8 else 'attention'
            })

        # 检查2：深夜使用（最近7天深夜使用>3次）
        late_night_count = self.get_late_night_usage_count(days=7)
        details['late_night_7d'] = late_night_count
        if late_night_count > 3:
            alerts.append({
                'type': 'late_night',
                'message': f'最近一周深夜使用{late_night_count}次，注意休息哦',
                'level': 'warning' if late_night_count > 5 else 'attention'
            })

        # 检查3：重复问题（同一类型问题反复查询）
        repeated = self.check_repeated_questions(days=7, threshold=4)
        details['repeated_questions'] = repeated
        if repeated:
            top_question = repeated[0]
            alerts.append({
                'type': 'repeated_query',
                'message': f'"{top_question[0]}"相关问题已查询{top_question[1]}次，或许可以暂时放下',
                'level': 'attention'
            })

        # 检查4：当前是否为深夜
        current_hour = datetime.now().hour
        details['current_hour'] = current_hour
        if current_hour >= 23 or current_hour < 5:
            alerts.append({
                'type': 'current_late_night',
                'message': '现在是深夜时段，早点休息对身体好',
                'level': 'attention'
            })

        # 综合评估状态
        warning_count = sum(1 for a in alerts if a['level'] == 'warning')
        attention_count = sum(1 for a in alerts if a['level'] == 'attention')

        if warning_count > 0:
            status = 'warning'
            status_emoji = '⚠️'
            status_text = '需要关注'
        elif attention_count >= 2:
            status = 'attention'
            status_emoji = '💛'
            status_text = '请留意'
        elif attention_count == 1:
            status = 'attention'
            status_emoji = '😊'
            status_text = '基本正常'
        else:
            status = 'normal'
            status_emoji = '😊'
            status_text = '正常'

        return {
            'status': status,
            'status_text': status_text,
            'status_emoji': status_emoji,
            'alerts': alerts,
            'details': details
        }

    # ==================== 数据管理 ====================

    def clear_all_data(self) -> bool:
        """
        清除所有使用数据

        Returns:
            是否清除成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("DELETE FROM usage_stats")
            cursor.execute("DELETE FROM behavior_log")
            cursor.execute("DELETE FROM risk_events")
            cursor.execute("DELETE FROM session_tracking")
            cursor.execute("DELETE FROM library_reading")

            conn.commit()
            conn.close()
            self.logger.info("已清除所有使用数据")
            return True

        except Exception as e:
            self.logger.error(f"清除数据失败: {e}")
            return False

    def export_data(self) -> Dict[str, Any]:
        """
        导出所有使用数据

        Returns:
            所有使用数据
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 使用统计
            cursor.execute("SELECT * FROM usage_stats ORDER BY created_at DESC")
            usage_stats = cursor.fetchall()

            # 行为日志
            cursor.execute("SELECT * FROM behavior_log ORDER BY created_at DESC")
            behavior_log = cursor.fetchall()

            # 风险事件
            cursor.execute("SELECT * FROM risk_events ORDER BY created_at DESC")
            risk_events = cursor.fetchall()

            # 会话追踪
            cursor.execute("SELECT * FROM session_tracking ORDER BY started_at DESC")
            session_tracking = cursor.fetchall()

            # 典籍阅读
            cursor.execute("SELECT * FROM library_reading ORDER BY created_at DESC")
            library_reading = cursor.fetchall()

            conn.close()

            return {
                'usage_stats': usage_stats,
                'behavior_log': behavior_log,
                'risk_events': risk_events,
                'session_tracking': session_tracking,
                'library_reading': library_reading,
                'exported_at': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"导出数据失败: {e}")
            return {}


# 全局单例
_usage_stats_manager = None


def get_usage_stats_manager() -> UsageStatsManager:
    """获取使用统计管理器单例"""
    global _usage_stats_manager
    if _usage_stats_manager is None:
        _usage_stats_manager = UsageStatsManager()
    return _usage_stats_manager
