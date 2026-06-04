"""
翻译导出/导入服务

支持多种格式的翻译文件导出和导入
包括PO/MO、JSON、YAML格式
"""

import json
from datetime import datetime
from typing import Any, Dict

import yaml


class TranslationExportImport:
    """
    翻译导出/导入服务
    
    支持多种格式的翻译文件操作
    """

    def __init__(self):
        """初始化导出导入服务"""
        # 支持的格式
        self.supported_formats = ['json', 'yaml', 'po']

    def export_to_json(
            self,
            translations: Dict[str, Dict[str, str]],
            language_code: str,
            pretty: bool = True
    ) -> str:
        """
        导出为JSON格式
        
        Args:
            translations: 翻译数据 {key: translation}
            language_code: 语言代码
            pretty: 是否格式化
        
        Returns:
            JSON字符串
        """
        export_data = {
            'language': language_code,
            'exported_at': datetime.now().isoformat(),
            'total_strings': len(translations),
            'translations': translations,
        }

        if pretty:
            return json.dumps(export_data, indent=2, ensure_ascii=False)
        else:
            return json.dumps(export_data, ensure_ascii=False)

    def export_to_yaml(
            self,
            translations: Dict[str, Dict[str, str]],
            language_code: str
    ) -> str:
        """
        导出为YAML格式
        
        Args:
            translations: 翻译数据
            language_code: 语言代码
        
        Returns:
            YAML字符串
        """
        export_data = {
            'language': language_code,
            'exported_at': datetime.now().isoformat(),
            'total_strings': len(translations),
            'translations': translations,
        }

        return yaml.dump(export_data, allow_unicode=True, default_flow_style=False)

    def export_to_po(
            self,
            translations: Dict[str, Dict[str, str]],
            language_code: str,
            project_name: str = "FastBlog",
            version: str = "1.0"
    ) -> str:
        """
        导出为PO格式（Gettext）
        
        Args:
            translations: 翻译数据
            language_code: 语言代码
            project_name: 项目名称
            version: 版本
        
        Returns:
            PO格式字符串
        """
        lines = []

        # PO文件头
        lines.append('# FastBlog Translation File')
        lines.append(f'# Language: {language_code}')
        lines.append(f'# Generated at: {datetime.now().isoformat()}')
        lines.append('')
        lines.append('msgid ""')
        lines.append('msgstr ""')
        lines.append('"Project-Id-Version: {} {}\\n"'.format(project_name, version))
        lines.append('"Language: {}\\n"'.format(language_code))
        lines.append('"Content-Type: text/plain; charset=UTF-8\\n"')
        lines.append('"Content-Transfer-Encoding: 8bit\\n"')
        lines.append('')

        # 翻译条目
        for key, trans_data in translations.items():
            msgid = key
            msgstr = trans_data.get('translation', '') if isinstance(trans_data, dict) else trans_data

            lines.append(f'msgid "{self._escape_po_string(msgid)}"')
            lines.append(f'msgstr "{self._escape_po_string(msgstr)}"')
            lines.append('')

        return '\n'.join(lines)

    def import_from_json(self, json_content: str) -> Dict[str, Any]:
        """
        从JSON导入
        
        Args:
            json_content: JSON字符串
        
        Returns:
            导入的翻译数据
        """
        try:
            data = json.loads(json_content)

            return {
                'success': True,
                'language': data.get('language', 'unknown'),
                'total_strings': data.get('total_strings', 0),
                'translations': data.get('translations', {}),
                'message': f"Successfully imported {data.get('total_strings', 0)} strings",
            }
        except json.JSONDecodeError as e:
            return {
                'success': False,
                'error': f"Invalid JSON format: {str(e)}",
            }

    def import_from_yaml(self, yaml_content: str) -> Dict[str, Any]:
        """
        从YAML导入
        
        Args:
            yaml_content: YAML字符串
        
        Returns:
            导入的翻译数据
        """
        try:
            data = yaml.safe_load(yaml_content)

            return {
                'success': True,
                'language': data.get('language', 'unknown'),
                'total_strings': data.get('total_strings', 0),
                'translations': data.get('translations', {}),
                'message': f"Successfully imported {data.get('total_strings', 0)} strings",
            }
        except yaml.YAMLError as e:
            return {
                'success': False,
                'error': f"Invalid YAML format: {str(e)}",
            }

    def import_from_po(self, po_content: str) -> Dict[str, Any]:
        """
        从PO格式导入
        
        Args:
            po_content: PO格式字符串
        
        Returns:
            导入的翻译数据
        """
        try:
            translations = {}
            current_msgid = None

            for line in po_content.split('\n'):
                line = line.strip()

                if line.startswith('msgid "'):
                    current_msgid = self._unescape_po_string(line[7:-1])
                elif line.startswith('msgstr "') and current_msgid is not None:
                    msgstr = self._unescape_po_string(line[8:-1])
                    translations[current_msgid] = {
                        'translation': msgstr,
                        'translated': bool(msgstr),
                    }
                    current_msgid = None

            return {
                'success': True,
                'language': 'unknown',  # PO文件中可能包含语言信息
                'total_strings': len(translations),
                'translations': translations,
                'message': f"Successfully imported {len(translations)} strings",
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to parse PO file: {str(e)}",
            }

    def batch_export(
            self,
            all_translations: Dict[str, Dict[str, Dict[str, str]]],
            format: str = 'json'
    ) -> Dict[str, str]:
        """
        批量导出所有语言
        
        Args:
            all_translations: 所有语言的翻译数据 {lang_code: translations}
            format: 导出格式
        
        Returns:
            {语言代码: 文件内容}
        """
        results = {}

        for lang_code, translations in all_translations.items():
            if format == 'json':
                content = self.export_to_json(translations, lang_code)
            elif format == 'yaml':
                content = self.export_to_yaml(translations, lang_code)
            elif format == 'po':
                content = self.export_to_po(translations, lang_code)
            else:
                continue

            results[lang_code] = content

        return results

    def batch_import(
            self,
            files: Dict[str, str],
            format: str = 'json'
    ) -> Dict[str, Any]:
        """
        批量导入多个语言文件
        
        Args:
            files: {文件名: 文件内容}
            format: 文件格式
        
        Returns:
            导入结果汇总
        """
        results = {
            'total_files': len(files),
            'successful': 0,
            'failed': 0,
            'details': [],
        }

        for filename, content in files.items():
            if format == 'json':
                result = self.import_from_json(content)
            elif format == 'yaml':
                result = self.import_from_yaml(content)
            elif format == 'po':
                result = self.import_from_po(content)
            else:
                result = {'success': False, 'error': f'Unsupported format: {format}'}

            detail = {
                'filename': filename,
                'success': result['success'],
            }

            if result['success']:
                results['successful'] += 1
                detail['language'] = result.get('language')
                detail['total_strings'] = result.get('total_strings')
            else:
                results['failed'] += 1
                detail['error'] = result.get('error')

            results['details'].append(detail)

        return results

    def _escape_po_string(self, s: str) -> str:
        """
        转义PO字符串
        
        Args:
            s: 原始字符串
        
        Returns:
            转义后的字符串
        """
        s = s.replace('\\', '\\\\')
        s = s.replace('"', '\\"')
        s = s.replace('\n', '\\n')
        s = s.replace('\t', '\\t')
        return s

    def _unescape_po_string(self, s: str) -> str:
        """
        反转义PO字符串
        
        Args:
            s: 转义后的字符串
        
        Returns:
            原始字符串
        """
        s = s.replace('\\n', '\n')
        s = s.replace('\\t', '\t')
        s = s.replace('\\"', '"')
        s = s.replace('\\\\', '\\')
        return s


# 全局实例
translation_io = TranslationExportImport()

# 导出
__all__ = ['TranslationExportImport', 'translation_io']
