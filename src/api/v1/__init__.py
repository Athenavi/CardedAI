import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi import APIRouter, Request, Depends, Query, HTTPException
from fastapi.logger import logger
from fastapi.responses import FileResponse, JSONResponse

api_v1_router = APIRouter(prefix="/api/v1", tags=["api-v1"])


# ------------------------------------------------------------
# QR 登录相关（延迟导入依赖）
# ------------------------------------------------------------
@api_v1_router.get("/qr/generate")
async def api_generate_qr(request: Request):
    from src.api.v1.user_utils.qrlogin_utils import qr_login
    from src.extensions import cache
    from src.setting import app_config
    try:
        callback_domain = request.query_params.get('callback_domain')

        if callback_domain:
            request_domain = callback_domain
        else:
            host = request.headers.get('host', 'localhost:9421')
            scheme = request.url.scheme

            forwarded_proto = request.headers.get('x-forwarded-proto')
            forwarded_host = request.headers.get('x-forwarded-host')

            if forwarded_proto:
                scheme = forwarded_proto
            if forwarded_host:
                host = forwarded_host

            request_domain = f"{scheme}://{host}/"

        return await qr_login(
            request,
            "1.0",
            app_config.global_encoding,
            request_domain,
            cache
        )
    except Exception as e:
        logger.error(f"QR generation failed: {e}", exc_info=True)
        return {"success": False, "message": f"Failed to generate QR code: {str(e)}"}


@api_v1_router.get("/qr/status")
async def api_check_qr_status(request: Request):
    from src.api.v1.user_utils.qrlogin_utils import check_qr_login_back
    from src.extensions import cache
    try:
        return await check_qr_login_back(request, cache)
    except Exception as e:
        logger.error(f"QR status check failed: {e}")
        return {"success": False, "message": "Failed to check QR code status"}


@api_v1_router.get("/phone/verify")
async def api_phone_verify(
        request: Request,
    db=Depends(lambda: __import__('src.extensions', fromlist=['get_async_db_session']).get_async_db_session()),
):
    from src.api.v1.user_utils.qrlogin_utils import phone_scan_back
    from src.auth import get_current_user
    from src.extensions import cache
    try:
        current_user = await get_current_user(request, db)
    except HTTPException as e:
        if e.status_code == 401:
            return {
                "success": False,
                "requires_auth": True,
                "message": "User not authenticated. Please log in to continue.",
                "action": "redirect_to_login",
            }
        raise e
    try:
        return await phone_scan_back(request, current_user=current_user, cache=cache)
    except Exception as e:
        logger.error(f"Phone verify failed: {e}")
        return {"success": False, "message": f"Failed to handle phone verification: {str(e)}"}


