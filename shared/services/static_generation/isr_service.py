"""
增量静态再生成 (ISR) 服务
支持在内容更新后自动触发前端页面的重新构建
"""
import httpx

from src.setting import app_config


class ISRService:
    """ISR 核心逻辑"""

    @staticmethod
    async def revalidate_path(path: str):
        """请求前端重新验证并生成指定路径的页面"""
        frontend_url = app_config.get("frontend", {}).get("url", "http://localhost:4321")
        try:
            async with httpx.AsyncClient() as client:
                # 调用 Astro 或 Next.js 的 ISR 端点
                await client.post(f"{frontend_url}/api/revalidate", json={"path": path})
        except Exception as e:
            print(f"ISR revalidation failed for {path}: {e}")

    @staticmethod
    async def on_article_update(slug: str):
        """文章更新时的 ISR 触发器"""
        # 1. 重新验证文章详情页
        await ISRService.revalidate_path(f"/article/{slug}")
        # 2. 重新验证首页和分类页（因为列表可能发生变化）
        await ISRService.revalidate_path("/")
        await ISRService.revalidate_path("/archive")


isr_service = ISRService()
