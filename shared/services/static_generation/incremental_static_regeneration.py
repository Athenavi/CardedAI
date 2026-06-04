"""
增量静态再生成（ISR）服务

基于Next.js ISR概念实现的增量静态页面更新机制

功能：
1. 按需重新生成页面
2. 后台重新验证（stale-while-revalidate）
3. 重验证时间配置
4. 缓存失效管理
5. 并发控制
6. 请求队列管理
"""
import asyncio
import hashlib

from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Any, Callable

from src.unified_logger import default_logger as logger


class ISRPage:
    """ISR页面元数据"""

    def __init__(self, path: str, revalidate_time: int = 60):
        self.path = path
        self.revalidate_time = revalidate_time  # 重新验证时间（秒）
        self.last_generated: Optional[datetime] = None
        self.last_revalidated: Optional[datetime] = None
        self.is_regenerating: bool = False
        self.pending_requests: int = 0
        self.cache_key: str = self._generate_cache_key()

    def _generate_cache_key(self) -> str:
        """生成缓存键"""
        return hashlib.md5(self.path.encode()).hexdigest()

    def should_revalidate(self) -> bool:
        """检查是否需要重新验证"""
        if not self.last_revalidated:
            return True

        elapsed = (datetime.now() - self.last_revalidated).total_seconds()
        return elapsed >= self.revalidate_time

    def is_stale(self) -> bool:
        """检查是否过期但仍可服务"""
        if not self.last_generated:
            return True

        elapsed = (datetime.now() - self.last_generated).total_seconds()
        return elapsed >= self.revalidate_time


