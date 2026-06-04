"""
静态页面管理服务
提供页面的CRUD操作和层级管理
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.pages import Pages
from shared.models.user import User


async def get_pages_list(
        db: AsyncSession,
        page: int = 1,
        per_page: int = 20,
        status: Optional[int] = None
) -> Dict[str, Any]:
    """
    获取页面列表（支持分页和状态筛选）
    
    Args:
        db: 数据库会话
        page: 页码
        per_page: 每页数量
        status: 状态筛选（可选）
        
    Returns:
        包含页面列表和分页信息的字典
    """
    try:
        # 构建查询
        query = select(Pages)

        if status is not None:
            query = query.where(Pages.status == status)

        # 查询总数
        count_query = select(func.count(Pages.id))
        if status is not None:
            count_query = count_query.where(Pages.status == status)

        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # 计算分页
        offset = (page - 1) * per_page
        total_pages = (total + per_page - 1) // per_page if total > 0 else 1

        # 查询页面列表（按排序索引和创建时间）
        pages_query = (
            query
            .order_by(Pages.order_index.asc(), Pages.created_at.desc())
            .offset(offset)
            .limit(per_page)
        )
        pages_result = await db.execute(pages_query)
        pages = pages_result.scalars().all()

        # 批量加载作者信息
        author_ids = [p.author_id for p in pages if p.author_id]
        authors_dict = {}
        if author_ids:
            authors_query = select(User).where(User.id.in_(author_ids))
            authors_result = await db.execute(authors_query)
            for author in authors_result.scalars().all():
                authors_dict[author.id] = author

        pages_data = []
        for p in pages:
            pages_data.append({
                "id": p.id,
                "title": p.title,
                "slug": p.slug,
                "excerpt": p.excerpt,
                "template": p.template,
                "status": p.status,
                "parent_id": p.parent_id,
                "order_index": p.order_index,
                "meta_title": p.meta_title,
                "meta_description": p.meta_description,
                "meta_keywords": p.meta_keywords,
                "author": {
                    "id": p.author_id,
                    "username": authors_dict.get(
                        p.author_id).username if p.author_id and p.author_id in authors_dict else "Unknown"
                } if p.author_id else None,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
                "published_at": p.published_at.isoformat() if p.published_at else None
            })

        return {
            "success": True,
            "pages": pages_data,
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
        print(f"获取页面列表失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "pages": [],
            "pagination": {
                "current_page": page,
                "per_page": per_page,
                "total": 0,
                "total_pages": 0,
                "has_next": False,
                "has_prev": False
            }
        }


async def get_page_by_slug(db: AsyncSession, slug: str) -> Optional[Dict[str, Any]]:
    """
    根据slug获取页面详情
    
    Args:
        db: 数据库会话
        slug: 页面slug
        
    Returns:
        页面详情字典
    """
    try:
        query = select(Pages).where(Pages.slug == slug)
        result = await db.execute(query)
        page = result.scalar_one_or_none()

        if not page:
            return None

        # 获取作者信息
        author = None
        if page.author_id:
            author_query = select(User).where(User.id == page.author_id)
            author_result = await db.execute(author_query)
            author = author_result.scalar_one_or_none()

        return {
            "id": page.id,
            "title": page.title,
            "slug": page.slug,
            "content": page.content,
            "excerpt": page.excerpt,
            "template": page.template,
            "status": page.status,
            "parent_id": page.parent_id,
            "order_index": page.order_index,
            "meta_title": page.meta_title,
            "meta_description": page.meta_description,
            "meta_keywords": page.meta_keywords,
            "author": {
                "id": author.id,
                "username": author.username
            } if author else None,
            "created_at": page.created_at.isoformat() if page.created_at else None,
            "updated_at": page.updated_at.isoformat() if page.updated_at else None,
            "published_at": page.published_at.isoformat() if page.published_at else None
        }

    except Exception as e:
        print(f"获取页面详情失败: {e}")
        return None


async def create_page(
        db: AsyncSession,
        title: str,
        slug: str,
        content: str,
        author_id: int,
        excerpt: Optional[str] = None,
        template: Optional[str] = None,
        status: int = 0,
        parent_id: Optional[int] = None,
        order_index: int = 0,
        meta_title: Optional[str] = None,
        meta_description: Optional[str] = None,
        meta_keywords: Optional[str] = None
) -> Optional[Pages]:
    """
    创建新页面
    
    Args:
        db: 数据库会话
        title: 页面标题
        slug: 页面slug
        content: 页面内容
        author_id: 作者ID
        excerpt: 摘要
        template: 模板
        status: 状态（0:草稿，1:已发布）
        parent_id: 父页面ID
        order_index: 排序索引
        meta_title: SEO标题
        meta_description: SEO描述
        meta_keywords: SEO关键词
        
    Returns:
        创建的页面对象
    """
    try:
        now = datetime.now(timezone.utc)

        page = Pages(
            title=title,
            slug=slug,
            content=content,
            excerpt=excerpt,
            template=template,
            status=status,
            author_id=author_id,
            parent_id=parent_id,
            order_index=order_index,
            meta_title=meta_title,
            meta_description=meta_description,
            meta_keywords=meta_keywords,
            created_at=now,
            updated_at=now,
            published_at=now if status == 1 else None
        )

        db.add(page)
        await db.commit()
        await db.refresh(page)

        return page

    except Exception as e:
        await db.rollback()
        print(f"创建页面失败: {e}")
        import traceback
        traceback.print_exc()
        return None


async def update_page(
        db: AsyncSession,
        page_id: int,
        **kwargs
) -> bool:
    """
    更新页面
    
    Args:
        db: 数据库会话
        page_id: 页面ID
        **kwargs: 要更新的字段
        
    Returns:
        是否成功
    """
    try:
        query = select(Pages).where(Pages.id == page_id)
        result = await db.execute(query)
        page = result.scalar_one_or_none()

        if not page:
            return False

        # 更新字段
        for key, value in kwargs.items():
            if hasattr(page, key):
                setattr(page, key, value)

        page.updated_at = datetime.now(timezone.utc)

        # 如果状态变为已发布，设置发布时间
        if kwargs.get('status') == 1 and not page.published_at:
            page.published_at = datetime.now(timezone.utc)

        await db.commit()

        return True

    except Exception as e:
        await db.rollback()
        print(f"更新页面失败: {e}")
        return False


async def delete_page(db: AsyncSession, page_id: int) -> bool:
    """
    删除页面
    
    Args:
        db: 数据库会话
        page_id: 页面ID
        
    Returns:
        是否成功
    """
    try:
        query = select(Pages).where(Pages.id == page_id)
        result = await db.execute(query)
        page = result.scalar_one_or_none()

        if not page:
            return False

        await db.delete(page)
        await db.commit()

        return True

    except Exception as e:
        await db.rollback()
        print(f"删除页面失败: {e}")
        return False


async def get_page_hierarchy(db: AsyncSession) -> List[Dict[str, Any]]:
    """
    获取页面层级结构（用于菜单树）
    
    Args:
        db: 数据库会话
        
    Returns:
        层级化的页面列表
    """
    try:
        # 获取所有已发布的页面
        query = (
            select(Pages)
            .where(Pages.status == 1)
            .order_by(Pages.order_index.asc(), Pages.created_at.asc())
        )
        result = await db.execute(query)
        all_pages = result.scalars().all()

        # 构建层级结构
        pages_dict = {p.id: {**p.to_dict(), "children": []} for p in all_pages}
        root_pages = []

        for page_data in pages_dict.values():
            parent_id = page_data["parent_id"]
            if parent_id and parent_id in pages_dict:
                pages_dict[parent_id]["children"].append(page_data)
            else:
                root_pages.append(page_data)

        return root_pages

    except Exception as e:
        print(f"获取页面层级失败: {e}")
        return []
