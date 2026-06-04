"""
V2 自动化引擎 API 路由

提供工作流定义 CRUD、执行管理、工具注册、触发器管理等端点。

端点列表:
  定义管理:
    POST   /definitions                    创建工作流
    GET    /definitions                    工作流列表
    GET    /definitions/{id}               工作流详情
    PUT    /definitions/{id}               更新工作流
    DELETE /definitions/{id}               删除工作流
    POST   /definitions/{id}/activate      激活工作流
    POST   /definitions/{id}/deactivate    停用工作流

  执行管理:
    POST   /definitions/{id}/execute       手动执行
    GET    /executions                     执行记录列表
    GET    /executions/{id}                执行详情
    POST   /executions/{id}/cancel         取消执行

  工具管理:
    GET    /tools                          可用工具列表
    POST   /tools                          注册新工具
    POST   /tools/{name}/test              工具测试

  触发器管理:
    GET    /triggers                       触发器列表
    POST   /triggers/cron                  创建 cron 触发器
    POST   /triggers/event                 创建 event 触发器
    DELETE /triggers/{trigger_id}          删除触发器

  Webhook:
    POST   /webhooks/{token}               Webhook 触发执行
"""

import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter

from src.api.v1.core.responses import ApiResponse
from src.extensions import get_db

router = APIRouter()


# ==================== 工作流定义管理 ====================


@router.post("/definitions", summary="创建工作流定义")
async def create_definition(
    name: str,
    graph: str,
    description: str = None,
    trigger_config: str = "{}",
):
    """创建新的工作流定义

    Args:
        name: 工作流名称
        graph: DAG 图结构 JSON 字符串（含 nodes 和 edges）
        description: 工作流描述
        trigger_config: 触发配置 JSON
    """
    from shared.models.workflow.workflow_definition import WorkflowDefinition
    from shared.services.workflow.dag_engine import DAGEngine

    # 校验图结构
    try:
        graph_data = json.loads(graph) if isinstance(graph, str) else graph
        errors = DAGEngine.validate_graph(
            graph_data.get("nodes", []),
            graph_data.get("edges", []),
        )
        if errors:
            return ApiResponse.error(message=f"图结构校验失败: {'; '.join(errors)}")
    except (json.JSONDecodeError, ValueError) as exc:
        return ApiResponse.error(message=f"graph 不是合法的 JSON: {exc}")

    try:
        trigger_json = json.loads(trigger_config) if isinstance(trigger_config, str) else trigger_config
    except json.JSONDecodeError:
        return ApiResponse.error(message="trigger_config 不是合法的 JSON")

    with get_db() as db:
        wf = WorkflowDefinition(
            name=name,
            description=description,
            graph=json.dumps(graph_data, ensure_ascii=False),
            trigger_config=json.dumps(trigger_json, ensure_ascii=False),
            is_active=False,
            version=1,
            created_at=datetime.now(timezone.utc),
        )
        db.add(wf)
        db.flush()
        wf_id = wf.id

    return ApiResponse.success(data={"id": wf_id}, message="工作流创建成功")


@router.get("/definitions", summary="获取工作流定义列表")
async def get_definitions(
    page: int = 1,
    per_page: int = 20,
    is_active: Optional[bool] = None,
):
    """获取所有工作流定义"""
    from shared.models.workflow.workflow_definition import WorkflowDefinition

    with get_db() as db:
        query = db.query(WorkflowDefinition)
        if is_active is not None:
            query = query.filter(WorkflowDefinition.is_active == is_active)
        total = query.count()
        items = query.order_by(WorkflowDefinition.id.desc()) \
            .offset((page - 1) * per_page) \
            .limit(per_page) \
            .all()

    return ApiResponse.success(data={
        "items": [wf.to_dict() for wf in items],
        "total": total,
        "page": page,
        "per_page": per_page,
    })


@router.get("/definitions/{def_id}", summary="获取工作流定义详情")
async def get_definition(def_id: int):
    """获取指定工作流定义详情"""
    from shared.models.workflow.workflow_definition import WorkflowDefinition

    with get_db() as db:
        wf = db.get(WorkflowDefinition, def_id)
        if not wf:
            return ApiResponse.error(message="工作流不存在", code=404)

    data = wf.to_dict()
    # 解析 graph JSON
    if data.get("graph"):
        try:
            data["graph"] = json.loads(data["graph"])
        except (json.JSONDecodeError, TypeError):
            pass
    if data.get("trigger_config"):
        try:
            data["trigger_config"] = json.loads(data["trigger_config"])
        except (json.JSONDecodeError, TypeError):
            pass

    return ApiResponse.success(data=data)


