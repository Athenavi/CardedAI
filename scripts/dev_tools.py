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
        output = []
        output.append('# ============================================================================')
        output.append('# 该模块已废弃')
        output.append('# ============================================================================')

        return output

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
    """路由一致性验证器（已废弃 - Django 支持已移除）"""

    def __init__(self):
        print("[RouteVerifier] Django 支持已移除，路由验证功能不可用")
        pass

    def verify(self):
        print("[RouteVerifier] Django 支持已移除，跳过路由验证")
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
