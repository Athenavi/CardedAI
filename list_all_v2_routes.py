"""
列出系统中所有注册的路由并保存到文件
按模块分组显示，包含路径、方法、端点函数等信息
"""
import io
import sys
from pathlib import Path

# 设置标准输出编码为 UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from src.app import create_app
    from src.setting import ProductionConfig

    # 创建应用实例
    app = create_app(ProductionConfig())

    if app is None:
        print("Error: app is None. The application failed to initialize.")
        sys.exit(1)
except Exception as e:
    print(f"Error importing or creating app: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

# 输出文件路径
output_file = project_root / "all_routes_list.txt"

print("=" * 140)
print("系统所有注册路由列表")
print("=" * 140)
print(f"\n正在生成路由列表并保存到: {output_file}\n")

all_routes = []

try:
    for route in app.routes:
        if not hasattr(route, 'path'):
            continue

        path = route.path
        methods = list(route.methods) if hasattr(route, 'methods') and route.methods else ['N/A']

        # 获取 endpoint 信息
        endpoint_name = "N/A"
        module_name = "unknown"
        if hasattr(route, 'endpoint'):
            if hasattr(route.endpoint, '__name__'):
                endpoint_name = route.endpoint.__name__
            if hasattr(route.endpoint, '__module__'):
                module_name = route.endpoint.__module__

        # 判断是否是通配符路由
        is_wildcard = '{' in path

        all_routes.append({
            'path': path,
            'methods': methods,
            'endpoint': endpoint_name,
            'module': module_name,
            'is_wildcard': is_wildcard
        })
except Exception as e:
    print(f"Error processing routes: {e}")
    import traceback

    traceback.print_exc()

# 按模块和路径排序
all_routes.sort(key=lambda x: (x['module'], x['path']))

# 统计信息
total_count = len(all_routes)
wildcard_count = sum(1 for r in all_routes if r['is_wildcard'])
specific_count = total_count - wildcard_count
wildcard_pct = (wildcard_count / total_count * 100) if total_count > 0 else 0

# 写入文件
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("=" * 140 + "\n")
    f.write("系统所有注册路由列表\n")
    f.write("=" * 140 + "\n\n")

    current_module = None
    route_index = 0

    for route_info in all_routes:
        if route_info['module'] != current_module:
            current_module = route_info['module']
            f.write(f"\n{'─' * 140}\n")
            f.write(f"模块: {current_module}\n")
            f.write(f"{'─' * 140}\n")

        route_index += 1
        marker = "[W]" if route_info['is_wildcard'] else "[S]"
        methods_str = ','.join(route_info['methods'])

        f.write(
            f"{marker} {route_index:5d}. {route_info['path']:80s} [{methods_str:10s}] -> {route_info['endpoint']}\n")

    f.write(f"\n{'=' * 140}\n")
    f.write(f"路由统计:\n")
    f.write(f"  总路由数:     {total_count}\n")
    f.write(f"  具体路由:     {specific_count}\n")
    f.write(f"  通配符路由:   {wildcard_count}\n")
    if total_count > 0:
        wildcard_pct = wildcard_count / total_count * 100
        f.write(f"  通配符占比:   {wildcard_pct:.1f}%\n")
    f.write(f"{'=' * 140}\n")

    # 按模块统计
    f.write("\n按模块统计路由数量:\n")
    f.write("-" * 100 + "\n")

    module_stats = {}
    for route_info in all_routes:
        module = route_info['module']
        if module not in module_stats:
            module_stats[module] = {'total': 0, 'wildcard': 0, 'specific': 0}
        module_stats[module]['total'] += 1
        if route_info['is_wildcard']:
            module_stats[module]['wildcard'] += 1
        else:
            module_stats[module]['specific'] += 1

    # 按总路由数排序
    sorted_modules = sorted(module_stats.items(), key=lambda x: x[1]['total'], reverse=True)

    for module, stats in sorted_modules[:30]:  # 显示前30个
        wildcard_pct = stats['wildcard'] / stats['total'] * 100 if stats['total'] > 0 else 0
        f.write(
            f"  {stats['total']:4d} 个路由 ({stats['specific']:3d} 具体 + {stats['wildcard']:3d} 通配符, {wildcard_pct:5.1f}%) - {module}\n")

    if len(sorted_modules) > 30:
        f.write(f"  ... 还有 {len(sorted_modules) - 30} 个模块\n")

    f.write(f"\n{'=' * 140}\n")
    f.write("说明:\n")
    f.write("  [S] 具体路由 - 固定路径，不会与其他路由冲突\n")
    f.write("  [W] 通配符路由 - 包含 {{placeholder}}，可能拦截其他路由\n")
    f.write(f"{'=' * 140}\n")

# 同时在控制台输出统计信息
print(f"\n{'=' * 140}")
print(f"路由统计:")
print(f"  总路由数:     {total_count}")
print(f"  具体路由:     {specific_count}")
print(f"  通配符路由:   {wildcard_count}")
if total_count > 0:
    print(f"  通配符占比:   {wildcard_count / total_count * 100:.1f}%")
print(f"{'=' * 140}")

print(f"\nOK: 路由列表已保存到: {output_file}")
print(f"共 {total_count} 条路由，其中 {wildcard_count} 条通配符路由")
