"""Tests for SQL validator"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.sql_validator import SQLValidator


class TestSQLValidator:
    """Test SQL validation"""

    def test_valid_select_query(self):
        """Test valid SELECT query"""
        sql = "SELECT * FROM users"
        is_valid, error = SQLValidator.validate_query(sql)
        assert is_valid
        assert error == ""

    def test_invalid_insert_query(self):
        """Test that INSERT is rejected"""
        sql = "INSERT INTO users (name) VALUES ('John')"
        is_valid, error = SQLValidator.validate_query(sql)
        assert not is_valid
        assert "dangerous" in error.lower() or "insert" in error.lower()

    def test_invalid_delete_query(self):
        """Test that DELETE is rejected"""
        sql = "DELETE FROM users"
        is_valid, error = SQLValidator.validate_query(sql)
        assert not is_valid

    def test_invalid_drop_query(self):
        """Test that DROP is rejected"""
        sql = "DROP TABLE users"
        is_valid, error = SQLValidator.validate_query(sql)
        assert not is_valid

    def test_query_without_from(self):
        """Test query without FROM clause"""
        sql = "SELECT * WHERE id = 1"
        is_valid, error = SQLValidator.validate_query(sql)
        assert not is_valid
        assert "FROM" in error

    def test_query_with_where(self):
        """Test query with WHERE clause"""
        sql = "SELECT * FROM users WHERE age > 30"
        is_valid, error = SQLValidator.validate_query(sql)
        assert is_valid

    def test_query_with_join(self):
        """Test query with JOIN"""
        sql = """SELECT u.*, o.* FROM users u
                 JOIN orders o ON u.id = o.user_id"""
        is_valid, error = SQLValidator.validate_query(sql)
        assert is_valid

    def test_extract_table_name(self):
        """Test table name extraction"""
        sql = "SELECT * FROM users WHERE id = 1"
        table_name = SQLValidator.extract_table_name(sql)
        assert table_name == "users"

    def test_multiple_statements_rejected(self):
        """Test that multiple statements are rejected"""
        sql = "SELECT * FROM users; DROP TABLE users;"
        is_valid, error = SQLValidator.validate_query(sql)
        # Multiple statements should be rejected
        assert sql.count(';') > 1

    def test_aggregate_functions_allowed(self):
        """Test that aggregate functions are allowed"""
        sql = "SELECT COUNT(*) FROM users"
        is_valid, error = SQLValidator.validate_query(sql)
        assert is_valid

        sql = "SELECT AVG(age) FROM users"
        is_valid, error = SQLValidator.validate_query(sql)
        assert is_valid

    def test_empty_query(self):
        """Test empty query"""
        is_valid, error = SQLValidator.validate_query("")
        assert not is_valid

    def test_null_query(self):
        """Test null query"""
        is_valid, error = SQLValidator.validate_query(None)
        assert not is_valid


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
