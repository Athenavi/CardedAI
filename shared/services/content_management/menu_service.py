"""
菜单管理服务
提供菜单和菜单项的完整管理功能，支持拖拽排序和层级结构
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.menu_items import MenuItems
from shared.models.menus import Menus


async def get_menus_list(db: AsyncSession) -> List[Dict[str, Any]]:
    """
    获取所有菜单列表
    
    Args:
        db: 数据库会话
        
    Returns:
        菜单列表
    """
    try:
        query = select(Menus).order_by(Menus.created_at.desc())
        result = await db.execute(query)
        menus = result.scalars().all()

        return [menu.to_dict() for menu in menus]

    except Exception as e:
        print(f"获取菜单列表失败: {e}")
        return []


async def get_menu_with_items(db: AsyncSession, menu_id: int) -> Optional[Dict[str, Any]]:
    """
    获取菜单及其所有菜单项（树形结构）
    
    Args:
        db: 数据库会话
        menu_id: 菜单ID
        
    Returns:
        包含菜单项树的菜单详情
    """
    try:
        # 获取菜单
        menu_query = select(Menus).where(Menus.id == menu_id)
        menu_result = await db.execute(menu_query)
        menu = menu_result.scalar_one_or_none()

        if not menu:
            return None

        # 获取所有菜单项
        items_query = (
            select(MenuItems)
            .where(MenuItems.menu_id == menu_id)
            .order_by(MenuItems.order_index.asc(), MenuItems.created_at.asc())
        )
        items_result = await db.execute(items_query)
        all_items = items_result.scalars().all()

        # 构建树形结构
        items_dict = {item.id: {**item.to_dict(), "children": []} for item in all_items}
        root_items = []

        for item_data in items_dict.values():
            parent_id = item_data["parent_id"]
            if parent_id and parent_id in items_dict:
                items_dict[parent_id]["children"].append(item_data)
            else:
                root_items.append(item_data)

        return {
            **menu.to_dict(),
            "items": root_items
        }

    except Exception as e:
        print(f"获取菜单详情失败: {e}")
        return None


async def create_menu(
        db: AsyncSession,
        name: str,
        slug: str,
        description: Optional[str] = None
) -> Optional[Menus]:
    """
    创建新菜单
    
    Args:
        db: 数据库会话
        name: 菜单名称
        slug: 菜单slug
        description: 菜单描述
        
    Returns:
        创建的菜单对象
    """
    try:
        now = datetime.now(timezone.utc)

        menu = Menus(
            name=name,
            slug=slug,
            description=description,
            is_active=True,
            created_at=now,
            updated_at=now
        )

        db.add(menu)
        await db.commit()
        await db.refresh(menu)

        return menu

    except Exception as e:
        await db.rollback()
        print(f"创建菜单失败: {e}")
        return None


async def update_menu(
        db: AsyncSession,
        menu_id: int,
        **kwargs
) -> bool:
    """
    更新菜单
    
    Args:
        db: 数据库会话
        menu_id: 菜单ID
        **kwargs: 要更新的字段
        
    Returns:
        是否成功
    """
    try:
        query = select(Menus).where(Menus.id == menu_id)
        result = await db.execute(query)
        menu = result.scalar_one_or_none()

        if not menu:
            return False

        for key, value in kwargs.items():
            if hasattr(menu, key):
                setattr(menu, key, value)

        menu.updated_at = datetime.now(timezone.utc)
        await db.commit()

        return True

    except Exception as e:
        await db.rollback()
        print(f"更新菜单失败: {e}")
        return False


async def delete_menu(db: AsyncSession, menu_id: int) -> bool:
    """
    删除菜单（级联删除所有菜单项）
    
    Args:
        db: 数据库会话
        menu_id: 菜单ID
        
    Returns:
        是否成功
    """
    try:
        # 先删除所有菜单项
        items_query = select(MenuItems).where(MenuItems.menu_id == menu_id)
        items_result = await db.execute(items_query)
        items = items_result.scalars().all()

        for item in items:
            await db.delete(item)

        # 再删除菜单
        menu_query = select(Menus).where(Menus.id == menu_id)
        menu_result = await db.execute(menu_query)
        menu = menu_result.scalar_one_or_none()

        if not menu:
            return False

        await db.delete(menu)
        await db.commit()

        return True

    except Exception as e:
        await db.rollback()
        print(f"删除菜单失败: {e}")
        return False


async def add_menu_item(
        db: AsyncSession,
        menu_id: int,
        title: str,
        url: str,
        parent_id: Optional[int] = None,
        target: str = "_self",
        order_index: int = 0
) -> Optional[MenuItems]:
    """
    添加菜单项
    
    Args:
        db: 数据库会话
        menu_id: 菜单ID
        title: 菜单项标题
        url: 链接URL
        parent_id: 父菜单项ID（用于子菜单）
        target: 打开方式（_self, _blank等）
        order_index: 排序索引
        
    Returns:
        创建的菜单项对象
    """
    try:
        now = datetime.now(timezone.utc)

        item = MenuItems(
            menu_id=menu_id,
            parent_id=parent_id,
            title=title,
            url=url,
            target=target,
            order_index=order_index,
            is_active=True,
            created_at=now
        )

        db.add(item)
        await db.commit()
        await db.refresh(item)

        return item

    except Exception as e:
        await db.rollback()
        print(f"添加菜单项失败: {e}")
        return None


async def update_menu_item(
        db: AsyncSession,
        item_id: int,
        **kwargs
) -> bool:
    """
    更新菜单项
    
    Args:
        db: 数据库会话
        item_id: 菜单项ID
        **kwargs: 要更新的字段
        
    Returns:
        是否成功
    """
    try:
        query = select(MenuItems).where(MenuItems.id == item_id)
        result = await db.execute(query)
        item = result.scalar_one_or_none()

        if not item:
            return False

        for key, value in kwargs.items():
            if hasattr(item, key):
                setattr(item, key, value)

        await db.commit()

        return True

    except Exception as e:
        await db.rollback()
        print(f"更新菜单项失败: {e}")
        return False


async def delete_menu_item(db: AsyncSession, item_id: int) -> bool:
    """
    删除菜单项（递归删除所有子项）
    
    Args:
        db: 数据库会话
        item_id: 菜单项ID
        
    Returns:
        是否成功
    """
    try:
        # 递归删除所有子项
        children_query = select(MenuItems).where(MenuItems.parent_id == item_id)
        children_result = await db.execute(children_query)
        children = children_result.scalars().all()

        for child in children:
            await delete_menu_item(db, child.id)

        # 删除当前项
        item_query = select(MenuItems).where(MenuItems.id == item_id)
        item_result = await db.execute(item_query)
        item = item_result.scalar_one_or_none()

        if not item:
            return False

        await db.delete(item)
        await db.commit()

        return True

    except Exception as e:
        await db.rollback()
        print(f"删除菜单项失败: {e}")
        return False


async def reorder_menu_items(
        db: AsyncSession,
        menu_id: int,
        items_order: List[Dict[str, Any]]
) -> bool:
    """
    批量重新排序菜单项（支持拖拽后的批量更新）
    
    Args:
        db: 数据库会话
        menu_id: 菜单ID
        items_order: 排序后的菜单项列表，每项包含id和parent_id
        
    Returns:
        是否成功
    """
    try:
        async def update_item_order(item_data: Dict[str, Any], order_index: int, parent_id: Optional[int] = None):
            """递归更新菜单项顺序"""
            item_id = item_data.get('id')
            if not item_id:
                return

            query = select(MenuItems).where(MenuItems.id == item_id)
            result = await db.execute(query)
            item = result.scalar_one_or_none()

            if item:
                item.order_index = order_index
                item.parent_id = parent_id

            # 处理子项
            children = item_data.get('children', [])
            for idx, child in enumerate(children):
                await update_item_order(child, idx, item_id)

        # 更新所有根级菜单项
        for idx, item_data in enumerate(items_order):
            await update_item_order(item_data, idx, None)

        await db.commit()

        return True

    except Exception as e:
        await db.rollback()
        print(f"重新排序菜单项失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def get_available_pages_for_menu(db: AsyncSession) -> List[Dict[str, Any]]:
    """
    获取可用于添加到菜单的页面列表
    
    Args:
        db: 数据库会话
        
    Returns:
        页面列表
    """
    try:
        from shared.models.pages import Pages

        query = (
            select(Pages)
            .where(Pages.status == 1)  # 只返回已发布的页面
            .order_by(Pages.title.asc())
        )
        result = await db.execute(query)
        pages = result.scalars().all()

        return [
            {
                "id": page.id,
                "title": page.title,
                "url": f"/page/{page.slug}",
                "type": "page"
            }
            for page in pages
        ]

    except Exception as e:
        print(f"获取可用页面失败: {e}")
        return []


async def get_available_categories_for_menu(db: AsyncSession) -> List[Dict[str, Any]]:
    """
    获取可用于添加到菜单的分类列表
    
    Args:
        db: 数据库会话
        
    Returns:
        分类列表
    """
    try:
        from shared.models.category import Category

        query = (
            select(Category)
            .where(Category.is_visible == True)
            .order_by(Category.name.asc())
        )
        result = await db.execute(query)
        categories = result.scalars().all()

        return [
            {
                "id": cat.id,
                "title": cat.name,
                "url": f"/category/{cat.slug}",
                "type": "category"
            }
            for cat in categories
        ]

    except Exception as e:
        print(f"获取可用分类失败: {e}")
        return []
