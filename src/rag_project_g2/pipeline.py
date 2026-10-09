"""End-to-end: CV -> search term -> JobTech ads -> Cosmos -> vector search -> top matches.

Run from the repo root (so .env.local and system_prompt.txt are found):

    PYTHONPATH=src python -m rag_project_g2.pipeline src/rag_project_g2/cv.pdf --region "Stockholms län"
"""

import argparse
import asyncio
from dataclasses import dataclass

from rag_project_g2 import cv_reader, llm, pdf
from rag_project_g2.config import get_settings
from rag_project_g2.ingestion.jobsearch import JobTechClient
from rag_project_g2.ingestion.store import upsert_ads
from rag_project_g2.models import JobAd
from rag_project_g2.retrieval_pipeline import retrieve_jobs


def read_cv_text(cv_path: str) -> str:
    """Content Understanding (OCR) first, plain pypdf extraction as fallback."""
    try:
        text = pdf.parse_pdf(cv_path)
    except Exception as err:
        print(f"[CV] Content Understanding unavailable ({err}); using pypdf")
        text = None
    return text or cv_reader.read_cv(cv_path)


async def fetch_jobs(
    search_phrase: str,
    regions: list[str] | None = None,
    remote: bool | None = None,
) -> list[JobAd]:
    client = JobTechClient()
    try:
        return await client.search_jobs(search_phrase, regions=regions, remote=remote)
    finally:
        await client.close()


@dataclass
class MatchResult:
    search_term: str
    fetched: int
    stored: int
    jobs: list[dict]


def match_cv(
    cv_text: str,
    region: str | None = None,
    remote_only: bool = False,
    top_k: int = 5,
    min_score: float | None = None,
) -> MatchResult:
    search_term = llm.get_search_term(cv_text).strip().strip("\"'")

    ads = asyncio.run(
        fetch_jobs(
            search_term,
            regions=[region] if region else None,
            remote=True if remote_only else None,
        )
    )
    stored = upsert_ads(ads)

    jobs = retrieve_jobs(
        cv_text,
        region=region,
        remote_only=remote_only,
        min_score=get_settings().min_similarity if min_score is None else min_score,
        top_k=top_k,
    )
    return MatchResult(search_term, len(ads), stored, jobs)


def run(
    cv_path: str,
    region: str | None = None,
    remote_only: bool = False,
    top_k: int = 5,
) -> list[dict]:
    result = match_cv(read_cv_text(cv_path), region, remote_only, top_k)
    print(f"[LLM] search term: {result.search_term!r}")
    print(f"[JobTech] fetched {result.fetched} ads")
    print(f"[Cosmos] embedded and stored {result.stored} new ads")
    return result.jobs


def main() -> None:
    parser = argparse.ArgumentParser(description="Match a CV against job ads")
    parser.add_argument("cv", nargs="?", default="src/rag_project_g2/cv.pdf")
    parser.add_argument("--region", help='Exact taxonomy label, e.g. "Stockholms län"')
    parser.add_argument("--remote", action="store_true", help="Only remote jobs")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    jobs = run(args.cv, region=args.region, remote_only=args.remote, top_k=args.top_k)

    if not jobs:
        print("No matching jobs found.")
    for i, job in enumerate(jobs, 1):
        print(f"\n{i}. {job['title']} — {job.get('employer') or 'okänd arbetsgivare'}")
        print(f"   {job.get('municipality')}, {job.get('region')}")
        print(f"   {job['match_level']} (score {job['score']:.3f})")
        print(f"   {job['url']}")


if __name__ == "__main__":
    main()
