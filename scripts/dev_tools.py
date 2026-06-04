#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastBlog 开发工具脚本
集成常用的开发和调试功能

使用方法:
    python scripts/dev_tools.py --help
    
子命令:
    - generate-shared-services: 生成共享服务模块的导入代码
    - verify-routes: 验证 FastAPI 和 Next.jsNinja 路由的一致性
    - check-all-list: 检查 __all__ 列表与导入是否一致
    - check-imports: 检查导入的函数是否存在于源文件中
"""

import argparse
import ast
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set

import yaml

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class SharedServicesGenerator:
    """共享服务导入生成器"""

    def __init__(self):
        self.routes_file = project_root / 'config' / 'routes.yaml'

    def generate(self):
        """分析 routes.yaml 并生成共享服务模块的导入代码"""
        if not self.routes_file.exists():
            print(f"❌ 配置文件不存在：{self.routes_file}")
            return False

        # 读取 routes.yaml
        with open(self.routes_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        # 收集所有 handler 及其 module 信息
        handlers_by_module = defaultdict(set)
        for endpoint in data['endpoints']:
            handler = endpoint.get('handler', '')
            module = endpoint.get('module', 'unknown')
            if handler and handler != 'placeholder':
                handlers_by_module[module].add(handler)

        # 打印统计信息
        print(f"共找到 {sum(len(h) for h in handlers_by_module.values())} 个 handler")
        print(f"涉及 {len(handlers_by_module)} 个模块\n")

        # 生成 __init__.py 内容
        output = self._generate_init_content(handlers_by_module)

        # 写入文件
        output_file = project_root / 'src' / 'shared' / 'services' / '__init__.py'
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output))

        print(f"\n✓ 已生成：{output_file}")
        print(f"共 {len([h for handlers in handlers_by_module.values() for h in handlers])} 个 API 函数")
        return True

    def _generate_init_content(self, handlers_by_module: Dict[str, Set[str]]) -> List[str]:
        """生成 __init__.py 文件内容"""
        output = []
        output.append('"""')
        output.append('共享 API 服务导出模块（该模块已于V0.2淘汰）')
        output.append('')
        output.append('这样可以在两个框架之间共享业务逻辑。')
        output.append('"""')
        output.append('')
        output.append('# ============================================================================')
        output.append('# 自动生成的 API 导出 - 根据 routes.yaml 配置')
        output.append('# ============================================================================')

        return output


