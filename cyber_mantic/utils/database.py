"""
数据持久化层 - SQLite数据库管理

安全说明：
- 所有SQL查询均使用参数化查询（? 占位符），防止SQL注入攻击
- 敏感数据（用户输入、报告内容）使用Fernet加密存储
- 加密密钥存储在独立文件中，不包含在代码仓库中
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from cryptography.fernet import Fernet
import os


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, db_path: str = "data/user/history.db", encryption_key: Optional[str] = None):
        """
        初始化数据库管理器

        Args:
            db_path: 数据库文件路径
            encryption_key: 加密密钥（可选）
        """
        self.db_path = db_path
        self.encryption_key = encryption_key or self._get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key.encode() if isinstance(self.encryption_key, str) else self.encryption_key)

        # 确保数据库目录存在
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # 初始化数据库
        self._init_database()

    def _get_or_create_encryption_key(self) -> bytes:
        """获取或创建加密密钥"""
        key_file = Path(".encryption_key")

        if key_file.exists():
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key

    def _init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建分析历史表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP NOT NULL,
                question_type TEXT NOT NULL,
                question_description TEXT,
                selected_theories TEXT NOT NULL,
                user_input_encrypted TEXT,
                report_data_encrypted TEXT,
                overall_confidence REAL,
                user_rating INTEGER,
                user_feedback TEXT,
                deleted_at TIMESTAMP
            )
        ''')

        # 创建索引
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_created_at
            ON analysis_history(created_at)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_question_type
            ON analysis_history(question_type)
        ''')

        conn.commit()
        conn.close()

    def save_analysis_report(self, report: 'ComprehensiveReport') -> bool:
        """
        保存分析报告

        Args:
            report: 综合报告对象

        Returns:
            是否保存成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 加密敏感数据
            user_input_encrypted = self._encrypt_data(report.user_input_summary)
            report_data_encrypted = self._encrypt_data(report.to_dict())

            cursor.execute('''
                INSERT INTO analysis_history (
                    report_id, created_at, question_type, question_description,
                    selected_theories, user_input_encrypted, report_data_encrypted,
                    overall_confidence
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                report.report_id,
                report.created_at,
                report.user_input_summary.get('question_type'),
                report.user_input_summary.get('question_description'),
                json.dumps(report.selected_theories),
                user_input_encrypted,
                report_data_encrypted,
                report.overall_confidence
            ))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            print(f"保存报告失败: {e}")
            return False

    def get_analysis_history(
        self,
        limit: int = 10,
        offset: int = 0,
        question_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取分析历史记录

        Args:
            limit: 返回记录数量
            offset: 偏移量
            question_type: 问题类型过滤

        Returns:
            历史记录列表
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = '''
            SELECT id, report_id, created_at, question_type, question_description,
                   selected_theories, overall_confidence, user_rating
            FROM analysis_history
            WHERE deleted_at IS NULL
        '''

        params = []

        if question_type:
            query += ' AND question_type = ?'
            params.append(question_type)

        query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()

        history = []
        for row in rows:
            history.append({
                'id': row['id'],
                'report_id': row['report_id'],
                'created_at': row['created_at'],
                'question_type': row['question_type'],
                'question_description': row['question_description'],
                'selected_theories': json.loads(row['selected_theories']),
                'overall_confidence': row['overall_confidence'],
                'user_rating': row['user_rating']
            })

        conn.close()
        return history

    def get_report_by_id(self, report_id: str) -> Optional[Dict[str, Any]]:
        """
        根据ID获取完整报告

        Args:
            report_id: 报告ID

        Returns:
            报告数据
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT report_data_encrypted
            FROM analysis_history
            WHERE report_id = ? AND deleted_at IS NULL
        ''', (report_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return self._decrypt_data(row['report_data_encrypted'])
        return None

    def update_user_feedback(self, report_id: str, rating: int, feedback: str = None) -> bool:
        """
        更新用户反馈

        Args:
            report_id: 报告ID
            rating: 评分（1-5）
            feedback: 文字反馈

        Returns:
            是否更新成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE analysis_history
                SET user_rating = ?, user_feedback = ?
                WHERE report_id = ?
            ''', (rating, feedback, report_id))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            print(f"更新反馈失败: {e}")
            return False

    def delete_old_records(self, days: int = 30) -> int:
        """
        删除旧记录（软删除）

        Args:
            days: 保留天数

        Returns:
            删除的记录数
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE analysis_history
            SET deleted_at = ?
            WHERE deleted_at IS NULL
              AND datetime(created_at) < datetime('now', '-' || ? || ' days')
        ''', (datetime.now(), days))

        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()

        return deleted_count

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计数据
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 总记录数
        cursor.execute('SELECT COUNT(*) FROM analysis_history WHERE deleted_at IS NULL')
        total_count = cursor.fetchone()[0]

        # 按问题类型统计
        cursor.execute('''
            SELECT question_type, COUNT(*) as count
            FROM analysis_history
            WHERE deleted_at IS NULL
            GROUP BY question_type
            ORDER BY count DESC
        ''')
        type_stats = dict(cursor.fetchall())

        # 平均置信度
        cursor.execute('SELECT AVG(overall_confidence) FROM analysis_history WHERE deleted_at IS NULL')
        avg_confidence = cursor.fetchone()[0] or 0

        # 用户评分统计
        cursor.execute('''
            SELECT AVG(user_rating) as avg_rating, COUNT(user_rating) as rating_count
            FROM analysis_history
            WHERE deleted_at IS NULL AND user_rating IS NOT NULL
        ''')
        rating_data = cursor.fetchone()

        conn.close()

        return {
            'total_count': total_count,
            'type_statistics': type_stats,
            'average_confidence': avg_confidence,
            'average_rating': rating_data[0] if rating_data[0] else None,
            'rating_count': rating_data[1]
        }

    def _encrypt_data(self, data: Any) -> str:
        """加密数据"""
        json_data = json.dumps(data, ensure_ascii=False)
        encrypted = self.cipher.encrypt(json_data.encode())
        return encrypted.decode()

    def _decrypt_data(self, encrypted_data: str) -> Any:
        """解密数据"""
        decrypted = self.cipher.decrypt(encrypted_data.encode())
        return json.loads(decrypted.decode())


class HistoryManager:
    """历史记录管理器（高级接口）"""

    def __init__(self, db_manager: DatabaseManager):
        """
        初始化历史管理器

        Args:
            db_manager: 数据库管理器
        """
        self.db = db_manager

    def save_report(self, report: 'ComprehensiveReport') -> bool:
        """保存报告"""
        return self.db.save_analysis_report(report)

    def get_recent_reports(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的报告"""
        return self.db.get_analysis_history(limit=limit)

    def get_reports_by_type(self, question_type: str, limit: int = 10) -> List[Dict[str, Any]]:
        """按类型获取报告"""
        return self.db.get_analysis_history(limit=limit, question_type=question_type)

    def get_full_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """获取完整报告"""
        return self.db.get_report_by_id(report_id)

    def rate_report(self, report_id: str, rating: int, feedback: str = None) -> bool:
        """评价报告"""
        if not 1 <= rating <= 5:
            raise ValueError("评分必须在1-5之间")
        return self.db.update_user_feedback(report_id, rating, feedback)

    def cleanup_old_data(self, days: int = 30) -> int:
        """清理旧数据"""
        return self.db.delete_old_records(days)

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.db.get_statistics()
