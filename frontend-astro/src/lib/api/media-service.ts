// Media service for Next.js frontend
import {apiClient} from './base-client';
import type {ApiResponse, MediaFile} from './base-types';

// 定义初始化分块上传响应的类型
interface ChunkUploadInitResponse {
    upload_id: string;
    filename: string;
    total_size: number;
    total_chunks: number;
    chunk_size: number;
    data?: {
        upload_id?: string;
    };
}

// 定义媒体响应类型
export interface MediaResponse {
    media_items: MediaFile[];
    users: { id: number; username: string }[];
    pagination: {
        current_page: number;
        pages?: number;
        total: number;
        has_prev: boolean;
        has_next: boolean;
        per_page: number;
    };
    stats?: {
        image_count: number;
        video_count: number;
        storage_used: string;
        storage_total: string;
        storage_percentage: number;
        canBeUploaded: boolean;
        totalUsed: number;
    };
}

/**
 * 媒体文件服务类
 * 提供媒体文件的上传、下载、删除等操作
 */
export class MediaService {
    private static readonly CHUNK_SIZE = 5 * 1024 * 1024; // 5MB 分块阈值

    static async getMediaFiles(params?: {
        media_type?: string;
        page?: number;
        q?: string;
        per_page?: number;
        folder_name?: string | null;
    }): Promise<ApiResponse<MediaResponse>> {
        // 过滤掉无效参数
        const validParams: any = {};
        if (params?.media_type) validParams.media_type = params.media_type;
        if (params?.page) validParams.page = params.page;
        if (params?.q) validParams.q = params.q;
        if (params?.per_page) validParams.per_page = params.per_page;
        if (params?.folder_name) validParams.folder_name = params.folder_name;

        return apiClient.get('/media/files', Object.keys(validParams).length > 0 ? validParams : undefined);
    }

    static async deleteMediaFile(fileIdList: string | number[]): Promise<ApiResponse<{ message: string }>> {
        const ids = Array.isArray(fileIdList) ? fileIdList.join(',') : fileIdList;
        return apiClient.delete(`/media/?file-id-list=${ids}`);
    }

    static async uploadMediaFile(file: File): Promise<ApiResponse<{ files?: MediaFile[], message?: string }>> {
        // 验证文件
        if (!file) {
            return {success: false, error: '文件不能为空', requires_auth: false};
        }

        // 验证文件类型 - 扩展支持的文件类型
        const allowedTypes = [
            // 图片格式
            'image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/webp', 'image/svg+xml', 'image/tiff',
            // 视频格式
            'video/mp4', 'video/mpeg', 'video/quicktime', 'video/x-msvideo', 'video/webm', 'video/x-matroska',
            // 音频格式
            'audio/mpeg', 'audio/wav', 'audio/x-wav', 'audio/flac', 'audio/aac', 'audio/mp4', 'audio/ogg', 'audio/mp3',
            // 文档格式
            'application/pdf',
            'application/msword',  // .doc
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  // .docx
            'application/vnd.ms-excel',  // .xls
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  // .xlsx
            'application/vnd.ms-powerpoint',  // .ppt
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',  // .pptx
            'text/plain',  // .txt
            'text/markdown',  // .md
            'text/csv',  // .csv
            'text/html',  // .html
            // 压缩格式
            'application/zip',
            'application/x-rar-compressed',
            'application/x-7z-compressed',
            'application/gzip',
            'application/x-tar',
            'application/x-bzip2',
            // 其他常见格式
            'application/json',
            'application/xml',
            'application/octet-stream',  // 通用二进制文件
        ];

        // 检查文件类型是否在允许列表中，或者是否是常见的媒体类型
        const isAllowedType = allowedTypes.includes(file.type) ||
            file.type.startsWith('image/') ||
            file.type.startsWith('video/') ||
            file.type.startsWith('audio/') ||
            file.type.startsWith('text/') ||
            file.type.startsWith('application/');

        if (!isAllowedType) {
            console.warn(`⚠️ 文件类型可能不受支持: ${file.type}`);
            // 不直接拒绝，只是警告，让后端进行最终验证
        }

        // 判断文件大小，决定使用哪种上传方式
        if (file.size <= MediaService.CHUNK_SIZE) {
            // 小文件直接上传
            const formData = new FormData();
            formData.append('file', file);

            return apiClient.request('/media/upload', {
                method: 'POST',
                body: formData,
                credentials: 'include',
            });
        } else {
            // 大文件使用分块上传
            return this.chunkedUpload(file, MediaService.CHUNK_SIZE);
        }
    }

