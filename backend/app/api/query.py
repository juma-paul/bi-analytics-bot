import logging
import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid

from app.database import get_db
from app.models.dataset import Dataset
from app.schemas.dataset import QueryRequest, QueryResponse
from app.services.sql_generator import SQLGenerator
from app.services.query_executor import QueryExecutor
from app.services.chart_advisor import ChartAdvisor
from app.services.insight_generator import InsightGenerator
from app.core.exceptions import SQLGenerationError, QueryExecutionError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/query", tags=["queries"])

# Services will be lazily initialized
_sql_generator = None
_chart_advisor = None
_insight_generator = None


def get_sql_generator():
    global _sql_generator
    if _sql_generator is None:
        _sql_generator = SQLGenerator()
    return _sql_generator


def get_chart_advisor():
    global _chart_advisor
    if _chart_advisor is None:
        _chart_advisor = ChartAdvisor()
    return _chart_advisor


def get_insight_generator():
    global _insight_generator
    if _insight_generator is None:
        _insight_generator = InsightGenerator()
    return _insight_generator


@router.post("")
async def execute_query(
    request: QueryRequest,
    db: Session = Depends(get_db)
):
    """
    Execute natural language query on dataset

    Returns results, visualization, and insights
    """
    start_time = time.time()

    try:
        # Verify dataset exists
        dataset = db.query(Dataset).filter(Dataset.id == request.dataset_id).first()
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")

        # Step 1: Generate SQL from natural language
        try:
            sql_query, sql_explanation = get_sql_generator().generate_sql(
                request.question,
                request.dataset_id,
                dataset.table_name
            )
        except SQLGenerationError as e:
            raise HTTPException(status_code=400, detail=f"SQL generation failed: {str(e)}")

        # Step 2: Execute SQL query
        try:
            results = QueryExecutor.execute_query(
                sql_query,
                request.dataset_id,
                request.question,
                request.session_id
            )
        except QueryExecutionError as e:
            raise HTTPException(status_code=400, detail=f"Query execution failed: {str(e)}")

        # Step 3: Recommend chart
        chart_recommendation = get_chart_advisor().recommend_chart(results, request.question)

        # Step 4: Generate insights
        insights = []
        if request.include_explanation:
            insights = get_insight_generator().generate_insights(request.question, results)

        # Calculate execution time
        execution_time_ms = int((time.time() - start_time) * 1000)

        # Build response
        response = QueryResponse(
            query_id=str(uuid.uuid4()),
            question=request.question,
            generated_sql=sql_query,
            sql_explanation=sql_explanation if request.include_explanation else None,
            results=QueryExecutor.format_results_for_response(results),
            visualization=chart_recommendation,
            insights=insights,
            execution_time_ms=execution_time_ms,
            cached=results.get("cached", False),
        )

        logger.info(f"Query executed: {execution_time_ms}ms")
        return response.dict()

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Query execution failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Query execution failed")


@router.get("/history")
async def get_query_history(
    dataset_id: str,
    session_id: str = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get query history for a dataset/session"""
    try:
        from app.models.dataset import QueryHistory

        query = db.query(QueryHistory).filter(QueryHistory.dataset_id == dataset_id)

        if session_id:
            query = query.filter(QueryHistory.session_id == session_id)

        histories = query.order_by(QueryHistory.created_at.desc()).limit(limit).all()

        return {
            "queries": [
                {
                    "id": h.id,
                    "question": h.user_question,
                    "sql": h.generated_sql,
                    "timestamp": h.created_at.isoformat() if h.created_at else None,
                    "row_count": h.result_row_count,
                }
                for h in histories
            ],
            "total": len(histories),
        }

    except Exception as e:
        logger.error(f"Get query history failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get query history")


@router.post("/explain")
async def explain_query(
    query_id: str,
    explain_type: str = "sql"
):
    """
    Get explanation of a query

    explain_type: 'sql' | 'insights'
    """
    try:
        if explain_type == "sql":
            return {
                "explanation": insight_generator.explain_sql("SELECT * FROM table")
            }
        else:
            return {
                "explanation": "No additional insights available"
            }

    except Exception as e:
        logger.error(f"Explain query failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to explain query")
