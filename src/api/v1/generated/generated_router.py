"""
FastAPI 路由文件
由 routes.yaml 自动生成 - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from fastapi import APIRouter, Request

from src.api.v1.responses import ApiResponse

from fastapi import APIRouter, Depends, Form, Query, Path
from src.api.v1.core.responses import ApiResponse
from src.auth import jwt_required_dependency as jwt_required

# 导入依赖

router = APIRouter()

# ====================
#
Articles
模块 == == == == == == == == == ==


@router.get("/articles", summary="获取文章列表")
async def get_articles_api_endpoint(
        page: int = Query(1)

        ,
        per_page: int = Query(10)

        ,
        search: str = Query(None)

        ,
        category_id: int = Query(None)

        ,
        user_id: int = Query(None)

        ,
        status: str = Query(None)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_articles_api
    result = await get_articles_api(
        page=page,
        per_page=per_page,
        search=search,
        category_id=category_id,
        user_id=user_id,
        status=status,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_articles_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/articles/{article_id}", summary="获取文章详情")
async def get_article_detail_api_endpoint(
        article_id: int = Query(...)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_article_detail_api
    result = await get_article_detail_api(
        article_id=article_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_article_detail_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/articles/{article_id}/raw", summary="获取文章原始内容")
async def get_article_raw_content_api_endpoint(
        article_id: int = Query(...)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_article_raw_content_api
    result = await get_article_raw_content_api(
        article_id=article_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_article_raw_content_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/articles", summary="创建文章")
async def create_article_api_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import create_article_api
    result = await create_article_api(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in create_article_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.put("/articles/{article_id}", summary="更新文章")
async def update_article_api_endpoint(
        article_id: int = Query(...)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import update_article_api
    result = await update_article_api(
        article_id=article_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in update_article_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.delete("/articles/{article_id}", summary="删除文章")
async def delete_article_api_endpoint(
        article_id: int = Query(...)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import delete_article_api
    result = await delete_article_api(
        article_id=article_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in delete_article_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/articles/user/{user_id}", summary="获取用户文章列表")
async def get_user_articles_api_endpoint(
        user_id: int = Query(...)

        ,
        page: int = Query(1)

        ,
        per_page: int = Query(10)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_user_articles_api
    result = await get_user_articles_api(
        user_id=user_id,
        page=page,
        per_page=per_page,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_user_articles_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/articles/user/{user_id}/stats", summary="获取用户统计信息")
async def get_user_articles_stats_api_endpoint(
        user_id: int = Query(...)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_user_articles_stats_api
    result = await get_user_articles_stats_api(
        user_id=user_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_user_articles_stats_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/blog/p/{slug}", summary="")
async def get_article_by_slug_api_endpoint(
        slug: str = Query(...)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_article_by_slug_api
    result = await get_article_by_slug_api(
        slug=slug,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_article_by_slug_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/blog/{article_id}.html", summary="")
async def get_article_by_id_api_endpoint(
        article_id: int = Query(...)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_article_by_id_api
    result = await get_article_by_id_api(
        article_id=article_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_article_by_id_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/blog/tag/{tag_name}", summary="")
async def get_articles_by_tag_api_endpoint(
        tag_name: str = Query(...)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_articles_by_tag_api
    result = await get_articles_by_tag_api(
        tag_name=tag_name,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_articles_by_tag_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/blog/featured", summary="")
async def get_featured_articles_api_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_featured_articles_api
    result = await get_featured_articles_api(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_featured_articles_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/blog/contribute/{article_id}", summary="")
async def get_contribute_info_api_endpoint(
        article_id: int = Query(...)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_contribute_info_api
    result = await get_contribute_info_api(
        article_id=article_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_contribute_info_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/blog/contribute/{article_id}", summary="")
async def submit_contribution_api_endpoint(
        article_id: int = Query(...)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import submit_contribution_api
    result = await submit_contribution_api(
        article_id=article_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in submit_contribution_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/blog/edit/{article_id}", summary="")
async def get_edit_article_api_endpoint(
        article_id: int = Query(...)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_edit_article_api
    result = await get_edit_article_api(
        article_id=article_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_edit_article_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/blog/new", summary="")
async def get_new_article_form_api_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_new_article_form_api
    result = await get_new_article_form_api(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_new_article_form_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/blog/edit/{article_id}", summary="")
async def update_article_via_blog_api_endpoint(
        request: Request,
        article_id: int = Query(...)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import update_article_via_blog_api
    result = await update_article_via_blog_api(
        article_id=article_id,
        request=request,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in update_article_via_blog_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/blog/new", summary="")
async def create_article_via_blog_api_endpoint(
        request: Request,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import create_article_via_blog_api
    result = await create_article_via_blog_api(
        request=request,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in create_article_via_blog_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/blog/{aid}/i18n/{iso}", summary="")
async def api_blog_i18n_content_endpoint(
        aid: int = Path(...),
        iso: str = Query(...)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import api_blog_i18n_content
    result = await api_blog_i18n_content(
        aid=aid,
        iso=iso,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in api_blog_i18n_content: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))


# ====================
#
Dashboard
模块 == == == == == == == == == ==


@router.get("/home/articles", summary="获取首页文章列表")
async def get_home_articles_api_endpoint(
        page: int = Query(1)

        ,
        per_page: int = Query(9)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_home_articles_api
    result = await get_home_articles_api(
        page=page,
        per_page=per_page,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_home_articles_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/home/data", summary="")
async def get_home_data_endpoint(
        limit_featured: int = Query(4)

        ,
        limit_popular: int = Query(5)

        ,
        limit_recent: int = Query(9)

        ,
        limit_categories: int = Query(8)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_home_data
    result = await get_home_data(
        limit_featured=limit_featured,
        limit_popular=limit_popular,
        limit_recent=limit_recent,
        limit_categories=limit_categories,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_home_data: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/home/config", summary="")
async def get_home_config_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_home_config
    result = await get_home_config(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_home_config: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/home/featured", summary="")
async def get_featured_articles_endpoint(
        limit: int = Query(4)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_featured_articles
    result = await get_featured_articles(
        limit=limit,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_featured_articles: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/home/recent", summary="")
async def get_recent_articles_endpoint(
        page: int = Query(1)

        ,
        per_page: int = Query(9)

        ,
        category_id: int = Query(None)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_recent_articles
    result = await get_recent_articles(
        page=page,
        per_page=per_page,
        category_id=category_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_recent_articles: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/home/popular", summary="")
async def get_popular_articles_endpoint(
        limit: int = Query(5)

        ,
        days: int = Query(30)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_popular_articles
    result = await get_popular_articles(
        limit=limit,
        days=days,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_popular_articles: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/home/categories", summary="")
async def get_home_categories_endpoint(
        limit: int = Query(8)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_home_categories
    result = await get_home_categories(
        limit=limit,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_home_categories: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/home/stats", summary="")
async def get_home_stats_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_home_stats
    result = await get_home_stats(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_home_stats: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/home/menus", summary="")
async def get_home_menus_endpoint(
        request: Request,
):


    """"""
try:
    from shared.services import get_home_menus
    result = await get_home_menus(
        request=request,
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_home_menus: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/home/subscribe", summary="")
async def subscribe_email_endpoint(
        email: str = Query(...)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import subscribe_email
    result = await subscribe_email(
        email=email,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in subscribe_email: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/home/search", summary="")
async def search_home_articles_endpoint(
        q: str = Query(...)

        ,
        page: int = Query(1)

        ,
        per_page: int = Query(10)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import search_home_articles
    result = await search_home_articles(
        q=q,
        page=page,
        per_page=per_page,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in search_home_articles: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/dashboard/comment_config", summary="")
async def get_comment_config_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_comment_config
    result = await get_comment_config(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_comment_config: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/dashboard/comment_config", summary="")
async def update_comment_config_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import update_comment_config
    result = await update_comment_config(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in update_comment_config: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/dashboard/stats", summary="")
async def get_dashboard_stats_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_dashboard_stats
    result = await get_dashboard_stats(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_dashboard_stats: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/dashboard/recent-articles", summary="")
async def __get_recent_articles_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import __get_recent_articles
    result = await __get_recent_articles(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in __get_recent_articles: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/dashboard/traffic", summary="")
async def get_traffic_data_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_traffic_data
    result = await get_traffic_data(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_traffic_data: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))


# ====================
#
Profile
模块 == == == == == == == == == ==


@router.get("/profile", summary="获取用户资料")
async def get_my_profile_api_endpoint(
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_my_profile_api
    result = await get_my_profile_api(
        current_user=current_user,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_my_profile_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.put("/profile", summary="更新用户资料")
async def update_my_profile_api_endpoint(
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import update_my_profile_api
    result = await update_my_profile_api(
        current_user=current_user,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in update_my_profile_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))


    # ====================
    #
模块 == == == == == == == == == ==


@router.get("/", summary="获取用户列表")
async def get_users_list_api_endpoint(
        page: int = Query(1)

        ,
        per_page: int = Query(10)

        ,
        search: str = Query(None)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_users_list_api
    result = await get_users_list_api(
        page=page,
        per_page=per_page,
        search=search,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_users_list_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))


# ====================
#
Me
模块 == == == == == == == == == ==


@router.get("/me", summary="获取当前用户信息")
async def get_current_user_api_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_current_user_api
    result = await get_current_user_api(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_current_user_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))


# ====================
#
Categories
模块 == == == == == == == == == ==


@router.get("/category/all", summary="")
async def get_all_categories_api_endpoint(
        page: int = Query(1)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_all_categories_api
    result = await get_all_categories_api(
        page=page,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_all_categories_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/category/public", summary="")
async def get_public_categories_api_endpoint(
        page: int = Query(1)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_public_categories_api
    result = await get_public_categories_api(
        page=page,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_public_categories_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/category/{name}", summary="")
async def get_category_by_name_api_endpoint(
        name: str = Query(...)

        ,
        page: int = Query(1)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_category_by_name_api
    result = await get_category_by_name_api(
        name=name,
        page=page,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_category_by_name_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/category/", summary="")
async def get_all_categories_root_api_endpoint(
        page: int = Query(1)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_all_categories_root_api
    result = await get_all_categories_root_api(
        page=page,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_all_categories_root_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/category/subscribe", summary="")
async def subscribe_category_api_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import subscribe_category_api
    result = await subscribe_category_api(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in subscribe_category_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/category/unsubscribe", summary="")
async def unsubscribe_category_api_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import unsubscribe_category_api
    result = await unsubscribe_category_api(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in unsubscribe_category_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/category-management/", summary="")
async def create_category_api_endpoint(
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import create_category_api
    result = await create_category_api(
        current_user=current_user,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in create_category_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.put("/category-management/{category_id}", summary="")
async def update_category_api_endpoint(
        category_id: int = Query(...)

        ,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import update_category_api
    result = await update_category_api(
        category_id=category_id,
        current_user=current_user,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in update_category_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/category-management/", summary="")
async def get_categories_with_stats_api_endpoint(
        page: int = Query(1)

        ,
        per_page: int = Query(10)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_categories_with_stats_api
    result = await get_categories_with_stats_api(
        page=page,
        per_page=per_page,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_categories_with_stats_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.delete("/category-management/{category_id}", summary="")
async def delete_category_api_endpoint(
        category_id: int = Query(...)

        ,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import delete_category_api
    result = await delete_category_api(
        category_id=category_id,
        current_user=current_user,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in delete_category_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))


# ====================
#
Admin
模块 == == == == == == == == == ==


@router.get("/admin-settings/", summary="")
async def get_settings_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_settings
    result = await get_settings(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_settings: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/admin-settings/", summary="")
async def update_settings_endpoint(
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import update_settings
    result = await update_settings(
        current_user=current_user,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in update_settings: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/admin-settings/menus", summary="")
async def create_menu_endpoint(
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import create_menu
    result = await create_menu(
        current_user=current_user,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in create_menu: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.put("/admin-settings/menus/{menu_id}", summary="")
async def update_menu_endpoint(
        menu_id: int = Query(...)

        ,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import update_menu
    result = await update_menu(
        menu_id=menu_id,
        current_user=current_user,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in update_menu: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.delete("/admin-settings/menus/{menu_id}", summary="")
async def delete_menu_endpoint(
        menu_id: int = Query(...)

        ,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import delete_menu
    result = await delete_menu(
        menu_id=menu_id,
        current_user=current_user,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in delete_menu: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/admin-settings/pages", summary="")
async def create_page_endpoint(
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import create_page
    result = await create_page(
        current_user=current_user,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in create_page: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.put("/admin-settings/pages/{page_id}", summary="")
async def update_page_endpoint(
        page_id: int = Query(...)

        ,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import update_page
    result = await update_page(
        page_id=page_id,
        current_user=current_user,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in update_page: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.delete("/admin-settings/pages/{page_id}", summary="")
async def delete_page_endpoint(
        page_id: int = Query(...)

        ,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import delete_page
    result = await delete_page(
        page_id=page_id,
        current_user=current_user,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in delete_page: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/admin-settings/menu-items", summary="")
async def create_menu_item_endpoint(
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import create_menu_item
    result = await create_menu_item(
        current_user=current_user,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in create_menu_item: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.put("/admin-settings/menu-items/{menu_item_id}", summary="")
async def update_menu_item_endpoint(
        menu_item_id: int = Query(...)

        ,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import update_menu_item
    result = await update_menu_item(
        menu_item_id=menu_item_id,
        current_user=current_user,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in update_menu_item: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.delete("/admin-settings/menu-items/{menu_item_id}", summary="")
async def delete_menu_item_endpoint(
        menu_item_id: int = Query(...)

        ,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import delete_menu_item
    result = await delete_menu_item(
        menu_item_id=menu_item_id,
        current_user=current_user,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in delete_menu_item: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/admin/dashboard", summary="")
async def admin_dashboard_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import admin_dashboard
    result = await admin_dashboard(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in admin_dashboard: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/backup/list", summary="")
async def list_backups_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import list_backups
    result = await list_backups(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in list_backups: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/backup/create", summary="")
async def create_backup_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import create_backup
    result = await create_backup(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in create_backup: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/backup/delete", summary="")
async def delete_backup_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import delete_backup
    result = await delete_backup(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in delete_backup: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/backup/download/{filename}", summary="")
async def download_backup_endpoint(
        filename: str = Query(...)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import download_backup
    result = await download_backup(
        filename=filename,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in download_backup: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/admin/role/search", summary="")
async def admin_roles_search_endpoint(
        page: int = Query(1)

        ,
        per_page: int = Query(10)

        ,
        search: str = Query(None)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import admin_roles_search
    result = await admin_roles_search(
        page=page,
        per_page=per_page,
        search=search,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in admin_roles_search: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/admin/role", summary="")
async def create_role_endpoint(
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import create_role
    result = await create_role(
        current_user=current_user,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in create_role: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/admin/role/{role_id}", summary="")
async def admin_role_detail_endpoint(
        role_id: int = Query(...)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import admin_role_detail
    result = await admin_role_detail(
        role_id=role_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in admin_role_detail: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.put("/admin/role/{role_id}", summary="")
async def update_role_endpoint(
        role_id: int = Query(...)

        ,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import update_role
    result = await update_role(
        role_id=role_id,
        current_user=current_user,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in update_role: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.delete("/admin/role/{role_id}", summary="")
async def delete_role_endpoint(
        role_id: int = Query(...)

        ,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import delete_role
    result = await delete_role(
        role_id=role_id,
        current_user=current_user,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in delete_role: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/admin/permission", summary="")
async def get_permissions_endpoint(
        page: int = Query(1)

        ,
        per_page: int = Query(10)

        ,
        search: str = Query(None)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_permissions
    result = await get_permissions(
        page=page,
        per_page=per_page,
        search=search,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_permissions: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/admin/permission", summary="")
async def create_permission_endpoint(
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import create_permission
    result = await create_permission(
        current_user=current_user,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in create_permission: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.put("/admin/permission/{permission_id}", summary="")
async def update_permission_endpoint(
        permission_id: int = Query(...)

        ,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import update_permission
    result = await update_permission(
        permission_id=permission_id,
        current_user=current_user,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in update_permission: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.delete("/admin/permission/{permission_id}", summary="")
async def delete_permission_endpoint(
        permission_id: int = Query(...)

        ,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import delete_permission
    result = await delete_permission(
        permission_id=permission_id,
        current_user=current_user,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in delete_permission: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/admin/user/{user_id}/roles", summary="")
async def get_user_roles_endpoint(
        user_id: int = Query(...)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_user_roles
    result = await get_user_roles(
        user_id=user_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_user_roles: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.put("/admin/user/{user_id}/roles", summary="")
async def update_user_roles_endpoint(
        user_id: int = Query(...)

        ,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import update_user_roles
    result = await update_user_roles(
        user_id=user_id,
        current_user=current_user,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in update_user_roles: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/admin/role-permission/stats", summary="")
async def get_admin_role_permission_stats_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_admin_role_permission_stats
    result = await get_admin_role_permission_stats(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_admin_role_permission_stats: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/system-settings", summary="")
async def get_system_settings_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_system_settings
    result = await get_system_settings(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_system_settings: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/system-settings", summary="")
async def update_system_settings_endpoint(
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import update_system_settings
    result = await update_system_settings(
        current_user=current_user,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in update_system_settings: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))


# ====================
#
Management
模块 == == == == == == == == == ==


@router.post("/management/auth/login", summary="用户登录（兼容 Django 认证方式）")
async def login_management_api_endpoint(
        request: Request,
        username: str = Form(
            ...),
        password: str = Form(
            ...),
        remember_me: bool = Form(
            False),
):


    """"""
try:
    from shared.services import login_management_api
    result = await login_management_api(
        username=username,
        password=password,
        remember_me=remember_me,
        request=request,
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in login_management_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/management/auth/register", summary="用户注册")
async def register_management_api_endpoint(
        username: str = Query(...)

        ,
        email: str = Query(...)

        ,
        password: str = Query(...)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import register_management_api
    result = await register_management_api(
        username=username,
        email=email,
        password=password,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in register_management_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/management/auth/logout", summary="用户登出")
async def logout_management_api_endpoint(
        request: Request,
):


    """"""
try:
    from shared.services import logout_management_api
    result = await logout_management_api(
        request=request,
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in logout_management_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/management/me/profile", summary="")
async def get_management_me_profile_api_endpoint(
        request: Request,
):


    """"""
try:
    from shared.services import get_management_me_profile_api
    result = await get_management_me_profile_api(
        request=request,
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_management_me_profile_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/management/{user_id}/profile", summary="")
async def get_user_profile_api_endpoint(
        user_id: int = Query(...)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_user_profile_api
    result = await get_user_profile_api(
        user_id=user_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_user_profile_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.put("/management/me/profile", summary="")
async def update_management_me_profile_api_endpoint(
        request: Request,
):


    """"""
try:
    from shared.services import update_management_me_profile_api
    result = await update_management_me_profile_api(
        request=request,
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in update_management_me_profile_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/management/me/security/confirm-password", summary="")
async def confirm_password_form_api_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import confirm_password_form_api
    result = await confirm_password_form_api(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in confirm_password_form_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/management/me/security/confirm-password", summary="")
async def confirm_password_api_endpoint(
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import confirm_password_api
    result = await confirm_password_api(
        current_user=current_user,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in confirm_password_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/management/me/security/change-password", summary="")
async def change_password_form_api_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import change_password_form_api
    result = await change_password_form_api(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in change_password_form_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.put("/management/me/security/change-password", summary="")
async def change_password_api_endpoint(
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import change_password_api
    result = await change_password_api(
        current_user=current_user,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in change_password_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.put("/management/setting/profiles", summary="")
async def update_setting_profiles_endpoint(
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import update_setting_profiles
    result = await update_setting_profiles(
        current_user=current_user,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in update_setting_profiles: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/management", summary="")
async def get_users_endpoint(
        page: int = Query(1)

        ,
        per_page: int = Query(10)

        ,
        search: str = Query(None)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_users
    result = await get_users(
        page=page,
        per_page=per_page,
        search=search,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_users: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))


# ====================
#
Auth
模块 == == == == == == == == == ==


@router.put("/user-settings/profile/avatar", summary="")
async def update_avatar_api_endpoint(
        file: str = Query(...)

        ,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import update_avatar_api
    result = await update_avatar_api(
        file=file,
        current_user=current_user,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in update_avatar_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.put("/user-settings/profiles", summary="")
async def update_user_setting_profiles_endpoint(
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import update_user_setting_profiles
    result = await update_user_setting_profiles(
        current_user=current_user,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in update_user_setting_profiles: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/auth/login", summary="用户登录")
async def login_api_endpoint(
        request: Request,
        username: str = Form(
            ...),
        password: str = Form(
            ...),
        remember_me: bool = Form(
            False),
):


    """"""
try:
    from shared.services import login_api
    result = await login_api(
        username=username,
        password=password,
        remember_me=remember_me,
        request=request,
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in login_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/auth/register", summary="用户注册")
async def register_api_endpoint(
        username: str = Query(...)

        ,
        email: str = Query(...)

        ,
        password: str = Query(...)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import register_api
    result = await register_api(
        username=username,
        email=email,
        password=password,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in register_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/auth/logout", summary="用户登出")
async def logout_api_endpoint(
        request: Request,
):


    """"""
try:
    from shared.services import logout_api
    result = await logout_api(
        request=request,
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in logout_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/user-management/users", summary="")
async def get_user_management_users_endpoint(
        page: int = Query(1)

        ,
        per_page: int = Query(10)

        ,
        role: str = Query(None)

        ,
        search: str = Query(None)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_user_management_users
    result = await get_user_management_users(
        page=page,
        per_page=per_page,
        role=role,
        search=search,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_user_management_users: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))


# ====================
#
Media
模块 == == == == == == == == == ==


@router.get("/media/", summary="")
async def get_user_media_api_endpoint(
        current_user_obj: string = Query(None)

        ,
        media_type: str = Query(all)

        ,
        page: int = Query(1)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_user_media_api
    result = await get_user_media_api(
        current_user_obj=current_user_obj,
        media_type=media_type,
        page=page,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_user_media_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/media/{media_id}", summary="")
async def get_media_file_by_id_endpoint(
        media_id: int = Query(...)

        ,
        range_header: str = Query(None)

        ,
        current_user_obj: string = Query(None)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_media_file_by_id
    result = await get_media_file_by_id(
        media_id=media_id,
        range_header=range_header,
        current_user_obj=current_user_obj,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_media_file_by_id: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.delete("/media/", summary="")
async def delete_user_media_api_endpoint(
        current_user_obj: string = Query(None)

        ,
        file_id_list: str = Query(...)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import delete_user_media_api
    result = await delete_user_media_api(
        current_user_obj=current_user_obj,
        file_id_list=file_id_list,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in delete_user_media_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/media/upload", summary="")
async def upload_media_file_endpoint(
        current_user_obj: string = Query(None)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import upload_media_file
    result = await upload_media_file(
        current_user_obj=current_user_obj,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in upload_media_file: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/media/upload/chunked/init", summary="")
async def chunked_upload_init_endpoint(
        current_user_obj: string = Query(None)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import chunked_upload_init
    result = await chunked_upload_init(
        current_user_obj=current_user_obj,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in chunked_upload_init: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/media/upload/chunked/chunk", summary="")
async def chunked_upload_chunk_endpoint(
        current_user_obj: string = Query(None)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import chunked_upload_chunk
    result = await chunked_upload_chunk(
        current_user_obj=current_user_obj,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in chunked_upload_chunk: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/media/upload/chunked/complete", summary="")
async def chunked_upload_complete_endpoint(
        current_user_obj: string = Query(None)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import chunked_upload_complete
    result = await chunked_upload_complete(
        current_user_obj=current_user_obj,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in chunked_upload_complete: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/media/upload/chunked/progress", summary="")
async def chunked_upload_progress_endpoint(
        current_user_obj: string = Query(None)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import chunked_upload_progress
    result = await chunked_upload_progress(
        current_user_obj=current_user_obj,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in chunked_upload_progress: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/media/upload/chunked/chunks", summary="")
async def chunked_upload_chunks_endpoint(
        current_user_obj: string = Query(None)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import chunked_upload_chunks
    result = await chunked_upload_chunks(
        current_user_obj=current_user_obj,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in chunked_upload_chunks: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/media/upload/chunked/cancel", summary="")
async def chunked_upload_cancel_endpoint(
        current_user_obj: string = Query(None)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import chunked_upload_cancel
    result = await chunked_upload_cancel(
        current_user_obj=current_user_obj,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in chunked_upload_cancel: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/media-management/files", summary="")
async def get_media_management_files_endpoint(
        page: int = Query(1)

        ,
        per_page: int = Query(10)

        ,
        file_type: str = Query(None)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_media_management_files
    result = await get_media_management_files(
        page=page,
        per_page=per_page,
        file_type=file_type,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_media_management_files: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))


# ====================
#
Notifications
模块 == == == == == == == == == ==


@router.post("/notifications/messages/read", summary="")
async def read_notification_api_endpoint(
        nid: int = Query(...)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import read_notification_api
    result = await read_notification_api(
        nid=nid,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in read_notification_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/notifications/messages", summary="")
async def fetch_message_api_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import fetch_message_api
    result = await fetch_message_api(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in fetch_message_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/notifications/messages/read_all", summary="")
async def mark_all_as_read_api_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import mark_all_as_read_api
    result = await mark_all_as_read_api(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in mark_all_as_read_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.delete("/notifications/messages/clean", summary="")
async def clean_notification_api_endpoint(
        nid: str = Query(all)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import clean_notification_api
    result = await clean_notification_api(
        nid=nid,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in clean_notification_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.patch("/notifications/{notification_id}/read", summary="")
async def mark_notification_as_read_api_endpoint(
        notification_id: int = Query(...)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import mark_notification_as_read_api
    result = await mark_notification_as_read_api(
        notification_id=notification_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in mark_notification_as_read_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.delete("/notifications/{notification_id}", summary="")
async def delete_notification_api_endpoint(
        notification_id: int = Query(...)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import delete_notification_api
    result = await delete_notification_api(
        notification_id=notification_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in delete_notification_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/notifications/", summary="")
async def get_notifications_api_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_notifications_api
    result = await get_notifications_api(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_notifications_api: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/notifications/read_all", summary="")
async def mark_all_as_read_api_new_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import mark_all_as_read_api_new
    result = await mark_all_as_read_api_new(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in mark_all_as_read_api_new: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))


# ====================
#
User
模块 == == == == == == == == == ==


@router.get("/user/avatar", summary="")
async def api_user_avatar_endpoint(
        user_id: int = Query(None)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import api_user_avatar
    result = await api_user_avatar(
        user_id=user_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in api_user_avatar: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/user/bio/{user_id}", summary="")
async def api_user_bio_endpoint(
        user_id: int = Query(...)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import api_user_bio
    result = await api_user_bio(
        user_id=user_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in api_user_bio: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/user/profile/{user_id}", summary="")
async def api_user_profile_endpoint_endpoint(
        user_id: int = Query(...)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import api_user_profile_endpoint
    result = await api_user_profile_endpoint(
        user_id=user_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in api_user_profile_endpoint: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/user/check-login", summary="")
async def check_login_status_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import check_login_status
    result = await check_login_status(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in check_login_status: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))


# ====================
#
Tags
模块 == == == == == == == == == ==


@router.get("/tags/suggest", summary="")
async def suggest_tags_endpoint(
        query: str = Query(None)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import suggest_tags
    result = await suggest_tags(
        query=query,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in suggest_tags: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))


# ====================
#
Change - Email
模块 == == == == == == == == == ==


@router.get("/change-email/confirm/{token}", summary="")
async def confirm_email_change_endpoint(
        token: str = Query(...)

        ,
        current_user_obj: string = Query(None)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import confirm_email_change
    result = await confirm_email_change(
        token=token,
        current_user_obj=current_user_obj,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in confirm_email_change: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))


# ====================
#
Email - Exists
模块 == == == == == == == == == ==


@router.get("/email-exists", summary="")
async def email_exists_back_endpoint(
        email: str = Query(...)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import email_exists_back
    result = await email_exists_back(
        email=email,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in email_exists_back: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))


# ====================
#
Username - Exists
模块 == == == == == == == == == ==


@router.get("/username-exists/{username}", summary="")
async def username_exists_endpoint(
        username: str = Query(...)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import username_exists
    result = await username_exists(
        username=username,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in username_exists: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))


# ====================
#
Search
模块 == == == == == == == == == ==


@router.get("/search/history", summary="")
async def get_search_history_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_search_history
    result = await get_search_history(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_search_history: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))


# ====================
#
Article
模块 == == == == == == == == == ==


@router.post("/article/{article_id}/status", summary="")
async def update_article_status_endpoint(
        article_id: int = Query(...)

        ,
        current_user_obj: string = Query(None)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import update_article_status
    result = await update_article_status(
        article_id=article_id,
        current_user_obj=current_user_obj,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in update_article_status: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/article/password-form/{aid}", summary="")
async def get_password_form_endpoint(
        aid: int = Path(...),
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_password_form
    result = await get_password_form(
        aid=aid,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_password_form: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/article/password/{aid}", summary="")
async def api_update_article_password_endpoint(
        aid: int = Path(...),
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import api_update_article_password
    result = await api_update_article_password(
        aid=aid,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in api_update_article_password: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/article/{article_id}/like", summary="")
async def like_article_endpoint(
        article_id: int = Query(...)

        ,
        current_user_obj: string = Query(None)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import like_article
    result = await like_article(
        article_id=article_id,
        current_user_obj=current_user_obj,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in like_article: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/article/{article_id}/view", summary="")
async def record_article_view_endpoint(
        article_id: int = Query(...)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import record_article_view
    result = await record_article_view(
        article_id=article_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in record_article_view: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))


# ====================
#
Upload
模块 == == == == == == == == == ==


@router.post("/upload/cover", summary="")
async def upload_cover_endpoint(
        current_user_obj: string = Query(None)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import upload_cover
    result = await upload_cover(
        current_user_obj=current_user_obj,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in upload_cover: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))


# ====================
#
Misc
模块 == == == == == == == == == ==


@router.get("/routes", summary="")
async def list_all_routes_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import list_all_routes
    result = await list_all_routes(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in list_all_routes: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/version/info", summary="")
async def get_version_info_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_version_info
    result = await get_version_info(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_version_info: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/version/frontend", summary="")
async def get_frontend_version_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_frontend_version
    result = await get_frontend_version(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_frontend_version: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/version/backend", summary="")
async def get_backend_version_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_backend_version
    result = await get_backend_version(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_backend_version: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))


# ====================
#
Check - Username
模块 == == == == == == == == == ==


@router.get("/check-username", summary="")
async def check_username_endpoint(
        username: str = Query(...)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import check_username
    result = await check_username(
        username=username,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in check_username: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/check-username", summary="检查用户名可用性")
async def api_check_username_endpoint(
        username: str = Query(...)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import api_check_username
    result = await api_check_username(
        username=username,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in api_check_username: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))


# ====================
#
Check - Email
模块 == == == == == == == == == ==


@router.get("/check-email", summary="")
async def check_email_endpoint(
        email: str = Query(...)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import check_email
    result = await check_email(
        email=email,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in check_email: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/check-email", summary="检查邮箱可用性")
async def api_check_email_endpoint(
        email: str = Query(...)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import api_check_email
    result = await api_check_email(
        email=email,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in api_check_email: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))


# ====================
#
Roles
模块 == == == == == == == == == ==


@router.get("/role-management/permission-stats", summary="")
async def get_role_permission_stats_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_role_permission_stats
    result = await get_role_permission_stats(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_role_permission_stats: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/role-management/roles", summary="")
async def get_role_management_roles_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_role_management_roles
    result = await get_role_management_roles(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_role_management_roles: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/role-management/permissions", summary="")
async def get_role_management_permissions_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_role_management_permissions
    result = await get_role_management_permissions(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_role_management_permissions: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/role-management/roles", summary="")
async def create_role_for_management_endpoint(
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import create_role_for_management
    result = await create_role_for_management(
        current_user=current_user,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in create_role_for_management: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.put("/role-management/roles/{role_id}", summary="")
async def update_role_for_management_endpoint(
        role_id: int = Query(...)

        ,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import update_role_for_management
    result = await update_role_for_management(
        role_id=role_id,
        current_user=current_user,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in update_role_for_management: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.delete("/role-management/roles/{role_id}", summary="")
async def delete_role_for_management_endpoint(
        role_id: int = Query(...)

        ,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import delete_role_for_management
    result = await delete_role_for_management(
        role_id=role_id,
        current_user=current_user,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in delete_role_for_management: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/role-management/permissions", summary="")
async def create_permission_for_management_endpoint(
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import create_permission_for_management
    result = await create_permission_for_management(
        current_user=current_user,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in create_permission_for_management: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.put("/role-management/permissions/{permission_id}", summary="")
async def update_permission_for_management_endpoint(
        permission_id: int = Query(...)

        ,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import update_permission_for_management
    result = await update_permission_for_management(
        permission_id=permission_id,
        current_user=current_user,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in update_permission_for_management: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.delete("/role-management/permissions/{permission_id}", summary="")
async def delete_permission_for_management_endpoint(
        permission_id: int = Query(...)

        ,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import delete_permission_for_management
    result = await delete_permission_for_management(
        permission_id=permission_id,
        current_user=current_user,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in delete_permission_for_management: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))


# ====================
#
Blog - Management
模块 == == == == == == == == == ==


@router.get("/blog-management/articles", summary="")
async def get_blog_management_articles_endpoint(
        page: int = Query(1)

        ,
        per_page: int = Query(10)

        ,
        status: str = Query(None)

        ,
        search: str = Query(None)

        ,
        category_id: int = Query(None)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_blog_management_articles
    result = await get_blog_management_articles(
        page=page,
        per_page=per_page,
        status=status,
        search=search,
        category_id=category_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_blog_management_articles: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/blog-management/articles/stats", summary="")
async def get_blog_management_articles_stats_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_blog_management_articles_stats
    result = await get_blog_management_articles_stats(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_blog_management_articles_stats: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.delete("/blog-management/articles/{article_id}", summary="")
async def delete_blog_management_article_endpoint(
        article_id: int = Query(...)

        ,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import delete_blog_management_article
    result = await delete_blog_management_article(
        article_id=article_id,
        current_user=current_user,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in delete_blog_management_article: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))


# ====================
#
My
模块 == == == == == == == == == ==


@router.get("/my/articles", summary="")
async def get_my_articles_endpoint(
        page: int = Query(1)

        ,
        per_page: int = Query(10)

        ,
        status: str = Query(None)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_my_articles
    result = await get_my_articles(
        page=page,
        per_page=per_page,
        status=status,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_my_articles: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/my/messages", summary="")
async def get_my_messages_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_my_messages
    result = await get_my_messages(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_my_messages: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))


# ====================
#
Vip - Management
模块 == == == == == == == == == ==


@router.get("/vip-management", summary="")
async def get_vip_management_data_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import get_vip_management_data
    result = await get_vip_management_data(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_vip_management_data: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))


# ====================
#
Qr
模块 == == == == == == == == == ==


@router.get("/qr/generate", summary="生成二维码")
async def api_generate_qr_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import api_generate_qr
    result = await api_generate_qr(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in api_generate_qr: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/qr/status", summary="检查二维码状态")
async def api_check_qr_status_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import api_check_qr_status
    result = await api_check_qr_status(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in api_check_qr_status: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))


# ====================
#
Phone
模块 == == == == == == == == == ==


@router.get("/phone/scan", summary="手机扫码登录")
async def api_phone_scan_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import api_phone_scan
    result = await api_phone_scan(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in api_phone_scan: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))


# ====================
#
Thumbnail
模块 == == == == == == == == == ==


@router.get("/thumbnail", summary="")
async def public_media_thumbnail_endpoint(
        data: str = Query(...)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """"""
try:
    from shared.services import public_media_thumbnail
    result = await public_media_thumbnail(
        data=data,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in public_media_thumbnail: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))


# ====================
#
Article_revisions
模块 == == == == == == == == == ==


@router.post("/articles/{article_id}/revisions", summary="创建文章修订版本")
async def create_article_revision_endpoint(
        article_id: int = Path(...),
        change_summary: str = Query(None)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """手动保存文章的修订版本"""
try:
    from shared.services import create_article_revision
    result = await create_article_revision(
        article_id=article_id,
        change_summary=change_summary,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in create_article_revision: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/articles/{article_id}/revisions", summary="获取文章修订历史列表")
async def list_article_revisions_endpoint(
        article_id: int = Path(...),
        page: int = Query(1)

        ,
        per_page: int = Query(20)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """获取指定文章的修订历史，支持分页"""
try:
    from shared.services import list_article_revisions
    result = await list_article_revisions(
        article_id=article_id,
        page=page,
        per_page=per_page,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in list_article_revisions: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/articles/revisions/{revision_id}", summary="获取修订版本详情")
async def get_revision_endpoint(
        revision_id: int = Path(...),
        db: AsyncSession = Depends(get_async_db),
):


    """获取特定修订版本的详细信息"""
try:
    from shared.services import get_revision
    result = await get_revision(
        revision_id=revision_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_revision: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/articles/{article_id}/revisions/{revision_id}/rollback", summary="回滚到指定修订版本")
async def rollback_article_endpoint(
        article_id: int = Path(...),
        revision_id: int = Path(...),
        db: AsyncSession = Depends(get_async_db),
):


    """将文章恢复到指定的历史版本"""
try:
    from shared.services import rollback_article
    result = await rollback_article(
        article_id=article_id,
        revision_id=revision_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in rollback_article: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/articles/revisions/compare", summary="比较两个修订版本")
async def compare_article_revisions_endpoint(
        revision1_id: int = Query(...)

        ,
        revision2_id: int = Query(...)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """对比两个修订版本的差异"""
try:
    from shared.services import compare_article_revisions
    result = await compare_article_revisions(
        revision1_id=revision1_id,
        revision2_id=revision2_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in compare_article_revisions: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/articles/{article_id}/draft", summary="保存文章草稿")
async def save_article_draft_endpoint(
        article_id: int = Path(...),
        db: AsyncSession = Depends(get_async_db),
):


    """保存文章草稿（不创建修订历史）"""
try:
    from shared.services import save_article_draft
    result = await save_article_draft(
        article_id=article_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in save_article_draft: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/articles/{article_id}/revisions/sync", summary="同步修订历史到云端")
async def sync_article_revisions_endpoint(
        article_id: int = Path(...),
        db: AsyncSession = Depends(get_async_db),
):


    """强制保存当前状态为修订版本并同步到云端"""
try:
    from shared.services import sync_article_revisions
    result = await sync_article_revisions(
        article_id=article_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in sync_article_revisions: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.delete("/articles/{article_id}/revisions/{revision_id}", summary="删除修订版本")
async def delete_article_revision_endpoint(
        article_id: int = Path(...),
        revision_id: int = Path(...),
        db: AsyncSession = Depends(get_async_db),
):


    """删除指定的修订版本"""
try:
    from shared.services import delete_article_revision
    result = await delete_article_revision(
        article_id=article_id,
        revision_id=revision_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in delete_article_revision: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/articles/{article_id}/revisions", summary="创建文章修订版本")
async def create_article_revision_endpoint(
        article_id: int = Path(...),
        db: AsyncSession = Depends(get_async_db),
):


    """手动创建文章修订版本或同步本地草稿"""
try:
    from shared.services import create_article_revision
    result = await create_article_revision(
        article_id=article_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in create_article_revision: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/articles/{article_id}/revisions", summary="获取文章修订历史列表")
async def list_article_revisions_endpoint(
        article_id: int = Path(...),
        page: int = Query(1)

        ,
        per_page: int = Query(20)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """获取文章的修订历史列表"""
try:
    from shared.services import list_article_revisions
    result = await list_article_revisions(
        article_id=article_id,
        page=page,
        per_page=per_page,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in list_article_revisions: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/articles/revisions/{revision_id}", summary="获取特定修订版本")
async def get_revision_endpoint(
        revision_id: int = Path(...),
        db: AsyncSession = Depends(get_async_db),
):


    """获取特定修订版本的详细信息"""
try:
    from shared.services import get_revision
    result = await get_revision(
        revision_id=revision_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_revision: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/articles/{article_id}/revisions/{revision_id}/rollback", summary="回滚文章到指定修订版本")
async def rollback_article_endpoint(
        article_id: int = Path(...),
        revision_id: int = Path(...),
        db: AsyncSession = Depends(get_async_db),
):


    """回滚文章到指定修订版本"""
try:
    from shared.services import rollback_article
    result = await rollback_article(
        article_id=article_id,
        revision_id=revision_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in rollback_article: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/articles/revisions/compare", summary="比较两个修订版本")
async def compare_article_revisions_endpoint(
        revision1_id: int = Query(...)

        ,
        revision2_id: int = Query(...)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """比较两个修订版本的差异"""
try:
    from shared.services import compare_article_revisions
    result = await compare_article_revisions(
        revision1_id=revision1_id,
        revision2_id=revision2_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in compare_article_revisions: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/articles/{article_id}/revisions/sync", summary="同步文章修订历史到云端")
async def sync_article_revisions_endpoint(
        article_id: int = Path(...),
        db: AsyncSession = Depends(get_async_db),
):


    """同步文章修订历史到云端（强制保存当前状态为修订版本）"""
try:
    from shared.services import sync_article_revisions
    result = await sync_article_revisions(
        article_id=article_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in sync_article_revisions: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.delete("/articles/{article_id}/revisions/{revision_id}", summary="删除修订版本")
async def delete_article_revision_endpoint(
        article_id: int = Path(...),
        revision_id: int = Path(...),
        db: AsyncSession = Depends(get_async_db),
):


    """删除指定的修订版本"""
try:
    from shared.services import delete_article_revision
    result = await delete_article_revision(
        article_id=article_id,
        revision_id=revision_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in delete_article_revision: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))


# ====================
#
Scheduled_publish
模块 == == == == == == == == == ==


@router.post("/articles/scheduled/check-and-publish", summary="触发定时发布检查")
async def trigger_scheduled_publish_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """手动检查并发布到期的定时文章"""
try:
    from shared.services import trigger_scheduled_publish
    result = await trigger_scheduled_publish(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in trigger_scheduled_publish: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/articles/scheduled/list", summary="获取定时文章列表")
async def list_scheduled_articles_endpoint(
        page: int = Query(1)

        ,
        per_page: int = Query(20)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """获取所有待发布的定时文章"""
try:
    from shared.services import list_scheduled_articles
    result = await list_scheduled_articles(
        page=page,
        per_page=per_page,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in list_scheduled_articles: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/articles/{article_id}/scheduled/cancel", summary="取消定时发布")
async def cancel_article_schedule_endpoint(
        article_id: int = Path(...),
        db: AsyncSession = Depends(get_async_db),
):


    """取消文章的定时发布设置"""
try:
    from shared.services import cancel_article_schedule
    result = await cancel_article_schedule(
        article_id=article_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in cancel_article_schedule: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))


# ====================
#
Feed
模块 == == == == == == == == == ==


@router.get("/feed/rss", summary="获取RSS订阅")
async def get_rss_feed_endpoint(
        limit: int = Query(20)

        ,
        category_id: int = Query(None)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """获取RSS 2.0格式的Feed订阅"""
try:
    from shared.services import get_rss_feed
    result = await get_rss_feed(
        limit=limit,
        category_id=category_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_rss_feed: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/feed/atom", summary="获取Atom订阅")
async def get_atom_feed_endpoint(
        limit: int = Query(20)

        ,
        category_id: int = Query(None)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """获取Atom 1.0格式的Feed订阅"""
try:
    from shared.services import get_atom_feed
    result = await get_atom_feed(
        limit=limit,
        category_id=category_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_atom_feed: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/feed/metadata", summary="获取Feed元数据")
async def get_feed_meta_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """获取Feed的统计信息和URL"""
try:
    from shared.services import get_feed_meta
    result = await get_feed_meta(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_feed_meta: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/feed", summary="Feed重定向")
async def legacy_feed_redirect_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """兼容旧版路径，重定向到RSS"""
try:
    from shared.services import legacy_feed_redirect
    result = await legacy_feed_redirect(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in legacy_feed_redirect: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))


# ====================
#
Pages
模块 == == == == == == == == == ==


@router.get("/pages", summary="获取页面列表")
async def list_pages_endpoint(
        page: int = Query(1)

        ,
        per_page: int = Query(20)

        ,
        status: int = Query(None)

        ,
        db: AsyncSession = Depends(get_async_db),
):


    """获取所有页面的列表，支持分页和状态筛选"""
try:
    from shared.services import list_pages
    result = await list_pages(
        page=page,
        per_page=per_page,
        status=status,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in list_pages: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/pages/hierarchy", summary="获取页面层级结构")
async def get_pages_tree_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """获取树形结构的页面层级"""
try:
    from shared.services import get_pages_tree
    result = await get_pages_tree(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_pages_tree: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/pages/{slug}", summary="获取页面详情")
async def get_page_detail_endpoint(
        slug: str = Path(...),
        db: AsyncSession = Depends(get_async_db),
):


    """根据slug获取页面详细信息"""
try:
    from shared.services import get_page_detail
    result = await get_page_detail(
        slug=slug,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_page_detail: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/pages", summary="创建页面")
async def create_new_page_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """创建新的静态页面"""
try:
    from shared.services import create_new_page
    result = await create_new_page(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in create_new_page: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.put("/pages/{page_id}", summary="更新页面")
async def update_existing_page_endpoint(
        page_id: int = Path(...),
        db: AsyncSession = Depends(get_async_db),
):


    """更新指定页面的信息"""
try:
    from shared.services import update_existing_page
    result = await update_existing_page(
        page_id=page_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in update_existing_page: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.delete("/pages/{page_id}", summary="删除页面")
async def delete_existing_page_endpoint(
        page_id: int = Path(...),
        db: AsyncSession = Depends(get_async_db),
):


    """删除指定的页面"""
try:
    from shared.services import delete_existing_page
    result = await delete_existing_page(
        page_id=page_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in delete_existing_page: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))


# ====================
#
Menu_management
模块 == == == == == == == == == ==


@router.get("/menus", summary="获取菜单列表")
async def list_menus_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """获取所有菜单的列表"""
try:
    from shared.services import list_menus
    result = await list_menus(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in list_menus: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/menus/{menu_id}", summary="获取菜单详情")
async def get_menu_detail_endpoint(
        menu_id: int = Path(...),
        db: AsyncSession = Depends(get_async_db),
):


    """获取菜单及其菜单项树形结构"""
try:
    from shared.services import get_menu_detail
    result = await get_menu_detail(
        menu_id=menu_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_menu_detail: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/menus", summary="创建菜单")
async def create_new_menu_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """创建新的菜单"""
try:
    from shared.services import create_new_menu
    result = await create_new_menu(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in create_new_menu: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.put("/menus/{menu_id}", summary="更新菜单")
async def update_existing_menu_endpoint(
        menu_id: int = Path(...),
        db: AsyncSession = Depends(get_async_db),
):


    """更新菜单信息"""
try:
    from shared.services import update_existing_menu
    result = await update_existing_menu(
        menu_id=menu_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in update_existing_menu: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.delete("/menus/{menu_id}", summary="删除菜单")
async def delete_existing_menu_endpoint(
        menu_id: int = Path(...),
        db: AsyncSession = Depends(get_async_db),
):


    """删除菜单及其所有菜单项"""
try:
    from shared.services import delete_existing_menu
    result = await delete_existing_menu(
        menu_id=menu_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in delete_existing_menu: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/menus/{menu_id}/items", summary="添加菜单项")
async def add_item_to_menu_endpoint(
        menu_id: int = Path(...),
        db: AsyncSession = Depends(get_async_db),
):


    """向菜单添加新的菜单项"""
try:
    from shared.services import add_item_to_menu
    result = await add_item_to_menu(
        menu_id=menu_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in add_item_to_menu: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.put("/menus/items/{item_id}", summary="更新菜单项")
async def update_menu_item_detail_endpoint(
        item_id: int = Path(...),
        db: AsyncSession = Depends(get_async_db),
):


    """更新菜单项信息"""
try:
    from shared.services import update_menu_item_detail
    result = await update_menu_item_detail(
        item_id=item_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in update_menu_item_detail: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.delete("/menus/items/{item_id}", summary="删除菜单项")
async def delete_menu_item_detail_endpoint(
        item_id: int = Path(...),
        db: AsyncSession = Depends(get_async_db),
):


    """删除菜单项及其子项"""
try:
    from shared.services import delete_menu_item_detail
    result = await delete_menu_item_detail(
        item_id=item_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in delete_menu_item_detail: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/menus/{menu_id}/reorder", summary="重新排序菜单项")
async def reorder_menu_endpoint(
        menu_id: int = Path(...),
        db: AsyncSession = Depends(get_async_db),
):


    """批量更新菜单项顺序（用于拖拽）"""
try:
    from shared.services import reorder_menu
    result = await reorder_menu(
        menu_id=menu_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in reorder_menu: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/menus/available/pages", summary="获取可用页面")
async def get_available_pages_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """获取可添加到菜单的页面列表"""
try:
    from shared.services import get_available_pages
    result = await get_available_pages(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_available_pages: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/menus/available/categories", summary="获取可用分类")
async def get_available_categories_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """获取可添加到菜单的分类列表"""
try:
    from shared.services import get_available_categories
    result = await get_available_categories(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_available_categories: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))


# ====================
#
Backup_management
模块 == == == == == == == == == ==


@router.post("/backup/restore", summary="恢复备份")
async def restore_backup_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """从备份文件恢复数据"""
try:
    from shared.services import restore_backup
    result = await restore_backup(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in restore_backup: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.delete("/backup/{backup_filename}", summary="删除备份")
async def delete_backup_file_endpoint(
        backup_filename: str = Path(...),
        db: AsyncSession = Depends(get_async_db),
):


    """删除指定的备份文件"""
try:
    from shared.services import delete_backup_file
    result = await delete_backup_file(
        backup_filename=backup_filename,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in delete_backup_file: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/backup/stats", summary="获取数据库统计")
async def get_db_stats_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """获取数据库各项数据统计"""
try:
    from shared.services import get_db_stats
    result = await get_db_stats(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_db_stats: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/backup/export", summary="导出数据")
async def export_data_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """导出数据为JSON格式"""
try:
    from shared.services import export_data
    result = await export_data(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in export_data: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))


# ====================
#
Plugin_management
模块 == == == == == == == == == ==


@router.get("/plugins", summary="获取插件列表")
async def list_plugins_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """获取所有已安装和可用的插件"""
try:
    from shared.services import list_plugins
    result = await list_plugins(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in list_plugins: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/plugins/install", summary="安装插件")
async def install_plugin_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """安装新的插件"""
try:
    from shared.services import install_plugin
    result = await install_plugin(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in install_plugin: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/plugins/{plugin_id}/activate", summary="激活插件")
async def activate_plugin_endpoint(
        plugin_id: int = Path(...),
        db: AsyncSession = Depends(get_async_db),
):


    """激活指定的插件"""
try:
    from shared.services import activate_plugin
    result = await activate_plugin(
        plugin_id=plugin_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in activate_plugin: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/plugins/{plugin_id}/deactivate", summary="停用插件")
async def deactivate_plugin_endpoint(
        plugin_id: int = Path(...),
        db: AsyncSession = Depends(get_async_db),
):


    """停用指定的插件"""
try:
    from shared.services import deactivate_plugin
    result = await deactivate_plugin(
        plugin_id=plugin_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in deactivate_plugin: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.delete("/plugins/{plugin_id}", summary="卸载插件")
async def uninstall_plugin_endpoint(
        plugin_id: int = Path(...),
        db: AsyncSession = Depends(get_async_db),
):


    """卸载指定的插件"""
try:
    from shared.services import uninstall_plugin
    result = await uninstall_plugin(
        plugin_id=plugin_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in uninstall_plugin: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.put("/plugins/{plugin_id}/settings", summary="更新插件设置")
async def update_plugin_settings_endpoint(
        plugin_id: int = Path(...),
        db: AsyncSession = Depends(get_async_db),
):


    """更新插件的配置设置"""
try:
    from shared.services import update_plugin_settings
    result = await update_plugin_settings(
        plugin_id=plugin_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in update_plugin_settings: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/plugins/hooks", summary="获取钩子列表")
async def list_hooks_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """获取所有已注册的钩子信息"""
try:
    from shared.services import list_hooks
    result = await list_hooks(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in list_hooks: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))


# ====================
#
Theme_management
模块 == == == == == == == == == ==


@router.get("/themes", summary="获取主题列表")
async def list_themes_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """获取所有已安装和可用的主题"""
try:
    from shared.services import list_themes
    result = await list_themes(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in list_themes: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/themes/install", summary="安装主题")
async def install_theme_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """安装新的主题"""
try:
    from shared.services import install_theme
    result = await install_theme(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in install_theme: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/themes/{theme_id}/activate", summary="激活主题")
async def activate_theme_endpoint(
        theme_id: int = Path(...),
        db: AsyncSession = Depends(get_async_db),
):


    """激活指定的主题"""
try:
    from shared.services import activate_theme
    result = await activate_theme(
        theme_id=theme_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in activate_theme: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/themes/{theme_id}/preview", summary="预览主题")
async def preview_theme_endpoint(
        theme_id: int = Path(...),
        db: AsyncSession = Depends(get_async_db),
):


    """预览指定主题的效枟"""
try:
    from shared.services import preview_theme
    result = await preview_theme(
        theme_id=theme_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in preview_theme: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.put("/themes/{theme_id}/settings", summary="更新主题设置")
async def update_theme_settings_endpoint(
        theme_id: int = Path(...),
        db: AsyncSession = Depends(get_async_db),
):


    """更新主题的配置设置"""
try:
    from shared.services import update_theme_settings
    result = await update_theme_settings(
        theme_id=theme_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in update_theme_settings: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.delete("/themes/{theme_id}", summary="卸载主题")
async def uninstall_theme_endpoint(
        theme_id: int = Path(...),
        db: AsyncSession = Depends(get_async_db),
):


    """卸载指定的主题"""
try:
    from shared.services import uninstall_theme
    result = await uninstall_theme(
        theme_id=theme_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in uninstall_theme: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/themes/active", summary="获取当前激活主题")
async def get_active_theme_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """获取当前正在使用的主题"""
try:
    from shared.services import get_active_theme
    result = await get_active_theme(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_active_theme: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))


# ====================
#
Permission_management
模块 == == == == == == == == == ==


@router.get("/permissions/list", summary="获取所有权限")
async def list_all_permissions_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """获取系统所有可用权限列表"""
try:
    from shared.services import list_all_permissions
    result = await list_all_permissions(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in list_all_permissions: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.get("/permissions/roles", summary="获取角色列表")
async def list_roles_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """获取所有角色及其权限"""
try:
    from shared.services import list_roles
    result = await list_roles(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in list_roles: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))



@router.post("/permissions/users/{user_id}/assign-role", summary="分配用户角色")
async def assign_user_role_endpoint(
        user_id: int = Path(...),
        db: AsyncSession = Depends(get_async_db),
):


    """为用户分配指定角色"""
try:
    from shared.services import assign_user_role
    result = await assign_user_role(
        user_id=user_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in assign_user_role: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))


@router.get("/permissions/users/{user_id}/permissions", summary="获取用户权限")
async def get_user_permissions_endpoint(
        user_id: int = Path(...),
        db: AsyncSession = Depends(get_async_db),
):


    """获取用户的所有权限列表"""
try:
    from shared.services import get_user_permissions
    result = await get_user_permissions(
        user_id=user_id,
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in get_user_permissions: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))


@router.post("/permissions/check", summary="检查权限")
async def check_permission_endpoint(
        db: AsyncSession = Depends(get_async_db),
):


    """检查用户是否有指定权限"""
try:
    from shared.services import check_permission
    result = await check_permission(
        db=db
    )
    return result
except Exception as e:
    import traceback

    print(f"Error in check_permission: {str(e)}")
    print(traceback.format_exc())
    return ApiResponse(success=False, error=str(e))
