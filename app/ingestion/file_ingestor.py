"""
File ingestion module.

Handles importing documents from local files (Markdown, text, HTML, etc.)
into the knowledge base.
"""

import os
import logging
from typing import Optional
from pathlib import Path

from app.ingestion.cleaner import clean_text, clean_markdown, clean_html_content, extract_title_from_html
from app.knowledge.chunker import chunk_text
from app.knowledge.embeddings import get_embedding_service
from app.knowledge.vector_store import get_vector_store
from app.knowledge.dedup import DeduplicationService
from app.models.knowledge import IngestResponse

logger = logging.getLogger(__name__)

# Supported file extensions and their handlers
SUPPORTED_EXTENSIONS = {
    ".md": "markdown",
    ".markdown": "markdown",
    ".txt": "text",
    ".html": "html",
    ".htm": "html",
    ".json": "text",
    ".yaml": "text",
    ".yml": "text",
    ".rst": "text",
    ".csv": "text",
}


def read_file(file_path: str) -> tuple[str, str]:
    """
    Read a file and return (content, file_type).

    Returns:
        tuple: (cleaned_content, file_type)
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = path.suffix.lower()
    file_type = SUPPORTED_EXTENSIONS.get(ext, "text")

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        raw_content = f.read()

    if file_type == "markdown":
        content = clean_markdown(raw_content)
    elif file_type == "html":
        content = clean_html_content(raw_content)
    else:
        content = clean_text(raw_content)

    return content, file_type


def ingest_file(
    file_path: str,
    document_type: str = "general",
    title: Optional[str] = None,
) -> IngestResponse:
    """
    Ingest a single file into the knowledge base.

    Steps:
    1. Read and clean file content
    2. Chunk the content
    3. Deduplicate
    4. Generate embeddings
    5. Store in vector database
    """
    response = IngestResponse()

    try:
        # Read and clean
        content, file_type = read_file(file_path)
        if not content or len(content) < 10:
            response.errors.append(f"File too short or empty: {file_path}")
            return response

        # Generate title if not provided
        if not title:
            title = Path(file_path).stem.replace("_", " ").replace("-", " ").title()

        # Chunk
        chunks = chunk_text(
            text=content,
            source=file_path,
            title=title,
            document_type=document_type,
            source_type="file",
        )
        response.total_chunks = len(chunks)

        if not chunks:
            response.errors.append(f"No chunks generated from: {file_path}")
            return response

        # Deduplicate
        store = get_vector_store()
        dedup = DeduplicationService(store)
        new_chunks, dup_count = dedup.filter_duplicates(chunks)
        response.duplicate_skipped = dup_count

        if not new_chunks:
            response.sources_processed.append(file_path)
            return response

        # Generate embeddings
        embedding_service = get_embedding_service()
        texts = [c["content"] for c in new_chunks]
        embeddings = embedding_service.embed_texts(texts)

        # Store
        ids = [c["id"] for c in new_chunks]
        metadatas = [c["metadata"] for c in new_chunks]
        added = store.add_documents(ids, texts, embeddings, metadatas)
        response.new_chunks = added
        response.sources_processed.append(file_path)

        logger.info(f"Ingested file: {file_path} -> {added} new chunks")

    except Exception as e:
        logger.error(f"Error ingesting file {file_path}: {e}")
        response.errors.append(str(e))

    return response


def ingest_directory(
    dir_path: str,
    document_type: str = "general",
    recursive: bool = True,
) -> IngestResponse:
    """Ingest all supported files from a directory."""
    response = IngestResponse()
    path = Path(dir_path)

    if not path.exists() or not path.is_dir():
        response.errors.append(f"Directory not found: {dir_path}")
        return response

    pattern = "**/*" if recursive else "*"
    files = [
        f for f in path.glob(pattern)
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    for file_path in files:
        result = ingest_file(
            str(file_path),
            document_type=document_type,
        )
        response.total_chunks += result.total_chunks
        response.new_chunks += result.new_chunks
        response.duplicate_skipped += result.duplicate_skipped
        response.errors.extend(result.errors)
        response.sources_processed.extend(result.sources_processed)

    return response
