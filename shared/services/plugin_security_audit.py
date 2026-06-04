"""
插件安全审计工具

提供全面的插件安全检查和审计功能

功能:
1. 静态代码分析
2. 危险函数检测
3. 依赖包安全扫描
4. 硬编码密钥检测
5. 动态行为监控
6. 运行时 API 调用追踪
7. 资源使用监控
8. 网络请求审计
9. 安全评分系统
10. 风险等级标识
11. 开发者修复建议
"""

import ast
import os
import re
from datetime import datetime
from typing import Dict, Any, List


class SecurityIssue:
    """安全问题"""

    def __init__(
            self,
            severity: str,
            category: str,
            message: str,
            line_number: int = 0,
            code_snippet: str = "",
            recommendation: str = "",
    ):
        self.severity = severity  # critical/high/medium/low
        self.category = category
        self.message = message
        self.line_number = line_number
        self.code_snippet = code_snippet
        self.recommendation = recommendation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "severity": self.severity,
            "category": self.category,
            "message": self.message,
            "line_number": self.line_number,
            "code_snippet": self.code_snippet,
            "recommendation": self.recommendation,
        }


class StaticCodeAnalyzer:
    """
    静态代码分析器
    
    分析插件代码中的潜在安全问题
    """

    def __init__(self):
        # 危险函数模式
        self.dangerous_functions = [
            ('eval', 'critical', 'Use of eval() can execute arbitrary code'),
            ('exec', 'critical', 'Use of exec() can execute arbitrary code'),
            ('compile', 'high', 'Use of compile() can be used for code injection'),
            ('__import__', 'high', 'Dynamic imports can load malicious modules'),
            ('getattr', 'medium', 'Dynamic attribute access can be exploited'),
            ('setattr', 'medium', 'Dynamic attribute setting can modify objects'),
        ]

        # 危险模块
        self.dangerous_modules = [
            ('os.system', 'critical', 'Direct system command execution'),
            ('os.popen', 'critical', 'Shell command execution'),
            ('subprocess', 'high', 'Subprocess execution can be dangerous'),
            ('socket', 'medium', 'Network socket operations'),
            ('ctypes', 'high', 'C library calls can bypass Python safety'),
            ('pickle', 'high', 'Pickle deserialization can execute code'),
            ('marshal', 'high', 'Marshal can execute arbitrary code'),
        ]

        # 敏感信息模式
        self.sensitive_patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', 'hardcoded_password'),
            (r'api_key\s*=\s*["\'][^"\']+["\']', 'hardcoded_api_key'),
            (r'secret\s*=\s*["\'][^"\']+["\']', 'hardcoded_secret'),
            (r'token\s*=\s*["\'][^"\']+["\']', 'hardcoded_token'),
            (r'AWS_ACCESS_KEY', 'aws_credentials'),
            (r'PRIVATE_KEY', 'private_key'),
        ]

    def analyze(self, code: str, filename: str = "") -> List[SecurityIssue]:
        """
        分析代码
        
        Args:
            code: 源代码
            filename: 文件名
            
        Returns:
            安全问题列表
        """
        issues = []

        # 检查危险函数
        issues.extend(self._check_dangerous_functions(code))

        # 检查危险模块
        issues.extend(self._check_dangerous_modules(code))

        # 检查敏感信息
        issues.extend(self._check_sensitive_info(code))

        # 检查代码复杂度
        issues.extend(self._check_code_complexity(code))

        # 检查 SQL 注入风险
        issues.extend(self._check_sql_injection(code))

        return issues

    def _check_dangerous_functions(self, code: str) -> List[SecurityIssue]:
        """检查危险函数调用"""
        issues = []
        lines = code.split('\n')

        for func_name, severity, message in self.dangerous_functions:
            pattern = rf'\b{func_name}\s*\('
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    issues.append(SecurityIssue(
                        severity=severity,
                        category="dangerous_function",
                        message=f"{message}: {func_name}()",
                        line_number=i,
                        code_snippet=line.strip(),
                        recommendation=f"Avoid using {func_name}(). Use safer alternatives."
                    ))

        return issues

    def _check_dangerous_modules(self, code: str) -> List[SecurityIssue]:
        """检查危险模块导入"""
        issues = []
        lines = code.split('\n')

        for module, severity, message in self.dangerous_modules:
            patterns = [
                rf'import\s+{module.split(".")[0]}',
                rf'from\s+{module.split(".")[0]}',
            ]

            for i, line in enumerate(lines, 1):
                for pattern in patterns:
                    if re.search(pattern, line):
                        issues.append(SecurityIssue(
                            severity=severity,
                            category="dangerous_module",
                            message=f"{message}: {module}",
                            line_number=i,
                            code_snippet=line.strip(),
                            recommendation=f"Avoid importing {module}. Use safer alternatives."
                        ))

        return issues

    def _check_sensitive_info(self, code: str) -> List[SecurityIssue]:
        """检查敏感信息泄露"""
        issues = []
        lines = code.split('\n')

        for pattern, issue_type in self.sensitive_patterns:
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(SecurityIssue(
                        severity="high",
                        category="sensitive_info",
                        message=f"Potential {issue_type} found",
                        line_number=i,
                        code_snippet=line.strip(),
                        recommendation="Move sensitive data to environment variables or config files."
                    ))

        return issues

    def _check_code_complexity(self, code: str) -> List[SecurityIssue]:
        """检查代码复杂度"""
        issues = []

        try:
            tree = ast.parse(code)

            # 检查嵌套深度
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    complexity = self._calculate_complexity(node)
                    if complexity > 10:
                        issues.append(SecurityIssue(
                            severity="low",
                            category="code_quality",
                            message=f"High cyclomatic complexity ({complexity}) in function '{node.name}'",
                            line_number=node.lineno,
                            recommendation="Refactor complex functions into smaller, simpler functions."
                        ))

        except SyntaxError as e:
            issues.append(SecurityIssue(
                severity="medium",
                category="syntax_error",
                message=f"Syntax error: {str(e)}",
                recommendation="Fix syntax errors before deployment."
            ))

        return issues

    def _calculate_complexity(self, node: ast.AST) -> int:
        """计算圈复杂度"""
        complexity = 1

        for child in ast.walk(node):
            if isinstance(child, (
                    ast.If, ast.While, ast.For, ast.ExceptHandler,
                    ast.With, ast.Assert, ast.comprehension
            )):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        return complexity

    def _check_sql_injection(self, code: str) -> List[SecurityIssue]:
        """检查 SQL 注入风险"""
        issues = []
        lines = code.split('\n')

        sql_patterns = [
            r'execute\s*\(\s*f["\']',
            r'execute\s*\(\s*["\'].*%\s*',
            r'execute\s*\(\s*["\'].*\+',
        ]

        for i, line in enumerate(lines, 1):
            for pattern in sql_patterns:
                if re.search(pattern, line):
                    issues.append(SecurityIssue(
                        severity="critical",
                        category="sql_injection",
                        message="Potential SQL injection vulnerability",
                        line_number=i,
                        code_snippet=line.strip(),
                        recommendation="Use parameterized queries instead of string formatting."
                    ))

        return issues


