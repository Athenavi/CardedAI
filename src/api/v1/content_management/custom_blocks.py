"""
自定义块插件管理 API
提供插件的加载、卸载、激活、停用等管理功能
"""

from typing import Dict, Any, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from shared.services.content_management.block_editor_service import block_editor_service
from shared.services.content_management.custom_block_framework import create_plugin_manager
from shared.services.content_management.example_custom_blocks import ExampleBlocksPlugin

router = APIRouter(tags=["Custom Blocks"])

# 创建全局插件管理器
plugin_manager = create_plugin_manager(block_editor_service)

# 预加载示例插件
example_plugin = ExampleBlocksPlugin()
plugin_manager.load_plugin(example_plugin)


class PluginInfo(BaseModel):
    """插件信息"""
    name: str
    version: str
    description: str = ""
    author: str = ""
    blocks_count: int = 0
    is_active: bool = True


class PluginActionResponse(BaseModel):
    """插件操作响应"""
    success: bool
    message: str
    data: Dict[str, Any] = {}


@router.get("/plugins", response_model=List[PluginInfo])
async def list_plugins():
    """
    获取所有插件列表
    
    Returns:
        插件信息列表
    """
    plugins = plugin_manager.get_all_plugins()

    result = []
    for plugin in plugins:
        result.append(PluginInfo(
            name=plugin.name,
            version=plugin.version,
            description=plugin.description,
            author=plugin.author,
            blocks_count=len(plugin.blocks),
            is_active=plugin.is_active
        ))

    return result


@router.get("/plugins/active", response_model=List[PluginInfo])
async def list_active_plugins():
    """
    获取所有激活的插件
    
    Returns:
        激活的插件信息列表
    """
    plugins = plugin_manager.get_active_plugins()

    result = []
    for plugin in plugins:
        result.append(PluginInfo(
            name=plugin.name,
            version=plugin.version,
            description=plugin.description,
            author=plugin.author,
            blocks_count=len(plugin.blocks),
            is_active=plugin.is_active
        ))

    return result


@router.post("/plugins/{plugin_name}/activate", response_model=PluginActionResponse)
async def activate_plugin(plugin_name: str):
    """
    激活插件
    
    Args:
        plugin_name: 插件名称
        
    Returns:
        操作结果
    """
    if plugin_name not in plugin_manager.plugins:
        raise HTTPException(status_code=404, detail=f"插件 '{plugin_name}' 不存在")

    success = plugin_manager.activate_plugin(plugin_name)

    if success:
        return PluginActionResponse(
            success=True,
            message=f"插件 '{plugin_name}' 已激活"
        )
    else:
        return PluginActionResponse(
            success=False,
            message=f"插件 '{plugin_name}' 激活失败"
        )


@router.post("/plugins/{plugin_name}/deactivate", response_model=PluginActionResponse)
async def deactivate_plugin(plugin_name: str):
    """
    停用插件
    
    Args:
        plugin_name: 插件名称
        
    Returns:
        操作结果
    """
    if plugin_name not in plugin_manager.plugins:
        raise HTTPException(status_code=404, detail=f"插件 '{plugin_name}' 不存在")

    success = plugin_manager.deactivate_plugin(plugin_name)

    if success:
        return PluginActionResponse(
            success=True,
            message=f"插件 '{plugin_name}' 已停用"
        )
    else:
        return PluginActionResponse(
            success=False,
            message=f"插件 '{plugin_name}' 停用失败"
        )


@router.get("/blocks", response_model=List[Dict[str, Any]])
async def list_all_blocks():
    """
    获取所有可用的块类型（包括内置和插件）
    
    Returns:
        块类型列表
    """
    # 获取内置块
    builtin_blocks = block_editor_service.get_all_block_types()

    # 获取插件块
    plugin_blocks = plugin_manager.get_all_blocks()

    # 合并并转换为字典
    all_blocks = []
    for block in builtin_blocks + plugin_blocks:
        all_blocks.append({
            "name": block.name,
            "display_name": block.display_name,
            "category": block.category,
            "icon": block.icon,
            "description": block.description,
            "attributes": block.attributes,
            "is_inline": block.is_inline
        })

    return all_blocks


@router.get("/blocks/by-category/{category}", response_model=List[Dict[str, Any]])
async def get_blocks_by_category(category: str):
    """
    按分类获取块类型
    
    Args:
        category: 分类名称 (text, media, layout, widget, embed)
        
    Returns:
        该分类下的块类型列表
    """
    # 从内置服务获取
    builtin_blocks = block_editor_service.get_block_types_by_category(category)

    # 从插件获取
    plugin_blocks = [
        block for block in plugin_manager.get_all_blocks()
        if block.category == category
    ]

    # 合并
    all_blocks = []
    for block in builtin_blocks + plugin_blocks:
        all_blocks.append({
            "name": block.name,
            "display_name": block.display_name,
            "category": block.category,
            "icon": block.icon,
            "description": block.description,
            "attributes": block.attributes,
            "is_inline": block.is_inline
        })

    return all_blocks


@router.get("/statistics", response_model=Dict[str, Any])
async def get_statistics():
    """
    获取插件和块统计信息
    
    Returns:
        统计信息
    """
    plugin_stats = plugin_manager.get_plugin_statistics()

    # 获取块的统计
    all_blocks = block_editor_service.get_all_block_types() + plugin_manager.get_all_blocks()

    block_stats = {
        "total_blocks": len(all_blocks),
        "by_category": {}
    }

    for block in all_blocks:
        category = block.category
        block_stats["by_category"][category] = block_stats["by_category"].get(category, 0) + 1

    return {
        "plugins": plugin_stats,
        "blocks": block_stats
    }


@router.post("/discover", response_model=PluginActionResponse)
async def discover_plugins():
    """
    自动发现并加载插件
    
    Returns:
        操作结果
    """
    try:
        loaded_count = plugin_manager.auto_discover_plugins()

        return PluginActionResponse(
            success=True,
            message=f"成功发现并加载 {loaded_count} 个插件",
            data={"loaded_count": loaded_count}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"插件发现失败: {str(e)}")


@router.get("/plugins/{plugin_name}", response_model=PluginInfo)
async def get_plugin_info(plugin_name: str):
    """
    获取单个插件的详细信息
    
    Args:
        plugin_name: 插件名称
        
    Returns:
        插件信息
    """
    plugin = plugin_manager.get_plugin(plugin_name)

    if not plugin:
        raise HTTPException(status_code=404, detail=f"插件 '{plugin_name}' 不存在")

    return PluginInfo(
        name=plugin.name,
        version=plugin.version,
        description=plugin.description,
        author=plugin.author,
        blocks_count=len(plugin.blocks),
        is_active=plugin.is_active
    )
