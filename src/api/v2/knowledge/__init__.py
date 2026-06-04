"""
V2 知识引擎 API 路由

提供知识库管理、文档上传与解析、RAG 搜索与问答、研报生成等端点。
"""

import json
import os
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, Form, Query
from sqlalchemy import select, func, desc

from src.extensions import get_db
from src.api.v1.core.responses import ApiResponse

router = APIRouter()


# ==================== 知识库管理 ====================

@router.post("/bases", summary="创建知识库")
async def create_knowledge_base(
    name: str = Form(...),
    description: str = Form(""),
    embedding_model: str = Form("all-MiniLM-L6-v2"),
    chunk_size: int = Form(512),
    chunk_overlap: int = Form(50),
):
    """创建新的知识库"""
    try:
        from shared.models.knowledge.knowledge_base import KnowledgeBase
        from shared.services.knowledge.rag_chain import rag_chain

        with get_db() as db:
            kb = KnowledgeBase(
                name=name,
                description=description,
                embedding_model=embedding_model,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                vector_collection=f"kb_{{placeholder}}",
                document_count=0,
                chunk_count=0,
                created_at=datetime.utcnow(),
            )
            db.add(kb)
            db.flush()

            # 设置向量集合名称并创建
            kb.vector_collection = f"kb_{kb.id}"
            await rag_chain.ensure_collection(kb.id)

            db.commit()
            db.refresh(kb)

            return ApiResponse.success(data=kb.to_dict(), message="知识库创建成功")
    except Exception as e:
        return ApiResponse.error(message=f"创建知识库失败: {str(e)}")


