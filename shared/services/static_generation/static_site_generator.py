"""
静态页面生成（SSG）服务

功能：
1. 生成文章静态页面
2. 生成列表页静态页面
3. 生成首页静态页面
4. 增量更新机制
5. 缓存管理
6. 批量生成支持
"""
import asyncio
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

import json

from jinja2 import Environment, FileSystemLoader
from shared.models.article import Article
from shared.models.category import Category
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.unified_logger import default_logger as logger


class StaticSiteGenerator:
    """
    静态站点生成器
    
    功能：
    1. 生成文章静态页面
    2. 生成列表页静态页面
    3. 生成首页静态页面
    4. 增量更新机制
    5. 缓存管理
    """

    def __init__(self, output_dir: str = "static_generated", template_dir: str = "themes/default"):
        self.output_dir = Path(output_dir)
        self.template_dir = Path(template_dir)
        self.generated_files: Dict[str, datetime] = {}
        self.cache_dir = self.output_dir / ".cache"

        # 确保目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 初始化Jinja2环境
        if self.template_dir.exists():
            self.jinja_env = Environment(
                loader=FileSystemLoader(str(self.template_dir)),
                autoescape=True,
                enable_async=True
            )
        else:
            self.jinja_env = None
            logger.warning(f"Template directory not found: {self.template_dir}")

    async def generate_article_page(self, db: AsyncSession, article_id: int,
                                    force: bool = False) -> Dict[str, Any]:
        """
        生成文章静态页面
        
        Args:
            db: 数据库会话
            article_id: 文章ID
            force: 是否强制重新生成
            
        Returns:
            生成结果
        """
        try:
            # 查询文章
            result = await db.execute(select(Article).where(Article.id == article_id))
            article = result.scalar_one_or_none()

            if not article:
                return {'success': False, 'error': f'Article {article_id} not found'}

            # 检查缓存
            cache_key = f"article_{article_id}"
            if not force and self._is_cache_valid(cache_key, article.updated_at):
                return {'success': True, 'cached': True, 'path': self._get_article_path(article)}

            # 生成HTML
            html_content = await self._render_article_template(article)

            # 保存文件
            output_path = self._get_article_path(article)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            # 更新缓存
            self._update_cache(cache_key)
            self.generated_files[str(output_path)] = datetime.now()

            logger.info(f"Generated static page for article {article_id}: {output_path}")

            return {
                'success': True,
                'cached': False,
                'path': str(output_path),
                'url': self._path_to_url(output_path)
            }

        except Exception as e:
            logger.error(f"Error generating article page {article_id}: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    async def generate_category_page(self, db: AsyncSession, category_id: int,
                                     page: int = 1, per_page: int = 20,
                                     force: bool = False) -> Dict[str, Any]:
        """
        生成分类列表页
        
        Args:
            db: 数据库会话
            category_id: 分类ID
            page: 页码
            per_page: 每页数量
            force: 是否强制重新生成
            
        Returns:
            生成结果
        """
        try:
            # 查询分类
            result = await db.execute(select(Category).where(Category.id == category_id))
            category = result.scalar_one_or_none()

            if not category:
                return {'success': False, 'error': f'Category {category_id} not found'}

            # 查询文章列表
            offset = (page - 1) * per_page
            result = await db.execute(
                select(Article)
                .where(Article.category_id == category_id, Article.status == 'published')
                .order_by(Article.created_at.desc())
                .offset(offset)
                .limit(per_page)
            )
            articles = result.scalars().all()

            # 获取总数
            result = await db.execute(
                select(Article)
                .where(Article.category_id == category_id, Article.status == 'published')
            )
            total_count = len(result.scalars().all())
            total_pages = (total_count + per_page - 1) // per_page

            # 检查缓存
            cache_key = f"category_{category_id}_page_{page}"
            if not force and self._is_cache_valid(cache_key):
                return {'success': True, 'cached': True, 'path': self._get_category_path(category, page)}

            # 生成HTML
            html_content = await self._render_category_template(
                category, articles, page, total_pages, total_count
            )

            # 保存文件
            output_path = self._get_category_path(category, page)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            # 更新缓存
            self._update_cache(cache_key)
            self.generated_files[str(output_path)] = datetime.now()

            logger.info(f"Generated category page {category_id} (page {page}): {output_path}")

            return {
                'success': True,
                'cached': False,
                'path': str(output_path),
                'url': self._path_to_url(output_path)
            }

        except Exception as e:
            logger.error(f"Error generating category page {category_id}: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    async def generate_homepage(self, db: AsyncSession, per_page: int = 20,
                                force: bool = False) -> Dict[str, Any]:
        """
        生成首页
        
        Args:
            db: 数据库会话
            per_page: 每页数量
            force: 是否强制重新生成
            
        Returns:
            生成结果
        """
        try:
            # 查询最新文章
            result = await db.execute(
                select(Article)
                .where(Article.status == 'published')
                .order_by(Article.created_at.desc())
                .limit(per_page)
            )
            articles = result.scalars().all()

            # 检查缓存
            cache_key = "homepage"
            if not force and self._is_cache_valid(cache_key):
                return {'success': True, 'cached': True, 'path': self.output_dir / "index.html"}

            # 生成HTML
            html_content = await self._render_homepage_template(articles)

            # 保存文件
            output_path = self.output_dir / "index.html"

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            # 更新缓存
            self._update_cache(cache_key)
            self.generated_files[str(output_path)] = datetime.now()

            logger.info(f"Generated homepage: {output_path}")

            return {
                'success': True,
                'cached': False,
                'path': str(output_path),
                'url': '/'
            }

        except Exception as e:
            logger.error(f"Error generating homepage: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    async def generate_all_articles(self, db: AsyncSession, batch_size: int = 50,
                                    force: bool = False) -> Dict[str, Any]:
        """
        批量生成所有文章静态页面
        
        Args:
            db: 数据库会话
            batch_size: 批次大小
            force: 是否强制重新生成
            
        Returns:
            生成统计
        """
        try:
            # 查询所有已发布文章
            result = await db.execute(
                select(Article)
                .where(Article.status == 'published')
                .order_by(Article.created_at.desc())
            )
            articles = result.scalars().all()

            total = len(articles)
            success_count = 0
            failed_count = 0
            cached_count = 0

            logger.info(f"Starting to generate {total} article pages...")

            # 分批处理
            for i in range(0, total, batch_size):
                batch = articles[i:i + batch_size]

                tasks = []
                for article in batch:
                    task = self.generate_article_page(db, article.id, force)
                    tasks.append(task)

                results = await asyncio.gather(*tasks, return_exceptions=True)

                for result in results:
                    if isinstance(result, Exception):
                        failed_count += 1
                        logger.error(f"Failed to generate article: {result}")
                    elif result.get('success'):
                        if result.get('cached'):
                            cached_count += 1
                        else:
                            success_count += 1
                    else:
                        failed_count += 1

                logger.info(f"Progress: {min(i + batch_size, total)}/{total}")

            return {
                'success': True,
                'total': total,
                'generated': success_count,
                'cached': cached_count,
                'failed': failed_count
            }

        except Exception as e:
            logger.error(f"Error generating all articles: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    async def clean_old_files(self, max_age_days: int = 30) -> Dict[str, Any]:
        """
        清理旧的静态文件
        
        Args:
            max_age_days: 最大保留天数
            
        Returns:
            清理统计
        """
        try:
            cleaned_count = 0

            for file_path_str, generated_time in list(self.generated_files.items()):
                file_path = Path(file_path_str)

                if file_path.exists():
                    age = datetime.now() - generated_time

                    if age > timedelta(days=max_age_days):
                        file_path.unlink()
                        del self.generated_files[file_path_str]
                        cleaned_count += 1

            logger.info(f"Cleaned {cleaned_count} old static files")

            return {
                'success': True,
                'cleaned_count': cleaned_count
            }

        except Exception as e:
            logger.error(f"Error cleaning old files: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def get_generation_stats(self) -> Dict[str, Any]:
        """获取生成统计信息"""
        return {
            'total_files': len(self.generated_files),
            'output_dir': str(self.output_dir),
            'template_dir': str(self.template_dir),
            'recently_generated': [
                {
                    'path': path,
                    'generated_at': time.isoformat()
                }
                for path, time in sorted(
                    self.generated_files.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10]
            ]
        }

    def _is_cache_valid(self, cache_key: str, updated_at: Optional[datetime] = None) -> bool:
        """检查缓存是否有效"""
        cache_file = self.cache_dir / f"{cache_key}.json"

        if not cache_file.exists():
            return False

        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)

            # 如果提供了更新时间，检查文件是否被修改
            if updated_at:
                cached_updated_at = cache_data.get('updated_at')
                if cached_updated_at and updated_at.isoformat() != cached_updated_at:
                    return False

            # 检查缓存时间（默认24小时）
            cached_time = datetime.fromisoformat(cache_data['generated_at'])
            if datetime.now() - cached_time > timedelta(hours=24):
                return False

            return True

        except Exception:
            return False

    def _update_cache(self, cache_key: str, updated_at: Optional[datetime] = None):
        """更新缓存"""
        cache_file = self.cache_dir / f"{cache_key}.json"

        cache_data = {
            'generated_at': datetime.now().isoformat(),
            'updated_at': updated_at.isoformat() if updated_at else None
        }

        with open(cache_file, 'w') as f:
            json.dump(cache_data, f)

    def _get_article_path(self, article: Article) -> Path:
        """获取文章输出路径"""
        # 使用日期和slug构建路径
        date_str = article.created_at.strftime('%Y/%m/%d')
        slug = article.slug or str(article.id)
        return self.output_dir / "articles" / date_str / f"{slug}.html"

    def _get_category_path(self, category: Category, page: int = 1) -> Path:
        """获取分类页输出路径"""
        slug = category.slug or str(category.id)
        if page == 1:
            return self.output_dir / "categories" / f"{slug}.html"
        else:
            return self.output_dir / "categories" / f"{slug}_page_{page}.html"

    def _path_to_url(self, path: Path) -> str:
        """将文件路径转换为URL"""
        relative_path = path.relative_to(self.output_dir)
        return f"/{relative_path.as_posix()}"

    async def _render_article_template(self, article: Article) -> str:
        """渲染文章模板"""
        if not self.jinja_env:
            return self._generate_simple_article_html(article)

        try:
            template = self.jinja_env.get_template("article.html")
            return await template.render_async(
                article=article,
                title=article.title,
                content=article.content,
                generated_at=datetime.now().isoformat()
            )
        except Exception as e:
            logger.error(f"Error rendering article template: {e}")
            return self._generate_simple_article_html(article)

    async def _render_category_template(self, category: Category, articles: List[Article],
                                        page: int, total_pages: int, total_count: int) -> str:
        """渲染分类模板"""
        if not self.jinja_env:
            return self._generate_simple_category_html(category, articles, page, total_pages, total_count)

        try:
            template = self.jinja_env.get_template("category.html")
            return await template.render_async(
                category=category,
                articles=articles,
                page=page,
                total_pages=total_pages,
                total_count=total_count,
                generated_at=datetime.now().isoformat()
            )
        except Exception as e:
            logger.error(f"Error rendering category template: {e}")
            return self._generate_simple_category_html(category, articles, page, total_pages, total_count)

    async def _render_homepage_template(self, articles: List[Article]) -> str:
        """渲染首页模板"""
        if not self.jinja_env:
            return self._generate_simple_homepage_html(articles)

        try:
            template = self.jinja_env.get_template("index.html")
            return await template.render_async(
                articles=articles,
                generated_at=datetime.now().isoformat()
            )
        except Exception as e:
            logger.error(f"Error rendering homepage template: {e}")
            return self._generate_simple_homepage_html(articles)

    def _generate_simple_article_html(self, article: Article) -> str:
        """生成简单的文章HTML（备用）"""
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{article.title}</title>
    <meta name="generator" content="FastBlog SSG">
    <meta name="generated-at" content="{datetime.now().isoformat()}">
</head>
<body>
    <article>
        <h1>{article.title}</h1>
        <div class="meta">
            <time>{article.created_at.strftime('%Y-%m-%d')}</time>
            <span>作者: {article.author_name if hasattr(article, 'author_name') else 'Unknown'}</span>
        </div>
        <div class="content">
            {article.content}
        </div>
    </article>
</body>
</html>"""

    def _generate_simple_category_html(self, category: Category, articles: List[Article],
                                       page: int, total_pages: int, total_count: int) -> str:
        """生成简单的分类HTML（备用）"""
        articles_html = "\n".join([
            f'<li><a href="/articles/{a.slug or a.id}.html">{a.title}</a></li>'
            for a in articles
        ])

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{category.name} - FastBlog</title>
</head>
<body>
    <h1>{category.name}</h1>
    <p>共 {total_count} 篇文章，第 {page}/{total_pages} 页</p>
    <ul>
        {articles_html}
    </ul>
</body>
</html>"""

    def _generate_simple_homepage_html(self, articles: List[Article]) -> str:
        """生成简单的首页HTML（备用）"""
        articles_html = "\n".join([
            f'<li><a href="/articles/{a.slug or a.id}.html">{a.title}</a></li>'
            for a in articles
        ])

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FastBlog</title>
</head>
<body>
    <h1>FastBlog</h1>
    <ul>
        {articles_html}
    </ul>
</body>
</html>"""


# 全局实例
ssg_service = StaticSiteGenerator()