@router.put("/definitions/{def_id}", summary="更新工作流定义")
async def update_definition(
    def_id: int,
    name: str = None,
    graph: str = None,
    description: str = None,
    trigger_config: str = None,
):
    """更新工作流定义"""
    from shared.models.workflow.workflow_definition import WorkflowDefinition
    from shared.services.workflow.dag_engine import DAGEngine

    with get_db() as db:
        wf = db.get(WorkflowDefinition, def_id)
        if not wf:
            return ApiResponse.error(message="工作流不存在", code=404)

        if name is not None:
            wf.name = name
        if description is not None:
            wf.description = description

        if graph is not None:
            try:
                graph_data = json.loads(graph) if isinstance(graph, str) else graph
                errors = DAGEngine.validate_graph(
                    graph_data.get("nodes", []),
                    graph_data.get("edges", []),
                )
                if errors:
                    return ApiResponse.error(message=f"图结构校验失败: {'; '.join(errors)}")
                wf.graph = json.dumps(graph_data, ensure_ascii=False)
                wf.version = (wf.version or 1) + 1
            except (json.JSONDecodeError, ValueError) as exc:
                return ApiResponse.error(message=f"graph 不是合法的 JSON: {exc}")

        if trigger_config is not None:
            try:
                tc = json.loads(trigger_config) if isinstance(trigger_config, str) else trigger_config
                wf.trigger_config = json.dumps(tc, ensure_ascii=False)
            except json.JSONDecodeError:
                return ApiResponse.error(message="trigger_config 不是合法的 JSON")

        wf.updated_at = datetime.now(timezone.utc)
        db.flush()

    return ApiResponse.success(message="工作流更新成功")


@router.delete("/definitions/{def_id}", summary="删除工作流定义")
async def delete_definition(def_id: int):
    """删除工作流定义"""
    from shared.models.workflow.workflow_definition import WorkflowDefinition

    with get_db() as db:
        wf = db.get(WorkflowDefinition, def_id)
        if not wf:
            return ApiResponse.error(message="工作流不存在", code=404)
        db.delete(wf)
        db.flush()

    return ApiResponse.success(message="工作流已删除")


@router.post("/definitions/{def_id}/activate", summary="激活工作流")
async def activate_definition(def_id: int):
    """激活工作流（启用触发器）"""
    from shared.models.workflow.workflow_definition import WorkflowDefinition

    with get_db() as db:
        wf = db.get(WorkflowDefinition, def_id)
        if not wf:
            return ApiResponse.error(message="工作流不存在", code=404)
        wf.is_active = True
        wf.updated_at = datetime.now(timezone.utc)
        db.flush()

    # 注册触发器
    if wf.trigger_config:
        try:
            tc = json.loads(wf.trigger_config) if isinstance(wf.trigger_config, str) else wf.trigger_config
            await _setup_triggers(def_id, wf.graph, tc)
        except Exception as exc:
            from src.unified_logger import default_logger as logger
            logger.warning(f"[WorkflowAPI] 注册触发器失败: {exc}")

    return ApiResponse.success(message="工作流已激活")


@router.post("/definitions/{def_id}/deactivate", summary="停用工作流")
async def deactivate_definition(def_id: int):
    """停用工作流（禁用触发器）"""
    from shared.models.workflow.workflow_definition import WorkflowDefinition
    from shared.services.workflow.trigger_service import trigger_service

    with get_db() as db:
        wf = db.get(WorkflowDefinition, def_id)
        if not wf:
            return ApiResponse.error(message="工作流不存在", code=404)
        wf.is_active = False
        wf.updated_at = datetime.now(timezone.utc)
        db.flush()

    # 取消 cron 触发器
    await trigger_service.unregister_cron_trigger(def_id)

    return ApiResponse.success(message="工作流已停用")


# ==================== 执行管理 ====================


@router.post("/definitions/{def_id}/execute", summary="手动触发工作流")
async def execute_workflow(def_id: int, input_data: str = "{}"):
    """手动触发指定工作流执行"""
    from shared.services.workflow.trigger_service import trigger_service

    try:
        data = json.loads(input_data) if isinstance(input_data, str) else input_data
    except json.JSONDecodeError:
        return ApiResponse.error(message="input_data 不是合法的 JSON")

    try:
        result = await trigger_service.trigger_workflow(
            workflow_id=def_id,
            input_data=data,
        )
        return ApiResponse.success(data=result, message="工作流执行完成")
    except ValueError as exc:
        return ApiResponse.error(message=str(exc))
    except Exception as exc:
        return ApiResponse.error(message=f"执行失败: {exc}")


