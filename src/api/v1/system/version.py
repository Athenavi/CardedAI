"""
版本管理 API
提供系统版本信息查询功能
"""


from fastapi import APIRouter

from src.unified_logger import default_logger as logger

router = APIRouter(tags=["system-version"])


def get_version_from_update_server(request_type: str):
    """从更新服务器获取版本信息"""
    import httpx

    try:
        # 更新服务器地址
        update_server_url = "http://127.0.0.1:8001"
        endpoint_map = {
            'full': '/api/v1/version/full',
            'frontend': '/api/v1/version/frontend',
            'backend': '/api/v1/version/backend'
        }

        endpoint = endpoint_map.get(request_type, '/api/v1/version/full')
        url = f"{update_server_url}{endpoint}"

        response = httpx.get(url, timeout=10)
        response.raise_for_status()

        return {
            'success': True,
            'data': response.json()
        }
    except Exception as e:
        logger.error(f"从更新服务器获取版本信息失败: {e}")
        return {
            'success': False,
            'error': str(e),
            'data': None
        }


@router.get('/full')
async def get_version_info():
    """获取完整的版本信息"""
    return get_version_from_update_server('full')


@router.get('/frontend')
async def get_frontend_version():
    """获取前端版本信息"""
    return get_version_from_update_server('frontend')


@router.get('/backend')
async def get_backend_version():
    """获取后端版本信息"""
    return get_version_from_update_server('backend')
