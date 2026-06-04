"""
文章评分 API
提供评分提交、查询等功能
"""
from fastapi import APIRouter, Depends, Request

from shared.models import User
from shared.services.plugins.plugin_manager.core import plugin_manager
from src.auth import jwt_required_dependency as jwt_required, jwt_optional_dependency

router = APIRouter(tags=["article-rating"])


@router.post("/rate")
async def submit_article_rating(
        request: Request,
        current_user: User = Depends(jwt_required)
):
    """
    提交文章评分
    
    Body参数:
        article_id: 文章ID
        rating: 评分 (1-5)
        comment: 评论（可选）
    """
    try:
        body = await request.json()
        article_id = body.get('article_id')
        rating = body.get('rating')
        comment = body.get('comment', '')

        if not article_id or not rating:
            return {
                'success': False,
                'message': '缺少必要参数'
            }

        # 获取文章评分插件
        rating_plugin = plugin_manager.get_plugin('article-rating')
        if not rating_plugin:
            return {
                'success': False,
                'message': '评分插件未加载'
            }

        if not rating_plugin.active:
            return {
                'success': False,
                'message': '评分功能未启用'
            }

        # 构建评分数据 - 自动从认证用户获取 user_id
        rating_data = {
            'article_id': str(article_id),
            'user_id': str(current_user.id),  # 自动从 JWT token 中提取
            'rating': rating,
            'comment': comment,
            'ip': request.client.host if request.client else '',
        }

        # 调用插件处理评分
        result = rating_plugin.handle_rating_submission(rating_data)

        return result

    except Exception as e:
        import traceback
        print(f"Error submitting rating: {str(e)}")
        print(traceback.format_exc())
        return {
            'success': False,
            'error': str(e)
        }


@router.get("/{article_id}/stats")
async def get_article_rating_stats(
        article_id: str,
        current_user: User = Depends(jwt_optional_dependency)
):
    """
    获取文章评分统计
    """
    try:
        # 获取文章评分插件
        rating_plugin = plugin_manager.get_plugin('article-rating')
        if not rating_plugin:
            return {
                'success': False,
                'message': '评分插件未加载'
            }

        # 获取统计数据
        stats = rating_plugin.get_article_stats(article_id)

        # 如果用户已登录，获取其评分
        user_rating = None
        if current_user:
            user_rating_obj = rating_plugin.get_user_rating(str(current_user.id), article_id)
            if user_rating_obj:
                user_rating = user_rating_obj['rating']

        return {
            'success': True,
            'data': {
                'stats': stats,
                'user_rating': user_rating,
            }
        }

    except Exception as e:
        import traceback
        print(f"Error getting rating stats: {str(e)}")
        print(traceback.format_exc())
        return {
            'success': False,
            'error': str(e)
        }


@router.get("/{article_id}/ratings")
async def get_article_ratings(
        article_id: str,
        limit: int = 10,
        current_user: User = Depends(jwt_optional_dependency)
):
    """
    获取文章的评分列表
    """
    try:
        # 获取文章评分插件
        rating_plugin = plugin_manager.get_plugin('article-rating')
        if not rating_plugin:
            return {
                'success': False,
                'message': '评分插件未加载'
            }

        # 获取评分列表
        ratings = rating_plugin.get_recent_ratings(article_id=article_id, limit=limit)

        return {
            'success': True,
            'data': ratings
        }

    except Exception as e:
        import traceback
        print(f"Error getting ratings: {str(e)}")
        print(traceback.format_exc())
        return {
            'success': False,
            'error': str(e)
        }
