"""
MCP Server 扩展模块

为 MCP Server 注册情报引擎、知识引擎、工作流引擎相关工具和资源

扩展的功能:
- 情报工具: search_intelligence, get_latest_briefing, create_data_source, trigger_collection
- 知识工具: query_knowledge_base, semantic_search, generate_report, list_knowledge_bases
- 工作流工具: trigger_workflow, list_workflows, get_workflow_execution
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


def register_intel_tools(mcp_server) -> None:
    """
    注册情报引擎相关 MCP 工具

    Args:
        mcp_server: MCPServer 实例
    """

    # ==================== 情报工具 ====================

    mcp_server.register_tool(
        name="search_intelligence",
        description="搜索情报数据，支持按关键词、分类、情感筛选",
        parameters={
            "query": {"type": "string", "description": "搜索关键词", "required": True},
            "category": {"type": "string", "description": "情报分类 (technology/business/security/market/other)", "required": False},
            "sentiment": {"type": "string", "description": "情感倾向 (positive/negative/neutral)", "required": False},
            "limit": {"type": "integer", "description": "返回数量上限，默认10", "required": False},
        },
        handler=_search_intelligence_handler
    )

    mcp_server.register_tool(
        name="get_latest_briefing",
        description="获取最新情报简报",
        parameters={
            "briefing_type": {"type": "string", "description": "简报类型 (daily/weekly/monthly/on_demand)", "required": False},
            "limit": {"type": "integer", "description": "返回数量，默认1", "required": False},
        },
        handler=_get_latest_briefing_handler
    )

    mcp_server.register_tool(
        name="create_data_source",
        description="创建新的数据源配置用于情报采集",
        parameters={
            "name": {"type": "string", "description": "数据源名称", "required": True},
            "source_type": {"type": "string", "description": "数据源类型 (rss/web/api)", "required": True},
            "url": {"type": "string", "description": "数据源 URL", "required": True},
            "config": {"type": "object", "description": "采集配置 (JSON)", "required": False},
        },
        handler=_create_data_source_handler
    )

    mcp_server.register_tool(
        name="trigger_collection",
        description="手动触发指定数据源的数据采集任务",
        parameters={
            "source_id": {"type": "integer", "description": "数据源 ID", "required": True},
        },
        handler=_trigger_collection_handler
    )

    mcp_server.register_tool(
        name="generate_briefing",
        description="生成新的情报简报",
        parameters={
            "briefing_type": {"type": "string", "description": "简报类型 (daily/weekly/monthly)", "required": False},
            "topic": {"type": "string", "description": "简报主题", "required": False},
            "days": {"type": "integer", "description": "覆盖天数，默认7", "required": False},
        },
        handler=_generate_briefing_handler
    )

    # ==================== 情报资源 ====================

    mcp_server.register_resource(
        uri="fastblog://intel/sources",
        name="Intelligence Sources",
        description="情报数据源列表",
        handler=_get_intel_sources_resource
    )

    mcp_server.register_resource(
        uri="fastblog://intel/alerts",
        name="Intelligence Alerts",
        description="预警规则与事件",
        handler=_get_intel_alerts_resource
    )

    # ==================== 情报提示词 ====================

    mcp_server.prompts["analyze_intelligence"] = """
请对以下情报进行深度分析：

标题: {title}
内容: {content}
来源: {source}
分类: {category}

