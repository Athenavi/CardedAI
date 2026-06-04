import json
from typing import Dict, Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import SystemSettings, MenuItems, Pages, Menus
from src.api.v1.core.responses import ApiResponse
from src.auth import jwt_required_page_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db

router = APIRouter(tags=["admin-settings"])


async def get_system_settings_dict(db: AsyncSession) -> Dict[str, str]:
    """
    获取系统设置字典
    """
    from sqlalchemy import select

    settings_query = select(SystemSettings)
    settings_result = await db.execute(settings_query)  # 使用 await，因为 db.execute 在异步函数中返回结果
    settings = settings_result.scalars().all()
    settings_dict = {}
    for setting in settings:
        # 对于简单的字符串、数字值，直接返回；对于JSON序列化的值，进行解析
        # 为了兼容性，先尝试JSON解析，如果失败则返回原值
        try:
            # 尝试解析JSON格式的值
            parsed_value = json.loads(setting.setting_value)
            # 如果解析出的值是字符串但包含引号，说明是被序列化的字符串
            if isinstance(parsed_value, str) and setting.setting_value.startswith('"') and setting.setting_value.endswith('"'):
                # 这种情况下，原始存储的可能是一个字符串，但被JSON序列化了
                # 返回解析后的值（即去除外层引号的原始字符串）
                settings_dict[setting.setting_key] = parsed_value
            else:
                settings_dict[setting.setting_key] = parsed_value
        except (json.JSONDecodeError, TypeError):
            # 如果不是JSON格式，则直接使用原始值
            settings_dict[setting.setting_key] = setting.setting_value
    return settings_dict


async def update_system_setting(key: str, value: Any, db: AsyncSession) -> None:
    """
    更新或创建系统设置
    """
    # 区分简单值和复杂对象
    # 简单值（字符串、数字、布尔值）直接存储，复杂对象（列表、字典）进行JSON序列化
    if isinstance(value, (str, int, float)):
        # 简单数据类型直接存储
        serialized_value = str(value)
    elif isinstance(value, bool):
        # 布尔值也进行JSON序列化以确保类型信息保留
        serialized_value = json.dumps(value, ensure_ascii=False)
    elif value is None:
        # None值也要进行序列化
        serialized_value = json.dumps(value, ensure_ascii=False)
    else:
        # 复杂类型（列表、字典等）进行JSON序列化
        try:
            serialized_value = json.dumps(value, ensure_ascii=False)
        except (TypeError, ValueError):
            serialized_value = str(value)

    # 检查设置是否已存在 - 使用异步SQLAlchemy语法
    from sqlalchemy import select
    existing_setting_query = select(SystemSettings).where(SystemSettings.setting_key == key)
    existing_setting_result = await db.execute(existing_setting_query)  # 使用 await，因为 db.execute 在异步函数中返回结果
    existing_setting = existing_setting_result.scalar_one_or_none()

    if existing_setting:
        from datetime import datetime
        existing_setting.setting_value = serialized_value
        existing_setting.updated_at = datetime.now()
        await db.commit()
    else:
        from datetime import datetime
        new_setting = SystemSettings(
            setting_key=key,
            setting_value=serialized_value,
            description=get_setting_description(key),
            updated_at=datetime.now()
        )
        db.add(new_setting)
        await db.commit()


def get_setting_description(key: str) -> str:
    """
    获取设置键的描述
    """
    descriptions = {
        'site_title': '站点标题',
        'site_img': '站点图像URL',
        'site_description': '站点描述',
        'site_domain': '站点域名',
        'site_beian': '备案号',
        'site_keywords': '站点关键词',
        'user_registration': '允许用户注册',
        'menu_slug': '当前使用的菜单标识',
        'home_hero_title': '首页英雄区域标题',
        'home_hero_subtitle': '首页英雄区域副标题',
        'home_hero_cta_text': '首页英雄区域CTA按钮文本',
        'home_hero_cta_link': '首页英雄区域CTA按钮链接',
        'home_cta_target': '首页CTA按钮跳转方式',
        'home_featured_count': '首页特色文章数量',
        'home_hero_background_image': '首页英雄区域背景图片',
        'home_featured_title': '首页特色文章区域标题',
        'home_featured_empty_title': '首页特色文章区域空状态标题',
        'home_featured_empty_subtitle': '首页特色文章区域空状态副标题',
        'home_main_title': '首页主要内容区域标题',
        'home_main_filter_buttons': '首页主要内容区域过滤按钮',
        'home_main_empty_title': '首页主要内容区域空状态标题',
        'home_main_empty_subtitle': '首页主要内容区域空状态副标题',
        'home_newsletter_title': '首页新闻通讯区域标题',
        'home_newsletter_subtitle': '首页新闻通讯区域副标题',
        'home_newsletter_placeholder': '首页新闻通讯区域输入框占位符',
        'home_newsletter_button_text': '首页新闻通讯区域按钮文本',
        'home_no_category_msg': '首页无分类消息',
        'home_unknown_author_msg': '首页未知作者消息',
        'home_no_summary_msg': '首页无摘要消息',
    }
    return descriptions.get(key, f'{key} 设置')


