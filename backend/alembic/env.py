"""Alembic 迁移环境配置"""
import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# 确保 backend/src 在 sys.path 中
_BACKEND_SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_SRC not in sys.path:
    sys.path.insert(0, _BACKEND_SRC)

from src.config import get_settings
from src.db.models import Base

# Alembic Config 对象
config = context.config

# 从集中化配置加载数据库 URL
_settings = get_settings()
config.set_main_option("sqlalchemy.url", _settings.DATABASE_URL)

# 日志配置
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 使用 SQLAlchemy 模型的 MetaData 支持 autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """离线模式（生成 SQL 脚本）"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """在线模式（直接执行到数据库）"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
