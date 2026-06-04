"""
OAuth 第三方登录服务
支持 GitHub, Google, 微信, QQ, 微博等
"""

from typing import Dict, List, Any
from urllib.parse import urlencode

import httpx


class OAuthService:
    """
    OAuth 第三方登录服务
    
    支持的提供商:
    1. GitHub
    2. Google
    3. 微信 (WeChat)
    4. QQ
    5. 微博 (Weibo)
    """
    
    def __init__(self):
        # OAuth 提供商配置
        self.providers = {
            "github": {
                "name": "GitHub",
                "authorize_url": "https://github.com/login/oauth/authorize",
                "token_url": "https://github.com/login/oauth/access_token",
                "user_info_url": "https://api.github.com/user",
                "scope": "user:email",
                "icon": "github"
            },
            "google": {
                "name": "Google",
                "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
                "token_url": "https://oauth2.googleapis.com/token",
                "user_info_url": "https://www.googleapis.com/oauth2/v3/userinfo",
                "scope": "openid profile email",
                "icon": "google"
            },
            "wechat": {
                "name": "微信",
                "authorize_url": "https://open.weixin.qq.com/connect/qrconnect",
                "token_url": "https://api.weixin.qq.com/sns/oauth2/access_token",
                "user_info_url": "https://api.weixin.qq.com/sns/userinfo",
                "scope": "snsapi_login",
                "icon": "wechat"
            },
            "qq": {
                "name": "QQ",
                "authorize_url": "https://graph.qq.com/oauth2.0/authorize",
                "token_url": "https://graph.qq.com/oauth2.0/token",
                "user_info_url": "https://graph.qq.com/user/get_user_info",
                "scope": "get_user_info",
                "icon": "qq"
            },
        }
    
    def get_authorization_url(
        self,
        provider: str,
        client_id: str,
        redirect_uri: str,
        state: str
    ) -> str:
        """
        生成授权URL
        
        Args:
            provider: 提供商名称
            client_id: 客户端ID
            redirect_uri: 回调URI
            state: CSRF保护状态
            
        Returns:
            授权URL
        """
        if provider not in self.providers:
            raise ValueError(f"不支持的OAuth提供商: {provider}")
        
        config = self.providers[provider]
        
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": config["scope"],
            "state": state
        }
        
        # 微信需要特殊处理
        if provider == "wechat":
            params["appid"] = client_id
            del params["client_id"]
        
        return f"{config['authorize_url']}?{urlencode(params)}"
    
    async def exchange_code_for_token(
        self,
        provider: str,
        code: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str
    ) -> Dict[str, Any]:
        """
        用授权码交换访问令牌
        
        Args:
            provider: 提供商名称
            code: 授权码
            client_id: 客户端ID
            client_secret: 客户端密钥
            redirect_uri: 回调URI
            
        Returns:
            令牌信息
        """
        if provider not in self.providers:
            raise ValueError(f"不支持的OAuth提供商: {provider}")
        
        config = self.providers[provider]
        
        data = {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        }
        
        # 微信需要特殊处理
        if provider == "wechat":
            data["appid"] = client_id
            del data["client_id"]
        
        async with httpx.AsyncClient() as client:
            response = await client.post(config["token_url"], data=data)
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"获取令牌失败: {response.text}"
                }
            
            # 解析响应
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                token_data = response.json()
            else:
                # URL编码格式
                from urllib.parse import parse_qs
                parsed = parse_qs(response.text)
                token_data = {k: v[0] for k, v in parsed.items()}
            
            return {
                "success": True,
                "access_token": token_data.get("access_token"),
                "refresh_token": token_data.get("refresh_token"),
                "expires_in": token_data.get("expires_in"),
                "token_type": token_data.get("token_type", "Bearer")
            }
    
    async def get_user_info(
        self,
        provider: str,
        access_token: str
    ) -> Dict[str, Any]:
        """
        获取用户信息
        
        Args:
            provider: 提供商名称
            access_token: 访问令牌
            
        Returns:
            用户信息
        """
        if provider not in self.providers:
            raise ValueError(f"不支持的OAuth提供商: {provider}")
        
        config = self.providers[provider]
        
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                config["user_info_url"],
                headers=headers
            )
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"获取用户信息失败: {response.text}"
                }
            
            user_data = response.json()
            
            # 标准化用户信息
            normalized = self._normalize_user_info(provider, user_data)
            
            return {
                "success": True,
                "user": normalized
            }
    
    def _normalize_user_info(self, provider: str, raw_data: Dict) -> Dict[str, Any]:
        """
        标准化不同提供商的用户信息
        
        Args:
            provider: 提供商名称
            raw_data: 原始用户数据
            
        Returns:
            标准化的用户信息
        """
        if provider == "github":
            return {
                "provider": "github",
                "provider_id": str(raw_data.get("id")),
                "username": raw_data.get("login"),
                "email": raw_data.get("email"),
                "name": raw_data.get("name") or raw_data.get("login"),
                "avatar": raw_data.get("avatar_url"),
                "profile_url": raw_data.get("html_url")
            }
        
        elif provider == "google":
            return {
                "provider": "google",
                "provider_id": raw_data.get("sub"),
                "username": raw_data.get("email"),
                "email": raw_data.get("email"),
                "name": raw_data.get("name"),
                "avatar": raw_data.get("picture"),
                "profile_url": None
            }
        
        elif provider == "wechat":
            return {
                "provider": "wechat",
                "provider_id": raw_data.get("unionid") or raw_data.get("openid"),
                "username": raw_data.get("nickname"),
                "email": None,  # 微信不提供邮箱
                "name": raw_data.get("nickname"),
                "avatar": raw_data.get("headimgurl"),
                "profile_url": None
            }
        
        elif provider == "qq":
            return {
                "provider": "qq",
                "provider_id": raw_data.get("openid"),
                "username": raw_data.get("nickname"),
                "email": None,  # QQ不直接提供邮箱
                "name": raw_data.get("nickname"),
                "avatar": raw_data.get("figureurl_qq_2"),
                "profile_url": None
            }
        
        elif provider == "weibo":
            return {
                "provider": "weibo",
                "provider_id": str(raw_data.get("id")),
                "username": raw_data.get("screen_name"),
                "email": raw_data.get("email"),
                "name": raw_data.get("screen_name"),
                "avatar": raw_data.get("avatar_large"),
                "profile_url": f"https://weibo.com/{raw_data.get('profile_url', '')}"
            }
        
        return raw_data
    
    def get_supported_providers(self) -> List[Dict[str, Any]]:
        """获取支持的OAuth提供商列表"""
        return [
            {
                "key": key,
                "name": config["name"],
                "icon": config["icon"]
            }
            for key, config in self.providers.items()
        ]


# 全局实例
oauth_service = OAuthService()
