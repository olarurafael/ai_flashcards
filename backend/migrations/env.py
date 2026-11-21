import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

from app import models  # noqa: F401  (registers the tables on Base.metadata)
from app.config import to_sqlalchemy_url
from app.db import Base

if context.config.config_file_name:
    fileConfig(context.config.config_file_name)

# Read DATABASE_URL directly so migrations don't need the app's other secrets.
engine = create_engine(to_sqlalchemy_url(os.environ["DATABASE_URL"]))

with engine.connect() as connection:
    context.configure(connection=connection, target_metadata=Base.metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()
