"""
翻译记忆系统服务
存储和管理原文-译文对,提供相似度匹配和自动建议
类似WordPress WPML Translation Memory
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# 默认配置
MEMORY_FILE_PATH = Path(__file__).parent.parent.parent / "plugins_data" / "translation_memory.json"
DEFAULT_SIMILARITY_THRESHOLD = 0.7
MAX_SUGGESTIONS = 10


class TranslationMemoryService:
    """翻译记忆库服务"""

    def __init__(self, memory_file: Path = None):
        self.memory_file = memory_file or MEMORY_FILE_PATH
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_memory()
    
    def _load_memory(self):
        """加载翻译记忆库"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    self.memory = json.load(f)
            except Exception:
                self.memory = {}
        else:
            self.memory = {}
    
    def _save_memory(self):
        """保存翻译记忆库"""
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.memory, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to save translation memory: {e}")
    
    def add_translation(self, source_text: str, target_text: str, 
                       source_lang: str, target_lang: str,
                       context: str = '') -> bool:
        """添加翻译到记忆库"""
        key = f"{source_lang}_{target_lang}"
        
        if key not in self.memory:
            self.memory[key] = []

        timestamp = self._get_timestamp()
        
        # 检查是否已存在
        for entry in self.memory[key]:
            if entry['source'] == source_text and entry['context'] == context:
                entry.update({'target': target_text, 'updated_at': timestamp})
                self._save_memory()
                return True
        
        # 添加新条目
        self.memory[key].append({
            'source': source_text,
            'target': target_text,
            'context': context,
            'created_at': timestamp,
            'updated_at': timestamp,
            'usage_count': 0,
        })
        
        self._save_memory()
        return True
    
    def find_similar_translations(self, source_text: str, source_lang: str,
                                  target_lang: str, threshold: float = DEFAULT_SIMILARITY_THRESHOLD) -> List[
        Dict[str, Any]]:
        """查找相似的翻译"""
        key = f"{source_lang}_{target_lang}"
        
        if key not in self.memory:
            return []

        suggestions = [
            {
                'source': entry['source'],
                'target': entry['target'],
                'similarity': round(self._calculate_similarity(source_text, entry['source']), 2),
                'context': entry.get('context', ''),
                'usage_count': entry.get('usage_count', 0),
            }
            for entry in self.memory[key]
            if self._calculate_similarity(source_text, entry['source']) >= threshold
        ]
        
        suggestions.sort(key=lambda x: x['similarity'], reverse=True)
        return suggestions[:MAX_SUGGESTIONS]
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算两个文本的相似度(简化版Levenshtein距离)"""
        if not text1 or not text2:
            return 0.0
        
        if text1 == text2:
            return 1.0
        
        distance = self._levenshtein_distance(text1, text2)
        max_len = max(len(text1), len(text2))

        return max(0.0, 1 - (distance / max_len)) if max_len > 0 else 1.0
    
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """计算Levenshtein编辑距离"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            
            previous_row = current_row
        
        return previous_row[-1]
    
    def get_translation_stats(self) -> Dict[str, Any]:
        """获取翻译记忆统计"""
        total_entries = sum(len(entries) for entries in self.memory.values())

        language_pairs = [
            {
                'source_lang': source_lang,
                'target_lang': target_lang,
                'entry_count': len(entries),
            }
            for key, entries in self.memory.items()
            for source_lang, target_lang in [key.split('_', 1)]
        ]
        
        return {
            'total_entries': total_entries,
            'language_pairs': len(self.memory),
            'pairs_detail': language_pairs,
            'memory_file': str(self.memory_file),
        }
    
    def export_memory(self) -> str:
        """导出翻译记忆为JSON字符串"""
        return json.dumps(self.memory, ensure_ascii=False, indent=2)
    
    def import_memory(self, json_str: str, merge: bool = True) -> bool:
        """导入翻译记忆"""
        try:
            imported = json.loads(json_str)
            
            if merge:
                for key, entries in imported.items():
                    if key not in self.memory:
                        self.memory[key] = []

                    existing_sources = {
                        (e['source'], e.get('context', ''))
                        for e in self.memory[key]
                    }
                    
                    for entry in entries:
                        entry_key = (entry['source'], entry.get('context', ''))
                        if entry_key not in existing_sources:
                            self.memory[key].append(entry)
                            existing_sources.add(entry_key)
            else:
                self.memory = imported
            
            self._save_memory()
            return True
        except Exception as e:
            print(f"Failed to import translation memory: {e}")
            return False
    
    def clear_memory(self, language_pair: Optional[str] = None):
        """清除翻译记忆"""
        if language_pair:
            self.memory.pop(language_pair, None)
        else:
            self.memory = {}
        
        self._save_memory()
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        return datetime.now().isoformat()


# 单例实例
translation_memory_service = TranslationMemoryService()
