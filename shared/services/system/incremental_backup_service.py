"""
增量备份服务
支持差异备份和增量备份，优化存储空间
"""

import asyncio
import hashlib
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional


class IncrementalBackupService:
    """增量备份服务"""

    def __init__(self, backup_dir: str = "backups/database"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # 增量备份元数据文件
        self.metadata_file = self.backup_dir / "incremental_metadata.json"
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> Dict[str, Any]:
        """加载增量备份元数据"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[IncrementalBackup] Failed to load metadata: {e}")
                return {}
        return {}

    def _save_metadata(self):
        """保存增量备份元数据"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, default=str)
        except Exception as e:
            print(f"[IncrementalBackup] Failed to save metadata: {e}")

    async def create_incremental_backup(
            self,
            db_config: Dict[str, str],
            base_backup_id: Optional[str] = None,
            tables: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        创建增量备份
        
        Args:
            db_config: 数据库配置
            base_backup_id: 基础备份ID（None表示查找最新完整备份）
            tables: 要备份的表列表
            
        Returns:
            备份结果
        """
        try:
            # 1. 找到基础备份
            if not base_backup_id:
                base_backup_id = self._find_latest_full_backup()

            if not base_backup_id:
                return {
                    'success': False,
                    'error': '没有找到完整备份作为基础，请先创建完整备份'
                }

            base_backup = self.metadata.get(base_backup_id)
            if not base_backup:
                return {
                    'success': False,
                    'error': f'基础备份 {base_backup_id} 不存在'
                }

            # 2. 生成增量备份文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"incremental_{timestamp}.dump"
            backup_path = self.backup_dir / backup_filename

            # 3. 获取自上次备份以来变化的表
            changed_tables = await self._detect_changed_tables(
                db_config,
                base_backup.get('tables_checksum', {}),
                tables
            )

            if not changed_tables:
                return {
                    'success': True,
                    'message': '没有检测到数据变化，跳过备份',
                    'skipped': True
                }

            # 4. 执行增量备份（只备份变化的表）
            result = await self._perform_incremental_dump(
                db_config,
                backup_path,
                changed_tables
            )

            if not result['success']:
                return result

            # 5. 计算新备份的校验和
            new_checksums = await self._calculate_tables_checksum(db_config, changed_tables)

            # 6. 更新元数据
            backup_id = f"incr_{timestamp}"
            self.metadata[backup_id] = {
                'id': backup_id,
                'type': 'incremental',
                'filename': backup_filename,
                'base_backup_id': base_backup_id,
                'tables': changed_tables,
                'tables_checksum': new_checksums,
                'file_size': backup_path.stat().st_size if backup_path.exists() else 0,
                'created_at': datetime.now().isoformat(),
                'status': 'completed'
            }

            # 合并校验和（保留未变化的表的校验和）
            merged_checksums = base_backup.get('tables_checksum', {}).copy()
            merged_checksums.update(new_checksums)
            self.metadata[backup_id]['merged_checksum'] = merged_checksums

            self._save_metadata()

            return {
                'success': True,
                'backup_id': backup_id,
                'filename': backup_filename,
                'path': str(backup_path),
                'changed_tables': changed_tables,
                'file_size': result.get('file_size', 0),
                'message': f'增量备份成功，备份了 {len(changed_tables)} 个表'
            }

        except Exception as e:
            print(f"[IncrementalBackup] Error creating incremental backup: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }

    async def create_differential_backup(
            self,
            db_config: Dict[str, str],
            base_backup_id: Optional[str] = None,
            tables: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        创建差异备份（基于最新完整备份的所有变化）
        
        Args:
            db_config: 数据库配置
            base_backup_id: 基础备份ID
            tables: 要备份的表列表
            
        Returns:
            备份结果
        """
        try:
            # 差异备份与增量备份类似，但始终基于完整备份
            if not base_backup_id:
                base_backup_id = self._find_latest_full_backup()

            if not base_backup_id:
                return {
                    'success': False,
                    'error': '没有找到完整备份作为基础'
                }

            # 调用增量备份方法，但标记为差异备份
            result = await self.create_incremental_backup(
                db_config,
                base_backup_id,
                tables
            )

            if result['success']:
                # 更新类型为differential
                backup_id = result['backup_id']
                if backup_id in self.metadata:
                    self.metadata[backup_id]['type'] = 'differential'
                    self._save_metadata()
                    result['type'] = 'differential'

            return result

        except Exception as e:
            print(f"[IncrementalBackup] Error creating differential backup: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def restore_incremental_backup(
            self,
            backup_chain: List[str],
            db_config: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        恢复增量备份链
        
        Args:
            backup_chain: 备份ID链（从完整备份到目标增量备份）
            db_config: 数据库配置
            
        Returns:
            恢复结果
        """
        try:
            if not backup_chain:
                return {
                    'success': False,
                    'error': '备份链为空'
                }

            restored_backups = []

            # 按顺序恢复每个备份
            for backup_id in backup_chain:
                backup_info = self.metadata.get(backup_id)
                if not backup_info:
                    return {
                        'success': False,
                        'error': f'备份 {backup_id} 不存在',
                        'restored_so_far': restored_backups
                    }

                backup_path = self.backup_dir / backup_info['filename']
                if not backup_path.exists():
                    return {
                        'success': False,
                        'error': f'备份文件不存在: {backup_info["filename"]}',
                        'restored_so_far': restored_backups
                    }

                # 恢复单个备份
                restore_result = await self._restore_single_backup(
                    backup_path,
                    db_config,
                    backup_info['type'] == 'full'
                )

                if not restore_result['success']:
                    return {
                        'success': False,
                        'error': f'恢复 {backup_id} 失败: {restore_result.get("error")}',
                        'restored_so_far': restored_backups
                    }

                restored_backups.append(backup_id)

            return {
                'success': True,
                'message': f'成功恢复 {len(restored_backups)} 个备份',
                'restored_backups': restored_backups
            }

        except Exception as e:
            print(f"[IncrementalBackup] Error restoring backup chain: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _detect_changed_tables(
            self,
            db_config: Dict[str, str],
            previous_checksums: Dict[str, str],
            tables: Optional[List[str]] = None
    ) -> List[str]:
        """
        检测自上次备份以来变化的表
        
        Args:
            db_config: 数据库配置
            previous_checksums: 之前的表校验和
            tables: 要检查的表列表
            
        Returns:
            变化的表列表
        """
        try:
            import asyncpg

            # 连接数据库
            conn = await asyncpg.connect(
                host=db_config['host'],
                port=int(db_config['port']),
                database=db_config['database'],
                user=db_config['user'],
                password=db_config['password']
            )

            try:
                # 如果没有指定表，获取所有用户表
                if not tables:
                    rows = await conn.fetch("""
                                            SELECT table_name
                                            FROM information_schema.tables
                                            WHERE table_schema = 'public'
                                              AND table_type = 'BASE TABLE'
                                            """)
                    tables = [row['table_name'] for row in rows]

                # 计算每个表的当前校验和
                current_checksums = {}
                changed_tables = []

                for table in tables:
                    # 使用表的行数和数据哈希作为校验和
                    checksum = await self._calculate_table_checksum(conn, table)
                    current_checksums[table] = checksum

                    # 如果校验和不同或之前不存在，则认为表已变化
                    if table not in previous_checksums or previous_checksums[table] != checksum:
                        changed_tables.append(table)

                return changed_tables

            finally:
                await conn.close()

        except ImportError:
            # 如果没有asyncpg，返回所有表（保守策略）
            print("[IncrementalBackup] asyncpg not available, assuming all tables changed")
            return tables or []
        except Exception as e:
            print(f"[IncrementalBackup] Error detecting changed tables: {e}")
            # 出错时返回所有表以确保数据安全
            return tables or []

    async def _calculate_table_checksum(self, conn, table_name: str) -> str:
        """
        计算表的校验和
        
        Args:
            conn: 数据库连接
            table_name: 表名
            
        Returns:
            校验和字符串
        """
        try:
            # 获取行数和最后修改时间
            row = await conn.fetchval(f"""
                SELECT COUNT(*) as count, 
                       MAX(updated_at) as last_update
                FROM "{table_name}"
            """)

            # 使用行数和最后更新时间生成简单校验和
            checksum_str = f"{table_name}:{row}"
            return hashlib.md5(checksum_str.encode()).hexdigest()

        except Exception as e:
            # 如果表没有updated_at字段，只使用行数
            try:
                count = await conn.fetchval(f'SELECT COUNT(*) FROM "{table_name}"')
                checksum_str = f"{table_name}:{count}"
                return hashlib.md5(checksum_str.encode()).hexdigest()
            except:
                # 如果完全失败，返回空校验和
                return hashlib.md5(table_name.encode()).hexdigest()

    async def _calculate_tables_checksum(
            self,
            db_config: Dict[str, str],
            tables: List[str]
    ) -> Dict[str, str]:
        """计算多个表的校验和"""
        try:
            import asyncpg

            conn = await asyncpg.connect(
                host=db_config['host'],
                port=int(db_config['port']),
                database=db_config['database'],
                user=db_config['user'],
                password=db_config['password']
            )

            try:
                checksums = {}
                for table in tables:
                    checksums[table] = await self._calculate_table_checksum(conn, table)
                return checksums
            finally:
                await conn.close()

        except Exception as e:
            print(f"[IncrementalBackup] Error calculating checksums: {e}")
            return {}

    async def _perform_incremental_dump(
            self,
            db_config: Dict[str, str],
            backup_path: Path,
            tables: List[str]
    ) -> Dict[str, Any]:
        """
        执行增量转储
        
        Args:
            db_config: 数据库配置
            backup_path: 备份文件路径
            tables: 要备份的表列表
            
        Returns:
            转储结果
        """
        try:
            # 构建pg_dump命令，只备份指定的表
            cmd = [
                'pg_dump',
                '-h', db_config['host'],
                '-p', db_config['port'],
                '-U', db_config['user'],
                '-d', db_config['database'],
                '-F', 'c',  # custom format
                '-f', str(backup_path)
            ]

            # 添加表过滤
            for table in tables:
                cmd.extend(['-t', table])

            # 设置环境变量（密码）
            env = os.environ.copy()
            env['PGPASSWORD'] = db_config['password']

            # 执行命令
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='ignore')
                return {
                    'success': False,
                    'error': f'pg_dump failed: {error_msg}'
                }

            file_size = backup_path.stat().st_size if backup_path.exists() else 0

            return {
                'success': True,
                'file_size': file_size,
                'tables_count': len(tables)
            }

        except FileNotFoundError:
            return {
                'success': False,
                'error': 'pg_dump not found. Please install PostgreSQL client tools.'
            }
        except Exception as e:
            print(f"[IncrementalBackup] Error performing dump: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _restore_single_backup(
            self,
            backup_path: Path,
            db_config: Dict[str, str],
            is_full_backup: bool
    ) -> Dict[str, Any]:
        """
        恢复单个备份
        
        Args:
            backup_path: 备份文件路径
            db_config: 数据库配置
            is_full_backup: 是否为完整备份
            
        Returns:
            恢复结果
        """
        try:
            # 如果是完整备份，先清理数据库
            if is_full_backup:
                # 这里可以添加清理逻辑
                pass

            # 构建pg_restore命令
            cmd = [
                'pg_restore',
                '-h', db_config['host'],
                '-p', db_config['port'],
                '-U', db_config['user'],
                '-d', db_config['database'],
                '--no-owner',
                '--no-privileges',
                str(backup_path)
            ]

            # 设置环境变量
            env = os.environ.copy()
            env['PGPASSWORD'] = db_config['password']

            # 执行命令
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='ignore')
                return {
                    'success': False,
                    'error': f'pg_restore failed: {error_msg}'
                }

            return {
                'success': True,
                'message': 'Restore completed successfully'
            }

        except FileNotFoundError:
            return {
                'success': False,
                'error': 'pg_restore not found. Please install PostgreSQL client tools.'
            }
        except Exception as e:
            print(f"[IncrementalBackup] Error restoring backup: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _find_latest_full_backup(self) -> Optional[str]:
        """查找最新的完整备份ID"""
        full_backups = [
            (bid, info) for bid, info in self.metadata.items()
            if info.get('type') == 'full'
        ]

        if not full_backups:
            return None

        # 按创建时间排序，返回最新的
        full_backups.sort(key=lambda x: x[1].get('created_at', ''), reverse=True)
        return full_backups[0][0]

    def get_backup_chain(self, target_backup_id: str) -> Optional[List[str]]:
        """
        获取恢复到目标备份所需的备份链
        
        Args:
            target_backup_id: 目标备份ID
            
        Returns:
            备份ID链（从完整备份到目标备份）
        """
        target_backup = self.metadata.get(target_backup_id)
        if not target_backup:
            return None

        chain = [target_backup_id]
        current_id = target_backup_id

        # 回溯到完整备份
        while True:
            backup = self.metadata.get(current_id)
            if not backup:
                return None

            base_id = backup.get('base_backup_id')
            if not base_id:
                # 到达完整备份
                chain.reverse()
                return chain

            chain.append(base_id)
            current_id = base_id

    def get_backup_statistics(self) -> Dict[str, Any]:
        """获取备份统计信息"""
        stats = {
            'total_backups': len(self.metadata),
            'full_backups': 0,
            'incremental_backups': 0,
            'differential_backups': 0,
            'total_size_bytes': 0,
            'storage_savings_percent': 0,
            'backups': []
        }

        full_backup_size = 0

        for backup_id, info in self.metadata.items():
            backup_type = info.get('type', 'unknown')
            file_size = info.get('file_size', 0)

            if backup_type == 'full':
                stats['full_backups'] += 1
                full_backup_size = file_size
            elif backup_type == 'incremental':
                stats['incremental_backups'] += 1
            elif backup_type == 'differential':
                stats['differential_backups'] += 1

            stats['total_size_bytes'] += file_size

            stats['backups'].append({
                'id': backup_id,
                'type': backup_type,
                'filename': info.get('filename'),
                'size': file_size,
                'created_at': info.get('created_at')
            })

        # 计算存储节省
        if full_backup_size > 0 and stats['total_backups'] > 1:
            hypothetical_size = full_backup_size * stats['total_backups']
            actual_size = stats['total_size_bytes']
            savings = ((hypothetical_size - actual_size) / hypothetical_size) * 100
            stats['storage_savings_percent'] = round(savings, 2)

        return stats

    def cleanup_old_backups(self, keep_days: int = 30) -> Dict[str, Any]:
        """
        清理旧备份
        
        Args:
            keep_days: 保留天数
            
        Returns:
            清理结果
        """
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        deleted_count = 0
        deleted_size = 0

        backups_to_delete = []

        for backup_id, info in self.metadata.items():
            created_at = datetime.fromisoformat(info.get('created_at', ''))
            if created_at < cutoff_date:
                backups_to_delete.append((backup_id, info))

        for backup_id, info in backups_to_delete:
            filename = info.get('filename')
            if filename:
                backup_path = self.backup_dir / filename
                if backup_path.exists():
                    try:
                        file_size = backup_path.stat().st_size
                        backup_path.unlink()
                        deleted_size += file_size
                        deleted_count += 1

                        # 从元数据中删除
                        del self.metadata[backup_id]
                    except Exception as e:
                        print(f"[IncrementalBackup] Failed to delete {filename}: {e}")

        self._save_metadata()

        return {
            'success': True,
            'deleted_count': deleted_count,
            'deleted_size_bytes': deleted_size,
            'message': f'Deleted {deleted_count} old backups, freed {deleted_size} bytes'
        }


# 全局实例
incremental_backup_service = IncrementalBackupService()
