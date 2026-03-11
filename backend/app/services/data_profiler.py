import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List

from app.core.exceptions import DataProfilingError

logger = logging.getLogger(__name__)


class DataProfiler:
    """Profiles data and computes quality metrics"""

    @staticmethod
    def profile_data(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Stage 5: Profile data - statistics, distributions, quality score

        Returns:
            dict: Comprehensive profile report
        """
        try:
            profile = {
                "dataset_info": {
                    "total_rows": len(df),
                    "total_columns": len(df.columns),
                    "total_cells": len(df) * len(df.columns),
                    "memory_usage_mb": df.memory_usage(deep=True).sum() / (1024 * 1024),
                },
                "columns": {},
            }

            # Profile each column
            for col in df.columns:
                col_profile = DataProfiler._profile_column(df[col], col)
                profile["columns"][col] = col_profile

            logger.info(f"Data profiling completed: {len(df.columns)} columns profiled")
            return profile

        except Exception as e:
            raise DataProfilingError(f"Data profiling failed: {str(e)}")

    @staticmethod
    def _profile_column(series: pd.Series, col_name: str) -> Dict[str, Any]:
        """Profile a single column"""
        profile = {
            "name": col_name,
            "type": str(series.dtype),
            "non_null_count": len(series) - series.isna().sum(),
            "null_count": series.isna().sum(),
            "null_percentage": float(series.isna().sum() / len(series) * 100),
            "unique_count": series.nunique(),
            "unique_percentage": float(series.nunique() / len(series) * 100),
        }

        # Get sample values
        profile["sample_values"] = series.dropna().head(5).tolist()

        # Numeric statistics
        if pd.api.types.is_numeric_dtype(series):
            non_null = series.dropna()
            if len(non_null) > 0:
                profile["statistics"] = {
                    "count": len(non_null),
                    "mean": float(non_null.mean()),
                    "median": float(non_null.median()),
                    "mode": float(non_null.mode()[0]) if len(non_null.mode()) > 0 else None,
                    "std": float(non_null.std()),
                    "variance": float(non_null.var()),
                    "min": float(non_null.min()),
                    "max": float(non_null.max()),
                    "q25": float(non_null.quantile(0.25)),
                    "q50": float(non_null.quantile(0.50)),
                    "q75": float(non_null.quantile(0.75)),
                    "skewness": float(non_null.skew()),
                    "kurtosis": float(non_null.kurtosis()),
                }

        # Categorical statistics
        elif pd.api.types.is_object_dtype(series):
            non_null = series.dropna()
            if len(non_null) > 0:
                value_counts = non_null.value_counts()
                profile["top_values"] = value_counts.head(10).to_dict()
                profile["cardinality_ratio"] = float(series.nunique() / len(series))

        return profile

    @staticmethod
    def calculate_quality_score(profile: Dict[str, Any], original_row_count: int, final_row_count: int) -> float:
        """
        Calculate overall data quality score (0-100)

        Factors:
        - Completeness (nulls)
        - Validity (type consistency)
        - Consistency (standardization)
        - Uniqueness (duplicates)
        """
        scores = []

        # Completeness: percentage of non-null cells
        total_cells = profile["dataset_info"]["total_cells"]
        null_cells = sum(col["null_count"] for col in profile["columns"].values())
        completeness_score = max(0, 100 - (null_cells / total_cells * 100))
        scores.append(completeness_score)

        # Uniqueness: based on duplicate removal
        if original_row_count > 0:
            uniqueness_score = (final_row_count / original_row_count) * 100
            scores.append(uniqueness_score)

        # Validity: assumed based on type consistency (simplified)
        validity_score = 90.0  # Default to 90% if we got here
        scores.append(validity_score)

        # Consistency: based on standardization
        consistency_score = 85.0  # Assume good standardization
        scores.append(consistency_score)

        # Calculate weighted average
        weights = [0.30, 0.25, 0.25, 0.20]  # Completeness, Uniqueness, Validity, Consistency
        final_score = sum(score * weight for score, weight in zip(scores, weights))

        logger.info(f"Quality score calculated: {final_score:.1f}/100")
        return float(final_score)

    @staticmethod
    def get_column_quality_report(profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate quality report for each column"""
        quality_report = []

        for col_name, col_profile in profile["columns"].items():
            col_quality = {
                "column": col_name,
                "type": col_profile["type"],
                "null_percentage": col_profile["null_percentage"],
                "unique_values": col_profile["unique_count"],
                "quality_score": 100.0,  # Default to excellent
                "issues": [],
            }

            # Check for issues
            if col_profile["null_percentage"] > 50:
                col_quality["quality_score"] -= 30
                col_quality["issues"].append(f"High null percentage ({col_profile['null_percentage']:.1f}%)")

            elif col_profile["null_percentage"] > 20:
                col_quality["quality_score"] -= 10
                col_quality["issues"].append(f"Moderate null percentage ({col_profile['null_percentage']:.1f}%)")

            if col_profile["unique_percentage"] < 1:
                col_quality["quality_score"] -= 5
                col_quality["issues"].append("Very low cardinality")

            # Check for numeric outliers
            if "statistics" in col_profile:
                mean = col_profile["statistics"]["mean"]
                std = col_profile["statistics"]["std"]
                if std > mean * 2:  # High variability
                    col_quality["issues"].append("High variability in values")

            # Ensure score is between 0 and 100
            col_quality["quality_score"] = max(0, min(100, col_quality["quality_score"]))

            quality_report.append(col_quality)

        return quality_report
