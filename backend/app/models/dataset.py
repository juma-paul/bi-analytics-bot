from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, Enum, ForeignKey, ARRAY, Text
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
import enum

from app.models.base import Base, TimestampMixin


class ETLStatus(str, enum.Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Dataset(Base, TimestampMixin):
    """Dataset metadata"""
    __tablename__ = "datasets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), unique=True, nullable=False, index=True)
    table_name = Column(String(255), unique=True, nullable=False)
    row_count = Column(Integer, nullable=True)
    column_count = Column(Integer, nullable=True)
    original_row_count = Column(Integer, nullable=True)
    rows_removed = Column(Integer, default=0)
    file_size_bytes = Column(Integer, nullable=True)
    upload_date = Column(DateTime, default=datetime.utcnow)
    etl_status = Column(String(50), default=ETLStatus.PROCESSING)
    data_quality_score = Column(Float, nullable=True)

    # Relationships
    columns = relationship("DatasetColumn", back_populates="dataset", cascade="all, delete-orphan")
    embeddings = relationship("DatasetEmbedding", back_populates="dataset", cascade="all, delete-orphan")
    queries = relationship("QueryHistory", back_populates="dataset", cascade="all, delete-orphan")
    cache = relationship("QueryCache", back_populates="dataset", cascade="all, delete-orphan")
    etl_logs = relationship("ETLLog", back_populates="dataset", cascade="all, delete-orphan")


class DatasetColumn(Base, TimestampMixin):
    """Column schema info with quality metrics"""
    __tablename__ = "dataset_columns"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    column_name = Column(String(255), nullable=False)
    original_column_name = Column(String(255), nullable=True)
    data_type = Column(String(50), nullable=False)
    sample_values = Column(ARRAY(String), nullable=True)
    unique_count = Column(Integer, nullable=True)
    null_count = Column(Integer, default=0)
    null_percentage = Column(Float, default=0.0)
    min_value = Column(String, nullable=True)
    max_value = Column(String, nullable=True)
    mean_value = Column(Float, nullable=True)
    median_value = Column(Float, nullable=True)
    std_dev = Column(Float, nullable=True)
    column_description = Column(Text, nullable=True)
    quality_issues = Column(ARRAY(String), default=[])
    transformations_applied = Column(ARRAY(String), default=[])

    # Relationships
    dataset = relationship("Dataset", back_populates="columns")


class DatasetEmbedding(Base, TimestampMixin):
    """Vector embeddings for RAG"""
    __tablename__ = "dataset_embeddings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    embedding = Column(String, nullable=True)  # Stored as JSON string of vector
    embedding_type = Column(String(50), nullable=False, index=True)  # 'schema', 'context', 'sample_query'
    embedding_metadata = Column(JSON, nullable=True)

    # Relationships
    dataset = relationship("Dataset", back_populates="embeddings")


class ETLLog(Base, TimestampMixin):
    """ETL processing logs"""
    __tablename__ = "etl_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    stage = Column(String(50), nullable=False, index=True)
    status = Column(String(50), nullable=False)
    message = Column(Text, nullable=True)
    rows_processed = Column(Integer, nullable=True)
    rows_affected = Column(Integer, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    error_details = Column(JSON, nullable=True)

    # Relationships
    dataset = relationship("Dataset", back_populates="etl_logs")


class QueryHistory(Base, TimestampMixin):
    """Query history for learning"""
    __tablename__ = "query_history"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    user_question = Column(Text, nullable=False)
    generated_sql = Column(Text, nullable=False)
    sql_valid = Column(Integer, default=1)
    result_row_count = Column(Integer, nullable=True)
    chart_type = Column(String(50), nullable=True)
    session_id = Column(String(100), index=True, nullable=True)

    # Relationships
    dataset = relationship("Dataset", back_populates="queries")


class QueryCache(Base, TimestampMixin):
    """Query result cache"""
    __tablename__ = "query_cache"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    query_hash = Column(String(64), unique=True, nullable=False)
    sql_query = Column(Text, nullable=False)
    result_data = Column(JSON, nullable=False)
    expires_at = Column(DateTime, nullable=True, index=True)

    # Relationships
    dataset = relationship("Dataset", back_populates="cache")
