#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastBlog 进程监督器 Web 管理界面启动器
独立运行的 Web 管理服务器
"""


import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

try:
    import uvicorn
    from process_supervisor.web_admin import app, set_supervisor
    from process_supervisor.process_manager import get_supervisor

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    from src.unified_logger import default_logger as logger


    def main():
        """启动 Web 管理界面"""
        try:
            logger.info("=" * 60)
            logger.info("FastBlog 进程监督器 Web 管理界面")
            logger.info("=" * 60)

            # 初始化监督器（只读模式，不启动实际进程）
            logger.info("初始化进程监督器（只读模式）...")
            supervisor = get_supervisor()
            set_supervisor(supervisor)

            logger.info("[OK] 监督器已连接")
            logger.info("")
            logger.info("Web 管理界面启动成功！")
            logger.info("访问地址：http://127.0.0.1:9422")
            logger.info("API 文档：http://127.0.0.1:9422/docs")
            logger.info("=" * 60)

            # 启动 Web 服务器
            uvicorn.run(
                app,
                host="127.0.0.1",
                port=9422,
                log_level="info"
            )

        except KeyboardInterrupt:
            logger.info("\n收到中断信号，正在关闭...")
        except Exception as e:
            logger.error(f"启动失败：{e}")
            import traceback
            logger.error(traceback.format_exc())
            sys.exit(1)


    if __name__ == "__main__":
        main()

except ImportError as e:
    print(f"错误：缺少必要的依赖包 - {e}")
    print("请安装 FastAPI 和 uvicorn:")
    print("  pip install fastapi uvicorn")
    sys.exit(1)
