from urllib.parse import urlparse

from fastapi import Request, HTTPException, status

from src.setting import app_config


def origin_required(request: Request):
    """
    FastAPI兼容的来源验证函数

    比较请求来源的 scheme + hostname + port 与配置的域名是否一致。
    例如 DOMAIN=http://localhost:9421 时，仅允许 http://localhost:9421 来源。
    """
    client_domain = request.url.hostname
    client_scheme = request.url.scheme
    client_port = request.url.port

    # 使用 urlparse 正确解析配置域名
    parsed = urlparse(app_config.domain)
    config_domain = parsed.hostname or app_config.domain
    config_scheme = parsed.scheme
    config_port = parsed.port

    # 校验 scheme、hostname、port 完全一致
    if client_domain != config_domain or client_scheme != config_scheme or client_port != config_port:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized access"
        )

    return request
