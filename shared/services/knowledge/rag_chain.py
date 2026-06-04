"""
RAG 检索增强生成链

将向量检索与 LLM 生成结合，实现知识问答和智能搜索。

流程：
1. 将查询文本 Embedding 为向量
2. 在向量数据库中检索相关文档切片
3. 构建包含引用来源的上下文 Prompt
4. 调用 LLM 生成带引用的回答
5. 计算置信度评分
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from src.unified_logger import default_logger as logger

# 性能优化：RAG 检索缓存（延迟导入避免循环依赖）
def _get_rag_cache():
    """延迟获取 RAG 缓存服务"""
    try:
        from shared.services.performance.engine_optimizer import get_rag_cache
        return get_rag_cache()
    except Exception:
        return None


@dataclass
class RAGResult:
    """RAG 查询结果"""
    answer: str = ""
    sources: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    query: str = ""
    knowledge_base_id: int = 0
    success: bool = True
    error: Optional[str] = None


class RAGChain:
    """
    RAG 检索增强生成链

    组合 EmbeddingService、VectorStoreService 和 LLMClient，
    提供端到端的知识问答能力。
    """

    def __init__(self):
        from shared.services.knowledge.embedding_service import embedding_service
        from shared.services.knowledge.vector_store import vector_store
        from shared.services.ai.llm_client import llm_client

        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.llm_client = llm_client

    async def query(
        self,
        question: str,
        knowledge_base_id: int,
        top_k: int = 5,
        system_prompt: str = None,
        include_sources: bool = True,
        score_threshold: float = 0.3,
    ) -> RAGResult:
        """
        RAG 查询流程

        Args:
            question: 用户问题
            knowledge_base_id: 知识库 ID
            top_k: 返回的最相关切片数量
            system_prompt: 自定义系统提示词（可选）
            include_sources: 是否在回答中包含来源引用
            score_threshold: 最低相关度阈值

        Returns:
            RAGResult 查询结果
        """
        collection_name = f"kb_{knowledge_base_id}"

        try:
            # 1. 问题 Embedding
            query_vector = await self.embedding_service.embed_single(question)
            if not query_vector:
                return RAGResult(
                    success=False,
                    error="Embedding 生成失败",
                    query=question,
                    knowledge_base_id=knowledge_base_id,
                )

            # 2. 向量检索
            raw_chunks = await self.vector_store.search(
                collection_name=collection_name,
                query_vector=query_vector,
                top_k=top_k,
            )

            if not raw_chunks:
                return RAGResult(
                    answer="未找到相关知识内容。",
                    sources=[],
                    confidence=0.0,
                    query=question,
                    knowledge_base_id=knowledge_base_id,
                )

            # 3. 过滤低相关度结果
            filtered_chunks = [
                c for c in raw_chunks if c.get("score", 0) >= score_threshold
            ]
            if not filtered_chunks:
                filtered_chunks = raw_chunks[:3]  # 保留前3个作为兜底

            # 4. 构建上下文
            context_parts = []
            for i, chunk in enumerate(filtered_chunks):
                content = chunk.get("metadata", {}).get("content", "")
                if not content:
                    content = str(chunk.get("metadata", {}))
                source_info = chunk.get("metadata", {}).get("document_title", f"来源{i + 1}")
                context_parts.append(f"[来源{i + 1}] (相关度: {chunk.get('score', 0):.2f}) {content}")

            context = "\n\n".join(context_parts)

            # 5. 构建 Prompt
            default_system = (
                "你是一个专业的知识助手。基于提供的参考资料回答用户问题。\n"
                "规则：\n"
                "1. 仅基于参考资料回答，如果资料中没有相关信息，请如实说明。\n"
                "2. 在回答中引用来源编号，如 [来源1]、[来源2]。\n"
                "3. 回答要准确、简洁、有条理。"
            )

            prompt = f"""参考资料：
{context}

用户问题：{question}

