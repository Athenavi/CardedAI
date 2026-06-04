"""
翻译管理服务包
提供多语言翻译、机器翻译、翻译记忆等功能
"""

from shared.services.translation.translation_manager.i18n_service import (
    I18nService,
    i18n_service
)
from shared.services.translation.translation_manager.machine_translation import (
    MachineTranslationService,
    machine_translation_service
)
from shared.services.translation.translation_manager.translation_manager import (
    TranslationManager,
    translation_manager
)
from shared.services.translation.translation_manager.translation_memory import (
    TranslationMemoryService,
    translation_memory_service
)

__all__ = [
    # 核心类
    'TranslationManager',
    'I18nService',
    'MachineTranslationService',
    'TranslationMemoryService',

    # 全局实例
    'translation_manager',
    'i18n_service',
    'machine_translation_service',
    'translation_memory_service',
]
