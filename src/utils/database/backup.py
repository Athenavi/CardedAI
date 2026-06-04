"""
数据库备份工具库
基于 SQLAlchemy 的数据库结构和数据备份工具
"""

import gzip
import os
import zipfile
from datetime import datetime, date

from sqlalchemy import text

from src.utils.security.safe import sanitize_sql_identifier


def _get_timestamp():
    """获取当前时间戳字符串"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


class DatabaseBackup:
    """数据库备份工具类"""

    def __init__(self, db, backup_dir="backups"):
        """
        初始化备份工具

        Args:
            db: SQLAlchemy 数据库会话或引擎实例
            backup_dir: 备份文件存储目录
        """
        self.db = db
        self.backup_dir = backup_dir
        self._ensure_backup_dir()

        # 获取数据库方言 - 支持多种SQLAlchemy实例类型
        if hasattr(db, 'bind') and hasattr(db.bind, 'dialect'):
            # Session实例
            self.dialect_name = db.bind.dialect.name
        elif hasattr(db, 'engine') and hasattr(db.engine, 'dialect'):
            # Flask-SQLAlchemy实例
            self.dialect_name = db.engine.dialect.name
        elif hasattr(db, 'dialect') and hasattr(db.dialect, 'name'):
            # Engine实例
            self.dialect_name = db.dialect.name
        elif hasattr(db, 'session') and hasattr(db.session, 'bind') and hasattr(db.session.bind, 'dialect'):
            # 具有session的包装实例
            self.dialect_name = db.session.bind.dialect.name
        else:
            # 尝试从连接获取方言
            try:
                with db.connect() if hasattr(db, 'connect') else db.begin() as conn:
                    self.dialect_name = conn.dialect.name
            except:
                raise ValueError("无法确定数据库方言 - 没有可用的数据库引擎或会话绑定")

    def _ensure_backup_dir(self):
        """确保备份目录存在"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

    def _get_tables(self):
        """获取需要备份的表列表"""
        # 根据db类型获取metadata
        if hasattr(self.db, 'metadata'):
            # Flask-SQLAlchemy 或直接访问metadata的情况
            metadata = self.db.metadata
        elif hasattr(self.db, 'bind') and hasattr(self.db.bind, 'metadata'):
            # Session实例
            metadata = self.db.bind.metadata
        else:
            # 通过反射获取表名
            from sqlalchemy import inspect
            with self.db.connect() if hasattr(self.db, 'connect') else self.db.begin() as conn:
                insp = inspect(conn)
                return insp.get_table_names()

        all_tables = list(metadata.tables.keys()) if hasattr(metadata, 'tables') else []
        # 过滤掉系统表
        exclude_tables = ['alembic_version', 'sqlite_sequence']
        tables_to_backup = [table for table in all_tables if table not in exclude_tables]

        return tables_to_backup

    def _get_connection(self):
        """获取数据库连接"""
        # 支持多种连接方式
        if hasattr(self.db, 'connection') and callable(getattr(self.db, 'connection')):
            # Session实例
            return self.db.connection()
        elif hasattr(self.db, 'connect') and callable(getattr(self.db, 'connect')):
            # Engine实例
            return self.db.connect()
        elif hasattr(self.db, 'bind') and hasattr(self.db.bind, 'connect'):
            # Session的bind
            return self.db.bind.connect()
        else:
            # 如果db本身就是连接对象
            return self.db

    def _format_value(self, value, column_type=None):
        """格式化数据库值用于SQL语句"""
        if value is None:
            return "NULL"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, bool):
            if self.dialect_name == 'sqlite':
                return "1" if value else "0"
            else:
                return "TRUE" if value else "FALSE"
        elif isinstance(value, (datetime, date)):
            return f"'{value.isoformat()}'"
        else:
            escaped = str(value).replace("'", "''")
            return f"'{escaped}'"

    @staticmethod
    def _is_valid_table_name(table_name):
        """验证表名是否合法，防止SQL注入"""
        try:
            # 使用安全函数验证表名
            sanitize_sql_identifier(table_name)
            return True
        except ValueError:
            return False

    def backup_schema(self, filepath=None, compress=False):
        """
        备份数据库结构

        Args:
            filepath: 备份文件路径，如果为None则自动生成
            compress: 是否压缩备份文件

        Returns:
            str: 备份文件路径
        """
        if filepath is None:
            timestamp = _get_timestamp()
            filename = f"schema_backup_{timestamp}.sql"
            filepath = os.path.join(self.backup_dir, filename)

        if compress and not filepath.endswith('.gz'):
            filepath += '.gz'

        try:
            print(f"开始备份数据库结构: {self.dialect_name}")

            tables = self._get_tables()
            print(f"找到 {len(tables)} 个表需要备份")

            schema_sql = ["-- Database Schema Backup",
                          f"-- Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                          f"-- Database dialect: {self.dialect_name}", ""]

            # 使用适当的方式获取连接
            if hasattr(self.db, 'connect') or hasattr(self.db, 'connection') or hasattr(self.db, 'bind'):
                connection = self._get_connection()
                own_connection = True
            else:
                # 如果db本身就是连接对象
                connection = self.db
                own_connection = False

            for table in tables:
                print(f"处理表结构: {table}")

                # 验证表名是否合法（防止SQL注入）
                if not self._is_valid_table_name(table):
                    print(f"警告: 表名包含非法字符: {table}")
                    schema_sql.append(f"-- Warning: Invalid table name: {table}")
                    schema_sql.append("")
                    continue

                # 检查表是否存在 - 使用参数化查询
                try:
                    if self.dialect_name == 'sqlite':
                        # SQLite 使用参数化查询
                        table_exists_result = connection.execute(
                            text("SELECT name FROM sqlite_master WHERE type='table' AND name = :table_name"),
                            {"table_name": table}
                        )
                        if not table_exists_result.fetchone():
                            print(f"警告: 表 {table} 不存在，跳过备份")
                            schema_sql.append(f"-- Warning: Table {table} does not exist, skipped")
                            schema_sql.append("")
                            continue
                    elif self.dialect_name == 'postgresql':
                        # PostgreSQL 使用参数化查询
                        table_exists_result = connection.execute(
                            text(
                                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = :table_name)"),
                            {"table_name": table}
                        )
                        if not table_exists_result.fetchone()[0]:
                            print(f"警告: 表 {table} 不存在，跳过备份")
                            schema_sql.append(f"-- Warning: Table {table} does not exist, skipped")
                            schema_sql.append("")
                            continue
                except Exception as e:
                    print(f"检查表 {table} 是否存在时出错: {str(e)}")
                    schema_sql.append(f"-- Error checking existence of table {table}: {str(e)}")
                    schema_sql.append("")
                    continue

                if self.dialect_name == 'sqlite':
                    # SQLite 获取表结构 - 使用参数化查询
                    try:
                        create_table_result = connection.execute(
                            text("SELECT sql FROM sqlite_master WHERE type='table' AND name = :table_name"),
                            {"table_name": table}
                        )
                        create_row = create_table_result.fetchone()
                        if create_row and create_row[0]:
                            create_sql = create_row[0]
                            schema_sql.append(create_sql + ";")
                        else:
                            schema_sql.append(f"-- Table {table} not found in sqlite_master")

                        # 获取索引 - 使用参数化查询
                        indexes_result = connection.execute(
                            text(
                                "SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name = :table_name AND sql IS NOT NULL"),
                            {"table_name": table}
                        )
                        for row in indexes_result:
                            if row[0]:
                                schema_sql.append(row[0] + ";")

                    except Exception as e:
                        schema_sql.append(f"-- Error processing table {table}: {str(e)}")
                        print(f"处理SQLite表 {table} 时出错: {str(e)}")

                elif self.dialect_name == 'postgresql':
                    # PostgreSQL 获取表结构 - 使用参数化查询
                    try:
                        create_table_result = connection.execute(
                            text("SELECT column_name, data_type, is_nullable, column_default "
                                 "FROM information_schema.columns WHERE table_name = :table_name "
                                 "ORDER BY ordinal_position"),
                            {"table_name": table}
                        )

                        columns = []
                        for row in create_table_result:
                            col_def = f"{row[0]} {row[1]}"
                            if row[2] == 'NO':
                                col_def += " NOT NULL"
                            if row[3]:
                                col_def += f" DEFAULT {row[3]}"
                            columns.append(col_def)

                        if columns:
                            schema_sql.append(f"CREATE TABLE {table} (")
                            schema_sql.append(",\n".join(columns))
                            schema_sql.append(");")

                    except Exception as e:
                        schema_sql.append(f"-- Error processing table {table}: {str(e)}")
                        print(f"处理PostgreSQL表 {table} 时出错: {str(e)}")

                schema_sql.append("")

            # 写入文件
            content = '\n'.join(schema_sql)
            if compress:
                with gzip.open(filepath, 'wt', encoding='utf-8') as f:
                    f.write(content)
            else:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)

            if own_connection and hasattr(connection, 'close'):
                connection.close()

            file_size = os.path.getsize(filepath)
            print(f"数据库结构备份完成: {filepath} ({file_size} 字节)")
            return filepath

        except Exception as e:
            print(f"数据库结构备份错误: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def backup_data(self, filepath=None, compress=False, batch_size=1000):
        """
        备份数据库数据

        Args:
            filepath: 备份文件路径，如果为None则自动生成
            compress: 是否压缩备份文件
            batch_size: 每批处理的记录数（用于大表）

        Returns:
            str: 备份文件路径
        """
        if filepath is None:
            timestamp = _get_timestamp()
            filename = f"data_backup_{timestamp}.sql"
            filepath = os.path.join(self.backup_dir, filename)

        if compress and not filepath.endswith('.gz'):
            filepath += '.gz'

        try:
            print(f"开始备份数据库数据: {self.dialect_name}")

            tables = self._get_tables()
            print(f"找到 {len(tables)} 个表需要备份")

            data_sql = [
                "-- Database Data Backup",
                f"-- Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"-- Database dialect: {self.dialect_name}",
                ""
            ]

            total_records = 0

            # 使用适当的方式获取连接
            if hasattr(self.db, 'connect') or hasattr(self.db, 'connection') or hasattr(self.db, 'bind'):
                connection = self._get_connection()
                own_connection = True
            else:
                # 如果db本身就是连接对象
                connection = self.db
                own_connection = False

            for table_name in tables:
                print(f"备份表数据: {table_name}")

                # 验证表名是否合法（防止SQL注入）
                if not self._is_valid_table_name(table_name):
                    print(f"警告: 表名包含非法字符: {table_name}")
                    data_sql.append(f"-- Warning: Invalid table name: {table_name}")
                    data_sql.append("")
                    continue

                # 检查表是否存在 - 使用参数化查询
                try:
                    if self.dialect_name == 'sqlite':
                        table_exists_result = connection.execute(
                            text("SELECT name FROM sqlite_master WHERE type='table' AND name = :table_name"),
                            {"table_name": table_name}
                        )
                        if not table_exists_result.fetchone():
                            print(f"警告: 表 {table_name} 不存在，跳过备份")
                            data_sql.append(f"-- Warning: Table {table_name} does not exist, skipped")
                            data_sql.append("")
                            continue
                    elif self.dialect_name == 'postgresql':
                        table_exists_result = connection.execute(
                            text(
                                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = :table_name)"),
                            {"table_name": table_name}
                        )
                        if not table_exists_result.fetchone()[0]:
                            print(f"警告: 表 {table_name} 不存在，跳过备份")
                            data_sql.append(f"-- Warning: Table {table_name} does not exist, skipped")
                            data_sql.append("")
                            continue
                except Exception as e:
                    print(f"检查表 {table_name} 是否存在时出错: {str(e)}")
                    data_sql.append(f"-- Error checking existence of table {table_name}: {str(e)}")
                    data_sql.append("")
                    continue

                # 获取表的列信息 - 使用参数化查询
                columns_info = []
                if self.dialect_name == 'sqlite':
                    result = connection.execute(
                        text("PRAGMA table_info(:table_name)"),
                        {"table_name": table_name}
                    )
                    columns_info = [{'name': row[1], 'type': row[2]} for row in result]
                elif self.dialect_name == 'postgresql':
                    try:
                        result = connection.execute(
                            text("SELECT column_name, data_type FROM information_schema.columns "
                                 "WHERE table_name = :table_name ORDER BY ordinal_position"),
                            {"table_name": table_name}
                        )
                        columns_info = [{'name': row[0], 'type': row[1]} for row in result]
                    except Exception as e:
                        print(f"获取表 {table_name} 的列信息时出错: {str(e)}")
                        data_sql.append(f"-- Error getting column info for table {table_name}: {str(e)}")
                        data_sql.append("")
                        continue

                # 执行查询获取数据 - 由于SQLAlchemy不支持动态表名参数化，我们验证表名后拼接
                # 但这是安全的，因为我们已经验证了表名
                try:
                    # 验证过的表名可以直接拼接，但仍需要小心
                    result = connection.execute(text(f"SELECT * FROM {table_name}"))
                    rows = result.fetchall()
                except Exception as e:
                    print(f"查询表 {table_name} 时出错: {str(e)}")
                    data_sql.append(f"-- Error querying table {table_name}: {str(e)}")
                    data_sql.append("")
                    continue

                if not rows:
                    data_sql.append(f"-- Table {table_name} is empty")
                    data_sql.append("")
                    continue

                # 生成INSERT语句
                table_records = 0
                columns = [col['name'] for col in columns_info] if columns_info else list(rows[0]._mapping.keys())

                for row in rows:
                    values = [self._format_value(value) for value in row]
                    insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(values)});"
                    data_sql.append(insert_sql)
                    total_records += 1
                    table_records += 1

                data_sql.append(f"-- {table_records} records from {table_name}")
                data_sql.append("")
                print(f"已备份 {table_records} 条记录从 {table_name}")

            # 添加摘要信息
            data_sql.append(f"-- Backup completed: {total_records} total records")

            # 写入文件
            content = '\n'.join(data_sql)
            if compress:
                with gzip.open(filepath, 'wt', encoding='utf-8') as f:
                    f.write(content)
            else:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)

            if own_connection and hasattr(connection, 'close'):
                connection.close()

            file_size = os.path.getsize(filepath)
            print(f"数据库数据备份完成: {filepath} ({file_size} 字节, {total_records} 条记录)")
            return filepath

        except Exception as e:
            print(f"数据库数据备份错误: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def backup_all(self, filepath=None, clean_temp_files=True):
        """
        备份整个数据库（结构和数据），并合并到单个文件后压缩为zip

        Args:
            filepath: 备份文件路径，如果为None则自动生成
            clean_temp_files: 是否清理临时文件

        Returns:
            dict: 包含备份文件路径的字典
        """
        timestamp = _get_timestamp()

        # 分别备份结构和数据
        schema_file = self.backup_schema(
            filepath=os.path.join(self.backup_dir, f"schema_backup_{timestamp}.sql"),
            compress=False
        )
        if not schema_file:
            return None

        data_file = self.backup_data(
            filepath=os.path.join(self.backup_dir, f"data_backup_{timestamp}.sql"),
            compress=False
        )
        if not data_file:
            return None

        # 合并文件到zip
        try:
            if filepath is None:
                filepath = os.path.join(self.backup_dir, f"full_backup_{timestamp}.zip")

            with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 添加结构文件到zip
                zipf.write(schema_file, os.path.basename(schema_file))
                # 添加数据文件到zip
                zipf.write(data_file, os.path.basename(data_file))

            if clean_temp_files:
                # 删除临时文件
                os.remove(schema_file)
                os.remove(data_file)

            file_size = os.path.getsize(filepath)
            print(f"完整数据库备份完成: {filepath} ({file_size} 字节)")

            return {
                'full': filepath,
                'timestamp': timestamp
            }

        except Exception as e:
            print(f"合并备份文件时出错: {str(e)}")
            return None

    def list_backups(self):
        """列出所有备份文件"""
        if not os.path.exists(self.backup_dir):
            return []

        backups = []
        for filename in os.listdir(self.backup_dir):
            if filename.endswith(('.sql', '.zip', '.gz')):
                filepath = os.path.join(self.backup_dir, filename)
                stat = os.stat(filepath)
                backups.append({
                    'name': filename,
                    'path': filepath,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime)
                })

        # 按修改时间排序
        backups.sort(key=lambda x: x['modified'], reverse=True)
        return backups


