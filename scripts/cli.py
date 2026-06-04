#!/usr/bin/env python3
"""
FastBlog CLI - 命令行工具

提供便捷的项目管理、代码生成、部署等功能

用法:
    python scripts/cli.py <command> [options]

命令:
    create          创建新项目
    generate        生成代码(model, plugin, api)
    dev             启动开发服务器
    build           构建项目
    deploy          部署项目
    info            显示项目信息
    doctor          检查环境配置
    plugin          插件管理 (install, uninstall, list, enable, disable)
    theme           主题管理 (list, activate, deactivate)
    user            用户管理 (create, list, delete)
    db              数据库管理 (backup, restore, migrate)
    cache           缓存管理 (clear, stats)
"""

import argparse
import subprocess
import sys
from pathlib import Path


def cmd_create(args):
    """创建新项目"""
    project_name = args.name
    template = args.template or "default"

    print(f"🚀 Creating new FastBlog project: {project_name}")
    print(f"   Template: {template}")

    # 创建项目目录
    project_dir = Path(project_name)
    if project_dir.exists():
        print(f"❌ Error: Directory '{project_name}' already exists")
        sys.exit(1)

    project_dir.mkdir(parents=True)

    # 复制模板文件 (简化版:创建基本结构)
    print("📁 Creating project structure...")

    # 创建基本目录
    (project_dir / "apps").mkdir()
    (project_dir / "config").mkdir()
    (project_dir / "plugins").mkdir()
    (project_dir / "themes").mkdir()

    # 创建基本文件
    env_example = project_dir / ".env.example"
    env_example.write_text("""# FastBlog Environment Configuration
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@localhost:5432/fastblog
REDIS_URL=redis://localhost:6379/0
CORS_ORIGINS=http://localhost:3000
""")

    readme = project_dir / "README.md"
    readme.write_text(f"""# {project_name}

A FastBlog powered blog site.

## Quick Start

1. Copy `.env.example` to `.env` and configure
2. Install dependencies: `pip install -r requirements.txt`
3. Run migrations: `python manage.py migrate`
4. Start server: `python main.py`

## Development

```bash
# Start development server
fastblog dev

# Generate code
fastblog generate model Article
fastblog generate plugin my-plugin
```
""")

    print(f"✅ Project '{project_name}' created successfully!")
    print(f"\n📝 Next steps:")
    print(f"   cd {project_name}")
    print(f"   cp .env.example .env")
    print(f"   # Edit .env with your configuration")
    print(f"   fastblog dev")


def cmd_generate(args):
    """生成代码"""
    gen_type = args.type

    if gen_type == "model":
        generate_model(args)
    elif gen_type == "plugin":
        generate_plugin(args)
    elif gen_type == "theme":
        generate_theme(args)
    elif gen_type == "api":
        generate_api_endpoint(args)
    else:
        print(f"❌ Unknown generation type: {gen_type}")
        sys.exit(1)


def generate_model(args):
    """生成 Django/FastAPI 模型"""
    model_name = args.name
    app_name = args.app or "blog"

    print(f"🔧 Generating model: {model_name}")
    print(f"   App: {app_name}")

    # 这里可以添加实际的模型生成逻辑
    print(f"⚠️  Model generation not fully implemented yet")
    print(f"   Please manually create the model in apps/{app_name}/models.py")


def generate_plugin(args):
    """生成插件"""
    plugin_name = args.name
    description = getattr(args, 'description', '') or ''
    author = getattr(args, 'author', '') or ''

    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from scripts.scaffold_generator import generate_plugin as gen_plugin
    gen_plugin(plugin_name, description, author)


def generate_theme(args):
    """生成主题"""
    theme_name = args.name
    description = getattr(args, 'description', '') or ''
    author = getattr(args, 'author', '') or ''

    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from scripts.scaffold_generator import generate_theme as gen_theme
    gen_theme(theme_name, description, author)


def generate_api_endpoint(args):
    """生成 API 端点"""
    endpoint_name = args.name
    description = getattr(args, 'description', '') or ''

    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from scripts.scaffold_generator import generate_api as gen_api
    gen_api(endpoint_name, description)


