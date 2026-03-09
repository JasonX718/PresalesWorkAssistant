"""
Document chunking utilities.

Splits documents into smaller chunks suitable for embedding and retrieval.
"""

import logging
import hashlib
import uuid
from typing import Optional

from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import get_settings

logger = logging.getLogger(__name__)


def generate_content_hash(content: str) -> str:
    """Generate a hash for content deduplication."""
    import xxhash
    return xxhash.xxh64(content.encode("utf-8")).hexdigest()


def generate_chunk_id(source: str, index: int) -> str:
    """Generate a unique chunk ID."""
    base = f"{source}::chunk_{index}"
    return hashlib.md5(base.encode()).hexdigest()


def chunk_text(
    text: str,
    source: str = "",
    title: str = "",
    document_type: str = "general",
    source_type: str = "file",
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
) -> list[dict]:
    """
    Split text into chunks with metadata.

    Returns list of dicts with keys:
        - id: unique chunk ID
        - content: chunk text
        - metadata: dict with source info
    """
    settings = get_settings()
    _chunk_size = chunk_size or settings.chunk_size
    _chunk_overlap = chunk_overlap or settings.chunk_overlap

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=_chunk_size,
        chunk_overlap=_chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", "。", ".", " ", ""],
    )

    chunks_text = splitter.split_text(text)

    if not chunks_text:
        return []

    from datetime import datetime

    chunks = []
    for i, chunk_content in enumerate(chunks_text):
        content_hash = generate_content_hash(chunk_content)
        chunk_id = generate_chunk_id(source, i)

        chunks.append({
            "id": chunk_id,
            "content": chunk_content,
            "metadata": {
                "source": source,
                "source_type": source_type,
                "title": title,
                "document_type": document_type,
                "chunk_id": chunk_id,
                "content_hash": content_hash,
                "fetch_timestamp": datetime.now().isoformat(),
                "original_doc_id": hashlib.md5(source.encode()).hexdigest() if source else str(uuid.uuid4()),
                "chunk_index": i,
                "total_chunks": len(chunks_text),
            },
        })

    logger.info(f"Chunked '{source}' into {len(chunks)} chunks (size={_chunk_size}, overlap={_chunk_overlap})")
    return chunks
