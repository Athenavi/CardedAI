"""
屏幕选项(Screen Options)服务
使用现有的fb_custom_fields表存储用户偏好
"""
import json
from typing import Dict, Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.custom_field import CustomField


class ScreenOptionsService:
    """屏幕选项服务"""
    
    def __init__(self):
        pass
    
    async def get_option(
        self,
        db: AsyncSession,
        user_id: int,
        page_name: str,
        option_key: str,
        default: Any = None
    ) -> Any:
        """
        获取用户的屏幕选项
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            page_name: 页面名称 (如: articles, users, media)
            option_key: 选项键名 (如: columns, per_page, sidebar_visible)
            default: 默认值
            
        Returns:
            选项值
        """
        field_name = f"{page_name}.{option_key}"
        
        query = select(CustomField).where(
            CustomField.user == user_id,
            CustomField.field_name == field_name
        )
        result = await db.execute(query)
        custom_field = result.scalar_one_or_none()
        
        if custom_field is None:
            return default
        
        # 尝试解析JSON
        try:
            return json.loads(custom_field.field_value)
        except (json.JSONDecodeError, TypeError):
            return custom_field.field_value
    
    async def set_option(
        self,
        db: AsyncSession,
        user_id: int,
        page_name: str,
        option_key: str,
        value: Any
    ) -> bool:
        """
        设置用户的屏幕选项
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            page_name: 页面名称
            option_key: 选项键名
            value: 选项值
            
        Returns:
            是否成功
        """
        field_name = f"{page_name}.{option_key}"
        
        # 序列化值为JSON
        if isinstance(value, (dict, list, bool)):
            field_value = json.dumps(value)
        else:
            field_value = str(value)
        
        # 查找现有记录
        query = select(CustomField).where(
            CustomField.user == user_id,
            CustomField.field_name == field_name
        )
        result = await db.execute(query)
        custom_field = result.scalar_one_or_none()
        
        if custom_field:
            # 更新现有记录
            custom_field.field_value = field_value
        else:
            # 创建新记录
            custom_field = CustomField(
                user=user_id,
                field_name=field_name,
                field_value=field_value
            )
            db.add(custom_field)
        
        return True
    
    async def delete_option(
        self,
        db: AsyncSession,
        user_id: int,
        page_name: str,
        option_key: str
    ) -> bool:
        """
        删除用户的屏幕选项
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            page_name: 页面名称
            option_key: 选项键名
            
        Returns:
            是否成功
        """
        field_name = f"{page_name}.{option_key}"
        
        query = select(CustomField).where(
            CustomField.user == user_id,
            CustomField.field_name == field_name
        )
        result = await db.execute(query)
        custom_field = result.scalar_one_or_none()
        
        if custom_field:
            await db.delete(custom_field)
            return True
        
        return False
    
    async def get_all_options(
        self,
        db: AsyncSession,
        user_id: int,
        page_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取用户的所有屏幕选项
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            page_name: 可选的页面名称过滤
            
        Returns:
            选项字典 {page_name.option_key: value}
        """
        query = select(CustomField).where(CustomField.user == user_id)
        
        if page_name:
            query = query.where(CustomField.field_name.like(f"{page_name}.%"))
        
        result = await db.execute(query)
        custom_fields = result.scalars().all()
        
        options = {}
        for cf in custom_fields:
            try:
                options[cf.field_name] = json.loads(cf.field_value)
            except (json.JSONDecodeError, TypeError):
                options[cf.field_name] = cf.field_value
        
        return options
    
    async def get_page_options(
        self,
        db: AsyncSession,
        user_id: int,
        page_name: str
    ) -> Dict[str, Any]:
        """
        获取指定页面的所有选项
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            page_name: 页面名称
            
        Returns:
            选项字典 {option_key: value}
        """
        all_options = await self.get_all_options(db, user_id, page_name)
        
        # 提取当前页面的选项
        page_options = {}
        prefix = f"{page_name}."
        for key, value in all_options.items():
            if key.startswith(prefix):
                option_key = key[len(prefix):]
                page_options[option_key] = value
        
        return page_options


# 单例实例
screen_options_service = ScreenOptionsService()
