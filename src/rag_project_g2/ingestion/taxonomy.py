from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Literal

import httpx

from rag_project_g2.config import get_settings

TaxonomyType = Literal[
    "region",
    "municipality",
    "occupation",
]


@dataclass(frozen=True)
class TaxonomyConcept:
    id: str
    label: str
    type: TaxonomyType
    deprecated: bool = False
    legacy_id: str | None = None


class TaxonomyClient:
    """
    Client for the JobTech Taxonomy API.

    Resolves human-readable labels such as:

        "Stockholms län"
        "Stockholm"
        "Systemutvecklare"

    into JobTech taxonomy concept IDs.
    """

    def __init__(self) -> None:
        settings = get_settings()

        self.base_url = settings.taxonomy_base_url.rstrip("/")

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0,
        )

        # Cache resolved concepts for this client instance.
        self._cache: dict[
            tuple[TaxonomyType, str],
            TaxonomyConcept,
        ] = {}

    async def close(self) -> None:
        await self._client.aclose()

    # ------------------------------------------------------------------
    # Public convenience methods
    # ------------------------------------------------------------------

    async def get_region(
        self,
        name: str,
    ) -> TaxonomyConcept:
        return await self._get_concept(
            "region",
            name,
        )

    async def get_municipality(
        self,
        name: str,
    ) -> TaxonomyConcept:
        return await self._get_concept(
            "municipality",
            name,
        )

    async def get_occupation(
        self,
        name: str,
    ) -> TaxonomyConcept:
        return await self._get_concept(
            "occupation",
            name,
        )

    # ------------------------------------------------------------------
    # List resolution helpers
    # ------------------------------------------------------------------

    async def resolve_regions(
        self,
        names: list[str],
    ) -> list[str]:
        return await self._resolve_ids(
            "region",
            names,
        )

    async def resolve_municipalities(
        self,
        names: list[str],
    ) -> list[str]:
        return await self._resolve_ids(
            "municipality",
            names,
        )

    async def resolve_occupations(
        self,
        names: list[str],
    ) -> list[str]:
        return await self._resolve_ids(
            "occupation",
            names,
        )

    # ------------------------------------------------------------------
    # Generic implementation
    # ------------------------------------------------------------------

    async def _resolve_ids(
        self,
        taxonomy_type: TaxonomyType,
        names: list[str],
    ) -> list[str]:
        if not names:
            return []

        concepts = await asyncio.gather(
            *(
                self._get_concept(
                    taxonomy_type,
                    name,
                )
                for name in names
            )
        )

        return [concept.id for concept in concepts]

    async def _get_concept(
        self,
        taxonomy_type: TaxonomyType,
        name: str,
    ) -> TaxonomyConcept:
        name = name.strip()

        if not name:
            raise ValueError(f"{taxonomy_type} name must not be empty")

        cache_key = (
            taxonomy_type,
            name.casefold(),
        )

        cached = self._cache.get(cache_key)

        if cached is not None:
            return cached

        concepts = await self._search(
            taxonomy_type,
            name,
        )

        if not concepts:
            raise ValueError(f"No JobTech {taxonomy_type} found for {name!r}")

        # Prefer exact label match.
        exact = next(
            (
                concept
                for concept in concepts
                if concept.get(
                    "taxonomy/preferred-label",
                    "",
                ).casefold()
                == name.casefold()
            ),
            None,
        )

        if exact is None:
            possible = [concept.get("taxonomy/preferred-label") for concept in concepts]

            raise ValueError(
                f"No exact JobTech {taxonomy_type} "
                f"found for {name!r}. "
                f"Possible matches: {possible}"
            )

        result = self._to_concept(
            taxonomy_type,
            exact,
        )

        self._cache[cache_key] = result

        return result

    async def _search(
        self,
        taxonomy_type: TaxonomyType,
        name: str,
    ) -> list[dict[str, Any]]:
        response = await self._client.get(
            f"/specific/concepts/{taxonomy_type}",
            params={
                "preferred-label": name,
                "limit": 10,
                "include-deprecated": False,
            },
        )

        response.raise_for_status()

        payload = response.json()

        # Taxonomy endpoints return a list of concepts.
        if not isinstance(payload, list):
            raise RuntimeError("Unexpected Taxonomy API response")

        return payload

    @staticmethod
    def _to_concept(
        taxonomy_type: TaxonomyType,
        data: dict[str, Any],
    ) -> TaxonomyConcept:
        return TaxonomyConcept(
            id=data["taxonomy/id"],
            label=data["taxonomy/preferred-label"],
            type=taxonomy_type,
            deprecated=data.get(
                "taxonomy/deprecated",
                False,
            ),
            legacy_id=data.get("taxonomy/deprecated-legacy-id"),
        )
