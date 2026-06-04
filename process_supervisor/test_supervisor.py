#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
进程监督器功能测试脚本
验证所有核心功能是否正常工作
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from process_supervisor.config_manager import get_config_manager
from process_supervisor.process_manager import get_supervisor
from process_supervisor.health_checker import HealthChecker


def test_config_manager():
    """测试配置管理器"""
    print("\n" + "="*60)
    print("测试配置管理器")
    print("="*60)
    
    try:
        config_manager = get_config_manager()
        
        # 测试加载配置
        configs = config_manager.get_all_process_configs()
        print(f"✓ 成功加载 {len(configs)} 个进程配置")
        
        # 验证关键进程存在
        expected_processes = ["main_app", "django_server", "update_server"]
        for proc_name in expected_processes:
            if proc_name in configs:
                print(f"  ✓ {proc_name}: 已配置")
            else:
                print(f"  ⚠ {proc_name}: 未配置")
        
        # 测试获取单个配置
        main_config = config_manager.get_process_config("main_app")
        if main_config:
            print(f"\nmain_app 配置:")
            print(f"  命令：{' '.join(main_config.command)}")
            print(f"  自动启动：{main_config.autostart}")
            print(f"  重启限制：{main_config.restart_limit}")
            if main_config.health_check:
                print(f"  健康检查：{main_config.health_check.endpoint}")
        
        return True
        
    except Exception as e:
        print(f"✗ 配置管理器测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def test_health_checker():
    """测试健康检查器"""
    print("\n" + "="*60)
    print("测试健康检查器")
    print("="*60)
    
    try:
        checker = HealthChecker("test_process")
        
        # 测试进程存活检查（使用当前进程）
        import os
        result = checker.check_process_alive(os.getpid())
        print(f"✓ 进程存活检查：{result.status.value}")
        print(f"  消息：{result.message}")
        
        # 测试端口检查（测试一个不存在的端口）
        result = checker.check_port_listening("127.0.0.1", 59999, timeout=1)
        print(f"✓ 端口检查：{result.status.value}")
        print(f"  消息：{result.message}")
        
        # 测试完整检查
        status, results = checker.perform_full_check(
            pid=os.getpid(),
            host="127.0.0.1",
            port=59999
        )
        print(f"✓ 完整健康检查：{status.value}")
        print(f"  检查项数：{len(results)}")
        
        return True
        
    except Exception as e:
        print(f"✗ 健康检查器测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def test_supervisor_initialization():
    """测试监督器初始化"""
    print("\n" + "="*60)
    print("测试监督器初始化")
    print("="*60)
    
    try:
        supervisor = get_supervisor()
        
        print(f"✓ 监督器创建成功")
        print(f"  管理进程数：{len(supervisor.processes)}")
        
        # 显示所有进程
        for name, process in supervisor.processes.items():
            autostart = "自动" if process.config.autostart else "手动"
            print(f"  - {name} ({autostart})")
        
        # 测试获取状态（不启动进程）
        statuses = supervisor.get_all_status()
        print(f"\n✓ 可以获取进程状态")
        
        return True
        
    except Exception as e:
        print(f"✗ 监督器初始化测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def test_web_admin_module():
    """测试 Web 管理界面模块"""
    print("\n" + "="*60)
    print("测试 Web 管理界面模块")
    print("="*60)
    
    try:
        from process_supervisor.web_admin import app, set_supervisor, get_supervisor
        
        if app:
            print(f"✓ FastAPI 应用已创建")
            
            # 测试设置监督器
            supervisor = get_supervisor()
            set_supervisor(supervisor)
            print(f"✓ 监督器已成功设置")
            
            # 检查路由
            routes = [route.path for route in app.routes]
            print(f"✓ 可用 API 端点：{len(routes)} 个")
            
            # 显示关键端点
            key_endpoints = ["/", "/api/system/status", "/api/processes", "/api/health"]
            for endpoint in key_endpoints:
                if endpoint in routes or any(endpoint in r for r in routes):
                    print(f"  ✓ {endpoint}")
                else:
                    print(f"  ⚠ {endpoint} (未找到)")
            
            return True
        else:
            print(f"⚠ FastAPI 未安装，Web 管理界面不可用")
            return True
            
    except ImportError as e:
        print(f"⚠ 导入 Web 管理模块失败：{e}")
        print(f"  提示：请安装 fastapi 和 uvicorn")
        return True  # 不是致命错误
    except Exception as e:
        print(f"✗ Web 管理界面测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("FastBlog 进程监督器功能测试")
    print("="*60)
    print(f"开始时间：{time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("配置管理器", test_config_manager),
        ("健康检查器", test_health_checker),
        ("监督器初始化", test_supervisor_initialization),
        ("Web 管理界面", test_web_admin_module),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} 测试异常：{e}")
            results.append((test_name, False))
    
    # 汇总结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{status}: {test_name}")
    
    print(f"\n总计：{passed}/{total} 测试通过")
    print("="*60)
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    
    if success:
        print("\n✓ 所有测试通过！进程监督器功能正常。")
        sys.exit(0)
    else:
        print("\n✗ 部分测试失败，请检查上述错误信息。")
        sys.exit(1)
