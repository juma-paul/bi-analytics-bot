from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class DatasetColumnSchema(BaseModel):
    """Column schema with quality metrics"""
    column_name: str
    original_column_name: Optional[str] = None
    data_type: str
    sample_values: Optional[List[str]] = None
    unique_count: Optional[int] = None
    null_count: Optional[int] = 0
    null_percentage: Optional[float] = 0.0
    min_value: Optional[str] = None
    max_value: Optional[str] = None
    mean_value: Optional[float] = None
    median_value: Optional[float] = None
    std_dev: Optional[float] = None
    column_description: Optional[str] = None
    quality_issues: List[str] = []
    transformations_applied: List[str] = []

    class Config:
        from_attributes = True


class DatasetResponse(BaseModel):
    """Dataset response with metadata"""
    id: str
    name: str
    table_name: str
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    original_row_count: Optional[int] = None
    rows_removed: Optional[int] = 0
    file_size_bytes: Optional[int] = None
    upload_date: Optional[datetime] = None
    etl_status: str
    data_quality_score: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DatasetDetailResponse(DatasetResponse):
    """Detailed dataset response with columns"""
    columns: List[DatasetColumnSchema] = []


class ETLReport(BaseModel):
    """ETL execution report"""
    dataset_id: str
    etl_status: str
    quality_score: float
    summary: Dict[str, Any]
    cleaning_report: Dict[str, Any]
    column_quality: List[Dict[str, Any]]
    transformations: List[str]
    execution_time_ms: int


class QueryRequest(BaseModel):
    """Natural language query request"""
    dataset_id: str
    question: str
    session_id: Optional[str] = None
    include_explanation: bool = True


class QueryResponse(BaseModel):
    """Query response with results and visualization"""
    query_id: str
    question: str
    generated_sql: str
    sql_explanation: Optional[str] = None
    results: Dict[str, Any]
    visualization: Optional[Dict[str, Any]] = None
    insights: List[str] = []
    execution_time_ms: int
    cached: bool = False

    class Config:
        from_attributes = True


class ChartConfig(BaseModel):
    """Chart configuration"""
    type: str
    xAxis: Optional[str] = None
    yAxis: Optional[str] = None
    title: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
