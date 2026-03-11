"""
Smart type detection and conversion for handling real-world messy data.
Handles various formats, encodings, and data quality issues.
"""
import re
import logging
from datetime import datetime
from typing import Any, Tuple, Optional, List, Dict
import pandas as pd
import numpy as np
from dateutil import parser as date_parser

logger = logging.getLogger(__name__)


class TypeDetector:
    """Intelligently detect and convert data types from real-world messy data"""

    # Common missing value representations
    MISSING_VALUES = {
        '', 'nan', 'NaN', 'null', 'Null', 'NULL', 'none', 'None', 'NONE',
        'na', 'NA', 'N/A', 'n/a', 'undefined', 'Undefined', '?', '-', '.',
        '#N/A', '#NA', 'missing', 'Missing', 'MISSING', 'empty', 'Empty'
    }

    # Boolean value mappings
    BOOLEAN_TRUE = {'true', 'True', 'TRUE', 'yes', 'Yes', 'YES', 'y', 'Y',
                    '1', 't', 'T', 'on', 'On', 'ON'}
    BOOLEAN_FALSE = {'false', 'False', 'FALSE', 'no', 'No', 'NO', 'n', 'N',
                     '0', 'f', 'F', 'off', 'Off', 'OFF'}

    @staticmethod
    def is_missing(value: Any) -> bool:
        """Check if value represents missing data"""
        if value is None or pd.isna(value):
            return True
        if isinstance(value, str):
            return value.strip() in TypeDetector.MISSING_VALUES
        return False

    @staticmethod
    def convert_to_boolean(value: Any) -> Optional[bool]:
        """Convert various boolean representations to bool"""
        if TypeDetector.is_missing(value):
            return None

        if isinstance(value, bool):
            return value

        if isinstance(value, (int, float)):
            if value == 0:
                return False
            elif value == 1:
                return True
            return None

        if isinstance(value, str):
            clean = value.strip()
            if clean in TypeDetector.BOOLEAN_TRUE:
                return True
            elif clean in TypeDetector.BOOLEAN_FALSE:
                return False

        return None

    @staticmethod
    def convert_to_numeric(value: Any) -> Optional[float]:
        """Convert various numeric representations to float"""
        if TypeDetector.is_missing(value):
            return None

        if isinstance(value, (int, float)):
            return float(value)

        if isinstance(value, str):
            clean = value.strip()

            # Remove common currency symbols and whitespace
            clean = re.sub(r'[$€£¥₹₽]', '', clean)

            # Remove percentage signs
            is_percentage = clean.endswith('%')
            if is_percentage:
                clean = clean[:-1].strip()

            # Remove commas used as thousands separator
            clean = clean.replace(',', '')

            # Try to parse as float
            try:
                num = float(clean)
                if is_percentage:
                    num = num / 100
                return num
            except ValueError:
                # Try to extract number from mixed string (e.g., "123 items")
                match = re.search(r'-?\d+\.?\d*', clean)
                if match:
                    try:
                        return float(match.group())
                    except ValueError:
                        pass

        return None

    @staticmethod
    def convert_to_date(value: Any) -> Optional[pd.Timestamp]:
        """Convert various date representations to datetime"""
        if TypeDetector.is_missing(value):
            return None

        if isinstance(value, (pd.Timestamp, datetime)):
            return pd.Timestamp(value)

        if isinstance(value, str):
            clean = value.strip()

            # Common date format patterns to try
            date_formats = [
                '%Y-%m-%d',          # 2024-01-15
                '%Y/%m/%d',          # 2024/01/15
                '%Y-%m',             # 2024-01
                '%d-%m-%Y',          # 15-01-2024
                '%d/%m/%Y',          # 15/01/2024
                '%m-%d-%Y',          # 01-15-2024
                '%m/%d/%Y',          # 01/15/2024
                '%d.%m.%Y',          # 15.01.2024
                '%Y%m%d',            # 20240115
                '%B %d, %Y',         # January 15, 2024
                '%b %d, %Y',         # Jan 15, 2024
                '%d %B %Y',          # 15 January 2024
                '%d %b %Y',          # 15 Jan 2024
                '%Y-%m-%d %H:%M:%S', # 2024-01-15 14:30:00
            ]

            # Try each format
            for fmt in date_formats:
                try:
                    return pd.Timestamp(datetime.strptime(clean, fmt))
                except ValueError:
                    continue

            # Try fuzzy parsing as last resort
            try:
                parsed = date_parser.parse(clean, dayfirst=False, fuzzy=True)
                return pd.Timestamp(parsed)
            except (ValueError, TypeError, date_parser.ParserError):
                pass

        return None

    @staticmethod
    def infer_column_type(series: pd.Series, column_name: str = "") -> Tuple[str, Dict[str, Any]]:
        """
        Intelligently infer the best type for a column.

        Returns: (type_string, metadata_dict)
        """
        # Remove missing values for analysis
        non_null = series.dropna()
        if len(non_null) == 0:
            return ("VARCHAR", {"reason": "all_missing"})

        # Count various test conversions
        numeric_count = 0
        boolean_count = 0
        date_count = 0

        test_size = min(100, len(non_null))  # Test up to 100 values
        test_sample = non_null.head(test_size)

        for val in test_sample:
            if TypeDetector.convert_to_numeric(val) is not None:
                numeric_count += 1
            if TypeDetector.convert_to_boolean(val) is not None:
                boolean_count += 1
            if TypeDetector.convert_to_date(val) is not None:
                date_count += 1

        # Determine type based on conversion success rates
        numeric_rate = numeric_count / len(test_sample) if test_sample.size > 0 else 0
        boolean_rate = boolean_count / len(test_sample) if test_sample.size > 0 else 0
        date_rate = date_count / len(test_sample) if test_sample.size > 0 else 0

        # Decision logic
        metadata = {
            "numeric_rate": numeric_rate,
            "boolean_rate": boolean_rate,
            "date_rate": date_rate,
            "unique_count": len(series.unique()),
            "null_count": series.isna().sum(),
        }

        # Date detection (highest priority)
        if date_rate > 0.7:
            metadata["reason"] = "date_detected"
            return ("DATE", metadata)

        # Boolean detection (must have high success rate AND small unique count)
        if boolean_rate > 0.8 and len(non_null.unique()) <= 4:
            metadata["reason"] = "boolean_detected"
            return ("BOOLEAN", metadata)

        # Numeric detection (check if it's actually numeric or just looks numeric)
        if numeric_rate > 0.8 and len(non_null.unique()) > 4:
            # Check for high cardinality numeric (likely float)
            all_numeric = all(TypeDetector.convert_to_numeric(v) is not None for v in test_sample)
            if all_numeric:
                # Check if all values are integers
                all_integers = all(
                    TypeDetector.convert_to_numeric(v) % 1 == 0
                    for v in test_sample
                    if TypeDetector.convert_to_numeric(v) is not None
                )
                metadata["reason"] = "integer_detected" if all_integers else "float_detected"
                return ("BIGINT" if all_integers else "FLOAT", metadata)

        # Categorical/Text detection
        unique_rate = len(non_null.unique()) / len(non_null)
        metadata["unique_rate"] = unique_rate

        # If low cardinality, it's categorical
        if len(non_null.unique()) <= 20:
            metadata["reason"] = "categorical_low_cardinality"
            return ("VARCHAR(100)", metadata)

        # Default to text
        metadata["reason"] = "text_default"
        return ("TEXT", metadata)

    @staticmethod
    def convert_value(value: Any, target_type: str) -> Tuple[Any, Optional[str]]:
        """
        Convert a value to target type.

        Returns: (converted_value, error_message_or_none)
        """
        if TypeDetector.is_missing(value):
            return (None, None)

        try:
            if target_type.upper() in ["BOOLEAN", "BOOL"]:
                converted = TypeDetector.convert_to_boolean(value)
                if converted is None:
                    return (None, f"Could not convert '{value}' to boolean")
                return (converted, None)

            elif target_type.upper() in ["DATE", "DATETIME", "TIMESTAMP"]:
                converted = TypeDetector.convert_to_date(value)
                if converted is None:
                    return (None, f"Could not parse '{value}' as date")
                return (converted, None)

            elif target_type.upper() in ["FLOAT", "DOUBLE", "DECIMAL", "NUMERIC"]:
                converted = TypeDetector.convert_to_numeric(value)
                if converted is None:
                    return (None, f"Could not convert '{value}' to number")
                return (converted, None)

            elif target_type.upper() in ["BIGINT", "INT", "INTEGER"]:
                converted = TypeDetector.convert_to_numeric(value)
                if converted is None:
                    return (None, f"Could not convert '{value}' to integer")
                try:
                    return (int(converted), None)
                except ValueError:
                    return (None, f"Could not convert '{value}' to integer")

            elif target_type.upper() in ["VARCHAR", "TEXT", "STRING"]:
                if value is None:
                    return (None, None)
                return (str(value).strip(), None)

            else:
                return (value, None)

        except Exception as e:
            return (None, str(e))


