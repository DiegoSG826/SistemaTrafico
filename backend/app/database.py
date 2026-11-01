from datetime import UTC, datetime

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


def utcnow():
    return datetime.now(UTC)


def aware(value: datetime) -> datetime:
    # SQLite no preserva zona; el contrato de persistencia usa UTC.
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def connect(url: str):
    engine = create_engine(url, pool_pre_ping=True, **(
        {"connect_args": {"check_same_thread": False}} if url.startswith("sqlite") else
        {"connect_args": {"connect_timeout": 2}}
    ))
    if url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def sqlite_settings(dbapi, _):
            dbapi.execute("PRAGMA foreign_keys=ON")
            dbapi.execute("PRAGMA busy_timeout=5000")
    return engine, sessionmaker(engine, expire_on_commit=False)
