"""Typed application settings, loaded from environment variables and `.env.local`."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Later files win. `.env` kept so existing local setups keep working; both are git-ignored.
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Azure AI Foundry (OpenAI-compatible v1 endpoint) ---
    azure_openai_endpoint: str | None = Field(
        None, description="https://<resource>.openai.azure.com"
    )
    azure_openai_api_key: SecretStr | None = None
    chat_deployment: str = "gpt-5.4"
    embedding_deployment: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    # --- Azure Content Understanding (CV/letter OCR; same Foundry resource is fine) ---
    # Env names match the first implementation: CONTENTUNDERSTANDING_ENDPOINT / _KEY.
    contentunderstanding_endpoint: str | None = None
    contentunderstanding_key: SecretStr | None = None
    contentunderstanding_analyzer: str = (
        "prebuilt-read"  # OCR only, no LLM deployment needed
    )
    contentunderstanding_api_version: str = (
        "2025-11-01"  # GA; "2026-06-01-preview" also works
    )

    # --- Cosmos DB for NoSQL ---
    cosmos_endpoint: str | None = None
    cosmos_key: SecretStr | None = None
    cosmos_database: str = "jobmatch"
    cosmos_ads_container: str = "ads"
    cosmos_queries_container: str = "query_cache"

    # --- JobTech APIs (no key required as of 2026-10) ---
    jobsearch_base_url: str = "https://jobsearch.api.jobtechdev.se"
    taxonomy_base_url: str = (
        "https://taxonomy.api.jobtechdev.se/v1/taxonomy"  # possibly unnessesary
    )
    jobtech_api_key: SecretStr | None = None  # not needed at this time

    # --- Retrieval / matching knobs ---
    query_cache_ttl_seconds: int = 24 * 3600
    max_ads_per_query: int = 100  # JobSearch hard limit per page is 100
    max_pages_per_query: int = 2  # => at most 200 ads fetched per occupation query
    vector_top_k: int = 30
    min_similarity: float = 0.30  # calibrate on real data, see docs/GUIDE.md
    rerank_top_n: int = 10  # how many candidates the LLM explains
    weight_llm: float = 0.6  # final = w_llm * llm_fit + (1 - w_llm) * similarity

    ## Raise error for missing values
    def require(self, *names: str) -> None:
        missing = [n.upper() for n in names if not getattr(self, n)]
        if missing:
            raise RuntimeError(f"Missing settings {missing} — fill them in .env.local")


@lru_cache
def get_settings() -> Settings:
    return Settings()
