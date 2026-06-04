"""
文章批注 API
支持协作编辑时的评论和批注功能
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import jwt_required
from src.utils.database.main import get_async_session

router = APIRouter(tags=["annotations"])


@router.post("/", summary="创建批注")
async def create_annotation(
        article_id: int = Body(..., description="文章ID"),
        content: str = Body(..., description="批注内容"),
        position: Optional[dict] = Body(None, description="批注位置（JSON）"),
        selection_text: Optional[str] = Body(None, description="选中的文本"),
        parent_id: Optional[int] = Body(None, description="父批注ID（回复）"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_session)
):
    """
    创建文章批注
    
    Args:
        article_id: 文章ID
        content: 批注内容
        position: 批注位置信息
        selection_text: 选中的文本片段
        parent_id: 父批注ID（用于回复）
        
    Returns:
        创建的批注
    """
    try:
        from shared.models.article_annotation import ArticleAnnotation
        from datetime import datetime
        from sqlalchemy import select

        # 验证文章是否存在
        from shared.models.article import Article
        article_result = await db.execute(
            select(Article).where(Article.id == article_id)
        )
        article = article_result.scalar_one_or_none()

        if not article:
            return ApiResponse(success=False, error="文章不存在")

        # 如果是回复，验证父批注
        if parent_id:
            parent_result = await db.execute(
                select(ArticleAnnotation).where(ArticleAnnotation.id == parent_id)
            )
            parent = parent_result.scalar_one_or_none()

            if not parent:
                return ApiResponse(success=False, error="父批注不存在")

            if parent.article != article_id:
                return ApiResponse(success=False, error="父批注不属于该文章")

        # 创建批注
        annotation = ArticleAnnotation(
            article=article_id,
            user=current_user.id,
            parent=parent_id,
            content=content,
            position=str(position) if position else None,
            selection_text=selection_text,
            is_resolved=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        db.add(annotation)
        await db.commit()
        await db.refresh(annotation)

        # 获取用户信息
        from shared.models.user import User
        user_result = await db.execute(
            select(User).where(User.id == current_user.id)
        )
        user = user_result.scalar_one_or_none()

        return ApiResponse(
            success=True,
            data={
                'id': annotation.id,
                'article_id': annotation.article,
                'user_id': annotation.user,
                'username': user.username if user else 'Unknown',
                'content': annotation.content,
                'position': annotation.position,
                'selection_text': annotation.selection_text,
                'is_resolved': annotation.is_resolved,
                'parent_id': annotation.parent,
                'created_at': annotation.created_at.isoformat(),
                'updated_at': annotation.updated_at.isoformat(),
            }
        )
    except Exception as e:
        await db.rollback()
        import traceback
        print(f"Error creating annotation: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=f"创建批注失败: {str(e)}")


@router.get("/article/{article_id}", summary="获取文章的所有批注")
async def get_article_annotations(
        article_id: int,
        resolved: Optional[bool] = Query(None, description="筛选已解决/未解决"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_session)
):
    """
    获取文章的所有批注（包括回复）
    
    Args:
        article_id: 文章ID
        resolved: 筛选已解决或未解决的批注
        
    Returns:
        批注列表（树形结构）
    """
    try:
        from shared.models.article_annotation import ArticleAnnotation
        from shared.models.user import User
        from sqlalchemy import select

        # 构建查询
        query = select(ArticleAnnotation).where(
            ArticleAnnotation.article == article_id
        )

        if resolved is not None:
            query = query.where(ArticleAnnotation.is_resolved == resolved)

        query = query.order_by(ArticleAnnotation.created_at.asc())

        result = await db.execute(query)
        annotations = result.scalars().all()

        # 获取所有用户信息
        user_ids = list(set([ann.user for ann in annotations]))
        users_result = await db.execute(
            select(User).where(User.id.in_(user_ids))
        )
        users = {user.id: user for user in users_result.scalars().all()}

        # 构建树形结构
        annotation_list = []
        annotations_dict = {}

        for ann in annotations:
            user = users.get(ann.user)
            annotation_data = {
                'id': ann.id,
                'article_id': ann.article,
                'user_id': ann.user,
                'username': user.username if user else 'Unknown',
                'content': ann.content,
                'position': ann.position,
                'selection_text': ann.selection_text,
                'is_resolved': ann.is_resolved,
                'parent_id': ann.parent,
                'created_at': ann.created_at.isoformat(),
                'updated_at': ann.updated_at.isoformat(),
                'replies': [],
            }
            annotations_dict[ann.id] = annotation_data

            if ann.parent is None:
                annotation_list.append(annotation_data)
            else:
                # 添加到父批注的replies中
                if ann.parent in annotations_dict:
                    annotations_dict[ann.parent]['replies'].append(annotation_data)

        return ApiResponse(
            success=True,
            data={
                'annotations': annotation_list,
                'count': len(annotation_list),
            }
        )
    except Exception as e:
        import traceback
        print(f"Error getting annotations: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=f"获取批注失败: {str(e)}")


@router.put("/{annotation_id}", summary="更新批注")
async def update_annotation(
        annotation_id: int,
        content: Optional[str] = Body(None, description="批注内容"),
        is_resolved: Optional[bool] = Body(None, description="是否已解决"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_session)
):
    """
    更新批注（只能更新自己的批注或管理员）
    
    Args:
        annotation_id: 批注ID
        content: 新的批注内容
        is_resolved: 解决状态
        
    Returns:
        更新后的批注
    """
    try:
        from shared.models.article_annotation import ArticleAnnotation
        from sqlalchemy import select
        from datetime import datetime

        result = await db.execute(
            select(ArticleAnnotation).where(ArticleAnnotation.id == annotation_id)
        )
        annotation = result.scalar_one_or_none()

        if not annotation:
            return ApiResponse(success=False, error="批注不存在")

        # 权限检查：只能修改自己的批注或管理员
        is_admin = getattr(current_user, 'is_superuser', False)
        if annotation.user != current_user.id and not is_admin:
            return ApiResponse(success=False, error="无权修改此批注")

        # 更新字段
        if content is not None:
            annotation.content = content

        if is_resolved is not None:
            annotation.is_resolved = is_resolved

        annotation.updated_at = datetime.now()

        await db.commit()
        await db.refresh(annotation)

        return ApiResponse(
            success=True,
            data={
                'message': '批注更新成功',
                'id': annotation.id,
                'is_resolved': annotation.is_resolved,
            }
        )
    except Exception as e:
        await db.rollback()
        import traceback
        print(f"Error updating annotation: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=f"更新批注失败: {str(e)}")


@router.delete("/{annotation_id}", summary="删除批注")
async def delete_annotation(
        annotation_id: int,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_session)
):
    """
    删除批注（只能删除自己的批注或管理员）
    
    Args:
        annotation_id: 批注ID
        
    Returns:
        删除结果
    """
    try:
        from shared.models.article_annotation import ArticleAnnotation
        from sqlalchemy import select

        result = await db.execute(
            select(ArticleAnnotation).where(ArticleAnnotation.id == annotation_id)
        )
        annotation = result.scalar_one_or_none()

        if not annotation:
            return ApiResponse(success=False, error="批注不存在")

        # 权限检查：只能删除自己的批注或管理员
        is_admin = getattr(current_user, 'is_superuser', False)
        if annotation.user != current_user.id and not is_admin:
            return ApiResponse(success=False, error="无权删除此批注")

        # 删除批注及其所有回复
        await db.delete(annotation)
        await db.commit()

        return ApiResponse(
            success=True,
            data={'message': '批注删除成功'}
        )
    except Exception as e:
        await db.rollback()
        import traceback
        print(f"Error deleting annotation: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=f"删除批注失败: {str(e)}")
