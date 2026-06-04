"""
面包屑导航API
"""
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from shared.services.seo.breadcrumb_service import breadcrumb_service
from src.api.v1.core.responses import ApiResponse
from src.utils.database.main import get_async_session

router = APIRouter()


@router.get("/article/{article_id}",
            summary="获取文章面包屑",
            description="获取指定文章的面包屑导航路径",
            response_description="返回面包屑列表和JSON-LD结构化数据")
async def get_article_breadcrumbs_api(
        article_id: int = Path(..., description="文章ID"),
        db: AsyncSession = Depends(get_async_session)
):
    """获取文章详情页的面包屑导航"""
    try:
        breadcrumbs = await breadcrumb_service.get_article_breadcrumbs(db, article_id)
        json_ld = breadcrumb_service.generate_json_ld(breadcrumbs)
        
        return ApiResponse(
            success=True,
            data={
                "breadcrumbs": breadcrumbs,
                "json_ld": json_ld
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in get_article_breadcrumbs_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/category/{category_id}",
            summary="获取分类面包屑",
            description="获取指定分类的面包屑导航路径",
            response_description="返回面包屑列表和JSON-LD结构化数据")
async def get_category_breadcrumbs_api(
        category_id: int = Path(..., description="分类ID"),
        db: AsyncSession = Depends(get_async_session)
):
    """获取分类页的面包屑导航"""
    try:
        breadcrumbs = await breadcrumb_service.get_category_breadcrumbs(db, category_id)
        json_ld = breadcrumb_service.generate_json_ld(breadcrumbs)
        
        return ApiResponse(
            success=True,
            data={
                "breadcrumbs": breadcrumbs,
                "json_ld": json_ld
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in get_category_breadcrumbs_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/page/{page_id}",
            summary="获取页面面包屑",
            description="获取指定页面的面包屑导航路径",
            response_description="返回面包屑列表和JSON-LD结构化数据")
async def get_page_breadcrumbs_api(
        page_id: int = Path(..., description="页面ID"),
        db: AsyncSession = Depends(get_async_session)
):
    """获取页面详情页的面包屑导航"""
    try:
        breadcrumbs = await breadcrumb_service.get_page_breadcrumbs(db, page_id)
        json_ld = breadcrumb_service.generate_json_ld(breadcrumbs)
        
        return ApiResponse(
            success=True,
            data={
                "breadcrumbs": breadcrumbs,
                "json_ld": json_ld
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in get_page_breadcrumbs_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/search",
            summary="获取搜索面包屑",
            description="获取搜索结果页的面包屑导航路径",
            response_description="返回面包屑列表和JSON-LD结构化数据")
async def get_search_breadcrumbs_api(
        q: str = Query(..., description="搜索关键词"),
):
    """获取搜索结果页的面包屑导航"""
    try:
        breadcrumbs = breadcrumb_service.get_search_breadcrumbs(q)
        json_ld = breadcrumb_service.generate_json_ld(breadcrumbs)
        
        return ApiResponse(
            success=True,
            data={
                "breadcrumbs": breadcrumbs,
                "json_ld": json_ld
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in get_search_breadcrumbs_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/tag/{tag_name}",
            summary="获取标签面包屑",
            description="获取标签页的面包屑导航路径",
            response_description="返回面包屑列表和JSON-LD结构化数据")
async def get_tag_breadcrumbs_api(
        tag_name: str = Path(..., description="标签名称"),
):
    """获取标签页的面包屑导航"""
    try:
        breadcrumbs = breadcrumb_service.get_tag_breadcrumbs(tag_name)
        json_ld = breadcrumb_service.generate_json_ld(breadcrumbs)
        
        return ApiResponse(
            success=True,
            data={
                "breadcrumbs": breadcrumbs,
                "json_ld": json_ld
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in get_tag_breadcrumbs_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/author/{author_name}",
            summary="获取作者面包屑",
            description="获取作者页的面包屑导航路径",
            response_description="返回面包屑列表和JSON-LD结构化数据")
async def get_author_breadcrumbs_api(
        author_name: str = Path(..., description="作者用户名"),
):
    """获取作者页的面包屑导航"""
    try:
        breadcrumbs = breadcrumb_service.get_author_breadcrumbs(author_name)
        json_ld = breadcrumb_service.generate_json_ld(breadcrumbs)
        
        return ApiResponse(
            success=True,
            data={
                "breadcrumbs": breadcrumbs,
                "json_ld": json_ld
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in get_author_breadcrumbs_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))
