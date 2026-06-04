"""
国际化(i18n)服务
提供多语言翻译、语言检测、本地化等功能
"""

import json
import os
from typing import Dict, List, Any, Optional

# 支持的语言配置
SUPPORTED_LANGUAGES = {
    'zh-CN': {'name': '简体中文', 'native_name': '简体中文', 'locale': 'zh_CN', 'direction': 'ltr', 'flag': '🇨🇳'},
    'zh-TW': {'name': '繁体中文', 'native_name': '繁體中文', 'locale': 'zh_TW', 'direction': 'ltr', 'flag': '🇹🇼'},
    'en': {'name': 'English', 'native_name': 'English', 'locale': 'en_US', 'direction': 'ltr', 'flag': '🇺🇸'},
    'ja': {'name': 'Japanese', 'native_name': '日本語', 'locale': 'ja_JP', 'direction': 'ltr', 'flag': '🇯🇵'},
    'ko': {'name': 'Korean', 'native_name': '한국어', 'locale': 'ko_KR', 'direction': 'ltr', 'flag': '🇰🇷'},
    'fr': {'name': 'French', 'native_name': 'Français', 'locale': 'fr_FR', 'direction': 'ltr', 'flag': '🇫🇷'},
    'de': {'name': 'German', 'native_name': 'Deutsch', 'locale': 'de_DE', 'direction': 'ltr', 'flag': '🇩🇪'},
    'es': {'name': 'Spanish', 'native_name': 'Español', 'locale': 'es_ES', 'direction': 'ltr', 'flag': '🇪🇸'},
    'ar': {'name': 'Arabic', 'native_name': 'العربية', 'locale': 'ar_SA', 'direction': 'rtl', 'flag': '🇸🇦'},
    'ru': {'name': 'Russian', 'native_name': 'Русский', 'locale': 'ru_RU', 'direction': 'ltr', 'flag': '🇷🇺'}
}

# 默认配置
DEFAULT_LANGUAGE = 'zh-CN'
TRANSLATIONS_DIR = 'translations'


