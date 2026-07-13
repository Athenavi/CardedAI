"""
V1 API 路由包 — 已废弃

注意：
- api_v1_router（prefix=/api/v1）从未被挂载到 FastAPI 应用中
- 所有 inline 路由（QR登录/手机验证/缩略图等）均为死代码
- 子路由系统（_V1_SUB_ROUTERS）亦为死代码

V1 模块文件仍被 V2 路由聚合器直接引用（如 src.api.v2.*），不可删除。
如需删除 V1 模块，请先确认 V2 的 __init__.py 无对应 import。
"""
