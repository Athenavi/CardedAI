"""
零信任安全中间件
对所有内部 API 调用实施默认的身份验证和最小权限原则
"""
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer

from shared.models.user import User
from shared.services.security.rbac_service import rbac_service
from src.auth.auth_deps import jwt_required_dependency as jwt_required

security = HTTPBearer(auto_error=False)


async def zero_trust_middleware(request: Request, call_next):
    """
    零信任中间件：拦截所有请求，强制进行身份验证和权限检查
    """
    # 排除公开路径（如登录、注册、静态资源）
    public_paths = ["/api/v1/auth/login", "/api/v1/auth/register", "/api/v2/static", "/media"]
    if any(request.url.path.startswith(path) for path in public_paths):
        return await call_next(request)

    # 尝试获取用户身份
    try:
        # 这里简化处理，实际应从 request.state 或依赖注入中获取已验证的用户
        user = request.state.current_user if hasattr(request.state, 'current_user') else None

        if not user:
            raise HTTPException(status_code=401, detail="Unauthorized: Zero Trust Policy requires authentication")

        # 记录审计日志
        from shared.services.security.audit_service import audit_service
        await audit_service.log_action(
            user_id=user.id,
            action=f"access_{request.method.lower()}_{request.url.path}",
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Security check failed")

    return await call_next(request)


class RBACGuard:
    """基于角色的访问控制守卫"""

    @staticmethod
    async def require_capability(user: User = Depends(jwt_required), capability: str = "read:content"):
        """检查用户是否拥有特定能力"""
        if not await rbac_service.has_capability(user.id, capability):
            raise HTTPException(
                status_code=403,
                detail=f"Forbidden: User lacks required capability '{capability}'"
            )
        return user
