"""
FastBlog API Python SDK Client
提供同步和异步客户端实现

API 版本: V2 (/api/v2/)
FastBlog 版本: V0.3.26.0521+
"""

from typing import Optional, Dict, Any

import requests

try:
    import aiohttp

    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False
    aiohttp = None


class FastBlogClient:
    """FastBlog API 同步客户端（V2 API）"""

    def __init__(self, base_url: str = "http://localhost:9421/api/v2", token: Optional[str] = None):
        """
        初始化客户端

        Args:
            base_url: API V2 基础 URL（默认 http://localhost:9421/api/v2）
            token: JWT Access Token（可选）
        """
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.session = requests.Session()

        if token:
            self.session.headers.update({
                'Authorization': f'Bearer {token}'
            })

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        发送 HTTP 请求

        Args:
            method: HTTP 方法
            endpoint: API 端点（相对于 base_url 的路径）
            **kwargs: 请求参数

        Returns:
            响应数据
        """
        url = f"{self.base_url}{endpoint}"
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()

    # ==================== 认证相关 ====================

    def login(self, username: str, password: str) -> Dict[str, Any]:
        """
        用户登录（支持用户名或邮箱）

        Args:
            username: 用户名或邮箱
            password: 密码

        Returns:
            包含 access_token 和 refresh_token 的响应

        Response 结构:
            {
                "success": true,
                "data": {
                    "user": {"id", "username", "email", ...},
                    "access_token": "...",
                    "refresh_token": "..."
                }
            }
        """
        response = self._request('POST', '/auth/login', json={
            'username': username,
            'password': password
        })

        if response.get('success'):
            self.token = response['data']['access_token']
            self.session.headers.update({
                'Authorization': f'Bearer {self.token}'
            })

        return response

    def logout(self) -> Dict[str, Any]:
        """用户登出"""
        response = self._request('POST', '/auth/logout')
        self.token = None
        self.session.headers.pop('Authorization', None)
        return response

    def register(self, email: str, password: str, username: str) -> Dict[str, Any]:
        """
        用户注册

        Args:
            email: 邮箱
            password: 密码
            username: 用户名

        Returns:
            注册结果
        """
        return self._request('POST', '/auth/register', json={
            'email': email,
            'password': password,
            'username': username
        })

    # ==================== 文章相关 ====================

    def get_articles(self, page: int = 1, per_page: int = 10, **params) -> Dict[str, Any]:
        """
        获取文章列表

        Args:
            page: 页码
            per_page: 每页数量
            **params: 其他查询参数

        Returns:
            文章列表
        """
        params.update({'page': page, 'per_page': per_page})
        return self._request('GET', '/articles', params=params)

    def get_article(self, article_id: int) -> Dict[str, Any]:
        """
        获取单篇文章

        Args:
            article_id: 文章ID

        Returns:
            文章详情
        """
        return self._request('GET', f'/articles/{article_id}')

    def create_article(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建文章

        Args:
            data: 文章数据

        Returns:
            创建的文章
        """
        return self._request('POST', '/articles', json=data)

    def update_article(self, article_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新文章

        Args:
            article_id: 文章ID
            data: 更新数据

        Returns:
            更新后的文章
        """
        return self._request('PUT', f'/articles/{article_id}', json=data)

    def delete_article(self, article_id: int) -> Dict[str, Any]:
        """
        删除文章

        Args:
            article_id: 文章ID

        Returns:
            删除结果
        """
        return self._request('DELETE', f'/articles/{article_id}')

    # ==================== 分类相关 ====================

    def get_categories(self) -> Dict[str, Any]:
        """获取分类列表"""
        return self._request('GET', '/categories')

    def create_category(self, name: str, slug: str, description: str = '') -> Dict[str, Any]:
        """
        创建分类

        Args:
            name: 分类名称
            slug: 分类别名
            description: 分类描述

        Returns:
            创建的分类
        """
        return self._request('POST', '/categories', json={
            'name': name,
            'slug': slug,
            'description': description
        })

    # ==================== 用户相关 ====================

    def get_current_user(self) -> Dict[str, Any]:
        """获取当前用户信息"""
        return self._request('GET', '/users/me')

    def update_profile(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新用户资料

        Args:
            data: 更新数据

        Returns:
            更新后的用户信息
        """
        return self._request('PUT', '/users/me', json=data)

    # ==================== 媒体相关 ====================

    def upload_media(self, file_path: str) -> Dict[str, Any]:
        """
        上传媒体文件

        Args:
            file_path: 文件路径

        Returns:
            上传的媒体信息
        """
        with open(file_path, 'rb') as f:
            files = {'file': f}
            return self._request('POST', '/media/upload', files=files)

    # ==================== 仪表板相关 ====================

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """获取仪表板统计数据"""
        return self._request('GET', '/dashboard/stats')

    # ==================== SEO 追踪相关 ====================

    def get_seo_traffic(self, days: int = 30) -> Dict[str, Any]:
        """
        获取 SEO 流量数据

        Args:
            days: 统计天数

        Returns:
            SEO 流量数据
        """
        return self._request('GET', '/seo/tracking/search-traffic', params={'days': days})

    def get_top_keywords(self, limit: int = 20, days: int = 30) -> Dict[str, Any]:
        """
        获取热门关键词

        Args:
            limit: 返回数量
            days: 统计天数

        Returns:
            关键词列表
        """
        return self._request('GET', '/seo/tracking/top-keywords', params={
            'limit': limit,
            'days': days
        })

    # ==================== SEO 仪表板相关 ====================

    def get_seo_dashboard(self) -> Dict[str, Any]:
        """获取 SEO 仪表板概览数据"""
        return self._request('GET', '/seo/tracking/dashboard')

    def get_dashboard_analytics(self, days: int = 30) -> Dict[str, Any]:
        """
        获取仪表板分析数据

        Args:
            days: 统计天数

        Returns:
            分析数据
        """
        return self._request('GET', '/dashboard/analytics', params={'days': days})

    def close(self):
        """关闭会话"""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# 异步客户端
class AsyncFastBlogClient:
    """FastBlog API 异步客户端（V2 API）"""

    def __init__(self, base_url: str = "http://localhost:9421/api/v2", token: Optional[str] = None):
        """
        初始化异步客户端

        Args:
            base_url: API V2 基础 URL（默认 http://localhost:9421/api/v2）
            token: JWT Access Token（可选）
        """
        if not HAS_AIOHTTP:
            raise ImportError(
                "aiohttp is required for AsyncFastBlogClient. "
                "Install it with: pip install aiohttp"
            )

        self.base_url = base_url.rstrip('/')
        self.token = token
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建会话"""
        if self.session is None or self.session.closed:
            headers = {}
            if self.token:
                headers['Authorization'] = f'Bearer {self.token}'

            self.session = aiohttp.ClientSession(
                headers=headers,
                json_serialize=lambda obj: __import__('json').dumps(obj)
            )
        return self.session

    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        发送 HTTP 请求

        Args:
            method: HTTP 方法
            endpoint: API 端点
            **kwargs: 请求参数

        Returns:
            响应数据
        """
        session = await self._get_session()
        url = f"{self.base_url}{endpoint}"

        async with session.request(method, url, **kwargs) as response:
            response.raise_for_status()
            return await response.json()

    # ==================== 认证相关 ====================

    async def login(self, username: str, password: str) -> Dict[str, Any]:
        """
        用户登录（支持用户名或邮箱）

        Args:
            username: 用户名或邮箱
            password: 密码

        Returns:
            包含 access_token 和 refresh_token 的响应
        """
        response = await self._request('POST', '/auth/login', json={
            'username': username,
            'password': password
        })

        if response.get('success'):
            self.token = response['data']['access_token']
            # 更新会话的 headers
            if self.session and not self.session.closed:
                self.session.headers.update({
                    'Authorization': f'Bearer {self.token}'
                })

        return response

    async def logout(self) -> Dict[str, Any]:
        """用户登出"""
        response = await self._request('POST', '/auth/logout')
        self.token = None
        return response

    async def register(self, email: str, password: str, username: str) -> Dict[str, Any]:
        """
        用户注册

        Args:
            email: 邮箱
            password: 密码
            username: 用户名

        Returns:
            注册结果
        """
        return await self._request('POST', '/auth/register', json={
            'email': email,
            'password': password,
            'username': username
        })

    # ==================== 文章相关 ====================

    async def get_articles(self, page: int = 1, per_page: int = 10, **params) -> Dict[str, Any]:
        """
        获取文章列表

        Args:
            page: 页码
            per_page: 每页数量
            **params: 其他查询参数

        Returns:
            文章列表
        """
        params.update({'page': page, 'per_page': per_page})
        return await self._request('GET', '/articles', params=params)

    async def get_article(self, article_id: int) -> Dict[str, Any]:
        """
        获取单篇文章

        Args:
            article_id: 文章ID

        Returns:
            文章详情
        """
        return await self._request('GET', f'/articles/{article_id}')

    async def create_article(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建文章

        Args:
            data: 文章数据

        Returns:
            创建的文章
        """
        return await self._request('POST', '/articles', json=data)

    async def update_article(self, article_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新文章

        Args:
            article_id: 文章ID
            data: 更新数据

        Returns:
            更新后的文章
        """
        return await self._request('PUT', f'/articles/{article_id}', json=data)

    async def delete_article(self, article_id: int) -> Dict[str, Any]:
        """
        删除文章

        Args:
            article_id: 文章ID

        Returns:
            删除结果
        """
        return await self._request('DELETE', f'/articles/{article_id}')

    # ==================== 分类相关 ====================

    async def get_categories(self) -> Dict[str, Any]:
        """获取分类列表"""
        return await self._request('GET', '/categories')

    async def create_category(self, name: str, slug: str, description: str = '') -> Dict[str, Any]:
        """
        创建分类

        Args:
            name: 分类名称
            slug: 分类别名
            description: 分类描述

        Returns:
            创建的分类
        """
        return await self._request('POST', '/categories', json={
            'name': name,
            'slug': slug,
            'description': description
        })

    # ==================== 用户相关 ====================

    async def get_current_user(self) -> Dict[str, Any]:
        """获取当前用户信息"""
        return await self._request('GET', '/users/me')

    async def update_profile(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新用户资料

        Args:
            data: 更新数据

        Returns:
            更新后的用户信息
        """
        return await self._request('PUT', '/users/me', json=data)

    # ==================== 媒体相关 ====================

    async def upload_media(self, file_path: str) -> Dict[str, Any]:
        """
        上传媒体文件

        Args:
            file_path: 文件路径

        Returns:
            上传的媒体信息
        """
        session = await self._get_session()

        from pathlib import Path
        file_name = Path(file_path).name

        with open(file_path, 'rb') as f:
            form_data = aiohttp.FormData()
            form_data.add_field('file', f, filename=file_name)

            return await self._request('POST', '/media/upload', data=form_data)

    # ==================== 仪表板相关 ====================

    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """获取仪表板统计数据"""
        return await self._request('GET', '/dashboard/stats')

    # ==================== SEO 追踪相关 ====================

    async def get_seo_traffic(self, days: int = 30) -> Dict[str, Any]:
        """
        获取 SEO 流量数据

        Args:
            days: 统计天数

        Returns:
            SEO 流量数据
        """
        return await self._request('GET', '/seo/tracking/search-traffic', params={'days': days})

    async def get_top_keywords(self, limit: int = 20, days: int = 30) -> Dict[str, Any]:
        """
        获取热门关键词

        Args:
            limit: 返回数量
            days: 统计天数

        Returns:
            关键词列表
        """
        return await self._request('GET', '/seo/tracking/top-keywords', params={
            'limit': limit,
            'days': days
        })

    # ==================== SEO 仪表板相关 ====================

    async def get_seo_dashboard(self) -> Dict[str, Any]:
        """获取 SEO 仪表板概览数据"""
        return await self._request('GET', '/seo/tracking/dashboard')

    async def get_dashboard_analytics(self, days: int = 30) -> Dict[str, Any]:
        """
        获取仪表板分析数据

        Args:
            days: 统计天数

        Returns:
            分析数据
        """
        return await self._request('GET', '/dashboard/analytics', params={'days': days})

    async def close(self):
        """关闭会话"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
