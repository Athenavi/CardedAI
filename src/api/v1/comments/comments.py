"""
评论管理API - 包含垃圾评论过滤
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.comment import Comment
from shared.services.comments.comment_manager import comment_like_service, comment_notification_service
from shared.services.notifications.webhook_service import webhook_service
from shared.services.plugins.plugin_manager.init import trigger_plugin_event
from shared.services.security.spam_filter_manager import spam_filter
from shared.services.users.user_manager import gravatar_service
from src.api.v1.core.responses import ApiResponse
from src.auth import jwt_required_dependency as jwt_required
from src.auth.auth_deps import jwt_optional_dependency
from src.extensions import get_async_db_session as get_async_db

router = APIRouter(tags=["comments"])


class CreateCommentRequest(BaseModel):
    """创建评论请求"""
    article_id: int
    content: str
    parent_id: Optional[int] = None  # 回复评论时使用

    # 访客信息（未登录用户必填）
    author_name: Optional[str] = None
    author_email: Optional[str] = None
    author_url: Optional[str] = None

    # 蜜罐字段(前端隐藏,正常用户不会填写)
    website_url: Optional[str] = None
    phone_field: Optional[str] = None
    comment_extra: Optional[str] = None

    # 页面加载时间戳(用于检测快速提交)
    page_load_time: Optional[float] = None


class UpdateCommentRequest(BaseModel):
    """更新评论请求"""
    content: str


@router.post("/")
async def create_comment(
        request: Request,
        comment_data: CreateCommentRequest,
        db: AsyncSession = Depends(get_async_db),
        current_user=Depends(jwt_optional_dependency)
):
    """
    创建新评论（支持登录用户和访客）
    
    自动进行垃圾评论检测:
    - 低风险: 直接发布
    - 中风险: 标记为待审核
    - 高风险: 直接拒绝
    """
    try:
        from sqlalchemy import select
        import json

        # 1. 检查文章是否存在
        from shared.models.article import Article
        article_query = select(Article).where(Article.id == comment_data.article_id)
        article_result = await db.execute(article_query)
        article = article_result.scalar_one_or_none()

        if not article:
            return ApiResponse(success=False, error="文章不存在")

        # 2. 获取用户IP和User-Agent
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")

        # 3. 收集蜜罐字段数据
        honeypot_data = {
            'website_url': comment_data.website_url or '',
            'phone_field': comment_data.phone_field or '',
            'comment_extra': comment_data.comment_extra or ''
        }

        # 4. 执行垃圾评论检测(增强版)
        spam_check = spam_filter.check_spam(
            content=comment_data.content,
            user_id=current_user.id if current_user else None,
            ip_address=ip_address,
            user_agent=user_agent,
            honeypot_data=honeypot_data,
            submit_time=comment_data.page_load_time
        )

        # 5. 敏感词过滤检查
        from shared.services.security.sensitive_word_service import sensitive_word_service
        sensitive_check = await sensitive_word_service.check_content(comment_data.content)

        # 如果包含需要拦截的敏感词，直接拒绝
        if sensitive_check['has_sensitive'] and 'block' in sensitive_check['actions']:
            return ApiResponse(
                success=False,
                error="评论包含违规内容，已拒绝",
                data={
                    "sensitive_words_detected": True,
                    "words_found": len(sensitive_check['words_found'])
                }
            )

        # 如果有警告级别的敏感词，标记为待审核
        if sensitive_check['has_sensitive'] and 'warn' in sensitive_check['actions']:
            is_approved = False  # 强制待审核
        else:
            # 根据垃圾检测结果决定审核状态
            is_approved = spam_check['action'] == 'approve'

        # 6. 如果内容需要替换敏感词，进行替换
        filtered_content = comment_data.content
        if sensitive_check['has_sensitive'] and 'replace' in sensitive_check['actions']:
            filtered_content, _ = await sensitive_word_service.filter_content(comment_data.content)

        # 5. 根据检测结果决定操作
        if spam_check['action'] == 'reject':
            return ApiResponse(
                success=False,
                error="评论被识别为垃圾内容，已拒绝",
                data={
                    "spam_detected": True,
                    "confidence": spam_check['confidence'],
                    "reasons": spam_check['reasons']
                }
            )

        # 7. 创建评论
        new_comment = Comment(
            article_id=comment_data.article_id,
            user_id=current_user.id if current_user else None,
            parent_id=comment_data.parent_id,
            content=filtered_content,  # 使用过滤后的内容
            is_approved=is_approved,
            likes=0,
            # 访客信息
            author_name=comment_data.author_name,
            author_email=comment_data.author_email,
            author_url=comment_data.author_url,
            author_ip=ip_address,
            user_agent=user_agent,
            # 垃圾检测信息
            spam_score=spam_check['confidence'],
            spam_reasons=json.dumps(spam_check['reasons']) if spam_check['reasons'] else None
        )

        db.add(new_comment)
        await db.commit()
        await db.refresh(new_comment)

        # 8. 发送通知(如果评论通过审核)
        if is_approved:
            try:
                from shared.models.article import Article
                from shared.models.user import User
                from urllib.parse import urljoin
                import os

                article_query = select(Article).where(Article.id == comment_data.article_id)
                article_result = await db.execute(article_query)
                article = article_result.scalar_one_or_none()

                # 触发关注插件的评论事件
                try:
                    commenter_id = current_user.id if current_user else None
                    if commenter_id and article:
                        await trigger_plugin_event('comment_created', {
                            'user_id': str(commenter_id),
                            'article_id': article.id,
                            'article_title': article.title,
                            'content': new_comment.content,
                        })
                except Exception as plugin_err:
                    print(f"Trigger plugin event failed: {plugin_err}")

                # 获取文章作者信息
                if article and article.user:
                    author_query = select(User).where(User.id == article.user)
                    author_result = await db.execute(author_query)
                    article_author = author_result.scalar_one_or_none()

                    if article_author and article_author.email:
                        # 获取评论者信息
                        commenter_name = current_user.username if current_user else comment_data.author_name or '访客'

                        # 构建URL
                        base_url = os.getenv('SITE_URL', 'http://localhost:3000')
                        article_url = urljoin(base_url, f"/articles/detail?id={article.id}")
                        comment_url = urljoin(base_url, f"/articles/detail?id={article.id}#comment-{new_comment.id}")

                        # 通知文章作者
                        comment_notification_service.notify_article_author(
                            author_email=article_author.email,
                            author_name=article_author.username,
                            article_title=article.title,
                            article_url=article_url,
                            commenter_name=commenter_name,
                            comment_content=new_comment.content,
                            comment_url=comment_url,
                            article_id=article.id,
                            author_user_id=article_author.id
                        )

                # 如果有父评论，通知被回复者
                if new_comment.parent_id:
                    parent_query = select(Comment).where(Comment.id == new_comment.parent_id)
                    parent_result = await db.execute(parent_query)
                    parent_comment = parent_result.scalar_one_or_none()

                    if parent_comment and parent_comment.author_email:
                        commenter_name = current_user.username if current_user else comment_data.author_name or '访客'

                        base_url = os.getenv('SITE_URL', 'http://localhost:3000')
                        article_url = urljoin(base_url, f"/articles/detail?id={comment_data.article_id}")
                        comment_url = urljoin(base_url,
                                              f"/articles/detail?id={comment_data.article_id}#comment-{new_comment.id}")

                        # 通知被回复者
                        comment_notification_service.notify_comment_reply(
                            recipient_email=parent_comment.author_email,
                            recipient_name=parent_comment.author_name or '用户',
                            article_title=article.title if article else '文章',
                            article_url=article_url,
                            replier_name=commenter_name,
                            reply_content=new_comment.content,
                            original_comment=parent_comment.content,
                            comment_url=comment_url,
                            article_id=comment_data.article_id,
                            recipient_user_id=parent_comment.user_id
                        )

            except Exception as e:
                print(f"发送评论通知失败: {e}")
                import traceback
                traceback.print_exc()
                # 通知失败不影响评论创建

        # 8. 返回结果

        # 触发 Webhook 事件
        try:
            await webhook_service.trigger_event(
                'comment.created',
                {
                    'comment_id': new_comment.id,
                    'article_id': comment_data.article_id,
                    'author_id': current_user.id if current_user else None,
                    'author_name': current_user.username if current_user else comment_data.author_name or '访客',
                    'content_preview': new_comment.content[:200],
                    'is_approved': new_comment.is_approved,
                    'created_at': new_comment.created_at.isoformat() if new_comment.created_at else None,
                },
                db=db
            )
        except Exception as webhook_err:
            print(f"Webhook trigger failed: {webhook_err}")

        return ApiResponse(
            success=True,
            data={
                "id": new_comment.id,
                "content": new_comment.content,
                "is_approved": new_comment.is_approved,
                "created_at": new_comment.created_at.isoformat() if new_comment.created_at else None,
                "spam_check": {
                    "action": spam_check['action'],
                    "confidence": spam_check['confidence'],
                    "needs_moderation": not is_approved
                }
            },
            message="评论提交成功" if is_approved else "评论已提交，等待审核"
        )

    except Exception as e:
        await db.rollback()
        import traceback
        print(f"创建评论失败: {e}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=f"创建评论失败: {str(e)}")


@router.get("/comments/{comment_id}")
async def get_comment(
        comment_id: int,
        db: AsyncSession = Depends(get_async_db)
):
    """获取单条评论详情"""
    try:
        from sqlalchemy import select

        query = select(Comment).where(Comment.id == comment_id)
        result = await db.execute(query)
        comment = result.scalar_one_or_none()

        if not comment:
            return ApiResponse(success=False, error="评论不存在")

        return ApiResponse(
            success=True,
            data=comment.to_dict()
        )

    except Exception as e:
        return ApiResponse(success=False, error=f"获取评论失败: {str(e)}")


@router.get("/article/{article_id}")
async def get_article_comments(
        article_id: int,
        page: int = 1,
        per_page: int = 20,
        sort_by: str = 'latest',  # latest | oldest | popular
        order: str = 'desc',  # asc | desc (仅用于兼容)
        tree: bool = False,  # 是否返回树形结构
        db: AsyncSession = Depends(get_async_db)
):
    """获取文章的评论
    
    Args:
        article_id: 文章ID
        page: 页码
        per_page: 每页数量
        sort_by: 排序方式 (latest-最新, oldest-最早, popular-最热)
        order: 排序方向 (asc-升序, desc-降序) - 仅用于向后兼容
        tree: 是否返回树形结构（嵌套回复）
    """
    try:
        from sqlalchemy import select, func
        from shared.models.user import User

        # 验证排序参数
        valid_sort_fields = ['latest', 'oldest', 'popular', 'created_at', 'likes']
        if sort_by not in valid_sort_fields:
            sort_by = 'latest'

        # 映射排序字段
        sort_field_map = {
            'latest': Comment.created_at,
            'oldest': Comment.created_at,
            'popular': Comment.likes,
            'created_at': Comment.created_at,
            'likes': Comment.likes
        }
        sort_field = sort_field_map.get(sort_by, Comment.created_at)

        # 确定排序方向
        if sort_by == 'oldest':
            sort_expression = sort_field.asc()
        elif sort_by == 'popular':
            sort_expression = sort_field.desc()
        else:  # latest
            sort_expression = sort_field.desc()

        # 查询已审核的评论
        query = (
            select(Comment)
            .where(Comment.article_id == article_id)
            .where(Comment.is_approved == True)
            .order_by(sort_expression)
            .offset((page - 1) * per_page)
            .limit(per_page)
        )

        result = await db.execute(query)
        comments = result.scalars().all()

        # 统计总数
        count_query = (
            select(func.count(Comment.id))
            .where(Comment.article_id == article_id)
            .where(Comment.is_approved == True)
        )
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # 为每个评论添加用户信息和头像
        comments_data = []
        for comment in comments:
            comment_dict = comment.to_dict()

            # 获取用户信息
            user_query = select(User).where(User.id == comment.user_id)
            user_result = await db.execute(user_query)
            user = user_result.scalar_one_or_none()

            if user:
                comment_dict['username'] = user.username
                comment_dict['avatar_url'] = gravatar_service.get_avatar_url(
                    email=user.email if hasattr(user, 'email') else '',
                    size=80,
                    default='identicon'
                )
            else:
                comment_dict['username'] = 'Unknown'
                comment_dict['avatar_url'] = gravatar_service.get_avatar_url(
                    email='',
                    size=80,
                    default='mp'
                )

            comments_data.append(comment_dict)

        # 如果请求树形结构，构建树
        if tree:
            tree_data = _build_comment_tree(comments_data)
            return ApiResponse(
                success=True,
                data={
                    "comments": tree_data,
                    "total": total,
                    "page": page,
                    "per_page": per_page,
                    "total_pages": (total + per_page - 1) // per_page,
                    "sort_by": sort_by,
                    "tree": True
                }
            )
        else:
            return ApiResponse(
                success=True,
                data={
                    "comments": comments_data,
                    "total": total,
                    "page": page,
                    "per_page": per_page,
                    "total_pages": (total + per_page - 1) // per_page,
                    "sort_by": sort_by,
                    "order": order,
                    "tree": False
                }
            )

    except Exception as e:
        return ApiResponse(success=False, error=f"获取评论列表失败: {str(e)}")


@router.put("/{comment_id}")
async def update_comment(
        comment_id: int,
        update_data: UpdateCommentRequest,
        db: AsyncSession = Depends(get_async_db),
        current_user=Depends(jwt_required)
):
    """更新评论(仅作者或管理员)"""
    try:
        from sqlalchemy import select

        query = select(Comment).where(Comment.id == comment_id)
        result = await db.execute(query)
        comment = result.scalar_one_or_none()

        if not comment:
            return ApiResponse(success=False, error="评论不存在")

        # 检查权限
        if comment.user_id != current_user.id and not getattr(current_user, 'is_admin', False):
            return ApiResponse(success=False, error="无权修改此评论")

        # 更新内容
        comment.content = update_data.content
        await db.commit()

        return ApiResponse(
            success=True,
            data=comment.to_dict(),
            message="评论更新成功"
        )

    except Exception as e:
        await db.rollback()
        return ApiResponse(success=False, error=f"更新评论失败: {str(e)}")


@router.delete("/{comment_id}")
async def delete_comment(
        comment_id: int,
        db: AsyncSession = Depends(get_async_db),
        current_user=Depends(jwt_required)
):
    """删除评论(仅作者或管理员)"""
    try:
        from sqlalchemy import select

        query = select(Comment).where(Comment.id == comment_id)
        result = await db.execute(query)
        comment = result.scalar_one_or_none()

        if not comment:
            return ApiResponse(success=False, error="评论不存在")

        # 检查权限
        if comment.user_id != current_user.id and not getattr(current_user, 'is_admin', False):
            return ApiResponse(success=False, error="无权删除此评论")

        await db.delete(comment)
        await db.commit()

        # 触发 Webhook 事件
        try:
            await webhook_service.trigger_event(
                'comment.deleted',
                {
                    'comment_id': comment_id,
                    'article_id': comment.article_id,
                    'author_id': comment.user_id,
                    'deleted_at': datetime.now().isoformat(),
                },
                db=db
            )
        except Exception as webhook_err:
            print(f"Webhook trigger failed: {webhook_err}")

        return ApiResponse(
            success=True,
            message="评论删除成功"
        )

    except Exception as e:
        await db.rollback()
        return ApiResponse(success=False, error=f"删除评论失败: {str(e)}")


# ==================== 管理员评论审核API ====================

@router.get("/pending")
async def get_pending_comments(
        page: int = 1,
        per_page: int = 20,
        db: AsyncSession = Depends(get_async_db),
        current_user=Depends(jwt_required)
):
    """获取待审核的评论(仅管理员)"""
    try:
        from sqlalchemy import select, func

        # 检查是否为管理员
        if not getattr(current_user, 'is_admin', False):
            return ApiResponse(success=False, error="需要管理员权限")

        # 查询待审核评论
        query = (
            select(Comment)
            .where(Comment.is_approved == False)
            .order_by(Comment.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )

        result = await db.execute(query)
        comments = result.scalars().all()

        # 统计总数
        count_query = (
            select(func.count(Comment.id))
            .where(Comment.is_approved == False)
        )
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        return ApiResponse(
            success=True,
            data={
                "comments": [c.to_dict() for c in comments],
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page
            }
        )

    except Exception as e:
        return ApiResponse(success=False, error=f"获取待审核评论失败: {str(e)}")


@router.post("/{comment_id}/approve")
async def approve_comment(
        comment_id: int,
        db: AsyncSession = Depends(get_async_db),
        current_user=Depends(jwt_required)
):
    """审核通过评论(仅管理员)"""
    try:
        from sqlalchemy import select
        from datetime import datetime, timezone

        # 检查权限
        if not getattr(current_user, 'is_admin', False) and not getattr(current_user, 'is_superuser', False):
            return ApiResponse(success=False, error="需要管理员权限")

        query = select(Comment).where(Comment.id == comment_id)
        result = await db.execute(query)
        comment = result.scalar_one_or_none()

        if not comment:
            return ApiResponse(success=False, error="评论不存在")

        comment.is_approved = True
        comment.approved_by = current_user.id
        comment.approved_at = datetime.now(timezone.utc)
        await db.commit()

        # 发送审核通过通知
        try:
            from shared.models.article import Article
            from shared.models.user import User
            from urllib.parse import urljoin
            import os

            # 获取文章信息
            article_query = select(Article).where(Article.id == comment.article_id)
            article_result = await db.execute(article_query)
            article = article_result.scalar_one_or_none()

            if article and comment.author_email:
                base_url = os.getenv('SITE_URL', 'http://localhost:3000')
                article_url = urljoin(base_url, f"/articles/detail?id={article.id}")

                # 通知评论者审核通过
                comment_notification_service.notify_approval_result(
                    recipient_email=comment.author_email,
                    recipient_name=comment.author_name or '用户',
                    article_title=article.title,
                    article_url=article_url,
                    is_approved=True,
                    comment_content=comment.content,
                    article_id=article.id,
                    recipient_user_id=comment.user_id
                )
        except Exception as e:
            print(f"发送审核通知失败: {e}")
            # 通知失败不影响审核

        return ApiResponse(
            success=True,
            message="评论已通过审核"
        )

    except Exception as e:
        await db.rollback()
        return ApiResponse(success=False, error=f"审核评论失败: {str(e)}")


@router.post("/{comment_id}/reject")
async def reject_comment(
        comment_id: int,
        db: AsyncSession = Depends(get_async_db),
        current_user=Depends(jwt_required)
):
    """拒绝评论(仅管理员)"""
    try:
        from sqlalchemy import select

        # 检查权限
        if not getattr(current_user, 'is_admin', False):
            return ApiResponse(success=False, error="需要管理员权限")

        query = select(Comment).where(Comment.id == comment_id)
        result = await db.execute(query)
        comment = result.scalar_one_or_none()

        if not comment:
            return ApiResponse(success=False, error="评论不存在")

        await db.delete(comment)
        await db.commit()

        return ApiResponse(
            success=True,
            message="评论已拒绝并删除"
        )

    except Exception as e:
        await db.rollback()
        return ApiResponse(success=False, error=f"拒绝评论失败: {str(e)}")


@router.get("/spam-filter/stats")
async def get_spam_filter_stats():
    """获取垃圾过滤器统计信息"""
    try:
        stats = spam_filter.get_stats()
        return ApiResponse(
            success=True,
            data=stats
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取统计信息失败: {str(e)}")


@router.post("/admin/spam-filter/blacklist")
async def add_ip_to_blacklist(
        request: Request,
        current_user=Depends(jwt_required)
):
    """添加IP到黑名单(仅管理员)"""
    try:
        # 检查权限
        if not getattr(current_user, 'is_admin', False) and not getattr(current_user, 'is_superuser', False):
            return ApiResponse(success=False, error="需要管理员权限")

        body = await request.json()
        ip_address = body.get('ip_address', '').strip()

        if not ip_address:
            return ApiResponse(success=False, error="请提供IP地址")

        spam_filter.add_ip_to_blacklist(ip_address)

        return ApiResponse(
            success=True,
            message=f"IP {ip_address} 已添加到黑名单"
        )

    except Exception as e:
        return ApiResponse(success=False, error=f"添加失败: {str(e)}")


@router.delete("/admin/spam-filter/blacklist/{ip_address}")
async def remove_ip_from_blacklist(
        ip_address: str,
        current_user=Depends(jwt_required)
):
    """从黑名单移除IP(仅管理员)"""
    try:
        # 检查权限
        if not getattr(current_user, 'is_admin', False) and not getattr(current_user, 'is_superuser', False):
            return ApiResponse(success=False, error="需要管理员权限")

        spam_filter.remove_ip_from_blacklist(ip_address)

        return ApiResponse(
            success=True,
            message=f"IP {ip_address} 已从黑名单移除"
        )

    except Exception as e:
        return ApiResponse(success=False, error=f"移除失败: {str(e)}")


@router.post("/admin/spam-filter/whitelist")
async def add_ip_to_whitelist(
        request: Request,
        current_user=Depends(jwt_required)
):
    """添加IP到白名单(仅管理员)"""
    try:
        # 检查权限
        if not getattr(current_user, 'is_admin', False) and not getattr(current_user, 'is_superuser', False):
            return ApiResponse(success=False, error="需要管理员权限")

        body = await request.json()
        ip_address = body.get('ip_address', '').strip()

        if not ip_address:
            return ApiResponse(success=False, error="请提供IP地址")

        spam_filter.add_ip_to_whitelist(ip_address)

        return ApiResponse(
            success=True,
            message=f"IP {ip_address} 已添加到白名单"
        )

    except Exception as e:
        return ApiResponse(success=False, error=f"添加失败: {str(e)}")


@router.delete("/admin/spam-filter/whitelist/{ip_address}")
async def remove_ip_from_whitelist(
        ip_address: str,
        current_user=Depends(jwt_required)
):
    """从白名单移除IP(仅管理员)"""
    try:
        # 检查权限
        if not getattr(current_user, 'is_admin', False) and not getattr(current_user, 'is_superuser', False):
            return ApiResponse(success=False, error="需要管理员权限")

        spam_filter.remove_ip_from_whitelist(ip_address)

        return ApiResponse(
            success=True,
            message=f"IP {ip_address} 已从白名单移除"
        )

    except Exception as e:
        return ApiResponse(success=False, error=f"移除失败: {str(e)}")


@router.put("/admin/spam-filter/config")
async def update_spam_filter_config(
        request: Request,
        current_user=Depends(jwt_required)
):
    """更新垃圾过滤器配置(仅管理员)"""
    try:
        # 检查权限
        if not getattr(current_user, 'is_admin', False) and not getattr(current_user, 'is_superuser', False):
            return ApiResponse(success=False, error="需要管理员权限")

        body = await request.json()
        config = body.get('config', {})

        success = spam_filter.update_config(config)

        if success:
            return ApiResponse(
                success=True,
                message="配置更新成功",
                data=spam_filter.get_stats()
            )
        else:
            return ApiResponse(success=False, error="配置更新失败")

    except Exception as e:
        return ApiResponse(success=False, error=f"更新配置失败: {str(e)}")


@router.post("/{comment_id}/like")
async def like_comment(
        comment_id: int,
        request: Request,
        db: AsyncSession = Depends(get_async_db),
        current_user=Depends(jwt_required)
):
    """
    点赞/取消点赞评论（增强版）
    
    支持：
    - 首次点赞
    - 取消点赞
    - 从反对改为点赞
    
    Args:
        comment_id: 评论ID
    """
    try:
        from shared.models.comment_vote import CommentVote
        from sqlalchemy import select
        from datetime import datetime

        # 检查评论是否存在
        stmt = select(Comment).where(Comment.id == comment_id)
        result = await db.execute(stmt)
        comment = result.scalar_one_or_none()

        if not comment:
            return ApiResponse(success=False, error="评论不存在")

        # 检查是否已经投票
        stmt = select(CommentVote).where(
            CommentVote.comment_id == comment_id,
            CommentVote.user == current_user.id
        )
        result = await db.execute(stmt)
        existing_vote = result.scalar_one_or_none()

        if existing_vote:
            if existing_vote.vote_type == 1:
                # 已经点赞，取消点赞
                await db.delete(existing_vote)
                comment.likes = max(0, comment.likes - 1)
                action = 'unliked'
                message = '已取消点赞'
            else:
                # 之前是反对，改为点赞
                existing_vote.vote_type = 1
                comment.likes += 1
                action = 'liked'
                message = '点赞成功'
        else:
            # 新建点赞
            vote = CommentVote(
                comment_id=comment_id,
                user=current_user.id,
                vote_type=1,
                ip_address=request.client.host if request.client else None,
                created_at=datetime.now()
            )
            db.add(vote)
            comment.likes += 1
            action = 'liked'
            message = '点赞成功'

        await db.commit()
        await db.refresh(comment)

        return ApiResponse(
            success=True,
            data={
                'action': action,
                'likes': comment.likes,
                'vote_type': 1 if action == 'liked' else None
            },
            message=message
        )

    except Exception as e:
        await db.rollback()
        return ApiResponse(success=False, error=f"操作失败: {str(e)}")


@router.post("/{comment_id}/dislike")
async def dislike_comment(
        comment_id: int,
        request: Request,
        db: AsyncSession = Depends(get_async_db),
        current_user=Depends(jwt_required)
):
    """
    反对/取消反对评论
    
    支持：
    - 首次反对
    - 取消反对
    - 从点赞改为反对
    
    Args:
        comment_id: 评论ID
    """
    try:
        from shared.models.comment_vote import CommentVote
        from sqlalchemy import select
        from datetime import datetime

        # 检查评论是否存在
        stmt = select(Comment).where(Comment.id == comment_id)
        result = await db.execute(stmt)
        comment = result.scalar_one_or_none()

        if not comment:
            return ApiResponse(success=False, error="评论不存在")

        # 检查是否已经投票
        stmt = select(CommentVote).where(
            CommentVote.comment_id == comment_id,
            CommentVote.user == current_user.id
        )
        result = await db.execute(stmt)
        existing_vote = result.scalar_one_or_none()

        if existing_vote:
            if existing_vote.vote_type == -1:
                # 已经反对，取消反对
                await db.delete(existing_vote)
                action = 'undisliked'
                message = '已取消反对'
            else:
                # 之前是点赞，改为反对
                existing_vote.vote_type = -1
                comment.likes = max(0, comment.likes - 1)
                action = 'disliked'
                message = '已反对'
        else:
            # 新建反对
            vote = CommentVote(
                comment_id=comment_id,
                user=current_user.id,
                vote_type=-1,
                ip_address=request.client.host if request.client else None,
                created_at=datetime.now()
            )
            db.add(vote)
            comment.likes = max(0, comment.likes - 1)
            action = 'disliked'
            message = '已反对'

        await db.commit()
        await db.refresh(comment)

        return ApiResponse(
            success=True,
            data={
                'action': action,
                'likes': comment.likes,
                'vote_type': -1 if action == 'disliked' else None
            },
            message=message
        )

    except Exception as e:
        await db.rollback()
        return ApiResponse(success=False, error=f"操作失败: {str(e)}")


@router.get("/{comment_id}/likes")
async def get_comment_likes(
        comment_id: int,
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取评论的点赞数
    
    Args:
        comment_id: 评论ID
    """
    try:
        result = await comment_like_service.get_comment_likes(
            db=db,
            comment_id=comment_id
        )

        if result['success']:
            return ApiResponse(
                success=True,
                data=result
            )
        else:
            return ApiResponse(success=False, error=result['error'])

    except Exception as e:
        return ApiResponse(success=False, error=f"获取失败: {str(e)}")