# def get_setting_category is no longer needed — model doesn't have a category column


@router.get("/")
async def get_settings(
        request: Request,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取所有系统设置
    """
    try:
        # 检查用户权限 - 只有超级用户才能访问
        from starlette.responses import RedirectResponse
        if isinstance(current_user, RedirectResponse):
            # 如果用户未认证，返回重定向响应
            return current_user
        if not current_user.is_superuser:
            from fastapi import HTTPException
            from fastapi import status
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user doesn't have enough privileges"
            )

        # 获取系统设置 - 使用异步版本
        settings_dict = await get_system_settings_dict(db)

        # 获取菜单
        ##from src.models.system import Menus
        from sqlalchemy import select
        menus_query = select(Menus).order_by(Menus.created_at.desc())
        menus_result = await db.execute(menus_query)
        menus = menus_result.scalars().all()

        # 获取所有菜单项并按菜单分组
        ##from src.models.system import MenuItems
        menu_items = {}
        for menu in menus:
            items_query = select(MenuItems).where(MenuItems.menu_id == menu.id).order_by(MenuItems.order_index)
            items_result = await db.execute(items_query)
            items = items_result.scalars().all()
            menu_items[menu.id] = items

        # 获取页面
        # from src.models.system import Pages
        pages_query = select(Pages).order_by(Pages.created_at.desc())
        pages_result = await db.execute(pages_query)
        pages = pages_result.scalars().all()

        return ApiResponse(
            success=True,
            data={
                "settings": settings_dict,
                "menus": [{
                    "id": menu.id,
                    "name": menu.name,
                    "slug": menu.slug,
                    "description": menu.description,
                    "is_active": menu.is_active,
                    "created_at": menu.created_at.isoformat() if menu.created_at else None,
                    "updated_at": menu.updated_at.isoformat() if menu.updated_at else None
                } for menu in menus],
                "menu_items": {
                    str(menu_id): [{
                        "id": item.id,
                        "title": item.title,
                        "url": item.url,
                        "target": item.target,
                        "parent_id": item.parent_id,
                        "order_index": item.order_index,
                        "created_at": item.created_at.isoformat() if item.created_at else None,
                    } for item in items] for menu_id, items in menu_items.items()
                },
                "pages": [{
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
                    "created_at": page.created_at.isoformat() if page.created_at else None,
                } for page in pages]
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in get_settings: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.post("/")
async def update_settings(
        request: Request,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    更新系统设置
    """
    try:
        # 检查用户权限 - 只有超级用户才能访问
        from starlette.responses import RedirectResponse
        if isinstance(current_user, RedirectResponse):
            # 如果用户未认证，返回重定向响应
            return current_user
        if not current_user.is_superuser:
            from fastapi import HTTPException
            from fastapi import status
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user doesn't have enough privileges"
            )

        data = await request.json()
        settings = data.get('settings', {})
        action = data.get('action', 'update_settings')

        if action == 'update_settings':
            for key, value in settings.items():
                await update_system_setting(key, value, db)

            return ApiResponse(
                success=True,
                data={"message": "设置更新成功"}
            )
        else:
            return ApiResponse(success=False, error="Invalid action", data=None)

    except Exception as e:
        import traceback
        print(f"Error in update_settings: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e), data=None)


@router.post("/menus")
async def create_menu(
        request: Request,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    创建菜单
    """
    try:
        # 检查用户权限 - 只有超级用户才能访问
        from starlette.responses import RedirectResponse
        if isinstance(current_user, RedirectResponse):
            # 如果用户未认证，返回重定向响应
            return current_user
        if not current_user.is_superuser:
            from fastapi import HTTPException
            from fastapi import status
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user doesn't have enough privileges"
            )

        data = await request.json()
        name = data.get('name')
        slug = data.get('slug')
        description = data.get('description', '')

        if not name or not slug:
            return ApiResponse(success=False, error='菜单名称和标识不能为空', data=None)

        # from src.models.system import Menus
        from datetime import datetime

        from sqlalchemy import select
        existing_menu_query = select(Menus).where(Menus.slug == slug)
        existing_menu_result = await db.execute(existing_menu_query)
        existing_menu = existing_menu_result.scalar_one_or_none()
        if existing_menu:
            return ApiResponse(success=False, error='菜单标识已存在', data=None)

        menu = Menus(
            name=name,
            slug=slug,
            description=description,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.add(menu)
        await db.commit()
        await db.refresh(menu)

        return ApiResponse(
            success=True,
            data={
                'id': menu.id,
                'name': menu.name,
                'slug': menu.slug,
                'description': menu.description,
                'is_active': menu.is_active,
                'created_at': menu.created_at.isoformat() if menu.created_at else None,
                'updated_at': menu.updated_at.isoformat() if menu.updated_at else None
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in create_menu: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.put("/menus/{menu_id}")
async def update_menu(
        menu_id: int,
        request: Request,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    更新菜单
    """
    try:
        # 检查用户权限 - 只有超级用户才能访问
        from starlette.responses import RedirectResponse
        if isinstance(current_user, RedirectResponse):
            # 如果用户未认证，返回重定向响应
            return current_user
        if not current_user.is_superuser:
            from fastapi import HTTPException
            from fastapi import status
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user doesn't have enough privileges"
            )

        data = await request.json()
        name = data.get('name')
        description = data.get('description', '')
        is_active = data.get('is_active', False)

        # from src.models.system import Menus
        from datetime import datetime
        from sqlalchemy import select

        menu_query = select(Menus).where(Menus.id == menu_id)
        menu_result = await db.execute(menu_query)
        menu = menu_result.scalar_one_or_none()
        if not menu:
            return ApiResponse(success=False, error='菜单不存在', data=None)

        menu.name = name
        menu.description = description
        menu.is_active = bool(is_active)
        menu.updated_at = datetime.now()

        await db.commit()
        await db.refresh(menu)

        return ApiResponse(
            success=True,
            data={
                'id': menu.id,
                'name': menu.name,
                'slug': menu.slug,
                'description': menu.description,
                'is_active': menu.is_active,
                'created_at': menu.created_at.isoformat() if menu.created_at else None,
                'updated_at': menu.updated_at.isoformat() if menu.updated_at else None
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in update_menu: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.delete("/menus/{menu_id}")
async def delete_menu(
        menu_id: int,
        request: Request,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    删除菜单
    """
    try:
        # 检查用户权限 - 只有超级用户才能访问
        from starlette.responses import RedirectResponse
        if isinstance(current_user, RedirectResponse):
            # 如果用户未认证，返回重定向响应
            return current_user
        if not current_user.is_superuser:
            from fastapi import HTTPException
            from fastapi import status
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user doesn't have enough privileges"
            )

        # from src.models.system import Menus, MenuItems
        from sqlalchemy import select

        menu_query = select(Menus).where(Menus.id == menu_id)
        menu_result = await db.execute(menu_query)
        menu = menu_result.scalar_one_or_none()
        if not menu:
            return ApiResponse(success=False, error='菜单不存在', data=None)

        # 检查是否有菜单项关联到此菜单
        menu_items_query = select(MenuItems).where(MenuItems.menu_id == menu_id)
        menu_items_result = await db.execute(menu_items_query)
        menu_items = menu_items_result.scalars().all()
        if menu_items:
            return ApiResponse(success=False, error='菜单下还有菜单项，无法删除', data=None)

        await db.delete(menu)
        await db.commit()

        return ApiResponse(
            success=True,
            data={"message": "菜单删除成功"}
        )
    except Exception as e:
        import traceback
        print(f"Error in delete_menu: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.post("/pages")
async def create_page(
        request: Request,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    创建页面
    """
    try:
        # 检查用户权限 - 只有超级用户才能访问
        from starlette.responses import RedirectResponse
        if isinstance(current_user, RedirectResponse):
            # 如果用户未认证，返回重定向响应
            return current_user
        if not current_user.is_superuser:
            from fastapi import HTTPException
            from fastapi import status
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user doesn't have enough privileges"
            )

        data = await request.json()
        title = data.get('title')
        slug = data.get('slug')

        if not title or not slug:
            return ApiResponse(success=False, error='页面标题和别名不能为空', data=None)

        # from src.models.system import Pages
        from datetime import datetime

        from sqlalchemy import select
        existing_page_query = select(Pages).where(Pages.slug == slug)
        existing_page_result = await db.execute(existing_page_query)
        existing_page = existing_page_result.scalar_one_or_none()
        if existing_page:
            return ApiResponse(success=False, error='页面别名已存在', data=None)

        page = Pages(
            title=title,
            slug=slug,
            content=data.get('content', ''),
            excerpt=data.get('excerpt', ''),
            template=data.get('template', 'default'),
            status=data.get('status', 0),
            parent_id=data.get('parent_id'),
            order_index=data.get('order_index', 0),
            meta_title=data.get('meta_title'),
            meta_description=data.get('meta_description'),
            meta_keywords=data.get('meta_keywords'),
            author_id=current_user.id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.add(page)
        await db.commit()
        await db.refresh(page)

        return ApiResponse(
            success=True,
            data={
                'id': page.id,
                'title': page.title,
                'slug': page.slug,
                'content': page.content,
                'excerpt': page.excerpt,
                'template': page.template,
                'status': page.status,
                'parent_id': page.parent_id,
                'order_index': page.order_index,
                'meta_title': page.meta_title,
                'meta_description': page.meta_description,
                'meta_keywords': page.meta_keywords,
                'author': {
                    'username': current_user.username
                },
                'created_at': page.created_at.isoformat() if page.created_at else None,
                'updated_at': page.updated_at.isoformat() if page.updated_at else None
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in create_page: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.put("/pages/{page_id}")
async def update_page(
        page_id: int,
        request: Request,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    更新页面
    """
    try:
        # 检查用户权限 - 只有超级用户才能访问
        from starlette.responses import RedirectResponse
        if isinstance(current_user, RedirectResponse):
            # 如果用户未认证，返回重定向响应
            return current_user
        if not current_user.is_superuser:
            from fastapi import HTTPException
            from fastapi import status
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user doesn't have enough privileges"
            )

        data = await request.json()

        # from src.models.system import Pages
        from datetime import datetime
        from sqlalchemy import select

        page_query = select(Pages).where(Pages.id == page_id)
        page_result = await db.execute(page_query)
        page = page_result.scalar_one_or_none()
        if not page:
            return ApiResponse(success=False, error='页面不存在', data=None)

        page.title = data.get('title', page.title)
        page.slug = data.get('slug', page.slug)
        page.content = data.get('content', page.content)
        page.excerpt = data.get('excerpt', page.excerpt)
        page.template = data.get('template', page.template)
        page.status = data.get('status', page.status)
        page.parent_id = data.get('parent_id', page.parent_id)
        page.order_index = data.get('order_index', page.order_index)
        page.meta_title = data.get('meta_title', page.meta_title)
        page.meta_description = data.get('meta_description', page.meta_description)
        page.meta_keywords = data.get('meta_keywords', page.meta_keywords)
        page.updated_at = datetime.now()

        await db.commit()
        await db.refresh(page)

        return ApiResponse(
            success=True,
            data={
                'id': page.id,
                'title': page.title,
                'slug': page.slug,
                'content': page.content,
                'excerpt': page.excerpt,
                'template': page.template,
                'status': page.status,
                'parent_id': page.parent_id,
                'order_index': page.order_index,
                'meta_title': page.meta_title,
                'meta_description': page.meta_description,
                'meta_keywords': page.meta_keywords,
                'author': {
                    'username': current_user.username
                },
                'created_at': page.created_at.isoformat() if page.created_at else None,
                'updated_at': page.updated_at.isoformat() if page.updated_at else None
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in update_page: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.delete("/pages/{page_id}")
async def delete_page(
        page_id: int,
        request: Request,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    删除页面
    """
    try:
        # 检查用户权限 - 只有超级用户才能访问
        from starlette.responses import RedirectResponse
        if isinstance(current_user, RedirectResponse):
            # 如果用户未认证，返回重定向响应
            return current_user
        if not current_user.is_superuser:
            from fastapi import HTTPException
            from fastapi import status
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user doesn't have enough privileges"
            )

        # from src.models.system import Pages

        from sqlalchemy import select
        page_query = select(Pages).where(Pages.id == page_id)
        page_result = await db.execute(page_query)
        page = page_result.scalar_one_or_none()
        if not page:
            return ApiResponse(success=False, error='页面不存在', data=None)

        await db.delete(page)
        await db.commit()

        return ApiResponse(
            success=True,
            data={"message": "页面删除成功"}
        )
    except Exception as e:
        import traceback
        print(f"Error in delete_page: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.post("/menu-items")
async def create_menu_item(
        request: Request,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    创建菜单项
    """
    try:
        # 检查用户权限 - 只有超级用户才能访问
        from starlette.responses import RedirectResponse
        if isinstance(current_user, RedirectResponse):
            # 如果用户未认证，返回重定向响应
            return current_user
        if not current_user.is_superuser:
            from fastapi import HTTPException
            from fastapi import status
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user doesn't have enough privileges"
            )

        data = await request.json()
        title = data.get('title')
        url = data.get('url')
        menu_id = data.get('menu_id')

        if not title or not url or not menu_id:
            return ApiResponse(success=False, error='菜单项标题、链接和菜单ID不能为空', data=None)

        # from src.models.system import MenuItems
        from datetime import datetime

        menu_item = MenuItems(
            title=title,
            url=url,
            menu_id=menu_id,
            target=data.get('target', '_self'),
            parent_id=data.get('parent_id'),
            order_index=data.get('order_index', 0),
            is_active=bool(data.get('is_active', True)),
            created_at=datetime.now(),
        )
        db.add(menu_item)
        await db.commit()
        await db.refresh(menu_item)

        return ApiResponse(
            success=True,
            data={
                'id': menu_item.id,
                'title': menu_item.title,
                'url': menu_item.url,
                'target': menu_item.target,
                'parent_id': menu_item.parent_id,
                'order_index': menu_item.order_index,
                'is_active': menu_item.is_active,
                'created_at': menu_item.created_at.isoformat() if menu_item.created_at else None,
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in create_menu_item: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.put("/menu-items/{menu_item_id}")
async def update_menu_item(
        menu_item_id: int,
        request: Request,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    更新菜单项
    """
    try:
        # 检查用户权限 - 只有超级用户才能访问
        from starlette.responses import RedirectResponse
        if isinstance(current_user, RedirectResponse):
            # 如果用户未认证，返回重定向响应
            return current_user
        if not current_user.is_superuser:
            from fastapi import HTTPException
            from fastapi import status
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user doesn't have enough privileges"
            )

        data = await request.json()

        # from src.models.system import MenuItems
        from datetime import datetime

        from sqlalchemy import select
        menu_item_query = select(MenuItems).where(MenuItems.id == menu_item_id)
        menu_item_result = await db.execute(menu_item_query)
        menu_item = menu_item_result.scalar_one_or_none()
        if not menu_item:
            return ApiResponse(success=False, error='菜单项不存在', data=None)

        menu_item.title = data.get('title', menu_item.title)
        menu_item.url = data.get('url', menu_item.url)
        menu_item.target = data.get('target', menu_item.target)
        menu_item.parent_id = data.get('parent_id', menu_item.parent_id)
        menu_item.order_index = data.get('order_index', menu_item.order_index)
        menu_item.is_active = bool(data.get('is_active', menu_item.is_active))
        menu_item.updated_at = datetime.now()

        await db.commit()
        await db.refresh(menu_item)

        return ApiResponse(
            success=True,
            data={
                'id': menu_item.id,
                'title': menu_item.title,
                'url': menu_item.url,
                'target': menu_item.target,
                'parent_id': menu_item.parent_id,
                'order_index': menu_item.order_index,
                'is_active': menu_item.is_active,
                'created_at': menu_item.created_at.isoformat() if menu_item.created_at else None
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in update_menu_item: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.delete("/menu-items/{menu_item_id}")
async def delete_menu_item(
        menu_item_id: int,
        request: Request,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    删除菜单项
    """
    try:
        # 检查用户权限 - 只有超级用户才能访问
        from starlette.responses import RedirectResponse
        if isinstance(current_user, RedirectResponse):
            # 如果用户未认证，返回重定向响应
            return current_user
        if not current_user.is_superuser:
            from fastapi import HTTPException
            from fastapi import status
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user doesn't have enough privileges"
            )

        # from src.models.system import MenuItems

        from sqlalchemy import select
        menu_item_query = select(MenuItems).where(MenuItems.id == menu_item_id)
        menu_item_result = await db.execute(menu_item_query)
        menu_item = menu_item_result.scalar_one_or_none()
        if not menu_item:
            return ApiResponse(success=False, error='菜单项不存在', data=None)

        # 检查是否有子菜单项关联到此菜单项
        from sqlalchemy import select
        child_items_query = select(MenuItems).where(MenuItems.parent_id == menu_item_id)
        child_items_result = await db.execute(child_items_query)
        child_items = child_items_result.scalars().all()
        if child_items:
            return ApiResponse(success=False, error='菜单项下还有子菜单项，无法删除', data=None)

        await db.delete(menu_item)
        await db.commit()

        return ApiResponse(
            success=True,
            data={"message": "菜单项删除成功"}
        )
    except Exception as e:
        import traceback
        print(f"Error in delete_menu_item: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))
