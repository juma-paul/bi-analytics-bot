import logging
from typing import List, Dict, Any

from app.database import get_db_context
from app.models.dataset import DatasetEmbedding, DatasetColumn, QueryHistory
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class RAGService:
    """Retrieval-Augmented Generation service for context retrieval"""

    @staticmethod
    def retrieve_context_for_query(user_question: str, dataset_id: str) -> Dict[str, Any]:
        """
        Retrieve relevant context for a user question

        Returns context about schema, similar queries, and data info
        """
        try:
            context = {
                "schema": "",
                "similar_queries": [],
                "dataset_info": "",
            }

            with get_db_context() as db:
                # 1. Get schema context
                schema_embedding = db.query(DatasetEmbedding).filter(
                    DatasetEmbedding.dataset_id == dataset_id,
                    DatasetEmbedding.embedding_type == "schema"
                ).first()

                if schema_embedding:
                    context["schema"] = schema_embedding.content

                # 2. Get similar queries from history
                recent_queries = db.query(QueryHistory).filter(
                    QueryHistory.dataset_id == dataset_id
                ).order_by(QueryHistory.created_at.desc()).limit(5).all()

                for query in recent_queries:
                    if query.sql_valid:
                        context["similar_queries"].append({
                            "question": query.user_question,
                            "sql": query.generated_sql,
                        })

                # 3. Get column information for LLM prompt
                columns = db.query(DatasetColumn).filter(
                    DatasetColumn.dataset_id == dataset_id
                ).all()

                column_info = []
                for col in columns:
                    col_info = f"{col.column_name} ({col.data_type})"
                    if col.sample_values:
                        col_info += f" - Examples: {', '.join(str(v) for v in col.sample_values[:3])}"
                    column_info.append(col_info)

                context["dataset_info"] = "Column Information:\n" + "\n".join(column_info)

                logger.info(f"Retrieved context for query in dataset {dataset_id}")
                return context

        except Exception as e:
            logger.error(f"Context retrieval failed: {str(e)}")
            return {
                "schema": "",
                "similar_queries": [],
                "dataset_info": "",
            }

    @staticmethod
    def build_sql_generation_prompt(user_question: str, context: Dict[str, Any], table_name: str) -> str:
        """Build prompt for SQL generation with RAG context"""

        prompt = f"""You are a PostgreSQL expert. Your task is to generate a SQL SELECT query to answer the user's question.

SCHEMA INFORMATION:
{context.get('schema', '')}

DATASET INFORMATION:
{context.get('dataset_info', '')}

EXAMPLE QUERIES:
"""

        for i, example in enumerate(context.get('similar_queries', [])[:3], 1):
            prompt += f"\n{i}. Question: {example['question']}\n   SQL: {example['sql']}"

        prompt += f"""

USER QUESTION: {user_question}

INSTRUCTIONS:
1. Generate a valid PostgreSQL SELECT query
2. Use the table name: {table_name}
3. Only return the SQL query, no explanation
4. Use the schema information provided above
5. If the question references columns, use the actual column names from the schema
6. Make sure the query is syntactically correct

SQL Query:"""

        return prompt

    @staticmethod
    def store_successful_query(dataset_id: str, question: str, generated_sql: str, session_id: str = None):
        """Store successful query for future RAG context"""
        try:
            from app.models.dataset import QueryHistory

            with get_db_context() as db:
                query_record = QueryHistory(
                    dataset_id=dataset_id,
                    user_question=question,
                    generated_sql=generated_sql,
                    sql_valid=True,
                    session_id=session_id,
                )
                db.add(query_record)
                db.commit()

                logger.info(f"Stored successful query for future context")

        except Exception as e:
            logger.error(f"Failed to store query: {str(e)}")

    @staticmethod
    def get_table_statistics(dataset_id: str, table_name: str) -> Dict[str, Any]:
        """Get table statistics for context"""
        try:
            from sqlalchemy import text

            with get_db_context() as db:
                # Get row count
                result = db.execute(text(f"SELECT COUNT(*) as row_count FROM {table_name}")).first()
                row_count = result[0] if result else 0

                # Get column count from database
                columns = db.query(DatasetColumn).filter(
                    DatasetColumn.dataset_id == dataset_id
                ).all()

                return {
                    "row_count": row_count,
                    "column_count": len(columns),
                    "table_name": table_name,
                }

        except Exception as e:
            logger.error(f"Failed to get table statistics: {str(e)}")
            return {}
