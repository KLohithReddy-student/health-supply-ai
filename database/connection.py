import logging
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from config import DATABASE_URI, DB_TYPE, SQLITE_PATH
from database.models import Base

logger = logging.getLogger(__name__)

# Configure engine with robust fallback
engine = None

def get_engine():
    global engine
    if engine is not None:
        return engine

    try:
        if DB_TYPE == "mysql":
            logger.info("Attempting connection to MySQL database...")
            test_engine = create_engine(
                DATABASE_URI,
                pool_pre_ping=True,
                pool_recycle=3600,
                connect_args={"connect_timeout": 5}
            )
            # Test connection
            with test_engine.connect() as conn:
                pass
            engine = test_engine
            logger.info("Connected successfully to MySQL database.")
            return engine
    except Exception as e:
        logger.warning(f"MySQL connection failed ({e}). Falling back to SQLite database at {SQLITE_PATH}.")

    # Fallback to SQLite
    SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
    sqlite_uri = f"sqlite:///{SQLITE_PATH.as_posix()}"
    engine = create_engine(
        sqlite_uri,
        connect_args={"check_same_thread": False}
    )
    logger.info(f"SQLite engine initialized at {SQLITE_PATH}.")
    return engine


_engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine, expire_on_commit=False)


def init_db():
    """Create all tables in the configured database."""
    eng = get_engine()
    Base.metadata.create_all(bind=eng)
    logger.info("Database schema initialized successfully.")


def reset_db():
    """Drop and recreate all tables (used for clean testing / demo seed)."""
    eng = get_engine()
    Base.metadata.drop_all(bind=eng)
    Base.metadata.create_all(bind=eng)
    logger.info("Database tables reset successfully.")


@contextmanager
def get_db():
    """Context manager for database sessions."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