    // 带进度的上传方法
    static async uploadMediaFileWithProgress(file: File, onProgress?: (percent: number, status: string) => void): Promise<ApiResponse<{
        files?: MediaFile[],
        message?: string
    }>> {
        if (file.size <= MediaService.CHUNK_SIZE) {
            // 小文件直接上传，使用 fetch API 和进度模拟
            return new Promise(async (resolve, reject) => {
                try {
                    // 创建一个模拟进度的函数
                    const simulateProgress = () => {
                        let simulatedProgress = 0;
                        const interval = setInterval(() => {
                            simulatedProgress += Math.random() * 10; // 随机增加进度
                            if (simulatedProgress >= 95) {
                                simulatedProgress = 95; // 留5%给完成处理
                            }

                            if (onProgress) {
                                onProgress(Math.floor(simulatedProgress), `正在上传: ${file.name} (${Math.floor(simulatedProgress)}%)`);
                            }
                        }, 200);

                        return interval;
                    };

                    const progressInterval = simulateProgress();

                    // 准备表单数据
                    const formData = new FormData();
                    formData.append('file', file);

                    // 发送请求 - 使用 apiClient 保证认证信息正确传递
                    const response = await apiClient.request('/media/upload', {
                        method: 'POST',
                        body: formData,
                        credentials: 'include',
                    });

                    clearInterval(progressInterval);

                    // 更新进度到100%
                    if (onProgress) {
                        onProgress(100, `已完成上传: ${file.name}`);
                    }

                    // 直接返回apiClient的响应，它已经是ApiResponse格式
                    resolve(response as ApiResponse<{ files?: MediaFile[], message?: string }>);
                } catch (error) {
                    reject(error);
                }
            });
        } else {
            // 大文件使用分块上传，同时报告进度
            return this.chunkedUploadWithProgress(file, MediaService.CHUNK_SIZE, onProgress);
        }
    }

    /**
     * 移动媒体文件到文件夹
     * @param mediaIds 媒体文件ID列表（可以是单个ID的数组）
     * @param folderPath 目标文件夹路径（如 "Photos/2024"），null表示移动到根目录
     */
    static async moveMediaFiles(
        mediaIds: number[],
        folderPath: string | null
    ): Promise<ApiResponse<{ moved_count: number }>> {
        return apiClient.post('/media/folders/move-media', {
            media_ids: mediaIds,
            folder_path: folderPath
        });
    }

    /**
     * 更新媒体文件的分类
     * @param mediaId 媒体文件ID
     * @param category 分类名称
     */
    static async updateMediaCategory(
        mediaId: number,
        category: string
    ): Promise<ApiResponse<{ message: string }>> {
        return apiClient.put(`/media/detail/${mediaId}`, {
            category: category
        });
    }

    /**
     * 更新媒体文件的标签
     * @param mediaId 媒体文件ID
     * @param tags 标签数组（最多5个）
     * @param mode 模式：'replace' 替换全部，'add' 追加（默认）
     */
    static async updateMediaTags(
        mediaId: number,
        tags: string[],
        mode: 'replace' | 'add' = 'replace'
    ): Promise<ApiResponse<{ message: string; tags: string[] }>> {
        return apiClient.post(`/media/${mediaId}/tags`, {
            tags: tags,
            mode: mode
        });
    }

    // 带进度的分块上传方法
    private static async chunkedUploadWithProgress(file: File, chunkSize: number = MediaService.CHUNK_SIZE, onProgress?: (percent: number, status: string) => void): Promise<ApiResponse<{
        files?: MediaFile[],
        message?: string
    }>> {
        const totalChunks = Math.ceil(file.size / chunkSize);
        const fileName = file.name;

        // 首先初始化上传任务
        const initResult = await apiClient.post<ChunkUploadInitResponse>('/media/upload/chunked/init', {
            filename: fileName,
            total_size: file.size,
            total_chunks: totalChunks,
        });

        if (!initResult.success) {
            return initResult as ApiResponse<{ files?: MediaFile[], message?: string }>;
        }

        const uploadId = initResult.data?.upload_id || (initResult as { upload_id?: string }).upload_id;

        // 检查 uploadId 是否存在
        if (!uploadId) {
            return {
                success: false,
                error: '无法获取上传ID',
                message: '初始化上传失败',
                requires_auth: false
            };
        }

        // 逐个上传分块
        for (let i = 0; i < totalChunks; i++) {
            const start = i * chunkSize;
            const end = Math.min(start + chunkSize, file.size);
            const chunk = file.slice(start, end);

            // 报告进度
            const progressPercent = ((i) / totalChunks) * 100;
            if (onProgress) {
                onProgress(progressPercent, `正在上传分块 ${i + 1}/${totalChunks}: ${file.name}`);
            }

            const chunkHash = await this.calculateChunkHash(chunk); // 使用实际内容哈希值

            const formData = new FormData();
            // 直接附加 File/Blob 对象，不指定文件名，让浏览器自动处理
            formData.append('chunk', chunk);
            formData.append('upload_id', uploadId);
            formData.append('chunk_index', i.toString());
            formData.append('chunk_hash', chunkHash);

            const chunkResult = await apiClient.request(`/media/upload/chunked/chunk`, {
                method: 'POST',
                body: formData,
            });

            if (!chunkResult.success) {
                // 如果上传分块失败，取消上传
                await this.cancelChunkedUpload(uploadId);
                return chunkResult as ApiResponse<{ files?: MediaFile[], message?: string }>;
            }
        }

        // 报告接近完成的进度
        if (onProgress) {
            onProgress(95, `正在完成上传: ${file.name}`);
        }

        // 计算文件哈希并完成上传
        const fileHash = await this.calculateFileHash(file);

        const completeResult = await apiClient.post('/media/upload/chunked/complete', {
            upload_id: uploadId,
            file_hash: fileHash,
            mime_type: file.type,
        });

        // 完成进度
        if (onProgress) {
            onProgress(100, `已完成上传: ${file.name}`);
        }

        return completeResult as ApiResponse<{ files?: MediaFile[], message?: string }>;
    }

