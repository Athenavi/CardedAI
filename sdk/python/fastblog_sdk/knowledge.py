"""
FastBlog SDK - 知识引擎模块

提供知识库管理、文档上传、RAG 问答、语义搜索、研报生成等 API 封装

用法:
    from fastblog_sdk import FastBlogClient

    client = FastBlogClient(base_url="http://localhost:9421/api/v2", token="...")

    # 知识库操作
    bases = client.knowledge.get_bases()
    result = client.knowledge.rag_qa("什么是 RAG？", knowledge_base_id=1)
    report = client.knowledge.generate_report("2024 AI 趋势", knowledge_base_id=1)
"""

from typing import Optional, Dict, Any, List


class KnowledgeMixin:
    """
    知识引擎 SDK Mixin

    为 FastBlogClient / AsyncFastBlogClient 添加知识库相关方法
    """

    # ==================== 知识库管理 ====================

    def get_knowledge_bases(self, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """
        获取知识库列表

        Args:
            page: 页码
            per_page: 每页数量

        Returns:
            知识库列表
        """
        return self._request('GET', '/knowledge/bases', params={'page': page, 'per_page': per_page})

    def get_knowledge_base(self, base_id: int) -> Dict[str, Any]:
        """
        获取知识库详情

        Args:
            base_id: 知识库 ID

        Returns:
            知识库详情
        """
        return self._request('GET', f'/knowledge/bases/{base_id}')

    def create_knowledge_base(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建知识库

        Args:
            data: 知识库数据 {name, description?, embedding_model?, chunk_size?, chunk_overlap?}

        Returns:
            创建结果
        """
        return self._request('POST', '/knowledge/bases', json=data)

    def update_knowledge_base(self, base_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新知识库配置

        Args:
            base_id: 知识库 ID
            data: 更新数据

        Returns:
            更新结果
        """
        return self._request('PUT', f'/knowledge/bases/{base_id}', json=data)

    def delete_knowledge_base(self, base_id: int) -> Dict[str, Any]:
        """
        删除知识库及其所有文档和向量

        Args:
            base_id: 知识库 ID

        Returns:
            删除结果
        """
        return self._request('DELETE', f'/knowledge/bases/{base_id}')

    # ==================== 文档管理 ====================

    def get_documents(self, base_id: int, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """
        获取知识库文档列表

        Args:
            base_id: 知识库 ID
            page: 页码
            per_page: 每页数量

        Returns:
            文档列表
        """
        return self._request('GET', f'/knowledge/bases/{base_id}/documents',
                             params={'page': page, 'per_page': per_page})

    def upload_document(self, base_id: int, file_path: str,
                        metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        上传文档到知识库

        Args:
            base_id: 知识库 ID
            file_path: 文件路径
            metadata: 文档元数据

        Returns:
            上传结果
        """
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {}
            if metadata:
                import json
                data['metadata'] = json.dumps(metadata)
            return self._request('POST', f'/knowledge/bases/{base_id}/documents/upload',
                                 files=files, data=data)

    def delete_document(self, base_id: int, doc_id: int) -> Dict[str, Any]:
        """
        删除文档及其切片和向量

        Args:
            base_id: 知识库 ID
            doc_id: 文档 ID

        Returns:
            删除结果
        """
        return self._request('DELETE', f'/knowledge/bases/{base_id}/documents/{doc_id}')

    # ==================== RAG 检索与问答 ====================

    def rag_search(self, base_id: int, query: str, top_k: int = 10) -> Dict[str, Any]:
        """
        语义搜索（纯向量检索，不经过 LLM）

        Args:
            base_id: 知识库 ID
            query: 搜索查询
            top_k: 返回结果数量

        Returns:
            搜索结果
        """
        return self._request('POST', f'/knowledge/bases/{base_id}/search',
                             json={'query': query, 'top_k': top_k})

    def rag_qa(self, question: str, knowledge_base_id: int,
               top_k: int = 5) -> Dict[str, Any]:
        """
        知识问答（RAG 检索 + LLM 回答）

        Args:
            question: 问题
            knowledge_base_id: 知识库 ID
            top_k: 检索文档数量

        Returns:
            回答结果 {answer, sources, ...}
        """
        return self._request('POST', f'/knowledge/bases/{knowledge_base_id}/qa',
                             json={'question': question, 'top_k': top_k})

    # ==================== 研报生成 ====================

    def generate_report(self, topic: str, knowledge_base_id: int,
                        report_type: str = "research",
                        additional_context: str = None) -> Dict[str, Any]:
        """
        生成研究报告

        Args:
            topic: 报告主题
            knowledge_base_id: 知识库 ID
            report_type: 报告类型 (research/analysis/summary)
            additional_context: 额外上下文

        Returns:
            生成的报告
        """
        data: Dict[str, Any] = {
            'topic': topic,
            'report_type': report_type,
        }
        if additional_context:
            data['additional_context'] = additional_context
        return self._request('POST', f'/knowledge/bases/{knowledge_base_id}/reports/generate',
                             json=data)

    def get_reports(self, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """
        获取研报列表

        Args:
            page: 页码
            per_page: 每页数量

        Returns:
            研报列表
        """
        return self._request('GET', '/knowledge/reports',
                             params={'page': page, 'per_page': per_page})

    def get_report_detail(self, report_id: int) -> Dict[str, Any]:
        """
        获取研报详情

        Args:
            report_id: 研报 ID

        Returns:
            研报详情
        """
        return self._request('GET', f'/knowledge/reports/{report_id}')

    # ==================== 报告模板 ====================

    def get_report_templates(self, page: int = 1, per_page: int = 20,
                             report_type: str = None) -> Dict[str, Any]:
        """
        获取报告模板列表

        Args:
            page: 页码
            per_page: 每页数量
            report_type: 模板类型筛选

        Returns:
            模板列表
        """
        params: Dict[str, Any] = {'page': page, 'per_page': per_page}
        if report_type:
            params['report_type'] = report_type
        return self._request('GET', '/knowledge/templates', params=params)

    def create_report_template(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建报告模板

        Args:
            data: 模板数据 {name, report_type, template_content, description?}

        Returns:
            创建结果
        """
        return self._request('POST', '/knowledge/templates', json=data)


class AsyncKnowledgeMixin:
    """
    知识引擎异步 SDK Mixin

    为 AsyncFastBlogClient 添加知识库相关异步方法
    """

    async def get_knowledge_bases(self, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        return await self._request('GET', '/knowledge/bases', params={'page': page, 'per_page': per_page})

    async def get_knowledge_base(self, base_id: int) -> Dict[str, Any]:
        return await self._request('GET', f'/knowledge/bases/{base_id}')

    async def create_knowledge_base(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return await self._request('POST', '/knowledge/bases', json=data)

    async def update_knowledge_base(self, base_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        return await self._request('PUT', f'/knowledge/bases/{base_id}', json=data)

    async def delete_knowledge_base(self, base_id: int) -> Dict[str, Any]:
        return await self._request('DELETE', f'/knowledge/bases/{base_id}')

    async def get_documents(self, base_id: int, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        return await self._request('GET', f'/knowledge/bases/{base_id}/documents',
                                   params={'page': page, 'per_page': per_page})

    async def upload_document(self, base_id: int, file_path: str,
                              metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        import aiohttp
        from pathlib import Path
        await self._get_session()
        file_name = Path(file_path).name
        with open(file_path, 'rb') as f:
            form_data = aiohttp.FormData()
            form_data.add_field('file', f, filename=file_name)
            if metadata:
                import json
                form_data.add_field('metadata', json.dumps(metadata))
            return await self._request('POST', f'/knowledge/bases/{base_id}/documents/upload',
                                       data=form_data)

    async def delete_document(self, base_id: int, doc_id: int) -> Dict[str, Any]:
        return await self._request('DELETE', f'/knowledge/bases/{base_id}/documents/{doc_id}')

    async def rag_search(self, base_id: int, query: str, top_k: int = 10) -> Dict[str, Any]:
        return await self._request('POST', f'/knowledge/bases/{base_id}/search',
                                   json={'query': query, 'top_k': top_k})

    async def rag_qa(self, question: str, knowledge_base_id: int,
                     top_k: int = 5) -> Dict[str, Any]:
        return await self._request('POST', f'/knowledge/bases/{knowledge_base_id}/qa',
                                   json={'question': question, 'top_k': top_k})

    async def generate_report(self, topic: str, knowledge_base_id: int,
                              report_type: str = "research",
                              additional_context: str = None) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            'topic': topic,
            'report_type': report_type,
        }
        if additional_context:
            data['additional_context'] = additional_context
        return await self._request('POST', f'/knowledge/bases/{knowledge_base_id}/reports/generate',
                                   json=data)

    async def get_reports(self, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        return await self._request('GET', '/knowledge/reports',
                                   params={'page': page, 'per_page': per_page})

    async def get_report_detail(self, report_id: int) -> Dict[str, Any]:
        return await self._request('GET', f'/knowledge/reports/{report_id}')

    async def get_report_templates(self, page: int = 1, per_page: int = 20,
                                   report_type: str = None) -> Dict[str, Any]:
        params: Dict[str, Any] = {'page': page, 'per_page': per_page}
        if report_type:
            params['report_type'] = report_type
        return await self._request('GET', '/knowledge/templates', params=params)

    async def create_report_template(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return await self._request('POST', '/knowledge/templates', json=data)
