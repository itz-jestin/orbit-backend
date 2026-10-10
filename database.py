"""
Database setup for user auth + research history.
Uses SQLite locally by default, Postgres in production via DATABASE_URL.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Falls back to local SQLite if DATABASE_URL isn't set (e.g. local dev)
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./orbit.db")

# Some providers give "postgres://", which SQLAlchemy 2.x rejects
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    # SQLite needs this connect_arg; no pooling tweaks needed locally
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
else:
    # Postgres (Neon): Neon suspends when idle and kills open connections,
    # so test each connection before use and recycle old ones.
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,   # check connection is alive; reconnect if not
        pool_recycle=300,     # replace connections older than 5 minutes
        pool_size=5,
        max_overflow=5,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