请提供:
1. 核心要点摘要（3-5条）
2. 对业务的潜在影响评估
3. 风险等级判断（高/中/低）
4. 建议采取的行动
5. 相关趋势分析
"""


def register_knowledge_tools(mcp_server) -> None:
    """
    注册知识引擎相关 MCP 工具

    Args:
        mcp_server: MCPServer 实例
    """

    mcp_server.register_tool(
        name="query_knowledge_base",
        description="使用 RAG 技术查询知识库，基于文档语义理解回答问题",
        parameters={
            "question": {"type": "string", "description": "要查询的问题", "required": True},
            "knowledge_base_id": {"type": "integer", "description": "知识库 ID", "required": True},
            "top_k": {"type": "integer", "description": "检索文档数量，默认5", "required": False},
        },
        handler=_query_knowledge_base_handler
    )

    mcp_server.register_tool(
        name="semantic_search",
        description="在知识库中进行纯向量语义搜索，不经过 LLM 回答",
        parameters={
            "query": {"type": "string", "description": "搜索查询", "required": True},
            "knowledge_base_id": {"type": "integer", "description": "知识库 ID", "required": True},
            "top_k": {"type": "integer", "description": "返回结果数量，默认10", "required": False},
        },
        handler=_semantic_search_handler
    )

    mcp_server.register_tool(
        name="generate_report",
        description="基于知识库内容生成研究报告",
        parameters={
            "topic": {"type": "string", "description": "报告主题", "required": True},
            "knowledge_base_id": {"type": "integer", "description": "知识库 ID", "required": True},
            "report_type": {"type": "string", "description": "报告类型 (research/analysis/summary)", "required": False},
        },
        handler=_generate_report_handler
    )

    mcp_server.register_tool(
        name="list_knowledge_bases",
        description="列出所有可用的知识库",
        parameters={
            "page": {"type": "integer", "description": "页码，默认1", "required": False},
            "per_page": {"type": "integer", "description": "每页数量，默认20", "required": False},
        },
        handler=_list_knowledge_bases_handler
    )

    # ==================== 知识资源 ====================

    mcp_server.register_resource(
        uri="fastblog://knowledge/bases",
        name="Knowledge Bases",
        description="知识库列表与状态",
        handler=_get_knowledge_bases_resource
    )

    # ==================== 知识提示词 ====================

    mcp_server.prompts["knowledge_qa"] = """
你是一个知识问答助手。请根据以下知识库检索结果回答用户的问题。

知识库检索结果:
{context}

用户问题: {question}

要求:
1. 仅基于提供的检索结果回答，不要编造信息
2. 引用相关来源
3. 如果检索结果不足以回答，请明确说明
4. 回答应准确、简洁、有条理
"""


def register_workflow_tools(mcp_server) -> None:
    """
    注册工作流引擎相关 MCP 工具

    Args:
        mcp_server: MCPServer 实例
    """

    mcp_server.register_tool(
        name="trigger_workflow",
        description="手动触发指定工作流执行",
        parameters={
            "workflow_id": {"type": "integer", "description": "工作流定义 ID", "required": True},
            "input_data": {"type": "object", "description": "输入数据 (JSON)", "required": False},
        },
        handler=_trigger_workflow_handler
    )

    mcp_server.register_tool(
        name="list_workflows",
        description="列出所有工作流定义",
        parameters={
            "is_active": {"type": "boolean", "description": "筛选活跃状态", "required": False},
            "trigger_type": {"type": "string", "description": "筛选触发类型 (manual/cron/event/webhook)", "required": False},
        },
        handler=_list_workflows_handler
    )

    mcp_server.register_tool(
        name="get_workflow_execution",
        description="获取工作流执行记录详情",
        parameters={
            "execution_id": {"type": "integer", "description": "执行记录 ID", "required": True},
        },
        handler=_get_workflow_execution_handler
    )

    mcp_server.register_tool(
        name="cancel_workflow",
        description="取消正在运行的工作流执行",
        parameters={
            "execution_id": {"type": "integer", "description": "执行记录 ID", "required": True},
        },
        handler=_cancel_workflow_handler
    )

    # ==================== 工作流资源 ====================

    mcp_server.register_resource(
        uri="fastblog://workflow/definitions",
        name="Workflow Definitions",
        description="工作流定义列表",
        handler=_get_workflow_definitions_resource
    )

    mcp_server.register_resource(
        uri="fastblog://workflow/tools",
        name="Workflow Tools",
        description="已注册的 Agent 工具列表",
        handler=_get_workflow_tools_resource
    )

    # ==================== 工作流提示词 ====================

    mcp_server.prompts["workflow_design"] = """
请帮助设计一个自动化工作流：

目标: {goal}
输入数据: {input_data}
期望输出: {expected_output}

