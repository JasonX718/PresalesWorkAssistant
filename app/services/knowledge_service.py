"""
Knowledge service layer.

Provides high-level knowledge base operations for the API layer.
"""

import logging
from typing import Optional

from app.knowledge.vector_store import get_vector_store
from app.knowledge.embeddings import get_embedding_service
from app.models.knowledge import (
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeSearchResult,
)

logger = logging.getLogger(__name__)


def search_knowledge(request: KnowledgeSearchRequest) -> KnowledgeSearchResponse:
    """Search the knowledge base."""
    embedding_service = get_embedding_service()
    store = get_vector_store()

    # Generate query embedding
    query_embedding = embedding_service.embed_query(request.query)

    # Build filter
    where = {}
    if request.document_type:
        where["document_type"] = request.document_type
    if request.source_type:
        where["source_type"] = request.source_type

    # Search
    results = store.search(
        query_embedding,
        top_k=request.top_k,
        where=where if where else None,
    )

    search_results = [
        KnowledgeSearchResult(
            content=r["content"],
            score=r["score"],
            metadata=r["metadata"],
        )
        for r in results
    ]

    return KnowledgeSearchResponse(
        query=request.query,
        results=search_results,
        total=len(search_results),
    )


def get_documents() -> list[dict]:
    """Get all document sources in the knowledge base."""
    store = get_vector_store()
    return store.get_all_sources()


def delete_document(source: str) -> dict:
    """Delete all chunks from a source."""
    store = get_vector_store()
    deleted = store.delete_by_source(source)
    return {
        "source": source,
        "chunks_deleted": deleted,
    }


def get_stats() -> dict:
    """Get knowledge base statistics."""
    store = get_vector_store()
    sources = store.get_all_sources()

    return {
        "total_chunks": store.count(),
        "total_sources": len(sources),
        "source_types": _count_by_key(sources, "source_type"),
        "document_types": _count_by_key(sources, "document_type"),
    }


def _count_by_key(items: list[dict], key: str) -> dict:
    """Count items by a specific key."""
    counts = {}
    for item in items:
        val = item.get(key, "unknown")
        counts[val] = counts.get(val, 0) + 1
    return counts
