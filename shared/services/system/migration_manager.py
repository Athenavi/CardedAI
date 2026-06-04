"""
数据库迁移管理器
基于Alembic实现自动数据库迁移
"""
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional


class MigrationManager:
    """基于Alembic的数据库迁移管理器"""
    
    def __init__(self):
        self.alembic_ini = Path(__file__).parent.parent.parent / "alembic.ini"
        self.migrations_dir = Path(__file__).parent.parent.parent / "alembic_migrations"
        self.versions_dir = self.migrations_dir / "versions"
    
    def _get_alembic_cmd(self) -> List[str]:
        """获取Alembic命令基础部分"""
        return [sys.executable, "-m", "alembic"]
    
    def _run_alembic(self, args: List[str], cwd: Optional[Path] = None) -> Dict[str, Any]:
        """
        执行Alembic命令
        
        Args:
            args: Alembic参数列表
            cwd: 工作目录
            
        Returns:
            执行结果
        """
        try:
            cmd = self._get_alembic_cmd() + args
            result = subprocess.run(
                cmd,
                cwd=str(cwd or self.alembic_ini.parent),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Command timed out',
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
            }
    
    def get_current_revision(self) -> Dict[str, Any]:
        """
        获取当前数据库版本
        
        Returns:
            当前版本信息
        """
        result = self._run_alembic(['current'])
        
        if result['success']:
            # 解析输出: <revision> (head)
            lines = result['stdout'].strip().split('\n')
            current_rev = None
            
            for line in lines:
                if line.strip() and not line.startswith('INFO'):
                    parts = line.split()
                    if parts:
                        current_rev = parts[0]
                        break
            
            return {
                'success': True,
                'current_revision': current_rev,
                'has_pending': 'head' in result['stdout'],
            }
        else:
            return {
                'success': False,
                'error': result.get('stderr', 'Unknown error'),
            }
    
    def get_pending_migrations(self) -> Dict[str, Any]:
        """
        获取待执行的迁移
        
        Returns:
            待执行迁移列表
        """
        result = self._run_alembic(['history'])
        
        if result['success']:
            # 解析历史记录
            migrations = []
            lines = result['stdout'].strip().split('\n')
            
            for line in lines:
                if '->' in line:
                    # 格式: <rev1> -> <rev2> (head), message
                    parts = line.split('->')
                    if len(parts) == 2:
                        rev_info = parts[1].strip().split(',')
                        rev_id = rev_info[0].strip().split()[0]
                        message = rev_info[-1].strip() if len(rev_info) > 1 else ''
                        
                        migrations.append({
                            'revision': rev_id,
                            'message': message,
                        })
            
            return {
                'success': True,
                'pending_count': len(migrations),
                'migrations': migrations,
            }
        else:
            return {
                'success': False,
                'error': result.get('stderr', 'Unknown error'),
            }
    
    async def apply_all_migrations(self, db_session=None) -> Dict[str, Any]:
        """
        执行所有待处理的迁移
        
        Args:
            db_session: 数据库会话(可选,Alembic会自行处理)
            
        Returns:
            执行结果
        """
        result = self._run_alembic(['upgrade', 'head'])
        
        if result['success']:
            return {
                'success': True,
                'message': 'All migrations applied successfully',
                'output': result['stdout'],
            }
        else:
            return {
                'success': False,
                'error': result.get('stderr', 'Migration failed'),
                'output': result['stdout'],
            }
    
    def create_migration(self, message: str, autogenerate: bool = False) -> Dict[str, Any]:
        """
        创建新的迁移文件
        
        Args:
            message: 迁移描述
            autogenerate: 是否自动生成(基于模型变化)
            
        Returns:
            创建结果
        """
        args = ['revision', '-m', message]
        
        if autogenerate:
            args.append('--autogenerate')
        
        result = self._run_alembic(args)
        
        if result['success']:
            # 提取生成的文件名
            lines = result['stdout'].strip().split('\n')
            generated_file = None
            
            for line in lines:
                if 'Generating' in line:
                    generated_file = line.split()[-1]
                    break
            
            return {
                'success': True,
                'message': f'Migration created: {message}',
                'file': generated_file,
                'output': result['stdout'],
            }
        else:
            return {
                'success': False,
                'error': result.get('stderr', 'Failed to create migration'),
            }
    
    def rollback_migration(self, steps: int = 1) -> Dict[str, Any]:
        """
        回滚迁移
        
        Args:
            steps: 回滚步数(-1表示回滚到base)
            
        Returns:
            回滚结果
        """
        target = f'-{steps}' if steps > 0 else 'base'
        result = self._run_alembic(['downgrade', target])
        
        if result['success']:
            return {
                'success': True,
                'message': f'Rolled back {steps} migration(s)',
                'output': result['stdout'],
            }
        else:
            return {
                'success': False,
                'error': result.get('stderr', 'Rollback failed'),
            }
    
    def get_migration_status(self) -> Dict[str, Any]:
        """
        获取迁移状态摘要
        
        Returns:
            状态信息
        """
        current = self.get_current_revision()
        history = self.get_pending_migrations()
        
        return {
            'success': current['success'] and history['success'],
            'current_revision': current.get('current_revision'),
            'has_pending': current.get('has_pending', False),
            'pending_count': history.get('pending_count', 0),
            'pending_migrations': history.get('migrations', []),
        }
    
    def stamp_revision(self, revision: str) -> Dict[str, Any]:
        """
        标记数据库为指定版本(不执行迁移)
        
        Args:
            revision: 目标版本号
            
        Returns:
            操作结果
        """
        result = self._run_alembic(['stamp', revision])
        
        if result['success']:
            return {
                'success': True,
                'message': f'Database stamped to {revision}',
            }
        else:
            return {
                'success': False,
                'error': result.get('stderr', 'Stamp failed'),
            }


# 单例实例
migration_manager = MigrationManager()
