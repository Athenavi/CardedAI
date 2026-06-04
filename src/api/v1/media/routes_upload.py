"""
媒体上传（普通上传、分块上传）
"""
import hashlib

from datetime import datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from shared.services.notifications.webhook_service import webhook_service
from src.auth import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db
from src.setting import app_config
from src.utils.upload.public_upload import ChunkedUploadProcessor, FileProcessor, process_single_file

router = APIRouter()
from src.unified_logger import default_logger as logger


# ---------- 普通上传 ----------
@router.post("/upload")
async def upload_media_file(
        request: Request,
        current_user_obj=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    try:
        upload_limit = getattr(app_config, 'UPLOAD_LIMIT', 10 * 1024 * 1024)
        allowed_mimes = getattr(app_config, 'ALLOWED_MIMES', [
            # 图片格式
            'image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/webp', 'image/svg+xml', 'image/tiff',
            # 视频格式
            'video/mp4', 'video/mpeg', 'video/quicktime', 'video/x-msvideo', 'video/webm', 'video/x-matroska',
            # 音频格式
            'audio/mpeg', 'audio/wav', 'audio/flac', 'audio/aac', 'audio/ogg', 'audio/mp3', 'audio/x-wav',
            # 文档格式
            'application/pdf',
            'application/msword',  # .doc
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # .docx
            'application/vnd.ms-excel',  # .xls
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
            'application/vnd.ms-powerpoint',  # .ppt
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',  # .pptx
            'text/plain',  # .txt
            'text/markdown',  # .md
            'text/csv',  # .csv
            'text/html',  # .html
            # 压缩文件格式
            'application/zip',
            'application/x-rar-compressed',
            'application/x-7z-compressed',
            'application/gzip',
            'application/x-tar',
            'application/x-bzip2',
            # 其他常见格式
            'application/json',
            'application/xml',
            'application/octet-stream',  # 通用二进制文件
        ])

        form = await request.form()
        files = form.getlist('file')
        if not files:
            return JSONResponse({'success': False, 'message': '未找到上传的文件'}, status_code=400)

        results = []
        for file in files:
            if hasattr(file, 'filename') and hasattr(file, 'read'):
                try:
                    file_data = await file.read()
                    result = await _process_single_file(
                        current_user_obj.id, file_data, file.filename,
                        upload_limit, allowed_mimes, db
                    )
                    results.append(result)
                except Exception as e:
                    logger.error(f"处理文件 {file.filename} 失败: {str(e)}")
                    results.append({'success': False, 'error': str(e)})

        successful = [r for r in results if r.get('success')]
        if successful:
            # 触发 Webhook 事件
            try:
                for file_result in successful:
                    if file_result.get('data'):
                        file_data = file_result['data']
                        await webhook_service.trigger_event(
                            'media.uploaded',
                            {
                                'file_id': file_data.get('id'),
                                'filename': file_data.get('filename'),
                                'file_type': file_data.get('mime_type'),
                                'file_size': file_data.get('size'),
                                'url': file_data.get('url'),
                                'uploaded_by': current_user_obj.id,
                                'uploaded_at': datetime.now().isoformat(),
                            },
                            db=db
                        )
            except Exception as webhook_err:
                logger.error(f"Webhook trigger failed: {webhook_err}")
            
            return JSONResponse({'success': True, 'message': '上传成功', 'data': {'files': successful}})
        errors = '; '.join([r.get('error', '未知错误') for r in results if not r.get('success')])
        return JSONResponse({'success': False, 'message': '文件上传失败', 'error': errors}, status_code=400)
    except Exception as e:
        logger.error(f"上传媒体文件错误: {str(e)}", exc_info=True)
        return JSONResponse({'success': False, 'message': '服务器内部错误', 'error': str(e)}, status_code=500)


async def _process_single_file(user_id, file_data, filename, allowed_size, allowed_mimes, db):
    allowed_set = set(str(m) for m in allowed_mimes) if allowed_mimes else {
        # 图片格式
        'image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/webp', 'image/svg+xml', 'image/tiff',
        # 视频格式
        'video/mp4', 'video/mpeg', 'video/quicktime', 'video/x-msvideo', 'video/webm', 'video/x-matroska',
        # 音频格式
        'audio/mpeg', 'audio/wav', 'audio/flac', 'audio/aac', 'audio/ogg', 'audio/mp3', 'audio/x-wav',
        # 文档格式
        'application/pdf',
        'application/msword',  # .doc
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # .docx
        'application/vnd.ms-excel',  # .xls
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
        'application/vnd.ms-powerpoint',  # .ppt
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',  # .pptx
        'text/plain',  # .txt
        'text/markdown',  # .md
        'text/csv',  # .csv
        'text/html',  # .html
        # 压缩文件格式
        'application/zip',
        'application/x-rar-compressed',
        'application/x-7z-compressed',
        'application/gzip',
        'application/x-tar',
        'application/x-bzip2',
        # 其他常见格式
        'application/json',
        'application/xml',
        'application/octet-stream',  # 通用二进制文件
    }
    
    # 调试日志
    logger.info(f"处理文件: {filename}")
    logger.info(f"允许的 MIME 类型数量: {len(allowed_set)}")
    
    processor = FileProcessor(user_id, allowed_mimes=allowed_set, allowed_size=allowed_size)
    is_valid, validation_result = processor.validate_file(file_data, filename)
    
    if not is_valid:
        logger.error(f"文件验证失败: {filename} - {validation_result}")
        return {'success': False, 'error': validation_result}
    
    logger.info(f"文件验证通过: {filename}")
    
    try:
        result = await process_single_file(processor, file_data, filename, db)
        logger.info(f"文件处理成功: {filename}")
        return result
    except Exception as e:
        logger.error(f"文件处理失败: {filename} - {str(e)}", exc_info=True)
        return {'success': False, 'error': str(e)}


# ---------- 分块上传 ----------
@router.post('/upload/chunked/init')
async def chunked_upload_init(
        request: Request,
        current_user_obj=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    try:
        # 读取原始请求体用于调试
        raw_body = await request.body()
        logger.info(f"分块上传初始化 - 原始请求体: {raw_body[:200]}")
        
        # 尝试解析 JSON
        try:
            data = await request.json()
            logger.info(f"分块上传初始化请求: {data}")
        except Exception as json_err:
            logger.error(f"JSON 解析失败: {json_err}")
            return JSONResponse({
                'success': False, 
                'error': f'JSON 解析失败: {str(json_err)}',
                'debug_raw_body': raw_body.decode('utf-8', errors='ignore')[:200]
            }, status_code=400)
        
        filename = data.get('filename')
        total_size = data.get('total_size')
        total_chunks = data.get('total_chunks')
        file_hash = data.get('file_hash')
        existing_upload_id = data.get('existing_upload_id')
        
        logger.info(f"   - filename: {filename} (type: {type(filename).__name__})")
        logger.info(f"   - total_size: {total_size} (type: {type(total_size).__name__})")
        logger.info(f"   - total_chunks: {total_chunks} (type: {type(total_chunks).__name__})")
        logger.info(f"   - file_hash: {file_hash}")
        logger.info(f"   - existing_upload_id: {existing_upload_id}")
        
        if not all([filename, total_size, total_chunks]):
            logger.error(f"缺少必要参数: filename={filename}, total_size={total_size}, total_chunks={total_chunks}")
            return JSONResponse({
                'success': False, 
                'error': '缺少必要参数',
                'received': {
                    'filename': filename,
                    'total_size': total_size,
                    'total_chunks': total_chunks
                }
            }, status_code=400)
        
        logger.info(f"参数验证通过，开始初始化上传任务...")
        processor = ChunkedUploadProcessor(current_user_obj.id)
        result = await processor.init_upload(filename, total_size, total_chunks, file_hash, existing_upload_id, db)
        
        if result.get('success'):
            logger.info(f"分块上传初始化成功: upload_id={result.get('upload_id')}")
        else:
            logger.error(f"分块上传初始化失败: {result.get('error')}")
        
        return JSONResponse(result, status_code=200 if result.get('success') else 400)
    except Exception as e:
        logger.error(f"分块上传初始化异常: {str(e)}", exc_info=True)
        return JSONResponse({'success': False, 'error': str(e)}, status_code=500)


@router.post('/upload/chunked/chunk')
async def chunked_upload_chunk(
        request: Request,
        current_user_obj=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    form = await request.form()
    upload_id = form.get('upload_id')
    chunk_index_str = form.get('chunk_index')
    chunk_hash = form.get('chunk_hash')
    if not upload_id or chunk_index_str is None or not chunk_hash:
        return JSONResponse({'success': False, 'error': '缺少必要参数'}, status_code=400)
    try:
        chunk_index = int(chunk_index_str)
    except (ValueError, TypeError):
        return JSONResponse({'success': False, 'error': 'chunk_index必须是数字'}, status_code=400)

    chunk_data = None
    if 'chunk' in form:
        chunk_item = form.get('chunk')
        if hasattr(chunk_item, 'read'):
            chunk_data = await chunk_item.read()
        elif isinstance(chunk_item, bytes):
            chunk_data = chunk_item
        elif isinstance(chunk_item, str):
            chunk_data = chunk_item.encode('utf-8')
    if chunk_data is None:
        chunk_data = await request.body()
    if not chunk_data:
        return JSONResponse({'success': False, 'error': '分块数据为空'}, status_code=400)

    if hashlib.sha256(chunk_data).hexdigest() != chunk_hash:
        return JSONResponse({'success': False, 'error': '分块哈希验证失败'}, status_code=400)

    processor = ChunkedUploadProcessor(current_user_obj.id)
    result = await processor.upload_chunk(upload_id, chunk_index, chunk_data, chunk_hash, db)
    return JSONResponse(result, status_code=200 if result.get('success') else 400)


@router.post('/upload/chunked/complete')
async def chunked_upload_complete(
        request: Request,
        current_user_obj=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    data = await request.json()
    upload_id = data.get('upload_id')
    file_hash = data.get('file_hash')
    mime_type = data.get('mime_type')
    if not all([upload_id, file_hash, mime_type]):
        return JSONResponse({'success': False, 'error': '缺少必要参数'}, status_code=400)
    processor = ChunkedUploadProcessor(current_user_obj.id)
    result = await processor.complete_upload(upload_id, file_hash, mime_type, db)
    return JSONResponse(result, status_code=200 if result.get('success') else 400)


@router.get('/upload/chunked/progress')
async def chunked_upload_progress(
        request: Request,
        current_user_obj=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    upload_id = request.query_params.get('upload_id')
    if not upload_id:
        return JSONResponse({'success': False, 'error': '缺少upload_id'}, status_code=400)
    processor = ChunkedUploadProcessor(current_user_obj.id)
    result = await processor.get_upload_progress(upload_id, db)
    return JSONResponse(result, status_code=200 if result.get('success') else 400)


@router.get('/upload/chunked/chunks')
async def chunked_upload_chunks(
        request: Request,
        current_user_obj=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    upload_id = request.query_params.get('upload_id')
    if not upload_id:
        return JSONResponse({'success': False, 'error': '缺少upload_id'}, status_code=400)
    processor = ChunkedUploadProcessor(current_user_obj.id)
    result = await processor.get_uploaded_chunks(upload_id, db)
    return JSONResponse(result, status_code=200 if result.get('success') else 400)


@router.post('/upload/chunked/cancel')
async def chunked_upload_cancel(
        request: Request,
        current_user_obj=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    data = await request.json()
    upload_id = data.get('upload_id')
    if not upload_id:
        return JSONResponse({'success': False, 'error': '缺少upload_id'}, status_code=400)
    processor = ChunkedUploadProcessor(current_user_obj.id)
    result = await processor.cancel_upload(upload_id, db)
    return JSONResponse(result, status_code=200 if result.get('success') else 400)
