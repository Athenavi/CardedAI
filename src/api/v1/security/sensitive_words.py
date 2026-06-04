"""
敏感词管理 API
提供敏感词的增删改查功能
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, Body, Request
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.sensitive_word import SensitiveWord
from src.api.v1.core.responses import ApiResponse
from src.auth import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db

router = APIRouter(tags=["sensitive-words"])

# Pydantic 模型定义
class SensitiveWordCreate(BaseModel):
    word: str
    level: int
    action: str
    replacement: Optional[str]
    category: Optional[str]


class SensitiveWordUpdate(BaseModel):
    level: Optional[int] = None
    action: Optional[str] = None
    replacement: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None


@router.post("/")
async def create_sensitive_word(
        request: Request,
        data: SensitiveWordCreate,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    添加敏感词

    Args:
        data: 敏感词数据
    """
    # 打印原始请求体
    try:
        body = await request.json()
        print(f"[DEBUG] Raw request body: {body}")
    except:
        print(f"[DEBUG] Could not read request body")

    print(f"[DEBUG] Received data: {data}")
    print(f"[DEBUG] Current user ID: {current_user.id}")
    try:
        # 验证action参数
        if data.action not in ['block', 'replace', 'warn']:
            return ApiResponse(success=False, error="无效的处理方式，必须是 block/replace/warn")

        # 检查是否已存在
        existing_query = select(SensitiveWord).where(SensitiveWord.word == data.word)
        existing_result = await db.execute(existing_query)
        existing = existing_result.scalar_one_or_none()

        if existing:
            return ApiResponse(success=False, error=f"敏感词 '{data.word}' 已存在")

        # 创建新敏感词
        new_word = SensitiveWord(
            word=data.word,
            level=data.level,
            action=data.action,
            replacement=data.replacement,
            category=data.category,
            is_active=True,
            created_by=1,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        db.add(new_word)
        await db.commit()
        await db.refresh(new_word)

        # 刷新缓存
        try:
            from shared.services.security.sensitive_word_service import sensitive_word_service
            await sensitive_word_service.refresh_cache()
        except Exception:
            pass  # 缓存刷新失败不影响主流程

        return ApiResponse(
            success=True,
            data={
                "id": new_word.id,
                "word": new_word.word,
                "message": "敏感词添加成功"
            }
        )

    except Exception as e:
        import traceback
        print(f"Error in create_sensitive_word: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/")
async def list_sensitive_words(
        page: int = Query(1, ge=1, description="页码"),
        per_page: int = Query(50, ge=1, le=200, description="每页数量"),
        level: Optional[int] = Query(None, ge=1, le=3, description="敏感级别筛选"),
        category: Optional[str] = Query(None, description="分类筛选"),
        is_active: Optional[bool] = Query(None, description="激活状态筛选"),
        keyword: Optional[str] = Query(None, description="关键词搜索"),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取敏感词列表

    Args:
        page: 页码
        per_page: 每页数量
        level: 敏感级别
        category: 分类
        is_active: 激活状态
        keyword: 搜索关键词
    """
    try:
        offset = (page - 1) * per_page

        # 构建查询
        query = select(SensitiveWord)

        # 应用筛选条件
        if level is not None:
            query = query.where(SensitiveWord.level == level)
        if category is not None:
            query = query.where(SensitiveWord.category == category)
        if is_active is not None:
            query = query.where(SensitiveWord.is_active == is_active)
        if keyword:
            query = query.where(SensitiveWord.word.ilike(f"%{keyword}%"))

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # 排序和分页
        query = query.order_by(SensitiveWord.created_at.desc()).offset(offset).limit(per_page)

        result = await db.execute(query)
        words = result.scalars().all()

        word_list = []
        for w in words:
            word_list.append({
                "id": w.id,
                "word": w.word,
                "level": w.level,
                "action": w.action,
                "replacement": w.replacement,
                "category": w.category,
                "is_active": w.is_active,
                "created_at": w.created_at.isoformat() if w.created_at else None,
                "updated_at": w.updated_at.isoformat() if w.updated_at else None
            })

        return ApiResponse(
            success=True,
            data={
                "items": word_list,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page
            }
        )

    except Exception as e:
        import traceback
        print(f"Error in list_sensitive_words: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/statistics")
async def get_sensitive_word_statistics(
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取敏感词统计信息
    """
    try:
        # 总数
        total_query = select(func.count()).select_from(SensitiveWord)
        total_result = await db.execute(total_query)
        total = total_result.scalar() or 0

        # 按级别统计
        level_query = (
            select(SensitiveWord.level, func.count())
            .group_by(SensitiveWord.level)
        )
        level_result = await db.execute(level_query)
        by_level = {row[0]: row[1] for row in level_result.fetchall()}

        # 按处理方式统计
        action_query = (
            select(SensitiveWord.action, func.count())
            .group_by(SensitiveWord.action)
        )
        action_result = await db.execute(action_query)
        by_action = {row[0]: row[1] for row in action_result.fetchall()}

        # 按分类统计
        category_query = (
            select(SensitiveWord.category, func.count())
            .where(SensitiveWord.category.isnot(None))
            .group_by(SensitiveWord.category)
        )
        category_result = await db.execute(category_query)
        by_category = {row[0]: row[1] for row in category_result.fetchall()}

        # 激活状态统计
        active_query = (
            select(SensitiveWord.is_active, func.count())
            .group_by(SensitiveWord.is_active)
        )
        active_result = await db.execute(active_query)
        by_status = {
            "active": 0,
            "inactive": 0
        }
        for row in active_result.fetchall():
            if row[0]:
                by_status["active"] = row[1]
            else:
                by_status["inactive"] = row[1]

        return ApiResponse(
            success=True,
            data={
                "total": total,
                "by_level": by_level,
                "by_action": by_action,
                "by_category": by_category,
                "by_status": by_status
            }
        )

    except Exception as e:
        import traceback
        print(f"Error in get_sensitive_word_statistics: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))
@router.get("/{word_id}")
async def get_sensitive_word(
        word_id: int,
        db: AsyncSession = Depends(get_async_db)
):
    """获取单个敏感词详情"""
    try:
        query = select(SensitiveWord).where(SensitiveWord.id == word_id)
        result = await db.execute(query)
        word = result.scalar_one_or_none()

        if not word:
            return ApiResponse(success=False, error="敏感词不存在")

        return ApiResponse(
            success=True,
            data={
                "id": word.id,
                "word": word.word,
                "level": word.level,
                "action": word.action,
                "replacement": word.replacement,
                "category": word.category,
                "is_active": word.is_active,
                "created_by": word.created_by,
                "created_at": word.created_at.isoformat() if word.created_at else None,
                "updated_at": word.updated_at.isoformat() if word.updated_at else None
            }
        )

    except Exception as e:
        import traceback
        print(f"Error in get_sensitive_word: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.put("/{word_id}")
async def update_sensitive_word(
        word_id: int,
        data: SensitiveWordUpdate,
        db: AsyncSession = Depends(get_async_db)
):
    """
    更新敏感词

    Args:
        word_id: 敏感词ID
        data: 更新数据
    """
    try:
        # 查询敏感词
        query = select(SensitiveWord).where(SensitiveWord.id == word_id)
        result = await db.execute(query)
        word = result.scalar_one_or_none()

        if not word:
            return ApiResponse(success=False, error="敏感词不存在")

        # 验证action参数
        if data.action and data.action not in ['block', 'replace', 'warn']:
            return ApiResponse(success=False, error="无效的处理方式")

        # 更新字段
        if data.level is not None:
            word.level = data.level
        if data.action is not None:
            word.action = data.action
        if data.replacement is not None:
            word.replacement = data.replacement
        if data.category is not None:
            word.category = data.category
        if data.is_active is not None:
            word.is_active = data.is_active

        word.updated_at = datetime.now()
        await db.commit()
        await db.refresh(word)

        # 刷新缓存
        try:
            from shared.services.security.sensitive_word_service import sensitive_word_service
            await sensitive_word_service.refresh_cache()
        except Exception:
            pass  # 缓存刷新失败不影响主流程

        return ApiResponse(
            success=True,
            message="敏感词更新成功"
        )

    except Exception as e:
        import traceback
        print(f"Error in update_sensitive_word: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.delete("/{word_id}")
async def delete_sensitive_word(
        word_id: int,
        db: AsyncSession = Depends(get_async_db)
):
    """删除敏感词"""
    try:
        query = select(SensitiveWord).where(SensitiveWord.id == word_id)
        result = await db.execute(query)
        word = result.scalar_one_or_none()

        if not word:
            return ApiResponse(success=False, error="敏感词不存在")

        await db.delete(word)
        await db.commit()

        # 刷新缓存
        try:
            from shared.services.security.sensitive_word_service import sensitive_word_service
            await sensitive_word_service.refresh_cache()
        except Exception:
            pass  # 缓存刷新失败不影响主流程

        return ApiResponse(
            success=True,
            message="敏感词删除成功"
        )

    except Exception as e:
        import traceback
        print(f"Error in delete_sensitive_word: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.post("/batch-import")
async def batch_import_sensitive_words(
        words: list = Body(..., description="敏感词列表，每项包含word, level, action等字段"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    批量导入敏感词

    Args:
        words: 敏感词列表
            [
                {"word": "xxx", "level": 1, "action": "block", "category": "政治"},
                ...
            ]
    """
    try:
        success_count = 0
        failed_count = 0
        errors = []

        for item in words:
            try:
                word_text = item.get('word')
                if not word_text:
                    failed_count += 1
                    errors.append({"word": item.get('word'), "error": "缺少word字段"})
                    continue

                # 检查是否已存在
                existing_query = select(SensitiveWord).where(SensitiveWord.word == word_text)
                existing_result = await db.execute(existing_query)
                existing = existing_result.scalar_one_or_none()

                if existing:
                    failed_count += 1
                    errors.append({"word": word_text, "error": "已存在"})
                    continue

                # 创建新敏感词
                new_word = SensitiveWord(
                    word=word_text,
                    level=item.get('level', 1),
                    action=item.get('action', 'block'),
                    replacement=item.get('replacement'),
                    category=item.get('category'),
                    is_active=True,
                    created_by=current_user.id,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )

                db.add(new_word)
                success_count += 1

            except Exception as e:
                failed_count += 1
                errors.append({"word": item.get('word'), "error": str(e)})

        await db.commit()

        # 刷新缓存
        try:
            from shared.services.security.sensitive_word_service import sensitive_word_service
            await sensitive_word_service.refresh_cache()
        except Exception:
            pass  # 缓存刷新失败不影响主流程

        return ApiResponse(
            success=True,
            data={
                "success_count": success_count,
                "failed_count": failed_count,
                "errors": errors[:10]  # 只返回前10个错误
            },
            message=f"成功导入 {success_count} 个敏感词"
        )

    except Exception as e:
        import traceback
        print(f"Error in batch_import_sensitive_words: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.post("/refresh-cache")
async def refresh_sensitive_word_cache(
        current_user=Depends(jwt_required),
):
    """
    刷新敏感词缓存（管理员操作）
    """
    try:
        from shared.services.security.sensitive_word_service import sensitive_word_service
        await sensitive_word_service.refresh_cache()

        return ApiResponse(
            success=True,
            message="缓存刷新成功"
        )

    except Exception as e:
        import traceback
        print(f"Error in refresh_sensitive_word_cache: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


