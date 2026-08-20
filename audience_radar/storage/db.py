from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.event import listens_for
from sqlalchemy.pool import Pool
import sqlite3
import structlog
from pathlib import Path

logger = structlog.get_logger(__name__)

DATABASE_URL = "sqlite:///data/radar.db"

def _load_sqlite_vec(dbapi_connection, connection_record):
    """Enable WAL mode and load sqlite-vec extension."""
    try:
        dbapi_connection.enable_load_extension(True)
        import sqlite_vec
        sqlite_vec.load(dbapi_connection)
    except AttributeError:
        logger.warning("sqlite_vec_load_failed", error="enable_load_extension not available on this sqlite3 build")
    except Exception as e:
        logger.warning("sqlite_vec_load_failed", error=str(e))
    finally:
        try:
            dbapi_connection.enable_load_extension(False)
        except AttributeError:
            pass
        
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()

engine = create_engine(DATABASE_URL, echo=False)
listens_for(engine, "connect")(_load_sqlite_vec)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Create data dir and db schemas if not exists."""
    Path("data").mkdir(exist_ok=True)
    from audience_radar.storage.models import Base
    Base.metadata.create_all(engine)
