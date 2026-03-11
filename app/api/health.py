"""
Health check API endpoint.
"""

from fastapi import APIRouter
from app.knowledge.vector_store import get_vector_store
from config import get_settings

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    """System health check."""
    settings = get_settings()
    try:
        store = get_vector_store()
        doc_count = store.count()
        db_status = "healthy"
    except Exception as e:
        doc_count = 0
        db_status = f"error: {str(e)}"

    return {
        "status": "running",
        "auth_required": bool(settings.auth_api_key),
        "vector_db": {
            "status": db_status,
            "document_count": doc_count,
        },
        "llm_model": settings.llm_model,
        "embedding_model": settings.embedding_model,
        "openai_configured": bool(settings.openai_api_key),
    }
