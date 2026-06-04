"""
插件安全审计 API

提供插件安全检查和审计功能
"""

from fastapi import APIRouter, Depends, Body

from shared.services.plugin_security_audit import (
    static_analyzer,
    dependency_scanner,
    behavior_monitor,
    security_scorer,
)
from src.api.v1.core.responses import ApiResponse
from src.api.v1.users.user_management import jwt_required

router = APIRouter(prefix="/plugin-audit", tags=["Plugin Security Audit"])


@router.post("/static-analysis")
async def run_static_analysis(
        code: str = Body(..., description="插件代码"),
        filename: str = Body("", description="文件名"),
        current_user=Depends(jwt_required)
):
    """
    运行静态代码分析

    检查代码中的潜在安全问题
    """
    issues = static_analyzer.analyze(code, filename)

    # 计算安全评分
    score_result = security_scorer.calculate_score(issues)

    return ApiResponse(
        success=True,
        data={
            "issues": [issue.to_dict() for issue in issues],
            "total_issues": len(issues),
            "security_score": score_result,
        }
    )


@router.post("/scan-dependencies")
async def scan_dependencies(
        requirements_content: str = Body(..., description="requirements.txt 内容"),
        current_user=Depends(jwt_required)
):
    """
    扫描依赖包安全漏洞

    检查插件依赖的已知安全问题
    """
    # 临时保存 requirements 文件
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(requirements_content)
        temp_file = f.name

    try:
        issues = dependency_scanner.scan_dependencies(temp_file)

        return ApiResponse(
            success=True,
            data={
                "issues": [issue.to_dict() for issue in issues],
                "total_vulnerabilities": len(issues),
            }
        )
    finally:
        import os
        os.unlink(temp_file)


@router.get("/behavior-report")
async def get_behavior_report(current_user=Depends(jwt_required)):
    """
    获取动态行为报告

    查看插件运行时的行为监控数据
    """
    report = behavior_monitor.get_behavior_report()

    return ApiResponse(
        success=True,
        data=report
    )


@router.post("/track-api-call")
async def track_api_call(
        api_name: str = Body(..., description="API 名称"),
        parameters: dict = Body({}, description="参数"),
        current_user=Depends(jwt_required)
):
    """
    追踪 API 调用

    记录插件的 API 使用情况
    """
    behavior_monitor.track_api_call(api_name, parameters)

    return ApiResponse(
        success=True,
        message="API call tracked"
    )


@router.post("/track-resource-usage")
async def track_resource_usage(
        cpu_percent: float = Body(..., description="CPU 使用率"),
        memory_mb: float = Body(..., description="内存使用 (MB)"),
        current_user=Depends(jwt_required)
):
    """
    追踪资源使用

    记录插件的资源消耗
    """
    behavior_monitor.track_resource_usage(cpu_percent, memory_mb)

    return ApiResponse(
        success=True,
        message="Resource usage tracked"
    )


@router.post("/track-network-request")
async def track_network_request(
        url: str = Body(..., description="请求 URL"),
        method: str = Body("GET", description="HTTP 方法"),
        status: int = Body(200, description="响应状态码"),
        current_user=Depends(jwt_required)
):
    """
    追踪网络请求

    记录插件的网络活动
    """
    behavior_monitor.track_network_request(url, method, status)

    return ApiResponse(
        success=True,
        message="Network request tracked"
    )


@router.post("/full-audit")
async def run_full_audit(
        plugin_code: str = Body(..., description="插件代码"),
        requirements_content: str = Body("", description="requirements.txt 内容"),
        plugin_name: str = Body("", description="插件名称"),
        current_user=Depends(jwt_required)
):
    """
    运行完整安全审计

    综合静态分析、依赖扫描和行为监控
    """
    # 静态代码分析
    static_issues = static_analyzer.analyze(plugin_code)

    # 依赖扫描
    dep_issues = []
    if requirements_content:
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(requirements_content)
            temp_file = f.name

        try:
            dep_issues = dependency_scanner.scan_dependencies(temp_file)
        finally:
            import os
            os.unlink(temp_file)

    # 合并所有问题
    all_issues = static_issues + dep_issues

    # 计算安全评分
    score_result = security_scorer.calculate_score(all_issues)

    # 获取行为报告
    behavior_report = behavior_monitor.get_behavior_report()

    return ApiResponse(
        success=True,
        data={
            "plugin_name": plugin_name,
            "timestamp": datetime.now().isoformat(),
            "static_analysis": {
                "issues": [issue.to_dict() for issue in static_issues],
                "total": len(static_issues),
            },
            "dependency_scan": {
                "issues": [issue.to_dict() for issue in dep_issues],
                "total": len(dep_issues),
            },
            "behavior_monitoring": behavior_report,
            "security_score": score_result,
            "overall_assessment": generate_overall_assessment(score_result, behavior_report),
        }
    )


