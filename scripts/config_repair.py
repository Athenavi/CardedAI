#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastBlog 配置修复工具
用于备份、还原、修复和生成 routes.yaml 和 models.yaml 配置文件

使用方法:
    python scripts/config_repair.py --help
    
子命令:
    - backup: 备份当前配置文件
    - restore: 从备份还原配置文件
    - repair: 尝试修复损坏的配置文件
    - generate: 生成最小的可执行配置
    - reverse: 从现有模型逆向生成配置
    - interactive: 终端交互式配置
    - add-orm: 为指定的模型添加 orm: true 标记
    - remove-orm: 移除模型的 orm 标记
    - list-orm: 列出所有有 orm 标记的模型
    - sync-shared: 根据 shared/models 目录自动同步 orm 标记
"""

import argparse
import ast
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml

# 项目根目录
project_root = Path(__file__).parent.parent
routes_file = project_root / 'config' / 'routes.yaml'
models_file = project_root / 'config' / 'models.yaml'
backup_dir = project_root / 'backups' / 'routes'


class ConfigRepairTool:
    """配置修复工具"""

    def __init__(self):
        # 确保备份目录存在
        backup_dir.mkdir(parents=True, exist_ok=True)

        # 加载配置文件
        self.data = {}
        self.models = {}
        self.extra_models_data = {}
        self._load_config()

    def _load_config(self):
        """加载 routes.yaml 和 models.yaml 配置"""
        # 加载 routes.yaml
        if routes_file.exists():
            try:
                with open(routes_file, 'r', encoding='utf-8') as f:
                    self.data = yaml.safe_load(f) or {}
                self.models = self.data.get('models', {})
            except Exception as e:
                print(f"⚠ 加载 routes.yaml 失败：{e}")
                self.data = {}
                self.models = {}
        else:
            print(f"⚠ routes.yaml 不存在，将使用空配置")
            self.data = {'endpoints': [], 'models': {}}
            self.models = {}

        # 加载 models.yaml（如果存在）
        if models_file.exists():
            try:
                with open(models_file, 'r', encoding='utf-8') as f:
                    self.extra_models_data = yaml.safe_load(f) or {}
                # 合并 extra_models 到 self.models
                extra_models = self.extra_models_data.get('models', {})
                self.models.update(extra_models)
            except Exception as e:
                print(f"⚠ 加载 models.yaml 失败：{e}")
                self.extra_models_data = {}
        else:
            self.extra_models_data = {}

    def backup(self, name: Optional[str] = None, include_models: bool = True):
        """
        备份当前配置文件
        
        Args:
            name: 备份名称，默认为时间戳
            include_models: 是否包含 models.yaml
        """
        files_to_backup = []

        if routes_file.exists():
            files_to_backup.append(('routes', routes_file))
        else:
            print(f"⚠ routes.yaml 不存在：{routes_file}")

        if include_models and models_file.exists():
            files_to_backup.append(('models', models_file))
        elif include_models:
            print(f"⚠ models.yaml 不存在：{models_file}")

        if not files_to_backup:
            print("❌ 没有文件需要备份")
            return False

        if not name:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            name = f'config_backup_{timestamp}'

        backup_subdir = backup_dir / name
        backup_subdir.mkdir(parents=True, exist_ok=True)

        try:
            metadata = {
                'backup_name': name,
                'backup_time': datetime.now().isoformat(),
                'files': {}
            }

            for file_type, file_path in files_to_backup:
                backup_file = backup_subdir / f'{file_type}.yaml'
                shutil.copy2(file_path, backup_file)
                print(f"✓ 已备份：{file_path.name} -> {backup_file}")

                metadata['files'][file_type] = {
                    'original': str(file_path),
                    'backup': str(backup_file),
                    'size': file_path.stat().st_size
                }

            # 保存元数据
            with open(backup_subdir / 'metadata.json', 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            print(f"\n✓ 备份完成：{backup_subdir}")
            print(f"✓ 元数据已保存")
            return True

        except Exception as e:
            print(f"❌ 备份失败：{e}")
            return False

    def list_backups(self):
        """列出所有可用的备份"""
        backups = [d for d in backup_dir.iterdir() if d.is_dir()]

        if not backups:
            print("ℹ️  没有找到备份文件")
            return []

        print(f"\n共有 {len(backups)} 个备份:\n")

        backup_list = []
        for backup_dir_item in sorted(backups, reverse=True):
            name = backup_dir_item.name
            meta_file = backup_dir_item / 'metadata.json'

            info = {'name': name, 'time': '未知', 'files': []}

            if meta_file.exists():
                with open(meta_file, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                    info['time'] = meta.get('backup_time', '未知')
                    info['files'] = list(meta.get('files', {}).keys())
            else:
                # 旧格式的备份
                yaml_files = list(backup_dir_item.glob('*.yaml'))
                info['files'] = [f.stem for f in yaml_files]

            backup_list.append(info)
            print(f"  📁 {name}")
            print(f"     时间：{info['time']}")
            print(f"     文件：{', '.join(info['files'])}")
            print()

        return backup_list

    def restore(self, backup_name: str, restore_routes: bool = True, restore_models: bool = True):
        """
        从备份还原配置文件
        
        Args:
            backup_name: 备份名称（不含扩展名）
            restore_routes: 是否还原 routes.yaml
            restore_models: 是否还原 models.yaml
        """
        backup_subdir = backup_dir / backup_name

        if not backup_subdir.exists():
            print(f"❌ 备份目录不存在：{backup_subdir}")
            print("\n可用的备份:")
            self.list_backups()
            return False

        try:
            # 先自动备份当前文件
            if routes_file.exists() or models_file.exists():
                auto_backup_name = f'auto_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
                self.backup(auto_backup_name)
                print()

            restored_count = 0

            # 还原 routes.yaml
            if restore_routes:
                routes_backup = backup_subdir / 'routes.yaml'
                if routes_backup.exists():
                    shutil.copy2(routes_backup, routes_file)
                    print(f"✓ 已还原 routes.yaml")
                    restored_count += 1
                else:
                    print(f"⚠ 备份中没有 routes.yaml")

            # 还原 models.yaml
            if restore_models:
                models_backup = backup_subdir / 'models.yaml'
                if models_backup.exists():
                    shutil.copy2(models_backup, models_file)
                    print(f"✓ 已还原 models.yaml")
                    restored_count += 1
                else:
                    print(f"⚠ 备份中没有 models.yaml")

            if restored_count > 0:
                print(f"\n✓ 成功还原 {restored_count} 个配置文件")
            else:
                print(f"\n⚠ 没有还原任何文件")

            return restored_count > 0

        except Exception as e:
            print(f"❌ 还原失败：{e}")
            return False

    def repair(self, file_type: str = 'all'):
        """
        尝试修复损坏的配置文件
        
        Args:
            file_type: 'routes', 'models', 或 'all'
        
        功能:
        - 修复 YAML 格式错误
        - 移除无效的 Unicode 字符
        - 修复缩进问题
        - 验证必需的配置项
        """
        files_to_check = []

        if file_type in ['routes', 'all'] and routes_file.exists():
            files_to_check.append(('routes.yaml', routes_file))
        if file_type in ['models', 'all'] and models_file.exists():
            files_to_check.append(('models.yaml', models_file))

        if not files_to_check:
            print(f"❌ 没有找到需要检查的文件")
            return False

        all_success = True

        for file_name, file_path in files_to_check:
            print(f"\n正在检查 {file_name}...")

            try:
                # 读取原始内容
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 尝试解析 YAML
                try:
                    data = yaml.safe_load(content)
                    print(f"✓ {file_name} YAML 格式正确")

                    # 验证必需的配置项
                    if file_name == 'routes.yaml':
                        required_keys = ['endpoints', 'models']
                        missing_keys = [key for key in required_keys if key not in data]

                        if missing_keys:
                            print(f"⚠ 缺少必需的顶级配置项：{missing_keys}")
                        else:
                            print(f"✓ 必需的配置项完整")

                        # 统计信息
                        print(f"\n📊 配置统计:")
                        print(f"   - 端点数量：{len(data.get('endpoints', []))}")
                        print(f"   - 模型数量：{len(data.get('models', {}))}")

                        if 'generation' in data:
                            print(f"   - 生成配置：已配置")

                    elif file_name == 'models.yaml':
                        if 'models' in data:
                            print(f"✓ 模型配置完整")
                            print(f"\n📊 模型统计:")
                            print(f"   - 模型数量：{len(data.get('models', {}))}")

                            orm_models = [k for k, v in data['models'].items() if v.get('orm') is True]
                            if orm_models:
                                print(f"   - ORM 模型：{len(orm_models)}")
                        else:
                            print(f"⚠ 缺少 models 配置项")

                    all_success = all_success and True

                except yaml.YAMLError as e:
                    print(f"❌ {file_name} YAML 格式错误：{e}")
                    print("\n尝试自动修复...")

                    if self._repair_yaml_content(content, file_path):
                        print(f"✓ {file_name} 自动修复成功")
                    else:
                        print(f"❌ {file_name} 自动修复失败")
                        all_success = False

            except Exception as e:
                print(f"❌ {file_name} 检查失败：{e}")
                all_success = False

        return all_success

    def _repair_yaml_content(self, content: str, file_path: Path) -> bool:
        """修复 YAML 内容"""
        # 创建修复后的文件
        repaired_file = file_path.with_suffix(file_path.suffix + '.repaired')

        # 简单的修复策略：逐行处理
        lines = content.split('\n')
        repaired_lines = []

        for i, line in enumerate(lines, 1):
            # 移除不可打印的字符
            cleaned_line = ''.join(char for char in line if char.isprintable() or char in '\t')
            repaired_lines.append(cleaned_line)

        repaired_content = '\n'.join(repaired_lines)

        # 再次尝试解析
        try:
            yaml.safe_load(repaired_content)
            print(f"✓ 自动修复成功")

            # 保存修复后的文件
            with open(repaired_file, 'w', encoding='utf-8') as f:
                f.write(repaired_content)

            print(f"✓ 修复后的文件已保存：{repaired_file}")
            print(f"\n请检查修复后的文件，确认无误后可以手动替换原文件")
            return True

        except yaml.YAMLError as e2:
            print(f"❌ 自动修复失败：{e2}")
            return False

    def interactive(self):
        """终端交互式配置"""
        print("\n" + "=" * 70)
        print("🛠️  FastBlog 配置修复工具 - 交互模式")
        print("=" * 70)

        while True:
            print("\n请选择操作:")
            print("  1. 📦 备份配置文件")
            print("  2. 📥 还原配置文件")
            print("  3. 🔧 修复配置文件")
            print("  4. 📋 查看配置信息")
            print("  5. 📊 查看备份列表")
            print("  6. 🚪 退出")

            choice = input("\n请输入选项 (1-6): ").strip()

            if choice == '1':
                name = input("请输入备份名称（直接回车使用时间戳）: ").strip()
                self.backup(name if name else None)

            elif choice == '2':
                print("\n可用的备份:")
                backups = self.list_backups()
                if backups:
                    backup_name = input("\n请输入要还原的备份名称: ").strip()

                    # 询问还原哪些文件
                    restore_routes = input("还原 routes.yaml? (Y/n): ").strip().lower() != 'n'
                    restore_models = input("还原 models.yaml? (Y/n): ").strip().lower() != 'n'

                    if restore_routes or restore_models:
                        self.restore(backup_name, restore_routes, restore_models)
                    else:
                        print("⚠ 没有选择还原任何文件")
                else:
                    print("\n❌ 没有找到可用的备份")

            elif choice == '3':
                print("\n请选择要修复的文件:")
                print("  a. 全部文件 (routes.yaml + models.yaml)")
                print("  b. 仅 routes.yaml")
                print("  c. 仅 models.yaml")
                file_choice = input("请选择 (a/b/c): ").strip().lower()

                if file_choice == 'a':
                    self.repair('all')
                elif file_choice == 'b':
                    self.repair('routes')
                elif file_choice == 'c':
                    self.repair('models')
                else:
                    print("⚠ 无效的选择")

            elif choice == '4':
                print("\n📊 当前配置信息:")

                # 检查 routes.yaml
                if routes_file.exists():
                    try:
                        with open(routes_file, 'r', encoding='utf-8') as f:
                            data = yaml.safe_load(f)
                        print(f"\n✅ routes.yaml")
                        print(f"   - 端点数量：{len(data.get('endpoints', []))}")
                        print(f"   - 模型数量：{len(data.get('models', {}))}")
                    except Exception as e:
                        print(f"\n❌ routes.yaml 读取失败：{e}")
                else:
                    print(f"\n❌ routes.yaml 不存在")

                # 检查 models.yaml
                if models_file.exists():
                    try:
                        with open(models_file, 'r', encoding='utf-8') as f:
                            data = yaml.safe_load(f)
                        print(f"\n✅ models.yaml")
                        print(f"   - 模型数量：{len(data.get('models', {}))}")
                        orm_models = [k for k, v in data['models'].items() if v.get('orm') is True]
                        if orm_models:
                            print(f"   - ORM 模型：{len(orm_models)}")
                    except Exception as e:
                        print(f"\n❌ models.yaml 读取失败：{e}")
                else:
                    print(f"\n❌ models.yaml 不存在")

            elif choice == '5':
                self.list_backups()

            elif choice == '6':
                print("\n👋 再见！")
                break

            else:
                print("\n❌ 无效的选项，请输入 1-6")

    def generate_minimal(self, include_models: bool = True):
        print("正在生成最小可执行配置...")

        minimal_config = {
            'endpoints': [],
            'models': {
                'ApiResponse': {
                    'description': '通用 API 响应',
                    'properties': {
                        'code': {'type': 'integer', 'description': '状态码'},
                        'message': {'type': 'string', 'description': '消息'},
                        'data': {'type': 'object', 'nullable': True, 'description': '响应数据'},
                    }
                },
                'PaginationInfo': {
                    'description': '分页信息',
                    'properties': {
                        'page': {'type': 'integer', 'description': '当前页码'},
                        'per_page': {'type': 'integer', 'description': '每页数量'},
                        'total': {'type': 'integer', 'description': '总数'},
                    }
                }
            },
            'generation': {
                'django_ninja': {
                    'output_dir': 'apps/generated',
                    'router_file': 'generated_router.py',
                    'models_file': 'auto_orm.py',
                },
                'fastapi': {
                    'output_dir': 'src/api/v1/generated',
                    'router_file': 'generated_router.py',
                },
                'typescript': {
                    'output_dir': 'frontend-next/types/generated',
                    'types_file': 'api-types.ts',
                    'client_file': 'api-client.ts',
                }
            }
        }

        # 转换为列表格式以保留注释
        output_lines = [
            '# ============================================================================',
            '# FastBlog 最小化配置文件',
            '# 由 config_repair.py 自动生成',
            '# ============================================================================',
            '',
            '# 注意：这是一个最小化的配置文件，仅包含基本功能',
            '# 警告：请在修改前备份原文件',
            '',
        ]

        # 使用 yaml 库生成规范的 YAML 内容
        yaml_content = yaml.dump(
            {k: v for k, v in minimal_config.items() if not k.startswith('#') and k != ''},
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
            indent=2
        )

        output_lines.append(yaml_content)

        # 写入文件
        minimal_file = project_root / 'config' / 'routes.minimal.yaml'

        with open(minimal_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines))

        print(f"✓ 已生成最小配置文件：{minimal_file}")
        print(f"\n下一步:")
        print(f"  1. 检查生成的配置文件")
        print(f"  2. 根据需要添加更多端点和模型")
        print(f"  3. 将文件重命名为 routes.yaml 或复制内容到 routes.yaml")

        return True

    def reverse_from_models(self):
        """
        从现有的 shared/models 逆向生成 routes.yaml
        
        分析 shared/models 目录下的 SQLAlchemy 模型，
        自动生成对应的 routes.yaml 配置
        """
        print("正在从 shared/models 逆向生成配置...")

        models_dir = project_root / 'shared' / 'models'

        if not models_dir.exists():
            print(f"❌ shared/models 目录不存在：{models_dir}")
            return False

        # 收集所有模型文件
        model_files = [f for f in models_dir.glob('*.py') if f.name != '__init__.py']

        if not model_files:
            print("ℹ️  shared/models 目录下没有找到模型文件")
            return False

        print(f"发现 {len(model_files)} 个模型文件")

        # 逆向生成的配置结构
        reversed_config = {
            'endpoints': [],  # 端点需要手动配置
            'models': {},
            'generation': {
                'typescript': {
                    'output_dir': 'frontend-next/types/generated',
                    'types_file': 'api-types.ts',
                    'client_file': 'api-client.ts',
                }
            }
        }

        # 解析每个模型文件
        for model_file in model_files:
            print(f"\n分析：{model_file.name}")

            try:
                # 读取模型文件内容
                with open(model_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 简单的 AST 解析
                import ast
                tree = ast.parse(content)

                # 提取类定义
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # 跳过 Base 和其他非模型类
                        if node.name == 'Base':
                            continue

                        print(f"  找到模型类：{node.name}")

                        # 提取属性
                        properties = {}

                        # 查找类体中的赋值语句（字段定义）
                        for item in node.body:
                            if isinstance(item, ast.AnnAssign):
                                # 有类型注解的赋值
                                target = self._get_target_name(item.target)
                                if target:
                                    annotation = self._get_annotation_type(item.annotation)
                                    properties[target] = {
                                        'type': annotation,
                                        'description': f'{target} 字段'
                                    }

                        # 添加到配置
                        if properties:
                            reversed_config['models'][node.name] = {
                                'description': f'{node.name} 模型',
                                'properties': properties,
                                'orm': True  # 标记为需要生成 ORM
                            }

            except Exception as e:
                print(f"  ⚠ 解析失败：{e}")
                continue

        # 保存逆向生成的配置
        reversed_file = project_root / 'config' / 'routes.reversed.yaml'

        with open(reversed_file, 'w', encoding='utf-8') as f:
            yaml.dump(
                reversed_config,
                f,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )

        print(f"\n✓ 已生成逆向配置文件：{reversed_file}")
        print(f"\n下一步:")
        print(f"  1. 检查生成的配置文件")
        print(f"  2. 手动添加 endpoints 配置（路由端点）")
        print(f"  3. 完善模型的 description 和 properties")
        print(f"  4. 确认无误后重命名为 routes.yaml")

        return True

    def _get_target_name(self, target) -> Optional[str]:
        """获取赋值目标的名称"""
        if isinstance(target, ast.Name):
            return target.id
        return None

    def _get_annotation_type(self, annotation) -> str:
        """获取类型注解的字符串表示"""
        if isinstance(annotation, ast.Name):
            return annotation.id.lower()
        elif isinstance(annotation, ast.Constant):
            return str(annotation.value).lower()
        elif isinstance(annotation, ast.Subscript):
            # 处理 List[int], Optional[str] 等
            if isinstance(annotation.value, ast.Name):
                return annotation.value.id.lower()
        return 'any'

    def _snake_to_camel(self, name: str) -> str:
        """将下划线命名转换为驼峰命名"""
        parts = name.split('_')
        return ''.join(word.capitalize() for word in parts)

    def add_orm(self, model_names: list):
        """为指定的模型添加 orm: true 标记"""
        updated_count = 0
        for model_name in model_names:
            if model_name not in self.models:
                print(f"⚠ 模型 {model_name} 不存在")
                continue

            model_def = self.models[model_name]
            if model_def.get('orm') is True:
                print(f"- {model_name} 已经有 orm: true")
            else:
                model_def['orm'] = True
                print(f"✓ 为 {model_name} 添加了 orm: true")
                updated_count += 1

        if updated_count > 0:
            self._save()
            print(f"\n完成！共更新 {updated_count} 个模型")

    def remove_orm(self, model_names: list):
        """移除指定模型的 orm 标记"""
        updated_count = 0
        for model_name in model_names:
            if model_name not in self.models:
                print(f"⚠ 模型 {model_name} 不存在")
                continue

            model_def = self.models[model_name]
            if 'orm' in model_def:
                del model_def['orm']
                print(f"✓ 移除了 {model_name} 的 orm 标记")
                updated_count += 1
            else:
                print(f"- {model_name} 没有 orm 标记")

        if updated_count > 0:
            self._save()
            print(f"\n完成！共更新 {updated_count} 个模型")

    def list_orm(self):
        """列出所有有 orm 标记的模型"""
        models_with_orm = [k for k, v in self.models.items() if v.get('orm') is True]

        if not models_with_orm:
            print("ℹ️  没有模型有 orm 标记")
            return

        print(f"\n共有 {len(models_with_orm)} 个模型有 orm: true 标记:\n")

        # 按首字母分组
        groups = {}
        for model in sorted(models_with_orm):
            first_letter = model[0].upper()
            if first_letter not in groups:
                groups[first_letter] = []
            groups[first_letter].append(model)

        for letter in sorted(groups.keys()):
            print(f"\n{letter}:")
            for model in groups[letter]:
                print(f"  - {model}")

    def sync_shared(self):
        """根据 shared/models 目录自动同步 orm 标记"""
        shared_models_dir = project_root / 'shared' / 'models'

        if not shared_models_dir.exists():
            print(f"❌ shared/models 目录不存在")
            return

        # 获取 shared/models 目录下的所有模型文件
        model_files = [f.stem for f in shared_models_dir.glob('*.py') if f.name != '__init__.py']
        print(f"发现 shared/models 中的模型文件：{model_files}\n")

        # 特殊映射规则（针对特定的模型）
        special_mapping = {
            'misc': ['SearchHistory', 'PageView', 'UserActivity'],
            'system': ['SystemSettings', 'Menus', 'MenuItems', 'Pages'],
            'upload': ['UploadTask', 'UploadChunk'],
            'vip': ['VIPPlan', 'VIPSubscription', 'VIPFeature'],
            'comment': ['Comment'],
            'article': ['Article', 'ArticleAuthor', 'ArticleContent', 'ArticleI18n', 'ArticleLike'],
            'category': ['Category', 'CategorySubscription'],
            'media': ['Media', 'FileHash'],
            'user': ['User', 'CustomField', 'EmailSubscription'],
            'notification': ['Notification'],
            'role': [],  # role.py 是空的，已弃用
        }

        # 收集需要添加 orm: true 的模型名称
        models_to_update = set()
        for model_file in model_files:
            if model_file in special_mapping:
                possible_names = special_mapping[model_file]
            else:
                # 默认使用文件名转换
                camel_name = self._snake_to_camel(model_file)
                possible_names = [camel_name, camel_name + 's']

            # 检查 routes.yaml 中是否存在这些模型
            for name in possible_names:
                if name in self.models:
                    models_to_update.add(name)
                    print(f"✓ 找到匹配的模型：{model_file} -> {name}")

        print(f"\n需要更新 orm 标记的模型：{sorted(models_to_update)}")

        # 为这些模型添加 orm: true
        updated_count = 0
        for model_name in sorted(models_to_update):
            model_def = self.models[model_name]
            if 'orm' not in model_def:
                model_def['orm'] = True
                print(f"✓ 为 {model_name} 添加了 orm: true")
                updated_count += 1
            elif model_def.get('orm') is True:
                print(f"- {model_name} 已经有 orm: true")
            else:
                print(f"- {model_name} 已有其他 orm 配置")

        if updated_count > 0:
            self._save()
            print(f"\n完成！共更新 {updated_count} 个模型")
            print(f"已更新的模型列表：{sorted(models_to_update)}")
        else:
            print("\nℹ️  所有模型已经是最新的")

    def _save(self):
        """保存 routes.yaml 和 models.yaml"""
        # 保存到 routes.yaml
        with open(routes_file, 'w', encoding='utf-8') as f:
            yaml.dump(self.data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        print("✓ 已保存到 routes.yaml")

        # 保存到 models.yaml（如果有修改）
        if self.extra_models_data:
            with open(self.models_config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.extra_models_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
            print("✓ 已保存到 models.yaml")


def main():
    parser = argparse.ArgumentParser(description='FastBlog 配置修复工具',
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog="""
示例:
  python scripts/config_repair.py interactive          # 交互模式
  python scripts/config_repair.py backup               # 备份配置文件
  python scripts/config_repair.py restore --list       # 列出所有备份
  python scripts/config_repair.py repair               # 修复配置文件
  python scripts/config_repair.py generate             # 生成最小配置
