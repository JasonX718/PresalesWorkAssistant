"""
AI Work Assistant - Global Configuration
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- OpenAI ---
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536

    # --- ChromaDB ---
    chroma_persist_dir: str = "./data/chroma_db"
    chroma_collection_name: str = "ai_work_assistant"

    # --- App ---
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_debug: bool = True
    log_level: str = "INFO"

    # --- Knowledge Base ---
    chunk_size: int = 800
    chunk_overlap: int = 200
    max_search_results: int = 5

    # --- Bootstrap ---
    seed_data_dir: str = "./data/seed"
    bootstrap_record_count: int = 1000

    # --- URL Ingestion ---
    url_fetch_timeout: int = 30
    url_user_agent: str = "AIWorkAssistant/1.0"

    # --- Time Limits (seconds) ---
    troubleshooting_time_limit: int = 600
    tech_qa_time_limit: int = 180
    weekly_report_time_limit: int = 300
    briefing_time_limit: int = 900
    escalation_time_limit: int = 600

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
