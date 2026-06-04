#!/usr/bin/env python3
"""
模型生命周期管理检查脚本

功能：
  1. 解析 config/models.yaml，提取所有 ORM 模型
  2. 扫描 src/ 和 shared/ 目录下的 Python 代码，检测模型的实际使用情况
  3. 验证每个模型是否有 status 字段（active / deprecated / planned）
  4. 生成模型使用率审计报告
  5. CI 模式下，未使用的 active 模型会触发警告

使用方法：
  python scripts/model_lifecycle_check.py check        # CI 检查模式（非零退出码表示有问题）
  python scripts/model_lifecycle_check.py report        # 生成详细审计报告
  python scripts/model_lifecycle_check.py add-status    # 为缺少 status 的模型批量添加 status 字段
"""

# Fix Windows console encoding for Chinese + special characters
import io
import sys

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import argparse
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

import yaml

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
MODELS_YAML = PROJECT_ROOT / "config" / "models.yaml"

# 扫描目录
SCAN_DIRS = [
    PROJECT_ROOT / "src",
    PROJECT_ROOT / "shared",
]

# 有效的 status 值
VALID_STATUSES = {"active", "deprecated", "planned"}

# 企业版模型（优先级低，标记为 planned）
ENTERPRISE_MODELS = {
    "EnterpriseLicense", "SupportTicket", "SupportTicketReply",
    "DeploymentScript", "DeploymentLog", "MonitoringAlert", "MonitoringMetric",
}


