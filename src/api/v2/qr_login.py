"""
FastBlog API v2 二维码登录

在 v2 注册表中注册本模块即可启用 QR 登录。

注册方式（在 src/api/v2/__init__.py 的 ROUTE_REGISTRY_V2 中添加）：
    ("src.api.v2.qr_login", "/api/v2/auth/qr", ["qr-login"], False),
"""

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.logger import logger
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import get_current_user
from src.extensions import cache
from src.extensions import get_async_db_session as get_async_db

router = APIRouter(tags=["qr-login"])

# ── 手机扫码确认页（自包含 HTML，无需前端构建产物） ──
_MOBILE_LOGIN_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>扫码确认 - FastBlog</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{min-height:100vh;display:flex;align-items:center;justify-content:center;
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
  background:linear-gradient(135deg,#eff6ff,#eef2ff,#faf5ff);color:#1e293b;padding:1rem}
.card{text-align:center;max-width:22rem;width:100%}
.icon-box{width:4rem;height:4rem;margin:0 auto 1.5rem;border-radius:1rem;
  background:#fff;box-shadow:0 1px 3px rgba(0,0,0,.1);display:flex;align-items:center;justify-content:center;font-size:2rem}
.spinner{width:1.5rem;height:1.5rem;margin:0 auto;border:3px solid #dbeafe;
  border-top-color:#2563eb;border-radius:50%;animation:spin .8s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.msg{margin-top:1rem;color:#475569;font-size:.95rem}
.success-icon{font-size:3rem;color:#22c55e}
.error-icon{font-size:3rem;color:#ef4444}
.btn{margin-top:1.5rem;padding:.75rem 1.5rem;border:none;border-radius:.75rem;
  background:#2563eb;color:#fff;font-size:1rem;font-weight:600;cursor:pointer;width:100%}
.btn:active{background:#1d4ed8}
.hidden{display:none}
</style>
</head>
<body>
<div class="card">
  <div class="icon-box">📱</div>
  <div id="checking"><div class="spinner"></div><p class="msg">检查登录状态...</p></div>
  <div id="confirming" class="hidden"><div class="spinner"></div><p class="msg">确认登录中...</p></div>
  <div id="success" class="hidden"><div class="success-icon">✅</div><p class="msg" id="successMsg"></p></div>
  <div id="error" class="hidden"><div class="error-icon">❌</div><p class="msg" id="errorMsg"></p></div>
  <div id="loginPrompt" class="hidden">
    <p class="msg">请先登录后再扫码确认</p>
    <button class="btn" onclick="window.location.href='{{FRONTEND_ORIGIN}}/login?next='+encodeURIComponent(window.location.href)">去登录</button>
  </div>
</div>
<script>
(function(){
  var params=new URLSearchParams(window.location.search);
  var token=params.get('login_token')||params.get('token');
  if(!token){show('error','缺少登录令牌');return;}
  show('confirming');
  var base=window.location.origin;
  fetch(base+'/api/v2/auth/qr/confirm',{
    method:'POST',headers:{'Content-Type':'application/json'},
    credentials:'include',body:JSON.stringify({login_token:token})
  }).then(function(r){return r.json();}).then(function(d){
    if(d.success){show('success','登录确认成功，请返回电脑端继续');}
    else if(d.requires_auth){
      show('loginPrompt');
    }else{show('error',d.message||d.error||'确认失败');}
  }).catch(function(){show('error','网络错误');});
  function show(id,msg){
    ['checking','confirming','success','error','loginPrompt'].forEach(function(s){
      var el=document.getElementById(s);if(el)el.classList.add('hidden');
    });
    var el=document.getElementById(id);if(el)el.classList.remove('hidden');
    if(msg){var m=document.getElementById(id+'Msg');if(m)m.textContent=msg;}
  }
})();
</script>
</body>
</html>"""


@router.get("/mobile-login-page", response_class=HTMLResponse)
async def mobile_login_page(request: Request):
    """手机扫码确认页面（独立于前端构建产物，供后端直接提供）"""
    return HTMLResponse(content=_MOBILE_LOGIN_HTML)


@router.get("/generate")
async def v2_generate_qr(request: Request):
    """生成登录二维码"""
    from src.api.v1.user_utils.qrlogin_utils import qr_login
    from src.setting import app_config
    try:
        sys_version = "2.0"
        global_encoding = app_config.global_encoding
        domain = request.query_params.get('callback_domain') or ""
        result = await qr_login(request, sys_version, global_encoding, domain, cache)
        # v2 响应格式：将 qr_login 返回的顶层字段包装到 data 中
        if result.get("success"):
            return {
                "success": True,
                "data": {
                    "token": result.get("token"),
                    "qr_code": result.get("qr_code"),
                    "expires_at": result.get("expires_at"),
                }
            }
        return result
    except Exception as e:
        logger.error(f"QR generation failed: {e}")
        return {"success": False, "message": "Failed to generate QR code"}


@router.get("/status")
async def v2_check_qr_status(request: Request):
    """PC 端轮询检查扫码状态"""
    from src.api.v1.user_utils.qrlogin_utils import check_qr_login_back
    try:
        result = await check_qr_login_back(request, cache)
        # v2 响应格式：将 check_qr_login_back 返回的顶层字段包装到 data 中
        if result.get("success"):
            resp = {
                "success": True,
                "data": {
                    "status": result.get("status", "pending"),
                    "refresh_token": result.get("refresh_token"),
                    "next_url": result.get("next_url"),
                }
            }
            logger.info(
                f"[QR Status] token={request.query_params.get('token', '')[:8]}... status={resp['data']['status']}")
            return resp
        logger.warning(f"[QR Status] check_qr_login_back returned success=False: {result}")
        return result
    except Exception as e:
        logger.error(f"QR status check failed: {e}")
        return {"success": False, "message": "Failed to check QR code status"}


@router.post("/confirm")
async def v2_phone_confirm(request: Request, db: AsyncSession = Depends(get_async_db)):
    """手机端扫码后确认登录（支持 JSON body 或 query params）"""
    from src.api.v1.user_utils.qrlogin_utils import phone_scan_back

    # 读取 login_token：优先从 JSON body，其次 query params
    login_token = None
    content_type = request.headers.get('content-type', '')
    if 'application/json' in content_type:
        try:
            body = await request.json()
            login_token = body.get('login_token') or body.get('token')
        except Exception:
            pass
    if not login_token:
        login_token = request.query_params.get('login_token') or request.query_params.get('token')

    if not login_token:
        return {"success": False, "message": "Missing login_token"}

    try:
        current_user = await get_current_user(request, db)
    except HTTPException as e:
        if e.status_code == 401:
            return {"success": False, "requires_auth": True, "message": "请先登录后再扫码"}
        raise e

    try:
        return await phone_scan_back(request, current_user, cache, login_token=login_token)
    except Exception as e:
        logger.error(f"Phone confirm failed: {e}")
        return {"success": False, "message": "确认失败"}
