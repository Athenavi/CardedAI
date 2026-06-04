"""
多语言服务
提供翻译管理、语言检测、自动翻译和语言切换功能
"""
import os
import json

from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from src.unified_logger import default_logger as logger


class TranslationService:
    """
    多语言服务
    
    功能:
    1. 翻译文件管理
    2. 语言检测和切换
    3. 自动翻译（集成第三方API）
    4. 翻译缓存
    5. 缺失翻译检测
    """

    def __init__(self, translations_dir: str = None):
        """
        初始化翻译服务
        
        Args:
            translations_dir: 翻译文件目录
        """
        self.translations_dir = translations_dir or os.getenv('TRANSLATIONS_DIR', './translations')
        os.makedirs(self.translations_dir, exist_ok=True)

        # 支持的语言列表
        self.supported_languages = {
            'en': {'name': 'English', 'native_name': 'English', 'direction': 'ltr'},
            'zh': {'name': 'Chinese', 'native_name': '中文', 'direction': 'ltr'},
            'ja': {'name': 'Japanese', 'native_name': '日本語', 'direction': 'ltr'},
            'ko': {'name': 'Korean', 'native_name': '한국어', 'direction': 'ltr'},
            'es': {'name': 'Spanish', 'native_name': 'Español', 'direction': 'ltr'},
            'fr': {'name': 'French', 'native_name': 'Français', 'direction': 'ltr'},
            'de': {'name': 'German', 'native_name': 'Deutsch', 'direction': 'ltr'},
            'ar': {'name': 'Arabic', 'native_name': 'العربية', 'direction': 'rtl'},
        }

        # 默认语言
        self.default_language = os.getenv('DEFAULT_LANGUAGE', 'en')

        # 翻译缓存
        self.translation_cache: Dict[str, Dict[str, str]] = {}

        # 加载翻译文件
        self._load_translations()

    def _load_translations(self):
        """加载所有翻译文件"""
        for lang_code in self.supported_languages.keys():
            translation_file = os.path.join(self.translations_dir, f'{lang_code}.json')
            if os.path.exists(translation_file):
                try:
                    with open(translation_file, 'r', encoding='utf-8') as f:
                        self.translation_cache[lang_code] = json.load(f)
                    logger.info(f"Loaded translations for {lang_code}")
                except Exception as e:
                    logger.error(f"Failed to load translations for {lang_code}: {e}")
                    self.translation_cache[lang_code] = {}
            else:
                self.translation_cache[lang_code] = {}

    def get_translation(self, key: str, language: str = None, default: str = None) -> str:
        """
        获取翻译
        
        Args:
            key: 翻译键
            language: 语言代码
            default: 默认值
            
        Returns:
            翻译文本
        """
        lang = language or self.default_language

        # 从缓存中获取
        if lang in self.translation_cache:
            translation = self.translation_cache[lang].get(key)
            if translation:
                return translation

        # 回退到默认语言
        if lang != self.default_language and self.default_language in self.translation_cache:
            translation = self.translation_cache[self.default_language].get(key)
            if translation:
                return translation

        # 返回默认值或键本身
        return default or key

    def set_translation(self, key: str, value: str, language: str):
        """
        设置翻译
        
        Args:
            key: 翻译键
            value: 翻译值
            language: 语言代码
        """
        if language not in self.translation_cache:
            self.translation_cache[language] = {}

        self.translation_cache[language][key] = value

        # 保存到文件
        self._save_translations(language)

    def _save_translations(self, language: str):
        """保存翻译到文件"""
        translation_file = os.path.join(self.translations_dir, f'{language}.json')

        try:
            with open(translation_file, 'w', encoding='utf-8') as f:
                json.dump(self.translation_cache.get(language, {}), f, ensure_ascii=False, indent=2)
            logger.info(f"Saved translations for {language}")
        except Exception as e:
            logger.error(f"Failed to save translations for {language}: {e}")

    def get_supported_languages(self) -> List[Dict[str, Any]]:
        """
        获取支持的语言列表
        
        Returns:
            语言列表
        """
        languages = []
        for code, info in self.supported_languages.items():
            languages.append({
                'code': code,
                'name': info['name'],
                'native_name': info['native_name'],
                'direction': info['direction'],
                'is_default': code == self.default_language,
            })
        return languages

    def detect_language(self, accept_language: str = None) -> str:
        """
        检测用户语言
        
        Args:
            accept_language: HTTP Accept-Language头
            
        Returns:
            检测到的语言代码
        """
        if not accept_language:
            return self.default_language

        # 解析Accept-Language头
        languages = [lang.split(';')[0].strip() for lang in accept_language.split(',')]

        for lang in languages:
            # 尝试精确匹配
            if lang in self.supported_languages:
                return lang

            # 尝试主语言匹配 (如 zh-CN -> zh)
            main_lang = lang.split('-')[0]
            if main_lang in self.supported_languages:
                return main_lang

        return self.default_language

    async def auto_translate(self, text: str, from_lang: str, to_lang: str,
                             api_key: str = None) -> str:
        """
        自动翻译文本（使用第三方API）
        
        Args:
            text: 要翻译的文本
            from_lang: 源语言
            to_lang: 目标语言
            api_key: API密钥
            
        Returns:
            翻译后的文本
        """
        if not api_key:
            api_key = os.getenv('TRANSLATION_API_KEY')

        if not api_key:
            logger.warning("Translation API key not configured")
            return text

        # 这里可以集成不同的翻译API
        # 例如 Google Translate, DeepL, Azure Translator等

        try:
            # 示例：使用Google Translate API
            import aiohttp

            url = "https://translation.googleapis.com/language/translate/v2"
            params = {
                'key': api_key,
                'q': text,
                'source': from_lang,
                'target': to_lang,
                'format': 'text'
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        translated_text = data['data']['translations'][0]['translatedText']
                        return translated_text
                    else:
                        logger.error(f"Translation API error: {response.status}")
                        return text

        except Exception as e:
            logger.error(f"Auto translation failed: {e}")
            return text

    def get_missing_translations(self, language: str) -> List[str]:
        """
        获取缺失的翻译键
        
        Args:
            language: 语言代码
            
        Returns:
            缺失的翻译键列表
        """
        if language not in self.translation_cache:
            return list(self.translation_cache.get(self.default_language, {}).keys())

        default_keys = set(self.translation_cache.get(self.default_language, {}).keys())
        lang_keys = set(self.translation_cache.get(language, {}).keys())

        missing_keys = default_keys - lang_keys
        return list(missing_keys)

    def export_translations(self, language: str = None) -> Dict[str, Any]:
        """
        导出翻译
        
        Args:
            language: 语言代码（None表示所有语言）
            
        Returns:
            翻译数据
        """
        if language:
            return {
                'language': language,
                'translations': self.translation_cache.get(language, {})
            }
        else:
            return {
                'languages': list(self.translation_cache.keys()),
                'translations': self.translation_cache
            }

    def import_translations(self, language: str, translations: Dict[str, str],
                            merge: bool = True):
        """
        导入翻译
        
        Args:
            language: 语言代码
            translations: 翻译数据
            merge: 是否合并（True）或覆盖（False）
        """
        if language not in self.translation_cache:
            self.translation_cache[language] = {}

        if merge:
            self.translation_cache[language].update(translations)
        else:
            self.translation_cache[language] = translations

        # 保存到文件
        self._save_translations(language)

    def get_translation_stats(self) -> Dict[str, Any]:
        """
        获取翻译统计
        
        Returns:
            统计数据
        """
        stats = {}
        default_count = len(self.translation_cache.get(self.default_language, {}))

        for lang_code in self.supported_languages.keys():
            lang_translations = self.translation_cache.get(lang_code, {})
            lang_count = len(lang_translations)
            completion_rate = (lang_count / default_count * 100) if default_count > 0 else 0

            stats[lang_code] = {
                'total_keys': lang_count,
                'completion_rate': round(completion_rate, 2),
                'missing_keys': default_count - lang_count,
            }

        return stats


# 全局实例
translation_service = TranslationService()