class DependencyScanner:
    """
    依赖包安全扫描器
    
    检查插件依赖的安全漏洞
    """

    def __init__(self):
        self.known_vulnerabilities = {
            # 示例：已知漏洞的包
            'requests': {'2.20.0': 'CVE-2023-XXXXX'},
            'flask': {'1.0': 'CVE-2023-YYYYY'},
        }

    def scan_dependencies(self, requirements_file: str = None) -> List[SecurityIssue]:
        """
        扫描依赖包
        
        Args:
            requirements_file: requirements.txt 文件路径
            
        Returns:
            安全问题列表
        """
        issues = []

        if not requirements_file or not os.path.exists(requirements_file):
            return issues

        try:
            with open(requirements_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # 解析包名和版本
                        if '==' in line:
                            package, version = line.split('==')

                            # 检查已知漏洞
                            if package in self.known_vulnerabilities:
                                if version in self.known_vulnerabilities[package]:
                                    issues.append(SecurityIssue(
                                        severity="high",
                                        category="dependency_vulnerability",
                                        message=f"Known vulnerability in {package}=={version}",
                                        recommendation=f"Update {package} to a patched version."
                                    ))

        except Exception as e:
            issues.append(SecurityIssue(
                severity="medium",
                category="scan_error",
                message=f"Failed to scan dependencies: {str(e)}",
                recommendation="Check requirements file format."
            ))

        return issues


class DynamicBehaviorMonitor:
    """
    动态行为监控器
    
    监控插件运行时的行为
    """

    def __init__(self):
        self.api_calls: List[Dict[str, Any]] = []
        self.resource_usage: List[Dict[str, Any]] = []
        self.network_requests: List[Dict[str, Any]] = []

    def track_api_call(self, api_name: str, parameters: dict, timestamp: str = None):
        """追踪 API 调用"""
        self.api_calls.append({
            "api_name": api_name,
            "parameters": parameters,
            "timestamp": timestamp or datetime.now().isoformat(),
        })

    def track_resource_usage(self, cpu_percent: float, memory_mb: float, timestamp: str = None):
        """追踪资源使用"""
        self.resource_usage.append({
            "cpu_percent": cpu_percent,
            "memory_mb": memory_mb,
            "timestamp": timestamp or datetime.now().isoformat(),
        })

    def track_network_request(self, url: str, method: str, status: int, timestamp: str = None):
        """追踪网络请求"""
        self.network_requests.append({
            "url": url,
            "method": method,
            "status": status,
            "timestamp": timestamp or datetime.now().isoformat(),
        })

    def get_behavior_report(self) -> Dict[str, Any]:
        """获取行为报告"""
        return {
            "total_api_calls": len(self.api_calls),
            "total_network_requests": len(self.network_requests),
            "avg_cpu_usage": self._calculate_avg_cpu(),
            "avg_memory_usage": self._calculate_avg_memory(),
            "suspicious_activities": self._detect_suspicious_activities(),
        }

    def _calculate_avg_cpu(self) -> float:
        if not self.resource_usage:
            return 0.0
        return sum(r["cpu_percent"] for r in self.resource_usage) / len(self.resource_usage)

    def _calculate_avg_memory(self) -> float:
        if not self.resource_usage:
            return 0.0
        return sum(r["memory_mb"] for r in self.resource_usage) / len(self.resource_usage)

    def _detect_suspicious_activities(self) -> List[str]:
        """检测可疑活动"""
        suspicious = []

        # 检查频繁的 API 调用
        if len(self.api_calls) > 100:
            suspicious.append("Excessive API calls detected")

        # 检查高资源使用
        avg_cpu = self._calculate_avg_cpu()
        if avg_cpu > 80:
            suspicious.append(f"High CPU usage: {avg_cpu:.2f}%")

        # 检查异常网络请求
        for req in self.network_requests:
            if req["status"] >= 400:
                suspicious.append(f"Failed network request: {req['url']}")

        return suspicious


class SecurityScorer:
    """
    安全评分计算器
    
    根据发现的问题计算安全评分
    """

    def __init__(self):
        self.severity_weights = {
            "critical": 25,
            "high": 15,
            "medium": 8,
            "low": 3,
        }

    def calculate_score(self, issues: List[SecurityIssue]) -> Dict[str, Any]:
        """
        计算安全评分
        
        Args:
            issues: 安全问题列表
            
        Returns:
            评分结果
        """
        if not issues:
            return {
                "score": 100,
                "grade": "A",
                "risk_level": "low",
                "total_issues": 0,
            }

        # 计算扣分
        total_deduction = 0
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        for issue in issues:
            severity = issue.severity
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            total_deduction += self.severity_weights.get(severity, 0)

        # 计算最终分数
        score = max(0, 100 - total_deduction)

        # 确定等级
        grade = self._get_grade(score)
        risk_level = self._get_risk_level(score)

        return {
            "score": score,
            "grade": grade,
            "risk_level": risk_level,
            "total_issues": len(issues),
            "severity_breakdown": severity_counts,
            "recommendations": self._generate_recommendations(issues),
        }

    def _get_grade(self, score: int) -> str:
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"

    def _get_risk_level(self, score: int) -> str:
        if score >= 80:
            return "low"
        elif score >= 60:
            return "medium"
        else:
            return "high"

    def _generate_recommendations(self, issues: List[SecurityIssue]) -> List[str]:
        """生成修复建议"""
        recommendations = []

        categories = set(issue.category for issue in issues)

        if "dangerous_function" in categories:
            recommendations.append("Replace dangerous functions (eval, exec) with safer alternatives")

        if "sensitive_info" in categories:
            recommendations.append("Move hardcoded credentials to environment variables")

        if "sql_injection" in categories:
            recommendations.append("Use parameterized queries to prevent SQL injection")

        if "dependency_vulnerability" in categories:
            recommendations.append("Update vulnerable dependencies to patched versions")

        if "code_quality" in categories:
            recommendations.append("Refactor complex code to improve maintainability")

        return recommendations


# 全局实例
static_analyzer = StaticCodeAnalyzer()
dependency_scanner = DependencyScanner()
behavior_monitor = DynamicBehaviorMonitor()
security_scorer = SecurityScorer()
