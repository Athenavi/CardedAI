"""
FastBlog 脚手架生成器

提供插件、主题、API 端点的代码生成功能
"""


class ScaffoldGenerator:
    """脚手架生成器基类"""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir

    def ensure_dir(self, path: Path):
        """确保目录存在"""
        path.mkdir(parents=True, exist_ok=True)

    def write_file(self, path: Path, content: str):
        """写入文件,如果文件已存在则提示"""
        if path.exists():
            print(f"⚠️  File already exists: {path}")
            response = input("Overwrite? (y/N): ").strip().lower()
            if response != 'y':
                print("Skipped")
                return False

        path.write_text(content, encoding='utf-8')
        try:
            rel_path = path.relative_to(Path.cwd())
            print(f"✅ Created: {rel_path}")
        except ValueError:
            print(f"✅ Created: {path}")
        return True


class PluginScaffold(ScaffoldGenerator):
    """插件脚手架生成器"""

    def generate(self, plugin_name: str, description: str = "", author: str = ""):
        """生成插件脚手架"""
        # 转换插件名称为 slug 格式
        slug = plugin_name.lower().replace(' ', '-').replace('_', '-')
        plugin_dir = self.output_dir / slug

        print(f"\n🔌 Generating plugin: {plugin_name}")
        print(f"   Slug: {slug}")
        print(f"   Output: {plugin_dir}")

        # 创建目录结构
        self.ensure_dir(plugin_dir)
        self.ensure_dir(plugin_dir / "templates")
        self.ensure_dir(plugin_dir / "static")
        self.ensure_dir(plugin_dir / "tests")

        # 生成 metadata.json
        self._generate_metadata(plugin_dir, plugin_name, description, author)

        # 生成 plugin.py
        self._generate_plugin_main(plugin_dir, plugin_name, slug)

        # 生成 README.md
        self._generate_readme(plugin_dir, plugin_name, description)

        # 生成 requirements.txt
        self._generate_requirements(plugin_dir)

        # 生成测试文件
        self._generate_tests(plugin_dir, plugin_name, slug)

        print(f"\n✅ Plugin '{plugin_name}' scaffold generated successfully!")
        print(f"\n📝 Next steps:")
        print(f"   1. Edit {plugin_dir}/metadata.json with your plugin details")
        print(f"   2. Implement your plugin logic in {plugin_dir}/plugin.py")
        print(f"   3. Add templates in {plugin_dir}/templates/")
        print(f"   4. Run tests: pytest {plugin_dir}/tests/")

    def _generate_metadata(self, plugin_dir: Path, name: str, description: str, author: str):
        """生成 metadata.json"""
        import json

        metadata = {
            "name": name,
            "slug": name.lower().replace(' ', '-').replace('_', '-'),
            "version": "1.0.0",
            "description": description or f"{name} plugin for FastBlog",
            "author": author or "Your Name",
            "author_email": "your@email.com",
            "license": "MIT",
            "homepage": "",
            "repository": "",
            "tags": [],
            "min_fastblog_version": "0.1.0",
            "dependencies": [],
            "hooks": [],
            "settings_schema": {}
        }

        metadata_file = plugin_dir / "metadata.json"
        metadata_file.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding='utf-8')
        try:
            rel_path = metadata_file.relative_to(Path.cwd())
            print(f"✅ Created: {rel_path}")
        except ValueError:
            print(f"✅ Created: {metadata_file}")

    def _generate_plugin_main(self, plugin_dir: Path, name: str, slug: str):
        """生成 plugin.py 主文件"""
        class_name = ''.join(word.capitalize() for word in name.replace('-', '_').split('_'))

        content = f'''
{name} Plugin

A plugin for FastBlog that provides additional functionality.
'''

from typing import Dict, Any

from src.unified_logger import default_logger as logger


