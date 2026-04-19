"""
facesyma_ai/rag/__init__.py
===========================
RAG (Retrieval Augmented Generation) system untuk Facesyma.

Components:
  - embedder: Ollama nomic-embed-text dengan caching
  - knowledge_base: Chroma vector database CRUD
  - retriever: Semantic search query builder
  - populate_db: Data load script (sifat, celebrities, golden ratio, personality types)
"""

from .embedder import embed_text, get_embedding_dimension
from .knowledge_base import search_knowledge_base, get_collection_stats
from .retriever import get_relevant_context

__all__ = [
    'embed_text',
    'get_embedding_dimension',
    'search_knowledge_base',
    'get_collection_stats',
    'get_relevant_context',
]
