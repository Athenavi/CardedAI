"""
小部件(Widgets)管理API
提供小部件的CRUD和渲染功能
"""

from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from shared.services.widgets.widget_manager import widget_service
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import admin_required as admin_required_api
from src.extensions import get_async_db_session as get_async_db

router = APIRouter(tags=["widgets"])


@router.get("/")
async def list_all_widgets(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    area: Optional[str] = Query(None),
    current_user=Depends(admin_required_api),
    db: AsyncSession = Depends(get_async_db)
):
    """获取所有小部件实例列表"""
    try:
        from shared.models.widget_instance import WidgetInstance
        from sqlalchemy import select, func

        query = select(WidgetInstance)
        count_query = select(func.count()).select_from(WidgetInstance)

        if area:
            query = query.where(WidgetInstance.area == area)
            count_query = count_query.where(WidgetInstance.area == area)

        # 总数
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页查询
        offset = (page - 1) * per_page
        query = query.order_by(WidgetInstance.area, WidgetInstance.order_index).offset(offset).limit(per_page)
        result = await db.execute(query)
        widgets = [w.to_dict() for w in result.scalars().all()]

        return ApiResponse(
            success=True,
            data={
                'items': widgets,
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return ApiResponse(success=False, error=f"获取小部件列表失败: {str(e)}")


@router.get("/types")
async def get_widget_types(category: Optional[str] = Query(None)):
    """获取小部件类型列表"""
    try:
        types = widget_service.get_widget_types(category)

        return ApiResponse(
            success=True,
            data={'types': types}
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取类型失败: {str(e)}")


@router.get("/areas")
async def get_widget_areas():
    """获取小部件区域列表"""
    try:
        areas = widget_service.get_widget_areas()

        return ApiResponse(
            success=True,
            data={'areas': areas}
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取区域失败: {str(e)}")


@router.get("/area/{area_id}")
async def get_area_widgets(area_id: str, db: AsyncSession = Depends(get_async_db)):
    """获取指定区域的小部件"""
    try:
        from shared.models.widget_instance import WidgetInstance
        from sqlalchemy import select

        # 从数据库查询
        stmt = (
            select(WidgetInstance)
            .where(WidgetInstance.area == area_id)
            .order_by(WidgetInstance.order_index.asc())
        )
        result = await db.execute(stmt)
        widgets = result.scalars().all()

        # 转换为字典列表
        widget_list = [w.to_dict() for w in widgets]

        return ApiResponse(
            success=True,
            data={'widgets': widget_list}
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return ApiResponse(success=False, error=f"获取小部件失败: {str(e)}")


@router.post("/register")
async def register_widget(
        area: str = Body(...),
        widget_type: str = Body(...),
        config: Optional[Dict] = Body(None),
        position: Optional[int] = Body(None),
        current_user=Depends(admin_required_api)
):
    """注册小部件到区域"""
    try:
        result = widget_service.register_widget(area, widget_type, config, position)

        if result['success']:
            return ApiResponse(
                success=True,
                data=result['data'],
                message="小部件添加成功"
            )
        else:
            return ApiResponse(success=False, error=result['error'])
    except Exception as e:
        return ApiResponse(success=False, error=f"注册失败: {str(e)}")


@router.put("/{widget_id}/config")
async def update_widget_config(
        widget_id: str,
        config: Dict[str, Any] = Body(...),
        current_user=Depends(admin_required_api)
):
    """更新小部件配置"""
    try:
        result = widget_service.update_widget_config(widget_id, config)

        if result['success']:
            return ApiResponse(success=True, message=result['message'])
        else:
            return ApiResponse(success=False, error=result['error'])
    except Exception as e:
        return ApiResponse(success=False, error=f"更新失败: {str(e)}")


@router.post("/reorder")
async def reorder_widgets(
        area: str = Body(...),
        widget_order: List[str] = Body(...),
        current_user=Depends(admin_required_api)
):
    """重新排序小部件"""
    try:
        result = widget_service.reorder_widgets(area, widget_order)

        if result['success']:
            return ApiResponse(success=True, message=result['message'])
        else:
            return ApiResponse(success=False, error=result['error'])
    except Exception as e:
        return ApiResponse(success=False, error=f"排序失败: {str(e)}")


@router.delete("/{widget_id}")
async def remove_widget(
        widget_id: str,
        current_user=Depends(admin_required_api)
):
    """移除小部件"""
    try:
        result = widget_service.remove_widget(widget_id)

        if result['success']:
            return ApiResponse(success=True, message=result['message'])
        else:
            return ApiResponse(success=False, error=result['error'])
    except Exception as e:
        return ApiResponse(success=False, error=f"移除失败: {str(e)}")


@router.post("")
async def create_widget(
        widget_type: str = Body(...),
        area: str = Body(...),
        title: str = Body(...),
        config: Optional[Dict] = Body(None),
        order_index: int = Body(0),
        is_active: bool = Body(True),
        current_user=Depends(admin_required_api),
        db: AsyncSession = Depends(get_async_db)
):
    """创建小部件实例"""
    try:
        from shared.models.widget_instance import WidgetInstance
        from sqlalchemy import select, func

        # 获取当前区域的最大 order_index
        stmt = select(func.max(WidgetInstance.order_index)).where(
            WidgetInstance.area == area
        )
        result = await db.execute(stmt)
        max_order = result.scalar() or -1

        # 创建新实例
        new_widget = WidgetInstance(
            widget_type=widget_type,
            area=area,
            title=title,
            config=str(config or {}),
            order_index=max_order + 1,
            is_active=is_active,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        db.add(new_widget)
        await db.commit()
        await db.refresh(new_widget)

        return ApiResponse(
            success=True,
            data=new_widget.to_dict(),
            message="Widget 创建成功"
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return ApiResponse(success=False, error=f"创建失败: {str(e)}")


@router.put("/{widget_id}")
async def update_widget(
        widget_id: int,
        title: Optional[str] = Body(None, embed=True),
        config: Optional[Dict] = Body(None, embed=True),
        current_user=Depends(admin_required_api),
        db: AsyncSession = Depends(get_async_db)
):
    """更新小部件配置"""
    try:
        from shared.models.widget_instance import WidgetInstance
        from sqlalchemy import select

        stmt = select(WidgetInstance).where(WidgetInstance.id == widget_id)
        result = await db.execute(stmt)
        widget = result.scalar_one_or_none()

        if not widget:
            return ApiResponse(success=False, error="Widget 不存在")

        if title is not None:
            widget.title = title
        if config is not None:
            widget.config = str(config)

        widget.updated_at = datetime.now()
        await db.commit()
        await db.refresh(widget)

        return ApiResponse(
            success=True,
            data=widget.to_dict(),
            message="Widget 更新成功"
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return ApiResponse(success=False, error=f"更新失败: {str(e)}")


@router.patch("/{widget_id}/toggle")
async def toggle_widget(
        widget_id: int,
        is_active: bool = Body(..., embed=True),
        current_user=Depends(admin_required_api),
        db: AsyncSession = Depends(get_async_db)
):
    """切换小部件启用状态"""
    try:
        from shared.models.widget_instance import WidgetInstance
        from sqlalchemy import select

        stmt = select(WidgetInstance).where(WidgetInstance.id == widget_id)
        result = await db.execute(stmt)
        widget = result.scalar_one_or_none()

        if not widget:
            return ApiResponse(success=False, error="Widget 不存在")

        widget.is_active = is_active
        widget.updated_at = datetime.now()
        await db.commit()

        return ApiResponse(
            success=True,
            message=f"Widget 已{'启用' if is_active else '禁用'}"
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return ApiResponse(success=False, error=f"操作失败: {str(e)}")


@router.patch("/{widget_id}/reorder")
async def reorder_single_widget(
        widget_id: int,
        order_index: int = Body(..., embed=True),
        current_user=Depends(admin_required_api),
        db: AsyncSession = Depends(get_async_db)
):
    """重新排序单个小部件"""
    try:
        from shared.models.widget_instance import WidgetInstance
        from sqlalchemy import select

        stmt = select(WidgetInstance).where(WidgetInstance.id == widget_id)
        result = await db.execute(stmt)
        widget = result.scalar_one_or_none()

        if not widget:
            return ApiResponse(success=False, error="Widget 不存在")

        old_order = widget.order_index
        widget.order_index = order_index
        widget.updated_at = datetime.now()

        # 如果有其他 Widget 在同一位置，调整它们的顺序
        stmt = select(WidgetInstance).where(
            WidgetInstance.area == widget.area,
            WidgetInstance.id != widget_id
        )
        result = await db.execute(stmt)
        other_widgets = result.scalars().all()

        for other_widget in other_widgets:
            if old_order < order_index:
                # 向下移动，中间的 Widget 上移
                if old_order < other_widget.order_index <= order_index:
                    other_widget.order_index -= 1
            elif old_order > order_index:
                # 向上移动，中间的 Widget 下移
                if order_index <= other_widget.order_index < old_order:
                    other_widget.order_index += 1

        await db.commit()

        return ApiResponse(
            success=True,
            message="排序更新成功"
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return ApiResponse(success=False, error=f"排序失败: {str(e)}")


@router.post("/batch-reorder")
async def batch_reorder_widgets(
        updates: List[Dict[str, Any]] = Body(...),
        current_user=Depends(admin_required_api),
        db: AsyncSession = Depends(get_async_db)
):
    """批量重新排序小部件（用于拖拽排序）"""
    try:
        from shared.models.widget_instance import WidgetInstance
        from sqlalchemy import select

        # 批量更新所有 widget 的 order_index
        for update_data in updates:
            widget_id = update_data.get('id')
            new_order = update_data.get('order_index')

            if widget_id is None or new_order is None:
                continue

            stmt = select(WidgetInstance).where(WidgetInstance.id == widget_id)
            result = await db.execute(stmt)
            widget = result.scalar_one_or_none()

            if widget:
                widget.order_index = new_order
                widget.updated_at = datetime.now()

        await db.commit()

        return ApiResponse(
            success=True,
            message="批量排序更新成功"
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return ApiResponse(success=False, error=f"批量排序失败: {str(e)}")


@router.get("/render/{widget_id}")
async def render_widget(widget_id: int, db: AsyncSession = Depends(get_async_db)):
    """渲染小部件为HTML"""
    try:
        from shared.models.widget_instance import WidgetInstance
        from sqlalchemy import select
        import json

        # 从数据库获取 widget 实例
        stmt = select(WidgetInstance).where(WidgetInstance.id == widget_id)
        result = await db.execute(stmt)
        widget = result.scalar_one_or_none()

        if not widget:
            return ApiResponse(success=False, error="Widget 不存在")

        # 解析配置
        config = {}
        if widget.config:
            try:
                config = json.loads(widget.config) if isinstance(widget.config, str) else widget.config
            except:
                config = {}

        # 构建 widget 数据
        widget_data = {
            'id': str(widget.id),
            'type': widget.widget_type,
            'title': widget.title,
            'config': config
        }

        # 渲染 HTML
        html = widget_service.render_widget(widget_data)

        return ApiResponse(
            success=True,
            data={'html': html}
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return ApiResponse(success=False, error=f"渲染失败: {str(e)}")


# ==================== Widget 数据获取 API ====================

@router.get("/data/recent-posts")
async def get_recent_posts_data(
        count: int = Query(5, description="文章数量"),
        show_thumbnail: bool = Query(True, description="是否显示缩略图"),
        show_date: bool = Query(True, description="是否显示日期"),
        db: AsyncSession = Depends(get_async_db)
):
    """获取最新文章数据"""
    try:
        posts = await widget_service.get_recent_posts_data(
            db=db,
            count=count,
            show_thumbnail=show_thumbnail,
            show_date=show_date
        )

        return ApiResponse(
            success=True,
            data={'posts': posts}
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return ApiResponse(success=False, error=f"获取失败: {str(e)}")


@router.get("/data/recent-comments")
async def get_recent_comments_data(
        count: int = Query(5, description="评论数量"),
        show_avatar: bool = Query(True, description="是否显示头像"),
        db: AsyncSession = Depends(get_async_db)
):
    """获取最新评论数据"""
    try:
        comments = await widget_service.get_recent_comments_data(
            db=db,
            count=count,
            show_avatar=show_avatar
        )

        return ApiResponse(
            success=True,
            data={'comments': comments}
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return ApiResponse(success=False, error=f"获取失败: {str(e)}")


@router.get("/data/tags-cloud")
async def get_tags_cloud_data(
        count: int = Query(20, description="标签数量"),
        display_type: str = Query('cloud', description="显示类型 (cloud 或 list)"),
        db: AsyncSession = Depends(get_async_db)
):
    """获取标签云数据"""
    try:
        tags = await widget_service.get_tags_cloud_data(
            db=db,
            count=count,
            display_type=display_type
        )

        return ApiResponse(
            success=True,
            data={'tags': tags}
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return ApiResponse(success=False, error=f"获取失败: {str(e)}")


@router.get("/data/categories")
async def get_categories_data(
        show_count: bool = Query(True, description="是否显示文章数"),
        hierarchical: bool = Query(True, description="是否层级显示"),
        db: AsyncSession = Depends(get_async_db)
):
    """获取分类目录数据"""
    try:
        categories = await widget_service.get_categories_data(
            db=db,
            show_count=show_count,
            hierarchical=hierarchical
        )

        return ApiResponse(
            success=True,
            data={'categories': categories}
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return ApiResponse(success=False, error=f"获取失败: {str(e)}")


@router.get("/data/archives")
async def get_archives_data(
        archive_type: str = Query('monthly', description="归档类型 (monthly 或 yearly)"),
        show_count: bool = Query(True, description="是否显示文章数"),
        db: AsyncSession = Depends(get_async_db)
):
    """获取文章归档数据"""
    try:
        archives = await widget_service.get_archives_data(
            db=db,
            archive_type=archive_type,
            show_count=show_count
        )

        return ApiResponse(
            success=True,
            data={'archives': archives}
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return ApiResponse(success=False, error=f"获取失败: {str(e)}")


@router.get("/data/popular-posts")
async def get_popular_posts_data(
        count: int = Query(5, description="文章数量"),
        period: str = Query('week', description="时间周期 (day, week, month, all)"),
        db: AsyncSession = Depends(get_async_db)
):
    """获取热门文章数据"""
    try:
        posts = await widget_service.get_popular_posts_data(
            db=db,
            count=count,
            period=period
        )

        return ApiResponse(
            success=True,
            data={'posts': posts}
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return ApiResponse(success=False, error=f"获取失败: {str(e)}")


@router.get("/data/menu")
async def get_menu_data(
        slug: str = Query('main-menu', description="菜单slug"),
        db: AsyncSession = Depends(get_async_db)
):
    """获取菜单数据"""
    try:
        from shared.models.menu import Menu, MenuItem
        from sqlalchemy import select

        # 查询菜单
        menu_stmt = select(Menu).where(Menu.slug == slug)
        menu_result = await db.execute(menu_stmt)
        menu = menu_result.scalar_one_or_none()

        if not menu:
            return ApiResponse(
                success=False,
                error=f"菜单不存在: {slug}"
            )

        # 查询菜单项（包括层级关系）
        items_stmt = (
            select(MenuItem)
            .where(MenuItem.menu_id == menu.id)
            .where(MenuItem.is_active == True)
            .order_by(MenuItem.order_index)
        )
        items_result = await db.execute(items_stmt)
        menu_items = items_result.scalars().all()

        # 构建树形结构
        def build_tree(items, parent_id=None):
            tree = []
            for item in items:
                if item.parent_id == parent_id:
                    node = {
                        'id': item.id,
                        'title': item.title,
                        'url': item.url,
                        'target': item.target,
                    }
                    children = build_tree(items, item.id)
                    if children:
                        node['children'] = children
                    tree.append(node)
            return tree

        items_data = build_tree(menu_items)

        return ApiResponse(
            success=True,
            data={'menu': menu.name, 'items': items_data}
        )
    except ImportError:
        # 如果 Menu 模型不存在，返回空数据
        return ApiResponse(
            success=True,
            data={'menu': slug, 'items': []}
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return ApiResponse(success=False, error=f"获取失败: {str(e)}")
