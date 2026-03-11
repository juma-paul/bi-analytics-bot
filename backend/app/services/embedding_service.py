import logging
import json
from typing import List, Dict, Any
import numpy as np

from openai import OpenAI

from app.config import settings
from app.core.exceptions import EmbeddingError
from app.database import get_db_context
from app.models.dataset import DatasetEmbedding

logger = logging.getLogger(__name__)

client = OpenAI(api_key=settings.OPENAI_API_KEY)


class EmbeddingService:
    """Generates and manages vector embeddings for RAG"""

    @staticmethod
    def generate_dataset_embeddings(dataset_id: str, df_columns: List[str],
                                    profile_report: Dict[str, Any]):
        """
        Generate embeddings for dataset schema, context, and sample queries

        Embeddings are used for semantic search in RAG
        """
        try:
            embeddings_to_store = []

            # 1. Schema embedding
            schema_text = EmbeddingService._build_schema_text(df_columns, profile_report)
            schema_embedding = EmbeddingService._embed_text(schema_text)
            if schema_embedding:
                embeddings_to_store.append({
                    "dataset_id": dataset_id,
                    "content": schema_text,
                    "embedding": json.dumps(schema_embedding),
                    "embedding_type": "schema",
                    "embedding_metadata": {"columns_count": len(df_columns)},
                })

            # 2. Context embedding
            context_text = EmbeddingService._build_context_text(df_columns)
            context_embedding = EmbeddingService._embed_text(context_text)
            if context_embedding:
                embeddings_to_store.append({
                    "dataset_id": dataset_id,
                    "content": context_text,
                    "embedding": json.dumps(context_embedding),
                    "embedding_type": "context",
                    "embedding_metadata": {},
                })

            # 3. Sample queries
            sample_queries = EmbeddingService._build_sample_queries(df_columns)
            for query in sample_queries:
                query_embedding = EmbeddingService._embed_text(query)
                if query_embedding:
                    embeddings_to_store.append({
                        "dataset_id": dataset_id,
                        "content": query,
                        "embedding": json.dumps(query_embedding),
                        "embedding_type": "sample_query",
                        "embedding_metadata": {},
                    })

            # Store embeddings in database
            with get_db_context() as db:
                for emb_data in embeddings_to_store:
                    emb = DatasetEmbedding(**emb_data)
                    db.add(emb)
                db.commit()

            logger.info(f"Generated {len(embeddings_to_store)} embeddings for dataset {dataset_id}")
            return len(embeddings_to_store)

        except Exception as e:
            raise EmbeddingError(f"Embedding generation failed: {str(e)}")

    @staticmethod
    def _embed_text(text: str) -> List[float]:
        """Generate embedding for text using OpenAI API"""
        try:
            response = client.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input=text,
            )
            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding for text: {text[:50]}...")
            return embedding

        except Exception as e:
            logger.error(f"OpenAI embedding failed: {str(e)}")
            return None

    @staticmethod
    def _build_schema_text(columns: List[str], profile_report: Dict[str, Any]) -> str:
        """Build human-readable schema description"""
        schema_text = "Dataset schema:\n"

        for col in columns:
            if col in profile_report["columns"]:
                col_profile = profile_report["columns"][col]
                col_type = col_profile.get("type", "VARCHAR")

                schema_text += f"- {col} ({col_type})"

                # Add sample values
                if col_profile.get("sample_values"):
                    samples = col_profile["sample_values"][:3]
                    schema_text += f" [Examples: {', '.join(str(s) for s in samples)}]"

                schema_text += "\n"

        return schema_text

    @staticmethod
    def _build_context_text(columns: List[str]) -> str:
        """Build dataset context description"""
        return f"""This is a dataset for analytics and querying.
It contains {len(columns)} columns: {', '.join(columns)}.
Use these columns to answer user questions about the data."""

    @staticmethod
    def _build_sample_queries(columns: List[str]) -> List[str]:
        """Build sample queries for the dataset"""
        queries = [
            f"Show all rows with distinct values from {columns[0] if columns else 'data'}",
            f"Count records grouped by {columns[0] if columns else 'data'}",
            f"Find the top values in {columns[0] if columns else 'data'}",
            "Show summary statistics for the dataset",
            "List all columns and their data types",
        ]

        # Add domain-specific queries if we detect certain columns
        if any("date" in col.lower() for col in columns):
            queries.append("Show data aggregated by date range")

        if any(any(x in col.lower() for x in ["count", "total", "amount"]) for col in columns):
            queries.append("Calculate totals and averages")

        return queries[:5]  # Return top 5

    @staticmethod
    def search_similar_embeddings(query_embedding: List[float], dataset_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar embeddings (RAG retrieval)"""
        try:
            with get_db_context() as db:
                # For now, return all embeddings (will need pgvector extension for true semantic search)
                embeddings = db.query(DatasetEmbedding).filter(
                    DatasetEmbedding.dataset_id == dataset_id
                ).limit(limit).all()

                results = []
                for emb in embeddings:
                    results.append({
                        "content": emb.content,
                        "embedding_type": emb.embedding_type,
                        "metadata": emb.embedding_metadata,
                    })

                logger.info(f"Retrieved {len(results)} similar embeddings")
                return results

        except Exception as e:
            logger.error(f"Embedding search failed: {str(e)}")
            return []
