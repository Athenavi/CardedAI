"""
协作编辑 HTTP API
"""
from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import ArticleRevision
from shared.services.chat.collaboration import collaboration_service, CollaborativeDocument
from src.auth import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db

router = APIRouter(tags=["collaboration"])


@router.post("/documents/{document_id}/save")
async def save_collaborative_document(
        document_id: str,
        save_data: dict,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    保存协作文档内容到文章修订版本
    
    Args:
        document_id: 文档ID（invite_id）
        save_data: {"content": "...", "change_summary": "..."}
    """
    print(f"[Collab Save] Saving document {document_id} for user {current_user.id}")

    # 获取协作文档
    doc = collaboration_service.documents.get(document_id)

    if not doc:
        print(f"[Collab Save] Document {document_id} not found in memory")
        # 即使文档不在内存中，也尝试从数据库保存
        # 这种情况可能发生在用户刷新页面后

    # 如果提供了新内容，更新文档状态
    if "content" in save_data:
        content = save_data["content"]
        print(f"[Collab Save] Received content, length: {len(content)}")

        # 更新或创建文档对象
        if not doc:
            doc = CollaborativeDocument(document_id)
            collaboration_service.documents[document_id] = doc

        doc.set_content(content)
    try:
        # 保存到修订版本
        change_summary = save_data.get("change_summary", "协作编辑保存")
        # 计算下一个版本号
        max_rev_query = select(func.max(ArticleRevision.revision_number)).where(
            ArticleRevision.article_id == doc.article_id
        )
        max_rev_result = await db.execute(max_rev_query)
        next_revision = (max_rev_result.scalar() or 0) + 1
        revision = ArticleRevision(
            article_id=doc.article_id,
            revision_number=next_revision,
            content=save_data["content"],
            change_summary=change_summary,
            created_at=datetime.now().replace(tzinfo=None)  # 移除时区信息以匹配数据库字段
        )

        db.add(revision)
        await db.commit()
        await db.refresh(revision)
        print(f"[Collab Save] Successfully saved document {document_id}")
        return {
            "success": True,
            "message": "Document saved successfully",
            "data": {
                "document_id": document_id,
                "article_id": doc.article_id if doc else None,
                "saved_at": doc.last_modified.isoformat() if doc else None
            }
        }
    except Exception as e:
        print(f"[Collab Save] Failed to save document {document_id}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Failed to save to revision:{e}"}
        )
