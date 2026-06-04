"""
插件管理 API 端点
提供插件的激活、停用、配置等功能
"""
import asyncio

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import User
from shared.services.plugins.plugin_manager.core import plugin_manager
from src.auth import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db

router = APIRouter(tags=["plugins"])


@router.get("/")
async def list_plugins(
        current_user: User = Depends(jwt_required)
):
    """
    获取所有已安装的插件列表
    
    Returns:
        插件列表
    """
    try:
        plugins = plugin_manager.get_installed_plugins()

        return {
            'success': True,
            'data': {
                'plugins': plugins,  # 包装成 plugins 字段以匹配前端期望
            },
        }

    except Exception as e:
        import traceback
        print(f"Error listing plugins: {str(e)}")
        print(traceback.format_exc())
        return {
            'success': False,
            'error': str(e)
        }


@router.post("/load")
async def load_all_plugins(
        current_user: User = Depends(jwt_required)
):
    """
    加载所有插件
    
    Returns:
        加载结果
    """
    try:

        plugin_manager.load_all_plugins()

        return {
            'success': True,
            'data': {
                'message': f'Loaded {len(plugin_manager.plugins)} plugins',
                'plugins': plugin_manager.get_installed_plugins(),
            }
        }

    except Exception as e:
        import traceback
        print(f"Error loading plugins: {str(e)}")
        print(traceback.format_exc())
        return {
            'success': False,
            'error': str(e)
        }


@router.post("/{plugin_slug}/activate")
async def activate_plugin(
        plugin_slug: str,
        current_user: User = Depends(jwt_required)
):
    """
    激活插件
    
    Args:
        plugin_slug: 插件标识
        
    Returns:
        激活结果
    """
    try:

        # 先加载插件(如果未加载)
        if plugin_slug not in plugin_manager.plugins:
            plugin_manager.load_plugin(plugin_slug)

        success = plugin_manager.activate_plugin(plugin_slug)

        if success:
            return {
                'success': True,
                'data': {
                    'message': f'Plugin {plugin_slug} activated',
                }
            }
        else:
            return {
                'success': False,
                'error': 'Failed to activate plugin',
            }

    except Exception as e:
        import traceback
        print(f"Error activating plugin: {str(e)}")
        print(traceback.format_exc())
        return {
            'success': False,
            'error': str(e)
        }


@router.post("/{plugin_slug}/deactivate")
async def deactivate_plugin(
        plugin_slug: str,
        current_user: User = Depends(jwt_required)
):
    """
    停用插件
    
    Args:
        plugin_slug: 插件标识
        
    Returns:
        停用结果
    """
    try:

        success = plugin_manager.deactivate_plugin(plugin_slug)

        if success:
            return {
                'success': True,
                'data': {
                    'message': f'Plugin {plugin_slug} deactivated',
                }
            }
        else:
            return {
                'success': False,
                'error': 'Failed to deactivate plugin',
            }

    except Exception as e:
        import traceback
        print(f"Error deactivating plugin: {str(e)}")
        print(traceback.format_exc())
        return {
            'success': False,
            'error': str(e)
        }


@router.get("/{plugin_slug}")
async def get_plugin_info(
        plugin_slug: str,
        current_user: User = Depends(jwt_required)
):
    """
    获取插件详细信息
    
    Args:
        plugin_slug: 插件标识
        
    Returns:
        插件信息
    """
    try:

        plugin = plugin_manager.get_plugin(plugin_slug)

        if not plugin:
            return {
                'success': False,
                'error': 'Plugin not found',
            }

        return {
            'success': True,
            'data': plugin.get_info(),
        }

    except Exception as e:
        import traceback
        print(f"Error getting plugin info: {str(e)}")
        print(traceback.format_exc())
        return {
            'success': False,
            'error': str(e)
        }


