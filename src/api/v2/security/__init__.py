"""
安全API聚合路由器 - V2统一入口
整合V1的security相关模块

使用懒加载模式：仅在首次访问 router 时才导入 V1 子模块。
"""
from fastapi import APIRouter

_router = None


def _build_router():
    global _router
    if _router is not None:
        return _router

    router = APIRouter(tags=["security"])

    # 导入V1的security子模块（延迟到首次访问时）
    from src.api.v2.security.anomaly_detection import router as anomaly_detection_router
    from src.api.v1.security.audit_log import router as audit_log_router
    from src.api.v1.security.content_approval import router as content_approval_router
    from src.api.v1.security.login_security import router as login_security_router
    from src.api.v1.security.rate_limit import router as rate_limit_router
    from src.api.v1.security.rbac import router as rbac_router
    from src.api.v1.security.security_alert import router as security_alert_router
    from src.api.v1.security.security_report import router as security_report_router
    from src.api.v1.security.sensitive_words import router as sensitive_words_router
    from src.api.v1.security.session_management import router as session_management_router
    from src.api.v1.security.two_factor_auth import router as two_factor_auth_router

    router.include_router(anomaly_detection_router, prefix="")
    router.include_router(sensitive_words_router, prefix="/sensitive-words")
    router.include_router(content_approval_router, prefix="/content-approval")
    router.include_router(session_management_router, prefix="/admin/session")
    router.include_router(two_factor_auth_router, prefix="/2fa")
    router.include_router(audit_log_router, prefix="/audit-log")
    router.include_router(login_security_router, prefix="/login-security")
    router.include_router(rate_limit_router, prefix="/rate-limit")
    router.include_router(rbac_router, prefix="/rbac")
    router.include_router(security_alert_router, prefix="/alerts")
    router.include_router(security_report_router, prefix="/reports")

    _router = router
    return _router


def __getattr__(name):
    if name == "router":
        return _build_router()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
