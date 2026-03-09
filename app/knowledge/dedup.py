"""
Deduplication logic for knowledge base.

Uses content hashing to prevent duplicate chunks from being stored.
"""

import logging
from app.knowledge.chunker import generate_content_hash

logger = logging.getLogger(__name__)


class DeduplicationService:
    """Handles content deduplication for the knowledge base."""

    def __init__(self, vector_store):
        self._store = vector_store

    def filter_duplicates(self, chunks: list[dict]) -> tuple[list[dict], int]:
        """
        Filter out chunks that already exist in the vector store.

        Returns:
            tuple: (new_chunks, duplicate_count)
        """
        if not chunks:
            return [], 0

        # Collect all content hashes from incoming chunks
        content_hashes = [c["metadata"]["content_hash"] for c in chunks]

        # Check which hashes already exist
        existing_hashes = self._store.get_ids_by_hashes(content_hashes)

        new_chunks = []
        duplicate_count = 0

        for chunk in chunks:
            if chunk["metadata"]["content_hash"] in existing_hashes:
                duplicate_count += 1
            else:
                new_chunks.append(chunk)

        if duplicate_count > 0:
            logger.info(f"Dedup: {duplicate_count} duplicates filtered, {len(new_chunks)} new chunks")

        return new_chunks, duplicate_count

    def is_source_exists(self, source: str) -> bool:
        """Check if content from this source already exists."""
        return self._store.has_source(source)
