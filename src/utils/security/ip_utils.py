def get_client_ip(req, trusted_proxies: set = None):
    """
    获取客户端真实 IP

    安全说明：
    - 如果配置了反向代理（如 Nginx），应设置 PROXY_TRUSTED_IPS 环境变量
      指定信任的代理 IP（逗号分隔），只有来自这些 IP 的 X-Forwarded-For 才会被信任。
    - 默认行为：优先使用 X-Real-IP（由反向代理设置），
      仅当请求来自可信代理时才信任 X-Forwarded-For。
    - 无代理时，直接使用 req.client.host。
    """
    if trusted_proxies is None:
        import os
        env_proxies = os.environ.get('PROXY_TRUSTED_IPS', '').strip()
        trusted_proxies = set(p.strip() for p in env_proxies.split(',') if p.strip())

    # 获取直接连接 IP
    direct_ip = getattr(req.client, 'host', '127.0.0.1') if hasattr(req, 'client') and req.client else '127.0.0.1'

    # 仅在来自可信代理时信任 X-Forwarded-For
    if 'X-Forwarded-For' in req.headers and (not trusted_proxies or direct_ip in trusted_proxies):
        ip = req.headers['X-Forwarded-For'].split(',')[0].strip()
    elif 'X-Real-IP' in req.headers:
        ip = req.headers['X-Real-IP'].strip()
    else:
        ip = direct_ip

    return ip


def anonymize_ip_address(ip):
    # 将 IP 地址分割成四个部分
    parts = ip.split('.')
    if len(parts) == 4:
        # 隐藏最后两个部分
        masked_ip = f"{parts[0]}.{parts[1]}.***.***"
        return masked_ip
    return ip
