"""
数据库 URL 替换服务
用于网站迁移时批量替换数据库中的URL
类似 WordPress 的 Search Replace DB 工具
"""

import re
from typing import Dict, List, Any, Optional

from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import AsyncSession


class DatabaseURLReplacer:
    """
    数据库 URL 替换服务
    
    功能:
    1. 序列化搜索和替换（处理PHP序列化数据）
    2. 正则表达式支持
    3. 预览模式（不实际执行替换）
    4. 按表/字段过滤
    5. 事务支持和回滚
    6. 详细的替换报告
    """

    def __init__(self):
        self.replacement_log = []

    async def search_replace(
            self,
            db: AsyncSession,
            search: str,
            replace: str,
            tables: Optional[List[str]] = None,
            exclude_tables: Optional[List[str]] = None,
            use_regex: bool = False,
            dry_run: bool = True,
            case_sensitive: bool = True,
            progress_callback=None
    ) -> Dict[str, Any]:
        """
        在数据库中搜索并替换URL
        
        Args:
            db: 数据库会话
            search: 搜索字符串或正则表达式
            replace: 替换字符串
            tables: 要处理的表列表（None表示所有表）
            exclude_tables: 排除的表列表
            use_regex: 是否使用正则表达式
            dry_run: 是否为预览模式（不实际执行）
            case_sensitive: 是否区分大小写
            progress_callback: 进度回调函数
            
        Returns:
            替换结果报告
        """
        try:
            # 1. 获取所有需要处理的表
            inspector = inspect(db.bind)
            all_tables = inspector.get_table_names()

            # 过滤表
            if tables:
                target_tables = [t for t in tables if t in all_tables]
            elif exclude_tables:
                target_tables = [t for t in all_tables if t not in exclude_tables]
            else:
                # 默认排除系统表
                system_tables = ['alembic_version', 'sqlite_sequence']
                target_tables = [t for t in all_tables if t not in system_tables]

            report = {
                'success': True,
                'dry_run': dry_run,
                'search': search,
                'replace': replace,
                'use_regex': use_regex,
                'tables_processed': 0,
                'total_replacements': 0,
                'table_reports': [],
                'warnings': []
            }

            # 2. 逐个表处理
            for table_name in target_tables:
                if progress_callback:
                    await progress_callback({
                        'type': 'progress',
                        'table': table_name,
                        'message': f'处理表: {table_name}'
                    })

                table_report = await self._process_table(
                    db,
                    table_name,
                    search,
                    replace,
                    use_regex,
                    dry_run,
                    case_sensitive
                )

                report['tables_processed'] += 1
                report['total_replacements'] += table_report['replacements']
                report['table_reports'].append(table_report)

                if table_report['warnings']:
                    report['warnings'].extend(table_report['warnings'])

            # 3. 如果不是预览模式，提交事务
            if not dry_run and report['total_replacements'] > 0:
                await db.commit()
                report['committed'] = True
            elif dry_run:
                await db.rollback()
                report['committed'] = False

            return report

        except Exception as e:
            await db.rollback()
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'dry_run': dry_run
            }

    async def _process_table(
            self,
            db: AsyncSession,
            table_name: str,
            search: str,
            replace: str,
            use_regex: bool,
            dry_run: bool,
            case_sensitive: bool
    ) -> Dict[str, Any]:
        """处理单个表"""
        try:
            # 获取表的列信息
            inspector = inspect(db.bind)
            columns = inspector.get_columns(table_name)

            # 只处理文本类型的列
            text_columns = []
            for col in columns:
                col_type = str(col['type']).lower()
                if any(t in col_type for t in ['varchar', 'text', 'char']):
                    text_columns.append(col['name'])

            if not text_columns:
                return {
                    'table': table_name,
                    'columns_processed': 0,
                    'replacements': 0,
                    'rows_affected': 0,
                    'warnings': []
                }

            table_report = {
                'table': table_name,
                'columns_processed': len(text_columns),
                'replacements': 0,
                'rows_affected': 0,
                'column_details': [],
                'warnings': []
            }

            # 逐列处理
            for col_name in text_columns:
                col_result = await self._process_column(
                    db,
                    table_name,
                    col_name,
                    search,
                    replace,
                    use_regex,
                    dry_run,
                    case_sensitive
                )

                table_report['replacements'] += col_result['replacements']
                table_report['rows_affected'] += col_result['rows_affected']

                if col_result['replacements'] > 0:
                    table_report['column_details'].append({
                        'column': col_name,
                        'replacements': col_result['replacements'],
                        'rows_affected': col_result['rows_affected']
                    })

                if col_result['warnings']:
                    table_report['warnings'].extend(col_result['warnings'])

            return table_report

        except Exception as e:
            return {
                'table': table_name,
                'columns_processed': 0,
                'replacements': 0,
                'rows_affected': 0,
                'warnings': [f'处理表失败: {str(e)}']
            }

    async def _process_column(
            self,
            db: AsyncSession,
            table_name: str,
            column_name: str,
            search: str,
            replace: str,
            use_regex: bool,
            dry_run: bool,
            case_sensitive: bool
    ) -> Dict[str, Any]:
        """处理单个列"""
        try:
            # 构建查询
            if use_regex:
                # PostgreSQL 正则表达式替换
                flags = '' if case_sensitive else 'i'
                query = text(f"""
                    SELECT COUNT(*) as count
                    FROM "{table_name}"
                    WHERE "{column_name}" ~ :pattern
                """)
                params = {'pattern': search}
            else:
                # 普通LIKE查询
                like_pattern = f'%{search}%'
                operator = 'LIKE' if case_sensitive else 'ILIKE'
                query = text(f"""
                    SELECT COUNT(*) as count
                    FROM "{table_name}"
                    WHERE "{column_name}" {operator} :pattern
                """)
                params = {'pattern': like_pattern}

            # 执行查询获取匹配数量
            result = await db.execute(query, params)
            row = result.fetchone()
            match_count = row[0] if row else 0

            if match_count == 0:
                return {
                    'replacements': 0,
                    'rows_affected': 0,
                    'warnings': []
                }

            # 如果不是预览模式，执行替换
            rows_affected = 0
            if not dry_run:
                if use_regex:
                    # PostgreSQL regex replace
                    flags = 'gi' if not case_sensitive else 'g'
                    replace_query = text(f"""
                        UPDATE "{table_name}"
                        SET "{column_name}" = regexp_replace(
                            "{column_name}",
                            :pattern,
                            :replacement,
                            '{flags}'
                        )
                        WHERE "{column_name}" ~ :pattern
                    """)
                else:
                    # 普通替换
                    replace_query = text(f"""
                        UPDATE "{table_name}"
                        SET "{column_name}" = REPLACE("{column_name}", :search, :replace)
                        WHERE "{column_name}" LIKE :pattern
                    """)
                    params = {'search': search, 'replace': replace, 'pattern': like_pattern}

                result = await db.execute(replace_query, params)
                rows_affected = result.rowcount

            return {
                'replacements': match_count,
                'rows_affected': rows_affected if not dry_run else match_count,
                'warnings': []
            }

        except Exception as e:
            return {
                'replacements': 0,
                'rows_affected': 0,
                'warnings': [f'处理列 {column_name} 失败: {str(e)}']
            }

    def serialize_search_replace(self, data: str, search: str, replace: str) -> str:
        """
        处理PHP序列化数据中的URL替换
        
        Args:
            data: 序列化数据字符串
            search: 搜索字符串
            replace: 替换字符串
            
        Returns:
            替换后的数据
        """
        # PHP序列化格式: s:length:"value";
        pattern = r's:(\d+):"([^"]*?)"'

        def replace_callback(match):
            length = int(match.group(1))
            value = match.group(2)

            # 替换值
            new_value = value.replace(search, replace)
            new_length = len(new_value)

            # 如果长度改变，更新长度前缀
            if new_length != length:
                return f's:{new_length}:"{new_value}"'
            return match.group(0)

        return re.sub(pattern, replace_callback, data)

    async def validate_urls(
            self,
            db: AsyncSession,
            old_url: str,
            new_url: str,
            sample_size: int = 10
    ) -> Dict[str, Any]:
        """
        验证URL替换的正确性
        
        Args:
            db: 数据库会话
            old_url: 旧URL
            new_url: 新URL
            sample_size: 采样数量
            
        Returns:
            验证结果
        """
        try:
            # 查找包含旧URL的样本
            query = text("""
                         SELECT table_name, column_name
                         FROM information_schema.columns
                         WHERE table_schema = 'public'
                           AND data_type IN ('character varying', 'text')
                         """)

            result = await db.execute(query)
            columns = result.fetchall()

            samples = []
            for table_name, column_name in columns[:20]:  # 只检查前20个列
                try:
                    sample_query = text(f"""
                        SELECT "{column_name}"
                        FROM "{table_name}"
                        WHERE "{column_name}" LIKE :pattern
                        LIMIT :limit
                    """)

                    sample_result = await db.execute(
                        sample_query,
                        {'pattern': f'%{old_url}%', 'limit': sample_size}
                    )

                    rows = sample_result.fetchall()
                    if rows:
                        samples.append({
                            'table': table_name,
                            'column': column_name,
                            'samples': [row[0][:200] for row in rows[:3]]
                        })
                except:
                    continue

            return {
                'success': True,
                'old_url': old_url,
                'new_url': new_url,
                'samples_found': len(samples),
                'samples': samples
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


# 全局实例
database_url_replacer = DatabaseURLReplacer()
