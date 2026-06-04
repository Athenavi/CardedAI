"""
V2 情报引擎 API 路由

提供数据源管理、情报查询、简报生成、预警规则管理等端点。
"""

from fastapi import APIRouter

router = APIRouter()


# ==================== 数据源管理 ====================

@router.post("/sources", summary="创建数据源")
async def create_source(
    name: str,
    source_type: str,
    url: str,
    config: str = "{}",
    schedule_cron: str = None,
):
    """创建新的数据源配置"""
    import json
    from datetime import datetime, timezone
    from shared.models import DataSource
    from src.extensions import get_db
    from src.auth import jwt_required_dependency as jwt_required

    try:
        parsed_config = json.loads(config)
    except json.JSONDecodeError:
        return {"success": False, "error": "config 不是合法的 JSON"}

    with get_db() as db:
        source = DataSource(
            name=name,
            source_type=source_type,
            url=url,
            config=json.dumps(parsed_config, ensure_ascii=False),
            schedule_cron=schedule_cron,
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        db.add(source)
        db.flush()
        source_id = source.id

    return {"success": True, "id": source_id, "message": "数据源创建成功"}


@router.get("/sources", summary="获取数据源列表")
async def get_sources(page: int = 1, per_page: int = 20, source_type: str = None, is_active: bool = None):
    """获取所有数据源配置"""
    from sqlalchemy import select
    from shared.models import DataSource
    from src.extensions import get_db

    with get_db() as db:
        query = select(DataSource)
        if source_type:
            query = query.where(DataSource.source_type == source_type)
        if is_active is not None:
            query = query.where(DataSource.is_active == is_active)
        query = query.order_by(DataSource.created_at.desc())

        # 简单分页
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)

        items = db.execute(query).scalars().all()
        return {
            "success": True,
            "items": [s.to_dict() for s in items],
            "page": page,
            "per_page": per_page,
        }


@router.get("/sources/{source_id}", summary="获取数据源详情")
async def get_source(source_id: int):
    """获取指定数据源详情"""
    from shared.models import DataSource
    from src.extensions import get_db

    with get_db() as db:
        source = db.get(DataSource, source_id)
        if not source:
            return {"success": False, "error": "数据源不存在"}

        return {"success": True, "data": source.to_dict()}


@router.put("/sources/{source_id}", summary="更新数据源")
async def update_source(source_id: int, name: str = None, url: str = None, config: str = None,
                         schedule_cron: str = None, is_active: bool = None):
    """更新数据源配置"""
    import json
    from shared.models import DataSource
    from src.extensions import get_db

    with get_db() as db:
        source = db.get(DataSource, source_id)
        if not source:
            return {"success": False, "error": "数据源不存在"}

        if name is not None:
            source.name = name
        if url is not None:
            source.url = url
        if config is not None:
            try:
                json.loads(config)  # 验证 JSON
                source.config = config
            except json.JSONDecodeError:
                return {"success": False, "error": "config 不是合法的 JSON"}
        if schedule_cron is not None:
            source.schedule_cron = schedule_cron
        if is_active is not None:
            source.is_active = is_active

    return {"success": True, "message": "数据源更新成功"}


@router.delete("/sources/{source_id}", summary="删除数据源")
async def delete_source(source_id: int):
    """删除数据源"""
    from shared.models import DataSource
    from src.extensions import get_db

    with get_db() as db:
        source = db.get(DataSource, source_id)
        if not source:
            return {"success": False, "error": "数据源不存在"}

        db.delete(source)

    return {"success": True, "message": "数据源已删除"}


@router.post("/sources/{source_id}/collect", summary="手动触发采集")
async def trigger_collect(source_id: int):
    """手动触发指定数据源的采集任务"""
    from shared.services.intel.collector_engine import collector_engine, setup_default_collectors

    # 确保采集器已注册
    if not collector_engine.registered_types:
        setup_default_collectors()

    result = await collector_engine.run_collection(source_id)
    return {"success": True, "data": result}


# ==================== 采集条目 ====================

@router.get("/items", summary="获取采集条目列表")
async def get_items(page: int = 1, per_page: int = 20, source_id: int = None, status: str = None):
    """获取采集到的原始数据条目"""
    from sqlalchemy import select
    from shared.models import CollectedItem
    from src.extensions import get_db

    with get_db() as db:
        query = select(CollectedItem)
        if source_id:
            query = query.where(CollectedItem.source_id == source_id)
        if status:
            query = query.where(CollectedItem.status == status)
        query = query.order_by(CollectedItem.collected_at.desc())

        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)

        items = db.execute(query).scalars().all()
        return {
            "success": True,
            "items": [i.to_dict() for i in items],
            "page": page,
            "per_page": per_page,
        }


# ==================== 情报 ====================