    // 分块上传方法
    private static async chunkedUpload(file: File, chunkSize: number = MediaService.CHUNK_SIZE): Promise<ApiResponse<{
        files?: MediaFile[],
        message?: string
    }>> {
        const totalChunks = Math.ceil(file.size / chunkSize);
        const fileName = file.name;

        // 首先初始化上传任务
        const initResult = await apiClient.post<ChunkUploadInitResponse>('/media/upload/chunked/init', {
            filename: fileName,
            total_size: file.size,
            total_chunks: totalChunks,
        });

        if (!initResult.success) {
            return initResult as ApiResponse<{ files?: MediaFile[], message?: string }>;
        }

        const uploadId = initResult.data?.upload_id || (initResult as { upload_id?: string }).upload_id;

        // 检查 uploadId 是否存在
        if (!uploadId) {
            return {
                success: false,
                error: '无法获取上传ID',
                message: '初始化上传失败',
                requires_auth: false
            };
        }

        // 逐个上传分块
        for (let i = 0; i < totalChunks; i++) {
            const start = i * chunkSize;
            const end = Math.min(start + chunkSize, file.size);
            const chunk = file.slice(start, end);

            // 为简单起见，我们暂不计算哈希值，直接上传分块
            // 在实际实现中，可以使用web worker或专用的哈希库来计算SHA256
            const chunkHash = await this.calculateChunkHash(chunk); // 使用实际内容哈希值

            const formData = new FormData();
            // 直接附加 File/Blob 对象，不指定文件名，让浏览器自动处理
            formData.append('chunk', chunk);
            formData.append('upload_id', uploadId);
            formData.append('chunk_index', i.toString());
            formData.append('chunk_hash', chunkHash);

            const chunkResult = await apiClient.request(`/media/upload/chunked/chunk`, {
                method: 'POST',
                body: formData,
                credentials: 'include',
            });

            if (!chunkResult.success) {
                // 如果上传分块失败，取消上传
                await this.cancelChunkedUpload(uploadId);
                return chunkResult as ApiResponse<{ files?: MediaFile[], message?: string }>;
            }
        }

        // 完成分块上传
        // 注意：在浏览器环境中计算大文件的SHA256可能会很慢，这里仅作演示
        // 在实际应用中，你可能需要在服务端计算哈希值
        const fileHash = await this.calculateFileHash(file);

        const completeResult = await apiClient.post('/media/upload/chunked/complete', {
            upload_id: uploadId,
            file_hash: fileHash,
            mime_type: file.type,
        });

        return completeResult as ApiResponse<{ files?: MediaFile[], message?: string }>;
    }

    // 取消分块上传
    private static async cancelChunkedUpload(uploadId: string): Promise<void> {
        try {
            await apiClient.post('/media/upload/chunked/cancel', {upload_id: uploadId});
        } catch (error) {
            console.error('取消上传失败:', error);
        }
    }

    // 计算文件哈希值（在浏览器中计算SHA256）
    private static async calculateFileHash(file: File): Promise<string> {
        // 对于大文件，我们需要使用流式处理来计算SHA256哈希
        // 这样可以避免将整个文件加载到内存中

        // 使用Web Crypto API来计算完整的文件哈希
        if (crypto && crypto.subtle && crypto.subtle.digest) {
            try {
                // 读取整个文件内容
                const fileBuffer = await file.arrayBuffer();
                const hashBuffer = await crypto.subtle.digest('SHA-256', fileBuffer);
                const hashArray = Array.from(new Uint8Array(hashBuffer));
                return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
            } catch (error) {
                console.error('哈希计算失败:', error);
                // 如果Web Crypto API不可用或出错，抛出错误
                throw new Error('无法计算文件哈希: ' + error);
            }
        } else {
            // Web Crypto API不可用时的降级处理
            throw new Error('浏览器不支持加密API，无法计算文件哈希');
        }
    }

    // 计算分块哈希值（在浏览器中计算SHA256）
    private static async calculateChunkHash(chunk: Blob): Promise<string> {
        // 使用Web Crypto API来计算分块的SHA256哈希值
        if (crypto && crypto.subtle && crypto.subtle.digest) {
            try {
                const arrayBuffer = await chunk.arrayBuffer();
                const hashBuffer = await crypto.subtle.digest('SHA-256', arrayBuffer);
                const hashArray = Array.from(new Uint8Array(hashBuffer));
                return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
            } catch (error) {
                console.error('分块哈希计算失败:', error);
                // 如果Web Crypto API不可用或出错，抛出错误
                throw new Error('无法计算分块哈希: ' + error);
            }
        } else {
            // Web Crypto API不可用时的降级处理
            throw new Error('浏览器不支持加密API，无法计算分块哈希');
        }
    }
}