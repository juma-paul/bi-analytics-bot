import re
import logging

logger = logging.getLogger(__name__)


class SQLValidator:
    """Validates SQL queries for safety and correctness"""

    DANGEROUS_KEYWORDS = [
        r'\b(INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE|EXEC|EXECUTE)\b',
        r'(;|--|/\*)',  # Statement separators and comments
    ]

    ALLOWED_FUNCTIONS = [
        'COUNT', 'SUM', 'AVG', 'MIN', 'MAX',
        'ROUND', 'FLOOR', 'CEIL',
        'LOWER', 'UPPER', 'LENGTH', 'SUBSTR',
        'CAST', 'COALESCE', 'DATE_PART', 'EXTRACT'
    ]

    @staticmethod
    def validate_query(sql: str) -> tuple[bool, str]:
        """
        Validate SQL query for safety and basic correctness

        Returns:
            tuple: (is_valid, error_message)
        """
        if not sql or not isinstance(sql, str):
            return False, "Query must be a non-empty string"

        sql_upper = sql.strip().upper()

        # Check for dangerous keywords
        for pattern in SQLValidator.DANGEROUS_KEYWORDS:
            if re.search(pattern, sql_upper, re.IGNORECASE):
                if 'INSERT' in sql_upper or 'UPDATE' in sql_upper or 'DELETE' in sql_upper:
                    return False, f"Query contains dangerous keywords. Only SELECT queries allowed."

        # Check for SELECT statement
        if not sql_upper.startswith('SELECT'):
            return False, "Query must be a SELECT statement"

        # Basic syntax check - should have FROM clause
        if ' FROM ' not in sql_upper:
            return False, "Query must contain FROM clause"

        # Check for excessive semicolons or statement separators
        if sql.count(';') > 1:
            return False, "Multiple statements not allowed"

        return True, ""

    @staticmethod
    def extract_table_name(sql: str) -> str:
        """Extract table name from SQL query"""
        match = re.search(r'FROM\s+(\w+)', sql, re.IGNORECASE)
        if match:
            return match.group(1)
        return ""

    @staticmethod
    def extract_columns(sql: str) -> list:
        """Extract referenced columns from SQL query"""
        # Simple regex - finds column names in SELECT and WHERE clauses
        pattern = r'(?:SELECT|WHERE)\s+(?:.*?\s+)?(\w+(?:\s*,\s*\w+)*)'
        matches = re.findall(pattern, sql, re.IGNORECASE)
        columns = []
        for match in matches:
            columns.extend([col.strip() for col in match.split(',')])
        return list(set(columns))
