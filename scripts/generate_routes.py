"""
路由代码生成器
根据 routes.yaml 声明文件自动生成 Django Ninja 和 FastAPI 的路由代码

使用方法:
    python scripts/generate_routes.py

子命令:
    - generate-all: 生成所有代码（默认）
    - sync-to-django: 同步 SQLAlchemy 模型到 Django ORM
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List

import yaml
from jinja2 import Environment, FileSystemLoader, TemplateNotFound


class RouteGenerator:
    """路线代码生成器"""

    # Module 名称到 FastAPI 模块路径的映射
    MODULE_MAPPING = {
        'articles': 'src.api.v1.articles',
        'blog': 'src.api.v1.blog',
        'media': 'src.api.v1.media',
        'category_management': 'src.api.v1.category_management',
        'user_management': 'src.api.v1.user_management',
        'dashboard': 'src.api.v1.dashboard',
        'admin_settings': 'src.api.v1.admin_settings',
        'users': 'src.api.v1.users',
        'notifications': 'src.api.v1.notifications',
        'backup': 'src.api.v1.backup',
        'misc': 'src.api.v1.misc',
        'home': 'src.api.v1.home',
        'category_ext': 'src.api.v1.category_ext',
        'comment_config': 'src.api.v1.comment_config',
        'user_settings': 'src.api.v1.user_settings',
    }

    def __init__(self, config_path: str = None):
        """
        初始化生成器
        
        Args:
            config_path: routes.yaml 配置文件路径
        """
        self.project_root = Path(__file__).parent.parent
        self.config_path = Path(config_path) if config_path else self.project_root / "config" / "routes.yaml"

        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在：{self.config_path}")

        # 加载配置
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        # 加载额外的模型配置（如果有）
        self.models_config_path = self.project_root / "config" / "models.yaml"
        self.extra_models = {}
        if self.models_config_path.exists():
            with open(self.models_config_path, 'r', encoding='utf-8') as f:
                extra_config = yaml.safe_load(f)
                self.extra_models = extra_config.get('models', {})
                print(f"已加载额外模型配置：{len(self.extra_models)} 个模型")

        # 设置模板目录
        self.template_dir = self.project_root / "scripts" / "templates"
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
        self.jinja_env.filters['quote'] = lambda x: f"'{x}'"

        # 注册自定义过滤器
        import sys
        sys.path.insert(0, str(self.project_root))
        from scripts.jinja_filters import register_filters
        register_filters(self.jinja_env)

        # 提取配置信息
        self.api_version = self.config.get('api_version', 'v1')
        self.base_path = self.config.get('base_path', f'/api/{self.api_version}')
        # 合并 models: routes.yaml 中的 + models.yaml 中的
        self.models = {**self.config.get('models', {}), **self.extra_models}
        self.endpoints = self.config.get('endpoints', [])
        self.generation_config = self.config.get('generation', {})
        # 不再使用 shared_models，改为从 models[*].orm 读取

    def generate_all(self):
        """生成所有代码"""
        print("=" * 70)
        print("开始生成路由代码...")
        print("=" * 70)
        print(f"\n配置文件：{self.config_path}")
        print(f"端点数量：{len(self.endpoints)}")
        print(f"模型数量：{len(self.models)}")

        # 1. 生成 Django ORM Mixins（已于V0.2淘汰）
        # self._generate_orm_mixins()

        # 3. 生成 FastAPI 路由
        self._generate_fastapi()

        # 4. 生成 TypeScript 类型和客户端
        self._generate_typescript()

        # 5. 生成 Shared SQLAlchemy Models
        self._generate_shared_models()

        # 6. 优化 SQLAlchemy 模型的导入
        self._optimize_sqlalchemy_imports()

        # 7. 自动格式化生成的文件
        self._format_generated_files()

        print("=" * 70)
        print("✓ 代码生成完成!")
        print("=" * 70)

    def _generate_orm_mixins(self):
        """生成 Django ORM Mixin 文件"""
        print("\n[1/4] 生成 Django ORM Mixins...")

        from datetime import datetime
        output_path = self.project_root / "apps" / "generated" / "auto_orm.py"

        # 导入 settings 以获取表前缀
        try:
            from src.setting import settings
            table_prefix = getattr(settings, 'db_table_prefix', '')
        except ImportError:
            table_prefix = ''

        # 不应该生成 Django ORM 的模型列表（这些是纯响应模型）
        EXCLUDED_MODELS = {
            'ApiResponse',
            'PaginationInfo',
            'UserListResponse',
            'ArticleListResponse',
            'CategoryListResponse',
            'MediaListResponse',
            'CommentListResponse',
        }

        # 过滤掉排除的模型，并为每个模型转换 properties 为 fields
        models_to_generate = {}
        for name, defn in self.models.items():
            if name not in EXCLUDED_MODELS:
                # 复制一份定义，添加转换后的 fields
                model_copy = defn.copy()
                properties = defn.get('properties', {})
                if properties:
                    # 传入模型名称以检测自引用
                    model_copy['fields'] = self._convert_properties_to_fields(properties, model_name=name)
                models_to_generate[name] = model_copy

        template_data = {
            'models': models_to_generate,
            'all_model_names': list(self.models.keys()),  # 传递所有模型名称，用于检查外键引用
            'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'table_prefix': table_prefix,  # 添加表前缀
        }

        content = self._render_template('django_orm_mixins.py.jinja2', template_data)
        self._write_file(output_path, content)
        print(f"  [OK] ORM Mixins: {output_path}")

    def _generate_fastapi(self):
        """生成 FastAPI 路由文件"""
        print("\n[3/4] 生成 FastAPI 路由...")

        output_path = self._get_output_path('fastapi', 'router_file')
        if not output_path:
            print("  ⚠ FastAPI 输出路径未配置")
            return

        # 准备模板数据
        template_data = {
            'api_version': self.api_version,
            'base_path': self.base_path,
            'endpoints': self._filter_endpoints_by_module(),
            'models': self.models,
            'imports': self._collect_fastapi_imports(),
            'handler_mapping': self.config.get('handler_mapping', {}),
            'module_import_map': self.MODULE_MAPPING
        }

        # 渲染模板
        content = self._render_template('fastapi_router.py.jinja2', template_data)

        # 后处理：修复参数格式问题
        import re
        # 在逗号后面添加换行符和正确的缩进（当检测到 Query/Form/Path 时）
        content = re.sub(r',\s*(page|per_page|search|category_id|user_id|status|article_id|slug|tag_name|name)\s*:',
                         r',\n        \1:', content)
        # 修复 request: Request，后面的参数
        content = re.sub(r'(request: Request,)\s*(\w+\s*:)', r'\1\n        \2', content)
        # 修复 db 参数前的格式
        content = re.sub(r'Query\(([^)]+)\),\s*(db: AsyncSession)', r'Query(\1),\n        \2', content)

        # 写入文件
        self._write_file(output_path, content)
        print(f"  [OK] FastAPI Router: {output_path}")

    def _generate_typescript(self):
        """生成 TypeScript 类型定义和 API 客户端"""
        print("\n[4/5] 生成 TypeScript 类型...")

        ts_config = self.generation_config.get('typescript', {})
        if not ts_config:
            print("  ⚠ TypeScript 生成未配置")
            return

        output_dir = self.project_root / ts_config.get('output_dir', 'frontend-next/types/generated')
        output_dir.mkdir(parents=True, exist_ok=True)

        # 生成类型定义
        types_file = output_dir / ts_config.get('types_file', 'api-types.ts')
        types_content = self._render_template('typescript_types.ts.jinja2', {
            'models': self.models,
            'endpoints': self.endpoints
        })
        self._write_file(types_file, types_content)
        print(f"  [OK] TypeScript Types: {types_file}")

        # 生成 API 客户端
        client_file = output_dir / ts_config.get('client_file', 'api-client.ts')
        client_content = self._render_template('typescript_client.ts.jinja2', {
            'endpoints': self.endpoints,
            'base_path': self.base_path
        })
        self._write_file(client_file, client_content)
        print(f"  [OK] TypeScript Client: {client_file}")

    def _generate_shared_models(self):
        """生成 Shared SQLAlchemy 模型文件（从 models[*].orm 读取配置）"""
        print("\n[5/5] 生成 Shared SQLAlchemy Models...")

        # 导入 settings 以获取表前缀
        try:
            from src.setting import settings
        except ImportError:
            settings = type('Settings', (), {'db_table_prefix': ''})()

        table_prefix = getattr(settings, 'db_table_prefix', '')

        # 收集所有需要生成 ORM 的模型（orm: true）
        orm_models = {}
        for model_name, model_def in self.models.items():
            if model_def.get('orm') is True:
                orm_models[model_name] = model_def

        if not orm_models:
            print("  ⚠ 没有需要生成 ORM 的模型，跳过")
            return

        from datetime import datetime
        output_base = self.project_root / "shared" / "models"
        output_base.mkdir(parents=True, exist_ok=True)

        generated_count = 0
        success_models = []

        for model_name, model_def in orm_models.items():
            try:
                # 每个模型生成一个单独的文件
                output_path = output_base / f"{self._model_name_to_filename(model_name)}.py"

                # 从 properties 自动生成 SQLAlchemy 字段，并传入全量模型配置用于外键解析
                properties = model_def.get('properties', {})
                fields = self._convert_properties_to_fields(
                    properties,
                    model_name=model_name,
                    all_models=self.models,
                    table_prefix=table_prefix
                )

                # 获取自定义方法
                def_list = model_def.get('def_list', [])
                custom_methods = {}
                if def_list:
                    defs_target = model_def.get('defs_target', f"{model_name.lower()}_defs.py")
                    custom_methods = self._load_custom_methods_from_target(model_name, def_list, defs_target)

                # 准备模板上下文
                class_def = {
                    'fields': fields,
                    'table': model_def.get('table'),
                    'description': model_def.get('description'),
                    'relationships': model_def.get('relationships', {}),
                    'indexes': model_def.get('indexes', []),
                    'unique_constraints': model_def.get('unique_constraints', []),
                }

                # 检测 uuid 主键 / datetime 默认值（用于控制顶层 import）
                has_uuid_pk = False
                has_datetime_default = False
                for fdef in fields.values():
                    if fdef.get('primary_key') and fdef.get('type') == 'string':
                        has_uuid_pk = True
                    if fdef.get('default') == 'datetime.utcnow':
                        has_datetime_default = True

                template_data = {
                    'model_name': model_name,
                    'classes': {model_name: class_def},
                    'table_prefix': table_prefix,
                    'all_models': self.models,
                    'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'has_numeric': self._check_decimal_fields_from_properties(properties),
                    'has_decimal': self._check_decimal_fields_from_properties(properties),
                    'has_text': self._check_text_fields_from_properties(properties),
                    'has_timestamps': self._check_timestamp_fields_from_properties(properties),
                    'has_foreign_keys': self._check_foreign_keys_in_fields(fields),
                    'has_relationships': self._check_relationships(model_def),
                    'is_unlogged': model_def.get('unlogged', False),
                    'custom_methods': custom_methods,
                    'table_has_indexes': bool(model_def.get('indexes')),
                    'table_has_unique_constraints': bool(model_def.get('unique_constraints')),
                    # 传入 jinja 模板内使用的命名空间变量
                    'ns': {
                        'has_uuid_pk': has_uuid_pk,
                        'has_datetime_default': has_datetime_default,
                    },
                }

                content = self._render_template('sqlalchemy_model.py.jinja2', template_data)
                self._write_file(output_path, content)
                print(f"  [OK] Model: {output_path}")
                success_models.append(model_name)
                generated_count += 1

            except Exception as e:
                import traceback
                print(f"  [ERROR] 生成 {model_name} 失败：{e}")
                print(f"    详细信息：{traceback.format_exc()}")
                # 存在失败模型时直接退出，避免生成不完整的 __init__.py
                raise SystemExit(1)

        # 全部生成成功后才更新 __init__.py
        if success_models:
            successful_orm_config = {k: v for k, v in orm_models.items() if k in success_models}
            self._update_shared_models_init_from_orm(successful_orm_config)

        print(f"  ✓ 共生成 {generated_count} 个模型文件")

    def _get_output_path(self, framework: str, config_key: str) -> Path:
        """获取输出文件路径"""
        gen_config = self.generation_config.get(framework, {})
        if not gen_config:
            return None

        output_dir = self.project_root / gen_config.get('output_dir', '')
        output_file = gen_config.get(config_key, '')

        if output_dir and output_file:
            output_dir.mkdir(parents=True, exist_ok=True)
            return output_dir / output_file

        return None

    def _filter_endpoints_by_module(self) -> Dict[str, List[Dict]]:
        """按模块分组端点"""
        modules = {}
        for endpoint in self.endpoints:
            module_name = endpoint.get('module', 'default')
            if module_name not in modules:
                modules[module_name] = []
            modules[module_name].append(endpoint)
        return modules

    def _collect_django_imports(self) -> List[str]:
        """收集 Django Ninja 需要的导入"""
        imports = set()

        # 基础导入
        imports.add("from ninja import Router, Form, Query, Path")
        imports.add("from django.http import HttpRequest")
        imports.add("from django_blog.django_ninja_compat import ApiResponse")

        # 根据端点参数类型添加导入
        for endpoint in self.endpoints:
            params = endpoint.get('parameters', [])
            for param in params:
                if param.get('location') == 'form':
                    imports.add("from ninja import Form")
                elif param.get('location') == 'query':
                    imports.add("from ninja import Query")
                elif param.get('location') == 'path':
                    imports.add("from ninja import Path")

        return sorted(list(imports))

    def _collect_fastapi_imports(self) -> List[str]:
        """收集 FastAPI 需要的导入"""
        imports = set()

        # 基础导入
        imports.add("from fastapi import APIRouter, Depends, Form, Query, Path")
        imports.add("from src.api.v1.core.responses import ApiResponse")

        # 根据端点是否需要认证添加导入
        for endpoint in self.endpoints:
            if endpoint.get('django_ninja_auth', False) or endpoint.get('fastapi_dependencies', []):
                imports.add("from src.auth import jwt_required_dependency as jwt_required")

        return sorted(list(imports))

    def _model_name_to_filename(self, model_name: str) -> str:
        """将模型名转换为文件名（驼峰转下划线）"""
        import re
        # 在大写字母前插入下划线
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', model_name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def _check_list_fields(self, model_def: Dict) -> bool:
        """检查是否有列表类型字段"""
        for field_def in model_def.get('fields', {}).values():
            if field_def.get('type') == 'array' or field_def.get('type') == 'list':
                return True
        return False

    def _check_numeric_fields(self, model_def: Dict) -> bool:
        """检查是否有数值类型字段"""
        for field_def in model_def.get('fields', {}).values():
            if field_def.get('type') in ['number', 'float', 'decimal']:
                return True
        return False

    def _check_text_fields(self, model_def: Dict) -> bool:
        """检查是否有文本类型字段"""
        for field_def in model_def.get('fields', {}).values():
            if field_def.get('type') == 'text':
                return True
        return False

    def _check_timestamp_fields(self, model_def: Dict) -> bool:
        """检查是否有时间戳字段"""
        for field_def in model_def.get('fields', {}).values():
            if field_def.get('type') in ['datetime', 'timestamp']:
                return True
        return False

    def _check_foreign_keys(self, model_def: Dict) -> bool:
        """检查是否有外键"""
        for field_def in model_def.get('fields', {}).values():
            if field_def.get('foreign_key'):
                return True
        return False

    def _check_foreign_keys_in_fields(self, fields: Dict) -> bool:
        """检查 fields 中是否有外键"""
        for field_def in fields.values():
            if field_def.get('foreign_key'):
                return True
        return False

    def _check_relationships(self, model_def: Dict) -> bool:
        """检查是否有关系定义"""
        return bool(model_def.get('relationships', {}))

    def _load_custom_methods(self, model_name: str, def_list: list) -> dict:
        """
        从 shared/defs/<model_name>_defs.py 加载自定义方法（向后兼容）
        
        Args:
            model_name: 模型名称（如 User）
            def_list: 方法名称列表（如 ['is_vip']）
            
        Returns:
            包含方法源码的字典 {method_name: source_code}
        """
        # 使用默认的目标文件名
        return self._load_custom_methods_from_target(model_name, def_list, f"{model_name.lower()}_defs.py")

    def _load_custom_methods_from_target(self, model_name: str, def_list: list, defs_target: str) -> dict:
        """
        从指定的文件加载自定义方法
        
        Args:
            model_name: 模型名称（如 User）
            def_list: 方法名称列表（如 ['is_vip']）
            defs_target: 目标文件名（相对于 shared/defs/），如 'user_defs.py' 或 'mydef.py'
            
        Returns:
            包含方法源码的字典 {method_name: source_code}
        """
        import importlib.util
        import inspect

        custom_methods = {}
        # 支持绝对路径和相对路径
        if Path(defs_target).is_absolute():
            defs_file = Path(defs_target)
        else:
            defs_file = self.project_root / "shared" / "defs" / defs_target

        if not defs_file.exists():
            print(f"  ⚠ 警告：自定义方法文件不存在：{defs_file}")
            return custom_methods

        try:
            # 动态加载模块
            module_name = Path(defs_target).stem  # 不带 .py 的文件名
            spec = importlib.util.spec_from_file_location(module_name, defs_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # 提取指定的方法
            for method_name in def_list:
                if hasattr(module, method_name):
                    method = getattr(module, method_name)
                    # 获取方法源码
                    try:
                        source = inspect.getsource(method)
                        custom_methods[method_name] = source
                        print(f"  [OK] 加载自定义方法：{model_name}.{method_name} (from {defs_target})")
                    except Exception as e:
                        print(f"  ⚠ 警告：无法获取方法 {method_name} 的源码：{e}")
                else:
                    print(f"  ⚠ 警告：方法 {method_name} 在 {defs_target} 中未找到")

        except Exception as e:
            import traceback
            print(f"  [ERROR] 加载自定义方法失败：{e}")
            print(f"    详细信息：{traceback.format_exc()}")

        return custom_methods

    # ==================== ORM 配置检查方法（从 models[*].orm 读取） ====================

    def _convert_properties_to_fields(self, properties: Dict, model_name: str = None,
                                      all_models: Dict = None, table_prefix: str = '') -> Dict:
        """从 API properties 转换为 SQLAlchemy fields，支持完整配置"""
        # SQLAlchemy 保留字列表
        RESERVED_NAMES = {
            'metadata', 'registry', 'declarative_base', 'Base',
            'query', 'session', 'mapper', 'column_property',
            'composite', 'synonym', 'relationship', 'backref',
            'validate', 'reconstructor', 'declared_attr',
            'hybrid_property', 'hybrid_method', 'AssociationProxy'
        }
        
        fields = {}
        first_integer_field = None  # 用于无 id 且未明确声明自增的主键自动设置递增

        # 先检查是否有名为 id 的字段
        has_id_field = any(k == 'id' for k in properties)

        for prop_name, prop_def in properties.items():
            raw_type = prop_def.get('type', 'string')
            field_type = self._map_property_type_to_sqlalchemy(raw_type)
            
            # 检查是否为保留字，如果是则重命名
            python_field_name = prop_name
            db_column_name = None
            if prop_name.lower() in RESERVED_NAMES:
                # 在字段名前添加前缀以避免冲突
                python_field_name = f"extra_{prop_name}"
                db_column_name = prop_name  # 数据库列名保持原样

            field_info = {
                'type': field_type,
                'description': prop_def.get('description', prop_name),
                'doc': prop_def.get('description', prop_name),
                'python_name': python_field_name,  # Python 属性名
                'db_column': db_column_name,  # 数据库列名（如果需要）
            }

            # 特殊处理：string + date-time 格式 -> datetime
            if raw_type == 'string' and prop_def.get('format') == 'date-time':
                field_info['type'] = 'datetime'

            # 主键处理
            if prop_name == 'id':
                field_info['primary_key'] = True
                field_info['autoincrement'] = True
            elif prop_def.get('primaryKey'):
                field_info['primary_key'] = True
                # 如果没有 id 字段，且该字段是 integer，则尝试自增
                if not has_id_field and field_type == 'integer':
                    if first_integer_field is None:
                        field_info['autoincrement'] = True
                        first_integer_field = prop_name  # 记录第一个
                    else:
                        # 后续的整数主键不再自动递增
                        pass

            # 常规属性
            if prop_def.get('nullable'):
                field_info['nullable'] = True
            if prop_def.get('maxLength'):
                field_info['max_length'] = prop_def['maxLength']
            if 'default' in prop_def:
                field_info['default'] = prop_def['default']
            if prop_def.get('unique'):
                field_info['unique'] = True
            if prop_def.get('index'):
                field_info['index'] = True
            if prop_def.get('sensitive'):
                field_info['sensitive'] = True

            # Decimal 精度
            if raw_type in ('number', 'float', 'decimal'):
                field_info['type'] = 'decimal'  # 统一为 decimal
                field_info['max_digits'] = prop_def.get('maxDigits', 10)
                field_info['decimal_places'] = prop_def.get('decimalPlaces', 2)

            # 外键处理：预解析目标表全名及主键列（默认为 'id'）
            if prop_def.get('foreignKey'):
                fk_model_name = prop_def['foreignKey']
                field_info['foreign_key'] = fk_model_name
                # 查找目标模型配置
                target_model = all_models.get(fk_model_name, {}) if all_models else {}
                target_table = target_model.get('table', self._model_name_to_filename(fk_model_name))
                field_info['fk_table'] = table_prefix + target_table
                # 简单起见，主键列默认为 'id'，如项目中统一规范即可
                field_info['fk_column'] = 'id'
                if model_name and fk_model_name == model_name:
                    field_info['is_self_reference'] = True

            fields[python_field_name] = field_info

        return fields

    def _map_property_type_to_sqlalchemy(self, prop_type: str) -> str:
        """映射 TypeScript/JSON 类型到 SQLAlchemy 类型"""
        type_mapping = {
            'integer': 'integer',
            'bigint': 'bigint',  # 大整数类型
            'number': 'decimal',  # number 类型映射为 decimal，用于 Django 的 DecimalField
            'float': 'decimal',  # float 也映射为 decimal
            'string': 'string',
            'boolean': 'boolean',
            'array': 'string',  # 数组通常存储为 JSON 字符串
            'object': 'text',  # 对象通常存储为 JSON 文本
            'text': 'text',  # 长文本类型
            'datetime': 'datetime',
            'timestamp': 'datetime',
            'date': 'datetime',
        }
        return type_mapping.get(prop_type, 'string')

    def _check_list_fields_from_properties(self, properties: Dict) -> bool:
        """检查是否有列表类型字段（从 properties）"""
        for prop_def in properties.values():
            if prop_def.get('type') == 'array':
                return True
        return False

    def _check_numeric_fields_from_properties(self, properties: Dict) -> bool:
        """检查是否有数值类型字段（从 properties）"""
        for prop_def in properties.values():
            if prop_def.get('type') in ['number', 'integer']:
                return True
        return False

    def _check_decimal_fields_from_properties(self, properties: Dict) -> bool:
        """检查是否有 decimal 类型字段（从 properties）"""
        for prop_def in properties.values():
            # number 和 float 类型都会被映射为 decimal
            if prop_def.get('type') in ['number', 'float', 'decimal']:
                return True
        return False

    def _check_text_fields_from_properties(self, properties: Dict) -> bool:
        """检查是否有文本类型字段（从 properties）"""
        for prop_def in properties.values():
            if prop_def.get('type') == 'string' and prop_def.get('maxLength', 0) > 500:
                return True
        return False

    def _check_timestamp_fields_from_properties(self, properties: Dict) -> bool:
        """检查是否有时间戳字段（从 properties）"""
        for prop_def in properties.values():
            if prop_def.get('format') == 'date-time':
                return True
        return False

    def _scan_association_tables(self) -> Dict[str, list]:
        """
        自动扫描 shared/models 目录下的关联表（Table 对象）
        
        Returns:
            {'imports': [import_statements], 'exports': [export_names]}
        """
        models_dir = self.project_root / "shared" / "models"
        imports = []
        exports = []

        if not models_dir.exists():
            return {'imports': imports, 'exports': exports}

        # 扫描所有 Python 文件
        for py_file in models_dir.glob("*.py"):
            if py_file.name.startswith('_') or py_file.name == '__init__.py':
                continue

            # 读取文件内容，查找 Table 对象定义
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 使用正则表达式查找 Table 对象定义
                # 匹配模式：table_name = Table(
                import re
                pattern = r'^(\w+)\s*=\s*Table\('
                matches = re.findall(pattern, content, re.MULTILINE)

                if matches:
                    module_name = py_file.stem  # 不带 .py 的文件名
                    for table_name in matches:
                        imports.append(f"from .{module_name} import {table_name}")
                        exports.append(table_name)
                        print(f"  [OK] 检测到关联表: {table_name} (from {module_name}.py)")
            except Exception as e:
                print(f"  [WARN] 扫描 {py_file.name} 失败: {e}")

        return {'imports': imports, 'exports': exports}

    def _update_shared_models_init_from_orm(self, orm_models_config: Dict):
        """更新 shared/models/__init__.py文件（从 orm 配置）"""
        init_path = self.project_root / "shared" / "models" / "__init__.py"

        # 生成导入语句
        imports = []
        all_exports = ['Base']

        for model_name, model_def in orm_models_config.items():
            filename = self._model_name_to_filename(model_name)
            # 每个模型只有一个类名
            class_names = [model_name]

            imports.append(f"from .{filename} import {', '.join(class_names)}")
            all_exports.extend(class_names)

        # 自动扫描并添加关联表（Table 对象）的导入
        association_imports = self._scan_association_tables()
        imports.extend(association_imports['imports'])
        all_exports.extend(association_imports['exports'])

        # 读取现有文件，保留非自动生成的部分
        if init_path.exists():
            with open(init_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 保留 Base 定义和手动维护的导入（删除所有自动生成部分）
            lines = content.split('\n')
            new_lines = []
            in_generated_section = False
            skip_next_empty = False

            for line in lines:
                # 检测自动生成部分的开始
                if '由 routes.yaml 自动生成' in line or 'GENERATED SECTION' in line or '自动生成的导入' in line:
                    in_generated_section = True
                    continue
                if in_generated_section and (
                        '# ===' in line or '# ================================================================='):
                    skip_next_empty = True
                    continue
                if skip_next_empty and (line.strip() == '' or line.startswith('#')):
                    continue
                skip_next_empty = False

                # 如果不在自动生成部分，保留该行
                if not in_generated_section:
                    # 但跳过旧的 from . 导入（这些会被重新生成）
                    if not (line.startswith('from .') or (line.startswith('__all__') and '=' in line)):
                        new_lines.append(line)

                # 遇到空的 __all__ 定义也跳过
                if line.strip() == '__all__ = [':
                    in_generated_section = True
                    continue
                if in_generated_section and line.strip() == ']':
                    in_generated_section = False
                    continue

            # 重新构建文件基础内容
            content = '\n'.join(new_lines)
            # 清理多余的空行
            while content.startswith('\n'):
                content = content[1:]
        else:
            content = "from sqlalchemy.orm import declarative_base\n\nBase = declarative_base()\n"

        # 添加新的导入
        import_section = "\n".join(imports)
        all_section = "\n__all__ = [\n    '" + "',\n    '".join(all_exports) + "'\n]"

        new_content = f"""{content}
{import_section}

