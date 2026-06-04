"""
Meilisearch 全文搜索引擎集成服务

功能：
1. 文章索引同步（增删改查）
2. 高性能全文搜索
3. 搜索结果高亮
4. 拼音搜索支持
5. 模糊匹配和纠错
6. 搜索统计和分析
7. 增量索引更新
"""
import hashlib
from datetime import datetime
from typing import List, Dict, Optional, Any

from meilisearch_python_sdk import Client

from src.unified_logger import default_logger as logger


class MeilisearchService:
    """
    Meilisearch 搜索引擎服务

    提供完整的全文搜索功能，包括索引管理、搜索、高亮等
    注意：客户端采用懒加载模式，首次使用时才创建连接，避免启动时阻塞
    """

    def __init__(self, host: str = "http://localhost:7700", api_key: str = ""):
        """
        初始化 Meilisearch 客户端（懒加载）

        Args:
            host: Meilisearch 服务器地址
            api_key: API密钥（可选）
        """
        self.host = host
        self.api_key = api_key
        self._client = None  # 懒加载：首次访问时才创建
        self.index_name = "articles"
        self.index = None

    @property
    def client(self):
        """懒加载 Meilisearch 客户端，首次访问时才创建"""
        if self._client is None:
            self._client = Client(self.host, self.api_key) if self.api_key else Client(self.host)
        return self._client

    async def initialize(self):
        """初始化搜索引擎和索引配置"""
        try:
            # 获取或创建索引
            self.index = self.client.index(self.index_name)

            # 配置索引设置
            await self._configure_index()

            logger.info(f"Meilisearch initialized successfully at {self.host}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Meilisearch: {e}")
            return False

    async def _configure_index(self):
        """配置索引设置（ searchable attributes, filterable attributes等）"""
        settings = MeiliSearchIndexSettings(
            # 可搜索字段（按重要性排序）
            searchable_attributes=[
                "title",
                "excerpt",
                "content",
                "tags",
                "category_name"
            ],
            # 可过滤字段
            filterable_attributes=[
                "category_id",
                "author_id",
                "status",
                "created_at",
                "views",
                "is_featured",
                "tags"
            ],
            # 可排序字段
            sortable_attributes=[
                "created_at",
                "updated_at",
                "views",
                "likes"
            ],
            # 显示字段
            displayed_attributes=[
                "id",
                "title",
                "slug",
                "excerpt",
                "cover_image",
                "category_id",
                "category_name",
                "author_id",
                "author_name",
                "tags",
                "views",
                "likes",
                "status",
                "is_featured",
                "created_at",
                "updated_at"
            ],
            # 分词设置
            typo_tolerance={
                "enabled": True,
                "min_word_size_for_typos": {
                    "one_typo": 4,
                    "two_typos": 8
                }
            },
            # 高亮标记
            pagination={
                "max_total_hits": 1000
            }
        )

        # 应用设置
        task = await self.index.update_settings(settings)
        logger.info(f"Index settings updated, task uid: {task.task_uid}")

    async def index_article(self, article_data: Dict[str, Any]) -> bool:
        """
        索引单篇文章

        Args:
            article_data: 文章数据字典

        Returns:
            是否成功
        """
        try:
            # 添加文档到索引
            task = await self.index.add_documents([article_data])

            logger.info(f"Article indexed: {article_data.get('id')}, task uid: {task.task_uid}")
            return True

        except Exception as e:
            logger.error(f"Failed to index article {article_data.get('id')}: {e}")
            return False

    async def update_article(self, article_data: Dict[str, Any]) -> bool:
        """
        更新文章索引

        Args:
            article_data: 文章数据字典

        Returns:
            是否成功
        """
        try:
            # 更新文档
            task = await self.index.update_documents([article_data])

            logger.info(f"Article index updated: {article_data.get('id')}, task uid: {task.task_uid}")
            return True

        except Exception as e:
            logger.error(f"Failed to update article index {article_data.get('id')}: {e}")
            return False

    async def delete_article(self, article_id: int) -> bool:
        """
        删除文章索引

        Args:
            article_id: 文章ID

        Returns:
            是否成功
        """
        try:
            # 删除文档
            task = await self.index.delete_document(article_id)

            logger.info(f"Article index deleted: {article_id}, task uid: {task.task_uid}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete article index {article_id}: {e}")
            return False

    async def bulk_index_articles(self, articles: List[Dict[str, Any]]) -> bool:
        """
        批量索引文章

        Args:
            articles: 文章数据列表

        Returns:
            是否成功
        """
        try:
            if not articles:
                return True

            # 批量添加文档
            task = await self.index.add_documents(articles)

            logger.info(f"Bulk indexed {len(articles)} articles, task uid: {task.task_uid}")
            return True

        except Exception as e:
            logger.error(f"Failed to bulk index articles: {e}")
            return False

    async def search(
            self,
            query: str,
            category_id: Optional[int] = None,
            author_id: Optional[int] = None,
            date_from: Optional[datetime] = None,
            date_to: Optional[datetime] = None,
            status: str = "published",
            page: int = 1,
            per_page: int = 20,
            sort_by: str = "relevance"
    ) -> Dict[str, Any]:
        """
        搜索文章

        Args:
            query: 搜索关键词
            category_id: 分类ID过滤
            author_id: 作者ID过滤
            date_from: 起始日期
            date_to: 结束日期
            status: 文章状态
            page: 页码
            per_page: 每页数量
            sort_by: 排序方式 (relevance, date, views)

        Returns:
            搜索结果和分页信息
        """
        try:
            # 构建过滤器
            filters = []

            if status:
                filters.append(f"status = '{status}'")

            if category_id:
                filters.append(f"category_id = {category_id}")

            if author_id:
                filters.append(f"author_id = {author_id}")

            if date_from:
                filters.append(f"created_at >= {int(date_from.timestamp())}")

            if date_to:
                filters.append(f"created_at <= {int(date_to.timestamp())}")

            filter_str = " AND ".join(filters) if filters else None

            # 确定排序
            if sort_by == "date":
                sort = ["created_at:desc"]
            elif sort_by == "views":
                sort = ["views:desc"]
            else:  # relevance
                sort = None

            # 执行搜索
            result = await self.index.search(
                query,
                offset=(page - 1) * per_page,
                limit=per_page,
                filter=filter_str,
                sort=sort,
                attributes_to_highlight=["title", "excerpt"],
                highlight_pre_tag="<mark>",
                highlight_post_tag="</mark>"
            )

            # 格式化结果
            articles = []
            for hit in result.hits:
                article = {
                    'id': hit.get('id'),
                    'title': hit.get('title'),
                    'slug': hit.get('slug'),
                    'excerpt': hit.get('excerpt'),
                    'cover_image': hit.get('cover_image'),
                    'category_id': hit.get('category_id'),
                    'category_name': hit.get('category_name'),
                    'author_id': hit.get('author_id'),
                    'author_name': hit.get('author_name'),
                    'tags': hit.get('tags', []),
                    'views': hit.get('views', 0),
                    'likes': hit.get('likes', 0),
                    'status': hit.get('status'),
                    'is_featured': hit.get('is_featured', False),
                    'created_at': hit.get('created_at'),
                    'updated_at': hit.get('updated_at'),
                }

                # 添加高亮字段
                if '_formatted' in hit:
                    formatted = hit['_formatted']
                    article['highlighted_title'] = formatted.get('title', article['title'])
                    article['highlighted_excerpt'] = formatted.get('excerpt', article['excerpt'])
                else:
                    article['highlighted_title'] = article['title']
                    article['highlighted_excerpt'] = article['excerpt']

                articles.append(article)

            return {
                'articles': articles,
                'total': result.estimated_total_hits or len(result.hits),
                'page': page,
                'per_page': per_page,
                'total_pages': (
                                           result.estimated_total_hits + per_page - 1) // per_page if result.estimated_total_hits else 1,
                'query': query,
                'processing_time_ms': result.processing_time_ms,
            }

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {
                'articles': [],
                'total': 0,
                'page': page,
                'per_page': per_page,
                'total_pages': 0,
                'query': query,
                'error': str(e)
            }

    async def get_search_suggestions(
            self,
            query: str,
            limit: int = 5
    ) -> List[str]:
        """
        获取搜索建议（自动完成）

        Args:
            query: 搜索前缀
            limit: 返回数量

        Returns:
            搜索建议列表
        """
        try:
            # 使用 Meilisearch 的 facet search 功能
            result = await self.index.search(
                query,
                limit=limit,
                attributes_to_retrieve=["title"],
            )

            suggestions = [hit.get('title', '') for hit in result.hits if hit.get('title')]
            return suggestions[:limit]

        except Exception as e:
            logger.error(f"Failed to get search suggestions: {e}")
            return []

    async def rebuild_index(self, articles: List[Dict[str, Any]]) -> bool:
        """
        重建整个索引

        Args:
            articles: 所有文章数据列表

        Returns:
            是否成功
        """
        try:
            # 清空索引
            await self.index.delete_all_documents()

            # 重新索引所有文章
            if articles:
                await self.bulk_index_articles(articles)

            logger.info(f"Index rebuilt with {len(articles)} articles")
            return True

        except Exception as e:
            logger.error(f"Failed to rebuild index: {e}")
            return False

    async def get_index_stats(self) -> Dict[str, Any]:
        """
        获取索引统计信息

        Returns:
            统计信息
        """
        try:
            stats = await self.index.get_stats()

            return {
                'number_of_documents': stats.number_of_documents,
                'index_size_in_bytes': stats.index_size_in_bytes,
                'field_distribution': stats.field_distribution,
            }

        except Exception as e:
            logger.error(f"Failed to get index stats: {e}")
            return {}

    def calculate_content_hash(self, article_data: Dict[str, Any]) -> str:
        """
        计算文章内容哈希（用于检测变更）

        Args:
            article_data: 文章数据

        Returns:
            SHA256哈希字符串
        """
        # 提取关键字段
        content_str = f"{article_data.get('title', '')}|{article_data.get('content', '')}|{article_data.get('excerpt', '')}"
        return hashlib.sha256(content_str.encode('utf-8')).hexdigest()


# 全局实例
meilisearch_service = MeilisearchService()