def cmd_dev(args):
    """启动开发服务器"""
    print("🚀 Starting FastBlog development server...")

    # 设置环境变量
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_blog.settings')

    # 启动主应用
    try:
        import uvicorn
        uvicorn.run(
            "main:app",
            host=args.host or "0.0.0.0",
            port=int(args.port) or 9421,
            reload=True,
            log_level="info"
        )
    except ImportError:
        print("❌ uvicorn not installed. Install with: pip install uvicorn")
        sys.exit(1)


def cmd_build(args):
    """构建项目"""
    print("🔨 Building FastBlog...")

    # 前端构建
    frontend_dir = Path("frontend-next")
    if frontend_dir.exists():
        print("   Building frontend...")
        try:
            subprocess.run(["npm", "run", "build"], cwd=frontend_dir, check=True)
            print("   ✅ Frontend built successfully")
        except subprocess.CalledProcessError:
            print("   ❌ Frontend build failed")
            sys.exit(1)
    else:
        print("   ⚠️  Frontend directory not found")

    print("✅ Build complete!")


def cmd_deploy(args):
    """部署项目"""
    print("🚀 Deploying FastBlog...")
    print("⚠️  Deployment not fully implemented yet")
    print("   Please use Docker or manual deployment for now")
    print("\n📚 Docker deployment:")
    print("   docker-compose up -d")


def cmd_info(args):
    """显示项目信息"""
    print("📊 FastBlog Project Information")
    print("=" * 50)

    # 版本信息
    version_file = Path("version.txt")
    if version_file.exists():
        version = version_file.read_text().strip()
        print(f"Version: {version}")

    # Python 版本
    print(f"Python: {sys.version.split()[0]}")

    # 项目路径
    print(f"Project Root: {Path.cwd()}")

    # 插件数量
    plugins_dir = Path("plugins")
    if plugins_dir.exists():
        plugin_count = len([p for p in plugins_dir.iterdir() if p.is_dir()])
        print(f"Plugins: {plugin_count}")

    # 主题数量
    themes_dir = Path("themes")
    if themes_dir.exists():
        theme_count = len([t for t in themes_dir.iterdir() if t.is_dir()])
        print(f"Themes: {theme_count}")


def cmd_doctor(args):
    """检查环境配置"""
    print("🔍 Checking environment...")
    print("=" * 50)

    issues = []

    # 检查 Python 版本
    if sys.version_info < (3, 8):
        issues.append("Python version should be >= 3.8")
    else:
        print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")

    # 检查 .env 文件
    env_file = Path(".env")
    if not env_file.exists():
        issues.append(".env file not found. Copy from .env.example")
        issues.append("OR ：open 前端地址/install to setup init sys")
    else:
        print("✅ .env file exists")

    # 检查依赖
    try:
        import fastapi
        print(f"✅ FastAPI {fastapi.__version__}")
    except ImportError:
        issues.append("FastAPI not installed")

    # 检查数据库连接
    print("\n" + "=" * 50)
    if issues:
        print(f"❌ Found {len(issues)} issue(s):")
        for issue in issues:
            print(f"   - {issue}")
        sys.exit(1)
    else:
        print("✅ All checks passed!")


def cmd_plugin(args):
    """插件管理"""
    action = args.action

    # 设置 Django 环境
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_blog.settings')

    try:
        import django
        django.setup()
    except Exception as e:
        print(f"⚠️  Warning: Could not setup Django: {e}")

    if action == "install":
        plugin_install(args)
    elif action == "uninstall":
        plugin_uninstall(args)
    elif action == "list":
        plugin_list(args)
    elif action == "enable":
        plugin_enable(args)
    elif action == "disable":
        plugin_disable(args)
    else:
        print(f"❌ Unknown plugin action: {action}")
        sys.exit(1)


