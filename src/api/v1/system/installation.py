"""
一键安装向导API
"""
import asyncio
import json

from fastapi import APIRouter, Body
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from shared.services.install.install_manager.installation_wizard import installation_wizard_service
from shared.services.install.install_manager.migration_service import migration_service
from src.api.v1.core.responses import ApiResponse

router = APIRouter()


@router.get("/prerequisites",
            summary="检查安装前置条件",
            description="检查系统环境是否满足安装要求",
            response_description="返回前置条件检查结果")
async def check_prerequisites_api():
    """检查安装前置条件"""
    try:
        result = installation_wizard_service.check_prerequisites()

        return ApiResponse(
            success=True,
            data=result
        )
    except Exception as e:
        import traceback
        print(f"Error in check_prerequisites_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


class DatabaseConfigRequest(BaseModel):
    """数据库配置请求"""
    db_url: str = None  # 可选，兼容旧版
    host: str = None
    port: str = None
    name: str = None
    user: str = None
    pass_: str = None  # 避免使用pass关键字


class AdminUserRequest(BaseModel):
    """管理员账户请求"""
    username: str
    email: str
    password: str
    password_confirm: str = ''  # 可选,前端已验证


class SiteSettingsRequest(BaseModel):
    """站点设置请求"""
    site_name: str
    site_url: str
    admin_email: str
    site_description: str = ''
    language: str = 'zh_CN'


class DatabaseConfigFullRequest(BaseModel):
    """数据库完整配置请求"""
    db_type: str = 'sqlite'
    host: str = ''
    port: str = ''
    database: str = 'blog.db'
    username: str = ''
    password: str = ''


class SampleDataRequest(BaseModel):
    """示例数据导入请求"""
    import_articles: bool = True
    import_categories: bool = True


@router.post("/configure-database",
             summary="配置数据库",
             description="配置数据库连接信息",
             response_description="返回配置结果")
async def configure_database_api(
        request: DatabaseConfigFullRequest
):
    """配置数据库"""
    try:
        # 检查是否已安装
        if installation_wizard_service.is_installed():
            return ApiResponse(
                success=False,
                error="System already installed"
            )

        config = {
            'db_type': request.db_type,
            'host': request.host,
            'port': request.port,
            'database': request.database,
            'username': request.username,
            'password': request.password
        }

        result = installation_wizard_service.configure_database(config)

        return ApiResponse(
            success=result['success'],
            data=result
        )
    except Exception as e:
        import traceback
        print(f"Error in configure_database_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


async def _import_sample_data_helper(import_articles: bool, import_categories: bool):
    """
    导入示例数据的辅助函数（可复用）

    Args:
        import_articles: 是否导入文章
        import_categories: 是否导入分类

    Returns:
        ApiResponse
    """
    # 如果都不导入，直接返回成功
    if not import_articles and not import_categories:
        return ApiResponse(
            success=True,
            data={
                'success': True,
                'message': '已跳过示例数据导入',
                'imported': {'articles': 0, 'categories': 0}
            }
        )

    from sqlalchemy import select
    from src.utils.database.unified_manager import db_manager as unified_db_manager
    from shared.models import Category, Article, ArticleContent
    from datetime import datetime

    async with unified_db_manager.get_session_no_auto_commit() as session:
        try:
            imported = {
                'articles': 0,
                'categories': 0
            }

            # 导入分类
            if import_categories:
                sample_categories = [
                    {'name': '技术分享', 'slug': 'tech', 'description': '技术相关文章'},
                    {'name': '生活随笔', 'slug': 'life', 'description': '生活感悟和随笔'},
                    {'name': '学习笔记', 'slug': 'study', 'description': '学习过程中的笔记'},
                    {'name': '项目实战', 'slug': 'project', 'description': '项目开发经验'},
                    {'name': '行业资讯', 'slug': 'news', 'description': '行业最新动态'},
                ]

                for cat_data in sample_categories:
                    result = await session.execute(
                        select(Category).where(Category.slug == cat_data['slug'])
                    )
                    existing = result.scalar_one_or_none()

                    if not existing:
                        category = Category(
                            name=cat_data['name'],
                            slug=cat_data['slug'],
                            description=cat_data['description'],
                            created_at=datetime.now(),
                            updated_at=datetime.now()
                        )
                        session.add(category)
                        imported['categories'] += 1

                await session.commit()

            # 导入文章
            if import_articles:
                result = await session.execute(select(Category))
                categories = result.scalars().all()

                if categories:
                    sample_articles = [
                        {
                            'title': '欢迎使用 FastBlog',
                            'slug': 'welcome-to-fastblog',
                            'content': '# 欢迎使用 FastBlog\n\n这是一个基于 FastAPI 和 Next.js构建的现代化博客系统。\n\n## 特性\n\n- 🚀 高性能：基于 FastAPI 异步框架\n- 🎨 美观：现代化的 UI 设计\n- 🔌 可扩展：强大的插件系统\n- 📱 响应式：完美支持移动端\n\n开始你的博客之旅吧！',
                            'excerpt': '欢迎使用 FastBlog 博客系统',
                            'status': 1,
                        },
                        {
                            'title': 'FastBlog 快速入门指南',
                            'slug': 'fastblog-quick-start',
                            'content': '# FastBlog 快速入门\n\n## 安装\n\n1. 克隆仓库\n2. 安装依赖\n3. 配置环境变量\n4. 运行安装向导\n\n## 基本使用\n\n- 创建文章\n- 管理分类\n- 自定义主题\n- 安装插件\n\n更多文档请访问我们的官方网站。',
                            'excerpt': 'FastBlog 的快速入门教程',
                            'status': 0,
                        },
                    ]

                    for article_data in sample_articles:
                        result = await session.execute(
                            select(Article).where(Article.slug == article_data['slug'])
                        )
                        existing = result.scalar_one_or_none()

                        if not existing:
                            category = categories[0]
                            article = Article(
                                title=article_data['title'],
                                slug=article_data['slug'],
                                excerpt=article_data['excerpt'],
                                status=article_data['status'],
                                category=category.id,
                                user=1,
                                created_at=datetime.now(),
                                updated_at=datetime.now()
                            )
                            session.add(article)
                            await session.flush()

                            article_content = ArticleContent(
                                article=article.id,
                                content=article_data['content'],
                                created_at=datetime.now(),
                                updated_at=datetime.now()
                            )
                            session.add(article_content)
                            imported['articles'] += 1

                    await session.commit()

            return ApiResponse(
                success=True,
                data={
                    'success': True,
                    'message': f'示例数据导入成功：{imported["categories"]} 个分类，{imported["articles"]} 篇文章',
                    'imported': imported
                }
            )
        except Exception:
            await session.rollback()
            raise


@router.post("/import-sample-data",
             summary="导入示例数据",
             description="导入示例文章和分类",
             response_description="返回导入结果")
async def import_sample_data_api(
        request: SampleDataRequest
):
    """导入示例数据"""
    try:
        # 检查是否已安装
        if installation_wizard_service.is_installed():
            return ApiResponse(
                success=False,
                error="System already installed"
            )

        # 调用辅助函数
        return await _import_sample_data_helper(
            import_articles=request.import_articles,
            import_categories=request.import_categories
        )

    except Exception as e:
        import traceback
        print(f"Error in import_sample_data_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/status",
            summary="获取安装状态",
            description="检查系统是否已安装及当前进度",
            response_description="返回安装状态")
async def get_installation_status_api():
    """获取安装状态"""
    try:
        status = installation_wizard_service.get_installation_status()

        return ApiResponse(
            success=True,
            data=status
        )
    except Exception as e:
        import traceback
        print(f"Error in get_installation_status_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/steps",
            summary="获取安装步骤",
            description="获取完整的安装步骤列表",
            response_description="返回安装步骤")
async def get_installation_steps_api():
    """获取安装步骤"""
    try:
        steps = installation_wizard_service.get_installation_steps()

        return ApiResponse(
            success=True,
            data={
                "steps": steps,
                "total_steps": len(steps)
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in get_installation_steps_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.post("/check-database",
             summary="检查数据库连接",
             description="验证数据库连接配置是否正确",
             response_description="返回检查结果")
async def check_database_connection_api(
        request: DatabaseConfigRequest
):
    """检查数据库连接"""
    try:
        result = installation_wizard_service.check_database_connection(request.db_url)

        return ApiResponse(
            success=result['success'],
            data=result
        )
    except Exception as e:
        import traceback
        print(f"Error in check_database_connection_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.post("/create-admin",
             summary="创建管理员账户",
             description="创建第一个管理员账户",
             response_description="返回创建结果")
async def create_admin_user_api(
        request: AdminUserRequest
):
    """创建管理员账户"""
    try:
        # 检查是否已安装
        if installation_wizard_service.is_installed():
            return ApiResponse(
                success=False,
                error="System already installed"
            )

        # 直接调用内部异步函数
        from shared.services.install.install_manager.installation_wizard import installation_wizard_service as wizard

        # 验证输入
        if not request.username or not request.email or not request.password:
            return ApiResponse(
                success=False,
                error='用户名、邮箱和密码不能为空'
            )

        if len(request.password) < 6:
            return ApiResponse(
                success=False,
                error='密码长度至少为6个字符'
            )

        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', request.email):
            return ApiResponse(
                success=False,
                error='邮箱格式不正确'
            )

        # 使用 Argon2 密码哈希
        from src.utils.security.password_validator import hash_password
        hashed_password = hash_password(request.password)

        # 使用统一管理器获取会话
        from src.utils.database.unified_manager import db_manager as unified_db_manager
        from sqlalchemy import select
        from shared.models import User
        from datetime import datetime

        # 确保数据库管理器已初始化
        if unified_db_manager._async_session_factory is None:
            print("[Install] 检测到数据库管理器未初始化，尝试重新加载配置...")
            try:
                # 强制重新加载 .env 文件和配置
                import importlib
                from dotenv import load_dotenv

                # 重新加载 .env 文件
                load_dotenv(override=True)
                print("  ✓ .env 文件已重新加载")

                # 重新导入并初始化设置
                import src.setting
                importlib.reload(src.setting)
                from src.setting import settings as new_settings
                print(f"  ✓ 配置已重新加载，数据库 URL: {new_settings.database_url[:50]}..." if new_settings.database_url else "  ⚠ 数据库 URL 仍为空")

                # 重置并重新初始化数据库管理器
                unified_db_manager._async_engine = None
                unified_db_manager._async_session_factory = None
                unified_db_manager.initialize()

                if unified_db_manager._async_session_factory is not None:
                    print("✓ 数据库连接池初始化成功")
                else:
                    return ApiResponse(
                        success=False,
                        error='数据库连接池初始化失败。请确认已完成“确认数据库配置并执行迁移”步骤。'
                    )
            except Exception as init_err:
                import traceback
                print(f"数据库管理器初始化失败: {init_err}")
                print(traceback.format_exc())
                return ApiResponse(
                    success=False,
                    error=f'数据库管理器初始化失败: {str(init_err)}'
                )

        async with unified_db_manager.get_session_no_auto_commit() as session:
            try:
                # 检查用户是否已存在
                result = await session.execute(
                    select(User).where(User.username == request.username)
                )
                existing_user = result.scalar_one_or_none()

                if existing_user:
                    return ApiResponse(
                        success=False,
                        error=f'用户名 "{request.username}" 已存在'
                    )

                # 检查邮箱是否已存在
                result = await session.execute(
                    select(User).where(User.email == request.email)
                )
                existing_email = result.scalar_one_or_none()

                if existing_email:
                    return ApiResponse(
                        success=False,
                        error=f'邮箱 "{request.email}" 已被注册'
                    )

                # 创建新用户
                new_user = User(
                    username=request.username,
                    email=request.email,
                    password=hashed_password,
                    is_active=True,
                    is_superuser=True,
                    is_staff=True,
                    date_joined=datetime.now(),
                )

                session.add(new_user)
                await session.commit()
                await session.refresh(new_user)

                return ApiResponse(
                    success=True,
                    data={
                        'success': True,
                        'message': f'管理员账号 "{request.username}" 创建成功',
                        'data': {
                            'user_id': new_user.id,
                            'username': new_user.username,
                            'email': new_user.email
                        }
                    }
                )
            except Exception:
                await session.rollback()
                raise

    except Exception as e:
        import traceback
        print(f"Error in create_admin_user_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.post("/configure-site",
             summary="配置站点设置",
             description="配置站点基本信息",
             response_description="返回配置结果")
async def configure_site_settings_api(
        request: SiteSettingsRequest
):
    """配置站点设置"""
    try:
        # 检查是否已安装
        if installation_wizard_service.is_installed():
            return ApiResponse(
                success=False,
                error="System already installed"
            )

        config = {
            'site_name': request.site_name,
            'site_url': request.site_url,
            'site_description': request.site_description,
            'admin_email': request.admin_email,
            'language': request.language
        }

        result = installation_wizard_service.configure_site_settings(
            site_name=request.site_name,
            site_url=request.site_url,
            admin_email=request.admin_email,
            site_description=request.site_description,
            language=request.language
        )

        return ApiResponse(
            success=result['success'],
            data=result
        )
    except Exception as e:
        import traceback
        print(f"Error in configure_site_settings_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.post("/complete",
             summary="完成安装",
             description="确认所有配置并完成安装",
             response_description="返回完成结果")
async def complete_installation_api(
        install_info: dict = Body(default={}, description="安装信息")
):
    """完成安装"""
    try:
        # 检查是否已安装
        if installation_wizard_service.is_installed():
            return ApiResponse(
                success=False,
                error="System already installed"
            )

        # 标记安装完成
        from datetime import datetime
        install_info['completed_at'] = datetime.now().isoformat()
        install_info['is_installed'] = True

        # 保存安装标志
        with open(installation_wizard_service.install_flag_file, 'w', encoding='utf-8') as f:
            import json
            json.dump(install_info, f, ensure_ascii=False, indent=2)

        print("\n" + "=" * 60)
        print("✓ 安装完成！")
        print("=" * 60)

        # 如果选择导入示例数据，调用辅助函数
        sample_data_imported = False
        if install_info.get('import_sample_data', False):
            print("\n正在导入示例数据...")
            try:
                result = await _import_sample_data_helper(
                    import_articles=install_info.get('import_articles', True),
                    import_categories=install_info.get('import_categories', True)
                )

                if result.success:
                    print(f"✓ {result.data.get('message', '示例数据导入成功')}")
                    sample_data_imported = True
                else:
                    print(f"✗ 示例数据导入失败: {result.error}")
            except Exception as e:
                print(f"✗ 示例数据导入失败: {str(e)}")

        return ApiResponse(
            success=True,
            data={
                "success": True,
                "message": "安装完成",
                "sample_data_imported": sample_data_imported
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in complete_installation_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.post("/confirm-database-and-migrate",
             summary="确认数据库配置并执行迁移",
             description="二次确认数据库配置并自动执行 Alembic 迁移",
             response_description="返回确认和迁移结果")
async def confirm_database_and_migrate_api():
    """确认数据库配置并执行迁移"""
    try:
        # 检查是否已安装
        if installation_wizard_service.is_installed():
            return ApiResponse(
                success=False,
                error="System already installed"
            )

        result = installation_wizard_service.confirm_database_and_migrate()

        return ApiResponse(
            success=result['success'],
            data=result
        )
    except Exception as e:
        import traceback
        print(f"Error in confirm_database_and_migrate_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.post("/reset",
             summary="重置安装状态",
             description="重置安装状态（仅用于开发/测试）",
             response_description="返回重置结果")
async def reset_installation_api():
    """重置安装状态"""
    try:
        result = installation_wizard_service.reset_installation()

        return ApiResponse(
            success=result['success'],
            data=result
        )
    except Exception as e:
        import traceback
        print(f"Error in reset_installation_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/migration/stream",
            summary="数据库迁移实时日志流",
            description="通过 SSE 实时推送 Alembic 迁移日志到前端",
            response_description="SSE 流式响应")
async def stream_migration_logs():
    """
    Server-Sent Events (SSE) 端点，实时推送迁移日志
    参考 Django migrations 和 Flask-Migrate 的设计
    """

    async def event_generator():
        """生成 SSE 事件"""
        try:
            import sys
            print(f"\n[SSE] 开始迁移日志流", file=sys.stderr)

            # 检查 Alembic 是否可用
            if not migration_service.check_alembic_available():
                error_msg = {'type': 'error', 'message': 'Alembic 未安装或不可用'}
                print(f"[SSE] {error_msg}", file=sys.stderr)
                yield f"data: {json.dumps(error_msg, ensure_ascii=False)}\n\n"
                return

            # 获取迁移状态
            status = migration_service.get_migration_status()
            print(f"[SSE] 当前版本: {status['current']}, 目标版本: {status['head']}", file=sys.stderr)

            current_ver = status["current"]
            head_ver = status["head"]
            yield f"data: {json.dumps({'type': 'info', 'message': f'当前版本: {current_ver}'}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'info', 'message': f'目标版本: {head_ver}'}, ensure_ascii=False)}\n\n"

            if status.get('is_up_to_date'):
                yield f"data: {json.dumps({'type': 'info', 'message': '数据库已是最新版本，无需迁移'}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'success', 'message': '✓ 数据库已就绪'}, ensure_ascii=False)}\n\n"
                return

            # 执行迁移并实时推送日志
            print(f"[SSE] 开始执行迁移...", file=sys.stderr)
            async for log_entry in migration_service.run_migration():
                yield f"data: {json.dumps(log_entry, ensure_ascii=False)}\n\n"
                # 给前端一点时间处理
                await asyncio.sleep(0.05)

            print(f"[SSE] 迁移完成", file=sys.stderr)

        except Exception as e:
            import traceback
            import sys
            error_msg = {
                'type': 'error',
                'message': f'SSE 端点出错: {str(e)}',
                'traceback': traceback.format_exc()
            }
            print(f"[SSE ERROR] {error_msg}", file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)
            yield f"data: {json.dumps(error_msg, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Nginx 禁用缓冲
        }
    )
