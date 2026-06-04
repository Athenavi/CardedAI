"""
多级缓存服务

实现三级缓存架构:
1. L1 - 内存缓存 (最快,容量小)
2. L2 - Redis缓存 (快,容量中等)
3. L3 - 文件缓存 (较慢,容量大,持久化)

提供缓存预热、统计和监控功能
"""

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional, List

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    from cachetools import TTLCache

    CACHE_TOOLS_AVAILABLE = True
except ImportError:
    CACHE_TOOLS_AVAILABLE = False


class MultiLevelCache:
    """
    多级缓存服务

    自动在多个缓存层级间同步数据
    支持缓存预热、统计和监控
    """

    def __init__(
            self,
            memory_max_size: int = 1000,
            memory_ttl: int = 300,
            redis_enabled: bool = False,
            redis_config: Optional[Dict[str, Any]] = None,
            file_cache_enabled: bool = True,
            file_cache_dir: str = "storage/cache/multi_level",
            file_cache_ttl: int = 3600,
    ):
        """
        初始化多级缓存

        Args:
            memory_max_size: L1内存缓存最大条目数
            memory_ttl: L1内存缓存TTL(秒)
            redis_enabled: 是否启用L2 Redis缓存
            redis_config: Redis配置
            file_cache_enabled: 是否启用L3文件缓存
            file_cache_dir: 文件缓存目录
            file_cache_ttl: 文件缓存TTL(秒)
        """
        # L1: 内存缓存
        if CACHE_TOOLS_AVAILABLE:
            self.memory_cache = TTLCache(maxsize=memory_max_size, ttl=memory_ttl)
        else:
            self.memory_cache = {}
            self.memory_ttl_map = {}

        self.memory_ttl = memory_ttl
        self.memory_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
        }

        # L2: Redis缓存
        self.redis_enabled = redis_enabled
        self.redis_client = None
        if redis_enabled and REDIS_AVAILABLE:
            try:
                config = redis_config or {
                    'host': 'localhost',
                    'port': 6379,
                    'db': 0,
                    'decode_responses': True,
                    'socket_connect_timeout': 1,  # 连接超时 1 秒
                    'socket_timeout': 1,  # 读写超时 1 秒
                }
                self.redis_client = redis.Redis(**config)
                # 移除 ping()：redis.Redis() 本身是惰性的，首次实际操作时才连接
                print("[MultiLevelCache] L2 Redis客户端已创建（惰性连接）")
            except Exception as e:
                print(f"[MultiLevelCache] L2 Redis连接失败: {e}")
                self.redis_enabled = False

        self.redis_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'errors': 0,
        }

        # L3: 文件缓存
        self.file_cache_enabled = file_cache_enabled
        self.file_cache_dir = Path(file_cache_dir)
        self.file_cache_ttl = file_cache_ttl

        if file_cache_enabled:
            self.file_cache_dir.mkdir(parents=True, exist_ok=True)
            print(f"[MultiLevelCache] L3 文件缓存已启用: {self.file_cache_dir}")

        self.file_cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'errors': 0,
        }

        # 总体统计
        self.total_requests = 0
        self.total_hits = 0

    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值 (从L1 -> L2 -> L3逐级查找)

        Args:
            key: 缓存键

        Returns:
            缓存值,不存在返回None
        """
        self.total_requests += 1

        # L1: 尝试从内存缓存获取
        value = self._get_from_memory(key)
        if value is not None:
            self.memory_stats['hits'] += 1
            self.total_hits += 1
            return value

        self.memory_stats['misses'] += 1

        # L2: 尝试从Redis获取
        if self.redis_enabled and self.redis_client:
            value = self._get_from_redis(key)
            if value is not None:
                self.redis_stats['hits'] += 1
                self.total_hits += 1
                # 回填到L1
                self._set_to_memory(key, value)
                return value

            self.redis_stats['misses'] += 1

        # L3: 尝试从文件缓存获取
        if self.file_cache_enabled:
            value = self._get_from_file(key)
            if value is not None:
                self.file_cache_stats['hits'] += 1
                self.total_hits += 1
                # 回填到L1和L2
                self._set_to_memory(key, value)
                if self.redis_enabled and self.redis_client:
                    self._set_to_redis(key, value)
                return value

            self.file_cache_stats['misses'] += 1

        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        设置缓存值 (同时写入L1, L2, L3)

        Args:
            key: 缓存键
            value: 缓存值
            ttl: TTL(秒),None使用默认值
        """
        # 写入L1
        self._set_to_memory(key, value, ttl)
        self.memory_stats['sets'] += 1

        # 写入L2
        if self.redis_enabled and self.redis_client:
            self._set_to_redis(key, value, ttl)
            self.redis_stats['sets'] += 1

        # 写入L3
        if self.file_cache_enabled:
            self._set_to_file(key, value, ttl)
            self.file_cache_stats['sets'] += 1

    def delete(self, key: str):
        """
        删除缓存 (从所有层级删除)

        Args:
            key: 缓存键
        """
        # 从L1删除
        self._delete_from_memory(key)
        self.memory_stats['deletes'] += 1

        # 从L2删除
        if self.redis_enabled and self.redis_client:
            self._delete_from_redis(key)

        # 从L3删除
        if self.file_cache_enabled:
            self._delete_from_file(key)

    def clear(self):
        """清空所有缓存层级"""
        # 清空L1
        if CACHE_TOOLS_AVAILABLE:
            self.memory_cache.clear()
        else:
            self.memory_cache.clear()
            self.memory_ttl_map.clear()

        # 清空L2
        if self.redis_enabled and self.redis_client:
            try:
                self.redis_client.flushdb()
            except Exception as e:
                print(f"[MultiLevelCache] Redis清空失败: {e}")

        # 清空L3
        if self.file_cache_enabled:
            try:
                for file in self.file_cache_dir.glob("*.cache"):
                    file.unlink()
            except Exception as e:
                print(f"[MultiLevelCache] 文件缓存清空失败: {e}")

        print("[MultiLevelCache] 所有缓存层级已清空")

    def warmup(self, keys_data: List[Dict[str, Any]]):
        """
        缓存预热

        Args:
            keys_data: 预热的数据列表,每项包含 {'key': ..., 'value': ..., 'ttl': ...}
        """
        print(f"[MultiLevelCache] 开始缓存预热,共 {len(keys_data)} 条数据")

        for item in keys_data:
            key = item.get('key')
            value = item.get('value')
            ttl = item.get('ttl')

            if key is not None and value is not None:
                self.set(key, value, ttl)

        print("[MultiLevelCache] 缓存预热完成")

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            统计信息字典
        """
        hit_rate = (self.total_hits / self.total_requests * 100) if self.total_requests > 0 else 0

        return {
            'total_requests': self.total_requests,
            'total_hits': self.total_hits,
            'hit_rate': f"{hit_rate:.2f}%",
            'levels': {
                'L1_memory': {
                    'hits': self.memory_stats['hits'],
                    'misses': self.memory_stats['misses'],
                    'sets': self.memory_stats['sets'],
                    'deletes': self.memory_stats['deletes'],
                    'size': len(self.memory_cache),
                },
                'L2_redis': {
                    'enabled': self.redis_enabled,
                    'hits': self.redis_stats['hits'],
                    'misses': self.redis_stats['misses'],
                    'sets': self.redis_stats['sets'],
                    'errors': self.redis_stats['errors'],
                },
                'L3_file': {
                    'enabled': self.file_cache_enabled,
                    'hits': self.file_cache_stats['hits'],
                    'misses': self.file_cache_stats['misses'],
                    'sets': self.file_cache_stats['sets'],
                    'errors': self.file_cache_stats['errors'],
                    'directory': str(self.file_cache_dir),
                }
            }
        }

    def _generate_file_key(self, key: str) -> str:
        """生成文件缓存的键名"""
        # 使用hash避免文件名过长或非法字符
        hash_key = hashlib.md5(key.encode()).hexdigest()
        return f"{hash_key}.cache"

    # ========== L1 内存缓存操作 ==========

    def _get_from_memory(self, key: str) -> Optional[Any]:
        """从内存缓存获取"""
        if CACHE_TOOLS_AVAILABLE:
            return self.memory_cache.get(key)
        else:
            if key in self.memory_cache:
                # 检查TTL
                if key in self.memory_ttl_map:
                    if time.time() > self.memory_ttl_map[key]:
                        del self.memory_cache[key]
                        del self.memory_ttl_map[key]
                        return None
                return self.memory_cache[key]
            return None

    def _set_to_memory(self, key: str, value: Any, ttl: Optional[int] = None):
        """设置内存缓存"""
        if CACHE_TOOLS_AVAILABLE:
            self.memory_cache[key] = value
        else:
            self.memory_cache[key] = value
            if ttl is None:
                ttl = self.memory_ttl
            self.memory_ttl_map[key] = time.time() + ttl

    def _delete_from_memory(self, key: str):
        """从内存缓存删除"""
        if key in self.memory_cache:
            del self.memory_cache[key]
        if key in self.memory_ttl_map:
            del self.memory_ttl_map[key]

    # ========== L2 Redis缓存操作 ==========

    def _get_from_redis(self, key: str) -> Optional[Any]:
        """从Redis获取"""
        try:
            value = self.redis_client.get(key)
            if value is not None:
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value
            return None
        except Exception as e:
            print(f"[MultiLevelCache] Redis获取失败: {e}")
            self.redis_stats['errors'] += 1
            return None

    def _set_to_redis(self, key: str, value: Any, ttl: Optional[int] = None):
        """设置Redis缓存"""
        try:
            if isinstance(value, (dict, list, bool, type(None))):
                serialized = json.dumps(value, ensure_ascii=False, default=str)
            else:
                serialized = str(value)

            if ttl is None:
                ttl = self.memory_ttl

            self.redis_client.setex(key, ttl, serialized)
        except Exception as e:
            print(f"[MultiLevelCache] Redis设置失败: {e}")
            self.redis_stats['errors'] += 1

    def _delete_from_redis(self, key: str):
        """从Redis删除"""
        try:
            self.redis_client.delete(key)
        except Exception as e:
            print(f"[MultiLevelCache] Redis删除失败: {e}")

    # ========== L3 文件缓存操作 ==========

    def _get_from_file(self, key: str) -> Optional[Any]:
        """从文件缓存获取"""
        try:
            file_path = self.file_cache_dir / self._generate_file_key(key)

            if not file_path.exists():
                return None

            # 读取元数据
            meta_path = file_path.with_suffix('.meta')
            if meta_path.exists():
                with open(meta_path, 'r', encoding='utf-8') as f:
                    meta = json.load(f)

                # 检查是否过期
                if time.time() - meta.get('created_at', 0) > meta.get('ttl', self.file_cache_ttl):
                    # 已过期,删除
                    file_path.unlink(missing_ok=True)
                    meta_path.unlink(missing_ok=True)
                    return None

            # 读取缓存内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return content

        except Exception as e:
            print(f"[MultiLevelCache] 文件缓存读取失败: {e}")
            self.file_cache_stats['errors'] += 1
            return None

    def _set_to_file(self, key: str, value: Any, ttl: Optional[int] = None):
        """设置文件缓存"""
        try:
            if ttl is None:
                ttl = self.file_cache_ttl

            file_path = self.file_cache_dir / self._generate_file_key(key)
            meta_path = file_path.with_suffix('.meta')

            # 序列化值
            if isinstance(value, (dict, list, bool, type(None))):
                content = json.dumps(value, ensure_ascii=False, default=str)
            else:
                content = str(value)

            # 写入缓存文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            # 写入元数据
            meta = {
                'key': key,
                'created_at': time.time(),
                'ttl': ttl,
            }
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(meta, f, ensure_ascii=False)

        except Exception as e:
            print(f"[MultiLevelCache] 文件缓存设置失败: {e}")
            self.file_cache_stats['errors'] += 1

    def _delete_from_file(self, key: str):
        """从文件缓存删除"""
        try:
            file_path = self.file_cache_dir / self._generate_file_key(key)
            meta_path = file_path.with_suffix('.meta')

            file_path.unlink(missing_ok=True)
            meta_path.unlink(missing_ok=True)
        except Exception as e:
            print(f"[MultiLevelCache] 文件缓存删除失败: {e}")


# 全局实例
multi_level_cache = MultiLevelCache()

# 导出
__all__ = ['MultiLevelCache', 'multi_level_cache']
