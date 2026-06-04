/**
 * FastBlog API JavaScript/TypeScript SDK (V2)
 *
 * 完整的 FastBlog 博客系统 API 客户端
 *
 * @version 2.0.0
 * @api-version V2 (/api/v2/)
 * @fastblog-version V0.3.26.0521+
 */

import axios, {AxiosInstance} from 'axios';

// ============================================================================
// 类型定义
// ============================================================================

export interface AuthResponse {
  user: UserInfo;
    access_token: string;
    refresh_token?: string;
}

export interface UserInfo {
    id: number;
    username: string;
    email: string;
    role?: string;
    bio?: string;
    profile_picture?: string;
  is_active?: boolean;
  is_superuser?: boolean;
  is_staff?: boolean;
  vip_level?: number;
}

export interface Article {
    id: number;
    title: string;
    slug: string;
    excerpt?: string;
    content?: string;
    cover_image?: string;
    tags?: string[];
    author?: UserInfo;
    category_id?: number;
    category_name?: string;
    views?: number;
    likes?: number;
    status?: number | string;
    created_at?: string;
    updated_at?: string;
}

export interface Category {
    id: number;
    name: string;
    slug: string;
    description?: string;
    parent_id?: number | null;
    article_count?: number;
    order?: number;
}

export interface MediaFile {
    id: number;
    filename: string;
    url: string;
    thumbnail_url?: string;
    size?: number;
    mime_type?: string;
    created_at?: string;
}

export interface Comment {
    id: number;
    content: string;
    article_id: number;
    user_id?: number;
    parent_id?: number | null;
    created_at?: string;
    updated_at?: string;
}

export interface DashboardStats {
    total_articles: number;
    published_articles: number;
    draft_articles: number;
    total_users: number;
    active_users: number;
    total_views: number;
    total_likes: number;
    total_comments: number;
    recent_articles?: Article[];
    popular_articles?: Article[];
    views_trend?: Array<{ date: string; views: number }>;
}

export interface Plugin {
    id: number;
    name: string;
    slug: string;
    version: string;
    description?: string;
    author?: string;
    active: boolean;
    installed: boolean;
    settings?: Record<string, any>;
}

// ============================================================================
// 情报引擎接口
// ============================================================================

export interface IntelSource {
    id: number;
    name: string;
    source_type: string;
    url?: string;
    config?: Record<string, any>;
    is_active: boolean;
    last_collected_at?: string;
    created_at?: string;
    updated_at?: string;
}

export interface Intelligence {
    id: number;
    title: string;
    summary?: string;
    content?: string;
    category?: string;
    sentiment?: string;
    importance_score?: number;
    source_url?: string;
    tags?: string[];
    created_at?: string;
}

export interface Briefing {
    id: number;
    title: string;
    briefing_type: string;
    content?: string;
    topic?: string;
    date_range_start?: string;
    date_range_end?: string;
    created_at?: string;
}

export interface AlertRule {
    id: number;
    name: string;
    rule_type: string;
    conditions?: Record<string, any>;
    actions?: Record<string, any>;
    is_active: boolean;
    created_at?: string;
}

// ============================================================================
// 知识引擎接口
// ============================================================================

export interface KnowledgeBase {
    id: number;
    name: string;
    description?: string;
    embedding_model?: string;
    chunk_size?: number;
    chunk_overlap?: number;
    document_count?: number;
    chunk_count?: number;
    created_at?: string;
    updated_at?: string;
}

export interface KnowledgeDocument {
    id: number;
    knowledge_base_id: number;
    filename: string;
    file_type?: string;
    file_size?: number;
    chunk_count?: number;
    status?: string;
    created_at?: string;
}

export interface GeneratedReport {
    id: number;
    title: string;
    content?: string;
    report_type?: string;
    knowledge_base_id?: number;
    template_id?: number;
    created_at?: string;
}

export interface ReportTemplate {
    id: number;
    name: string;
    description?: string;
    template_type?: string;
    structure?: Record<string, any>;
    created_at?: string;
}

// ============================================================================
// 工作流引擎接口
// ============================================================================

export interface WorkflowDefinition {
    id: number;
    name: string;
    description?: string;
    graph_data?: Record<string, any>;
    trigger_config?: Record<string, any>;
    is_active: boolean;
    version?: number;
    created_at?: string;
    updated_at?: string;
}

