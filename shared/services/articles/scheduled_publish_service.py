"""
文章定时发布服务
负责检查并自动发布到期的定时文章
"""

from datetime import datetime, timezone
from typing import Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.article import Article


async def check_and_publish_scheduled_articles(db: AsyncSession) -> Dict[str, Any]:
    """
    检查并发布到期的定时文章
    
    Args:
        db: 数据库会话
        
    Returns:
        包含发布统计信息的字典
    """
    try:
        now = datetime.now(timezone.utc)

        # 查询所有状态为草稿(0)且有定时发布时间且时间已到的文章
        query = (
            select(Article)
            .where(
                Article.status == 0,  # 草稿状态
                Article.scheduled_publish_at.isnot(None),
                Article.scheduled_publish_at <= now
            )
        )

        result = await db.execute(query)
        articles_to_publish = result.scalars().all()

        published_count = 0
        failed_count = 0
        published_articles = []

        for article in articles_to_publish:
            try:
                # 更新文章状态为已发布
                article.status = 1
                article.updated_at = now

                published_articles.append({
                    "id": article.id,
                    "title": article.title,
                    "scheduled_time": article.scheduled_publish_at.isoformat(),
                    "published_time": now.isoformat()
                })

                published_count += 1

            except Exception as e:
                print(f"发布文章 {article.id} 失败: {e}")
                failed_count += 1

        # 提交所有更改
        if published_count > 0:
            await db.commit()

        return {
            "success": True,
            "published_count": published_count,
            "failed_count": failed_count,
            "total_checked": len(articles_to_publish),
            "published_articles": published_articles
        }

    except Exception as e:
        await db.rollback()
        print(f"检查定时发布失败: {e}")
        import traceback
        traceback.print_exc()

        return {
            "success": False,
            "error": str(e),
            "published_count": 0,
            "failed_count": 0,
            "total_checked": 0,
            "published_articles": []
        }


async def get_scheduled_articles(
        db: AsyncSession,
        page: int = 1,
        per_page: int = 20
) -> Dict[str, Any]:
    """
    获取所有待发布的定时文章列表
    
    Args:
        db: 数据库会话
        page: 页码
        per_page: 每页数量
        
    Returns:
        包含文章列表和分页信息的字典
    """
    try:
        from sqlalchemy import func

        # 查询总数
        count_query = (
            select(func.count(Article.id))
            .where(
                Article.status == 0,
                Article.scheduled_publish_at.isnot(None)
            )
        )
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # 计算分页
        offset = (page - 1) * per_page
        total_pages = (total + per_page - 1) // per_page if total > 0 else 1

        # 查询文章列表（按定时发布时间排序）
        articles_query = (
            select(Article)
            .where(
                Article.status == 0,
                Article.scheduled_publish_at.isnot(None)
            )
            .order_by(Article.scheduled_publish_at.asc())
            .offset(offset)
            .limit(per_page)
        )
        articles_result = await db.execute(articles_query)
        articles = articles_result.scalars().all()

        articles_data = []
        for article in articles:
            articles_data.append({
                "id": article.id,
                "title": article.title,
                "slug": article.slug,
                "excerpt": article.excerpt,
                "cover_image": article.cover_image,
                "status": article.status,
                "scheduled_publish_at": article.scheduled_publish_at.isoformat() if article.scheduled_publish_at else None,
                "created_at": article.created_at.isoformat() if article.created_at else None,
                "updated_at": article.updated_at.isoformat() if article.updated_at else None
            })

        return {
            "success": True,
            "articles": articles_data,
            "pagination": {
                "current_page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }

    except Exception as e:
        print(f"获取定时文章列表失败: {e}")
        import traceback
        traceback.print_exc()

        return {
            "success": False,
            "error": str(e),
            "articles": [],
            "pagination": {
                "current_page": page,
                "per_page": per_page,
                "total": 0,
                "total_pages": 0,
                "has_next": False,
                "has_prev": False
            }
        }


async def cancel_scheduled_publish(
        db: AsyncSession,
        article_id: int
) -> bool:
    """
    取消文章的定时发布
    
    Args:
        db: 数据库会话
        article_id: 文章ID
        
    Returns:
        是否成功
    """
    try:
        # 获取文章
        article_query = select(Article).where(Article.id == article_id)
        article_result = await db.execute(article_query)
        article = article_result.scalar_one_or_none()

        if not article:
            return False

        # 清除定时发布时间
        article.scheduled_publish_at = None
        article.updated_at = datetime.now(timezone.utc)

        await db.commit()

        return True

    except Exception as e:
        await db.rollback()
        print(f"取消定时发布失败: {e}")
        return False