class IncrementalStaticRegenerator:
    """
    增量静态再生成器
    
    实现Next.js风格的ISR机制：
    1. 首次请求时生成静态页面
    2. 在revalidate时间内返回缓存页面
    3. 超过revalidate时间后，后台触发重新生成
    4. 重新生成期间继续返回旧页面
    5. 生成完成后更新缓存
    """

    def __init__(self, output_dir: str = "static_generated",
                 max_concurrent_revalidations: int = 5):
        self.output_dir = Path(output_dir)
        self.pages: Dict[str, ISRPage] = {}
        self.max_concurrent = max_concurrent_revalidations
        self.current_revalidations: int = 0
        self.revalidation_queue: asyncio.Queue = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None
        self._running: bool = False

        # 统计信息
        self.stats = {
            'total_pages': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'background_revalidations': 0,
            'failed_revalidations': 0
        }

        # 确保目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def start(self):
        """启动ISR后台工作器"""
        if self._running:
            return

        self._running = True
        self._worker_task = asyncio.create_task(self._revalidation_worker())
        logger.info("ISR revalidation worker started")

    async def stop(self):
        """停止ISR后台工作器"""
        if not self._running:
            return

        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

        logger.info("ISR revalidation worker stopped")

    async def get_or_generate_page(self, page_path: str,
                                   generator_func: Callable,
                                   revalidate_time: int = 60,
                                   **kwargs) -> Dict[str, Any]:
        """
        获取或生成ISR页面
        
        Args:
            page_path: 页面路径
            generator_func: 页面生成函数（异步）
            revalidate_time: 重新验证时间（秒）
            **kwargs: 传递给生成函数的参数
            
        Returns:
            页面数据和状态
        """
        # 获取或创建页面元数据
        if page_path not in self.pages:
            self.pages[page_path] = ISRPage(page_path, revalidate_time)
            self.stats['total_pages'] += 1

        page = self.pages[page_path]
        page.pending_requests += 1

        try:
            # 检查文件是否存在
            file_path = self.output_dir / page_path
            file_exists = file_path.exists()

            # 情况1: 文件不存在，需要生成
            if not file_exists:
                logger.info(f"ISR cache miss (no file): {page_path}")
                self.stats['cache_misses'] += 1
                return await self._generate_and_save(page, generator_func, **kwargs)

            # 情况2: 文件存在且未过期，直接返回
            if not page.should_revalidate():
                logger.debug(f"ISR cache hit: {page_path}")
                self.stats['cache_hits'] += 1

                # 读取文件内容
                content = await self._read_file_async(file_path)

                return {
                    'success': True,
                    'content': content,
                    'path': str(file_path),
                    'cached': True,
                    'stale': False,
                    'last_generated': page.last_generated.isoformat() if page.last_generated else None,
                    'next_revalidate': (page.last_revalidated + timedelta(
                        seconds=revalidate_time)).isoformat() if page.last_revalidated else None
                }

            # 情况3: 文件存在但已过期，触发后台重新验证
            logger.info(f"ISR stale, triggering background revalidation: {page_path}")
            self.stats['cache_hits'] += 1

            # 如果当前没有在重新生成，加入队列
            if not page.is_regenerating and self.current_revalidations < self.max_concurrent:
                await self._queue_revalidation(page, generator_func, **kwargs)

            # 立即返回旧内容（stale-while-revalidate）
            content = await self._read_file_async(file_path)

            return {
                'success': True,
                'content': content,
                'path': str(file_path),
                'cached': True,
                'stale': True,
                'is_revalidating': page.is_regenerating,
                'last_generated': page.last_generated.isoformat() if page.last_generated else None,
                'message': 'Serving stale content, revalidation in progress'
            }

        finally:
            page.pending_requests -= 1

    async def force_revalidate(self, page_path: str,
                               generator_func: Callable,
                               **kwargs) -> Dict[str, Any]:
        """
        强制重新验证页面
        
        Args:
            page_path: 页面路径
            generator_func: 页面生成函数
            **kwargs: 传递给生成函数的参数
            
        Returns:
            重新验证结果
        """
        if page_path not in self.pages:
            return {'success': False, 'error': f'Page not found: {page_path}'}

        page = self.pages[page_path]

        if page.is_regenerating:
            return {
                'success': False,
                'error': 'Page is currently being regenerated',
                'is_regenerating': True
            }

        logger.info(f"Force revalidation requested: {page_path}")
        return await self._generate_and_save(page, generator_func, **kwargs)

    async def invalidate_page(self, page_path: str) -> Dict[str, Any]:
        """
        使页面缓存失效
        
        Args:
            page_path: 页面路径
            
        Returns:
            操作结果
        """
        if page_path not in self.pages:
            return {'success': False, 'error': f'Page not found: {page_path}'}

        page = self.pages[page_path]
        file_path = self.output_dir / page_path

        # 删除文件
        if file_path.exists():
            file_path.unlink()

        # 重置页面元数据
        page.last_generated = None
        page.last_revalidated = None
        page.is_regenerating = False

        logger.info(f"Page invalidated: {page_path}")

        return {
            'success': True,
            'message': f'Page {page_path} invalidated'
        }

    async def invalidate_by_pattern(self, pattern: str) -> Dict[str, Any]:
        """
        按模式批量使页面失效
        
        Args:
            pattern: 路径模式（支持 * 通配符）
            
        Returns:
            操作结果
        """
        import fnmatch

        invalidated_count = 0

        for page_path in list(self.pages.keys()):
            if fnmatch.fnmatch(page_path, pattern):
                result = await self.invalidate_page(page_path)
                if result.get('success'):
                    invalidated_count += 1

        logger.info(f"Invalidated {invalidated_count} pages matching pattern: {pattern}")

        return {
            'success': True,
            'invalidated_count': invalidated_count,
            'pattern': pattern
        }

    def get_page_info(self, page_path: str) -> Optional[Dict[str, Any]]:
        """获取页面信息"""
        if page_path not in self.pages:
            return None

        page = self.pages[page_path]
        file_path = self.output_dir / page_path

        return {
            'path': page_path,
            'exists': file_path.exists(),
            'file_size': file_path.stat().st_size if file_path.exists() else 0,
            'revalidate_time': page.revalidate_time,
            'last_generated': page.last_generated.isoformat() if page.last_generated else None,
            'last_revalidated': page.last_revalidated.isoformat() if page.last_revalidated else None,
            'is_regenerating': page.is_regenerating,
            'pending_requests': page.pending_requests,
            'should_revalidate': page.should_revalidate(),
            'is_stale': page.is_stale()
        }

    def get_stats(self) -> Dict[str, Any]:
        """获取ISR统计信息"""
        active_pages = sum(1 for p in self.pages.values() if p.last_generated)

        return {
            **self.stats,
            'active_pages': active_pages,
            'total_tracked_pages': len(self.pages),
            'current_revalidations': self.current_revalidations,
            'queue_size': self.revalidation_queue.qsize(),
            'max_concurrent': self.max_concurrent
        }

    async def _revalidation_worker(self):
        """后台重新验证工作器"""
        while self._running:
            try:
                # 从队列获取重新验证任务
                task = await asyncio.wait_for(
                    self.revalidation_queue.get(),
                    timeout=1.0
                )

                page, generator_func, kwargs = task

                # 执行重新验证
                await self._execute_revalidation(page, generator_func, **kwargs)

                self.revalidation_queue.task_done()

            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in revalidation worker: {e}", exc_info=True)

    async def _queue_revalidation(self, page: ISRPage,
                                  generator_func: Callable,
                                  **kwargs):
        """将重新验证任务加入队列"""
        if self.current_revalidations >= self.max_concurrent:
            logger.warning(f"Revalidation queue full, skipping: {page.path}")
            return

        page.is_regenerating = True
        self.current_revalidations += 1
        self.stats['background_revalidations'] += 1

        await self.revalidation_queue.put((page, generator_func, kwargs))
        logger.debug(f"Queued revalidation: {page.path}")

    async def _execute_revalidation(self, page: ISRPage,
                                    generator_func: Callable,
                                    **kwargs):
        """执行重新验证"""
        try:
            logger.info(f"Starting revalidation: {page.path}")

            result = await self._generate_and_save(page, generator_func, **kwargs)

            if result.get('success'):
                logger.info(f"Revalidation completed: {page.path}")
            else:
                logger.error(f"Revalidation failed: {page.path} - {result.get('error')}")
                self.stats['failed_revalidations'] += 1

        except Exception as e:
            logger.error(f"Revalidation error for {page.path}: {e}", exc_info=True)
            self.stats['failed_revalidations'] += 1

        finally:
            page.is_regenerating = False
            self.current_revalidations -= 1

    async def _generate_and_save(self, page: ISRPage,
                                 generator_func: Callable,
                                 **kwargs) -> Dict[str, Any]:
        """生成并保存页面"""
        try:
            # 调用生成函数
            result = await generator_func(**kwargs)

            if not result.get('success'):
                return {
                    'success': False,
                    'error': result.get('error', 'Generation failed')
                }

            content = result.get('content', '')
            output_path = result.get('path')

            if not output_path:
                # 如果没有指定路径，使用默认路径
                output_path = self.output_dir / page.path

            # 确保父目录存在
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # 写入文件
            await self._write_file_async(output_path, content)

            # 更新页面元数据
            now = datetime.now()
            page.last_generated = now
            page.last_revalidated = now

            logger.info(f"Page generated and saved: {output_path}")

            return {
                'success': True,
                'content': content,
                'path': str(output_path),
                'cached': False,
                'stale': False,
                'last_generated': now.isoformat(),
                'next_revalidate': (now + timedelta(seconds=page.revalidate_time)).isoformat()
            }

        except Exception as e:
            logger.error(f"Error generating page {page.path}: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    async def _read_file_async(self, file_path: Path) -> str:
        """异步读取文件"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: file_path.read_text(encoding='utf-8')
        )

    async def _write_file_async(self, file_path: Path, content: str):
        """异步写入文件"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: file_path.write_text(content, encoding='utf-8')
        )


# 全局实例
isr_service = IncrementalStaticRegenerator()
