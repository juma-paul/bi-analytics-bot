import logging
from typing import List, Dict, Any
import statistics

from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

from app.config import settings

logger = logging.getLogger(__name__)


class InsightGenerator:
    """Generates AI insights from query results"""

    def __init__(self):
        self.llm = OpenAI(
            temperature=0.7,  # Slightly higher temperature for more insightful output
            model_name=settings.OPENAI_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
        )

        self.insight_template = PromptTemplate(
            input_variables=["question", "data_summary", "data_preview"],
            template="""Analyze the following query result and provide 2-3 key insights.

USER QUESTION: {question}

QUERY RESULTS SUMMARY:
{data_summary}

DATA PREVIEW:
{data_preview}

Provide 2-3 brief, actionable insights from this data. Focus on:
1. Key patterns or trends
2. Outliers or unusual values
3. Business implications or recommendations

Format as bullet points."""
        )

    def generate_insights(self, user_question: str, query_results: Dict[str, Any]) -> List[str]:
        """
        Generate insights from query results

        Returns:
            list: List of insight strings
        """
        try:
            # Build data summary and preview
            data_summary = self._build_data_summary(query_results)
            data_preview = self._build_data_preview(query_results)

            # Generate insights using LLM
            llm_chain = LLMChain(llm=self.llm, prompt=self.insight_template)
            insights_text = llm_chain.run(
                question=user_question,
                data_summary=data_summary,
                data_preview=data_preview,
            ).strip()

            # Parse insights from response
            insights = self._parse_insights(insights_text)

            # Add fallback insights if LLM didn't produce good output
            if len(insights) < 2:
                fallback_insights = self._generate_fallback_insights(query_results)
                insights.extend(fallback_insights)

            logger.info(f"Generated {len(insights)} insights")
            return insights[:3]  # Return top 3

        except Exception as e:
            logger.error(f"Insight generation failed: {str(e)}")
            return self._generate_fallback_insights(query_results)

    def _build_data_summary(self, query_results: Dict[str, Any]) -> str:
        """Build summary of query results"""
        columns = query_results.get("columns", [])
        rows = query_results.get("rows", [])
        row_count = len(rows)

        summary = f"Total records: {row_count}\nColumns: {', '.join(columns)}\n"

        # Add numeric statistics
        for col in columns:
            numeric_values = []
            for row in rows:
                try:
                    val = float(row.get(col))
                    numeric_values.append(val)
                except:
                    pass

            if numeric_values:
                avg = statistics.mean(numeric_values)
                min_val = min(numeric_values)
                max_val = max(numeric_values)
                summary += f"\n{col}: min={min_val:.2f}, avg={avg:.2f}, max={max_val:.2f}"

        return summary

    def _build_data_preview(self, query_results: Dict[str, Any]) -> str:
        """Build data preview for context"""
        rows = query_results.get("rows", [])[:5]  # First 5 rows

        preview = "First 5 rows:\n"
        for i, row in enumerate(rows, 1):
            preview += f"{i}. {row}\n"

        return preview

    def _parse_insights(self, insights_text: str) -> List[str]:
        """Parse insights from LLM response"""
        insights = []

        # Split by bullet points or newlines
        lines = insights_text.split('\n')

        for line in lines:
            line = line.strip()
            # Remove bullet points and numbers
            if line and line[0] in ['•', '-', '*', '1', '2', '3']:
                insight = line.lstrip('•-*123456789. ').strip()
                if insight and len(insight) > 10:
                    insights.append(insight)

        return insights

    def _generate_fallback_insights(self, query_results: Dict[str, Any]) -> List[str]:
        """Generate fallback insights when LLM fails"""
        insights = []
        rows = query_results.get("rows", [])
        columns = query_results.get("columns", [])

        if len(rows) == 0:
            return ["No data available for analysis"]

        # Insight 1: Row count
        insights.append(f"Found {len(rows)} records matching the criteria")

        # Insight 2: Column count
        if len(columns) > 0:
            insights.append(f"Results include {len(columns)} data columns: {', '.join(columns[:3])}")

        # Insight 3: Data variety
        # Count unique values in first text column
        for col in columns:
            unique_vals = set()
            for row in rows:
                val = row.get(col)
                if isinstance(val, str):
                    unique_vals.add(val)
                    if len(unique_vals) > 5:
                        break

            if len(unique_vals) > 1:
                insights.append(f"Data shows {len(unique_vals)} distinct {col} values")
                break

        return insights[:3]

    def explain_sql(self, sql_query: str) -> str:
        """Explain what a SQL query does"""
        try:
            sql_upper = sql_query.upper()

            explanation = "This query "

            # Add basic explanation
            if "COUNT" in sql_upper:
                explanation += "counts records"
            elif "SUM" in sql_upper:
                explanation += "calculates totals"
            elif "AVG" in sql_upper:
                explanation += "calculates averages"
            else:
                explanation += "retrieves data"

            if "WHERE" in sql_upper:
                explanation += " based on specific conditions"

            if "GROUP BY" in sql_upper:
                explanation += " grouped by specific columns"

            if "ORDER BY" in sql_upper:
                explanation += " sorted by specific columns"

            if "LIMIT" in sql_upper:
                explanation += " with a limited number of results"

            explanation += "."

            return explanation

        except Exception as e:
            logger.error(f"SQL explanation failed: {str(e)}")
            return "This query retrieves data from your dataset."
