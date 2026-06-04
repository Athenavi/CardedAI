#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新检查服务器
作为独立进程运行，提供版本检查服务
"""


import os
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# 导入版本管理器（简化版）
try:
    from shared.utils.version_manager import version_manager, get_current_version_info, get_version_summary
    VERSION_MANAGER_AVAILABLE = True
    logging.info("版本管理器加载成功")
except Exception as e:
    logging.warning(f"版本管理器导入失败：{e}")
    VERSION_MANAGER_AVAILABLE = False

# 导入自动更新检查器
try:
    from shared.utils.auto_update_checker import AutoUpdateChecker, auto_update_checker
    AUTO_CHECKER_AVAILABLE = True
    logging.info("自动更新检查器加载成功")
except Exception as e:
    logging.warning(f"自动更新检查器导入失败：{e}")
    AUTO_CHECKER_AVAILABLE = False

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from src.unified_logger import default_logger as logger

app = FastAPI(
    title="FastBlog Update Checker",
    description="独立的更新检查服务",
    version="1.0.0"
)


class UpdateChecker:
    """更新检查器类"""

    def __init__(self):
        self.base_dir = project_root
        self.version_file = self.base_dir / "version.txt"
        self.running = False
        self.start_time = time.time()

    def get_local_version_info(self) -> Dict[str, Any]:
        """获取本地版本信息（兼容旧版）"""
        try:
            # 优先使用版本管理器
            if VERSION_MANAGER_AVAILABLE:
                all_versions = version_manager.get_all_versions()
                backend_info = all_versions.get('BACKEND', {})
                frontend_info = all_versions.get('FRONTEND', {})

                return {
                    "backend_version": backend_info.get('version', '0.0.0'),
                    "frontend_version": frontend_info.get('version', '0.0.0'),
                    "build_time": backend_info.get('build_time', ''),
                    "framework": backend_info.get('framework', ''),
                    "status": "success"
                }

            # 回退到读取文件方式
            if self.version_file.exists():
                with open(self.version_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 解析 INI 格式
                version_info = {}
                current_section = None
                for line in content.strip().split('\n'):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if line.startswith('[') and line.endswith(']'):
                        current_section = line[1:-1]
                        version_info[current_section] = {}
                    elif '=' in line and current_section:
                        key, value = line.split('=', 1)
                        version_info[current_section][key.strip()] = value.strip()

                return {
                    "backend_version": version_info.get("BACKEND", {}).get("version", "0.0.0"),
                    "frontend_version": version_info.get("FRONTEND", {}).get("version", "0.0.0"),
                    "build_time": version_info.get("BACKEND", {}).get("build_time", ""),
                    "framework": version_info.get("BACKEND", {}).get("framework", ""),
                    "status": "success"
                }

            return {
                "backend_version": "0.0.0",
                "frontend_version": "0.0.0",
                "build_time": "",
                "framework": "FastAPI",
                "status": "default"
            }

        except Exception as e:
            logger.error(f"读取版本信息失败：{e}")
            return {
                "backend_version": "0.0.0",
                "frontend_version": "0.0.0",
                "build_time": "",
                "framework": "FastAPI",
                "status": "error",
                "error": str(e)
            }

    def get_version_info(self) -> Dict[str, Any]:
        """获取完整的版本信息"""
        try:
            if VERSION_MANAGER_AVAILABLE:
                versions = version_manager.get_all_versions()
                summary = get_version_summary()

                return {
                    'success': True,
                    'data': {
                        'versions': versions,
                        'summary': summary,
                        'timestamp': datetime.now().isoformat()
                    }
                }
            else:
                # 兼容旧版本
                local_info = self.get_local_version_info()
                return {
                    'success': True,
                    'data': {
                        'backend_version': local_info.get('backend_version', 'unknown'),
                        'frontend_version': local_info.get('frontend_version', 'unknown'),
                        'timestamp': datetime.now().isoformat()
                    }
                }
        except Exception as e:
            logger.error(f"获取版本信息失败：{e}")
            return {
                'success': False,
                'error': str(e),
                'data': None
            }

    def get_frontend_version_info(self) -> Dict[str, Any]:
        """获取前端版本信息"""
        try:
            if VERSION_MANAGER_AVAILABLE:
                frontend_info = version_manager.get_frontend_version()
                return {
                    'success': True,
                    'data': frontend_info
                }
            else:
                local_info = self.get_local_version_info()
                return {
                    'success': True,
                    'data': {
                        'version': local_info.get('frontend_version', 'unknown')
                    }
                }
        except Exception as e:
            logger.error(f"获取前端版本失败：{e}")
            return {
                'success': False,
                'error': str(e),
                'data': None
            }

    def get_backend_version_info(self) -> Dict[str, Any]:
        """获取后端版本信息"""
        try:
            if VERSION_MANAGER_AVAILABLE:
                backend_info = version_manager.get_backend_version()
                return {
                    'success': True,
                    'data': backend_info
                }
            else:
                local_info = self.get_local_version_info()
                return {
                    'success': True,
                    'data': {
                        'version': local_info.get('backend_version', 'unknown')
                    }
                }
        except Exception as e:
            logger.error(f"获取后端版本失败：{e}")
            return {
                'success': False,
                'error': str(e),
                'data': None
            }


# 创建更新检查器实例
update_checker = UpdateChecker()


@app.get("/")
async def root():
    """根路径，返回服务器状态"""
    return {
        "message": "FastBlog Update Checker is running",
        "service": "update-checker",
        "uptime": time.time() - update_checker.start_time
    }


@app.get("/api/v1/version")
async def get_version_info():
    """获取版本信息接口"""
    try:
        version_info = update_checker.get_local_version_info()
        return JSONResponse(content=version_info)
    except Exception as e:
        logger.error(f"获取版本信息异常: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "service": "update-checker",
        "version": "1.0.0",
        "uptime": time.time() - update_checker.start_time
    }


@app.get("/api/v1/config")
async def get_config_info():
    """获取配置信息"""
    return {
        "auto_check_enabled": True,
        "check_interval": 3600,
        "server_info": {
            "name": "FastBlog Update Checker",
            "version": "1.0.0"
        }
    }


# ==================== 版本管理API ====================

@app.get("/api/v1/version/full")
async def get_full_version_info():
    """获取完整的版本信息"""
    result = update_checker.get_version_info()
    if result['success']:
        return JSONResponse(content=result['data'])
    else:
        raise HTTPException(status_code=500, detail=result['error'])


@app.get("/api/v1/version/frontend")
async def get_frontend_version_api():
    """获取前端版本信息"""
    result = update_checker.get_frontend_version_info()
    if result['success']:
        return JSONResponse(content=result['data'])
    else:
        raise HTTPException(status_code=500, detail=result['error'])


@app.get("/api/v1/version/backend")
async def get_backend_version_api():
    """获取后端版本信息"""
    result = update_checker.get_backend_version_info()
    if result['success']:
        return JSONResponse(content=result['data'])
    else:
        raise HTTPException(status_code=500, detail=result['error'])


# ==================== 基础更新状态API ====================

@app.get("/api/v1/update/status")
async def get_update_status():
    """获取基础更新状态信息"""
    try:
        # 获取当前版本信息
        version_info = update_checker.get_version_info()
        if not version_info['success']:
            raise HTTPException(status_code=500, detail=version_info['error'])

        return JSONResponse(content={
            'success': True,
            'data': {
                'current_version': version_info['data'].get('versions', {}).get('backend', {}).get('version', 'unknown'),
                'frontend_version': version_info['data'].get('versions', {}).get('frontend', {}).get('version', 'unknown'),
                'is_updating': False,  # 基础状态，实际更新状态由独立更新器管理
                'last_check': datetime.now().isoformat(),
                'update_server': 'running'
            }
        })
    except Exception as e:
        logger.error(f"获取更新状态失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/update/check")
async def check_for_updates():
    """检查是否有新版本"""
    try:
        # 获取当前版本
        current_info = update_checker.get_version_info()
        current_version = current_info['data'].get('versions', {}).get('backend', {}).get('version', '0.0.0')

        # 从本地 releases 目录查找最新版本
        releases_dir = project_root / "releases"
        latest_version = current_version
        changelog = ''
        has_update = False

        if releases_dir.exists():
            # 查找所有更新包
            update_packages = list(releases_dir.glob("update_*.zip"))

            if update_packages:
                # 提取版本号并排序
                versions = []
                for pkg in update_packages:
                    version_str = pkg.stem.replace('update_', '')
                    try:
                        versions.append((version_str, pkg))
                    except:
                        pass

                if versions:
                    # 按版本号排序（假设版本号格式为 x.y.z）
                    versions.sort(key=lambda x: [int(p) for p in x[0].split('.')], reverse=True)
                    latest_version = versions[0][0]

                    # 检查是否有更新
                    from packaging import version as pkg_version
                    if pkg_version.parse(latest_version) > pkg_version.parse(current_version):
                        has_update = True

                        # 读取changelog
                        metadata_file = releases_dir / f"update_{latest_version}.json"
                        if metadata_file.exists():
                            with open(metadata_file, 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                                changelog = metadata.get('changelog', '')
        return JSONResponse(content={
            'success': True,
            'data': {
                'has_update': False,
                'current_version': current_version,
                'latest_version': current_version,
                'message': '已是最新版本',
                'changelog': ''
            }
        })
    except Exception as e:
        logger.error(f"检查更新失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/update/apply")
async def apply_update(version: str = None):
    """应用更新"""
    try:
        # 实现更新应用逻辑
        import subprocess
        import sys
        from pathlib import Path

        # 如果没有指定版本，使用最新版本
        if not version:
            # 从releases目录获取最新版本
            releases_dir = project_root / "releases"
            if releases_dir.exists():
                update_packages = list(releases_dir.glob("update_*.zip"))
                if update_packages:
                    # 排序获取最新版本
                    versions = []
                    for pkg in update_packages:
                        version_str = pkg.stem.replace('update_', '')
                        try:
                            versions.append(version_str)
                        except:
                            pass

                    if versions:
                        versions.sort(key=lambda x: [int(p) for p in x.split('.')], reverse=True)
                        version = versions[0]

            if not version:
                version = "latest"

        # 准备命令
        cmd = [sys.executable, "-m", "updater.updater",
               "--target-version", version,
               "--app-path", str(project_root)]

        logger.info(f"执行更新命令: {' '.join(cmd)}")

        # 执行更新命令
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)  # 5分钟超时

        if result.returncode == 0:
            return JSONResponse(content={
                'success': True,
                'data': {
                    'message': '更新成功启动',
                    'version': version,
                    'output': result.stdout
                }
            })
        else:
            logger.error(f"更新失败: {result.stderr}")
            return JSONResponse(content={
                'success': False,
                'data': {
                    'message': '更新失败',
                    'version': version,
                    'error': result.stderr,
                    'stdout': result.stdout
                }
            })

    except subprocess.TimeoutExpired:
        logger.error("更新超时")
        return JSONResponse(content={
            'success': False,
            'data': {
                'message': '更新超时',
                'error': '更新过程超过5分钟，已取消'
            }
        })
    except Exception as e:
        logger.error(f"应用更新失败：{e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/update/download")
async def download_update_package(version: str = "latest"):
    """下载更新包（从本地 releases 目录）"""
    try:
        # 获取项目根目录
        base_dir = project_root
        releases_dir = base_dir / "releases"

        # 如果指定 latest，查找最新的更新包
        if version == "latest":
            if not releases_dir.exists():
                raise HTTPException(status_code=404, detail="Releases 目录不存在")

            update_packages = list(releases_dir.glob("update_*.zip"))
            if not update_packages:
                raise HTTPException(status_code=404, detail="未找到更新包")

            # 按文件名排序（假设文件名包含版本号）
            update_packages.sort(key=lambda x: x.name, reverse=True)
            package_file = update_packages[0]
        else:
            package_file = releases_dir / f"update_{version}.zip"
            if not package_file.exists():
                raise HTTPException(status_code=404, detail=f"版本 {version} 的更新包不存在")

        # 读取文件并返回
        from fastapi.responses import FileResponse

        logger.info(f"提供下载：{package_file}")
        return FileResponse(
            path=package_file,
            filename=package_file.name,
            media_type='application/zip'
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"提供下载失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/update/packages")
async def list_update_packages():
    """列出所有可用的更新包"""
    try:
        base_dir = project_root
        releases_dir = base_dir / "releases"

        if not releases_dir.exists():
            return JSONResponse(content={
                'success': True,
                'data': {
                    'packages': [],
                    'total': 0
                }
            })

        packages = []
        for zip_file in releases_dir.glob("update_*.zip"):
            # 尝试读取元数据
            metadata_file = releases_dir / f"{zip_file.stem}.json"
            metadata = {}
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

            packages.append({
                'filename': zip_file.name,
                'version': zip_file.stem.replace('update_', ''),
                'size': zip_file.stat().st_size,
                'build_time': metadata.get('build_time', ''),
                'metadata': metadata
            })

        # 按版本号排序
        packages.sort(key=lambda x: x['version'], reverse=True)

        return JSONResponse(content={
            'success': True,
            'data': {
                'packages': packages,
                'total': len(packages)
            }
        })

    except Exception as e:
        logger.error(f"列出更新包失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/update/check-now")
async def check_updates_now():
    """立即检查更新（手动触发）"""
    try:
        if not AUTO_CHECKER_AVAILABLE:
            return JSONResponse(content={
                'success': False,
                'error': '自动更新检查器未加载'
            })

        result = await auto_update_checker.check_for_updates()

        return JSONResponse(content={
            'success': True,
            'data': result
        })

    except Exception as e:
        logger.error(f"检查更新失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/update/auto-check/status")
async def get_auto_check_status():
    """获取自动检查状态"""
    try:
        if not AUTO_CHECKER_AVAILABLE:
            return JSONResponse(content={
                'success': False,
                'error': '自动更新检查器未加载'
            })

        return JSONResponse(content={
            'success': True,
            'data': {
                'is_running': auto_update_checker.is_running,
                'check_interval': auto_update_checker.check_interval,
                'last_check_time': auto_update_checker.last_check_time.isoformat() if auto_update_checker.last_check_time else None,
                'current_version': auto_update_checker.current_version
            }
        })

    except Exception as e:
        logger.error(f"获取自动检查状态失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/backups")
async def list_backups(limit: int = 10):
    """列出所有备份"""
    try:
        # 导入备份管理器
        from shared.utils.backup_manager import backup_manager

        backups = backup_manager.list_backups(limit)

        return JSONResponse(content={
            'success': True,
            'data': {
                'backups': backups,
                'total': len(backup_manager.backups),
                'total_size': backup_manager.get_total_size()
            }
        })

    except Exception as e:
        logger.error(f"列出备份失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/backups/create")
async def create_backup(version: str = None):
    """创建当前系统备份"""
    try:
        from shared.utils.backup_manager import backup_manager
        from pathlib import Path

        project_root = Path(__file__).resolve().parent.parent.parent

        backup_info = backup_manager.create_backup(str(project_root), version)

        if backup_info:
            return JSONResponse(content={
                'success': True,
                'data': backup_info,
                'message': '备份创建成功'
            })
        else:
            return JSONResponse(content={
                'success': False,
                'error': '备份创建失败'
            }, status_code=500)

    except Exception as e:
        logger.error(f"创建备份失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/backups/restore")
async def restore_backup(backup_id: str):
    """恢复备份

    Args:
        backup_id: 备份 ID（时间戳）
    """
    try:
        from shared.utils.backup_manager import backup_manager
        from pathlib import Path

        project_root = Path(__file__).resolve().parent.parent.parent

        success = backup_manager.restore_backup(backup_id, str(project_root))

        if success:
            return JSONResponse(content={
                'success': True,
                'message': '备份恢复成功',
                'warning': '请手动重启应用以生效'
            })
        else:
            return JSONResponse(content={
                'success': False,
                'error': '备份恢复失败'
            }, status_code=500)

    except Exception as e:
        logger.error(f"恢复备份失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/backups/{backup_id}")
async def delete_backup(backup_id: str):
    """删除备份"""
    try:
        from shared.utils.backup_manager import backup_manager

        success = backup_manager.delete_backup(backup_id)

        if success:
            return JSONResponse(content={
                'success': True,
                'message': '备份删除成功'
            })
        else:
            return JSONResponse(content={
                'success': False,
                'error': '备份不存在或删除失败'
            }, status_code=404)

    except Exception as e:
        logger.error(f"删除备份失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


def setup_signal_handlers():
    """设置信号处理器"""

    def signal_handler(signum, frame):
        logger.info(f"收到信号 {signum}，正在关闭更新检查服务器...")
        update_checker.running = False
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Windows特定信号
    if hasattr(signal, 'SIGBREAK'):
        signal.signal(signal.SIGBREAK, signal_handler)


def main():
    """服务器入口函数"""
    import uvicorn

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/update_checker.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    # 默认配置
    host = "127.0.0.1"
    port = 8001  # 使用不同的端口避免冲突

    # 从环境变量获取配置
    host = os.getenv("UPDATE_CHECKER_HOST", host)
    port = int(os.getenv("UPDATE_CHECKER_PORT", port))

    logger.info("=== 更新检查服务器启动 ===")
    logger.info(f"监听地址: http://{host}:{port}")
    logger.info(f"API文档: http://{host}:{port}/api/v2/docs")

    # 设置信号处理器
    setup_signal_handlers()
    update_checker.running = True

    try:
        uvicorn.run(
            "update_server.server:app",
            host=host,
            port=port,
            reload=False,
            log_level="info"
        )
    except KeyboardInterrupt:
        logger.info("更新检查服务器被用户中断")
    except Exception as e:
        logger.error(f"服务器启动失败: {e}")
        sys.exit(1)
    finally:
        update_checker.running = False
        logger.info("更新检查服务器已停止")


if __name__ == "__main__":
    main()
