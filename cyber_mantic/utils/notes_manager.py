"""
笔记管理器
用于管理典籍模块的笔记摘抄功能

功能：
- notes: 摘录内容、来源、用户笔记、标签
- tags: 标签管理

设计参考：docs/design/02_典籍模块设计.md
"""
import sqlite3
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
from utils.logger import get_logger


class NotesManager:
    """笔记管理器"""

    def __init__(self, db_path: Optional[str] = None):
        """
        初始化笔记管理器

        Args:
            db_path: 数据库路径，默认使用 ~/.cyber_mantic/notes.db
        """
        self.logger = get_logger(__name__)

        if db_path is None:
            app_dir = Path.home() / ".cyber_mantic"
            app_dir.mkdir(exist_ok=True)
            db_path = str(app_dir / "notes.db")

        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 笔记表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                source_file TEXT NOT NULL,
                source_position TEXT,
                user_note TEXT,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 标签表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                color TEXT DEFAULT '#666666'
            )
        """)

        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_notes_source
            ON notes(source_file)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_notes_created
            ON notes(created_at)
        """)

        conn.commit()
        conn.close()
        self.logger.info(f"笔记数据库初始化完成: {self.db_path}")

    # ==================== 笔记操作 ====================

    def create_note(
        self,
        content: str,
        source_file: str,
        source_position: Optional[str] = None,
        user_note: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> int:
        """
        创建笔记

        Args:
            content: 摘录原文
            source_file: 来源文件路径
            source_position: 来源位置（章节/页码）
            user_note: 用户笔记
            tags: 标签列表

        Returns:
            笔记ID，失败返回 -1
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO notes (content, source_file, source_position, user_note, tags)
                VALUES (?, ?, ?, ?, ?)
            """, (
                content,
                source_file,
                source_position,
                user_note,
                json.dumps(tags) if tags else None
            ))

            note_id = cursor.lastrowid
            conn.commit()
            conn.close()

            # 自动创建标签
            if tags:
                for tag in tags:
                    self.create_tag(tag)

            self.logger.debug(f"创建笔记: id={note_id}")
            return note_id

        except Exception as e:
            self.logger.error(f"创建笔记失败: {e}")
            return -1

    def get_note(self, note_id: int) -> Optional[Dict[str, Any]]:
        """
        获取单个笔记

        Args:
            note_id: 笔记ID

        Returns:
            笔记字典，不存在返回 None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
            row = cursor.fetchone()
            conn.close()

            if row:
                note = dict(row)
                note['tags'] = json.loads(note['tags']) if note['tags'] else []
                return note
            return None

        except Exception as e:
            self.logger.error(f"获取笔记失败: {e}")
            return None

    def get_all_notes(
        self,
        source_file: Optional[str] = None,
        tag: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        获取笔记列表

        Args:
            source_file: 按来源文件筛选
            tag: 按标签筛选
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            笔记列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = "SELECT * FROM notes WHERE 1=1"
            params = []

            if source_file:
                query += " AND source_file = ?"
                params.append(source_file)

            if tag:
                query += " AND tags LIKE ?"
                params.append(f'%"{tag}"%')

            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            notes = []
            for row in rows:
                note = dict(row)
                note['tags'] = json.loads(note['tags']) if note['tags'] else []
                notes.append(note)

            return notes

        except Exception as e:
            self.logger.error(f"获取笔记列表失败: {e}")
            return []

    def update_note(
        self,
        note_id: int,
        user_note: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """
        更新笔记

        Args:
            note_id: 笔记ID
            user_note: 用户笔记（可选更新）
            tags: 标签列表（可选更新）

        Returns:
            是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            updates = ["updated_at = CURRENT_TIMESTAMP"]
            params = []

            if user_note is not None:
                updates.append("user_note = ?")
                params.append(user_note)

            if tags is not None:
                updates.append("tags = ?")
                params.append(json.dumps(tags))
                # 自动创建新标签
                for tag in tags:
                    self.create_tag(tag)

            params.append(note_id)

            cursor.execute(f"""
                UPDATE notes SET {', '.join(updates)} WHERE id = ?
            """, params)

            conn.commit()
            conn.close()
            self.logger.debug(f"更新笔记: id={note_id}")
            return True

        except Exception as e:
            self.logger.error(f"更新笔记失败: {e}")
            return False

    def delete_note(self, note_id: int) -> bool:
        """
        删除笔记

        Args:
            note_id: 笔记ID

        Returns:
            是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))

            conn.commit()
            conn.close()
            self.logger.debug(f"删除笔记: id={note_id}")
            return True

        except Exception as e:
            self.logger.error(f"删除笔记失败: {e}")
            return False

    def get_notes_count(self, source_file: Optional[str] = None) -> int:
        """
        获取笔记数量

        Args:
            source_file: 按来源文件筛选

        Returns:
            笔记数量
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            if source_file:
                cursor.execute(
                    "SELECT COUNT(*) FROM notes WHERE source_file = ?",
                    (source_file,)
                )
            else:
                cursor.execute("SELECT COUNT(*) FROM notes")

            count = cursor.fetchone()[0]
            conn.close()
            return count

        except Exception as e:
            self.logger.error(f"获取笔记数量失败: {e}")
            return 0

    # ==================== 标签操作 ====================

    def create_tag(self, name: str, color: str = "#666666") -> int:
        """
        创建标签（如果不存在）

        Args:
            name: 标签名
            color: 标签颜色

        Returns:
            标签ID
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 尝试插入，如果已存在则忽略
            cursor.execute("""
                INSERT OR IGNORE INTO tags (name, color) VALUES (?, ?)
            """, (name, color))

            # 获取标签ID
            cursor.execute("SELECT id FROM tags WHERE name = ?", (name,))
            tag_id = cursor.fetchone()[0]

            conn.commit()
            conn.close()
            return tag_id

        except Exception as e:
            self.logger.error(f"创建标签失败: {e}")
            return -1

    def get_all_tags(self) -> List[Dict[str, Any]]:
        """
        获取所有标签

        Returns:
            标签列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM tags ORDER BY name")
            rows = cursor.fetchall()
            conn.close()

            return [dict(row) for row in rows]

        except Exception as e:
            self.logger.error(f"获取标签列表失败: {e}")
            return []

    def update_tag_color(self, name: str, color: str) -> bool:
        """
        更新标签颜色

        Args:
            name: 标签名
            color: 新颜色

        Returns:
            是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("UPDATE tags SET color = ? WHERE name = ?", (color, name))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            self.logger.error(f"更新标签颜色失败: {e}")
            return False

    def delete_tag(self, name: str) -> bool:
        """
        删除标签（从标签表删除，笔记中的标签保留）

        Args:
            name: 标签名

        Returns:
            是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("DELETE FROM tags WHERE name = ?", (name,))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            self.logger.error(f"删除标签失败: {e}")
            return False

    # ==================== 搜索功能 ====================

    def search_notes(self, keyword: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        搜索笔记

        Args:
            keyword: 搜索关键词
            limit: 返回数量限制

        Returns:
            笔记列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM notes
                WHERE content LIKE ? OR user_note LIKE ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (f"%{keyword}%", f"%{keyword}%", limit))

            rows = cursor.fetchall()
            conn.close()

            notes = []
            for row in rows:
                note = dict(row)
                note['tags'] = json.loads(note['tags']) if note['tags'] else []
                notes.append(note)

            return notes

        except Exception as e:
            self.logger.error(f"搜索笔记失败: {e}")
            return []

    # ==================== 导出功能 ====================

    def export_notes_markdown(self, tag: Optional[str] = None) -> str:
        """
        导出笔记为 Markdown 格式

        Args:
            tag: 按标签筛选导出

        Returns:
            Markdown 文本
        """
        notes = self.get_all_notes(tag=tag, limit=1000)

        if not notes:
            return "# 我的笔记\n\n暂无笔记"

        lines = ["# 我的笔记\n"]

        if tag:
            lines.append(f"> 标签筛选: #{tag}\n")

        lines.append(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        lines.append("---\n")

        for note in notes:
            # 标题（来源）
            source_name = Path(note['source_file']).stem if note['source_file'] else "未知来源"
            lines.append(f"## 来自《{source_name}》\n")

            if note['source_position']:
                lines.append(f"*位置: {note['source_position']}*\n")

            # 摘录内容
            lines.append(f"> {note['content']}\n")

            # 用户笔记
            if note['user_note']:
                lines.append(f"\n**我的笔记:** {note['user_note']}\n")

            # 标签
            if note['tags']:
                tag_str = " ".join([f"`#{t}`" for t in note['tags']])
                lines.append(f"\n{tag_str}\n")

            # 时间
            lines.append(f"\n*记录于 {note['created_at']}*\n")
            lines.append("\n---\n")

        return "\n".join(lines)

    def clear_all_notes(self) -> bool:
        """
        清除所有笔记

        Returns:
            是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("DELETE FROM notes")
            cursor.execute("DELETE FROM tags")

            conn.commit()
            conn.close()
            self.logger.info("已清除所有笔记")
            return True

        except Exception as e:
            self.logger.error(f"清除笔记失败: {e}")
            return False


# 全局单例
_notes_manager = None


def get_notes_manager() -> NotesManager:
    """获取笔记管理器单例"""
    global _notes_manager
    if _notes_manager is None:
        _notes_manager = NotesManager()
    return _notes_manager
