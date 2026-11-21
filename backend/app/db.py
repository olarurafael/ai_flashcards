from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session

from app.config import get_settings


class Base(DeclarativeBase):
    pass


@lru_cache
def get_engine() -> Engine:
    # A frozen Lambda can hold a connection the server has already closed,
    # so check it before use and recycle well inside Neon's idle timeout.
    return create_engine(get_settings().sqlalchemy_url, pool_pre_ping=True, pool_recycle=300)


def get_db() -> Iterator[Session]:
    with Session(get_engine()) as session:
        yield session
