from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from rag_project_g2.config import get_settings
from rag_project_g2.ingestion.taxonomy import TaxonomyClient
from rag_project_g2.models import JobAd


class JobTechClient:
    def __init__(self) -> None:
        self.settings = get_settings()

        self.base_url = self.settings.jobsearch_base_url.rstrip("/")

        self.taxonomy = TaxonomyClient()

    async def close(self) -> None:
        await self.taxonomy.close()

    async def search_jobs(
        self,
        query: str,
        *,
        regions: list[str] | None = None,
        municipalities: list[str] | None = None,
        occupations: list[str] | None = None,
        remote: bool | None = None,
        max_pages: int | None = None,
        limit: int | None = None,
    ) -> list[JobAd]:

        if not query.strip():
            raise ValueError("query must not be empty")

        max_pages = max_pages or self.settings.max_pages_per_query

        limit = min(
            limit or self.settings.max_ads_per_query,
            self.settings.max_ads_per_query,
        )

        # Resolve human-readable taxonomy names.
        region_ids = await self.taxonomy.resolve_regions(regions or [])

        municipality_ids = await self.taxonomy.resolve_municipalities(
            municipalities or []
        )

        occupation_ids = await self.taxonomy.resolve_occupations(occupations or [])

        jobs: list[JobAd] = []

        async with httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0,
        ) as client:
            for page in range(max_pages):
                offset = page * limit

                params: list[tuple[str, str | int]] = [
                    ("q", query),
                    ("limit", limit),
                    ("offset", offset),
                ]

                for region_id in region_ids:
                    params.append(("region", region_id))

                for municipality_id in municipality_ids:
                    params.append(("municipality", municipality_id))

                for occupation_id in occupation_ids:
                    params.append(("occupation", occupation_id))

                # The API detects remote work from the ad text; hits carry no reliable flag.
                if remote is not None:
                    params.append(("remote", str(remote).lower()))

                response = await client.get(
                    "/search",
                    params=params,
                )

                response.raise_for_status()

                payload = response.json()
                hits = payload.get("hits", [])

                if not hits:
                    break

                jobs.extend(self._to_job_ad(hit, remote=remote) for hit in hits)

                if len(hits) < limit:
                    break

        return jobs

    @staticmethod
    def _to_job_ad(
        data: dict[str, Any],
        remote: bool | None = None,
    ) -> JobAd:

        workplace = data.get("workplace_address") or {}

        employer = data.get("employer") or {}

        occupation = data.get("occupation") or {}

        occupation_group = data.get("occupation_group") or {}

        workplace_model = (
            (data.get("workplace_model") or {}).get("label") or ""
        ).casefold()

        if remote is None and workplace_model:
            remote = "distans" in workplace_model or "remote" in workplace_model

        source_id = str(data.get("id") or data.get("external_id"))

        return JobAd(
            id=f"jobtech:{source_id}",
            source="jobtech",
            source_id=source_id,
            title=(data.get("headline") or data.get("title") or ""),
            employer=employer.get("name"),
            description=(
                data.get("description", {}).get(
                    "text",
                    "",
                )
                if isinstance(
                    data.get("description"),
                    dict,
                )
                else (data.get("description", "") or "")
            ),
            municipality=workplace.get("municipality"),
            region=workplace.get("region"),
            region_id=(
                workplace.get("regionconceptid") or workplace.get("region_code")
            ),
            occupation=occupation.get("label"),
            occupation_id=occupation.get("concept_id"),
            occupation_group_id=(occupation_group.get("concept_id")),
            must_have_skills=[],
            nice_to_have_skills=[],
            url=(
                data.get("webpage_url")
                or data.get(
                    "application_details",
                    {},
                ).get("url")
                or ""
            ),
            published_at=_parse_datetime(data.get("publication_date")),
            deadline=_parse_datetime(data.get("application_deadline")),
            remote=remote,
        )


def _parse_datetime(
    value: Any,
) -> datetime | None:
    if not value:
        return None

    if isinstance(value, datetime):
        return value

    try:
        return datetime.fromisoformat(
            str(value).replace(
                "Z",
                "+00:00",
            )
        )
    except ValueError:
        return None