def load_models_yaml() -> dict:
    """加载 models.yaml 配置"""
    if not MODELS_YAML.exists():
        print(f"[ERROR] 配置文件不存在: {MODELS_YAML}")
        sys.exit(1)
    with open(MODELS_YAML, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_orm_models(config: dict) -> Dict[str, dict]:
    """提取所有 ORM 模型（orm: true）"""
    models = config.get("models", {})
    orm_models = {}
    for name, definition in models.items():
        if isinstance(definition, dict) and definition.get("orm", False):
            orm_models[name] = definition
    return orm_models


def scan_codebase_for_usage(model_name: str) -> List[str]:
    """
    扫描代码库，查找模型的实际使用位置。
    匹配模式：
      - import 语句: from shared.models.xxx import ModelName
      - 直接引用: ModelName 作为类名使用
    """
    # 从模型名推导文件名 (e.g., ArticleSEO -> article_seo)
    snake_case = re.sub(r"(?<!^)(?=[A-Z])", "_", model_name).lower()
    model_file = PROJECT_ROOT / "shared" / "models" / f"{snake_case}.py"

    usage_locations = []

    for scan_dir in SCAN_DIRS:
        if not scan_dir.exists():
            continue
        for py_file in scan_dir.rglob("*.py"):
            # 跳过自动生成的模型文件本身
            if py_file.resolve() == model_file.resolve():
                continue
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            # 匹配模型名作为标识符引用
            pattern = rf"\b{re.escape(model_name)}\b"
            if re.search(pattern, content):
                rel_path = py_file.relative_to(PROJECT_ROOT)
                usage_locations.append(str(rel_path))

    return usage_locations


def scan_all_usage(orm_models: Dict[str, dict]) -> Dict[str, List[str]]:
    """扫描所有 ORM 模型的使用情况"""
    usage_map = {}
    for model_name in orm_models:
        usage_map[model_name] = scan_codebase_for_usage(model_name)
    return usage_map


def run_check(config: dict, orm_models: Dict[str, dict], usage_map: Dict[str, List[str]]) -> int:
    """
    CI 检查模式：
    - 检查缺少 status 字段的模型
    - 检查 active 模型是否在代码中有引用
    - 检查 deprecated 模型是否仍在使用
    - 检查新模型是否有 frontend_page 字段
    返回：0=通过, 1=有警告, 2=有错误
    """
    exit_code = 0
    warnings = []
    errors = []

    # 1. 检查 status 字段
    missing_status = []
    invalid_status = []
    for name, defn in orm_models.items():
        status = defn.get("status")
        if status is None:
            missing_status.append(name)
        elif status not in VALID_STATUSES:
            invalid_status.append((name, status))

    if missing_status:
        warnings.append(f"[WARN] {len(missing_status)} 个模型缺少 status 字段:")
        for name in sorted(missing_status):
            warnings.append(f"    - {name}")

    if invalid_status:
        errors.append(f"[ERROR] {len(invalid_status)} 个模型的 status 值无效:")
        for name, status in sorted(invalid_status):
            errors.append(f"    - {name}: status={status} (有效值: {VALID_STATUSES})")

    # 2. 检查 active 模型是否有引用
    active_unused = []
    for name, defn in orm_models.items():
        if defn.get("status") == "active" and not usage_map.get(name):
            active_unused.append(name)

    if active_unused:
        warnings.append(f"[WARN] {len(active_unused)} 个 active 模型未在代码中被引用:")
        for name in sorted(active_unused):
            warnings.append(f"    - {name}")

    # 3. 检查 deprecated 模型是否仍在使用
    deprecated_in_use = []
    for name, defn in orm_models.items():
        if defn.get("status") == "deprecated" and usage_map.get(name):
            deprecated_in_use.append((name, usage_map[name]))

    if deprecated_in_use:
        errors.append(f"[ERROR] {len(deprecated_in_use)} 个 deprecated 模型仍在使用中:")
        for name, locations in sorted(deprecated_in_use):
            errors.append(f"    - {name}: {', '.join(locations[:3])}")

    # 4. 检查 frontend_page 字段
    missing_frontend_page = []
    for name, defn in orm_models.items():
        if "frontend_page" not in defn:
            missing_frontend_page.append(name)

    if missing_frontend_page:
        warnings.append(f"[WARN] {len(missing_frontend_page)} 个模型缺少 frontend_page 字段:")
        for name in sorted(missing_frontend_page):
            warnings.append(f"    - {name}")
        warnings.append("    提示: 运行 python scripts/add_frontend_page_to_models.py 添加字段")

    # 输出结果
    print("=" * 60)
    print("  模型生命周期检查报告")
    print("=" * 60)
    print()

    # 统计信息
    status_counts = defaultdict(int)
    for defn in orm_models.values():
        status_counts[defn.get("status", "未设置")] += 1
    print(f"[STATS] ORM 模型总数: {len(orm_models)}")
    for status, count in sorted(status_counts.items()):
        tag = {"active": "[OK]", "deprecated": "[DEP]", "planned": "[PLAN]"}.get(status, "[?]")
        print(f"   {tag} {status}: {count}")
    print()

    if warnings:
        print("-- 警告 --")
        for w in warnings:
            print(f"  {w}")
        print()
        exit_code = max(exit_code, 1)

    if errors:
        print("-- 错误 --")
        for e in errors:
            print(f"  {e}")
        print()
        exit_code = max(exit_code, 2)

    if exit_code == 0:
        print("[PASS] 所有检查通过！")
    elif exit_code == 1:
        print("[WARN] 有警告，请检查上述输出。")
    else:
        print("[FAIL] 有错误，必须修复后才能合并。")

    return exit_code


def run_report(orm_models: Dict[str, dict], usage_map: Dict[str, List[str]]):
    """生成详细审计报告"""
    print("=" * 70)
    print("  模型使用率审计报告")
    print("=" * 70)
    print()

    # 按状态分组
    by_status = defaultdict(list)
    for name, defn in orm_models.items():
        status = defn.get("status", "未设置")
        by_status[status].append(name)

    for status in ["active", "deprecated", "planned", "未设置"]:
        models = by_status.get(status, [])
        if not models:
            continue
        tag = {"active": "[ACTIVE]", "deprecated": "[DEPRECATED]", "planned": "[PLANNED]"}.get(status, "[UNSET]")
        print(f"\n{tag} ({len(models)} 个)")
        print("-" * 50)
        for name in sorted(models):
            usage = usage_map.get(name, [])
            usage_count = len(usage)
            usage_indicator = f"[{usage_count} refs]" if usage_count else "[unused]"
            table = orm_models[name].get("table", "")
            print(f"  {name:30s} {usage_indicator:15s} table={table}")
            if usage:
                for loc in usage[:3]:
                    print(f"    -> {loc}")
                if len(usage) > 3:
                    print(f"    -> ... +{len(usage) - 3} more")

    # 前端页面映射统计
    print()
    print("=" * 70)
    print("  前端页面映射统计")
    print("=" * 70)
    print()

    has_frontend = []
    no_frontend = []
    missing_field = []
    for name, defn in orm_models.items():
        fp = defn.get("frontend_page")
        if "frontend_page" not in defn:
            missing_field.append(name)
        elif fp:
            has_frontend.append((name, fp))
        else:
            no_frontend.append(name)

    print(f"  有前端页面:  {len(has_frontend)}")
    print(f"  仅后端 API:  {len(no_frontend)}")
    if missing_field:
        print(f"  缺少字段:    {len(missing_field)} (运行 add-frontend-page 补充)")

    if no_frontend:
        print()
        print("[NO FRONTEND PAGE]")
        print("-" * 50)
        for name in sorted(no_frontend):
            print(f"  {name}")

    # 汇总
    print()
    print("=" * 70)
    print("[SUMMARY]")
    print("-" * 70)
    total = len(orm_models)
    used = sum(1 for name in orm_models if usage_map.get(name))
    unused = total - used
    print(f"  ORM 模型总数:  {total}")
    print(f"  有代码引用:    {used}")
    print(f"  无代码引用:    {unused}")
    print(f"  使用率:        {used / total * 100:.1f}%")
    print(f"  有前端页面:    {len(has_frontend)}")
    print(f"  前端覆盖率:    {len(has_frontend) / total * 100:.1f}%")
    print()


def run_add_status(orm_models: Dict[str, dict]):
    """
    为缺少 status 字段的模型批量添加 status 字段。
    使用行级文本插入，保留原有格式和注释。
    """
    with open(MODELS_YAML, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # 收集需要添加 status 的模型名及其应设的 status 值
    models_to_add = {}
    for name, defn in orm_models.items():
        if "status" not in defn:
            if name in ENTERPRISE_MODELS:
                models_to_add[name] = "planned"
            else:
                models_to_add[name] = "active"

    if not models_to_add:
        print("[OK] 所有 ORM 模型已有 status 字段，无需修改。")
        return

    # 策略：在每个模型定义块中，找到 "description:" 行，在其后插入 "    status: xxx"
    # 模型定义的模式: "  ModelName:" 后面紧跟 "    description:"
    new_lines = []
    current_model = None
    i = 0
    added_count = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.rstrip()

        # 检测模型名称行 (两个空格开头 + 模型名 + 冒号)
        model_match = re.match(r'^  (\w+):\s*$', line)
        if model_match:
            current_model = model_match.group(1)

        # 检测 description 行，在其后插入 status
        if current_model and current_model in models_to_add:
            desc_match = re.match(r'^    description:', line)
            if desc_match:
                new_lines.append(line)
                # 确定缩进：与 description 行对齐
                status_value = models_to_add[current_model]
                new_lines.append(f"    status: {status_value}\n")
                added_count += 1
                # 标记为已添加，避免重复
                del models_to_add[current_model]
                current_model = None
                i += 1
                continue

        new_lines.append(line)
        i += 1

    # 写回文件
    with open(MODELS_YAML, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print(f"[OK] 已为 {added_count} 个模型添加 status 字段，已保存到 {MODELS_YAML}")
    if models_to_add:
        print(f"[WARN] {len(models_to_add)} 个模型未找到 description 行，未能添加 status:")
        for name in sorted(models_to_add.keys()):
            print(f"    - {name}")


def run_add_frontend_page(orm_models: Dict[str, dict]):
    """
    为缺少 frontend_page 字段的模型批量添加 frontend_page 字段。
    使用行级文本插入，保留原有格式和注释。
    """
    # 导入映射表
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
    try:
        from add_frontend_page_to_models import FRONTEND_PAGE_MAP
    except ImportError:
        print("[ERROR] 无法导入 FRONTEND_PAGE_MAP，请确保 scripts/add_frontend_page_to_models.py 存在")
        return

    with open(MODELS_YAML, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # 收集需要添加 frontend_page 的模型名
    models_to_add = {}
    for name, defn in orm_models.items():
        if "frontend_page" not in defn:
            models_to_add[name] = FRONTEND_PAGE_MAP.get(name, None)

    if not models_to_add:
        print("[OK] 所有 ORM 模型已有 frontend_page 字段，无需修改。")
        return

    # 策略：在每个模型定义块中，找到 "status:" 行，在其后插入 "    frontend_page: xxx"
    new_lines = []
    current_model = None
    added_count = 0

    for line in lines:
        stripped = line.rstrip()

        # 检测模型名称行 (两个空格开头 + 模型名 + 冒号)
        model_match = re.match(r'^  (\w+):\s*$', line)
        if model_match:
            current_model = model_match.group(1)

        # 检测 status 行，在其后插入 frontend_page
        if current_model and current_model in models_to_add:
            status_match = re.match(r'^    status:', line)
            if status_match:
                new_lines.append(line)
                page_value = models_to_add[current_model]
                if page_value:
                    new_lines.append(f'    frontend_page: "{page_value}"\n')
                else:
                    new_lines.append(f'    frontend_page: null\n')
                added_count += 1
                del models_to_add[current_model]
                current_model = None
                continue

        new_lines.append(line)

    # 写回文件
    with open(MODELS_YAML, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print(f"[OK] 已为 {added_count} 个模型添加 frontend_page 字段，已保存到 {MODELS_YAML}")
    if models_to_add:
        print(f"[WARN] {len(models_to_add)} 个模型未找到 status 行，未能添加 frontend_page:")
        for name in sorted(models_to_add.keys()):
            print(f"    - {name}")


def main():
    parser = argparse.ArgumentParser(description="模型生命周期管理检查工具")
    parser.add_argument(
        "command",
        choices=["check", "report", "add-status", "add-frontend-page"],
        help="子命令: check=CI检查, report=详细报告, add-status=批量添加status字段, add-frontend-page=批量添加frontend_page字段",
    )
    args = parser.parse_args()

    config = load_models_yaml()
    orm_models = get_orm_models(config)

    if not orm_models:
        print("[WARN] 未找到任何 ORM 模型（orm: true）")
        sys.exit(0)

    print(f"[SCAN] {len(orm_models)} 个 ORM 模型")

    if args.command == "add-status":
        run_add_status(orm_models)
    elif args.command == "add-frontend-page":
        run_add_frontend_page(orm_models)
    else:
        print("[SCAN] 正在检测代码引用...")
        usage_map = scan_all_usage(orm_models)
        print()

        if args.command == "check":
            exit_code = run_check(config, orm_models, usage_map)
            sys.exit(exit_code)
        elif args.command == "report":
            run_report(orm_models, usage_map)


if __name__ == "__main__":
    main()
