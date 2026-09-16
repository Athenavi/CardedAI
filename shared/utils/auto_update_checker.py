#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动更新检查工具
检查 GitHub Releases 和本地更新包
"""


from datetime import datetime
from typing import Optional, Dict

import httpx
from aioitertools import asyncio

from src.unified_logger import default_logger as logger


class AutoUpdateChecker:
    """自动更新检查器（简化版）"""

    def __init__(self):
        self.github_repo = "Athenavi/fast_blog"
        self.current_version = "0.0.0"
        self.last_check_time = None

    async def check_github_releases(self) -> Optional[Dict]:
        """检查 GitHub Releases 获取最新版本"""
        try:
            url = f"https://api.github.com/repos/{self.github_repo}/releases/latest"
            headers = {
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'FastBlog-Update-Checker'
            }

            response = httpx.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            latest_version = data.get('tag_name', '').lstrip('vV')
            if not latest_version:
                return None

            return {
                'version': latest_version,
                'name': data.get('name', ''),
                'published_at': data.get('published_at', ''),
                'html_url': data.get('html_url', ''),
                'body': data.get('body', '')
            }

        except Exception as e:
            logger.error(f"检查 GitHub Releases 失败：{e}")
            return None

    async def check_local_releases(self) -> Optional[str]:
        """检查本地 releases 目录的最新版本"""
        try:
            from pathlib import Path

            project_root = Path(__file__).resolve().parent.parent.parent
            releases_dir = project_root / "releases"

            if not releases_dir.exists():
                return None

            update_packages = list(releases_dir.glob("update_*.zip"))
            if not update_packages:
                return None

            # 按文件名排序，获取最新版本
            update_packages.sort(key=lambda x: x.name, reverse=True)
            version = update_packages[0].stem.replace('update_', '')
            logger.info(f"本地最新版本：{version}")
            return version

        except Exception as e:
            logger.error(f"检查本地 releases 失败：{e}")
            return None

    @staticmethod
    def compare_versions(current: str, latest: str) -> bool:
        """比较版本号，有新版本返回 True"""
        try:
            def parse_version(v: str):
                v = v.lstrip('vV')
                parts = v.split('.')
                return [int(p) for p in parts if p.isdigit()]

            current_parts = parse_version(current)
            latest_parts = parse_version(latest)

            # 补齐长度
            max_len = max(len(current_parts), len(latest_parts))
            current_parts.extend([0] * (max_len - len(current_parts)))
            latest_parts.extend([0] * (max_len - len(latest_parts)))

            # 逐位比较
            for c, l in zip(current_parts, latest_parts):
                if l > c:
                    return True
                elif l < c:
                    return False

            return False

        except Exception as e:
            logger.error(f"版本比较失败：{e}")
            return False

    async def check_for_updates(self) -> Dict:
        """执行更新检查"""
        logger.info("开始检查更新...")
        self.last_check_time = datetime.now()

        # 获取当前版本
        try:
            from shared.utils.version_manager import version_manager
            backend_info = version_manager.get_backend_version()
            self.current_version = backend_info.get('version', '0.0.0')
        except Exception as e:
            logger.error(f"获取当前版本失败：{e}")
            self.current_version = "0.0.0"

        # 同时检查 GitHub 和本地
        github_result, local_version = await asyncio.gather(
            self.check_github_releases(),
            self.check_local_releases()
        )

        result = {
            'has_update': False,
            'current_version': self.current_version,
            'github_latest': None,
            'local_latest': local_version,
            'check_time': self.last_check_time.isoformat(),
            'message': '已是最新版本'
        }

        # 处理 GitHub 结果
        if github_result:
            result['github_latest'] = github_result['version']
            if self.compare_versions(self.current_version, github_result['version']):
                result['has_update'] = True
                result['message'] = f"发现新版本：{github_result['version']}"
                result['release_info'] = github_result

        # 检查本地更新
        if not result['has_update'] and local_version:
            if self.compare_versions(self.current_version, local_version):
                result['has_update'] = True
                result['message'] = f"发现本地更新包：{local_version}"

        logger.info(f"更新检查结果：{result['message']}")
        return result


# 全局单例
auto_update_checker = AutoUpdateChecker()


async def check_updates_now() -> Dict:
    """便捷函数：立即检查更新"""
    return await auto_update_checker.check_for_updates()
