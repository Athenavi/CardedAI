"""
FastBlog SDK - 工作流引擎模块

提供工作流定义管理、执行触发、执行记录查询、工具注册等 API 封装

用法:
    from fastblog_sdk import FastBlogClient

    client = FastBlogClient(base_url="http://localhost:9421/api/v2", token="...")

    # 工作流操作
    workflows = client.workflow.get_definitions()
    result = client.workflow.execute_workflow(workflow_id=1, input_data={"key": "value"})
    execution = client.workflow.get_execution(execution_id=1)
"""

from typing import Optional, Dict, Any, List


class WorkflowMixin:
    """
    工作流引擎 SDK Mixin

    为 FastBlogClient / AsyncFastBlogClient 添加工作流相关方法
    """

    # ==================== 工作流定义管理 ====================

    def get_workflow_definitions(self, page: int = 1, per_page: int = 20,
                                 is_active: bool = None,
                                 trigger_type: str = None) -> Dict[str, Any]:
        """
        获取工作流定义列表

        Args:
            page: 页码
            per_page: 每页数量
            is_active: 筛选活跃状态
            trigger_type: 筛选触发类型 (manual/cron/event/webhook)

        Returns:
            工作流定义列表
        """
        params: Dict[str, Any] = {'page': page, 'per_page': per_page}
        if is_active is not None:
            params['is_active'] = is_active
        if trigger_type:
            params['trigger_type'] = trigger_type
        return self._request('GET', '/workflow/definitions', params=params)

    def get_workflow_definition(self, def_id: int) -> Dict[str, Any]:
        """
        获取工作流定义详情

        Args:
            def_id: 工作流定义 ID

        Returns:
            工作流定义详情（含 graph_data, trigger_config）
        """
        return self._request('GET', f'/workflow/definitions/{def_id}')

    def create_workflow_definition(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建工作流定义

        Args:
            data: 工作流数据 {
                name: str,
                description: str,
                graph_data: str,  # JSON string: {"nodes": [...], "edges": [...]}
                trigger_type: str,
                trigger_config: str,  # JSON string
            }

        Returns:
            创建结果
        """
        return self._request('POST', '/workflow/definitions', json=data)

    def update_workflow_definition(self, def_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新工作流定义

        Args:
            def_id: 工作流定义 ID
            data: 更新数据

        Returns:
            更新结果
        """
        return self._request('PUT', f'/workflow/definitions/{def_id}', json=data)

    def delete_workflow_definition(self, def_id: int) -> Dict[str, Any]:
        """
        删除工作流定义

        Args:
            def_id: 工作流定义 ID

        Returns:
            删除结果
        """
        return self._request('DELETE', f'/workflow/definitions/{def_id}')

    def activate_workflow(self, def_id: int) -> Dict[str, Any]:
        """
        激活工作流（启用触发器）

        Args:
            def_id: 工作流定义 ID

        Returns:
            激活结果
        """
        return self._request('POST', f'/workflow/definitions/{def_id}/activate')

    def deactivate_workflow(self, def_id: int) -> Dict[str, Any]:
        """
        停用工作流（禁用触发器）

        Args:
            def_id: 工作流定义 ID

        Returns:
            停用结果
        """
        return self._request('POST', f'/workflow/definitions/{def_id}/deactivate')

    # ==================== 工作流执行 ====================

    def execute_workflow(self, def_id: int, input_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        手动触发工作流执行

        Args:
            def_id: 工作流定义 ID
            input_data: 输入数据

        Returns:
            执行结果
        """
        import json
        params = {
            'input_data': json.dumps(input_data or {}, ensure_ascii=False)
        }
        return self._request('POST', f'/workflow/definitions/{def_id}/execute', params=params)

    def get_executions(self, page: int = 1, per_page: int = 20,
                       workflow_definition_id: int = None,
                       status: str = None) -> Dict[str, Any]:
        """
        获取执行记录列表

        Args:
            page: 页码
            per_page: 每页数量
            workflow_definition_id: 按工作流定义 ID 筛选
            status: 按状态筛选 (pending/running/completed/failed/cancelled)

        Returns:
            执行记录列表
        """
        params: Dict[str, Any] = {'page': page, 'per_page': per_page}
        if workflow_definition_id:
            params['workflow_definition_id'] = workflow_definition_id
        if status:
            params['status'] = status
        return self._request('GET', '/workflow/executions', params=params)

    def get_execution(self, execution_id: int) -> Dict[str, Any]:
        """
        获取执行记录详情

        Args:
            execution_id: 执行记录 ID

        Returns:
            执行记录详情（含节点执行状态）
        """
        return self._request('GET', f'/workflow/executions/{execution_id}')

    def cancel_execution(self, execution_id: int) -> Dict[str, Any]:
        """
        取消正在运行的执行

        Args:
            execution_id: 执行记录 ID

        Returns:
            取消结果
        """
        return self._request('POST', f'/workflow/executions/{execution_id}/cancel')

    # ==================== 工具管理 ====================

    def get_workflow_tools(self, tool_type: str = None) -> Dict[str, Any]:
        """
        获取已注册的 Agent 工具列表

        Args:
            tool_type: 工具类型筛选

        Returns:
            工具列表
        """
        params = {}
        if tool_type:
            params['tool_type'] = tool_type
        return self._request('GET', '/workflow/tools', params=params)

    def register_workflow_tool(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        注册新的 Agent 工具

        Args:
            data: 工具数据 {name, tool_type, description, config, ...}

        Returns:
            注册结果
        """
        return self._request('POST', '/workflow/tools', json=data)

    def test_workflow_tool(self, name: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        测试调用指定工具

        Args:
            name: 工具名称
            params: 测试参数

        Returns:
            测试结果
        """
        import json
        return self._request('POST', f'/workflow/tools/{name}/test',
                             params={'params': json.dumps(params or {}, ensure_ascii=False)})

    # ==================== 触发器管理 ====================

    def get_triggers(self) -> Dict[str, Any]:
        """
        获取工作流触发器列表

        Returns:
            触发器列表
        """
        return self._request('GET', '/workflow/triggers')

    def create_cron_trigger(self, workflow_definition_id: int, cron_expr: str,
                            timezone: str = "UTC") -> Dict[str, Any]:
        """
        创建定时触发器

        Args:
            workflow_definition_id: 工作流定义 ID
            cron_expr: Cron 表达式
            timezone: 时区

        Returns:
            创建结果
        """
        return self._request('POST', '/workflow/triggers/cron', params={
            'workflow_definition_id': workflow_definition_id,
            'cron_expr': cron_expr,
            'timezone': timezone,
        })

    def create_event_trigger(self, workflow_definition_id: int, event_type: str,
                             filter_config: str = "{}") -> Dict[str, Any]:
        """
        创建事件触发器

        Args:
            workflow_definition_id: 工作流定义 ID
            event_type: 事件类型
            filter_config: 过滤配置 JSON

        Returns:
            创建结果
        """
        return self._request('POST', '/workflow/triggers/event', params={
            'workflow_definition_id': workflow_definition_id,
            'event_type': event_type,
            'filter_config': filter_config,
        })

    def delete_trigger(self, trigger_id: int) -> Dict[str, Any]:
        """
        删除触发器

        Args:
            trigger_id: 触发器 ID

        Returns:
            删除结果
        """
        return self._request('DELETE', f'/workflow/triggers/{trigger_id}')


class AsyncWorkflowMixin:
    """
    工作流引擎异步 SDK Mixin

    为 AsyncFastBlogClient 添加工作流相关异步方法
    """

    async def get_workflow_definitions(self, page: int = 1, per_page: int = 20,
                                       is_active: bool = None,
                                       trigger_type: str = None) -> Dict[str, Any]:
        params: Dict[str, Any] = {'page': page, 'per_page': per_page}
        if is_active is not None:
            params['is_active'] = is_active
        if trigger_type:
            params['trigger_type'] = trigger_type
        return await self._request('GET', '/workflow/definitions', params=params)

    async def get_workflow_definition(self, def_id: int) -> Dict[str, Any]:
        return await self._request('GET', f'/workflow/definitions/{def_id}')

    async def create_workflow_definition(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return await self._request('POST', '/workflow/definitions', json=data)

    async def update_workflow_definition(self, def_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        return await self._request('PUT', f'/workflow/definitions/{def_id}', json=data)

    async def delete_workflow_definition(self, def_id: int) -> Dict[str, Any]:
        return await self._request('DELETE', f'/workflow/definitions/{def_id}')

    async def activate_workflow(self, def_id: int) -> Dict[str, Any]:
        return await self._request('POST', f'/workflow/definitions/{def_id}/activate')

    async def deactivate_workflow(self, def_id: int) -> Dict[str, Any]:
        return await self._request('POST', f'/workflow/definitions/{def_id}/deactivate')

    async def execute_workflow(self, def_id: int, input_data: Dict[str, Any] = None) -> Dict[str, Any]:
        import json
        params = {
            'input_data': json.dumps(input_data or {}, ensure_ascii=False)
        }
        return await self._request('POST', f'/workflow/definitions/{def_id}/execute', params=params)

    async def get_executions(self, page: int = 1, per_page: int = 20,
                             workflow_definition_id: int = None,
                             status: str = None) -> Dict[str, Any]:
        params: Dict[str, Any] = {'page': page, 'per_page': per_page}
        if workflow_definition_id:
            params['workflow_definition_id'] = workflow_definition_id
        if status:
            params['status'] = status
        return await self._request('GET', '/workflow/executions', params=params)

    async def get_execution(self, execution_id: int) -> Dict[str, Any]:
        return await self._request('GET', f'/workflow/executions/{execution_id}')

    async def cancel_execution(self, execution_id: int) -> Dict[str, Any]:
        return await self._request('POST', f'/workflow/executions/{execution_id}/cancel')

    async def get_workflow_tools(self, tool_type: str = None) -> Dict[str, Any]:
        params = {}
        if tool_type:
            params['tool_type'] = tool_type
        return await self._request('GET', '/workflow/tools', params=params)

    async def register_workflow_tool(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return await self._request('POST', '/workflow/tools', json=data)

    async def test_workflow_tool(self, name: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        import json
        return await self._request('POST', f'/workflow/tools/{name}/test',
                                   params={'params': json.dumps(params or {}, ensure_ascii=False)})

    async def get_triggers(self) -> Dict[str, Any]:
        return await self._request('GET', '/workflow/triggers')

    async def create_cron_trigger(self, workflow_definition_id: int, cron_expr: str,
                                  timezone: str = "UTC") -> Dict[str, Any]:
        return await self._request('POST', '/workflow/triggers/cron', params={
            'workflow_definition_id': workflow_definition_id,
            'cron_expr': cron_expr,
            'timezone': timezone,
        })

    async def create_event_trigger(self, workflow_definition_id: int, event_type: str,
                                   filter_config: str = "{}") -> Dict[str, Any]:
        return await self._request('POST', '/workflow/triggers/event', params={
            'workflow_definition_id': workflow_definition_id,
            'event_type': event_type,
            'filter_config': filter_config,
        })

    async def delete_trigger(self, trigger_id: int) -> Dict[str, Any]:
        return await self._request('DELETE', f'/workflow/triggers/{trigger_id}')
