"""Embed job ads and upsert them into the Cosmos `ads` container used by vector_search."""

from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache

from azure.cosmos import ContainerProxy, CosmosClient
from openai import OpenAI

from rag_project_g2.config import get_settings
from rag_project_g2.models import JobAd

EMBED_BATCH_SIZE = 64
MAX_EMBED_CHARS = 6000  # keeps us well under the 8191-token limit of text-embedding-3
DEFAULT_TTL_SECONDS = 14 * 24 * 3600  # ads without a deadline
MIN_TTL_SECONDS = 24 * 3600


@lru_cache
def _openai_client() -> OpenAI:
    settings = get_settings()
    settings.require("azure_openai_api_key")
    return OpenAI(
        api_key=settings.azure_openai_api_key.get_secret_value(),
        base_url=settings.openai_base_url,
    )


@lru_cache
def _ads_container() -> ContainerProxy:
    settings = get_settings()
    settings.require("cosmos_endpoint", "cosmos_key")
    client = CosmosClient(
        settings.cosmos_endpoint, credential=settings.cosmos_key.get_secret_value()
    )
    return client.get_database_client(settings.cosmos_database).get_container_client(
        settings.cosmos_ads_container
    )


def ad_to_text(ad: JobAd) -> str:
    """The text we embed for an ad. Title and occupation first so they always fit."""
    parts = [ad.title, ad.occupation, ad.employer, ad.municipality, ad.description]
    return "\n".join(p for p in parts if p)[:MAX_EMBED_CHARS]


def embed_texts(texts: list[str]) -> list[list[float]]:
    settings = get_settings()
    vectors: list[list[float]] = []
    for start in range(0, len(texts), EMBED_BATCH_SIZE):
        response = _openai_client().embeddings.create(
            model=settings.embedding_deployment,
            input=texts[start : start + EMBED_BATCH_SIZE],
        )
        vectors.extend(item.embedding for item in response.data)
    return vectors


def _ttl_seconds(ad: JobAd) -> int:
    """Expire ads at their application deadline (only applies if TTL is enabled on the container)."""
    if ad.deadline is None:
        return DEFAULT_TTL_SECONDS
    deadline = ad.deadline
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)
    remaining = int((deadline - datetime.now(timezone.utc)).total_seconds())
    return max(remaining, MIN_TTL_SECONDS)


def _existing_ids(ids: list[str]) -> set[str]:
    query = "SELECT VALUE c.id FROM c WHERE ARRAY_CONTAINS(@ids, c.id)"
    return set(
        _ads_container().query_items(
            query=query,
            parameters=[{"name": "@ids", "value": ids}],
            enable_cross_partition_query=True,
        )
    )


def upsert_ads(ads: list[JobAd], *, skip_existing: bool = True) -> int:
    """Embed and store ads. Returns how many were written.

    Ads already in Cosmos are skipped by default so we don't pay to re-embed them.
    """
    # The same ad can appear on several result pages; keep one copy.
    unique = list({ad.id: ad for ad in ads}.values())
    if skip_existing and unique:
        existing = _existing_ids([ad.id for ad in unique])
        unique = [ad for ad in unique if ad.id not in existing]
    if not unique:
        return 0

    vectors = embed_texts([ad_to_text(ad) for ad in unique])

    container = _ads_container()
    for ad, vector in zip(unique, vectors, strict=True):
        doc = ad.model_dump(mode="json")
        doc["embedding"] = vector
        doc["ttl"] = _ttl_seconds(ad)
        container.upsert_item(doc)

    return len(unique)
