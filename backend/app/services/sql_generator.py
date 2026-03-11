import logging
import re
import os
from typing import Tuple

from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

from app.config import settings
from app.core.exceptions import SQLGenerationError
from app.core.sql_validator import SQLValidator
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)


class SQLGenerator:
    """Generates SQL queries from natural language using LLM + RAG"""

    def __init__(self):
        # Get API key from environment or settings
        api_key = os.getenv("OPENAI_API_KEY") or settings.OPENAI_API_KEY
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        self.llm = OpenAI(
            temperature=0,
            model_name=settings.OPENAI_MODEL,
            openai_api_key=api_key,
        )

        self.prompt_template = PromptTemplate(
            input_variables=["context", "question", "table_name"],
            template="""You are a PostgreSQL expert. Generate a SQL SELECT query to answer the user's question.

{context}

USER QUESTION: {question}

TABLE NAME: {table_name}

INSTRUCTIONS:
1. Generate ONLY a valid PostgreSQL SELECT query
2. Use the table name provided
3. Return ONLY the SQL query, nothing else
4. No explanation or markdown formatting

SQL:"""
        )

    def generate_sql(self, user_question: str, dataset_id: str, table_name: str) -> Tuple[str, str]:
        """
        Generate SQL query from natural language

        Returns:
            tuple: (sql_query, explanation)
        """
        try:
            # Step 1: Retrieve RAG context
            context = RAGService.retrieve_context_for_query(user_question, dataset_id)

            # Step 2: Build prompt with context
            context_text = self._build_context_text(context)

            # Step 3: Generate SQL using LLM
            llm_chain = LLMChain(llm=self.llm, prompt=self.prompt_template)
            sql_output = llm_chain.run(
                context=context_text,
                question=user_question,
                table_name=table_name,
            ).strip()

            # Step 4: Extract SQL from output (remove markdown formatting if present)
            sql_query = self._extract_sql(sql_output)

            # Step 5: Validate SQL
            is_valid, error = SQLValidator.validate_query(sql_query)
            if not is_valid:
                # Retry with error feedback
                logger.warning(f"SQL validation failed: {error}. Retrying...")
                sql_query = self._retry_sql_generation(user_question, context_text, table_name, error)

            # Step 6: Generate explanation
            explanation = self._generate_explanation(sql_query, user_question)

            logger.info(f"Generated SQL query from question: {user_question[:50]}...")
            return sql_query, explanation

        except Exception as e:
            raise SQLGenerationError(f"SQL generation failed: {str(e)}")

    def _build_context_text(self, context: dict) -> str:
        """Build context string for prompt"""
        context_parts = []

        if context.get("schema"):
            context_parts.append("SCHEMA:\n" + context["schema"])

        if context.get("dataset_info"):
            context_parts.append("DATASET INFO:\n" + context["dataset_info"])

        if context.get("similar_queries"):
            context_parts.append("\nSIMILAR SUCCESSFUL QUERIES:")
            for i, query in enumerate(context["similar_queries"][:3], 1):
                context_parts.append(f"{i}. {query['question']}\n   SQL: {query['sql']}")

        return "\n\n".join(context_parts)

    def _extract_sql(self, output: str) -> str:
        """Extract SQL from LLM output (handle markdown formatting)"""
        # Remove markdown code blocks if present
        if "```sql" in output:
            match = re.search(r'```sql\n(.*?)\n```', output, re.DOTALL)
            if match:
                return match.group(1).strip()

        if "```" in output:
            match = re.search(r'```\n(.*?)\n```', output, re.DOTALL)
            if match:
                return match.group(1).strip()

        # Return as-is if no markdown
        return output.strip()

    def _retry_sql_generation(self, question: str, context: str, table_name: str, error: str) -> str:
        """Retry SQL generation with error feedback"""
        retry_prompt = PromptTemplate(
            input_variables=["context", "question", "table_name", "error"],
            template="""You are a PostgreSQL expert. Generate a SQL SELECT query to answer the user's question.

{context}

USER QUESTION: {question}
TABLE NAME: {table_name}

PREVIOUS ATTEMPT FAILED WITH ERROR: {error}

Fix the error and generate a valid PostgreSQL SELECT query.
Return ONLY the SQL query, nothing else.

SQL:"""
        )

        try:
            llm_chain = LLMChain(llm=self.llm, prompt=retry_prompt)
            sql_output = llm_chain.run(
                context=context,
                question=question,
                table_name=table_name,
                error=error,
            ).strip()

            return self._extract_sql(sql_output)

        except Exception as e:
            logger.error(f"SQL retry generation failed: {str(e)}")
            # Return a safe fallback query
            return f"SELECT * FROM {table_name} LIMIT 10"

    def _generate_explanation(self, sql: str, question: str) -> str:
        """Generate explanation of the SQL query"""
        try:
            # Simple explanation based on SQL structure
            if "GROUP BY" in sql.upper():
                return "This query groups the data by specific columns to show aggregated results."
            elif "ORDER BY" in sql.upper():
                return "This query sorts the results by specific columns."
            elif "JOIN" in sql.upper():
                return "This query combines data from multiple tables."
            else:
                return "This query retrieves data from the table based on your criteria."

        except:
            return "This query retrieves data from the table to answer your question."
