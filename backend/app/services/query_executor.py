import logging
import hashlib
import json
from typing import Dict, Any, List
from datetime import datetime, timedelta

from sqlalchemy import text, exc

from app.config import settings
from app.core.exceptions import QueryExecutionError
from app.database import get_db_context
from app.models.dataset import QueryCache, QueryHistory

logger = logging.getLogger(__name__)


class QueryExecutor:
    """Executes SQL queries with caching and error handling"""

    @staticmethod
    def execute_query(sql: str, dataset_id: str, user_question: str = None,
                     session_id: str = None) -> Dict[str, Any]:
        """
        Execute SQL query with caching

        Returns:
            dict: Query results with metadata
        """
        try:
            # Generate query hash for caching
            query_hash = QueryExecutor._hash_query(sql)

            with get_db_context() as db:
                # Check cache first
                cached_result = QueryExecutor._get_cached_result(db, dataset_id, query_hash)
                if cached_result:
                    logger.info(f"Returning cached result for query")
                    return {
                        **cached_result,
                        "cached": True,
                    }

                # Execute query
                engine = db.get_bind()
                result = engine.execute(text(sql).execution_options(timeout=settings.QUERY_TIMEOUT_SECONDS))

                # Fetch results
                rows = result.fetchall()
                columns = result.keys()

                # Format results
                results_data = {
                    "columns": list(columns),
                    "rows": [dict(zip(columns, row)) for row in rows],
                    "row_count": len(rows),
                }

                # Cache results
                QueryExecutor._cache_result(db, dataset_id, query_hash, sql, results_data)

                # Store in query history if it's a valid query
                if user_question:
                    try:
                        query_history = QueryHistory(
                            dataset_id=dataset_id,
                            user_question=user_question,
                            generated_sql=sql,
                            sql_valid=True,
                            result_row_count=len(rows),
                            session_id=session_id,
                        )
                        db.add(query_history)
                        db.commit()
                    except Exception as e:
                        logger.warning(f"Could not store query history: {str(e)}")

                logger.info(f"Query executed successfully: {len(rows)} rows returned")
                return {
                    **results_data,
                    "cached": False,
                }

        except exc.OperationalError as e:
            if "timeout" in str(e).lower():
                raise QueryExecutionError(f"Query timeout after {settings.QUERY_TIMEOUT_SECONDS} seconds")
            else:
                raise QueryExecutionError(f"Database error: {str(e)}")

        except Exception as e:
            raise QueryExecutionError(f"Query execution failed: {str(e)}")

    @staticmethod
    def _hash_query(sql: str) -> str:
        """Generate hash of normalized query for caching"""
        # Normalize query (remove extra spaces, lowercase keywords)
        normalized = ' '.join(sql.split()).upper()
        return hashlib.sha256(normalized.encode()).hexdigest()

    @staticmethod
    def _get_cached_result(db, dataset_id: str, query_hash: str) -> Dict[str, Any] or None:
        """Get cached query result if it exists and hasn't expired"""
        try:
            cache_record = db.query(QueryCache).filter(
                QueryCache.dataset_id == dataset_id,
                QueryCache.query_hash == query_hash,
                QueryCache.expires_at > datetime.utcnow(),
            ).first()

            if cache_record:
                logger.debug(f"Cache hit for query hash: {query_hash}")
                return {
                    "columns": cache_record.result_data.get("columns", []),
                    "rows": cache_record.result_data.get("rows", []),
                    "row_count": cache_record.result_data.get("row_count", 0),
                }

            return None

        except Exception as e:
            logger.warning(f"Cache retrieval failed: {str(e)}")
            return None

    @staticmethod
    def _cache_result(db, dataset_id: str, query_hash: str, sql: str, results_data: Dict[str, Any]):
        """Cache query result"""
        try:
            # Delete old cache entry if exists
            db.query(QueryCache).filter(QueryCache.query_hash == query_hash).delete()

            # Create new cache entry
            expires_at = datetime.utcnow() + timedelta(minutes=settings.CACHE_TTL_MINUTES)

            cache_record = QueryCache(
                dataset_id=dataset_id,
                query_hash=query_hash,
                sql_query=sql,
                result_data=results_data,
                expires_at=expires_at,
            )

            db.add(cache_record)
            db.commit()

            logger.debug(f"Cached query result (expires in {settings.CACHE_TTL_MINUTES} minutes)")

        except Exception as e:
            logger.warning(f"Could not cache result: {str(e)}")

    @staticmethod
    def format_results_for_response(results_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format query results for API response"""
        # Convert any non-serializable objects to strings
        formatted_rows = []
        for row in results_data.get("rows", []):
            formatted_row = {}
            for k, v in row.items():
                if isinstance(v, (str, int, float, bool, type(None))):
                    formatted_row[k] = v
                else:
                    formatted_row[k] = str(v)
            formatted_rows.append(formatted_row)

        return {
            "columns": results_data.get("columns", []),
            "rows": formatted_rows,
            "row_count": results_data.get("row_count", 0),
        }
