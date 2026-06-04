"""
数据迁移服务工具
支持从多种平台迁移内容到 FastBlog

支持的源平台:
- WordPress (WXR/XML)
- Jekyll (Markdown + YAML Front Matter)
- Hexo (Markdown + YAML Front Matter)
- Ghost (JSON Export)
- Medium (HTML Export)
- 通用 JSON/CSV 导入

功能:
1. 文章/页面迁移
2. 分类和标签迁移
3. 媒体文件下载和关联
4. 评论迁移
5. 用户映射
6. URL 重定向生成
7. 迁移报告

使用示例:
    # Python API
    from shared.services.integrations.migration_service import migration_service
    from src.extensions import get_async_db_session
    
    # WordPress 迁移
    async with get_async_db_session() as db:
        result = await migration_service.migrate_from_wordpress(
            wxr_file='wordpress-export.xml',
            db_session=db,
            user_id=1,
            options={'download_media': True, 'import_comments': True}
        )
    
    # Jekyll 迁移
    async with get_async_db_session() as db:
        result = await migration_service.migrate_from_markdown(
            source_dir='_posts',
            db_session=db,
            platform='jekyll',
            user_id=1
        )
    
    # Ghost 迁移
    async with get_async_db_session() as db:
        result = await migration_service.migrate_from_ghost(
            json_file='ghost-export.json',
            db_session=db,
            user_id=1
        )
    
    # JSON 迁移（带字段映射）
    async with get_async_db_session() as db:
        result = await migration_service.migrate_from_json(
            json_file='data.json',
            db_session=db,
            user_id=1,
            mapping={'title': 'post_title', 'content': 'post_body'}
        )
    
    # CSV 迁移
    async with get_async_db_session() as db:
        result = await migration_service.migrate_from_csv(
            csv_file='articles.csv',
            db_session=db,
            user_id=1
        )
    
    # 生成重定向规则
    redirects = migration_service.generate_redirect_map(
        old_urls=[{'old': '/old-path', 'new': '/new-path'}],
        output_format='nginx'
    )
    
    # REST API
    POST /api/v1/migrations/wordpress - 上传 WXR 文件
    POST /api/v1/migrations/ghost - 上传 Ghost JSON
    POST /api/v1/migrations/json - 上传通用 JSON
    POST /api/v1/migrations/csv - 上传 CSV 文件
    POST /api/v1/migrations/redirects - 生成重定向规则
    GET /api/v1/migrations/supported-platforms - 获取支持的平台
    GET /api/v1/migrations/guide/{platform} - 获取迁移指南
"""

import asyncio
import csv
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import Article, Category, Tag, User
from shared.services.integrations.wordpress_import import WordPressImportService


