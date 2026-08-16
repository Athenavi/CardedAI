# -*- coding: utf-8 -*-
"""
环境检测器 —— 检测本机外部服务可用性，并为 CardedAI 推荐最佳配置。

零外部依赖（仅标准库 socket），供 run.sh 在安装/启动前调用：

    python src/utils/environment_detector.py --detect-only   # 输出 JSON 检测报告
    python src/utils/environment_detector.py --recommend     # 输出 .env 推荐配置片段

设计原则：
- 只探测端口连通性（TCP connect），不做认证（密码未知）；
  认证与真实可用性由应用启动时自行处理（均有降级路径）。
- 检测结果仅作为"推荐"，用户已在 .env 中显式配置的值不会被覆盖。
"""

import argparse
import json
import socket
import sys
from typing import Dict, List, Optional

# 服务 -> (环境变量名, 默认端口)
SERVICES: Dict[str, Dict] = {
    "postgresql": {"env": "DB_ENGINE", "port": 5432, "label": "PostgreSQL"},
    "redis": {"env": "CACHE_TYPE", "port": 6379, "label": "Redis"},
    "milvus": {"env": "VECTOR_DB_TYPE", "port": 19530, "label": "Milvus"},
    "qdrant": {"env": "VECTOR_DB_TYPE", "port": 6333, "label": "Qdrant"},
    "meilisearch": {"env": "MEILISEARCH_HOST", "port": 7700, "label": "Meilisearch"},
}

# 推荐优先级：同组服务（如向量库）检测到多个时，按此顺序取第一个
VECTOR_PRIORITY = ["milvus", "qdrant"]


def _tcp_probe(host: str, port: int, timeout: float) -> bool:
    """TCP 端口连通性探测"""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def detect_services(host: str = "127.0.0.1", timeout: float = 0.8) -> Dict[str, bool]:
    """检测本机各外部服务是否可达，返回 {服务名: 是否可用}"""
    result = {}
    for name in SERVICES:
        result[name] = _tcp_probe(host, SERVICES[name]["port"], timeout)
    return result


def recommend_config(detection: Optional[Dict[str, bool]] = None) -> Dict[str, str]:
    """基于检测结果生成推荐配置（.env 键值对）。

    未检测到任何外部服务时，全部使用本地降级方案（SQLite + 内存缓存 + 本地向量）。
    """
    if detection is None:
        detection = detect_services()

    cfg: Dict[str, str] = {}

    # 数据库：检测到 PostgreSQL -> postgresql，否则 SQLite
    if detection.get("postgresql"):
        cfg["DB_ENGINE"] = "postgresql"
    else:
        cfg["DB_ENGINE"] = "sqlite"
        cfg["DB_PATH"] = "data/cardedai.db"

    # 缓存：检测到 Redis -> redis，否则内存缓存
    if detection.get("redis"):
        cfg["CACHE_TYPE"] = "redis"
    else:
        cfg["CACHE_TYPE"] = "simple"

    # 向量库：Milvus / Qdrant（按优先级），否则内置本地向量
    vector_backend = next((svc for svc in VECTOR_PRIORITY if detection.get(svc)), None)
    if vector_backend:
        cfg["VECTOR_DB_TYPE"] = vector_backend
    else:
        cfg["VECTOR_DB_TYPE"] = "local"

    # 搜索：检测到 Meilisearch 则启用，否则使用内置搜索（留空即可）
    if detection.get("meilisearch"):
        cfg["MEILISEARCH_HOST"] = "http://127.0.0.1:7700"

    return cfg


def format_env_block(cfg: Dict[str, str]) -> str:
    """将推荐配置格式化为 .env 片段"""
    lines = [
        "# ============================================================================",
        "# 环境自动检测推荐配置（由 environment_detector.py 生成）",
        "# 如需手动指定，请取消注释并修改对应行；已存在的配置不会被覆盖",
        "# ============================================================================",
    ]
    comments = {
        "DB_ENGINE": "# 数据库引擎: sqlite(默认) / postgresql",
        "DB_PATH": "# SQLite 数据库文件路径",
        "CACHE_TYPE": "# 缓存: simple(默认, 内存) / redis",
        "VECTOR_DB_TYPE": "# 向量存储: local(默认, 内置) / milvus / qdrant",
        "MEILISEARCH_HOST": "# Meilisearch 搜索服务地址（可选）",
    }
    for key, value in cfg.items():
        comment = comments.get(key, "")
        if comment:
            lines.append(comment)
        lines.append(f"{key}={value}")
    return "\n".join(lines) + "\n"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="CardedAI 环境检测器")
    parser.add_argument("--detect-only", action="store_true", help="仅输出 JSON 检测报告")
    parser.add_argument("--recommend", action="store_true", help="输出 .env 推荐配置片段")
    parser.add_argument("--host", default="127.0.0.1", help="检测主机地址（默认 127.0.0.1）")
    parser.add_argument("--timeout", type=float, default=0.8, help="单服务探测超时秒数（默认 0.8）")
    args = parser.parse_args(argv)

    detection = detect_services(args.host, args.timeout)

    if args.detect_only:
        report = {
            "host": args.host,
            "services": {
                name: {
                    "available": available,
                    "port": SERVICES[name]["port"],
                    "label": SERVICES[name]["label"],
                }
                for name, available in detection.items()
            },
        }
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    if args.recommend:
        cfg = recommend_config(detection)
        print(format_env_block(cfg))
        return 0

    # 默认：人类可读摘要
    print("CardedAI 环境检测报告")
    print("-" * 40)
    for name, available in detection.items():
        status = "✅ 可用" if available else "❌ 未检测到"
        print(f"  {SERVICES[name]['label']:<14} (端口 {SERVICES[name]['port']:<6}) {status}")
    print("-" * 40)
    cfg = recommend_config(detection)
    print("推荐配置：")
    for key, value in cfg.items():
        print(f"  {key}={value}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
