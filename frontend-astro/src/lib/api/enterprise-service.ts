/**
 * 企业管理服务
 * 提供许可证、工单、部署脚本、监控告警的API调用
 */

import {apiClient} from './base-client';

// ==================== 类型定义 ====================

export interface EnterpriseLicense {
  id: number;
  license_key: string;
  license_type: string;
  company_name: string;
  contact_email: string;
  max_sites: number;
  features: string | null;
  valid_from: string | null;
  valid_until: string | null;
  is_active: boolean;
  support_level: string;
  sla_enabled: boolean;
  sla_uptime_guarantee: number | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface SupportTicket {
  id: number;
  ticket_number: string;
  user_id: number;
  license_id: number | null;
  subject: string;
  description: string;
  priority: string;
  status: string;
  category: string | null;
  assigned_to: number | null;
  resolved_at: string | null;
  closed_at: string | null;
  created_at: string | null;
  updated_at: string | null;
  replies?: SupportTicketReply[];
}

export interface SupportTicketReply {
  id: number;
  ticket_id: number;
  user_id: number;
  content: string;
  is_staff: boolean;
  attachments: string | null;
  created_at: string | null;
}

export interface DeploymentScript {
  id: number;
  name: string;
  script_type: string;
  content: string;
  version: string;
  description: string | null;
  parameters: string | null;
  is_active: boolean;
  created_by: number | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface DeploymentLog {
  id: number;
  script_id: number;
  user_id: number | null;
  status: string;
  output: string | null;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string | null;
}

export interface MonitoringAlert {
  id: number;
  alert_type: string;
  severity: string;
  title: string;
  message: string;
  source: string | null;
  metric_name: string | null;
  metric_value: number | null;
  threshold: number | null;
  is_resolved: boolean;
  resolved_at: string | null;
  notified_users: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface MonitoringMetric {
  id: number;
  metric_name: string;
  metric_value: number;
  metric_type: string;
  labels: string | null;
  timestamp: string | null;
  site_id: number | null;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface EnterpriseOverview {
  licenses: { total: number; active: number };
  tickets: { total: number; open: number; in_progress: number };
  scripts: { total: number; deployments: number; failed: number };
  alerts: { total: number; unresolved: number };
}

// ==================== API 服务 ====================

class EnterpriseService {
  private readonly base = '/enterprise';

  // ---- 许可证 ----

  async getLicenses(params?: {
    license_type?: string;
    is_active?: boolean;
    page?: number;
    page_size?: number;
  }): Promise<{ success: boolean; data?: PaginatedResponse<EnterpriseLicense>; error?: string }> {
    const query: Record<string, string> = {};
    if (params?.license_type) query.license_type = params.license_type;
    if (params?.is_active !== undefined) query.is_active = String(params.is_active);
    if (params?.page) query.page = String(params.page);
    if (params?.page_size) query.page_size = String(params.page_size);
    return apiClient.request(`${this.base}/admin/licenses`, {method: 'GET'});
  }

  async getLicenseDetail(id: number): Promise<{ success: boolean; data?: EnterpriseLicense; error?: string }> {
    return apiClient.request(`${this.base}/admin/licenses/${id}`);
  }

  async updateLicense(id: number, data: Partial<EnterpriseLicense>): Promise<{
    success: boolean;
    data?: EnterpriseLicense;
    error?: string
  }> {
    return apiClient.request(`${this.base}/admin/licenses/${id}`, {method: 'PUT', body: data});
  }

  async deactivateLicense(id: number): Promise<{ success: boolean; error?: string }> {
    return apiClient.request(`${this.base}/admin/licenses/${id}`, {method: 'DELETE'});
  }

  // ---- 工单 ----

  async getTickets(params?: {
    status?: string;
    priority?: string;
    category?: string;
    page?: number;
    page_size?: number;
  }): Promise<{ success: boolean; data?: PaginatedResponse<SupportTicket>; error?: string }> {
    return apiClient.request(`${this.base}/admin/tickets`, {method: 'GET'});
  }

  async getTicketDetail(id: number): Promise<{ success: boolean; data?: SupportTicket; error?: string }> {
    return apiClient.request(`${this.base}/admin/tickets/${id}`);
  }

  async updateTicket(id: number, data: { status?: string; priority?: string; assigned_to?: number }): Promise<{
    success: boolean;
    data?: SupportTicket;
    error?: string
  }> {
    return apiClient.request(`${this.base}/admin/tickets/${id}`, {method: 'PUT', body: data});
  }

  async replyToTicket(ticketId: number, content: string): Promise<{ success: boolean; error?: string }> {
    return apiClient.request(`${this.base}/support/ticket/${ticketId}/reply`, {method: 'POST', body: {content}});
  }

  // ---- 部署脚本 ----

  async getScripts(params?: {
    script_type?: string;
    is_active?: boolean;
    page?: number;
    page_size?: number;
  }): Promise<{ success: boolean; data?: PaginatedResponse<DeploymentScript>; error?: string }> {
    return apiClient.request(`${this.base}/admin/scripts`, {method: 'GET'});
  }

  async getScriptDetail(id: number): Promise<{ success: boolean; data?: DeploymentScript; error?: string }> {
    return apiClient.request(`${this.base}/admin/scripts/${id}`);
  }

  async createScript(data: {
    name: string;
    script_type: string;
    content: string;
    version?: string;
    description?: string;
  }): Promise<{ success: boolean; data?: DeploymentScript; error?: string }> {
    return apiClient.request(`${this.base}/deployment/script`, {method: 'POST', body: data});
  }

  async updateScript(id: number, data: Partial<DeploymentScript>): Promise<{
    success: boolean;
    data?: DeploymentScript;
    error?: string
  }> {
    return apiClient.request(`${this.base}/admin/scripts/${id}`, {method: 'PUT', body: data});
  }

  async deleteScript(id: number): Promise<{ success: boolean; error?: string }> {
    return apiClient.request(`${this.base}/admin/scripts/${id}`, {method: 'DELETE'});
  }

  async executeScript(scriptId: number): Promise<{ success: boolean; error?: string }> {
    return apiClient.request(`${this.base}/deployment/script/${scriptId}/execute`, {method: 'POST'});
  }

  // ---- 部署日志 ----

  async getLogs(params?: {
    script_id?: number;
    status?: string;
    page?: number;
    page_size?: number;
  }): Promise<{ success: boolean; data?: PaginatedResponse<DeploymentLog>; error?: string }> {
    return apiClient.request(`${this.base}/admin/logs`, {method: 'GET'});
  }

  // ---- 监控告警 ----

  async getAlerts(params?: {
    severity?: string;
    alert_type?: string;
    is_resolved?: boolean;
    page?: number;
    page_size?: number;
  }): Promise<{ success: boolean; data?: PaginatedResponse<MonitoringAlert>; error?: string }> {
    return apiClient.request(`${this.base}/admin/alerts`, {method: 'GET'});
  }

  async resolveAlert(id: number): Promise<{ success: boolean; error?: string }> {
    return apiClient.request(`${this.base}/admin/alerts/${id}/resolve`, {method: 'PUT'});
  }

  async deleteAlert(id: number): Promise<{ success: boolean; error?: string }> {
    return apiClient.request(`${this.base}/admin/alerts/${id}`, {method: 'DELETE'});
  }

  // ---- 监控指标 ----

  async getMetrics(params?: {
    metric_name?: string;
    metric_type?: string;
    hours?: number;
    page?: number;
    page_size?: number;
  }): Promise<{ success: boolean; data?: PaginatedResponse<MonitoringMetric>; error?: string }> {
    return apiClient.request(`${this.base}/admin/metrics`, {method: 'GET'});
  }

  // ---- 概览 ----

  async getOverview(): Promise<{ success: boolean; data?: EnterpriseOverview; error?: string }> {
    return apiClient.request(`${this.base}/admin/overview`);
  }
}

export const enterpriseService = new EnterpriseService();