# FastAPI专用的数据库备份类
class FastAPIDatabaseBackup:
    """专门为FastAPI设计的数据库备份工具类"""

    def __init__(self, session, engine, backup_dir="backups"):
        """
        初始化备份工具

        Args:
            session: FastAPI的SQLAlchemy数据库会话
            engine: FastAPI的SQLAlchemy数据库引擎
            backup_dir: 备份文件存储目录
        """
        self.session = session
        self.engine = engine
        self.backup_dir = backup_dir
        self._ensure_backup_dir()

        # 获取数据库方言
        self.dialect_name = engine.dialect.name

    def _ensure_backup_dir(self):
        """确保备份目录存在"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

    def _get_tables(self):
        """获取需要备份的表列表"""
        # 从FastAPI的数据库模型中获取表名
        from utils.database.main import Base
        all_tables = list(Base.metadata.tables.keys())

        # 过滤掉系统表
        exclude_tables = ['alembic_version', 'sqlite_sequence']
        tables_to_backup = [table for table in all_tables if table not in exclude_tables]

        return tables_to_backup

    def _format_value(self, value, column_type=None):
        """格式化数据库值用于SQL语句"""
        if value is None:
            return "NULL"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, bool):
            if self.dialect_name == 'sqlite':
                return "1" if value else "0"
            else:
                return "TRUE" if value else "FALSE"
        elif isinstance(value, (datetime, date)):
            return f"'{value.isoformat()}'"
        else:
            escaped = str(value).replace("'", "''")
            return f"'{escaped}'"

    def backup_schema(self, filepath=None, compress=False):
        """
        备份数据库结构

        Args:
            filepath: 备份文件路径，如果为None则自动生成
            compress: 是否压缩备份文件

        Returns:
            str: 备份文件路径
        """
        if filepath is None:
            timestamp = _get_timestamp()
            filename = f"schema_backup_{timestamp}.sql"
            filepath = os.path.join(self.backup_dir, filename)

        if compress and not filepath.endswith('.gz'):
            filepath += '.gz'

        try:
            print(f"开始备份数据库结构: {self.dialect_name}")

            tables = self._get_tables()
            print(f"找到 {len(tables)} 个表需要备份")

            schema_sql = ["-- FastAPI Database Schema Backup",
                          f"-- Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                          f"-- Database dialect: {self.dialect_name}", ""]

            # 使用引擎连接进行备份
            with self.engine.connect() as connection:
                for table in tables:
                    print(f"处理表结构: {table}")

                    # 检查表是否存在 - 使用参数化查询
                    try:
                        if self.dialect_name == 'sqlite':
                            # SQLite 使用参数化查询
                            table_exists_result = connection.execute(
                                text("SELECT name FROM sqlite_master WHERE type='table' AND name = :table_name"),
                                {"table_name": table}
                            )
                            if not table_exists_result.fetchone():
                                print(f"警告: 表 {table} 不存在，跳过备份")
                                schema_sql.append(f"-- Warning: Table {table} does not exist, skipped")
                                schema_sql.append("")
                                continue
                        elif self.dialect_name == 'postgresql':
                            # PostgreSQL 使用参数化查询
                            table_exists_result = connection.execute(
                                text(
                                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = :table_name)"),
                                {"table_name": table}
                            )
                            if not table_exists_result.fetchone()[0]:
                                print(f"警告: 表 {table} 不存在，跳过备份")
                                schema_sql.append(f"-- Warning: Table {table} does not exist, skipped")
                                schema_sql.append("")
                                continue
                    except Exception as e:
                        print(f"检查表 {table} 是否存在时出错: {str(e)}")
                        schema_sql.append(f"-- Error checking existence of table {table}: {str(e)}")
                        schema_sql.append("")
                        continue

                    if self.dialect_name == 'sqlite':
                        # SQLite 获取表结构 - 使用参数化查询
                        try:
                            create_table_result = connection.execute(
                                text("SELECT sql FROM sqlite_master WHERE type='table' AND name = :table_name"),
                                {"table_name": table}
                            )
                            create_row = create_table_result.fetchone()
                            if create_row and create_row[0]:
                                create_sql = create_row[0]
                                schema_sql.append(create_sql + ";")
                            else:
                                schema_sql.append(f"-- Table {table} not found in sqlite_master")

                            # 获取索引 - 使用参数化查询
                            indexes_result = connection.execute(
                                text(
                                    "SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name = :table_name AND sql IS NOT NULL"),
                                {"table_name": table}
                            )
                            for row in indexes_result:
                                if row[0]:
                                    schema_sql.append(row[0] + ";")

                        except Exception as e:
                            schema_sql.append(f"-- Error processing table {table}: {str(e)}")
                            print(f"处理SQLite表 {table} 时出错: {str(e)}")

                    elif self.dialect_name == 'postgresql':
                        # PostgreSQL 获取表结构 - 使用参数化查询
                        try:
                            create_table_result = connection.execute(
                                text("SELECT column_name, data_type, is_nullable, column_default "
                                     "FROM information_schema.columns WHERE table_name = :table_name "
                                     "ORDER BY ordinal_position"),
                                {"table_name": table}
                            )

                            columns = []
                            for row in create_table_result:
                                col_def = f"{row[0]} {row[1]}"
                                if row[2] == 'NO':
                                    col_def += " NOT NULL"
                                if row[3]:
                                    col_def += f" DEFAULT {row[3]}"
                                columns.append(col_def)

                            if columns:
                                schema_sql.append(f"CREATE TABLE {table} (")
                                schema_sql.append(",\n".join(columns))
                                schema_sql.append(");")

                        except Exception as e:
                            schema_sql.append(f"-- Error processing table {table}: {str(e)}")
                            print(f"处理PostgreSQL表 {table} 时出错: {str(e)}")

                    schema_sql.append("")

            # 写入文件
            content = '\n'.join(schema_sql)
            if compress:
                with gzip.open(filepath, 'wt', encoding='utf-8') as f:
                    f.write(content)
            else:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)

            file_size = os.path.getsize(filepath)
            print(f"FastAPI数据库结构备份完成: {filepath} ({file_size} 字节)")
            return filepath

        except Exception as e:
            print(f"FastAPI数据库结构备份错误: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def backup_data(self, filepath=None, compress=False, batch_size=1000):
        """
        备份数据库数据

        Args:
            filepath: 备份文件路径，如果为None则自动生成
            compress: 是否压缩备份文件
            batch_size: 每批处理的记录数（用于大表）

        Returns:
            str: 备份文件路径
        """
        if filepath is None:
            timestamp = _get_timestamp()
            filename = f"data_backup_{timestamp}.sql"
            filepath = os.path.join(self.backup_dir, filename)

        if compress and not filepath.endswith('.gz'):
            filepath += '.gz'

        try:
            print(f"开始备份数据库数据: {self.dialect_name}")

            tables = self._get_tables()
            print(f"找到 {len(tables)} 个表需要备份")

            data_sql = [
                "-- FastAPI Database Data Backup",
                f"-- Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"-- Database dialect: {self.dialect_name}",
                ""
            ]

            total_records = 0

            # 使用引擎连接进行备份
            with self.engine.connect() as connection:
                for table_name in tables:
                    print(f"备份表数据: {table_name}")

                    # 检查表是否存在 - 使用参数化查询
                    try:
                        if self.dialect_name == 'sqlite':
                            table_exists_result = connection.execute(
                                text("SELECT name FROM sqlite_master WHERE type='table' AND name = :table_name"),
                                {"table_name": table_name}
                            )
                            if not table_exists_result.fetchone():
                                print(f"警告: 表 {table_name} 不存在，跳过备份")
                                data_sql.append(f"-- Warning: Table {table_name} does not exist, skipped")
                                data_sql.append("")
                                continue
                        elif self.dialect_name == 'postgresql':
                            table_exists_result = connection.execute(
                                text(
                                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = :table_name)"),
                                {"table_name": table_name}
                            )
                            if not table_exists_result.fetchone()[0]:
                                print(f"警告: 表 {table_name} 不存在，跳过备份")
                                data_sql.append(f"-- Warning: Table {table_name} does not exist, skipped")
                                data_sql.append("")
                                continue
                    except Exception as e:
                        print(f"检查表 {table_name} 是否存在时出错: {str(e)}")
                        data_sql.append(f"-- Error checking existence of table {table_name}: {str(e)}")
                        data_sql.append("")
                        continue

                    # 获取表的列信息 - 使用参数化查询
                    columns_info = []
                    if self.dialect_name == 'sqlite':
                        result = connection.execute(
                            text("PRAGMA table_info(:table_name)"),
                            {"table_name": table_name}
                        )
                        columns_info = [{'name': row[1], 'type': row[2]} for row in result]
                    elif self.dialect_name == 'postgresql':
                        try:
                            result = connection.execute(
                                text("SELECT column_name, data_type FROM information_schema.columns "
                                     "WHERE table_name = :table_name ORDER BY ordinal_position"),
                                {"table_name": table_name}
                            )
                            columns_info = [{'name': row[0], 'type': row[1]} for row in result]
                        except Exception as e:
                            print(f"获取表 {table_name} 的列信息时出错: {str(e)}")
                            data_sql.append(f"-- Error getting column info for table {table_name}: {str(e)}")
                            data_sql.append("")
                            continue

                    # 执行查询获取数据
                    try:
                        result = connection.execute(text(f"SELECT * FROM {table_name}"))
                        rows = result.fetchall()
                    except Exception as e:
                        print(f"查询表 {table_name} 时出错: {str(e)}")
                        data_sql.append(f"-- Error querying table {table_name}: {str(e)}")
                        data_sql.append("")
                        continue

                    if not rows:
                        data_sql.append(f"-- Table {table_name} is empty")
                        data_sql.append("")
                        continue

                    # 生成INSERT语句
                    table_records = 0
                    columns = [col['name'] for col in columns_info] if columns_info else list(rows[0]._mapping.keys())

                    for row in rows:
                        values = [self._format_value(value) for value in row]
                        insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(values)});"
                        data_sql.append(insert_sql)
                        total_records += 1
                        table_records += 1

                    data_sql.append(f"-- {table_records} records from {table_name}")
                    data_sql.append("")
                    print(f"已备份 {table_records} 条记录从 {table_name}")

            # 添加摘要信息
            data_sql.append(f"-- Backup completed: {total_records} total records")

            # 写入文件
            content = '\n'.join(data_sql)
            if compress:
                with gzip.open(filepath, 'wt', encoding='utf-8') as f:
                    f.write(content)
            else:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)

            file_size = os.path.getsize(filepath)
            print(f"FastAPI数据库数据备份完成: {filepath} ({file_size} 字节, {total_records} 条记录)")
            return filepath

        except Exception as e:
            print(f"FastAPI数据库数据备份错误: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def backup_all(self, filepath=None, clean_temp_files=True):
        """
        备份整个数据库（结构和数据），并合并到单个文件后压缩为zip

        Args:
            filepath: 备份文件路径，如果为None则自动生成
            clean_temp_files: 是否清理临时文件

        Returns:
            dict: 包含备份文件路径的字典
        """
        timestamp = _get_timestamp()

        # 分别备份结构和数据
        schema_file = self.backup_schema(
            filepath=os.path.join(self.backup_dir, f"schema_backup_{timestamp}.sql"),
            compress=False
        )
        if not schema_file:
            return None

        data_file = self.backup_data(
            filepath=os.path.join(self.backup_dir, f"data_backup_{timestamp}.sql"),
            compress=False
        )
        if not data_file:
            return None

        # 合并文件到zip
        try:
            if filepath is None:
                filepath = os.path.join(self.backup_dir, f"full_backup_{timestamp}.zip")

            with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 添加结构文件到zip
                zipf.write(schema_file, os.path.basename(schema_file))
                # 添加数据文件到zip
                zipf.write(data_file, os.path.basename(data_file))

            if clean_temp_files:
                # 删除临时文件
                os.remove(schema_file)
                os.remove(data_file)

            file_size = os.path.getsize(filepath)
            print(f"FastAPI完整数据库备份完成: {filepath} ({file_size} 字节)")

            return {
                'full': filepath,
                'timestamp': timestamp
            }

        except Exception as e:
            print(f"FastAPI合并备份文件时出错: {str(e)}")
            return None

    def list_backups(self):
        """列出所有备份文件"""
        if not os.path.exists(self.backup_dir):
            return []

        backups = []
        for filename in os.listdir(self.backup_dir):
            if filename.endswith(('.sql', '.zip', '.gz')):
                filepath = os.path.join(self.backup_dir, filename)
                stat = os.stat(filepath)
                backups.append({
                    'name': filename,
                    'path': filepath,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime)
                })

        # 按修改时间排序
        backups.sort(key=lambda x: x['modified'], reverse=True)
        return backups


# 基于SQLAlchemy反射的数据库备份类
class SQLAlchemyBackup:
    """基于SQLAlchemy反射机制的数据库备份工具类"""

    def __init__(self, engine, backup_dir="backups"):
        """
        初始化备份工具

        Args:
            engine: FastAPI的SQLAlchemy数据库引擎
            backup_dir: 备份文件存储目录
        """
        self.engine = engine
        self.backup_dir = backup_dir
        self._ensure_backup_dir()

        # 获取数据库方言
        self.dialect_name = engine.dialect.name

    def _ensure_backup_dir(self):
        """确保备份目录存在"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

    def _format_value(self, value, column_type=None):
        """格式化数据库值用于SQL语句"""
        if value is None:
            return "NULL"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, bool):
            if self.dialect_name == 'sqlite':
                return "1" if value else "0"
            else:
                return "TRUE" if value else "FALSE"
        elif isinstance(value, (datetime, date)):
            return f"'{value.isoformat()}'"
        else:
            escaped = str(value).replace("'", "''")
            return f"'{escaped}'"

    def backup_schema(self, filepath=None, compress=False):
        """
        使用SQLAlchemy反射备份数据库结构

        Args:
            filepath: 备份文件路径，如果为None则自动生成
            compress: 是否压缩备份文件

        Returns:
            str: 备份文件路径
        """
        if filepath is None:
            timestamp = _get_timestamp()
            filename = f"schema_backup_{timestamp}.sql"
            filepath = os.path.join(self.backup_dir, filename)

        if compress and not filepath.endswith('.gz'):
            filepath += '.gz'

        try:
            print(f"开始使用SQLAlchemy反射备份数据库结构: {self.dialect_name}")

            from sqlalchemy import inspect
            insp = inspect(self.engine)
            table_names = insp.get_table_names()

            print(f"找到 {len(table_names)} 个表需要备份")

            schema_sql = ["-- SQLAlchemy Reflected Database Schema Backup",
                          f"-- Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                          f"-- Database dialect: {self.dialect_name}", ""]

            for table_name in table_names:
                print(f"处理表结构: {table_name}")

                # 跳过系统表
                if table_name in ['alembic_version', 'sqlite_sequence']:
                    print(f"跳过系统表: {table_name}")
                    continue

                # 获取表的列信息
                columns = insp.get_columns(table_name)

                # 获取主键信息
                primary_keys = insp.get_pk_constraint(table_name)

                # 获取外键信息
                foreign_keys = insp.get_foreign_keys(table_name)

                # 获取索引信息
                indexes = insp.get_indexes(table_name)

                # 构建CREATE TABLE语句
                table_def_parts = [f"CREATE TABLE {table_name} ("]

                for col in columns:
                    col_def = f"  {col['name']} {col['type']}"
                    if col['nullable'] is False:
                        col_def += " NOT NULL"
                    if col.get('default') is not None:
                        col_def += f" DEFAULT {col['default']}"
                    table_def_parts.append(f"  {col_def},")

                # 添加主键约束
                if primary_keys and primary_keys.get('constrained_columns'):
                    pk_cols = ', '.join(primary_keys['constrained_columns'])
                    table_def_parts.append(f"  PRIMARY KEY ({pk_cols}),")

                # 移除最后一个逗号并添加结束括号
                if table_def_parts[-1].endswith(','):
                    table_def_parts[-1] = table_def_parts[-1][:-1]
                table_def_parts.append(");")

                schema_sql.extend(table_def_parts)
                schema_sql.append("")  # 空行分隔

                # 添加索引
                for idx in indexes:
                    idx_name = idx['name']
                    idx_cols = ', '.join(idx['column_names'])
                    unique = "UNIQUE " if idx.get('unique') else ""
                    schema_sql.append(f"CREATE {unique}INDEX {idx_name} ON {table_name} ({idx_cols});")

                schema_sql.append("")  # 空行分隔

            # 写入文件
            content = '\n'.join(schema_sql)
            if compress:
                with gzip.open(filepath, 'wt', encoding='utf-8') as f:
                    f.write(content)
            else:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)

            file_size = os.path.getsize(filepath)
            print(f"SQLAlchemy反射数据库结构备份完成: {filepath} ({file_size} 字节)")
            return filepath

        except Exception as e:
            print(f"SQLAlchemy反射数据库结构备份错误: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def backup_data(self, filepath=None, compress=False, batch_size=1000):
        """
        使用SQLAlchemy反射备份数据库数据

        Args:
            filepath: 备份文件路径，如果为None则自动生成
            compress: 是否压缩备份文件
            batch_size: 每批处理的记录数（用于大表）

        Returns:
            str: 备份文件路径
        """
        if filepath is None:
            timestamp = _get_timestamp()
            filename = f"data_backup_{timestamp}.sql"
            filepath = os.path.join(self.backup_dir, filename)

        if compress and not filepath.endswith('.gz'):
            filepath += '.gz'

        try:
            print(f"开始使用SQLAlchemy反射备份数据库数据: {self.dialect_name}")

            from sqlalchemy import inspect, text
            insp = inspect(self.engine)
            table_names = insp.get_table_names()

            print(f"找到 {len(table_names)} 个表需要备份")

            data_sql = [
                "-- SQLAlchemy Reflected Database Data Backup",
                f"-- Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"-- Database dialect: {self.dialect_name}",
                ""
            ]

            total_records = 0

            for table_name in table_names:
                print(f"备份表数据: {table_name}")

                # 跳过系统表
                if table_name in ['alembic_version', 'sqlite_sequence']:
                    print(f"跳过系统表: {table_name}")
                    continue

                # 获取表的列信息
                columns = insp.get_columns(table_name)
                column_names = [col['name'] for col in columns]

                # 执行查询获取数据
                try:
                    with self.engine.connect() as connection:
                        result = connection.execute(text(f"SELECT * FROM {table_name}"))
                        rows = result.fetchall()
                except Exception as e:
                    print(f"查询表 {table_name} 时出错: {str(e)}")
                    data_sql.append(f"-- Error querying table {table_name}: {str(e)}")
                    data_sql.append("")
                    continue

                if not rows:
                    data_sql.append(f"-- Table {table_name} is empty")
                    data_sql.append("")
                    continue

                # 生成INSERT语句
                table_records = 0

                for row in rows:
                    values = [self._format_value(value) for value in row]
                    insert_sql = f"INSERT INTO {table_name} ({', '.join(column_names)}) VALUES ({', '.join(values)});"
                    data_sql.append(insert_sql)
                    total_records += 1
                    table_records += 1

                data_sql.append(f"-- {table_records} records from {table_name}")
                data_sql.append("")
                print(f"已备份 {table_records} 条记录从 {table_name}")

            # 添加摘要信息
            data_sql.append(f"-- Backup completed: {total_records} total records")

            # 写入文件
            content = '\n'.join(data_sql)
            if compress:
                with gzip.open(filepath, 'wt', encoding='utf-8') as f:
                    f.write(content)
            else:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)

            file_size = os.path.getsize(filepath)
            print(f"SQLAlchemy反射数据库数据备份完成: {filepath} ({file_size} 字节, {total_records} 条记录)")
            return filepath

        except Exception as e:
            print(f"SQLAlchemy反射数据库数据备份错误: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def backup_all(self, filepath=None, clean_temp_files=True):
        """
        备份整个数据库（结构和数据），并合并到单个文件后压缩为zip

        Args:
            filepath: 备份文件路径，如果为None则自动生成
            clean_temp_files: 是否清理临时文件

        Returns:
            dict: 包含备份文件路径的字典
        """
        timestamp = _get_timestamp()

        # 分别备份结构和数据
        schema_file = self.backup_schema(
            filepath=os.path.join(self.backup_dir, f"schema_backup_{timestamp}.sql"),
            compress=False
        )
        if not schema_file:
            return None

        data_file = self.backup_data(
            filepath=os.path.join(self.backup_dir, f"data_backup_{timestamp}.sql"),
            compress=False
        )
        if not data_file:
            return None

        # 合并文件到zip
        try:
            if filepath is None:
                filepath = os.path.join(self.backup_dir, f"full_backup_{timestamp}.zip")

            with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 添加结构文件到zip
                zipf.write(schema_file, os.path.basename(schema_file))
                # 添加数据文件到zip
                zipf.write(data_file, os.path.basename(data_file))

            if clean_temp_files:
                # 删除临时文件
                os.remove(schema_file)
                os.remove(data_file)

            file_size = os.path.getsize(filepath)
            print(f"SQLAlchemy反射完整数据库备份完成: {filepath} ({file_size} 字节)")

            return {
                'full': filepath,
                'timestamp': timestamp
            }

        except Exception as e:
            print(f"SQLAlchemy反射合并备份文件时出错: {str(e)}")
            return None

    def list_backups(self):
        """列出所有备份文件"""
        if not os.path.exists(self.backup_dir):
            return []

        backups = []
        for filename in os.listdir(self.backup_dir):
            if filename.endswith(('.sql', '.zip', '.gz')):
                filepath = os.path.join(self.backup_dir, filename)
                stat = os.stat(filepath)
                backups.append({
                    'name': filename,
                    'path': filepath,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime)
                })

        # 按修改时间排序
        backups.sort(key=lambda x: x['modified'], reverse=True)
        return backups


# 便捷函数
def create_backup_tool(db, backup_dir="backups"):
    """创建备份工具实例的便捷函数"""
    return DatabaseBackup(db, backup_dir)


# 使用示例
if __name__ == "__main__":
    # 假设您已经有一个 Flask-SQLAlchemy 实例
    # from yourapp import db

    # 创建备份工具
    # backup_tool = DatabaseBackup(db, "my_backups")

    # 备份数据库结构
    # schema_file = backup_tool.backup_schema()

    # 备份数据库数据
    # data_file = backup_tool.backup_data()

    # 完整备份（分开文件）
    # result = backup_tool.backup_all(separate_files=True)

    # 完整备份（单个文件）
    # result = backup_tool.backup_all(separate_files=False)

    # 列出所有备份
    # backups = backup_tool.list_backups()

    print("数据库备份工具库已加载")
