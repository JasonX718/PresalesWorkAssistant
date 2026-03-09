"""
Knowledge base API endpoints.

POST /knowledge/ingest/file    - Import file
POST /knowledge/ingest/url     - Import URL(s)
POST /knowledge/bootstrap      - Initialize with seed data
POST /knowledge/refresh/url    - Re-fetch URL content
GET  /knowledge/search         - Search knowledge base
GET  /knowledge/documents      - List all documents
GET  /knowledge/stats          - Knowledge base statistics
DELETE /knowledge/document/{source} - Delete document
"""

import logging
import tempfile
import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional

from app.models.knowledge import (
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    FileIngestRequest,
    URLIngestRequest,
    IngestResponse,
    BootstrapResponse,
)
from app.services.knowledge_service import (
    search_knowledge,
    get_documents,
    delete_document,
    get_stats,
)
from app.ingestion.file_ingestor import ingest_file, ingest_directory
from app.ingestion.url_ingestor import ingest_url, ingest_urls
from app.ingestion.bootstrap import bootstrap_knowledge_base

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])


# =============================================================================
# Search
# =============================================================================

@router.post("/search", response_model=KnowledgeSearchResponse)
def api_search_knowledge(request: KnowledgeSearchRequest):
    """Search the knowledge base with a query."""
    try:
        return search_knowledge(request)
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_model=KnowledgeSearchResponse)
def api_search_knowledge_get(
    query: str,
    top_k: int = 5,
    document_type: Optional[str] = None,
    source_type: Optional[str] = None,
):
    """Search knowledge base via GET (convenience endpoint)."""
    request = KnowledgeSearchRequest(
        query=query,
        top_k=top_k,
        document_type=document_type,
        source_type=source_type,
    )
    try:
        return search_knowledge(request)
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Ingestion
# =============================================================================

@router.post("/ingest/file", response_model=IngestResponse)
def api_ingest_file(request: FileIngestRequest):
    """Ingest a local file into the knowledge base."""
    try:
        return ingest_file(
            file_path=request.file_path,
            document_type=request.document_type,
            title=request.title,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"File ingestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest/upload", response_model=IngestResponse)
async def api_upload_file(
    file: UploadFile = File(...),
    document_type: str = Form("general"),
):
    """
    Upload and ingest a file from the browser into the knowledge base.

    Accepts multipart/form-data file upload. Supported formats:
    .md, .txt, .html, .htm, .json, .yaml, .yml, .rst, .csv

    This endpoint is designed for the web frontend (browser-based uploads).
    For server-local files, use POST /knowledge/ingest/file instead.
    """
    # Validate file extension
    suffix = Path(file.filename).suffix.lower() if file.filename else ""
    supported = {".md", ".markdown", ".txt", ".html", ".htm", ".json", ".yaml", ".yml", ".rst", ".csv"}
    if suffix not in supported:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {suffix}. Supported: {', '.join(sorted(supported))}",
        )

    tmp_path = None
    try:
        # Save uploaded file to temp directory
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
            prefix="upload_",
            dir=tempfile.gettempdir(),
        ) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Derive title from original filename
        title = Path(file.filename).stem.replace("_", " ").replace("-", " ").title() if file.filename else None

        # Ingest the temp file
        result = ingest_file(
            file_path=tmp_path,
            document_type=document_type,
            title=title,
        )

        # Update source to show original filename instead of temp path
        if result.sources_processed:
            result.sources_processed = [file.filename or tmp_path]

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload ingestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temp file
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


@router.post("/ingest/url", response_model=IngestResponse)
async def api_ingest_url(request: URLIngestRequest):
    """
    Ingest content from URL(s) into the knowledge base.

    Fetches web pages, extracts content, chunks, embeds, and stores.
    Returns chunk counts and metadata.
    """
    try:
        if len(request.urls) == 1:
            return await ingest_url(
                url=request.urls[0],
                document_type=request.document_type,
                force_refresh=request.force_refresh,
            )
        else:
            return await ingest_urls(
                urls=request.urls,
                document_type=request.document_type,
                force_refresh=request.force_refresh,
            )
    except Exception as e:
        logger.error(f"URL ingestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh/url", response_model=IngestResponse)
async def api_refresh_url(request: URLIngestRequest):
    """Re-fetch and update content from URL(s). Forces refresh."""
    request.force_refresh = True
    try:
        return await ingest_urls(
            urls=request.urls,
            document_type=request.document_type,
            force_refresh=True,
        )
    except Exception as e:
        logger.error(f"URL refresh error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Bootstrap
# =============================================================================

@router.post("/bootstrap", response_model=BootstrapResponse)
def api_bootstrap():
    """
    Bootstrap the knowledge base with initial seed data.

    Loads seed files and generates synthetic data to reach ~1000 records.
    """
    try:
        return bootstrap_knowledge_base()
    except Exception as e:
        logger.error(f"Bootstrap error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Documents Management
# =============================================================================

@router.get("/documents")
def api_get_documents():
    """List all document sources in the knowledge base."""
    try:
        documents = get_documents()
        return {
            "total": len(documents),
            "documents": documents,
        }
    except Exception as e:
        logger.error(f"Get documents error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/document/{source:path}")
def api_delete_document(source: str):
    """Delete all chunks from a specific source."""
    try:
        result = delete_document(source)
        if result["chunks_deleted"] == 0:
            raise HTTPException(status_code=404, detail=f"Source not found: {source}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete document error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Statistics
# =============================================================================

@router.get("/stats")
def api_get_stats():
    """Get knowledge base statistics."""
    try:
        return get_stats()
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