@router.get("/{comment_id}/vote")
async def get_user_vote(
        comment_id: int,
        db: AsyncSession = Depends(get_async_db),
        current_user=Depends(jwt_required)
):
    """
    获取用户对评论的投票状态
    
    Args:
        comment_id: 评论ID
        
    Returns:
        vote_type: 1 (赞) | -1 (踩) | null
    """
    try:
        from shared.models.comment_vote import CommentVote
        from sqlalchemy import select

        stmt = select(CommentVote).where(
            CommentVote.comment_id == comment_id,
            CommentVote.user == current_user.id
        )
        result = await db.execute(stmt)
        vote = result.scalar_one_or_none()

        vote_type = vote.vote_type if vote else None

        return ApiResponse(
            success=True,
            data={
                "comment_id": comment_id,
                "vote_type": vote_type
            }
        )

    except Exception as e:
        return ApiResponse(success=False, error=f"获取失败: {str(e)}")


@router.post("/{comment_id}/notify-reply")
async def notify_comment_reply(
        comment_id: int,
        db: AsyncSession = Depends(get_async_db),
        current_user=Depends(jwt_required)
):
    """
    通知评论被回复（通常在创建回复评论后调用）
    
    Args:
        comment_id: 新评论ID
        
    Returns:
        通知结果
    """
    try:
        from shared.models.notification import Notification
        from sqlalchemy import select

        # 获取新评论
        stmt = select(Comment).where(Comment.id == comment_id)
        result = await db.execute(stmt)
        new_comment = result.scalar_one_or_none()

        if not new_comment or not new_comment.parent_id:
            return ApiResponse(success=False, error="不是回复评论")

        # 获取父评论
        stmt = select(Comment).where(Comment.id == new_comment.parent_id)
        result = await db.execute(stmt)
        parent_comment = result.scalar_one_or_none()

        if not parent_comment or not parent_comment.user_id:
            return ApiResponse(success=False, error="父评论没有用户")

        # 如果是自己回复自己，不发送通知
        if parent_comment.user_id == new_comment.user_id:
            return ApiResponse(success=False, error="自己回复自己")

        # 创建通知
        notification = Notification(
            user_id=parent_comment.user_id,
            type='comment_reply',
            title='有人回复了你的评论',
            content=f'{new_comment.author_name or "匿名用户"} 回复了你的评论',
            related_id=new_comment.id,
            related_type='comment',
            is_read=False
        )

        db.add(notification)
        await db.commit()

        return ApiResponse(
            success=True,
            data={
                'notification_id': notification.id
            },
            message="通知已发送"
        )

    except Exception as e:
        await db.rollback()
        return ApiResponse(success=False, error=f"通知失败: {str(e)}")


