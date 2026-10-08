def search_top_jobs(jobs, top_k=5):
    """
    Sort jobs by similarity score and return the best matches.

    jobs:
        A list of job dictionaries.

    top_k:
        How many jobs to return.
    """

    # Keep only jobs that have a score
    jobs_with_scores = [
        job for job in jobs
        if "score" in job
    ]

    # Sort from highest score to lowest score
    ranked_jobs = sorted(
        jobs_with_scores,
        key=lambda job: job["score"],
        reverse=True
    )

    # Return only the top results
    return ranked_jobs[:top_k]
