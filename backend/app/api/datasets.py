import logging
import uuid
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.dataset import Dataset, DatasetColumn, ETLLog, DatasetEmbedding
from app.schemas.dataset import DatasetResponse, DatasetDetailResponse, ETLReport
from app.services.etl_pipeline import ETLPipeline
from app.services.embedding_service import EmbeddingService
from app.core.exceptions import ETLException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/datasets", tags=["datasets"])


@router.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    dataset_name: str = None,
    db: Session = Depends(get_db)
):
    """
    Upload CSV file and run ETL pipeline

    Returns ETL report with quality metrics
    """
    try:
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files allowed")

        # Use filename or provided name
        if not dataset_name:
            dataset_name = file.filename.replace('.csv', '')

        # Read file content
        content = await file.read()

        # Run ETL pipeline
        pipeline = ETLPipeline(content, file.filename, dataset_name)
        dataset_id, etl_report = pipeline.execute()

        # Get dataset for full response
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()

        # Generate embeddings for RAG
        profile_report = {}  # Would come from ETL, simplified here
        try:
            EmbeddingService.generate_dataset_embeddings(
                dataset_id,
                [col.column_name for col in db.query(DatasetColumn).filter(
                    DatasetColumn.dataset_id == dataset_id
                ).all()],
                profile_report
            )
        except Exception as e:
            logger.warning(f"Embedding generation failed: {str(e)}")

        return {
            "success": True,
            "dataset_id": dataset_id,
            "dataset": DatasetResponse.from_orm(dataset),
            "etl_report": etl_report,
        }

    except ETLException as e:
        logger.error(f"ETL failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Upload failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Upload failed")


@router.get("")
async def list_datasets(db: Session = Depends(get_db)):
    """List all datasets"""
    try:
        datasets = db.query(Dataset).all()
        return {
            "datasets": [DatasetResponse.from_orm(ds) for ds in datasets],
            "total": len(datasets),
        }
    except Exception as e:
        logger.error(f"List datasets failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list datasets")


@router.get("/{dataset_id}")
async def get_dataset(dataset_id: str, db: Session = Depends(get_db)):
    """Get dataset details"""
    try:
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()

        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")

        # Get columns
        columns = db.query(DatasetColumn).filter(
            DatasetColumn.dataset_id == dataset_id
        ).all()

        return DatasetDetailResponse(
            **DatasetResponse.from_orm(dataset).dict(),
            columns=[{
                "column_name": col.column_name,
                "data_type": col.data_type,
                "null_percentage": col.null_percentage,
                "unique_count": col.unique_count,
                "sample_values": col.sample_values,
            } for col in columns],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get dataset failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get dataset")


@router.get("/{dataset_id}/quality-report")
async def get_quality_report(dataset_id: str, db: Session = Depends(get_db)):
    """Get detailed quality report"""
    try:
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()

        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")

        # Get column quality info
        columns = db.query(DatasetColumn).filter(
            DatasetColumn.dataset_id == dataset_id
        ).all()

        column_quality = []
        for col in columns:
            quality = {
                "column": col.column_name,
                "type": col.data_type,
                "null_percentage": col.null_percentage,
                "unique_values": col.unique_count,
                "issues": col.quality_issues or [],
            }
            column_quality.append(quality)

        return {
            "dataset_id": dataset_id,
            "overall_quality_score": dataset.data_quality_score or 0,
            "summary": {
                "total_rows": dataset.row_count,
                "original_rows": dataset.original_row_count,
                "rows_removed": dataset.rows_removed,
                "columns": dataset.column_count,
            },
            "column_quality": column_quality,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get quality report failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get quality report")


@router.get("/{dataset_id}/etl-logs")
async def get_etl_logs(dataset_id: str, db: Session = Depends(get_db)):
    """Get ETL execution logs"""
    try:
        logs = db.query(ETLLog).filter(ETLLog.dataset_id == dataset_id).all()

        return {
            "dataset_id": dataset_id,
            "logs": [
                {
                    "stage": log.stage,
                    "status": log.status,
                    "message": log.message,
                    "rows_processed": log.rows_processed,
                    "execution_time_ms": log.execution_time_ms,
                    "timestamp": log.created_at.isoformat() if log.created_at else None,
                }
                for log in logs
            ],
        }

    except Exception as e:
        logger.error(f"Get ETL logs failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get ETL logs")


@router.get("/{dataset_id}/schema")
async def get_dataset_schema(dataset_id: str, db: Session = Depends(get_db)):
    """Get dataset schema - column information for data explorer"""
    try:
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()

        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")

        # Get columns
        columns = db.query(DatasetColumn).filter(
            DatasetColumn.dataset_id == dataset_id
        ).all()

        return {
            "dataset_id": dataset_id,
            "columns": [
                {
                    "column_name": col.column_name,
                    "data_type": col.data_type,
                    "nullable": col.null_count > 0,
                    "unique_count": col.unique_count,
                    "null_count": col.null_count,
                    "sample_values": col.sample_values or [],
                }
                for col in columns
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get schema failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get schema")


@router.get("/{dataset_id}/preview")
async def get_dataset_preview(dataset_id: str, limit: int = 10, db: Session = Depends(get_db)):
    """Get data preview - first N rows of dataset"""
    try:
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()

        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")

        # Get columns to know column names
        columns = db.query(DatasetColumn).filter(
            DatasetColumn.dataset_id == dataset_id
        ).all()
        column_names = [col.column_name for col in columns]

        # Query the dataset table
        if not column_names:
            return {"columns": [], "rows": []}

        from sqlalchemy import text
        engine = db.get_bind()

        # Build SELECT query for preview
        columns_str = ", ".join([f'"{col}"' for col in column_names])
        query = f"SELECT {columns_str} FROM {dataset.table_name} LIMIT {limit}"

        with engine.begin() as conn:
            result = conn.execute(text(query))
            rows = []
            for row in result:
                row_dict = dict(row)
                # Convert any non-serializable types
                for key, val in row_dict.items():
                    if val is None:
                        row_dict[key] = None
                    elif not isinstance(val, (str, int, float, bool)):
                        row_dict[key] = str(val)
                rows.append(row_dict)

        return {
            "columns": column_names,
            "rows": rows,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get preview failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get data preview")


@router.get("/{dataset_id}/embeddings")
async def get_dataset_embeddings(dataset_id: str, db: Session = Depends(get_db)):
    """Get embeddings for dataset"""
    try:
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()

        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")

        embeddings = db.query(DatasetEmbedding).filter(
            DatasetEmbedding.dataset_id == dataset_id
        ).all()

        return {
            "dataset_id": dataset_id,
            "embeddings": [
                {
                    "id": str(emb.id),
                    "dataset_id": str(emb.dataset_id),
                    "content": emb.content,
                    "embedding_type": emb.embedding_type,
                    "embedding_metadata": emb.embedding_metadata or {},
                    "created_at": emb.created_at.isoformat() if emb.created_at else None,
                }
                for emb in embeddings
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get embeddings failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get embeddings")


@router.delete("/{dataset_id}")
async def delete_dataset(dataset_id: str, db: Session = Depends(get_db)):
    """Delete a dataset"""
    try:
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()

        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")

        # Drop table from database
        from sqlalchemy import text
        engine = db.get_bind()
        try:
            with engine.begin() as conn:
                conn.execute(text(f"DROP TABLE IF EXISTS {dataset.table_name}"))
        except Exception as e:
            logger.warning(f"Could not drop table: {str(e)}")

        # Delete from database
        db.delete(dataset)
        db.commit()

        return {"success": True, "message": "Dataset deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete dataset failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete dataset")
