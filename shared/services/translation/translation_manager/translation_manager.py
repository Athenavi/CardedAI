"""
多语言翻译管理服务
提供翻译编辑、批量翻译、进度跟踪等功能
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

# 支持的语言配置
SUPPORTED_LANGUAGES = [
    {"code": "en", "name": "English", "native_name": "English"},
    {"code": "zh-CN", "name": "Chinese (Simplified)", "native_name": "简体中文"},
    {"code": "zh-TW", "name": "Chinese (Traditional)", "native_name": "繁體中文"},
    {"code": "ja", "name": "Japanese", "native_name": "日本語"},
    {"code": "ko", "name": "Korean", "native_name": "한국어"},
    {"code": "es", "name": "Spanish", "native_name": "Español"},
    {"code": "fr", "name": "French", "native_name": "Français"},
    {"code": "de", "name": "German", "native_name": "Deutsch"},
    {"code": "ru", "name": "Russian", "native_name": "Русский"},
    {"code": "ar", "name": "Arabic", "native_name": "العربية"}
]

# 默认配置
DEFAULT_DOMAIN = "messages"
DEFAULT_SOURCE_LOCALE = "en"
DEFAULT_STATUS = "translated"


class TranslationManager:
    """
    翻译管理器
    
    功能:
    1. 翻译编辑器（原文/译文对照）
    2. 批量翻译
    3. 翻译状态标记
    4. 翻译进度仪表板
    5. 翻译历史记录
    """
    
    def __init__(self, translations_dir: str = "translations"):
        self.translations_dir = Path(translations_dir)
        self.translations_dir.mkdir(parents=True, exist_ok=True)
        self.supported_languages = SUPPORTED_LANGUAGES

    def get_translation_file(self, locale: str, domain: str = DEFAULT_DOMAIN) -> Dict[str, Any]:
        """获取翻译文件"""
        translation_file = self.translations_dir / locale / f"{domain}.json"
        
        if translation_file.exists():
            try:
                with open(translation_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载翻译文件失败: {e}")
        
        return {}
    
    def save_translation(
        self,
        locale: str,
        key: str,
        value: str,
            domain: str = DEFAULT_DOMAIN,
            status: str = DEFAULT_STATUS
    ) -> bool:
        """保存单个翻译"""
        try:
            translations = self.get_translation_file(locale, domain)
            
            translations[key] = {
                "value": value,
                "status": status,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            translation_file = self.translations_dir / locale / f"{domain}.json"
            translation_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(translation_file, 'w', encoding='utf-8') as f:
                json.dump(translations, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"保存翻译失败: {e}")
            return False
    
    def batch_translate(
        self,
        source_locale: str,
        target_locale: str,
        translations: Dict[str, str],
            domain: str = DEFAULT_DOMAIN
    ) -> Dict[str, Any]:
        """批量翻译"""
        success_count = 0
        failed_keys = []
        
        for key, value in translations.items():
            if self.save_translation(target_locale, key, value, domain):
                success_count += 1
            else:
                failed_keys.append(key)
        
        return {
            "success": len(failed_keys) == 0,
            "total": len(translations),
            "success_count": success_count,
            "failed_count": len(failed_keys),
            "failed_keys": failed_keys
        }

    def get_translation_progress(self, locale: str, domain: str = DEFAULT_DOMAIN) -> Dict[str, Any]:
        """获取翻译进度"""
        source_translations = self.get_translation_file(DEFAULT_SOURCE_LOCALE, domain)
        total_keys = len(source_translations)
        target_translations = self.get_translation_file(locale, domain)
        
        # 统计各状态的翻译数量
        status_counts = {"translated": 0, "pending": 0, "reviewed": 0}
        update_times = []

        for data in target_translations.values():
            if isinstance(data, dict):
                status = data.get("status", "pending")
                if status in status_counts:
                    status_counts[status] += 1
                if "updated_at" in data:
                    update_times.append(data["updated_at"])
            else:
                status_counts["translated"] += 1

        completion_rate = (status_counts["translated"] + status_counts[
            "reviewed"]) / total_keys * 100 if total_keys > 0 else 0
        
        return {
            "locale": locale,
            "total_keys": total_keys,
            **status_counts,
            "completion_rate": round(completion_rate, 2),
            "last_updated": max(update_times) if update_times else None
        }

    def get_all_locales_progress(self, domain: str = DEFAULT_DOMAIN) -> List[Dict[str, Any]]:
        """获取所有语言的翻译进度"""
        progress_list = []
        
        for lang in self.supported_languages:
            if lang["code"] != DEFAULT_SOURCE_LOCALE:
                progress = self.get_translation_progress(lang["code"], domain)
                progress["language"] = lang
                progress_list.append(progress)
        
        progress_list.sort(key=lambda x: x["completion_rate"], reverse=True)
        return progress_list
    
    def get_pending_translations(
        self,
        locale: str,
        limit: int = 50,
            domain: str = DEFAULT_DOMAIN
    ) -> List[Dict[str, Any]]:
        """获取待翻译的内容"""
        source_translations = self.get_translation_file(DEFAULT_SOURCE_LOCALE, domain)
        target_translations = self.get_translation_file(locale, domain)
        
        pending = []
        
        for key, source_data in source_translations.items():
            source_text = source_data if isinstance(source_data, str) else source_data.get("value", "")
            
            if key not in target_translations:
                pending.append({
                    "key": key,
                    "source_text": source_text,
                    "target_text": "",
                    "status": "missing"
                })
            else:
                target_data = target_translations[key]
                if isinstance(target_data, dict) and target_data.get("status") == "pending":
                    pending.append({
                        "key": key,
                        "source_text": source_text,
                        "target_text": target_data.get("value", ""),
                        "status": "pending"
                    })
        
        return pending[:limit]
    
    def export_translations(self, locale: str, format: str = "json") -> Optional[str]:
        """导出翻译文件"""
        translation_file = self.translations_dir / locale / f"{DEFAULT_DOMAIN}.json"
        
        if not translation_file.exists():
            return None
        
        if format == "json":
            return str(translation_file)
        elif format == "po":
            po_file = translation_file.with_suffix('.po')
            try:
                with open(translation_file, 'r', encoding='utf-8') as f:
                    translations = json.load(f)
                
                with open(po_file, 'w', encoding='utf-8') as f:
                    f.write('msgid ""\nmsgstr ""\n"Content-Type: text/plain; charset=utf-8\\n"\n\n')
                    for key, value in translations.items():
                        f.write(f'msgid "{key}"\nmsgstr "{value}"\n\n')
                
                return str(po_file)
            except Exception:
                return None
        return None
    
    def import_translations(
        self,
        locale: str,
        file_path: str,
        merge: bool = False
    ) -> Dict[str, Any]:
        """导入翻译文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_data = json.load(f)
            
            if merge:
                existing = self.get_translation_file(locale)
                existing.update(imported_data)
                imported_data = existing

            translation_file = self.translations_dir / locale / f"{DEFAULT_DOMAIN}.json"
            translation_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(translation_file, 'w', encoding='utf-8') as f:
                json.dump(imported_data, f, ensure_ascii=False, indent=2)
            
            return {
                "success": True,
                "message": f"成功导入 {len(imported_data)} 条翻译",
                "count": len(imported_data)
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"导入失败: {str(e)}"
            }


# 全局实例
translation_manager = TranslationManager()
