"""
表单构建器服务
提供动态表单创建、字段管理、提交处理等功能
"""

from datetime import datetime
from typing import Dict, List, Any, Optional


class FormBuilderService:
    """
    表单构建器服务
    
    功能:
    1. 动态表单创建和编辑
    2. 多种字段类型支持
    3. 表单验证规则配置
    4. 表单提交数据处理
    5. 表单模板管理
    6. 表单统计分析
    """

    def __init__(self):
        # 支持的字段类型
        self.field_types = {
            'text': {
                'name': '单行文本',
                'icon': '📝',
                'default_config': {
                    'placeholder': '',
                    'required': False,
                    'max_length': 255,
                    'min_length': 0
                }
            },
            'textarea': {
                'name': '多行文本',
                'icon': '📄',
                'default_config': {
                    'placeholder': '',
                    'required': False,
                    'rows': 4,
                    'max_length': 5000
                }
            },
            'email': {
                'name': '邮箱',
                'icon': '📧',
                'default_config': {
                    'placeholder': 'example@email.com',
                    'required': True
                }
            },
            'number': {
                'name': '数字',
                'icon': '🔢',
                'default_config': {
                    'placeholder': '',
                    'required': False,
                    'min': None,
                    'max': None
                }
            },
            'select': {
                'name': '下拉选择',
                'icon': '📋',
                'default_config': {
                    'options': [],
                    'required': False,
                    'multiple': False
                }
            },
            'radio': {
                'name': '单选框',
                'icon': '⭕',
                'default_config': {
                    'options': [],
                    'required': False
                }
            },
            'checkbox': {
                'name': '复选框',
                'icon': '☑️',
                'default_config': {
                    'options': [],
                    'required': False
                }
            },
            'date': {
                'name': '日期',
                'icon': '📅',
                'default_config': {
                    'required': False,
                    'format': 'YYYY-MM-DD'
                }
            },
            'file': {
                'name': '文件上传',
                'icon': '📎',
                'default_config': {
                    'required': False,
                    'accept': '*/*',
                    'max_size': 10485760  # 10MB
                }
            },
            'url': {
                'name': '网址',
                'icon': '🔗',
                'default_config': {
                    'placeholder': 'https://',
                    'required': False
                }
            },
            'phone': {
                'name': '电话',
                'icon': '📱',
                'default_config': {
                    'placeholder': '',
                    'required': False,
                    'pattern': r'^1[3-9]\d{9}$'
                }
            }
        }

        # 预设表单模板
        self.form_templates = {
            'contact': {
                'name': '联系表单',
                'description': '标准的联系信息收集表单',
                'fields': [
                    {
                        'type': 'text',
                        'label': '姓名',
                        'name': 'name',
                        'config': {'required': True}
                    },
                    {
                        'type': 'email',
                        'label': '邮箱',
                        'name': 'email',
                        'config': {'required': True}
                    },
                    {
                        'type': 'text',
                        'label': '主题',
                        'name': 'subject',
                        'config': {'required': True}
                    },
                    {
                        'type': 'textarea',
                        'label': '消息',
                        'name': 'message',
                        'config': {'required': True, 'rows': 6}
                    }
                ]
            },
            'feedback': {
                'name': '反馈表单',
                'description': '用户反馈和建议收集',
                'fields': [
                    {
                        'type': 'select',
                        'label': '反馈类型',
                        'name': 'feedback_type',
                        'config': {
                            'required': True,
                            'options': [
                                {'value': 'bug', 'label': 'Bug报告'},
                                {'value': 'feature', 'label': '功能建议'},
                                {'value': 'improvement', 'label': '改进建议'},
                                {'value': 'other', 'label': '其他'}
                            ]
                        }
                    },
                    {
                        'type': 'text',
                        'label': '标题',
                        'name': 'title',
                        'config': {'required': True}
                    },
                    {
                        'type': 'textarea',
                        'label': '详细描述',
                        'name': 'description',
                        'config': {'required': True, 'rows': 8}
                    },
                    {
                        'type': 'email',
                        'label': '联系邮箱(可选)',
                        'name': 'email',
                        'config': {'required': False}
                    }
                ]
            },
            'survey': {
                'name': '调查问卷',
                'description': '简单的满意度调查',
                'fields': [
                    {
                        'type': 'radio',
                        'label': '总体满意度',
                        'name': 'satisfaction',
                        'config': {
                            'required': True,
                            'options': [
                                {'value': '5', 'label': '非常满意'},
                                {'value': '4', 'label': '满意'},
                                {'value': '3', 'label': '一般'},
                                {'value': '2', 'label': '不满意'},
                                {'value': '1', 'label': '非常不满意'}
                            ]
                        }
                    },
                    {
                        'type': 'textarea',
                        'label': '您的建议',
                        'name': 'suggestions',
                        'config': {'required': False, 'rows': 4}
                    }
                ]
            }
        }

    def create_form(
            self,
            title: str,
            description: str = '',
            fields: Optional[List[Dict]] = None,
            template: Optional[str] = None,
            settings: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        创建新表单
        
        Args:
            title: 表单标题
            description: 表单描述
            fields: 字段列表
            template: 使用模板名称
            settings: 表单设置
            
        Returns:
            创建的表单数据
        """
        try:
            # 如果使用模板
            if template and template in self.form_templates:
                template_data = self.form_templates[template]
                if not fields:
                    fields = template_data['fields']

            # 默认设置
            default_settings = {
                'submit_button_text': '提交',
                'success_message': '提交成功!感谢您的反馈。',
                'error_message': '提交失败,请重试。',
                'require_login': False,
                'allow_anonymous': True,
                'max_submissions': None,
                'start_date': None,
                'end_date': None,
                'email_notifications': False,
                'notification_emails': []
            }

            form_settings = {**default_settings, **(settings or {})}

            form_data = {
                'title': title,
                'description': description,
                'fields': fields or [],
                'settings': form_settings,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'status': 'active',
                'submission_count': 0
            }

            return {
                'success': True,
                'data': form_data
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def validate_field_value(
            self,
            field: Dict[str, Any],
            value: Any
    ) -> Dict[str, Any]:
        """
        验证单个字段值
        
        Args:
            field: 字段配置
            value: 字段值
            
        Returns:
            验证结果
        """
        field_type = field.get('type')
        config = field.get('config', {})
        label = field.get('label', '字段')

        # 检查必填
        if config.get('required') and (value is None or value == ''):
            return {
                'valid': False,
                'error': f'{label}是必填项'
            }

        # 如果值为空且非必填,通过验证
        if value is None or value == '':
            return {'valid': True}

        # 根据类型验证
        if field_type == 'email':
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, str(value)):
                return {
                    'valid': False,
                    'error': f'{label}格式不正确'
                }

        elif field_type == 'phone':
            import re
            pattern = config.get('pattern', r'^1[3-9]\d{9}$')
            if not re.match(pattern, str(value)):
                return {
                    'valid': False,
                    'error': f'{label}格式不正确'
                }

        elif field_type == 'url':
            import re
            url_pattern = r'^https?://'
            if not re.match(url_pattern, str(value)):
                return {
                    'valid': False,
                    'error': f'{label}必须是有效的URL'
                }

        elif field_type == 'number':
            try:
                num_value = float(value)
                min_val = config.get('min')
                max_val = config.get('max')

                if min_val is not None and num_value < min_val:
                    return {
                        'valid': False,
                        'error': f'{label}不能小于{min_val}'
                    }
                if max_val is not None and num_value > max_val:
                    return {
                        'valid': False,
                        'error': f'{label}不能大于{max_val}'
                    }
            except (ValueError, TypeError):
                return {
                    'valid': False,
                    'error': f'{label}必须是数字'
                }

        elif field_type in ['text', 'textarea']:
            max_length = config.get('max_length')
            min_length = config.get('min_length', 0)

            if max_length and len(str(value)) > max_length:
                return {
                    'valid': False,
                    'error': f'{label}不能超过{max_length}个字符'
                }
            if len(str(value)) < min_length:
                return {
                    'valid': False,
                    'error': f'{label}至少需要{min_length}个字符'
                }

        return {'valid': True}

    def validate_form_submission(
            self,
            form_data: Dict[str, Any],
            submission: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        验证表单提交数据
        
        Args:
            form_data: 表单配置
            submission: 提交的数据
            
        Returns:
            验证结果
        """
        errors = []
        validated_data = {}

        for field in form_data.get('fields', []):
            field_name = field.get('name')
            field_value = submission.get(field_name)

            validation_result = self.validate_field_value(field, field_value)

            if not validation_result['valid']:
                errors.append({
                    'field': field_name,
                    'error': validation_result['error']
                })
            else:
                validated_data[field_name] = field_value

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'data': validated_data
        }

    def get_field_types(self) -> List[Dict[str, Any]]:
        """获取所有支持的字段类型"""
        types = []
        for key, config in self.field_types.items():
            types.append({
                'type': key,
                'name': config['name'],
                'icon': config['icon'],
                'default_config': config['default_config']
            })
        return types

    def get_templates(self) -> List[Dict[str, Any]]:
        """获取所有表单模板"""
        templates = []
        for key, data in self.form_templates.items():
            templates.append({
                'id': key,
                'name': data['name'],
                'description': data['description'],
                'field_count': len(data['fields'])
            })
        return templates

    def generate_form_html(
            self,
            form_data: Dict[str, Any],
            form_id: str = 'dynamic-form'
    ) -> str:
        """
        生成表单HTML代码
        
        Args:
            form_data: 表单配置
            form_id: 表单ID
            
        Returns:
            HTML字符串
        """
        html_parts = [f'<form id="{form_id}" class="dynamic-form">']

        # 添加表单描述
        if form_data.get('description'):
            html_parts.append(f'<p class="form-description">{form_data["description"]}</p>')

        # 生成字段
        for field in form_data.get('fields', []):
            html_parts.append(self._render_field(field))

        # 提交按钮
        settings = form_data.get('settings', {})
        button_text = settings.get('submit_button_text', '提交')
        html_parts.append(f'<button type="submit" class="form-submit-btn">{button_text}</button>')

        html_parts.append('</form>')

        return '\n'.join(html_parts)

    def _render_field(self, field: Dict[str, Any]) -> str:
        """渲染单个字段为HTML"""
        field_type = field.get('type')
        label = field.get('label', '')
        name = field.get('name', '')
        config = field.get('config', {})
        required = config.get('required', False)

        required_mark = '<span class="required">*</span>' if required else ''
        html = f'<div class="form-field field-{field_type}">'
        html += f'<label for="{name}">{label}{required_mark}</label>'

        if field_type == 'textarea':
            rows = config.get('rows', 4)
            placeholder = config.get('placeholder', '')
            html += f'<textarea id="{name}" name="{name}" rows="{rows}" placeholder="{placeholder}"'
            if required:
                html += ' required'
            html += '></textarea>'

        elif field_type == 'select':
            multiple = 'multiple' if config.get('multiple') else ''
            html += f'<select id="{name}" name="{name}" {multiple}'
            if required:
                html += ' required'
            html += '>'
            html += '<option value="">请选择</option>'
            for option in config.get('options', []):
                html += f'<option value="{option["value"]}">{option["label"]}</option>'
            html += '</select>'

        elif field_type in ['radio', 'checkbox']:
            for option in config.get('options', []):
                input_type = field_type
                html += f'<label class="{input_type}-label">'
                html += f'<input type="{input_type}" name="{name}" value="{option["value"]}"'
                if required and input_type == 'radio':
                    html += ' required'
                html += f'> {option["label"]}'
                html += '</label>'

        else:
            input_type = field_type if field_type in ['email', 'number', 'date', 'url', 'tel'] else 'text'
            placeholder = config.get('placeholder', '')
            html += f'<input type="{input_type}" id="{name}" name="{name}" placeholder="{placeholder}"'
            if required:
                html += ' required'
            html += '>'

        html += '</div>'
        return html


# 全局实例
form_builder = FormBuilderService()
