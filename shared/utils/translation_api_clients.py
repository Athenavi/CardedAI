"""
翻译服务API客户端
集成Google Translate、DeepL等翻译服务商API
"""
from typing import Dict, Any, Optional, List

import httpx


class GoogleTranslateClient:
    """Google Translate API客户端"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://translation.googleapis.com/language/translate/v2"

    def translate(self, text: str, target_lang: str, source_lang: str = 'auto') -> Dict[str, Any]:
        """
        翻译文本

        Args:
            text: 要翻译的文本
            target_lang: 目标语言代码
            source_lang: 源语言代码(auto为自动检测)

        Returns:
            翻译结果
        """
        try:
            params = {
                'key': self.api_key,
                'q': text,
                'target': target_lang,
            }

            if source_lang != 'auto':
                params['source'] = source_lang

            response = httpx.post(self.base_url, json=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            translated_text = data['data']['translations'][0]['translatedText']

            return {
                'success': True,
                'translated_text': translated_text,
                'detected_source': data['data']['translations'][0].get('detectedSourceLanguage', ''),
                'provider': 'google',
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'provider': 'google',
            }

    def detect_language(self, text: str) -> Dict[str, Any]:
        """
        检测语言

        Args:
            text: 要检测的文本

        Returns:
            检测结果
        """
        try:
            params = {
                'key': self.api_key,
                'q': text,
            }

            response = httpx.post(f"{self.base_url}/detect", json=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            detections = data['data']['detections'][0]

            # 返回置信度最高的语言
            best_detection = max(detections, key=lambda x: x['confidence'])

            return {
                'success': True,
                'language': best_detection['language'],
                'confidence': best_detection['confidence'],
                'provider': 'google',
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'provider': 'google',
            }


class DeepLClient:
    """DeepL API客户端"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api-free.deepl.com/v2"  # 免费版

    def translate(self, text: str, target_lang: str, source_lang: str = '') -> Dict[str, Any]:
        """
        翻译文本

        Args:
            text: 要翻译的文本
            target_lang: 目标语言代码(EN/ZH/JA等)
            source_lang: 源语言代码(可选)

        Returns:
            翻译结果
        """
        try:
            headers = {
                'Authorization': f'DeepL-Auth-Key {self.api_key}',
                'Content-Type': 'application/x-www-form-urlencoded',
            }

            data = {
                'text': text,
                'target_lang': target_lang.upper(),
            }

            if source_lang:
                data['source_lang'] = source_lang.upper()

            response = httpx.post(
                f"{self.base_url}/translate",
                headers=headers,
                data=data,
                timeout=10
            )
            response.raise_for_status()

            result = response.json()
            translated_text = result['translations'][0]['text']

            return {
                'success': True,
                'translated_text': translated_text,
                'detected_source': result['translations'][0].get('detected_source_language', ''),
                'provider': 'deepl',
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'provider': 'deepl',
            }


class TranslationServiceManager:
    """翻译服务管理器"""

    def __init__(self):
        self.clients = {}
        self.default_provider = 'google'

    def register_client(self, provider: str, client):
        """注册翻译客户端"""
        self.clients[provider] = client

    def translate(self, text: str, target_lang: str,
                  source_lang: str = 'auto',
                 provider: Optional[str] = None) -> Dict[str, Any]:
        """
        使用指定或默认提供商翻译

        Args:
            text: 要翻译的文本
            target_lang: 目标语言
            source_lang: 源语言
            provider: 提供商(google/deepl),None则使用默认

        Returns:
            翻译结果
        """
        if not provider:
            provider = self.default_provider

        if provider not in self.clients:
            return {
                'success': False,
                'error': f'Provider {provider} not configured',
            }

        client = self.clients[provider]
        return client.translate(text, target_lang, source_lang)

    def get_available_providers(self) -> List[str]:
        """获取可用的翻译提供商"""
        return list(self.clients.keys())

    def set_default_provider(self, provider: str):
        """设置默认提供商"""
        if provider in self.clients:
            self.default_provider = provider


# 全局实例
translation_service_manager = TranslationServiceManager()
