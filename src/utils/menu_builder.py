"""
菜单构建工具，用于根据菜单slug生成菜单树结构
"""
from typing import List, Dict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from shared.models import Menus, MenuItems, SystemSettings


# from src.models.system import Menus, MenuItems, SystemSettings


def get_menu_tree_by_slug(db: Session, menu_slug: str) -> List[Dict]:
    """
    根据菜单slug获取菜单树结构

    Args:
        db: 数据库会话
        menu_slug: 菜单标识符

    Returns:
        包含菜单项树结构的列表
    """
    try:
        # 首先获取菜单ID
        from sqlalchemy import select
        menu_query = select(Menus).where(Menus.slug == menu_slug, Menus.is_active == True)
        menu_result = db.execute(menu_query)
        menu = menu_result.scalar_one_or_none()
        if not menu:
            # 如果找不到指定的菜单，返回默认菜单
            return get_default_menu()

        # 获取该菜单下的所有菜单项，按order_index排序
        from sqlalchemy import select
        menu_items_query = select(MenuItems).where(
            MenuItems.menu_id == menu.id,
            MenuItems.is_active == True
        ).order_by(MenuItems.order_index)
        menu_items_result = db.execute(menu_items_query)
        menu_items = menu_items_result.scalars().all()

        # 构建菜单树
        menu_tree = []
        item_dict = {}

        # 首先创建所有菜单项的字典映射
        for item in menu_items:
            item_dict[item.id] = {
                'id': item.id,
                'title': item.title,
                'url': item.url,
                'target': item.target,
                'children': [],
                'parent_id': item.parent_id
            }

        # 构建树结构
        for item_id, item_data in item_dict.items():
            parent_id = item_data['parent_id']
            if parent_id is None:
                # 没有父级，这是根节点
                menu_tree.append(item_data)
            else:
                # 有父级，将其添加到父级的children中
                if parent_id in item_dict:
                    item_dict[parent_id]['children'].append(item_data)

        # 按照order_index对根菜单进行排序，对每个节点的子菜单也进行排序
        menu_tree.sort(key=lambda x: get_original_menu_item(menu_items, x['id']).order_index)
        sort_children_recursive(menu_tree, menu_items)

        return menu_tree
    except Exception as e:
        # 如果数据库查询失败，返回默认菜单
        print(f"获取菜单失败: {e}")
        return get_default_menu()


def sort_children_recursive(menu_tree: List[Dict], all_menu_items: List[MenuItems]):
    """递归地对菜单树的所有层级进行排序"""
    for item in menu_tree:
        # 对当前项目的子项进行排序
        if item['children']:
            item['children'].sort(key=lambda x: get_original_menu_item(all_menu_items, x['id']).order_index)
            # 递归处理子项
            sort_children_recursive(item['children'], all_menu_items)


def get_original_menu_item(all_menu_items: List[MenuItems], item_id: int) -> MenuItems:
    """从原始菜单项列表中获取特定ID的菜单项"""
    for item in all_menu_items:
        if item.id == item_id:
            return item
    return None


def get_default_menu() -> List[Dict]:
    """
    返回默认菜单结构

    Returns:
        默认菜单结构
    """
    return [
        {
            'id': 1,
            'title': '首页',
            'url': '/',
            'target': '_self',
            'children': []
        },
        {
            'id': 2,
            'title': '分类',
            'url': '/categories',
            'target': '_self',
            'children': []
        },
        {
            'id': 3,
            'title': '标签',
            'url': '/tags',
            'target': '_self',
            'children': []
        },
        {
            'id': 4,
            'title': '关于',
            'url': '/about',
            'target': '_self',
            'children': []
        }
    ]


def get_all_menus_with_items(db: Session) -> Dict:
    """
    获取所有菜单及其菜单项的结构

    Args:
        db: 数据库会话

    Returns:
        包含所有菜单和其菜单项的字典
    """
    try:
        # 获取所有启用的菜单
        from sqlalchemy import select
        menus_query = select(Menus).where(Menus.is_active == True).order_by(Menus.id)
        menus_result = db.execute(menus_query)
        menus = menus_result.scalars().all()

        result = {}
        for menu in menus:
            # 获取该菜单下的所有菜单项
            from sqlalchemy import select
            menu_items_query = select(MenuItems).where(
                MenuItems.menu_id == menu.id,
                MenuItems.is_active == True
            ).order_by(MenuItems.order_index)
            menu_items_result = db.execute(menu_items_query)
            menu_items = menu_items_result.scalars().all()

            # 构建菜单树
            menu_tree = []
            item_dict = {}

            # 创建所有菜单项的字典映射
            for item in menu_items:
                item_dict[item.id] = {
                    'id': item.id,
                    'title': item.title,
                    'url': item.url,
                    'target': item.target,
                    'order_index': item.order_index,
                    'children': [],
                    'parent_id': item.parent_id
                }

            # 构建树结构
            for item_id, item_data in item_dict.items():
                parent_id = item_data['parent_id']
                if parent_id is None:
                    # 没有父级，这是根节点
                    menu_tree.append(item_data)
                else:
                    # 有父级，将其添加到父级的children中
                    if parent_id in item_dict:
                        item_dict[parent_id]['children'].append(item_data)

            # 排序
            menu_tree.sort(key=lambda x: x['order_index'])
            sort_children_recursive_simple(menu_tree)

            result[menu.id] = {
                'id': menu.id,
                'name': menu.name,
                'slug': menu.slug,
                'description': menu.description,
                'items': menu_tree
            }

        return result
    except Exception as e:
        # 如果数据库查询失败，返回空字典
        print(f"获取所有菜单失败: {e}")
        return {}


