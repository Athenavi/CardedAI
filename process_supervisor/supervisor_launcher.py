#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastBlog 进程监督器启动器
统一管理所有子进程的生命周期
"""


import signal
import sys
import time
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent.parent  # 使用父目录的父目录作为项目根目录
sys.path.insert(0, str(project_root))

from process_supervisor.process_manager import get_supervisor, ProcessSupervisor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/supervisor_launcher.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
from src.unified_logger import default_logger as logger


class SupervisedLauncher:
    """监督式启动器（增强版：支持 Web 管理界面）"""

    def __init__(self):
        self.base_dir = project_root
        self.supervisor: ProcessSupervisor = None
        self.running = False
        self.web_app = None

    def setup_signal_handlers(self):
        """设置信号处理器"""

        def signal_handler(signum, frame):
            logger.info(f"收到信号 {signum}，正在优雅关闭...")
            self.shutdown()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Windows特定信号
        if hasattr(signal, 'SIGBREAK'):
            signal.signal(signal.SIGBREAK, signal_handler)

    def initialize_supervisor(self) -> bool:
        """初始化进程监督器（增强版：同时初始化 Web 管理界面）"""
        try:
            logger.info("初始化进程监督器...")
            self.supervisor = get_supervisor()

            # 自定义进程配置
            self._customize_process_configs()

            # 初始化 Web 管理界面
            self._initialize_web_admin()
    
            logger.info("进程监督器初始化完成")
            return True
        except Exception as e:
            logger.error(f"初始化进程监督器失败：{e}")
            return False

    def _customize_process_configs(self):
        """自定义进程配置（增强版：更智能的配置适配）"""
        if not self.supervisor:
            return

        # 修改更新检查器配置
        if "update_checker" in self.supervisor.processes:
            update_process = self.supervisor.processes["update_checker"]
            update_process.config.command = [sys.executable, "-m", "update_server.server"]
            update_process.config.working_dir = str(self.base_dir)
            # 更新检查器使用不同端口
            update_process.config.environment = {
                "UPDATE_CHECKER_PORT": "8001",
                "UPDATE_CHECKER_HOST": "127.0.0.1"
            }
            logger.info("已自定义 update_checker 进程配置")

        # 修改主应用配置（使用 uvicorn 多 workers 模式）
        if "main_app" in self.supervisor.processes:
            main_process = self.supervisor.processes["main_app"]
            # 从环境变量读取 workers 数量，默认 6 个
            import os
            workers_count = int(os.environ.get('UVICORN_WORKERS', '6'))
            main_process.config.command = [
                sys.executable, "-m", "uvicorn", "src.app:app",
                "--host", "0.0.0.0",
                "--port", "9421",
                "--workers", str(workers_count)
            ]
            main_process.config.working_dir = str(self.base_dir)  # 确保使用项目根目录
            logger.info(f"已自定义 main_app 进程配置 (uvicorn {workers_count} workers)")

        # 自定义 Django 服务配置
        if "django_server" in self.supervisor.processes:
            django_process = self.supervisor.processes["django_server"]
            django_process.config.command = [sys.executable, "django_blog/manage.py", "runserver", "127.0.0.1:8000"]
            django_process.config.working_dir = str(self.base_dir)  # 确保使用项目根目录
            logger.info("已自定义 django_server 进程配置")

        # 自定义前端开发服务器配置
        if "frontend_dev" in self.supervisor.processes:
            frontend_process = self.supervisor.processes["frontend_dev"]
            frontend_process.config.command = ["npm", "run", "dev"]
            frontend_process.config.working_dir = str(self.base_dir / "frontend-next")
            logger.info("已自定义 frontend_dev 进程配置")

    def _initialize_web_admin(self):
        """初始化 Web 管理界面"""
        try:
            from process_supervisor.web_admin import app as web_app, set_supervisor

            if web_app:
                self.web_app = web_app
                set_supervisor(self.supervisor)
                logger.info("Web 管理界面已初始化")
                logger.info("访问地址：http://127.0.0.1:9422 (需要单独启动)")
            else:
                logger.warning("FastAPI 未安装，跳过 Web 管理界面初始化")
        except ImportError as e:
            logger.warning(f"导入 Web 管理模块失败：{e}，跳过 Web 界面")
        except Exception as e:
            logger.error(f"初始化 Web 管理界面失败：{e}")

    def _start_web_admin_server(self):
        """启动 Web 管理界面服务器"""
        try:
            import uvicorn
            from threading import Thread

            if self.web_app:
                # 在后台线程中启动 Web 服务器
                def run_server():
                    logger.info("正在启动 Web 管理界面...")
                    uvicorn.run(
                        self.web_app,
                        host="127.0.0.1",
                        port=9422,
                        log_level="warning",
                        access_log=False
                    )

                server_thread = Thread(target=run_server, daemon=True)
                server_thread.start()
                logger.info("[OK] Web 管理界面已启动：http://127.0.0.1:9422")
            else:
                logger.warning("Web 管理界面未初始化，无法启动")
        except ImportError:
            logger.warning("uvicorn 未安装，无法启动 Web 管理界面")
        except Exception as e:
            logger.error(f"启动 Web 管理界面失败：{e}")

    def start_system(self) -> bool:
        """启动整个系统（增强版：带详细错误处理和验证）"""
        logger.info("=== FastBlog 进程监督器启动 ===")
        logger.info(f"启动时间：{time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"工作目录：{self.base_dir}")

        # 初始化监督器
        if not self.initialize_supervisor():
            logger.error("监督器初始化失败")
            return False

        # 显示所有进程配置
        self._print_process_configurations()
        
        # 启动所有进程
        logger.info("开始启动所有子进程...")
        if not self.supervisor.start_all_processes():
            logger.error("启动子进程失败")
            return False

        # 启动监控
        self.supervisor.start_monitoring()

        # 等待系统稳定
        logger.info("等待所有进程启动稳定...")
        time.sleep(5)

        # 验证关键进程状态
        success = self._verify_processes()

        if success:
            self.running = True
            logger.info("[OK] 系统启动完成，所有进程已在监督下运行")
            logger.info(f"共启动 {len(self.supervisor.processes)} 个进程")

            # 启动 Web 管理界面（集成模式）
            self._start_web_admin_server()
        else:
            logger.warning("[WARN] 系统启动完成，但部分进程状态异常")

        return success

    def _verify_processes(self) -> bool:
        """验证关键进程状态（增强版：详细验证报告）"""
        # 只检查自动启动的关键进程
        critical_processes = [name for name in ["main_app", "django_server"]
                              if name in self.supervisor.processes and self.supervisor.processes[name].config.autostart]
        all_healthy = True

        logger.info("\n" + "=" * 60)
        logger.info("进程状态验证报告")
        logger.info("=" * 60)

        for process_name, process in self.supervisor.processes.items():
            status = self.supervisor.get_process_status(process_name)
            is_critical = process_name in critical_processes
            should_be_running = process.config.autostart  # 是否应该运行

            if status and status['status'] == 'running':
                health_icon = "[OK]" if status.get('health_check_failures', 0) == 0 else "[WARN]"
                uptime_str = f" (运行 {status['uptime_formatted']})" if status['uptime'] > 0 else ""
                pid_str = f"PID: {status['pid']}" if status['pid'] else "PID: N/A"

                logger.info(f"{health_icon} {process_name}: 运行中 {uptime_str} [{pid_str}]")

                # 显示资源使用情况
                if 'cpu_percent' in status and status['cpu_percent'] is not None:
                    logger.info(f"    CPU: {status['cpu_percent']}%, 内存：{status['memory_mb']}MB")
            else:
                status_str = status['status'] if status else 'unknown'
                # 只有应该运行的进程才标记为失败
                if should_be_running:
                    logger.warning(f"[FAIL] {process_name}: {status_str}" + (" [关键进程]" if is_critical else ""))
                    all_healthy = False
                else:
                    logger.info(f"[SKIP] {process_name}: {status_str} (手动启动模式)")

        logger.info("=" * 60 + "\n")

        # 检查关键进程
        for process_name in critical_processes:
            if process_name in self.supervisor.processes:
                status = self.supervisor.get_process_status(process_name)
                if not status or status['status'] != 'running':
                    logger.error(f"关键进程 {process_name} 未运行！")
                    all_healthy = False

        return all_healthy

    def _print_process_configurations(self):
        """打印所有进程配置"""
        logger.info("\n进程配置列表:")
        logger.info("-" * 60)

        for name, process in self.supervisor.processes.items():
            autostart_str = "自动启动" if process.config.autostart else "手动启动"
            command_str = " ".join(process.config.command)
            logger.info(f"  {name}:")
            logger.info(f"    命令：{command_str}")
            logger.info(f"    模式：{autostart_str}")
            logger.info(f"    重启限制：{process.config.restart_limit}次")
            if process.config.health_check and process.config.health_check.endpoint:
                logger.info(f"    健康检查：{process.config.health_check.endpoint}")

        logger.info("-" * 60 + "\n")

    def monitor_system(self):
        """监控系统运行状态"""
        logger.info("进入系统监控模式...")

        try:
            while self.running:
                # 定期输出系统状态
                if int(time.time()) % 30 == 0:  # 每30秒输出一次
                    self._print_system_status()

                time.sleep(1)

        except KeyboardInterrupt:
            logger.info("收到键盘中断信号")
        finally:
            self.shutdown()

    def _print_system_status(self):
        """打印系统状态（增强版：详细统计）"""
        if not self.supervisor:
            return

        statuses = self.supervisor.get_all_status()
        running_count = sum(1 for status in statuses.values()
                            if status['status'] == 'running')
        healthy_count = sum(1 for status in statuses.values()
                            if status['status'] == 'running' and status.get('health_check_failures', 0) == 0)

        logger.info(f"\n系统状态概览：{healthy_count}/{running_count}/{len(statuses)} (健康/运行/总计)")
    
        for name, status in statuses.items():
            if status['status'] == 'running':
                uptime_str = f" (运行 {status['uptime_formatted']})" if status['uptime'] > 0 else ""
                health_str = " [OK]" if status.get('health_check_failures',
                                                   0) == 0 else f" [WARN]({status.get('health_check_failures', 0)}次失败)"
                logger.info(f"  {name}: {status['status']}{uptime_str}{health_str}")
            else:
                logger.info(f"  {name}: {status['status']}")

    def shutdown(self):
        """关闭系统"""
        if not self.running:
            return

        logger.info("正在关闭系统...")
        self.running = False

        if self.supervisor:
            self.supervisor.shutdown()

        logger.info("系统已完全关闭")


def main():
    """启动器入口函数"""
    try:
        launcher = SupervisedLauncher()
        launcher.setup_signal_handlers()

        # 启动系统
        if not launcher.start_system():
            logger.error("系统启动失败")
            sys.exit(1)

        # 进入监控模式
        launcher.monitor_system()

    except Exception as e:
        logger.error(f"启动器运行异常: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