class {class_name}Plugin(BasePlugin):
    """{name} Plugin Implementation"""

    def __init__(self):
        super().__init__(
            plugin_id=0,  # Will be set by plugin manager
            name="{name}",
            slug="{slug}",
            version="1.0.0"
        )

    def register_hooks(self):
        """Register plugin hooks"""
        # Example: Register a hook
        # @plugin_hooks.register('article.created')
        # def on_article_created(article):
        #     logger.info(f"Article created: {{article.title}}")
        pass

    def activate(self):
        """Activate plugin"""
        super().activate()
        logger.info(f"[{name}] Plugin activated")
        # Activation logic can be added here (e.g., create database tables)

    def deactivate(self):
        """Deactivate plugin"""
        super().deactivate()
        logger.info(f"[{name}] Plugin deactivated")
        # Deactivation logic can be added here (e.g., cleanup resources)

    def uninstall(self):
        """Uninstall plugin"""
        super().uninstall()
        logger.info(f"[{name}] Plugin uninstalled")
        # Uninstallation logic can be added here (e.g., drop database tables)

    def get_settings_ui(self) -> str:
        """Return settings UI HTML (optional)"""
        return """
        <div class="plugin-settings">
            <h3>{name} Settings</h3>
            <p>Configure your plugin settings here.</p>
        </div>
        """

    def save_settings(self, settings: Dict[str, Any]):
        """Save plugin settings (optional)"""
        # Save settings to database or config file
        # Example: self.settings.update(settings)
        pass


# Plugin instance (required)
plugin_instance = {class_name}Plugin()
'''

        plugin_file = plugin_dir / "plugin.py"
        self.write_file(plugin_file, content)

    def _generate_readme(self, plugin_dir: Path, name: str, description: str):
        """生成 README.md"""
        content = f'''# {name}

{description or f"A plugin for FastBlog"}

## Features

- Feature 1
- Feature 2
- Feature 3

## Installation

1. Copy this plugin to the `plugins/` directory
2. Activate the plugin from the admin panel

## Configuration

Configure your plugin settings from the admin panel.

## Usage

After activation, the plugin will automatically hook into the system.

## Development

### Running Tests

```bash
pytest plugins/{name.lower().replace(' ', '-')}/tests/
```

## Changelog

### 1.0.0 ({datetime.now().strftime('%Y-%m-%d')})
- Initial release

## License

MIT License
'''

        readme_file = plugin_dir / "README.md"
        self.write_file(readme_file, content)

    def _generate_requirements(self, plugin_dir: Path):
        """生成 requirements.txt"""
        content = '''# Plugin dependencies
# Add your plugin-specific dependencies here
# Example: requests>=2.28.0
'''

        req_file = plugin_dir / "requirements.txt"
        self.write_file(req_file, content)

    def _generate_tests(self, plugin_dir: Path, name: str, slug: str):
        """生成测试文件"""
        class_name = ''.join(word.capitalize() for word in name.replace('-', '_').split('_'))

        content = f'''"""
Tests for {name} Plugin
"""
from pathlib import Path


def test_plugin_initialization():
    """Test plugin can be initialized"""
    from plugins.{slug}.plugin import plugin_instance

    assert plugin_instance is not None
    assert plugin_instance.name == "{name}"
    assert plugin_instance.slug == "{slug}"


def test_plugin_activation():
    """Test plugin activation"""
    from plugins.{slug}.plugin import plugin_instance

    plugin_instance.activate()
    assert plugin_instance.is_active()

    plugin_instance.deactivate()
    assert not plugin_instance.is_active()


def test_plugin_feature():
    """Test plugin core functionality - customize for your plugin"""
    from plugins.
    {slug}.plugin
    import plugin_instance

    plugin_instance.activate()

    # Verify plugin info
    info = plugin_instance.get_info()
    assert isinstance(info, dict)
    assert 'name' in info
    assert 'slug' in info
    assert 'version' in info

    # Verify hooks are registered
    assert hasattr(plugin_instance, 'register_hooks')

    # Add more tests for your specific plugin features below


def test_plugin_settings():
    """测试插件设置"""
    from plugins.
    {slug}.plugin
    import plugin_instance

    # 检查默认设置是否存在
    assert hasattr(plugin_instance, 'settings')
    assert isinstance(plugin_instance.settings, dict)

    # 验证必需的设置项
    required_keys = []  # 根据你的插件添加必需的键
    for key in required_keys:
        assert key in plugin_instance.settings, f"Missing required setting: {{key}}"


