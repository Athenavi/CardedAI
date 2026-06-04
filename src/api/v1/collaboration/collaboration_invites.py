"""
协作文档邀请管理API
"""
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends, Body, Request
from pydantic import BaseModel

router = APIRouter(tags=["collaboration-invites"])

# 简化的邀请存储(生产环境应使用数据库)
# 结构: {invite_id: invitation_data}
invitations_db = {}

# 用户活跃邀请映射: {user_id: invite_id} - 确保用户同一时间只有一个活跃邀请
user_active_invites = {}


async def get_current_user(request: Request) -> dict:
    """从请求中获取当前用户信息"""
    # 从 cookie 或 header 中获取 token
    token = None

    # 尝试从 cookie 获取
    if "access_token" in request.cookies:
        token = request.cookies["access_token"]
    # 尝试从 Authorization header 获取
    elif "authorization" in request.headers:
        auth_header = request.headers["authorization"]
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")

    # 解码 JWT token
    import jwt
    from src.setting import settings

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get('sub') or payload.get('user_id')
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        return {"user_id": int(user_id)}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


class CreateInvitationRequest(BaseModel):
    """创建邀请请求"""
    article_id: int  # 文章ID
    permission: str = "edit"  # edit or view
    expire_hours: int = 24  # 过期时间(小时)
    max_users: int = 3  # 最大用户数


class InvitationResponse(BaseModel):
    """邀请响应"""
    invite_id: str
    document_id: str
    invite_url: str
    permission: str
    expires_at: str
    max_users: int
    current_users: int


@router.post("/", response_model=InvitationResponse)
async def create_invitation(request: CreateInvitationRequest = Body(...),
                            current_user: dict = Depends(get_current_user)):
    """
    创建协作文档邀请链接
    
    Args:
        request: 邀请配置
        user_info: 当前用户信息（从认证中间件获取）
        
    Returns:
        邀请信息,包含邀请链接
    """
    try:
        # 获取当前用户ID
        creator_id = current_user['user_id']
        print(f"User {creator_id} creating invitation for article: {request.article_id}")

        # 验证输入参数
        if request.article_id <= 0:
            raise HTTPException(status_code=400, detail="Invalid article ID")

        if request.permission not in ["edit", "view"]:
            raise HTTPException(status_code=400, detail="Permission must be 'edit' or 'view'")

        if request.expire_hours <= 0:
            raise HTTPException(status_code=400, detail="Expire hours must be positive")

        if request.max_users <= 0:
            raise HTTPException(status_code=400, detail="Max users must be positive")

        from shared.models.article import Article
        from sqlalchemy import select
        from src.utils.database.unified_manager import db_manager

        async with db_manager.get_session() as db_session:
            article_query = select(Article).where(Article.id == request.article_id)
            result = await db_session.execute(article_query)
            article = result.scalar_one_or_none()

            if not article:
                raise HTTPException(status_code=404, detail="Article not found")

            # 验证权限：只有文章作者可以创建协作邀请
            # Article模型使用'user'字段存储作者ID
            if article.user != creator_id:
                raise HTTPException(
                    status_code=403, 
                    detail="You don't have permission to create collaboration for this article"
                )

        # 检查用户是否已有活跃邀请，如果有则先撤销
        existing_invite_id = user_active_invites.get(creator_id)
        if existing_invite_id and existing_invite_id in invitations_db:
            existing_invite = invitations_db[existing_invite_id]
            # 检查是否过期
            if datetime.now() <= existing_invite["expires_at"]:
                print(f"Revoking existing invite {existing_invite_id} for user {creator_id}")
                del invitations_db[existing_invite_id]
        
        # 生成唯一邀请ID
        invite_id = str(uuid.uuid4())

        # 计算过期时间
        expires_at = datetime.now() + timedelta(hours=request.expire_hours)

        # 创建邀请记录
        invitation = {
            "invite_id": invite_id,
            "article_id": request.article_id,  # 存储文章ID
            "creator_id": creator_id,
            "permission": request.permission,
            "expires_at": expires_at,
            "max_users": request.max_users,
            "current_users": 0,
            "active_users": [],
            "created_at": datetime.now(),
        }

        invitations_db[invite_id] = invitation

        # 更新用户活跃邀请映射
        user_active_invites[creator_id] = invite_id

        # 生成邀请URL
        base_url = "http://localhost:3000"  # 前端地址
        invite_url = f"{base_url}/collaboration/room?invite={invite_id}"

        print(f"Invitation created successfully: {invite_id} for article {request.article_id}")

        return InvitationResponse(
            invite_id=invite_id,
            document_id=f"article-{request.article_id}",  # 兼容前端格式
            invite_url=invite_url,
            permission=request.permission,
            expires_at=expires_at.isoformat(),
            max_users=request.max_users,
            current_users=0,
        )

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        print(f"Error creating invitation: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create invitation: {str(e)}")


