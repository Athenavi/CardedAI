"""
备份服务核心逻辑
提供本地备份和恢复功能
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession


# 注意: 不要在这里导入 backup_service，会导致循环依赖
# 如需使用，请在方法内部延迟导入


class BackupService:
    """备份恢复服务"""

    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, include_files: bool = True, incremental: bool = False) -> Dict[str, Any]:
        """创建备份"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_type = 'incremental' if incremental else 'full'
            backup_name = f"backup_{backup_type}_{timestamp}"
            backup_path = self.backup_dir / backup_name
            backup_path.mkdir()

            backup_info = {
                'name': backup_name,
                'type': backup_type,
                'created_at': datetime.now().isoformat(),
                'include_files': include_files,
                'size': 0,
                'status': 'completed',
                'tables_backed_up': [],
                'files_backed_up': []
            }

            # 备份插件数据库
            plugins_data_dir = Path('plugins_data')
            if plugins_data_dir.exists():
                db_backup_dir = backup_path / 'plugins_databases'
                db_backup_dir.mkdir()

                for db_file in plugins_data_dir.glob('*.db'):
                    if incremental and not self._file_has_changed(db_file):
                        continue

                    shutil.copy2(db_file, db_backup_dir / db_file.name)
                    backup_info['tables_backed_up'].append(db_file.name)

                    for ext in ['-wal', '-shm']:
                        wal_file = Path(str(db_file) + ext)
                        if wal_file.exists():
                            shutil.copy2(wal_file, db_backup_dir / wal_file.name)

            # 备份主数据库
            main_db = Path('data/blog.db')
            if main_db.exists():
                db_backup_dir = backup_path / 'main_database'
                db_backup_dir.mkdir()
                shutil.copy2(main_db, db_backup_dir / 'blog.db')
                backup_info['tables_backed_up'].append('blog.db')

            # 备份文件
            if include_files:
                media_dir = Path('media')
                if media_dir.exists():
                    files_backup_dir = backup_path / 'media_files'
                    shutil.copytree(media_dir, files_backup_dir)
                    file_count = sum(1 for _ in files_backup_dir.rglob('*') if _.is_file())
                    backup_info['files_backed_up'].append(f'media: {file_count} files')

            # 计算大小并保存元数据
            size = sum(f.stat().st_size for f in backup_path.rglob('*') if f.is_file())
            backup_info['size'] = size

            with open(backup_path / 'metadata.json', 'w') as f:
                json.dump(backup_info, f, indent=2, ensure_ascii=False)

            return {'success': True, 'backup_name': backup_name, 'info': backup_info}
        except Exception as e:
            print(f"[BackupService] Backup failed: {e}")
            return {'success': False, 'error': str(e)}

    def restore_backup(self, backup_name: str, restore_files: bool = True) -> Dict[str, Any]:
        """一键恢复备份"""
        try:
            backup_path = self.backup_dir / backup_name
            if not backup_path.exists():
                return {'success': False, 'error': '备份不存在'}

            metadata_file = backup_path / 'metadata.json'
            metadata = {}
            if metadata_file.exists():
                with open(metadata_file) as f:
                    metadata = json.load(f)

            restored_items = []

            # 恢复插件数据库
            plugins_db_backup = backup_path / 'plugins_databases'
            if plugins_db_backup.exists():
                plugins_data_dir = Path('plugins_data')
                plugins_data_dir.mkdir(exist_ok=True)

                for db_file in plugins_db_backup.glob('*.db'):
                    shutil.copy2(db_file, plugins_data_dir / db_file.name)
                    restored_items.append(f'plugin_db:{db_file.name}')

                    for ext in ['-wal', '-shm']:
                        wal_file = Path(str(db_file) + ext)
                        if wal_file.exists():
                            shutil.copy2(wal_file, plugins_data_dir / wal_file.name)

            # 恢复主数据库
            main_db_backup = backup_path / 'main_database' / 'blog.db'
            if main_db_backup.exists():
                main_db_dir = Path('data')
                main_db_dir.mkdir(exist_ok=True)
                shutil.copy2(main_db_backup, main_db_dir / 'blog.db')
                restored_items.append('main_db:blog.db')

            # 恢复文件
            if restore_files:
                media_backup = backup_path / 'media_files'
                if media_backup.exists():
                    media_dir = Path('media')
                    if media_dir.exists():
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        backup_current = Path(f'media_backup_{timestamp}')
                        shutil.copytree(media_dir, backup_current)
                        shutil.rmtree(media_dir)
                    shutil.copytree(media_backup, media_dir)
                    restored_items.append('media_files')

            return {
                'success': True,
                'message': '恢复成功',
                'metadata': metadata,
                'restored_items': restored_items
            }
        except Exception as e:
            print(f"[BackupService] Restore failed: {e}")
            return {'success': False, 'error': str(e)}

    def list_backups(self) -> List[Dict[str, Any]]:
        """列出所有备份"""
        backups = []
        for backup_dir in self.backup_dir.iterdir():
            if backup_dir.is_dir():
                metadata_file = backup_dir / 'metadata.json'
                if metadata_file.exists():
                    with open(metadata_file) as f:
                        metadata = json.load(f)
                        backups.append(metadata)
        return sorted(backups, key=lambda x: x['created_at'], reverse=True)

    def delete_backup(self, backup_name: str) -> Dict[str, Any]:
        """删除备份"""
        try:
            backup_path = self.backup_dir / backup_name
            if backup_path.exists():
                shutil.rmtree(backup_path)
                return {'success': True}
            return {'success': False, 'error': '备份不存在'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _file_has_changed(self, file_path: Path) -> bool:
        """检查文件是否自上次备份后发生变化"""
        try:
            backups = self.list_backups()
            if not backups:
                return True

            latest_backup = backups[0]
            latest_backup_path = self.backup_dir / latest_backup['name']

            backup_file = None
            for candidate in latest_backup_path.rglob(file_path.name):
                if candidate.is_file():
                    backup_file = candidate
                    break

            if not backup_file:
                return True

            current_stat = file_path.stat()
            backup_stat = backup_file.stat()

            if current_stat.st_size != backup_stat.st_size:
                return True

            if abs(current_stat.st_mtime - backup_stat.st_mtime) > 1:
                return True

            return False
        except Exception as e:
            print(f"[BackupService] Failed to check file changes: {e}")
            return True


# 异步辅助函数
async def create_full_backup(db: AsyncSession) -> Dict[str, Any]:
    """创建完整数据库备份"""
    try:
        from shared.models import Article, Category, User, Pages, Menus, MenuItems, Media

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"backup_{timestamp}.json"
        backup_path = backup_service.backup_dir / backup_filename

        backup_data = {
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'type': 'full',
                'version': '1.0',
            },
            'data': {}
        }

        # 导出各表数据
        for model_name, model in [
            ('articles', Article), ('categories', Category), ('users', User),
            ('pages', Pages), ('menus', Menus), ('menu_items', MenuItems), ('media', Media)
        ]:
            result = await db.execute(select(model))
            items = result.scalars().all()

            if model_name == 'users':
                backup_data['data'][model_name] = [item.to_dict(exclude_sensitive=True) for item in items]
            else:
                backup_data['data'][model_name] = [item.to_dict() for item in items]

        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False, default=str)

        return {
            'success': True,
            'backup_path': str(backup_path),
            'backup_filename': backup_filename,
            'stats': {model_name: len(items) for model_name, _ in [
                ('articles', Article), ('categories', Category), ('users', User),
                ('pages', Pages), ('menus', Menus), ('menu_items', MenuItems), ('media', Media)
            ]}
        }
    except Exception as e:
        print(f"[BackupService] JSON backup failed: {e}")
        return {'success': False, 'error': str(e)}