class I18nService:
    """
    国际化服务
    
    功能:
    1. 多语言翻译管理
    2. 语言自动检测
    3. 翻译缓存
    4. 翻译文件导入导出
    5. 缺失翻译检测
    6. RTL(从右到左)语言支持
    """

    def __init__(self):
        self.supported_languages = SUPPORTED_LANGUAGES
        self.default_language = DEFAULT_LANGUAGE
        self.translations_cache = {}
        self.translations_dir = TRANSLATIONS_DIR

    def translate(
            self,
            key: str,
            language: str = None,
            variables: Dict[str, Any] = None,
            default: str = None
    ) -> str:
        """翻译文本"""
        lang = language or self.default_language
        translation = self._get_translation(key, lang)

        if not translation and lang != self.default_language:
            translation = self._get_translation(key, self.default_language)

        if not translation:
            translation = default or key

        if variables and isinstance(translation, str):
            try:
                translation = translation.format(**variables)
            except (KeyError, IndexError):
                pass

        return translation

    def _get_translation(self, key: str, language: str) -> Optional[str]:
        """获取单个翻译"""
        if language in self.translations_cache:
            return self.translations_cache[language].get(key)

        translation_file = os.path.join(self.translations_dir, f'{language}.json')
        if os.path.exists(translation_file):
            try:
                with open(translation_file, 'r', encoding='utf-8') as f:
                    translations = json.load(f)
                    self.translations_cache[language] = translations
                    return translations.get(key)
            except Exception:
                pass

        return None

    def detect_language(self, accept_language: str = None) -> str:
        """检测用户语言"""
        if not accept_language:
            return self.default_language

        languages = []
        for part in accept_language.split(','):
            if ';' in part:
                lang, quality = part.split(';')
                quality = float(quality.replace('q=', ''))
            else:
                lang = part
                quality = 1.0
            languages.append((lang.strip(), quality))

        languages.sort(key=lambda x: x[1], reverse=True)

        for lang, _ in languages:
            if lang in self.supported_languages:
                return lang
            base_lang = lang.split('-')[0]
            if base_lang in self.supported_languages:
                return base_lang

        return self.default_language

    def get_supported_languages(self) -> List[Dict[str, Any]]:
        """获取所有支持的语言"""
        return [{'code': code, **info} for code, info in self.supported_languages.items()]

    def get_rtl_languages(self) -> List[str]:
        """获取RTL(从右到左)语言列表"""
        return [code for code, info in self.supported_languages.items() if info['direction'] == 'rtl']

    def is_rtl(self, language: str) -> bool:
        """检查语言是否为RTL"""
        lang_info = self.supported_languages.get(language)
        return lang_info and lang_info['direction'] == 'rtl'

    def add_translation(self, language: str, key: str, value: str) -> Dict[str, Any]:
        """添加翻译"""
        try:
            if language not in self.supported_languages:
                return {'success': False, 'error': f'不支持的语言: {language}'}
            
            if language not in self.translations_cache:
                self.translations_cache[language] = {}

            self.translations_cache[language][key] = value
            self._save_translations(language)

            return {'success': True, 'message': '翻译添加成功'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def batch_add_translations(self, language: str, translations: Dict[str, str]) -> Dict[str, Any]:
        """批量添加翻译"""
        try:
            if language not in self.supported_languages:
                return {'success': False, 'error': f'不支持的语言: {language}'}
            
            if language not in self.translations_cache:
                self.translations_cache[language] = {}

            self.translations_cache[language].update(translations)
            self._save_translations(language)

            return {
                'success': True,
                'count': len(translations),
                'message': f'成功添加{len(translations)}条翻译'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_missing_translations(self, language: str, reference_language: str = None) -> List[str]:
        """获取缺失的翻译"""
        ref_lang = reference_language or self.default_language
        ref_translations = self._load_translations(ref_lang)
        target_translations = self._load_translations(language)
        
        if not ref_translations:
            return []
        if not target_translations:
            return list(ref_translations.keys())

        return [key for key in ref_translations.keys() if key not in target_translations]

    def _load_translations(self, language: str) -> Dict[str, str]:
        """加载翻译（从缓存或文件）"""
        if language in self.translations_cache:
            return self.translations_cache[language]

        translation_file = os.path.join(self.translations_dir, f'{language}.json')
        if os.path.exists(translation_file):
            try:
                with open(translation_file, 'r', encoding='utf-8') as f:
                    translations = json.load(f)
                    self.translations_cache[language] = translations
                    return translations
            except Exception:
                pass

        return {}

    def export_translations(self, language: str = None, format: str = 'json') -> Dict[str, Any]:
        """导出翻译"""
        try:
            if language:
                translations = self.translations_cache.get(language, {})
                return {'success': True, 'data': {language: translations}, 'format': format}
            else:
                all_translations = {
                    lang: self.translations_cache.get(lang, {})
                    for lang in self.supported_languages.keys()
                    if self.translations_cache.get(lang)
                }
                return {'success': True, 'data': all_translations, 'format': format}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def import_translations(self, data: Dict[str, Dict[str, str]], overwrite: bool = False) -> Dict[str, Any]:
        """导入翻译"""
        try:
            imported_count = 0
            errors = []

            for language, translations in data.items():
                if language not in self.supported_languages:
                    errors.append(f'不支持的语言: {language}')
                    continue

                if language not in self.translations_cache:
                    self.translations_cache[language] = {}

                if overwrite:
                    self.translations_cache[language].update(translations)
                else:
                    for key, value in translations.items():
                        if key not in self.translations_cache[language]:
                            self.translations_cache[language][key] = value
                            imported_count += 1

                self._save_translations(language)

            return {
                'success': True,
                'imported': imported_count,
                'errors': errors,
                'message': f'成功导入{imported_count}条翻译'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _save_translations(self, language: str):
        """保存翻译到文件"""
        try:
            os.makedirs(self.translations_dir, exist_ok=True)
            translation_file = os.path.join(self.translations_dir, f'{language}.json')
            translations = self.translations_cache.get(language, {})

            with open(translation_file, 'w', encoding='utf-8') as f:
                json.dump(translations, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving translations: {e}")

    def generate_translation_template(self) -> Dict[str, str]:
        """生成翻译模板(基于默认语言)"""
        return self.translations_cache.get(self.default_language, {})

    def get_language_stats(self) -> Dict[str, Any]:
        """获取语言统计信息"""
        return {
            lang_code: {
                'total_translations': len(self.translations_cache.get(lang_code, {})),
                'is_default': lang_code == self.default_language,
                'is_rtl': self.is_rtl(lang_code)
            }
            for lang_code in self.supported_languages.keys()
        }


# 全局实例
i18n_service = I18nService()
