"""
自定义块模式服务
使用 ORM BlockPattern 模型进行持久化存储

架构说明：
- 内置模式：由 BuiltinBlockPattern (block_pattern_library.py) 管理，硬编码在内存中
- 自定义模式：由本服务管理，通过 ORM BlockPattern 模型持久化到数据库
"""

import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional


class CustomBlockPatternService:
    """
    自定义块模式服务

    功能:
    1. 保存自定义块模式（ORM 持久化）
    2. 加载用户的块模式
    3. 编辑和删除
    4. 分类管理
    """

    async def save_pattern(
        self,
        user_id: int,
        title: str,
        description: str,
        blocks: List[Dict[str, Any]],
        category: str = "custom",
        tags: Optional[List[str]] = None,
        pattern_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        保存自定义块模式到数据库

        Args:
            user_id: 用户ID
            title: 模式标题
            description: 描述
            blocks: 区块数据
            category: 分类
            tags: 标签
            pattern_id: 模式ID（编辑时使用）

        Returns:
            保存结果
        """
        try:
            from src.utils.database.unified_manager import db_manager
            from shared.models.block_pattern import BlockPattern as ORMBlockPattern

            now = datetime.now(timezone.utc)

            async with db_manager.get_async_session() as session:
                if pattern_id:
                    # 编辑已有模式
                    from sqlalchemy import select
                    result = await session.execute(
                        select(ORMBlockPattern).where(
                            ORMBlockPattern.id == pattern_id,
                            ORMBlockPattern.user_id == user_id
                        )
                    )
                    pattern = result.scalar_one_or_none()

                    if not pattern:
                        return {
                            "success": False,
                            "error": "块模式不存在或无权修改"
                        }

                    pattern.title = title
                    pattern.description = description
                    pattern.blocks = json.dumps(blocks, ensure_ascii=False)
                    pattern.category = category
                    pattern.keywords = ",".join(tags) if tags else None
                    pattern.updated_at = now

                    await session.commit()
                    await session.refresh(pattern)

                    return {
                        "success": True,
                        "message": "块模式已更新",
                        "pattern_id": pattern.id,
                        "pattern": pattern.to_dict()
                    }
                else:
                    # 创建新模式
                    # 生成唯一名称
                    name = f"user_{user_id}_{title.replace(' ', '_').lower()}_{int(now.timestamp())}"

                    pattern = ORMBlockPattern(
                        name=name,
                        title=title,
                        description=description,
                        category=category,
                        blocks=json.dumps(blocks, ensure_ascii=False),
                        keywords=",".join(tags) if tags else None,
                        is_public=False,
                        user_id=user_id,
                        created_at=now,
                        updated_at=now
                    )

                    session.add(pattern)
                    await session.commit()
                    await session.refresh(pattern)

                    return {
                        "success": True,
                        "message": "块模式已保存",
                        "pattern_id": pattern.id,
                        "pattern": pattern.to_dict()
                    }

        except Exception as e:
            return {
                "success": False,
                "error": f"保存失败: {str(e)}"
            }

    async def get_user_patterns(self, user_id: int, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取用户的自定义块模式

        Args:
            user_id: 用户ID
            category: 可选的分类过滤

        Returns:
            块模式列表
        """
        try:
            from src.utils.database.unified_manager import db_manager
            from shared.models.block_pattern import BlockPattern as ORMBlockPattern
            from sqlalchemy import select

            async with db_manager.get_async_session() as session:
                query = select(ORMBlockPattern).where(ORMBlockPattern.user_id == user_id)

                if category:
                    query = query.where(ORMBlockPattern.category == category)

                query = query.order_by(ORMBlockPattern.created_at.desc())

                result = await session.execute(query)
                patterns = result.scalars().all()

                return [p.to_dict() for p in patterns]

        except Exception as e:
            print(f"获取用户块模式失败: {e}")
            return []

    async def get_pattern_by_id(self, user_id: int, pattern_id: int) -> Optional[Dict[str, Any]]:
        """
        根据ID获取块模式

        Args:
            user_id: 用户ID
            pattern_id: 模式ID

        Returns:
            块模式数据，不存在返回None
        """
        try:
            from src.utils.database.unified_manager import db_manager
            from shared.models.block_pattern import BlockPattern as ORMBlockPattern
            from sqlalchemy import select

            async with db_manager.get_async_session() as session:
                result = await session.execute(
                    select(ORMBlockPattern).where(
                        ORMBlockPattern.id == pattern_id,
                        ORMBlockPattern.user_id == user_id
                    )
                )
                pattern = result.scalar_one_or_none()

                if pattern:
                    return pattern.to_dict()
                return None

        except Exception as e:
            print(f"获取块模式失败: {e}")
            return None

    async def update_pattern(
        self,
        user_id: int,
        pattern_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        blocks: Optional[List[Dict[str, Any]]] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        更新块模式

        Args:
            user_id: 用户ID
            pattern_id: 模式ID
            其他参数为可选更新字段

        Returns:
            更新结果
        """
        try:
            from src.utils.database.unified_manager import db_manager
            from shared.models.block_pattern import BlockPattern as ORMBlockPattern
            from sqlalchemy import select

            async with db_manager.get_async_session() as session:
                result = await session.execute(
                    select(ORMBlockPattern).where(
                        ORMBlockPattern.id == pattern_id,
                        ORMBlockPattern.user_id == user_id
                    )
                )
                pattern = result.scalar_one_or_none()

                if not pattern:
                    return {
                        "success": False,
                        "error": "块模式不存在或无权修改"
                    }

                # 更新字段
                if title is not None:
                    pattern.title = title
                if description is not None:
                    pattern.description = description
                if blocks is not None:
                    pattern.blocks = json.dumps(blocks, ensure_ascii=False)
                if category is not None:
                    pattern.category = category
                if tags is not None:
                    pattern.keywords = ",".join(tags)

                pattern.updated_at = datetime.now(timezone.utc)
                await session.commit()
                await session.refresh(pattern)

                return {
                    "success": True,
                    "message": "块模式已更新",
                    "pattern": pattern.to_dict()
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"更新失败: {str(e)}"
            }

    async def delete_pattern(self, user_id: int, pattern_id: int) -> Dict[str, Any]:
        """
        删除块模式

        Args:
            user_id: 用户ID
            pattern_id: 模式ID

        Returns:
            删除结果
        """
        try:
            from src.utils.database.unified_manager import db_manager
            from shared.models.block_pattern import BlockPattern as ORMBlockPattern
            from sqlalchemy import select, delete

            async with db_manager.get_async_session() as session:
                result = await session.execute(
                    select(ORMBlockPattern).where(
                        ORMBlockPattern.id == pattern_id,
                        ORMBlockPattern.user_id == user_id
                    )
                )
                pattern = result.scalar_one_or_none()

                if not pattern:
                    return {
                        "success": False,
                        "error": "块模式不存在或无权删除"
                    }

                await session.delete(pattern)
                await session.commit()

                return {
                    "success": True,
                    "message": "块模式已删除"
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"删除失败: {str(e)}"
            }

    async def get_categories(self, user_id: int) -> List[str]:
        """获取用户的所有分类"""
        try:
            from src.utils.database.unified_manager import db_manager
            from shared.models.block_pattern import BlockPattern as ORMBlockPattern
            from sqlalchemy import select, distinct

            async with db_manager.get_async_session() as session:
                result = await session.execute(
                    select(distinct(ORMBlockPattern.category)).where(
                        ORMBlockPattern.user_id == user_id
                    )
                )
                categories = [row[0] for row in result.all() if row[0]]
                return sorted(categories)

        except Exception as e:
            print(f"获取分类失败: {e}")
            return []


# 全局实例
custom_block_pattern_service = CustomBlockPatternService()
