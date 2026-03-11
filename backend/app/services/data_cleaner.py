import pandas as pd
import numpy as np
import logging
import re
from typing import Tuple, Dict, Any
from difflib import SequenceMatcher

from app.core.exceptions import DataCleaningError
from app.services.type_detector import TypeDetector

logger = logging.getLogger(__name__)


class DataCleaner:
    """Cleans and standardizes data with comprehensive error handling"""

    @staticmethod
    def clean_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Stage 3: Clean data - remove duplicates, handle nulls, standardize values

        Returns:
            tuple: (cleaned_dataframe, cleaning_report)
        """
        original_rows = len(df)
        report = {
            "duplicates_removed": 0,
            "duplicate_rows_removed": 0,
            "rows_affected": 0,
            "nulls_handled": {},
            "outliers_detected": {},
            "standardizations": [],
            "invalid_rows_removed": 0,
            "issues_found": [],
        }

        try:
            df_cleaned = df.copy()

            # Step 0: Handle obviously invalid rows (all nulls, completely empty)
            before_invalid = len(df_cleaned)
            df_cleaned = df_cleaned.dropna(how='all')  # Drop rows that are completely null
            invalid_removed = before_invalid - len(df_cleaned)
            if invalid_removed > 0:
                report["invalid_rows_removed"] = invalid_removed
                logger.info(f"Removed {invalid_removed} completely empty rows")

            # Step 1: Remove exact duplicates
            exact_dups = df_cleaned.duplicated().sum()
            if exact_dups > 0:
                df_cleaned = df_cleaned.drop_duplicates(keep='first')
                report["duplicates_removed"] = int(exact_dups)
                logger.info(f"Removed {exact_dups} exact duplicate rows")

            # Step 2: Detect and handle fuzzy duplicates (for small datasets)
            fuzzy_dups = DataCleaner._remove_fuzzy_duplicates(df_cleaned)
            if fuzzy_dups > 0:
                report["fuzzy_duplicates_removed"] = fuzzy_dups

            # Step 3: Handle missing values intelligently
            nulls_report = DataCleaner._handle_missing_values(df_cleaned)
            report["nulls_handled"] = nulls_report["handled"]
            if nulls_report["issues"]:
                report["issues_found"].extend(nulls_report["issues"])

            # Step 4: Detect outliers (but don't remove, just flag)
            outliers = DataCleaner._detect_outliers(df_cleaned)
            report["outliers_detected"] = outliers
            if outliers:
                logger.info(f"Detected outliers: {outliers}")

            # Step 5: Standardize and normalize values
            standardizations = DataCleaner._standardize_values(df_cleaned)
            report["standardizations"] = standardizations

            # Step 6: Validate data consistency
            validation_issues = DataCleaner._validate_data_consistency(df_cleaned)
            if validation_issues:
                report["issues_found"].extend(validation_issues)

            report["rows_affected"] = original_rows - len(df_cleaned)
            report["final_row_count"] = len(df_cleaned)

            logger.info(f"Data cleaning completed: {original_rows} -> {len(df_cleaned)} rows")
            return df_cleaned, report

        except Exception as e:
            logger.error(f"Data cleaning failed: {str(e)}", exc_info=True)
            raise DataCleaningError(f"Data cleaning failed: {str(e)}")

    @staticmethod
    def _remove_fuzzy_duplicates(df: pd.DataFrame, threshold: float = 0.95) -> int:
        """
        Remove fuzzy duplicates (rows that are very similar).
        Only for datasets with < 10000 rows to avoid performance issues.
        """
        if len(df) > 10000:
            return 0

        removed = 0
        indices_to_drop = set()

        try:
            for i in range(len(df)):
                if i in indices_to_drop:
                    continue

                for j in range(i + 1, len(df)):
                    if j in indices_to_drop:
                        continue

                    # Calculate similarity
                    similarity = 0
                    count = 0
                    for col in df.columns:
                        val_i = str(df.iloc[i][col])
                        val_j = str(df.iloc[j][col])
                        ratio = SequenceMatcher(None, val_i, val_j).ratio()
                        similarity += ratio
                        count += 1

                    avg_similarity = similarity / count if count > 0 else 0

                    if avg_similarity >= threshold:
                        indices_to_drop.add(j)
                        removed += 1

            if removed > 0:
                df.drop(df.index[list(indices_to_drop)], inplace=True)
                logger.info(f"Removed {removed} fuzzy duplicate rows")

            return removed
        except Exception as e:
            logger.warning(f"Fuzzy duplicate detection failed: {e}")
            return 0

    @staticmethod
    def _handle_missing_values(df: pd.DataFrame) -> Dict[str, Any]:
        """Handle missing values intelligently with comprehensive strategies"""
        handled = {}
        issues = []
        columns_to_drop = []

        for col in df.columns:
            null_count = df[col].isna().sum()
            if null_count == 0:
                continue

            null_percentage = (null_count / len(df)) * 100

            # Strategy 1: Drop column if >50% missing
            if null_percentage > 50:
                columns_to_drop.append(col)
                issues.append({
                    "type": "column_dropped",
                    "column": col,
                    "reason": f"{null_percentage:.1f}% missing values",
                })
                logger.warning(f"Dropping column {col}: {null_percentage:.1f}% missing")
                continue

            # Strategy 2: Drop rows with critical missing values
            if null_percentage > 30 and col in ['id', 'key', 'identifier']:
                logger.warning(f"Cannot fill {null_percentage:.1f}% nulls in key column {col}")
                continue

            # Strategy 3: Fill numeric columns
            if pd.api.types.is_numeric_dtype(df[col]):
                if null_percentage < 5:
                    # Less than 5% missing - use median
                    median_val = df[col].median()
                    if not pd.isna(median_val):
                        df[col].fillna(median_val, inplace=True)
                        handled[col] = int(null_count)
                        logger.info(f"Filled {null_count} nulls in {col} with median ({median_val})")

                elif null_percentage < 20:
                    # 5-20% missing - use mean
                    mean_val = df[col].mean()
                    if not pd.isna(mean_val):
                        df[col].fillna(mean_val, inplace=True)
                        handled[col] = int(null_count)
                        logger.info(f"Filled {null_count} nulls in {col} with mean ({mean_val:.2f})")

                else:
                    # 20-30% missing - keep as null
                    issues.append({
                        "type": "high_missing_numeric",
                        "column": col,
                        "null_percentage": null_percentage,
                        "recommendation": "Consider dropping rows with missing values in this column",
                    })

            # Strategy 4: Fill categorical columns
            else:
                if null_percentage < 5:
                    # Less than 5% missing - use mode
                    mode_val = df[col].mode()
                    fill_value = mode_val[0] if len(mode_val) > 0 else 'Unknown'
                    df[col].fillna(fill_value, inplace=True)
                    handled[col] = int(null_count)
                    logger.info(f"Filled {null_count} nulls in {col} with mode ({fill_value})")

                elif null_percentage < 20:
                    # 5-20% missing - fill with 'Unknown'
                    df[col].fillna('Unknown', inplace=True)
                    handled[col] = int(null_count)
                    logger.info(f"Filled {null_count} nulls in {col} with 'Unknown'")

                else:
                    # 20-30% missing - keep as null
                    issues.append({
                        "type": "high_missing_categorical",
                        "column": col,
                        "null_percentage": null_percentage,
                        "recommendation": "Consider dropping rows or keeping as null",
                    })

        # Drop columns with >50% missing
        if columns_to_drop:
            df.drop(columns=columns_to_drop, inplace=True)
            logger.info(f"Dropped columns: {columns_to_drop}")

        return {"handled": handled, "issues": issues}

    @staticmethod
    def _detect_outliers(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """Detect outliers using multiple methods"""
        outliers = {}

        numeric_cols = df.select_dtypes(include=[np.number]).columns

        for col in numeric_cols:
            try:
                valid_data = df[col].dropna()
                if len(valid_data) < 5:  # Need at least 5 points for outlier detection
                    continue

                # IQR method
                Q1 = valid_data.quantile(0.25)
                Q3 = valid_data.quantile(0.75)
                IQR = Q3 - Q1

                if IQR == 0:  # No spread
                    continue

                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR

                outlier_mask = ((df[col] < lower_bound) | (df[col] > upper_bound)) & df[col].notna()
                outlier_count = outlier_mask.sum()

                # Z-score method (for comparison)
                mean = valid_data.mean()
                std = valid_data.std()
                if std > 0:
                    z_scores = np.abs((valid_data - mean) / std)
                    z_outlier_count = (z_scores > 3).sum()
                else:
                    z_outlier_count = 0

                if outlier_count > 0 or z_outlier_count > 0:
                    outliers[col] = {
                        "iqr_outliers": int(outlier_count),
                        "z_score_outliers": int(z_outlier_count),
                        "lower_bound": float(lower_bound),
                        "upper_bound": float(upper_bound),
                        "mean": float(mean),
                        "std": float(std),
                    }
                    logger.info(f"Detected {outlier_count} IQR outliers in {col}")

            except Exception as e:
                logger.warning(f"Outlier detection failed for {col}: {e}")

        return outliers

    @staticmethod
    def _standardize_values(df: pd.DataFrame) -> list:
        """Standardize and normalize values"""
        standardizations = []

        for col in df.columns:
            original = df[col].copy()

            # String columns: strip whitespace, normalize case
            if df[col].dtype == 'object':
                df[col] = df[col].apply(
                    lambda x: str(x).strip().lower() if not TypeDetector.is_missing(x) else x
                )

                # Check if anything changed
                if not original.equals(df[col]):
                    standardizations.append(f"Normalized whitespace and case in '{col}'")

            # Remove special characters from strings
            if df[col].dtype == 'object':
                df[col] = df[col].apply(
                    lambda x: re.sub(r'[^\w\s-]', '', str(x)) if not TypeDetector.is_missing(x) else x
                )

        logger.info(f"Applied {len(standardizations)} value standardizations")
        return standardizations

    @staticmethod
    def _validate_data_consistency(df: pd.DataFrame) -> list:
        """Validate data consistency and flag issues"""
        issues = []

        # Check for rows where all numeric columns are null
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            all_null_numeric = df[numeric_cols].isna().all(axis=1).sum()
            if all_null_numeric > 0:
                issues.append({
                    "type": "all_numeric_null",
                    "count": int(all_null_numeric),
                    "recommendation": "Consider removing rows with all numeric values null",
                })

        # Check for rows where all categorical columns are null
        string_cols = df.select_dtypes(include=['object']).columns
        if len(string_cols) > 0:
            all_null_string = df[string_cols].isna().all(axis=1).sum()
            if all_null_string > 0:
                issues.append({
                    "type": "all_categorical_null",
                    "count": int(all_null_string),
                    "recommendation": "Consider removing rows with all categorical values null",
                })

        return issues