export interface WorkflowExecution {
    id: number;
    workflow_id: number;
    status: string;
    input_data?: Record<string, any>;
    output_data?: Record<string, any>;
    error_message?: string;
    started_at?: string;
    finished_at?: string;
    created_at?: string;
}

export interface AgentTool {
    id: number;
    name: string;
    tool_type: string;
    description?: string;
    parameters?: Record<string, any>;
    implementation?: string;
    created_at?: string;
}

export interface Trigger {
    id: number;
    workflow_id: number;
    trigger_type: string;
    config?: Record<string, any>;
    is_active: boolean;
    created_at?: string;
}

export interface ApiResponse<T = any> {
    success: boolean;
    data?: T;
    error?: string;
    message?: string;
    pagination?: {
        current_page: number;
        per_page: number;
        total: number;
        total_pages: number;
        has_next: boolean;
        has_prev: boolean;
    };
}

// ============================================================================
// SDK 配置
// ============================================================================

export interface SDKConfig {
  /** API V2 基础 URL，例如 http://localhost:9421/api/v2 */
    baseURL: string;
    timeout?: number;
    accessToken?: string;
    headers?: Record<string, string>;
}

// ============================================================================
// FastBlog SDK 主类
// ============================================================================

export class FastBlogSDK {
    private client: AxiosInstance;
    private accessToken: string | null = null;

    constructor(config: SDKConfig) {
        this.accessToken = config.accessToken || null;

        this.client = axios.create({
            baseURL: config.baseURL,
            timeout: config.timeout || 30000,
            headers: {
                'Content-Type': 'application/json',
                ...config.headers,
            },
        });

        // 请求拦截器 - 自动添加 Token
        this.client.interceptors.request.use((config) => {
            if (this.accessToken) {
                config.headers['Authorization'] = `Bearer ${this.accessToken}`;
            }
            return config;
        });

        // 响应拦截器 - 统一错误处理
        this.client.interceptors.response.use(
            (response) => response,
            (error) => {
                const message = error.response?.data?.error || error.message;
                return Promise.reject(new Error(`FastBlog API Error: ${message}`));
            }
        );
    }

  // 🔐 认端点: /api/v2/auth/

    /**
     * 用户登录（支持用户名或邮箱）
     * 端点: POST /auth/login
     */
    async login(username: string, password: string): Promise<AuthResponse> {
        const response = await this.client.post<ApiResponse<AuthResponse>>('/auth/login', {
            username,
            password,
        });

        const data = response.data.data!;
        this.accessToken = data.access_token;

        return data;
    }

    /**
     * 刷新 Token
     * 端点: POST /auth/token/refresh
     */
    async refreshToken(): Promise<AuthResponse> {
      const response = await this.client.post<ApiResponse<AuthResponse>>('/auth/token/refresh');
        const data = response.data.data!;
        this.accessToken = data.access_token;
        return data;
    }

    /**
     * 登出（将当前 token 加入黑名单）
     * 端点: POST /auth/logout
     */
    async logout(): Promise<void> {
        await this.client.post('/auth/logout');
        this.accessToken = null;
    }

    /**
     * 设置 Access Token
     */
    setAccessToken(token: string): void {
        this.accessToken = token;
    }

  // 📝 文章模块 - 端点: /api/v2/articles/

    /**
     * 获取文章列表
     * 端点: GET /articles
     */
    async getArticles(params?: {
        page?: number;
        perPage?: number;
        search?: string;
        categoryId?: number;
        userId?: number;
        status?: string;
        orderBy?: string;
        order?: 'asc' | 'desc';
    }): Promise<ApiResponse<Article[]>> {
        const queryParams: Record<string, any> = {
            page: params?.page || 1,
            per_page: params?.perPage || 10,
        };

        if (params?.search) queryParams.search = params.search;
        if (params?.categoryId) queryParams.category_id = params.categoryId;
        if (params?.userId) queryParams.user_id = params.userId;
        if (params?.status) queryParams.status = params.status;
        if (params?.orderBy) queryParams.order_by = params.orderBy;
        if (params?.order) queryParams.order = params.order;

        const response = await this.client.get<ApiResponse<Article[]>>('/articles', {
            params: queryParams,
        });

        return response.data;
    }

