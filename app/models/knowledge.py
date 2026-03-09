"""
Knowledge base data models.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class DocumentMetadata(BaseModel):
    """Metadata attached to each document chunk in the vector store."""
    source: str = ""                    # file path or URL
    source_type: str = "file"           # file | url | seed
    title: str = ""
    document_type: str = ""             # faq, troubleshooting, architecture, etc.
    chunk_id: str = ""
    content_hash: str = ""
    fetch_timestamp: str = ""
    original_doc_id: str = ""


class KnowledgeSearchRequest(BaseModel):
    """Request model for knowledge search."""
    query: str
    top_k: int = Field(default=5, ge=1, le=20)
    document_type: Optional[str] = None
    source_type: Optional[str] = None


class KnowledgeSearchResult(BaseModel):
    """Single search result from knowledge base."""
    content: str
    score: float
    metadata: dict = Field(default_factory=dict)


class KnowledgeSearchResponse(BaseModel):
    """Response for knowledge search."""
    query: str
    results: list[KnowledgeSearchResult]
    total: int


class FileIngestRequest(BaseModel):
    """Request to ingest a file."""
    file_path: str
    document_type: str = "general"
    title: Optional[str] = None


class URLIngestRequest(BaseModel):
    """Request to ingest content from URL(s)."""
    urls: list[str]
    document_type: str = "web"
    force_refresh: bool = False


class IngestResponse(BaseModel):
    """Response from ingestion operations."""
    total_chunks: int = 0
    new_chunks: int = 0
    duplicate_skipped: int = 0
    errors: list[str] = Field(default_factory=list)
    sources_processed: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class BootstrapResponse(BaseModel):
    """Response from bootstrap operation."""
    total_records: int = 0
    chunks_created: int = 0
    errors: list[str] = Field(default_factory=list)
    duration_seconds: float = 0.0


class DocumentInfo(BaseModel):
    """Information about a stored document."""
    doc_id: str
    source: str
    title: str
    document_type: str
    source_type: str
    chunk_count: int = 0
    fetch_timestamp: str = ""
