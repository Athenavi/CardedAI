"""
敏感词过滤服务
提供内容审核和敏感词检测功能
"""


from datetime import datetime
from typing import List, Dict, Optional, Tuple

from sqlalchemy import select, func

from shared.models.sensitive_word import SensitiveWord
from src.utils.database.unified_manager import db_manager

from src.unified_logger import default_logger as logger


class SensitiveWordService:
    """敏感词过滤服务"""

    def __init__(self):
        self._cache: Dict[str, SensitiveWord] = {}
        self._cache_loaded = False

    async def _load_cache(self):
        """加载敏感词到缓存"""
        if self._cache_loaded:
            return

        try:
            async with db_manager.get_session() as session:
                # 执行查询
                result = await session.execute(
                    select(SensitiveWord).where(SensitiveWord.is_active == True)
                )
                words = result.scalars().all()

                for word in words:
                    self._cache[word.word] = word
                self._cache_loaded = True
                logger.info(f"Loaded {len(words)} sensitive words into cache")
        except Exception as e:
            logger.error(f"Failed to load sensitive words cache: {e}")

    async def refresh_cache(self):
        """刷新缓存"""
        self._cache.clear()
        self._cache_loaded = False
        await self._load_cache()

    async def check_content(self, content: str) -> Dict:
        """
        检查内容是否包含敏感词
        
        Args:
            content: 待检查的内容
            
        Returns:
            {
                'has_sensitive': bool,  # 是否包含敏感词
                'words_found': [],  # 发现的敏感词列表
                'highest_level': 0,  # 最高敏感级别
                'actions': []  # 需要执行的操作列表
            }
        """
        if not content:
            return {
                'has_sensitive': False,
                'words_found': [],
                'highest_level': 0,
                'actions': []
            }

        await self._load_cache()

        words_found = []
        highest_level = 0
        actions = set()

        for word_str, word_obj in self._cache.items():
            if word_str in content:
                words_found.append({
                    'word': word_str,
                    'level': word_obj.level,
                    'action': word_obj.action,
                    'category': word_obj.category,
                    'replacement': word_obj.replacement
                })

                if word_obj.level > highest_level:
                    highest_level = word_obj.level

                actions.add(word_obj.action)

        return {
            'has_sensitive': len(words_found) > 0,
            'words_found': words_found,
            'highest_level': highest_level,
            'actions': list(actions)
        }

    async def filter_content(self, content: str) -> Tuple[str, List[Dict]]:
        """
        过滤内容中的敏感词
        
        Args:
            content: 原始内容
            
        Returns:
            (过滤后的内容, 发现的敏感词列表)
        """
        result = await self.check_content(content)

        if not result['has_sensitive']:
            return content, []

        filtered_content = content
        for word_info in result['words_found']:
            if word_info['action'] == 'replace' and word_info['replacement']:
                # 替换敏感词
                filtered_content = filtered_content.replace(
                    word_info['word'],
                    word_info['replacement']
                )
            elif word_info['action'] == 'block':
                # 拦截：用***替换
                filtered_content = filtered_content.replace(
                    word_info['word'],
                    '*' * len(word_info['word'])
                )

        return filtered_content, result['words_found']

    async def should_block(self, content: str) -> bool:
        """
        判断是否应该拦截内容（包含高等级敏感词）
        
        Args:
            content: 待检查的内容
            
        Returns:
            是否应该拦截
        """
        result = await self.check_content(content)

        # 如果包含任何需要拦截的敏感词，或者最高级别>=3
        if 'block' in result['actions'] or result['highest_level'] >= 3:
            return True

        return False

    async def add_sensitive_word(
            self,
            word: str,
            level: int = 1,
            action: str = 'block',
            replacement: Optional[str] = None,
            category: Optional[str] = None,
            created_by: Optional[int] = None
    ) -> SensitiveWord:
        """
        添加敏感词
        
        Args:
            word: 敏感词
            level: 敏感级别 (1-3)
            action: 处理方式 (block/replace/warn)
            replacement: 替换词
            category: 分类
            created_by: 创建者ID
            
        Returns:
            创建的敏感词对象
        """
        # 检查是否已存在
        async with db_manager.get_session() as session:
            result = await session.execute(
                select(SensitiveWord).where(SensitiveWord.word == word)
            )
            existing = result.scalar_one_or_none()

            if existing:
                raise ValueError(f"Sensitive word '{word}' already exists")

            new_word = SensitiveWord(
                word=word,
                level=level,
                action=action,
                replacement=replacement,
                category=category,
                is_active=True,
                created_by=created_by,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            session.add(new_word)
            await session.commit()
            await session.refresh(new_word)

        # 更新缓存
        self._cache[word] = new_word

        logger.info(f"Added sensitive word: {word} (level={level}, action={action})")
        return new_word

    async def remove_sensitive_word(self, word_id: int) -> bool:
        """
        删除敏感词
        
        Args:
            word_id: 敏感词ID
            
        Returns:
            是否成功删除
        """
        async with db_manager.get_session() as session:
            result = await session.execute(
                select(SensitiveWord).where(SensitiveWord.id == word_id)
            )
            word = result.scalar_one_or_none()

            if not word:
                return False

            word_str = word.word
            await session.delete(word)
            await session.commit()

        # 从缓存中移除
        if word_str in self._cache:
            del self._cache[word_str]

        logger.info(f"Removed sensitive word: {word_str}")
        return True

    async def update_sensitive_word(
            self,
            word_id: int,
            level: Optional[int] = None,
            action: Optional[str] = None,
            replacement: Optional[str] = None,
            category: Optional[str] = None,
            is_active: Optional[bool] = None
    ) -> Optional[SensitiveWord]:
        """
        更新敏感词
        
        Args:
            word_id: 敏感词ID
            level: 敏感级别
            action: 处理方式
            replacement: 替换词
            category: 分类
            is_active: 是否激活
            
        Returns:
            更新后的敏感词对象
        """
        async with db_manager.get_session() as session:
            result = await session.execute(
                select(SensitiveWord).where(SensitiveWord.id == word_id)
            )
            word = result.scalar_one_or_none()

            if not word:
                return None

            if level is not None:
                word.level = level
            if action is not None:
                word.action = action
            if replacement is not None:
                word.replacement = replacement
            if category is not None:
                word.category = category
            if is_active is not None:
                word.is_active = is_active

            word.updated_at = datetime.now()
            await session.commit()
            await session.refresh(word)

        # 更新缓存
        self._cache[word.word] = word

        return word

    async def get_sensitive_words(
            self,
            level: Optional[int] = None,
            category: Optional[str] = None,
            is_active: Optional[bool] = None,
            page: int = 1,
            per_page: int = 50
    ) -> Dict:
        """
        获取敏感词列表
        
        Args:
            level: 敏感级别筛选
            category: 分类筛选
            is_active: 激活状态筛选
            page: 页码
            per_page: 每页数量
            
        Returns:
            {
                'items': [],
                'total': int,
                'page': int,
                'per_page': int,
                'pages': int
            }
        """
        async with db_manager.get_session() as session:
            # 构建查询
            query = select(SensitiveWord)

            if level is not None:
                query = query.where(SensitiveWord.level == level)
            if category is not None:
                query = query.where(SensitiveWord.category == category)
            if is_active is not None:
                query = query.where(SensitiveWord.is_active == is_active)

            # 获取总数
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await session.execute(count_query)
            total = total_result.scalar()

            # 分页和排序
            query = query.order_by(SensitiveWord.created_at.desc())
            offset = (page - 1) * per_page
            query = query.offset(offset).limit(per_page)

            result = await session.execute(query)
            words = result.scalars().all()

            # 计算总页数
            pages = (total + per_page - 1) // per_page if per_page > 0 else 0

            return {
                'items': [word.to_dict() for word in words],
                'total': total,
                'page': page,
                'per_page': per_page,
                'pages': pages
            }

    async def batch_import_words(self, words: List[Dict], created_by: Optional[int] = None) -> Dict:
        """
        批量导入敏感词
        
        Args:
            words: 敏感词列表，每个元素为字典，包含 word, level, action, replacement, category
            created_by: 创建者ID
            
        Returns:
            {
                'success': int,  # 成功数量
                'failed': int,   # 失败数量
                'errors': []     # 错误信息列表
            }
        """
        success_count = 0
        failed_count = 0
        errors = []

        async with db_manager.get_session() as session:
            for word_data in words:
                try:
                    word = word_data.get('word', '').strip()
                    if not word:
                        failed_count += 1
                        errors.append(f"Empty word")
                        continue

                    # 检查是否已存在
                    result = await session.execute(
                        select(SensitiveWord).where(SensitiveWord.word == word)
                    )
                    existing = result.scalar_one_or_none()

                    if existing:
                        failed_count += 1
                        errors.append(f"Word '{word}' already exists")
                        continue

                    new_word = SensitiveWord(
                        word=word,
                        level=word_data.get('level', 1),
                        action=word_data.get('action', 'block'),
                        replacement=word_data.get('replacement'),
                        category=word_data.get('category'),
                        is_active=True,
                        created_by=created_by,
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )

                    session.add(new_word)
                    self._cache[word] = new_word
                    success_count += 1

                except Exception as e:
                    failed_count += 1
                    errors.append(f"Error importing '{word_data.get('word', '')}': {str(e)}")

            await session.commit()
        
        self._cache_loaded = True

        logger.info(f"Batch import: {success_count} succeeded, {failed_count} failed")
        return {
            'success': success_count,
            'failed': failed_count,
            'errors': errors
        }


# 全局实例
sensitive_word_service = SensitiveWordService()