# ==================== 自动生成的导入 - 由 routes.yaml 管理 ====================
# 此部分由脚本自动生成 - 请勿手动修改
{all_section}
# ============================================================================
"""

        self._write_file(init_path, new_content)

    def _update_shared_models_init(self, shared_models_config: Dict):
        """更新 shared/models/__init__.py 文件"""
        init_path = self.project_root / "shared" / "models" / "__init__.py"

        # 生成导入语句
        imports = []
        all_exports = ['Base']

        for model_name, model_def in shared_models_config.items():
            filename = self._model_name_to_filename(model_name)
            # 从 model_def 中获取类名，可能有多个类
            class_names = [model_name]
            if 'additional_classes' in model_def:
                class_names.extend(model_def['additional_classes'])

            imports.append(f"from .{filename} import {', '.join(class_names)}")
            all_exports.extend(class_names)

        # 读取现有文件，保留非自动生成的部分
        if init_path.exists():
            with open(init_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 保留 Base 定义和手动维护的导入（删除所有自动生成部分）
            lines = content.split('\n')
            new_lines = []
            in_generated_section = False
            skip_next_empty = False

            for line in lines:
                # 检测自动生成部分的开始
                if '由 routes.yaml 自动生成' in line or 'GENERATED SECTION' in line or '自动生成的导入' in line:
                    in_generated_section = True
                    continue
                if in_generated_section and (
                        '# ===' in line or '# ================================================================='):
                    skip_next_empty = True
                    continue
                if skip_next_empty and (line.strip() == '' or line.startswith('#')):
                    continue
                skip_next_empty = False

                # 如果不在自动生成部分，保留该行
                if not in_generated_section:
                    # 但跳过旧的 from . 导入（这些会被重新生成）
                    if not (line.startswith('from .') or (line.startswith('__all__') and '=' in line)):
                        new_lines.append(line)

                # 遇到空的 __all__ 定义也跳过
                if line.strip() == '__all__ = [':
                    in_generated_section = True
                    continue
                if in_generated_section and line.strip() == ']':
                    in_generated_section = False
                    continue

            # 重新构建文件基础内容
            content = '\n'.join(new_lines)
            # 清理多余的空行
            while content.startswith('\n'):
                content = content[1:]
        else:
            content = "from sqlalchemy.orm import declarative_base\n\nBase = declarative_base()\n"

        # 添加新的导入
        import_section = "\n".join(imports)
        all_section = "\n__all__ = [\n    '" + "',\n    '".join(all_exports) + "'\n]"

        new_content = f"""{content}
{import_section}