请基于以上参考资料回答问题，并在回答中标注引用来源。"""

            # 6. LLM 生成回答
            llm_result = await self.llm_client.generate_text(
                prompt=prompt,
                system_prompt=system_prompt or default_system,
                temperature=0.3,
                max_tokens=2000,
            )

            if not llm_result.get("success"):
                return RAGResult(
                    success=False,
                    error=f"LLM 生成失败: {llm_result.get('error', '未知错误')}",
                    query=question,
                    knowledge_base_id=knowledge_base_id,
                    sources=filtered_chunks,
                )

            answer = llm_result.get("content", "")

            # 7. 计算置信度
            confidence = self._calculate_confidence(filtered_chunks)

            # 8. 构建来源信息
            sources = []
            if include_sources:
                for i, chunk in enumerate(filtered_chunks):
                    sources.append({
                        "index": i + 1,
                        "score": chunk.get("score", 0.0),
                        "content": chunk.get("metadata", {}).get("content", "")[:200],
                        "document_title": chunk.get("metadata", {}).get("document_title", ""),
                        "chunk_id": chunk.get("id", ""),
                    })

            return RAGResult(
                answer=answer,
                sources=sources,
                confidence=confidence,
                query=question,
                knowledge_base_id=knowledge_base_id,
            )

        except Exception as e:
            logger.error(f"RAG 查询失败: {e}")
            return RAGResult(
                success=False,
                error=str(e),
                query=question,
                knowledge_base_id=knowledge_base_id,
            )

    async def search(
        self,
        query: str,
        knowledge_base_id: int,
        top_k: int = 10,
        score_threshold: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        纯向量检索（不经过 LLM 生成）

        集成 RAGCacheService 进行结果缓存，相同查询可命中缓存跳过向量检索。

        Args:
            query: 查询文本
            knowledge_base_id: 知识库 ID
            top_k: 返回结果数量
            score_threshold: 最低相关度阈值

        Returns:
            检索结果列表
        """
        collection_name = f"kb_{knowledge_base_id}"
        rag_cache = _get_rag_cache()

        # 1. 尝试命中缓存
        if rag_cache:
            cached = await rag_cache.get_cached_search(
                collection=collection_name,
                query=query,
                top_k=top_k,
                filters={"score_threshold": score_threshold} if score_threshold > 0 else None,
            )
            if cached is not None:
                logger.debug("RAG 搜索命中缓存: collection=%s, query=%s", collection_name, query[:50])
                return cached

        # 2. 缓存未命中，执行向量检索
        try:
            query_vector = await self.embedding_service.embed_single(query)
            if not query_vector:
                return []

            results = await self.vector_store.search(
                collection_name=collection_name,
                query_vector=query_vector,
                top_k=top_k,
            )

            if score_threshold > 0:
                results = [r for r in results if r.get("score", 0) >= score_threshold]

            # 3. 写入缓存
            if rag_cache and results:
                await rag_cache.set_cached_search(
                    collection=collection_name,
                    query=query,
                    top_k=top_k,
                    results=results,
                    filters={"score_threshold": score_threshold} if score_threshold > 0 else None,
                )

            return results
        except Exception as e:
            logger.error(f"向量检索失败: {e}")
            return []

    async def ingest_document(
        self,
        knowledge_base_id: int,
        document_id: int,
        chunks: List[Dict[str, Any]],
    ) -> List[str]:
        """
        将文档切片导入向量数据库

        Args:
            knowledge_base_id: 知识库 ID
            document_id: 文档 ID
            chunks: 切片列表 [{"content": "...", "metadata": {...}}, ...]

        Returns:
            向量 ID 列表
        """
        try:
            collection_name = f"kb_{knowledge_base_id}"

            # 提取文本进行 Embedding
            texts = [c["content"] for c in chunks]
            embeddings = await self.embedding_service.embed(texts)

            if not embeddings:
                logger.error("Embedding 生成失败，跳过导入")
                return []

            # 构建元数据
            metadata_list = []
            for i, chunk in enumerate(chunks):
                meta = {
                    "content": chunk["content"],
                    "document_id": document_id,
                    "chunk_index": i,
                    **chunk.get("metadata", {}),
                }
                metadata_list.append(meta)

            # 插入向量数据库
            vector_ids = await self.vector_store.insert(
                collection_name=collection_name,
                vectors=embeddings,
                metadata=metadata_list,
            )

            logger.info(f"文档 {document_id} 导入完成: {len(vector_ids)} 个切片 -> {collection_name}")

            # 性能优化：文档更新后使该集合的 RAG 缓存失效
            rag_cache = _get_rag_cache()
            if rag_cache:
                await rag_cache.invalidate_collection(collection_name)

            return vector_ids

        except Exception as e:
            logger.error(f"文档导入失败: {e}")
            return []

    async def delete_document_vectors(
        self,
        knowledge_base_id: int,
        vector_ids: List[str],
    ) -> bool:
        """
        删除文档的向量数据

        Args:
            knowledge_base_id: 知识库 ID
            vector_ids: 向量 ID 列表

        Returns:
            是否成功
        """
        try:
            collection_name = f"kb_{knowledge_base_id}"
            result = await self.vector_store.delete(
                collection_name=collection_name,
                ids=vector_ids,
            )

            # 性能优化：删除向量后使该集合的 RAG 缓存失效
            if result:
                rag_cache = _get_rag_cache()
                if rag_cache:
                    await rag_cache.invalidate_collection(collection_name)

            return result
        except Exception as e:
            logger.error(f"删除向量失败: {e}")
            return False

    async def ensure_collection(
        self,
        knowledge_base_id: int,
        dimension: int = None,
    ) -> bool:
        """
        确保向量集合存在

        Args:
            knowledge_base_id: 知识库 ID
            dimension: 向量维度（默认使用 embedding_service 的维度）

        Returns:
            是否成功
        """
        try:
            collection_name = f"kb_{knowledge_base_id}"
            dim = dimension or self.embedding_service.get_dimension()
            return await self.vector_store.create_collection(
                collection_name=collection_name,
                dimension=dim,
            )
        except Exception as e:
            logger.error(f"创建集合失败: {e}")
            return False

    @staticmethod
    def _calculate_confidence(chunks: List[Dict]) -> float:
        """
        计算回答的置信度

        基于检索结果的分数分布来评估。
        """
        if not chunks:
            return 0.0

        scores = [c.get("score", 0) for c in chunks]
        avg_score = sum(scores) / len(scores)

        # 置信度 = 平均分数 * 结果数量权重
        count_weight = min(len(chunks) / 5.0, 1.0)
        confidence = avg_score * count_weight

        return round(min(confidence, 1.0), 4)


# 全局单例
rag_chain = RAGChain()