@router.get("/bases", summary="获取知识库列表")
async def get_knowledge_bases(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """获取所有知识库列表"""
    try:
        from shared.models.knowledge.knowledge_base import KnowledgeBase

        with get_db() as db:
            query = select(KnowledgeBase).order_by(desc(KnowledgeBase.created_at))

            # 总数
            count_result = db.execute(select(func.count()).select_from(KnowledgeBase))
            total = count_result.scalar() or 0

            # 分页
            offset = (page - 1) * per_page
            result = db.execute(query.offset(offset).limit(per_page))
            items = [kb.to_dict() for kb in result.scalars().all()]

            return ApiResponse.success(data={
                "items": items,
                "total": total,
                "page": page,
                "per_page": per_page,
                "pages": (total + per_page - 1) // per_page,
            })
    except Exception as e:
        return ApiResponse.error(message=f"获取知识库列表失败: {str(e)}")


@router.get("/bases/{base_id}", summary="获取知识库详情")
async def get_knowledge_base(base_id: int):
    """获取指定知识库详情"""
    try:
        from shared.models.knowledge.knowledge_base import KnowledgeBase

        with get_db() as db:
            kb = db.get(KnowledgeBase, base_id)
            if not kb:
                return ApiResponse.error(message="知识库不存在", code=404)

            return ApiResponse.success(data=kb.to_dict())
    except Exception as e:
        return ApiResponse.error(message=f"获取知识库详情失败: {str(e)}")


@router.put("/bases/{base_id}", summary="更新知识库")
async def update_knowledge_base(
    base_id: int,
    name: str = Form(None),
    description: str = Form(None),
    chunk_size: int = Form(None),
    chunk_overlap: int = Form(None),
):
    """更新知识库配置"""
    try:
        from shared.models.knowledge.knowledge_base import KnowledgeBase

        with get_db() as db:
            kb = db.get(KnowledgeBase, base_id)
            if not kb:
                return ApiResponse.error(message="知识库不存在", code=404)

            if name is not None:
                kb.name = name
            if description is not None:
                kb.description = description
            if chunk_size is not None:
                kb.chunk_size = chunk_size
            if chunk_overlap is not None:
                kb.chunk_overlap = chunk_overlap
            kb.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(kb)

            return ApiResponse.success(data=kb.to_dict(), message="知识库更新成功")
    except Exception as e:
        return ApiResponse.error(message=f"更新知识库失败: {str(e)}")


@router.delete("/bases/{base_id}", summary="删除知识库")
async def delete_knowledge_base(base_id: int):
    """删除知识库及其所有文档和向量"""
    try:
        from shared.models.knowledge.knowledge_base import KnowledgeBase
        from shared.models.knowledge.knowledge_document import KnowledgeDocument
        from shared.models.knowledge.document_chunk import DocumentChunk
        from shared.services.knowledge.vector_store import vector_store

        with get_db() as db:
            kb = db.get(KnowledgeBase, base_id)
            if not kb:
                return ApiResponse.error(message="知识库不存在", code=404)

            # 删除所有切片记录
            db.execute(
                select(DocumentChunk).where(DocumentChunk.knowledge_base_id == base_id)
            )
            chunks = db.execute(
                select(DocumentChunk).where(DocumentChunk.knowledge_base_id == base_id)
            ).scalars().all()
            for chunk in chunks:
                db.delete(chunk)

            # 删除所有文档记录
            docs = db.execute(
                select(KnowledgeDocument).where(KnowledgeDocument.knowledge_base_id == base_id)
            ).scalars().all()
            for doc in docs:
                db.delete(doc)

            # 删除向量集合
            await vector_store.drop_collection(f"kb_{base_id}")

            db.delete(kb)
            db.commit()

            return ApiResponse.success(message="知识库已删除")
    except Exception as e:
        return ApiResponse.error(message=f"删除知识库失败: {str(e)}")


# ==================== 文档管理 ====================

@router.post("/bases/{base_id}/documents/upload", summary="上传文档")
async def upload_document(
    base_id: int,
    file: UploadFile = File(...),
):
    """
    上传文档到知识库

    支持格式: PDF, DOCX, TXT, HTML, MD
    流程: 上传 → 解析 → 切片 → Embedding → 存入向量数据库
    """
    try:
        from shared.models.knowledge.knowledge_base import KnowledgeBase
        from shared.models.knowledge.knowledge_document import KnowledgeDocument
        from shared.models.knowledge.document_chunk import DocumentChunk
        from shared.services.knowledge.document_parser import document_parser
        from shared.services.knowledge.chunker import document_chunker
        from shared.services.knowledge.rag_chain import rag_chain

        with get_db() as db:
            kb = db.get(KnowledgeBase, base_id)
            if not kb:
                return ApiResponse.error(message="知识库不存在", code=404)

            # 1. 保存上传文件
            upload_dir = os.path.join("media", "knowledge", str(base_id))
            os.makedirs(upload_dir, exist_ok=True)

            file_path = os.path.join(upload_dir, file.filename)
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)

            # 2. 检测文件类型
            _, ext = os.path.splitext(file.filename)
            file_type = ext.lstrip(".").lower()

            # 3. 创建文档记录
            doc = KnowledgeDocument(
                knowledge_base_id=base_id,
                title=file.filename,
                file_path=file_path,
                file_type=file_type,
                status="parsing",
                created_at=datetime.utcnow(),
            )
            db.add(doc)
            db.flush()

            # 4. 解析文档
            parse_result = await document_parser.parse(file_path, file_type)
            if not parse_result.success:
                doc.status = "failed"
                db.commit()
                return ApiResponse.error(message=f"文档解析失败: {parse_result.error}")

            doc.content_text = parse_result.text

            # 5. 切片
            chunks = await document_chunker.chunk(
                text=parse_result.text,
                strategy="recursive",
                chunk_size=kb.chunk_size,
                chunk_overlap=kb.chunk_overlap,
                metadata={"document_title": file.filename, "file_type": file_type},
            )

            if not chunks:
                doc.status = "failed"
                db.commit()
                return ApiResponse.error(message="文档切片为空")

            # 6. 保存切片记录
            chunk_records = []
            for chunk in chunks:
                record = DocumentChunk(
                    document_id=doc.id,
                    knowledge_base_id=base_id,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    token_count=chunk.token_count,
                    metadata_json=json.dumps(chunk.metadata, ensure_ascii=False),
                    created_at=datetime.utcnow(),
                )
                db.add(record)
                chunk_records.append({"content": chunk.content, "metadata": chunk.metadata})
            db.flush()

            # 7. Embedding + 向量存储
            vector_ids = await rag_chain.ingest_document(
                knowledge_base_id=base_id,
                document_id=doc.id,
                chunks=chunk_records,
            )

            # 更新切片的 embedding_id
            chunk_objs = db.execute(
                select(DocumentChunk).where(DocumentChunk.document_id == doc.id)
            ).scalars().all()
            for i, chunk_obj in enumerate(chunk_objs):
                if i < len(vector_ids):
                    chunk_obj.embedding_id = vector_ids[i]

            # 8. 更新统计
            doc.chunk_count = len(chunks)
            doc.status = "indexed"
            doc.metadata_json = json.dumps({
                "page_count": parse_result.page_count,
                "parser_metadata": parse_result.metadata,
            }, ensure_ascii=False)

            kb.document_count = (kb.document_count or 0) + 1
            kb.chunk_count = (kb.chunk_count or 0) + len(chunks)

            db.commit()
            db.refresh(doc)

            return ApiResponse.success(data={
                "document": doc.to_dict(),
                "chunk_count": len(chunks),
                "vector_count": len(vector_ids),
            }, message="文档上传并索引成功")
    except Exception as e:
        return ApiResponse.error(message=f"文档上传失败: {str(e)}")


