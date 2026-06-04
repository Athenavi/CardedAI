"""
FastBlog API v3 - 移动端专用API

为移动端App提供优化的API接口，包括：
- 文章阅读（列表、详情、分类浏览、搜索）
- 评论功能（查看、发表、回复、点赞）
- 用户管理（登录、注册、个人资料）
- 媒体上传（图片上传、压缩）
- 推送通知
- 离线缓存支持
"""

from fastapi import APIRouter

# v3 路由注册表：(模块路径, v3前缀, 标签列表, 是否必需)
ROUTE_REGISTRY_V3 = [
    # ==================== 认证模块 ====================
    ("src.api.v3.mobile.auth", "/api/v3/auth", ["mobile-auth"], True),

    # ==================== 文章模块 ====================
    ("src.api.v3.mobile.articles", "/api/v3/articles", ["mobile-articles"], True),

    # ==================== 评论模块 ====================
    ("src.api.v3.mobile.comments", "/api/v3/comments", ["mobile-comments"], True),

    # ==================== 用户模块 ====================
    ("src.api.v3.mobile.users", "/api/v3/users", ["mobile-users"], True),

    # ==================== 媒体模块 ====================
    ("src.api.v3.mobile.media", "/api/v3/media", ["mobile-media"], True),

    # ==================== 分类模块 ====================
    ("src.api.v3.mobile.categories", "/api/v3/categories", ["mobile-categories"], True),
]


def register_v3_routes(app):
    """注册v3移动端API路由"""
    from importlib import import_module

    for module_path, prefix, tags, required in ROUTE_REGISTRY_V3:
        try:
            module = import_module(module_path)
            if hasattr(module, 'router'):
                app.include_router(module.router, prefix=prefix, tags=tags)
                print(f"[V3 API] Registered: {prefix}")
            else:
                print(f"[V3 API] Warning: No router found in {module_path}")
        except Exception as e:
            if required:
                print(f"[V3 API] Error: Failed to load required module {module_path}: {e}")
                raise
            else:
                print(f"[V3 API] Warning: Failed to load optional module {module_path}: {e}")


# 创建主路由器
router = APIRouter(prefix="/api/v3", tags=["mobile-api-v3"])