# 用户名/邮箱可用性检查
@api_v1_router.get("/check-username")
async def api_check_username(username: str, db=Depends(
    lambda: __import__('src.extensions', fromlist=['get_async_db_session']).get_async_db_session())):
    from shared.models import User
    from sqlalchemy import func, select
    try:
        existing = await db.scalar(
            select(User).where(func.lower(User.username) == func.lower(username))
        )
        return JSONResponse({"success": True, "available": existing is None, "exists": existing is not None})
    except Exception as e:
        logger.error(f"Check username error: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@api_v1_router.get("/check-email")
async def api_check_email(email: str, db=Depends(
    lambda: __import__('src.extensions', fromlist=['get_async_db_session']).get_async_db_session())):
    from shared.models import User
    from sqlalchemy import func, select
    try:
        existing = await db.scalar(
            select(User).where(func.lower(User.email) == func.lower(email))
        )
        return JSONResponse({"success": True, "available": existing is None, "exists": existing is not None})
    except Exception as e:
        logger.error(f"Check email error: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


# 公共缩略图（已废弃，请使用 /api/v2/media/{media_id}/thumbnail）
@api_v1_router.get("/thumbnail", deprecated=True)
async def public_media_thumbnail(
        request: Request,
        data: str = Query(...)
):
    """
    ⚠️ 此 API 已废弃

    请使用新的基于 media_id 的 API: GET /api/v2/media/{media_id}/thumbnail

    旧 API 使用文件 hash 作为参数，新 API 使用媒体 ID，更加 RESTful 且易于管理。
    """
    import traceback
    from fastapi.responses import Response
    from shared.utils.logger import get_logger
    from src.utils.security.safe import is_valid_hash

    logger = get_logger(__name__)

    try:
        logger.info("=" * 80)
        logger.info(f"收到缩略图请求")
        logger.info(f"  原始 data 参数: {data}")
        logger.info(f"  请求 URL: {request.url}")
        logger.info(f"  请求头: {dict(request.headers)}")

        clean_data = data.split(".")[0]
        logger.info(f"  清理后的 hash: {clean_data}")

        if not is_valid_hash(64, clean_data):
            logger.error(f"  [ERROR] Hash 验证失败: {clean_data}")
            raise HTTPException(status_code=400, detail="无效的文件哈希")

        data = clean_data
        thumb_path = Path(f"storage/thumbnails/{data[:2]}/{data}.jpg")
        logger.info(f"  缩略图路径: {thumb_path.absolute()}")
        logger.info(f"  缩略图存在: {thumb_path.exists()}")

        # 如果缩略图不存在，尝试生成
        if not thumb_path.exists():
            logger.info(f"  → 缩略图不存在，开始生成流程")

            # 尝试查找原始文件（可能带扩展名或不带扩展名）
            original_dir = Path(f"storage/objects/{data[:2]}")
            original_path = None

            # 首先尝试不带扩展名的路径
            path_without_ext = original_dir / data
            if path_without_ext.exists():
                original_path = path_without_ext
                logger.info(f"  找到原始文件（无扩展名）: {original_path.absolute()}")
            else:
                # 尝试查找带扩展名的文件
                if original_dir.exists():
                    for file in original_dir.iterdir():
                        if file.name.startswith(data + '.'):
                            original_path = file
                            logger.info(f"  找到原始文件（带扩展名）: {original_path.absolute()}")
                            break

            if not original_path:
                logger.error(f"  [ERROR] 原始文件不存在！")
                logger.error(f"     检查目录是否存在: {original_dir.exists()}")
                if original_dir.exists():
                    logger.error(f"     目录内容: {list(original_dir.iterdir())}")
                raise HTTPException(status_code=404, detail=f"文件不存在: {data}")

            logger.info(f"  原始文件路径: {original_path.absolute()}")
            logger.info(f"  原始文件存在: {original_path.exists()}")

            logger.info(f"  → 创建缩略图目录: {thumb_path.parent}")
            thumb_path.parent.mkdir(parents=True, exist_ok=True)

            logger.info(f"  → 开始异步生成缩略图...")
            thumbnail_generated = await generate_thumbnail_async(original_path, thumb_path, filehash=data)
            logger.info(f"  → 生成完成，缩略图存在: {thumb_path.exists()}, 生成结果: {thumbnail_generated}")

            if thumb_path.exists():
                logger.info(f"     缩略图大小: {thumb_path.stat().st_size} bytes")

        # 再次检查缩略图是否存在
        if not thumb_path.exists():
            logger.warning(f"  [WARN] 缩略图不存在（可能是非图片/视频文件）")
            logger.warning(f"     路径: {thumb_path.absolute()}")
            # 对于不支持缩略图的文件，返回 404 而不是 500
            raise HTTPException(status_code=404, detail="该文件类型不支持缩略图")

        # 生成 ETag：直接使用文件修改时间
        try:
            stat = thumb_path.stat()
            etag = f'"{int(stat.st_mtime)}"'
            logger.info(f"  ETag: {etag}")
        except Exception as e:
            logger.error(f"  [ERROR] 生成 ETag 失败: {e}")
            logger.error(traceback.format_exc())
            etag = f'"0"'

        # 检查客户端是否有缓存（If-None-Match）
        if_none_match = request.headers.get("if-none-match")
        logger.info(f"  If-None-Match: {if_none_match}")
        logger.info(f"  匹配结果: {if_none_match == etag if if_none_match else 'N/A'}")

        if if_none_match and if_none_match == etag:
            logger.info(f"  [OK] 命中 ETag 缓存，返回 304")
            logger.info("=" * 80)
            return Response(
                status_code=304,
                headers={
                    "ETag": etag,
                    "Access-Control-Allow-Origin": "*",
                    "Vary": "Origin"
                }
            )

        # 返回缩略图文件
        file_size = thumb_path.stat().st_size
        logger.info(f"  [OK] 返回缩略图 - 大小: {file_size} bytes")
        logger.info("=" * 80)

        response = FileResponse(
            thumb_path,
            media_type="image/jpeg",
            headers={
                "Cache-Control": "public, max-age=2592000",
                "ETag": etag,
                "Access-Control-Allow-Origin": "*",
                "Vary": "Origin",
                "X-API-Deprecated": "true",
                "X-API-Sunset": "请使用 /api/v2/media/{media_id}/thumbnail 代替"
            }
        )

        response.headers["ETag"] = etag
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Vary"] = "Origin"
        response.headers["X-API-Deprecated"] = "true"
        response.headers["X-API-Sunset"] = "请使用 /api/v2/media/{media_id}/thumbnail 代替"

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"[ERROR] 缩略图接口发生未预期错误")
        logger.error(f"  错误类型: {type(e).__name__}")
        logger.error(f"  错误信息: {str(e)}")
        logger.error(f"  堆栈跟踪:")
        logger.error(traceback.format_exc())
        logger.error("=" * 80)
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")


async def generate_thumbnail_async(source_path: Path, thumb_path: Path, filehash: str) -> bool:
    """异步生成缩略图（在线程池中执行）

    Returns:
        bool: 是否成功生成缩略图
    """
    import os
    from src.utils.image.processing import generate_thumbnail, get_file_mime_type

    try:
        mime_type = await get_file_mime_type(filehash)
        logger.info(f"   [INFO] 文件 MIME 类型: {mime_type}")
    except Exception as e:
        logger.warning(f"   [WARN] 无法获取 MIME 类型: {e}")
        mime_type = "application/octet-stream"

    def sync_generate():
        try:
            # 只处理图片、视频和音频
            if mime_type.startswith("image/"):
                logger.info(f"   [IMAGE] 开始生成图片缩略图...")
                generate_thumbnail(str(source_path), str(thumb_path))
                success = os.path.exists(str(thumb_path))
                logger.info(f"   [{'OK' if success else 'FAIL'}] 图片缩略图生成{'成功' if success else '失败'}")
                return success
            elif mime_type.startswith("video/"):
                logger.info(f"   [VIDEO] 开始生成视频缩略图...")
                from src.utils.image.processing import create_video_thumbnail
                success = create_video_thumbnail(str(source_path), str(thumb_path))
                logger.info(f"   [{'OK' if success else 'FAIL'}] 视频缩略图生成{'成功' if success else '失败'}")
                return success
            elif mime_type.startswith("audio/"):
                logger.info(f"   [AUDIO] 开始生成音频缩略图（提取封面）...")
                from src.utils.image.audio_processor import create_audio_thumbnail
                success = create_audio_thumbnail(str(source_path), str(thumb_path))
                logger.info(f"   [{'OK' if success else 'FAIL'}] 音频缩略图生成{'成功' if success else '失败'}")
                return success
            else:
                # 对于不支持的文件类型（PDF、ZIP等），不生成缩略图
                logger.info(f"   [INFO] 文件类型 {mime_type} 不支持缩略图，跳过生成")
                return False
        except Exception as e:
            logger.error(f"   [ERROR] 缩略图生成失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        result = await loop.run_in_executor(pool, sync_generate)
        return result


# ------------------------------------------------------------
# 子路由懒加载注册（避免模块级导入重量级子路由）
# ------------------------------------------------------------

# 子路由映射：(属性名, 模块路径)
_V1_SUB_ROUTERS = [
    ('ai_router', 'src.api.v1.ai.ai_assist_routes'),
    ('mobile_router', 'src.api.v1.user_utils.mobile_sync_routes'),
    ('feed_router', 'src.api.v1.utils.feed_routes'),
    ('security_router', 'src.api.v1.system.security_monitor_routes'),
    ('publish_router', 'src.api.v1.articles.third_party_publish_routes'),
    ('webhook_router', 'src.api.v1.system.webhook_routes'),
    ('plugin_market_router', 'src.api.v1.plugins.marketplace_routes'),
    ('page_builder_router', 'src.api.v1.content_management.page_builder_routes'),
    ('component_router', 'src.api.v1.content_management.component_routes'),
    ('theme_market_router', 'src.api.v1.content_management.theme_market_routes'),
]


def _lazy_include_sub_routers():
    """延迟加载并注册所有 V1 子路由"""
    import importlib

    for attr_name, module_path in _V1_SUB_ROUTERS:
        try:
            mod = importlib.import_module(module_path)
            sub_router = getattr(mod, 'router', None)
            if sub_router is not None:
                api_v1_router.include_router(sub_router)
        except ImportError as e:
            logger.warning(f"[V1] 子路由 {module_path} 加载失败: {e}")
        except Exception as e:
            logger.warning(f"[V1] 子路由 {module_path} 注册异常: {e}")

    # 注册 GraphQL 接口 (Headless CMS)
    try:
        from strawberry.fastapi import GraphQLRouter
        from src.api.v1.core.graphql_schema import schema
        graphql_router = GraphQLRouter(schema, prefix="/graphql")
        api_v1_router.include_router(graphql_router)
    except ImportError:
        pass


# 延迟执行子路由注册（首次访问 router 属性时触发）
_sub_routers_loaded = False


def _ensure_sub_routers():
    global _sub_routers_loaded
    if not _sub_routers_loaded:
        _lazy_include_sub_routers()
        _sub_routers_loaded = True


# 为路由自动发现系统提供统一的 router 名称
# 使用延迟加载包装
class _RouterProxy:
    """路由代理，首次访问时才加载子路由"""

    def __init__(self, target_router):
        object.__setattr__(self, '_target', target_router)

    def __getattr__(self, name):
        _ensure_sub_routers()
        return getattr(object.__getattribute__(self, '_target'), name)

    def __repr__(self):
        return repr(object.__getattribute__(self, '_target'))


router = _RouterProxy(api_v1_router)
