"""
数据库迁移服务 - 支持实时日志输出
参考 Django migrations 和 Flask-Migrate 的设计
"""
import asyncio

import subprocess
import sys
from pathlib import Path
from typing import AsyncGenerator, Dict, Any

from src.unified_logger import default_logger as logger


class DatabaseMigrationService:
    """数据库迁移服务"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent.parent.parent
        self.alembic_dir = self.project_root / "alembic_migrations"

    async def run_migration(self) -> AsyncGenerator[Dict[str, Any], None]:
        """
        执行数据库迁移并实时返回日志
        
        Yields:
            dict: {
                'type': 'info' | 'error' | 'success' | 'progress',
                'message': str,
                'timestamp': float
            }
        """
        import time

        try:
            yield {
                'type': 'info',
                'message': '开始执行数据库迁移...',
                'timestamp': time.time()
            }

            yield {
                'type': 'info',
                'message': f'项目根目录: {self.project_root}',
                'timestamp': time.time()
            }

            yield {
                'type': 'info',
                'message': f'Alembic 目录: {self.alembic_dir}',
                'timestamp': time.time()
            }

            # 检查 alembic.ini 是否存在
            alembic_ini = self.project_root / "alembic.ini"
            if not alembic_ini.exists():
                yield {
                    'type': 'error',
                    'message': f'错误: alembic.ini 文件不存在于 {alembic_ini}',
                    'timestamp': time.time()
                }
                return

            yield {
                'type': 'info',
                'message': f'找到 alembic.ini: {alembic_ini}',
                'timestamp': time.time()
            }

            # 检查是否有迁移脚本
            versions_dir = self.alembic_dir / "versions"
            migration_files = list(versions_dir.glob("*.py")) if versions_dir.exists() else []
            migration_files = [f for f in migration_files if f.name != "__init__.py"]

            yield {
                'type': 'info',
                'message': f'检查迁移脚本... (找到 {len(migration_files)} 个)',
                'timestamp': time.time()
            }

            # 如果没有迁移脚本，生成初始迁移
            if len(migration_files) == 0:
                yield {
                    'type': 'info',
                    'message': '→ 未找到迁移脚本，正在生成初始迁移...',
                    'timestamp': time.time()
                }

                import subprocess as sync_subprocess
                result = sync_subprocess.run(
                    [sys.executable, "-m", "alembic", "revision", "--autogenerate", "-m", "Initial migration"],
                    cwd=str(self.project_root),
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                # Alembic autogenerate 可能返回非零退出码但仍然成功生成迁移
                # 检查是否实际生成了迁移文件
                migration_files_after = list(versions_dir.glob("*.py")) if versions_dir.exists() else []
                migration_files_after = [f for f in migration_files_after if f.name != "__init__.py"]
                
                # 如果有新的迁移文件生成，认为成功
                if len(migration_files_after) > len(migration_files):
                    yield {
                        'type': 'info',
                        'message': '初始迁移脚本生成中...',
                        'timestamp': time.time()
                    }
                    
                    # 输出日志
                    if result.stdout:
                        for line in result.stdout.split('\n'):
                            if line.strip():
                                yield {
                                    'type': 'info',
                                    'message': line,
                                    'timestamp': time.time()
                                }
                    
                    yield {
                        'type': 'success',
                        'message': '✓ 初始迁移脚本生成成功',
                        'timestamp': time.time()
                    }
                else:
                    # 没有生成新文件，才是真正的失败
                    error_msg = f'生成迁移脚本失败:\n{result.stderr}'
                    yield {
                        'type': 'error',
                        'message': error_msg,
                        'timestamp': time.time()
                    }
                    return

                # 重新检查迁移文件
                migration_files = list(versions_dir.glob("*.py")) if versions_dir.exists() else []
                migration_files = [f for f in migration_files if f.name != "__init__.py"]
                yield {
                    'type': 'info',
                    'message': f'→ 现在共有 {len(migration_files)} 个迁移脚本',
                    'timestamp': time.time()
                }

            # 执行 alembic upgrade head（使用同步 subprocess，避免 Windows asyncio 问题）
            cmd = [sys.executable, "-m", "alembic", "upgrade", "head"]
            print(f"\n[Migration] 执行命令: {' '.join(cmd)}")
            print(f"[Migration] 工作目录: {self.project_root}")

            # 在线程池中执行同步 subprocess
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=str(self.project_root),
                    env=self._get_env_with_path(),
                    timeout=300  # 5分钟超时
                )
            )

            # 输出 stdout
            if result.stdout:
                print(f"[Migration STDOUT]\n{result.stdout}")
                for line in result.stdout.split('\n'):
                    if line.strip():
                        yield {
                            'type': 'info',
                            'message': line,
                            'timestamp': time.time()
                        }
                        await asyncio.sleep(0.01)  # 模拟流式输出

            # 输出 stderr
            if result.stderr:
                print(f"[Migration STDERR]\n{result.stderr}")
                for line in result.stderr.split('\n'):
                    if line.strip():
                        is_error = any(keyword in line for keyword in ['ERROR', 'Error', 'Traceback', 'Exception'])
                        yield {
                            'type': 'error' if is_error else 'info',
                            'message': line,
                            'timestamp': time.time()
                        }
                        await asyncio.sleep(0.01)

            print(f"[Migration] 退出码: {result.returncode}")

            if result.returncode == 0:
                yield {
                    'type': 'success',
                    'message': '✓ 数据库迁移成功完成',
                    'timestamp': time.time()
                }
            else:
                error_msg = f'✗ 迁移失败，退出码: {result.returncode}'
                if result.stderr:
                    error_msg += f'\n\n错误详情:\n{result.stderr}'
                yield {
                    'type': 'error',
                    'message': error_msg,
                    'timestamp': time.time()
                }

        except FileNotFoundError as e:
            error_msg = f'错误: 找不到命令或文件 - {str(e)}'
            print(f"[Migration ERROR] {error_msg}")
            yield {
                'type': 'error',
                'message': error_msg,
                'timestamp': time.time()
            }
        except subprocess.TimeoutExpired:
            error_msg = '迁移超时（超过5分钟）'
            print(f"[Migration ERROR] {error_msg}")
            yield {
                'type': 'error',
                'message': error_msg,
                'timestamp': time.time()
            }
        except Exception as e:
            import traceback
            error_msg = f'迁移过程出错: {str(e)}'
            traceback_str = traceback.format_exc()
            print(f"[Migration ERROR] {error_msg}")
            print(traceback_str)

            yield {
                'type': 'error',
                'message': error_msg,
                'timestamp': time.time()
            }
            yield {
                'type': 'error',
                'message': f'\n详细堆栈信息:\n{traceback_str}',
                'timestamp': time.time()
            }

    def _get_env_with_path(self) -> dict:
        """获取包含正确 PATH 的环境变量"""
        import os
        env = os.environ.copy()

        # 确保 Python 路径正确
        python_path = str(self.project_root)
        if 'PYTHONPATH' in env:
            env['PYTHONPATH'] = f"{python_path}{os.pathsep}{env['PYTHONPATH']}"
        else:
            env['PYTHONPATH'] = python_path

        return env

    def check_alembic_available(self) -> bool:
        """检查 Alembic 是否可用"""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "alembic", "--version"],
                capture_output=True,
                text=True,
                cwd=str(self.project_root)
            )
            return result.returncode == 0
        except Exception:
            return False

    def get_migration_status(self) -> Dict[str, Any]:
        """获取当前迁移状态"""
        try:
            # 检查当前版本
            result = subprocess.run(
                [sys.executable, "-m", "alembic", "current"],
                capture_output=True,
                text=True,
                cwd=str(self.project_root)
            )

            current_version = result.stdout.strip() if result.returncode == 0 else "未知"

            # 检查待迁移版本
            result = subprocess.run(
                [sys.executable, "-m", "alembic", "heads"],
                capture_output=True,
                text=True,
                cwd=str(self.project_root)
            )

            head_version = result.stdout.strip() if result.returncode == 0 else "未知"

            return {
                'current': current_version,
                'head': head_version,
                'is_up_to_date': current_version == head_version and current_version != "未知"
            }
        except Exception as e:
            return {
                'current': '错误',
                'head': '错误',
                'is_up_to_date': False,
                'error': str(e)
            }


# 全局实例
migration_service = DatabaseMigrationService()
