from urllib.parse import urlparse

from fastapi import Request, HTTPException, status

from src.setting import app_config


def origin_required(request: Request):
    """
    FastAPI兼容的来源验证函数

    比较请求来源的 hostname 与配置的域名 hostname 是否一致。
    例如 DOMAIN=http://localhost:9421 时，只比较 hostname 部分（localhost），
    不比较端口，以兼容不同端口部署场景。
    """
    client_domain = request.url.hostname

    # 使用 urlparse 正确解析配置域名，提取 hostname 部分
    parsed = urlparse(app_config.domain)
    config_domain = parsed.hostname or app_config.domain

    if client_domain != config_domain:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized access"
        )

    return request
