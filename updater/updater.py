#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastBlog 独立更新器
完全独立的更新程序，负责：
1. 下载新版本文件
2. 安全地替换现有文件
3. 处理更新过程中的各种异常情况
"""

import argparse
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional
from zipfile import ZipFile

# 添加项目根目录到 Python 路径
base_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(base_dir))

# 导入版本管理器
try:
    from shared.utils.version_manager import version_manager
except Exception as e:
    print(f"警告：无法导入版本管理器：{e}")

# 导入更新历史管理器
try:
    from shared.utils.update_history import add_update_history
except Exception as e:
    print(f"警告：无法导入更新历史管理器：{e}")
    add_update_history = None

from src.unified_logger import default_logger as logger


class FastBlogUpdater:
    """FastBlog 更新器类"""

    def __init__(self, target_version: str, app_path: str):
        self.target_version = target_version
        self.app_path = Path(app_path).resolve()
        self.base_dir = Path(__file__).resolve().parent.parent
        self.temp_dir = Path(tempfile.mkdtemp(prefix="fastblog_update_"))
        self.backup_dir = self.base_dir / "backups" / "update_backups"
    
        # 确保备份目录存在
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
        logger.info(f"更新器初始化")
        logger.info(f"目标版本：{target_version}")
        logger.info(f"应用路径：{app_path}")
        logger.info(f"临时目录：{self.temp_dir}")
        logger.info(f"备份目录：{self.backup_dir}")

    def download_update_package(self) -> Optional[Path]:
        """下载更新包"""
        try:
            # 优先从本地 releases 目录查找
            local_release_path = self.base_dir / "releases" / f"update_{self.target_version}.zip"
            if local_release_path.exists():
                logger.info(f"找到本地更新包：{local_release_path}")
                return local_release_path
            
            # 尝试从更新服务器下载
            update_server_url = os.getenv('UPDATE_SERVER_URL', 'http://localhost:8001')
            download_url = f"{update_server_url}/api/v1/releases/download/{self.target_version}"
            
            logger.info(f"尝试从更新服务器下载: {download_url}")
            
            import requests
            response = requests.get(download_url, timeout=60)
            
            if response.status_code == 200:
                # 保存到releases目录
                self.base_dir.mkdir(parents=True, exist_ok=True)
                releases_dir = self.base_dir / "releases"
                releases_dir.mkdir(exist_ok=True)
                
                package_file = releases_dir / f"update_{self.target_version}.zip"
                with open(package_file, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"更新包下载成功: {package_file}")
                return package_file
            else:
                logger.warning(f"从更新服务器下载失败，状态码: {response.status_code}")
                logger.info("提示：请先使用 build_release.py 生成更新包并放到 releases/ 目录")
                return None
            
        except ImportError:
            logger.warning("未安装 requests 库，无法从远程下载")
            logger.info("提示：请先使用 build_release.py 生成更新包并放到 releases/ 目录")
            return None
        except Exception as e:
            logger.error(f"下载更新包失败：{e}")
            import traceback
            traceback.print_exc()
            return None

    def verify_package_integrity(self, package_file: Path) -> bool:
        """验证更新包完整性"""
        try:
            # 这里可以添加校验和验证、数字签名验证等
            if not package_file.exists():
                return False

            # 简单的文件大小检查
            if package_file.stat().st_size < 1024:  # 小于1KB认为无效
                logger.error("更新包文件过小")
                return False

            # 尝试解压验证
            with ZipFile(package_file, 'r') as zip_ref:
                zip_ref.testzip()  # 测试ZIP文件完整性

            logger.info("更新包完整性验证通过")
            return True

        except Exception as e:
            logger.error(f"更新包验证失败: {e}")
            return False

    def backup_current_version(self) -> bool:
        """备份当前版本"""
        try:
            backup_name = f"backup_{int(time.time())}"
            backup_path = self.backup_dir / backup_name

            logger.info(f"开始备份当前版本到: {backup_path}")

            # 复制整个应用目录
            shutil.copytree(self.app_path, backup_path, dirs_exist_ok=True)

            # 记录备份信息
            backup_info = {
                "timestamp": int(time.time()),
                "version": self.get_current_version(),
                "backup_path": str(backup_path)
            }

            info_file = backup_path / "backup_info.json"
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, indent=2, ensure_ascii=False)

            logger.info("当前版本备份完成")
            return True

        except Exception as e:
            logger.error(f"备份当前版本失败: {e}")
            return False

    def get_current_version(self) -> str:
        """获取当前版本号"""
        try:
            # 使用版本管理器获取后端版本
            backend_info = version_manager.get_backend_version()
            return backend_info.get('version', '0.0.0')
        except Exception as e:
            logger.warning(f"获取当前版本失败，使用默认版本：{e}")
            return "0.0.0"

    def extract_update_package(self, package_file: Path) -> Optional[Path]:
        """解压更新包"""
        try:
            extract_path = self.temp_dir / "extracted"
            extract_path.mkdir(exist_ok=True)

            logger.info(f"开始解压更新包到: {extract_path}")

            with ZipFile(package_file, 'r') as zip_ref:
                zip_ref.extractall(extract_path)

            logger.info("更新包解压完成")
            return extract_path

        except Exception as e:
            logger.error(f"解压更新包失败: {e}")
            return None

    def stop_main_application(self) -> bool:
        """停止主应用程序"""
        try:
            logger.info("正在停止主应用程序...")

            # 这里需要实现进程查找和终止逻辑
            # 可以通过进程名、PID文件等方式识别主程序进程

            # 简单示例：查找并终止相关进程
            import psutil

            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['cmdline'] and 'main.py' in ' '.join(proc.info['cmdline']):
                        logger.info(f"终止进程 PID: {proc.info['pid']}")
                        proc.terminate()
                        proc.wait(timeout=10)  # 等待10秒
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                    pass

            # 额外等待确保进程完全终止
            time.sleep(3)
            logger.info("主应用程序已停止")
            return True

        except ImportError:
            logger.warning("未安装 psutil，跳过进程终止")
            return True
        except Exception as e:
            logger.error(f"停止主应用程序失败: {e}")
            return False

    def apply_update(self, extracted_path: Path) -> bool:
        """应用更新"""
        try:
            logger.info("开始应用更新...")

            # 确保目标目录存在
            self.app_path.mkdir(parents=True, exist_ok=True)

            # 使用临时目录进行原子性更新
            temp_app_path = self.temp_dir / "temp_app"
            shutil.copytree(extracted_path, temp_app_path, dirs_exist_ok=True)

            # 原子性替换（先移动旧版本，再移动新版本）
            old_app_backup = self.temp_dir / "old_app"
            if self.app_path.exists():
                shutil.move(str(self.app_path), str(old_app_backup))

            shutil.move(str(temp_app_path), str(self.app_path))

            # 清理临时的旧版本
            if old_app_backup.exists():
                shutil.rmtree(old_app_backup)

            logger.info("更新应用完成")
            return True

        except Exception as e:
            logger.error(f"应用更新失败: {e}")
            return False

    def cleanup(self):
        """清理临时文件"""
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                logger.info("临时文件清理完成")
        except Exception as e:
            logger.warning(f"清理临时文件失败: {e}")

    def rollback(self) -> bool:
        """回滚到备份版本"""
        try:
            logger.info("开始回滚操作...")

            # 查找最新的备份
            backups = []
            for backup_dir in self.backup_dir.iterdir():
                if backup_dir.is_dir():
                    info_file = backup_dir / "backup_info.json"
                    if info_file.exists():
                        try:
                            with open(info_file, 'r', encoding='utf-8') as f:
                                info = json.load(f)
                                backups.append((info['timestamp'], backup_dir))
                        except Exception:
                            pass

            if not backups:
                logger.error("未找到可用的备份")
                return False

            # 按时间排序，获取最新的备份
            backups.sort(reverse=True)
            latest_backup = backups[0][1]

            logger.info(f"使用备份进行回滚: {latest_backup}")

            # 执行回滚
            if self.app_path.exists():
                shutil.rmtree(self.app_path)

            shutil.copytree(latest_backup, self.app_path)

            logger.info("回滚完成")
            return True

        except Exception as e:
            logger.error(f"回滚失败: {e}")
            return False

    def update(self) -> bool:
        """执行完整的更新流程"""
        logger.info("=== 开始执行更新 ===")
            
        start_time = time.time()
        from_version = self.get_current_version()
            
        try:
            # 1. 下载更新包
            package_file = self.download_update_package()
            if not package_file:
                if add_update_history:
                    add_update_history(
                        from_version=from_version,
                        to_version=self.target_version,
                        status='failed',
                        error='下载更新包失败',
                        duration=time.time() - start_time
                    )
                return False
    
            # 2. 验证更新包
            if not self.verify_package_integrity(package_file):
                if add_update_history:
                    add_update_history(
                        from_version=from_version,
                        to_version=self.target_version,
                        status='failed',
                        error='更新包验证失败',
                        duration=time.time() - start_time
                    )
                return False
    
            # 3. 备份当前版本
            backup_success = self.backup_current_version()
            backup_path = str(self.backup_dir / f"backup_{int(time.time())}") if backup_success else None
            if not backup_success:
                logger.warning("备份失败，但仍继续更新")
    
            # 4. 解压更新包
            extracted_path = self.extract_update_package(package_file)
            if not extracted_path:
                if add_update_history:
                    add_update_history(
                        from_version=from_version,
                        to_version=self.target_version,
                        status='failed',
                        error='解压更新包失败',
                        backup_path=backup_path,
                        duration=time.time() - start_time
                    )
                return False
    
            # 5. 停止主应用程序
            if not self.stop_main_application():
                logger.warning("停止主程序失败，可能影响更新")
    
            # 6. 应用更新
            if not self.apply_update(extracted_path):
                logger.error("更新应用失败，尝试回滚")
                self.rollback()
                if add_update_history:
                    add_update_history(
                        from_version=from_version,
                        to_version=self.target_version,
                        status='rollback',
                        error='更新应用失败，已回滚',
                        backup_path=backup_path,
                        duration=time.time() - start_time
                    )
                return False
    
            duration = time.time() - start_time
            logger.info("=== 更新成功完成 ===")
            logger.info(f"总耗时：{duration:.2f}秒")
                
            # 记录成功的更新历史
            if add_update_history:
                add_update_history(
                    from_version=from_version,
                    to_version=self.target_version,
                    status='success',
                    backup_path=backup_path,
                    duration=duration
                )
                
            return True
    
        except Exception as e:
            logger.error(f"更新过程中发生异常：{e}")
            self.rollback()
            if add_update_history:
                add_update_history(
                    from_version=from_version,
                    to_version=self.target_version,
                    status='failed',
                    error=f'更新异常：{str(e)}',
                    duration=time.time() - start_time
                )
            return False
        finally:
            self.cleanup()


def main():
    """更新器入口函数"""
    parser = argparse.ArgumentParser(description="FastBlog 独立更新器")
    parser.add_argument("--target-version", required=True, help="目标版本号")
    parser.add_argument("--app-path", required=True, help="应用程序路径")

    args = parser.parse_args()

    try:
        updater = FastBlogUpdater(args.target_version, args.app_path)
        success = updater.update()

        if success:
            logger.info("更新器执行成功")
            sys.exit(0)
        else:
            logger.error("更新器执行失败")
            sys.exit(1)

    except Exception as e:
        logger.error(f"更新器运行异常: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
