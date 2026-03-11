import logging
from typing import Dict, Any, List

from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

from app.config import settings

logger = logging.getLogger(__name__)


class ChartAdvisor:
    """Recommends chart types for query results"""

    def __init__(self):
        self.llm = OpenAI(
            temperature=0,
            model_name=settings.OPENAI_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
        )

    def recommend_chart(self, query_results: Dict[str, Any], user_question: str = None) -> Dict[str, Any]:
        """
        Recommend best chart type for query results

        Returns:
            dict: Chart configuration and recommendation
        """
        try:
            columns = query_results.get("columns", [])
            rows = query_results.get("rows", [])
            row_count = len(rows)

            # Analyze data structure
            analysis = self._analyze_data_structure(columns, rows)

            # Use LLM to get recommendation
            recommendation = self._get_llm_recommendation(analysis, user_question)

            logger.info(f"Chart recommendation: {recommendation['type']}")
            return recommendation

        except Exception as e:
            logger.error(f"Chart recommendation failed: {str(e)}")
            # Return safe default
            return self._get_default_recommendation(len(columns), len(rows))

    def _analyze_data_structure(self, columns: List[str], rows: List[Dict]) -> Dict[str, Any]:
        """Analyze data structure for chart suitability"""
        analysis = {
            "column_count": len(columns),
            "row_count": len(rows),
            "column_types": {},
        }

        if len(rows) == 0:
            return analysis

        # Analyze each column
        for col in columns:
            col_type = "unknown"

            # Sample first value
            sample_val = rows[0].get(col)

            if isinstance(sample_val, (int, float)):
                col_type = "numeric"
            elif isinstance(sample_val, bool):
                col_type = "boolean"
            elif isinstance(sample_val, str):
                # Check if it looks like a date
                if any(x in sample_val.lower() for x in ['-', '/', '2023', '2024']):
                    col_type = "datetime"
                else:
                    col_type = "categorical"

            analysis["column_types"][col] = col_type

        return analysis

    def _get_llm_recommendation(self, analysis: Dict[str, Any], question: str = None) -> Dict[str, Any]:
        """Use LLM to recommend chart type"""
        try:
            col_count = analysis["column_count"]
            row_count = analysis["row_count"]
            col_types = analysis["column_types"]

            # Rule-based selection with LLM confirmation
            if row_count > 100:
                chart_type = "table"
                reason = "Too many rows for visualization"

            elif col_count == 1:
                chart_type = "card"
                reason = "Single metric"

            elif col_count == 2:
                # Check types
                types = list(col_types.values())
                if "numeric" in types and "numeric" in types:
                    chart_type = "scatter"
                    reason = "Two numeric columns"
                elif "numeric" in types:
                    chart_type = "bar"
                    reason = "Numeric and categorical data"
                else:
                    chart_type = "table"
                    reason = "Text data"

            elif "datetime" in col_types.values():
                chart_type = "line"
                reason = "Time series data"

            elif "numeric" in col_types.values():
                chart_type = "bar"
                reason = "Categorical comparison"

            else:
                chart_type = "table"
                reason = "Complex data structure"

            return {
                "type": chart_type,
                "reason": reason,
                "config": self._get_chart_config(chart_type, analysis),
            }

        except Exception as e:
            logger.warning(f"LLM recommendation failed, using default: {str(e)}")
            return self._get_default_recommendation(analysis["column_count"], analysis["row_count"])

    def _get_chart_config(self, chart_type: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Get chart configuration"""
        config = {
            "type": chart_type,
            "responsive": True,
        }

        columns = list(analysis["column_types"].keys())

        if chart_type == "bar":
            config["xAxis"] = columns[0] if columns else "category"
            config["yAxis"] = columns[1] if len(columns) > 1 else "value"
            config["title"] = "Data Comparison"

        elif chart_type == "line":
            config["xAxis"] = columns[0] if columns else "time"
            config["yAxis"] = columns[1] if len(columns) > 1 else "value"
            config["title"] = "Trend Over Time"

        elif chart_type == "pie":
            config["dimension"] = columns[0] if columns else "category"
            config["measure"] = columns[1] if len(columns) > 1 else "value"
            config["title"] = "Distribution"

        elif chart_type == "scatter":
            config["xAxis"] = columns[0] if columns else "x"
            config["yAxis"] = columns[1] if len(columns) > 1 else "y"
            config["title"] = "Correlation"

        return config

    def _get_default_recommendation(self, col_count: int, row_count: int) -> Dict[str, Any]:
        """Get default chart recommendation"""
        chart_type = "table"

        if col_count == 1 and row_count == 1:
            chart_type = "card"
        elif col_count <= 2 and row_count <= 50:
            chart_type = "bar"

        return {
            "type": chart_type,
            "reason": "Default recommendation",
            "config": {
                "type": chart_type,
                "responsive": True,
            }
        }