@router.get("/{plugin_slug}/settings")
async def get_plugin_settings(
        plugin_slug: str,
        current_user: User = Depends(jwt_required)
):
    """
    获取插件设置
    
    Args:
        plugin_slug: 插件标识
        
    Returns:
        插件设置和UI配置
    """
    try:

        plugin = plugin_manager.get_plugin(plugin_slug)

        if not plugin:
            return {
                'success': False,
                'error': 'Plugin not found',
            }

        settings_ui = plugin.get_settings_ui()

        return {
            'success': True,
            'data': {
                'settings': plugin.settings,
                'ui': settings_ui,
            }
        }

    except Exception as e:
        import traceback
        print(f"Error getting plugin settings: {str(e)}")
        print(traceback.format_exc())
        return {
            'success': False,
            'error': str(e)
        }


@router.put("/{plugin_slug}/settings")
async def update_plugin_settings(
        plugin_slug: str,
        request: Request,
        current_user: User = Depends(jwt_required)
):
    """
    更新插件设置
    
    Args:
        plugin_slug: 插件标识
        
    Body参数:
        settings: 新的设置值
        
    Returns:
        更新结果
    """
    try:

        body = await request.json()
        settings = body.get('settings', {})

        success = plugin_manager.update_plugin_settings(plugin_slug, settings)

        if success:
            return {
                'success': True,
                'data': {
                    'message': 'Settings updated',
                }
            }
        else:
            return {
                'success': False,
                'error': 'Failed to update settings',
            }

    except Exception as e:
        import traceback
        print(f"Error updating plugin settings: {str(e)}")
        print(traceback.format_exc())
        return {
            'success': False,
            'error': str(e)
        }


@router.post("/{plugin_slug}/action")
async def execute_plugin_action(
        plugin_slug: str,
        request: Request,
        current_user: User = Depends(jwt_required)
):
    """
    执行插件自定义动作
    
    Args:
        plugin_slug: 插件标识
        
    Body参数:
        action: 动作名称
        params: 动作参数
        
    Returns:
        执行结果
    """
    try:

        body = await request.json()
        action = body.get('action')
        params = body.get('params', {})

        plugin = plugin_manager.get_plugin(plugin_slug)

        if not plugin:
            return {
                'success': False,
                'error': 'Plugin not found',
            }

        # 检查插件是否有该方法
        if not hasattr(plugin, action):
            return {
                'success': False,
                'error': f'Action {action} not found',
            }

        # 执行动作
        method = getattr(plugin, action)

        if asyncio.iscoroutinefunction(method):
            result = await method(**params)
        else:
            result = method(**params)

        return {
            'success': True,
            'data': result,
        }

    except Exception as e:
        import traceback
        print(f"Error executing plugin action: {str(e)}")
        print(traceback.format_exc())
        return {
            'success': False,
            'error': str(e)
        }


@router.get("/active")
async def get_active_plugins(
        current_user: User = Depends(jwt_required)
):
    """
    获取所有激活的插件
    
    Returns:
        激活的插件列表
    """
    try:

        active_plugins = plugin_manager.get_active_plugins()

        return {
            'success': True,
            'data': [p.get_info() for p in active_plugins],
        }

    except Exception as e:
        import traceback
        print(f"Error getting active plugins: {str(e)}")
        print(traceback.format_exc())
        return {
            'success': False,
            'error': str(e)
        }


