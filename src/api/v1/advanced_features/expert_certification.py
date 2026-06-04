"""
专家认证系统 API
提供领域专家申请、审核、认证标识等功能
"""

from fastapi import APIRouter, Depends, Query, Body

from shared.models.user import User as UserModel
from shared.services.advanced_features.expert_certification_system import expert_certification_system
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import get_current_active_user, admin_required as admin_required_api

router = APIRouter(tags=["expert-certification"])


@router.get("/fields", summary="获取可认证领域")
async def get_available_fields():
    """
    获取所有可申请的认证领域
    
    Returns:
        领域列表
    """
    try:
        fields = expert_certification_system.get_available_fields()

        return ApiResponse(
            success=True,
            data={
                'fields': fields,
                'count': len(fields),
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取领域失败: {str(e)}")


@router.post("/apply", summary="申请专家认证")
async def apply_certification(
        field_id: str = Body(..., description="认证领域ID"),
        credentials: dict = Body(..., description="资质证明"),
        bio: str = Body('', description="个人简介"),
        current_user: UserModel = Depends(get_current_active_user)
):
    """
    提交专家认证申请
    
    Args:
        field_id: 认证领域ID
        credentials: 资质证明(学历/工作经历/作品等)
        bio: 个人简介
        
    Returns:
        申请结果
    """
    try:
        app_id = expert_certification_system.apply_certification(
            user_id=current_user.id,
            field_id=field_id,
            credentials=credentials,
            bio=bio,
        )

        return ApiResponse(
            success=True,
            message='申请已提交，等待审核',
            data={
                'application_id': app_id,
            }
        )
    except ValueError as e:
        return ApiResponse(success=False, error=str(e))
    except Exception as e:
        return ApiResponse(success=False, error=f"申请失败: {str(e)}")


@router.get("/my-status", summary="获取我的认证状态")
async def get_my_certification_status(
        current_user: UserModel = Depends(get_current_active_user)
):
    """
    获取当前用户的认证状态
    
    Returns:
        认证信息
    """
    try:
        cert = expert_certification_system.get_user_certification(current_user.id)

        if not cert:
            return ApiResponse(
                success=True,
                data={
                    'is_certified': False,
                    'message': '未认证',
                }
            )

        return ApiResponse(
            success=True,
            data={
                'is_certified': True,
                'certification': cert,
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取状态失败: {str(e)}")


@router.get("/check-expert/{user_id}", summary="检查用户是否是专家")
async def check_expert(
        user_id: int,
        field_id: str = Query(None, description="领域ID(可选)"),
):
    """
    检查指定用户是否是认证专家
    
    Args:
        user_id: 用户ID
        field_id: 领域ID(可选)
        
    Returns:
        专家状态
    """
    try:
        is_expert = expert_certification_system.is_expert(user_id, field_id)

        return ApiResponse(
            success=True,
            data={
                'user_id': user_id,
                'is_expert': is_expert,
                'field_id': field_id,
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"检查失败: {str(e)}")


@router.get("/experts", summary="获取认证专家列表")
async def get_certified_experts(
        field_id: str = Query(None, description="领域过滤"),
        limit: int = Query(100, ge=1, le=500, description="返回数量"),
):
    """
    获取已认证的专家列表
    
    Args:
        field_id: 领域过滤
        limit: 返回数量(1-500)
        
    Returns:
        专家列表
    """
    try:
        experts = expert_certification_system.get_certified_experts(
            field_id=field_id,
            limit=limit,
        )

        return ApiResponse(
            success=True,
            data={
                'experts': experts,
                'count': len(experts),
                'field_id': field_id,
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取专家列表失败: {str(e)}")


# 管理员接口

@router.get("/admin/pending-applications", summary="获取待审核申请")
async def get_pending_applications(
        field_id: str = Query(None, description="领域过滤"),
        current_user: UserModel = Depends(admin_required_api)
):
    """
    获取所有待审核的认证申请
    
    Args:
        field_id: 领域过滤
        
    Returns:
        申请列表
    """
    try:
        applications = expert_certification_system.get_pending_applications(field_id=field_id)

        return ApiResponse(
            success=True,
            data={
                'applications': applications,
                'count': len(applications),
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取申请列表失败: {str(e)}")


@router.get("/admin/application/{application_id}", summary="获取申请详情")
async def get_application_details(
        application_id: str,
        current_user: UserModel = Depends(admin_required_api)
):
    """
    获取认证申请详情
    
    Args:
        application_id: 申请ID
        
    Returns:
        申请详情
    """
    try:
        details = expert_certification_system.get_application_details(application_id)

        if not details:
            return ApiResponse(success=False, error='申请不存在')

        return ApiResponse(
            success=True,
            data=details
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取详情失败: {str(e)}")


@router.post("/admin/review", summary="审核认证申请")
async def review_application(
        application_id: str = Body(..., description="申请ID"),
        approved: bool = Body(..., description="是否通过"),
        rejection_reason: str = Body(None, description="拒绝原因"),
        current_user: UserModel = Depends(admin_required_api)
):
    """
    审核专家认证申请
    
    Args:
        application_id: 申请ID
        approved: 是否通过
        rejection_reason: 拒绝原因(拒绝时必需)
        
    Returns:
        审核结果
    """
    try:
        success = expert_certification_system.review_application(
            application_id=application_id,
            reviewer_id=current_user.id,
            approved=approved,
            rejection_reason=rejection_reason,
        )

        if success:
            status = '已通过' if approved else '已拒绝'
            return ApiResponse(
                success=True,
                message=f'申请{status}'
            )
        else:
            return ApiResponse(success=False, error='审核失败')
    except Exception as e:
        return ApiResponse(success=False, error=f"审核失败: {str(e)}")


@router.post("/admin/revoke", summary="撤销专家认证")
async def revoke_certification(
        user_id: int = Body(..., description="用户ID"),
        reason: str = Body('', description="撤销原因"),
        current_user: UserModel = Depends(admin_required_api)
):
    """
    撤销用户的专家认证
    
    Args:
        user_id: 用户ID
        reason: 撤销原因
        
    Returns:
        操作结果
    """
    try:
        success = expert_certification_system.revoke_certification(user_id, reason)

        if success:
            return ApiResponse(
                success=True,
                message='认证已撤销'
            )
        else:
            return ApiResponse(success=False, error='撤销失败')
    except Exception as e:
        return ApiResponse(success=False, error=f"撤销失败: {str(e)}")


@router.get("/admin/stats", summary="获取认证系统统计")
async def get_certification_stats(
        current_user: UserModel = Depends(admin_required_api)
):
    """
    获取专家认证系统整体统计
    
    Returns:
        统计数据
    """
    try:
        stats = expert_certification_system.get_certification_stats()

        return ApiResponse(
            success=True,
            data=stats
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取统计失败: {str(e)}")
