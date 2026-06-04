#!/usr/bin/env python3
"""
FastBlog 路由管理工具

集成所有路由相关的检查和生成功能

使用方法:
    python scripts/route_tools.py --help
    
子命令:
    - check-conflicts: 检查路由冲突和重复
    - check-routers: 检查路由模块的 router 属性
    - find-routers: 扫描并查找所有路由器
    - generate-registry: 生成路由注册表配置
    - verify: 验证路由一致性
"""

import argparse
import importlib
import sys
from collections import defaultdict
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class RouteConflictChecker:
    """路由冲突检查器"""

    def __init__(self):
        """初始化并加载应用"""
        try:
            from src.app import create_app
            from src.setting import ProductionConfig

            self.app = create_app(ProductionConfig())

            if self.app is None:
                print("Error: app is None. The application failed to initialize.")
                sys.exit(1)
        except Exception as e:
            print(f"Error importing or creating app: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

    def check_duplicate_routes(self):
        """检测完全相同的 (method, path) 对"""
        print("\n" + "=" * 80)
        print("检查重复路由...")
        print("=" * 80)

        routes_map = defaultdict(list)
        duplicates_found = False

        for route in self.app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                for method in route.methods:
                    if method in ['HEAD', 'OPTIONS']:
                        continue
                    key = (method, route.path)
                    endpoint_name = route.endpoint.__name__ if hasattr(route.endpoint, '__name__') else str(
                        route.endpoint)
                    routes_map[key].append(endpoint_name)

        for (method, path), endpoints in routes_map.items():
            if len(endpoints) > 1:
                duplicates_found = True
                print(f"\n❌ 发现重复路由: {method} {path}")
                for endpoint in endpoints:
                    print(f"   - {endpoint}")

        if not duplicates_found:
            print("\n✅ 未发现重复路由")

        return not duplicates_found

    def check_path_conflicts(self):
        """检测路径参数与具体路径的冲突"""
        print("\n" + "=" * 80)
        print("检查路径冲突...")
        print("=" * 80)

        # 收集所有路由路径
        static_paths = []
        dynamic_paths = []

        for route in self.app.routes:
            if hasattr(route, 'path'):
                path = route.path
                if '{' in path:
                    dynamic_paths.append((path, route))
                else:
                    static_paths.append((path, route))

        conflicts_found = False

        # 检查静态路径是否是动态路径的前缀
        for static_path, static_route in static_paths:
            for dynamic_path, dynamic_route in dynamic_paths:
                # 将动态路径转换为正则模式
                pattern = dynamic_path.replace('{', '<').replace('}', '>')
                parts_dynamic = pattern.split('/')
                parts_static = static_path.split('/')

                # 检查是否可能冲突
                if len(parts_static) == len(parts_dynamic):
                    match = True
                    for s_part, d_part in zip(parts_static, parts_dynamic):
                        if d_part.startswith('<') and d_part.endswith('>'):
                            continue  # 动态参数，匹配任何值
                        elif s_part != d_part:
                            match = False
                            break

                    if match:
                        conflicts_found = True
                        static_endpoint = static_route.endpoint.__name__ if hasattr(static_route.endpoint,
                                                                                    '__name__') else str(
                            static_route.endpoint)
                        dynamic_endpoint = dynamic_route.endpoint.__name__ if hasattr(dynamic_route.endpoint,
                                                                                      '__name__') else str(
                            dynamic_route.endpoint)
                        print(f"\n⚠️  潜在路径冲突:")
                        print(f"   静态路径: {static_path} -> {static_endpoint}")
                        print(f"   动态路径: {dynamic_path} -> {dynamic_endpoint}")
                        print(f"   建议: 确保静态路径在动态路径之前注册")

        if not conflicts_found:
            print("\n✅ 未发现路径冲突")

        return not conflicts_found

    def check_path_redundancy(self):
        """检测路径冗余（如重复的单词）"""
        print("\n" + "=" * 80)
        print("检查路径冗余...")
        print("=" * 80)

        redundancy_found = False

        for route in self.app.routes:
            if hasattr(route, 'path'):
                path = route.path
                parts = path.split('/')

                # 检查是否有连续的重复部分
                for i in range(len(parts) - 1):
                    if parts[i] and parts[i] == parts[i + 1]:
                        redundancy_found = True
                        endpoint_name = route.endpoint.__name__ if hasattr(route.endpoint, '__name__') else str(
                            route.endpoint)
                        print(f"\n❌ 发现路径冗余: {path}")
                        print(f"   重复部分: '{parts[i]}'")
                        print(f"   端点: {endpoint_name}")
                        break

        if not redundancy_found:
            print("\n✅ 未发现路径冗余")

        return not redundancy_found

    def check_naming_consistency(self):
        """检查路由命名一致性"""
        print("\n" + "=" * 80)
        print("检查路由命名一致性...")
        print("=" * 80)

        issues_found = False

        for route in self.app.routes:
            if hasattr(route, 'path'):
                path = route.path

                # 检查是否使用了下划线而不是连字符
                if '_' in path and '/api/' in path:
                    issues_found = True
                    endpoint_name = route.endpoint.__name__ if hasattr(route.endpoint, '__name__') else str(
                        route.endpoint)
                    suggested = path.replace('_', '-')
                    print(f"\n⚠️  命名不一致: {path}")
                    print(f"   建议使用连字符: {suggested}")
                    print(f"   端点: {endpoint_name}")

        if not issues_found:
            print("\n✅ 路由命名一致性好")

        return not issues_found

    def generate_report(self):
        """生成完整的检测报告"""
        print("\n" + "=" * 80)
        print("路由自动检测报告")
        print("=" * 80)
        print(f"应用路由总数: {len(self.app.routes)}")

        results = {
            'duplicate_routes': self.check_duplicate_routes(),
            'path_conflicts': self.check_path_conflicts(),
            'path_redundancy': self.check_path_redundancy(),
            'naming_consistency': self.check_naming_consistency(),
        }

        print("\n" + "=" * 80)
        print("检测总结")
        print("=" * 80)

        all_passed = all(results.values())

        for check_name, passed in results.items():
            status = "✅ 通过" if passed else "❌ 失败"
            print(f"{check_name}: {status}")

        print("\n" + "=" * 80)
        if all_passed:
            print("🎉 所有检查通过！路由配置良好。")
        else:
            print("⚠️  发现一些问题，请查看上述详情进行修复。")
        print("=" * 80)

        return all_passed


class RouterChecker:
    """路由器检查器"""

    def check_all_routers(self):
        """检查所有路由模块是否有 router 属性"""
        # 从 app.py 导入路由注册表
        from src.app import ROUTE_REGISTRY

        print("检查所有路由模块的 router 属性...")
        print("=" * 60)

        failed_modules = []
        success_modules = []

        for module_path, prefix, tags, required in ROUTE_REGISTRY:
            try:
                mod = importlib.import_module(module_path)
                router = getattr(mod, "router", None)
                if router is None:
                    status = "❌ FAIL"
                    failed_modules.append((module_path, prefix, tags, required))
                else:
                    status = "✅ OK"
                    success_modules.append(module_path)
                print(f"{status} | {module_path:50s} | prefix: {prefix:30s} | required: {required}")
            except ImportError as e:
                status = "❌ IMPORT ERROR"
                failed_modules.append((module_path, prefix, tags, required))
                print(f"{status} | {module_path:50s} | {e}")
            except Exception as e:
                status = "❌ ERROR"
                failed_modules.append((module_path, prefix, tags, required))
                print(f"{status} | {module_path:50s} | {e}")

        print("\n" + "=" * 60)
        print(f"成功: {len(success_modules)}, 失败: {len(failed_modules)}")

        if failed_modules:
            print("\n失败的模块:")
            for module_path, prefix, tags, required in failed_modules:
                print(f"  - {module_path} (required: {required})")

        return len(failed_modules) == 0

    def find_routers(self):
        """扫描所有 API 模块，找出有 router 属性的模块"""
        api_v1_path = Path("src/api/v1")
        modules_with_router = []

        print("扫描 src/api/v1 目录下的所有模块...")
        print("=" * 80)

        # 遍历所有子目录
        for item in api_v1_path.iterdir():
            if item.is_dir() and not item.name.startswith('_'):
                # 检查目录下是否有 __init__.py 或 .py 文件
                init_file = item / "__init__.py"

                # 尝试导入目录（如果有 __init__.py）
                if init_file.exists():
                    module_name = f"src.api.v1.{item.name}"
                    try:
                        mod = importlib.import_module(module_name)
                        router = getattr(mod, "router", None)
                        if router:
                            modules_with_router.append((module_name, item.name))
                            print(f"✅ {module_name:50s} - 找到 router")
                    except Exception as e:
                        print(f"❌ {module_name:50s} - 导入失败: {e}")

                # 检查目录下的 .py 文件
                for py_file in item.glob("*.py"):
                    if py_file.name.startswith('_'):
                        continue

                    module_name = f"src.api.v1.{item.name}.{py_file.stem}"
                    try:
                        mod = importlib.import_module(module_name)
                        router = getattr(mod, "router", None)
                        if router:
                            modules_with_router.append((module_name, f"{item.name}/{py_file.name}"))
                            print(f"✅ {module_name:50s} - 找到 router")
                    except Exception:
                        # 忽略导入错误，只报告成功找到的
                        pass

        print("\n" + "=" * 80)
        print(f"共找到 {len(modules_with_router)} 个带有 router 的模块\n")

        print("可用的模块列表（可用于 ROUTE_REGISTRY）:")
        print("-" * 80)
        for module_name, file_path in sorted(modules_with_router):
            print(f'    ("{module_name}", "/api/v1", ["{module_name.split(".")[-1]}"], False),')

        return modules_with_router

    def generate_registry(self):
        """生成正确的 ROUTE_REGISTRY 配置"""
        api_v1_path = Path("src/api/v1")
        modules_with_router = []

        # 遍历所有子目录
        for item in api_v1_path.iterdir():
            if item.is_dir() and not item.name.startswith('_'):
                # 检查目录下是否有 __init__.py
                init_file = item / "__init__.py"

                if init_file.exists():
                    module_name = f"src.api.v1.{item.name}"
                    try:
                        mod = importlib.import_module(module_name)
                        router = getattr(mod, "router", None)
                        if router:
                            modules_with_router.append((module_name, item.name))
                    except Exception:
                        pass

                # 检查目录下的 .py 文件
                for py_file in sorted(item.glob("*.py")):
                    if py_file.name.startswith('_'):
                        continue

                    module_name = f"src.api.v1.{item.name}.{py_file.stem}"
                    try:
                        mod = importlib.import_module(module_name)
                        router = getattr(mod, "router", None)
                        if router:
                            modules_with_router.append((module_name, f"{item.name}/{py_file.name}"))
                    except Exception:
                        pass

        # 核心模块（必需）
        core_modules = [
            "src.api.v1.users.users",
            "src.api.v1.__init__",
            "src.api.v1.content_management.category_management",
            "src.api.v1.dashboard.dashboard",
            "src.api.v1.core.home",
        ]

        # 生成配置
        print("# ---------- 路由自动发现 ----------")
        print("# 配置表：(模块路径, 前缀, 标签列表, 是否必需)")
        print("ROUTE_REGISTRY = [")
        print("    # 核心模块（必需）")

        for module_name, _ in modules_with_router:
            if module_name in core_modules:
                prefix_map = {
                    "src.api.v1.users.users": ("/api/v1/users", ["users"]),
                    "src.api.v1.__init__": ("", []),
                    "src.api.v1.content_management.category_management": ("/api/v1/categories", ["categories"]),
                    "src.api.v1.dashboard.dashboard": ("/api/v1/dashboard", ["dashboard"]),
                    "src.api.v1.core.home": ("/api/v1", ["home"]),
                }
                prefix, tags = prefix_map.get(module_name, ("/api/v1", [module_name.split(".")[-1]]))
                print(f'    ("{module_name}", "{prefix}", {tags}, True),')

        print("    # 功能模块（可选加载，失败仅警告）")

        # 添加其他模块
        for module_name, file_path in sorted(modules_with_router):
            if module_name not in core_modules:
                # 简化标签名
                tag = module_name.split(".")[-1].replace("_", "-")
                print(f'    ("{module_name}", "/api/v1", ["{tag}"], False),')

        print("]")


def main():
    """主入口函数"""
    parser = argparse.ArgumentParser(
        description='FastBlog 路由管理工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python scripts/route_tools.py check-conflicts
  python scripts/route_tools.py check-routers
  python scripts/route_tools.py find-routers
  python scripts/route_tools.py generate-registry
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='要执行的命令')

    # check-conflicts 命令
    subparsers.add_parser('check-conflicts', help='检查路由冲突和重复')

    # check-routers 命令
    subparsers.add_parser('check-routers', help='检查路由模块的 router 属性')

    # find-routers 命令
    subparsers.add_parser('find-routers', help='扫描并查找所有路由器')

    # generate-registry 命令
    subparsers.add_parser('generate-registry', help='生成路由注册表配置')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == 'check-conflicts':
            checker = RouteConflictChecker()
            success = checker.generate_report()
            sys.exit(0 if success else 1)

        elif args.command == 'check-routers':
            checker = RouterChecker()
            success = checker.check_all_routers()
            sys.exit(0 if success else 1)

        elif args.command == 'find-routers':
            checker = RouterChecker()
            checker.find_routers()

        elif args.command == 'generate-registry':
            checker = RouterChecker()
            checker.generate_registry()

        else:
            print(f"❌ 未知命令：{args.command}")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ 执行出错：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
