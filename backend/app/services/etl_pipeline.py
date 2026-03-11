import pandas as pd
import logging
from io import BytesIO
from typing import Dict, Any, Tuple
import time
from datetime import datetime, timedelta
import hashlib

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.exceptions import ETLException
from app.models.dataset import Dataset, DatasetColumn, ETLLog, ETLStatus
from app.database import get_db_context
from app.config import settings
from app.services.data_validator import DataValidator
from app.services.data_cleaner import DataCleaner
from app.services.data_transformer import DataTransformer
from app.services.data_profiler import DataProfiler
from app.services.schema_inference import SchemaInference
from app.services.type_detector import SmartTypeConverter

logger = logging.getLogger(__name__)


class ETLPipeline:
    """Main ETL orchestrator - 7-stage pipeline"""

    def __init__(self, file_content: bytes, filename: str, dataset_name: str):
        self.file_content = file_content
        self.filename = filename
        self.dataset_name = dataset_name
        self.start_time = time.time()
        self.etl_logs = []

    def execute(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute complete ETL pipeline

        Returns:
            tuple: (dataset_id, etl_report)
        """
        try:
            dataset_id = None

            with get_db_context() as db:
                # Create dataset record
                dataset = Dataset(
                    name=self.dataset_name,
                    table_name=self._generate_table_name(),
                    etl_status=ETLStatus.PROCESSING,
                )
                db.add(dataset)
                db.commit()
                dataset_id = dataset.id

                # Stage 1: File Validation
                self._log_stage("file_validation", "started", db, dataset_id)
                is_valid, error = DataValidator.validate_file(self.file_content, self.filename)
                if not is_valid:
                    self._log_stage("file_validation", "failed", db, dataset_id, error)
                    raise ETLException(f"File validation failed: {error}")
                self._log_stage("file_validation", "completed", db, dataset_id)

                # Load CSV with smart detection (encoding, delimiter, etc.)
                import tempfile
                import os
                with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
                    tmp.write(self.file_content)
                    tmp_path = tmp.name

                try:
                    df, csv_metadata = SmartTypeConverter.read_csv_smart(tmp_path)
                    original_row_count = len(df)
                    logger.info(f"Read CSV with smart detection: {csv_metadata}")

                    # Stage 2: Data Type Validation & Conversion
                    self._log_stage("type_validation", "started", db, dataset_id, rows_processed=original_row_count)
                    df, type_conversion_report = SmartTypeConverter.convert_types(df)
                    self._log_stage("type_validation", "completed", db, dataset_id, rows_processed=original_row_count)

                finally:
                    # Clean up temp file
                    try:
                        os.unlink(tmp_path)
                    except:
                        pass

                # Stage 3: Data Cleaning
                self._log_stage("cleaning", "started", db, dataset_id, rows_processed=original_row_count)
                df_cleaned, cleaning_report = DataCleaner.clean_data(df)
                rows_removed = original_row_count - len(df_cleaned)
                self._log_stage("cleaning", "completed", db, dataset_id, rows_affected=rows_removed)

                # Stage 4: Data Transformation
                self._log_stage("transformation", "started", db, dataset_id, rows_processed=len(df_cleaned))
                df_transformed, transform_report = DataTransformer.transform_data(df_cleaned)
                self._log_stage("transformation", "completed", db, dataset_id, rows_processed=len(df_transformed))

                # Stage 5: Data Profiling
                self._log_stage("profiling", "started", db, dataset_id, rows_processed=len(df_transformed))
                profile_report = DataProfiler.profile_data(df_transformed)
                quality_score = DataProfiler.calculate_quality_score(profile_report, original_row_count, len(df_transformed))
                self._log_stage("profiling", "completed", db, dataset_id)

                # Stage 6: Table Creation & Loading
                self._log_stage("table_creation", "started", db, dataset_id)
                schema = SchemaInference.infer_schema(df_transformed, dataset.table_name)
                self._create_table_and_load_data(df_transformed, schema, db, dataset_id)
                self._log_stage("table_creation", "completed", db, dataset_id, rows_processed=len(df_transformed))

                # Stage 7: Metadata Storage & Reporting
                self._log_stage("metadata_storage", "started", db, dataset_id)
                self._store_metadata(
                    db, dataset_id, dataset, df_transformed,
                    profile_report, cleaning_report, transform_report,
                    original_row_count, quality_score
                )
                self._log_stage("metadata_storage", "completed", db, dataset_id)

                # Update dataset status
                db.query(Dataset).filter(Dataset.id == dataset_id).update({
                    Dataset.etl_status: ETLStatus.COMPLETED,
                    Dataset.data_quality_score: quality_score,
                    Dataset.row_count: len(df_transformed),
                    Dataset.original_row_count: original_row_count,
                    Dataset.rows_removed: rows_removed,
                    Dataset.column_count: len(df_transformed.columns),
                })
                db.commit()

                # Build ETL report
                execution_time_ms = int((time.time() - self.start_time) * 1000)
                etl_report = self._build_etl_report(
                    dataset_id, quality_score, original_row_count, len(df_transformed),
                    cleaning_report, transform_report, profile_report, execution_time_ms
                )

                logger.info(f"ETL pipeline completed successfully for dataset {dataset_id}")
                return dataset_id, etl_report

        except Exception as e:
            logger.error(f"ETL pipeline failed: {str(e)}", exc_info=True)
            if dataset_id:
                with get_db_context() as db:
                    db.query(Dataset).filter(Dataset.id == dataset_id).update({
                        Dataset.etl_status: ETLStatus.FAILED
                    })
                    db.commit()
            raise

    def _generate_table_name(self) -> str:
        """Generate sanitized table name"""
        # Replace spaces and special chars with underscores
        name = self.dataset_name.lower().replace(' ', '_').replace('-', '_')
        name = ''.join(c if c.isalnum() or c == '_' else '' for c in name)
        return f"user_data_{name[:50]}"

    def _log_stage(self, stage: str, status: str, db: Session, dataset_id: str,
                   message: str = "", rows_processed: int = None, rows_affected: int = None):
        """Log ETL stage execution"""
        etl_log = ETLLog(
            dataset_id=dataset_id,
            stage=stage,
            status=status,
            message=message,
            rows_processed=rows_processed,
            rows_affected=rows_affected,
            execution_time_ms=int((time.time() - self.start_time) * 1000),
        )
        db.add(etl_log)
        db.commit()
        logger.info(f"ETL Stage {stage}: {status}")

    def _create_table_and_load_data(self, df: pd.DataFrame, schema: Dict[str, Any],
                                     db: Session, dataset_id: str):
        """Create PostgreSQL table and load data"""
        table_name = schema["table_name"]

        try:
            # Get engine from db session
            engine = db.get_bind()

            # Drop table if exists
            with engine.begin() as conn:
                conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))

            # Create table from schema
            create_sql = SchemaInference.generate_create_table_sql(schema)
            with engine.begin() as conn:
                conn.execute(text(create_sql))
                logger.info(f"Table {table_name} created")

                # Create indexes
                index_sqls = SchemaInference.get_create_indexes_sql(schema)
                for idx_sql in index_sqls:
                    conn.execute(text(idx_sql))

            # Load data using to_sql (which uses COPY command)
            df.to_sql(table_name, engine, if_exists='append', index=False)
            logger.info(f"Loaded {len(df)} rows into {table_name}")

        except Exception as e:
            raise ETLException(f"Table creation/loading failed: {str(e)}")

    def _store_metadata(self, db: Session, dataset_id: str, dataset: Dataset,
                       df: pd.DataFrame, profile_report: Dict[str, Any],
                       cleaning_report: Dict[str, Any], transform_report: Dict[str, Any],
                       original_row_count: int, quality_score: float):
        """Store column metadata and quality information"""

        for col_name in df.columns:
            if col_name in profile_report["columns"]:
                col_profile = profile_report["columns"][col_name]

                # Build quality issues list
                quality_issues = []
                if col_profile["null_percentage"] > 20:
                    quality_issues.append(f"High null percentage ({col_profile['null_percentage']:.1f}%)")

                # Build transformations list
                transformations = []
                if col_name in transform_report.get("type_conversions", {}):
                    transformations.append(transform_report["type_conversions"][col_name])
                if col_name in transform_report.get("date_parsing", {}):
                    transformations.append(transform_report["date_parsing"][col_name])

                # Create DatasetColumn record
                dataset_col = DatasetColumn(
                    dataset_id=dataset_id,
                    column_name=col_name,
                    data_type=col_profile.get("type", "VARCHAR"),
                    null_count=col_profile.get("null_count", 0),
                    null_percentage=col_profile.get("null_percentage", 0.0),
                    unique_count=col_profile.get("unique_count", 0),
                    sample_values=col_profile.get("sample_values", [])[:5],
                    quality_issues=quality_issues,
                    transformations_applied=transformations,
                )

                # Add numeric statistics if available
                if "statistics" in col_profile:
                    stats = col_profile["statistics"]
                    dataset_col.mean_value = stats.get("mean")
                    dataset_col.median_value = stats.get("median")
                    dataset_col.std_dev = stats.get("std")
                    dataset_col.min_value = str(stats.get("min"))
                    dataset_col.max_value = str(stats.get("max"))

                db.add(dataset_col)

        db.commit()
        logger.info(f"Metadata stored for {len(df.columns)} columns")

    def _build_etl_report(self, dataset_id: str, quality_score: float,
                         original_rows: int, final_rows: int,
                         cleaning_report: Dict[str, Any],
                         transform_report: Dict[str, Any],
                         profile_report: Dict[str, Any],
                         execution_time_ms: int) -> Dict[str, Any]:
        """Build comprehensive ETL report"""

        return {
            "dataset_id": dataset_id,
            "etl_status": "completed",
            "quality_score": round(quality_score, 1),
            "summary": {
                "original_rows": original_rows,
                "final_rows": final_rows,
                "rows_removed": original_rows - final_rows,
                "columns": len(profile_report["columns"]),
                "data_quality_score": round(quality_score, 1),
            },
            "cleaning_report": {
                "duplicates_removed": cleaning_report.get("duplicates_removed", 0),
                "nulls_filled": cleaning_report.get("nulls_filled", {}),
                "outliers_detected": cleaning_report.get("outliers_detected", {}),
            },
            "column_quality": DataProfiler.get_column_quality_report(profile_report),
            "transformations": transform_report.get("standardizations", []),
            "execution_time_ms": execution_time_ms,
        }