# ==================== 辅助函数 ====================

def _build_comment_tree(comments: list) -> list:
    """
    构建评论树形结构
    
    Args:
        comments: 评论列表（字典格式）
        
    Returns:
        树形结构的评论列表
    """
    # 转换为字典并添加 children 字段
    comment_map = {}
    for comment in comments:
        comment_dict = comment.copy() if isinstance(comment, dict) else comment.to_dict()
        comment_dict['children'] = []
        comment_dict['depth'] = 0
        comment_map[comment_dict['id']] = comment_dict

    # 构建树
    root_comments = []
    for comment_dict in comment_map.values():
        parent_id = comment_dict.get('parent_id')

        if parent_id is None or parent_id not in comment_map:
            # 根评论
            root_comments.append(comment_dict)
        else:
            # 子评论，添加到父评论的 children
            parent = comment_map[parent_id]
            comment_dict['depth'] = parent['depth'] + 1
            parent['children'].append(comment_dict)

    return root_comments


@router.get("/notifications/comments")
async def get_comment_notifications(
        page: int = 1,
        per_page: int = 20,
        db: AsyncSession = Depends(get_async_db),
        current_user=Depends(jwt_required)
):
    """
    获取用户的评论相关通知
    
    Args:
        page: 页码
        per_page: 每页数量
    """
    try:
        result = await comment_notification_service.get_user_comment_notifications(
            db=db,
            user_id=current_user.id,
            page=page,
            per_page=per_page
        )

        if result['success']:
            return ApiResponse(
                success=True,
                data=result
            )
        else:
            return ApiResponse(success=False, error=result['error'])

    except Exception as e:
        return ApiResponse(success=False, error=f"获取通知失败: {str(e)}")