async def get_backup_list() -> List[Dict[str, Any]]:
    """获取所有备份文件列表"""
    try:
        backups = []
        for backup_file in backup_service.backup_dir.glob('backup_*.json'):
            if backup_file.is_file():
                with open(backup_file, 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                        backups.append({
                            'filename': backup_file.name,
                            'path': str(backup_file),
                            'size': backup_file.stat().st_size,
                            'created_at': data.get('metadata', {}).get('created_at', ''),
                            'type': data.get('metadata', {}).get('type', 'unknown')
                        })
                    except json.JSONDecodeError:
                        backups.append({
                            'filename': backup_file.name,
                            'path': str(backup_file),
                            'size': backup_file.stat().st_size,
                            'created_at': '',
                            'type': 'corrupted'
                        })

        return sorted(backups, key=lambda x: x.get('created_at', ''), reverse=True)
    except Exception:
        return []


async def restore_from_backup(
        db: AsyncSession,
        backup_filename: str,
        restore_options: Optional[Dict[str, bool]] = None
) -> Dict[str, Any]:
    """从备份文件恢复数据"""
    try:
        from shared.models import Article, Category, User, Pages, Menus, MenuItems, Media

        backup_path = backup_service.backup_dir / backup_filename

        if not backup_path.exists():
            return {'success': False, 'error': '备份文件不存在'}

        with open(backup_path, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)

        if 'data' not in backup_data:
            return {'success': False, 'error': '备份文件格式错误'}

        restored_types = []
        error_messages = []

        if not restore_options:
            restore_options = {
                'articles': True, 'categories': True, 'users': True,
                'pages': True, 'menus': True, 'menu_items': True, 'media': True,
            }

        model_map = {
            'articles': Article, 'categories': Category, 'users': User,
            'pages': Pages, 'menus': Menus, 'menu_items': MenuItems, 'media': Media
        }

        for key, model in model_map.items():
            if restore_options.get(key) and key in backup_data['data']:
                try:
                    for item_data in backup_data['data'][key]:
                        existing = await db.execute(select(model).where(model.id == item_data['id']))
                        if not existing.scalar_one_or_none():
                            exclude_sensitive = (key == 'users')
                            if exclude_sensitive:
                                item = model(**{k: v for k, v in item_data.items() if k != 'password'})
                            else:
                                item = model(**item_data)
                            db.add(item)
                    restored_types.append(key)
                except Exception as e:
                    error_messages.append(f"{key}: {str(e)}")

        await db.commit()

        message = f'成功恢复数据类型: {", ".join(restored_types)}'
        if error_messages:
            message += f"\n警告: {'; '.join(error_messages)}"

        return {
            'success': True,
            'message': message,
            'restored_types': restored_types,
            'errors': error_messages if error_messages else None
        }
    except Exception as e:
        await db.rollback()
        return {'success': False, 'error': str(e)}


async def delete_backup(backup_filename: str) -> bool:
    """删除备份文件"""
    try:
        backup_path = backup_service.backup_dir / backup_filename
        if backup_path.exists():
            backup_path.unlink()
            return True
        return False
    except Exception:
        return False


async def get_database_stats(db: AsyncSession) -> Dict[str, Any]:
    """获取数据库统计信息"""
    try:
        from shared.models import Article, Category, Pages, Menus, MenuItems, Media, User

        stats = {}
        for key, model in [
            ('total_articles', Article, Article.status == 1),
            ('total_categories', Category, None),
            ('total_pages', Pages, None),
            ('total_menus', Menus, None),
            ('total_media', Media, None),
            ('total_users', User, None),
        ]:
            query = select(func.count(model.id))
            if model == Article:
                query = query.where(Article.status == 1)
            result = await db.execute(query)
            stats[key] = result.scalar() or 0

        backups = backup_service.list_backups()
        stats['last_backup'] = backups[0]['created_at'] if backups else None

        # 估算数据库大小
        stats['database_size'] = 'Unknown'
        try:
            result = await db.execute(text(
                "SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS size_mb "
                "FROM information_schema.tables WHERE table_schema = DATABASE()"
            ))
            size_row = result.fetchone()
            if size_row and size_row[0]:
                stats['database_size'] = f"{size_row[0]} MB"
        except:
            pass

        return stats
    except Exception as e:
        return {'error': str(e)}