    /**
     * 获取文章详情
     * 端点: GET /articles/{id}
     */
    async getArticle(id: number): Promise<ApiResponse<Article>> {
        const response = await this.client.get<ApiResponse<Article>>(`/articles/${id}`);
        return response.data;
    }

    /**
     * 创建文章
     * 端点: POST /articles
     */
    async createArticle(article: {
        title: string;
        slug?: string;
        excerpt?: string;
        content: string;
        categoryId?: number;
        tags?: string[];
        coverImage?: string;
        status?: string;
    }): Promise<ApiResponse<Article>> {
        const response = await this.client.post<ApiResponse<Article>>('/articles', {
            title: article.title,
            slug: article.slug,
            excerpt: article.excerpt,
            content: article.content,
            category_id: article.categoryId,
            tags: article.tags,
            cover_image: article.coverImage,
            status: article.status,
        });
        return response.data;
    }

    /**
     * 更新文章
     * 端点: PUT /articles/{id}
     */
    async updateArticle(id: number, updates: Partial<Article>): Promise<ApiResponse<Article>> {
        const response = await this.client.put<ApiResponse<Article>>(`/articles/${id}`, updates);
        return response.data;
    }

    /**
     * 删除文章
     * 端点: DELETE /articles/{id}
     */
    async deleteArticle(id: number): Promise<ApiResponse<void>> {
        const response = await this.client.delete<ApiResponse<void>>(`/articles/${id}`);
        return response.data;
    }

  // 📂 分类模块 - 端点: /api/v2/categories/

    /**
     * 获取分类列表
     * 端点: GET /categories
     */
    async getCategories(): Promise<ApiResponse<Category[]>> {
        const response = await this.client.get<ApiResponse<Category[]>>('/categories');
        return response.data;
    }

    /**
     * 创建分类
     * 端点: POST /categories
     */
    async createCategory(category: {
        name: string;
        slug?: string;
        description?: string;
        parentId?: number | null;
    }): Promise<ApiResponse<Category>> {
        const response = await this.client.post<ApiResponse<Category>>('/categories', {
            name: category.name,
            slug: category.slug,
            description: category.description,
            parent_id: category.parentId,
        });
        return response.data;
    }

  // 🖼️ 媒体模块 - 端点: /api/v2/media/

