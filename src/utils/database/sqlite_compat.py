# -*- coding: utf-8 -*-
"""
SQLite 方言兼容适配

解决 SQLAlchemy BigInteger 主键在 SQLite 下不自增的问题：
- SQLite 仅对 INTEGER PRIMARY KEY 自动递增
- 通过 @compiles 让 BigInteger 在 SQLite 方言下编译为 INTEGER（不影响其他方言）
- 不修改任何 ORM 模型文件，全局生效

需在模型定义 / DDL 编译之前导入：
- src/utils/database/unified_manager.py（应用路径）
- alembic_migrations/env.py（迁移路径）
"""

from sqlalchemy import BigInteger
from sqlalchemy.ext.compiler import compiles


@compiles(BigInteger, "sqlite")
def _compile_bigint_sqlite(type_, compiler, **kw):
    """SQLite 下 BigInteger 编译为 INTEGER（使主键支持自增）"""
    return "INTEGER"
