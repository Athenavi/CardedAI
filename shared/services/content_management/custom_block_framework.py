"""
自定义块开发框架
提供插件化的块类型注册机制，支持动态加载和热更新

使用示例:
    # 1. 创建自定义块插件
    from shared.services.custom_block_framework import CustomBlockPlugin, BlockType
    
    class MyCustomPlugin(CustomBlockPlugin):
        name = "my-custom-plugin"
        version = "1.0.0"
        
        def register_blocks(self):
            # 注册自定义块
            self.register_block(BlockType(
                name="custom-alert",
                display_name="自定义警告框",
                category="widget",
                icon="⚠️",
                attributes={
                    "message": {"type": "string", "required": True},
                    "level": {"type": "string", "enum": ["info", "warning", "error"]}
                }
            ))
            
        def render_custom_alert(self, attributes, children):
            # 自定义渲染逻辑
            level = attributes.get("level", "info")
            message = attributes.get("message", "")
            return f'<div class="alert alert-{level}">{message}</div>'
    
    # 2. 加载插件
    from shared.services.custom_block_framework import block_plugin_manager
    plugin = MyCustomPlugin()
    block_plugin_manager.load_plugin(plugin)
    
    # 3. 使用自定义块
    blocks = block_plugin_manager.get_all_blocks()
"""

import importlib
import inspect
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional

from .block_editor_service import BlockType, BlockEditorService


@dataclass
class BlockPlugin:
    """块插件信息"""
    name: str  # 插件名称（唯一标识）
    version: str  # 版本
    description: str = ""  # 描述
    author: str = ""  # 作者
    blocks: List[BlockType] = field(default_factory=list)  # 注册的块类型
    is_active: bool = True  # 是否激活
    metadata: Dict[str, Any] = field(default_factory=dict)  # 额外元数据


class CustomBlockPlugin:
    """
    自定义块插件基类
    
    开发者继承此类来创建自定义块插件
    """

    name: str = ""  # 插件名称
    version: str = "1.0.0"  # 版本
    description: str = ""  # 描述
    author: str = ""  # 作者

    def __init__(self):
        self.service: Optional[BlockEditorService] = None
        self._blocks: List[BlockType] = []

    def initialize(self, service: BlockEditorService):
        """初始化插件"""
        self.service = service
        self.register_blocks()

    def register_blocks(self):
        """
        注册块类型（子类必须实现）
        
        在此方法中调用 self.register_block() 来注册自定义块
        """
        raise NotImplementedError("Subclasses must implement register_blocks()")

    def register_block(self, block_type: BlockType):
        """
        注册单个块类型
        
        Args:
            block_type: 块类型定义
        """
        if self.service:
            self.service.register_block(block_type)
        self._blocks.append(block_type)

    def get_registered_blocks(self) -> List[BlockType]:
        """获取此插件注册的所有块类型"""
        return self._blocks.copy()

    def on_activate(self):
        """插件激活时调用（可选）"""
        pass

    def on_deactivate(self):
        """插件停用时调用（可选）"""
        pass

    def get_render_method(self, block_name: str) -> Optional[Any]:
        """
        获取块的自定义渲染方法
        
        如果插件定义了 render_{block_name} 方法，则返回该方法
        
        Args:
            block_name: 块名称
            
        Returns:
            渲染方法或 None
        """
        method_name = f"render_{block_name.replace('-', '_')}"
        return getattr(self, method_name, None)