@router.get("/bases/{base_id}/documents", summary="获取文档列表")
async def get_documents(
    base_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: str = Query(None),
):
    """获取指定知识库的文档列表"""
    try:
        from shared.models.knowledge.knowledge_document import KnowledgeDocument

        with get_db() as db:
            query = select(KnowledgeDocument).where(
                KnowledgeDocument.knowledge_base_id == base_id
            ).order_by(desc(KnowledgeDocument.created_at))

            if status:
                query = query.where(KnowledgeDocument.status == status)

            # 总数
            count_q = select(func.count()).select_from(KnowledgeDocument).where(
                KnowledgeDocument.knowledge_base_id == base_id
            )
            if status:
                count_q = count_q.where(KnowledgeDocument.status == status)
            total = db.execute(count_q).scalar() or 0

            # 分页
            offset = (page - 1) * per_page
            result = db.execute(query.offset(offset).limit(per_page))
            items = [doc.to_dict() for doc in result.scalars().all()]

            return ApiResponse.success(data={
                "items": items,
                "total": total,
                "page": page,
                "per_page": per_page,
            })
    except Exception as e:
        return ApiResponse.error(message=f"获取文档列表失败: {str(e)}")


@router.delete("/bases/{base_id}/documents/{doc_id}", summary="删除文档")
async def delete_document(base_id: int, doc_id: int):
    """删除文档及其切片和向量"""
    try:
        from shared.models.knowledge.knowledge_document import KnowledgeDocument
        from shared.models.knowledge.document_chunk import DocumentChunk
        from shared.models.knowledge.knowledge_base import KnowledgeBase
        from shared.services.knowledge.rag_chain import rag_chain

        with get_db() as db:
            doc = db.get(KnowledgeDocument, doc_id)
            if not doc or doc.knowledge_base_id != base_id:
                return ApiResponse.error(message="文档不存在", code=404)

            # 收集向量 ID
            chunks = db.execute(
                select(DocumentChunk).where(DocumentChunk.document_id == doc_id)
            ).scalars().all()
            vector_ids = [c.embedding_id for c in chunks if c.embedding_id]

            # 删除向量
            if vector_ids:
                await rag_chain.delete_document_vectors(base_id, vector_ids)

            # 删除切片记录
            for chunk in chunks:
                db.delete(chunk)

            # 删除物理文件
            if doc.file_path and os.path.exists(doc.file_path):
                try:
                    os.remove(doc.file_path)
                except OSError:
                    pass

            # 更新知识库统计
            kb = db.get(KnowledgeBase, base_id)
            if kb:
                kb.document_count = max(0, (kb.document_count or 0) - 1)
                kb.chunk_count = max(0, (kb.chunk_count or 0) - len(chunks))

            db.delete(doc)
            db.commit()

            return ApiResponse.success(message="文档已删除")
    except Exception as e:
        return ApiResponse.error(message=f"删除文档失败: {str(e)}")


# ==================== RAG 搜索与问答 ====================

@router.post("/bases/{base_id}/search", summary="RAG 语义搜索")
async def rag_search(
    base_id: int,
    query: str = Form(...),
    top_k: int = Form(10),
    score_threshold: float = Form(0.0),
):
    """在知识库中进行语义搜索（纯向量检索，不经过 LLM）"""
    try:
        from shared.services.knowledge.rag_chain import rag_chain

        results = await rag_chain.search(
            query=query,
            knowledge_base_id=base_id,
            top_k=top_k,
            score_threshold=score_threshold,
        )

        return ApiResponse.success(data={
            "query": query,
            "results": results,
            "count": len(results),
        })
    except Exception as e:
        return ApiResponse.error(message=f"搜索失败: {str(e)}")


@router.post("/bases/{base_id}/qa", summary="知识问答")
async def knowledge_qa(
    base_id: int,
    question: str = Form(...),
    top_k: int = Form(5),
    system_prompt: str = Form(None),
):
    """
    知识库问答（RAG）

    流程: Embedding → 向量检索 → LLM 生成回答（附引用来源）
    """
    try:
        from shared.services.knowledge.rag_chain import rag_chain

        result = await rag_chain.query(
            question=question,
            knowledge_base_id=base_id,
            top_k=top_k,
            system_prompt=system_prompt,
            include_sources=True,
        )

        if not result.success:
            return ApiResponse.error(message=f"问答失败: {result.error}")

        return ApiResponse.success(data={
            "question": question,
            "answer": result.answer,
            "sources": result.sources,
            "confidence": result.confidence,
        })
    except Exception as e:
        return ApiResponse.error(message=f"问答失败: {str(e)}")


