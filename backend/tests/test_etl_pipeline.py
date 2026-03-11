"""Tests for ETL pipeline"""
import pytest
import pandas as pd
import io
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.data_validator import DataValidator
from app.services.data_cleaner import DataCleaner
from app.services.data_transformer import DataTransformer
from app.services.data_profiler import DataProfiler


@pytest.fixture
def sample_csv():
    """Create sample CSV data"""
    data = """name,age,salary,hired_date
John,30,50000.00,2020-01-15
Jane,25,60000.00,2019-03-20
Bob,35,55000.00,2021-06-10
Alice,28,65000.00,2018-11-05
Charlie,32,52000.00,2022-02-14"""
    return data.encode()


@pytest.fixture
def sample_dataframe():
    """Create sample DataFrame"""
    data = {
        'name': ['John', 'Jane', 'Bob', 'Alice', 'Charlie'],
        'age': [30, 25, 35, 28, 32],
        'salary': [50000.0, 60000.0, 55000.0, 65000.0, 52000.0],
        'hired_date': pd.to_datetime(['2020-01-15', '2019-03-20', '2021-06-10', '2018-11-05', '2022-02-14']),
    }
    return pd.DataFrame(data)


class TestDataValidator:
    """Test data validation"""

    def test_validate_csv_file(self, sample_csv):
        """Test CSV file validation"""
        is_valid, error = DataValidator.validate_file(sample_csv, "test.csv")
        assert is_valid
        assert error == ""

    def test_invalid_file_extension(self, sample_csv):
        """Test invalid file extension"""
        is_valid, error = DataValidator.validate_file(sample_csv, "test.xlsx")
        assert not is_valid
        assert "Only CSV files allowed" in error

    def test_empty_file(self):
        """Test empty file"""
        is_valid, error = DataValidator.validate_file(b"", "test.csv")
        assert not is_valid

    def test_validate_data_types(self, sample_dataframe):
        """Test data type validation"""
        report = DataValidator.validate_data_types(sample_dataframe)
        assert "columns" in report
        assert "name" in report["columns"]
        assert report["columns"]["name"]["null_count"] == 0


class TestDataCleaner:
    """Test data cleaning"""

    def test_remove_duplicates(self):
        """Test duplicate removal"""
        df = pd.DataFrame({
            'name': ['John', 'John', 'Jane'],
            'age': [30, 30, 25],
        })
        df_cleaned, report = DataCleaner.clean_data(df)
        assert len(df_cleaned) == 2  # One duplicate removed
        assert report["duplicates_removed"] == 1

    def test_handle_missing_values(self, sample_dataframe):
        """Test missing value handling"""
        df = sample_dataframe.copy()
        df.loc[0, 'age'] = None
        df_cleaned, report = DataCleaner.clean_data(df)
        # Check that nulls were filled
        assert df_cleaned['age'].isna().sum() == 0

    def test_standardize_values(self):
        """Test value standardization"""
        df = pd.DataFrame({
            'category': ['  ACTIVE  ', 'inactive', 'ACTIVE'],
        })
        df_cleaned, report = DataCleaner.clean_data(df)
        # Check standardization applied
        assert 'Standardized' in ' '.join(report['standardizations'])


class TestDataTransformer:
    """Test data transformation"""

    def test_clean_column_names(self):
        """Test column name cleaning"""
        name = "Product Name-2020"
        cleaned = DataTransformer._clean_column_name(name)
        assert cleaned == "product_name_2020"
        assert ' ' not in cleaned
        assert '-' not in cleaned

    def test_convert_types(self, sample_dataframe):
        """Test type conversion"""
        conversions = DataTransformer._convert_types(sample_dataframe)
        # Salary should be converted to numeric
        assert 'salary' in conversions

    def test_parse_dates(self, sample_dataframe):
        """Test date parsing"""
        date_parsing = DataTransformer._parse_dates(sample_dataframe)
        # Should detect date columns
        assert isinstance(date_parsing, dict)


class TestDataProfiler:
    """Test data profiling"""

    def test_profile_data(self, sample_dataframe):
        """Test data profiling"""
        profile = DataProfiler.profile_data(sample_dataframe)
        assert "dataset_info" in profile
        assert "columns" in profile
        assert "age" in profile["columns"]
        assert profile["columns"]["age"]["type"] == "int64"

    def test_calculate_quality_score(self, sample_dataframe):
        """Test quality score calculation"""
        profile = DataProfiler.profile_data(sample_dataframe)
        score = DataProfiler.calculate_quality_score(profile, 5, 5)
        assert 0 <= score <= 100

    def test_get_column_quality_report(self, sample_dataframe):
        """Test column quality reporting"""
        profile = DataProfiler.profile_data(sample_dataframe)
        quality_report = DataProfiler.get_column_quality_report(profile)
        assert len(quality_report) == len(sample_dataframe.columns)
        assert all("quality_score" in col for col in quality_report)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
