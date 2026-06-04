"""
文章修订历史服务
提供版本保存、查询、回滚等功能
"""

import hashlib

from datetime import datetime, timezone
from typing import Optional, Dict, Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.article import Article
from shared.models.article_content import ArticleContent
from shared.models.article_revision import ArticleRevision

from src.unified_logger import default_logger as logger


def calculate_revision_hash(
        title: str,
        content: str,
        cover_image: str = "",
        tags_list: str = ""
) -> str:
    """
    计算修订版本的哈希码（基于标题、内容、封面图、标签）
    
    Args:
        title: 标题
        content: 内容
        cover_image: 封面图
        tags_list: 标签列表
        
    Returns:
        SHA256哈希字符串
    """
    # 确保所有字段都是字符串类型，避免None值
    title = title or ""
    content = content or ""
    cover_image = cover_image or ""
    tags_list = tags_list or ""

    # 将四个字段组合成一个字符串，使用分隔符避免歧义
    hash_input = f"title:{title}||content:{content}||cover:{cover_image}||tags:{tags_list}"
    # 计算SHA256哈希
    return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()


async def save_article_revision(
        db: AsyncSession,
        article_id: int,
        author_id: int,
        change_summary: Optional[str] = None
) -> Optional[ArticleRevision]:
    """
    保存文章修订版本（优化：减少查询次数 + 去重）
    
    Args:
        db: 数据库会话
        article_id: 文章ID
        author_id: 作者ID
        change_summary: 变更说明
        
    Returns:
        创建的修订对象，如果内容未变化则返回None
    """
    try:
        # 使用 JOIN 一次性获取文章和内容
        query = (
            select(Article, ArticleContent)
            .outerjoin(ArticleContent, Article.id == ArticleContent.article)
            .where(Article.id == article_id)
        )
        result = await db.execute(query)
        row = result.first()

        if not row:
            return None

        article, content_obj = row

        if not content_obj:
            return None

        # 计算当前内容的哈希码
        current_hash = calculate_revision_hash(
            title=article.title or "",
            content=content_obj.content or "",
            cover_image=article.cover_image or "",
            tags_list=article.tags_list or ""
        )

        # 检查是否与最新的修订版本相同（去重）
        latest_revision_query = (
            select(ArticleRevision)
            .where(ArticleRevision.article_id == article_id)
            .order_by(ArticleRevision.revision_number.desc())
            .limit(1)
        )
        latest_result = await db.execute(latest_revision_query)
        latest_revision = latest_result.scalar_one_or_none()

        if latest_revision and latest_revision.hash_code == current_hash:
            logger.info(f"文章 {article_id} 内容未变化，跳过创建修订版本")
            return None

        # 计算下一个版本号
        max_rev_query = select(func.max(ArticleRevision.revision_number)).where(
            ArticleRevision.article_id == article_id
        )
        max_rev_result = await db.execute(max_rev_query)
        next_revision = (max_rev_result.scalar() or 0) + 1

        # 创建修订记录
        revision = ArticleRevision(
            article_id=article_id,
            revision_number=next_revision,
            title=article.title,
            excerpt=article.excerpt,
            content=content_obj.content,
            cover_image=article.cover_image,
            tags_list=article.tags_list,
            category_id=article.category,
            status=article.status,
            hidden=article.hidden,
            is_featured=article.is_featured,
            is_vip_only=article.is_vip_only,
            required_vip_level=article.required_vip_level,
            author_id=author_id,
            change_summary=change_summary,
            hash_code=current_hash,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None)  # 移除时区信息以匹配数据库字段
        )

        db.add(revision)
        await db.commit()
        await db.refresh(revision)

        return revision

    except Exception as e:
        await db.rollback()
        logger.error(f"保存修订失败: {e}", exc_info=True)
        return None


