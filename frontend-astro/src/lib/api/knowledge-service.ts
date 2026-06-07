// Knowledge (知识引擎) service for frontend
import {apiClient} from './base-client';
import type {ApiResponse} from '@/lib/api/base-types';

// ===== 知识引擎数据类型 =====

export interface KnowledgeBase {
    id: number;
    name: string;
    description?: string;
    embedding_model?: string;
    chunk_size: number;
    chunk_overlap: number;
    document_count: number;
    chunk_count: number;
    created_at: string;
    updated_at?: string;
}

export interface KnowledgeDocument {
    id: number;
    knowledge_base_id: number;
    filename: string;
    file_type?: string;
    file_size?: number;
    status: string; // uploading, processing, indexed, failed
    chunk_count: number;
    metadata?: Record<string, any>;
    created_at: string;
}

export interface SearchResult {
    chunk_id: number;
    document_id: number;
    content: string;
    score: number;
    metadata?: Record<string, any>;
}

export interface QAResult {
    answer: string;
    sources: Array<{
        document_id: number;
        chunk_id: number;
        content: string;
        score: number;
    }>;
}

export interface GeneratedReport {
    id: number;
    knowledge_base_id: number;
    title: string;
    report_type: string;
    content: string;
    query?: string;
    template_id?: number;
    metadata?: Record<string, any>;
    created_at: string;
}

export interface ReportTemplate {
    id: number;
    name: string;
    description?: string;
    template_type: string;
    structure: Record<string, any>;
    created_at: string;
}

export interface KnowledgeStats {
    knowledge_bases: { total: number };
    documents: { total: number; by_status: Record<string, number> };
    chunks: { total: number };
    reports: { total: number };
}

// ===== 知识引擎 API 服务 =====

export class KnowledgeService {
    // --- 知识库管理 ---
    static async getBases(params?: {
        page?: number;
        per_page?: number;
    }): Promise<ApiResponse<KnowledgeBase[]>> {
        return apiClient.get('/knowledge/bases', params);
    }

    static async getBase(baseId: number): Promise<ApiResponse<KnowledgeBase>> {
        return apiClient.get(`/knowledge/bases/${baseId}`);
    }

    static async createBase(data: {
        name: string;
        description?: string;
        embedding_model?: string;
        chunk_size?: number;
        chunk_overlap?: number;
    }): Promise<ApiResponse<KnowledgeBase>> {
        // Backend uses Form() annotation → must send form-encoded body
        return apiClient.postForm('/knowledge/bases', data);
    }

    static async updateBase(baseId: number, data: {
        name?: string;
        description?: string;
        chunk_size?: number;
        chunk_overlap?: number;
    }): Promise<ApiResponse<KnowledgeBase>> {
        // Backend uses Form() annotation → must send form-encoded body
        return apiClient.putForm(`/knowledge/bases/${baseId}`, data);
    }

    static async deleteBase(baseId: number): Promise<ApiResponse<void>> {
        return apiClient.delete(`/knowledge/bases/${baseId}`);
    }

    // --- 文档管理 ---
    static async getDocuments(baseId: number, params?: {
        page?: number;
        per_page?: number;
        status?: string;
    }): Promise<ApiResponse<KnowledgeDocument[]>> {
        return apiClient.get(`/knowledge/bases/${baseId}/documents`, params);
    }

    static async uploadDocument(baseId: number, file: File, metadata?: Record<string, any>): Promise<ApiResponse<KnowledgeDocument>> {
        const form = new FormData();
        form.append('file', file);
        if (metadata) {
            form.append('metadata', JSON.stringify(metadata));
        }
        // 使用 XMLHttpRequest 支持上传进度
        const xhr = new XMLHttpRequest();
        return new Promise((resolve, reject) => {
            xhr.open('POST', `/api/v2/knowledge/bases/${baseId}/documents/upload`);
            xhr.withCredentials = true;
            xhr.onload = () => {
                try {
                    resolve(JSON.parse(xhr.responseText));
                } catch {
                    resolve({success: false, error: xhr.responseText} as any);
                }
            };
            xhr.onerror = () => reject(new Error('文档上传失败'));
            xhr.send(form);
        });
    }

    static async deleteDocument(baseId: number, docId: number): Promise<ApiResponse<void>> {
        return apiClient.delete(`/knowledge/bases/${baseId}/documents/${docId}`);
    }

    // --- RAG 搜索与问答 ---
    static async ragSearch(baseId: number, query: string, topK: number = 5): Promise<ApiResponse<SearchResult[]>> {
        // Backend uses Form() annotation → must send form-encoded body
        return apiClient.postForm(`/knowledge/bases/${baseId}/search`, {query, top_k: topK});
    }

    static async knowledgeQA(baseId: number, question: string, params?: {
        top_k?: number;
        system_prompt?: string;
    }): Promise<ApiResponse<QAResult>> {
        // Backend uses Form() annotation → must send form-encoded body
        return apiClient.postForm(`/knowledge/bases/${baseId}/qa`, {
            question,
            top_k: params?.top_k,
            system_prompt: params?.system_prompt,
        });
    }

    // --- 研报生成 ---
    static async generateReport(baseId: number, data: {
        topic: string;
        template?: string;
        max_sections?: number;
        detail_level?: string;
    }): Promise<ApiResponse<GeneratedReport>> {
        // Backend uses Form() annotation → must send form-encoded body
        return apiClient.postForm(`/knowledge/bases/${baseId}/reports/generate`, data);
    }

    static async getReports(params?: {
        page?: number;
        per_page?: number;
        knowledge_base_id?: number;
    }): Promise<ApiResponse<GeneratedReport[]>> {
        return apiClient.get('/knowledge/reports', params);
    }

    static async getReportDetail(reportId: number): Promise<ApiResponse<GeneratedReport>> {
        return apiClient.get(`/knowledge/reports/${reportId}`);
    }

    // --- 报告模板 ---
    static async getReportTemplates(params?: {
        page?: number;
        per_page?: number;
        template_type?: string;
    }): Promise<ApiResponse<ReportTemplate[]>> {
        return apiClient.get('/knowledge/templates', params);
    }

    static async createReportTemplate(data: {
        name: string;
        description?: string;
        template_content?: string;
        sections?: string;
    }): Promise<ApiResponse<ReportTemplate>> {
        // Backend uses Form() annotation → must send form-encoded body
        return apiClient.postForm('/knowledge/templates', data);
    }

    // --- 统计 ---
    static async getStats(): Promise<ApiResponse<KnowledgeStats>> {
        return apiClient.get('/knowledge/stats');
    }
}
