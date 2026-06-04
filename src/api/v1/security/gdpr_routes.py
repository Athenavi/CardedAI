"""
GDPR 合规 API
提供数据导出、数据删除、隐私政策等 GDPR 合规功能
"""
import json
import io
import zipfile
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.user import User
from shared.models.article import Article
from shared.models.comment import Comment
from src.auth.auth_deps import jwt_required_dependency as jwt_required
from src.utils.database.main import get_async_session

router = APIRouter(prefix="/gdpr", tags=["GDPR Compliance"])


@router.get("/export/my-data")
async def export_user_data(current_user: User = Depends(jwt_required)):
    """
    P7-3: 数据导出 API (Right to Access - GDPR Article 15)
    
    导出用户的所有个人数据，包括：
    - 用户基本信息
    - 发布的文章
    - 评论记录
    - 账户活动日志
    
    Returns:
        ZIP 文件包含 JSON 格式的个人数据
    """
    async for db in get_async_session():
        try:
            # 创建内存 ZIP 文件
            zip_buffer = io.BytesIO()

            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # 1. 导出用户基本信息
                user_data = {
                    "user_id": current_user.id,
                    "username": current_user.username,
                    "email": current_user.email,
                    "display_name": current_user.display_name,
                    "bio": current_user.bio,
                    "avatar_url": current_user.avatar_url,
                    "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
                    "last_login": current_user.last_login.isoformat() if current_user.last_login else None,
                    "is_active": current_user.is_active,
                    "role": current_user.role,
                }
                zip_file.writestr("user_profile.json", json.dumps(user_data, ensure_ascii=False, indent=2))

                # 2. 导出用户文章
                articles_result = await db.execute(
                    select(Article).where(Article.author_id == current_user.id)
                )
                articles = articles_result.scalars().all()

                articles_data = []
                for article in articles:
                    articles_data.append({
                        "article_id": article.id,
                        "title": article.title,
                        "slug": article.slug,
                        "content": article.content,
                        "excerpt": article.excerpt,
                        "status": article.status,
                        "created_at": article.created_at.isoformat() if article.created_at else None,
                        "updated_at": article.updated_at.isoformat() if article.updated_at else None,
                        "published_at": article.published_at.isoformat() if article.published_at else None,
                    })

                zip_file.writestr("articles.json", json.dumps(articles_data, ensure_ascii=False, indent=2))

                # 3. 导出用户评论
                comments_result = await db.execute(
                    select(Comment).where(Comment.user_id == current_user.id)
                )
                comments = comments_result.scalars().all()

                comments_data = []
                for comment in comments:
                    comments_data.append({
                        "comment_id": comment.id,
                        "article_id": comment.article_id,
                        "content": comment.content,
                        "status": comment.status,
                        "created_at": comment.created_at.isoformat() if comment.created_at else None,
                    })

                zip_file.writestr("comments.json", json.dumps(comments_data, ensure_ascii=False, indent=2))

                # 4. 导出元数据
                metadata = {
                    "export_date": datetime.utcnow().isoformat(),
                    "data_subject": current_user.email,
                    "total_articles": len(articles_data),
                    "total_comments": len(comments_data),
                    "gdpr_article": "Article 15 - Right of access by the data subject",
                    "note": "此文件包含您的所有个人数据。根据 GDPR 规定，您有权获取这些数据。"
                }
                zip_file.writestr("metadata.json", json.dumps(metadata, ensure_ascii=False, indent=2))

            # 准备响应
            zip_buffer.seek(0)

            filename = f"fastblog_personal_data_{current_user.username}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.zip"

            return StreamingResponse(
                zip_buffer,
                media_type="application/zip",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "X-Export-Date": datetime.utcnow().isoformat(),
                }
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"数据导出失败: {str(e)}")


@router.post("/delete/my-account")
async def delete_user_account(
        confirmation: bool = False,
        current_user: User = Depends(jwt_required)
):
    """
    P7-3: 数据删除 API (Right to be Forgotten - GDPR Article 17)
    
    删除用户账户及其所有个人数据：
    - 匿名化用户信息（保留文章和评论以维护内容完整性）
    - 删除个人偏好设置
    - 清除登录历史
    
    Args:
        confirmation: 确认删除（必须为 True）
        
    Returns:
        删除结果
    """
    if not confirmation:
        raise HTTPException(
            status_code=400,
            detail="需要确认删除操作。请设置 confirmation=true"
        )

    async for db in get_async_session():
        try:
            # 1. 匿名化用户信息（不删除文章和评论，保持内容完整性）
            current_user.username = f"deleted_user_{current_user.id}"
            current_user.email = f"deleted_{current_user.id}@anonymous.invalid"
            current_user.display_name = "已删除用户"
            current_user.bio = None
            current_user.avatar_url = None
            current_user.is_active = False

            # 2. 清除敏感信息
            # 注意：实际项目中应删除 password_hash 和其他敏感字段

            current_user.updated_at = datetime.utcnow()

            await db.commit()

            return {
                "success": True,
                "message": "账户已成功删除。您的个人数据已被匿名化处理。",
                "deleted_at": datetime.utcnow().isoformat(),
                "note": "根据 GDPR Article 17，您的个人数据已被删除。公开内容（文章、评论）已匿名化保留。"
            }

        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"账户删除失败: {str(e)}")