def test_plugin_hooks():
    """测试插件钩子注册"""
    from plugins.
    {slug}.plugin
    import plugin_instance

    # 激活插件
    plugin_instance.activate()

    # 检查钩子是否已注册
    from shared.services.plugins.plugin_manager.core import plugin_hooks
    # 这里可以添加钩子注册的验证逻辑

    # 停用插件
    plugin_instance.deactivate()


def test_plugin_activation_deactivation():
    """测试插件的激活和停用"""
    from plugins.
    {slug}.plugin
    import plugin_instance

    # 初始状态应该是未激活
    assert not plugin_instance.is_active()

    # 激活插件
    plugin_instance.activate()
    assert plugin_instance.is_active()

    # 停用插件
    plugin_instance.deactivate()
    assert not plugin_instance.is_active()


def test_plugin_info():
    """测试插件信息"""
    from plugins.
    {slug}.plugin
    import plugin_instance

    # 检查插件基本信息
    assert hasattr(plugin_instance, 'name')
    assert hasattr(plugin_instance, 'slug')
    assert hasattr(plugin_instance, 'version')

    # 验证 slug 格式
    assert plugin_instance.slug == '{slug}'
    assert ' ' not in plugin_instance.slug
'''

        test_file = plugin_dir / "tests" / "test_plugin.py"
        self.write_file(test_file, content)


class ThemeScaffold(ScaffoldGenerator):
    """主题脚手架生成器"""

    def generate(self, theme_name: str, description: str = "", author: str = ""):
        """生成主题脚手架"""
        slug = theme_name.lower().replace(' ', '-').replace('_', '-')
        theme_dir = self.output_dir / slug

        print(f"\n🎨 Generating theme: {theme_name}")
        print(f"   Slug: {slug}")
        print(f"   Output: {theme_dir}")

        # 创建目录结构
        self.ensure_dir(theme_dir)
        self.ensure_dir(theme_dir / "templates")
        self.ensure_dir(theme_dir / "static" / "css")
        self.ensure_dir(theme_dir / "static" / "js")
        self.ensure_dir(theme_dir / "static" / "images")

        # 生成 theme.json
        self._generate_theme_json(theme_dir, theme_name, description, author)

        # 生成基础模板
        self._generate_base_template(theme_dir)

        # 生成样式文件
        self._generate_styles(theme_dir)

        # 生成 README
        self._generate_theme_readme(theme_dir, theme_name, description)

        print(f"\n✅ Theme '{theme_name}' scaffold generated successfully!")
        print(f"\n📝 Next steps:")
        print(f"   1. Edit {theme_dir}/theme.json with your theme details")
        print(f"   2. Customize templates in {theme_dir}/templates/")
        print(f"   3. Add styles in {theme_dir}/static/css/")
        print(f"   4. Preview the theme in admin panel")

    def _generate_theme_json(self, theme_dir: Path, name: str, description: str, author: str):
        """生成 theme.json"""
        import json

        theme_config = {
            "name": name,
            "slug": name.lower().replace(' ', '-').replace('_', '-'),
            "version": "1.0.0",
            "description": description or f"{name} theme for FastBlog",
            "author": author or "Your Name",
            "license": "MIT",
            "homepage": "",
            "screenshot": "screenshot.png",
            "tags": ["modern", "responsive"],
            "min_fastblog_version": "0.1.0",
            "settings": {
                "primary_color": "#3b82f6",
                "secondary_color": "#10b981",
                "font_family": "system-ui, -apple-system, sans-serif"
            }
        }

        theme_file = theme_dir / "theme.json"
        theme_file.write_text(json.dumps(theme_config, indent=2, ensure_ascii=False), encoding='utf-8')
        try:
            rel_path = theme_file.relative_to(Path.cwd())
            print(f"✅ Created: {rel_path}")
        except ValueError:
            print(f"✅ Created: {theme_file}")

    def _generate_base_template(self, theme_dir: Path):
        """生成基础模板"""
        content = '''<!DOCTYPE html>
<html lang="{{ locale }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - {{ site_name }}</title>

