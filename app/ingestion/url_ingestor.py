"""
URL ingestion module.

Handles importing documents from web URLs into the knowledge base.
Fetches, cleans, chunks, embeds, and stores web content.
"""

import logging
from typing import Optional
from datetime import datetime

import httpx

from app.ingestion.cleaner import clean_html_content, extract_title_from_html
from app.knowledge.chunker import chunk_text
from app.knowledge.embeddings import get_embedding_service
from app.knowledge.vector_store import get_vector_store
from app.knowledge.dedup import DeduplicationService
from app.models.knowledge import IngestResponse
from config import get_settings

logger = logging.getLogger(__name__)


async def fetch_url(url: str) -> tuple[str, str]:
    """
    Fetch content from a URL.

    Returns:
        tuple: (html_content, title)
    """
    settings = get_settings()

    headers = {
        "User-Agent": settings.url_user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }

    async with httpx.AsyncClient(
        timeout=settings.url_fetch_timeout,
        follow_redirects=True,
        verify=False,
    ) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        html = response.text

    title = extract_title_from_html(html)
    return html, title


async def ingest_url(
    url: str,
    document_type: str = "web",
    force_refresh: bool = False,
    title_override: Optional[str] = None,
) -> IngestResponse:
    """
    Ingest content from a single URL into the knowledge base.

    Steps:
    1. Check for duplicates (unless force_refresh)
    2. Fetch URL content
    3. Clean HTML → plain text
    4. Chunk the content
    5. Deduplicate at chunk level
    6. Generate embeddings
    7. Store in vector database
    """
    response = IngestResponse()

    try:
        store = get_vector_store()
        dedup = DeduplicationService(store)

        # Check if URL already imported
        if not force_refresh and dedup.is_source_exists(url):
            response.duplicate_skipped = 1
            response.metadata = {"message": f"URL already imported: {url}. Use force_refresh=true to update."}
            response.sources_processed.append(url)
            return response

        # If force refresh, delete existing chunks first
        if force_refresh:
            deleted = store.delete_by_source(url)
            if deleted > 0:
                logger.info(f"Deleted {deleted} existing chunks for refresh: {url}")

        # Fetch
        html, title = await fetch_url(url)
        if title_override:
            title = title_override

        # Clean
        content = clean_html_content(html)
        if not content or len(content) < 50:
            response.errors.append(f"Insufficient content extracted from: {url}")
            return response

        # Chunk
        chunks = chunk_text(
            text=content,
            source=url,
            title=title or url,
            document_type=document_type,
            source_type="url",
        )
        response.total_chunks = len(chunks)

        if not chunks:
            response.errors.append(f"No chunks generated from: {url}")
            return response

        # Deduplicate
        new_chunks, dup_count = dedup.filter_duplicates(chunks)
        response.duplicate_skipped += dup_count

        if not new_chunks:
            response.sources_processed.append(url)
            return response

        # Embed
        embedding_service = get_embedding_service()
        texts = [c["content"] for c in new_chunks]
        embeddings = embedding_service.embed_texts(texts)

        # Store
        ids = [c["id"] for c in new_chunks]
        metadatas = [c["metadata"] for c in new_chunks]
        added = store.add_documents(ids, texts, embeddings, metadatas)
        response.new_chunks = added
        response.sources_processed.append(url)

        response.metadata = {
            "title": title,
            "url": url,
            "content_length": len(content),
            "fetch_timestamp": datetime.now().isoformat(),
        }

        logger.info(f"Ingested URL: {url} -> {added} new chunks")

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching {url}: {e}")
        response.errors.append(f"HTTP {e.response.status_code}: {url}")
    except httpx.TimeoutException:
        logger.error(f"Timeout fetching {url}")
        response.errors.append(f"Timeout fetching: {url}")
    except Exception as e:
        logger.error(f"Error ingesting URL {url}: {e}")
        response.errors.append(str(e))

    return response


async def ingest_urls(
    urls: list[str],
    document_type: str = "web",
    force_refresh: bool = False,
) -> IngestResponse:
    """Ingest multiple URLs."""
    combined = IngestResponse()

    for url in urls:
        result = await ingest_url(url, document_type, force_refresh)
        combined.total_chunks += result.total_chunks
        combined.new_chunks += result.new_chunks
        combined.duplicate_skipped += result.duplicate_skipped
        combined.errors.extend(result.errors)
        combined.sources_processed.extend(result.sources_processed)

    return combined
