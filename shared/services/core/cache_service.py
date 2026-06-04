"""
性能优化服务 - 缓存、懒加载、资源压缩
"""

import json
import time
from functools import wraps
from typing import Dict, Any, Optional, Callable, List

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


class CacheService:
    """缓存服务 - 支持内存和Redis

    使用cachetools.TTLCache实现高效的内存缓存(如果可用)
    支持Redis作为后端缓存(可选)
    """

    def __init__(self, use_redis: bool = False, redis_config: Dict[str, Any] = None,
                 max_size: int = 1000, default_ttl: int = 3600):
        """
        初始化缓存服务

        Args:
            use_redis: 是否使用Redis
            redis_config: Redis配置字典
            max_size: 内存缓存最大条目数
            default_ttl: 默认TTL(秒)
        """
        self.default_ttl = default_ttl
        self.use_redis = use_redis
        self.redis_client = None

        # 使用cachetools.TTLCache(如果可用)或普通字典
        if CACHE_TOOLS_AVAILABLE:
            self.cache = TTLCache(maxsize=max_size, ttl=default_ttl)
        else:
            self.cache: Dict[str, Any] = {}
            self.ttl: Dict[str, float] = {}

        # 初始化Redis客户端
        if use_redis and REDIS_AVAILABLE:
            try:
                config = redis_config or {
                    'host': 'localhost',
                    'port': 6379,
                    'db': 0,
                    'decode_responses': True,  # 自动解码为字符串
                    'socket_connect_timeout': 1,  # 连接超时 1 秒
                    'socket_timeout': 1,  # 读写超时 1 秒
                }
                self.redis_client = redis.Redis(**config)
                # 移除 ping()：redis.Redis() 本身是惰性的，首次实际操作时才连接
                print("[CacheService] Redis客户端已创建（惰性连接）")
            except Exception as e:
                print(f"[CacheService] Redis连接失败: {e}, 使用内存缓存")
                self.use_redis = False
                self.redis_client = None
        elif use_redis and not REDIS_AVAILABLE:
            print("[CacheService] redis库未安装,使用内存缓存")
            self.use_redis = False

    def get(self, key: str) -> Optional[Any]:
        """获取缓存

        Args:
            key: 缓存键

        Returns:
            缓存值,不存在则返回None
        """
        # 优先从Redis获取
        if self.use_redis and self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value is not None:
                    # 尝试反序列化JSON
                    try:
                        return json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        return value
                return None
            except Exception as e:
                print(f"[CacheService] Redis获取失败: {e}, 降级到内存缓存")
                self.use_redis = False

        # 从内存缓存获取(cachetools会自动处理TTL)
        if CACHE_TOOLS_AVAILABLE:
            return self.cache.get(key)
        else:
            # 手动TTL检查(兼容模式)
            if key in self.cache:
                if key in self.ttl and time.time() > self.ttl[key]:
                    del self.cache[key]
                    del self.ttl[key]
                    return None
                return self.cache[key]
            return None

    def set(self, key: str, value: Any, ttl: int = None):
        """设置缓存

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间(秒),默认使用default_ttl
        """
        if ttl is None:
            ttl = self.default_ttl

        # 存储到Redis
        if self.use_redis and self.redis_client:
            try:
                # 将值序列化为JSON字符串
                if isinstance(value, (dict, list, bool, type(None))):
                    serialized_value = json.dumps(value, ensure_ascii=False)
                else:
                    serialized_value = str(value)

                self.redis_client.setex(key, ttl, serialized_value)
            except Exception as e:
                print(f"[CacheService] Redis存储失败: {e}, 降级到内存缓存")
                self.use_redis = False

        # 存储到内存缓存
        if CACHE_TOOLS_AVAILABLE:
            # cachetools需要重新创建带TTL的条目
            # 注意:TTLCache的TTL在创建时设定,这里简化处理
            self.cache[key] = value
        else:
            # 手动管理TTL
            self.cache[key] = value
            self.ttl[key] = time.time() + ttl

    def delete(self, key: str):
        """删除缓存

        Args:
            key: 缓存键
        """
        if self.use_redis and self.redis_client:
            try:
                self.redis_client.delete(key)
            except Exception as e:
                print(f"[CacheService] Redis删除失败: {e}")

        if key in self.cache:
            del self.cache[key]

    def clear(self):
        """清空缓存"""
        if self.use_redis and self.redis_client:
            try:
                self.redis_client.flushdb()
            except Exception as e:
                print(f"[CacheService] Redis清空失败: {e}")

        self.cache.clear()


