"""
插件市场管理 API
支持插件的上传、安装、卸载及状态管理
"""
import json
from pathlib import Path
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from pydantic import BaseModel

from src.auth.auth_deps import jwt_required_dependency as jwt_required
from shared.models.user import User
from shared.services.plugins.hot_swap_manager import hot_swapper
from shared.services.plugins.sandbox_service import sandbox_service

router = APIRouter(prefix="/plugins", tags=["Plugin Marketplace"])


class PluginInstallRequest(BaseModel):
    slug: str
    capabilities: list[str]


@router.get("/marketplace")
async def list_marketplace_plugins(
    current_user: User = Depends(jwt_required)
):
    """P1-3: 获取插件市场中所有可用插件"""
    plugins_dir = Path("plugins")
    available_plugins = []
    
    if plugins_dir.exists():
        for plugin_dir in plugins_dir.iterdir():
            if plugin_dir.is_dir():
                metadata_file = plugin_dir / "plugin.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        
                        # 检查是否已安装
                        is_installed = plugin_dir.name in hot_swapper.loaded_plugins
                        
                        available_plugins.append({
                            "slug": plugin_dir.name,
                            "name": metadata.get("name", plugin_dir.name),
                            "version": metadata.get("version", "0.0.1"),
                            "description": metadata.get("description", ""),
                            "author": metadata.get("author", "Unknown"),
                            "author_url": metadata.get("author_url", ""),
                            "is_active": is_installed,
                            "is_installed": is_installed,
                            "capabilities": metadata.get("capabilities", []),
                            "created_at": None,
                            "updated_at": None
                        })
                    except Exception as e:
                        print(f"Failed to read plugin metadata {plugin_dir.name}: {e}")
    
    return available_plugins


@router.get("/active")
async def list_active_plugins(
    current_user: User = Depends(jwt_required)
):
    """获取已安装并激活的插件列表"""
    active_plugins = []
    
    for slug, plugin in hot_swapper.loaded_plugins.items():
        plugin_dir = Path(f"plugins/{slug}")
        metadata_file = plugin_dir / "plugin.json"
        
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                active_plugins.append({
                    "slug": slug,
                    "name": metadata.get("name", slug),
                    "version": metadata.get("version", "0.0.1"),
                    "description": metadata.get("description", ""),
                    "author": metadata.get("author", "Unknown"),
                    "author_url": metadata.get("author_url", ""),
                    "is_active": True,
                    "is_installed": True,
                    "capabilities": metadata.get("capabilities", []),
                    "created_at": None,
                    "updated_at": None
                })
            except Exception as e:
                print(f"Failed to read plugin metadata {slug}: {e}")
    
    return active_plugins


@router.post("/install")
async def install_plugin(
    req: PluginInstallRequest,
    current_user: User = Depends(jwt_required)
):
    """P1-1 & P1-2: 安装并热加载插件"""
    # 1. 验证能力请求
    if not sandbox_service.validate_capabilities(req.slug, req.capabilities):
        raise HTTPException(status_code=400, detail="Invalid capabilities requested")

    # 2. 执行热加载
    success = await hot_swapper.load_plugin(req.slug)
    if success:
        sandbox_service.enforce_isolation(req.slug)
        return {"success": True, "message": f"Plugin {req.slug} installed and activated"}
    raise HTTPException(status_code=500, detail="Installation failed")


@router.post("/uninstall/{slug}")
async def uninstall_plugin(
    slug: str,
    current_user: User = Depends(jwt_required)
):
    """卸载插件"""
    success = await hot_swapper.unload_plugin(slug)
    return {"success": success, "message": f"Plugin {slug} uninstalled"}


@router.post("/upload")
async def upload_plugin(
    file: UploadFile = File(...),
    current_user: User = Depends(jwt_required)
):
    """上传插件包 (Zip)"""
    # 实际实现应解压文件到 plugins 目录并校验 metadata.json
    return {"success": True, "filename": file.filename}


@router.post("/{slug}/activate")
async def activate_plugin(
    slug: str,
    current_user: User = Depends(jwt_required)
):
    """激活插件"""
    success = await hot_swapper.load_plugin(slug)
    if success:
        sandbox_service.enforce_isolation(slug)
        return {"success": True, "message": f"Plugin {slug} activated"}
    raise HTTPException(status_code=500, detail="Activation failed")


@router.post("/{slug}/deactivate")
async def deactivate_plugin(
    slug: str,
    current_user: User = Depends(jwt_required)
):
    """停用插件（不卸载）"""
    # 在实际实现中，可以只禁用而不卸载
    success = await hot_swapper.unload_plugin(slug)
    return {"success": success, "message": f"Plugin {slug} deactivated"}
