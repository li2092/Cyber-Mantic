#!/usr/bin/env python3
"""
数据清理工具

功能：
1. 清理对话历史（conversation_history表）
2. 清理分析记录（analysis_records表）
3. 清理缓存数据
4. 重置数据库

使用方法：
    python tools/clear_data.py --help
"""

import argparse
import sqlite3
import sys
from pathlib import Path


def clear_conversation_history(db_path: str):
    """清理对话历史"""
    if not Path(db_path).exists():
        print(f"❌ 数据库文件不存在: {db_path}")
        return False

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # 检查表是否存在
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='conversation_history'
            """)

            if cursor.fetchone():
                cursor.execute("DELETE FROM conversation_history")
                deleted_count = cursor.rowcount
                conn.commit()
                print(f"✅ 已清理 {deleted_count} 条对话历史记录")
            else:
                print("ℹ️  对话历史表不存在，跳过")

        return True
    except Exception as e:
        print(f"❌ 清理对话历史失败: {e}")
        return False


def clear_analysis_records(db_path: str, confirm: bool = False):
    """清理分析记录"""
    if not Path(db_path).exists():
        print(f"❌ 数据库文件不存在: {db_path}")
        return False

    if not confirm:
        print("⚠️  清理分析记录需要确认（使用 --confirm 参数）")
        return False

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # 检查表是否存在
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='analysis_records'
            """)

            if cursor.fetchone():
                # 先获取记录数
                cursor.execute("SELECT COUNT(*) FROM analysis_records")
                count = cursor.fetchone()[0]

                if count > 0:
                    cursor.execute("DELETE FROM analysis_records")
                    conn.commit()
                    print(f"✅ 已清理 {count} 条分析记录")
                else:
                    print("ℹ️  分析记录为空")
            else:
                print("ℹ️  分析记录表不存在，跳过")

        return True
    except Exception as e:
        print(f"❌ 清理分析记录失败: {e}")
        return False


def clear_cache(db_path: str):
    """清理缓存数据"""
    if not Path(db_path).exists():
        print(f"❌ 数据库文件不存在: {db_path}")
        return False

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # 检查表是否存在
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='cache_data'
            """)

            if cursor.fetchone():
                cursor.execute("DELETE FROM cache_data")
                deleted_count = cursor.rowcount
                conn.commit()
                print(f"✅ 已清理 {deleted_count} 条缓存记录")
            else:
                print("ℹ️  缓存表不存在，跳过")

        return True
    except Exception as e:
        print(f"❌ 清理缓存失败: {e}")
        return False


def vacuum_database(db_path: str):
    """优化数据库（回收空间）"""
    if not Path(db_path).exists():
        print(f"❌ 数据库文件不存在: {db_path}")
        return False

    try:
        with sqlite3.connect(db_path) as conn:
            conn.execute("VACUUM")
            print("✅ 数据库已优化")
        return True
    except Exception as e:
        print(f"❌ 优化数据库失败: {e}")
        return False


def show_database_info(db_path: str):
    """显示数据库信息"""
    if not Path(db_path).exists():
        print(f"❌ 数据库文件不存在: {db_path}")
        return False

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            print(f"\n📊 数据库信息: {db_path}")
            print(f"文件大小: {Path(db_path).stat().st_size / 1024:.2f} KB\n")

            # 获取所有表
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table'
                ORDER BY name
            """)
            tables = cursor.fetchall()

            if tables:
                print("📋 数据表统计:")
                for (table_name,) in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    print(f"  - {table_name}: {count} 条记录")
            else:
                print("ℹ️  数据库中没有表")

        return True
    except Exception as e:
        print(f"❌ 获取数据库信息失败: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="赛博玄数 - 数据清理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 查看数据库信息
  python tools/clear_data.py --info

  # 清理对话历史
  python tools/clear_data.py --clear-conversations

  # 清理缓存
  python tools/clear_data.py --clear-cache

  # 清理所有数据（需要确认）
  python tools/clear_data.py --clear-all --confirm

  # 优化数据库
  python tools/clear_data.py --vacuum
        """
    )

    parser.add_argument(
        '--db-path',
        default='data/user/history.db',
        help='数据库文件路径（默认: data/user/history.db）'
    )

    parser.add_argument(
        '--info',
        action='store_true',
        help='显示数据库信息'
    )

    parser.add_argument(
        '--clear-conversations',
        action='store_true',
        help='清理对话历史'
    )

    parser.add_argument(
        '--clear-records',
        action='store_true',
        help='清理分析记录（需要 --confirm）'
    )

    parser.add_argument(
        '--clear-cache',
        action='store_true',
        help='清理缓存数据'
    )

    parser.add_argument(
        '--clear-all',
        action='store_true',
        help='清理所有数据（需要 --confirm）'
    )

    parser.add_argument(
        '--vacuum',
        action='store_true',
        help='优化数据库（回收空间）'
    )

    parser.add_argument(
        '--confirm',
        action='store_true',
        help='确认执行危险操作'
    )

    args = parser.parse_args()

    # 如果没有任何参数，显示帮助
    if len(sys.argv) == 1:
        parser.print_help()
        return

    print("🚀 赛博玄数 - 数据清理工具\n")

    # 显示数据库信息
    if args.info:
        show_database_info(args.db_path)
        print()

    # 清理对话历史
    if args.clear_conversations or args.clear_all:
        clear_conversation_history(args.db_path)

    # 清理缓存
    if args.clear_cache or args.clear_all:
        clear_cache(args.db_path)

    # 清理分析记录
    if args.clear_records or args.clear_all:
        clear_analysis_records(args.db_path, args.confirm)

    # 优化数据库
    if args.vacuum:
        vacuum_database(args.db_path)

    # 最后再次显示信息
    if args.clear_conversations or args.clear_cache or args.clear_records or args.clear_all:
        print()
        show_database_info(args.db_path)

    print("\n✨ 完成！")


if __name__ == "__main__":
    main()