class LazyLoadService:
    """图片懒加载服务"""

    def generate_lazy_html(self, image_url: str, alt: str = "", class_name: str = "") -> str:
        """
        生成懒加载HTML

        Args:
            image_url: 图片URL
            alt: 替代文本
            class_name: CSS类名
        """
        return f'''
        <img
            data-src="{image_url}"
            alt="{alt}"
            class="lazyload {class_name}"
            loading="lazy"
            onload="this.src=this.dataset.src"
        />
        '''

    def add_lazy_load_script(self) -> str:
        """添加懒加载JavaScript"""
        return '''
        <script>
        document.addEventListener("DOMContentLoaded", function() {
            const lazyImages = document.querySelectorAll('img[data-src]');
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                        observer.unobserve(img);
                    }
                });
            });
            lazyImages.forEach(img => imageObserver.observe(img));
        });
        </script>
        '''


class AssetMinifier:
    """CSS/JS合并压缩服务"""

    def minify_css(self, css_content: str) -> str:
        """压缩CSS"""
        # 移除注释
        import re
        css = re.sub(r'/\*.*?\*/', '', css_content, flags=re.DOTALL)
        # 移除多余空白
        css = re.sub(r'\s+', ' ', css)
        css = re.sub(r'\s*([{}:;,])\s*', r'\1', css)
        return css.strip()

    def minify_js(self, js_content: str) -> str:
        """压缩JavaScript"""
        import re
        # 移除单行注释(不在字符串中的)
        js = re.sub(r'//[^\n]*', '', js_content)
        # 移除多余空白
        js = re.sub(r'\s+', ' ', js)
        return js.strip()

    def combine_files(self, file_paths: List[str], output_path: str, file_type: str = 'css'):
        """
        合并多个文件

        Args:
            file_paths: 文件路径列表
            output_path: 输出文件路径
            file_type: 文件类型(css/js)
        """
        combined = []
        for path in file_paths:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    combined.append(f.read())
            except Exception as e:
                print(f"读取文件失败 {path}: {e}")

        content = '\n'.join(combined)

        # 压缩
        if file_type == 'css':
            content = self.minify_css(content)
        elif file_type == 'js':
            content = self.minify_js(content)

        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return output_path


def cached(ttl: int = 3600):
    """缓存装饰器"""

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            cached_value = cache_service.get(cache_key)

            if cached_value is not None:
                return cached_value

            result = await func(*args, **kwargs)
            cache_service.set(cache_key, result, ttl)
            return result

        return wrapper

    return decorator