@router.get("/executions", summary="获取执行记录列表")
async def get_executions(
    page: int = 1,
    per_page: int = 20,
    workflow_id: Optional[int] = None,
    status: Optional[str] = None,
):
    """获取工作流执行记录"""
    from shared.models.workflow.workflow_execution import WorkflowExecution

    with get_db() as db:
        query = db.query(WorkflowExecution)
        if workflow_id is not None:
            query = query.filter(WorkflowExecution.workflow_id == workflow_id)
        if status:
            query = query.filter(WorkflowExecution.status == status)
        total = query.count()
        items = query.order_by(WorkflowExecution.id.desc()) \
            .offset((page - 1) * per_page) \
            .limit(per_page) \
            .all()

    return ApiResponse.success(data={
        "items": [ex.to_dict() for ex in items],
        "total": total,
        "page": page,
        "per_page": per_page,
    })


@router.get("/executions/{exec_id}", summary="获取执行记录详情")
async def get_execution(exec_id: int):
    """获取指定执行记录详情，包含所有节点执行状态"""
    from shared.models.workflow.workflow_execution import WorkflowExecution

    with get_db() as db:
        ex = db.get(WorkflowExecution, exec_id)
        if not ex:
            return ApiResponse.error(message="执行记录不存在", code=404)

        data = ex.to_dict()
        # 附加节点执行记录
        node_execs = []
        for ne in (ex.node_executions or []):
            node_execs.append(ne.to_dict())
        data["node_executions"] = node_execs

    return ApiResponse.success(data=data)


@router.post("/executions/{exec_id}/cancel", summary="取消执行")
async def cancel_execution(exec_id: int):
    """取消正在运行的执行"""
    from shared.models.workflow.workflow_execution import WorkflowExecution
    from shared.services.workflow.dag_engine import dag_engine

    with get_db() as db:
        ex = db.get(WorkflowExecution, exec_id)
        if not ex:
            return ApiResponse.error(message="执行记录不存在", code=404)
        if ex.status not in ("pending", "running"):
            return ApiResponse.error(message=f"执行状态为 {ex.status}，无法取消")

    dag_engine.cancel_execution(ex.workflow_id)

    # 更新状态
    with get_db() as db:
        ex = db.get(WorkflowExecution, exec_id)
        if ex:
            ex.status = "cancelled"
            ex.completed_at = datetime.now(timezone.utc)
            ex.error_message = "执行被用户取消"
            db.flush()

    return ApiResponse.success(message="执行已取消")


# ==================== 工具管理 ====================


@router.get("/tools", summary="获取工具列表")
async def get_tools(tool_type: Optional[str] = None):
    """获取已注册的 Agent 工具列表"""
    from shared.services.workflow.tool_registry import tool_registry

    tools = tool_registry.list_tools(tool_type=tool_type)
    return ApiResponse.success(data={
        "items": tools,
        "total": len(tools),
    })