<!-- Theme Styles -->
    <link rel="stylesheet" href="{{ theme_static_url }}/css/style.css">

{% block head %}{% endblock %}
</head>
<body>
    <!-- Header -->
    <header class="site-header">
        <nav class="navbar">
            <div class="container">
                <a href="/" class="logo">{{ site_name }}</a>

<ul class="nav-menu">
                    <li><a href="/">Home</a></li>
                    <li><a href="/articles">Articles</a></li>
                    <li><a href="/categories">Categories</a></li>
                </ul>
            </div>
        </nav>
    </header>

<!-- Main Content -->
    <main class="site-main">
        <div class="container">
            {% block content %}{% endblock %}
        </div>
    </main>

<!-- Footer -->
    <footer class="site-footer">
        <div class="container">
            <p>&copy; {{ current_year }} {{ site_name }}. All rights reserved.</p>
        </div>
    </footer>

<!-- Theme Scripts -->
    <script src="{{ theme_static_url }}/js/main.js"></script>

{% block scripts %}{% endblock %}
</body>
</html>
'''

        template_file = theme_dir / "templates" / "base.html"
        self.write_file(template_file, content)

    def _generate_styles(self, theme_dir: Path):
        """生成样式文件"""
        content = '''/* Theme Styles */

:root {
    --primary-color: #3b82f6;
    --secondary-color: #10b981;
    --text-color: #1f2937;
    --bg-color: #ffffff;
    --border-color: #e5e7eb;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: system-ui, -apple-system, sans-serif;
    color: var(--text-color);
    background-color: var(--bg-color);
    line-height: 1.6;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 1rem;
}

/* Header */
.site-header {
    background: white;
    border-bottom: 1px solid var(--border-color);
    padding: 1rem 0;
}

.navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.logo {
    font-size: 1.5rem;
    font-weight: bold;
    color: var(--primary-color);
    text-decoration: none;
}

.nav-menu {
    display: flex;
    list-style: none;
    gap: 2rem;
}

.nav-menu a {
    color: var(--text-color);
    text-decoration: none;
    transition: color 0.2s;
}

.nav-menu a:hover {
    color: var(--primary-color);
}

/* Main Content */
.site-main {
    padding: 2rem 0;
    min-height: calc(100vh - 200px);
}

/* Footer */
.site-footer {
    background: #f9fafb;
    border-top: 1px solid var(--border-color);
    padding: 2rem 0;
    text-align: center;
}

/* Responsive */
@media (max-width: 768px) {
    .nav-menu {
        flex-direction: column;
        gap: 1rem;
    }
}
'''

        style_file = theme_dir / "static" / "css" / "style.css"
        self.write_file(style_file, content)

        # 生成 JavaScript 文件
        js_content = '''// Theme JavaScript

document.addEventListener('DOMContentLoaded', function() {
    console.log('Theme loaded');

// Add your custom JavaScript here
});
'''

        js_file = theme_dir / "static" / "js" / "main.js"
        self.write_file(js_file, js_content)

    def _generate_theme_readme(self, theme_dir: Path, name: str, description: str):
        """生成主题 README"""
        content = f'''# {name} Theme

{description or f"A modern theme for FastBlog"}

## Features

- Responsive design
- Modern UI
- Customizable colors
- SEO optimized

## Installation

1. Copy this theme to the `themes/` directory
2. Activate the theme from the admin panel

## Customization

Edit `theme.json` to customize:
- Colors
- Fonts
- Layout options

## Screenshots

Add a `screenshot.png` file (1200x800px recommended)

## License