class BlockPluginManager:
    """
    块插件管理器
    
    功能：
    1. 插件加载和卸载
    2. 插件生命周期管理
    3. 自动发现插件
    4. 插件依赖管理
    """

    def __init__(self, base_service: BlockEditorService):
        self.base_service = base_service
        self.plugins: Dict[str, BlockPlugin] = {}
        self.plugin_instances: Dict[str, CustomBlockPlugin] = {}
        self.plugin_dir = Path("plugins/blocks")  # 插件目录

    def load_plugin(self, plugin_instance: CustomBlockPlugin) -> bool:
        """
        加载插件
        
        Args:
            plugin_instance: 插件实例
            
        Returns:
            是否加载成功
        """
        plugin_name = plugin_instance.name

        # 检查是否已加载
        if plugin_name in self.plugins:
            print(f"⚠️ 插件 '{plugin_name}' 已加载")
            return False

        try:
            # 初始化插件
            plugin_instance.initialize(self.base_service)

            # 创建插件信息
            plugin_info = BlockPlugin(
                name=plugin_name,
                version=plugin_instance.version,
                description=plugin_instance.description,
                author=plugin_instance.author,
                blocks=plugin_instance.get_registered_blocks()
            )

            # 注册插件
            self.plugins[plugin_name] = plugin_info
            self.plugin_instances[plugin_name] = plugin_instance

            # 调用激活钩子
            plugin_instance.on_activate()

            print(f"✅ 插件 '{plugin_name}' v{plugin_instance.version} 加载成功")
            print(f"   注册了 {len(plugin_info.blocks)} 个块类型")

            return True

        except Exception as e:
            print(f"❌ 插件 '{plugin_name}' 加载失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def unload_plugin(self, plugin_name: str) -> bool:
        """
        卸载插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            是否卸载成功
        """
        if plugin_name not in self.plugins:
            print(f"⚠️ 插件 '{plugin_name}' 未加载")
            return False

        try:
            plugin_instance = self.plugin_instances[plugin_name]

            # 调用停用钩子
            plugin_instance.on_deactivate()

            # 移除插件
            del self.plugins[plugin_name]
            del self.plugin_instances[plugin_name]

            print(f"✅ 插件 '{plugin_name}' 已卸载")
            return True

        except Exception as e:
            print(f"❌ 插件 '{plugin_name}' 卸载失败: {e}")
            return False

    def activate_plugin(self, plugin_name: str) -> bool:
        """激活插件"""
        if plugin_name not in self.plugins:
            return False

        plugin = self.plugins[plugin_name]
        plugin.is_active = True

        if plugin_name in self.plugin_instances:
            self.plugin_instances[plugin_name].on_activate()

        return True

    def deactivate_plugin(self, plugin_name: str) -> bool:
        """停用插件"""
        if plugin_name not in self.plugins:
            return False

        plugin = self.plugins[plugin_name]
        plugin.is_active = False

        if plugin_name in self.plugin_instances:
            self.plugin_instances[plugin_name].on_deactivate()

        return True

    def auto_discover_plugins(self) -> int:
        """
        自动发现并加载插件
        
        扫描插件目录，自动加载所有有效的插件
        
        Returns:
            成功加载的插件数量
        """
        if not self.plugin_dir.exists():
            print(f"📁 插件目录不存在: {self.plugin_dir}")
            return 0

        loaded_count = 0

        # 扫描插件目录
        for plugin_path in self.plugin_dir.glob("*/plugin.py"):
            try:
                # 动态导入插件模块
                module_path = str(plugin_path).replace("/", ".").replace("\\", ".")
                module_path = module_path.replace(".py", "")

                if module_path.startswith("."):
                    module_path = module_path[1:]

                module = importlib.import_module(module_path)

                # 查找插件类
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and
                            issubclass(obj, CustomBlockPlugin) and
                            obj != CustomBlockPlugin):

                        # 实例化并加载插件
                        plugin_instance = obj()
                        if self.load_plugin(plugin_instance):
                            loaded_count += 1

            except Exception as e:
                print(f"⚠️ 加载插件 {plugin_path} 失败: {e}")

        print(f"🔍 自动发现完成，成功加载 {loaded_count} 个插件")
        return loaded_count

    def get_plugin(self, plugin_name: str) -> Optional[BlockPlugin]:
        """获取插件信息"""
        return self.plugins.get(plugin_name)

    def get_all_plugins(self) -> List[BlockPlugin]:
        """获取所有插件"""
        return list(self.plugins.values())

    def get_active_plugins(self) -> List[BlockPlugin]:
        """获取所有激活的插件"""
        return [p for p in self.plugins.values() if p.is_active]

    def get_all_blocks(self) -> List[BlockType]:
        """获取所有插件注册的块类型"""
        all_blocks = []
        for plugin in self.plugins.values():
            if plugin.is_active:
                all_blocks.extend(plugin.blocks)
        return all_blocks

    def get_plugin_by_block(self, block_name: str) -> Optional[str]:
        """
        根据块名称查找所属插件
        
        Args:
            block_name: 块名称
            
        Returns:
            插件名称或 None
        """
        for plugin_name, plugin in self.plugins.items():
            for block in plugin.blocks:
                if block.name == block_name:
                    return plugin_name
        return None

    def get_plugin_statistics(self) -> Dict[str, Any]:
        """获取插件统计信息"""
        stats = {
            "total_plugins": len(self.plugins),
            "active_plugins": len([p for p in self.plugins.values() if p.is_active]),
            "total_blocks": sum(len(p.blocks) for p in self.plugins.values()),
            "plugins": []
        }

        for plugin in self.plugins.values():
            stats["plugins"].append({
                "name": plugin.name,
                "version": plugin.version,
                "author": plugin.author,
                "blocks_count": len(plugin.blocks),
                "is_active": plugin.is_active
            })

        return stats


# 全局插件管理器实例
def create_plugin_manager(base_service: BlockEditorService) -> BlockPluginManager:
    """创建插件管理器实例"""
    return BlockPluginManager(base_service)
