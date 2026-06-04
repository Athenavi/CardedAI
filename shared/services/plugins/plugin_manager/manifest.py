"""
插件清单(Manifest)验证和管理模块

提供标准化的插件元数据格式和验证机制
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional

from pydantic import BaseModel, Field, field_validator, ConfigDict

from shared.services.plugins.plugin_manager.version_utils import check_version_match


class PluginCapability(BaseModel):
    """
    插件能力声明
    
    定义插件需要的权限和能力
    格式: <resource>:<action>
    
    示例:
    - read:articles - 读取文章
    - write:articles - 写入文章
    - read:users - 读取用户信息
    - write:settings - 写入设置
    - access:filesystem - 访问文件系统
    - send:email - 发送邮件
    - execute:network - 网络请求
    """
    resource: str = Field(..., description="资源类型")
    action: str = Field(..., description="操作类型")
    description: Optional[str] = Field(None, description="能力描述")

    @field_validator('resource')
    @classmethod
    def validate_resource(cls, v):
        allowed_resources = [
            'articles', 'users', 'categories', 'media',
            'settings', 'comments', 'tags', 'pages',
            'filesystem', 'database', 'network', 'email'
        ]
        if v not in allowed_resources and not v.startswith('custom:'):
            raise ValueError(f"Invalid resource: {v}. Must be one of {allowed_resources} or start with 'custom:'")
        return v

    @field_validator('action')
    @classmethod
    def validate_action(cls, v):
        allowed_actions = ['read', 'write', 'delete', 'execute', 'send', 'access']
        if v not in allowed_actions:
            raise ValueError(f"Invalid action: {v}. Must be one of {allowed_actions}")
        return v

    def __str__(self):
        return f"{self.resource}:{self.action}"


class PluginDependency(BaseModel):
    """插件依赖"""
    name: str = Field(..., description="依赖包名称")
    version: Optional[str] = Field(None, description="版本要求，如 >=1.0.0")
    optional: bool = Field(False, description="是否可选依赖")


class PluginSettingsField(BaseModel):
    """插件设置字段定义"""
    type: str = Field(..., description="字段类型: text, number, boolean, select, textarea")
    label: str = Field(..., description="显示标签")
    default: Optional[Any] = Field(None, description="默认值")
    required: bool = Field(False, description="是否必填")
    options: Optional[List[str]] = Field(None, description="选项列表（用于select类型）")
    help: Optional[str] = Field(None, description="帮助文本")
    min: Optional[float] = Field(None, description="最小值（用于number类型）")
    max: Optional[float] = Field(None, description="最大值（用于number类型）")


class PluginManifest(BaseModel):
    """
    插件清单(Manifest)
    
    标准化的插件元数据格式，包含插件的所有必要信息
    """

    # 基本信息
    id: int = Field(0, description="插件ID（由系统分配）")
    name: str = Field(..., description="插件名称", min_length=1, max_length=100)
    slug: str = Field(..., description="插件标识符（唯一）", pattern=r'^[a-z0-9-]+$')
    version: str = Field(..., description="版本号（语义化版本）", pattern=r'^\d+\.\d+\.\d+$')
    description: str = Field(..., description="插件描述", max_length=500)

    # 作者信息
    author: str = Field(..., description="作者名称")
    author_url: Optional[str] = Field(None, description="作者网站")
    author_email: Optional[str] = Field(None, description="作者邮箱")

    # 插件信息
    plugin_url: Optional[str] = Field(None, description="插件主页")
    documentation_url: Optional[str] = Field(None, description="文档地址")
    icon: Optional[str] = Field(None, description="图标（emoji或URL）")
    category: Optional[str] = Field(None, description="分类")

    # 许可和状态
    license: str = Field("MIT", description="许可证")
    rating: Optional[float] = Field(None, ge=0, le=5, description="评分（0-5）")
    installs: Optional[int] = Field(None, ge=0, description="安装次数")

    # 兼容性要求
    requires: Dict[str, str] = Field(
        default_factory=lambda: {"fastblog": ">=1.0.0", "python": ">=3.8"},
        description="系统和版本要求"
    )

    # 依赖管理
    dependencies: List[PluginDependency] = Field(
        default_factory=list,
        description="Python包依赖"
    )
    plugin_dependencies: List[str] = Field(
        default_factory=list,
        description="其他插件依赖（slug列表）"
    )

    # 权限声明（新增 - 安全特性）
    capabilities: List[str] = Field(
        default_factory=list,
        description="""
        插件所需的能力/权限列表
        
        格式: <resource>:<action>
        
        示例:
        - "read:articles" - 读取文章
        - "write:articles" - 写入文章
        - "access:filesystem" - 访问文件系统
        - "send:email" - 发送邮件
        
        未在此声明的操作将被拒绝执行
        """
    )

    # 钩子注册
    hooks: List[str] = Field(
        default_factory=list,
        description="插件注册的钩子列表"
    )

    # 设置界面
    settings_schema: Dict[str, PluginSettingsField] = Field(
        default_factory=dict,
        description="设置界面字段定义"
    )

    # 市场信息
    changelog: Optional[str] = Field(None, description="更新日志")
    download_url: Optional[str] = Field(None, description="下载地址")
    screenshots: List[str] = Field(
        default_factory=list,
        description="截图URL列表"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="标签列表，用于搜索"
    )

    # 文件路径
    main_file: str = Field("plugin.py", description="主文件路径")
    readme_file: Optional[str] = Field(None, description="README文件路径")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "SEO Optimizer",
                "slug": "seo-optimizer",
                "version": "1.0.0",
                "description": "自动优化文章 SEO",
                "author": "FastBlog Team",
                "author_url": "https://fastblog.com",
                "license": "MIT",
                "capabilities": [
                    "read:articles",
                    "write:settings"
                ],
                "dependencies": [
                    {"name": "beautifulsoup4", "version": ">=4.9.0"}
                ],
                "hooks": ["article_published", "article_updated"],
                "requires": {
                    "fastblog": ">=1.0.0",
                    "python": ">=3.8"
                }
            }
        }
    )


class ManifestValidator:
    """
    插件清单验证器
    
    验证插件的 metadata.json 文件是否符合规范
    """

    @staticmethod
    def validate_file(manifest_path: Path) -> tuple[bool, str, Optional[PluginManifest]]:
        """
        验证插件清单文件
        
        Args:
            manifest_path: metadata.json 文件路径
            
        Returns:
            (是否有效, 错误消息, 解析后的manifest对象)
        """
        if not manifest_path.exists():
            return False, f"Manifest file not found: {manifest_path}", None

        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON format: {str(e)}", None
        except Exception as e:
            return False, f"Failed to read file: {str(e)}", None

        try:
            manifest = PluginManifest(**data)
            return True, "Valid", manifest
        except Exception as e:
            return False, f"Validation failed: {str(e)}", None

    @staticmethod
    def validate_capabilities(capabilities: List[str]) -> tuple[bool, List[str]]:
        """
        验证能力声明列表
        
        Returns:
            (是否全部有效, 错误列表)
        """
        errors = []
        for cap_str in capabilities:
            try:
                parts = cap_str.split(':')
                if len(parts) != 2:
                    errors.append(f"Invalid capability format: {cap_str}. Expected format: resource:action")
                    continue

                resource, action = parts
                PluginCapability(resource=resource, action=action)
            except Exception as e:
                errors.append(f"Invalid capability '{cap_str}': {str(e)}")

        return len(errors) == 0, errors

    @staticmethod
    def create_template(output_path: Path, plugin_name: str = "My Plugin"):
        """
        创建标准的 manifest 模板文件
        
        Args:
            output_path: 输出目录
            plugin_name: 插件名称
        """
        slug = plugin_name.lower().replace(' ', '-')

        template = PluginManifest(
            name=plugin_name,
            slug=slug,
            version="1.0.0",
            description="插件描述",
            author="Your Name",
            author_url="https://yourwebsite.com",
            license="MIT",
            capabilities=["read:articles"],
            dependencies=[],
            hooks=["article_published"],
            requires={
                "fastblog": ">=1.0.0",
                "python": ">=3.8"
            }
        )

        output_file = output_path / "metadata.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(template.model_dump(exclude_none=True), f, indent=2, ensure_ascii=False)

        return output_file


# 预定义的能力列表（供参考）
PREDEFINED_CAPABILITIES = {
    "read:articles": "读取文章内容",
    "write:articles": "创建和编辑文章",
    "delete:articles": "删除文章",
    "read:users": "读取用户信息",
    "write:users": "修改用户信息",
    "read:categories": "读取分类信息",
    "write:categories": "管理分类",
    "read:media": "读取媒体文件",
    "write:media": "上传和管理媒体",
    "read:settings": "读取系统设置",
    "write:settings": "修改系统设置",
    "read:comments": "读取评论",
    "write:comments": "管理评论",
    "access:filesystem": "访问文件系统",
    "execute:network": "发起网络请求",
    "send:email": "发送邮件",
    "access:database": "直接访问数据库",
}


def get_capability_description(capability: str) -> str:
    """获取能力的中文描述"""
    return PREDEFINED_CAPABILITIES.get(capability, f"自定义能力: {capability}")


class DependencyResolver:
    """
    插件依赖解析器
    
    负责解析、验证和管理插件的依赖关系
    """

    @staticmethod
    def check_python_version(required_version: str) -> tuple[bool, str]:
        """
        检查 Python 版本是否满足要求
        
        Args:
            required_version: 版本要求，如 ">=3.8", "3.9.x"
            
        Returns:
            (是否满足, 消息)
        """
        import sys
        current_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

        # 简单版本比较
        try:
            from packaging import version

            # 解析版本要求
            if required_version.startswith(">="):
                min_ver = required_version[2:]
                if version.parse(current_version) >= version.parse(min_ver):
                    return True, f"Python {current_version} >= {min_ver}"
                else:
                    return False, f"Python {current_version} < {min_ver}"
            elif required_version.startswith(">"):
                min_ver = required_version[1:]
                if version.parse(current_version) > version.parse(min_ver):
                    return True, f"Python {current_version} > {min_ver}"
                else:
                    return False, f"Python {current_version} <= {min_ver}"
            elif required_version.startswith("=="):
                target_ver = required_version[2:]
                if version.parse(current_version) == version.parse(target_ver):
                    return True, f"Python {current_version} == {target_ver}"
                else:
                    return False, f"Python {current_version} != {target_ver}"
            else:
                # 默认当作 >= 处理
                min_ver = required_version
                if version.parse(current_version) >= version.parse(min_ver):
                    return True, f"Python {current_version} >= {min_ver}"
                else:
                    return False, f"Python {current_version} < {min_ver}"
        except ImportError:
            # 如果没有 packaging 库，使用简单比较
            return True, f"Python {current_version} (未严格验证)"

    @staticmethod
    def check_package_installed(package_name: str, required_version: Optional[str] = None) -> tuple[bool, str]:
        """
        检查 Python 包是否已安装且版本满足要求
        
        Args:
            package_name: 包名
            required_version: 版本要求（可选）
            
        Returns:
            (是否满足, 消息)
        """
        try:
            import pkg_resources

            # 检查包是否安装
            dist = pkg_resources.get_distribution(package_name)
            installed_version = dist.version

            if not required_version:
                return True, f"{package_name} {installed_version} 已安装"

            # 检查版本是否满足要求
            from packaging import version as pkg_version

            if required_version.startswith(">="):
                min_ver = required_version[2:]
                if pkg_version.parse(installed_version) >= pkg_version.parse(min_ver):
                    return True, f"{package_name} {installed_version} >= {min_ver}"
                else:
                    return False, f"{package_name} {installed_version} < {min_ver}"
            elif required_version.startswith("=="):
                target_ver = required_version[2:]
                if pkg_version.parse(installed_version) == pkg_version.parse(target_ver):
                    return True, f"{package_name} {installed_version} == {target_ver}"
                else:
                    return False, f"{package_name} {installed_version} != {target_ver}"
            else:
                # 默认当作 >= 处理
                min_ver = required_version
                if pkg_version.parse(installed_version) >= pkg_version.parse(min_ver):
                    return True, f"{package_name} {installed_version} >= {min_ver}"
                else:
                    return False, f"{package_name} {installed_version} < {min_ver}"

        except pkg_resources.DistributionNotFound:
            return False, f"{package_name} 未安装"
        except Exception as e:
            return False, f"检查失败: {str(e)}"
    
    @staticmethod
    def _check_version_compatibility(current_version: str, required_version: str) -> bool:
        """
        检查版本兼容性（使用统一的版本比较工具）
        
        Args:
            current_version: 当前版本
            required_version: 要求的版本（支持 >=, >, = 等前缀）
            
        Returns:
            是否兼容
        """
        return check_version_match(current_version, required_version)

    @staticmethod
    def resolve_plugin_dependencies(
            manifest: PluginManifest,
            available_plugins: Dict[str, Any]
    ) -> tuple[bool, List[str], List[str]]:
        """
        解析插件依赖关系
        
        Args:
            manifest: 插件清单
            available_plugins: 已安装的插件字典 {slug: plugin_instance}
            
        Returns:
            (是否满足所有依赖, 缺失的依赖列表, 错误消息列表)
        """
        missing_deps = []
        errors = []

        # 1. 检查插件依赖
        for dep_slug in manifest.plugin_dependencies:
            if dep_slug not in available_plugins:
                missing_deps.append(f"plugin:{dep_slug}")
                errors.append(f"缺少插件依赖: {dep_slug}")

        # 2. 检查 Python 包依赖
        for dep in manifest.dependencies:
            is_ok, message = DependencyResolver.check_package_installed(
                dep.name,
                dep.version
            )

            if not is_ok:
                if not dep.optional:
                    missing_deps.append(f"package:{dep.name}")
                    errors.append(f"缺少必需依赖: {message}")
                else:
                    errors.append(f"缺少可选依赖: {message}")

        # 3. 检查系统要求
        for system, version_req in manifest.requires.items():
            if system == "python":
                is_ok, message = DependencyResolver.check_python_version(version_req)
                if not is_ok:
                    errors.append(f"Python 版本不满足: {message}")
            elif system == "fastblog":
                # 检查 FastBlog 版本
                try:
                    from pathlib import Path
                    version_file = Path(__file__).parent.parent.parent / 'version.txt'
                    if version_file.exists():
                        with open(version_file, 'r') as f:
                            current_version = f.read().strip()
                    else:
                        current_version = '0.0.1'
                    
                    # 使用版本比较逻辑
                    if not DependencyResolver._check_version_compatibility(current_version, version_req):
                        errors.append(f"FastBlog 版本不满足: 需要 {version_req}，当前 {current_version}")
                except Exception as e:
                    errors.append(f"检查 FastBlog 版本失败: {str(e)}")

        all_satisfied = len(missing_deps) == 0
        return all_satisfied, missing_deps, errors

    @staticmethod
    def get_dependency_tree(
            manifests: Dict[str, PluginManifest]
    ) -> Dict[str, List[str]]:
        """
        生成依赖树
        
        Args:
            manifests: 所有插件的清单字典 {slug: manifest}
            
        Returns:
            依赖树 {plugin_slug: [依赖列表]}
        """
        tree = {}

        for slug, manifest in manifests.items():
            deps = []

            # 添加插件依赖
            for dep_slug in manifest.plugin_dependencies:
                deps.append(f"plugin:{dep_slug}")

            # 添加包依赖
            for dep in manifest.dependencies:
                version_str = f" ({dep.version})" if dep.version else ""
                optional_str = " [optional]" if dep.optional else ""
                deps.append(f"package:{dep.name}{version_str}{optional_str}")

            tree[slug] = deps

        return tree

    @staticmethod
    def detect_circular_dependencies(
            manifests: Dict[str, PluginManifest]
    ) -> List[List[str]]:
        """
        检测循环依赖
        
        Args:
            manifests: 所有插件的清单字典
            
        Returns:
            循环依赖列表，每个元素是一个循环链
        """
        # 构建依赖图
        graph = {}
        for slug, manifest in manifests.items():
            graph[slug] = manifest.plugin_dependencies

        # DFS 检测循环
        visited = set()
        rec_stack = set()
        cycles = []

        def dfs(node, path):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, path)
                elif neighbor in rec_stack:
                    # 找到循环
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)

            path.pop()
            rec_stack.remove(node)

        for node in graph:
            if node not in visited:
                dfs(node, [])

        return cycles

    @staticmethod
    def install_dependencies(manifest: PluginManifest) -> tuple[bool, List[str]]:
        """
        安装插件依赖
        
        Args:
            manifest: 插件清单
            
        Returns:
            (是否成功, 消息列表)
        """
        import subprocess
        import sys

        messages = []
        success = True

        for dep in manifest.dependencies:
            if dep.optional:
                messages.append(f"跳过可选依赖: {dep.name}")
                continue

            # 构建 pip 安装命令
            package_spec = dep.name
            if dep.version:
                package_spec += dep.version

            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", package_spec],
                    capture_output=True,
                    text=True,
                    timeout=300  # 5分钟超时
                )

                if result.returncode == 0:
                    messages.append(f"✓ 安装成功: {package_spec}")
                else:
                    messages.append(f"✗ 安装失败: {package_spec}")
                    messages.append(f"  错误: {result.stderr[:200]}")
                    success = False
            except subprocess.TimeoutExpired:
                messages.append(f"✗ 安装超时: {package_spec}")
                success = False
            except Exception as e:
                messages.append(f"✗ 安装异常: {package_spec} - {str(e)}")
                success = False

        return success, messages
