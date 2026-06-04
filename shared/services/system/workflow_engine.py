"""
工作流引擎服务
提供可视化的工作流设计、执行和监控功能
"""
import json

from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

from src.unified_logger import default_logger as logger


class WorkflowStatus(Enum):
    """工作流状态"""
    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NodeStatus(Enum):
    """节点状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class NodeType(Enum):
    """节点类型"""
    START = "start"
    END = "end"
    ACTION = "action"
    CONDITION = "condition"
    APPROVAL = "approval"
    DELAY = "delay"


class WorkflowNode:
    """工作流节点"""

    def __init__(self, node_id: str, node_type: NodeType, config: Dict[str, Any]):
        self.node_id = node_id
        self.node_type = node_type
        self.config = config
        self.status = NodeStatus.PENDING
        self.result = None
        self.started_at = None
        self.completed_at = None
        self.error = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'node_id': self.node_id,
            'node_type': self.node_type.value,
            'config': self.config,
            'status': self.status.value,
            'result': self.result,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error': self.error,
        }


class WorkflowInstance:
    """工作流实例"""

    def __init__(self, workflow_id: str, instance_id: str, context: Dict[str, Any] = None):
        self.workflow_id = workflow_id
        self.instance_id = instance_id
        self.context = context or {}
        self.status = WorkflowStatus.DRAFT
        self.nodes: Dict[str, WorkflowNode] = {}
        self.current_node_id = None
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.completed_at = None
        self.error = None

    def add_node(self, node: WorkflowNode):
        """添加节点"""
        self.nodes[node.node_id] = node

    def get_node(self, node_id: str) -> Optional[WorkflowNode]:
        """获取节点"""
        return self.nodes.get(node_id)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'workflow_id': self.workflow_id,
            'instance_id': self.instance_id,
            'context': self.context,
            'status': self.status.value,
            'current_node_id': self.current_node_id,
            'nodes': {nid: node.to_dict() for nid, node in self.nodes.items()},
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error': self.error,
        }


class WorkflowEngine:
    """
    工作流引擎
    
    功能:
    1. 工作流定义管理
    2. 工作流实例执行
    3. 节点状态跟踪
    4. 条件判断
    5. 审批流程
    6. 执行历史
    """

    def __init__(self):
        # 工作流定义 {workflow_id: workflow_definition}
        self.workflows: Dict[str, Dict[str, Any]] = {}

        # 工作流实例 {instance_id: WorkflowInstance}
        self.instances: Dict[str, WorkflowInstance] = {}

        # 执行历史 [{timestamp, instance_id, event, data}]
        self.execution_history: List[Dict[str, Any]] = []

    def register_workflow(self, workflow_id: str, definition: Dict[str, Any]):
        """
        注册工作流定义
        
        Args:
            workflow_id: 工作流ID
            definition: 工作流定义 {
                'name': '工作流名称',
                'description': '描述',
                'nodes': [
                    {
                        'id': 'node_1',
                        'type': 'start',
                        'config': {},
                        'next': ['node_2']
                    }
                ],
                'edges': [
                    {'from': 'node_1', 'to': 'node_2'}
                ]
            }
        """
        self.workflows[workflow_id] = definition
        logger.info(f"Registered workflow: {workflow_id}")

    def create_instance(self, workflow_id: str, context: Dict[str, Any] = None) -> str:
        """
        创建工作流实例
        
        Args:
            workflow_id: 工作流ID
            context: 上下文数据
            
        Returns:
            实例ID
        """
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")

        import uuid
        instance_id = str(uuid.uuid4())

        workflow_def = self.workflows[workflow_id]
        instance = WorkflowInstance(workflow_id, instance_id, context)

        # 创建节点
        for node_def in workflow_def.get('nodes', []):
            node = WorkflowNode(
                node_id=node_def['id'],
                node_type=NodeType(node_def['type']),
                config=node_def.get('config', {})
            )
            instance.add_node(node)

        # 设置起始节点
        start_nodes = [n for n in workflow_def['nodes'] if n['type'] == 'start']
        if start_nodes:
            instance.current_node_id = start_nodes[0]['id']
            instance.status = WorkflowStatus.RUNNING

        self.instances[instance_id] = instance

        self._record_history(instance_id, 'created', {
            'workflow_id': workflow_id,
            'context': context
        })

        logger.info(f"Created workflow instance: {instance_id}")
        return instance_id

    async def execute_instance(self, instance_id: str) -> bool:
        """
        执行工作流实例
        
        Args:
            instance_id: 实例ID
            
        Returns:
            是否执行成功
        """
        if instance_id not in self.instances:
            raise ValueError(f"Instance {instance_id} not found")

        instance = self.instances[instance_id]

        if instance.status != WorkflowStatus.RUNNING:
            logger.warning(f"Instance {instance_id} is not running")
            return False

        try:
            while instance.current_node_id and instance.status == WorkflowStatus.RUNNING:
                current_node = instance.get_node(instance.current_node_id)

                if not current_node:
                    break

                # 执行节点
                success = await self._execute_node(instance, current_node)

                if not success:
                    instance.status = WorkflowStatus.FAILED
                    instance.error = f"Node {current_node.node_id} execution failed"
                    self._record_history(instance_id, 'failed', {
                        'node_id': current_node.node_id,
                        'error': instance.error
                    })
                    return False

                # 获取下一个节点
                next_node_id = self._get_next_node(instance, current_node)

                if next_node_id:
                    instance.current_node_id = next_node_id
                else:
                    # 没有下一个节点，工作流完成
                    instance.status = WorkflowStatus.COMPLETED
                    instance.completed_at = datetime.now()
                    self._record_history(instance_id, 'completed', {})

            return instance.status == WorkflowStatus.COMPLETED

        except Exception as e:
            instance.status = WorkflowStatus.FAILED
            instance.error = str(e)
            self._record_history(instance_id, 'error', {'exception': str(e)})
            logger.error(f"Workflow execution failed: {e}")
            return False

    async def _execute_node(self, instance: WorkflowInstance, node: WorkflowNode) -> bool:
        """
        执行节点
        
        Args:
            instance: 工作流实例
            node: 节点
            
        Returns:
            是否执行成功
        """
        node.status = NodeStatus.RUNNING
        node.started_at = datetime.now()

        self._record_history(instance.instance_id, 'node_started', {
            'node_id': node.node_id,
            'node_type': node.node_type.value
        })

        try:
            # 根据节点类型执行不同的逻辑
            if node.node_type == NodeType.START:
                node.result = {'status': 'started'}

            elif node.node_type == NodeType.END:
                node.result = {'status': 'ended'}

            elif node.node_type == NodeType.ACTION:
                node.result = await self._execute_action(node.config, instance.context)

            elif node.node_type == NodeType.CONDITION:
                node.result = await self._evaluate_condition(node.config, instance.context)

            elif node.node_type == NodeType.APPROVAL:
                node.result = await self._handle_approval(node.config, instance.context)

            elif node.node_type == NodeType.DELAY:
                import asyncio
                delay_seconds = node.config.get('seconds', 1)
                await asyncio.sleep(delay_seconds)
                node.result = {'delayed': delay_seconds}

            node.status = NodeStatus.COMPLETED
            node.completed_at = datetime.now()

            self._record_history(instance.instance_id, 'node_completed', {
                'node_id': node.node_id,
                'result': node.result
            })

            return True

        except Exception as e:
            node.status = NodeStatus.FAILED
            node.error = str(e)
            node.completed_at = datetime.now()

            self._record_history(instance.instance_id, 'node_failed', {
                'node_id': node.node_id,
                'error': str(e)
            })

            return False

    async def _execute_action(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行动作节点
        
        Args:
            config: 节点配置 {action_type, action_params}
            context: 上下文
            
        Returns:
            执行结果
        """
        action_type = config.get('action_type', '')

        # 这里可以根据action_type调用不同的处理函数
        # 示例：发送通知、更新数据库、调用API等

        if action_type == 'send_notification':
            # 发送通知
            return {'sent': True, 'type': config.get('notification_type')}

        elif action_type == 'update_status':
            # 更新状态
            field = config.get('field')
            value = config.get('value')
            if field:
                context[field] = value
            return {'updated': field}

        else:
            # 默认动作
            return {'action': action_type, 'executed': True}

    async def _evaluate_condition(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        评估条件节点
        
        Args:
            config: 节点配置 {conditions: [{field, operator, value}]}
            context: 上下文
            
        Returns:
            评估结果
        """
        conditions = config.get('conditions', [])

        result = True
        for condition in conditions:
            field = condition.get('field')
            operator = condition.get('operator')
            expected_value = condition.get('value')

            actual_value = context.get(field)

            # 简单的条件判断
            if operator == 'equals':
                if actual_value != expected_value:
                    result = False
                    break
            elif operator == 'not_equals':
                if actual_value == expected_value:
                    result = False
                    break
            elif operator == 'greater_than':
                if not (actual_value > expected_value):
                    result = False
                    break
            elif operator == 'less_than':
                if not (actual_value < expected_value):
                    result = False
                    break

        return {'condition_met': result}

    async def _handle_approval(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理审批节点
        
        Args:
            config: 节点配置 {approver, approval_type}
            context: 上下文
            
        Returns:
            审批结果
        """
        # 在实际应用中，这里应该等待用户审批
        # 现在简化为自动通过
        return {
            'approved': True,
            'approver': config.get('approver'),
            'timestamp': datetime.now().isoformat()
        }

    def _get_next_node(self, instance: WorkflowInstance, current_node: WorkflowNode) -> Optional[str]:
        """
        获取下一个节点
        
        Args:
            instance: 工作流实例
            current_node: 当前节点
            
        Returns:
            下一个节点ID
        """
        workflow_def = self.workflows.get(instance.workflow_id, {})
        edges = workflow_def.get('edges', [])

        # 查找从当前节点出发的边
        for edge in edges:
            if edge['from'] == current_node.node_id:
                # 如果是条件节点，根据结果选择分支
                if current_node.node_type == NodeType.CONDITION:
                    condition_result = current_node.result.get('condition_met', False)
                    if edge.get('condition') == 'true' and condition_result:
                        return edge['to']
                    elif edge.get('condition') == 'false' and not condition_result:
                        return edge['to']
                else:
                    return edge['to']

        return None

    def _record_history(self, instance_id: str, event: str, data: Dict[str, Any]):
        """
        记录执行历史
        
        Args:
            instance_id: 实例ID
            event: 事件类型
            data: 事件数据
        """
        self.execution_history.append({
            'timestamp': datetime.now().isoformat(),
            'instance_id': instance_id,
            'event': event,
            'data': data
        })

    def get_instance(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """
        获取工作流实例
        
        Args:
            instance_id: 实例ID
            
        Returns:
            实例数据
        """
        instance = self.instances.get(instance_id)
        if instance:
            return instance.to_dict()
        return None

    def get_execution_history(self, instance_id: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取执行历史
        
        Args:
            instance_id: 实例ID（可选）
            limit: 返回数量限制
            
        Returns:
            历史记录列表
        """
        history = self.execution_history

        if instance_id:
            history = [h for h in history if h['instance_id'] == instance_id]

        # 按时间倒序
        history = sorted(history, key=lambda x: x['timestamp'], reverse=True)

        return history[:limit]

    def cancel_instance(self, instance_id: str) -> bool:
        """
        取消工作流实例
        
        Args:
            instance_id: 实例ID
            
        Returns:
            是否取消成功
        """
        if instance_id not in self.instances:
            return False

        instance = self.instances[instance_id]

        if instance.status in [WorkflowStatus.COMPLETED, WorkflowStatus.CANCELLED]:
            return False

        instance.status = WorkflowStatus.CANCELLED
        instance.completed_at = datetime.now()

        self._record_history(instance_id, 'cancelled', {})

        return True


# 全局实例
workflow_engine = WorkflowEngine()
