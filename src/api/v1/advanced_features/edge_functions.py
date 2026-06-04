"""
Edge Functions API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from shared.services.integrations.edge_functions import edge_functions_service

router = APIRouter(tags=["edge-functions"])


class RegisterFunctionRequest(BaseModel):
    """注册函数请求"""
    name: str
    route: str
    cache_ttl: int = 0
    description: str = ""


@router.get("/list")
async def list_functions():
    """
    列出所有 Edge Functions

    Returns:
        函数列表
    """
    try:
        functions = edge_functions_service.list_functions()

        return {
            'success': True,
            'data': functions,
            'count': len(functions),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/register")
async def register_function(request: RegisterFunctionRequest):
    """
    注册 Edge Function

    Args:
        request: 函数配置

    Returns:
        注册结果
    """
    try:
        # 创建一个简单的处理函数（实际项目中应该从插件或配置文件加载）
        def default_handler(req):
            return {'message': f'Edge Function: {request.name}'}

        func = edge_functions_service.register_function(
            name=request.name,
            handler=default_handler,
            route=request.route,
            cache_ttl=request.cache_ttl,
            description=request.description
        )

        return {
            'success': True,
            'data': func.to_dict(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/items/{function_name}")
async def remove_function(function_name: str):
    """
    移除 Edge Function

    Args:
        function_name: 函数名称

    Returns:
        操作结果
    """
    try:
        success = edge_functions_service.remove_function(function_name)

        if not success:
            raise HTTPException(status_code=404, detail=f"Function '{function_name}' not found")

        return {
            'success': True,
            'message': f"Function '{function_name}' removed",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/cloudflare")
async def generate_cloudflare_worker():
    """
    生成 Cloudflare Workers 代码

    Returns:
        生成结果
    """
    try:
        output_file = edge_functions_service.generate_cloudflare_worker()

        return {
            'success': True,
            'data': {
                'output_file': output_file,
                'message': 'Cloudflare Worker code generated successfully',
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/vercel")
async def generate_vercel_edge_functions():
    """
    生成 Vercel Edge Functions 代码

    Returns:
        生成结果
    """
    try:
        output_dir = edge_functions_service.generate_vercel_edge_function()

        return {
            'success': True,
            'data': {
                'output_dir': output_dir,
                'message': 'Vercel Edge Functions code generated successfully',
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 注册一些示例 Edge Functions
def register_default_functions():
    """注册默认的 Edge Functions"""

    # 文章缓存函数
    def article_cache_handler(request):
        return {'type': 'article_cache'}

    edge_functions_service.register_function(
        name='article-cache',
        handler=article_cache_handler,
        route='/api/articles/*',
        cache_ttl=300,  # 5分钟缓存
        description='Cache article API responses at edge'
    )

    # 首页缓存函数
    def homepage_cache_handler(request):
        return {'type': 'homepage_cache'}

    edge_functions_service.register_function(
        name='homepage-cache',
        handler=homepage_cache_handler,
        route='/',
        cache_ttl=60,  # 1分钟缓存
        description='Cache homepage at edge'
    )

    # 静态资源缓存函数
    def static_cache_handler(request):
        return {'type': 'static_cache'}

    edge_functions_service.register_function(
        name='static-cache',
        handler=static_cache_handler,
        route='/api/v2/static/*',
        cache_ttl=86400,  # 24小时缓存
        description='Cache static assets at edge'
    )


# 自动注册默认函数
register_default_functions()
