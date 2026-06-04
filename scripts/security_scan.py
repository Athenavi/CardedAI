#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依赖安全扫描工具
检查 Python 和 Node.js 依赖的安全漏洞
"""

import subprocess
import sys
import os
from pathlib import Path


def check_python_dependencies():
    """检查 Python 依赖的安全漏洞"""
    print("=" * 80)
    print("Python 依赖安全扫描")
    print("=" * 80)

    # 检查是否安装了 safety
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", "safety"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print("\n⚠️  Safety 未安装，正在安装...")
            install_result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "safety"],
                capture_output=True,
                text=True
            )
            if install_result.returncode != 0:
                print(f"❌ Safety 安装失败: {install_result.stderr}")
                return False

    except Exception as e:
        print(f"❌ 检查 Safety 时出错: {e}")
        return False

    # 运行安全检查
    print("\n🔍 正在扫描 Python 依赖漏洞...\n")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "safety", "check", "--bare"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )

        print(result.stdout)
        if result.stderr:
            print("警告信息:", result.stderr)

        if result.returncode == 0:
            print("\n✅ Python 依赖安全检查通过！")
            return True
        else:
            print("\n⚠️  发现安全漏洞，请查看上述报告并更新依赖")
            return False

    except Exception as e:
        print(f"❌ 安全扫描失败: {e}")
        return False


def check_nodejs_dependencies():
    """检查 Node.js 依赖的安全漏洞"""
    print("\n" + "=" * 80)
    print("Node.js 依赖安全扫描")
    print("=" * 80)

    frontend_dir = Path(__file__).parent.parent / "frontend-next"

    if not frontend_dir.exists():
        print("⚠️  frontend-next 目录不存在，跳过 Node.js 依赖检查")
        return True

    package_json = frontend_dir / "package.json"
    if not package_json.exists():
        print("⚠️  package.json 不存在，跳过 Node.js 依赖检查")
        return True

    # 检查 npm audit
    print("\n🔍 正在扫描 Node.js 依赖漏洞...\n")
    try:
        result = subprocess.run(
            ["npm", "audit", "--json"],
            capture_output=True,
            text=True,
            cwd=frontend_dir
        )

        if result.returncode == 0:
            print("✅ Node.js 依赖安全检查通过！")
            return True
        else:
            # 解析 JSON 输出
            import json
            try:
                audit_data = json.loads(result.stdout)
                metadata = audit_data.get("metadata", {})
                vulnerabilities = audit_data.get("vulnerabilities", {})

                total_vulns = metadata.get("vulnerabilities", {}).get("total", 0)

                if total_vulns > 0:
                    print(f"\n⚠️  发现 {total_vulns} 个安全漏洞\n")

                    # 按严重程度统计
                    severity_counts = {}
                    for vuln in vulnerabilities.values():
                        severity = vuln.get("severity", "unknown")
                        severity_counts[severity] = severity_counts.get(severity, 0) + 1

                    for severity, count in sorted(severity_counts.items()):
                        print(f"  - {severity}: {count}")

                    print("\n建议运行以下命令修复:")
                    print("  npm audit fix          # 自动修复兼容的漏洞")
                    print("  npm audit fix --force  # 强制修复（可能引入 breaking changes）")

                    return False
                else:
                    print("✅ Node.js 依赖安全检查通过！")
                    return True

            except json.JSONDecodeError:
                print("⚠️  无法解析 npm audit 输出")
                print(result.stdout[:500])
                return False

    except FileNotFoundError:
        print("⚠️  npm 命令未找到，跳过 Node.js 依赖检查")
        return True
    except Exception as e:
        print(f"❌ Node.js 安全扫描失败: {e}")
        return False


def generate_security_report(python_ok: bool, nodejs_ok: bool):
    """生成安全报告"""
    print("\n" + "=" * 80)
    print("安全扫描总结")
    print("=" * 80)

    print(f"\nPython 依赖: {'✅ 通过' if python_ok else '⚠️  发现问题'}")
    print(f"Node.js 依赖: {'✅ 通过' if nodejs_ok else '⚠️  发现问题'}")

    if python_ok and nodejs_ok:
        print("\n🎉 所有依赖安全检查通过！")
        return True
    else:
        print("\n⚠️  建议尽快修复发现的安全漏洞")
        print("\n后续步骤:")
        print("1. 查看上述详细报告")
        print("2. 更新有漏洞的依赖包")
        print("3. 重新运行此脚本验证修复")
        print("4. 将此脚本添加到 CI/CD 流程中")
        return False


def main():
    """主函数"""
    print("FastBlog 依赖安全扫描工具")
    print(f"扫描时间: {Path(__file__).stat().st_mtime}")
    print()

    # 检查 Python 依赖
    python_ok = check_python_dependencies()

    # 检查 Node.js 依赖
    nodejs_ok = check_nodejs_dependencies()

    # 生成报告
    overall_ok = generate_security_report(python_ok, nodejs_ok)

    # 返回退出码
    sys.exit(0 if overall_ok else 1)


if __name__ == "__main__":
    main()
