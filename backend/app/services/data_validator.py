import pandas as pd
import numpy as np
from io import BytesIO
import logging
from typing import Tuple, Dict, Any, List
from datetime import datetime

from app.core.exceptions import FileValidationError, DataValidationError
from app.config import settings

logger = logging.getLogger(__name__)


class DataValidator:
    """Validates CSV files and data types"""

    VALID_EXTENSIONS = settings.ALLOWED_EXTENSIONS

    @staticmethod
    def validate_file(file_content: bytes, filename: str) -> Tuple[bool, str]:
        """
        Stage 1: Validate file format, size, encoding, structure

        Returns:
            tuple: (is_valid, error_message)
        """
        # Check file extension
        if not filename.lower().endswith('.csv'):
            return False, f"Only CSV files allowed. Got: {filename}"

        # Check file size
        file_size_mb = len(file_content) / (1024 * 1024)
        if file_size_mb > settings.MAX_UPLOAD_SIZE_MB:
            return False, f"File size {file_size_mb:.2f}MB exceeds limit of {settings.MAX_UPLOAD_SIZE_MB}MB"

        # Try to detect encoding and read CSV
        try:
            df = pd.read_csv(BytesIO(file_content), nrows=10)
            if len(df) == 0:
                return False, "CSV file is empty"

            if len(df.columns) == 0:
                return False, "CSV has no columns"

            logger.info(f"File validation passed: {filename} ({file_size_mb:.2f}MB, {len(df)} rows)")
            return True, ""

        except Exception as e:
            return False, f"Could not read CSV file: {str(e)}"

    @staticmethod
    def validate_data_types(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Stage 2: Validate data types, consistency, nulls, duplicates

        Returns:
            dict: Validation report with detected issues and quality scores
        """
        report = {
            "columns": {},
            "global_issues": [],
            "total_rows": len(df),
            "total_cells": len(df) * len(df.columns),
        }

        # Check duplicates
        duplicate_rows = df.duplicated().sum()
        if duplicate_rows > 0:
            report["global_issues"].append(f"Found {duplicate_rows} duplicate rows ({duplicate_rows/len(df)*100:.1f}%)")

        # Analyze each column
        for col in df.columns:
            col_report = {
                "detected_type": None,
                "type_consistency": 0.0,
                "null_count": 0,
                "null_percentage": 0.0,
                "unique_count": 0,
                "issues": [],
            }

            # Count nulls
            null_count = df[col].isna().sum()
            col_report["null_count"] = int(null_count)
            col_report["null_percentage"] = float(null_count / len(df) * 100)

            # Unique values
            col_report["unique_count"] = int(df[col].nunique())

            # Try to infer type
            try:
                inferred_type = DataValidator._infer_column_type(df[col])
                col_report["detected_type"] = inferred_type

                # Check type consistency
                consistency = DataValidator._check_type_consistency(df[col], inferred_type)
                col_report["type_consistency"] = consistency

                if consistency < 80:
                    col_report["issues"].append(f"Mixed types detected ({consistency:.1f}% consistent)")

            except Exception as e:
                col_report["issues"].append(f"Could not infer type: {str(e)}")

            # Check for suspicious values
            if col_report["null_percentage"] > 50:
                col_report["issues"].append(f"Very high null percentage ({col_report['null_percentage']:.1f}%)")

            report["columns"][col] = col_report

        logger.info(f"Data validation completed: {len(report['columns'])} columns analyzed")
        return report

    @staticmethod
    def _infer_column_type(series: pd.Series) -> str:
        """Infer the data type of a column"""
        # Drop nulls for type inference
        non_null = series.dropna()

        if len(non_null) == 0:
            return "unknown"

        # Try numeric
        try:
            pd.to_numeric(non_null)
            return "numeric"
        except:
            pass

        # Try datetime
        try:
            pd.to_datetime(non_null)
            return "datetime"
        except:
            pass

        # Check if boolean
        unique_vals = set(non_null.unique())
        if unique_vals.issubset({'yes', 'no', 'true', 'false', 'y', 'n', '0', '1', 0, 1, True, False}):
            return "boolean"

        # Default to categorical/text
        if len(unique_vals) < len(non_null) * 0.1:
            return "categorical"
        else:
            return "text"

    @staticmethod
    def _check_type_consistency(series: pd.Series, detected_type: str) -> float:
        """Check what percentage of values match the detected type"""
        non_null = series.dropna()

        if len(non_null) == 0:
            return 0.0

        consistent_count = 0

        if detected_type == "numeric":
            for val in non_null:
                try:
                    float(val)
                    consistent_count += 1
                except:
                    pass

        elif detected_type == "datetime":
            for val in non_null:
                try:
                    pd.to_datetime(val)
                    consistent_count += 1
                except:
                    pass

        elif detected_type == "boolean":
            bool_vals = {'yes', 'no', 'true', 'false', 'y', 'n', '0', '1', 0, 1, True, False}
            consistent_count = sum(1 for val in non_null if val in bool_vals)

        else:
            # For text/categorical, all are consistent
            consistent_count = len(non_null)

        return float(consistent_count / len(non_null) * 100)
