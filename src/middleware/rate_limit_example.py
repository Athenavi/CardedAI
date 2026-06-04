"""
速率限制使用示例

展示如何使用 secure-python-utils 为特定路由添加速率限制
"""
from fastapi import FastAPI, Request

try:
    from secure_python_utils.rate_limiter import RateLimiter
except (ImportError, AttributeError):
    RateLimiter = None

# 创建 FastAPI 应用
app = FastAPI()

# 初始化速率限制器（需要 Redis）
# 如果没有 Redis，可以使用内存存储或其他方案
rate_limiter = RateLimiter("redis://localhost:6379")
rate_limiter.init_app(app)


@app.post("/api/v1/auth/login")
@rate_limiter.limit("5/minute")  # 登录接口：每分钟最多5次
async def login(request: Request, username: str, password: str):
    """登录接口 - 严格限流"""
    # 登录逻辑
    return {"message": "Login successful"}


@app.post("/api/v1/auth/register")
@rate_limiter.limit("3/5minutes")  # 注册接口：每5分钟最多3次
async def register(request: Request, username: str, email: str, password: str):
    """注册接口 - 严格限流"""
    # 注册逻辑
    return {"message": "Registration successful"}


@app.get("/api/v1/articles")
@rate_limiter.limit("100/hour")  # 文章列表：每小时最多100次
async def get_articles(request: Request, page: int = 1):
    """获取文章列表 - 中等限流"""
    # 获取文章逻辑
    return {"articles": [], "page": page}


@app.get("/api/v1/users/profile")
@rate_limiter.limit("200/hour")  # 用户资料：每小时最多200次
async def get_profile(request: Request):
    """获取用户资料 - 宽松限流"""
    # 获取用户资料逻辑
    return {"profile": {}}


@app.get("/api/v2/health")
# 健康检查接口不限流
async def health_check():
    """健康检查 - 不限流"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
