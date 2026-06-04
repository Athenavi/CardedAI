"""
V1 到 V2 API 重定向中间件

提供向后兼容性，将旧的 v1 路由自动重定向到新的 v2 路由。
支持：
1. 精确路径匹配重定向
2. 模式匹配重动态路径
3. 保留查询参数
4. 可选的 301/302 重定向类型
"""
import re
from typing import Dict, Optional, Tuple
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse


class V1ToV2RedirectMiddleware(BaseHTTPMiddleware):
    """
    V1 到 V2 API 重定向中间件
    
    功能：
    - 拦截所有 /api/v1/* 请求
    - 根据映射表重定向到对应的 /api/v2/* 路径
    - 保留原始查询参数和 HTTP 方法
    - 记录重定向日志用于后续清理
    """

    def __init__(self, app, redirect_type: int = 301, enable_logging: bool = True):
        """
        初始化中间件
        
        Args:
            app: FastAPI 应用实例
            redirect_type: 重定向类型 (301=永久, 302=临时)
            enable_logging: 是否启用重定向日志
        """
        super().__init__(app)
        self.redirect_type = redirect_type
        self.enable_logging = enable_logging
        self.redirect_count = 0

        # 加载重定向映射
        from src.api.v2 import V1_TO_V2_REDIRECT_MAP
        self.redirect_map = V1_TO_V2_REDIRECT_MAP

        # 编译正则表达式模式（用于动态路径匹配）
        self.pattern_map = {}
        for pattern_str, replacement in self.redirect_map.items():
            if '{' in pattern_str:
                # 转换 {param} 为正则捕获组 (?P<param>[^/]+)
                regex_pattern = pattern_str.replace('{', '(?P<').replace('}', '>[^/]+)')
                self.pattern_map[re.compile(f'^{regex_pattern}$')] = replacement

    async def dispatch(self, request: Request, call_next):
        """
        处理请求，检查是否需要重定向
        
        Args:
            request: FastAPI 请求对象
            call_next: 下一个处理器
            
        Returns:
            重定向响应或继续处理
        """
        path = request.url.path
        method = request.method

        # 只处理 GET/POST/PUT/DELETE/PATCH 等标准方法的 v1 API 请求
        if not path.startswith('/api/v1/'):
            return await call_next(request)

        # 尝试精确匹配
        v2_path = self._find_redirect_target(path)

        if v2_path:
            # 构建新的 URL，保留查询参数
            query_string = request.url.query
            new_url = f"{v2_path}"
            if query_string:
                new_url += f"?{query_string}"

            # 记录重定向日志
            if self.enable_logging:
                self.redirect_count += 1
                print(f"[V1->V2 Redirect #{self.redirect_count}] "
                      f"{method} {path} -> {new_url}")

            # 返回重定向响应
            return RedirectResponse(
                url=new_url,
                status_code=self.redirect_type,
                headers={
                    "X-Redirect-From": path,
                    "X-Redirect-To": v2_path,
                    "X-API-Version-Migration": "v1-to-v2"
                }
            )

        # 如果没有匹配的重定向规则，继续正常处理
        return await call_next(request)

    def _find_redirect_target(self, v1_path: str) -> Optional[str]:
        """
        查找 v1 路径对应的 v2 目标路径
        
        Args:
            v1_path: v1 API 路径
            
        Returns:
            v2 API 路径，如果未找到则返回 None
        """
        # 1. 精确匹配
        if v1_path in self.redirect_map:
            return self.redirect_map[v1_path]

        # 2. 模式匹配（动态路径）
        for pattern, replacement_template in self.pattern_map.items():
            match = pattern.match(v1_path)
            if match:
                # 替换模板中的命名捕获组
                result = replacement_template
                for param_name, param_value in match.groupdict().items():
                    result = result.replace(f'{{{param_name}}}', param_value)
                return result

        # 3. 前缀匹配（通用规则）
        # 如果 v1 路径以某个已知模块前缀开头，尝试智能转换
        module_prefixes = {
            '/api/v1/users/': '/api/v2/users/',
            '/api/v1/articles/': '/api/v2/articles/',
            '/api/v1/categories/': '/api/v2/categories/',
            '/api/v1/comments/': '/api/v2/comments/',
            '/api/v1/chats/': '/api/v2/chats/',
            '/api/v1/messages/': '/api/v2/messages/',
            '/api/v1/notifications/': '/api/v2/notifications/',
            '/api/v1/shop/': '/api/v2/shop/',
            '/api/v1/media/': '/api/v2/media/',
            '/api/v1/seo/': '/api/v2/seo/',
            '/api/v1/security/': '/api/v2/security/',
            '/api/v1/admin/': '/api/v2/admin/',
            '/api/v2/themes/': '/api/v2/themes/',
            '/api/v2/translations/': '/api/v2/translations/',
            '/api/v2/integrations/': '/api/v2/integrations/',
            '/api/v2/ads/': '/api/v2/ads/',
            '/api/v2/monitoring/': '/api/v2/monitoring/',
            '/api/v2/cache/': '/api/v2/cache/',
            '/api/v2/cdn/': '/api/v2/cdn/',
            '/api/v2/backup/': '/api/v2/backup/',
            '/api/v2/gdpr/': '/api/v2/gdpr/',
            '/api/v2/ext/': '/api/v2/ext/',
            '/api/v2/dashboard/': '/api/v2/dashboard/',
            '/api/v2/system/': '/api/v2/system/',
            '/api/v2/workflow/': '/api/v2/workflow/',
            '/api/v2/payments/': '/api/v2/payments/',
            '/api/v2/accessibility/': '/api/v2/accessibility/',
            '/api/v2/amp/': '/api/v2/amp/',
            '/api/v2/misc/': '/api/v2/misc/',
            '/api/v2/feed/': '/api/v2/feed/',
            '/api/v2/search/': '/api/v2/search/',
            '/api/v2/analytics/': '/api/v2/analytics/',
            '/api/v2/social/': '/api/v2/social/',
            '/api/v2/membership/': '/api/v2/membership/',
            '/api/v2/install/': '/api/v2/install/',
            '/api/v2/sites/': '/api/v2/sites/',
            '/api/v2/static-site/': '/api/v2/static-site/',
            '/api/v2/cms/': '/api/v2/cms/',
            '/api/v2/collaboration/': '/api/v2/collaboration/',
            '/api/v2/optimization/': '/api/v2/optimization/',
        }

        for v1_prefix, v2_prefix in module_prefixes.items():
            if v1_path.startswith(v1_prefix):
                # 提取后缀部分
                suffix = v1_path[len(v1_prefix):]
                # 特殊处理：某些模块需要额外映射
                mapped_suffix = self._map_module_suffix(v1_prefix, suffix)
                return f"{v2_prefix}{mapped_suffix}"

        return None

    def _map_module_suffix(self, module_prefix: str, suffix: str) -> str:
        """
        映射模块特定的路径后缀
        
        Args:
            module_prefix: 模块前缀
            suffix: 路径后缀
            
        Returns:
            映射后的后缀
        """
        # 这里可以添加特定模块的路径转换逻辑
        # 目前直接返回原后缀，保持路径结构不变
        return suffix

    def get_redirect_stats(self) -> Dict[str, int]:
        """获取重定向统计信息"""
        return {
            "total_redirects": self.redirect_count,
            "redirect_type": self.redirect_type,
            "mapping_rules_count": len(self.redirect_map),
            "pattern_rules_count": len(self.pattern_map)
        }


def create_v1_to_v2_middleware(app, redirect_type: int = 301, enable_logging: bool = True):
    """
    工厂函数：创建 V1 到 V2 重定向中间件
    
    Args:
        app: FastAPI 应用实例
        redirect_type: 重定向类型 (301=永久, 302=临时)
        enable_logging: 是否启用日志
        
    Returns:
        配置好的中间件实例
    """
    return V1ToV2RedirectMiddleware(
        app,
        redirect_type=redirect_type,
        enable_logging=enable_logging
    )