class RouteVerifier:
    """路由一致性验证器"""

    def __init__(self):
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_blog.settings')
        import django

        # 防止重复初始化 Django
        if not hasattr(django, '_setup_complete') or not django.apps.apps.ready:
            try:
                django.setup()
                django._setup_complete = True
            except RuntimeError as e:
                if "populate() isn't reentrant" in str(e):
                    pass  # Django 已经初始化过了
                else:
                    raise

    def verify(self):
        """验证 FastAPI 和 Next.jsNinja 路由的一致性"""
        from dataclasses import dataclass
        from typing import List

        @dataclass
        class RouteInfo:
            path: str
            method: str
            handler: str
            summary: str = ""
            tags: List[str] = None
            module: str = ""

            def __hash__(self):
                return hash((self.path, self.method))

            def __eq__(self, other):
                if not isinstance(other, RouteInfo):
                    return False
                return self.path == other.path and self.method == other.method

        # 提取 FastAPI 路由
        print("\n[1/4] 提取 FastAPI 路由...")
        try:
            from src.api.v1 import api_v1_router
            fastapi_routes = []

            if hasattr(api_v1_router, 'routes'):
                for route in api_v1_router.routes:
                    if hasattr(route, 'path') and hasattr(route, 'methods'):
                        path = route.path
                        if path.startswith('/api/v1'):
                            path = path[7:]

                        methods = list(route.methods) if route.methods else ['GET']
                        handler_name = ""
                        if hasattr(route, 'endpoint') and route.endpoint:
                            handler_name = route.endpoint.__name__

                        summary = ""
                        if hasattr(route, 'summary') and route.summary:
                            summary = route.summary

                        for method in methods:
                            if method not in ['HEAD', 'OPTIONS']:
                                fastapi_routes.append(RouteInfo(
                                    path=path,
                                    method=method,
                                    handler=handler_name,
                                    summary=summary,
                                    module='fastapi'
                                ))

            print(f"  ✓ 提取到 {len(fastapi_routes)} 条 FastAPI 路由")
        except Exception as e:
            print(f"  ❌ 提取 FastAPI 路由失败：{e}")
            return False

        # 提取 Django Ninja 路由
        print("\n[2/4] 提取 Django Ninja 路由...")
        django_routes = []
        routers = {}

        # 导入所有 routers
        router_modules = [
            ('user', 'apps.user.ninja_api'),
            ('blog', 'apps.blog.ninja_api'),
            ('category', 'apps.category.ninja_api'),
            ('media', 'apps.media.ninja_api'),
            ('settings', 'apps.settings.ninja_api'),
        ]

        for module_name, import_path in router_modules:
            try:
                module = __import__(import_path, fromlist=['router'])
                if hasattr(module, 'router'):
                    routers[module_name] = getattr(module, 'router')
            except ImportError as e:
                print(f"  ⚠ 无法导入 {module_name}: {e}")

        # 从 routers 中提取路由
        for module_name, router in routers.items():
            if hasattr(router, '_routers'):
                for path_str, operations_list in router._routers.items():
                    if isinstance(operations_list, list):
                        for operation in operations_list:
                            method = getattr(operation, 'method', 'GET')
                            handler_name = ""
                            if hasattr(operation, 'view_func') and operation.view_func:
                                handler_name = operation.view_func.__name__
                            elif hasattr(operation, 'callback') and operation.callback:
                                handler_name = operation.callback.__name__

                            summary = ""
                            if hasattr(operation, 'summary') and operation.summary:
                                summary = operation.summary

                            django_routes.append(RouteInfo(
                                path=path_str,
                                method=method,
                                handler=handler_name,
                                summary=summary,
                                module=f'django_{module_name}'
                            ))

        print(f"  ✓ 提取到 {len(django_routes)} 条 Django 路由")

        # 对比路由
        print("\n[3/4] 对比路由...")
        fastapi_map = {(r.path, r.method): r for r in fastapi_routes}
        django_map = {(r.path, r.method): r for r in django_routes}

        only_in_fastapi = []
        only_in_django = []
        mismatched_handler = []
        identical = []

        all_keys = set(fastapi_map.keys()) | set(django_map.keys())

        for key in all_keys:
            path, method = key
            fastapi_route = fastapi_map.get(key)
            django_route = django_map.get(key)

            if fastapi_route and not django_route:
                only_in_fastapi.append(fastapi_route)
            elif django_route and not fastapi_route:
                only_in_django.append(django_route)
            elif fastapi_route and django_route:
                if fastapi_route.handler != django_route.handler:
                    mismatched_handler.append({
                        'path': path,
                        'method': method,
                        'fastapi_handler': fastapi_route.handler,
                        'django_handler': django_route.handler
                    })
                else:
                    identical.append(fastapi_route)

        # 打印报告
        print("\n[4/4] 生成对比报告...")
        print("\n" + "=" * 80)
        print("路由一致性验证报告")
        print("=" * 80)

        print(f"\n统计信息:")
        print(f"  FastAPI 路由总数：{len(fastapi_routes)}")
        print(f"  Django 路由总数：{len(django_routes)}")

        print(f"\n对比结果:")
        print(f"  ✅ 完全一致的路由：{len(identical)}")
        print(f"  ⚠️  Handler 不一致：{len(mismatched_handler)}")
        print(f"  ❌ 仅 FastAPI 有：{len(only_in_fastapi)}")
        print(f"  ❌ 仅 Django 有：{len(only_in_django)}")

        if only_in_fastapi:
            print("\n" + "-" * 80)
            print("❌ 仅在 FastAPI 中存在的路由:")
            print("-" * 80)
            for route in sorted(only_in_fastapi, key=lambda x: x.path):
                print(f"  {route.method:6} {route.path:50} ({route.handler})")

        if only_in_django:
            print("\n" + "-" * 80)
            print("❌ 仅在 Django 中存在的路由:")
            print("-" * 80)
            for route in sorted(only_in_django, key=lambda x: x.path):
                print(f"  {route.method:6} {route.path:50} ({route.handler})")

        if mismatched_handler:
            print("\n" + "-" * 80)
            print("⚠️  Handler 名称不一致的路由:")
            print("-" * 80)
            for item in sorted(mismatched_handler, key=lambda x: x['path']):
                print(f"  {item['method']:6} {item['path']:50}")
                print(f"         FastAPI: {item['fastapi_handler']}")
                print(f"         Django:  {item['django_handler']}")

        # 总结
        print("\n" + "=" * 80)
        total_public = len(identical) + len(mismatched_handler) + len(only_in_fastapi) + len(only_in_django)
        consistency_rate = (len(identical) / total_public * 100) if total_public > 0 else 0

        print(f"一致性评估:")
        print(f"  公共 API 路由总数：{total_public}")
        print(f"  完全一致率：{consistency_rate:.1f}%")

        if consistency_rate >= 95:
            print(f"  ✅ 路由一致性良好!")
        elif consistency_rate >= 80:
            print(f"  ⚠️  路由一致性较好，但有少量差异需要处理")
        else:
            print(f"  ❌ 路由一致性较差，建议进行统一")

        print("=" * 80 + "\n")

        return True


