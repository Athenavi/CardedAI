"""
插件数据库管理器
为每个插件提供独立的SQLite数据库,统一存放在plugins_data目录
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


class PluginDatabaseManager:
    """插件数据库管理器 - 为每个插件管理独立的SQLite数据库"""

    def __init__(self, base_dir: str = "plugins_data"):
        """
        初始化数据库管理器
        
        Args:
            base_dir: 插件数据库根目录
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.connections: Dict[str, sqlite3.Connection] = {}

    def get_connection(self, plugin_slug: str) -> sqlite3.Connection:
        """
        获取插件的数据库连接(单例模式)
        
        Args:
            plugin_slug: 插件标识符
            
        Returns:
            SQLite数据库连接
        """
        if plugin_slug not in self.connections:
            db_path = self.base_dir / f"{plugin_slug}.db"
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row  # 支持字典式访问
            # 启用外键支持
            conn.execute("PRAGMA foreign_keys = ON")
            # 设置WAL模式提高并发性能
            conn.execute("PRAGMA journal_mode = WAL")
            self.connections[plugin_slug] = conn

        return self.connections[plugin_slug]

    @contextmanager
    def get_cursor(self, plugin_slug: str):
        """
        获取数据库游标(上下文管理器,自动提交/回滚)
        
        Args:
            plugin_slug: 插件标识符
            
        Yields:
            数据库游标
        """
        conn = self.get_connection(plugin_slug)
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e

    def close_all(self):
        """关闭所有数据库连接"""
        for conn in self.connections.values():
            conn.close()
        self.connections.clear()

    def close_plugin_db(self, plugin_slug: str):
        """关闭指定插件的数据库连接"""
        if plugin_slug in self.connections:
            self.connections[plugin_slug].close()
            del self.connections[plugin_slug]

    def delete_plugin_db(self, plugin_slug: str) -> bool:
        """
        删除插件的数据库文件
        
        Args:
            plugin_slug: 插件标识符
            
        Returns:
            是否删除成功
        """
        try:
            # 先关闭连接
            self.close_plugin_db(plugin_slug)

            # 删除数据库文件
            db_path = self.base_dir / f"{plugin_slug}.db"
            if db_path.exists():
                db_path.unlink()

            # 删除WAL和SHM文件
            for ext in ['-wal', '-shm']:
                wal_path = Path(str(db_path) + ext)
                if wal_path.exists():
                    wal_path.unlink()

            return True
        except Exception as e:
            print(f"[PluginDB] Failed to delete database for {plugin_slug}: {e}")
            return False

    def list_plugin_databases(self) -> List[Dict[str, Any]]:
        """
        列出所有插件数据库
        
        Returns:
            数据库信息列表
        """
        databases = []
        for db_file in self.base_dir.glob("*.db"):
            stat = db_file.stat()
            databases.append({
                'plugin_slug': db_file.stem,
                'file_path': str(db_file),
                'size_bytes': stat.st_size,
                'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
        return databases

    def execute_query(self, plugin_slug: str, query: str, params: tuple = ()) -> List[Dict]:
        """
        执行查询语句
        
        Args:
            plugin_slug: 插件标识符
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            查询结果列表
        """
        with self.get_cursor(plugin_slug) as cursor:
            cursor.execute(query, params)
            if cursor.description:  # SELECT语句
                return [dict(row) for row in cursor.fetchall()]
            return []

    def execute_update(self, plugin_slug: str, query: str, params: tuple = ()) -> int:
        """
        执行更新语句(INSERT/UPDATE/DELETE)
        
        Args:
            plugin_slug: 插件标识符
            query: SQL更新语句
            params: 更新参数
            
        Returns:
            影响的行数
        """
        with self.get_cursor(plugin_slug) as cursor:
            cursor.execute(query, params)
            return cursor.rowcount

    def table_exists(self, plugin_slug: str, table_name: str) -> bool:
        """
        检查表是否存在
        
        Args:
            plugin_slug: 插件标识符
            table_name: 表名
            
        Returns:
            表是否存在
        """
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        result = self.execute_query(plugin_slug, query, (table_name,))
        return len(result) > 0


# 全局实例
plugin_db = PluginDatabaseManager()
