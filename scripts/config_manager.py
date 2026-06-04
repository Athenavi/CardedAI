"""
环境配置管理工具
用于切换、对比和管理不同环境的配置文件
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, base_dir: Path = None):
        self.base_dir = base_dir or Path(__file__).resolve().parent.parent
        self.env_file = self.base_dir / '.env'
        self.environments = ['development', 'staging', 'production']
    
    def get_current_environment(self) -> str:
        """获取当前环境"""
        if self.env_file.exists():
            load_dotenv(self.env_file)
            return os.getenv('ENVIRONMENT', 'development')
        return 'development'
    
    def switch_environment(self, env_name: str) -> bool:
        """
        切换到指定环境
        
        Args:
            env_name: 环境名称 (development/staging/production)
            
        Returns:
            是否成功
        """
        if env_name not in self.environments:
            print(f"错误: 未知环境 '{env_name}'")
            print(f"可用环境: {', '.join(self.environments)}")
            return False
        
        # 检查环境文件是否存在
        env_file = self.base_dir / f'.env.{env_name}'
        if not env_file.exists():
            print(f"警告: 环境配置文件 .env.{env_name} 不存在")
            print("请先创建环境配置文件或从示例文件复制")
            return False
        
        # 更新主.env文件的ENVIRONMENT变量
        if self.env_file.exists():
            # 读取现有内容
            with open(self.env_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 更新或添加ENVIRONMENT变量
            updated = False
            for i, line in enumerate(lines):
                if line.startswith('ENVIRONMENT='):
                    lines[i] = f'ENVIRONMENT={env_name}\n'
                    updated = True
                    break
            
            if not updated:
                lines.append(f'\n# Current Environment\nENVIRONMENT={env_name}\n')
            
            # 写回文件
            with open(self.env_file, 'w', encoding='utf-8') as f:
                f.writelines(lines)
        
        print(f"✓ 已切换到 {env_name} 环境")
        print(f"  配置文件: .env.{env_name}")
        return True
    
    def compare_environments(self, env1: str, env2: str) -> dict:
        """
        比较两个环境的配置差异
        
        Args:
            env1: 第一个环境
            env2: 第二个环境
            
        Returns:
            差异字典
        """
        config1 = self._load_env_config(env1)
        config2 = self._load_env_config(env2)
        
        all_keys = set(list(config1.keys()) + list(config2.keys()))
        
        differences = {
            'only_in_env1': {},
            'only_in_env2': {},
            'different_values': {},
        }
        
        for key in all_keys:
            val1 = config1.get(key)
            val2 = config2.get(key)
            
            if val1 is not None and val2 is None:
                differences['only_in_env1'][key] = val1
            elif val1 is None and val2 is not None:
                differences['only_in_env2'][key] = val2
            elif val1 != val2:
                differences['different_values'][key] = {
                    env1: val1,
                    env2: val2,
                }
        
        return differences
    
    def _load_env_config(self, env_name: str) -> dict:
        """加载环境配置"""
        env_file = self.base_dir / f'.env.{env_name}'
        config = {}
        
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()
        
        return config
    
    def list_environments(self):
        """列出所有可用环境"""
        print("可用环境:")
        current = self.get_current_environment()
        
        for env in self.environments:
            env_file = self.base_dir / f'.env.{env}'
            exists = "✓" if env_file.exists() else "✗"
            marker = " ← 当前" if env == current else ""
            print(f"  {exists} {env}{marker}")
    
    def validate_environment(self, env_name: str) -> list:
        """
        验证环境配置的完整性
        
        Args:
            env_name: 环境名称
            
        Returns:
            缺失的必要配置列表
        """
        config = self._load_env_config(env_name)
        
        required_vars = {
            'development': ['DEBUG', 'DB_ENGINE'],
            'staging': ['DEBUG', 'DB_ENGINE', 'DB_NAME'],
            'production': [
                'DEBUG', 'DB_ENGINE', 'DB_NAME', 'DB_USER',
                'DB_PASSWORD', 'SECRET_KEY', 'ALLOWED_HOSTS'
            ],
        }
        
        missing = []
        for var in required_vars.get(env_name, []):
            if var not in config:
                missing.append(var)
        
        return missing


def main():
    """CLI入口"""
    manager = ConfigManager()
    
    if len(sys.argv) < 2:
        print("用法: python config_manager.py <command> [args]")
        print("\n可用命令:")
        print("  list                    - 列出所有环境")
        print("  current                 - 显示当前环境")
        print("  switch <environment>    - 切换环境")
        print("  compare <env1> <env2>   - 比较两个环境")
        print("  validate <environment>  - 验证环境配置")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'list':
        manager.list_environments()
    
    elif command == 'current':
        current = manager.get_current_environment()
        print(f"当前环境: {current}")
    
    elif command == 'switch':
        if len(sys.argv) < 3:
            print("用法: python config_manager.py switch <environment>")
            sys.exit(1)
        env_name = sys.argv[2]
        manager.switch_environment(env_name)
    
    elif command == 'compare':
        if len(sys.argv) < 4:
            print("用法: python config_manager.py compare <env1> <env2>")
            sys.exit(1)
        env1, env2 = sys.argv[2], sys.argv[3]
        diff = manager.compare_environments(env1, env2)
        
        print(f"\n配置差异: {env1} vs {env2}")
        print("=" * 60)
        
        if diff['only_in_env1']:
            print(f"\n仅在 {env1} 中:")
            for key, val in diff['only_in_env1'].items():
                print(f"  {key}={val}")
        
        if diff['only_in_env2']:
            print(f"\n仅在 {env2} 中:")
            for key, val in diff['only_in_env2'].items():
                print(f"  {key}={val}")
        
        if diff['different_values']:
            print(f"\n值不同:")
            for key, vals in diff['different_values'].items():
                print(f"  {key}:")
                print(f"    {env1}: {vals[env1]}")
                print(f"    {env2}: {vals[env2]}")
        
        if not any(diff.values()):
            print("  无差异")
    
    elif command == 'validate':
        if len(sys.argv) < 3:
            print("用法: python config_manager.py validate <environment>")
            sys.exit(1)
        env_name = sys.argv[2]
        missing = manager.validate_environment(env_name)
        
        if missing:
            print(f"环境 {env_name} 缺少以下必要配置:")
            for var in missing:
                print(f"  - {var}")
            sys.exit(1)
        else:
            print(f"✓ 环境 {env_name} 配置完整")
    
    else:
        print(f"未知命令: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()
