"""
FastBlog SDK - 情报引擎模块

提供情报数据源管理、情报搜索、简报生成、预警规则等 API 封装

用法:
    from fastblog_sdk import FastBlogClient

    client = FastBlogClient(base_url="http://localhost:9421/api/v2", token="...")

    # 情报操作
    sources = client.intel.get_sources()
    intel = client.intel.search_intelligence(query="AI", category="technology")
    briefing = client.intel.generate_briefing(topic="AI 行业动态")
"""

from typing import Optional, Dict, Any, List


class IntelMixin:
    """
    情报引擎 SDK Mixin

    为 FastBlogClient / AsyncFastBlogClient 添加情报相关方法
    """

    # ==================== 数据源管理 ====================

    def get_intel_sources(self, page: int = 1, per_page: int = 20, **params) -> Dict[str, Any]:
        """
        获取数据源列表

        Args:
            page: 页码
            per_page: 每页数量
            **params: 额外查询参数 (source_type, is_active)

        Returns:
            数据源列表
        """
        params.update({'page': page, 'per_page': per_page})
        return self._request('GET', '/intel/sources', params=params)

    def get_intel_source(self, source_id: int) -> Dict[str, Any]:
        """
        获取数据源详情

        Args:
            source_id: 数据源 ID

        Returns:
            数据源详情
        """
        return self._request('GET', f'/intel/sources/{source_id}')

    def create_intel_source(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建数据源

        Args:
            data: 数据源数据 {name, source_type, url, config?}

        Returns:
            创建结果
        """
        return self._request('POST', '/intel/sources', json=data)

    def update_intel_source(self, source_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新数据源

        Args:
            source_id: 数据源 ID
            data: 更新数据

        Returns:
            更新结果
        """
        return self._request('PUT', f'/intel/sources/{source_id}', json=data)

    def delete_intel_source(self, source_id: int) -> Dict[str, Any]:
        """
        删除数据源

        Args:
            source_id: 数据源 ID

        Returns:
            删除结果
        """
        return self._request('DELETE', f'/intel/sources/{source_id}')

    def trigger_collection(self, source_id: int) -> Dict[str, Any]:
        """
        手动触发数据采集

        Args:
            source_id: 数据源 ID

        Returns:
            采集任务结果
        """
        return self._request('POST', f'/intel/sources/{source_id}/collect')

    # ==================== 情报查询 ====================

    def get_intelligence(self, page: int = 1, per_page: int = 20, **params) -> Dict[str, Any]:
        """
        获取情报列表

        Args:
            page: 页码
            per_page: 每页数量
            **params: 额外筛选参数 (category, sentiment)

        Returns:
            情报列表
        """
        params.update({'page': page, 'per_page': per_page})
        return self._request('GET', '/intel/intelligence', params=params)

    def get_intelligence_detail(self, intel_id: int) -> Dict[str, Any]:
        """
        获取情报详情

        Args:
            intel_id: 情报 ID

        Returns:
            情报详情
        """
        return self._request('GET', f'/intel/intelligence/{intel_id}')

    def search_intelligence(self, query: str = None, category: str = None,
                            sentiment: str = None, limit: int = 10) -> Dict[str, Any]:
        """
        搜索情报（便捷方法）

        Args:
            query: 搜索关键词
            category: 分类筛选
            sentiment: 情感筛选 (positive/negative/neutral)
            limit: 返回数量

        Returns:
            搜索结果
        """
        params: Dict[str, Any] = {'per_page': limit}
        if category:
            params['category'] = category
        if sentiment:
            params['sentiment'] = sentiment
        return self._request('GET', '/intel/intelligence', params=params)

    # ==================== 简报管理 ====================

    def get_briefings(self, page: int = 1, per_page: int = 20, **params) -> Dict[str, Any]:
        """
        获取简报列表

        Args:
            page: 页码
            per_page: 每页数量
            **params: 额外筛选参数 (briefing_type)

        Returns:
            简报列表
        """
        params.update({'page': page, 'per_page': per_page})
        return self._request('GET', '/intel/briefings', params=params)

    def get_briefing_detail(self, briefing_id: int) -> Dict[str, Any]:
        """
        获取简报详情

        Args:
            briefing_id: 简报 ID

        Returns:
            简报详情
        """
        return self._request('GET', f'/intel/briefings/{briefing_id}')

    def generate_briefing(self, briefing_type: str = "daily",
                          topic: str = None, days: int = 7) -> Dict[str, Any]:
        """
        生成情报简报

        Args:
            briefing_type: 简报类型 (daily/weekly/monthly/on_demand)
            topic: 简报主题
            days: 覆盖天数

        Returns:
            生成的简报
        """
        params: Dict[str, Any] = {
            'briefing_type': briefing_type,
            'days': days,
        }
        if topic:
            params['topic'] = topic
        return self._request('POST', '/intel/briefings/generate', params=params)

    # ==================== 预警管理 ====================

    def get_alert_rules(self, page: int = 1, per_page: int = 20, **params) -> Dict[str, Any]:
        """
        获取预警规则列表

        Args:
            page: 页码
            per_page: 每页数量
            **params: 额外筛选参数 (is_active)

        Returns:
            预警规则列表
        """
        params.update({'page': page, 'per_page': per_page})
        return self._request('GET', '/intel/alerts/rules', params=params)

    def create_alert_rule(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建预警规则

        Args:
            data: 规则数据 {name, condition, actions, ...}

        Returns:
            创建结果
        """
        return self._request('POST', '/intel/alerts/rules', json=data)

    def get_alert_events(self) -> Dict[str, Any]:
        """
        获取预警事件历史

        Returns:
            预警事件列表
        """
        return self._request('GET', '/intel/alerts/events')

    def trigger_analysis(self, source_id: int) -> Dict[str, Any]:
        """
        触发数据源分析

        Args:
            source_id: 数据源 ID

        Returns:
            分析结果
        """
        return self._request('POST', f'/intel/analyze/{source_id}')


class AsyncIntelMixin:
    """
    情报引擎异步 SDK Mixin

    为 AsyncFastBlogClient 添加情报相关异步方法
    """

    async def get_intel_sources(self, page: int = 1, per_page: int = 20, **params) -> Dict[str, Any]:
        params.update({'page': page, 'per_page': per_page})
        return await self._request('GET', '/intel/sources', params=params)

    async def get_intel_source(self, source_id: int) -> Dict[str, Any]:
        return await self._request('GET', f'/intel/sources/{source_id}')

    async def create_intel_source(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return await self._request('POST', '/intel/sources', json=data)

    async def update_intel_source(self, source_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        return await self._request('PUT', f'/intel/sources/{source_id}', json=data)

    async def delete_intel_source(self, source_id: int) -> Dict[str, Any]:
        return await self._request('DELETE', f'/intel/sources/{source_id}')

    async def trigger_collection(self, source_id: int) -> Dict[str, Any]:
        return await self._request('POST', f'/intel/sources/{source_id}/collect')

    async def get_intelligence(self, page: int = 1, per_page: int = 20, **params) -> Dict[str, Any]:
        params.update({'page': page, 'per_page': per_page})
        return await self._request('GET', '/intel/intelligence', params=params)

    async def get_intelligence_detail(self, intel_id: int) -> Dict[str, Any]:
        return await self._request('GET', f'/intel/intelligence/{intel_id}')

    async def search_intelligence(self, query: str = None, category: str = None,
                                  sentiment: str = None, limit: int = 10) -> Dict[str, Any]:
        params: Dict[str, Any] = {'per_page': limit}
        if category:
            params['category'] = category
        if sentiment:
            params['sentiment'] = sentiment
        return await self._request('GET', '/intel/intelligence', params=params)

    async def get_briefings(self, page: int = 1, per_page: int = 20, **params) -> Dict[str, Any]:
        params.update({'page': page, 'per_page': per_page})
        return await self._request('GET', '/intel/briefings', params=params)

    async def get_briefing_detail(self, briefing_id: int) -> Dict[str, Any]:
        return await self._request('GET', f'/intel/briefings/{briefing_id}')

    async def generate_briefing(self, briefing_type: str = "daily",
                                topic: str = None, days: int = 7) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            'briefing_type': briefing_type,
            'days': days,
        }
        if topic:
            params['topic'] = topic
        return await self._request('POST', '/intel/briefings/generate', params=params)

    async def get_alert_rules(self, page: int = 1, per_page: int = 20, **params) -> Dict[str, Any]:
        params.update({'page': page, 'per_page': per_page})
        return await self._request('GET', '/intel/alerts/rules', params=params)

    async def create_alert_rule(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return await self._request('POST', '/intel/alerts/rules', json=data)

    async def get_alert_events(self) -> Dict[str, Any]:
        return await self._request('GET', '/intel/alerts/events')

    async def trigger_analysis(self, source_id: int) -> Dict[str, Any]:
        return await self._request('POST', f'/intel/analyze/{source_id}')
