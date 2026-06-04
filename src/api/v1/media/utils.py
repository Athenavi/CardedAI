"""
媒体包工具函数
"""

import tempfile
from pathlib import Path
from typing import Optional

import aioboto3
import aiofiles
from botocore.exceptions import ClientError
from fastapi import HTTPException
from fastapi.responses import FileResponse, StreamingResponse, Response

from src.setting import app_config

from src.unified_logger import default_logger as logger

PREVIEWABLE_TYPES = {
    'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml',
    'video/mp4', 'video/webm', 'video/ogg',
    'audio/mpeg', 'audio/ogg', 'audio/wav',
    'application/pdf',
    'text/plain', 'text/html', 'text/css', 'text/javascript',
    'application/json'
}


async def handle_local_file(
        file_path: Path,
        mime_type: str,
        filename: str,
        range_header: Optional[str],
        headers: dict
) -> Response:
    file_size = file_path.stat().st_size
    if range_header:
        return await handle_range_request(file_path, range_header, file_size, mime_type, headers)
    
    # 创建 FileResponse
    response = FileResponse(
        path=str(file_path),
        media_type=mime_type,
        filename=filename
    )
    
    # 手动设置所有自定义 headers（必须在创建后设置）
    for key, value in headers.items():
        response.headers[key] = value
    
    return response


async def handle_range_request(
        file_path: Path,
        range_header: str,
        file_size: int,
        mime_type: str,
        headers: dict
) -> Response:
    range_bytes = range_header.replace("bytes=", "").split("-")
    start = int(range_bytes[0]) if range_bytes[0] else 0
    end = int(range_bytes[1]) if range_bytes[1] else file_size - 1
    if end >= file_size:
        end = file_size - 1
    content_length = end - start + 1
    headers.update({
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Content-Length": str(content_length)
    })

    async def file_iterator():
        async with aiofiles.open(file_path, 'rb') as f:
            await f.seek(start)
            remaining = content_length
            while remaining > 0:
                chunk = await f.read(min(8192, remaining))
                if not chunk:
                    break
                yield chunk
                remaining -= len(chunk)

    # 创建 StreamingResponse
    response = StreamingResponse(
        file_iterator(),
        status_code=206,
        media_type=mime_type
    )
        
    # 手动设置所有自定义 headers
    for key, value in headers.items():
        response.headers[key] = value
        
    return response


async def handle_s3_streaming(
        s3_path: str,
        mime_type: str,
        filename: str,
        range_header: Optional[str],
        headers: dict,
        media_hash: str
) -> Response:
    s3_url = s3_path.replace("s3://", "")
    bucket_name, object_key = s3_url.split("/", 1)
    cache_path = Path(f"cache/objects/{media_hash}")
    if cache_path.exists() and not range_header:
        return await handle_local_file(cache_path, mime_type, filename, range_header, headers)
    if range_header:
        return await stream_s3_range(bucket_name, object_key, mime_type, range_header, headers)
    return await stream_and_cache_s3(bucket_name, object_key, mime_type, filename, headers, cache_path)


async def stream_s3_range(
        bucket_name: str,
        object_key: str,
        mime_type: str,
        range_header: str,
        headers: dict
) -> Response:
    try:
        session = aioboto3.Session()
        async with session.client('s3') as s3_client:
            head_response = await s3_client.head_object(Bucket=bucket_name, Key=object_key)
            file_size = head_response['ContentLength']
            range_bytes = range_header.replace("bytes=", "").split("-")
            start = int(range_bytes[0]) if range_bytes[0] else 0
            end = int(range_bytes[1]) if range_bytes[1] else file_size - 1
            if end >= file_size:
                end = file_size - 1
            content_length = end - start + 1
            range_str = f"bytes={start}-{end}"
            headers.update({
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Content-Length": str(content_length)
            })
            response = await s3_client.get_object(Bucket=bucket_name, Key=object_key, Range=range_str)

            async def s3_stream_iterator():
                async with response['Body'] as stream:
                    async for chunk in stream.iter_chunks(chunk_size=8192):
                        yield chunk

            # 创建 StreamingResponse
            response = StreamingResponse(
                s3_stream_iterator(),
                status_code=206,
                media_type=mime_type
            )
                        
            # 手动设置所有自定义 headers
            for key, value in headers.items():
                response.headers[key] = value
                        
            return response
    except ClientError as e:
        logger.error(f"S3范围请求失败: {str(e)}")
        raise HTTPException(status_code=500, detail="文件获取失败")


async def stream_and_cache_s3(
        bucket_name: str,
        object_key: str,
        mime_type: str,
        filename: str,
        headers: dict,
        cache_path: Path
) -> Response:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    temp_file = tempfile.NamedTemporaryFile(delete=False, dir=cache_path.parent)
    temp_path = Path(temp_file.name)
    try:
        s3_config = {
            'endpoint_url': getattr(app_config, 'S3_ENDPOINT_URL', None),
            'aws_access_key_id': getattr(app_config, 'S3_ACCESS_KEY', None),
            'aws_secret_access_key': getattr(app_config, 'S3_SECRET_KEY', None),
            'region_name': getattr(app_config, 'S3_REGION', 'us-east-1'),
            'use_ssl': getattr(app_config, 'S3_USE_SSL', True)
        }
        s3_config = {k: v for k, v in s3_config.items() if v is not None}
        session = aioboto3.Session()
        async with session.client('s3', **s3_config) as s3_client:
            response = await s3_client.get_object(Bucket=bucket_name, Key=object_key)
            file_size = response['ContentLength']
            headers["Content-Length"] = str(file_size)

            async def s3_stream_and_cache_iterator():
                total_bytes = 0
                try:
                    async with aiofiles.open(temp_path, 'wb') as cache_file:
                        async with response['Body'] as stream:
                            async for chunk in stream.iter_chunks(chunk_size=8192):
                                yield chunk
                                await cache_file.write(chunk)
                                total_bytes += len(chunk)
                    if total_bytes == file_size:
                        temp_path.rename(cache_path)
                        logger.info(f"文件已缓存: {cache_path}")
                except Exception as e:
                    logger.error(f"流式传输/缓存失败: {str(e)}")
                    if temp_path.exists():
                        temp_path.unlink()
                    raise

            # 创建 StreamingResponse
            response = StreamingResponse(
                s3_stream_and_cache_iterator(),
                media_type=mime_type
            )
                        
            # 手动设置所有自定义 headers
            for key, value in headers.items():
                response.headers[key] = value
                        
            return response
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        raise HTTPException(status_code=500, detail="文件获取失败")


def convert_storage_size(size_bytes):
    """将字节转换为可读格式"""
    # 确保 size_bytes 是数值类型（支持 Decimal、int、float）
    from decimal import Decimal
    if isinstance(size_bytes, Decimal):
        size_bytes = float(size_bytes)
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"