# ==================== 自动生成的导入 - 由 routes.yaml 管理 ====================
# 此部分由脚本自动生成 - 请勿手动修改
{all_section}
# ============================================================================
"""

        self._write_file(init_path, new_content)

    def _render_template(self, template_name: str, context: Dict) -> str:
        """渲染 Jinja2 模板"""
        try:
            template = self.jinja_env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound:
            print(f"  ⚠ 模板未找到：{template_name}")
            return ""

    def _write_file(self, file_path: Path, content: str):
        """写入文件，确保编码为 UTF-8"""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"    已写入：{file_path}")

    def _format_generated_files(self):
        """使用 black 格式化生成的 Python 文件"""
        print("\n正在格式化生成的文件...")

        try:
            import subprocess

            # 需要格式化的文件列表
            files_to_format = [
                self.project_root / "apps" / "generated" / "auto_orm.py",
                self._get_output_path('django_ninja', 'router_file'),
                self._get_output_path('fastapi', 'router_file'),
            ]

            # 添加 SQLAlchemy 模型文件
            sqlalchemy_models_dir = self.project_root / "shared" / "models"
            if sqlalchemy_models_dir.exists():
                for py_file in sqlalchemy_models_dir.glob("*.py"):
                    if py_file.name != "__init__.py":
                        files_to_format.append(py_file)

            # 过滤掉 None 值
            files_to_format = [f for f in files_to_format if f is not None]

            if not files_to_format:
                print("  ⚠ 没有需要格式化的文件")
                return

            # 检查 black 是否可用
            result = subprocess.run(
                ['black', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                print("  ⚠ black 未安装，跳过格式化")
                print("  提示：运行 'pip install black' 安装 black 格式化器")
                return

            # 格式化每个文件
            for file_path in files_to_format:
                if file_path.exists():
                    print(f"  格式化：{file_path}")
                    subprocess.run(
                        ['black', '-q', str(file_path)],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                else:
                    print(f"  ⚠ 文件不存在，跳过：{file_path}")

            print("  ✓ 格式化完成")

        except subprocess.TimeoutExpired:
            print("  ⚠ 格式化超时，跳过")
        except FileNotFoundError:
            print("  ⚠ black 未找到，跳过格式化")
        except Exception as e:
            print(f"  ⚠ 格式化失败：{e}")

    def sync_to_django(self, app_name: str = None):
        """将 SQLAlchemy 模型同步为 Django 模型"""
        print("🔄 开始同步 SQLAlchemy 模型到 Django...\n")

        # 1. 先生成 Mixins
        print("步骤 1: 生成 Django Mixin...")
        self._generate_orm_mixins()

        # 2. 如果有指定 app，生成该 app 的 models.py
        if app_name:
            print(f"\n步骤 2: 为 app '{app_name}' 生成 models.py...")
            # 待实现：Django 模型生成功能
            print("  ⚠️  Django 模型生成功能尚未实现")
            print("  提示：请手动在 apps/{app_name}/models.py 中定义 Django 模型")
        else:
            print("\nℹ️  未指定 app 名称，仅生成 Mixin")

        print("\n✅ 同步完成！")

    def _optimize_sqlalchemy_imports(self):
        """优化 SQLAlchemy 模型文件的导入语句"""
        print("\n正在优化 SQLAlchemy 模型的导入...")

        try:
            import subprocess

            # 检查 isort 是否可用
            result = subprocess.run(
                ['isort', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                print("  ⚠ isort 未安装，跳过导入优化")
                print("  提示：运行 'pip install isort' 安装 isort")
                return

            # 优化 shared/models 目录下的所有 Python 文件
            sqlalchemy_models_dir = self.project_root / "shared" / "models"
            if not sqlalchemy_models_dir.exists():
                print("  ⚠ shared/models 目录不存在")
                return

            py_files = list(sqlalchemy_models_dir.glob("*.py"))
            if not py_files:
                print("  ⚠ 没有需要优化导入的文件")
                return

            # 使用 isort 优化导入
            for file_path in py_files:
                print(f"  优化导入：{file_path}")
                subprocess.run(
                    ['isort', '-q', str(file_path)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

            print("  ✓ 导入优化完成")

        except subprocess.TimeoutExpired:
            print("  ⚠ 优化导入超时，跳过")
        except FileNotFoundError:
            print("  ⚠ isort 未找到，跳过导入优化")
        except Exception as e:
            print(f"  ⚠ 优化导入失败：{e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='路由代码生成器')
    parser.add_argument('--config', type=str, default=None, help='routes.yaml 配置文件路径')
    parser.add_argument('command', nargs='?', choices=['generate-all', 'sync-to-django'], default='generate-all',
                        help='要执行的命令（默认：generate-all）')
    parser.add_argument('--app', type=str, help='app 名称（用于 sync-to-django 命令）')

    args = parser.parse_args()

    try:
        generator = RouteGenerator(config_path=args.config)

        if args.command == 'sync-to-django':
            generator.sync_to_django(app_name=args.app)
        else:  # generate-all
            generator.generate_all()

    except FileNotFoundError as e:
        print(f"错误：{e}")
        sys.exit(1)
    except Exception as e:
        print(f"生成失败：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
