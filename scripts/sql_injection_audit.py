#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQL 注入防护审计工具

用于测试和验证 SQL 注入防护系统的有效性
"""

import requests
import json
from typing import List, Dict


class SQLInjectionAuditor:
    """SQL 注入审计器"""

    def __init__(self, base_url: str = "http://localhost:9421"):
        self.base_url = base_url
        self.results = []

    def test_endpoint(self, url: str, method: str = "GET",
                      payload: dict = None, description: str = "") -> Dict:
        """
        测试单个端点
        
        Args:
            url: 测试 URL
            method: HTTP 方法
            payload: 请求载荷
            description: 测试描述
            
        Returns:
            测试结果字典
        """
        try:
            if method == "GET":
                response = requests.get(url, params=payload, timeout=5)
            elif method == "POST":
                response = requests.post(url, json=payload, timeout=5)
            else:
                response = requests.request(method, url, json=payload, timeout=5)

            result = {
                'url': url,
                'method': method,
                'payload': payload,
                'status_code': response.status_code,
                'description': description,
                'blocked': response.status_code == 400,
                'response_preview': response.text[:200] if response.text else ''
            }

            return result

        except Exception as e:
            return {
                'url': url,
                'method': method,
                'payload': payload,
                'status_code': None,
                'description': description,
                'error': str(e),
                'blocked': False
            }

    def run_basic_tests(self):
        """运行基本 SQL 注入测试"""
        print("=" * 80)
        print("SQL 注入防护审计 - 基本测试")
        print("=" * 80)

        # 常见的 SQL 注入 payload
        sqli_payloads = [
            # 经典 UNION 注入
            {"q": "1' UNION SELECT NULL--"},
            {"q": "1' OR '1'='1"},
            {"q": "admin'--"},

            # 布尔盲注
            {"q": "1' AND 1=1--"},
            {"q": "1' AND 1=2--"},

            # 时间盲注
            {"q": "1'; WAITFOR DELAY '0:0:5'--"},
            {"q": "1' AND SLEEP(5)--"},

            # 错误注入
            {"q": "1' AND EXTRACTVALUE(1, CONCAT(0x7e, (SELECT version())))--"},

            # DROP 语句（严重）
            {"q": "'; DROP TABLE users--"},
            {"q": "'; TRUNCATE TABLE articles--"},

            # 文件操作（严重）
            {"q": "' UNION SELECT LOAD_FILE('/etc/passwd')--"},
            {"q": "' INTO OUTFILE '/tmp/test.txt'"},
        ]

        test_url = f"{self.base_url}/api/v1/search"

        for i, payload in enumerate(sqli_payloads, 1):
            print(f"\n[{i}/{len(sqli_payloads)}] 测试: {payload}")
            result = self.test_endpoint(
                test_url,
                method="GET",
                payload=payload,
                description=f"SQL 注入测试 #{i}"
            )

            status = "✅ 已拦截" if result['blocked'] else "❌ 未拦截"
            print(f"  状态码: {result['status_code']} - {status}")

            if result.get('error'):
                print(f"  错误: {result['error']}")

            self.results.append(result)

    def run_post_tests(self):
        """运行 POST 请求的 SQL 注入测试"""
        print("\n" + "=" * 80)
        print("SQL 注入防护审计 - POST 测试")
        print("=" * 80)

        post_payloads = [
            # 登录表单注入
            {
                "username": "admin' OR '1'='1'--",
                "password": "anything"
            },
            {
                "username": "admin",
                "password": "' OR 1=1--"
            },

            # 文章搜索
            {
                "title": "test' UNION SELECT * FROM users--",
                "content": "normal content"
            },

            # 评论注入
            {
                "content": "Nice article!'; DROP TABLE comments;--"
            },
        ]

        test_endpoints = [
            (f"{self.base_url}/api/v1/auth/login", "POST"),
            (f"{self.base_url}/api/v1/articles", "POST"),
            (f"{self.base_url}/api/v1/comments", "POST"),
        ]

        for endpoint, method in test_endpoints:
            print(f"\n测试端点: {endpoint}")
            for i, payload in enumerate(post_payloads, 1):
                result = self.test_endpoint(
                    endpoint,
                    method=method,
                    payload=payload,
                    description=f"POST SQL 注入测试 #{i}"
                )

                status = "✅ 已拦截" if result['blocked'] else "⚠️  未拦截"
                print(f"  [{i}] {status} (状态码: {result['status_code']})")

                self.results.append(result)

    def generate_report(self):
        """生成审计报告"""
        print("\n" + "=" * 80)
        print("SQL 注入防护审计报告")
        print("=" * 80)

        total_tests = len(self.results)
        blocked_tests = sum(1 for r in self.results if r.get('blocked'))
        failed_tests = sum(1 for r in self.results if r.get('error'))

        print(f"\n测试统计:")
        print(f"  总测试数: {total_tests}")
        print(f"  已拦截: {blocked_tests} ({blocked_tests / total_tests * 100:.1f}%)")
        print(f"  未拦截: {total_tests - blocked_tests - failed_tests}")
        print(f"  测试失败: {failed_tests}")

        print(f"\n安全评级:", end=" ")
        if blocked_tests / total_tests >= 0.95:
            print("🟢 优秀 (A+)")
        elif blocked_tests / total_tests >= 0.85:
            print("🟡 良好 (B)")
        elif blocked_tests / total_tests >= 0.70:
            print("🟠 一般 (C)")
        else:
            print("🔴 需要改进 (D)")

        # 显示未拦截的测试
        unblocked = [r for r in self.results if not r.get('blocked') and not r.get('error')]
        if unblocked:
            print(f"\n⚠️  未拦截的测试 ({len(unblocked)}个):")
            for r in unblocked[:5]:  # 只显示前5个
                print(f"  - {r['description']}: {r['payload']}")

        # 保存详细报告
        report_file = "logs/sql_injection_audit_report.json"
        try:
            import os
            os.makedirs("logs", exist_ok=True)
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            print(f"\n📄 详细报告已保存到: {report_file}")
        except Exception as e:
            print(f"\n⚠️  无法保存报告: {e}")

    def run_full_audit(self):
        """运行完整审计"""
        print("开始 SQL 注入防护审计...\n")

        # 运行测试
        self.run_basic_tests()
        self.run_post_tests()

        # 生成报告
        self.generate_report()

        print("\n" + "=" * 80)
        print("审计完成！")
        print("=" * 80)


def main():
    """主函数"""
    import sys

    # 从命令行参数获取 base URL
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:9421"

    print(f"目标服务器: {base_url}\n")

    auditor = SQLInjectionAuditor(base_url)
    auditor.run_full_audit()


if __name__ == "__main__":
    main()
