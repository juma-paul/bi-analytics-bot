from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Ensure psycopg3 is used
db_url = settings.DATABASE_URL
if db_url and not db_url.startswith("postgresql+psycopg"):
    # Convert to psycopg driver if needed
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://")

# Create engine with connection pooling (optimized for serverless)
engine = create_engine(
    db_url,
    pool_size=5,  # Reduced for serverless
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,  # Recycle connections every hour
    echo=settings.DEBUG,
    connect_args={
        "connect_timeout": 10,
    },
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Dependency for FastAPI to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """Context manager for database operations"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database - create all tables and enable pgvector extension"""
    from app.models.base import Base

    # Enable pgvector extension
    with engine.begin() as conn:
        try:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            logger.info("pgvector extension enabled")
        except Exception as e:
            logger.warning(f"Could not enable pgvector: {e}")

    # Create all tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")


def get_engine():
    """Get SQLAlchemy engine"""
    return engine
