"""
翻译进度跟踪服务

跟踪多语言翻译的完成进度
统计翻译贡献者
生成翻译报告
"""

from datetime import datetime
from typing import Any, Dict, List, Optional


class TranslationProgressTracker:
    """
    翻译进度跟踪服务
    
    管理和跟踪翻译进度
    """

    def __init__(self):
        """初始化翻译进度跟踪器"""
        # 存储翻译数据 {language_code: {key: {translated: bool, translator: str, updated_at: ...}}}
        self.translations: Dict[str, Dict[str, Dict[str, Any]]] = {}

        # 贡献者统计 {user_id: {translations_count, last_contribution}}
        self.contributors: Dict[int, Dict[str, Any]] = {}

    def register_translation(
            self,
            language_code: str,
            translation_key: str,
            is_translated: bool,
            translator_id: Optional[int] = None,
            translator_name: Optional[str] = None,
    ):
        """
        注册翻译项
        
        Args:
            language_code: 语言代码 (en, zh, ja, etc.)
            translation_key: 翻译键
            is_translated: 是否已翻译
            translator_id: 翻译者ID
            translator_name: 翻译者名称
        """
        if language_code not in self.translations:
            self.translations[language_code] = {}

        self.translations[language_code][translation_key] = {
            'translated': is_translated,
            'translator_id': translator_id,
            'translator_name': translator_name,
            'updated_at': datetime.now().isoformat(),
        }

        # 更新贡献者统计
        if translator_id and is_translated:
            if translator_id not in self.contributors:
                self.contributors[translator_id] = {
                    'name': translator_name,
                    'translations_count': 0,
                    'last_contribution': None,
                }

            self.contributors[translator_id]['translations_count'] += 1
            self.contributors[translator_id]['last_contribution'] = datetime.now().isoformat()

    def get_language_progress(self, language_code: str) -> Dict[str, Any]:
        """
        获取语言翻译进度
        
        Args:
            language_code: 语言代码
        
        Returns:
            进度信息
        """
        if language_code not in self.translations:
            return {
                'language': language_code,
                'total_strings': 0,
                'translated_strings': 0,
                'progress_percentage': 0,
                'untranslated_keys': [],
            }

        translations = self.translations[language_code]
        total = len(translations)
        translated = sum(1 for t in translations.values() if t['translated'])

        progress = (translated / total * 100) if total > 0 else 0

        untranslated_keys = [
            key for key, value in translations.items()
            if not value['translated']
        ]

        return {
            'language': language_code,
            'total_strings': total,
            'translated_strings': translated,
            'untranslated_strings': total - translated,
            'progress_percentage': round(progress, 2),
            'untranslated_keys': untranslated_keys[:50],  # 限制返回数量
        }

    def get_all_languages_progress(self) -> List[Dict[str, Any]]:
        """
        获取所有语言的翻译进度
        
        Returns:
            所有语言的进度列表
        """
        results = []

        for language_code in self.translations.keys():
            progress = self.get_language_progress(language_code)
            results.append(progress)

        # 按进度排序
        results.sort(key=lambda x: x['progress_percentage'], reverse=True)

        return results

    def get_contributor_stats(self) -> List[Dict[str, Any]]:
        """
        获取贡献者统计
        
        Returns:
            贡献者统计列表
        """
        contributors_list = []

        for user_id, stats in self.contributors.items():
            contributors_list.append({
                'user_id': user_id,
                'name': stats['name'],
                'translations_count': stats['translations_count'],
                'last_contribution': stats['last_contribution'],
            })

        # 按翻译数量排序
        contributors_list.sort(key=lambda x: x['translations_count'], reverse=True)

        return contributors_list

    def generate_progress_report(self) -> Dict[str, Any]:
        """
        生成翻译进度报告
        
        Returns:
            完整的进度报告
        """
        languages_progress = self.get_all_languages_progress()
        contributor_stats = self.get_contributor_stats()

        # 计算总体统计
        total_languages = len(languages_progress)
        completed_languages = sum(
            1 for lang in languages_progress
            if lang['progress_percentage'] == 100
        )
        avg_progress = (
            sum(lang['progress_percentage'] for lang in languages_progress) / total_languages
            if total_languages > 0
            else 0
        )

        return {
            'summary': {
                'total_languages': total_languages,
                'completed_languages': completed_languages,
                'average_progress': round(avg_progress, 2),
                'generated_at': datetime.now().isoformat(),
            },
            'languages': languages_progress,
            'top_contributors': contributor_stats[:10],
        }

    def get_untranslated_strings(
            self,
            language_code: str,
            limit: int = 100
    ) -> List[str]:
        """
        获取未翻译的字符串
        
        Args:
            language_code: 语言代码
            limit: 返回数量限制
        
        Returns:
            未翻译的键列表
        """
        if language_code not in self.translations:
            return []

        untranslated = [
            key for key, value in self.translations[language_code].items()
            if not value['translated']
        ]

        return untranslated[:limit]

    def clear_language(self, language_code: str):
        """
        清空指定语言的翻译数据
        
        Args:
            language_code: 语言代码
        """
        if language_code in self.translations:
            del self.translations[language_code]


# 全局实例
translation_tracker = TranslationProgressTracker()

# 导出
__all__ = ['TranslationProgressTracker', 'translation_tracker']