def cmd_theme(args):
    """主题管理"""
    action = args.action

    # 设置 Django 环境
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_blog.settings')

    try:
        import django
        django.setup()
    except Exception as e:
        print(f"⚠️  Warning: Could not setup Django: {e}")

    if action == "list":
        theme_list(args)
    elif action == "activate":
        theme_activate(args)
    elif action == "deactivate":
        theme_deactivate(args)
    else:
        print(f"❌ Unknown theme action: {action}")
        sys.exit(1)


def theme_list(args):
    """列出主题"""
    try:
        from shared.services.theme_manager import ThemeManager
        manager = ThemeManager()

        themes = manager.get_installed_themes()
        active_theme = manager.get_active_theme()

        print(f"🎨 Installed Themes ({len(themes)}):")
        print("=" * 60)

        if not themes:
            print("   No themes found")
            return

        for theme in themes:
            is_active = theme['slug'] == active_theme.get('slug') if active_theme else False
            status = "✅" if is_active else "⭕"
            version = theme.get('version', 'N/A')
            description = theme.get('description', '')[:50]
            print(f"   {status} {theme['slug']} v{version}")
            if description:
                print(f"      {description}")

    except Exception as e:
        print(f"❌ Error listing themes: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def theme_activate(args):
    """激活主题"""
    slug = args.slug
    print(f"🎨 Activating theme: {slug}")

    try:
        from shared.services.theme_manager import ThemeManager
        manager = ThemeManager()

        success = manager.activate_theme(slug)

        if success:
            print(f"✅ Theme '{slug}' activated successfully")
        else:
            print(f"❌ Failed to activate theme '{slug}'")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error activating theme: {e}")
        sys.exit(1)


def theme_deactivate(args):
    """停用主题（切换到默认主题）"""
    print(f"⭕ Deactivating current theme")

    try:
        from shared.services.theme_manager import ThemeManager
        manager = ThemeManager()

        # 切换到默认主题
        success = manager.activate_theme('default')

        if success:
            print(f"✅ Switched to default theme")
        else:
            print(f"❌ Failed to switch theme")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error deactivating theme: {e}")
        sys.exit(1)


def cmd_user(args):
    """用户管理"""
    action = args.action

    # 设置 Django 环境
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_blog.settings')

    try:
        import django
        django.setup()
    except Exception as e:
        print(f"⚠️  Warning: Could not setup Django: {e}")

    if action == "create":
        user_create(args)
    elif action == "list":
        user_list(args)
    elif action == "delete":
        user_delete(args)
    else:
        print(f"❌ Unknown user action: {action}")
        sys.exit(1)


def user_create(args):
    """创建用户"""
    username = args.username
    email = getattr(args, 'email', None) or ''
    password = getattr(args, 'password', None) or ''
    is_admin = getattr(args, 'admin', False)

    print(f"👤 Creating user: {username}")

    try:
        from shared.models.user import User
        from shared.utils.database.main import get_async_session, get_async_session_context
        import asyncio
        from datetime import datetime

        async def create_user():
            async with get_async_session_context() as db:
                # 检查用户名是否已存在
                from sqlalchemy import select
                result = await db.execute(select(User).where(User.username == username))
                existing_user = result.scalar_one_or_none()

                if existing_user:
                    print(f"❌ Username '{username}' already exists")
                    return False

                # 创建新用户
                from passlib.context import CryptContext
                pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
                hashed_password = pwd_context.hash(password)

                new_user = User(
                    username=username,
                    email=email,
                    password=hashed_password,
                    is_active=True,
                    is_superuser=is_admin,
                    is_staff=is_admin,
                    date_joined=datetime.now(),
                    locale='zh_CN'
                )

                db.add(new_user)
                await db.commit()

                print(f"✅ User '{username}' created successfully")
                if is_admin:
                    print(f"   User has administrator privileges")
                return True

        asyncio.run(create_user())

    except Exception as e:
        print(f"❌ Error creating user: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def user_list(args):
    """列出用户"""
    try:
        from shared.models.user import User
        from shared.utils.database.main import get_async_session, get_async_session_context
        from sqlalchemy import select
        import asyncio

        async def list_users():
            async with get_async_session_context() as db:
                result = await db.execute(select(User).order_by(User.date_joined.desc()))
                users = result.scalars().all()

                print(f"👥 Users ({len(users)}):")
                print("=" * 80)

                if not users:
                    print("   No users found")
                    return

                print(f"   {'ID':<6} {'Username':<20} {'Email':<30} {'Role':<15} {'Joined'}")
                print("   " + "-" * 76)

                for user in users:
                    role = "Admin" if user.is_superuser else "User"
                    joined = user.date_joined.strftime('%Y-%m-%d') if user.date_joined else 'N/A'
                    print(f"   {user.id:<6} {user.username:<20} {user.email or 'N/A':<30} {role:<15} {joined}")

        asyncio.run(list_users())

    except Exception as e:
        print(f"❌ Error listing users: {e}")
        sys.exit(1)


def user_delete(args):
    """删除用户"""
    username = args.username
    print(f"🗑️  Deleting user: {username}")

    try:
        from shared.models.user import User
        from shared.utils.database.main import get_async_session, get_async_session_context
        from sqlalchemy import select
        import asyncio

        async def delete_user():
            async with get_async_session_context() as db:
                result = await db.execute(select(User).where(User.username == username))
                user = result.scalar_one_or_none()

                if not user:
                    print(f"❌ User '{username}' not found")
                    return False

                await db.delete(user)
                await db.commit()

                print(f"✅ User '{username}' deleted successfully")
                return True

        asyncio.run(delete_user())

    except Exception as e:
        print(f"❌ Error deleting user: {e}")
        sys.exit(1)


def cmd_db(args):
    """数据库管理"""
    action = args.action

    if action == "backup":
        db_backup(args)
    elif action == "restore":
        db_restore(args)
    elif action == "migrate":
        db_migrate(args)
    else:
        print(f"❌ Unknown db action: {action}")
        sys.exit(1)


def db_backup(args):
    """数据库备份"""
    import os
    from datetime import datetime

    print("📦 开始备份数据库...")

    try:
        # 获取数据库配置
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '5432')
        db_user = os.getenv('DB_USER', 'postgres')
        db_name = os.getenv('DB_NAME', 'fast_blog')
        db_password = os.getenv('DB_PASSWORD', '')

        # 创建备份目录
        backup_dir = Path('backups/database')
        backup_dir.mkdir(parents=True, exist_ok=True)

        # 生成备份文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = backup_dir / f"{db_name}_{timestamp}.sql"

        # 设置环境变量（密码）
        env = os.environ.copy()
        if db_password:
            env['PGPASSWORD'] = db_password

        # 执行 pg_dump
        cmd = [
            'pg_dump',
            '-h', db_host,
            '-p', db_port,
            '-U', db_user,
            '-F', 'c',  # 自定义格式
            '-f', str(backup_file),
            db_name
        ]

        print(f"   主机: {db_host}:{db_port}")
        print(f"   数据库: {db_name}")
        print(f"   备份文件: {backup_file}")

        result = subprocess.run(cmd, env=env, capture_output=True, text=True)

        if result.returncode == 0:
            file_size = backup_file.stat().st_size
            print(f"✅ 数据库备份成功!")
            print(f"   文件大小: {file_size / 1024 / 1024:.2f} MB")
        else:
            print(f"❌ 备份失败: {result.stderr}")
            sys.exit(1)

    except FileNotFoundError:
        print("❌ 错误: 未找到 pg_dump 命令")
        print("   请确保 PostgreSQL 客户端工具已安装并在 PATH 中")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 备份失败: {str(e)}")
        sys.exit(1)


def db_restore(args):
    """数据库恢复"""
    backup_file = args.file

    backup_path = Path(backup_file)

    if not backup_path.exists():
        print(f"❌ 错误: 备份文件不存在: {backup_file}")
        sys.exit(1)

    print(f"🔄 开始恢复数据库...")
    print(f"   备份文件: {backup_file}")

    try:
        import os

        # 获取数据库配置
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '5432')
        db_user = os.getenv('DB_USER', 'postgres')
        db_name = os.getenv('DB_NAME', 'fast_blog')
        db_password = os.getenv('DB_PASSWORD', '')

        # 确认操作
        confirm = input(f"⚠️  警告: 这将覆盖数据库 '{db_name}' 的所有数据!\n继续? (yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ 操作已取消")
            sys.exit(0)

        # 设置环境变量
        env = os.environ.copy()
        if db_password:
            env['PGPASSWORD'] = db_password

        # 先删除现有数据库并重新创建
        print("   正在重置数据库...")
        drop_cmd = ['dropdb', '-h', db_host, '-p', db_port, '-U', db_user, '--if-exists', db_name]
        subprocess.run(drop_cmd, env=env, check=True, capture_output=True)

        create_cmd = ['createdb', '-h', db_host, '-p', db_port, '-U', db_user, db_name]
        subprocess.run(create_cmd, env=env, check=True, capture_output=True)

        # 恢复数据库
        print("   正在恢复数据...")
        restore_cmd = [
            'pg_restore',
            '-h', db_host,
            '-p', db_port,
            '-U', db_user,
            '-d', db_name,
            '--no-owner',
            '--no-privileges',
            str(backup_path)
        ]

        result = subprocess.run(restore_cmd, env=env, capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ 数据库恢复成功!")
        else:
            print(f"❌ 恢复失败: {result.stderr}")
            sys.exit(1)

    except FileNotFoundError:
        print("❌ 错误: 未找到 PostgreSQL 客户端工具")
        print("   请确保 pg_restore, dropdb, createdb 在 PATH 中")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"❌ 命令执行失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 恢复失败: {str(e)}")
        sys.exit(1)


