"""Custom exceptions for the application"""


class ETLException(Exception):
    """Base ETL exception"""
    pass


class FileValidationError(ETLException):
    """Raised when file validation fails"""
    pass


class DataValidationError(ETLException):
    """Raised when data validation fails"""
    pass


class DataCleaningError(ETLException):
    """Raised during data cleaning"""
    pass


class DataTransformationError(ETLException):
    """Raised during data transformation"""
    pass


class DataProfilingError(ETLException):
    """Raised during data profiling"""
    pass


class DatabaseError(ETLException):
    """Raised when database operations fail"""
    pass


class SQLGenerationError(Exception):
    """Raised when SQL generation fails"""
    pass


class QueryExecutionError(Exception):
    """Raised when query execution fails"""
    pass


class EmbeddingError(Exception):
    """Raised when embedding generation fails"""
    pass


class RAGError(Exception):
    """Raised when RAG operations fail"""
    pass