class SmartTypeConverter:
    """Apply smart type conversions to entire DataFrame"""

    @staticmethod
    def detect_encoding(file_path: str) -> str:
        """Detect file encoding"""
        import chardet

        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(100000)  # Read first 100KB
                result = chardet.detect(raw_data)
                encoding = result.get('encoding', 'utf-8')
                confidence = result.get('confidence', 0)
                logger.info(f"Detected encoding: {encoding} (confidence: {confidence})")
                return encoding or 'utf-8'
        except Exception as e:
            logger.warning(f"Could not detect encoding: {e}, using UTF-8")
            return 'utf-8'

    @staticmethod
    def detect_delimiter(file_path: str) -> str:
        """Detect CSV delimiter"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                sample = f.read(1000)

            # Common delimiters
            delimiters = [',', ';', '\t', '|']
            delimiter_counts = {d: sample.count(d) for d in delimiters}

            best_delimiter = max(delimiter_counts, key=delimiter_counts.get)
            logger.info(f"Detected delimiter: {repr(best_delimiter)}")
            return best_delimiter
        except Exception as e:
            logger.warning(f"Could not detect delimiter: {e}, using comma")
            return ','

    @staticmethod
    def read_csv_smart(file_path: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Read CSV with smart detection of encoding, delimiter, etc.

        Returns: (DataFrame, metadata_dict)
        """
        metadata = {}

        # Detect encoding
        encoding = SmartTypeConverter.detect_encoding(file_path)
        metadata['encoding'] = encoding

        # Detect delimiter
        delimiter = SmartTypeConverter.detect_delimiter(file_path)
        metadata['delimiter'] = delimiter

        # Read CSV
        try:
            df = pd.read_csv(
                file_path,
                encoding=encoding,
                sep=delimiter,
                keep_default_na=True,
                na_values=TypeDetector.MISSING_VALUES,
                dtype=str,  # Read everything as string first
                low_memory=False,
            )

            metadata['rows_read'] = len(df)
            metadata['columns_read'] = len(df.columns)
            logger.info(f"Successfully read CSV: {len(df)} rows, {len(df.columns)} columns")

            return df, metadata

        except Exception as e:
            logger.error(f"Failed to read CSV: {e}")
            raise

    @staticmethod
    def convert_types(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Convert DataFrame columns to appropriate types intelligently.

        Returns: (converted_df, type_mapping_dict)
        """
        type_mapping = {}
        conversion_issues = []

        for column in df.columns:
            logger.info(f"Analyzing column: {column}")

            # Infer type
            inferred_type, metadata = TypeDetector.infer_column_type(df[column], column)
            type_mapping[column] = {
                "inferred_type": inferred_type,
                "metadata": metadata
            }

            # Convert based on inferred type
            if inferred_type == "BOOLEAN":
                df[column] = df[column].apply(lambda x: TypeDetector.convert_to_boolean(x))

            elif inferred_type == "DATE":
                converted = []
                for value in df[column]:
                    converted_val, error = TypeDetector.convert_value(value, "DATE")
                    if error and not TypeDetector.is_missing(value):
                        conversion_issues.append({
                            "column": column,
                            "value": value,
                            "error": error
                        })
                    converted.append(converted_val)
                df[column] = converted

            elif inferred_type == "BIGINT":
                converted = []
                for value in df[column]:
                    converted_val, error = TypeDetector.convert_value(value, "BIGINT")
                    if error and not TypeDetector.is_missing(value):
                        conversion_issues.append({
                            "column": column,
                            "value": value,
                            "error": error
                        })
                    converted.append(converted_val)
                df[column] = converted

            elif inferred_type == "FLOAT":
                converted = []
                for value in df[column]:
                    converted_val, error = TypeDetector.convert_value(value, "FLOAT")
                    if error and not TypeDetector.is_missing(value):
                        conversion_issues.append({
                            "column": column,
                            "value": value,
                            "error": error
                        })
                    converted.append(converted_val)
                df[column] = converted

            else:  # TEXT/VARCHAR
                df[column] = df[column].apply(
                    lambda x: str(x).strip() if not TypeDetector.is_missing(x) else None
                )

        return df, {
            "type_mapping": type_mapping,
            "conversion_issues": conversion_issues[:50],  # Keep first 50 issues
            "total_conversion_issues": len(conversion_issues)
        }
