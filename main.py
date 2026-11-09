# -*- coding: utf-8 -*-
"""
FastAPI 应用入口点（精简版）
"""

import argparse
import os
import signal
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).resolve().parent))

_ENV_ALIASES = {
    "prod": "production",
    "production": "production",
    "dev": "development",
    "development": "development",
    "test": "testing",
    "testing": "testing",
}


def _scan_env_arg(argv):
    """从 argv 中读取 --env 的值，返回原始字符串或 None。

    必须是手工解析：ENVIRONMENT 需要在导入 src.* 之前写入，
    否则 src.setting.load_dotenv() 与 src.app 的中间件判断会先读到 .env 的值。
    """
    for index, item in enumerate(argv):
        if item == "--env" and index + 1 < len(argv):
            return argv[index + 1]
        if item.startswith("--env="):
            return item.split("=", 1)[1]
    return None


def _normalize_env(value):
    """把 prod/dev/test 等简写规范化为完整环境名，无法识别时返回 None"""
    if not value:
        return None
    key = str(value).strip().lower()
    return _ENV_ALIASES.get(key)


# 命令行 --env 优先级最高；未指定时保留已有环境变量（.env 由 dotenv 加载）。
_CLI_ENV = _normalize_env(_scan_env_arg(sys.argv))
if _CLI_ENV:
    # load_dotenv 默认不覆盖已存在的环境变量，这里显式写入即可压过 .env
    os.environ["ENVIRONMENT"] = _CLI_ENV

_ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")

# 全局 FastAPI 应用实例（供外部工具使用）
# 注意：src.app 在模块导入时就会按 ENVIRONMENT 创建实例，这里直接复用，
# 不再二次 create_app()，否则每次启动都会完整初始化两遍（中间件、路由、
# 懒加载、数据库探测），显著拖慢启动并浪费内存。
try:
    from src.app import app

    print(f"[Main] FastAPI app ready (env={_ENVIRONMENT})")
except Exception as e:
    import traceback
    print(f"[Main] Error creating app: {e}")
    traceback.print_exc()
    app = None

# 使用统一的日志系统
from src.unified_logger import default_logger as logger


def parse_arguments():
    parser = argparse.ArgumentParser(description='启动 FastBlog 应用')
    parser.add_argument('--mode', choices=['app', 'supervisor'], default='app')
    parser.add_argument('--port', type=int, default=9421)
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--nolog', action='store_true', default=False)
    # 默认 None：未显式指定时沿用 .env 中的 ENVIRONMENT，避免覆盖本地配置
    parser.add_argument('--env', choices=['prod', 'dev', 'test'], default=None)
    return parser.parse_args()


def setup_signal_handlers():
    def handler(signum, frame):
        logger.info(f"收到信号 {signum}，正在退出...")
        sys.exit(0)

    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)


def main():
    setup_signal_handlers()
    args = parse_arguments()
    # 日志系统已由 unified_logger 初始化，无需再次初始化

    logger.info(f"启动 FastAPI 后端，端口 {args.port}，环境 {_ENVIRONMENT}")

    if app is None:
        logger.error("FastAPI 应用实例创建失败")
        sys.exit(1)

    try:
        import uvicorn

        logger.info("FastAPI 应用已加载，准备启动服务器...")
        logger.info(f"服务器地址: http://{args.host}:{args.port}")

        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            log_level="info",
            reload=False,
            workers=1,
            # 默认仅信任 127.0.0.1 转发头；置于 nginx 之后时需设置
            # FORWARDED_ALLOW_IPS=<nginx 出口 IP>（或容器网段），
            # 否则 request.url.scheme 恒为 http，Secure Cookie 永不下发。
            forwarded_allow_ips=os.environ.get("FORWARDED_ALLOW_IPS", "127.0.0.1"),
        )
    except KeyboardInterrupt:
        logger.info("服务器已关闭")
    except Exception as e:
        logger.error(f"FastAPI 启动失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
