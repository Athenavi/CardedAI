// Workflow (工作流引擎) service for frontend
import {apiClient} from './base-client';
import type {ApiResponse} from '@/lib/api/base-types';

// ===== 工作流引擎数据类型 =====

export interface WorkflowDefinition {
    id: number;
    name: string;
    description?: string;
    graph: string;  // JSON string of {nodes, edges}
    trigger_config?: string;  // JSON string
    is_active: boolean;
    version: number;
    created_at: string;
    updated_at?: string;
}

export interface WorkflowExecution {
    id: number;
    workflow_id: number;
    workflow_name?: string;
    status: string; // pending, running, completed, failed, cancelled
    trigger_type: string;
    input_data?: Record<string, any>;
    output_data?: Record<string, any>;
    error_message?: string;
    node_status?: Record<string, any>;
    started_at: string;
    completed_at?: string;
}

export interface AgentTool {
    id: number;
    name: string;
    tool_type: string;
    description?: string;
    parameters?: Record<string, any>;
    implementation?: string;
    is_active: boolean;
    created_at: string;
}

export interface Trigger {
    id: number;
    workflow_id: number;
    trigger_type: string; // cron, event, webhook
    config: Record<string, any>;
    is_active: boolean;
    last_triggered_at?: string;
    next_run_at?: string;
    created_at: string;
}

export interface WorkflowStats {
    definitions: { total: number; active: number };
    executions: { total: number; by_status: Record<string, number>; recent_24h: number };
    tools: { total: number; by_type: Record<string, number> };
    triggers: { total: number; by_type: Record<string, number> };
}

// ===== 工作流引擎 API 服务 =====

export class WorkflowService {
    // --- 工作流定义管理 ---
    static async getDefinitions(params?: {
        page?: number;
        per_page?: number;
        is_active?: boolean;
    }): Promise<ApiResponse<WorkflowDefinition[]>> {
        return apiClient.get('/workflow/definitions', params);
    }

    static async getDefinition(defId: number): Promise<ApiResponse<WorkflowDefinition>> {
        return apiClient.get(`/workflow/definitions/${defId}`);
    }

    static async createDefinition(data: {
        name: string;
        description?: string;
        graph: string;
        trigger_config?: string;
    }): Promise<ApiResponse<WorkflowDefinition>> {
        return apiClient.post('/workflow/definitions', data);
    }

    static async updateDefinition(defId: number, data: {
        name?: string;
        description?: string;
        graph?: string;
        trigger_config?: string;
    }): Promise<ApiResponse<WorkflowDefinition>> {
        return apiClient.put(`/workflow/definitions/${defId}`, data);
    }

    static async deleteDefinition(defId: number): Promise<ApiResponse<void>> {
        return apiClient.delete(`/workflow/definitions/${defId}`);
    }

    static async activateDefinition(defId: number): Promise<ApiResponse<void>> {
        return apiClient.post(`/workflow/definitions/${defId}/activate`);
    }

    static async deactivateDefinition(defId: number): Promise<ApiResponse<void>> {
        return apiClient.post(`/workflow/definitions/${defId}/deactivate`);
    }

    // --- 工作流执行 ---
    static async executeWorkflow(defId: number, inputData?: Record<string, any>): Promise<ApiResponse<WorkflowExecution>> {
        return apiClient.post(`/workflow/definitions/${defId}/execute`, {input_data: inputData});
    }

    static async getExecutions(params?: {
        page?: number;
        per_page?: number;
        workflow_id?: number;
        status?: string;
    }): Promise<ApiResponse<WorkflowExecution[]>> {
        return apiClient.get('/workflow/executions', params);
    }

    static async getExecution(execId: number): Promise<ApiResponse<WorkflowExecution>> {
        return apiClient.get(`/workflow/executions/${execId}`);
    }

    static async cancelExecution(execId: number): Promise<ApiResponse<void>> {
        return apiClient.post(`/workflow/executions/${execId}/cancel`);
    }

    // --- Agent 工具管理 ---
    static async getTools(toolType?: string): Promise<ApiResponse<AgentTool[]>> {
        return apiClient.get('/workflow/tools', toolType ? {tool_type: toolType} : undefined);
    }

    static async registerTool(data: {
        name: string;
        tool_type: string;
        description: string;
        parameters?: Record<string, any>;
    }): Promise<ApiResponse<AgentTool>> {
        const body: Record<string, any> = {
            name: data.name,
            tool_type: data.tool_type,
            description: data.description,
            parameters: JSON.stringify(data.parameters || {}),
        };
        return apiClient.post('/workflow/tools', body);
    }

    static async testTool(name: string, toolParams?: Record<string, any>): Promise<ApiResponse<any>> {
        return apiClient.post(`/workflow/tools/${name}/test`, {
            params: JSON.stringify(toolParams || {}),
        });
    }

    // --- 触发器管理 ---
    static async getTriggers(): Promise<ApiResponse<Trigger[]>> {
        return apiClient.get('/workflow/triggers');
    }

    static async createCronTrigger(data: {
        workflow_id: number;
        cron_expr: string;
    }): Promise<ApiResponse<Trigger>> {
        return apiClient.post('/workflow/triggers/cron', {
            workflow_id: data.workflow_id,
            cron_expr: data.cron_expr,
        });
    }

    static async createEventTrigger(data: {
        workflow_id: number;
        event_name: string;
    }): Promise<ApiResponse<Trigger>> {
        return apiClient.post('/workflow/triggers/event', {
            workflow_id: data.workflow_id,
            event_name: data.event_name,
        });
    }

    static async createWebhookTrigger(data: {
        workflow_id: number;
    }): Promise<ApiResponse<Trigger>> {
        return apiClient.post('/workflow/triggers/webhook', {
            workflow_id: data.workflow_id,
        });
    }

    static async deleteTrigger(triggerId: number): Promise<ApiResponse<void>> {
        return apiClient.delete(`/workflow/triggers/${triggerId}`);
    }

    // --- 统计 ---
    static async getStats(): Promise<ApiResponse<WorkflowStats>> {
        return apiClient.get('/workflow/stats');
    }
}
