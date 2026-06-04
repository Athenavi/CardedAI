"""
主题市场管理 API
提供主题的浏览、安装、激活、卸载和配置功能
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from pydantic import BaseModel
from sqlalchemy import select, desc

from shared.models.theme import Theme
from src.auth.auth_deps import jwt_required_dependency as jwt_required
from shared.models.user import User
from src.utils.database.main import get_async_session

router = APIRouter(prefix="/themes", tags=["Theme Marketplace"])


class ThemeInfo(BaseModel):
    """主题信息响应"""
    id: int
    name: str
    slug: str
    version: str
    description: Optional[str] = None
    author: Optional[str] = None
    author_url: Optional[str] = None
    theme_url: Optional[str] = None
    screenshot: Optional[str] = None
    tags: Optional[str] = None
    is_active: bool
    is_installed: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ThemeInstallRequest(BaseModel):
    """安装主题请求"""
    slug: str
    version: Optional[str] = None


class ThemeConfigUpdateRequest(BaseModel):
    """更新主题配置请求"""
    settings: Dict[str, Any]


@router.get("/marketplace", response_model=List[Dict[str, Any]])
async def list_marketplace_themes(
        category: Optional[str] = Query(None, description="按分类过滤"),
        current_user: User = Depends(jwt_required)
):
    """P2-4: 获取主题市场中的所有可用主题
    
    Args:
        category: 可选，按分类过滤
        
    Returns:
        主题列表（包含远程市场和本地已安装的主题）
    """
    # 扫描本地 themes 目录
    themes_dir = Path("themes")
    available_themes = []

    if themes_dir.exists():
        for theme_dir in themes_dir.iterdir():
            if not theme_dir.is_dir():
                continue

            # 读取 theme.json 或 package.json
            metadata_file = theme_dir / "theme.json"
            if not metadata_file.exists():
                metadata_file = theme_dir / "package.json"

            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)

                    # 检查是否已安装
                    async for db in get_async_session():
                        result = await db.execute(
                            select(Theme).where(Theme.slug == theme_dir.name)
                        )
                        installed_theme = result.scalar_one_or_none()

                        theme_info = {
                            "name": metadata.get("name", theme_dir.name),
                            "slug": theme_dir.name,
                            "version": metadata.get("version", "1.0.0"),
                            "description": metadata.get("description", ""),
                            "author": metadata.get("author", ""),
                            "screenshot": f"/themes/{theme_dir.name}/screenshot.png",
                            "tags": metadata.get("tags", []),
                            "is_installed": installed_theme is not None,
                            "is_active": installed_theme.is_active if installed_theme else False,
                            "category": metadata.get("category", "general")
                        }

                        # 如果指定了分类，进行过滤
                        if not category or theme_info["category"] == category:
                            available_themes.append(theme_info)
                except Exception as e:
                    print(f"Error reading theme {theme_dir.name}: {e}")

    return available_themes


@router.get("/installed", response_model=List[ThemeInfo])
async def list_installed_themes(
        current_user: User = Depends(jwt_required)
):
    """P2-4: 获取所有已安装的主题
    
    Returns:
        已安装主题列表
    """
    async for db in get_async_session():
        result = await db.execute(select(Theme).order_by(desc(Theme.created_at)))
        themes = result.scalars().all()

        return [
            ThemeInfo(
                id=theme.id,
                name=theme.name,
                slug=theme.slug,
                version=theme.version or "1.0.0",
                description=theme.description,
                author=theme.author,
                author_url=theme.author_url,
                theme_url=theme.theme_url,
                screenshot=theme.screenshot,
                tags=theme.tags,
                is_active=theme.is_active,
                is_installed=theme.is_installed,
                created_at=theme.created_at.isoformat() if theme.created_at else None,
                updated_at=theme.updated_at.isoformat() if theme.updated_at else None
            )
            for theme in themes
        ]


@router.post("/install")
async def install_theme(
        req: ThemeInstallRequest,
        current_user: User = Depends(jwt_required)
):
    """P2-4: 安装主题
    
    Args:
        req: 安装请求
        current_user: 当前用户
        
    Returns:
        安装结果
    """
    themes_dir = Path("themes")
    theme_path = themes_dir / req.slug

    # 检查主题目录是否存在
    if not theme_path.exists():
        raise HTTPException(status_code=404, detail=f"Theme '{req.slug}' not found in marketplace")

    # 读取主题元数据
    metadata_file = theme_path / "theme.json"
    if not metadata_file.exists():
        metadata_file = theme_path / "package.json"

    if not metadata_file.exists():
        raise HTTPException(status_code=400, detail="Invalid theme: missing metadata file")

    with open(metadata_file, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    async for db in get_async_session():
        # 检查是否已安装
        result = await db.execute(select(Theme).where(Theme.slug == req.slug))
        existing = result.scalar_one_or_none()

        if existing:
            # 更新版本
            existing.version = metadata.get("version", "1.0.0")
            existing.updated_at = datetime.utcnow()
            await db.commit()

            return {
                "success": True,
                "message": f"Theme '{req.slug}' updated to version {metadata.get('version')}",
                "theme_id": existing.id
            }

        # 创建新主题记录
        new_theme = Theme(
            name=metadata.get("name", req.slug),
            slug=req.slug,
            version=metadata.get("version", "1.0.0"),
            description=metadata.get("description", ""),
            author=metadata.get("author", ""),
            author_url=metadata.get("author_url", ""),
            theme_url=metadata.get("theme_url", ""),
            screenshot=f"/themes/{req.slug}/screenshot.png",
            tags=json.dumps(metadata.get("tags", [])),
            requires=json.dumps(metadata.get("requires", {})),
            settings_schema=json.dumps(metadata.get("settings_schema", {})),
            theme_path=str(theme_path),
            is_installed=True,
            is_active=False,
            settings=json.dumps(metadata.get("default_settings", {})),
            supports=json.dumps(metadata.get("supports", [])),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(new_theme)
        await db.commit()
        await db.refresh(new_theme)

        return {
            "success": True,
            "message": f"Theme '{req.slug}' installed successfully",
            "theme_id": new_theme.id
        }


@router.post("/{theme_slug}/activate")
async def activate_theme(
        theme_slug: str,
        current_user: User = Depends(jwt_required)
):
    """P2-4: 激活主题
    
    Args:
        theme_slug: 主题标识
        current_user: 当前用户
        
    Returns:
        激活结果
    """
    async for db in get_async_session():
        # 查找主题
        result = await db.execute(select(Theme).where(Theme.slug == theme_slug))
        theme = result.scalar_one_or_none()

        if not theme:
            raise HTTPException(status_code=404, detail="Theme not found")

        if not theme.is_installed:
            raise HTTPException(status_code=400, detail="Theme is not installed")

        # 停用当前活动主题
        result = await db.execute(select(Theme).where(Theme.is_active == True))
        active_themes = result.scalars().all()

        for active_theme in active_themes:
            active_theme.is_active = False

        # 激活新主题
        theme.is_active = True
        theme.updated_at = datetime.utcnow()

        await db.commit()

        return {
            "success": True,
            "message": f"Theme '{theme_slug}' activated successfully"
        }


@router.delete("/{theme_slug}/uninstall")
async def uninstall_theme(
        theme_slug: str,
        current_user: User = Depends(jwt_required)
):
    """P2-4: 卸载主题
    
    Args:
        theme_slug: 主题标识
        current_user: 当前用户
        
    Returns:
        卸载结果
    """
    async for db in get_async_session():
        # 查找主题
        result = await db.execute(select(Theme).where(Theme.slug == theme_slug))
        theme = result.scalar_one_or_none()

        if not theme:
            raise HTTPException(status_code=404, detail="Theme not found")

        # 不允许卸载当前活动主题
        if theme.is_active:
            raise HTTPException(status_code=400, detail="Cannot uninstall active theme")

        # 标记为未安装
        theme.is_installed = False
        theme.updated_at = datetime.utcnow()

        await db.commit()

        return {
            "success": True,
            "message": f"Theme '{theme_slug}' uninstalled successfully"
        }


@router.get("/{theme_slug}/config")
async def get_theme_config(
        theme_slug: str,
        current_user: User = Depends(jwt_required)
):
    """P2-4: 获取主题配置
    
    Args:
        theme_slug: 主题标识
        current_user: 当前用户
        
    Returns:
        主题配置
    """
    async for db in get_async_session():
        result = await db.execute(select(Theme).where(Theme.slug == theme_slug))
        theme = result.scalar_one_or_none()

        if not theme:
            raise HTTPException(status_code=404, detail="Theme not found")

        try:
            settings = json.loads(theme.settings) if theme.settings else {}
            settings_schema = json.loads(theme.settings_schema) if theme.settings_schema else {}
        except:
            settings = {}
            settings_schema = {}

        return {
            "theme_slug": theme_slug,
            "settings": settings,
            "settings_schema": settings_schema
        }


@router.put("/{theme_slug}/config")
async def update_theme_config(
        theme_slug: str,
        req: ThemeConfigUpdateRequest,
        current_user: User = Depends(jwt_required)
):
    """P2-4: 更新主题配置
    
    Args:
        theme_slug: 主题标识
        req: 配置更新请求
        current_user: 当前用户
        
    Returns:
        更新结果
    """
    async for db in get_async_session():
        result = await db.execute(select(Theme).where(Theme.slug == theme_slug))
        theme = result.scalar_one_or_none()

        if not theme:
            raise HTTPException(status_code=404, detail="Theme not found")

        theme.settings = json.dumps(req.settings)
        theme.updated_at = datetime.utcnow()

        await db.commit()

        return {
            "success": True,
            "message": f"Theme '{theme_slug}' configuration updated"
        }


@router.get("/categories", response_model=List[str])
async def list_theme_categories():
    """P2-4: 获取所有主题分类
    
    Returns:
        分类列表
    """
    categories = ["general", "minimal", "magazine", "photography", "business", "portfolio"]
    return categories


@router.get("/{theme_slug}/preview")
async def preview_theme(theme_slug: str):
    """P2-4: 预览主题（公开接口，无需认证）
    
    Args:
        theme_slug: 主题标识
        
    Returns:
        主题预览信息
    """
    themes_dir = Path("themes")
    theme_path = themes_dir / theme_slug

    if not theme_path.exists():
        raise HTTPException(status_code=404, detail="Theme not found")

    # 读取元数据
    metadata_file = theme_path / "theme.json"
    if not metadata_file.exists():
        metadata_file = theme_path / "package.json"

    if not metadata_file.exists():
        raise HTTPException(status_code=400, detail="Invalid theme")

    with open(metadata_file, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    return {
        "name": metadata.get("name", theme_slug),
        "slug": theme_slug,
        "version": metadata.get("version", "1.0.0"),
        "description": metadata.get("description", ""),
        "screenshot": f"/themes/{theme_slug}/screenshot.png",
        "demo_url": f"/preview/{theme_slug}"
    }