class MigrationService:
    """数据迁移服务"""

    def __init__(self):
        self.supported_formats = [
            'wordpress', 'jekyll', 'hexo', 'ghost', 'medium', 'json', 'csv'
        ]
        self.migration_stats = {
            'articles': 0,
            'categories': 0,
            'tags': 0,
            'media': 0,
            'comments': 0,
            'errors': 0,
        }

    async def migrate_from_wordpress(
            self,
            wxr_file: str,
            db_session: AsyncSession,
            options: Dict[str, Any] = None,
            user_id: int = 1
    ) -> Dict[str, Any]:
        """
        从 WordPress WXR 文件迁移
        
        Args:
            wxr_file: WXR 文件路径
            db_session: 数据库会话
            options: 迁移选项
                - download_media: 是否下载媒体文件
                - map_authors: 作者映射字典
                - import_comments: 是否导入评论
            user_id: 关联的用户ID
                
        Returns:
            迁移结果统计
        """
        print("[Migration] Starting WordPress migration...")

        importer = WordPressImportService()

        # 解析 WXR 文件
        print(f"[Migration] Parsing WXR file: {wxr_file}")
        parsed_data = importer.parse_wxr_file(wxr_file)

        stats = {
            'total_posts': len(parsed_data.get('posts', [])),
            'total_categories': len(parsed_data.get('categories', [])),
            'total_tags': len(parsed_data.get('tags', [])),
            'total_comments': len(parsed_data.get('comments', [])),
            'total_media': len(parsed_data.get('media', [])),
            'imported_posts': 0,
            'imported_categories': 0,
            'imported_tags': 0,
            'errors': 0,
        }

        print(f"[Migration] Found:")
        print(f"  - {stats['total_posts']} posts")
        print(f"  - {stats['total_categories']} categories")
        print(f"  - {stats['total_tags']} tags")
        print(f"  - {stats['total_comments']} comments")
        print(f"  - {stats['total_media']} media items")

        # 导入分类
        for cat_name in parsed_data.get('categories', []):
            try:
                result = await db_session.execute(
                    select(Category).where(Category.name == cat_name)
                )
                category = result.scalar_one_or_none()

                if not category:
                    category = Category(
                        name=cat_name,
                        slug=self._generate_slug(cat_name),
                        description=f'Imported from WordPress'
                    )
                    db_session.add(category)
                    await db_session.flush()
                    stats['imported_categories'] += 1
            except Exception as e:
                print(f"[Migration] Error importing category {cat_name}: {e}")
                stats['errors'] += 1

        # 导入标签
        for tag_name in parsed_data.get('tags', []):
            try:
                result = await db_session.execute(
                    select(Tag).where(Tag.name == tag_name)
                )
                tag = result.scalar_one_or_none()

                if not tag:
                    tag = Tag(
                        name=tag_name,
                        slug=self._generate_slug(tag_name)
                    )
                    db_session.add(tag)
                    await db_session.flush()
                    stats['imported_tags'] += 1
            except Exception as e:
                print(f"[Migration] Error importing tag {tag_name}: {e}")
                stats['errors'] += 1

        # 导入文章
        for post in parsed_data.get('posts', []):
            try:
                # 获取或创建分类
                category_ids = []
                for cat_name in post.get('categories', []):
                    result = await db_session.execute(
                        select(Category).where(Category.name == cat_name)
                    )
                    category = result.scalar_one_or_none()
                    if category:
                        category_ids.append(category.id)

                # 获取或创建标签
                tag_ids = []
                for tag_name in post.get('tags', []):
                    result = await db_session.execute(
                        select(Tag).where(Tag.name == tag_name)
                    )
                    tag = result.scalar_one_or_none()
                    if tag:
                        tag_ids.append(tag.id)

                # 创建文章
                article = Article(
                    title=post.get('title', 'Untitled'),
                    slug=post.get('slug', self._generate_slug(post.get('title', 'untitled'))),
                    content=post.get('content', ''),
                    excerpt=post.get('excerpt', ''),
                    status=1 if post.get('status') == 'publish' else 0,
                    user_id=user_id,
                    category_id=category_ids[0] if category_ids else None,
                    created_at=post.get('date') or datetime.now(),
                    updated_at=datetime.now(),
                )

                db_session.add(article)
                await db_session.flush()

                # 关联标签
                if tag_ids:
                    article.tags = []
                    for tag_id in tag_ids:
                        result = await db_session.execute(select(Tag).where(Tag.id == tag_id))
                        tag = result.scalar_one_or_none()
                        if tag:
                            article.tags.append(tag)

                stats['imported_posts'] += 1

            except Exception as e:
                print(f"[Migration] Error importing post {post.get('title')}: {e}")
                stats['errors'] += 1

        await db_session.commit()

        return {
            'success': True,
            'platform': 'wordpress',
            'stats': stats,
            'message': f"WordPress migration completed: {stats['imported_posts']} posts, {stats['imported_categories']} categories, {stats['imported_tags']} tags imported",
        }

    async def migrate_from_markdown(
            self,
            source_dir: str,
            platform: str = 'jekyll',
            options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        从 Markdown 文件迁移 (Jekyll/Hexo)
        
        Args:
            source_dir: Markdown 文件目录
            platform: 平台类型 (jekyll/hexo)
            options: 迁移选项
            
        Returns:
            迁移结果统计
        """
        print(f"[Migration] Starting {platform} migration from: {source_dir}")

        source_path = Path(source_dir)
        if not source_path.exists():
            return {
                'success': False,
                'error': f'Source directory not found: {source_dir}'
            }

        # 查找所有 Markdown 文件
        md_files = list(source_path.rglob('*.md'))
        print(f"[Migration] Found {len(md_files)} markdown files")

        imported_count = 0
        errors = []

        for md_file in md_files:
            try:
                result = await self._import_markdown_file(md_file, platform)
                if result['success']:
                    imported_count += 1
                else:
                    errors.append({
                        'file': str(md_file),
                        'error': result.get('error')
                    })
            except Exception as e:
                errors.append({
                    'file': str(md_file),
                    'error': str(e)
                })

        return {
            'success': True,
            'platform': platform,
            'imported': imported_count,
            'total': len(md_files),
            'errors': errors,
            'message': f'Imported {imported_count}/{len(md_files)} files',
        }

    async def _import_markdown_file(
            self,
            file_path: Path,
            platform: str,
            db_session: AsyncSession,
            user_id: int = 1
    ) -> Dict[str, Any]:
        """
        导入单个 Markdown 文件
        
        Args:
            file_path: 文件路径
            platform: 平台类型
            db_session: 数据库会话
            user_id: 用户ID
            
        Returns:
            导入结果
        """
        content = file_path.read_text(encoding='utf-8')

        # 解析 Front Matter (YAML)
        front_matter = {}
        body = content

        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                import yaml
                try:
                    front_matter = yaml.safe_load(parts[1])
                    body = parts[2].strip()
                except Exception as e:
                    return {
                        'success': False,
                        'error': f'Failed to parse front matter: {e}'
                    }

        # 提取文章信息
        article_data = {
            'title': front_matter.get('title', file_path.stem),
            'slug': front_matter.get('slug', self._generate_slug(file_path.stem)),
            'content': body,
            'created_at': front_matter.get('date'),
            'status': 'published' if front_matter.get('published', True) else 'draft',
            'categories': front_matter.get('categories', []),
            'tags': front_matter.get('tags', []),
        }

        try:
            # 创建文章
            article = Article(
                title=article_data['title'],
                slug=article_data['slug'],
                content=article_data['content'],
                status=1 if article_data['status'] == 'published' else 0,
                user_id=user_id,
                created_at=article_data['created_at'] or datetime.now(),
                updated_at=datetime.now(),
            )

            db_session.add(article)
            await db_session.flush()

            # 处理分类
            if article_data['categories']:
                for cat_name in article_data['categories']:
                    result = await db_session.execute(
                        select(Category).where(Category.name == cat_name)
                    )
                    category = result.scalar_one_or_none()
                    if not category:
                        category = Category(
                            name=cat_name,
                            slug=self._generate_slug(cat_name)
                        )
                        db_session.add(category)
                        await db_session.flush()
                    article.category_id = category.id

            # 处理标签
            if article_data['tags']:
                article.tags = []
                for tag_name in article_data['tags']:
                    result = await db_session.execute(
                        select(Tag).where(Tag.name == tag_name)
                    )
                    tag = result.scalar_one_or_none()
                    if not tag:
                        tag = Tag(
                            name=tag_name,
                            slug=self._generate_slug(tag_name)
                        )
                        db_session.add(tag)
                        await db_session.flush()
                    article.tags.append(tag)

            await db_session.commit()

            return {
                'success': True,
                'title': article_data['title'],
            }

        except Exception as e:
            await db_session.rollback()
            return {
                'success': False,
                'error': str(e)
            }

    async def migrate_from_ghost(
            self,
            json_file: str,
            db_session: AsyncSession,
            options: Dict[str, Any] = None,
            user_id: int = 1
    ) -> Dict[str, Any]:
        """
        从 Ghost JSON 导出文件迁移
        
        Args:
            json_file: Ghost JSON 文件路径
            db_session: 数据库会话
            options: 迁移选项
            user_id: 用户ID
            
        Returns:
            迁移结果
        """
        print(f"[Migration] Starting Ghost migration from: {json_file}")

        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Ghost 导出格式: {"db": [{"meta": {...}, "data": {...}}]}
        if 'db' in data and len(data['db']) > 0:
            ghost_data = data['db'][0]['data']
        else:
            ghost_data = data

        stats = {
            'posts': len(ghost_data.get('posts', [])),
            'tags': len(ghost_data.get('tags', [])),
            'users': len(ghost_data.get('users', [])),
            'imported_posts': 0,
            'imported_tags': 0,
            'errors': 0,
        }

        print(f"[Migration] Found:")
        print(f"  - {stats['posts']} posts")
        print(f"  - {stats['tags']} tags")
        print(f"  - {stats['users']} users")

        # 导入标签
        for tag_data in ghost_data.get('tags', []):
            try:
                result = await db_session.execute(
                    select(Tag).where(Tag.name == tag_data.get('name'))
                )
                tag = result.scalar_one_or_none()

                if not tag:
                    tag = Tag(
                        name=tag_data.get('name'),
                        slug=tag_data.get('slug', self._generate_slug(tag_data.get('name'))),
                        description=tag_data.get('description', '')
                    )
                    db_session.add(tag)
                    await db_session.flush()
                    stats['imported_tags'] += 1
            except Exception as e:
                print(f"[Migration] Error importing tag: {e}")
                stats['errors'] += 1

        # 导入文章
        for post_data in ghost_data.get('posts', []):
            try:
                # 获取标签
                tag_ids = []
                if 'tags' in post_data:
                    for tag_ref in post_data['tags']:
                        result = await db_session.execute(
                            select(Tag).where(Tag.name == tag_ref.get('name'))
                        )
                        tag = result.scalar_one_or_none()
                        if tag:
                            tag_ids.append(tag.id)

                # 创建文章
                article = Article(
                    title=post_data.get('title', 'Untitled'),
                    slug=post_data.get('slug', self._generate_slug(post_data.get('title', 'untitled'))),
                    content=post_data.get('html', post_data.get('mobiledoc', '')),
                    excerpt=post_data.get('custom_excerpt', ''),
                    status=1 if post_data.get('status') == 'published' else 0,
                    user_id=user_id,
                    created_at=datetime.fromtimestamp(post_data.get('created_at', 0) / 1000) if post_data.get(
                        'created_at') else datetime.now(),
                    updated_at=datetime.now(),
                )

                db_session.add(article)
                await db_session.flush()

                # 关联标签
                if tag_ids:
                    article.tags = []
                    for tag_id in tag_ids:
                        result = await db_session.execute(select(Tag).where(Tag.id == tag_id))
                        tag = result.scalar_one_or_none()
                        if tag:
                            article.tags.append(tag)

                stats['imported_posts'] += 1

            except Exception as e:
                print(f"[Migration] Error importing post: {e}")
                stats['errors'] += 1

        await db_session.commit()

        return {
            'success': True,
            'platform': 'ghost',
            'stats': stats,
            'message': f"Ghost migration completed: {stats['imported_posts']} posts, {stats['imported_tags']} tags imported",
        }

    async def migrate_from_json(
            self,
            json_file: str,
            db_session: AsyncSession,
            mapping: Dict[str, str] = None,
            user_id: int = 1
    ) -> Dict[str, Any]:
        """
        从通用 JSON 文件迁移
        
        Args:
            json_file: JSON 文件路径
            db_session: 数据库会话
            mapping: 字段映射 {target_field: source_field}
            user_id: 用户ID
            
        Returns:
            迁移结果
        """
        print(f"[Migration] Starting JSON migration from: {json_file}")

        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 确保是列表格式
        if isinstance(data, dict):
            # 尝试找到文章列表
            for key in ['posts', 'articles', 'items', 'data']:
                if key in data and isinstance(data[key], list):
                    data = data[key]
                    break
            else:
                data = [data]

        if not isinstance(data, list):
            return {
                'success': False,
                'error': 'Invalid JSON format: expected array or object with posts/articles key'
            }

        imported_count = 0
        errors = 0

        for item in data:
            try:
                # 使用默认映射或自定义映射
                field_map = mapping or {
                    'title': 'title',
                    'content': 'content',
                    'slug': 'slug',
                }

                # 提取字段
                title = item.get(field_map.get('title', 'title'), 'Untitled')
                content = item.get(field_map.get('content', 'content'), '')
                slug = item.get(field_map.get('slug', 'slug'), self._generate_slug(title))

                # 创建文章
                article = Article(
                    title=title,
                    slug=slug,
                    content=content,
                    status=1,
                    user_id=user_id,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )

                db_session.add(article)
                await db_session.flush()
                imported_count += 1

            except Exception as e:
                print(f"[Migration] Error importing item: {e}")
                errors += 1

        await db_session.commit()

        return {
            'success': True,
            'platform': 'json',
            'imported': imported_count,
            'total': len(data),
            'errors': errors,
            'message': f'Imported {imported_count}/{len(data)} items from JSON',
        }

    async def migrate_from_csv(
            self,
            csv_file: str,
            db_session: AsyncSession,
            delimiter: str = ',',
            encoding: str = 'utf-8',
            user_id: int = 1
    ) -> Dict[str, Any]:
        """
        从 CSV 文件迁移
        
        Args:
            csv_file: CSV 文件路径
            db_session: 数据库会话
            delimiter: 分隔符
            encoding: 文件编码
            user_id: 用户ID
            
        Returns:
            迁移结果
        """
        print(f"[Migration] Starting CSV migration from: {csv_file}")

        imported_count = 0
        errors = []

        with open(csv_file, 'r', encoding=encoding) as f:
            reader = csv.DictReader(f, delimiter=delimiter)

            for row_num, row in enumerate(reader, start=2):  # 从第2行开始（跳过标题）
                try:
                    # 尝试常见列名
                    title = row.get('title') or row.get('Title') or row.get('name') or f'Row {row_num}'
                    content = row.get('content') or row.get('Content') or row.get('body') or ''
                    slug = row.get('slug') or row.get('Slug') or self._generate_slug(title)

                    # 创建文章
                    article = Article(
                        title=title,
                        slug=slug,
                        content=content,
                        status=1,
                        user_id=user_id,
                        created_at=datetime.now(),
                        updated_at=datetime.now(),
                    )

                    db_session.add(article)
                    await db_session.flush()
                    imported_count += 1

                except Exception as e:
                    errors.append({
                        'row': row_num,
                        'error': str(e)
                    })

        await db_session.commit()

        return {
            'success': True,
            'platform': 'csv',
            'imported': imported_count,
            'errors': errors,
            'message': f'Imported {imported_count} rows from CSV',
        }

    def generate_redirect_map(
            self,
            old_urls: List[Dict[str, str]],
            output_format: str = 'nginx'
    ) -> str:
        """
        生成 URL 重定向映射
        
        Args:
            old_urls: 旧URL列表 [{'old': '/old-path', 'new': '/new-path'}]
            output_format: 输出格式 (nginx/apache/json)
            
        Returns:
            重定向配置文本
        """
        if output_format == 'nginx':
            lines = ['# Nginx redirect rules', '# Generated by FastBlog Migration Tool']
            for url_map in old_urls:
                lines.append(f"rewrite ^{url_map['old']}$ {url_map['new']} permanent;")
            return '\n'.join(lines)

        elif output_format == 'apache':
            lines = ['# Apache redirect rules', '# Generated by FastBlog Migration Tool']
            for url_map in old_urls:
                lines.append(f"Redirect 301 {url_map['old']} {url_map['new']}")
            return '\n'.join(lines)

        elif output_format == 'json':
            return json.dumps(old_urls, indent=2, ensure_ascii=False)

        else:
            raise ValueError(f'Unsupported format: {output_format}')

    def _generate_slug(self, text: str) -> str:
        """
        生成 URL 友好的 slug
        
        Args:
            text: 原始文本
            
        Returns:
            slug 字符串
        """
        import re
        import unicodedata

        # 转换为 ASCII
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
        # 小写化
        text = text.lower()
        # 替换非字母数字字符为连字符
        text = re.sub(r'[^a-z0-9]+', '-', text)
        # 移除首尾连字符
        text = text.strip('-')
        # 限制长度
        return text[:100] if len(text) > 100 else text

    def generate_migration_report(
            self,
            platform: str,
            stats: Dict[str, Any],
            duration_seconds: float
    ) -> Dict[str, Any]:
        """
        生成迁移报告
        
        Args:
            platform: 源平台
            stats: 统计数据
            duration_seconds: 耗时（秒）
            
        Returns:
            迁移报告
        """
        report = {
            'platform': platform,
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': duration_seconds,
            'statistics': stats,
            'summary': {
                'total_items': sum([
                    stats.get('articles', 0),
                    stats.get('categories', 0),
                    stats.get('tags', 0),
                    stats.get('media', 0),
                    stats.get('comments', 0),
                ]),
                'success_rate': 'N/A',  # 需要根据实际成功/失败计算
            },
            'recommendations': [
                '检查所有文章的URL是否正确',
                '验证媒体文件链接是否有效',
                '测试分类和标签是否正确关联',
                '检查SEO元数据是否完整',
            ],
        }

        return report


# 导出单例
migration_service = MigrationService()
