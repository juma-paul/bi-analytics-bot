"""
Data transformation with smart type detection and conversion.
Handles all common data format variations and edge cases.
"""
import pandas as pd
import numpy as np
import logging
import re
from typing import Tuple, Dict, Any

from app.core.exceptions import DataTransformationError
from app.services.type_detector import TypeDetector, SmartTypeConverter

logger = logging.getLogger(__name__)


class DataTransformer:
    """Transforms and normalizes data with comprehensive error handling"""

    @staticmethod
    def transform_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Stage 4: Transform data - column names, types, dates, standardization

        Returns:
            tuple: (transformed_dataframe, transformation_report)
        """
        report = {
            "columns_cleaned": 0,
            "column_name_changes": {},
            "type_conversions": {},
            "type_inference": {},
            "date_parsing": {},
            "categorical_standardization": {},
            "transformations_applied": [],
            "issues": [],
        }

        try:
            df_transformed = df.copy()

            # Step 1: Clean column names
            original_cols = df_transformed.columns.tolist()
            df_transformed.columns = [
                DataTransformer._clean_column_name(col, idx)
                for idx, col in enumerate(df_transformed.columns)
            ]

            # Track column name changes
            for orig, new in zip(original_cols, df_transformed.columns):
                if orig != new:
                    report["column_name_changes"][orig] = new
                    report["transformations_applied"].append(f"Renamed '{orig}' -> '{new}'")

            report["columns_cleaned"] = len(df_transformed.columns)
            logger.info(f"Cleaned {len(report['column_name_changes'])} column names")

            # Step 2: Intelligently detect and convert types
            type_report = DataTransformer._smart_convert_types(df_transformed)
            report["type_conversions"] = type_report["conversions"]
            report["type_inference"] = type_report["inference"]
            if type_report["issues"]:
                report["issues"].extend(type_report["issues"])

            # Step 3: Parse and standardize dates
            date_report = DataTransformer._parse_and_standardize_dates(df_transformed)
            report["date_parsing"] = date_report["conversions"]
            if date_report["issues"]:
                report["issues"].extend(date_report["issues"])

            # Step 4: Standardize categorical values
            categorical_report = DataTransformer._standardize_categorical(df_transformed)
            report["categorical_standardization"] = categorical_report
            report["transformations_applied"].extend(categorical_report.get("transformations", []))

            logger.info(f"Data transformation completed successfully")
            return df_transformed, report

        except Exception as e:
            logger.error(f"Data transformation failed: {str(e)}", exc_info=True)
            raise DataTransformationError(f"Data transformation failed: {str(e)}")

    @staticmethod
    def _clean_column_name(name: str, index: int = 0) -> str:
        """Clean column name: lowercase, snake_case, no special chars"""
        if not isinstance(name, str):
            name = f"column_{index}"

        # Convert to lowercase
        name = name.lower().strip()

        # Replace spaces, hyphens, and dots with underscores
        name = re.sub(r'[\s\-\.]+', '_', name)

        # Remove special characters (keep alphanumeric and underscore)
        name = re.sub(r'[^\w]', '', name)

        # Remove consecutive underscores
        name = re.sub(r'_+', '_', name)

        # Remove leading/trailing underscores
        name = name.strip('_')

        # Ensure name is not empty
        if not name or not name[0].isalpha():
            name = f"col_{index}"

        return name

    @staticmethod
    def _smart_convert_types(df: pd.DataFrame) -> Dict[str, Any]:
        """Use smart type detection to convert columns"""
        conversions = {}
        inference = {}
        issues = []

        for col in df.columns:
            try:
                original_type = str(df[col].dtype)

                # Infer the best type for this column
                inferred_type, metadata = TypeDetector.infer_column_type(df[col], col)
                inference[col] = {
                    "inferred_type": inferred_type,
                    "metadata": metadata
                }

                # Convert based on inferred type
                converted = False

                if inferred_type == "BOOLEAN":
                    df[col] = df[col].apply(TypeDetector.convert_to_boolean)
                    conversions[col] = f"{original_type} -> bool"
                    converted = True

                elif inferred_type == "DATE":
                    converted_values = []
                    conversion_errors = 0
                    for value in df[col]:
                        converted_val, error = TypeDetector.convert_value(value, "DATE")
                        if error and not TypeDetector.is_missing(value):
                            conversion_errors += 1
                        converted_values.append(converted_val)
                    df[col] = converted_values
                    conversions[col] = f"{original_type} -> date"
                    converted = True
                    if conversion_errors > 0:
                        issues.append({
                            "type": "date_conversion_errors",
                            "column": col,
                            "errors": conversion_errors,
                            "recommendation": "Some values could not be parsed as dates, kept as null"
                        })

                elif inferred_type == "BIGINT":
                    converted_values = []
                    conversion_errors = 0
                    for value in df[col]:
                        converted_val, error = TypeDetector.convert_value(value, "BIGINT")
                        if error and not TypeDetector.is_missing(value):
                            conversion_errors += 1
                        converted_values.append(converted_val)
                    df[col] = converted_values
                    conversions[col] = f"{original_type} -> int64"
                    converted = True
                    if conversion_errors > 0:
                        issues.append({
                            "type": "integer_conversion_errors",
                            "column": col,
                            "errors": conversion_errors,
                            "recommendation": "Some values could not be converted to integers, kept as null"
                        })

                elif inferred_type == "FLOAT":
                    converted_values = []
                    conversion_errors = 0
                    for value in df[col]:
                        converted_val, error = TypeDetector.convert_value(value, "FLOAT")
                        if error and not TypeDetector.is_missing(value):
                            conversion_errors += 1
                        converted_values.append(converted_val)
                    df[col] = converted_values
                    conversions[col] = f"{original_type} -> float64"
                    converted = True
                    if conversion_errors > 0:
                        issues.append({
                            "type": "float_conversion_errors",
                            "column": col,
                            "errors": conversion_errors,
                            "recommendation": "Some values could not be converted to floats, kept as null"
                        })

                else:  # TEXT/VARCHAR
                    # Ensure strings are cleaned
                    df[col] = df[col].apply(
                        lambda x: str(x).strip() if not TypeDetector.is_missing(x) else None
                    )
                    conversions[col] = f"{original_type} -> string"
                    converted = True

                if converted:
                    logger.info(f"Converted {col}: {original_type} -> {inferred_type}")

            except Exception as e:
                logger.warning(f"Failed to convert {col}: {e}")
                issues.append({
                    "type": "conversion_failed",
                    "column": col,
                    "error": str(e),
                })

        return {
            "conversions": conversions,
            "inference": inference,
            "issues": issues
        }

    @staticmethod
    def _parse_and_standardize_dates(df: pd.DataFrame) -> Dict[str, Any]:
        """Parse and standardize date columns"""
        conversions = {}
        issues = []

        # Identify date-like columns
        date_keywords = ['date', 'time', 'month', 'year', 'period', 'created', 'updated', 'born', 'start', 'end']
        date_cols = [col for col in df.columns if any(kw in col.lower() for kw in date_keywords)]

        for col in date_cols:
            try:
                if pd.api.types.is_datetime64_any_dtype(df[col]):
                    # Already datetime
                    df[col] = pd.to_datetime(df[col]).dt.strftime('%Y-%m-%d')
                    conversions[col] = "Standardized to ISO format (YYYY-MM-DD)"
                    logger.info(f"Standardized date column {col}")

                elif df[col].dtype == 'object':
                    # Try to parse as dates
                    parsed_dates = []
                    parse_errors = 0

                    for value in df[col]:
                        converted_val, error = TypeDetector.convert_value(value, "DATE")
                        if error and not TypeDetector.is_missing(value):
                            parse_errors += 1
                        if converted_val is not None:
                            parsed_dates.append(str(converted_val.date()))
                        else:
                            parsed_dates.append(None)

                    df[col] = parsed_dates
                    conversions[col] = "Parsed and standardized to ISO format (YYYY-MM-DD)"

                    if parse_errors > 0:
                        issues.append({
                            "type": "date_parse_errors",
                            "column": col,
                            "errors": parse_errors,
                            "recommendation": "Some date values could not be parsed"
                        })

                    logger.info(f"Parsed {col} with {parse_errors} conversion errors")

            except Exception as e:
                logger.warning(f"Failed to parse dates in {col}: {e}")
                issues.append({
                    "type": "date_parsing_failed",
                    "column": col,
                    "error": str(e),
                })

        return {"conversions": conversions, "issues": issues}

    @staticmethod
    def _standardize_categorical(df: pd.DataFrame) -> Dict[str, Any]:
        """Standardize categorical columns"""
        report = {
            "columns_processed": 0,
            "transformations": [],
            "standardizations": {}
        }

        object_cols = df.select_dtypes(include=['object']).columns

        for col in object_cols:
            try:
                unique_before = df[col].nunique()

                # Clean and standardize
                df[col] = df[col].apply(
                    lambda x: str(x).strip().lower() if not TypeDetector.is_missing(x) else None
                )

                # Remove extra whitespace and special chars (but keep reasonable names)
                df[col] = df[col].apply(
                    lambda x: re.sub(r'\s+', ' ', str(x)).strip() if x else None
                )

                unique_after = df[col].nunique()

                if unique_before != unique_after:
                    reduction = unique_before - unique_after
                    report["standardizations"][col] = {
                        "before": int(unique_before),
                        "after": int(unique_after),
                        "reduction": int(reduction)
                    }
                    report["transformations"].append(
                        f"Standardized '{col}': {unique_before} -> {unique_after} unique values"
                    )
                    logger.info(f"Standardized categorical {col}: {unique_before} -> {unique_after}")

                report["columns_processed"] += 1

            except Exception as e:
                logger.warning(f"Failed to standardize {col}: {e}")

        return report