@router.post("/tools", summary="注册新工具")
async def register_tool(
    name: str,
    description: str,
    parameters: str,
    tool_type: str = "function",
):
    """注册新的 Agent 工具（仅记录元数据到数据库）"""
    from shared.models.workflow.agent_tool import AgentTool

    try:
        params = json.loads(parameters) if isinstance(parameters, str) else parameters
    except json.JSONDecodeError:
        return ApiResponse.error(message="parameters 不是合法的 JSON Schema")

    with get_db() as db:
        existing = db.query(AgentTool).filter_by(name=name).first()
        if existing:
            return ApiResponse.error(message=f"工具 '{name}' 已存在")

        tool = AgentTool(
            name=name,
            description=description,
            tool_type=tool_type,
            schema=json.dumps(params, ensure_ascii=False),
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        db.add(tool)
        db.flush()
        tool_id = tool.id

    return ApiResponse.success(data={"id": tool_id}, message="工具注册成功")


@router.post("/tools/{name}/test", summary="工具测试")
async def test_tool(name: str, params: str = "{}"):
    """测试调用指定工具"""
    from shared.services.workflow.tool_registry import tool_registry

    try:
        p = json.loads(params) if isinstance(params, str) else params
    except json.JSONDecodeError:
        return ApiResponse.error(message="params 不是合法的 JSON")

    result = await tool_registry.call_tool_safe(name, p)
    return ApiResponse.success(data=result)


# ==================== 触发器管理 ====================


@router.get("/triggers", summary="获取触发器列表")
async def get_triggers():
    """获取工作流触发器配置"""
    from shared.services.workflow.trigger_service import trigger_service
    from shared.models.workflow.trigger import Trigger

    # 内存中的触发器
    runtime_triggers = trigger_service.get_all_triggers()

    # 数据库中的触发器
    db_triggers = []
    try:
        with get_db() as db:
            items = db.query(Trigger).all()
            db_triggers = [t.to_dict() for t in items]
    except Exception:
        pass

    return ApiResponse.success(data={
        "runtime_triggers": runtime_triggers,
        "db_triggers": db_triggers,
    })


@router.post("/triggers/cron", summary="创建 cron 触发器")
async def create_cron_trigger(
    workflow_id: int,
    cron_expr: str,
):
    """注册定时触发器"""
    from shared.services.workflow.trigger_service import trigger_service

    try:
        result = await trigger_service.register_cron_trigger(
            workflow_id=workflow_id,
            cron_expr=cron_expr,
        )

        # 持久化到数据库
        try:
            with get_db() as db:
                from shared.models.workflow.trigger import Trigger
                trigger = Trigger(
                    workflow_id=workflow_id,
                    trigger_type="cron",
                    config=json.dumps({"cron_expr": cron_expr}, ensure_ascii=False),
                    is_active=True,
                    created_at=datetime.now(timezone.utc),
                )
                db.add(trigger)
                db.flush()
        except Exception:
            pass

        return ApiResponse.success(data=result, message="Cron 触发器创建成功")
    except ValueError as exc:
        return ApiResponse.error(message=str(exc))


@router.post("/triggers/event", summary="创建 event 触发器")
async def create_event_trigger(
    workflow_id: int,
    event_name: str,
):
    """注册事件触发器"""
    from shared.services.workflow.trigger_service import trigger_service

    result = await trigger_service.register_event_trigger(
        workflow_id=workflow_id,
        event_name=event_name,
    )

    # 持久化到数据库
    try:
        with get_db() as db:
            from shared.models.workflow.trigger import Trigger
            trigger = Trigger(
                workflow_id=workflow_id,
                trigger_type="event",
                config=json.dumps({"event_name": event_name}, ensure_ascii=False),
                is_active=True,
                created_at=datetime.now(timezone.utc),
            )
            db.add(trigger)
            db.flush()
    except Exception:
        pass

    return ApiResponse.success(data=result, message="事件触发器创建成功")


@router.post("/triggers/webhook", summary="创建 webhook 触发器")
async def create_webhook_trigger(
    workflow_id: int,
):
    """注册 Webhook 触发器"""
    from shared.services.workflow.trigger_service import trigger_service

    result = await trigger_service.register_webhook_trigger(
        workflow_id=workflow_id,
    )

    # 持久化到数据库
    try:
        with get_db() as db:
            from shared.models.workflow.trigger import Trigger
            trigger = Trigger(
                workflow_id=workflow_id,
                trigger_type="webhook",
                config=json.dumps({"token": result.get("token")}, ensure_ascii=False),
                is_active=True,
                created_at=datetime.now(timezone.utc),
            )
            db.add(trigger)
            db.flush()
    except Exception:
        pass

    return ApiResponse.success(data=result, message="Webhook 触发器创建成功")


@router.delete("/triggers/{trigger_id}", summary="删除触发器")
async def delete_trigger(trigger_id: int):
    """删除触发器"""
    from shared.models.workflow.trigger import Trigger

    with get_db() as db:
        trigger = db.get(Trigger, trigger_id)
        if not trigger:
            return ApiResponse.error(message="触发器不存在", code=404)
        db.delete(trigger)
        db.flush()

    return ApiResponse.success(message="触发器已删除")


# ==================== Webhook 触发 ====================


@router.post("/webhooks/{token}", summary="Webhook 触发执行")
async def webhook_trigger(token: str, payload: dict = None):
    """通过 Webhook token 触发工作流执行"""
    from shared.services.workflow.trigger_service import trigger_service

    try:
        result = await trigger_service.trigger_by_webhook(token, payload or {})
        return ApiResponse.success(data=result, message="Webhook 触发成功")
    except ValueError as exc:
        return ApiResponse.error(message=str(exc), code=404)
    except Exception as exc:
        return ApiResponse.error(message=f"Webhook 触发失败: {exc}")


# ==================== 内部辅助 ====================


async def _setup_triggers(workflow_id: int, graph_data, trigger_config: dict):
    """根据触发配置设置触发器"""
    from shared.services.workflow.trigger_service import trigger_service

    trigger_type = trigger_config.get("type", "manual")

    if trigger_type == "cron":
        cron_expr = trigger_config.get("cron")
        if cron_expr:
            await trigger_service.register_cron_trigger(
                workflow_id=workflow_id,
                cron_expr=cron_expr,
                graph_data=graph_data,
            )
    elif trigger_type == "event":
        event_name = trigger_config.get("event")
        if event_name:
            await trigger_service.register_event_trigger(
                workflow_id=workflow_id,
                event_name=event_name,
                graph_data=graph_data,
            )
    elif trigger_type == "webhook":
        await trigger_service.register_webhook_trigger(
            workflow_id=workflow_id,
            graph_data=graph_data,
        )