async def get_article_revisions(
        db: AsyncSession,
        article_id: int,
        page: int = 1,
        per_page: int = 20
) -> Dict[str, Any]:
    """
    获取文章的修订历史列表
    
    Args:
        db: 数据库会话
        article_id: 文章ID
        page: 页码
        per_page: 每页数量
        
    Returns:
        包含修订列表和分页信息的字典
    """
    try:
        # 查询总数
        count_query = select(func.count(ArticleRevision.id)).where(
            ArticleRevision.article_id == article_id
        )
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # 计算分页
        offset = (page - 1) * per_page
        total_pages = (total + per_page - 1) // per_page if total > 0 else 1

        # 查询修订列表（按版本号降序）
        revisions_query = (
            select(ArticleRevision)
            .where(ArticleRevision.article_id == article_id)
            .order_by(ArticleRevision.revision_number.desc())
            .offset(offset)
            .limit(per_page)
        )
        revisions_result = await db.execute(revisions_query)
        revisions = revisions_result.scalars().all()

        return {
            "revisions": [rev.to_dict() for rev in revisions],
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
        logger.error(f"获取修订历史失败: {e}", exc_info=True)
        return {
            "revisions": [],
            "pagination": {
                "current_page": page,
                "per_page": per_page,
                "total": 0,
                "total_pages": 0,
                "has_next": False,
                "has_prev": False
            }
        }


async def get_revision_detail(
        db: AsyncSession,
        revision_id: int
) -> Optional[Dict[str, Any]]:
    """
    获取特定修订版本的详细信息
    
    Args:
        db: 数据库会话
        revision_id: 修订ID
        
    Returns:
        修订详情字典
    """
    try:
        revision_query = select(ArticleRevision).where(
            ArticleRevision.id == revision_id
        )
        revision_result = await db.execute(revision_query)
        revision = revision_result.scalar_one_or_none()

        if not revision:
            return None

        return revision.to_dict()

    except Exception as e:
        logger.error(f"获取修订详情失败: {e}", exc_info=True)
        return None


async def rollback_to_revision(
        db: AsyncSession,
        article_id: int,
        revision_id: int,
        author_id: int
) -> bool:
    """
    回滚到指定修订版本（优化：减少查询次数）
    
    Args:
        db: 数据库会话
        article_id: 文章ID
        revision_id: 目标修订ID
        author_id: 执行回滚的用户ID
        
    Returns:
        是否成功
    """
    try:
        # 获取目标修订
        revision_query = select(ArticleRevision).where(
            ArticleRevision.id == revision_id,
            ArticleRevision.article_id == article_id
        )
        revision_result = await db.execute(revision_query)
        revision = revision_result.scalar_one_or_none()

        if not revision:
            return False

        # 获取当前文章和内容
        article_query = (
            select(Article, ArticleContent)
            .outerjoin(ArticleContent, Article.id == ArticleContent.article)
            .where(Article.id == article_id)
        )
        article_result = await db.execute(article_query)
        row = article_result.first()

        if not row:
            return False

        article, content_obj = row

        # 更新文章内容
        now = datetime.now(timezone.utc).replace(tzinfo=None)  # 移除时区信息以匹配数据库字段
        if content_obj:
            content_obj.content = revision.content
            content_obj.updated_at = now
        else:
            # 如果内容不存在，创建新的
            new_content = ArticleContent(
                article=article_id,
                content=revision.content,
                created_at=now,
                updated_at=now
            )
            db.add(new_content)

        # 更新文章元数据
        article.title = revision.title
        article.excerpt = revision.excerpt
        article.cover_image = revision.cover_image
        article.tags_list = revision.tags_list
        article.category = revision.category_id
        article.status = revision.status
        article.hidden = revision.hidden
        article.is_featured = revision.is_featured
        article.is_vip_only = revision.is_vip_only
        article.required_vip_level = revision.required_vip_level
        article.updated_at = now

        await db.commit()

        # 自动创建回滚操作的修订记录
        await save_article_revision(
            db=db,
            article_id=article_id,
            author_id=author_id,
            change_summary=f"回滚到版本 #{revision.revision_number}"
        )

        return True

    except Exception as e:
        await db.rollback()
        logger.error(f"回滚失败: {e}", exc_info=True)
        return False


async def compare_revisions(
        db: AsyncSession,
        revision1_id: int,
        revision2_id: int
) -> Optional[Dict[str, Any]]:
    """
    比较两个修订版本的差异
    
    Args:
        db: 数据库会话
        revision1_id: 第一个修订ID
        revision2_id: 第二个修订ID
        
    Returns:
        包含差异信息的字典
    """
    try:
        # 批量获取两个修订
        revisions_query = select(ArticleRevision).where(
            ArticleRevision.id.in_([revision1_id, revision2_id])
        )
        revisions_result = await db.execute(revisions_query)
        revisions = {rev.id: rev for rev in revisions_result.scalars().all()}

        rev1 = revisions.get(revision1_id)
        rev2 = revisions.get(revision2_id)

        if not rev1 or not rev2:
            return None

        # 比较各个字段的差异
        differences = {
            "title_changed": rev1.title != rev2.title,
            "excerpt_changed": rev1.excerpt != rev2.excerpt,
            "content_changed": rev1.content != rev2.content,
            "cover_image_changed": rev1.cover_image != rev2.cover_image,
            "tags_changed": rev1.tags_list != rev2.tags_list,
            "category_changed": rev1.category_id != rev2.category_id,
            "status_changed": rev1.status != rev2.status,
        }

        return {
            "revision1": rev1.to_dict(),
            "revision2": rev2.to_dict(),
            "differences": differences
        }

    except Exception as e:
        logger.error(f"比较修订失败: {e}", exc_info=True)
        return None


async def delete_revision(
        db: AsyncSession,
        revision_id: int,
        article_id: int
) -> bool:
    """
    删除指定的修订版本
    
    Args:
        db: 数据库会话
        revision_id: 修订ID
        article_id: 文章ID（用于验证权限）
        
    Returns:
        是否成功删除
    """
    try:
        # 获取修订记录并验证属于指定文章
        revision_query = select(ArticleRevision).where(
            ArticleRevision.id == revision_id,
            ArticleRevision.article_id == article_id
        )
        revision_result = await db.execute(revision_query)
        revision = revision_result.scalar_one_or_none()

        if not revision:
            return False

        # 删除修订记录
        await db.delete(revision)
        await db.commit()

        return True

    except Exception as e:
        await db.rollback()
        logger.error(f"删除修订失败: {e}", exc_info=True)
        return False