class PageCacheService:
    """页面级缓存服务 - 生成静态HTML缓存

    用于缓存完整的页面HTML,提升访问速度
    """

    def __init__(self, cache_dir: str = "storage/cache/pages", default_ttl: int = 3600):
        """
        Args:
            cache_dir: 缓存目录
            default_ttl: 默认TTL(秒)
        """
        self.cache_dir = cache_dir
        self.default_ttl = default_ttl
        import os
        os.makedirs(cache_dir, exist_ok=True)

    def _get_cache_path(self, url: str) -> str:
        """根据URL生成缓存文件路径"""
        import hashlib
        import os
        # 将URL转换为安全的文件名
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
        return os.path.join(self.cache_dir, f"{url_hash}.html")

    def _get_meta_path(self, url: str) -> str:
        """获取元数据文件路径"""
        import hashlib
        import os
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
        return os.path.join(self.cache_dir, f"{url_hash}.meta.json")

    def get_page(self, url: str) -> Optional[Dict[str, Any]]:
        """
        获取缓存的页面

        Args:
            url: 页面URL

        Returns:
            包含content、status_code、headers的字典,不存在返回None
        """
        import os
        import json
        import time

        cache_path = self._get_cache_path(url)
        meta_path = self._get_meta_path(url)

        if not os.path.exists(cache_path) or not os.path.exists(meta_path):
            return None

        try:
            # 检查是否过期
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)

            if time.time() - meta['cached_at'] > meta.get('ttl', self.default_ttl):
                # 已过期,删除缓存
                os.remove(cache_path)
                os.remove(meta_path)
                return None

            # 读取缓存内容
            with open(cache_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return {
                'content': content,
                'status_code': meta.get('status_code', 200),
                'headers': meta.get('headers', {}),
                'cached_at': meta['cached_at'],
                'age': int(time.time() - meta['cached_at'])
            }
        except Exception as e:
            print(f"[PageCache] 读取缓存失败: {e}")
            return None

    def set_page(self, url: str, content: str, status_code: int = 200,
                 headers: Dict[str, str] = None, ttl: int = None):
        """
        缓存页面

        Args:
            url: 页面URL
            content: HTML内容
            status_code: HTTP状态码
            headers: HTTP头
            ttl: TTL(秒)
        """
        import json
        import time

        if ttl is None:
            ttl = self.default_ttl

        cache_path = self._get_cache_path(url)
        meta_path = self._get_meta_path(url)

        try:
            # 保存HTML内容
            with open(cache_path, 'w', encoding='utf-8') as f:
                f.write(content)

            # 保存元数据
            meta = {
                'url': url,
                'status_code': status_code,
                'headers': headers or {},
                'cached_at': time.time(),
                'ttl': ttl
            }

            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"[PageCache] 保存缓存失败: {e}")

    def invalidate_page(self, url: str):
        """使页面缓存失效"""
        import os

        cache_path = self._get_cache_path(url)
        meta_path = self._get_meta_path(url)

        try:
            if os.path.exists(cache_path):
                os.remove(cache_path)
            if os.path.exists(meta_path):
                os.remove(meta_path)
        except Exception as e:
            print(f"[PageCache] 删除缓存失败: {e}")

    def clear_all(self):
        """清空所有页面缓存"""
        import os
        import glob

        try:
            for file in glob.glob(os.path.join(self.cache_dir, "*.html")):
                os.remove(file)
            for file in glob.glob(os.path.join(self.cache_dir, "*.meta.json")):
                os.remove(file)
        except Exception as e:
            print(f"[PageCache] 清空缓存失败: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        import os
        import glob

        html_files = glob.glob(os.path.join(self.cache_dir, "*.html"))
        meta_files = glob.glob(os.path.join(self.cache_dir, "*.meta.json"))

        total_size = sum(os.path.getsize(f) for f in html_files)

        return {
            'total_pages': len(html_files),
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'cache_dir': self.cache_dir
        }


class CacheWarmer:
    """缓存预热器 - 预热热门页面缓存"""

    def __init__(self, page_cache: PageCacheService = None):
        self.page_cache = page_cache or page_cache_service_page
        self.warmup_queue = []

    def add_url(self, url: str, priority: int = 10):
        """
        添加需要预热的URL

        Args:
            url: 页面URL
            priority: 优先级(数字越小优先级越高)
        """
        self.warmup_queue.append({'url': url, 'priority': priority})
        # 按优先级排序
        self.warmup_queue.sort(key=lambda x: x['priority'])

    async def warmup(self, fetch_func=None):
        """
        执行缓存预热

        Args:
            fetch_func: 获取页面内容的函数,接收url参数
        """
        import aiohttp

        warmed_count = 0
        failed_count = 0

        for item in self.warmup_queue:
            url = item['url']
            try:
                if fetch_func:
                    # 使用自定义fetch函数
                    content = await fetch_func(url)
                else:
                    # 默认使用HTTP请求
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url) as response:
                            content = await response.text()

                if content:
                    self.page_cache.set_page(url, content)
                    warmed_count += 1
                    print(f"[CacheWarmer] ✓ 预热成功: {url}")
                else:
                    failed_count += 1
                    print(f"[CacheWarmer] ✗ 预热失败(空内容): {url}")

            except Exception as e:
                failed_count += 1
                print(f"[CacheWarmer] ✗ 预热失败: {url} - {e}")

        print(f"[CacheWarmer] 预热完成: 成功{warmed_count}, 失败{failed_count}")
        self.warmup_queue.clear()


# 全局实例
cache_service = CacheService()
lazy_load_service = LazyLoadService()
asset_minifier = AssetMinifier()
page_cache_service_page = PageCacheService()
cache_warmer = CacheWarmer(page_cache_service_page)
