"""
Vector store wrapper for ChromaDB.

Provides a clean interface for storing, searching, and managing
document chunks with their embeddings.
"""

import logging
from typing import Optional
import chromadb
from chromadb.config import Settings as ChromaSettings

from config import get_settings

logger = logging.getLogger(__name__)


class VectorStore:
    """ChromaDB vector store wrapper."""

    def __init__(self):
        settings = get_settings()
        self._client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=settings.chroma_collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            f"VectorStore initialized. Collection '{settings.chroma_collection_name}' "
            f"has {self._collection.count()} documents."
        )

    @property
    def collection(self):
        return self._collection

    def add_documents(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict],
    ) -> int:
        """
        Add document chunks to the vector store.
        Returns number of documents added.
        """
        if not ids:
            return 0

        # Filter out existing IDs to avoid duplicates
        existing = set()
        try:
            result = self._collection.get(ids=ids)
            if result and result["ids"]:
                existing = set(result["ids"])
        except Exception:
            pass

        new_ids = []
        new_docs = []
        new_embeds = []
        new_metas = []

        for i, doc_id in enumerate(ids):
            if doc_id not in existing:
                new_ids.append(doc_id)
                new_docs.append(documents[i])
                new_embeds.append(embeddings[i])
                new_metas.append(metadatas[i])

        if not new_ids:
            logger.info("All documents already exist. Skipping.")
            return 0

        self._collection.add(
            ids=new_ids,
            documents=new_docs,
            embeddings=new_embeds,
            metadatas=new_metas,
        )
        logger.info(f"Added {len(new_ids)} documents. Skipped {len(existing)} duplicates.")
        return len(new_ids)

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        where: Optional[dict] = None,
    ) -> list[dict]:
        """
        Search for similar documents.
        Returns list of {content, score, metadata} dicts.
        """
        kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": min(top_k, self._collection.count() or 1),
        }
        if where:
            kwargs["where"] = where

        try:
            results = self._collection.query(**kwargs)
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

        output = []
        if results and results["documents"] and results["documents"][0]:
            docs = results["documents"][0]
            distances = results["distances"][0] if results.get("distances") else [0.0] * len(docs)
            metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)

            for doc, dist, meta in zip(docs, distances, metas):
                # ChromaDB cosine distance: 0 = identical, 2 = opposite
                # Convert to similarity score: 1 - (distance / 2)
                score = 1.0 - (dist / 2.0)
                output.append({
                    "content": doc,
                    "score": round(score, 4),
                    "metadata": meta,
                })

        return output

    def delete_by_source(self, source: str) -> int:
        """Delete all chunks from a specific source. Returns count deleted."""
        try:
            results = self._collection.get(where={"source": source})
            if results and results["ids"]:
                self._collection.delete(ids=results["ids"])
                count = len(results["ids"])
                logger.info(f"Deleted {count} chunks from source: {source}")
                return count
        except Exception as e:
            logger.error(f"Delete error: {e}")
        return 0

    def get_all_sources(self, limit: int = 0, offset: int = 0) -> list[dict]:
        """Get information about all unique sources in the store.

        Args:
            limit: Max number of sources to return (0 = all).
            offset: Number of sources to skip (for pagination).
        """
        try:
            all_data = self._collection.get(include=["metadatas"])
            if not all_data or not all_data["metadatas"]:
                return []

            sources = {}
            for meta in all_data["metadatas"]:
                src = meta.get("source", "unknown")
                if src not in sources:
                    sources[src] = {
                        "source": src,
                        "title": meta.get("title", ""),
                        "source_type": meta.get("source_type", ""),
                        "document_type": meta.get("document_type", ""),
                        "chunk_count": 0,
                    }
                sources[src]["chunk_count"] += 1

            all_sources = list(sources.values())

            if offset:
                all_sources = all_sources[offset:]
            if limit > 0:
                all_sources = all_sources[:limit]

            return all_sources
        except Exception as e:
            logger.error(f"Error getting sources: {e}")
            return []

    def count(self) -> int:
        """Get total document count."""
        return self._collection.count()

    def has_source(self, source: str) -> bool:
        """Check if a source already exists in the store."""
        try:
            results = self._collection.get(
                where={"source": source},
                limit=1,
            )
            return bool(results and results["ids"])
        except Exception:
            return False

    def get_ids_by_hashes(self, content_hashes: list[str]) -> set[str]:
        """Get existing content hashes to detect duplicates (batched)."""
        if not content_hashes:
            return set()

        existing = set()
        try:
            batch_size = 50
            for i in range(0, len(content_hashes), batch_size):
                batch = content_hashes[i:i + batch_size]
                if len(batch) == 1:
                    results = self._collection.get(
                        where={"content_hash": batch[0]},
                        include=["metadatas"],
                    )
                else:
                    results = self._collection.get(
                        where={"content_hash": {"$in": batch}},
                        include=["metadatas"],
                    )
                if results and results["metadatas"]:
                    for meta in results["metadatas"]:
                        h = meta.get("content_hash")
                        if h:
                            existing.add(h)
        except Exception as e:
            logger.warning(f"Batch hash lookup failed, falling back to single: {e}")
            for h in content_hashes:
                try:
                    results = self._collection.get(
                        where={"content_hash": h},
                        limit=1,
                    )
                    if results and results["ids"]:
                        existing.add(h)
                except Exception:
                    pass
        return existing


# Singleton instance
_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Get or create the singleton vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
