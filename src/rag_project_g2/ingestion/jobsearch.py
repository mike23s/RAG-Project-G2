from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from rag_project_g2.config import get_settings
from rag_project_g2.models import JobAd


class JobTechClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.base_url = self.settings.jobsearch_base_url.rstrip("/")

    async def search_jobs(
        self,
        query: str,
        *,
        max_pages: int | None = None,
        limit: int | None = None,
    ) -> list[JobAd]:
        """
        Search JobTech for jobs matching a free-text query.

        Example:
            jobs = await client.search_jobs("python developer")

        Returns normalized JobAd objects.
        """

        if not query.strip():
            raise ValueError("query must not be empty")

        max_pages = max_pages or self.settings.max_pages_per_query
        limit = min(
            limit or self.settings.max_ads_per_query,
            self.settings.max_ads_per_query,
        )

        jobs: list[JobAd] = []

        async with httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0,
        ) as client:
            for page in range(max_pages):
                offset = page * limit

                response = await client.get(
                    "/search",
                    params={
                        "q": query,
                        "limit": limit,
                        "offset": offset,
                    },
                )

                response.raise_for_status()
                payload = response.json()

                hits = payload.get("hits", [])

                if not hits:
                    break

                jobs.extend(self._to_job_ad(hit) for hit in hits)

                # Last page — no reason to request another.
                if len(hits) < limit:
                    break

        return jobs

    @staticmethod
    def _to_job_ad(data: dict[str, Any]) -> JobAd:
        """
        Convert JobTech's native job-ad representation into our
        source-agnostic JobAd model.
        """

        workplace = data.get("workplace_address") or {}
        employer = data.get("employer") or {}

        occupation = data.get("occupation") or {}
        occupation_group = data.get("occupation_group") or {}

        source_id = str(data.get("id") or data.get("external_id"))

        return JobAd(
            id=f"jobtech:{source_id}",
            source="jobtech",
            source_id=source_id,
            title=data.get("headline") or data.get("title") or "",
            employer=employer.get("name"),
            description=data.get("description", {}).get("text", "")
            if isinstance(data.get("description"), dict)
            else data.get("description", "") or "",
            municipality=workplace.get("municipality"),
            region=workplace.get("region"),
            region_id=workplace.get("region_code"),
            occupation=occupation.get("label"),
            occupation_id=occupation.get("concept_id"),
            occupation_group_id=occupation_group.get("concept_id"),
            must_have_skills=[],
            nice_to_have_skills=[],
            url=(
                data.get("webpage_url")
                or data.get("application_details", {}).get("url")
                or ""
            ),
            published_at=_parse_datetime(data.get("publication_date")),
            deadline=_parse_datetime(data.get("application_deadline")),
            remote=None,
        )


def _parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None

    if isinstance(value, datetime):
        return value

    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
