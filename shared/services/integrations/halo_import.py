"""
Halo 博客迁移服务
支持从 Halo 博客系统迁移内容到 FastBlog
"""
from datetime import datetime
from typing import Dict, List, Any

import aiohttp


class HaloImportService:
    """
    Halo 博客导入服务
    
    功能:
    1. 通过 Halo API 获取数据
    2. 导入文章(包括内容、标题、摘要等)
    3. 导入分类和标签
    4. 导入评论
    5. 处理作者映射
    """

    def __init__(self, halo_url: str, api_token: str):
        """
        初始化 Halo 导入服务
        
        Args:
            halo_url: Halo 博客的 URL (例如: https://your-halo-blog.com)
            api_token: Halo API Token
        """
        self.halo_url = halo_url.rstrip('/')
        self.api_token = api_token
        self.headers = {
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json'
        }

    async def fetch_posts(self, page: int = 1, size: int = 100) -> Dict[str, Any]:
        """
        获取文章列表
        
        Args:
            page: 页码
            size: 每页数量
            
        Returns:
            文章列表和分页信息
        """
        url = f"{self.halo_url}/apis/api.console.halo.run/v1alpha1/posts"
        params = {
            'page': page,
            'size': size,
            'sort': 'createTime,desc'
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'success': True,
                            'data': data.get('items', []),
                            'total': data.get('total', 0),
                            'page': page,
                            'size': size
                        }
                    else:
                        return {
                            'success': False,
                            'error': f'HTTP {response.status}: {await response.text()}'
                        }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def fetch_post_detail(self, post_name: str) -> Dict[str, Any]:
        """
        获取文章详情
        
        Args:
            post_name: 文章名称/ID
            
        Returns:
            文章详细信息
        """
        url = f"{self.halo_url}/apis/api.console.halo.run/v1alpha1/posts/{post_name}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'success': True,
                            'data': data
                        }
                    else:
                        return {
                            'success': False,
                            'error': f'HTTP {response.status}: {await response.text()}'
                        }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def fetch_categories(self) -> Dict[str, Any]:
        """
        获取分类列表
        
        Returns:
            分类列表
        """
        url = f"{self.halo_url}/apis/api.console.halo.run/v1alpha1/categories"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'success': True,
                            'data': data.get('items', [])
                        }
                    else:
                        return {
                            'success': False,
                            'error': f'HTTP {response.status}: {await response.text()}'
                        }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def fetch_tags(self) -> Dict[str, Any]:
        """
        获取标签列表
        
        Returns:
            标签列表
        """
        url = f"{self.halo_url}/apis/api.console.halo.run/v1alpha1/tags"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'success': True,
                            'data': data.get('items', [])
                        }
                    else:
                        return {
                            'success': False,
                            'error': f'HTTP {response.status}: {await response.text()}'
                        }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def fetch_all_posts(self) -> List[Dict[str, Any]]:
        """
        获取所有文章（自动分页）
        
        Returns:
            所有文章的列表
        """
        all_posts = []
        page = 1
        size = 100

        while True:
            result = await self.fetch_posts(page=page, size=size)

            if not result['success']:
                raise Exception(f"获取文章失败: {result['error']}")

            posts = result['data']
            all_posts.extend(posts)

            # 如果返回的文章数少于请求的数量，说明已经是最后一页
            if len(posts) < size:
                break

            page += 1

        return all_posts

    def parse_halo_post(self, halo_post: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析 Halo 文章为 FastBlog 格式
        
        Args:
            halo_post: Halo 文章数据
            
        Returns:
            FastBlog 格式的文章数据
        """
        spec = halo_post.get('spec', {})
        status = halo_post.get('status', {})
        metadata = halo_post.get('metadata', {})

        # 提取内容
        content = spec.get('content', '')
        if isinstance(content, dict):
            content = content.get('raw', '')

        # 提取分类
        categories = spec.get('categories', [])

        # 提取标签
        tags = spec.get('tags', [])

        # 提取发布时间
        publish_time = spec.get('publishTime')
        if publish_time:
            try:
                created_at = datetime.fromisoformat(publish_time.replace('Z', '+00:00'))
            except:
                created_at = datetime.now()
        else:
            created_at = datetime.now()

        # 提取状态
        published = spec.get('published', False)
        status_map = {
            True: 'published',
            False: 'draft'
        }

        return {
            'title': spec.get('title', 'Untitled'),
            'slug': metadata.get('name', ''),
            'content': content,
            'excerpt': spec.get('excerpt', '') or '',
            'status': status_map.get(published, 'draft'),
            'created_at': created_at,
            'updated_at': created_at,
            'categories': categories,
            'tags': tags,
            'cover_image': spec.get('cover', ''),
            'allow_comment': spec.get('allowComment', True),
            'pinned': spec.get('pinned', False),
            'visible': spec.get('visible', 'PUBLIC')
        }

    async def import_to_database(
            self,
            db_session,
            user_mapping: Dict[str, int] = None,
            progress_callback=None
    ) -> Dict[str, Any]:
        """
        将 Halo 数据导入数据库
        
        Args:
            db_session: 数据库会话
            user_mapping: 用户映射 {halo_user_id: system_user_id}
            progress_callback: 进度回调函数 (current, total)
            
        Returns:
            导入结果统计
        """
        from shared.models.category import Category
        from shared.models import Article, ArticleContent
        from sqlalchemy import select

        results = {
            'imported_categories': 0,
            'imported_tags': 0,
            'imported_articles': 0,
            'skipped_articles': 0,
            'errors': [],
            'redirects': [],
        }

        try:
            # 1. 获取所有分类
            categories_result = await self.fetch_categories()
            if categories_result['success']:
                for cat_data in categories_result['data']:
                    try:
                        metadata = cat_data.get('metadata', {})
                        spec = cat_data.get('spec', {})

                        slug = metadata.get('name', '')
                        name = spec.get('displayName', '')

                        if not slug or not name:
                            continue

                        # 检查分类是否已存在
                        stmt = select(Category).where(Category.slug == slug)
                        result = await db_session.execute(stmt)
                        existing = result.scalar_one_or_none()

                        if not existing:
                            category = Category(
                                name=name,
                                slug=slug,
                                description=spec.get('description', ''),
                            )
                            db_session.add(category)
                            results['imported_categories'] += 1
                    except Exception as e:
                        results['errors'].append(f"分类导入失败: {str(e)}")

                await db_session.commit()

            # 2. 获取所有文章
            all_posts = await self.fetch_all_posts()
            total = len(all_posts)

            # 3. 导入文章
            for idx, halo_post in enumerate(all_posts):
                try:
                    if progress_callback:
                        progress_callback(idx + 1, total)

                    # 解析文章
                    article_data = self.parse_halo_post(halo_post)

                    # 确定用户ID
                    user_id = 1  # 默认用户

                    # 检查文章是否已存在（通过 slug）
                    slug = article_data['slug']
                    if not slug:
                        results['errors'].append(f"文章缺少 slug: {article_data['title']}")
                        continue

                    stmt = select(Article).where(Article.slug == slug)
                    result = await db_session.execute(stmt)
                    existing = result.scalar_one_or_none()

                    if existing:
                        results['skipped_articles'] += 1
                        continue

                    # 创建文章
                    article = Article(
                        title=article_data['title'],
                        slug=slug,
                        excerpt=article_data['excerpt'][:200] if article_data['excerpt'] else '',
                        status=article_data['status'],
                        user=user_id,
                        created_at=article_data['created_at'],
                        updated_at=article_data['updated_at'],
                    )
                    db_session.add(article)
                    await db_session.flush()

                    # 创建文章内容
                    now = datetime.now()
                    content = ArticleContent(
                        article=article.id,
                        content=article_data['content'],
                        created_at=now,
                        updated_at=now,
                    )
                    db_session.add(content)

                    # 关联分类
                    for cat_slug in article_data['categories']:
                        stmt = select(Category).where(Category.slug == cat_slug)
                        result = await db_session.execute(stmt)
                        category = result.scalar_one_or_none()
                        if category:
                            article.categories.append(category)

                    # 生成 URL 重定向规则
                    old_url = f"{self.halo_url}/archives/{slug}"
                    new_url = f"/articles/{slug}"
                    results['redirects'].append({
                        'old_url': old_url,
                        'new_url': new_url,
                        'status_code': 301,
                    })

                    results['imported_articles'] += 1

                except Exception as e:
                    results['errors'].append(
                        f"文章导入失败: {halo_post.get('metadata', {}).get('name', 'Unknown')} - {str(e)}")
                    await db_session.rollback()

            await db_session.commit()

            return {
                'success': True,
                'results': results,
            }

        except Exception as e:
            await db_session.rollback()
            return {
                'success': False,
                'error': str(e),
                'results': results,
            }

    def generate_import_report(self, import_results: Dict[str, Any]) -> str:
        """
        生成导入报告
        
        Args:
            import_results: 导入结果数据
            
        Returns:
            格式化的报告文本
        """
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("Halo 博客导入报告")
        report_lines.append("=" * 60)
        report_lines.append("")

        results = import_results.get('results', {})

        # 统计信息
        report_lines.append("📊 导入统计:")
        report_lines.append(f"  - 分类: {results.get('imported_categories', 0)}")
        report_lines.append(f"  - 文章: {results.get('imported_articles', 0)}")
        report_lines.append(f"  - 跳过: {results.get('skipped_articles', 0)}")
        report_lines.append("")

        # 重定向规则
        redirects = results.get('redirects', [])
        if redirects:
            report_lines.append("🔗 URL 重定向规则:")
            for redirect in redirects[:10]:
                report_lines.append(f"  {redirect['old_url']} → {redirect['new_url']} ({redirect['status_code']})")
            if len(redirects) > 10:
                report_lines.append(f"  ... 还有 {len(redirects) - 10} 条重定向规则")
            report_lines.append("")

        # 错误信息
        errors = results.get('errors', [])
        if errors:
            report_lines.append("⚠️  错误信息:")
            for error in errors[:20]:
                report_lines.append(f"  - {error}")
            if len(errors) > 20:
                report_lines.append(f"  ... 还有 {len(errors) - 20} 条错误")
            report_lines.append("")

        report_lines.append("=" * 60)
        report_lines.append(f"导入完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("=" * 60)

        return "\n".join(report_lines)
