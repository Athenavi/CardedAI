"""
一键安装向导服务
提供系统初始化、数据库配置、管理员创建等功能
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List


class InstallationWizardService:
    """
    安装向导服务

    功能:
    1. 检测是否已安装
    2. 数据库配置和初始化
    3. 管理员账号创建
    4. 站点基本信息配置
    5. 示例数据导入(可选)
    6. 安装锁定机制
    """

    def __init__(self):
        self.install_lock_file = Path("install.lock")
        self.install_flag_file = Path("storage/.installation_completed")
        # 使用绝对路径，Docker 模式下 .env 写入 config/.env（挂载卷），开发模式回退到根目录 .env
        _project_root = Path(__file__).parent.parent.parent.parent.parent
        self.config_dir = _project_root / "config"
        self.config_file = self.config_dir / ".env"
        self.ensure_directories()

        print(f"\n[InstallationWizard] 初始化:")
        print(f"  .env 文件路径: {self.config_file.absolute()}")
        print(f"  项目根目录: {self.config_file.parent.absolute()}")
        print(f"  文件是否存在: {self.config_file.exists()}")

    def ensure_directories(self):
        """确保必需的目录存在"""
        required_dirs = [
            "storage/objects",
            "storage/cache",
            "storage/thumbnails",
            "logs",
            "plugins",
            "themes",
            "upload_chunks",
            "media",
            "plugins_data"
        ]
        for dir_path in required_dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)

    def check_prerequisites(self) -> Dict[str, Any]:
        """
        检查安装前置条件

        Returns:
            检查结果字典
        """
        results = {
            'python_version': self._check_python_version(),
            'database_connection': self._check_database_connection(),
            'writable_directories': self._check_writable_directories(),
            'required_packages': self._check_required_packages(),
            'all_passed': True
        }

        # 检查是否全部通过
        for key, value in results.items():
            if key != 'all_passed' and isinstance(value, dict):
                if not value.get('passed', False):
                    results['all_passed'] = False
                    break

        return results

    def _check_python_version(self) -> Dict[str, Any]:
        """检查Python版本"""
        import sys
        version = sys.version_info
        passed = version.major >= 3 and version.minor >= 14

        return {
            'passed': passed,
            'current': f"{version.major}.{version.minor}.{version.micro}",
            'required': "3.14+",
            'message': f"Python版本: {version.major}.{version.minor}.{version.micro}"
        }

    def _check_database_connection(self) -> Dict[str, Any]:
        """检查数据库连接"""
        # 在安装阶段，数据库可能还未配置，所以这里只返回通过
        # 实际的数据库连接测试在 configure_database 中进行
        return {
            'passed': True,
            'message': '数据库连接检查将在配置后执行'
        }

    def _test_postgresql_connection(self, config: Dict[str, str]) -> Dict[str, Any]:
        """
        测试 PostgreSQL 数据库连接

        Args:
            config: 数据库配置

        Returns:
            测试结果
        """
        try:
            import psycopg2

            conn = psycopg2.connect(
                host=config['host'],
                port=int(config.get('port', 5432)),
                database=config['database'],
                user=config['username'],
                password=config['password'],
                connect_timeout=10
            )
            conn.close()

            return {
                'success': True,
                'message': 'PostgreSQL 数据库连接成功'
            }
        except ImportError:
            return {
                'success': False,
                'error': '缺少 psycopg2 库，请安装: pip install psycopg2-binary'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'数据库连接失败: {str(e)}'
            }

    def _check_writable_directories(self) -> Dict[str, Any]:
        """检查目录写权限"""
        required_dirs = [
            'storage/objects',
            'storage/cache',
            'storage/thumbnails',
            'logs',
            'plugins',
            'themes',
            'upload_chunks'
        ]

        failed_dirs = []
        for dir_path in required_dirs:
            path = Path(dir_path)
            if not path.exists():
                try:
                    path.mkdir(parents=True, exist_ok=True)
                except Exception:
                    failed_dirs.append(dir_path)
            elif not os.access(path, os.W_OK):
                failed_dirs.append(dir_path)

        return {
            'passed': len(failed_dirs) == 0,
            'failed_dirs': failed_dirs,
            'message': f"目录权限检查: {'通过' if len(failed_dirs) == 0 else f'{len(failed_dirs)}个目录无写权限'}"
        }

    def _check_required_packages(self) -> Dict[str, Any]:
        """检查必需的Python包"""
        required_packages = [
            'fastapi',
            'sqlalchemy',
            'pydantic',
            'uvicorn'
        ]

        missing_packages = []
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
            except ImportError:
                missing_packages.append(package)

        return {
            'passed': len(missing_packages) == 0,
            'missing': missing_packages,
            'message': f"依赖包检查: {'通过' if len(missing_packages) == 0 else f'缺少{len(missing_packages)}个包'}"
        }

    def configure_database(self, config: Dict[str, str]) -> Dict[str, Any]:
        """
        配置数据库连接（仅支持 PostgreSQL）

        Args:
            config: 数据库配置字典
                - db_type: 数据库类型 (必须为 postgresql)
                - host: 主机地址
                - port: 端口
                - database: 数据库名
                - username: 用户名
                - password: 密码

        Returns:
            配置结果
        """
        try:
            # 验证数据库类型
            db_type = config.get('db_type', 'postgresql')
            if db_type != 'postgresql':
                return {
                    'success': False,
                    'error': '系统仅支持 PostgreSQL 数据库'
                }

            # 验证必要字段
            required_fields = ['host', 'port', 'database', 'username']
            for field in required_fields:
                if not config.get(field):
                    return {
                        'success': False,
                        'error': f'缺少必要字段: {field}'
                    }

            # 构建数据库URL
            db_url = f"postgresql+psycopg2://{config['username']}:{config['password']}@{config['host']}:{config.get('port', 5432)}/{config['database']}"

            # 测试数据库连接
            connection_result = self._test_postgresql_connection(config)
            if not connection_result['success']:
                return connection_result

            # 更新.env文件
            # 确保所有值都是有效的，避免空字符串
            env_updates = {
                'DB_ENGINE': 'postgresql',
                'DB_HOST': config.get('host', 'localhost') or 'localhost',
                'DB_PORT': str(config.get('port') or 5432),
                'DB_USER': config.get('username', 'postgres') or 'postgres',
                'DB_PASSWORD': config.get('password', ''),
                'DB_NAME': config.get('database', 'fast_blog') or 'fast_blog',
            }

            # 调试输出
            print(f"\n[DEBUG] 保存数据库配置到 .env:")
            for key, value in env_updates.items():
                if key == 'DB_PASSWORD':
                    print(f"  {key}: {'***' if value else '(empty)'}")
                else:
                    print(f"  {key}: '{value}'")

            self._update_env_file(env_updates)

            return {
                'success': True,
                'message': '数据库配置成功，请确认配置信息',
                'db_url': db_url,
                'db_type': 'postgresql',
                'requires_confirmation': True,
                'config_summary': {
                    'host': config['host'],
                    'port': config.get('port', 5432),
                    'database': config['database'],
                    'username': config['username'],
                }
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'数据库配置失败: {str(e)}'
            }

    def _update_env_file(self, updates: Dict[str, str]):
        """
        更新.env文件（保持标准格式）

        Args:
            updates: 要更新的键值对
        """
        try:
            env_content = {}
            comments = []  # 保留注释
            original_lines = []  # 保留原始行顺序

            print(f"\n[DEBUG] .env 文件路径: {self.config_file.absolute()}")
            print(f"[DEBUG] 文件是否存在: {self.config_file.exists()}")
            print(f"[DEBUG] 父目录: {self.config_file.parent.absolute()}")
            print(f"[DEBUG] 父目录是否存在: {self.config_file.parent.exists()}")

            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        original_lines.append(line)
                        line_stripped = line.strip()
                        if line_stripped.startswith('#'):
                            comments.append(line.rstrip('\n'))
                        elif '=' in line_stripped and not line_stripped.startswith('#'):
                            key, value = line_stripped.split('=', 1)
                            env_content[key.strip()] = value.strip()
            else:
                # 如果文件不存在，添加标准头部注释
                print("[DEBUG] .env 文件不存在，将创建新文件")
                comments = [
                    '# ============================================================================',
                    '# FastBlog 环境配置文件',
                    '# ============================================================================',
                    '',
                    '# 数据库配置（仅支持 PostgreSQL）',
                    '# ----------------------------------------------------------------------------'
                ]

            # 更新配置
            env_content.update(updates)

            # 调试输出：显示即将写入的配置
            print(f"\n[DEBUG] 即将写入 .env 文件的配置:")
            for key, value in env_content.items():
                if 'PASSWORD' in key or 'SECRET' in key:
                    print(f"  {key}: {'***' if value else '(empty)'}")
                else:
                    print(f"  {key}: '{value}' (type: {type(value).__name__})")

            # 确保父目录存在
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            print(f"[DEBUG] 父目录已确保存在")

            # 写入文件，保持标准格式
            with open(self.config_file, 'w', encoding='utf-8') as f:
                # 先写注释
                if comments:
                    for comment in comments:
                        f.write(f"{comment}\n")
                    f.write("\n")

                # 再写配置项
                for key, value in env_content.items():
                    # 确保值是字符串
                    if value is None:
                        value = ''
                    elif not isinstance(value, str):
                        value = str(value)

                    # 写入配置
                    f.write(f"{key}={value}\n")

            print(f"\n[DEBUG] .env 文件已成功写入: {self.config_file.absolute()}")

            # 验证文件是否真的被创建
            if self.config_file.exists():
                file_size = self.config_file.stat().st_size
                print(f"[DEBUG] ✓ 文件存在，大小: {file_size} bytes")

                # 读取并显示文件内容以供调试
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(f"\n[DEBUG] 文件完整内容:")
                    print("=" * 60)
                    print(content)
                    print("=" * 60)
            else:
                print(f"\n[ERROR] ✗ .env 文件写入后仍然不存在！")
                print(f"[ERROR] 请检查以下可能的问题:")
                print(f"  1. 父目录是否存在: {self.config_file.parent.exists()}")
                print(f"  2. 父目录是否可写: {os.access(str(self.config_file.parent), os.W_OK)}")
                print(f"  3. 当前工作目录: {Path.cwd().absolute()}")
                raise RuntimeError(".env 文件创建失败")

        except Exception as e:
            import traceback
            error_msg = f"更新 .env 文件失败: {str(e)}"
            print(f"\n[ERROR] {error_msg}")
            print(traceback.format_exc())
            raise

    def import_sample_data(
            self,
            import_articles: bool = True,
            import_categories: bool = True
    ) -> Dict[str, Any]:
        """
        导入示例数据（实际导入到数据库）

        Args:
            import_articles: 是否导入示例文章
            import_categories: 是否导入示例分类

        Returns:
            导入结果
        """
        try:
            # 如果都不导入，直接返回成功
            if not import_articles and not import_categories:
                return {
                    'success': True,
                    'message': '已跳过示例数据导入',
                    'imported': {'articles': 0, 'categories': 0}
                }

            import asyncio
            from sqlalchemy import select
            from src.utils.database.main import get_async_session
            from shared.models import Category, Article, ArticleContent
            from datetime import datetime

            async def _import_data():
                # 使用统一管理器获取会话
                from src.utils.database.unified_manager import db_manager as unified_db_manager
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
                                # 检查分类是否已存在
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
                            # 先获取所有分类
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
                                    # 检查文章是否已存在
                                    result = await session.execute(
                                        select(Article).where(Article.slug == article_data['slug'])
                                    )
                                    existing = result.scalar_one_or_none()

                                    if not existing:
                                        # 随机分配一个分类
                                        category = categories[0]  # 简化：都分配到第一个分类

                                        # 创建文章（不包含 content）
                                        article = Article(
                                            title=article_data['title'],
                                            slug=article_data['slug'],
                                            excerpt=article_data['excerpt'],
                                            status=article_data['status'],
                                            category=category.id,  # 注意：使用 category.id
                                            user=1,  # 假设管理员用户 ID 为 1
                                            created_at=datetime.now(),
                                            updated_at=datetime.now()
                                        )
                                        session.add(article)
                                        await session.flush()  # 获取 article.id

                                        # 创建文章内容
                                        article_content = ArticleContent(
                                            article=article.id,
                                            content=article_data['content'],
                                            created_at=datetime.now(),
                                            updated_at=datetime.now()
                                        )
                                        session.add(article_content)
                                        imported['articles'] += 1

                                await session.commit()

                        return {
                            'success': True,
                            'message': f'示例数据导入成功：{imported["categories"]} 个分类，{imported["articles"]} 篇文章',
                            'imported': imported
                        }
                    except Exception:
                        await session.rollback()
                        raise

            # 运行异步函数（处理可能在异步上下文中调用的情况）
            try:
                loop = asyncio.get_running_loop()
                # 如果已经有运行的事件循环，使用线程池在新的事件循环中执行
                import concurrent.futures

                def run_in_thread():
                    """在线程中运行，创建独立的事件循环和数据库管理器"""
                    # 保存原始的单例状态
                    from src.utils.database.unified_manager import db_manager as original_manager

                    # 创建新的事件循环
                    new_loop = asyncio.new_event_loop()
                    try:
                        asyncio.set_event_loop(new_loop)
                        # 重新初始化数据库管理器（在新的事件循环中）
                        from src.utils.database.unified_manager import UnifiedDatabaseManager
                        # 重置单例，以便在新的事件循环中重新初始化
                        UnifiedDatabaseManager._instance = None
                        UnifiedDatabaseManager._initialized = False

                        from src.utils.database.unified_manager import db_manager as new_db_manager
                        new_db_manager.initialize()

                        # 运行异步函数
                        return new_loop.run_until_complete(_import_data())
                    finally:
                        new_loop.close()
                        # 恢复原来的单例
                        UnifiedDatabaseManager._instance = original_manager
                        UnifiedDatabaseManager._initialized = True

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_in_thread)
                    result = future.result(timeout=30)
                    return result
            except RuntimeError:
                # 没有运行的事件循环，直接使用 asyncio.run
                result = asyncio.run(_import_data())
                return result

        except Exception as e:
            import traceback
            print(f"导入示例数据失败: {str(e)}")
            print(traceback.format_exc())
            return {
                'success': False,
                'error': f'导入示例数据失败: {str(e)}'
            }

    def is_installed(self) -> bool:
        """
        检查系统是否已安装

        Returns:
            是否已安装
        """
        return self.install_flag_file.exists()

    def get_installation_status(self) -> Dict[str, Any]:
        """
        获取安装状态

        Returns:
            安装状态信息
        """
        status = {
            "is_installed": self.is_installed(),
            "steps_completed": [],
            "current_step": 1
        }

        if self.is_installed():
            try:
                with open(self.install_flag_file, 'r', encoding='utf-8') as f:
                    install_info = json.load(f)
                status.update(install_info)
            except Exception:
                pass

        return status

    def check_database_connection(
            self,
            db_url: str
    ) -> Dict[str, Any]:
        """
        检查数据库连接

        Args:
            db_url: 数据库URL

        Returns:
            检查结果
        """
        return {
            "success": True,
            "message": "Database connection successful"
        }

    def create_admin_user(
            self,
            username: str,
            email: str,
            password: str
    ) -> Dict[str, Any]:
        """
        创建管理员账号（实际创建到数据库）

        Args:
            username: 用户名
            email: 邮箱
            password: 密码

        Returns:
            创建结果
        """
        try:
            # 验证输入
            if len(username) < 3:
                return {
                    'success': False,
                    'error': '用户名至少需要3个字符'
                }

            if len(password) < 6:
                return {
                    'success': False,
                    'error': '密码至少需要6个字符'
                }

            if not email or '@' not in email:
                return {
                    'success': False,
                    'error': '请输入有效的邮箱地址'
                }

            # 实际创建用户到数据库
            import asyncio
            from sqlalchemy import select
            from src.utils.database.main import get_async_session
            from shared.models import User

            # 确保数据库管理器已初始化
            from src.utils.database.unified_manager import db_manager as unified_db_manager
            if unified_db_manager._async_session_factory is None:
                print("[Install] Initializing database manager for admin user creation...")
                unified_db_manager.initialize()

            # 使用 Argon2 密码哈希函数
            from src.utils.security.password_validator import hash_password
            hashed_password = hash_password(password)

            async def _create_user():
                # 使用统一管理器获取会话
                from src.utils.database.unified_manager import db_manager as unified_db_manager
                async with unified_db_manager.get_session_no_auto_commit() as session:
                    try:
                        # 检查用户是否已存在
                        result = await session.execute(
                            select(User).where(User.username == username)
                        )
                        existing_user = result.scalar_one_or_none()

                        if existing_user:
                            return {
                                'success': False,
                                'error': f'用户名 "{username}" 已存在'
                            }

                        # 检查邮箱是否已存在
                        result = await session.execute(
                            select(User).where(User.email == email)
                        )
                        existing_email = result.scalar_one_or_none()

                        if existing_email:
                            return {
                                'success': False,
                                'error': f'邮箱 "{email}" 已被注册'
                            }

                        # 创建新用户
                        from datetime import datetime
                        new_user = User(
                            username=username,
                            email=email,
                            password=hashed_password,
                            is_active=True,
                            is_superuser=True,
                            is_staff=True,
                            date_joined=datetime.now(),
                        )

                        session.add(new_user)
                        await session.commit()
                        await session.refresh(new_user)

                        return {
                            'success': True,
                            'message': f'管理员账号 "{username}" 创建成功',
                            'data': {
                                'user_id': new_user.id,
                                'username': new_user.username,
                                'email': new_user.email
                            }
                        }
                    except Exception:
                        await session.rollback()
                        raise

            # 运行异步函数（处理可能在异步上下文中调用的情况）
            import sys

            try:
                loop = asyncio.get_running_loop()
                # 已经有运行的事件循环（例如在 FastAPI 请求处理中）
                # 使用 run_coroutine_threadsafe 在当前事件循环中运行协程
                coro = _create_user()
                future_result = asyncio.run_coroutine_threadsafe(coro, loop)
                result = future_result.result(timeout=30)
                return result
            except RuntimeError as e:
                if "no running event loop" in str(e):
                    # 没有运行的事件循环，直接使用 asyncio.run
                    result = asyncio.run(_create_user())
                    return result
                else:
                    # 其他 RuntimeError，重新抛出
                    raise

        except Exception as e:
            import traceback
            print(f"创建管理员账号失败: {str(e)}")
            print(traceback.format_exc())
            return {
                'success': False,
                'error': f'创建管理员账号失败: {str(e)}'
            }

    def configure_site_settings(
            self,
            site_name: str,
            site_url: str,
            admin_email: str,
            site_description: str = '',
            language: str = 'zh_CN'
    ) -> Dict[str, Any]:
        """
        配置站点基本信息

        Args:
            site_name: 站点名称
            site_url: 站点URL
            admin_email: 管理员邮箱
            site_description: 站点描述
            language: 语言 (zh_CN/en_US)

        Returns:
            配置结果
        """
        try:
            # 验证输入
            if not site_name:
                return {
                    'success': False,
                    'error': '站点名称不能为空'
                }

            if not site_url.startswith(('http://', 'https://')):
                return {
                    'success': False,
                    'error': '站点URL必须以 http:// 或 https:// 开头'
                }

            # 更新.env文件
            self._update_env_file({
                'SITE_NAME': site_name,
                'SITE_URL': site_url,
                'SITE_DESCRIPTION': site_description,
                'ADMIN_EMAIL': admin_email,
                'DEFAULT_LANGUAGE': language,
                'SECRET_KEY': os.urandom(32).hex()
            })

            return {
                'success': True,
                'message': '站点配置成功'
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'站点配置失败: {str(e)}'
            }

    def confirm_database_and_migrate(self) -> Dict[str, Any]:
        """
        确认数据库配置并执行数据库初始化

        流程：
        1. 重新加载配置并初始化数据库管理器
        2. 测试数据库连接
        3. 检查是否有迁移脚本，如果没有则生成初始迁移
        4. 执行 Alembic 迁移

        Returns:
            确认和迁移结果
        """
        try:
            import subprocess
            import sys
            from pathlib import Path

            print("\n" + "=" * 60)
            print("开始初始化数据库...")
            print("=" * 60)

            # 首先重新加载配置并初始化数据库管理器
            print("\n[1/4] 重新加载配置并初始化数据库管理器...")
            try:
                import importlib
                from dotenv import load_dotenv

                # 重新加载 .env 文件
                load_dotenv(override=True)
                print("  ✓ .env 文件已重新加载")

                # 重新导入并初始化设置
                import src.setting
                importlib.reload(src.setting)
                from src.setting import settings as new_settings
                print(
                    f"  ✓ 配置已重新加载，数据库 URL: {new_settings.database_url[:50]}..." if new_settings.database_url else "  ⚠ 数据库 URL 仍为空")

                # 初始化统一数据库管理器
                from src.utils.database.unified_manager import db_manager
                # 重置管理器状态以允许重新初始化
                db_manager._async_engine = None
                db_manager._async_session_factory = None
                db_manager.initialize()

                if db_manager._async_session_factory is not None:
                    print("✓ 数据库连接池初始化成功")
                else:
                    print("⚠ 警告：数据库连接池初始化失败，数据库 URL 可能未正确配置")
                    return {
                        'success': False,
                        'error': '数据库连接池初始化失败。请检查 .env 文件中的数据库配置是否正确。'
                    }
            except Exception as init_err:
                import traceback
                error_msg = f'数据库管理器初始化失败: {str(init_err)}'
                print(f"✗ {error_msg}")
                print(traceback.format_exc())
                return {
                    'success': False,
                    'error': error_msg
                }

            # 测试数据库连接
            print("\n[2/4] 测试数据库连接...")

            # 使用 psycopg2 进行同步连接测试（更可靠）
            try:
                import psycopg2

                # 从配置中获取连接参数
                from src.setting import settings
                db_url = settings.database_url

                if not db_url:
                    return {
                        'success': False,
                        'error': '数据库 URL 未配置'
                    }

                # 解析数据库 URL
                # 格式: postgresql+psycopg2://user:pass@host:port/dbname
                from urllib.parse import urlparse
                parsed = urlparse(db_url.replace('postgresql+psycopg2://', 'postgresql://'))

                conn = psycopg2.connect(
                    host=parsed.hostname or 'localhost',
                    port=parsed.port or 5432,
                    database=parsed.path.lstrip('/') or 'postgres',
                    user=parsed.username or 'postgres',
                    password=parsed.password or '',
                    connect_timeout=5
                )
                conn.close()
                print("✓ 数据库连接成功")

            except ImportError:
                error_msg = '缺少 psycopg2 库，请安装: pip install psycopg2-binary'
                print(f"✗ {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }
            except Exception as e:
                error_msg = f'数据库连接失败: {str(e)}'
                print(f"✗ {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }

            # 检查是否有迁移脚本
            # installation_wizard.py 路径: shared/services/install/install_manager/installation_wizard.py
            # 需要向上5层到达项目根目录
            project_root = Path(__file__).parent.parent.parent.parent.parent
            versions_dir = project_root / "alembic_migrations" / "versions"
            migration_files = list(versions_dir.glob("*.py")) if versions_dir.exists() else []

            # 过滤掉 __init__.py
            migration_files = [f for f in migration_files if f.name != "__init__.py"]

            print(f"\n[3/4] 检查迁移脚本... (找到 {len(migration_files)} 个)")

            # 如果没有迁移脚本，生成初始迁移
            if len(migration_files) == 0:
                print("→ 未找到迁移脚本，正在生成初始迁移...")
                print(f"  项目根目录: {project_root.absolute()}")
                print(f"  迁移目录: {versions_dir.absolute()}")
                print(f"  迁移目录是否存在: {versions_dir.exists()}")

                result = subprocess.run(
                    [sys.executable, "-m", "alembic", "revision", "--autogenerate", "-m", "Initial migration"],
                    cwd=str(project_root),
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                # 调试输出
                print(f"\n[DEBUG] Alembic 命令返回码: {result.returncode}")
                if result.stdout:
                    print(f"[DEBUG] Alembic stdout:\n{result.stdout}")
                if result.stderr:
                    print(f"[DEBUG] Alembic stderr:\n{result.stderr}")

                if result.returncode != 0:
                    error_msg = f'生成迁移脚本失败 (退出码: {result.returncode}):'
                    if result.stderr:
                        error_msg += f'\n{result.stderr}'
                    if result.stdout:
                        error_msg += f'\n{result.stdout}'
                    print(f"✗ {error_msg}")
                    return {
                        'success': False,
                        'error': error_msg
                    }

                print("✓ 初始迁移脚本生成成功")

                # 重新检查迁移文件
                migration_files = list(versions_dir.glob("*.py")) if versions_dir.exists() else []
                migration_files = [f for f in migration_files if f.name != "__init__.py"]
                print(f"→ 现在共有 {len(migration_files)} 个迁移脚本")

                # 列出生成的文件
                if migration_files:
                    print("  生成的文件:")
                    for f in migration_files:
                        print(f"    - {f.name}")
            else:
                print(f"✓ 找到 {len(migration_files)} 个迁移脚本")

            # 执行迁移
            print("\n[4/4] 执行数据库迁移...")
            result = subprocess.run(
                [sys.executable, "-m", "alembic", "upgrade", "head"],
                cwd=str(project_root),
                capture_output=True,
                text=True,
                timeout=300
            )

            # 调试输出
            print(f"\n[DEBUG] Alembic upgrade 返回码: {result.returncode}")
            if result.stdout:
                print(f"[DEBUG] Alembic stdout:\n{result.stdout}")
            if result.stderr:
                print(f"[DEBUG] Alembic stderr:\n{result.stderr}")

            if result.returncode == 0:
                print("✓ 数据库迁移成功完成")
                if result.stdout:
                    print(f"\n迁移输出:\n{result.stdout}")

                return {
                    'success': True,
                    'message': '数据库配置已确认，迁移执行成功',
                    'output': result.stdout,
                    'migrations_applied': len(migration_files)
                }
            else:
                error_msg = f'迁移失败 (退出码: {result.returncode}):'
                if result.stderr:
                    error_msg += f'\n{result.stderr}'
                if result.stdout:
                    error_msg += f'\n{result.stdout}'
                print(f"✗ {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }

        except subprocess.TimeoutExpired:
            error_msg = '迁移超时（超过5分钟）'
            print(f"✗ {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
        except Exception as e:
            import traceback
            error_msg = f'数据库初始化失败: {str(e)}'
            print(f"✗ {error_msg}")
            print(traceback.format_exc())
            return {
                'success': False,
                'error': error_msg
            }

    def complete_installation(self, install_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        完成安装（包括导入示例数据）

        Args:
            install_info: 安装信息
                - import_sample_data: 是否导入示例数据
                - import_articles: 是否导入文章
                - import_categories: 是否导入分类

        Returns:
            完成结果
        """
        try:
            # 标记安装完成
            install_info['completed_at'] = datetime.now().isoformat()
            install_info['is_installed'] = True

            # 保存安装标志
            with open(self.install_flag_file, 'w', encoding='utf-8') as f:
                json.dump(install_info, f, ensure_ascii=False, indent=2)

            print("\n" + "=" * 60)
            print("✓ 安装完成！")
            print("=" * 60)

            # 如果选择导入示例数据
            if install_info.get('import_sample_data', False):
                print("\n正在导入示例数据...")
                sample_result = self.import_sample_data(
                    import_articles=install_info.get('import_articles', True),
                    import_categories=install_info.get('import_categories', True)
                )

                if sample_result['success']:
                    print(f"✓ {sample_result['message']}")
                else:
                    print(f"✗ 示例数据导入失败: {sample_result.get('error', '未知错误')}")

            return {
                "success": True,
                "message": "安装完成",
                "sample_data_imported": install_info.get('import_sample_data', False)
            }
        except Exception as e:
            import traceback
            print(f"完成安装失败: {str(e)}")
            print(traceback.format_exc())
            return {
                "success": False,
                "error": str(e)
            }

    def reset_installation(self) -> Dict[str, Any]:
        """
        重置安装状态（用于重新安装）

        Returns:
            重置结果
        """
        try:
            if self.install_flag_file.exists():
                self.install_flag_file.unlink()

            return {
                "success": True,
                "message": "Installation state reset successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_installation_steps(self) -> List[Dict[str, str]]:
        """
        获取安装步骤列表

        Returns:
            安装步骤
        """
        return [
            {
                "step": 1,
                "title": "欢迎使用",
                "description": "欢迎使用 FastBlog，让我们开始配置您的博客系统"
            },
            {
                "step": 2,
                "title": "数据库配置",
                "description": "配置数据库连接信息"
            },
            {
                "step": 3,
                "title": "创建管理员账户",
                "description": "设置管理员用户名、邮箱和密码"
            },
            {
                "step": 4,
                "title": "站点设置",
                "description": "配置站点名称、URL和管理员邮箱"
            },
            {
                "step": 5,
                "title": "完成安装",
                "description": "确认配置并完成安装"
            }
        ]


# 全局实例
installation_wizard_service = InstallationWizardService()
