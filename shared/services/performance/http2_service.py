"""
HTTP/2 和 HTTP/3 配置服务

提供HTTP/2和HTTP/3的配置和优化建议
支持服务器推送和资源预加载
"""

from typing import Dict, Any, List


class HTTP2Service:
    """
    HTTP/2 和 HTTP/3 配置服务
    
    提供现代HTTP协议的配置和优化
    """

    def __init__(self):
        """初始化HTTP/2服务"""
        self.config = {
            'http2_enabled': True,
            'http3_enabled': False,
            'server_push_enabled': True,
            'max_concurrent_streams': 100,
            'initial_window_size': 65535,
            'header_table_size': 4096,
        }

    def get_configuration(self) -> Dict[str, Any]:
        """
        获取当前配置
        
        Returns:
            配置字典
        """
        return self.config.copy()

    def update_configuration(self, **kwargs) -> Dict[str, Any]:
        """
        更新配置
        
        Args:
            **kwargs: 配置项
        
        Returns:
            更新后的配置
        """
        for key, value in kwargs.items():
            if key in self.config:
                self.config[key] = value

        return self.config.copy()

    def get_optimization_suggestions(self) -> List[Dict[str, str]]:
        """
        获取优化建议
        
        Returns:
            优化建议列表
        """
        suggestions = []

        # HTTP/2建议
        if self.config['http2_enabled']:
            suggestions.append({
                'type': 'info',
                'category': 'http2',
                'title': 'HTTP/2已启用',
                'message': 'HTTP/2可以提供更好的性能',
                'recommendations': [
                    '使用单个域名（不需要分片）',
                    '启用服务器推送关键资源',
                    '优化TLS配置',
                    '使用HPACK头部压缩',
                ]
            })
        else:
            suggestions.append({
                'type': 'warning',
                'category': 'http2',
                'title': 'HTTP/2未启用',
                'message': '建议启用HTTP/2以提升性能',
                'recommendations': [
                    '升级Web服务器到支持HTTP/2的版本',
                    '配置SSL/TLS证书（HTTP/2需要HTTPS）',
                    '调整并发流数量',
                ]
            })

        # HTTP/3建议
        if self.config['http3_enabled']:
            suggestions.append({
                'type': 'info',
                'category': 'http3',
                'title': 'HTTP/3已启用',
                'message': 'HTTP/3 (QUIC) 可以提供更低的延迟',
                'recommendations': [
                    '确保UDP端口443开放',
                    '监控连接迁移性能',
                    '测试弱网环境表现',
                ]
            })
        else:
            suggestions.append({
                'type': 'info',
                'category': 'http3',
                'title': 'HTTP/3未启用',
                'message': 'HTTP/3仍处于实验阶段，但值得尝试',
                'recommendations': [
                    '考虑在CDN层面启用HTTP/3',
                    '测试客户端兼容性',
                    '监控错误率',
                ]
            })

        # 服务器推送建议
        if self.config['server_push_enabled']:
            suggestions.append({
                'type': 'tip',
                'category': 'server_push',
                'title': '服务器推送已启用',
                'message': '合理使用服务器推送可以提升首屏加载速度',
                'recommendations': [
                    '只推送关键资源（CSS、字体、关键JS）',
                    '避免推送过多资源',
                    '使用Link头声明推送资源',
                    '监控推送资源的缓存命中率',
                ]
            })

        return suggestions

    def generate_nginx_config(self) -> str:
        """
        生成Nginx配置示例
        
        Returns:
            Nginx配置字符串
        """
        config = '''
# HTTP/2 Nginx 配置示例

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    
    # SSL证书配置
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # HTTP/2优化
    http2_max_concurrent_streams 100;
    http2_initial_window_size 65535;
    http2_header_table_size 4096;
    
    # TLS优化
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    location / {
        # 服务器推送示例
        add_header Link "</css/style.css>; rel=preload; as=style";
        add_header Link "</js/app.js>; rel=preload; as=script";
        add_header Link "</fonts/main.woff2>; rel=preload; as=font; crossorigin";
        
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# HTTP/3 配置（需要Nginx 1.25+和QUIC支持）
server {
    listen 443 quic;
    listen [::]:443 quic;
    
    # HTTP/3特定配置
    http3 on;
    quic_retry on;
    
    add_header Alt-Svc 'h3=":443"; ma=86400';
    
    # ... 其他配置同HTTP/2
}
        '''.strip()

        return config

    def generate_apache_config(self) -> str:
        """
        生成Apache配置示例
        
        Returns:
            Apache配置字符串
        """
        config = '''
# HTTP/2 Apache 配置示例

# 启用HTTP/2模块
LoadModule http2_module modules/mod_http2.so

# 全局HTTP/2配置
Protocols h2 http/1.1
H2MaxConcurrentStreams 100
H2WindowSize 65535
H2HeaderTableSize 4096

<VirtualHost *:443>
    ServerName example.com
    
    # SSL配置
    SSLEngine on
    SSLCertificateFile /path/to/cert.pem
    SSLCertificateKeyFile /path/to/key.pem
    
    # TLS优化
    SSLProtocol all -SSLv3 -TLSv1 -TLSv1.1
    SSLCipherSuite HIGH:!aNULL:!MD5
    SSLHonorCipherOrder on
    
    # HSTS
    Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"
    
    # 服务器推送
    Header add Link "</css/style.css>; rel=preload; as=style"
    Header add Link "</js/app.js>; rel=preload; as=script"
    
    DocumentRoot /var/www/html
</VirtualHost>
        '''.strip()

        return config

    def get_best_practices(self) -> Dict[str, Any]:
        """
        获取最佳实践
        
        Returns:
            最佳实践字典
        """
        return {
            'general': {
                'title': '通用最佳实践',
                'items': [
                    '始终使用HTTPS（HTTP/2和HTTP/3都需要）',
                    '优化TLS配置以减少握手时间',
                    '启用会话复用和票据',
                    '使用OCSP Stapling加速证书验证',
                ]
            },
            'http2': {
                'title': 'HTTP/2优化',
                'items': [
                    '不需要域名分片（HTTP/2支持多路复用）',
                    '合并小文件以减少请求数',
                    '使用服务器推送关键资源',
                    '优化头部大小（使用短cookie名）',
                    '调整并发流数量（默认100）',
                ]
            },
            'http3': {
                'title': 'HTTP/3 (QUIC) 优化',
                'items': [
                    '确保UDP端口443开放',
                    '利用0-RTT快速重连',
                    '测试连接迁移功能',
                    '监控队头阻塞改善情况',
                    '注意防火墙和代理兼容性',
                ]
            },
            'server_push': {
                'title': '服务器推送最佳实践',
                'items': [
                    '只推送用户确实需要的资源',
                    '避免推送可缓存的大文件',
                    '使用Link头声明推送关系',
                    '监控推送资源的实际使用情况',
                    '考虑使用Early Hints (103状态码)',
                ]
            },
            'monitoring': {
                'title': '监控指标',
                'items': [
                    'HTTP/2连接数和流数',
                    '服务器推送命中率',
                    'TLS握手时间',
                    '首字节时间 (TTFB)',
                    '页面完全加载时间',
                ]
            }
        }


# 全局实例
http2_service = HTTP2Service()

# 导出
__all__ = ['HTTP2Service', 'http2_service']