@router.get("/notifications/preferences")
async def get_notification_preferences(
        current_user=Depends(jwt_required)
):
    """
    获取用户的通知偏好设置
    """
    try:
        preferences = await comment_notification_service.get_user_preferences(
            user_id=current_user.id
        )

        return ApiResponse(
            success=True,
            data={
                "preferences": preferences
            }
        )

    except Exception as e:
        return ApiResponse(success=False, error=f"获取偏好失败: {str(e)}")


@router.put("/notifications/preferences")
async def update_notification_preferences(
        request: Request,
        current_user=Depends(jwt_required)
):
    """
    更新用户的通知偏好设置
    
    Body参数:
        preferences: 偏好设置字典
            - notify_on_reply: 回复时通知 (bool)
            - notify_on_new_comment: 新评论时通知 (bool)
            - email_on_reply: 回复时发送邮件 (bool)
            - email_on_new_comment: 新评论时发送邮件 (bool)
    """
    try:
        body = await request.json()
        preferences = body.get('preferences', {})

        success = await comment_notification_service.update_user_preference(
            user_id=current_user.id,
            preferences=preferences
        )

        if success:
            return ApiResponse(
                success=True,
                message="偏好设置已更新",
                data={
                    "preferences": await comment_notification_service.get_user_preferences(
                        user_id=current_user.id
                    )
                }
            )
        else:
            return ApiResponse(success=False, error="更新失败")

    except Exception as e:
        return ApiResponse(success=False, error=f"更新失败: {str(e)}")