@router.get("/{invite_id}")
async def get_invitation(invite_id: str):
    """
    获取邀请详情
    
    Args:
        invite_id: 邀请ID
        
    Returns:
        邀请信息
    """
    invitation = invitations_db.get(invite_id)

    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")

    # 检查是否过期
    if datetime.now() > invitation["expires_at"]:
        raise HTTPException(status_code=410, detail="Invitation expired")

    return {
        "success": True,
        "data": {
            "invite_id": invite_id,
            "document_id": f"article-{invitation['article_id']}",  # 兼容前端格式
            "article_id": invitation["article_id"],
            "permission": invitation["permission"],
            "expires_at": invitation["expires_at"].isoformat(),
            "max_users": invitation["max_users"],
            "current_users": invitation["current_users"],
        }
    }


@router.post("/{invite_id}/accept")
async def accept_invitation(invite_id: str, user_info: dict = None):
    """
    接受邀请,加入协作文档
    
    Args:
        invite_id: 邀请ID
        user_info: 用户信息(可选)
        
    Returns:
        加入结果
    """
    invitation = invitations_db.get(invite_id)

    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")

    # 检查是否过期
    if datetime.now() > invitation["expires_at"]:
        raise HTTPException(status_code=410, detail="Invitation expired")

    # 检查人数限制
    if invitation["current_users"] >= invitation["max_users"]:
        raise HTTPException(
            status_code=403,
            detail=f"Maximum users ({invitation['max_users']}) reached"
        )

    # 更新邀请状态
    invitation["current_users"] += 1
    user_id = user_info.get("user_id",
                            f"guest_{uuid.uuid4().hex[:8]}") if user_info else f"guest_{uuid.uuid4().hex[:8]}"
    invitation["active_users"].append({
        "user_id": user_id,
        "joined_at": datetime.now().isoformat()
    })

    return {
        "success": True,
        "data": {
            "document_id": f"article-{invitation['article_id']}",  # 动态生成
            "permission": invitation["permission"],
            "user_id": user_id,
        }
    }


@router.get("/document/{document_id}/active")
async def get_active_invitations(document_id: str):
    """
    获取文档的活跃邀请列表
    
    Args:
        document_id: 文档ID
        
    Returns:
        活跃邀请列表
    """
    active_invites = []

    for invite_id, invitation in invitations_db.items():
        # 动态生成 document_id
        doc_id = f"article-{invitation['article_id']}"
        if (doc_id == document_id and
                datetime.now() <= invitation["expires_at"]):
            active_invites.append({
                "invite_id": invite_id,
                "permission": invitation["permission"],
                "expires_at": invitation["expires_at"].isoformat(),
                "max_users": invitation["max_users"],
                "current_users": invitation["current_users"],
                "invite_url": f"http://localhost:3000/collaboration/room?invite={invite_id}&doc={document_id}",
            })

    return {
        "success": True,
        "data": {
            "invitations": active_invites,
            "count": len(active_invites)
        }
    }


@router.delete("/{invite_id}")
async def revoke_invitation(invite_id: str):
    """
    撤销邀请
    
    Args:
        invite_id: 邀请ID
        
    Returns:
        操作结果
    """
    if invite_id not in invitations_db:
        raise HTTPException(status_code=404, detail="Invitation not found")

    del invitations_db[invite_id]

    return {
        "success": True,
        "message": "Invitation revoked"
    }