@router.get("/intelligence", summary="获取情报列表")
async def get_intelligence(page: int = 1, per_page: int = 20, category: str = None, sentiment: str = None):
    """获取 AI 分析后的情报条目"""
    from sqlalchemy import select, desc
    from shared.models import Intelligence
    from src.extensions import get_db

    with get_db() as db:
        query = select(Intelligence)
        if category:
            query = query.where(Intelligence.category == category)
        if sentiment:
            query = query.where(Intelligence.sentiment == sentiment)
        query = query.order_by(desc(Intelligence.created_at))

        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)

        items = db.execute(query).scalars().all()
        return {
            "success": True,
            "items": [i.to_dict() for i in items],
            "page": page,
            "per_page": per_page,
        }


@router.get("/intelligence/{intel_id}", summary="获取情报详情")
async def get_intelligence_detail(intel_id: int):
    """获取单条情报详情"""
    from shared.models import Intelligence
    from src.extensions import get_db

    with get_db() as db:
        intel = db.get(Intelligence, intel_id)
        if not intel:
            return {"success": False, "error": "情报不存在"}

        return {"success": True, "data": intel.to_dict()}


# ==================== 简报 ====================

@router.get("/briefings", summary="获取简报列表")
async def get_briefings(page: int = 1, per_page: int = 20, briefing_type: str = None):
    """获取情报简报"""
    from sqlalchemy import select, desc
    from shared.models import Briefing
    from src.extensions import get_db

    with get_db() as db:
        query = select(Briefing)
        if briefing_type:
            query = query.where(Briefing.briefing_type == briefing_type)
        query = query.order_by(desc(Briefing.created_at))

        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)

        items = db.execute(query).scalars().all()
        return {
            "success": True,
            "items": [b.to_dict() for b in items],
            "page": page,
            "per_page": per_page,
        }


@router.get("/briefings/{briefing_id}", summary="获取简报详情")
async def get_briefing_detail(briefing_id: int):
    """获取单条简报详情"""
    from shared.models import Briefing
    from src.extensions import get_db

    with get_db() as db:
        briefing = db.get(Briefing, briefing_id)
        if not briefing:
            return {"success": False, "error": "简报不存在"}

        return {"success": True, "data": briefing.to_dict()}


@router.post("/briefings/generate", summary="生成简报")
async def generate_briefing(briefing_type: str = "daily", topic: str = None, days: int = 7):
    """基于最新情报生成简报"""
    from shared.services.intel.briefing_generator import briefing_generator

    if briefing_type == "daily":
        result = await briefing_generator.generate_daily_briefing()
    elif briefing_type == "custom" and topic:
        result = await briefing_generator.generate_custom_briefing(topic=topic, days=days)
    else:
        return {"success": False, "error": "自定义简报需要提供 topic 参数"}

    return {"success": result.get("success", False), "data": result}


# ==================== 预警 ====================

@router.get("/alerts/rules", summary="获取预警规则列表")
async def get_alert_rules(page: int = 1, per_page: int = 20, is_active: bool = None):
    """获取预警规则"""
    from sqlalchemy import select, desc
    from shared.models import AlertRule
    from src.extensions import get_db

    with get_db() as db:
        query = select(AlertRule)
        if is_active is not None:
            query = query.where(AlertRule.is_active == is_active)
        query = query.order_by(desc(AlertRule.created_at))

        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)

        items = db.execute(query).scalars().all()
        return {
            "success": True,
            "items": [r.to_dict() for r in items],
            "page": page,
            "per_page": per_page,
        }


@router.post("/alerts/rules", summary="创建预警规则")
async def create_alert_rule(
    name: str,
    severity: str = "medium",
    keywords: str = "[]",
    conditions: str = "{}",
    actions: str = "[]",
):
    """创建新的预警规则"""
    import json
    from datetime import datetime, timezone
    from shared.models import AlertRule
    from src.extensions import get_db

    # 验证 JSON
    for field_name, field_val in [("keywords", keywords), ("conditions", conditions), ("actions", actions)]:
        try:
            json.loads(field_val)
        except json.JSONDecodeError:
            return {"success": False, "error": f"{field_name} 不是合法的 JSON"}

    with get_db() as db:
        rule = AlertRule(
            name=name,
            severity=severity,
            keywords=keywords,
            conditions=conditions,
            actions=actions,
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        db.add(rule)
        db.flush()
        rule_id = rule.id

    return {"success": True, "id": rule_id, "message": "预警规则创建成功"}


@router.get("/alerts/events", summary="获取预警事件历史")
async def get_alert_events():
    """获取预警事件列表（当前基于日志，后续可扩展为数据库存储）"""
    return {
        "success": True,
        "message": "预警事件查询 API（建议通过日志系统查看）",
        "items": [],
    }


# ==================== 分析 ====================

@router.post("/analyze/{source_id}", summary="触发数据源分析")
async def trigger_analysis(source_id: int):
    """触发指定数据源的 AI 分析"""
    from shared.services.intel.analysis_engine import analysis_engine

    result = await analysis_engine.analyze_source(source_id)
    return {"success": True, "data": result}


@router.post("/analyze-pending", summary="分析所有待处理条目")
async def analyze_all_pending():
    """分析所有已清洗但未分析的采集条目"""
    from shared.services.intel.analysis_engine import analysis_engine

    result = await analysis_engine.analyze_pending()
    return {"success": True, "data": result}
