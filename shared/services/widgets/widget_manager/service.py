"""
Widget服务核心逻辑
提供Widget注册、查询、配置管理等功能
"""

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.widget_instance import WidgetInstance
from shared.services.performance.cache_manager import cache_service
from shared.services.widgets.widget_manager.config import WIDGET_TYPES, WIDGET_AREAS
from shared.services.widgets.widget_manager.renderer import WidgetRenderer


class WidgetService:
    """
    小部件系统服务

    功能:
    1. 动态小部件注册
    2. 小部件位置管理
    3. 小部件配置
    4. 拖拽排序
    5. 条件显示
    6. 小部件缓存
    """

    def __init__(self, cache_ttl: int = 3600):
        self.cache_ttl = cache_ttl
        self.renderer = WidgetRenderer()
        self.widget_types = WIDGET_TYPES
        self.widget_areas = WIDGET_AREAS

    def register_widget(
            self,
            area: str,
            widget_type: str,
            config: Optional[Dict] = None,
            position: Optional[int] = None,
            conditions: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """注册小部件到指定位置"""
        try:
            if area not in self.widget_areas:
                return {'success': False, 'error': f'无效的小部件区域: {area}'}

            if widget_type not in self.widget_types:
                return {'success': False, 'error': f'无效的小部件类型: {widget_type}'}

            default_config = self.widget_types[widget_type]['default_config'].copy()
            if config:
                default_config.update(config)

            widget_instance = {
                'id': f"{widget_type}_{datetime.now().timestamp()}",
                'type': widget_type,
                'area': area,
                'config': default_config,
                'position': position or 0,
                'conditions': conditions or {},
                'enabled': True,
                'created_at': datetime.now().isoformat()
            }

            return {'success': True, 'data': widget_instance}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def get_widgets_for_area(
            self,
            area: str,
            context: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """获取指定区域的小部件列表"""
        from src.utils.database.unified_manager import db_manager
        from sqlalchemy import select

        async with db_manager.get_session() as db:
            result = await db.execute(
                select(WidgetInstance)
                .where(WidgetInstance.area == area, WidgetInstance.is_active == True)
                .order_by(WidgetInstance.order_index)
            )
            widgets_db = result.scalars().all()

        widgets = []
        for w in widgets_db:
            try:
                config = json.loads(w.config) if w.config else {}
                conditions = json.loads(w.conditions) if w.conditions else {}
            except:
                config, conditions = {}, {}

            widgets.append({
                'id': str(w.id),
                'type': w.widget_type,
                'title': w.title,
                'config': config,
                'position': w.order_index,
                'enabled': w.is_active,
                'conditions': conditions
            })

        # 检查显示条件
        if context:
            widgets = [w for w in widgets if self._check_conditions(w.get('conditions', {}), context)]

        return widgets

    def _check_conditions(self, conditions: Dict, context: Dict) -> bool:
        """检查小部件显示条件"""
        if not conditions:
            return True

        if 'page_type' in conditions and context.get('page_type') not in conditions['page_type']:
            return False
        if 'user_role' in conditions and context.get('user_role') not in conditions['user_role']:
            return False
        if 'device' in conditions and context.get('device') not in conditions['device']:
            return False

        return True

    async def update_widget_config(self, widget_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """更新小部件配置"""
        try:
            from src.utils.database.unified_manager import db_manager
            from sqlalchemy import select, update

            async with db_manager.get_session() as db:
                result = await db.execute(
                    select(WidgetInstance).where(WidgetInstance.id == int(widget_id))
                )
                widget = result.scalar_one_or_none()

                if not widget:
                    return {'success': False, 'error': '小部件不存在'}

                widget.config = json.dumps(config, ensure_ascii=False)
                widget.updated_at = datetime.now()
                await db.commit()

            return {'success': True, 'message': '配置更新成功'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def reorder_widgets(self, area: str, widget_order: List[str]) -> Dict[str, Any]:
        """重新排序小部件"""
        try:
            from src.utils.database.unified_manager import db_manager
            from sqlalchemy import select

            async with db_manager.get_session() as db:
                for index, widget_id in enumerate(widget_order):
                    result = await db.execute(
                        select(WidgetInstance).where(WidgetInstance.id == int(widget_id))
                    )
                    widget = result.scalar_one_or_none()
                    if widget:
                        widget.order_index = index

                await db.commit()

            return {'success': True, 'message': '排序更新成功'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def remove_widget(self, widget_id: str) -> Dict[str, Any]:
        """移除小部件"""
        try:
            from src.utils.database.unified_manager import db_manager
            from sqlalchemy import select, delete

            async with db_manager.get_session() as db:
                result = await db.execute(
                    select(WidgetInstance).where(WidgetInstance.id == int(widget_id))
                )
                widget = result.scalar_one_or_none()

                if not widget:
                    return {'success': False, 'error': '小部件不存在'}

                await db.delete(widget)
                await db.commit()

            return {'success': True, 'message': '小部件已移除'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_widget_types(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取小部件类型列表"""
        types = []
        for key, info in self.widget_types.items():
            if category and info.get('category') != category:
                continue
            types.append({
                'type': key,
                'name': info['name'],
                'description': info['description'],
                'icon': info['icon'],
                'category': info.get('category'),
                'default_config': info['default_config']
            })
        return types

    def get_widget_areas(self) -> List[Dict[str, Any]]:
        """获取所有小部件区域"""
        return [{
            'id': key,
            'name': info['name'],
            'description': info['description'],
            'max_widgets': info.get('max_widgets')
        } for key, info in self.widget_areas.items()]

    def render_widget(self, widget: Dict[str, Any], context: Optional[Dict] = None) -> str:
        """渲染小部件为HTML(带缓存)"""
        widget_type = widget.get('type')
        config = widget.get('config', {})
        title = widget.get('title', '')

        # 生成缓存键
        cache_key = self._generate_cache_key(widget, context)

        # 尝试从缓存获取
        cached_html = cache_service.get(cache_key)
        if cached_html:
            return cached_html

        # 渲染
        html = self.renderer.render_widget(widget_type, config, title)

        # 缓存结果
        cache_service.set(cache_key, html, ttl=self.cache_ttl)

        return html

    def _generate_cache_key(self, widget: Dict[str, Any], context: Optional[Dict] = None) -> str:
        """生成Widget缓存键"""
        key_data = {
            'id': widget.get('id'),
            'type': widget.get('type'),
            'config': widget.get('config', {}),
            'context': context or {}
        }

        key_string = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_string.encode('utf-8')).hexdigest()

        return f"widget_render:{key_hash}"

    def invalidate_widget_cache(self, widget_id: str = None, widget_type: str = None):
        """清除Widget缓存"""
        if widget_id:
            cache_service.delete(f"widget_render:{widget_id}")
        elif widget_type:
            cache_service.delete_pattern(f"widget_render:type:{widget_type}:*")
        else:
            cache_service.delete_pattern("widget_render:*")

    # ==================== 异步数据库方法 ====================

    async def save_widget_to_db(
            self,
            db: AsyncSession,
            area: str,
            widget_type: str,
            config: Dict[str, Any],
            title: Optional[str] = None,
            order_index: int = 0,
            conditions: Optional[Dict] = None
    ) -> Optional[WidgetInstance]:
        """保存Widget实例到数据库"""
        try:
            widget = WidgetInstance(
                widget_type=widget_type,
                area=area,
                title=title or self.widget_types.get(widget_type, {}).get('name', ''),
                config=json.dumps(config, ensure_ascii=False),
                order_index=order_index,
                is_active=True,
                conditions=json.dumps(conditions, ensure_ascii=False) if conditions else None,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )

            db.add(widget)
            await db.commit()
            await db.refresh(widget)
            return widget
        except Exception as e:
            await db.rollback()
            print(f"保存Widget失败: {e}")
            return None

    async def get_widgets_by_area(self, db: AsyncSession, area: str) -> List[WidgetInstance]:
        """获取指定区域的所有Widget实例"""
        try:
            query = (
                select(WidgetInstance)
                .where(WidgetInstance.area == area)
                .where(WidgetInstance.is_active == True)
                .order_by(WidgetInstance.order_index)
            )
            result = await db.execute(query)
            return result.scalars().all()
        except Exception as e:
            print(f"获取Widget列表失败: {e}")
            return []

    async def update_widget_config_in_db(
            self,
            db: AsyncSession,
            widget_id: int,
            config: Dict[str, Any]
    ) -> bool:
        """更新Widget配置"""
        try:
            stmt = (
                update(WidgetInstance)
                .where(WidgetInstance.id == widget_id)
                .values(
                    config=json.dumps(config, ensure_ascii=False),
                    updated_at=datetime.now(timezone.utc)
                )
            )
            await db.execute(stmt)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            print(f"更新Widget配置失败: {e}")
            return False

    async def reorder_widgets_in_db(
            self,
            db: AsyncSession,
            area: str,
            widget_ids: List[int]
    ) -> bool:
        """重新排序Widget"""
        try:
            for index, widget_id in enumerate(widget_ids):
                stmt = (
                    update(WidgetInstance)
                    .where(WidgetInstance.id == widget_id)
                    .where(WidgetInstance.area == area)
                    .values(order_index=index, updated_at=datetime.now(timezone.utc))
                )
                await db.execute(stmt)

            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            print(f"重新排序Widget失败: {e}")
            return False

    async def delete_widget_from_db(self, db: AsyncSession, widget_id: int) -> bool:
        """删除Widget实例"""
        try:
            stmt = delete(WidgetInstance).where(WidgetInstance.id == widget_id)
            await db.execute(stmt)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            print(f"删除Widget失败: {e}")
            return False

    async def toggle_widget_active(self, db: AsyncSession, widget_id: int, is_active: bool) -> bool:
        """启用/禁用Widget"""
        try:
            stmt = (
                update(WidgetInstance)
                .where(WidgetInstance.id == widget_id)
                .values(is_active=is_active, updated_at=datetime.now(timezone.utc))
            )
            await db.execute(stmt)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            print(f"切换Widget状态失败: {e}")
            return False

    # ==================== Widget数据获取方法 ====================

    async def get_recent_posts_data(self, db: AsyncSession, count: int = 5, **kwargs) -> List[Dict[str, Any]]:
        """获取最新文章数据"""
        try:
            from shared.models.article import Article
            from sqlalchemy import desc

            stmt = (
                select(Article)
                .where(Article.status == 1)
                .order_by(desc(Article.created_at))
                .limit(count)
            )
            result = await db.execute(stmt)
            articles = result.scalars().all()

            return [{
                'id': article.id,
                'title': article.title,
                'slug': article.slug,
                'excerpt': article.excerpt[:100] + '...' if article.excerpt and len(
                    article.excerpt) > 100 else article.excerpt,
                'created_at': article.created_at.isoformat() if hasattr(article.created_at, 'isoformat') else str(
                    article.created_at),
                'cover_image': article.cover_image,
            } for article in articles]
        except Exception as e:
            print(f"获取最新文章失败: {e}")
            return []

    async def get_recent_comments_data(self, db: AsyncSession, count: int = 5, show_avatar: bool = True) -> List[
        Dict[str, Any]]:
        """获取最新评论数据"""
        try:
            from shared.models.comment import Comment
            from shared.models.article import Article
            from shared.models.user import User
            from sqlalchemy import desc

            stmt = (
                select(Comment)
                .where(Comment.is_approved == True)
                .order_by(desc(Comment.created_at))
                .limit(count)
            )
            result = await db.execute(stmt)
            comments = result.scalars().all()

            comments_data = []
            for comment in comments:
                article_stmt = select(Article).where(Article.id == comment.article_id)
                article_result = await db.execute(article_stmt)
                article = article_result.scalar_one_or_none()

                author_name = comment.author_name or '匿名'
                avatar_url = None

                if comment.user_id and show_avatar:
                    user_stmt = select(User).where(User.id == comment.user_id)
                    user_result = await db.execute(user_stmt)
                    user = user_result.scalar_one_or_none()
                    if user:
                        author_name = user.username
                        avatar_url = user.profile_picture or user.avatar_url

                comments_data.append({
                    'id': comment.id,
                    'author_name': author_name,
                    'avatar_url': avatar_url,
                    'content': comment.content[:100] + '...' if len(comment.content) > 100 else comment.content,
                    'created_at': comment.created_at.isoformat() if hasattr(comment.created_at, 'isoformat') else str(
                        comment.created_at),
                    'article_id': comment.article_id,
                    'article_title': article.title if article else '未知文章',
                })

            return comments_data
        except Exception as e:
            print(f"获取最新评论失败: {e}")
            return []

    async def get_tags_cloud_data(self, db: AsyncSession, count: int = 20, **kwargs) -> List[Dict[str, Any]]:
        """获取标签云数据"""
        try:
            from shared.models.article import Article
            from collections import Counter

            stmt = select(Article.tags_list).where(Article.status == 1)  # 修复：使用 tags_list
            result = await db.execute(stmt)
            articles = result.scalars().all()

            tag_counter = Counter()
            for article in articles:
                if article.tags_list:  # 修复：使用 tags_list
                    tags_list = article.tags_list if isinstance(article.tags_list, list) else [tag.strip() for tag in
                                                                                               re.split(r'[,;]',
                                                                                                        article.tags_list)
                                                                                               if
                                                                                               tag.strip()]
                    tag_counter.update(tags_list)

            most_common = tag_counter.most_common(count)
            max_count = most_common[0][1] if most_common else 1

            return [{
                'name': tag_name,
                'count': tag_count,
                'font_size': round(0.8 + (tag_count / max_count) * 1.2, 2),
                'slug': tag_name.lower().replace(' ', '-'),
            } for tag_name, tag_count in most_common]
        except Exception as e:
            print(f"获取标签云失败: {e}")
            return []

    async def get_categories_data(self, db: AsyncSession, show_count: bool = True, **kwargs) -> List[Dict[str, Any]]:
        """获取分类目录数据"""
        try:
            from shared.models.category import Category
            from shared.models.article import Article
            from sqlalchemy import func

            stmt = select(Category).where(Category.is_visible == True).order_by(Category.sort_order)
            result = await db.execute(stmt)
            categories = result.scalars().all()

            categories_data = []
            for category in categories:
                cat_data = {
                    'id': category.id,
                    'name': category.name,
                    'slug': category.slug,
                    'description': category.description,
                    'parent_id': category.parent_id,
                }

                if show_count:
                    count_stmt = select(func.count(Article.id)).where(
                        Article.category == category.id,
                        Article.status == 1
                    )
                    count_result = await db.execute(count_stmt)
                    cat_data['count'] = count_result.scalar() or 0

                categories_data.append(cat_data)

            return categories_data
        except Exception as e:
            print(f"获取分类目录失败: {e}")
            return []

    async def get_archives_data(self, db: AsyncSession, archive_type: str = 'monthly', show_count: bool = True) -> List[
        Dict[str, Any]]:
        """获取文章归档数据"""
        try:
            from shared.models.article import Article
            from sqlalchemy import func, extract

            if archive_type == 'monthly':
                stmt = select(
                    extract('year', Article.created_at).label('year'),
                    extract('month', Article.created_at).label('month'),
                    func.count(Article.id).label('count')
                ).where(Article.status == 1).group_by(
                    extract('year', Article.created_at),
                    extract('month', Article.created_at)
                ).order_by(
                    extract('year', Article.created_at).desc(),
                    extract('month', Article.created_at).desc()
                )
            else:
                stmt = select(
                    extract('year', Article.created_at).label('year'),
                    func.count(Article.id).label('count')
                ).where(Article.status == 1).group_by(
                    extract('year', Article.created_at)
                ).order_by(extract('year', Article.created_at).desc())

            result = await db.execute(stmt)
            archives = result.all()

            archives_data = []
            for row in archives:
                if archive_type == 'monthly':
                    year, month = int(row.year), int(row.month)
                    label, slug = f"{year}年{month:02d}月", f"{year}/{month:02d}"
                else:
                    year = int(row.year)
                    label, slug = f"{year}年", str(year)

                archive_data = {'label': label, 'slug': slug}
                if show_count:
                    archive_data['count'] = row.count

                archives_data.append(archive_data)

            return archives_data
        except Exception as e:
            print(f"获取文章归档失败: {e}")
            return []

    async def get_popular_posts_data(self, db: AsyncSession, count: int = 5, period: str = 'week') -> List[
        Dict[str, Any]]:
        """获取热门文章数据"""
        try:
            from shared.models.article import Article
            from sqlalchemy import desc
            from datetime import datetime, timedelta

            stmt = select(Article).where(Article.status == 1)

            now = datetime.now()
            if period == 'day':
                stmt = stmt.where(Article.created_at >= now - timedelta(days=1))
            elif period == 'week':
                stmt = stmt.where(Article.created_at >= now - timedelta(weeks=1))
            elif period == 'month':
                stmt = stmt.where(Article.created_at >= now - timedelta(days=30))

            stmt = stmt.order_by(desc(Article.views)).limit(count)
            result = await db.execute(stmt)
            articles = result.scalars().all()

            return [{
                'id': article.id,
                'title': article.title,
                'slug': article.slug,
                'views': article.views or 0,
                'cover_image': article.cover_image,
                'created_at': article.created_at.isoformat() if hasattr(article.created_at, 'isoformat') else str(
                    article.created_at),
            } for article in articles]
        except Exception as e:
            print(f"获取热门文章失败: {e}")
            return []