class AllListChecker:
    """__all__ 列表检查器"""

    def __init__(self):
        self.init_file = project_root / 'src' / 'shared' / 'services' / '__init__.py'

    def check(self):
        """检查 __all__ 列表与导入是否一致"""
        if not self.init_file.exists():
            print(f"❌ 文件不存在：{self.init_file}")
            return False

        with open(self.init_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取所有实际导入的函数
        imported_funcs = set()
        import_pattern = r'from\s+[\w.]+\s+import\s+\(([^)]+)\)'
        for match in re.finditer(import_pattern, content, re.DOTALL):
            imports_str = match.group(1)
            for line in imports_str.split('\n'):
                func_name = line.strip().rstrip(',')
                if func_name and not func_name.startswith('#'):
                    imported_funcs.add(func_name)

        # 提取 __all__ 列表中的所有函数
        all_funcs = set()
        all_pattern = r'__all__\s*=\s*\[(.*?)\]'
        all_match = re.search(all_pattern, content, re.DOTALL)
        if all_match:
            all_str = all_match.group(1)
            for line in all_str.split('\n'):
                func_match = re.search(r"'([^']+)'", line)
                if func_match:
                    all_funcs.add(func_match.group(1))

        print(f"实际导入的函数数量：{len(imported_funcs)}")
        print(f"__all__ 中的函数数量：{len(all_funcs)}")

        # 找出在 __all__ 中但不在实际导入中的函数
        missing_imports = all_funcs - imported_funcs
        if missing_imports:
            print(f"\n❌ 发现 {len(missing_imports)} 个函数在 __all__ 中但未在实际 import 中:")
            for func in sorted(missing_imports):
                print(f"    - {func}")
        else:
            print("\n✅ __all__ 中的所有函数都在实际 import 中存在！")

        # 找出在实际导入中但不在 __all__ 中的函数
        extra_imports = imported_funcs - all_funcs
        if extra_imports:
            print(f"\n⚠️  发现 {len(extra_imports)} 个函数在实际 import 中但未在 __all__ 中:")
            for func in sorted(extra_imports):
                print(f"    - {func}")

        return True


class ImportChecker:
    """导入检查器"""

    def __init__(self):
        self.init_file = project_root / 'src' / 'shared' / 'services' / '__init__.py'
        self.module_paths = {
            'src.api.v1.articles': 'src/api/v1/articles.py',
            'src.api.v1.dashboard': 'src/api/v1/dashboard.py',
            'src.api.v1.media': 'src/api/v1/media.py',
            'src.api.v1.notifications': 'src/api/v1/notifications.py',
            'apps.category.views': 'apps/category/views.py',
            'apps.user.views': 'apps/user/views.py',
        }

    def _get_module_functions(self, file_path: Path) -> Set[str]:
        """获取模块中所有函数名"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
            funcs = []
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    funcs.append(node.name)
            return set(funcs)
        except Exception as e:
            print(f"❌ 读取 {file_path} 失败：{e}")
            return set()

    def check(self):
        """检查导入的函数是否存在于源文件中"""
        # 收集所有实际存在的函数
        all_existing_funcs = {}
        for module_name, file_path in self.module_paths.items():
            file_path = project_root / file_path
            if file_path.exists():
                all_existing_funcs[module_name] = self._get_module_functions(file_path)
                print(f"✓ {module_name}: {len(all_existing_funcs[module_name])} 个函数")
            else:
                print(f"⚠ {module_name}: 文件不存在")
                all_existing_funcs[module_name] = set()

        # 读取 __init__.py 文件，提取所有导入的函数
        if not self.init_file.exists():
            print(f"❌ 文件不存在：{self.init_file}")
            return False

        with open(self.init_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 解析导入语句
        imported_funcs = {}
        current_module = None
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('from ') and ' import ' in line:
                try:
                    parts = line.split(' from ')[1].split(' import ')[0]
                    current_module = parts
                except IndexError:
                    continue
            elif line.startswith('from ') and '(' in line:
                try:
                    parts = line.split(' from ')[1].split(' import (')[0]
                    current_module = parts
                except IndexError:
                    continue
            elif current_module and line.endswith(','):
                func_name = line.rstrip(',').strip()
                if func_name and not func_name.startswith('#'):
                    if current_module not in imported_funcs:
                        imported_funcs[current_module] = []
                    imported_funcs[current_module].append(func_name)
            elif current_module and ')' in line:
                func_name = line.rstrip(')').strip().rstrip(',')
                if func_name and not func_name.startswith('#'):
                    if current_module not in imported_funcs:
                        imported_funcs[current_module] = []
                    imported_funcs[current_module].append(func_name)

        # 检查哪些函数不存在
        print("\n" + "=" * 80)
        print("检查结果:")
        print("=" * 80)

        missing_funcs = []
        for module_name, funcs in imported_funcs.items():
            if module_name in all_existing_funcs:
                existing = all_existing_funcs[module_name]
                for func in funcs:
                    if func not in existing:
                        missing_funcs.append((module_name, func))
                        print(f"❌ {module_name}.{func} - 不存在")
            else:
                for func in funcs:
                    missing_funcs.append((module_name, func))
                    print(f"❌ {module_name}.{func} - 模块不存在")

        if not missing_funcs:
            print("\n✅ 所有导入的函数都存在！")
        else:
            print(f"\n共发现 {len(missing_funcs)} 个不存在的函数")

            print("\n" + "=" * 80)
            print("建议从 __all__ 中移除以下函数:")
            print("=" * 80)
            for module_name, func in missing_funcs:
                print(f"    '{func}',")

        return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='FastBlog 开发工具脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python scripts/dev_tools.py generate-shared-services
  python scripts/dev_tools.py verify-routes
  python scripts/dev_tools.py check-all-list
  python scripts/dev_tools.py check-imports
        """
    )

    parser.add_argument(
        'command',
        choices=['generate-shared-services', 'verify-routes', 'check-all-list', 'check-imports'],
        help='要执行的命令'
    )

    args = parser.parse_args()

    print("=" * 80)
    print(f"执行命令：{args.command}")
    print("=" * 80)

    try:
        if args.command == 'generate-shared-services':
            generator = SharedServicesGenerator()
            success = generator.generate()

        elif args.command == 'verify-routes':
            verifier = RouteVerifier()
            success = verifier.verify()

        elif args.command == 'check-all-list':
            checker = AllListChecker()
            success = checker.check()

        elif args.command == 'check-imports':
            checker = ImportChecker()
            success = checker.check()

        else:
            print(f"❌ 未知命令：{args.command}")
            success = False

        if success:
            print("\n✅ 命令执行完成!")
            sys.exit(0)
        else:
            print("\n❌ 命令执行失败!")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ 执行出错：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
