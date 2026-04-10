from logging.config import fileConfig
import sys
import os
from os.path import abspath, dirname
from sqlalchemy import engine_from_config, pool
from alembic import context
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.insert(0, dirname(dirname(abspath(__file__))))

from app.db.base import Base
from app.models import *

load_dotenv()

# Build connection string dynamically from individual env vars
user = os.getenv("DB_USER", "postgres")
password = os.getenv("DB_PASS", "")
host = os.getenv("DB_HOST", "localhost")
port = os.getenv("DB_PORT", "5432")
db_name = os.getenv("DB_NAME", "clinical_db")

SQLALCHEMY_DATABASE_URL = f"postgresql://{user}:{quote_plus(password)}@{host}:{port}/{db_name}"

config = context.config
# We must escape '%' signs as '%%' because Alembic's ConfigParser treats '%' as an interpolation character
config.set_main_option("sqlalchemy.url", SQLALCHEMY_DATABASE_URL.replace("%", "%%"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
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
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
