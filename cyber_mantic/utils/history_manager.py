"""
历史记录管理器 - 管理分析报告的存储和查询
"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from models import ComprehensiveReport


class HistoryManager:
    """历史记录管理器"""

    def __init__(self, db_path: str = "data/user/history.db"):
        """
        初始化历史记录管理器

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 创建历史记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analysis_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_id TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    question_type TEXT,
                    question_desc TEXT,
                    selected_theories TEXT,
                    executive_summary TEXT,
                    report_data TEXT NOT NULL,
                    user_input_summary TEXT
                )
            """)

            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at
                ON analysis_history(created_at DESC)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_question_type
                ON analysis_history(question_type)
            """)

            conn.commit()

    def save_report(self, report: ComprehensiveReport) -> bool:
        """
        保存分析报告

        Args:
            report: 综合报告对象

        Returns:
            是否保存成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 提取关键信息
                question_type = report.user_input_summary.get('question_type', '')
                question_desc = report.user_input_summary.get('question_description', '')
                selected_theories = ','.join(report.selected_theories)

                # 保存完整报告数据（JSON格式）
                report_data = report.to_json()
                user_input_summary = json.dumps(report.user_input_summary, ensure_ascii=False)

                cursor.execute("""
                    INSERT OR REPLACE INTO analysis_history
                    (report_id, created_at, question_type, question_desc,
                     selected_theories, executive_summary, report_data, user_input_summary)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    report.report_id,
                    report.created_at,
                    question_type,
                    question_desc,
                    selected_theories,
                    report.executive_summary,
                    report_data,
                    user_input_summary
                ))

                conn.commit()
                return True

        except Exception as e:
            print(f"保存历史记录失败: {e}")
            return False

    def get_recent_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取最近的历史记录列表

        Args:
            limit: 返回记录数量

        Returns:
            历史记录列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT id, report_id, created_at, question_type,
                           question_desc, selected_theories, executive_summary
                    FROM analysis_history
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (limit,))

                rows = cursor.fetchall()
                return [dict(row) for row in rows]

        except Exception as e:
            print(f"查询历史记录失败: {e}")
            return []

    def get_report_by_id(self, report_id: str) -> Optional[ComprehensiveReport]:
        """
        根据 report_id 获取完整报告

        Args:
            report_id: 报告ID

        Returns:
            综合报告对象，如果不存在则返回 None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT report_data
                    FROM analysis_history
                    WHERE report_id = ?
                """, (report_id,))

                row = cursor.fetchone()
                if row:
                    report_json = row[0]
                    report_dict = json.loads(report_json)
                    return self._dict_to_report(report_dict)

                return None

        except Exception as e:
            print(f"查询报告失败: {e}")
            return None

    def search_by_question_type(self, question_type: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        按问题类型搜索历史记录

        Args:
            question_type: 问题类型
            limit: 返回记录数量

        Returns:
            历史记录列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT id, report_id, created_at, question_type,
                           question_desc, selected_theories, executive_summary
                    FROM analysis_history
                    WHERE question_type = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (question_type, limit))

                rows = cursor.fetchall()
                return [dict(row) for row in rows]

        except Exception as e:
            print(f"搜索历史记录失败: {e}")
            return []

    def search_by_keyword(self, keyword: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        按关键词搜索历史记录（搜索问题描述）

        Args:
            keyword: 搜索关键词
            limit: 返回记录数量

        Returns:
            历史记录列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT id, report_id, created_at, question_type,
                           question_desc, selected_theories, executive_summary
                    FROM analysis_history
                    WHERE question_desc LIKE ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (f'%{keyword}%', limit))

                rows = cursor.fetchall()
                return [dict(row) for row in rows]

        except Exception as e:
            print(f"搜索历史记录失败: {e}")
            return []

    def search_by_module(self, module: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        按模块筛选历史记录（问道/推演）

        Args:
            module: 模块名称（"问道" 或 "推演"）
            limit: 返回记录数量

        Returns:
            历史记录列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # 通过 user_input_summary 中的 module 字段或推断逻辑
                # 如果有出生信息（birth_datetime），通常是推演；否则是问道
                if module == "推演":
                    cursor.execute("""
                        SELECT id, report_id, created_at, question_type,
                               question_desc, selected_theories, executive_summary
                        FROM analysis_history
                        WHERE user_input_summary LIKE '%"birth_datetime"%'
                           OR user_input_summary LIKE '%"module": "tuiyan"%'
                        ORDER BY created_at DESC
                        LIMIT ?
                    """, (limit,))
                else:  # 问道
                    cursor.execute("""
                        SELECT id, report_id, created_at, question_type,
                               question_desc, selected_theories, executive_summary
                        FROM analysis_history
                        WHERE user_input_summary NOT LIKE '%"birth_datetime"%'
                          AND user_input_summary NOT LIKE '%"module": "tuiyan"%'
                        ORDER BY created_at DESC
                        LIMIT ?
                    """, (limit,))

                rows = cursor.fetchall()
                return [dict(row) for row in rows]

        except Exception as e:
            print(f"按模块搜索历史记录失败: {e}")
            return []

    def search_by_module_and_type(self, module: str, question_type: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        同时按模块和问题类型筛选历史记录

        Args:
            module: 模块名称（"问道" 或 "推演"）
            question_type: 问题类型
            limit: 返回记录数量

        Returns:
            历史记录列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                if module == "推演":
                    cursor.execute("""
                        SELECT id, report_id, created_at, question_type,
                               question_desc, selected_theories, executive_summary
                        FROM analysis_history
                        WHERE question_type = ?
                          AND (user_input_summary LIKE '%"birth_datetime"%'
                               OR user_input_summary LIKE '%"module": "tuiyan"%')
                        ORDER BY created_at DESC
                        LIMIT ?
                    """, (question_type, limit))
                else:  # 问道
                    cursor.execute("""
                        SELECT id, report_id, created_at, question_type,
                               question_desc, selected_theories, executive_summary
                        FROM analysis_history
                        WHERE question_type = ?
                          AND user_input_summary NOT LIKE '%"birth_datetime"%'
                          AND user_input_summary NOT LIKE '%"module": "tuiyan"%'
                        ORDER BY created_at DESC
                        LIMIT ?
                    """, (question_type, limit))

                rows = cursor.fetchall()
                return [dict(row) for row in rows]

        except Exception as e:
            print(f"按模块和类型搜索历史记录失败: {e}")
            return []

    def delete_report(self, report_id: str) -> bool:
        """
        删除历史记录

        Args:
            report_id: 报告ID

        Returns:
            是否删除成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    DELETE FROM analysis_history
                    WHERE report_id = ?
                """, (report_id,))

                conn.commit()
                return cursor.rowcount > 0

        except Exception as e:
            print(f"删除历史记录失败: {e}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取历史记录统计信息

        Returns:
            统计信息字典
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 总记录数
                cursor.execute("SELECT COUNT(*) FROM analysis_history")
                total_count = cursor.fetchone()[0]

                # 按问题类型统计
                cursor.execute("""
                    SELECT question_type, COUNT(*) as count
                    FROM analysis_history
                    GROUP BY question_type
                    ORDER BY count DESC
                """)
                type_stats = {row[0]: row[1] for row in cursor.fetchall()}

                # 最近分析时间
                cursor.execute("""
                    SELECT MAX(created_at) FROM analysis_history
                """)
                last_analysis = cursor.fetchone()[0]

                return {
                    'total_count': total_count,
                    'type_statistics': type_stats,
                    'last_analysis_time': last_analysis
                }

        except Exception as e:
            print(f"获取统计信息失败: {e}")
            return {
                'total_count': 0,
                'type_statistics': {},
                'last_analysis_time': None
            }

    def _dict_to_report(self, data: Dict[str, Any]) -> ComprehensiveReport:
        """
        将字典转换为 ComprehensiveReport 对象

        Args:
            data: 报告字典数据

        Returns:
            ComprehensiveReport 对象
        """
        from models import TheoryAnalysisResult, ConflictInfo

        # 转换时间字符串为 datetime 对象
        created_at = datetime.fromisoformat(data['created_at'])

        # 转换理论结果
        theory_results = []
        for tr_data in data['theory_results']:
            tr = TheoryAnalysisResult(
                theory_name=tr_data['theory_name'],
                calculation_data=tr_data.get('calculation_data', {}),
                interpretation=tr_data['interpretation'],
                judgment=tr_data.get('judgment', '平'),
                judgment_level=tr_data.get('judgment_level', 0.5),
                timing=tr_data.get('timing'),
                advice=tr_data.get('advice'),
                confidence=tr_data.get('confidence', 0.8),
                retrospective_answer=tr_data.get('retrospective_answer'),
                predictive_answer=tr_data.get('predictive_answer')
            )
            theory_results.append(tr)

        # 转换冲突信息
        conflict_data = data['conflict_info']
        conflict_info = ConflictInfo(
            has_conflict=conflict_data['has_conflict'],
            conflicts=conflict_data['conflicts'],
            resolution=conflict_data['resolution']
        )

        # 处理详细分析字段（新版本字段，兼容旧版本报告）
        if 'detailed_analysis' not in data:
            self.logger.info(
                f"加载旧版本报告 {data['report_id'][:8]}... (创建于 {created_at.strftime('%Y-%m-%d %H:%M')}), "
                f"该报告使用旧版格式，详细分析内容已从执行摘要中提取"
            )
            detailed_analysis = f"*【此报告为旧版本格式，详细内容请参考执行摘要】*\n\n{data['executive_summary']}"
        else:
            detailed_analysis = data['detailed_analysis']

        # 创建报告对象
        report = ComprehensiveReport(
            report_id=data['report_id'],
            created_at=created_at,
            user_input_summary=data['user_input_summary'],
            selected_theories=data['selected_theories'],
            selection_reason=data['selection_reason'],
            theory_results=theory_results,
            conflict_info=conflict_info,
            executive_summary=data['executive_summary'],
            detailed_analysis=detailed_analysis,
            retrospective_analysis=data['retrospective_analysis'],
            predictive_analysis=data['predictive_analysis'],
            comprehensive_advice=data['comprehensive_advice'],
            overall_confidence=data['overall_confidence'],
            limitations=data['limitations'],
            user_feedback=data.get('user_feedback')
        )

        return report


# 全局历史管理器实例
_history_manager: Optional[HistoryManager] = None


def get_history_manager() -> HistoryManager:
    """获取全局历史管理器实例（从配置文件读取路径）"""
    global _history_manager
    if _history_manager is None:
        # 从配置读取历史记录路径
        try:
            from utils.config_manager import get_config_manager
            config = get_config_manager()
            # 优先使用新配置项 data.history.db_path
            db_path = config.get("data.history.db_path")
            if not db_path:
                # 兼容旧配置项 data.user_history_db
                db_path = config.get("data.user_history_db", "data/user/history.db")
        except Exception:
            # 如果配置读取失败，使用默认路径
            db_path = "data/user/history.db"

        _history_manager = HistoryManager(db_path=db_path)
    return _history_manager