@router.get("/audit-history")
async def get_audit_history(
        limit: int = 10,
        current_user=Depends(jwt_required)
):
    """
    获取审计历史

    查看之前的安全审计记录
    """
    from shared.services.plugins.plugin_audit import plugin_audit_logger
    history = plugin_audit_logger.get_audit_logs(limit=limit)

    return ApiResponse(
        success=True,
        data={
            "history": history,
            "total": len(history),
        }
    )


@router.get("/security-guidelines")
async def get_security_guidelines(current_user=Depends(jwt_required)):
    """
    获取安全开发指南

    提供插件开发的安全最佳实践
    """
    guidelines = {
        "overview": {
            "title": "插件安全开发指南",
            "description": "确保插件安全性和可靠性的最佳实践。",
            "version": "1.0.0"
        },
        "critical_rules": [
            {
                "rule": "禁止使用 eval() 和 exec()",
                "reason": "这些函数可以执行任意代码，存在严重安全风险",
                "alternative": "使用 ast.literal_eval() 或专门的解析器"
            },
            {
                "rule": "避免硬编码敏感信息",
                "reason": "密码、API 密钥等不应出现在代码中",
                "alternative": "使用环境变量或配置文件"
            },
            {
                "rule": "使用参数化查询",
                "reason": "防止 SQL 注入攻击",
                "alternative": "使用 ORM 或参数化 SQL"
            },
            {
                "rule": "验证所有输入",
                "reason": "防止注入攻击和数据损坏",
                "alternative": "使用输入验证库"
            },
            {
                "rule": "限制权限",
                "reason": "最小权限原则",
                "alternative": "只请求必要的权限"
            }
        ],
        "code_quality": [
            "保持函数简洁（不超过 50 行）",
            "控制圈复杂度（低于 10）",
            "添加适当的错误处理",
            "编写清晰的文档字符串",
            "遵循 PEP 8 编码规范"
        ],
        "dependency_management": [
            "定期更新依赖包",
            "使用固定版本号",
            "审查依赖的安全性",
            "移除未使用的依赖",
            "监控安全公告"
        ],
        "testing": [
            "编写单元测试",
            "进行安全扫描",
            "测试边界情况",
            "性能测试",
            "集成测试"
        ],
        "deployment": [
            "在生产环境前进行安全审计",
            "使用沙箱环境测试",
            "监控系统日志",
            "准备回滚计划",
            "定期备份数据"
        ]
    }

    return ApiResponse(
        success=True,
        data=guidelines
    )


@router.get("/common-vulnerabilities")
async def get_common_vulnerabilities(current_user=Depends(jwt_required)):
    """
    获取常见漏洞列表

    了解插件开发中常见的安全问题
    """
    vulnerabilities = {
        "owasp_top_10": [
            {
                "id": "A01",
                "name": "Broken Access Control",
                "description": "访问控制失效",
                "prevention": "实施严格的权限检查"
            },
            {
                "id": "A02",
                "name": "Cryptographic Failures",
                "description": "加密失败",
                "prevention": "使用强加密算法和安全密钥管理"
            },
            {
                "id": "A03",
                "name": "Injection",
                "description": "注入攻击",
                "prevention": "验证和清理所有输入"
            },
            {
                "id": "A04",
                "name": "Insecure Design",
                "description": "不安全的设计",
                "prevention": "采用安全设计模式"
            },
            {
                "id": "A05",
                "name": "Security Misconfiguration",
                "description": "安全配置错误",
                "prevention": "遵循安全配置指南"
            }
        ],
        "python_specific": [
            {
                "name": "Pickle Deserialization",
                "risk": "高",
                "description": "反序列化不可信数据可执行任意代码",
                "mitigation": "避免使用 pickle，或使用更安全的格式如 JSON"
            },
            {
                "name": "Path Traversal",
                "risk": "高",
                "description": "文件路径遍历漏洞",
                "mitigation": "验证和规范化文件路径"
            },
            {
                "name": "Command Injection",
                "risk": "严重",
                "description": "命令注入漏洞",
                "mitigation": "避免使用 os.system()，使用 subprocess 并验证输入"
            }
        ]
    }

    return ApiResponse(
        success=True,
        data=vulnerabilities
    )


# ==================== 辅助函数 ====================

def generate_overall_assessment(score_result: dict, behavior_report: dict) -> str:
    """生成总体评估"""
    score = score_result.get("score", 0)
    risk_level = score_result.get("risk_level", "high")

    suspicious_activities = behavior_report.get("suspicious_activities", [])

    if score >= 80 and not suspicious_activities:
        return "插件安全性良好，可以放心使用"
    elif score >= 60:
        return "插件存在一些安全问题，建议修复后再使用"
    else:
        return "插件存在严重安全问题，不建议使用"


from datetime import datetime
