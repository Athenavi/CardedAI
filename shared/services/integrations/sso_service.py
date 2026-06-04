"""
SSO单点登录服务
提供OAuth2.0、SAML和LDAP集成功能
"""
import os
import json

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from src.unified_logger import default_logger as logger


class SSOService:
    """
    SSO单点登录服务
    
    功能:
    1. OAuth2.0认证（Google, GitHub, Microsoft等）
    2. SAML 2.0支持
    3. LDAP/AD集成
    4. 单点登录/登出
    """

    def __init__(self):
        # OAuth2配置
        self.oauth_providers = {
            'google': {
                'client_id': os.getenv('GOOGLE_OAUTH_CLIENT_ID'),
                'client_secret': os.getenv('GOOGLE_OAUTH_CLIENT_SECRET'),
                'authorize_url': 'https://accounts.google.com/o/oauth2/v2/auth',
                'token_url': 'https://oauth2.googleapis.com/token',
                'userinfo_url': 'https://www.googleapis.com/oauth2/v3/userinfo',
                'scope': 'openid email profile',
            },
            'github': {
                'client_id': os.getenv('GITHUB_OAUTH_CLIENT_ID'),
                'client_secret': os.getenv('GITHUB_OAUTH_CLIENT_SECRET'),
                'authorize_url': 'https://github.com/login/oauth/authorize',
                'token_url': 'https://github.com/login/oauth/access_token',
                'userinfo_url': 'https://api.github.com/user',
                'scope': 'user:email',
            },
            'microsoft': {
                'client_id': os.getenv('MICROSOFT_OAUTH_CLIENT_ID'),
                'client_secret': os.getenv('MICROSOFT_OAUTH_CLIENT_SECRET'),
                'tenant_id': os.getenv('MICROSOFT_OAUTH_TENANT_ID', 'common'),
                'authorize_url': f'https://login.microsoftonline.com/{os.getenv("MICROSOFT_OAUTH_TENANT_ID", "common")}/oauth2/v2.0/authorize',
                'token_url': f'https://login.microsoftonline.com/{os.getenv("MICROSOFT_OAUTH_TENANT_ID", "common")}/oauth2/v2.0/token',
                'userinfo_url': 'https://graph.microsoft.com/oidc/userinfo',
                'scope': 'openid email profile',
            },
        }

        # SAML配置
        self.saml_config = {
            'entity_id': os.getenv('SAML_ENTITY_ID'),
            'acs_url': os.getenv('SAML_ACS_URL'),
            'idp_metadata_url': os.getenv('SAML_IDP_METADATA_URL'),
            'certificate': os.getenv('SAML_CERTIFICATE'),
            'private_key': os.getenv('SAML_PRIVATE_KEY'),
        }

        # LDAP配置
        self.ldap_config = {
            'server': os.getenv('LDAP_SERVER'),
            'port': int(os.getenv('LDAP_PORT', '389')),
            'base_dn': os.getenv('LDAP_BASE_DN'),
            'bind_dn': os.getenv('LDAP_BIND_DN'),
            'bind_password': os.getenv('LDAP_BIND_PASSWORD'),
            'user_filter': os.getenv('LDAP_USER_FILTER', '(uid={username})'),
            'use_ssl': os.getenv('LDAP_USE_SSL', 'false').lower() == 'true',
        }

    async def get_oauth_authorization_url(self, provider: str, redirect_uri: str,
                                          state: str = None) -> str:
        """
        获取OAuth2授权URL
        
        Args:
            provider: OAuth提供商 (google/github/microsoft)
            redirect_uri: 回调URL
            state: 状态参数
            
        Returns:
            授权URL
        """
        if provider not in self.oauth_providers:
            raise ValueError(f"Unsupported OAuth provider: {provider}")

        config = self.oauth_providers[provider]

        if not config['client_id']:
            raise ValueError(f"OAuth {provider} not configured")

        import urllib.parse

        params = {
            'client_id': config['client_id'],
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': config['scope'],
        }

        if state:
            params['state'] = state

        # Google需要access_type和prompt
        if provider == 'google':
            params['access_type'] = 'offline'
            params['prompt'] = 'consent'

        query_string = urllib.parse.urlencode(params)
        authorization_url = f"{config['authorize_url']}?{query_string}"

        return authorization_url

    async def handle_oauth_callback(self, db, provider: str, code: str,
                                    redirect_uri: str) -> Dict[str, Any]:
        """
        处理OAuth回调
        
        Args:
            db: 数据库会话
            provider: OAuth提供商
            code: 授权码
            redirect_uri: 回调URL
            
        Returns:
            用户信息和访问令牌
        """
        if provider not in self.oauth_providers:
            raise ValueError(f"Unsupported OAuth provider: {provider}")

        config = self.oauth_providers[provider]

        # 交换授权码为访问令牌
        token_data = await self._exchange_code_for_token(provider, code, redirect_uri)

        # 获取用户信息
        userinfo = await self._get_userinfo(provider, token_data['access_token'])

        # 查找或创建用户
        user = await self._find_or_create_user(db, userinfo, provider)

        return {
            'user': user,
            'token': token_data['access_token'],
            'provider': provider,
        }

    async def _exchange_code_for_token(self, provider: str, code: str,
                                       redirect_uri: str) -> Dict[str, Any]:
        """交换授权码为访问令牌"""
        import aiohttp

        config = self.oauth_providers[provider]

        data = {
            'client_id': config['client_id'],
            'client_secret': config['client_secret'],
            'code': code,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code',
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(config['token_url'], data=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Token exchange failed: {error_text}")

                return await response.json()

    async def _get_userinfo(self, provider: str, access_token: str) -> Dict[str, Any]:
        """获取用户信息"""
        import aiohttp

        config = self.oauth_providers[provider]

        headers = {
            'Authorization': f'Bearer {access_token}',
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(config['userinfo_url'], headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Failed to get userinfo: {error_text}")

                return await response.json()

    async def _find_or_create_user(self, db, userinfo: Dict, provider: str):
        """查找或创建用户"""
        from sqlalchemy import select
        from shared.models.user import User

        # 根据邮箱查找用户
        email = userinfo.get('email')
        if not email:
            raise ValueError("Email not provided by OAuth provider")

        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            # 创建新用户
            username = userinfo.get('preferred_username') or userinfo.get('login') or email.split('@')[0]

            user = User(
                username=username,
                email=email,
                password='',  # OAuth用户不需要密码
                is_active=True,
                oauth_provider=provider,
                oauth_id=userinfo.get('sub') or userinfo.get('id'),
            )

            db.add(user)
            await db.commit()
            await db.refresh(user)

            logger.info(f"New user created via OAuth {provider}: {email}")
        else:
            # 更新OAuth信息
            user.oauth_provider = provider
            user.oauth_id = userinfo.get('sub') or userinfo.get('id')
            await db.commit()

        return user

    async def authenticate_ldap(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        LDAP认证
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            用户信息
        """
        if not self.ldap_config['server']:
            raise ValueError("LDAP not configured")

        try:
            import ldap3

            # 连接LDAP服务器
            server = ldap3.Server(
                self.ldap_config['server'],
                port=self.ldap_config['port'],
                use_ssl=self.ldap_config['use_ssl']
            )

            # 绑定管理员账户
            conn = ldap3.Connection(
                server,
                user=self.ldap_config['bind_dn'],
                password=self.ldap_config['bind_password'],
                auto_bind=True
            )

            # 搜索用户
            user_filter = self.ldap_config['user_filter'].format(username=username)
            conn.search(
                search_base=self.ldap_config['base_dn'],
                search_filter=user_filter,
                attributes=['uid', 'mail', 'cn', 'sn']
            )

            if not conn.entries:
                return None

            # 验证密码
            user_dn = conn.entries[0].entry_dn
            auth_conn = ldap3.Connection(server, user=user_dn, password=password)

            if auth_conn.bind():
                # 认证成功
                entry = conn.entries[0]
                return {
                    'username': str(entry.uid.value) if hasattr(entry, 'uid') else username,
                    'email': str(entry.mail.value) if hasattr(entry, 'mail') else None,
                    'full_name': str(entry.cn.value) if hasattr(entry, 'cn') else username,
                }
            else:
                return None

        except ImportError:
            logger.warning("ldap3 library not installed")
            return None
        except Exception as e:
            logger.error(f"LDAP authentication failed: {e}")
            return None

    async def create_saml_login_request(self) -> Dict[str, Any]:
        """
        创建SAML登录请求
        
        Returns:
            SAML请求数据
        """
        if not self.saml_config['entity_id']:
            raise ValueError("SAML not configured")

        try:
            from onelogin.saml2.auth import OneLogin_Saml2_Auth

            request_data = {
                'http_host': '',  # 需要在调用时设置
                'script_name': '/api/v1/sso/saml/acs',
                'server_port': 443,
            }

            settings = {
                'sp': {
                    'entityId': self.saml_config['entity_id'],
                    'assertionConsumerService': {
                        'url': self.saml_config['acs_url'],
                        'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST',
                    },
                },
                'idp': {
                    'entityId': '',  # 从metadata中获取
                    'singleSignOnService': {
                        'url': '',
                        'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect',
                    },
                },
            }

            auth = OneLogin_Saml2_Auth(request_data, settings)
            saml_request = auth.login()

            return {
                'saml_request': saml_request,
                'relay_state': auth.get_last_relay_state(),
            }

        except ImportError:
            logger.warning("python3-saml library not installed")
            return {'error': 'SAML library not available'}
        except Exception as e:
            logger.error(f"SAML login request failed: {e}")
            return {'error': str(e)}

    async def handle_saml_response(self, db, saml_response: str) -> Optional[Dict[str, Any]]:
        """
        处理SAML响应
        
        Args:
            db: 数据库会话
            saml_response: SAML响应数据
            
        Returns:
            用户信息
        """
        try:
            from onelogin.saml2.response import OneLogin_Saml2_Response

            # 这里需要完整的SAML处理逻辑
            # 简化实现，实际需要验证签名、解析属性等

            logger.info("SAML response received (processing not fully implemented)")
            return None

        except ImportError:
            logger.warning("python3-saml library not installed")
            return None
        except Exception as e:
            logger.error(f"SAML response handling failed: {e}")
            return None

    async def create_sso_session(self, user_id: int, session_id: str) -> str:
        """
        创建SSO会话
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            
        Returns:
            SSO令牌
        """
        import uuid
        import hashlib

        # 生成SSO令牌
        sso_token = str(uuid.uuid4())

        # 在实际应用中，应该将SSO令牌存储到Redis或其他共享存储
        # 这里简化处理

        logger.info(f"SSO session created for user {user_id}")
        return sso_token

    async def validate_sso_token(self, sso_token: str) -> Optional[int]:
        """
        验证SSO令牌
        
        Args:
            sso_token: SSO令牌
            
        Returns:
            用户ID
        """
        # 在实际应用中，应该从Redis或其他共享存储中验证
        # 这里简化处理

        logger.warning("SSO token validation not fully implemented")
        return None


# 全局实例
sso_service = SSOService()