@router.delete("/{plugin_slug}")
async def uninstall_plugin(
        plugin_slug: str,
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    卸载插件
    
    Args:
        plugin_slug: 插件标识
        
    Returns:
        卸载结果
    """
    try:

        success = plugin_manager.uninstall_plugin(plugin_slug)

        if success:
            return {
                'success': True,
                'data': {
                    'message': f'Plugin {plugin_slug} uninstalled',
                }
            }
        else:
            return {
                'success': False,
                'error': 'Failed to uninstall plugin',
            }

    except Exception as e:
        import traceback
        print(f"Error uninstalling plugin: {str(e)}")
        print(traceback.format_exc())
        return {
            'success': False,
            'error': str(e)
        }


@router.post("/sync-config")
async def sync_plugin_config(
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    同步插件配置 - 将本地插件状态同步到数据库
    
    此接口会:
    1. 扫描本地 plugins 目录中的所有插件
    2. 读取 plugin_state.json 中的激活状态
    3. 将状态同步到数据库的 fb_plugins 表
    4. 确保数据库和本地状态一致
    
    Returns:
        同步结果
    """
    try:
        from pathlib import Path
        import json
        from datetime import datetime
        from shared.models import Plugin
        from sqlalchemy import select

        # 1. 读取本地 plugin_state.json
        state_file = Path("storage/plugin_state.json")
        if not state_file.exists():
            return {
                'success': False,
                'error': 'plugin_state.json 不存在'
            }

        with open(state_file, 'r', encoding='utf-8') as f:
            plugin_states = json.load(f)

        # 2. 扫描本地插件目录
        plugins_dir = Path("plugins")
        local_plugins = []
        if plugins_dir.exists():
            for item in plugins_dir.iterdir():
                if item.is_dir():
                    metadata_file = item / "metadata.json"
                    if metadata_file.exists():
                        try:
                            with open(metadata_file, 'r', encoding='utf-8') as mf:
                                metadata = json.load(mf)
                                local_plugins.append({
                                    'slug': item.name,
                                    'metadata': metadata
                                })
                        except Exception as e:
                            print(f"读取插件元数据失败 {item.name}: {e}")

        # 3. 获取数据库中现有的插件 (使用异步会话)
        result = await db.execute(select(Plugin))
        db_plugins = result.scalars().all()
        existing_plugins = {plugin.slug: plugin for plugin in db_plugins}

        # 4. 同步状态
        synced_count = 0
        created_count = 0
        updated_count = 0
        settings_synced = 0

        try:
            for local_plugin in local_plugins:
                slug = local_plugin['slug']
                metadata = local_plugin['metadata']

                # 从 plugin_state.json 获取激活状态
                state = plugin_states.get(slug, {})
                is_active = state.get('active', False)
                # 如果 active 为 true，则 installed 也必须为 true
                is_installed = state.get('installed', True) or is_active

                # 读取插件设置文件 (如果存在)
                settings_data = None
                settings_file = Path("plugins") / slug / "settings.json"
                if settings_file.exists():
                    try:
                        with open(settings_file, 'r', encoding='utf-8') as sf:
                            settings_data = json.load(sf)
                    except Exception as e:
                        print(f"读取插件设置失败 {slug}: {e}")

                # 检查数据库中是否存在
                if slug in existing_plugins:
                    # 更新现有记录
                    plugin = existing_plugins[slug]
                    needs_update = False

                    # 检查激活状态
                    if plugin.is_active != is_active:
                        plugin.is_active = is_active
                        needs_update = True

                    if plugin.is_installed != is_installed:
                        plugin.is_installed = is_installed
                        needs_update = True

                    # 同步设置
                    if settings_data is not None:
                        settings_json = json.dumps(settings_data, ensure_ascii=False)
                        if plugin.settings != settings_json:
                            plugin.settings = settings_json
                            needs_update = True
                            settings_synced += 1

                    if needs_update:
                        plugin.updated_at = datetime.now()
                        updated_count += 1
                        print(
                            f"[SyncConfig] Updated plugin: {slug} (active={is_active}, settings={'yes' if settings_data else 'no'})")
                else:
                    # 创建新记录
                    settings_json = json.dumps(settings_data, ensure_ascii=False) if settings_data else None

                    plugin = Plugin(
                        slug=slug,
                        name=metadata.get('name', slug),
                        version=metadata.get('version', '1.0.0'),
                        description=metadata.get('description', ''),
                        author=metadata.get('author', ''),
                        author_url=metadata.get('author_url', ''),
                        plugin_url=metadata.get('plugin_url', ''),
                        is_active=is_active,
                        is_installed=is_installed,
                        settings=settings_json,
                        priority=metadata.get('priority', 0),
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    db.add(plugin)
                    created_count += 1
                    if settings_data:
                        settings_synced += 1
                    print(f"[SyncConfig] Created plugin: {slug} (with settings={'yes' if settings_data else 'no'})")

                synced_count += 1

            # 提交更改
            await db.commit()

            return {
                'success': True,
                'data': {
                    'message': '插件配置同步成功',
                    'synced': synced_count,
                    'created': created_count,
                    'updated': updated_count,
                    'settings_synced': settings_synced,
                    'total_local_plugins': len(local_plugins),
                    'total_db_plugins': len(existing_plugins) + created_count
                }
            }

        except Exception as e:
            await db.rollback()
            raise e

    except Exception as e:
        import traceback
        print(f"Error syncing plugin config: {str(e)}")
        print(traceback.format_exc())
        return {
            'success': False,
            'error': str(e)
        }


# ==================== 热插拔 API ====================

@router.post("/{plugin_slug}/hot-reload")
async def hot_reload_plugin(
        plugin_slug: str,
        current_user: User = Depends(jwt_required)
):
    """
    热重载插件（无需重启应用）
    
    步骤:
    1. 停用当前插件（注销钩子）
    2. 重新加载模块代码
    3. 创建新的插件实例
    4. 激活新插件（注册钩子）
    
    Args:
        plugin_slug: 插件slug
        
    Returns:
        重载结果
    """
    try:
        success = plugin_manager.hot_reload_plugin(plugin_slug)

        if success:
            return {
                'success': True,
                'data': {
                    'message': f'插件 {plugin_slug} 已热重载',
                }
            }
        else:
            return {
                'success': False,
                'error': '热重载失败，请查看日志',
            }

    except Exception as e:
        import traceback
        print(f"Error hot reloading plugin: {str(e)}")
        print(traceback.format_exc())
        return {
            'success': False,
            'error': str(e)
        }


@router.post("/{plugin_slug}/hot-load")
async def hot_load_plugin(
        plugin_slug: str,
        current_user: User = Depends(jwt_required)
):
    """
    热加载新插件（运行时动态加载，无需重启）
    
    Args:
        plugin_slug: 插件slug
        
    Returns:
        加载结果
    """
    try:
        success = plugin_manager.hot_load_plugin(plugin_slug)

        if success:
            return {
                'success': True,
                'data': {
                    'message': f'插件 {plugin_slug} 已热加载并激活',
                }
            }
        else:
            return {
                'success': False,
                'error': '热加载失败，请查看日志',
            }

    except Exception as e:
        import traceback
        print(f"Error hot loading plugin: {str(e)}")
        print(traceback.format_exc())
        return {
            'success': False,
            'error': str(e)
        }


@router.post("/{plugin_slug}/hot-unload")
async def hot_unload_plugin(
        plugin_slug: str,
        current_user: User = Depends(jwt_required)
):
    """
    热卸载插件（运行时动态卸载，无需重启）
    
    Args:
        plugin_slug: 插件slug
        
    Returns:
        卸载结果
    """
    try:
        success = plugin_manager.hot_unload_plugin(plugin_slug)

        if success:
            return {
                'success': True,
                'data': {
                    'message': f'插件 {plugin_slug} 已热卸载',
                }
            }
        else:
            return {
                'success': False,
                'error': '热卸载失败，请查看日志',
            }

    except Exception as e:
        import traceback
        print(f"Error hot unloading plugin: {str(e)}")
        print(traceback.format_exc())
        return {
            'success': False,
            'error': str(e)
        }


@router.get("/scan-new")
async def scan_new_plugins(
        current_user: User = Depends(jwt_required)
):
    """
    扫描新插件（发现plugins目录中未加载的插件）
    
    Returns:
        新发现的插件列表
    """
    try:
        new_plugins = plugin_manager.scan_for_new_plugins()

        return {
            'success': True,
            'data': {
                'new_plugins': new_plugins,
                'count': len(new_plugins),
                'message': f'发现 {len(new_plugins)} 个新插件'
            }
        }

    except Exception as e:
        import traceback
        print(f"Error scanning new plugins: {str(e)}")
        print(traceback.format_exc())
        return {
            'success': False,
            'error': str(e)
        }
