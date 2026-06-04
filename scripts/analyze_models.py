#!/usr/bin/env python3
"""Models.yaml 审查脚本 - 检查每个模型在后端和前端的使用情况"""
import io
import os
import re
import sys

import yaml

# 确保 Windows 终端支持 UTF-8 输出
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def read_file_content(filepath):
    """安全读取文件内容"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except:
        return ''


def search_in_dir(directory, pattern, file_extensions=None):
    """在目录中搜索正则匹配，返回匹配的文件列表"""
    if file_extensions is None:
        file_extensions = ['.py', '.ts', '.tsx', '.astro']
    matches = []
    if not os.path.exists(directory):
        return matches
    for root, dirs, files in os.walk(directory):
        # Skip hidden dirs and common non-essential dirs
        dirs[:] = [d for d in dirs if
                   not d.startswith('.') and d not in ('node_modules', '__pycache__', '.next', 'dist')]
        for fname in files:
            if any(fname.endswith(ext) for ext in file_extensions):
                fpath = os.path.join(root, fname)
                content = read_file_content(fpath)
                if re.search(pattern, content):
                    rel_path = os.path.relpath(fpath, '.').replace('\\', '/')
                    matches.append(rel_path)
    return matches


def check_frontend_page_exists(frontend_page, frontend_files=None):
    """检查前端页面是否真实存在"""
    if not frontend_page:
        return False

    page_path = frontend_page.strip('/')

    # 检查 .astro 页面
    possible_astro_paths = [
        f'frontend-astro/src/pages/{page_path}/index.astro',
        f'frontend-astro/src/pages/{page_path}.astro',
    ]
    for p in possible_astro_paths:
        if os.path.exists(p):
            return True

    # 检查 TSX 管理组件（AdminXxxManagement 或类似的 .tsx 文件）
    if frontend_files:
        for f in frontend_files:
            if f.endswith('.tsx') and ('Admin' in f or 'Management' in f or 'Page' in f):
                return True

    # 检查目录下是否有任何页面文件
    page_dir = f'frontend-astro/src/pages/{page_path}'
    if os.path.isdir(page_dir):
        for fname in os.listdir(page_dir):
            if fname.endswith(('.astro', '.tsx', '.ts')):
                return True

    return False


def classify_model_type(model_name, model_info):
    """根据模型定义判断类型：orm / schema / enum / config"""
    # 如果显式指定了 type 字段，直接使用
    explicit_type = model_info.get('type', '')
    if explicit_type:
        return explicit_type

    # 如果有 orm: true 或 table 字段，判定为 orm
    if model_info.get('orm') or model_info.get('table'):
        return 'orm'

    # 如果有 enum 属性但没有 table，判定为 enum
    properties = model_info.get('properties', {})
    has_enum_fields = any(
        isinstance(v, dict) and 'enum' in v
        for v in properties.values()
        if isinstance(v, dict)
    )

    # 检查是否是请求/响应 DTO 模型（没有 table、没有 orm、有 required 或 writeOnly）
    has_required = bool(model_info.get('required'))
    has_writeonly = any(
        isinstance(v, dict) and v.get('writeOnly')
        for v in properties.values()
        if isinstance(v, dict)
    )

    if has_required or has_writeonly:
        return 'schema'

    if has_enum_fields and not model_info.get('table'):
        return 'enum'

    return 'unknown'


def main():
    # 1. Read models.yaml
    with open('config/models.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    models_dict = config.get('models', {})
    print(f'模型总数: {len(models_dict)}', flush=True)
    print(flush=True)

    # 2. For each model, check backend and frontend usage
    unused_models = []  # 完全未使用
    backend_only_has_page = []  # 仅后端使用，前端页面已存在
    backend_only_no_file = []  # 仅后端使用，前端页面已定义但文件不存在
    backend_only_no_page = []  # 仅后端使用，无前端页面定义
    full_coverage = []  # 前后端均有覆盖
    planned_models = []  # planned 状态
    schema_models = []  # schema/DTO 模型

    model_results = {}

    for model_name, model_info in sorted(models_dict.items()):
        if not isinstance(model_info, dict):
            continue

        status = model_info.get('status', 'unknown')
        frontend_page = model_info.get('frontend_page', '')
        description = model_info.get('description', '')
        model_type = classify_model_type(model_name, model_info)

        if status == 'planned':
            planned_models.append({
                'name': model_name,
                'description': description,
                'frontend_page': frontend_page,
                'type': model_type,
            })
            continue

        # Check backend usage
        backend_pattern = rf'\b{model_name}\b'
        backend_files = search_in_dir('src', backend_pattern, ['.py'])
        backend_files += search_in_dir('shared', backend_pattern, ['.py'])
        backend_files = list(set(backend_files))

        # Check frontend usage
        frontend_pattern = rf'\b{model_name}\b'
        frontend_files = search_in_dir('frontend-astro/src', frontend_pattern, ['.ts', '.tsx', '.astro'])
        frontend_files = list(set(frontend_files))

        # Check if frontend_page exists in codebase
        frontend_page_exists = check_frontend_page_exists(frontend_page, frontend_files)

        result = {
            'name': model_name,
            'description': description,
            'status': status,
            'type': model_type,
            'frontend_page': frontend_page,
            'backend_files': backend_files[:5],  # Top 5
            'backend_count': len(backend_files),
            'frontend_files': frontend_files[:5],
            'frontend_count': len(frontend_files),
            'frontend_page_exists': frontend_page_exists,
        }
        model_results[model_name] = result

        # Schema/DTO models: 没有 table/orm 标记，且没有后端 ORM 文件
        if model_type == 'schema' and not model_info.get('table'):
            schema_models.append(result)
            continue

        if len(backend_files) == 0 and len(frontend_files) == 0:
            unused_models.append(result)
        elif len(frontend_files) > 0 and frontend_page_exists:
            full_coverage.append(result)
        elif len(frontend_files) > 0:
            # 前端有引用但页面标记未存在 - 也算全覆盖
            full_coverage.append(result)
        else:
            # 仅后端使用
            if frontend_page and frontend_page_exists:
                backend_only_has_page.append(result)
            elif frontend_page and not frontend_page_exists:
                backend_only_no_file.append(result)
            else:
                backend_only_no_page.append(result)

    # 3. Output results
    print('=' * 80, flush=True)
    print('一、完全未使用的模型', flush=True)
    print('=' * 80, flush=True)
    if unused_models:
        for m in unused_models:
            print(f"  {m['name']}: {m['description']} (status={m['status']}, type={m['type']})", flush=True)
    else:
        print('  无', flush=True)
    print(f'  共 {len(unused_models)} 个', flush=True)
    print(flush=True)

    print('=' * 80, flush=True)
    print('二、仅在后端使用、前端无对应页面的模型', flush=True)
    print('=' * 80, flush=True)

    print(flush=True)
    print('  --- 2.1 前端管理页面已存在但模型未被前端直接引用 ---', flush=True)
    if backend_only_has_page:
        for m in backend_only_has_page:
            print(f"  {m['name']}: {m['description']}", flush=True)
            print(f"    后端: {m['backend_count']} 个文件 | 前端页面: {m['frontend_page']} ✅", flush=True)
    else:
        print('    无', flush=True)
    print(f'    共 {len(backend_only_has_page)} 个', flush=True)

    print(flush=True)
    print('  --- 2.2 前端页面已定义但页面文件不存在 ---', flush=True)
    if backend_only_no_file:
        for m in backend_only_no_file:
            print(f"  {m['name']}: {m['description']}", flush=True)
            print(f"    后端: {m['backend_count']} 个文件 | 前端页面: {m['frontend_page']} ❌", flush=True)
    else:
        print('    无', flush=True)
    print(f'    共 {len(backend_only_no_file)} 个', flush=True)

    print(flush=True)
    print('  --- 2.3 无前端页面定义的模型 ---', flush=True)
    if backend_only_no_page:
        for m in backend_only_no_page:
            print(f"  {m['name']}: {m['description']} (type={m['type']})", flush=True)
            print(f"    后端: {m['backend_count']} 个文件 | 前端引用: {m['frontend_count']} 个文件", flush=True)
    else:
        print('    无', flush=True)
    print(f'    共 {len(backend_only_no_page)} 个', flush=True)
    print(flush=True)

    print('=' * 80, flush=True)
    print('三、前后端均有覆盖的模型', flush=True)
    print('=' * 80, flush=True)
    if full_coverage:
        for m in full_coverage:
            fe_page = m['frontend_page'] or '无'
            print(f"  {m['name']}: {m['description']}", flush=True)
            print(
                f"    后端: {m['backend_count']} 个文件 | 前端页面: {fe_page} | 前端引用: {m['frontend_count']} 个文件",
                flush=True)
            if m['backend_files']:
                print(f"    后端文件: {', '.join(m['backend_files'])}", flush=True)
            if m['frontend_files']:
                print(f"    前端文件: {', '.join(m['frontend_files'])}", flush=True)
    else:
        print('  无', flush=True)
    print(f'  共 {len(full_coverage)} 个', flush=True)
    print(flush=True)

    print('=' * 80, flush=True)
    print('四、Planned 状态的模型（按需开发）', flush=True)
    print('=' * 80, flush=True)
    if planned_models:
        for m in planned_models:
            print(f"  {m['name']}: {m['description']}", flush=True)
    else:
        print('  无', flush=True)
    print(f'  共 {len(planned_models)} 个', flush=True)
    print(flush=True)

    print('=' * 80, flush=True)
    print('五、Schema/DTO 模型（非 ORM 模型）', flush=True)
    print('=' * 80, flush=True)
    if schema_models:
        for m in schema_models:
            print(f"  {m['name']}: {m['description']}", flush=True)
    else:
        print('  无', flush=True)
    print(f'  共 {len(schema_models)} 个', flush=True)
    print(flush=True)

    # 汇总统计
    total_backend_only = len(backend_only_has_page) + len(backend_only_no_file) + len(backend_only_no_page)
    effective_models = len(models_dict) - len(schema_models) - len(planned_models)
    if effective_models > 0:
        coverage_rate = (len(full_coverage) + len(backend_only_has_page)) / effective_models * 100
    else:
        coverage_rate = 0

    print('=' * 80, flush=True)
    print('六、汇总统计', flush=True)
    print('=' * 80, flush=True)
    print(f'  模型总数: {len(models_dict)}', flush=True)
    print(f'  完全未使用: {len(unused_models)} ({len(unused_models) / len(models_dict) * 100:.1f}%)', flush=True)
    print(
        f'  仅后端使用（页面已存在）: {len(backend_only_has_page)} ({len(backend_only_has_page) / len(models_dict) * 100:.1f}%)',
        flush=True)
    print(
        f'  仅后端使用（页面缺失）: {len(backend_only_no_file)} ({len(backend_only_no_file) / len(models_dict) * 100:.1f}%)',
        flush=True)
    print(
        f'  仅后端使用（无页面定义）: {len(backend_only_no_page)} ({len(backend_only_no_page) / len(models_dict) * 100:.1f}%)',
        flush=True)
    print(f'  前后端均有覆盖: {len(full_coverage)} ({len(full_coverage) / len(models_dict) * 100:.1f}%)', flush=True)
    print(f'  Planned（企业版）: {len(planned_models)} ({len(planned_models) / len(models_dict) * 100:.1f}%)', flush=True)
    print(f'  Schema/DTO 模型: {len(schema_models)} ({len(schema_models) / len(models_dict) * 100:.1f}%)', flush=True)
    print(f'  有效覆盖率（排除 DTO 和 planned）: {coverage_rate:.1f}%', flush=True)
    print(flush=True)


if __name__ == '__main__':
    main()
