"""
菜单管理API端点
提供菜单和菜单项的完整管理功能
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from shared.services.content_management.menu_service import (
    get_menus_list,
    get_menu_with_items,
    create_menu,
    update_menu,
    delete_menu,
    add_menu_item,
    update_menu_item,
    delete_menu_item,
    reorder_menu_items,
    get_available_pages_for_menu,
    get_available_categories_for_menu
)
from src.api.v1.core.responses import ApiResponse
from src.auth import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db

router = APIRouter(tags=["menus"])


@router.get("")
async def list_menus(
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取所有菜单列表
    """
    try:
        menus = await get_menus_list(db=db)

        return ApiResponse(
            success=True,
            data={"menus": menus}
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/{menu_id}")
async def get_menu_detail(
        menu_id: int,
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取菜单详情（包含菜单项树）
    
    Args:
        menu_id: 菜单ID
    """
    try:
        menu = await get_menu_with_items(db=db, menu_id=menu_id)

        if not menu:
            return ApiResponse(
                success=False,
                error="菜单不存在"
            )

        return ApiResponse(
            success=True,
            data=menu
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("")
async def create_new_menu(
        request: Request,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    创建新菜单
    
    Body参数:
        name: 菜单名称（必填）
        slug: 菜单slug（必填）
        description: 菜单描述（可选）
    """
    try:
        form_data = await request.form()

        name = form_data.get('name', '').strip()
        slug = form_data.get('slug', '').strip()
        description = form_data.get('description', None)

        if not name or not slug:
            return ApiResponse(
                success=False,
                error="菜单名称和slug不能为空"
            )

        menu = await create_menu(
            db=db,
            name=name,
            slug=slug,
            description=description
        )

        if not menu:
            return ApiResponse(
                success=False,
                error="创建菜单失败"
            )

        return ApiResponse(
            success=True,
            data={
                "message": "菜单创建成功",
                "menu_id": menu.id
            }
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.put("/{menu_id}")
async def update_existing_menu(
        menu_id: int,
        request: Request,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    更新菜单
    
    Args:
        menu_id: 菜单ID
    
    Body参数:
        name: 菜单名称（可选）
        slug: 菜单slug（可选）
        description: 菜单描述（可选）
        is_active: 是否激活（可选）
    """
    try:
        form_data = await request.form()

        update_data = {}

        if 'name' in form_data:
            update_data['name'] = form_data.get('name')
        if 'slug' in form_data:
            update_data['slug'] = form_data.get('slug')
        if 'description' in form_data:
            update_data['description'] = form_data.get('description')
        if 'is_active' in form_data:
            update_data['is_active'] = form_data.get('is_active').lower() == 'true'

        if not update_data:
            return ApiResponse(
                success=False,
                error="没有提供要更新的字段"
            )

        success = await update_menu(db=db, menu_id=menu_id, **update_data)

        if not success:
            return ApiResponse(
                success=False,
                error="更新菜单失败，菜单可能不存在"
            )

        return ApiResponse(
            success=True,
            data={"message": "菜单更新成功"}
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.delete("/{menu_id}")
async def delete_existing_menu(
        menu_id: int,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    删除菜单（级联删除所有菜单项）
    
    Args:
        menu_id: 菜单ID
    """
    try:
        success = await delete_menu(db=db, menu_id=menu_id)

        if not success:
            return ApiResponse(
                success=False,
                error="删除菜单失败，菜单可能不存在"
            )

        return ApiResponse(
            success=True,
            data={"message": "菜单删除成功"}
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/{menu_id}/items")
async def add_item_to_menu(
        menu_id: int,
        request: Request,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    添加菜单项到菜单
    
    Args:
        menu_id: 菜单ID
    
    Body参数:
        title: 菜单项标题（必填）
        url: 链接URL（必填）
        parent_id: 父菜单项ID（可选，用于子菜单）
        target: 打开方式（_self或_blank，默认_self）
        order_index: 排序索引（默认0）
    """
    try:
        form_data = await request.form()

        title = form_data.get('title', '').strip()
        url = form_data.get('url', '').strip()

        if not title or not url:
            return ApiResponse(
                success=False,
                error="标题和URL不能为空"
            )

        try:
            parent_id = int(form_data.get('parent_id')) if form_data.get('parent_id') else None
        except ValueError:
            parent_id = None

        target = form_data.get('target', '_self')

        try:
            order_index = int(form_data.get('order_index', 0))
        except ValueError:
            order_index = 0

        item = await add_menu_item(
            db=db,
            menu_id=menu_id,
            title=title,
            url=url,
            parent_id=parent_id,
            target=target,
            order_index=order_index
        )

        if not item:
            return ApiResponse(
                success=False,
                error="添加菜单项失败"
            )

        return ApiResponse(
            success=True,
            data={
                "message": "菜单项添加成功",
                "item_id": item.id
            }
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.put("/items/{item_id}")
async def update_menu_item_detail(
        item_id: int,
        request: Request,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    更新菜单项
    
    Args:
        item_id: 菜单项ID
    
    Body参数:
        title: 菜单项标题（可选）
        url: 链接URL（可选）
        parent_id: 父菜单项ID（可选）
        target: 打开方式（可选）
        order_index: 排序索引（可选）
        is_active: 是否激活（可选）
    """
    try:
        form_data = await request.form()

        update_data = {}

        if 'title' in form_data:
            update_data['title'] = form_data.get('title')
        if 'url' in form_data:
            update_data['url'] = form_data.get('url')
        if 'parent_id' in form_data:
            try:
                update_data['parent_id'] = int(form_data.get('parent_id')) if form_data.get('parent_id') else None
            except ValueError:
                update_data['parent_id'] = None
        if 'target' in form_data:
            update_data['target'] = form_data.get('target')
        if 'order_index' in form_data:
            try:
                update_data['order_index'] = int(form_data.get('order_index', 0))
            except ValueError:
                pass
        if 'is_active' in form_data:
            update_data['is_active'] = form_data.get('is_active').lower() == 'true'

        if not update_data:
            return ApiResponse(
                success=False,
                error="没有提供要更新的字段"
            )

        success = await update_menu_item(db=db, item_id=item_id, **update_data)

        if not success:
            return ApiResponse(
                success=False,
                error="更新菜单项失败，菜单项可能不存在"
            )

        return ApiResponse(
            success=True,
            data={"message": "菜单项更新成功"}
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.delete("/items/{item_id}")
async def delete_menu_item_detail(
        item_id: int,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    删除菜单项（递归删除所有子项）
    
    Args:
        item_id: 菜单项ID
    """
    try:
        success = await delete_menu_item(db=db, item_id=item_id)

        if not success:
            return ApiResponse(
                success=False,
                error="删除菜单项失败，菜单项可能不存在"
            )

        return ApiResponse(
            success=True,
            data={"message": "菜单项删除成功"}
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/{menu_id}/reorder")
async def reorder_menu(
        menu_id: int,
        request: Request,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    批量重新排序菜单项（用于拖拽后的保存）
    
    Args:
        menu_id: 菜单ID
    
    Body参数:
        items: JSON数组，包含排序后的菜单项结构
    """
    try:
        import json

        body = await request.json()
        items_order = body.get('items', [])

        if not items_order:
            return ApiResponse(
                success=False,
                error="没有提供菜单项数据"
            )

        success = await reorder_menu_items(
            db=db,
            menu_id=menu_id,
            items_order=items_order
        )

        if not success:
            return ApiResponse(
                success=False,
                error="重新排序失败"
            )

        return ApiResponse(
            success=True,
            data={"message": "菜单项排序已更新"}
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/available/pages")
async def get_available_pages(
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取可用于添加到菜单的页面列表
    """
    try:
        pages = await get_available_pages_for_menu(db=db)

        return ApiResponse(
            success=True,
            data={"pages": pages}
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/available/categories")
async def get_available_categories(
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取可用于添加到菜单的分类列表
    """
    try:
        categories = await get_available_categories_for_menu(db=db)

        return ApiResponse(
            success=True,
            data={"categories": categories}
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))
