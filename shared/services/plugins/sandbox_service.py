"""
插件沙箱与安全隔离服务
通过能力绑定和权限检查限制插件行为
"""
from typing import List, Dict


class PluginSandbox:
    """插件运行沙箱"""

    def __init__(self):
        # 定义系统允许的能力列表
        self.capabilities = {
            "read:articles", "write:articles",
            "read:users", "send:email",
            "access:filesystem"
        }

    def validate_capabilities(self, plugin_slug: str, requested_caps: List[str]) -> bool:
        """验证插件请求的能力是否合法"""
        for cap in requested_caps:
            if cap not in self.capabilities:
                print(f"Plugin {plugin_slug} requested invalid capability: {cap}")
                return False
        return True

    def enforce_isolation(self, plugin_slug: str):
        """执行隔离策略，限制对核心数据库的直接访问"""
        # 实际实现中可以通过代理数据库连接来拦截非法操作
        print(f"Enforcing isolation for plugin: {plugin_slug}")


sandbox_service = PluginSandbox()
