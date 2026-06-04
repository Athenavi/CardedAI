"""
V2 聚合路由器懒加载工具

提供 create_lazy_router 工具函数，将 V2 聚合路由器的 V1 子模块导入延迟到
首次访问 router 属性时才执行，大幅减少启动时的级联导入开销。
"""

import importlib
from typing import List, Tuple, Optional

from fastapi import APIRouter


def create_lazy_router(
    tags: List[str],
    sub_routers: List[Tuple[str, str, str]],
    extra_routers: Optional[List[Tuple[str, str]]] = None,
) -> APIRouter:
    """
    创建懒加载聚合路由器。

    只有当 router 的 routes/paths 等属性被实际访问时（即 register_all_routes 中
    app.include_router(router) 时），才会真正导入 V1 子模块并构建路由树。

    Args:
        tags: 路由标签列表
        sub_routers: 子路由列表，每项为 (模块路径, 属性名, URL前缀)
            例如: ("src.api.v1.security.rbac", "router", "/rbac")
        extra_routers: 额外的子路由列表（不需要 prefix 的），每项为 (模块路径, 属性名)

    Returns:
        APIRouter: 懒加载的聚合路由器
    """
    _loaded = False
    _router = APIRouter(tags=tags)

    def _ensure_loaded():
        nonlocal _loaded
        if _loaded:
            return
        _loaded = True

        for module_path, attr_name, prefix in sub_routers:
            try:
                mod = importlib.import_module(module_path)
                sub = getattr(mod, attr_name, None)
                if sub is not None:
                    _router.include_router(sub, prefix=prefix)
            except ImportError as e:
                import logging
                logging.getLogger(__name__).warning(
                    f"[V2 lazy] 子路由 {module_path} 加载失败: {e}"
                )
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(
                    f"[V2 lazy] 子路由 {module_path} 注册异常: {e}"
                )

        if extra_routers:
            for module_path, attr_name in extra_routers:
                try:
                    mod = importlib.import_module(module_path)
                    sub = getattr(mod, attr_name, None)
                    if sub is not None:
                        _router.include_router(sub)
                except ImportError as e:
                    import logging
                    logging.getLogger(__name__).warning(
                        f"[V2 lazy] 额外路由 {module_path} 加载失败: {e}"
                    )

    # 用属性代理拦截对 router 的访问，触发懒加载
    class _LazyRouterProxy:
        """代理 FastAPI APIRouter，首次访问 routes 时触发子路由加载"""

        def __getattr__(self, name):
            # 访问任何路由相关属性时触发加载
            if name in ('routes', 'on_startup', 'on_shutdown', 'dependency_overrides',
                        'include_router', 'add_api_route', 'add_route'):
                _ensure_loaded()
            return getattr(_router, name)

        def __repr__(self):
            return f"<LazyRouter tags={tags}>"

    return _LazyRouterProxy()