""")
    subparsers = parser.add_subparsers(dest='command', help='子命令')

    # backup 命令
    backup_parser = subparsers.add_parser('backup', help='备份当前配置文件')
    backup_parser.add_argument('--name', type=str, help='备份名称（默认为时间戳）')
    backup_parser.add_argument('--no-models', action='store_true', help='不备份 models.yaml')

    # restore 命令
    restore_parser = subparsers.add_parser('restore', help='从备份还原配置文件')
    restore_parser.add_argument('backup_name', nargs='?', default=None, help='备份名称')
    restore_parser.add_argument('--list', action='store_true', help='列出所有备份')
    restore_parser.add_argument('--routes-only', action='store_true', help='仅还原 routes.yaml')
    restore_parser.add_argument('--models-only', action='store_true', help='仅还原 models.yaml')

    # repair 命令
    repair_parser = subparsers.add_parser('repair', help='修复配置文件')
    repair_parser.add_argument('--file', choices=['all', 'routes', 'models'], default='all',
                               help='要修复的文件 (默认：all)')

    # generate 命令
    generate_parser = subparsers.add_parser('generate', help='生成最小可执行配置')
    generate_parser.add_argument('--no-models', action='store_true', help='不生成 models.yaml')

    # reverse 命令
    reverse_parser = subparsers.add_parser('reverse', help='从现有模型逆向生成配置')
    reverse_parser.add_argument('--source', choices=['models', 'database'], default='models',
                                help='逆向来源（models: 从 shared/models, database: 从数据库）')

    # interactive 命令
    interactive_parser = subparsers.add_parser('interactive', help='终端交互式配置')
    interactive_parser.add_argument('-i', '--info', action='store_true', help='直接显示配置信息')

    # add-orm 命令
    add_orm_parser = subparsers.add_parser('add-orm', help='为指定的模型添加 orm: true 标记')
    add_orm_parser.add_argument('models', nargs='+', help='模型名称列表')

    # remove-orm 命令
    remove_orm_parser = subparsers.add_parser('remove-orm', help='移除模型的 orm 标记')
    remove_orm_parser.add_argument('models', nargs='+', help='模型名称列表')

    # list-orm 命令
    list_orm_parser = subparsers.add_parser('list-orm', help='列出所有有 orm 标记的模型')

    # sync-shared 命令
    sync_shared_parser = subparsers.add_parser('sync-shared', help='根据 shared/models 目录自动同步 orm 标记')

    args = parser.parse_args()

    if not args.command:
        print("💡 提示：使用 'python scripts/config_repair.py interactive' 进入交互模式")
        print("   或 'python scripts/config_repair.py --help' 查看帮助\n")
        parser.print_help()
        sys.exit(1)

    tool = ConfigRepairTool()

    if args.command == 'backup':
        tool.backup(args.name, include_models=not args.no_models)
    elif args.command == 'restore':
        if args.list or not args.backup_name:
            tool.list_backups()
        else:
            restore_routes = not args.models_only
            restore_models = not args.routes_only
            tool.restore(args.backup_name, restore_routes, restore_models)
    elif args.command == 'repair':
        tool.repair(args.file)
    elif args.command == 'generate':
        tool.generate_minimal(include_models=not args.no_models)
    elif args.command == 'reverse':
        if args.source == 'models':
            tool.reverse_from_models()
        elif args.source == 'database':
            print("⚠ 数据库逆向功能尚未实现")
            print("提示：可以使用 'python scripts/model_tools.py sync-shared' 来同步模型配置")
    elif args.command == 'interactive':
        if args.info:
            # 直接显示配置信息
            print("\n📊 当前配置信息:")
            if routes_file.exists():
                try:
                    with open(routes_file, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                    print(f"\n✅ routes.yaml")
                    print(f"   - 端点数量：{len(data.get('endpoints', []))}")
                    print(f"   - 模型数量：{len(data.get('models', {}))}")
                except Exception as e:
                    print(f"\n❌ routes.yaml 读取失败：{e}")
            else:
                print(f"\n❌ routes.yaml 不存在")

            if models_file.exists():
                try:
                    with open(models_file, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                    print(f"\n✅ models.yaml")
                    print(f"   - 模型数量：{len(data.get('models', {}))}")
                    orm_models = [k for k, v in data['models'].items() if v.get('orm') is True]
                    if orm_models:
                        print(f"   - ORM 模型：{len(orm_models)}")
                except Exception as e:
                    print(f"\n❌ models.yaml 读取失败：{e}")
            else:
                print(f"\n❌ models.yaml 不存在")
        else:
            tool.interactive()
    elif args.command == 'add-orm':
        tool.add_orm(args.models)
    elif args.command == 'remove-orm':
        tool.remove_orm(args.models)
    elif args.command == 'list-orm':
        tool.list_orm()
    elif args.command == 'sync-shared':
        tool.sync_shared()


if __name__ == '__main__':
    main()