def sort_children_recursive_simple(menu_tree: List[Dict]):
    """简单的递归排序，用于get_all_menus_with_items"""
    for item in menu_tree:
        # 对当前项目的子项进行排序
        if 'children' in item and isinstance(item['children'], list):
            # 只对有效的字典对象进行排序
            valid_children = [child for child in item['children'] if isinstance(child, dict)]
            item['children'] = valid_children
            item['children'].sort(key=lambda x: x.get('order_index', 0))
            # 递归处理子项
            sort_children_recursive_simple(item['children'])


def get_menu_tree_by_system_config(db: Session) -> List[Dict]:
    """
    从系统配置中获取菜单slug并返回对应的菜单树结构

    Args:
        db: 数据库会话

    Returns:
        包含菜单项树结构的列表
    """
    try:
        # 从系统设置中获取菜单slug配置
        from sqlalchemy import select
        menu_setting_query = select(SystemSettings).where(SystemSettings.setting_key == 'menu_slug')
        menu_setting_result = db.execute(menu_setting_query)
        menu_setting = menu_setting_result.scalar_one_or_none()
        menu_slug = menu_setting.setting_value if menu_setting else 'default'

        # 获取菜单树
        return get_menu_tree_by_slug(db, menu_slug)
    except Exception as e:
        # 如果数据库查询失败，返回默认菜单
        print(f"获取系统配置菜单失败: {e}")
        return get_default_menu()


async def get_all_menus_with_items_async(db: AsyncSession) -> Dict:
    """
    异步获取所有菜单及其菜单项的结构

    Args:
        db: 异步数据库会话

    Returns:
        包含所有菜单和其菜单项的字典
    """
    try:
        # 获取所有启用的菜单 - 使用ORM查询方式确保获取对象
        from sqlalchemy import select
        menus_result = await db.execute(
            select(Menus).where(Menus.is_active == True).order_by(Menus.id)
        )
        menus = menus_result.scalars().all()

        result_dict = {}
        for menu in menus:
            # 获取该菜单下的所有菜单项
            menu_items_result = await db.execute(
                select(MenuItems).where(
                    MenuItems.menu_id == menu.id,
                    MenuItems.is_active == True
                ).order_by(MenuItems.order_index)
            )
            menu_items = menu_items_result.scalars().all()

            # 构建菜单树
            menu_tree = []
            item_dict = {}

            # 创建所有菜单项的字典映射
            for item in menu_items:
                item_dict[item.id] = {
                    'id': item.id,
                    'title': item.title,
                    'url': item.url,
                    'target': item.target,
                    'order_index': item.order_index,
                    'children': [],
                    'parent_id': item.parent_id
                }

            # 构建树结构 - 先收集所有根节点（无父节点的项目）
            root_items = []
            child_items = []  # 存储有待处理的孩子节点

            for item in menu_items:
                if item.parent_id is None:
                    root_items.append(item_dict[item.id])
                else:
                    # 将有父节点的项目保存起来稍后处理
                    child_items.append(item)

            # 添加根节点到菜单树
            menu_tree.extend(root_items)

            # 处理子节点，确保只添加到有效的字典对象
            for item in child_items:
                if item.parent_id in item_dict:
                    parent_item = item_dict[item.parent_id]
                    # 确保父项是字典且包含children键
                    if isinstance(parent_item, dict) and 'children' in parent_item:
                        # 确保要添加的子项也是字典
                        if item.id in item_dict and isinstance(item_dict[item.id], dict):
                            parent_item['children'].append(item_dict[item.id])

            # 排序
            menu_tree.sort(key=lambda x: x['order_index'])
            sort_children_recursive_simple(menu_tree)

            result_dict[menu.id] = {
                'id': menu.id,
                'name': menu.name,
                'slug': menu.slug,
                'description': menu.description,
                'items': menu_tree
            }

        return result_dict
    except Exception as e:
        # 如果数据库查询失败，返回空字典
        print(f"获取所有菜单失败: {e}")
        import traceback
        traceback.print_exc()  # 打印完整的堆栈跟踪
        return {}
