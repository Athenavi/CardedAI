"""
批量操作服务

功能：
1. 批量删除文章/评论/用户
2. 批量更新状态（发布/草稿）
3. 批量移动分类
4. 批量添加标签
5. 操作日志记录
"""

from datetime import datetime
from typing import List, Dict, Optional

from sqlalchemy import update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.unified_logger import default_logger as logger


class BatchOperationService:
    """
    批量操作服务

    参考 WordPress 和 Django Admin 的设计模式
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.operation_log = []

    async def batch_delete_articles(
            self,
            article_ids: List[int],
            operator_id: Optional[int] = None,
            user=None
    ) -> Dict:
        """
        批量删除文章

        Args:
            article_ids: 文章ID列表
            operator_id: 操作者ID
            user: 当前用户对象（用于权限检查）

        Returns:
            操作结果
        """
        from shared.models.article import Article
        from shared.models.comment import Comment
        from shared.models.comment_vote import CommentVote
        from shared.models.comment_subscription import CommentSubscription
        from sqlalchemy import select

        if not article_ids:
            return {'success': False, 'message': '没有选择任何文章'}

        try:
            # 权限检查：如果不是管理员，只能删除自己的文章
            if user and not getattr(user, 'is_superuser', False):
                stmt = select(Article).where(
                    Article.id.in_(article_ids),
                    Article.user == user.id
                )
                result = await self.db.execute(stmt)
                allowed_articles = result.scalars().all()
                allowed_ids = [a.id for a in allowed_articles]

                if len(allowed_ids) != len(article_ids):
                    forbidden_count = len(article_ids) - len(allowed_ids)
                    return {
                        'success': False,
                        'message': f'您没有权限删除 {forbidden_count} 篇文章'
                    }

            # 先删除相关文章的评论投票
            comment_ids_result = await self.db.execute(
                select(Comment.id).where(Comment.article_id.in_(article_ids))
            )
            comment_ids = [row[0] for row in comment_ids_result.all()]
            if comment_ids:
                await self.db.execute(
                    delete(CommentVote).where(CommentVote.comment_id.in_(comment_ids))
                )

            # 删除评论订阅
            await self.db.execute(
                delete(CommentSubscription).where(
                    CommentSubscription.article_id.in_(article_ids)
                )
            )

            # 删除相关文章的评论
            await self.db.execute(
                delete(Comment).where(
                    Comment.article_id.in_(article_ids)
                )
            )

            # 注意：如果有文章浏览记录表，也应该在这里删除
            # 目前文章浏览量直接存储在 Article 表中，随文章一起删除

            # 删除文章
            result = await self.db.execute(
                delete(Article).where(
                    Article.id.in_(article_ids)
                )
            )

            deleted_count = result.rowcount
            await self.db.commit()

            # 记录操作日志
            self._log_operation(
                'batch_delete_articles',
                {'article_ids': article_ids, 'count': deleted_count},
                operator_id
            )

            return {
                'success': True,
                'message': f'成功删除 {deleted_count} 篇文章',
                'deleted_count': deleted_count,
            }
        except Exception as e:
            await self.db.rollback()
            return {
                'success': False,
                'message': f'删除失败: {str(e)}',
            }

    async def batch_update_article_status(
            self,
            article_ids: List[int],
            status: str,
            operator_id: Optional[int] = None,
            user=None
    ) -> Dict:
        """
        批量更新文章状态

        Args:
            article_ids: 文章ID列表
            status: 新状态 (published, draft, archived)
            operator_id: 操作者ID
            user: 当前用户对象（用于权限检查）

        Returns:
            操作结果
        """
        from shared.models.article import Article
        from sqlalchemy import select

        if not article_ids:
            return {'success': False, 'message': '没有选择任何文章'}

        valid_statuses = ['published', 'draft', 'archived']
        if status not in valid_statuses:
            return {'success': False, 'message': f'无效的状态: {status}'}

        try:
            # 权限检查：如果不是管理员，只能更新自己的文章
            if user and not getattr(user, 'is_superuser', False):
                stmt = select(Article).where(
                    Article.id.in_(article_ids),
                    Article.user == user.id
                )
                result = await self.db.execute(stmt)
                allowed_articles = result.scalars().all()
                allowed_ids = [a.id for a in allowed_articles]

                if len(allowed_ids) != len(article_ids):
                    forbidden_count = len(article_ids) - len(allowed_ids)
                    return {
                        'success': False,
                        'message': f'您没有权限更新 {forbidden_count} 篇文章'
                    }

            result = await self.db.execute(
                update(Article)
                .where(Article.id.in_(article_ids))
                .values(
                    status=status,
                    updated_at=datetime.now()
                )
            )

            updated_count = result.rowcount
            await self.db.commit()

            # 记录操作日志
            self._log_operation(
                'batch_update_status',
                {'article_ids': article_ids, 'status': status, 'count': updated_count},
                operator_id
            )

            return {
                'success': True,
                'message': f'成功更新 {updated_count} 篇文章状态为 {status}',
                'updated_count': updated_count,
            }
        except Exception as e:
            await self.db.rollback()
            return {
                'success': False,
                'message': f'更新失败: {str(e)}',
            }

    async def batch_move_to_category(
            self,
            article_ids: List[int],
            category_id: int,
            operator_id: Optional[int] = None,
            user=None
    ) -> Dict:
        """
        批量移动文章到指定分类

        Args:
            article_ids: 文章ID列表
            category_id: 目标分类ID
            operator_id: 操作者ID
            user: 当前用户对象（用于权限检查）

        Returns:
            操作结果
        """
        from shared.models.article import Article
        from shared.models.category import Category
        from sqlalchemy import select

        if not article_ids:
            return {'success': False, 'message': '没有选择任何文章'}

        # 验证分类是否存在
        category = await self.db.get(Category, category_id)
        if not category:
            return {'success': False, 'message': '分类不存在'}

        try:
            # 权限检查：如果不是管理员，只能移动自己的文章
            if user and not getattr(user, 'is_superuser', False):
                stmt = select(Article).where(
                    Article.id.in_(article_ids),
                    Article.user == user.id
                )
                result = await self.db.execute(stmt)
                allowed_articles = result.scalars().all()
                allowed_ids = [a.id for a in allowed_articles]

                if len(allowed_ids) != len(article_ids):
                    forbidden_count = len(article_ids) - len(allowed_ids)
                    return {
                        'success': False,
                        'message': f'您没有权限移动 {forbidden_count} 篇文章'
                    }

            result = await self.db.execute(
                update(Article)
                .where(Article.id.in_(article_ids))
                .values(
                    category=category_id,
                    updated_at=datetime.now()
                )
            )

            updated_count = result.rowcount
            await self.db.commit()

            # 记录操作日志
            self._log_operation(
                'batch_move_category',
                {'article_ids': article_ids, 'category_id': category_id, 'count': updated_count},
                operator_id
            )

            return {
                'success': True,
                'message': f'成功移动 {updated_count} 篇文章到分类 "{category.name}"',
                'updated_count': updated_count,
            }
        except Exception as e:
            await self.db.rollback()
            return {
                'success': False,
                'message': f'移动失败: {str(e)}',
            }

    async def batch_add_tags(
            self,
            article_ids: List[int],
            tags: List[str],
            operator_id: Optional[int] = None,
            user=None
    ) -> Dict:
        """
        批量添加标签

        Args:
            article_ids: 文章ID列表
            tags: 标签列表
            operator_id: 操作者ID
            user: 当前用户对象（用于权限检查）

        Returns:
            操作结果
        """
        from shared.models.article import Article
        from sqlalchemy import select
        import json

        if not article_ids:
            return {'success': False, 'message': '没有选择任何文章'}

        if not tags:
            return {'success': False, 'message': '没有提供标签'}

        try:
            # 权限检查：如果不是管理员，只能为自己的文章添加标签
            if user and not getattr(user, 'is_superuser', False):
                stmt = select(Article).where(
                    Article.id.in_(article_ids),
                    Article.user == user.id
                )
                result = await self.db.execute(stmt)
                allowed_articles = result.scalars().all()
                allowed_ids = [a.id for a in allowed_articles]

                if len(allowed_ids) != len(article_ids):
                    forbidden_count = len(article_ids) - len(allowed_ids)
                    return {
                        'success': False,
                        'message': f'您没有权限为 {forbidden_count} 篇文章添加标签'
                    }

            # 获取所有文章
            result = await self.db.execute(
                select(Article.id, Article.tags_list).where(
                    Article.id.in_(article_ids)
                )
            )

            articles = result.all()
            updated_count = 0

            for article_id, current_tags_json in articles:
                # 解析现有标签
                current_tags = json.loads(current_tags_json) if current_tags_json else []

                # 添加新标签（去重）
                for tag in tags:
                    if tag not in current_tags:
                        current_tags.append(tag)

                # 更新文章
                await self.db.execute(
                    update(Article)
                    .where(Article.id == article_id)
                    .values(
                        tags_list=';'.join(current_tags),
                        updated_at=datetime.now()
                    )
                )
                updated_count += 1

            await self.db.commit()

            # 记录操作日志
            self._log_operation(
                'batch_add_tags',
                {'article_ids': article_ids, 'tags': tags, 'count': updated_count},
                operator_id
            )

            return {
                'success': True,
                'message': f'成功为 {updated_count} 篇文章添加标签',
                'updated_count': updated_count,
            }
        except Exception as e:
            await self.db.rollback()
            return {
                'success': False,
                'message': f'添加标签失败: {str(e)}',
            }

    async def batch_delete_comments(
            self,
            comment_ids: List[int],
            operator_id: Optional[int] = None
    ) -> Dict:
        """
        批量删除评论

        Args:
            comment_ids: 评论ID列表
            operator_id: 操作者ID

        Returns:
            操作结果
        """
        from shared.models.comment import Comment

        if not comment_ids:
            return {'success': False, 'message': '没有选择任何评论'}

        try:
            result = await self.db.execute(
                delete(Comment).where(
                    Comment.id.in_(comment_ids)
                )
            )

            deleted_count = result.rowcount
            await self.db.commit()

            # 记录操作日志
            self._log_operation(
                'batch_delete_comments',
                {'comment_ids': comment_ids, 'count': deleted_count},
                operator_id
            )

            return {
                'success': True,
                'message': f'成功删除 {deleted_count} 条评论',
                'deleted_count': deleted_count,
            }
        except Exception as e:
            await self.db.rollback()
            return {
                'success': False,
                'message': f'删除失败: {str(e)}',
            }

    async def batch_update_comment_status(
            self,
            comment_ids: List[int],
            status: str,
            operator_id: Optional[int] = None
    ) -> Dict:
        """
        批量更新评论状态

        Args:
            comment_ids: 评论ID列表
            status: 新状态 (approved, pending, spam)
            operator_id: 操作者ID

        Returns:
            操作结果
        """
        from shared.models.comment import Comment

        if not comment_ids:
            return {'success': False, 'message': '没有选择任何评论'}

        valid_statuses = ['approved', 'pending', 'spam']
        if status not in valid_statuses:
            return {'success': False, 'message': f'无效的状态: {status}'}

        try:
            result = await self.db.execute(
                update(Comment)
                .where(Comment.id.in_(comment_ids))
                .values(
                    status=status,
                    updated_at=datetime.now()
                )
            )

            updated_count = result.rowcount
            await self.db.commit()

            # 记录操作日志
            self._log_operation(
                'batch_update_comment_status',
                {'comment_ids': comment_ids, 'status': status, 'count': updated_count},
                operator_id
            )

            return {
                'success': True,
                'message': f'成功更新 {updated_count} 条评论状态为 {status}',
                'updated_count': updated_count,
            }
        except Exception as e:
            await self.db.rollback()
            return {
                'success': False,
                'message': f'更新失败: {str(e)}',
            }

    async def batch_delete_products(
            self,
            product_ids: List[int],
            operator_id: Optional[int] = None,
            user=None
    ) -> Dict:
        """
        批量删除商品

        Args:
            product_ids: 商品ID列表
            operator_id: 操作者ID
            user: 当前用户对象（用于权限检查）

        Returns:
            操作结果
        """
        from shared.models.product import Product
        from shared.models.cart_item import CartItem

        if not product_ids:
            return {'success': False, 'message': '没有选择任何商品'}

        try:
            # 先删除相关购物车项
            await self.db.execute(
                delete(CartItem).where(
                    CartItem.product_id.in_(product_ids)
                )
            )

            # 删除商品
            result = await self.db.execute(
                delete(Product).where(
                    Product.id.in_(product_ids)
                )
            )

            deleted_count = result.rowcount
            await self.db.commit()

            # 记录操作日志
            self._log_operation(
                'batch_delete_products',
                {'product_ids': product_ids, 'count': deleted_count},
                operator_id
            )

            return {
                'success': True,
                'message': f'成功删除 {deleted_count} 个商品',
                'deleted_count': deleted_count,
            }
        except Exception as e:
            await self.db.rollback()
            return {
                'success': False,
                'message': f'删除失败: {str(e)}',
            }

    async def batch_update_product_price(
            self,
            product_ids: List[int],
            price: float,
            original_price: Optional[float] = None,
            operator_id: Optional[int] = None,
            user=None
    ) -> Dict:
        """
        批量更新商品价格

        Args:
            product_ids: 商品ID列表
            price: 新价格
            original_price: 原价（可选）
            operator_id: 操作者ID
            user: 当前用户对象（用于权限检查）

        Returns:
            操作结果
        """
        from shared.models.product import Product
        from decimal import Decimal

        if not product_ids:
            return {'success': False, 'message': '没有选择任何商品'}

        if price < 0:
            return {'success': False, 'message': '价格不能为负数'}

        try:
            update_values = {
                'price': Decimal(str(price)),
                'updated_at': datetime.now()
            }

            if original_price is not None:
                update_values['original_price'] = Decimal(str(original_price))

            result = await self.db.execute(
                update(Product)
                .where(Product.id.in_(product_ids))
                .values(**update_values)
            )

            updated_count = result.rowcount
            await self.db.commit()

            # 记录操作日志
            self._log_operation(
                'batch_update_product_price',
                {'product_ids': product_ids, 'price': price, 'count': updated_count},
                operator_id
            )

            return {
                'success': True,
                'message': f'成功更新 {updated_count} 个商品价格',
                'updated_count': updated_count,
            }
        except Exception as e:
            await self.db.rollback()
            return {
                'success': False,
                'message': f'更新价格失败: {str(e)}',
            }

    async def batch_update_product_stock(
            self,
            product_ids: List[int],
            stock: int,
            operation: str = 'set',
            operator_id: Optional[int] = None,
            user=None
    ) -> Dict:
        """
        批量更新商品库存

        Args:
            product_ids: 商品ID列表
            stock: 库存数量
            operation: 操作类型 (set=设置, add=增加, subtract=减少)
            operator_id: 操作者ID
            user: 当前用户对象（用于权限检查）

        Returns:
            操作结果
        """
        from shared.models.product import Product
        from sqlalchemy import select

        if not product_ids:
            return {'success': False, 'message': '没有选择任何商品'}

        if operation not in ['set', 'add', 'subtract']:
            return {'success': False, 'message': f'无效的操作类型: {operation}'}

        try:
            updated_count = 0

            if operation == 'set':
                # 直接设置库存
                result = await self.db.execute(
                    update(Product)
                    .where(Product.id.in_(product_ids))
                    .values(
                        stock=stock,
                        updated_at=datetime.now()
                    )
                )
                updated_count = result.rowcount
            else:
                # 需要逐个处理增加或减少
                for product_id in product_ids:
                    stmt = select(Product).where(Product.id == product_id)
                    result = await self.db.execute(stmt)
                    product = result.scalar_one_or_none()

                    if product:
                        if operation == 'add':
                            new_stock = product.stock + stock
                        else:  # subtract
                            new_stock = max(0, product.stock - stock)

                        await self.db.execute(
                            update(Product)
                            .where(Product.id == product_id)
                            .values(
                                stock=new_stock,
                                updated_at=datetime.now()
                            )
                        )
                        updated_count += 1

            await self.db.commit()

            # 记录操作日志
            self._log_operation(
                'batch_update_product_stock',
                {'product_ids': product_ids, 'stock': stock, 'operation': operation, 'count': updated_count},
                operator_id
            )

            return {
                'success': True,
                'message': f'成功更新 {updated_count} 个商品库存',
                'updated_count': updated_count,
            }
        except Exception as e:
            await self.db.rollback()
            return {
                'success': False,
                'message': f'更新库存失败: {str(e)}',
            }

    async def batch_update_product_status(
            self,
            product_ids: List[int],
            status: str,
            operator_id: Optional[int] = None,
            user=None
    ) -> Dict:
        """
        批量更新商品状态

        Args:
            product_ids: 商品ID列表
            status: 新状态 (active/inactive)
            operator_id: 操作者ID
            user: 当前用户对象（用于权限检查）

        Returns:
            操作结果
        """
        from shared.models.product import Product

        if not product_ids:
            return {'success': False, 'message': '没有选择任何商品'}

        valid_statuses = ['active', 'inactive']
        if status not in valid_statuses:
            return {'success': False, 'message': f'无效的状态: {status}'}

        try:
            is_active = (status == 'active')

            result = await self.db.execute(
                update(Product)
                .where(Product.id.in_(product_ids))
                .values(
                    is_active=is_active,
                    updated_at=datetime.now()
                )
            )

            updated_count = result.rowcount
            await self.db.commit()

            # 记录操作日志
            self._log_operation(
                'batch_update_product_status',
                {'product_ids': product_ids, 'status': status, 'count': updated_count},
                operator_id
            )

            return {
                'success': True,
                'message': f'成功更新 {updated_count} 个商品状态为 {status}',
                'updated_count': updated_count,
            }
        except Exception as e:
            await self.db.rollback()
            return {
                'success': False,
                'message': f'更新状态失败: {str(e)}',
            }

    async def batch_update_categories_sort(
            self,
            category_orders: List[Dict[str, int]],
            operator_id: Optional[int] = None
    ) -> Dict:
        """
        批量更新分类排序

        Args:
            category_orders: 分类排序列表，每个元素包含 {id: 分类ID, sort_order: 排序值}
            operator_id: 操作者ID

        Returns:
            操作结果
        """
        from shared.models.category import Category

        if not category_orders:
            return {'success': False, 'message': '没有提供排序数据'}

        try:
            updated_count = 0

            for item in category_orders:
                category_id = item.get('id')
                sort_order = item.get('sort_order')

                if category_id is None or sort_order is None:
                    continue

                result = await self.db.execute(
                    update(Category)
                    .where(Category.id == category_id)
                    .values(
                        sort_order=sort_order,
                        updated_at=datetime.now()
                    )
                )

                if result.rowcount > 0:
                    updated_count += 1

            await self.db.commit()

            # 记录操作日志
            self._log_operation(
                'batch_update_categories_sort',
                {'category_orders': category_orders, 'count': updated_count},
                operator_id
            )

            return {
                'success': True,
                'message': f'成功更新 {updated_count} 个分类的排序',
                'updated_count': updated_count,
            }
        except Exception as e:
            await self.db.rollback()
            return {
                'success': False,
                'message': f'更新排序失败: {str(e)}',
            }

    async def batch_update_articles_sort(
            self,
            article_orders: List[Dict[str, int]],
            operator_id: Optional[int] = None
    ) -> Dict:
        """
        批量更新文章排序

        Args:
            article_orders: 文章排序列表，每个元素包含 {id: 文章ID, sort_order: 排序值}
            operator_id: 操作者ID

        Returns:
            操作结果
        """
        from shared.models.article import Article

        if not article_orders:
            return {'success': False, 'message': '没有提供排序数据'}

        try:
            updated_count = 0

            for item in article_orders:
                article_id = item.get('id')
                sort_order = item.get('sort_order')

                if article_id is None or sort_order is None:
                    continue

                result = await self.db.execute(
                    update(Article)
                    .where(Article.id == article_id)
                    .values(
                        sort_order=sort_order,
                        updated_at=datetime.now()
                    )
                )

                if result.rowcount > 0:
                    updated_count += 1

            await self.db.commit()

            # 记录操作日志
            self._log_operation(
                'batch_update_articles_sort',
                {'article_orders': article_orders, 'count': updated_count},
                operator_id
            )

            return {
                'success': True,
                'message': f'成功更新 {updated_count} 个文章的排序',
                'updated_count': updated_count,
            }
        except Exception as e:
            await self.db.rollback()
            return {
                'success': False,
                'message': f'更新排序失败: {str(e)}',
            }

    def _log_operation(
            self,
            operation_type: str,
            details: Dict,
            operator_id: Optional[int] = None
    ):
        """
        记录操作日志

        Args:
            operation_type: 操作类型
            details: 操作详情
            operator_id: 操作者ID
        """
        log_entry = {
            'operation': operation_type,
            'details': details,
            'operator_id': operator_id,
            'timestamp': datetime.now().isoformat(),
        }

        self.operation_log.append(log_entry)

        # Log to database or file in production
        # Example: await db.execute(insert(OperationLog).values(**log_entry))
        logger.info(f"[Batch Operation] {operation_type} - {details}")

    def get_operation_log(self) -> List[Dict]:
        """
        获取操作日志

        Returns:
            操作日志列表
        """
        return self.operation_log.copy()


# 工厂函数
def create_batch_service(db: AsyncSession) -> BatchOperationService:
    return BatchOperationService(db)