# ==================== 研报生成 ====================

@router.post("/bases/{base_id}/reports/generate", summary="生成研报")
async def generate_report(
    base_id: int,
    topic: str = Form(...),
    template: str = Form("default"),
    max_sections: int = Form(6),
    detail_level: str = Form("standard"),
):
    """
    基于知识库内容生成 AI 研报

    流程: RAG 检索 → 生成提纲 → 逐章节生成 → 汇总摘要
    """
    try:
        from shared.services.knowledge.report_generator import report_generator
        from shared.models.knowledge.generated_report import GeneratedReport

        result = await report_generator.generate_report(
            topic=topic,
            knowledge_base_id=base_id,
            template=template,
            max_sections=max_sections,
            detail_level=detail_level,
        )

        if not result.success:
            return ApiResponse.error(message=f"研报生成失败: {result.error}")

        # 保存研报到数据库
        with get_db() as db:
            report = GeneratedReport(
                title=result.title,
                content=result.markdown,
                knowledge_base_ids=json.dumps([base_id]),
                status="completed",
                created_at=datetime.utcnow(),
            )
            db.add(report)
            db.commit()
            db.refresh(report)

            return ApiResponse.success(data={
                "report_id": report.id,
                "title": result.title,
                "summary": result.summary,
                "sections": [{"title": s.title, "content": s.content, "order": s.order} for s in result.sections],
                "sources_count": len(result.sources),
                "generated_at": result.generated_at,
            }, message="研报生成成功")
    except Exception as e:
        return ApiResponse.error(message=f"研报生成失败: {str(e)}")


@router.get("/reports", summary="获取研报列表")
async def get_reports(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: str = Query(None),
):
    """获取已生成的报告列表"""
    try:
        from shared.models.knowledge.generated_report import GeneratedReport

        with get_db() as db:
            query = select(GeneratedReport).order_by(desc(GeneratedReport.created_at))

            if status:
                query = query.where(GeneratedReport.status == status)

            count_q = select(func.count()).select_from(GeneratedReport)
            if status:
                count_q = count_q.where(GeneratedReport.status == status)
            total = db.execute(count_q).scalar() or 0

            offset = (page - 1) * per_page
            result = db.execute(query.offset(offset).limit(per_page))
            items = [r.to_dict() for r in result.scalars().all()]

            return ApiResponse.success(data={
                "items": items,
                "total": total,
                "page": page,
                "per_page": per_page,
            })
    except Exception as e:
        return ApiResponse.error(message=f"获取研报列表失败: {str(e)}")


@router.get("/reports/{report_id}", summary="获取研报详情")
async def get_report_detail(report_id: int):
    """获取指定研报详情"""
    try:
        from shared.models.knowledge.generated_report import GeneratedReport

        with get_db() as db:
            report = db.get(GeneratedReport, report_id)
            if not report:
                return ApiResponse.error(message="研报不存在", code=404)

            return ApiResponse.success(data=report.to_dict())
    except Exception as e:
        return ApiResponse.error(message=f"获取研报详情失败: {str(e)}")


# ==================== 报告模板 ====================

@router.get("/templates", summary="获取报告模板列表")
async def get_report_templates(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """获取报告模板列表"""
    try:
        from shared.models.knowledge.report_template import ReportTemplate

        with get_db() as db:
            query = select(ReportTemplate).order_by(desc(ReportTemplate.created_at))

            count_q = select(func.count()).select_from(ReportTemplate)
            total = db.execute(count_q).scalar() or 0

            offset = (page - 1) * per_page
            result = db.execute(query.offset(offset).limit(per_page))
            items = [t.to_dict() for t in result.scalars().all()]

            return ApiResponse.success(data={
                "items": items,
                "total": total,
                "page": page,
                "per_page": per_page,
            })
    except Exception as e:
        return ApiResponse.error(message=f"获取模板列表失败: {str(e)}")


@router.post("/templates", summary="创建报告模板")
async def create_report_template(
    name: str = Form(...),
    description: str = Form(""),
    template_content: str = Form(""),
    sections: str = Form("[]"),
):
    """创建新的报告模板"""
    try:
        from shared.models.knowledge.report_template import ReportTemplate

        with get_db() as db:
            template = ReportTemplate(
                name=name,
                description=description,
                template_content=template_content,
                sections=sections,
                created_at=datetime.utcnow(),
            )
            db.add(template)
            db.commit()
            db.refresh(template)

            return ApiResponse.success(data=template.to_dict(), message="模板创建成功")
    except Exception as e:
        return ApiResponse.error(message=f"创建模板失败: {str(e)}")
