from fastapi import Request, HTTPException, status

from src.setting import app_config


def origin_required(request: Request):
    """
    FastAPI兼容的来源验证函数
    """
    client_domain = request.url.hostname
    config_domain = app_config.domain.split(':')[0] if ':' in app_config.domain else app_config.domain

    if client_domain != config_domain:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized access"
        )

    return request