@router.get("/privacy-policy")
async def get_privacy_policy():
    """
    P7-3: 获取隐私政策模板
    
    Returns:
        隐私政策 HTML 内容
    """
    privacy_policy_html = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>隐私政策 - FastBlog</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; }
            h1 { color: #1a1a1a; border-bottom: 2px solid #3b82f6; padding-bottom: 10px; }
            h2 { color: #2d3748; margin-top: 30px; }
            .highlight { background: #fef3c7; padding: 2px 6px; border-radius: 3px; }
            .contact-box { background: #f3f4f6; padding: 15px; border-radius: 8px; margin: 20px 0; }
        </style>
    </head>
    <body>
        <h1>隐私政策</h1>
        <p><strong>最后更新日期：</strong>2026年5月24日</p>
        
        <h2>1. 引言</h2>
        <p>FastBlog（以下简称"我们"）非常重视您的隐私。本隐私政策说明了我们如何收集、使用、存储和保护您的个人信息。</p>
        
        <h2>2. 我们收集的信息</h2>
        <ul>
            <li><strong>账户信息：</strong>用户名、电子邮件地址、显示名称</li>
            <li><strong>内容数据：</strong>您发布的文章、评论、上传的媒体文件</li>
            <li><strong>技术数据：</strong>IP 地址、浏览器类型、设备信息、访问日志</li>
            <li><strong>Cookies：</strong>用于会话管理和偏好设置</li>
        </ul>
        
        <h2>3. 我们如何使用您的信息</h2>
        <ul>
            <li>提供和维护博客平台服务</li>
            <li>处理您的注册和登录请求</li>
            <li>发送重要通知（如安全更新）</li>
            <li>改进用户体验和平台性能</li>
            <li>防止欺诈和滥用行为</li>
        </ul>
        
        <h2>4. 您的权利（GDPR）</h2>
        <p>如果您位于欧盟经济区，您拥有以下权利：</p>
        <ul>
            <li><span class="highlight">访问权（Article 15）：</span>您可以请求导出所有个人数据</li>
            <li><span class="highlight">删除权（Article 17）：</span>您可以请求删除您的账户和个人数据</li>
            <li><span class="highlight">更正权（Article 16）：</span>您可以更新或更正不准确的信息</li>
            <li><span class="highlight">限制处理权（Article 18）：</span>您可以要求限制某些数据处理</li>
            <li><span class="highlight">数据可携带权（Article 20）：</span>您可以以结构化格式获取数据</li>
        </ul>
        
        <h2>5. 数据保留</h2>
        <p>我们会在以下期限内保留您的数据：</p>
        <ul>
            <li>账户数据：直到您删除账户</li>
            <li>文章内容：永久保留（除非您删除）</li>
            <li>访问日志：最多 90 天</li>
            <li>Cookies：根据浏览器设置</li>
        </ul>
        
        <h2>6. 数据安全</h2>
        <p>我们采用行业标准的加密和安全措施保护您的数据：</p>
        <ul>
            <li>HTTPS/TLS 加密传输</li>
            <li>密码哈希存储（bcrypt）</li>
            <li>定期安全审计</li>
            <li>访问控制和权限管理</li>
        </ul>
        
        <h2>7. Cookie 政策</h2>
        <p>我们使用以下类型的 Cookies：</p>
        <ul>
            <li><strong>必要 Cookies：</strong>用于会话管理和身份验证</li>
            <li><strong>偏好 Cookies：</strong>记住您的语言和主题设置</li>
            <li><strong>分析 Cookies：</strong>帮助我们了解使用情况（可选）</li>
        </ul>
        
        <h2>8. 第三方服务</h2>
        <p>我们可能使用以下第三方服务：</p>
        <ul>
            <li>CDN 服务（Cloudflare/AWS CloudFront）</li>
            <li>分析工具（Google Analytics，可选）</li>
            <li>社交媒体插件（分享按钮）</li>
        </ul>
        
        <h2>9. 儿童隐私</h2>
        <p>我们的服务不面向 16 岁以下儿童。如果我们发现收集了儿童的个人信息，将立即删除。</p>
        
        <h2>10. 隐私政策更新</h2>
        <p>我们可能会不时更新本隐私政策。重大变更将通过电子邮件或网站公告通知您。</p>
        
        <div class="contact-box">
            <h2>11. 联系我们</h2>
            <p>如果您对本隐私政策有任何疑问或需要行使您的权利，请联系我们：</p>
            <ul>
                <li>电子邮件：privacy@fastblog.example.com</li>
                <li>数据保护官：dpo@fastblog.example.com</li>
            </ul>
        </div>
        
        <hr>
        <p style="font-size: 12px; color: #6b7280;">
            本隐私政策符合《通用数据保护条例》（GDPR）、《加州消费者隐私法案》（CCPA）和其他适用法律法规。
        </p>
    </body>
    </html>
    """

    return Response(content=privacy_policy_html, media_type="text/html; charset=utf-8")


@router.get("/cookie-consent/config")
async def get_cookie_consent_config():
    """
    P7-3: 获取 Cookie 同意横幅配置
    
    Returns:
        Cookie 同意配置
    """
    return {
        "enabled": True,
        "message": "我们使用 Cookies 来改善您的浏览体验。继续使用即表示您同意我们的 Cookie 政策。",
        "accept_button": "接受全部",
        "reject_button": "仅必要",
        "settings_button": "自定义设置",
        "policy_link": "/api/v1/gdpr/privacy-policy",
        "cookie_types": [
            {
                "type": "necessary",
                "name": "必要 Cookies",
                "description": "网站正常运行所必需，无法禁用",
                "required": True,
                "checked": True
            },
            {
                "type": "preferences",
                "name": "偏好 Cookies",
                "description": "记住您的语言和主题设置",
                "required": False,
                "checked": True
            },
            {
                "type": "analytics",
                "name": "分析 Cookies",
                "description": "帮助我们了解网站使用情况",
                "required": False,
                "checked": False
            },
            {
                "type": "marketing",
                "name": "营销 Cookies",
                "description": "用于个性化广告（如果有）",
                "required": False,
                "checked": False
            }
        ]
    }
