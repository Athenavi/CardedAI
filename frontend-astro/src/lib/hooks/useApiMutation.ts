'use client';

import {useMutation, useQueryClient, type UseMutationResult} from '@tanstack/react-query';
import {useToast} from '@/components/ui/toast-provider';
import {apiClient} from '@/lib/api/base-client';
import type {ApiResponse} from '@/lib/api/base-types';

/**
 * useApiMutation 配置选项
 */
export interface UseApiMutationOptions<TData = any, TVariables = void> {
  /** mutation 函数 */
  mutationFn: (variables: TVariables) => Promise<ApiResponse<TData>>;
  /** 成功时显示的消息（静态字符串或从响应中提取） */
  successMessage?: string | ((data: ApiResponse<TData>, variables: TVariables) => string);
  /** 失败时显示的消息（默认从 response.error 提取） */
  errorMessage?: string | ((error: unknown) => string);
  /** 成功后需要失效的 queryKey 列表 */
  invalidateQueries?: (string | number)[][];
  /** 成功后的额外回调 */
  onSuccess?: (data: ApiResponse<TData>, variables: TVariables) => void;
  /** 失败后的额外回调 */
  onError?: (error: unknown, variables: TVariables) => void;
  /** 成功后的额外操作（如关闭弹窗） */
  onSettled?: () => void;
}

/**
 * 统一的 API mutation 封装 hook
 * - 自动通过 useToast 显示成功/失败通知
 * - 自动处理 ApiResponse 的 success/error 判断
 * - 自动失效 React Query 缓存
 *
 * @example
 * const createMut = useApiMutation({
 *   mutationFn: (data) => apiClient.post('/articles', data),
 *   successMessage: '文章已创建',
 *   invalidateQueries: [['articles']],
 *   onSuccess: () => setShowForm(false),
 * });
 *
 * // 使用: createMut.mutate(formData)
 */
export function useApiMutation<TData = any, TVariables = void>(
  options: UseApiMutationOptions<TData, TVariables>
): UseMutationResult<ApiResponse<TData>, unknown, TVariables> {
  const toast = useToast();
  const qc = useQueryClient();

  return useMutation({
    mutationFn: options.mutationFn,
    onSuccess: (data, variables) => {
      if (data.success) {
        const msg = typeof options.successMessage === 'function'
          ? options.successMessage(data, variables)
          : options.successMessage || data.message;
        if (msg) toast.success(msg);
        if (options.invalidateQueries) {
          for (const key of options.invalidateQueries) {
            qc.invalidateQueries({queryKey: key});
          }
        }
        options.onSuccess?.(data, variables);
      } else {
        const msg = data.error || '操作失败';
        toast.error(msg);
        options.onError?.(new Error(msg), variables);
      }
    },
    onError: (error, variables) => {
      const msg = typeof options.errorMessage === 'function'
        ? options.errorMessage(error)
        : options.errorMessage || (error instanceof Error ? error.message : '网络异常');
      toast.error(msg);
      options.onError?.(error, variables);
    },
    onSettled: options.onSettled,
  });
}

/**
 * 便捷的快捷方法：创建 POST mutation
 */
export function useCreateMutation<TData = any, TVariables = void>(
  path: string,
  queryKey: (string | number)[],
  options?: Omit<UseApiMutationOptions<TData, TVariables>, 'mutationFn' | 'invalidateQueries'>
) {
  return useApiMutation<TData, TVariables>({
    mutationFn: (data) => apiClient.post<TData>(path, data as any),
    invalidateQueries: [queryKey],
    ...options,
  });
}

/**
 * 便捷的快捷方法：创建 PUT mutation
 */
export function useUpdateMutation<TData = any, TVariables = { id: number; data: any }>(
  pathBuilder: (id: number) => string,
  queryKey: (string | number)[],
  options?: Omit<UseApiMutationOptions<TData, TVariables>, 'mutationFn' | 'invalidateQueries'>
) {
  return useApiMutation<TData, TVariables>({
    mutationFn: (vars) => apiClient.put<TData>(pathBuilder((vars as any).id), (vars as any).data ?? vars),
    invalidateQueries: [queryKey],
    ...options,
  });
}

/**
 * 便捷的快捷方法：创建 DELETE mutation
 */
export function useDeleteMutation<TData = any>(
  pathBuilder: (id: number) => string,
  queryKey: (string | number)[],
  options?: Omit<UseApiMutationOptions<TData, number>, 'mutationFn' | 'invalidateQueries'>
) {
  return useApiMutation<TData, number>({
    mutationFn: (id) => apiClient.delete<TData>(pathBuilder(id)),
    invalidateQueries: [queryKey],
    successMessage: options?.successMessage || '已删除',
    ...options,
  });
}