请提供:
1. 推荐的工作流节点类型和顺序
2. 每个节点的配置建议
3. 条件分支逻辑
4. 错误处理策略
5. 预期执行时间和资源消耗
"""


# ============================================================================
# 情报工具处理器
# ============================================================================

async def _search_intelligence_handler(arguments: Dict) -> Dict:
    """搜索情报数据"""
    try:
        from src.extensions import get_db
        from shared.models.intel.intelligence import Intelligence

        query = arguments.get("query", "")
        category = arguments.get("category")
        sentiment = arguments.get("sentiment")
        limit = arguments.get("limit", 10)

        with get_db() as db:
            q = db.query(Intelligence)
            if category:
                q = q.filter(Intelligence.category == category)
            if sentiment:
                q = q.filter(Intelligence.sentiment == sentiment)
            if query:
                q = q.filter(
                    Intelligence.title.ilike(f"%{query}%") |
                    Intelligence.summary.ilike(f"%{query}%")
                )
            results = q.order_by(Intelligence.created_at.desc()).limit(limit).all()
            return {
                "success": True,
                "count": len(results),
                "items": [r.to_dict() for r in results],
            }
    except Exception as e:
        logger.error(f"MCP search_intelligence failed: {e}")
        return {"success": False, "error": str(e)}


async def _get_latest_briefing_handler(arguments: Dict) -> Dict:
    """获取最新简报"""
    try:
        from src.extensions import get_db
        from shared.models.intel.briefing import Briefing

        briefing_type = arguments.get("briefing_type")
        limit = arguments.get("limit", 1)

        with get_db() as db:
            q = db.query(Briefing)
            if briefing_type:
                q = q.filter(Briefing.briefing_type == briefing_type)
            results = q.order_by(Briefing.created_at.desc()).limit(limit).all()
            return {
                "success": True,
                "count": len(results),
                "items": [r.to_dict() for r in results],
            }
    except Exception as e:
        logger.error(f"MCP get_latest_briefing failed: {e}")
        return {"success": False, "error": str(e)}


async def _create_data_source_handler(arguments: Dict) -> Dict:
    """创建数据源"""
    try:
        from src.extensions import get_db
        from shared.models.intel.data_source import DataSource
        import json as _json

        name = arguments.get("name")
        source_type = arguments.get("source_type")
        url = arguments.get("url")
        config = arguments.get("config", {})

        if not all([name, source_type, url]):
            return {"success": False, "error": "name, source_type, url are required"}

        with get_db() as db:
            ds = DataSource(
                name=name,
                source_type=source_type,
                url=url,
                config=_json.dumps(config, ensure_ascii=False) if isinstance(config, dict) else str(config),
                is_active=True,
            )
            db.add(ds)
            db.commit()
            db.refresh(ds)
            return {
                "success": True,
                "message": f"Data source '{name}' created",
                "source_id": ds.id,
            }
    except Exception as e:
        logger.error(f"MCP create_data_source failed: {e}")
        return {"success": False, "error": str(e)}


async def _trigger_collection_handler(arguments: Dict) -> Dict:
    """触发数据采集"""
    try:
        from shared.services.intel.collector_engine import collector_engine

        source_id = arguments.get("source_id")
        if not source_id:
            return {"success": False, "error": "source_id is required"}

        result = await collector_engine.run_collection(source_id)
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"MCP trigger_collection failed: {e}")
        return {"success": False, "error": str(e)}


async def _generate_briefing_handler(arguments: Dict) -> Dict:
    """生成简报"""
    try:
        from shared.services.intel.briefing_generator import briefing_generator

        briefing_type = arguments.get("briefing_type", "daily")
        topic = arguments.get("topic")
        days = arguments.get("days", 7)

        result = await briefing_generator.generate(
            briefing_type=briefing_type,
            topic=topic,
            days=days,
        )
        return {"success": True, "briefing": result}
    except Exception as e:
        logger.error(f"MCP generate_briefing failed: {e}")
        return {"success": False, "error": str(e)}


# ============================================================================
# 知识工具处理器
# ============================================================================

async def _query_knowledge_base_handler(arguments: Dict) -> Dict:
    """RAG 知识问答"""
    try:
        from shared.services.knowledge.rag_chain import rag_chain

        question = arguments.get("question")
        knowledge_base_id = arguments.get("knowledge_base_id")
        top_k = arguments.get("top_k", 5)

        if not question or not knowledge_base_id:
            return {"success": False, "error": "question and knowledge_base_id are required"}

        result = await rag_chain.query(
            question=question,
            knowledge_base_id=knowledge_base_id,
            top_k=top_k,
        )
        return {"success": True, "answer": result.get("answer", ""), "sources": result.get("sources", [])}
    except Exception as e:
        logger.error(f"MCP query_knowledge_base failed: {e}")
        return {"success": False, "error": str(e)}


async def _semantic_search_handler(arguments: Dict) -> Dict:
    """语义搜索"""
    try:
        from shared.services.knowledge.rag_chain import rag_chain

        query = arguments.get("query")
        knowledge_base_id = arguments.get("knowledge_base_id")
        top_k = arguments.get("top_k", 10)

        if not query or not knowledge_base_id:
            return {"success": False, "error": "query and knowledge_base_id are required"}

        results = await rag_chain.search(
            query=query,
            knowledge_base_id=knowledge_base_id,
            top_k=top_k,
        )
        return {"success": True, "count": len(results), "results": results}
    except Exception as e:
        logger.error(f"MCP semantic_search failed: {e}")
        return {"success": False, "error": str(e)}


async def _generate_report_handler(arguments: Dict) -> Dict:
    """生成研报"""
    try:
        from shared.services.knowledge.report_generator import report_generator

        topic = arguments.get("topic")
        knowledge_base_id = arguments.get("knowledge_base_id")
        report_type = arguments.get("report_type", "research")

        if not topic or not knowledge_base_id:
            return {"success": False, "error": "topic and knowledge_base_id are required"}

        result = await report_generator.generate(
            topic=topic,
            knowledge_base_id=knowledge_base_id,
            report_type=report_type,
        )
        return {"success": True, "report": result}
    except Exception as e:
        logger.error(f"MCP generate_report failed: {e}")
        return {"success": False, "error": str(e)}


async def _list_knowledge_bases_handler(arguments: Dict) -> Dict:
    """列出知识库"""
    try:
        from src.extensions import get_db
        from shared.models.knowledge.knowledge_base import KnowledgeBase

        page = arguments.get("page", 1)
        per_page = arguments.get("per_page", 20)

        with get_db() as db:
            query = db.query(KnowledgeBase)
            total = query.count()
            items = query.order_by(KnowledgeBase.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
            return {
                "success": True,
                "total": total,
                "page": page,
                "per_page": per_page,
                "items": [b.to_dict() for b in items],
            }
    except Exception as e:
        logger.error(f"MCP list_knowledge_bases failed: {e}")
        return {"success": False, "error": str(e)}


# ============================================================================
# 工作流工具处理器
# ============================================================================

async def _trigger_workflow_handler(arguments: Dict) -> Dict:
    """触发工作流"""
    try:
        import json as _json
        from src.extensions import get_db
        from shared.models.workflow.workflow_definition import WorkflowDefinition
        from shared.services.workflow.dag_engine import DAGEngine

        workflow_id = arguments.get("workflow_id")
        input_data = arguments.get("input_data", {})

        if not workflow_id:
            return {"success": False, "error": "workflow_id is required"}

        with get_db() as db:
            wf_def = db.get(WorkflowDefinition, workflow_id)
            if not wf_def:
                return {"success": False, "error": f"Workflow {workflow_id} not found"}

            graph_data = _json.loads(wf_def.graph_data) if isinstance(wf_def.graph_data, str) else wf_def.graph_data
            nodes = graph_data.get("nodes", [])
            edges = graph_data.get("edges", [])

        engine = DAGEngine()
        # Register node executors
        from shared.services.workflow.node_executors import get_all_executors
        for node_type, executor in get_all_executors().items():
            engine.register_executor(node_type, executor)

        result = await engine.execute(
            workflow_id=workflow_id,
            nodes=nodes,
            edges=edges,
            input_data=input_data,
        )
        return {
            "success": True,
            "execution_id": result.execution_id,
            "status": result.status,
            "outputs": result.outputs,
        }
    except Exception as e:
        logger.error(f"MCP trigger_workflow failed: {e}")
        return {"success": False, "error": str(e)}


async def _list_workflows_handler(arguments: Dict) -> Dict:
    """列出工作流"""
    try:
        from src.extensions import get_db
        from shared.models.workflow.workflow_definition import WorkflowDefinition

        is_active = arguments.get("is_active")
        trigger_type = arguments.get("trigger_type")

        with get_db() as db:
            q = db.query(WorkflowDefinition)
            if is_active is not None:
                q = q.filter(WorkflowDefinition.is_active == is_active)
            if trigger_type:
                q = q.filter(WorkflowDefinition.trigger_type == trigger_type)
            results = q.order_by(WorkflowDefinition.created_at.desc()).all()
            return {
                "success": True,
                "count": len(results),
                "items": [w.to_dict() for w in results],
            }
    except Exception as e:
        logger.error(f"MCP list_workflows failed: {e}")
        return {"success": False, "error": str(e)}


async def _get_workflow_execution_handler(arguments: Dict) -> Dict:
    """获取工作流执行记录"""
    try:
        from src.extensions import get_db
        from shared.models.workflow.workflow_execution import WorkflowExecution
        from shared.models.workflow.node_execution import NodeExecution

        execution_id = arguments.get("execution_id")
        if not execution_id:
            return {"success": False, "error": "execution_id is required"}

        with get_db() as db:
            execution = db.get(WorkflowExecution, execution_id)
            if not execution:
                return {"success": False, "error": f"Execution {execution_id} not found"}

            node_execs = db.query(NodeExecution).filter(
                NodeExecution.workflow_execution_id == execution_id
            ).all()

            return {
                "success": True,
                "execution": execution.to_dict(),
                "node_executions": [ne.to_dict() for ne in node_execs],
            }
    except Exception as e:
        logger.error(f"MCP get_workflow_execution failed: {e}")
        return {"success": False, "error": str(e)}


async def _cancel_workflow_handler(arguments: Dict) -> Dict:
    """取消工作流"""
    try:
        from src.extensions import get_db
        from shared.models.workflow.workflow_execution import WorkflowExecution
        from shared.services.workflow.dag_engine import DAGEngine

        execution_id = arguments.get("execution_id")
        if not execution_id:
            return {"success": False, "error": "execution_id is required"}

        with get_db() as db:
            execution = db.get(WorkflowExecution, execution_id)
            if not execution:
                return {"success": False, "error": f"Execution {execution_id} not found"}

            workflow_id = execution.workflow_definition_id

        engine = DAGEngine()
        engine.cancel_execution(workflow_id)

        return {"success": True, "message": f"Execution {execution_id} cancellation requested"}
    except Exception as e:
        logger.error(f"MCP cancel_workflow failed: {e}")
        return {"success": False, "error": str(e)}


# ============================================================================
# 资源处理器
# ============================================================================

async def _get_intel_sources_resource(params: Dict) -> List[Dict]:
    """获取情报数据源列表"""
    try:
        from src.extensions import get_db
        from shared.models.intel.data_source import DataSource

        with get_db() as db:
            sources = db.query(DataSource).order_by(DataSource.created_at.desc()).all()
            return [s.to_dict() for s in sources]
    except Exception as e:
        logger.error(f"MCP intel sources resource failed: {e}")
        return []


async def _get_intel_alerts_resource(params: Dict) -> Dict:
    """获取预警规则和事件"""
    try:
        from src.extensions import get_db
        from shared.models.intel.alert_rule import AlertRule

        with get_db() as db:
            rules = db.query(AlertRule).order_by(AlertRule.created_at.desc()).all()
            return {
                "rules": [r.to_dict() for r in rules],
                "total_rules": len(rules),
            }
    except Exception as e:
        logger.error(f"MCP intel alerts resource failed: {e}")
        return {"rules": [], "total_rules": 0}


async def _get_knowledge_bases_resource(params: Dict) -> List[Dict]:
    """获取知识库列表"""
    try:
        from src.extensions import get_db
        from shared.models.knowledge.knowledge_base import KnowledgeBase

        with get_db() as db:
            bases = db.query(KnowledgeBase).order_by(KnowledgeBase.created_at.desc()).all()
            return [b.to_dict() for b in bases]
    except Exception as e:
        logger.error(f"MCP knowledge bases resource failed: {e}")
        return []


async def _get_workflow_definitions_resource(params: Dict) -> List[Dict]:
    """获取工作流定义列表"""
    try:
        from src.extensions import get_db
        from shared.models.workflow.workflow_definition import WorkflowDefinition

        with get_db() as db:
            defs = db.query(WorkflowDefinition).order_by(WorkflowDefinition.created_at.desc()).all()
            return [d.to_dict() for d in defs]
    except Exception as e:
        logger.error(f"MCP workflow definitions resource failed: {e}")
        return []


async def _get_workflow_tools_resource(params: Dict) -> List[Dict]:
    """获取已注册的 Agent 工具列表"""
    try:
        from src.extensions import get_db
        from shared.models.workflow.agent_tool import AgentTool

        with get_db() as db:
            tools = db.query(AgentTool).order_by(AgentTool.created_at.desc()).all()
            return [t.to_dict() for t in tools]
    except Exception as e:
        logger.error(f"MCP workflow tools resource failed: {e}")
        return []


# ============================================================================
# 便捷注册入口
# ============================================================================

def register_all_extensions(mcp_server) -> None:
    """
    一键注册所有 MCP 扩展

    Args:
        mcp_server: MCPServer 实例
    """
    register_intel_tools(mcp_server)
    register_knowledge_tools(mcp_server)
    register_workflow_tools(mcp_server)
    logger.info(
        f"MCP extensions registered: "
        f"tools={len(mcp_server.tools)}, "
        f"resources={len(mcp_server.resources)}, "
        f"prompts={len(mcp_server.prompts)}"
    )
