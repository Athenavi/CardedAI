"""
WordPress XML 导入服务
支持从 WordPress 导出的 WXR (WordPress eXtended RSS) 文件导入文章、分类、标签等内容
"""

import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse


# aiohttp 仅在 download_media_files 中使用，延迟导入避免模块加载失败


class WordPressImportService:
    """
    WordPress XML 导入服务

    功能:
    1. 解析 WordPress WXR 文件
    2. 导入文章(包括内容、标题、摘要等)
    3. 导入分类和标签
    4. 导入媒体文件引用
    5. 导入评论
    6. 处理作者映射
    """

    def __init__(self):
        self.namespaces = {
            'content': 'http://purl.org/rss/1.0/modules/content/',
            'wfw': 'http://wellformedweb.org/CommentAPI/',
            'dc': 'http://purl.org/dc/elements/1.1/',
            'wp': 'http://wordpress.org/export/1.2/',
            'excerpt': 'http://wordpress.org/export/1.2/excerpt/',
        }

    def parse_wxr_file(self, file_path: str) -> Dict[str, Any]:
        """
        解析 WordPress WXR 文件

        Args:
            file_path: WXR 文件路径

        Returns:
            包含所有解析数据的字典
        """
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            # 提取频道信息
            channel = root.find('channel')
            if channel is None:
                raise ValueError("无效的 WXR 文件格式")

            data = {
                'site_info': self._parse_site_info(channel),
                'authors': self._parse_authors(channel),
                'categories': self._parse_categories(channel),
                'tags': self._parse_tags(channel),
                'articles': self._parse_articles(channel),
                'media': self._parse_media(channel),
            }

            return {
                'success': True,
                'data': data,
                'stats': self._calculate_stats(data)
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _parse_site_info(self, channel) -> Dict[str, str]:
        """解析站点基本信息"""
        return {
            'title': self._get_text(channel, 'title'),
            'link': self._get_text(channel, 'link'),
            'description': self._get_text(channel, 'description'),
            'pubDate': self._get_text(channel, 'pubDate'),
            'language': self._get_text(channel, 'language', 'zh-CN'),
        }

    def _parse_authors(self, channel) -> List[Dict[str, str]]:
        """解析作者信息"""
        authors = []
        for author in channel.findall('wp:author', self.namespaces):
            authors.append({
                'author_id': self._get_text(author, 'wp:author_id'),
                'login': self._get_text(author, 'wp:author_login'),
                'email': self._get_text(author, 'wp:author_email'),
                'display_name': self._get_text(author, 'wp:author_display_name'),
                'first_name': self._get_text(author, 'wp:author_first_name'),
                'last_name': self._get_text(author, 'wp:author_last_name'),
            })
        return authors

    def _parse_categories(self, channel) -> List[Dict[str, Any]]:
        """解析分类"""
        categories = []
        for category in channel.findall('wp:category', self.namespaces):
            cat_name = category.find('wp:cat_name', self.namespaces)
            cat_nicename = category.find('wp:category_nicename', self.namespaces)
            cat_parent = category.find('wp:category_parent', self.namespaces)

            categories.append({
                'name': cat_name.text if cat_name is not None else '',
                'slug': cat_nicename.text if cat_nicename is not None else '',
                'parent': cat_parent.text if cat_parent is not None else '',
                'description': '',
            })
        return categories

    def _parse_tags(self, channel) -> List[Dict[str, str]]:
        """解析标签"""
        tags = []
        for tag in channel.findall('wp:tag', self.namespaces):
            tag_name = tag.find('wp:tag_name', self.namespaces)
            tag_slug = tag.find('wp:tag_slug', self.namespaces)

            tags.append({
                'name': tag_name.text if tag_name is not None else '',
                'slug': tag_slug.text if tag_slug is not None else '',
            })
        return tags

    def _parse_articles(self, channel) -> List[Dict[str, Any]]:
        """解析文章"""
        ns = self.namespaces
        articles = []
        for item in channel.findall('item'):
            post_type = self._get_text(item, 'wp:post_type', ns)

            # 只处理文章类型
            if post_type != 'post' and post_type != 'page':
                continue

            article = {
                'type': post_type,
                'title': self._get_text(item, 'title'),
                'link': self._get_text(item, 'link'),
                'pubDate': self._get_text(item, 'pubDate'),
                'author': self._get_text(item, 'dc:creator', ns),
                'content': self._get_text(item, 'content:encoded', ns),
                'excerpt': self._get_text(item, 'excerpt:encoded', ns),
                'status': self._get_text(item, 'wp:status', ns),
                'slug': self._get_text(item, 'wp:post_name', ns),
                'created_at': self._parse_date(self._get_text(item, 'wp:post_date', ns)),
                'modified_at': self._parse_date(self._get_text(item, 'wp:post_modified', ns)),
                'categories': [],
                'tags': [],
                'comments': [],
                'featured_image': None,
            }

            # 解析分类
            for category in item.findall('category'):
                domain = category.get('domain', '')
                nicename = category.get('nicename', '')

                if domain == 'category':
                    article['categories'].append({
                        'name': category.text or '',
                        'slug': nicename,
                    })
                elif domain == 'post_tag':
                    article['tags'].append({
                        'name': category.text or '',
                        'slug': nicename,
                    })

            # 解析评论
            for comment in item.findall('wp:comment', ns):
                article['comments'].append(self._parse_comment(comment))

            # 解析特色图片（遍历 postmeta 寻找 _thumbnail_id）
            for meta in item.findall('wp:postmeta', ns):
                meta_key = self._get_text(meta, 'wp:meta_key', ns)
                if meta_key == '_thumbnail_id':
                    article['featured_image'] = self._get_text(meta, 'wp:meta_value', ns)
                    break

            articles.append(article)

        return articles

    def _parse_comment(self, comment_elem) -> Dict[str, Any]:
        """解析评论"""
        ns = self.namespaces
        return {
            'id': self._get_text(comment_elem, 'wp:comment_id', ns),
            'author': self._get_text(comment_elem, 'wp:comment_author', ns),
            'email': self._get_text(comment_elem, 'wp:comment_author_email', ns),
            'url': self._get_text(comment_elem, 'wp:comment_author_url', ns),
            'ip': self._get_text(comment_elem, 'wp:comment_author_IP', ns),
            'date': self._parse_date(self._get_text(comment_elem, 'wp:comment_date', ns)),
            'content': self._get_text(comment_elem, 'wp:comment_content', ns),
            'approved': self._get_text(comment_elem, 'wp:comment_approved', ns) == '1',
            'parent': self._get_text(comment_elem, 'wp:comment_parent', ns),
        }

    def _parse_media(self, channel) -> List[Dict[str, Any]]:
        """解析媒体文件"""
        ns = self.namespaces
        media = []
        for item in channel.findall('item'):
            post_type = self._get_text(item, 'wp:post_type', ns)

            if post_type != 'attachment':
                continue

            media_item = {
                'id': self._get_text(item, 'wp:post_id', ns),
                'title': self._get_text(item, 'title'),
                'url': self._get_text(item, 'wp:attachment_url', ns),
                'mime_type': self._get_text(item, 'wp:post_mime_type', ns),
                'created_at': self._parse_date(self._get_text(item, 'wp:post_date', ns)),
            }
            media.append(media_item)

        return media

    def _get_text(self, parent, path, namespaces=None, default=''):
        """安全获取文本内容"""
        try:
            if namespaces:
                elem = parent.find(path, namespaces)
            else:
                elem = parent.find(path)
            return elem.text.strip() if elem is not None and elem.text else default
        except:
            return default

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """解析日期字符串"""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        except:
            try:
                return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%SZ')
            except:
                return None

    def _calculate_stats(self, data: Dict[str, Any]) -> Dict[str, int]:
        """计算导入统计信息"""
        return {
            'total_articles': len(data['articles']),
            'total_pages': sum(1 for a in data['articles'] if a['type'] == 'page'),
            'total_posts': sum(1 for a in data['articles'] if a['type'] == 'post'),
            'total_categories': len(data['categories']),
            'total_tags': len(data['tags']),
            'total_comments': sum(len(a['comments']) for a in data['articles']),
            'total_media': len(data['media']),
            'total_authors': len(data['authors']),
        }

    async def import_to_database(self, parsed_data: Dict[str, Any], db_session, user_mapping: Dict[str, int] = None) -> \
            Dict[str, Any]:
        """
        将解析的数据导入数据库

        Args:
            parsed_data: parse_wxr_file 返回的解析数据
            db_session: 数据库会话
            user_mapping: 作者ID映射 {wordpress_author_id: system_user_id}

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
            'imported_comments': 0,
            'imported_media': 0,
            'skipped_articles': 0,
            'errors': [],
            'redirects': [],
        }

        try:
            # 1. 导入分类
            for cat_data in parsed_data['categories']:
                try:
                    # 检查分类是否已存在
                    stmt = select(Category).where(Category.slug == cat_data['slug'])
                    result = await db_session.execute(stmt)
                    existing = result.scalar_one_or_none()

                    if not existing:
                        category = Category(
                            name=cat_data['name'],
                            slug=cat_data['slug'],
                            description=cat_data.get('description', ''),
                        )
                        db_session.add(category)
                        results['imported_categories'] += 1
                except Exception as e:
                    results['errors'].append(f"分类导入失败: {cat_data['name']} - {str(e)}")

            await db_session.commit()

            # 2. 导入标签 本系统无tags表
            # for tag_data in parsed_data['tags']:
            #     try:
            #         stmt = select(Tag).where(Tag.slug == tag_data['slug'])
            #         result = await db_session.execute(stmt)
            #         existing = result.scalar_one_or_none()
            #
            #         if not existing:
            #             tag = Tag(
            #                 name=tag_data['name'],
            #                 slug=tag_data['slug'],
            #             )
            #             db_session.add(tag)
            #             results['imported_tags'] += 1
            #     except Exception as e:
            #         results['errors'].append(f"标签导入失败: {tag_data['name']} - {str(e)}")
            #
            # await db_session.commit()

            # 3. 导入文章
            for idx, article_data in enumerate(parsed_data['articles']):
                try:
                    # 确定用户ID
                    user_id = 1  # 默认用户
                    if user_mapping and article_data['author'] in user_mapping:
                        user_id = user_mapping[article_data['author']]

                    # 生成有效的 slug
                    slug = article_data.get('slug', '').strip()
                    if not slug:
                        # slug 为空时从 title 生成，再不行用 index 兜底
                        slug = re.sub(r'[^\w\-]', '-', (article_data.get('title') or f'imported-{idx}').strip())[
                            :50].strip('-')
                        if not slug:
                            slug = f'imported-{idx}'

                    # 检查文章是否已存在（通过 slug）
                    stmt = select(Article).where(Article.slug == slug)
                    result = await db_session.execute(stmt)
                    existing = result.scalar_one_or_none()

                    if existing:
                        results['skipped_articles'] += 1
                        continue

                    # 创建文章
                    # tags_list 是逗号分隔的字符串，不是列表
                    tags_str = ','.join(
                        t.get('name', '') for t in article_data.get('tags', []) if t.get('name')
                    )
                    article = Article(
                        title=article_data.get('title') or f'未命名文章 {idx + 1}',
                        slug=slug,
                        excerpt=(article_data.get('excerpt') or '')[:200],
                        status=self._map_status(article_data.get('status', 'draft')),
                        tags_list=tags_str[:255] if tags_str else '',
                        post_type='page' if article_data.get('type') == 'page' else 'article',
                        user=user_id,
                        created_at=article_data.get('created_at') or datetime.now(),
                        updated_at=article_data.get('modified_at') or datetime.now(),
                    )
                    db_session.add(article)
                    await db_session.flush()  # 获取文章ID

                    # 创建文章内容（content 为 NOT NULL，确保不为 None）
                    now = datetime.now()
                    content = ArticleContent(
                        article=article.id,
                        content=article_data.get('content') or '',
                        created_at=now,
                        updated_at=now,
                    )
                    db_session.add(content)

                    # 关联分类（Article 只有单个 category FK，取第一个匹配的分类）
                    if article_data.get('categories'):
                        for cat_info in article_data['categories']:
                            stmt = select(Category).where(Category.slug == cat_info.get('slug'))
                            result = await db_session.execute(stmt)
                            category = result.scalar_one_or_none()
                            if category:
                                article.category = category.id
                                break  # 只取第一个分类

                    # 生成 URL 重定向规则
                    old_url = article_data.get('link')
                    if old_url:
                        new_url = f"/articles/{slug}"
                        results['redirects'].append({
                            'old_url': old_url,
                            'new_url': new_url,
                            'status_code': 301,
                        })

                    results['imported_articles'] += 1

                except Exception as e:
                    results['errors'].append(f"文章导入失败: {article_data.get('title', 'Unknown')} - {str(e)}")
                    # 不 rollback 整个事务，只跳过当前文章（已 flush 的需 expunge）
                    try:
                        if 'article' in dir() and article in db_session:
                            await db_session.expunge(article)
                    except Exception:
                        pass

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

    def _map_status(self, wp_status: str) -> int:
        """映射 WordPress 状态到系统状态（Article.status 是 Integer: -1=deleted, 0=draft, 1=published）"""
        status_map = {
            'publish': 1,
            'draft': 0,
            'pending': 0,
            'private': 1,
            'trash': -1,
        }
        return status_map.get(wp_status, 0)

    async def download_media_files(self, media_list: List[Dict[str, Any]], progress_callback=None) -> Dict[str, Any]:
        """
        下载媒体文件

        Args:
            media_list: 媒体文件列表
            progress_callback: 进度回调函数 (current, total)

        Returns:
            下载结果统计
        """
        try:
            import aiohttp
        except ImportError:
            return {
                'downloaded': 0,
                'failed': 0,
                'skipped': len(media_list),
                'errors': ['aiohttp 未安装，无法下载媒体文件。请运行: pip install aiohttp'],
                'media_mapping': {},
            }
        results = {
            'downloaded': 0,
            'failed': 0,
            'skipped': 0,
            'errors': [],
            'media_mapping': {},  # {old_url: new_local_path}
        }

        media_dir = Path("media/wordpress_import")
        media_dir.mkdir(parents=True, exist_ok=True)

        total = len(media_list)

        for idx, media_item in enumerate(media_list):
            try:
                if progress_callback:
                    progress_callback(idx + 1, total)

                url = media_item.get('url')
                if not url:
                    results['skipped'] += 1
                    continue

                # 解析文件名
                parsed_url = urlparse(url)
                filename = os.path.basename(parsed_url.path)

                # 生成唯一文件名
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                local_filename = f"{timestamp}_{filename}"
                local_path = media_dir / local_filename

                # 如果文件已存在，跳过
                if local_path.exists():
                    results['skipped'] += 1
                    results['media_mapping'][url] = str(local_path)
                    continue

                # 下载文件
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as response:
                        if response.status == 200:
                            content = await response.read()
                            with open(local_path, 'wb') as f:
                                f.write(content)

                            results['downloaded'] += 1
                            results['media_mapping'][url] = str(local_path)
                        else:
                            results['failed'] += 1
                            results['errors'].append(f"下载失败: {url} - HTTP {response.status}")

            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"下载错误: {media_item.get('url', 'Unknown')} - {str(e)}")

        return results

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
        report_lines.append("WordPress 导入报告")
        report_lines.append("=" * 60)
        report_lines.append("")

        results = import_results.get('results', {})

        # 统计信息
        report_lines.append("📊 导入统计:")
        report_lines.append(f"  - 分类: {results.get('imported_categories', 0)}")
        report_lines.append(f"  - 标签: {results.get('imported_tags', 0)}")
        report_lines.append(f"  - 文章: {results.get('imported_articles', 0)}")
        report_lines.append(f"  - 跳过: {results.get('skipped_articles', 0)}")
        report_lines.append(f"  - 媒体: {results.get('imported_media', 0)}")
        report_lines.append("")

        # 重定向规则
        redirects = results.get('redirects', [])
        if redirects:
            report_lines.append("🔗 URL 重定向规则:")
            for redirect in redirects[:10]:  # 只显示前10条
                report_lines.append(f"  {redirect['old_url']} → {redirect['new_url']} ({redirect['status_code']})")
            if len(redirects) > 10:
                report_lines.append(f"  ... 还有 {len(redirects) - 10} 条重定向规则")
            report_lines.append("")

        # 错误信息
        errors = results.get('errors', [])
        if errors:
            report_lines.append("⚠️  错误信息:")
            for error in errors[:20]:  # 只显示前20条
                report_lines.append(f"  - {error}")
            if len(errors) > 20:
                report_lines.append(f"  ... 还有 {len(errors) - 20} 条错误")
            report_lines.append("")

        report_lines.append("=" * 60)
        report_lines.append(f"导入完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("=" * 60)

        return "\n".join(report_lines)
