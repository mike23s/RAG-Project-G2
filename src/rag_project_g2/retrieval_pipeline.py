from .vector_search import vector_search
from .filters import filter_jobs
from .scoring import filter_by_score, get_match_level
from .search import search_top_jobs




def retrieve_jobs(
    candidate_profile,
    region=None,
    remote_only=False,
    min_score=0.0,
    top_k=5
):
    # Get real matching jobs from Cosmos DB
    jobs = vector_search(
        candidate_profile,
        top_k=20
    )

    # Filter by region and remote preference
    filtered_jobs = filter_jobs(
        jobs,
        region=region,
        remote_only=remote_only
    )

    # Remove jobs below the score threshold
    scored_jobs = filter_by_score(
        filtered_jobs,
        min_score=min_score
    )

    # Rank jobs and return Top-K
    top_jobs = search_top_jobs(
        scored_jobs,
        top_k=top_k
    )

    # Add readable match level
    for job in top_jobs:
        job["match_level"] = get_match_level(
            job["score"]
        )

    return top_jobs
