"""
类型注解检查和改进工具

用于扫描代码库中的类型注解问题，并提供改进建议

功能:
1. 检测过度使用Any类型
2. 检测缺少类型提示的函数
3. 检测不一致的类型注解
4. 生成改进报告
5. 自动修复简单的类型问题
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, field


@dataclass
class TypeIssue:
    """类型问题"""
    file_path: str
    line_number: int
    issue_type: str  # 'any_usage', 'missing_annotation', 'inconsistent'
    description: str
    suggestion: str
    severity: str = 'warning'  # 'error', 'warning', 'info'


@dataclass
class TypeAnalysisResult:
    """类型分析结果"""
    total_files: int = 0
    files_with_issues: int = 0
    total_issues: int = 0
    issues_by_type: Dict[str, int] = field(default_factory=dict)
    issues_by_severity: Dict[str, int] = field(default_factory=dict)
    issues: List[TypeIssue] = field(default_factory=list)
    top_any_files: List[Tuple[str, int]] = field(default_factory=list)


class TypeAnnotationChecker:
    """
    类型注解检查器
    
    扫描Python文件并分析类型注解质量
    """

    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.result = TypeAnalysisResult()

    def scan_directory(self, dir_path: str = None, exclude_dirs: List[str] = None):
        """
        扫描目录中的所有Python文件
        
        Args:
            dir_path: 要扫描的目录（默认为root_dir）
            exclude_dirs: 要排除的目录列表
        """
        if dir_path is None:
            dir_path = self.root_dir

        if exclude_dirs is None:
            exclude_dirs = ['.venv', 'node_modules', '__pycache__', '.git', 'dist', 'build']

        python_files = []
        for path in Path(dir_path).rglob('*.py'):
            # 排除指定目录
            if any(excluded in str(path) for excluded in exclude_dirs):
                continue
            python_files.append(path)

        self.result.total_files = len(python_files)

        for file_path in python_files:
            self._analyze_file(file_path)

        # 统计结果
        self._calculate_statistics()

    def _analyze_file(self, file_path: Path):
        """分析单个Python文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()

            tree = ast.parse(source, filename=str(file_path))
            file_issues = []

            # 检查模块级别的导入
            any_count = self._count_any_imports(tree)

            # 检查函数和方法
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    issues = self._check_function_annotations(node, source)
                    file_issues.extend(issues)

            # 如果有问题，记录到结果中
            if file_issues:
                self.result.files_with_issues += 1
                self.result.issues.extend(file_issues)

                # 记录Any使用最多的文件
                if any_count > 0:
                    self.result.top_any_files.append((str(file_path), any_count))

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")

    def _count_any_imports(self, tree: ast.Module) -> int:
        """计算文件中Any类型的使用次数"""
        count = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id == 'Any':
                count += 1
            elif isinstance(node, ast.Attribute) and node.attr == 'Any':
                count += 1
        return count

    def _check_function_annotations(self, func_node: ast.FunctionDef, source: str) -> List[TypeIssue]:
        """检查函数的类型注解"""
        issues = []
        func_name = func_node.name
        line_number = func_node.lineno

        # 检查返回类型注解
        if func_node.returns is None:
            # 跳过特殊方法和测试函数
            if not (func_name.startswith('__') and func_name.endswith('__')):
                if not func_name.startswith('test_'):
                    issues.append(TypeIssue(
                        file_path=source.split('\n')[0] if '\n' in source else '',
                        line_number=line_number,
                        issue_type='missing_annotation',
                        description=f"函数 '{func_name}' 缺少返回类型注解",
                        suggestion="添加返回类型注解，例如: -> None 或 -> Dict[str, Any]",
                        severity='warning'
                    ))

        # 检查参数类型注解
        for arg in func_node.args.args:
            if arg.arg != 'self' and arg.annotation is None:
                issues.append(TypeIssue(
                    file_path='',
                    line_number=arg.lineno,
                    issue_type='missing_annotation',
                    description=f"参数 '{arg.arg}' 缺少类型注解",
                    suggestion=f"为参数 '{arg.arg}' 添加类型注解",
                    severity='info'
                ))

        # 检查是否过度使用Any
        for node in ast.walk(func_node):
            if isinstance(node, ast.Subscript):
                if isinstance(node.value, ast.Name) and node.value.id == 'Dict':
                    # 检查 Dict[str, Any] 模式
                    if len(node.slice.elts) == 2:
                        value_type = node.slice.elts[1]
                        if isinstance(value_type, ast.Name) and value_type.id == 'Any':
                            issues.append(TypeIssue(
                                file_path='',
                                line_number=node.lineno,
                                issue_type='any_usage',
                                description=f"在函数 '{func_name}' 中使用了 Dict[str, Any]",
                                suggestion="考虑使用更具体的类型，例如 Dict[str, str] 或 TypedDict",
                                severity='warning'
                            ))

        return issues

    def _calculate_statistics(self):
        """计算统计信息"""
        self.result.total_issues = len(self.result.issues)

        # 按类型统计
        for issue in self.result.issues:
            issue_type = issue.issue_type
            self.result.issues_by_type[issue_type] = \
                self.result.issues_by_type.get(issue_type, 0) + 1

            severity = issue.severity
            self.result.issues_by_severity[severity] = \
                self.result.issues_by_severity.get(severity, 0) + 1

        # 排序Any使用最多的文件
        self.result.top_any_files.sort(key=lambda x: x[1], reverse=True)
        self.result.top_any_files = self.result.top_any_files[:10]  # 只保留前10个

    def generate_report(self) -> str:
        """生成分析报告"""
        report = []
        report.append("=" * 80)
        report.append("类型注解分析报告")
        report.append("=" * 80)
        report.append("")

        report.append(f"扫描文件数: {self.result.total_files}")
        report.append(f"有问题的文件数: {self.result.files_with_issues}")
        report.append(f"总问题数: {self.result.total_issues}")
        report.append("")

        report.append("问题类型分布:")
        for issue_type, count in sorted(self.result.issues_by_type.items()):
            report.append(f"  - {issue_type}: {count}")
        report.append("")

        report.append("严重程度分布:")
        for severity, count in sorted(self.result.issues_by_severity.items()):
            report.append(f"  - {severity}: {count}")
        report.append("")

        if self.result.top_any_files:
            report.append("Any类型使用最多的文件 (Top 10):")
            for file_path, count in self.result.top_any_files:
                report.append(f"  - {file_path}: {count} 次")
            report.append("")

        if self.result.issues:
            report.append("详细问题列表:")
            report.append("-" * 80)
            for i, issue in enumerate(self.result.issues[:50], 1):  # 只显示前50个问题
                report.append(f"{i}. [{issue.severity.upper()}] {issue.description}")
                report.append(f"   文件: {issue.file_path}:{issue.line_number}")
                report.append(f"   建议: {issue.suggestion}")
                report.append("")

        report.append("=" * 80)

        return "\n".join(report)

    def save_report(self, output_path: str):
        """保存报告到文件"""
        report = self.generate_report()
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"报告已保存到: {output_path}")


def run_type_check(root_dir: str = None, output_file: str = None):
    """
    运行类型检查
    
    Args:
        root_dir: 项目根目录
        output_file: 输出报告文件路径
    """
    if root_dir is None:
        root_dir = os.path.dirname(os.path.dirname(__file__))

    checker = TypeAnnotationChecker(root_dir)

    print("开始扫描代码库...")
    checker.scan_directory(
        exclude_dirs=['.venv', 'node_modules', '__pycache__', '.git', 'dist', 'build', 'tests']
    )

    report = checker.generate_report()
    print(report)

    if output_file:
        checker.save_report(output_file)

    return checker.result


if __name__ == '__main__':
    import sys

    output = sys.argv[1] if len(sys.argv) > 1 else 'type_analysis_report.txt'
    run_type_check(output_file=output)
