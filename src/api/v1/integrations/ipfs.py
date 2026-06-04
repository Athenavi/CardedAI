"""
IPFS 存储管理 API
提供文件上传、下载、固定等功能
"""

from typing import Dict, List

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from shared.services.integrations.ipfs_service import ipfs_service

router = APIRouter(tags=["IPFS"])


class UploadTextRequest(BaseModel):
    """上传文本请求"""
    text: str
    filename: str = "content.txt"


class UploadArticleRequest(BaseModel):
    """上传文章请求"""
    article_id: int
    title: str
    content: str
    author: str = ""
    tags: List[str] = []


@router.post("/upload/file")
async def upload_file(file: UploadFile = File(...)):
    """
    上传文件到 IPFS
    
    Args:
        file: 上传的文件
        
    Returns:
        IPFS 文件信息
    """
    try:
        # 读取文件内容
        content = await file.read()
        filename = file.filename or "unknown"
        content_type = file.content_type or "application/octet-stream"

        # 上传到 IPFS
        ipfs_file = ipfs_service.upload_file(content, filename, content_type)

        if not ipfs_file:
            raise HTTPException(status_code=500, detail="文件上传失败")

        return {
            "success": True,
            "message": "文件上传成功",
            "data": {
                "cid": ipfs_file.cid,
                "filename": ipfs_file.filename,
                "size": ipfs_file.size,
                "content_type": ipfs_file.content_type,
                "gateway_url": ipfs_file.gateway_url,
                "pinned": ipfs_file.pinned
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.post("/upload/text")
async def upload_text(request: UploadTextRequest):
    """
    上传文本内容到 IPFS
    
    Args:
        request: 上传请求
        
    Returns:
        IPFS 文件信息
    """
    try:
        ipfs_file = ipfs_service.upload_text(request.text, request.filename)

        if not ipfs_file:
            raise HTTPException(status_code=500, detail="文本上传失败")

        return {
            "success": True,
            "message": "文本上传成功",
            "data": {
                "cid": ipfs_file.cid,
                "filename": ipfs_file.filename,
                "size": ipfs_file.size,
                "gateway_url": ipfs_file.gateway_url
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.post("/upload/article")
async def upload_article(request: UploadArticleRequest):
    """
    上传文章内容到 IPFS
    
    Args:
        request: 文章数据
        
    Returns:
        IPFS 文件信息
    """
    try:
        article_data = {
            "id": request.article_id,
            "title": request.title,
            "content": request.content,
            "author": request.author,
            "tags": request.tags,
            "created_at": None
        }

        ipfs_file = ipfs_service.upload_article(article_data)

        if not ipfs_file:
            raise HTTPException(status_code=500, detail="文章上传失败")

        return {
            "success": True,
            "message": "文章上传成功",
            "data": {
                "cid": ipfs_file.cid,
                "filename": ipfs_file.filename,
                "gateway_url": ipfs_file.gateway_url,
                "article_id": request.article_id
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.get("/download/{cid}")
async def download_file(cid: str):
    """
    从 IPFS 下载文件
    
    Args:
        cid: 内容 ID
        
    Returns:
        文件内容
    """
    try:
        content = ipfs_service.download_file(cid)

        if not content:
            raise HTTPException(status_code=404, detail="文件不存在")

        # 获取文件信息
        file_info = ipfs_service.get_file_info(cid)

        return {
            "success": True,
            "data": {
                "cid": cid,
                "content": content.decode('utf-8', errors='ignore'),
                "info": file_info
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载失败: {str(e)}")


@router.get("/file/{cid}")
async def get_file_info(cid: str):
    """
    获取文件信息
    
    Args:
        cid: 内容 ID
        
    Returns:
        文件信息
    """
    file_info = ipfs_service.get_file_info(cid)

    if not file_info:
        raise HTTPException(status_code=404, detail="文件不存在")

    return {
        "success": True,
        "data": file_info
    }


@router.get("/files")
async def list_files(pinned_only: bool = False):
    """
    列出所有文件
    
    Args:
        pinned_only: 是否只列出已固定的文件
        
    Returns:
        文件列表
    """
    files = ipfs_service.list_files(pinned_only)

    return {
        "success": True,
        "data": {
            "total": len(files),
            "files": files
        }
    }


@router.post("/pin/{cid}")
async def pin_file(cid: str):
    """
    固定文件
    
    Args:
        cid: 内容 ID
        
    Returns:
        操作结果
    """
    success = ipfs_service.pin_file(cid)

    if not success:
        raise HTTPException(status_code=404, detail="文件不存在")

    return {
        "success": True,
        "message": "文件已固定"
    }


@router.post("/unpin/{cid}")
async def unpin_file(cid: str):
    """
    取消固定文件
    
    Args:
        cid: 内容 ID
        
    Returns:
        操作结果
    """
    success = ipfs_service.unpin_file(cid)

    if not success:
        raise HTTPException(status_code=404, detail="文件不存在")

    return {
        "success": True,
        "message": "文件已取消固定"
    }


@router.delete("/file/{cid}")
async def delete_file(cid: str):
    """
    删除文件记录
    
    Args:
        cid: 内容 ID
        
    Returns:
        操作结果
    """
    success = ipfs_service.delete_file(cid)

    if not success:
        raise HTTPException(status_code=404, detail="文件不存在")

    return {
        "success": True,
        "message": "文件记录已删除（注意：IPFS 上的文件无法真正删除）"
    }


@router.post("/configure")
async def configure_ipfs(config: Dict[str, str]):
    """
    配置 IPFS 服务
    
    Args:
        config: 配置信息
        
    Returns:
        配置结果
    """
    try:
        ipfs_service.configure(config)

        return {
            "success": True,
            "message": "IPFS 服务配置已更新"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"配置失败: {str(e)}")