MIT License
'''

        readme_file = theme_dir / "README.md"
        self.write_file(readme_file, content)


class ApiScaffold(ScaffoldGenerator):
    """API 端点脚手架生成器"""

    def generate(self, endpoint_name: str, description: str = ""):
        """生成 API 端点脚手架"""
        # 转换端点名称
        snake_case = endpoint_name.lower().replace(' ', '_').replace('-', '_')
        module_name = snake_case

        api_dir = self.output_dir / "v1"

        print(f"\n🌐 Generating API endpoint: {endpoint_name}")
        print(f"   Module: {module_name}")
        print(f"   Output: {api_dir}")

        self.ensure_dir(api_dir)

        # 生成 API 模块
        self._generate_api_module(api_dir, endpoint_name, module_name, description)

        print(f"\n✅ API endpoint '{endpoint_name}' scaffold generated successfully!")
        print(f"\n📝 Next steps:")
        print(f"   1. Implement your API logic in {api_dir}/{module_name}.py")
        print(f"   2. Register the router in src/api/v1/__init__.py")
        print(f"   3. Test your endpoints at /docs")

    def _generate_api_module(self, api_dir: Path, name: str, module_name: str, description: str):
        """生成 API 模块文件"""
        content = f'''"""
{name} API Endpoints

{description or f"API endpoints for managing {name.lower()}"}
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.extensions import get_async_db_session
from src.auth.dependencies import get_current_user

router = APIRouter(
    prefix="/{module_name}",
    tags=["{name}"],
    responses={{404: {{"description": "Not found"}}}},
)


@router.get("/")
async def list_{module_name}(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_async_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    List all {name.lower()}

    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    """
# Example implementation:
# from sqlalchemy import select
# stmt = select({name}).offset(skip).limit(limit)
# result = await db.execute(stmt)
# items = result.scalars().all()
# return {{"items": items, "total": len(items), "skip": skip, "limit": limit}}

return {{
        "items": [],
        "total": 0,
        "skip": skip,
        "limit": limit
    }}


@router.get("/{{item_id}}")
async def get_{module_name}(
    item_id: int,
    db: AsyncSession = Depends(get_async_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific {name.lower()} by ID
    """
# Example implementation:
# from sqlalchemy import select
# stmt = select({name}).where({name}.id == item_id)
# result = await db.execute(stmt)
# item = result.scalar_one_or_none()
    # if not item:
    #     raise HTTPException(status_code=404, detail="{name} not found")
    # return item

raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/")
async def create_{module_name}(
    # data: {name}CreateSchema,
    db: AsyncSession = Depends(get_async_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new {name.lower()}
    """
# Example implementation:
# new_item = {name}(**data.dict(), user_id=current_user.id)
# db.add(new_item)
# await db.commit()
# await db.refresh(new_item)
# return new_item

raise HTTPException(status_code=501, detail="Not implemented yet")


@router.put("/{{item_id}}")
async def update_{module_name}(
    item_id: int,
    # data: {name}UpdateSchema,
    db: AsyncSession = Depends(get_async_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    Update a {name.lower()}
    """
# Example implementation:
# stmt = select({name}).where({name}.id == item_id)
# result = await db.execute(stmt)
# item = result.scalar_one_or_none()
# if not item:
#     raise HTTPException(status_code=404, detail="{name} not found")
# for key, value in data.dict(exclude_unset=True).items():
#     setattr(item, key, value)
# await db.commit()
# await db.refresh(item)
# return item

raise HTTPException(status_code=501, detail="Not implemented yet")


@router.delete("/{{item_id}}")
async def delete_{module_name}(
    item_id: int,
    db: AsyncSession = Depends(get_async_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a {name.lower()}
    """
# Example implementation:
# stmt = select({name}).where({name}.id == item_id)
# result = await db.execute(stmt)
# item = result.scalar_one_or_none()
# if not item:
#     raise HTTPException(status_code=404, detail="{name} not found")
# await db.delete(item)
# await db.commit()
# return {{"message": "Deleted successfully"}}

raise HTTPException(status_code=501, detail="Not implemented yet")
'''

        api_file = api_dir / f"{module_name}.py"
        self.write_file(api_file, content)


def generate_plugin(name: str, description: str = "", author: str = ""):
    """生成插件脚手架的便捷函数"""
    generator = PluginScaffold(Path("plugins"))
    generator.generate(name, description, author)


def generate_theme(name: str, description: str = "", author: str = ""):
    """生成主题脚手架的便捷函数"""
    generator = ThemeScaffold(Path("themes"))
    generator.generate(name, description, author)


def generate_api(name: str, description: str = ""):
    """生成 API 端点脚手架的便捷函数"""
    generator = ApiScaffold(Path("src") / "api")
    generator.generate(name, description)
