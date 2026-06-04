"""
插件依赖管理器
负责解析、验证和管理插件依赖关系
"""

from pathlib import Path
from typing import Dict, Any, List, Set, Tuple

from shared.services.plugins.plugin_manager.marketplace import plugin_marketplace


class DependencyManager:
    """
    依赖管理器
    
    功能:
    1. 依赖解析
    2. 版本冲突检测
    3. 循环依赖检测
    4. 依赖树生成
    """

    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = Path(plugins_dir)

    def resolve_dependencies(self, plugin_slug: str) -> Tuple[bool, str, List[str]]:
        """
        解析插件的所有依赖
        
        Args:
            plugin_slug: 插件slug
            
        Returns:
            (成功标志, 消息, 依赖列表)
        """
        try:
            # 获取插件元数据
            plugin = plugin_marketplace.get_plugin_detail(plugin_slug)

            if not plugin:
                return False, f"插件 '{plugin_slug}' 不存在", []

            dependencies = plugin.get('dependencies', [])

            if not dependencies:
                return True, "无依赖", []

            # 递归解析所有依赖
            resolved_deps = []
            visited = set()

            success, message = self._resolve_recursive(
                plugin_slug, dependencies, resolved_deps, visited
            )

            if not success:
                return False, message, []

            return True, "依赖解析成功", resolved_deps

        except Exception as e:
            return False, f"依赖解析失败: {str(e)}", []

    def _resolve_recursive(
            self,
            parent_slug: str,
            dependencies: List[str],
            resolved: List[str],
            visited: Set[str]
    ) -> Tuple[bool, str]:
        """
        递归解析依赖
        
        Args:
            parent_slug: 父插件slug
            dependencies: 依赖列表
            resolved: 已解析的依赖
            visited: 已访问的节点(用于检测循环依赖)
            
        Returns:
            (成功标志, 消息)
        """
        # 检测循环依赖
        if parent_slug in visited:
            return False, f"检测到循环依赖: {' -> '.join(list(visited))} -> {parent_slug}"

        visited.add(parent_slug)

        for dep_slug in dependencies:
            # 检查是否已解析
            if dep_slug in resolved:
                continue

            # 检查依赖是否存在
            dep_plugin = plugin_marketplace.get_plugin_detail(dep_slug)

            if not dep_plugin:
                return False, f"缺少依赖: {dep_slug}"

            # 检查依赖的版本要求
            version_check = self._check_version_requirement(dep_plugin)
            if not version_check[0]:
                return False, version_check[1]

            # 递归解析依赖的依赖
            dep_dependencies = dep_plugin.get('dependencies', [])
            if dep_dependencies:
                success, message = self._resolve_recursive(
                    dep_slug, dep_dependencies, resolved, visited.copy()
                )

                if not success:
                    return False, message

            # 添加到已解析列表
            resolved.append(dep_slug)

        visited.discard(parent_slug)
        return True, "解析成功"

    def _check_version_requirement(self, plugin: Dict[str, Any]) -> Tuple[bool, str]:
        """
        检查插件版本要求
        
        Args:
            plugin: 插件元数据
            
        Returns:
            (满足标志, 消息)
        """
        try:
            from packaging import version as pkg_version
            import sys

            requires = plugin.get('requires', {})

            # 检查FastBlog版本
            fastblog_req = requires.get('fastblog')
            if fastblog_req:
                # 获取当前FastBlog版本
                current_version = self._get_fastblog_version()

                # 解析版本要求(支持 >=, <=, ==, >, <, != 等运算符)
                if not self._check_version_constraint(current_version, fastblog_req):
                    return False, f"FastBlog版本不满足: 需要 {fastblog_req}, 当前 {current_version}"

            # 检查Python版本
            python_req = requires.get('python')
            if python_req:
                current_python = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

                if not self._check_version_constraint(current_python, python_req):
                    return False, f"Python版本不满足: 需要 {python_req}, 当前 {current_python}"

            return True, "版本要求满足"

        except ImportError:
            # 如果没有packaging库,使用简化版本检查
            return self._simple_version_check(plugin)
        except Exception as e:
            return False, f"版本检查失败: {str(e)}"

    def detect_conflicts(self, plugin_slug: str) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        检测插件冲突
        
        Args:
            plugin_slug: 要检查的插件slug
            
        Returns:
            (有冲突标志, 冲突列表)
        """
        conflicts = []

        # 获取目标插件信息
        target_plugin = plugin_marketplace.get_plugin_detail(plugin_slug)
        if not target_plugin:
            return False, []

        # 获取所有已安装插件
        installed_plugins = plugin_marketplace.discover_plugins()

        # 检查冲突
        for installed in installed_plugins:
            if installed['slug'] == plugin_slug:
                continue

            # 检查是否有互斥声明
            target_excludes = target_plugin.get('excludes', [])
            if installed['slug'] in target_excludes:
                conflicts.append({
                    'type': 'mutual_exclusion',
                    'plugin': installed['slug'],
                    'message': f"与插件 '{installed['name']}' 互斥"
                })

            installed_excludes = installed.get('excludes', [])
            if plugin_slug in installed_excludes:
                conflicts.append({
                    'type': 'mutual_exclusion',
                    'plugin': installed['slug'],
                    'message': f"插件 '{installed['name']}' 声明与此插件互斥"
                })

            # 检查相同功能冲突
            target_features = set(target_plugin.get('provides', []))
            installed_features = set(installed.get('provides', []))

            common_features = target_features & installed_features
            if common_features:
                conflicts.append({
                    'type': 'feature_conflict',
                    'plugin': installed['slug'],
                    'features': list(common_features),
                    'message': f"与插件 '{installed['name']}' 存在功能重叠: {', '.join(common_features)}"
                })

        return len(conflicts) > 0, conflicts

    def get_dependency_tree(self, plugin_slug: str, max_depth: int = 5) -> Dict[str, Any]:
        """
        生成依赖树
        
        Args:
            plugin_slug: 插件slug
            max_depth: 最大深度
            
        Returns:
            依赖树结构
        """
        plugin = plugin_marketplace.get_plugin_detail(plugin_slug)

        if not plugin:
            return {"error": f"插件 '{plugin_slug}' 不存在"}

        tree = {
            "slug": plugin_slug,
            "name": plugin.get('name', ''),
            "version": plugin.get('version', ''),
            "dependencies": []
        }

        self._build_tree(plugin_slug, tree, 0, max_depth, set())

        return tree

    def _build_tree(
            self,
            slug: str,
            node: Dict[str, Any],
            current_depth: int,
            max_depth: int,
            visited: Set[str]
    ):
        """
        递归构建依赖树
        
        Args:
            slug: 插件slug
            node: 当前节点
            current_depth: 当前深度
            max_depth: 最大深度
            visited: 已访问节点
        """
        if current_depth >= max_depth or slug in visited:
            return

        visited.add(slug)

        plugin = plugin_marketplace.get_plugin_detail(slug)
        if not plugin:
            return

        dependencies = plugin.get('dependencies', [])

        for dep_slug in dependencies:
            dep_plugin = plugin_marketplace.get_plugin_detail(dep_slug)

            if not dep_plugin:
                node["dependencies"].append({
                    "slug": dep_slug,
                    "name": dep_slug,
                    "version": "未知",
                    "status": "missing",
                    "dependencies": []
                })
                continue

            dep_node = {
                "slug": dep_slug,
                "name": dep_plugin.get('name', ''),
                "version": dep_plugin.get('version', ''),
                "status": "installed" if (self.plugins_dir / dep_slug).exists() else "not_installed",
                "dependencies": []
            }

            node["dependencies"].append(dep_node)

            # 递归处理子依赖
            self._build_tree(dep_slug, dep_node, current_depth + 1, max_depth, visited.copy())

    def check_all_dependencies(self) -> Dict[str, Any]:
        """
        检查所有已安装插件的依赖状态
        
        Returns:
            依赖状态报告
        """
        installed = plugin_marketplace.discover_plugins()

        report = {
            "total": len(installed),
            "healthy": 0,
            "warnings": [],
            "errors": []
        }

        for plugin in installed:
            slug = plugin['slug']

            # 检查依赖
            success, message, deps = self.resolve_dependencies(slug)

            if not success:
                report["errors"].append({
                    "plugin": slug,
                    "error": message
                })
            else:
                report["healthy"] += 1

                # 检查是否有警告(如可选依赖缺失)
                optional_deps = plugin.get('optional_dependencies', [])
                missing_optional = [
                    dep for dep in optional_deps
                    if not (self.plugins_dir / dep).exists()
                ]

                if missing_optional:
                    report["warnings"].append({
                        "plugin": slug,
                        "warning": f"缺少可选依赖: {', '.join(missing_optional)}"
                    })

        return report

    def _get_fastblog_version(self) -> str:
        """
        获取当前FastBlog版本
        
        Returns:
            版本号字符串
        """
        try:
            # 从version.txt读取
            version_file = Path(__file__).parent.parent.parent / "version.txt"
            if version_file.exists():
                with open(version_file, 'r') as f:
                    return f.read().strip()
        except:
            pass

        # 默认版本
        return "1.0.0"

    def _check_version_constraint(self, current_version: str, constraint: str) -> bool:
        """
        检查版本是否满足约束条件
        
        Args:
            current_version: 当前版本
            constraint: 版本约束(如 >=1.0.0, <2.0.0, ==1.5.0)
            
        Returns:
            是否满足约束
        """
        try:
            from packaging import version as pkg_version
            from packaging.specifiers import SpecifierSet

            # 使用packaging库解析版本约束
            spec = SpecifierSet(constraint)
            return pkg_version.parse(current_version) in spec

        except ImportError:
            # 简化版本检查(不支持复杂约束)
            return self._simple_version_compare(current_version, constraint)

    def _simple_version_compare(self, current: str, required: str) -> bool:
        """
        简化版本比较(当packaging库不可用时使用)
        
        Args:
            current: 当前版本
            required: 要求版本
            
        Returns:
            是否满足要求
        """
        try:
            # 简单处理:只支持 >= 和 ==
            if required.startswith('>='):
                req_ver = required[2:].strip()
                return self._version_gte(current, req_ver)
            elif required.startswith('=='):
                req_ver = required[2:].strip()
                return current == req_ver
            else:
                # 默认为 >=
                return self._version_gte(current, required)
        except:
            return True  # 出错时默认通过

    def _version_gte(self, v1: str, v2: str) -> bool:
        """
        比较版本号 v1 >= v2
        
        Args:
            v1: 版本1
            v2: 版本2
            
        Returns:
            v1 >= v2
        """
        try:
            v1_parts = [int(x) for x in v1.split('.')]
            v2_parts = [int(x) for x in v2.split('.')]

            # 补齐长度
            while len(v1_parts) < len(v2_parts):
                v1_parts.append(0)
            while len(v2_parts) < len(v1_parts):
                v2_parts.append(0)

            return v1_parts >= v2_parts
        except:
            return True

    def _simple_version_check(self, plugin: Dict[str, Any]) -> Tuple[bool, str]:
        """
        简化版本检查(不使用packaging库)
        
        Args:
            plugin: 插件元数据
            
        Returns:
            (满足标志, 消息)
        """
        import sys

        requires = plugin.get('requires', {})

        # 检查FastBlog版本
        fastblog_req = requires.get('fastblog')
        if fastblog_req:
            current_version = self._get_fastblog_version()
            if not self._simple_version_compare(current_version, fastblog_req):
                return False, f"FastBlog版本可能不满足: 需要 {fastblog_req}, 当前 {current_version}"

        # 检查Python版本
        python_req = requires.get('python')
        if python_req:
            current_python = f"{sys.version_info.major}.{sys.version_info.minor}"
            if not self._simple_version_compare(current_python, python_req):
                return False, f"Python版本可能不满足: 需要 {python_req}, 当前 {current_python}"

        return True, "版本要求满足(简化检查)"


# 全局实例
dependency_manager = DependencyManager()