def db_migrate(args):
    """数据库迁移"""
    print("🔄 运行数据库迁移...")

    try:
        import sys
        # 使用 Alembic 进行迁移
        result = subprocess.run(
            [sys.executable, '-m', 'alembic', 'upgrade', 'head'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("✅ 迁移成功!")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"❌ 迁移失败:")
            print(result.stderr)
            sys.exit(1)

    except FileNotFoundError:
        print("❌ Alembic 未找到。安装命令: pip install alembic")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 迁移失败: {str(e)}")
        sys.exit(1)


def cmd_cache(args):
    """缓存管理"""
    action = args.action

    if action == "clear":
        cache_clear(args)
    elif action == "stats":
        cache_stats(args)
    else:
        print(f"❌ Unknown cache action: {action}")
        sys.exit(1)


def cache_clear(args):
    """清除缓存"""
    print("🧹 Clearing cache...")

    try:
        # 清除各种缓存目录
        cache_dirs = [
            Path("storage/cache"),
            Path("__pycache__"),
        ]

        cleared_count = 0
        for cache_dir in cache_dirs:
            if cache_dir.exists():
                import shutil
                for item in cache_dir.glob("*"):
                    if item.is_dir():
                        shutil.rmtree(item)
                        cleared_count += 1
                    elif item.is_file():
                        item.unlink()
                        cleared_count += 1

        print(f"✅ Cache cleared ({cleared_count} items removed)")

    except Exception as e:
        print(f"❌ Error clearing cache: {e}")
        sys.exit(1)


def cache_stats(args):
    """显示缓存统计"""
    print("📊 Cache Statistics")
    print("=" * 50)

    try:
        cache_dir = Path("storage/cache")
        if cache_dir.exists():
            total_size = sum(f.stat().st_size for f in cache_dir.rglob('*') if f.is_file())
            file_count = len(list(cache_dir.rglob('*')))

            print(f"   Cache Directory: {cache_dir}")
            print(f"   Total Files: {file_count}")
            print(f"   Total Size: {total_size / 1024:.2f} KB")
        else:
            print("   Cache directory not found")

    except Exception as e:
        print(f"❌ Error getting cache stats: {e}")


def plugin_install(args):
    """安装插件"""
    slug = args.slug
    print(f"📦 Installing plugin: {slug}")

    try:
        from shared.services.plugin_manager import PluginManager
        manager = PluginManager()

        # 检查插件是否已存在
        if manager.is_plugin_installed(slug):
            print(f"⚠️  Plugin '{slug}' is already installed")
            return

        # 安装插件
        success = manager.install_plugin(slug)

        if success:
            print(f"✅ Plugin '{slug}' installed successfully")
            print(f"   Run 'python scripts/cli.py plugin enable {slug}' to activate it")
        else:
            print(f"❌ Failed to install plugin '{slug}'")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error installing plugin: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def plugin_uninstall(args):
    """卸载插件"""
    slug = args.slug
    print(f"🗑️  Uninstalling plugin: {slug}")

    try:
        from shared.services.plugin_manager import PluginManager
        manager = PluginManager()

        success = manager.uninstall_plugin(slug)

        if success:
            print(f"✅ Plugin '{slug}' uninstalled successfully")
        else:
            print(f"❌ Failed to uninstall plugin '{slug}'")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error uninstalling plugin: {e}")
        sys.exit(1)


def plugin_list(args):
    """列出插件"""
    show_active = getattr(args, 'active', False)

    try:
        from shared.services.plugin_manager import PluginManager
        manager = PluginManager()

        if show_active:
            plugins = manager.get_active_plugins()
            print(f"🔌 Active Plugins ({len(plugins)}):")
        else:
            plugins = manager.get_installed_plugins()
            print(f"🔌 Installed Plugins ({len(plugins)}):")

        print("=" * 60)

        if not plugins:
            print("   No plugins found")
            return

        for plugin in plugins:
            status = "✅" if plugin.get('is_active') else "⭕"
            version = plugin.get('version', 'N/A')
            description = plugin.get('description', '')[:50]
            print(f"   {status} {plugin['slug']} v{version}")
            if description:
                print(f"      {description}")

    except Exception as e:
        print(f"❌ Error listing plugins: {e}")
        sys.exit(1)


def plugin_enable(args):
    """启用插件"""
    slug = args.slug
    print(f"✅ Enabling plugin: {slug}")

    try:
        from shared.services.plugin_manager import PluginManager
        manager = PluginManager()

        success = manager.activate_plugin(slug)

        if success:
            print(f"✅ Plugin '{slug}' enabled successfully")
        else:
            print(f"❌ Failed to enable plugin '{slug}'")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error enabling plugin: {e}")
        sys.exit(1)


def plugin_disable(args):
    """禁用插件"""
    slug = args.slug
    print(f"⭕ Disabling plugin: {slug}")

    try:
        from shared.services.plugin_manager import PluginManager
        manager = PluginManager()

        success = manager.deactivate_plugin(slug)

        if success:
            print(f"✅ Plugin '{slug}' disabled successfully")
        else:
            print(f"❌ Failed to disable plugin '{slug}'")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error disabling plugin: {e}")
        sys.exit(1)


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        prog='fastblog',
        description='FastBlog CLI - Command Line Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/cli.py create my-blog
  python scripts/cli.py generate plugin "SEO Optimizer"
  python scripts/cli.py dev --port 8000
  python scripts/cli.py doctor
  python scripts/cli.py plugin list
  python scripts/cli.py theme activate modern-minimal
  python scripts/cli.py user create admin --admin
  python scripts/cli.py db backup
  python scripts/cli.py cache clear
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # create 命令
    create_parser = subparsers.add_parser('create', help='Create new project')
    create_parser.add_argument('name', help='Project name')
    create_parser.add_argument('--template', '-t', default='default', help='Template to use')

    # generate 命令
    gen_parser = subparsers.add_parser('generate', aliases=['gen'], help='Generate code')
    gen_parser.add_argument('type', choices=['model', 'plugin', 'theme', 'api'], help='Type to generate')
    gen_parser.add_argument('name', help='Name')
    gen_parser.add_argument('--app', '-a', help='App name (for models)')
    gen_parser.add_argument('--description', '-d', default='', help='Description')
    gen_parser.add_argument('--author', default='', help='Author name')

    # dev 命令
    dev_parser = subparsers.add_parser('dev', help='Start development server')
    dev_parser.add_argument('--host', default='0.0.0.0', help='Host')
    dev_parser.add_argument('--port', '-p', default='9421', help='Port')

    # build 命令
    subparsers.add_parser('build', help='Build project')

    # deploy 命令
    subparsers.add_parser('deploy', help='Deploy project')

    # info 命令
    subparsers.add_parser('info', help='Show project information')

    # doctor 命令
    subparsers.add_parser('doctor', help='Check environment')

    # plugin 命令
    plugin_parser = subparsers.add_parser('plugin', help='Plugin management')
    plugin_subparsers = plugin_parser.add_subparsers(dest='action', help='Plugin action')

    plugin_install_parser = plugin_subparsers.add_parser('install', help='Install plugin')
    plugin_install_parser.add_argument('slug', help='Plugin slug')

    plugin_uninstall_parser = plugin_subparsers.add_parser('uninstall', help='Uninstall plugin')
    plugin_uninstall_parser.add_argument('slug', help='Plugin slug')

    plugin_list_parser = plugin_subparsers.add_parser('list', help='List plugins')
    plugin_list_parser.add_argument('--active', '-a', action='store_true', help='Show only active plugins')

    plugin_enable_parser = plugin_subparsers.add_parser('enable', help='Enable plugin')
    plugin_enable_parser.add_argument('slug', help='Plugin slug')

    plugin_disable_parser = plugin_subparsers.add_parser('disable', help='Disable plugin')
    plugin_disable_parser.add_argument('slug', help='Plugin slug')

    # theme 命令
    theme_parser = subparsers.add_parser('theme', help='Theme management')
    theme_subparsers = theme_parser.add_subparsers(dest='action', help='Theme action')

    theme_list_parser = theme_subparsers.add_parser('list', help='List themes')

    theme_activate_parser = theme_subparsers.add_parser('activate', help='Activate theme')
    theme_activate_parser.add_argument('slug', help='Theme slug')

    theme_deactivate_parser = theme_subparsers.add_parser('deactivate', help='Deactivate theme')

    # user 命令
    user_parser = subparsers.add_parser('user', help='User management')
    user_subparsers = user_parser.add_subparsers(dest='action', help='User action')

    user_create_parser = user_subparsers.add_parser('create', help='Create user')
    user_create_parser.add_argument('username', help='Username')
    user_create_parser.add_argument('--email', '-e', default='', help='Email')
    user_create_parser.add_argument('--password', '-p', default='', help='Password')
    user_create_parser.add_argument('--admin', '-a', action='store_true', help='Create as admin')

    user_list_parser = user_subparsers.add_parser('list', help='List users')

    user_delete_parser = user_subparsers.add_parser('delete', help='Delete user')
    user_delete_parser.add_argument('username', help='Username')

    # db 命令
    db_parser = subparsers.add_parser('db', help='Database management')
    db_subparsers = db_parser.add_subparsers(dest='action', help='Database action')

    db_backup_parser = db_subparsers.add_parser('backup', help='Backup database')

    db_restore_parser = db_subparsers.add_parser('restore', help='Restore database')
    db_restore_parser.add_argument('file', help='Backup file path')

    db_migrate_parser = db_subparsers.add_parser('migrate', help='Run migrations')

    # cache 命令
    cache_parser = subparsers.add_parser('cache', help='Cache management')
    cache_subparsers = cache_parser.add_subparsers(dest='action', help='Cache action')

    cache_clear_parser = cache_subparsers.add_parser('clear', help='Clear cache')

    cache_stats_parser = cache_subparsers.add_parser('stats', help='Show cache stats')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # 路由到对应的命令处理函数
    commands = {
        'create': cmd_create,
        'generate': cmd_generate,
        'gen': cmd_generate,
        'dev': cmd_dev,
        'build': cmd_build,
        'deploy': cmd_deploy,
        'info': cmd_info,
        'doctor': cmd_doctor,
        'plugin': cmd_plugin,
        'theme': cmd_theme,
        'user': cmd_user,
        'db': cmd_db,
        'cache': cmd_cache,
    }

    handler = commands.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
