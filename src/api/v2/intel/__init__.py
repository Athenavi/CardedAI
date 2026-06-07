"""
V2 情报引擎 API 路由

提供数据源管理、情报查询、简报生成、预警规则管理等端点。
统一使用 ApiResponse 响应格式，分页接口包含 total 总数。
"""

import json
import logging
import math
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, model_validator

from src.api.v1.core.responses import ApiResponse, PaginationInfo

logger = logging.getLogger(__name__)
router = APIRouter(tags=["intel-v2"])


# ==================== 请求模型 ====================

class CreateSourceRequest(BaseModel):
    name: str
    source_type: str
    url: str
    config: Optional[str] = "{}"
    schedule_cron: Optional[str] = None


class UpdateSourceRequest(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    config: Optional[str] = None
    schedule_cron: Optional[str] = None
    is_active: Optional[bool] = None


class CreateAlertRuleRequest(BaseModel):
    name: str
    severity: str = "medium"
    keywords: str = "[]"
    conditions: str = "{}"
    actions: str = "[]"
    is_active: bool = True

    @model_validator(mode='before')
    @classmethod
    def normalize_fields(cls, data):
        if isinstance(data, dict):
            # Accept rule_type as alias for severity
            if 'rule_type' in data and 'severity' not in data:
                data['severity'] = data.pop('rule_type')
            # Accept condition (singular) as alias for conditions
            if 'condition' in data and 'conditions' not in data:
                data['conditions'] = data.pop('condition')
            # Coerce dict/list fields to JSON strings
            for key in ('conditions', 'keywords', 'actions'):
                if key in data and isinstance(data[key], (dict, list)):
                    data[key] = json.dumps(data[key], ensure_ascii=False)
        return data


# ==================== 数据源管理 ====================

@router.post("/sources", summary="创建数据源", response_model=ApiResponse)
async def create_source(req: CreateSourceRequest):
    """创建新的数据源配置"""
    from shared.models import DataSource
    from src.extensions import get_db

    try:
        parsed_config = json.loads(req.config)
    except json.JSONDecodeError:
        return ApiResponse(success=False, error="config 不是合法的 JSON")

    try:
        with get_db() as db:
            source = DataSource(
                name=req.name,
                source_type=req.source_type,
                url=req.url,
                config=json.dumps(parsed_config, ensure_ascii=False),
                schedule_cron=req.schedule_cron,
                is_active=True,
                created_at=datetime.now(timezone.utc),
            )
            db.add(source)
            db.flush()
            source_id = source.id
            db.commit()

        return ApiResponse(success=True, data={"id": source_id}, message="数据源创建成功")
    except Exception as e:
        logger.error(f"创建数据源失败: {e}")
        return ApiResponse(success=False, error=f"创建数据源失败: {str(e)}")


@router.get("/sources", summary="获取数据源列表", response_model=ApiResponse)
async def get_sources(
    page: int = 1,
    per_page: int = 20,
    source_type: Optional[str] = None,
    is_active: Optional[bool] = None,
):
    """获取所有数据源配置"""
    from sqlalchemy import select, func
    from shared.models import DataSource
    from src.extensions import get_db

    try:
        with get_db() as db:
            base_query = select(DataSource)
            if source_type:
                base_query = base_query.where(DataSource.source_type == source_type)
            if is_active is not None:
                base_query = base_query.where(DataSource.is_active == is_active)

            # 统计总数
            count_query = select(func.count()).select_from(base_query.subquery())
            total = db.execute(count_query).scalar() or 0

            # 分页查询
            offset = (page - 1) * per_page
            query = base_query.order_by(DataSource.created_at.desc()).offset(offset).limit(per_page)
            items = db.execute(query).scalars().all()

            total_pages = math.ceil(total / per_page) if per_page > 0 else 0
            return ApiResponse(
                success=True,
                data=[s.to_dict() for s in items],
                pagination=PaginationInfo(
                    current_page=page,
                    per_page=per_page,
                    total=total,
                    total_pages=total_pages,
                    has_next=page < total_pages,
                    has_prev=page > 1,
                ),
            )
    except Exception as e:
        logger.error(f"获取数据源列表失败: {e}")
        return ApiResponse(success=False, error=f"获取数据源列表失败: {str(e)}")


@router.get("/sources/{source_id}", summary="获取数据源详情", response_model=ApiResponse)
async def get_source(source_id: int):
    """获取指定数据源详情"""
    from shared.models import DataSource
    from src.extensions import get_db

    try:
        with get_db() as db:
            source = db.get(DataSource, source_id)
            if not source:
                raise HTTPException(status_code=404, detail="数据源不存在")
            return ApiResponse(success=True, data=source.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取数据源详情失败: {e}")
        return ApiResponse(success=False, error=f"获取数据源详情失败: {str(e)}")


@router.put("/sources/{source_id}", summary="更新数据源", response_model=ApiResponse)
async def update_source(source_id: int, req: UpdateSourceRequest):
    """更新数据源配置"""
    from shared.models import DataSource
    from src.extensions import get_db

    try:
        with get_db() as db:
            source = db.get(DataSource, source_id)
            if not source:
                raise HTTPException(status_code=404, detail="数据源不存在")

            if req.name is not None:
                source.name = req.name
            if req.url is not None:
                source.url = req.url
            if req.config is not None:
                try:
                    json.loads(req.config)  # 验证 JSON
                    source.config = req.config
                except json.JSONDecodeError:
                    return ApiResponse(success=False, error="config 不是合法的 JSON")
            if req.schedule_cron is not None:
                source.schedule_cron = req.schedule_cron
            if req.is_active is not None:
                source.is_active = req.is_active

            db.commit()

        return ApiResponse(success=True, message="数据源更新成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新数据源失败: {e}")
        return ApiResponse(success=False, error=f"更新数据源失败: {str(e)}")


@router.delete("/sources/{source_id}", summary="删除数据源", response_model=ApiResponse)
async def delete_source(source_id: int):
    """删除数据源"""
    from shared.models import DataSource
    from src.extensions import get_db

    try:
        with get_db() as db:
            source = db.get(DataSource, source_id)
            if not source:
                raise HTTPException(status_code=404, detail="数据源不存在")
            db.delete(source)
            db.commit()

        return ApiResponse(success=True, message="数据源已删除")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除数据源失败: {e}")
        return ApiResponse(success=False, error=f"删除数据源失败: {str(e)}")


@router.post("/sources/{source_id}/collect", summary="手动触发采集", response_model=ApiResponse)
async def trigger_collect(source_id: int):
    """手动触发指定数据源的采集任务"""
    from shared.services.intel.collector_engine import collector_engine, setup_default_collectors

    try:
        # 确保采集器已注册
        if not collector_engine.registered_types:
            setup_default_collectors()

        result = await collector_engine.run_collection(source_id)
        return ApiResponse(success=True, data=result)
    except Exception as e:
        logger.error(f"触发采集失败: {e}")
        return ApiResponse(success=False, error=f"触发采集失败: {str(e)}")


# ==================== 采集条目 ====================

@router.get("/items", summary="获取采集条目列表", response_model=ApiResponse)
async def get_items(
    page: int = 1,
    per_page: int = 20,
    source_id: Optional[int] = None,
    status: Optional[str] = None,
):
    """获取采集到的原始数据条目"""
    from sqlalchemy import select, func
    from shared.models import CollectedItem
    from src.extensions import get_db

    try:
        with get_db() as db:
            base_query = select(CollectedItem)
            if source_id:
                base_query = base_query.where(CollectedItem.source_id == source_id)
            if status:
                base_query = base_query.where(CollectedItem.status == status)

            # 统计总数
            count_query = select(func.count()).select_from(base_query.subquery())
            total = db.execute(count_query).scalar() or 0

            # 分页查询
            offset = (page - 1) * per_page
            query = base_query.order_by(CollectedItem.collected_at.desc()).offset(offset).limit(per_page)
            items = db.execute(query).scalars().all()

            total_pages = math.ceil(total / per_page) if per_page > 0 else 0
            return ApiResponse(
                success=True,
                data=[i.to_dict() for i in items],
                pagination=PaginationInfo(
                    current_page=page,
                    per_page=per_page,
                    total=total,
                    total_pages=total_pages,
                    has_next=page < total_pages,
                    has_prev=page > 1,
                ),
            )
    except Exception as e:
        logger.error(f"获取采集条目失败: {e}")
        return ApiResponse(success=False, error=f"获取采集条目失败: {str(e)}")


# ==================== 情报 ====================

@router.get("/intelligence", summary="获取情报列表", response_model=ApiResponse)
async def get_intelligence(
    page: int = 1,
    per_page: int = 20,
    category: Optional[str] = None,
    sentiment: Optional[str] = None,
):
    """获取 AI 分析后的情报条目"""
    from sqlalchemy import select, func, desc
    from shared.models import Intelligence
    from src.extensions import get_db

    try:
        with get_db() as db:
            base_query = select(Intelligence)
            if category:
                base_query = base_query.where(Intelligence.category == category)
            if sentiment:
                base_query = base_query.where(Intelligence.sentiment == sentiment)

            # 统计总数
            count_query = select(func.count()).select_from(base_query.subquery())
            total = db.execute(count_query).scalar() or 0

            # 分页查询
            offset = (page - 1) * per_page
            query = base_query.order_by(desc(Intelligence.created_at)).offset(offset).limit(per_page)
            items = db.execute(query).scalars().all()

            total_pages = math.ceil(total / per_page) if per_page > 0 else 0
            return ApiResponse(
                success=True,
                data=[i.to_dict() for i in items],
                pagination=PaginationInfo(
                    current_page=page,
                    per_page=per_page,
                    total=total,
                    total_pages=total_pages,
                    has_next=page < total_pages,
                    has_prev=page > 1,
                ),
            )
    except Exception as e:
        logger.error(f"获取情报列表失败: {e}")
        return ApiResponse(success=False, error=f"获取情报列表失败: {str(e)}")


@router.get("/intelligence/{intel_id}", summary="获取情报详情", response_model=ApiResponse)
async def get_intelligence_detail(intel_id: int):
    """获取单条情报详情"""
    from shared.models import Intelligence
    from src.extensions import get_db

    try:
        with get_db() as db:
            intel = db.get(Intelligence, intel_id)
            if not intel:
                raise HTTPException(status_code=404, detail="情报不存在")
            return ApiResponse(success=True, data=intel.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取情报详情失败: {e}")
        return ApiResponse(success=False, error=f"获取情报详情失败: {str(e)}")


# ==================== 简报 ====================

@router.get("/briefings", summary="获取简报列表", response_model=ApiResponse)
async def get_briefings(
    page: int = 1,
    per_page: int = 20,
    briefing_type: Optional[str] = None,
):
    """获取情报简报"""
    from sqlalchemy import select, func, desc
    from shared.models import Briefing
    from src.extensions import get_db

    try:
        with get_db() as db:
            base_query = select(Briefing)
            if briefing_type:
                base_query = base_query.where(Briefing.briefing_type == briefing_type)

            # 统计总数
            count_query = select(func.count()).select_from(base_query.subquery())
            total = db.execute(count_query).scalar() or 0

            # 分页查询
            offset = (page - 1) * per_page
            query = base_query.order_by(desc(Briefing.created_at)).offset(offset).limit(per_page)
            items = db.execute(query).scalars().all()

            total_pages = math.ceil(total / per_page) if per_page > 0 else 0
            return ApiResponse(
                success=True,
                data=[b.to_dict() for b in items],
                pagination=PaginationInfo(
                    current_page=page,
                    per_page=per_page,
                    total=total,
                    total_pages=total_pages,
                    has_next=page < total_pages,
                    has_prev=page > 1,
                ),
            )
    except Exception as e:
        logger.error(f"获取简报列表失败: {e}")
        return ApiResponse(success=False, error=f"获取简报列表失败: {str(e)}")


@router.get("/briefings/{briefing_id}", summary="获取简报详情", response_model=ApiResponse)
async def get_briefing_detail(briefing_id: int):
    """获取单条简报详情"""
    from shared.models import Briefing
    from src.extensions import get_db

    try:
        with get_db() as db:
            briefing = db.get(Briefing, briefing_id)
            if not briefing:
                raise HTTPException(status_code=404, detail="简报不存在")
            return ApiResponse(success=True, data=briefing.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取简报详情失败: {e}")
        return ApiResponse(success=False, error=f"获取简报详情失败: {str(e)}")


@router.post("/briefings/generate", summary="生成简报", response_model=ApiResponse)
async def generate_briefing(briefing_type: str = "daily", topic: Optional[str] = None, days: int = 7):
    """基于最新情报生成简报"""
    from shared.services.intel.briefing_generator import briefing_generator

    try:
        if briefing_type == "daily":
            result = await briefing_generator.generate_daily_briefing()
        elif briefing_type == "custom" and topic:
            result = await briefing_generator.generate_custom_briefing(topic=topic, days=days)
        else:
            return ApiResponse(success=False, error="自定义简报需要提供 topic 参数")

        return ApiResponse(
            success=result.get("success", False),
            data=result,
            message="简报生成成功" if result.get("success") else "简报生成失败",
        )
    except Exception as e:
        logger.error(f"生成简报失败: {e}")
        return ApiResponse(success=False, error=f"生成简报失败: {str(e)}")


# ==================== 预警 ====================

@router.get("/alerts/rules", summary="获取预警规则列表", response_model=ApiResponse)
async def get_alert_rules(
    page: int = 1,
    per_page: int = 20,
    is_active: Optional[bool] = None,
):
    """获取预警规则"""
    from sqlalchemy import select, func, desc
    from shared.models import AlertRule
    from src.extensions import get_db

    try:
        with get_db() as db:
            base_query = select(AlertRule)
            if is_active is not None:
                base_query = base_query.where(AlertRule.is_active == is_active)

            # 统计总数
            count_query = select(func.count()).select_from(base_query.subquery())
            total = db.execute(count_query).scalar() or 0

            # 分页查询
            offset = (page - 1) * per_page
            query = base_query.order_by(desc(AlertRule.created_at)).offset(offset).limit(per_page)
            items = db.execute(query).scalars().all()

            total_pages = math.ceil(total / per_page) if per_page > 0 else 0
            return ApiResponse(
                success=True,
                data=[r.to_dict() for r in items],
                pagination=PaginationInfo(
                    current_page=page,
                    per_page=per_page,
                    total=total,
                    total_pages=total_pages,
                    has_next=page < total_pages,
                    has_prev=page > 1,
                ),
            )
    except Exception as e:
        logger.error(f"获取预警规则失败: {e}")
        return ApiResponse(success=False, error=f"获取预警规则失败: {str(e)}")


@router.post("/alerts/rules", summary="创建预警规则", response_model=ApiResponse)
async def create_alert_rule(req: CreateAlertRuleRequest):
    """创建新的预警规则"""
    from shared.models import AlertRule
    from src.extensions import get_db

    # 验证 JSON
    for field_name, field_val in [("keywords", req.keywords), ("conditions", req.conditions), ("actions", req.actions)]:
        try:
            json.loads(field_val)
        except json.JSONDecodeError:
            return ApiResponse(success=False, error=f"{field_name} 不是合法的 JSON")

    try:
        with get_db() as db:
            rule = AlertRule(
                name=req.name,
                severity=req.severity,
                keywords=req.keywords,
                conditions=req.conditions,
                actions=req.actions,
                is_active=req.is_active,
                created_at=datetime.now(timezone.utc),
            )
            db.add(rule)
            db.flush()
            rule_id = rule.id
            db.commit()

        return ApiResponse(success=True, data={"id": rule_id}, message="预警规则创建成功")
    except Exception as e:
        logger.error(f"创建预警规则失败: {e}")
        return ApiResponse(success=False, error=f"创建预警规则失败: {str(e)}")


@router.get("/alerts/events", summary="获取预警事件历史", response_model=ApiResponse)
async def get_alert_events(
    page: int = 1,
    per_page: int = 20,
):
    """获取预警事件列表"""
    from sqlalchemy import select, func, desc
    from src.extensions import get_db

    try:
        # 尝试从数据库获取 AlertEvent
        from shared.models import AlertEvent
        with get_db() as db:
            base_query = select(AlertEvent)

            # 统计总数
            count_query = select(func.count()).select_from(base_query.subquery())
            total = db.execute(count_query).scalar() or 0

            # 分页查询
            offset = (page - 1) * per_page
            query = base_query.order_by(desc(AlertEvent.created_at)).offset(offset).limit(per_page)
            items = db.execute(query).scalars().all()

            total_pages = math.ceil(total / per_page) if per_page > 0 else 0
            return ApiResponse(
                success=True,
                data=[e.to_dict() for e in items],
                pagination=PaginationInfo(
                    current_page=page,
                    per_page=per_page,
                    total=total,
                    total_pages=total_pages,
                    has_next=page < total_pages,
                    has_prev=page > 1,
                ),
            )
    except Exception as e:
        logger.warning(f"获取预警事件失败（表可能不存在）: {e}")
        return ApiResponse(
            success=True,
            data=[],
            message="预警事件查询 API（建议通过日志系统查看）",
            pagination=PaginationInfo(
                current_page=1,
                per_page=per_page,
                total=0,
                total_pages=0,
                has_next=False,
                has_prev=False,
            ),
        )


# ==================== 分析 ====================

@router.post("/analyze/{source_id}", summary="触发数据源分析", response_model=ApiResponse)
async def trigger_analysis(source_id: int):
    """触发指定数据源的 AI 分析"""
    from shared.services.intel.analysis_engine import analysis_engine

    try:
        result = await analysis_engine.analyze_source(source_id)
        return ApiResponse(success=True, data=result, message="分析完成")
    except Exception as e:
        logger.error(f"触发数据源分析失败: {e}")
        return ApiResponse(success=False, error=f"触发分析失败: {str(e)}")


@router.post("/analyze-pending", summary="分析所有待处理条目", response_model=ApiResponse)
async def analyze_all_pending():
    """分析所有已清洗但未分析的采集条目"""
    from shared.services.intel.analysis_engine import analysis_engine

    try:
        result = await analysis_engine.analyze_pending()
        return ApiResponse(success=True, data=result, message="待处理分析完成")
    except Exception as e:
        logger.error(f"分析待处理条目失败: {e}")
        return ApiResponse(success=False, error=f"分析失败: {str(e)}")


# ==================== 统计概览 ====================

@router.get("/stats", summary="情报引擎统计概览", response_model=ApiResponse)
async def get_intel_stats():
    """获取情报引擎的统计数据（用于仪表盘集成）"""
    from sqlalchemy import select, func
    from src.extensions import get_db

    try:
        from shared.models import DataSource, CollectedItem, Intelligence, Briefing, AlertRule

        with get_db() as db:
            sources_total = db.execute(select(func.count(DataSource.id))).scalar() or 0
            sources_active = db.execute(
                select(func.count(DataSource.id)).where(DataSource.is_active == True)
            ).scalar() or 0
            items_total = db.execute(select(func.count(CollectedItem.id))).scalar() or 0
            intel_total = db.execute(select(func.count(Intelligence.id))).scalar() or 0
            briefings_total = db.execute(select(func.count(Briefing.id))).scalar() or 0
            rules_total = db.execute(select(func.count(AlertRule.id))).scalar() or 0
            rules_active = db.execute(
                select(func.count(AlertRule.id)).where(AlertRule.is_active == True)
            ).scalar() or 0

        return ApiResponse(
            success=True,
            data={
                "sources": {"total": sources_total, "active": sources_active},
                "collected_items": {"total": items_total},
                "intelligence": {"total": intel_total},
                "briefings": {"total": briefings_total},
                "alert_rules": {"total": rules_total, "active": rules_active},
            },
        )
    except Exception as e:
        logger.error(f"获取情报统计失败: {e}")
        return ApiResponse(success=False, error=f"获取统计失败: {str(e)}")
