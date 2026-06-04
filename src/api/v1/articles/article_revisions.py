"""
文章修订历史API端点
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query, Body
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from shared.services.articles.article_manager import compare_revisions, get_article_revisions, get_revision_detail, \
    rollback_to_revision, save_article_revision, delete_revision
from src.api.v1.core.responses import ApiResponse
from src.auth import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db

router = APIRouter(tags=["article-revisions"])


class DraftData(BaseModel):
    """草稿数据模型"""
    title: Optional[str] = None
    excerpt: Optional[str] = None
    content: Optional[str] = ""
    cover_image: Optional[str] = None
    tags: Optional[str] = None
    category_id: Optional[int] = None

    class Config:
        extra = "ignore"  # 忽略额外字段


class CreateRevisionRequest(BaseModel):
    """创建修订请求模型"""
    change_summary: Optional[str] = None
    # 可选的草稿数据（如果提供，则使用这些数据创建修订）
    title: Optional[str] = None
    excerpt: Optional[str] = None
    content: Optional[str] = None
    cover_image: Optional[str] = None
    tags: Optional[str] = None
    category_id: Optional[int] = None


@router.post("/{article_id}/revisions")
async def create_article_revision(
        article_id: int,
        request_data: CreateRevisionRequest = Body(None),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    手动创建文章修订版本或同步本地草稿
    
    Args:
        article_id: 文章ID
        request_data: 请求数据，包含变更说明和可选的草稿数据
    """
    try:
        change_summary = request_data.change_summary if request_data else None

        # 检查是否提供了草稿数据
        has_draft_data = any([
            request_data and request_data.title,
            request_data and request_data.content,
        ])

        if has_draft_data and request_data:
            # 如果有草稿数据，先更新文章，然后创建修订
            from shared.models.article import Article
            from shared.models.article_content import ArticleContent
            from sqlalchemy import select

            # 获取当前文章
            article_query = (
                select(Article, ArticleContent)
                .outerjoin(ArticleContent, Article.id == ArticleContent.article)
                .where(Article.id == article_id)
            )
            article_result = await db.execute(article_query)
            row = article_result.first()

            if not row:
                return ApiResponse(
                    success=False,
                    error="文章不存在"
                )

            article, content_obj = row

            # 智能合并：只更新提供的字段
            if request_data.title is not None:
                article.title = request_data.title
            if request_data.excerpt is not None:
                article.excerpt = request_data.excerpt
            if request_data.cover_image is not None:
                article.cover_image = request_data.cover_image
            if request_data.tags is not None:
                article.tags_list = request_data.tags
            if request_data.category_id is not None:
                article.category = request_data.category_id

            # 更新内容
            if request_data.content is not None:
                now = datetime.now(timezone.utc).replace(tzinfo=None)  # 移除时区信息以匹配数据库字段
                if content_obj:
                    content_obj.content = request_data.content
                    content_obj.updated_at = now
                else:
                    new_content = ArticleContent(
                        article=article_id,
                        content=request_data.content,
                        created_at=now,
                        updated_at=now
                    )
                    db.add(new_content)

            article.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)  # 移除时区信息以匹配数据库字段
            await db.commit()

            # 创建修订版本
            revision = await save_article_revision(
                db=db,
                article_id=article_id,
                author_id=current_user.id,
                change_summary=change_summary or "从本地草稿同步"
            )
        else:
            # 没有草稿数据，直接基于数据库当前状态创建修订
            revision = await save_article_revision(
                db=db,
                article_id=article_id,
                author_id=current_user.id,
                change_summary=change_summary
            )

        if not revision:
            # 检查是否是因为去重而跳过
            return ApiResponse(
                success=True,
                data={
                    "message": "内容未发生变化，已跳过创建修订版本",
                    "skipped": True,
                    "reason": "deduplication"
                }
            )

        return ApiResponse(
            success=True,
            data={
                "message": "修订版本已保存",
                "revision": revision.to_dict()
            }
        )

    except Exception as e:
        import traceback
        print(f"Error creating revision: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/{article_id}/revisions")
async def list_article_revisions(
        article_id: int,
        page: int = Query(1, ge=1, description="页码"),
        per_page: int = Query(20, ge=1, le=100, description="每页数量"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取文章的修订历史列表
    
    Args:
        article_id: 文章ID
        page: 页码
        per_page: 每页数量
    """
    try:
        result = await get_article_revisions(
            db=db,
            article_id=article_id,
            page=page,
            per_page=per_page
        )

        return ApiResponse(
            success=True,
            data=result
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/revisions/compare")
async def compare_article_revisions(
        revision1_id: int = Query(..., description="第一个修订ID"),
        revision2_id: int = Query(..., description="第二个修订ID"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    比较两个修订版本的差异
    
    Args:
        revision1_id: 第一个修订ID
        revision2_id: 第二个修订ID
    """
    try:
        result = await compare_revisions(
            db=db,
            revision1_id=revision1_id,
            revision2_id=revision2_id
        )

        if not result:
            return ApiResponse(
                success=False,
                error="无法比较，修订版本可能不存在"
            )

        return ApiResponse(
            success=True,
            data=result
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/{revision_id}")
async def get_revision(
        revision_id: int,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取特定修订版本的详细信息
    
    Args:
        revision_id: 修订ID
    """
    try:
        revision = await get_revision_detail(
            db=db,
            revision_id=revision_id
        )

        if not revision:
            return ApiResponse(
                success=False,
                error="修订版本不存在"
            )

        return ApiResponse(
            success=True,
            data=revision
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/{article_id}/revisions/{revision_id}/rollback")
async def rollback_article(
        article_id: int,
        revision_id: int,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    回滚文章到指定修订版本
    
    Args:
        article_id: 文章ID
        revision_id: 目标修订ID
    """
    try:
        success = await rollback_to_revision(
            db=db,
            article_id=article_id,
            revision_id=revision_id,
            author_id=current_user.id
        )

        if not success:
            return ApiResponse(
                success=False,
                error="回滚失败，请检查文章和修订版本是否存在"
            )

        return ApiResponse(
            success=True,
            data={"message": "文章已成功回滚到指定版本"}
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/{article_id}/revisions/sync")
async def sync_article_revisions(
        article_id: int,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    同步文章修订历史到云端（强制保存当前状态为修订版本）
    
    Args:
        article_id: 文章ID
    """
    try:
        # 保存当前状态为修订版本
        revision = await save_article_revision(
            db=db,
            article_id=article_id,
            author_id=current_user.id,
            change_summary="手动同步到云端"
        )

        if not revision:
            return ApiResponse(
                success=False,
                error="同步失败，文章可能不存在"
            )

        return ApiResponse(
            success=True,
            data={
                "message": "修订历史已同步到云端",
                "revision": revision.to_dict()
            }
        )

    except Exception as e:
        import traceback
        print(f"Error syncing revisions: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.delete("/{article_id}/revisions/{revision_id}")
async def delete_article_revision(
        article_id: int,
        revision_id: int,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    删除指定的修订版本
    
    Args:
        article_id: 文章ID
        revision_id: 修订ID
    """
    try:
        success = await delete_revision(
            db=db,
            revision_id=revision_id,
            article_id=article_id
        )

        if not success:
            return ApiResponse(
                success=False,
                error="删除失败，修订版本可能不存在或不属于该文章"
            )

        return ApiResponse(
            success=True,
            data={"message": "修订版本已成功删除"}
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))
