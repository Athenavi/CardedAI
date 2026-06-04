"""
Edge Functions 服务

功能：
1. Edge Function 注册和管理
2. Cloudflare Workers 部署支持
3. Vercel Edge Functions 支持
4. 边缘缓存策略
"""
import json
import os
from typing import Dict, List, Optional, Callable
from datetime import datetime


class EdgeFunction:
    """
    Edge Function 定义
    """

    def __init__(
            self,
            name: str,
            handler: Callable,
            route: str,
            cache_ttl: int = 0,
            description: str = ""
    ):
        self.name = name
        self.handler = handler
        self.route = route
        self.cache_ttl = cache_ttl
        self.description = description
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'route': self.route,
            'cache_ttl': self.cache_ttl,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }


class EdgeFunctionsService:
    """
    Edge Functions 管理服务
    """

    def __init__(self):
        # 注册的 Edge Functions
        self.functions: Dict[str, EdgeFunction] = {}

        # 函数路由映射 {route: function_name}
        self.route_map: Dict[str, str] = {}

        # 缓存配置
        self.cache_config: Dict[str, dict] = {}

    def register_function(
            self,
            name: str,
            handler: Callable,
            route: str,
            cache_ttl: int = 0,
            description: str = ""
    ) -> EdgeFunction:
        """
        注册 Edge Function
        
        Args:
            name: 函数名称
            handler: 处理函数
            route: 路由路径
            cache_ttl: 缓存时间（秒）
            description: 函数描述
            
        Returns:
            EdgeFunction 实例
        """
        func = EdgeFunction(
            name=name,
            handler=handler,
            route=route,
            cache_ttl=cache_ttl,
            description=description
        )

        self.functions[name] = func
        self.route_map[route] = name

        # 配置缓存
        if cache_ttl > 0:
            self.cache_config[name] = {
                'ttl': cache_ttl,
                'strategy': 'edge',
            }

        return func

    def get_function(self, name: str) -> Optional[EdgeFunction]:
        """获取函数"""
        return self.functions.get(name)

    def get_function_by_route(self, route: str) -> Optional[EdgeFunction]:
        """根据路由获取函数"""
        func_name = self.route_map.get(route)
        if func_name:
            return self.functions.get(func_name)
        return None

    def list_functions(self) -> List[dict]:
        """列出所有函数"""
        return [func.to_dict() for func in self.functions.values()]

    def remove_function(self, name: str) -> bool:
        """移除函数"""
        if name in self.functions:
            func = self.functions[name]
            if func.route in self.route_map:
                del self.route_map[func.route]
            if name in self.cache_config:
                del self.cache_config[name]
            del self.functions[name]
            return True
        return False

    def generate_cloudflare_worker(self, output_dir: str = "edge-functions/cf") -> str:
        """
        生成 Cloudflare Workers 代码
        
        Args:
            output_dir: 输出目录
            
        Returns:
            生成的文件路径
        """
        os.makedirs(output_dir, exist_ok=True)

        worker_code = self._generate_cf_worker_code()
        output_file = os.path.join(output_dir, "worker.js")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(worker_code)

        # 生成 wrangler.toml 配置文件
        wrangler_config = self._generate_wrangler_toml()
        wrangler_file = os.path.join(output_dir, "wrangler.toml")

        with open(wrangler_file, 'w', encoding='utf-8') as f:
            f.write(wrangler_config)

        return output_file

    def generate_vercel_edge_function(self, output_dir: str = "edge-functions/vercel") -> str:
        """
        生成 Vercel Edge Function 代码
        
        Args:
            output_dir: 输出目录
            
        Returns:
            生成的文件路径
        """
        os.makedirs(output_dir, exist_ok=True)

        for name, func in self.functions.items():
            edge_code = self._generate_vercel_edge_code(func)
            output_file = os.path.join(output_dir, f"{name}.js")

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(edge_code)

        # 生成 vercel.json 配置
        vercel_config = self._generate_vercel_json()
        vercel_file = os.path.join(output_dir, "vercel.json")

        with open(vercel_file, 'w', encoding='utf-8') as f:
            f.write(vercel_config)

        return output_dir

    def _generate_cf_worker_code(self) -> str:
        """生成 Cloudflare Worker 代码"""
        routes_config = json.dumps([
            {
                'route': func.route,
                'name': func.name,
                'cache_ttl': func.cache_ttl,
            }
            for func in self.functions.values()
        ], indent=2)

        return f"""// Cloudflare Worker - Auto-generated by FastBlog
// Generated at: {datetime.now().isoformat()}

const ROUTES_CONFIG = {routes_config};

addEventListener('fetch', event => {{
  event.respondWith(handleRequest(event.request));
}});

async function handleRequest(request) {{
  const url = new URL(request.url);
  const pathname = url.pathname;
  
  // 查找匹配的路由
  const matchedRoute = ROUTES_CONFIG.find(route => {{
    if (route.route === pathname) return true;
    if (route.route.endsWith('*')) {{
      return pathname.startsWith(route.route.slice(0, -1));
    }}
    return false;
  }});
  
  if (!matchedRoute) {{
    return new Response('Not Found', {{ status: 404 }});
  }}
  
  // 检查缓存
  const cache = caches.default;
  const cacheKey = new Request(request.url, request);
  
  if (matchedRoute.cache_ttl > 0) {{
    let cachedResponse = await cache.match(cacheKey);
    if (cachedResponse) {{
      return cachedResponse;
    }}
  }}
  
  // 转发请求到源站
  const response = await fetch(request);
  
  // 缓存响应
  if (matchedRoute.cache_ttl > 0) {{
    const cachedResponse = response.clone();
    cachedResponse.headers.set('Cache-Control', `public, max-age=${{matchedRoute.cache_ttl}}`);
    event.waitUntil(cache.put(cacheKey, cachedResponse));
  }}
  
  return response;
}}
"""

    def _generate_wrangler_toml(self) -> str:
        """生成 wrangler.toml 配置"""
        return """# Cloudflare Workers 配置
name = "fastblog-edge"
main = "worker.js"
compatibility_date = "2024-01-01"

# 环境变量
[vars]
API_BASE_URL = "https://your-api-domain.com"

# 路由配置
[[routes]]
pattern = "your-domain.com/*"
zone_name = "your-domain.com"
"""

    def _generate_vercel_edge_code(self, func: EdgeFunction) -> str:
        """生成 Vercel Edge Function 代码"""
        return f"""// Vercel Edge Function - {func.name}
// Auto-generated by FastBlog
// {func.description}

export const config = {{
  runtime: 'edge',
}};

export default async function handler(request) {{
  const url = new URL(request.url);
  
  // 缓存配置
  const cacheTTL = {func.cache_ttl};
  
  if (cacheTTL > 0) {{
    return new Response(
      JSON.stringify({{ message: 'Edge Function: {func.name}' }}),
      {{
        status: 200,
        headers: {{
          'Content-Type': 'application/json',
          'Cache-Control': `public, s-maxage=${{cacheTTL}}, stale-while-revalidate=${{cacheTTL * 2}}`,
        }},
      }}
    );
  }}
  
  return new Response(
    JSON.stringify({{ message: 'Edge Function: {func.name}' }}),
    {{
      status: 200,
      headers: {{
        'Content-Type': 'application/json',
      }},
    }}
  );
}}
"""

    def _generate_vercel_json(self) -> str:
        """生成 vercel.json 配置"""
        routes = [
            {
                "src": func.route,
                "dest": f"/api/edge/{func.name}",
            }
            for func in self.functions.values()
        ]

        config = {
            "version": 2,
            "functions": {
                f"edge-functions/vercel/{name}.js": {
                    "runtime": "edge",
                }
                for name in self.functions.keys()
            },
            "routes": routes,
        }

        return json.dumps(config, indent=2)


# 全局实例
edge_functions_service = EdgeFunctionsService()