    /**
     * 上传文件
     * 端点: POST /media/upload
     */
    async uploadFile(file: File | Blob, folder: string = 'uploads'): Promise<ApiResponse<MediaFile>> {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('folder', folder);

        const response = await this.client.post<ApiResponse<MediaFile>>('/media/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });

        return response.data;
    }

    /**
     * 获取媒体列表
     * 端点: GET /media/files
     */
    async getMedia(page: number = 1, perPage: number = 20): Promise<ApiResponse<MediaFile[]>> {
      const response = await this.client.get<ApiResponse<MediaFile[]>>('/media/files', {
            params: {page, per_page: perPage},
        });
        return response.data;
    }

  // 👥 用户模块 - 端点: /api/v2/users/

    /**
     * 获取当前用户信息
     * 端点: GET /users/me
     */
    async getCurrentUser(): Promise<ApiResponse<UserInfo>> {
        const response = await this.client.get<ApiResponse<UserInfo>>('/users/me');
        return response.data;
    }

    /**
     * 获取用户列表
     * 端点: GET /users/
     */
    async getUsers(page: number = 1, perPage: number = 10): Promise<ApiResponse<UserInfo[]>> {
      const response = await this.client.get<ApiResponse<UserInfo[]>>('/users/', {
            params: {page, per_page: perPage},
        });
        return response.data;
    }

  // 💬 评论模块 - 端点: /api/v2/comments/

    /**
     * 获取文章评论
     * 端点: GET /comments
     */
    async getComments(articleId: number, page: number = 1, perPage: number = 20): Promise<ApiResponse<Comment[]>> {
        const response = await this.client.get<ApiResponse<Comment[]>>('/comments', {
            params: {article_id: articleId, page, per_page: perPage},
        });
        return response.data;
    }

    /**
     * 发表评论
     * 端点: POST /comments
     */
    async createComment(comment: {
        articleId: number;
        content: string;
        parentId?: number | null;
    }): Promise<ApiResponse<Comment>> {
        const response = await this.client.post<ApiResponse<Comment>>('/comments', {
            article_id: comment.articleId,
            content: comment.content,
            parent_id: comment.parentId,
        });
        return response.data;
    }

  // 📊 仪表板模块 - 端点: /api/v2/dashboard/

    /**
     * 获取统计数据
     * 端点: GET /dashboard/stats
     */
    async getDashboardStats(): Promise<ApiResponse<DashboardStats>> {
        const response = await this.client.get<ApiResponse<DashboardStats>>('/dashboard/stats');
        return response.data;
    }

    /**
     * 获取分析数据
     * 端点: GET /dashboard/analytics
     */
    async getDashboardAnalytics(days: number = 30): Promise<ApiResponse<any>> {
        const response = await this.client.get<ApiResponse<any>>('/dashboard/analytics', {
            params: {days},
        });
        return response.data;
    }

  // 🔌 插件模块 - 端点: /api/v2/plugins/

    /**
     * 获取插件列表
     * 端点: GET /plugins/
     */
    async getPlugins(): Promise<ApiResponse<Plugin[]>> {
      const response = await this.client.get<ApiResponse<Plugin[]>>('/plugins/');
        return response.data;
    }

    /**
     * 激活插件
     * 端点: POST /plugins/{slug}/activate
     */
    async activatePlugin(slug: string): Promise<ApiResponse<void>> {
        const response = await this.client.post<ApiResponse<void>>(`/plugins/${slug}/activate`);
        return response.data;
    }

    /**
     * 停用插件
     * 端点: POST /plugins/{slug}/deactivate
     */
    async deactivatePlugin(slug: string): Promise<ApiResponse<void>> {
        const response = await this.client.post<ApiResponse<void>>(`/plugins/${slug}/deactivate`);
        return response.data;
    }

  // ═══════════════════════════════════════════════════════════════════════════
  // 🕵️ 情报引擎 - 端点: /api/v2/intel/
  // ═══════════════════════════════════════════════════════════════════════════

    /** 获取数据源列表 */
    async getIntelSources(params?: { page?: number; per_page?: number; source_type?: string; is_active?: boolean }): Promise<ApiResponse<IntelSource[]>> {
        const response = await this.client.get<ApiResponse<IntelSource[]>>('/intel/sources', { params });
        return response.data;
    }

    /** 获取数据源详情 */
    async getIntelSource(sourceId: number): Promise<ApiResponse<IntelSource>> {
        const response = await this.client.get<ApiResponse<IntelSource>>(`/intel/sources/${sourceId}`);
        return response.data;
    }

    /** 创建数据源 */
    async createIntelSource(source: { name: string; source_type: string; url?: string; config?: Record<string, any> }): Promise<ApiResponse<IntelSource>> {
        const response = await this.client.post<ApiResponse<IntelSource>>('/intel/sources', source);
        return response.data;
    }

    /** 更新数据源 */
    async updateIntelSource(sourceId: number, updates: Partial<IntelSource>): Promise<ApiResponse<IntelSource>> {
        const response = await this.client.put<ApiResponse<IntelSource>>(`/intel/sources/${sourceId}`, updates);
        return response.data;
    }

    /** 删除数据源 */
    async deleteIntelSource(sourceId: number): Promise<ApiResponse<void>> {
        const response = await this.client.delete<ApiResponse<void>>(`/intel/sources/${sourceId}`);
        return response.data;
    }

    /** 手动触发采集 */
    async triggerCollection(sourceId: number): Promise<ApiResponse<any>> {
        const response = await this.client.post<ApiResponse<any>>(`/intel/sources/${sourceId}/collect`);
        return response.data;
    }

    /** 获取情报列表 */
    async getIntelligence(params?: { page?: number; per_page?: number; category?: string; sentiment?: string }): Promise<ApiResponse<Intelligence[]>> {
        const response = await this.client.get<ApiResponse<Intelligence[]>>('/intel/intelligence', { params });
        return response.data;
    }

    /** 获取情报详情 */
    async getIntelligenceDetail(intelId: number): Promise<ApiResponse<Intelligence>> {
        const response = await this.client.get<ApiResponse<Intelligence>>(`/intel/intelligence/${intelId}`);
        return response.data;
    }

    /** 搜索情报 */
    async searchIntelligence(query: string, params?: { category?: string; sentiment?: string; limit?: number }): Promise<ApiResponse<Intelligence[]>> {
        const response = await this.client.get<ApiResponse<Intelligence[]>>('/intel/intelligence', {
            params: { search: query, ...params },
        });
        return response.data;
    }

    /** 获取简报列表 */
    async getBriefings(params?: { page?: number; per_page?: number; briefing_type?: string }): Promise<ApiResponse<Briefing[]>> {
        const response = await this.client.get<ApiResponse<Briefing[]>>('/intel/briefings', { params });
        return response.data;
    }

    /** 获取简报详情 */
    async getBriefingDetail(briefingId: number): Promise<ApiResponse<Briefing>> {
        const response = await this.client.get<ApiResponse<Briefing>>(`/intel/briefings/${briefingId}`);
        return response.data;
    }

    /** 生成简报 */
    async generateBriefing(params?: { briefing_type?: string; topic?: string; days?: number }): Promise<ApiResponse<Briefing>> {
        const response = await this.client.post<ApiResponse<Briefing>>('/intel/briefings/generate', null, { params });
        return response.data;
    }

    /** 获取预警规则列表 */
    async getAlertRules(params?: { page?: number; per_page?: number; is_active?: boolean }): Promise<ApiResponse<AlertRule[]>> {
        const response = await this.client.get<ApiResponse<AlertRule[]>>('/intel/alerts/rules', { params });
        return response.data;
    }

    /** 创建预警规则 */
    async createAlertRule(rule: { name: string; rule_type: string; conditions: Record<string, any>; actions: Record<string, any> }): Promise<ApiResponse<AlertRule>> {
        const response = await this.client.post<ApiResponse<AlertRule>>('/intel/alerts/rules', rule);
        return response.data;
    }

    /** 触发数据源分析 */
    async triggerAnalysis(sourceId: number): Promise<ApiResponse<any>> {
        const response = await this.client.post<ApiResponse<any>>(`/intel/analyze/${sourceId}`);
        return response.data;
    }

  // ═══════════════════════════════════════════════════════════════════════════
  // 📚 知识引擎 - 端点: /api/v2/knowledge/
  // ═══════════════════════════════════════════════════════════════════════════

    /** 获取知识库列表 */
    async getKnowledgeBases(params?: { page?: number; per_page?: number }): Promise<ApiResponse<KnowledgeBase[]>> {
        const response = await this.client.get<ApiResponse<KnowledgeBase[]>>('/knowledge/bases', { params });
        return response.data;
    }

    /** 获取知识库详情 */
    async getKnowledgeBase(baseId: number): Promise<ApiResponse<KnowledgeBase>> {
        const response = await this.client.get<ApiResponse<KnowledgeBase>>(`/knowledge/bases/${baseId}`);
        return response.data;
    }

    /** 创建知识库 */
    async createKnowledgeBase(base: { name: string; description?: string; embedding_model?: string; chunk_size?: number; chunk_overlap?: number }): Promise<ApiResponse<KnowledgeBase>> {
        const response = await this.client.post<ApiResponse<KnowledgeBase>>('/knowledge/bases', base);
        return response.data;
    }

    /** 更新知识库 */
    async updateKnowledgeBase(baseId: number, updates: Partial<KnowledgeBase>): Promise<ApiResponse<KnowledgeBase>> {
        const response = await this.client.put<ApiResponse<KnowledgeBase>>(`/knowledge/bases/${baseId}`, updates);
        return response.data;
    }

    /** 删除知识库 */
    async deleteKnowledgeBase(baseId: number): Promise<ApiResponse<void>> {
        const response = await this.client.delete<ApiResponse<void>>(`/knowledge/bases/${baseId}`);
        return response.data;
    }

    /** 获取文档列表 */
    async getKnowledgeDocuments(baseId: number, params?: { page?: number; per_page?: number; status?: string }): Promise<ApiResponse<KnowledgeDocument[]>> {
        const response = await this.client.get<ApiResponse<KnowledgeDocument[]>>(`/knowledge/bases/${baseId}/documents`, { params });
        return response.data;
    }

    /** 上传文档到知识库 */
    async uploadKnowledgeDocument(baseId: number, file: File | Blob, filename?: string): Promise<ApiResponse<KnowledgeDocument>> {
        const formData = new FormData();
        formData.append('file', file, filename);
        const response = await this.client.post<ApiResponse<KnowledgeDocument>>(
            `/knowledge/bases/${baseId}/documents/upload`,
            formData,
            { headers: { 'Content-Type': 'multipart/form-data' } }
        );
        return response.data;
    }

    /** 删除文档 */
    async deleteKnowledgeDocument(baseId: number, docId: number): Promise<ApiResponse<void>> {
        const response = await this.client.delete<ApiResponse<void>>(`/knowledge/bases/${baseId}/documents/${docId}`);
        return response.data;
    }

    /** RAG 语义搜索 */
    async ragSearch(baseId: number, query: string, topK: number = 5): Promise<ApiResponse<any>> {
        const response = await this.client.post<ApiResponse<any>>(`/knowledge/bases/${baseId}/search`, null, {
            params: { query, top_k: topK },
        });
        return response.data;
    }

    /** 知识问答 */
    async knowledgeQA(baseId: number, question: string, params?: { top_k?: number; model?: string }): Promise<ApiResponse<any>> {
        const response = await this.client.post<ApiResponse<any>>(`/knowledge/bases/${baseId}/qa`, null, {
            params: { question, ...params },
        });
        return response.data;
    }

    /** 生成研报 */
    async generateReport(baseId: number, params: { title: string; report_type?: string; query?: string; template_id?: number }): Promise<ApiResponse<GeneratedReport>> {
        const response = await this.client.post<ApiResponse<GeneratedReport>>(`/knowledge/bases/${baseId}/reports/generate`, null, { params });
        return response.data;
    }

    /** 获取研报列表 */
    async getReports(params?: { page?: number; per_page?: number; knowledge_base_id?: number }): Promise<ApiResponse<GeneratedReport[]>> {
        const response = await this.client.get<ApiResponse<GeneratedReport[]>>('/knowledge/reports', { params });
        return response.data;
    }

    /** 获取研报详情 */
    async getReportDetail(reportId: number): Promise<ApiResponse<GeneratedReport>> {
        const response = await this.client.get<ApiResponse<GeneratedReport>>(`/knowledge/reports/${reportId}`);
        return response.data;
    }

    /** 获取报告模板列表 */
    async getReportTemplates(params?: { page?: number; per_page?: number; template_type?: string }): Promise<ApiResponse<ReportTemplate[]>> {
        const response = await this.client.get<ApiResponse<ReportTemplate[]>>('/knowledge/templates', { params });
        return response.data;
    }

    /** 创建报告模板 */
    async createReportTemplate(template: { name: string; description?: string; template_type?: string; structure: Record<string, any> }): Promise<ApiResponse<ReportTemplate>> {
        const response = await this.client.post<ApiResponse<ReportTemplate>>('/knowledge/templates', template);
        return response.data;
    }

  // ═══════════════════════════════════════════════════════════════════════════
  // ⚙️ 工作流引擎 - 端点: /api/v2/workflow/
  // ═══════════════════════════════════════════════════════════════════════════

    /** 获取工作流定义列表 */
    async getWorkflowDefinitions(params?: { page?: number; per_page?: number; is_active?: boolean }): Promise<ApiResponse<WorkflowDefinition[]>> {
        const response = await this.client.get<ApiResponse<WorkflowDefinition[]>>('/workflow/definitions', { params });
        return response.data;
    }

    /** 获取工作流定义详情 */
    async getWorkflowDefinition(defId: number): Promise<ApiResponse<WorkflowDefinition>> {
        const response = await this.client.get<ApiResponse<WorkflowDefinition>>(`/workflow/definitions/${defId}`);
        return response.data;
    }

    /** 创建工作流定义 */
    async createWorkflowDefinition(def: { name: string; description?: string; graph_data: Record<string, any>; trigger_config?: Record<string, any> }): Promise<ApiResponse<WorkflowDefinition>> {
        const response = await this.client.post<ApiResponse<WorkflowDefinition>>('/workflow/definitions', def);
        return response.data;
    }

    /** 更新工作流定义 */
    async updateWorkflowDefinition(defId: number, updates: Partial<WorkflowDefinition>): Promise<ApiResponse<WorkflowDefinition>> {
        const response = await this.client.put<ApiResponse<WorkflowDefinition>>(`/workflow/definitions/${defId}`, updates);
        return response.data;
    }

    /** 删除工作流定义 */
    async deleteWorkflowDefinition(defId: number): Promise<ApiResponse<void>> {
        const response = await this.client.delete<ApiResponse<void>>(`/workflow/definitions/${defId}`);
        return response.data;
    }

    /** 激活工作流 */
    async activateWorkflow(defId: number): Promise<ApiResponse<void>> {
        const response = await this.client.post<ApiResponse<void>>(`/workflow/definitions/${defId}/activate`);
        return response.data;
    }

    /** 停用工作流 */
    async deactivateWorkflow(defId: number): Promise<ApiResponse<void>> {
        const response = await this.client.post<ApiResponse<void>>(`/workflow/definitions/${defId}/deactivate`);
        return response.data;
    }

    /** 手动执行工作流 */
    async executeWorkflow(defId: number, inputData?: Record<string, any>): Promise<ApiResponse<WorkflowExecution>> {
        const response = await this.client.post<ApiResponse<WorkflowExecution>>(`/workflow/definitions/${defId}/execute`, null, {
            params: { input_data: JSON.stringify(inputData || {}) },
        });
        return response.data;
    }

    /** 获取执行记录列表 */
    async getWorkflowExecutions(params?: { page?: number; per_page?: number; workflow_id?: number; status?: string }): Promise<ApiResponse<WorkflowExecution[]>> {
        const response = await this.client.get<ApiResponse<WorkflowExecution[]>>('/workflow/executions', { params });
        return response.data;
    }

    /** 获取执行记录详情 */
    async getWorkflowExecution(execId: number): Promise<ApiResponse<WorkflowExecution>> {
        const response = await this.client.get<ApiResponse<WorkflowExecution>>(`/workflow/executions/${execId}`);
        return response.data;
    }

    /** 取消执行 */
    async cancelWorkflowExecution(execId: number): Promise<ApiResponse<void>> {
        const response = await this.client.post<ApiResponse<void>>(`/workflow/executions/${execId}/cancel`);
        return response.data;
    }

    /** 获取工作流工具列表 */
    async getWorkflowTools(toolType?: string): Promise<ApiResponse<AgentTool[]>> {
        const response = await this.client.get<ApiResponse<AgentTool[]>>('/workflow/tools', {
            params: toolType ? { tool_type: toolType } : undefined,
        });
        return response.data;
    }

    /** 注册新工具 */
    async registerWorkflowTool(tool: { name: string; tool_type: string; description?: string; parameters?: Record<string, any>; implementation?: string }): Promise<ApiResponse<AgentTool>> {
        const response = await this.client.post<ApiResponse<AgentTool>>('/workflow/tools', tool);
        return response.data;
    }

    /** 获取触发器列表 */
    async getTriggers(): Promise<ApiResponse<Trigger[]>> {
        const response = await this.client.get<ApiResponse<Trigger[]>>('/workflow/triggers');
        return response.data;
    }

    /** 创建 cron 触发器 */
    async createCronTrigger(params: { workflow_id: number; cron_expression: string; timezone?: string }): Promise<ApiResponse<Trigger>> {
        const response = await this.client.post<ApiResponse<Trigger>>('/workflow/triggers/cron', null, { params });
        return response.data;
    }

    /** 创建事件触发器 */
    async createEventTrigger(params: { workflow_id: number; event_type: string; filter_expression?: string }): Promise<ApiResponse<Trigger>> {
        const response = await this.client.post<ApiResponse<Trigger>>('/workflow/triggers/event', null, { params });
        return response.data;
    }

    /** 删除触发器 */
    async deleteTrigger(triggerId: number): Promise<ApiResponse<void>> {
        const response = await this.client.delete<ApiResponse<void>>(`/workflow/triggers/${triggerId}`);
        return response.data;
    }
}

// ============================================================================
// 默认导出
// ============================================================================

export default FastBlogSDK;
