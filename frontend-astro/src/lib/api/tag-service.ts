// Tag service — 标签列表 / 标签建议 / 标签文章
import {apiClient} from './base-client';
import type {ApiResponse, Pagination, TagSummary, Article} from '@/lib/api/base-types';

export interface TagListResult {
  tags: TagSummary[];
  total_tags: number;
  pagination: Pagination;
}

export interface TagArticlesResult {
  tag_name: string;
  articles: Array<Partial<Article> & {
    id: number;
    title: string;
    slug: string;
    author?: { id: number; username: string };
  }>;
}

export class TagService {
  /** 标签列表（含文章计数，支持排序 / 搜索 / 分页） */
  static async getTags(params?: {
    page?: number;
    per_page?: number;
    sort?: 'count' | 'name';
    q?: string;
  }): Promise<ApiResponse<TagListResult>> {
    return apiClient.get('/tags', params);
  }

  /** 标签建议（后端返回裸字符串数组） */
  static async getTagSuggestions(query: string): Promise<string[]> {
    const response: any = await apiClient.get('/tags/suggest', {q: query});
    if (Array.isArray(response)) return response;
    if (Array.isArray(response?.data)) return response.data;
    return [];
  }

  /** 某标签下的文章列表 */
  static async getArticlesByTag(tag: string): Promise<ApiResponse<TagArticlesResult>> {
    return apiClient.get(`/articles/tag/${encodeURIComponent(tag)}`);
  }
}
