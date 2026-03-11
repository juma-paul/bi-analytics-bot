import pandas as pd
import logging
from typing import Dict, Any, List
from sqlalchemy import (
    Column, String, Integer, Float, Date, DateTime, Boolean, Text, JSON
)

logger = logging.getLogger(__name__)


class SchemaInference:
    """Infers PostgreSQL schema from pandas DataFrame"""

    @staticmethod
    def infer_schema(df: pd.DataFrame, table_name: str) -> Dict[str, Any]:
        """
        Infer PostgreSQL schema from dataframe

        Returns:
            dict: Schema information with columns and types
        """
        schema = {
            "table_name": table_name,
            "columns": [],
            "primary_key": "id",
        }

        # Add ID column
        schema["columns"].append({
            "name": "id",
            "type": "SERIAL PRIMARY KEY",
            "nullable": False,
        })

        # Infer column types
        for col in df.columns:
            pg_type = SchemaInference._infer_pg_type(df[col])
            schema["columns"].append({
                "name": col,
                "type": pg_type,
                "nullable": True,
            })

        return schema

    @staticmethod
    def _infer_pg_type(series: pd.Series) -> str:
        """Infer PostgreSQL type for a pandas Series"""

        # Check pandas dtype
        dtype_str = str(series.dtype)

        # Handle numeric types
        if dtype_str == "int64" or dtype_str == "Int64":
            return "BIGINT"
        elif dtype_str == "int32" or dtype_str == "int16" or dtype_str == "int8":
            return "INTEGER"
        elif dtype_str == "float64" or dtype_str == "Float64":
            return "FLOAT"
        elif dtype_str == "float32" or dtype_str == "float16":
            return "FLOAT"

        # Handle boolean types
        elif dtype_str == "bool" or dtype_str == "boolean":
            return "BOOLEAN"

        # Handle datetime types (these should have been converted already)
        elif dtype_str == "datetime64[ns]" or "datetime" in dtype_str.lower():
            return "DATE"

        # Handle string/object types
        elif dtype_str == "object" or dtype_str == "string":
            # For object columns, check average string length
            non_null = series.dropna()
            if len(non_null) == 0:
                return "VARCHAR(255)"

            # Estimate average length
            try:
                avg_length = non_null.astype(str).str.len().mean()
                if avg_length > 500:
                    return "TEXT"
                else:
                    max_length = non_null.astype(str).str.len().max()
                    return f"VARCHAR({min(int(max_length * 1.2), 4000)})"
            except:
                return "VARCHAR(255)"

        else:
            return "VARCHAR(255)"

    @staticmethod
    def generate_create_table_sql(schema: Dict[str, Any]) -> str:
        """Generate CREATE TABLE SQL from schema"""

        table_name = schema["table_name"]
        sql = f"CREATE TABLE IF NOT EXISTS {table_name} (\n"

        column_defs = []
        for col in schema["columns"]:
            col_def = f"    {col['name']} {col['type']}"
            if not col.get("nullable", True):
                col_def += " NOT NULL"
            column_defs.append(col_def)

        sql += ",\n".join(column_defs)
        sql += "\n);"

        logger.info(f"Generated CREATE TABLE SQL for {table_name}")
        return sql

    @staticmethod
    def get_create_indexes_sql(schema: Dict[str, Any]) -> List[str]:
        """Generate CREATE INDEX SQL for key columns"""

        table_name = schema["table_name"]
        indexes = []

        # Create indexes for common column patterns
        for col in schema["columns"]:
            col_name = col["name"]

            # Index date columns
            if "date" in col_name.lower() or "time" in col_name.lower():
                idx_name = f"idx_{table_name}_{col_name}"
                indexes.append(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name}({col_name});")

            # Index categorical columns (VARCHAR with low cardinality assumed)
            if col["type"].startswith("VARCHAR") and col_name not in ["id"]:
                if any(x in col_name.lower() for x in ["status", "category", "type", "mode", "country", "region"]):
                    idx_name = f"idx_{table_name}_{col_name}"
                    indexes.append(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name}({col_name});")

        logger.info(f"Generated {len(indexes)} index SQL statements")
        return indexes
